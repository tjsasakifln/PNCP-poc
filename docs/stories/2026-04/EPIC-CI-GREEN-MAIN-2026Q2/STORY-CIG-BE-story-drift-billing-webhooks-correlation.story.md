# STORY-CIG-BE-story-drift-billing-webhooks-correlation — Webhook/auth 403s + quota delegation não invocado — 4 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
**Priority:** P1 — Gate (auth/webhook = superfície crítica)
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Duas suítes `test_crit004_correlation.py` e `test_organizations.py` rodam em `backend-tests.yml` e falham em **4 testes** do triage row #29/30. Causa raiz classificada como **mock-drift**:

1. **Webhook/auth 403s**: Stripe webhook handlers recebem 403 (autorização falha). Possível drift em `webhooks/stripe.py` signature verification mock.
2. **Quota delegation não invocado**: CRIT-004 (correlação de IDs) esperava delegação para `check_and_increment_quota_atomic` mas o mock não captura a call.

**Arquivos principais afetados:**
- `backend/tests/test_crit004_correlation.py`
- `backend/tests/test_organizations.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Refactor recente em `webhooks/handlers/` (relacionado a STORY #28) ou em `authorization.py` mudou superfície. Validar com `grep -rn "verify_webhook_signature\\|check_and_increment_quota_atomic" backend/`.

---

## Acceptance Criteria

- [x] AC1: `pytest backend/tests/test_crit004_correlation.py backend/tests/test_organizations.py -v` retorna exit code 0 localmente. **Ajuste em Implement:** triage row #29/30 reportava 4 testes; reprodução local encontrou **7 testes falhando** (4 sub-drifts distintos — ver RCA). Resultado final: **54/54 PASS**.
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log.
- [x] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift). **4 sub-drifts distintos** identificados (não 2 como hipotetizado): (a) `config` virou package → `inspect.getsource(config)` perde format string; (b) rota `/v1/admin/search-trace/{id}` agora usa `require_admin` (não `require_auth`); (c) `quota.py` virou package → facade patch não intercepta chamada interna; (d) helper chain de `llm_summary_job` (`_ground_truth_summary` + `recompute_temporal_alerts`) assume atributos string/list em `resumo`, incompatível com MagicMock cru. **Webhooks/Stripe não foram afetados** — hipótese inicial de "webhook auth 403" era na verdade admin auth drift.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [x] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados. CLAUDE.md invariante: tests mockando `/buscar` devem mockar `check_and_increment_quota_atomic` — **não aplicável** a estes testes (nenhum toca `/buscar`); a invariante foi respeitada no patch de `quota.quota_atomic.check_and_increment_quota_atomic`.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 2 suítes isoladas.
- [ ] `grep -rn "verify_webhook_signature\\|check_and_increment_quota_atomic" backend/`.
- [ ] Validar que Stripe webhook signature verification continua ativa em produção.
- [ ] Coordenar com STORY-CIG-BE-pgrst205-http503-contract (#18) se `test_organizations.py` overlap — evitar duplicação de fix.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #29/30)

## Stories relacionadas no epic

- STORY-CIG-BE-pgrst205-http503-contract (#18 — também toca `test_organizations.py`)
- STORY-CIG-BE-asyncio-run-production-scan (#28 — `webhooks/handlers/__init__.py` impactado)

---

## Root Cause Analysis

Reprodução local mostrou **7 testes falhando** (não 4) — 4 sub-drifts distintos, todos mock-drift de patch-path após refactors de packaging e mudança de dependency:

### Sub-drift (a) — `config` package refactor quebra `inspect.getsource`

- **Testes:** `TestLogFormatConfiguration::test_log_format_has_{search,correlation}_id`
- **Sintoma:** `assert "search_id" in source` falha — o assert vê apenas o `__init__.py` do pacote (pure re-export), não a format string.
- **Causa:** DEBT-015 SYS-012 decomposição de `config.py` → package `config/` com `base.py`, `pncp.py`, `features.py`, `cors.py`, `pipeline.py`. O format string `setup_logging(fmt="... %(search_id)s %(correlation_id)s ...")` ficou em `config/base.py` (linha 49/59).
- **Fix:** `inspect.getsource(config.base)` em vez de `inspect.getsource(config)`.

### Sub-drift (b) — admin auth dep mudou: `require_auth` → `require_admin`

- **Testes:** `TestAdminTraceEndpoint::test_trace_endpoint_returns_structure`, `..._with_active_tracker`, `..._with_completed_jobs` (3 testes retornando 403)
- **Sintoma:** `assert 403 == 200` — override de `require_auth` não é invocado.
- **Causa:** `routes/admin_trace.py::get_search_trace` agora depende de `require_admin` (admin.py), que internamente depende de `require_auth`. Override em `require_auth` não alcança o gate de `is_admin`.
- **Fix:** `app.dependency_overrides[require_admin] = lambda: {...}` (padrão consistente com `test_admin_cron.py`, `test_admin_cache.py`, etc). `test_trace_endpoint_requires_auth` também atualizado para remover o override de `require_admin`.

### Sub-drift (c) — `quota` package refactor quebra facade-patch de delegação

- **Teste:** `TestOrgLevelQuotaIsolation::test_check_and_increment_org_quota_delegates_to_atomic`
- **Sintoma:** `mock_fn.assert_called_once_with("org-abc", 5000)` → "Called 0 times" (a função real rodou e retornou 22P02 UUID error).
- **Causa:** TD-007 decompôs `quota.py` em `quota/quota_core.py`, `quota/quota_atomic.py`, `quota/plan_enforcement.py`, `quota/plan_auth.py`, `quota/session_tracker.py`. O `quota/__init__.py` re-exporta tudo como facade, mas `check_and_increment_org_quota_atomic` (definida em `quota/quota_atomic.py`) chama `check_and_increment_quota_atomic` via nome module-local dentro do mesmo arquivo. Patch em `quota.check_and_…` (facade) não intercepta a referência local do caller.
- **Fix:** `patch("quota.quota_atomic.check_and_increment_quota_atomic", ...)`. Preserva CLAUDE.md invariant de mockar o helper atomic.

### Sub-drift (d) — `llm_summary_job` helper chain quebra sob MagicMock cru

- **Teste:** `TestJobQueueCorrelation::test_llm_job_accepts_kwargs`
- **Sintoma:** `TypeError: expected string or bytes-like object, got 'MagicMock'` em `re.sub(..., resumo.resumo_executivo)`.
- **Causa:** `jobs/queue/jobs.py::llm_summary_job` chama, **após** `gerar_resumo`, dois helpers novos (provável refactor pós-story criação): `_ground_truth_summary(resumo)` (regex em `resumo.resumo_executivo`) e `recompute_temporal_alerts(resumo, licitacoes)` (iteração em `resumo.destaques`). Ambos assumem atributos string/list no `resumo` — o MagicMock devolvido por `patch("llm.gerar_resumo", return_value=mock_resumo)` tinha `resumo_executivo` como sub-MagicMock, quebrando o `re.sub`.
- **Fix:** `mock_resumo.resumo_executivo = ""` (falsy → early-return em `_ground_truth_summary`) e `mock_resumo.destaques = []` (list filter noop em `recompute_temporal_alerts`). Patch continua em `llm.gerar_resumo` (correto — deferred import lê atributo do módulo no call-site).

### Escopo de "webhooks/stripe"

A hipótese inicial da story (webhook Stripe signature verification mockada errada) **não foi confirmada**: nenhum teste desta suíte exercita webhook handlers. O label "webhooks" veio do nome do endpoint `/v1/admin/search-trace/` interpretado como superfície admin crítica — e a fix de `require_admin` cobre esse vetor. Caso o PR #383 triage tenha classificado algum teste de webhook aqui equivocadamente, ele já passa neste run (47 testes não-relacionados continuam green).

---

## File List

**Modified (test files only — ZERO prod changes):**
- `backend/tests/test_crit004_correlation.py` (6 testes fixed: 3 admin auth + 2 log format + 1 llm job helper chain)
- `backend/tests/test_organizations.py` (1 teste fixed: quota submodule patch path)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #29/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. Dois sub-drifts (webhook auth 403 + quota delegation) — RCA deve separá-los; coordenar com #18 se overlap em `test_organizations.py`.
- **2026-04-18** — @dev: Implementado. Reprodução local encontrou **7 falhas** (não 4) desdobradas em **4 sub-drifts** (RCA acima). Fix aplicado apenas em test files (zero prod changes); patch paths atualizados para: `config.base` (log format), `require_admin` via `admin.py` (admin trace), `quota.quota_atomic.check_and_increment_quota_atomic` (delegation), e shaping do mock resumo (`resumo_executivo=""`, `destaques=[]`). Resultado: `pytest tests/test_crit004_correlation.py tests/test_organizations.py` → **54 passed, 0 failed, 0 errors** (23.40s). Guard de skip/xfail/only → vazio. Status Ready → InReview.
