# DEBT-115: Search Route Decomposition

**Prioridade:** GTM-RISK (30 dias)
**Estimativa:** 16h
**Fonte:** Brownfield Discovery — @architect (ARCH-001), @qa regression risk HIGH
**Score Impact:** Maint 6→8

## Contexto
`routes/search.py` é o maior arquivo do backend com 2177 LOC. Contém SSE generator, state machine wiring, retry logic, e search orchestration misturados. Dificulta hotfixes e code review. @qa alerta: adicionar contract tests ANTES de decompor.

## Acceptance Criteria

### Fase 1: Contract Tests (4h)
- [x] AC1: Snapshot tests para response schemas de POST /buscar (JSON response)
- [x] AC2: Snapshot tests para SSE event format (/buscar-progress/{id})
- [x] AC3: Contract test para retry endpoint (POST /v1/search/{id}/retry)
- [x] AC4: Contract test para status endpoint (GET /v1/search/{id}/status)

### Fase 2: Decomposição (12h)
- [x] AC5: Extrair SSE generator para `routes/search_sse.py` (~400 LOC) → 466 LOC
- [x] AC6: Extrair state machine wiring para `routes/search_state.py` (~300 LOC) → 633 LOC
- [x] AC7: Extrair retry/status endpoints para `routes/search_status.py` (~200 LOC) → 460 LOC
- [x] AC8: `routes/search.py` reduzido para <800 LOC (orchestration + POST /buscar) → 748 LOC
- [x] AC9: Todos os 5131+ backend tests passam, 0 regressions (4 falhas pre-existentes mantidas)
- [x] AC10: Todos os contract tests da Fase 1 passam (18/18)
- [x] AC11: SSE heartbeat + progress tracking funciona end-to-end (backward-compat re-exports)

## File List
- [x] `backend/routes/search.py` (EDIT — reduzido de 2177 para 748 LOC)
- [x] `backend/routes/search_sse.py` (NEW — 466 LOC, SSE progress stream)
- [x] `backend/routes/search_state.py` (NEW — 633 LOC, background results + async search)
- [x] `backend/routes/search_status.py` (NEW — 460 LOC, status/results/retry/cancel)
- [x] `backend/tests/test_search_contracts.py` (NEW — 18 contract tests)
- [x] `backend/tests/test_harden005_safe_persist.py` (EDIT — 11 mock paths updated)
- [x] `backend/tests/test_story362_l3_persistence.py` (EDIT — 11 mock paths updated)
- [x] `backend/tests/test_state_externalization.py` (EDIT — 8 mock paths updated)
- [x] `backend/tests/test_story292_async_search.py` (EDIT — 6 mock paths updated)
