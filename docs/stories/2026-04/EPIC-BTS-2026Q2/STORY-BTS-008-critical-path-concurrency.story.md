# STORY-BTS-008 — Critical Path & Concurrency (18 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P1 (critical-path = alta severidade, bugs aqui são P0 em produção)
**Effort:** M (3-5h)
**Agents:** @dev + @qa + @architect (race conditions podem revelar prod bugs)
**Status:** Ready

---

## Contexto

18 testes cobrindo crises documentadas (CRIT-046 pool exhaustion, CRIT-057 filter time budget, CRIT-050 pipeline hardening, CRIT-004 correlation), concurrency safety (optimistic locking em pipeline + quota atomicity), revalidation, e job queue. Qualquer flakiness aqui é dívida técnica de alto risco.

**Importante:** este grupo pode revelar prod bugs reais (não só mock-drift). Se teste captura race condition em produção, story escala para @architect e @po.

---

## Arquivos (tests)

- `backend/tests/test_crit046_pool_exhaustion.py` (3 failures)
- `backend/tests/test_crit057_filter_time_budget.py` (4 failures)
- `backend/tests/test_crit050_pipeline_hardening.py` (1 failure)
- `backend/tests/test_crit004_correlation.py` (4 failures) — webhook 403s + quota delegation (sobrepõe STORY-CIG-BE-story-drift-billing-webhooks-correlation)
- `backend/tests/test_concurrency_safety.py` (2 failures)
- `backend/tests/test_revalidation_quota_cache.py` (1 failure)
- `backend/tests/test_job_queue.py` (4 failures)

---

## Acceptance Criteria

- [ ] AC1: `pytest` nos 7 arquivos retorna exit code 0 (18/18 PASS) localmente.
- [ ] AC2: CI `backend-tests.yml` verde nos 7.
- [ ] AC3: RCA detalhada, distinguindo mock-drift de prod bug. Para cada prod bug identificado: abrir issue separada + escalar.
- [ ] AC4: Cobertura não caiu.
- [ ] AC5: zero quarantine.

---

## Investigation Checklist

- [ ] `test_crit004_correlation`: validar webhook signature mock + `check_and_increment_quota_atomic` path
- [ ] `test_crit046_pool_exhaustion`: httpx pool limits em `backend/clients/` configs
- [ ] `test_crit057_filter_time_budget`: batch budget guard em `backend/filter/pipeline.py`
- [ ] `test_concurrency_safety`: optimistic locking em `backend/routes/pipeline.py`, `quota.check_and_increment_quota_atomic`
- [ ] `test_job_queue`: ARQ conftest `_isolate_arq_module` fixture ainda funciona?

---

## Dependências

- **Bloqueado por:** BTS-001 (quota atomicity)
- **Relacionado:** `STORY-CIG-BE-story-drift-billing-webhooks-correlation` (CRIT-004 overlap)

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready. Prod-bug risk flagged.
