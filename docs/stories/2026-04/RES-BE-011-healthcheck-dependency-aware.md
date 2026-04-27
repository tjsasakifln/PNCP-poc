# RES-BE-011: Healthcheck Dependency-Aware — `/health/live` + `/health/ready`

**Priority:** P0
**Effort:** S (1 dia)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 1 (2026-04-29 → 2026-05-05)
**Dependências bloqueadoras:** Nenhuma (foundation)

---

## Contexto

`backend/routes/health.py` retorna **200 OK incondicionalmente** — mesmo quando Supabase ou Redis estão indisponíveis. Durante o P0 de 2026-04-27, Railway continuou roteando tráfego para o worker wedged porque healthcheck respondia 200 enquanto Supabase queries enfileiravam indefinidamente. Healthcheck saudável + worker doente = traffic loss invisível.

Padrão Kubernetes/Railway: dois endpoints distintos:

- **`/health/live`** — *liveness probe*: processo está rodando? Sempre 200 se Python/uvicorn responde. **Não** verifica dependências. Usado para reiniciar container se travar.
- **`/health/ready`** — *readiness probe*: processo pode atender requests? Verifica Redis (ping) + Supabase (lightweight query) com timeout <1s. Retorna 503 se qualquer dependência falha. Railway desconecta serviço do load balancer quando 503.

Esta story é P0 effort S — mudança cirúrgica em 1 arquivo + atualização Railway healthcheck path. Imprescindível Sprint 1 para prevenir reincidência: se P0 reincide, Railway deve isolar instância automaticamente.

---

## Acceptance Criteria

### AC1: Endpoint `/health/live`

- [ ] Em `backend/routes/health.py`, criar:
  ```python
  @router.get("/health/live", include_in_schema=False)
  async def liveness():
      """Liveness probe: returns 200 if process is alive. No dependency checks."""
      return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
  ```
- [ ] Sem auth (público — Railway probe)
- [ ] Sem `_run_with_budget` (deve responder em <10ms)
- [ ] Response model documentado com Pydantic mas `include_in_schema=False` (não polui OpenAPI)

### AC2: Endpoint `/health/ready`

- [ ] Em `backend/routes/health.py`:
  ```python
  @router.get("/health/ready", include_in_schema=False)
  async def readiness(response: Response):
      """Readiness probe: 200 if all critical deps respond <1s, 503 otherwise."""
      checks = await asyncio.gather(
          _check_redis(),
          _check_supabase(),
          return_exceptions=True,
      )
      results = {
          "redis": "ok" if not isinstance(checks[0], Exception) else f"fail: {checks[0]}",
          "supabase": "ok" if not isinstance(checks[1], Exception) else f"fail: {checks[1]}",
      }
      all_ok = all(v == "ok" for v in results.values())
      if not all_ok:
          response.status_code = 503
      return {"status": "ready" if all_ok else "not_ready", "checks": results}
  ```
- [ ] Helpers:
  ```python
  async def _check_redis():
      try:
          redis = await get_redis()
          await asyncio.wait_for(redis.ping(), timeout=1.0)
      except Exception as e:
          raise RuntimeError(f"redis: {e}")

  async def _check_supabase():
      try:
          await asyncio.wait_for(
              asyncio.to_thread(lambda: supabase.from_("health_check").select("1").limit(1).execute()),
              timeout=1.0,
          )
      except Exception as e:
          raise RuntimeError(f"supabase: {e}")
  ```
- [ ] **Atenção:** tabela `health_check` existe? Se não, usar tabela leve existente (e.g. `profiles LIMIT 1`) ou criar via migration mínima. **TODO @data-engineer:** decidir.

### AC3: Endpoint `/health` legado mantido

- [ ] **NÃO remover** `/health` existente — pode haver consumidores externos
- [ ] `/health` retorna estrutura combinada: `{"status": "ok", "live": <live_response>, "ready": <ready_response>}`
- [ ] Marcar com `# TODO: deprecate after Q3 2026` em comentário
- [ ] Documentar deprecation em `CHANGELOG.md`

### AC4: Atualizar configuração Railway

- [ ] `backend/railway.toml` ou `Dockerfile` — atualizar healthcheck:
  ```toml
  [deploy]
  healthcheckPath = "/health/ready"
  healthcheckTimeout = 5
  ```
- [ ] Documentar mudança em `docs/runbooks/healthcheck.md`
- [ ] Antes do deploy: testar manualmente `/health/ready` retorna 200 com Supabase normal

### AC5: Métricas Prometheus

- [ ] Em `backend/metrics.py`:
  ```python
  HEALTHCHECK_DEPENDENCY_STATUS = Gauge(
      "smartlic_healthcheck_dependency_status",
      "1 if dependency is reachable, 0 otherwise",
      ["dependency"],
  )
  HEALTHCHECK_DEPENDENCY_LATENCY_SECONDS = Histogram(
      "smartlic_healthcheck_dependency_latency_seconds",
      "Latency of healthcheck dependency probe",
      ["dependency"],
      buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
  )
  ```
- [ ] `_check_redis` e `_check_supabase` atualizam gauge + histogram
- [ ] Sentry warning se gauge=0 por mais de 5min consecutivos

### AC6: Testes

- [ ] **Unit tests:** `backend/tests/routes/test_health.py`
  - `/health/live` sempre 200
  - `/health/ready` 200 quando Redis+Supabase respondem (mock)
  - `/health/ready` 503 quando Redis falha
  - `/health/ready` 503 quando Supabase falha
  - `/health/ready` 503 quando ambos falham
  - Response inclui detalhes de cada check
  - Cobertura ≥85%
- [ ] **Integration test:** smoke test contra Redis+Supabase real em staging
  - Hit `/health/live` → 200 em <50ms
  - Hit `/health/ready` → 200 em <1.5s (com folga)
- [ ] **E2E test (post-deploy):** Railway healthcheck path responde 200 em prod

---

## Scope

**IN:**
- Endpoint `/health/live`
- Endpoint `/health/ready` com checks Redis + Supabase
- Manter `/health` legado (deprecation futura)
- Atualizar Railway config para usar `/health/ready`
- Métricas Prometheus
- Testes unit + integration + E2E
- Runbook

**OUT:**
- Checks de dependências adicionais (Sentry, Mixpanel, OpenAI) — escopo futuro se valor justificar
- Healthcheck WebSocket — fora de escopo
- Custom Kubernetes-style status page — over-engineering MVP
- Dashboard de uptime histórica — escopo separado
- Remover `/health` legado — Q3+ deprecation

---

## Definition of Done

- [ ] `/health/live` e `/health/ready` implementados
- [ ] `/health` legado mantido com deprecation note
- [ ] Railway config atualizada para `/health/ready`
- [ ] Métricas Prometheus funcionais
- [ ] Cobertura testes ≥85%
- [ ] Sem regressão (5131+ passing)
- [ ] Deploy staging: Railway healthcheck verde por 24h
- [ ] CodeRabbit clean
- [ ] PR review por @architect (Aria) e @qa (Quinn) com verdict PASS
- [ ] Runbook `docs/runbooks/healthcheck.md` criado
- [ ] CLAUDE.md "Critical Implementation Notes" atualizado
- [ ] CHANGELOG.md menciona deprecation `/health`

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/routes/health.py` (modificar — adicionar live/ready)
- `/mnt/d/pncp-poc/backend/redis_client.py` (existente — usar `get_redis()`)
- `/mnt/d/pncp-poc/backend/database.py` (existente — usar `supabase` client)
- `/mnt/d/pncp-poc/backend/metrics.py` (adicionar gauge + histogram)
- `/mnt/d/pncp-poc/backend/railway.toml` (modificar — `healthcheckPath`)
- `/mnt/d/pncp-poc/backend/tests/routes/test_health.py` (modificar/criar)
- `/mnt/d/pncp-poc/docs/runbooks/healthcheck.md` (novo)
- `/mnt/d/pncp-poc/CHANGELOG.md` (atualizar)

### Padrão referência

- Kubernetes liveness/readiness: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- Railway healthcheck docs: https://docs.railway.app/reference/healthchecks
- `backend/health.py` existente já tem PNCP canary (RES-BE-XXX previous) — coordenar

### Frameworks de teste

- pytest 8.x + httpx + pytest-asyncio
- File location: `backend/tests/routes/test_health.py`
- Marks: `@pytest.mark.timeout(10)`
- Fixtures: `monkeypatch` para mock Redis ping e Supabase query

### Convenções

- `include_in_schema=False` em endpoints de health (não documentar em OpenAPI público)
- Response model Pydantic para type-safety
- Latência de probe deve ser <1s — se exceder, é bug ou DB lento (sinal real)
- Logger: `logger.warning` apenas em falha (não logar 200 cada probe — Railway hits a cada 30s)

### Detalhe Railway

Railway envia healthcheck a cada ~30s (configurable). Se 3 falhas consecutivas, marca instância como unhealthy e roteia tráfego para outra (ou re-deploy). Em ambiente single-instance hobby, instância vira 503 user-facing — desejável vs wedge silencioso.

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| `/health/ready` falha esporadicamente em prod (Redis/Supabase blip) | Aceitar — é o ponto: instância marca 503 brevemente; Railway retry |
| Railway re-deploy loop (3 falhas consecutivas → restart) | Investigar dependência crítica; aumentar timeout do probe se latência legítima >1s; revert healthcheck path se loop persistente |
| Tabela `health_check` não existe e fix improvisado quebra | Usar `profiles LIMIT 1` ou criar migration trivial: `CREATE TABLE health_check (id int PRIMARY KEY DEFAULT 1)` |
| Métrica gauge fica 0 por bug em probe (não Redis/Supabase real) | Verificar via Sentry; rollback PR se persistente |
| `/health` legado consumidores externos quebram | Manter retorno backward-compatible (campo `status: "ok"` no top level) |

**Rollback completo:** revert PR + restaurar Railway `healthcheckPath = "/health"` (legado).

---

## Dependencies

**Entrada:** Nenhuma — foundation. `backend/redis_client.py`, `backend/database.py` já existem.

**Saída:** Habilita Railway a isolar instância wedged automaticamente. Pré-requisito para multi-instance scaling futuro (não escopo agora).

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 9/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | "/health/live + /health/ready" pattern Kubernetes/Railway nomeado. |
| 2 | Complete description | ✓ | Liga incidente P0 → Railway 200 mascarando wedge → padrão dois endpoints. |
| 3 | Testable acceptance criteria | ✓ | 6 ACs com 6 casos unit + integration + E2E pós-deploy. |
| 4 | Well-defined scope | ✓ | IN/OUT delimitados; legado `/health` mantido (deprecation Q3+). |
| 5 | Dependencies mapped | ✓ | Foundation (sem entrada); saída habilita Railway isolar instância wedged. |
| 6 | Complexity estimate | ✓ | S (1 dia) coerente — 1 arquivo + Railway config + métricas + tests. |
| 7 | Business value | ✓ | "Se P0 reincide, Railway isola instância automaticamente" — tradução operacional clara. |
| 8 | Risks documented | ✓ | 5 riscos incluindo Railway re-deploy loop e fallback `profiles LIMIT 1`; rollback path explícito. |
| 9 | Criteria of Done | ✗ | TODO @data-engineer em AC2 sobre tabela leve para `_check_supabase` probe — não bloqueia (fallback documentado em Risk), mas DoD não menciona explicitamente "decisão de tabela registrada antes de Phase 3". |
| 10 | Alignment with PRD/Epic | ✓ | Sprint 1 P0 anti-reincidência conforme EPIC sequenciamento. |

### Required Fixes (não bloqueia Ready, mas resolver no Phase 3)

- [ ] **@data-engineer (Dara)** decidir entre opções para `_check_supabase` probe ANTES de @dev iniciar implementação:
  - (a) usar tabela leve existente como `profiles LIMIT 1` (zero migration);
  - (b) criar migration trivial `CREATE TABLE health_check (id int PRIMARY KEY DEFAULT 1)` (overhead +1 migration mas isolamento clean);
  - (c) usar Postgres `SELECT 1` direto (não envolve nenhuma tabela; mais leve).
- Decisão registrada via comentário no PR + atualização AC2 da story (in-place pelo @architect/@dev se @po não estiver disponível).

### Observations

- Pattern Kubernetes liveness/readiness é canônico — adoção alinhada com indústria.
- AC3 mantém `/health` legado backward-compatible — boa prática (consumidores externos não quebram).
- Métricas gauge (1/0 por dependência) + histogram de latência cobrem ambos status e perf.
- Effort S apropriado para Sprint 1 P0.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — separação live/ready healthcheck | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (9/10). Required fix: @data-engineer decidir tabela para probe Supabase antes de Phase 3. Status: Draft → Ready. | @po (Pax) |
