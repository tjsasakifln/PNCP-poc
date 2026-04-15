# STORY-4.4: Railway 120s Time Budgets Audit + Tuning (TD-SYS-003)

**Priority:** P1 (Railway hard timeout sub-utilizado)
**Effort:** S (8-16h)
**Squad:** @architect + @dev + @devops
**Status:** InReview
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 3

---

## Story

**As a** SmartLic,
**I want** time budgets stage-wise alinhados com Railway 120s hard timeout,
**so that** requests >120s sejam evitados ou degradem graciosamente.

---

## Acceptance Criteria

### AC1: Audit timeouts

- [x] Documentar todos timeouts atuais + novos valores em CLAUDE.md waterfall ASCII
- [x] Identificar + corrigir inconsistência `source_config/sources.py` (300/180) vs `config/pncp.py` (100/80)

### AC2: Reduce + align

- [x] Pipeline timeout: 110s → **100s** (margin de 20s antes Railway kill)
- [x] Consolidation: 100s → **90s**
- [x] PerSource: 80s → **70s**
- [x] PerUF: 30s → **25s** (degraded 15→12)
- [x] CONSOLIDATION_TIMEOUT_GLOBAL / PER_SOURCE em `source_config/sources.py` sincronizados (90/70)

### AC3: Graceful degradation + métricas

- [x] `backend/pipeline/budget.py::_run_with_budget` wraps ``asyncio.wait_for`` e emite Prometheus counter
- [x] Aplicado em `pipeline/stages/execute.py:612` (consolidation) e `:1079` (direct fetch)
- [x] `fallback=None` preserva as recovery paths existentes (TimeoutError propaga para blocks de cache cascata / PNCPDegradedError)
- [x] Métricas: `smartlic_pipeline_budget_exceeded_total{phase,source}` + `smartlic_pipeline_duration_seconds` histogram

### AC4: Documentation

- [x] CLAUDE.md "Railway/Gunicorn Critical Notes" atualizado com waterfall + query Prometheus + emergência override via env

---

## Tasks / Subtasks

- [x] Task 1: Audit (AC1)
- [x] Task 2: Adjust configs (AC2)
- [x] Task 3: Graceful degradation logic (AC3)
- [x] Task 4: Métricas Prometheus
- [x] Task 5: Docs (AC4)

## Dev Notes

- Approach não-destrutivo: wrapper com `fallback=None` mantém 100% do comportamento de recovery existente. Apenas adiciona métrica observável.
- Env vars continuam como override em produção — deploy Railway pode reverter valores sem rebuild.
- Invariante descendente testada em `test_default_timeout_invariant_holds`: pipeline > consolidation > per_source > per_uf > per_modality.
- Sincronização `source_config/sources.ConsolidationConfig.from_env` com `config/pncp.py` elimina divergência dupla (300/180 vs 100/80) identificada na auditoria.

## File List

### Created

- `backend/pipeline/budget.py` — `_run_with_budget` wrapper (timeout + Prometheus)
- `backend/tests/test_timeout_invariants.py` — 6 tests (invariante + wrapper)

### Modified

- `backend/config/pncp.py` — reduced `PIPELINE_TIMEOUT`, `CONSOLIDATION_TIMEOUT`, `PNCP_TIMEOUT_PER_SOURCE`, `PNCP_TIMEOUT_PER_UF`, `PNCP_TIMEOUT_PER_UF_DEGRADED`
- `backend/source_config/sources.py` — `ConsolidationConfig.from_env` defaults mirrored
- `backend/metrics.py` — added `PIPELINE_BUDGET_EXCEEDED_TOTAL`, `PIPELINE_DURATION_SECONDS`
- `backend/pipeline/stages/execute.py` — 2 call sites (consolidation, direct fetch) through wrapper
- `CLAUDE.md` — waterfall diagram + Prometheus queries + emergency overrides

## Testing

- 6 tests em `test_timeout_invariants.py` — 6/6 passing
- Regression check: `test_stab004_never_lose_data.py` (11 tests) + `test_story416_ac4_graceful_degradation.py` (6 tests) — todos passam (recovery paths preservados)
- Load test comparison (STORY-3.3) pode ser executado pós-merge para medir %>100s reduce

## Definition of Done

- [x] Timeouts aligned + degradation tested + docs

## Risks

- **R1**: Reduce demais → user gets partial sempre — mitigation: `smartlic_pipeline_budget_exceeded_total{phase="pipeline"} rate > 0` alerta ops; env override disponível ✅

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-15 | 2.0     | Implementation complete: budget wrapper + reduced timeouts + sync divergência + 6 tests + CLAUDE.md waterfall | @dev |
