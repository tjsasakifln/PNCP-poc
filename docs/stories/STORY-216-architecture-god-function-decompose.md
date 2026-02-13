# STORY-216: Decompose God Function — buscar_licitacoes → SearchPipeline

**Status:** Pending
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

- [ ] AC1: Create `backend/search_pipeline.py` with a `SearchPipeline` class implementing a stage pattern:
  ```
  Stage 1: ValidateRequest — validate input, check quota, resolve plan
  Stage 2: PrepareSearch — parse terms, configure sector, build query params
  Stage 3: ExecuteSearch — call PNCP API (+ other sources), collect raw results
  Stage 4: FilterResults — keyword filter, status filter, modality filter, value filter
  Stage 5: EnrichResults — LLM arbiter, relevance scoring, deduplication
  Stage 6: GenerateOutput — pagination, Excel generation, LLM summary
  Stage 7: Persist — save session, build response
  ```
- [ ] AC2: Each stage is an independent method that takes and returns a typed `SearchContext` dataclass
- [ ] AC3: `SearchContext` carries all intermediate state (raw results, filtered results, scores, etc.)
- [ ] AC4: Each stage has its own error handling — failure in Stage 6 preserves Stage 4 results
- [ ] AC5: `buscar_licitacoes()` in `routes/search.py` becomes a thin ~30-line wrapper that creates `SearchPipeline` and runs stages

### Cleanup

- [ ] AC6: Move `_PNCPLegacyAdapter` to its own module or into `pncp_client.py`
- [ ] AC7: Extract duplicated quota fallback logic into shared function (used by both `routes/search.py` and `routes/user.py`)
- [ ] AC8: Move all 12+ deferred imports to module level (pipeline class uses dependency injection)
- [ ] AC9: Remove duplicated link-building logic (consolidate with `excel.py`)

### Testing

- [ ] AC10: Each pipeline stage is independently testable
- [ ] AC11: Existing `test_api_buscar.py` tests pass unchanged (API contract unchanged)
- [ ] AC12: Add unit tests for at least 3 individual stages
- [ ] AC13: TypeScript check passes: `npx tsc --noEmit --pretty`

### Non-Goals

- Do NOT change the API contract (request/response shapes stay identical)
- Do NOT refactor the filter logic itself (that's a separate story)
- Do NOT change the PNCP client integration

## Validation Metric

- `routes/search.py:buscar_licitacoes()` is < 50 lines
- `search_pipeline.py` has clear stage boundaries
- All existing API tests pass

## Risk Mitigated

- P1: Unmaintainable 860-line function blocks feature development
- P1: Single point of failure — any exception loses all computation
- P2: Code duplication across modules

## File References

| File | Change |
|------|--------|
| `backend/search_pipeline.py` | NEW — SearchPipeline class with 7 stages |
| `backend/routes/search.py` | Refactor to thin wrapper |
| `backend/pncp_client.py` | Receive _PNCPLegacyAdapter |
| `backend/tests/test_api_buscar.py` | Verify unchanged behavior |
