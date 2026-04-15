# STORY-4.5: PNCP API Breaking Change Detection Alert (TD-SYS-002)

**Priority:** P1 (recurring risk — PNCP changed page size silently in Feb 2026)
**Effort:** XS (4h)
**Squad:** @dev + @qa
**Status:** InReview
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 3

---

## Story

**As a** SmartLic,
**I want** alert se PNCP API rejeita `tamanhoPagina` >50 ou response shape muda,
**so that** descobrimos breaking changes em horas (não dias).

---

## Acceptance Criteria

### AC1: Health canary com tamanhoPagina=51

- [x] `backend/pncp_canary.py` tenta `tamanhoPagina=51` a cada 10 min
- [x] Se HTTP 200 → captura como métrica `smartlic_pncp_max_page_size_changed_total`
- [x] `backend/health.py` refatorado para delegar a `validate_page_size_limit` (zero duplicação)

### AC2: Sentry alert

- [x] Se canary falha por 3 runs consecutivos → Sentry level=fatal
- [x] Tags: `pncp_breaking_change` (reason), `source=pncp`
- [x] Fingerprint `["pncp_canary", reason]` para dedup

### AC3: Response shape canary

- [x] Compara resposta atual vs schema cached (`backend/contracts/schemas/pncp_search_response.schema.json`)
- [x] Diff alerta imediatamente se shape change (não espera 3x)
- [x] Métrica `smartlic_pncp_canary_shape_drift_total`

### AC4: Documentation

- [x] CLAUDE.md "PNCP API" section atualizado com canary + alert process

---

## Tasks / Subtasks

- [x] Task 1: Implementar canary (AC1)
- [x] Task 2: Sentry integration (AC2)
- [x] Task 3: Schema diff (AC3)
- [x] Task 4: Schedule cron (10min interval)
- [x] Task 5: Docs (AC4)

## Dev Notes

- Resolve a lacuna identificada na Phase 1: "Health canary uses tamanhoPagina=10 — doesn't detect page size limits"
- Overlap com STORY-3.4 (contract tests) mas mais granular/frequente (10min vs weekly)
- Redis-backed consecutive failure counter com TTL de 1h (auto-reset se worker cair)
- Sentry dedup via Redis flag (TTL 6h) — operador recebe 1 alerta, não 36/dia
- Schema reuse: copiou-se `pncp_search_response.schema.json` de `tests/contracts/schemas/` para `backend/contracts/schemas/` (runtime path, não envolve test tree)
- `validate_page_size_limit` é entrypoint leve para health.py (sem Redis/Sentry overhead)

## File List

### Created

- `backend/pncp_canary.py` — canary module (probes A+B, Redis state, Sentry escalation)
- `backend/jobs/cron/pncp_canary.py` — ARQ cron task loop (10min interval)
- `backend/contracts/schemas/pncp_search_response.schema.json` — runtime-shipped schema (copied from tests/contracts/schemas/)
- `backend/tests/test_pncp_canary.py` — 6 tests (probe A, 3x gate, reset, shape drift, dedup, scheduler)

### Modified

- `backend/jobs/cron/scheduler.py` — registers `start_pncp_canary_task`
- `backend/config/pncp.py` — adds `PNCP_CANARY_INTERVAL_S`, `PNCP_CANARY_FAIL_THRESHOLD`
- `backend/config/__init__.py` — re-exports
- `backend/metrics.py` — adds `PNCP_MAX_PAGE_SIZE_CHANGED`, `PNCP_CANARY_CONSECUTIVE_FAILURES`, `PNCP_CANARY_SHAPE_DRIFT`
- `backend/health.py:140-213` — delegates page-size probe to `validate_page_size_limit`
- `CLAUDE.md` — PNCP API section with canary notes

## Testing

- 6 unit tests em `backend/tests/test_pncp_canary.py` — 6/6 passing
- Scheduler smoke: `register_all_cron_tasks()` inclui `start_pncp_canary_task` (21 tasks total)
- Graceful degradation: Redis ausente → canary roda sem state persistence; Sentry ausente → silent no-op

## Definition of Done

- [x] Canary running + alert tested + docs

## Risks

- **R1**: PNCP rate limit no canary — mitigation: low frequency (10min) ✅
- **R2**: Redis outage suppresses state — mitigation: graceful skip, schema check still ativo ✅

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-15 | 2.0     | Implementation complete: canary module + ARQ cron + 6 tests + metrics + Sentry dedup | @dev |
