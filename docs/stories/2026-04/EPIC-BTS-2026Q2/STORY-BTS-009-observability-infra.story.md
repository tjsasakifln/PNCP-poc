# STORY-BTS-009 — Observability & Infra Drift (20 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P2
**Effort:** S (2-3h) — mostly assertion-drift
**Agents:** @dev + @qa
**Status:** Ready

---

## Contexto

20 testes cobrindo infra (GTM-INFRA-001, GTM-INFRA-002, GTM-CRITICAL-SCENARIOS), observabilidade (logs, audit, cron monitoring, prometheus, openapi, schema validation), e error handling. Maioria deve ser assertion-drift sobre valores de config mudados (ex: GUNICORN_TIMEOUT 120→110 já foi fixado parcialmente em PR #392).

---

## Arquivos (tests)

- `backend/tests/test_gtm_infra_001.py` (4 failures) — parciais já fixados em PR #392; remaining 4 são diferentes
- `backend/tests/test_gtm_infra_002.py` (1 failure)
- `backend/tests/test_gtm_critical_scenarios.py` (2 failures)
- `backend/tests/test_gtm_fix_041_042.py` (3 failures)
- `backend/tests/test_gtm_fix_027_track2.py` (1 failure)
- `backend/tests/test_log_volume.py` (6 failures)
- `backend/tests/test_audit.py` (1 failure)
- `backend/tests/test_cron_monitoring.py` (1 failure)
- `backend/tests/test_prometheus_labels.py` (1 failure)
- `backend/tests/test_openapi_schema.py` (1 failure)
- `backend/tests/test_schema_validation.py` (1 failure)
- `backend/tests/test_error_handler.py` (1 failure)

---

## Acceptance Criteria

- [ ] AC1: `pytest` nos 12 arquivos retorna exit code 0 (20/20 PASS).
- [ ] AC2: CI verde.
- [ ] AC3: RCA distinguindo (a) config value drift vs (b) observability output shape drift vs (c) openapi schema drift.
- [ ] AC4: Cobertura não caiu.
- [ ] AC5: zero quarantine.

---

## Investigation Checklist

- [ ] Para `test_openapi_schema`: re-gerar schema via `pytest --openapi` se utility existe + commit drift
- [ ] Para `test_gtm_infra_001` remainders (4 ainda falham após PR #392): sync fallback não blocking, CB prometheus metric, time.sleep grep
- [ ] Para `test_log_volume`: verificar se patterns de log mudaram

---

## Dependências

- **Bloqueado por:** nenhum (paralelo)
- **Bloqueia:** nenhum

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready.
