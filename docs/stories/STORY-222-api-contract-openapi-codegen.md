# STORY-222: Shared API Contract — OpenAPI → TypeScript Codegen

**Status:** Pending
**Priority:** P1 — Pre-GTM Important
**Sprint:** Sprint 3 (Weeks 4-5)
**Estimated Effort:** 2 days
**Source:** AUDIT-FRENTE-1-CODEBASE (CRIT-03), AUDIT-CONSOLIDATED (REFACTOR-03)
**Squad:** team-bidiq-feature (architect, dev)

---

## Context

The frontend API proxy at `api/buscar/route.ts` lines 216-229 manually constructs responses, cherry-picking fields from the backend. This causes:

**Silently dropped fields:**
- `source_stats` (multi-source consolidation metrics)
- `hidden_by_min_match` (minimum match filtering count)
- `filter_relaxed` (zero-results relaxation flag)
- `synonym_matches` (synonym-based recovery results)
- `llm_arbiter_stats` (LLM classification statistics)

**Type mismatches:**
- Frontend `Resumo.distribuicao_uf` exists in `types.ts` but NOT in backend `ResumoLicitacoes` schema
- `BuscaResult.download_id` typed as `string` but can be `null`

Any backend field additions are invisible to the frontend until manually added to both the proxy and the types.

## Acceptance Criteria

### OpenAPI Schema Stabilization

- [ ] AC1: Ensure all backend endpoints have explicit Pydantic `response_model` defined (audit current gaps)
- [ ] AC2: Run `backend/tests/test_openapi_schema.py` to capture current schema snapshot
- [ ] AC3: Fix any schema diff issues (update snapshot if intentional changes)

### TypeScript Code Generation

- [ ] AC4: Add `openapi-typescript` to frontend devDependencies
- [ ] AC5: Create `scripts/generate-api-types.sh` that:
  1. Fetches `http://localhost:8000/openapi.json`
  2. Runs `npx openapi-typescript` to generate `frontend/app/api-types.generated.ts`
- [ ] AC6: Generated types replace manual `types.ts` interfaces for API responses
- [ ] AC7: `types.ts` retains frontend-only types (UI state, etc.) but imports API types from generated file

### Proxy Passthrough

- [ ] AC8: Update `api/buscar/route.ts` to forward ALL backend response fields (not cherry-pick)
- [ ] AC9: If field filtering is needed (e.g., strip internal fields), do it explicitly with documented reason
- [ ] AC10: Remove `Resumo.distribuicao_uf` from frontend types (does not exist in backend)
- [ ] AC11: Fix `download_id` type to be `string | null`

### CI Integration

- [ ] AC12: Add CI step: generate types, run `tsc --noEmit` — if type generation fails or produces type errors, CI fails
- [ ] AC13: Add pre-commit hook or CI check that verifies generated types are up-to-date

### Testing

- [ ] AC14: TypeScript check passes: `npx tsc --noEmit --pretty`
- [ ] AC15: All frontend tests pass with generated types
- [ ] AC16: OpenAPI schema snapshot test passes

## Validation Metric

- Zero manually-defined API response types in frontend (all from codegen)
- Adding a new field to backend Pydantic model automatically appears in frontend types after regeneration
- `api/buscar/route.ts` forwards all fields (no silent drops)

## Risk Mitigated

- P1: Silent data loss from proxy field filtering
- P1: Frontend types diverge from backend reality
- P2: Manual type maintenance burden

## File References

| File | Change |
|------|--------|
| `frontend/app/api/buscar/route.ts` | Forward all fields |
| `frontend/app/types.ts` | Import from generated types |
| `frontend/app/api-types.generated.ts` | NEW — auto-generated |
| `scripts/generate-api-types.sh` | NEW — codegen script |
| `frontend/package.json` | Add openapi-typescript devDep |
