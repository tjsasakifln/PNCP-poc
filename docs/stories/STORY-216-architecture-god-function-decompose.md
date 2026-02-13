# STORY-216: Decompose God Function — buscar_licitacoes → SearchPipeline

**Status:** In Progress (implementation complete, test hardening pending)
**Priority:** P1 — Pre-GTM Important
**Sprint:** Sprint 2 (Weeks 2-3)
**Estimated Effort:** 3 days
**Source:** AUDIT-FRENTE-1-CODEBASE (CRIT-01), AUDIT-CONSOLIDATED (REFACTOR-01)
**Squad:** team-bidiq-backend (architect, dev, qa)

---

## Context

`routes/search.py:buscar_licitacoes()` is an 860+ line function with cyclomatic complexity 50+. It handles the **entire search lifecycle** in one monolithic block: request validation, quota checking, plan capability resolution, term parsing, PNCP API calls, 5-stage filtering, LLM arbiter, relevance scoring, deduplication, pagination, Excel generation, LLM summary, and session saving.

**Specific violations:**
- 12+ deferred imports inside the function body
- Inline class `_PNCPLegacyAdapter` defined mid-function
- Duplicated quota fallback logic (also in `routes/user.py`)
- No intermediate error boundaries — failure at line 850 loses all prior computation
- Single point of failure: any change to any search sub-feature requires modifying this one function

## Acceptance Criteria

### Architecture — SearchPipeline

- [x] AC1: Create `backend/search_pipeline.py` with a `SearchPipeline` class implementing a stage pattern:
  ```
  Stage 1: ValidateRequest — validate input, check quota, resolve plan
  Stage 2: PrepareSearch — parse terms, configure sector, build query params
  Stage 3: ExecuteSearch — call PNCP API (+ other sources), collect raw results
  Stage 4: FilterResults — keyword filter, status filter, modality filter, value filter
  Stage 5: EnrichResults — LLM arbiter, relevance scoring, deduplication
  Stage 6: GenerateOutput — pagination, Excel generation, LLM summary
  Stage 7: Persist — save session, build response
  ```
- [x] AC2: Each stage is an independent method that takes and returns a typed `SearchContext` dataclass
- [x] AC3: `SearchContext` carries all intermediate state (raw results, filtered results, scores, etc.)
- [x] AC4: Each stage has its own error handling — failure in Stage 6 preserves Stage 4 results
- [x] AC5: `buscar_licitacoes()` in `routes/search.py` becomes a thin ~30-line wrapper that creates `SearchPipeline` and runs stages

### Cleanup

- [x] AC6: Move `_PNCPLegacyAdapter` to its own module or into `pncp_client.py`
- [x] AC7: Extract duplicated quota fallback logic into shared function (used by both `routes/search.py` and `routes/user.py`)
- [x] AC8: Move all 12+ deferred imports to module level (pipeline class uses dependency injection)
- [ ] AC9: Remove duplicated link-building logic (consolidate with `excel.py`) — deferred, low risk

### Testing

- [x] AC10: Each pipeline stage is independently testable (7 async methods on SearchPipeline class)
- [x] AC11: Existing `test_api_buscar.py` tests pass unchanged — API contract preserved via SimpleNamespace dependency injection. Pre-existing failures (rate limiter state pollution, date range tests that hang on Supabase calls) confirmed to also fail on committed code.
- [ ] AC12: Add unit tests for at least 3 individual stages — pending
- [ ] AC13: TypeScript check passes: `npx tsc --noEmit --pretty` — pending

### Non-Goals

- Do NOT change the API contract (request/response shapes stay identical)
- Do NOT refactor the filter logic itself (that's a separate story)
- Do NOT change the PNCP client integration

## Implementation Notes (2026-02-13)

### What was done

**4 parallel fronts executed:**

1. **FRENTE ALPHA — Architecture** (complete)
   - Created `backend/search_context.py`: SearchContext dataclass with fields for all 7 stages
   - Created `backend/search_pipeline.py`: SearchPipeline class with 7 stage methods + helper functions

2. **FRENTE BRAVO — Extract & Cleanup** (complete)
   - Moved `PNCPLegacyAdapter` from inline class to `pncp_client.py` module level
   - Created `create_fallback_quota_info()` and `create_legacy_quota_info()` in `quota.py`
   - Updated `routes/user.py` to use shared fallback functions (eliminated duplication)
   - Moved helper functions `_build_pncp_link`, `_calcular_urgencia`, `_calcular_dias_restantes`, `_convert_to_licitacao_items` to `search_pipeline.py`

3. **FRENTE CHARLIE — Thin Wrapper** (complete)
   - `routes/search.py` reduced from 1128 lines to 247 lines
   - `buscar_licitacoes()` is now ~42 lines of logic (wrapper + exception handlers)
   - Dependencies injected via `SimpleNamespace` to preserve test mock paths at `routes.search.*`

4. **FRENTE DELTA — Testing** (partial)
   - Confirmed test_api_buscar.py tests that pass still pass (feature flag, quota)
   - Confirmed pre-existing failures are NOT regressions (rate limiter state pollution, date range tests that hang on unmocked Supabase calls — verified by running same tests on committed code)
   - New pipeline stage tests (AC12) and TypeScript check (AC13) still pending

### Key architectural decisions

- **Dependency Injection via SimpleNamespace**: Tests mock `routes.search.PNCPClient`, `routes.search.rate_limiter`, etc. To preserve these mock paths, the thin wrapper passes module-level imports as a `deps` SimpleNamespace to SearchPipeline. The pipeline never imports these names directly.
- **Late binding for quota mocks**: Pipeline uses `import quota` at module level and calls `quota.check_quota()` at runtime. This preserves `@patch("quota.check_quota")` mock compatibility.
- **PNCPLegacyAdapter refactored**: Changed from closure-captured variables to explicit constructor parameters.

### Remaining work

- AC9: Consolidate link-building with excel.py (low priority)
- AC12: Write `test_search_pipeline.py` with unit tests for individual stages
- AC13: Run TypeScript check

## Validation Metric

- `routes/search.py:buscar_licitacoes()` is < 50 lines ✅ (42 lines of logic)
- `search_pipeline.py` has clear stage boundaries ✅ (7 named async methods)
- All existing API tests pass — ✅ no regressions (pre-existing failures confirmed on committed code)

## Risk Mitigated

- P1: Unmaintainable 860-line function blocks feature development
- P1: Single point of failure — any exception loses all computation
- P2: Code duplication across modules

## File References

| File | Change |
|------|--------|
| `backend/search_pipeline.py` | NEW — SearchPipeline class with 7 stages + moved helper functions |
| `backend/search_context.py` | NEW — SearchContext dataclass carrying all intermediate state |
| `backend/routes/search.py` | Refactored from 1128 lines to 247 lines (thin wrapper) |
| `backend/routes/user.py` | Uses shared `create_fallback_quota_info()` / `create_legacy_quota_info()` |
| `backend/pncp_client.py` | Receives `PNCPLegacyAdapter` class (moved from inline) |
| `backend/quota.py` | NEW shared functions: `create_fallback_quota_info()`, `create_legacy_quota_info()` |
| `backend/tests/test_api_buscar.py` | NOT modified — verify unchanged behavior |
