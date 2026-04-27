# MON-FN-005: MIXPANEL_TOKEN Startup Assertion (Boot Fail Se Ausente)

**Priority:** P0
**Effort:** S (0.5-1 dia)
**Squad:** @dev + @devops
**Status:** Ready
**Epic:** [EPIC-MON-FN-2026-Q2](EPIC-MON-FN-2026-Q2.md)
**Sprint:** 1 (29/abr–05/mai)
**Sprint Window:** Sprint 1 (paralelo, S effort, 0 bloqueio)
**Dependências bloqueadoras:** Nenhuma

---

## Contexto

`backend/analytics_events.py:26-30` lazy-init Mixpanel client e silenciosamente cai em `logger.debug()` quando `MIXPANEL_TOKEN` ausente:

```python
token = os.getenv("MIXPANEL_TOKEN", "").strip()
if not token:
    logger.debug("MIXPANEL_TOKEN not configured — analytics events will be logged only")
    return None
```

**Memory `reference_mixpanel_backend_token_gap_2026_04_24`** documenta que até `piped-cray` deploy, var `MIXPANEL_TOKEN` estava **ausente em `bidiq-backend`** Railway service — silenciou eventos `paywall_hit`, `trial_started` em prod por **período não definido**. Evento foi descoberto por acidente durante outra investigação. Cegueira analytics destrói qualquer tentativa de medir funil.

**Problema sistêmico:** `track_event` é fire-and-forget (linha 60: `pass # Fire-and-forget — never fail`) — desenho correto para resilience, mas perigoso em prod sem assertion explícita: bug silencioso indistinguível de "sem eventos no período". Requer **fail-closed em prod** (boot fail) + healthcheck visível.

**Por que P0:** todo o EPIC-MON-FN depende de eventos visíveis em Mixpanel; sem assertion, qualquer rollout futuro pode silenciosamente degradar telemetria. S effort, 0 dependência, máxima alavancagem.

**Paths críticos:**
- `backend/analytics_events.py:19-41` (lazy init)
- `backend/main.py` (startup hook FastAPI lifespan)
- `backend/config.py` (env var declaration)
- `backend/routes/health.py` (healthcheck `/health/ready`)

---

## Acceptance Criteria

### AC1: Boot fail em prod se `MIXPANEL_TOKEN` ausente

Given que `ENVIRONMENT=production`,
When backend startup,
Then app falha boot com `RuntimeError` se `MIXPANEL_TOKEN` ausente ou string vazia.

- [ ] Em `backend/main.py:lifespan` (ou novo `backend/startup/assertions.py`):
```python
import os
import logging

logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS_PRODUCTION = {
    "MIXPANEL_TOKEN": "Funnel analytics token (Mixpanel project settings)",
    # add more here as we harden config (ALL P0 envs go here over time)
}

def assert_required_env_vars() -> None:
    """Boot-time assertion: fail fast if required env vars missing in production.

    MON-FN-005: Operationalizes memory `reference_mixpanel_backend_token_gap_2026_04_24`
    where MIXPANEL_TOKEN was silently absent in prod for unknown period.

    Raises:
        RuntimeError: if any required var is missing/empty in production env.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env != "production":
        logger.info(f"Env-var assertion skipped (ENVIRONMENT={env})")
        return

    missing = []
    for var_name, description in REQUIRED_ENV_VARS_PRODUCTION.items():
        value = os.getenv(var_name, "").strip()
        if not value:
            missing.append(f"  - {var_name}: {description}")

    if missing:
        msg = (
            "FATAL: Required environment variables missing in production:\n"
            + "\n".join(missing)
            + "\n\nSet these via `railway variables --service bidiq-backend set ...`"
        )
        logger.critical(msg)
        raise RuntimeError(msg)

    logger.info(f"Env-var assertion passed: {len(REQUIRED_ENV_VARS_PRODUCTION)} required vars present")
```
- [ ] Chamar `assert_required_env_vars()` no `lifespan` ANTES de aceitar tráfego
- [ ] Em dev (`ENVIRONMENT != production`), warn-only: log `WARNING` + continue
- [ ] Documentar em `docs/operations/env-vars.md`: lista de "required in production" vars

### AC2: Eager Mixpanel initialization em prod

Given assertion AC1 passou,
When startup,
Then forçar `_get_mixpanel()` chamada eager (não lazy) e validar conexão.

- [ ] Em `assertions.py` ou direto em lifespan, adicionar:
```python
def assert_mixpanel_reachable() -> None:
    """Validate Mixpanel client initializes successfully in production."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env != "production":
        return
    from analytics_events import _get_mixpanel
    mp = _get_mixpanel()  # forces lazy init now
    if mp is None:
        raise RuntimeError(
            "Mixpanel client failed to initialize in production. "
            "Check MIXPANEL_TOKEN and 'mixpanel-python' package installed."
        )
    # Smoke event — fire-and-forget, doesn't block boot
    try:
        mp.track("system", "backend_boot", {
            "environment": env,
            "release": os.getenv("SENTRY_RELEASE", "unknown"),
        })
    except Exception as e:
        logger.warning(f"Mixpanel boot smoke event failed (non-fatal): {e}")
```
- [ ] Smoke event `backend_boot` permite verificação visual em Mixpanel "Live View" pós-deploy
- [ ] Capturar `mixpanel-python` ImportError → boot fail (lib é dep obrigatória)

### AC3: Healthcheck `/health/ready` reporta Mixpanel

Given que kubernetes-style readiness probe espera 200 antes de rotear traffic,
When `GET /health/ready`,
Then retorna 200 só se Mixpanel reachable + DB + Redis OK.

- [ ] Estender `backend/routes/health.py` (ou criar `health_core.py` se não existir):
```python
@router.get("/health/ready")
async def health_ready() -> dict:
    """Readiness probe — used by Railway healthcheck.

    Returns 200 only if all critical dependencies are reachable.
    503 in any failure (Railway will not route traffic).
    """
    checks = {}
    overall_ok = True

    # 1. DB
    try:
        sb = get_supabase()
        sb.table("profiles").select("id").limit(1).execute()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"failed: {str(e)[:100]}"
        overall_ok = False

    # 2. Redis
    try:
        redis = await get_redis_client()
        await redis.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"failed: {str(e)[:100]}"
        overall_ok = False

    # 3. Mixpanel (best-effort — HEAD request, doesn't fail boot)
    try:
        from analytics_events import _get_mixpanel
        mp = _get_mixpanel()
        checks["mixpanel"] = "configured" if mp else "not_configured"
        # In production, "not_configured" is an error
        if os.getenv("ENVIRONMENT") == "production" and not mp:
            overall_ok = False
    except Exception as e:
        checks["mixpanel"] = f"check_failed: {str(e)[:100]}"
        overall_ok = False

    status_code = 200 if overall_ok else 503
    return JSONResponse(content={"status": "ok" if overall_ok else "degraded", "checks": checks}, status_code=status_code)
```
- [ ] Manter `/health/live` separado (apenas valida que processo está vivo) — não verifica deps
- [ ] Railway service config aponta healthcheck para `/health/ready`
- [ ] Counter Prometheus `smartlic_health_check_failures_total{check}` para alerting

### AC4: Logging e Sentry em init failure

Given Mixpanel init falha (`ImportError`, ou `MIXPANEL_TOKEN` rejeitado por SDK),
When detectado,
Then loga error + Sentry capture com fingerprint `["mixpanel_init", failure_type]`.

- [ ] Modificar `analytics_events.py:_get_mixpanel`:
```python
def _get_mixpanel():
    global _mixpanel_client, _mixpanel_initialized
    if _mixpanel_initialized:
        return _mixpanel_client
    _mixpanel_initialized = True

    token = os.getenv("MIXPANEL_TOKEN", "").strip()
    if not token:
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production":
            # MON-FN-005: this should never happen if startup assertion ran
            logger.critical("MIXPANEL_TOKEN missing in production despite startup assertion")
            sentry_sdk.capture_message(
                "MIXPANEL_TOKEN missing post-startup",
                level="fatal",
                fingerprint=["mixpanel_init", "missing_token"],
            )
        logger.debug("MIXPANEL_TOKEN not configured — analytics events will be logged only")
        return None

    try:
        from mixpanel import Mixpanel
        _mixpanel_client = Mixpanel(token)
        logger.info("Mixpanel analytics initialized")
        return _mixpanel_client
    except ImportError as e:
        logger.critical(f"mixpanel-python package missing: {e}")
        sentry_sdk.capture_exception(e, fingerprint=["mixpanel_init", "import_error"])
        return None
    except Exception as e:
        logger.error(f"Mixpanel init failed: {e}")
        sentry_sdk.capture_exception(e, fingerprint=["mixpanel_init", "init_failed"])
        return None
```
- [ ] Counter `smartlic_mixpanel_init_failed_total{reason}` (missing_token|import_error|init_failed)
- [ ] Sentry alert em fingerprint `["mixpanel_init", *]`

### AC5: Allow-list pattern para futuras vars

Given que mais env vars vão entrar em "required production" no roadmap,
When time precisa expandir,
Then `REQUIRED_ENV_VARS_PRODUCTION` é a única source of truth.

- [ ] Adicionar candidatos comentados (não obrigatórios ainda):
```python
REQUIRED_ENV_VARS_PRODUCTION = {
    "MIXPANEL_TOKEN": "Funnel analytics (Mixpanel)",
    # "STRIPE_WEBHOOK_SECRET": "Webhook signature validation (added by MON-FN-002 expansion)",
    # "RESEND_WEBHOOK_SECRET": "Resend webhook HMAC (added by MON-FN-001 expansion)",
    # "SENTRY_DSN": "Error tracking",
    # "SUPABASE_SERVICE_ROLE_KEY": "Server-side DB access",
}
```
- [ ] Decision-log entry em `docs/decisions/` justificando "required" vs "optional"

### AC6: Test boot-time assertion

Given que tests rodam em `ENVIRONMENT=test`,
When pytest invokes lifespan,
Then assertion não dispara (skip).

- [ ] Test `backend/tests/startup/test_env_assertions.py`:
  - [ ] `assert_required_env_vars()` em `ENVIRONMENT=production` + `MIXPANEL_TOKEN` ausente → raises RuntimeError
  - [ ] `assert_required_env_vars()` em `ENVIRONMENT=development` → returns silently
  - [ ] `assert_required_env_vars()` em `ENVIRONMENT=production` + todas vars presentes → returns silently
  - [ ] Mock env via `monkeypatch.setenv("ENVIRONMENT", "production")` + `monkeypatch.delenv("MIXPANEL_TOKEN", raising=False)`
  - [ ] `assert_mixpanel_reachable()` mock `_get_mixpanel()` → None em prod → RuntimeError
- [ ] Test `backend/tests/test_health.py`:
  - [ ] `/health/ready` retorna 200 com all checks ok
  - [ ] `/health/ready` retorna 503 quando Redis down (mock `get_redis_client` raise)
  - [ ] `/health/ready` em prod sem Mixpanel → 503

### AC7: Operational runbook

- [ ] Documentar em `docs/operations/mixpanel-runbook.md`:
  - Como obter `MIXPANEL_TOKEN`: Mixpanel project > Settings > Project Token (NOT API Secret)
  - Como setar em Railway: `railway variables --service bidiq-backend set MIXPANEL_TOKEN=mp_xxx`
  - Como validar: pós-deploy, ver "backend_boot" event em Mixpanel Live View
  - Audit env vars: `railway variables --service bidiq-backend --kv | grep -i mixpanel`
  - Memory `feedback_audit_env_vars_after_incident` referenciada

---

## Scope

**IN:**
- `assert_required_env_vars()` em startup com lista P0 vars
- Eager Mixpanel init + smoke event "backend_boot"
- `/health/ready` reportando Mixpanel + DB + Redis
- Sentry capture em init failure
- Allow-list extensível
- Operational runbook

**OUT:**
- Migrar para Mixpanel server-side projects (mantém current setup)
- Multi-Mixpanel project routing (over-engineering)
- Ingestão Mixpanel via custom HTTP endpoint (não usa SDK) — fora de escopo
- Validação semântica do token (formato, validade) — Mixpanel SDK valida em runtime
- Operacionalizar STRIPE_WEBHOOK_SECRET / SENTRY_DSN como required (ficam comentados; expandido em stories futuras)

---

## Definition of Done

- [ ] `assert_required_env_vars` chamado em `lifespan` ANTES de FastAPI aceitar tráfego
- [ ] Boot fail demonstrado: `unset MIXPANEL_TOKEN && ENVIRONMENT=production python -m main` → RuntimeError
- [ ] Boot success: var setada → "Env-var assertion passed" log + "Mixpanel analytics initialized"
- [ ] Smoke event `backend_boot` visível em Mixpanel Live View pós-deploy
- [ ] `/health/ready` retorna 200 com todos checks; 503 se Mixpanel ausente em prod
- [ ] Counter `smartlic_health_check_failures_total` exposto
- [ ] Cobertura ≥85% em `assertions.py`
- [ ] CodeRabbit clean
- [ ] `MIXPANEL_TOKEN` confirmado em Railway `bidiq-backend` (e `bidiq-worker` se existir)
- [ ] Operational runbook publicado
- [ ] Memory `reference_mixpanel_backend_token_gap_2026_04_24` atualizada com "resolved by MON-FN-005"

---

## Dev Notes

### Padrões existentes a reutilizar

- **Lifespan pattern:** `backend/main.py::lifespan` (FastAPI 0.129)
- **Logger sanitizer:** `from log_sanitizer import get_sanitized_logger`
- **Sentry SDK:** `import sentry_sdk` (já em requirements)
- **Counter pattern:** `backend/metrics.py` tem dezenas de exemplos (`prometheus_client.Counter`)

### Funções afetadas

- `backend/main.py` (lifespan: chama `assert_required_env_vars` + `assert_mixpanel_reachable`)
- `backend/startup/assertions.py` (NOVO ou expansão de existente)
- `backend/analytics_events.py:19-41` (modificar `_get_mixpanel` para Sentry capture)
- `backend/routes/health.py` ou `backend/routes/health_core.py` (NOVO `/health/ready`)
- `backend/metrics.py` (counters)
- `backend/config.py` (declarar `REQUIRED_ENV_VARS_PRODUCTION` ou referenciar)

### Operacionalização da memory

Memory `feedback_audit_env_vars_after_incident` (2026-04-27) sugere:
> "PYTHONASYNCIODEBUG=1 descoberto em prod durante Stage 2; debug flags persistem despercebidos. `--kv | grep -iE \"DEBUG|DEV|TRACE\"` antes de declarar recovery"

Esta story instala o **first half** da defesa: required vars boot-fail. RES-BE-013 (story do EPIC-A) instalará o **second half**: deny-list em CI/CD para flags como `*_DEBUG=1` em prod.

### Testing Standards

- Unit tests em `backend/tests/startup/test_env_assertions.py`
- Mock env via `monkeypatch` (pytest fixture)
- Não inicializar real Mixpanel em test (`@patch("analytics_events._get_mixpanel")`)
- Cobertura: `pytest --cov=backend/startup/assertions.py --cov-report=term`
- Anti-hang: pytest-timeout 30s default; assertion functions são síncronas
- E2E: pode ser smoke test em CI (`ENVIRONMENT=production python -c "from main import app"`)

---

## Risk & Rollback

### Triggers de rollback
- Deploy falha boot (provável: var faltando em outro env Railway service ou typo)
- Healthcheck `/ready` flapping (DB/Redis transient → 503 cascading)
- False positive Sentry alerts em init (race condition em lazy init)

### Ações de rollback
1. **Imediato:** revert PR; Railway redeploy versão anterior
2. **Override:** env var `BYPASS_REQUIRED_ENV_ASSERTIONS=true` (escape hatch documentado mas auditado em logs CRITICAL)
3. **Healthcheck-only revert:** voltar `/health` simples sem dep checks; manter assertion (assertion é mais importante que healthcheck)
4. **Comunicação:** Sentry release tag deveria ter capturado boot failures — investigar antes de re-deploy

### Compliance
- Token Mixpanel é segredo — nunca logar valor, apenas presença/ausência
- LGPD: nada a fazer (env vars não são PII)

---

## Dependencies

### Entrada
- Mixpanel project criado (já existe — `confenge` workspace)
- Railway service `bidiq-backend` ativo
- Sentry SDK em requirements (`sentry-sdk[fastapi]`)

### Saída
- **MON-FN-006** (eventos funil): depende de Mixpanel garantidamente disponível em prod
- **MON-FN-014** (onboarding tracking): mesmo
- **RES-BE-013** (CI gate env vars): complementa esta story (audit pre-deploy)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | OK | Notes |
|---|---|---|---|
| 1 | Clear and objective title | Y | "MIXPANEL_TOKEN Startup Assertion (Boot Fail Se Ausente)" — comportamento explícito |
| 2 | Complete description | Y | Cita memory gap + linhas analytics_events.py:26-30 + "fire-and-forget" trade-off |
| 3 | Testable acceptance criteria | Y | 7 ACs incluindo dev mode skip + healthcheck 503 + Sentry capture |
| 4 | Well-defined scope (IN/OUT) | Y | IN/OUT explícitos; OUT distingue "Mixpanel only este sprint" vs futuras vars |
| 5 | Dependencies mapped | Y | Entrada Mixpanel project + Railway service; Saída MON-FN-006/014 |
| 6 | Complexity estimate | Y | S (0.5-1 dia) coerente — assertion + healthcheck + tests |
| 7 | Business value | Y | "Cegueira analytics destrói qualquer tentativa de medir funil" |
| 8 | Risks documented | Y | Boot fail trigger + escape hatch `BYPASS_REQUIRED_ENV_ASSERTIONS` documentado |
| 9 | Criteria of Done | Y | Boot fail demonstrado + smoke event "backend_boot" Mixpanel Live View |
| 10 | Alignment with PRD/Epic | Y | EPIC gap #5 + memória `feedback_audit_env_vars_after_incident` operacionalizada |

### Observations
- Pattern allow-list extensível (`REQUIRED_ENV_VARS_PRODUCTION`) é reutilizável para futuras stories
- Healthcheck `/health/ready` separado de `/health/live` é Kubernetes-style correct
- Concern de "boot fail em prod = comportamento crítico" endereçada: rollback via `BYPASS_REQUIRED_ENV_ASSERTIONS=true` documentado + Sentry release tag
- Sentry capture com fingerprint `["mixpanel_init", failure_type]` previne spam
- Memory update mandatory documentada em DoD

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — operacionaliza memory MIXPANEL_TOKEN gap | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). P0 instrumentação foundation; Status Draft → Ready. | @po (Pax) |
