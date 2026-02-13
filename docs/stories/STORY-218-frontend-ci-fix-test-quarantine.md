# STORY-218: Fix Frontend CI & Quarantine Pre-existing Test Failures

**Status:** Pending
**Priority:** P1 — Pre-GTM Important
**Sprint:** Sprint 2 (Weeks 2-3)
**Estimated Effort:** 2 days
**Source:** AUDIT-FRENTE-3-TESTS (GAP-2, QA-01, QA-06), AUDIT-CONSOLIDATED (QA-01, QA-07)
**Squad:** team-bidiq-frontend (dev, qa)

---

## Context

The CI pipeline provides **false confidence** through multiple mechanisms:
1. Frontend tests run with `|| true` — failures never block merges
2. Coverage threshold lowered from 60% → branches: 35%, functions: 40%, lines: 44%, statements: 43% (comment: "TEMPORARY: Lowered to unblock PR #129" — still in effect)
3. 91 pre-existing failures (70 frontend + 21 backend) mask new regressions
4. `api/download.test.ts` is entirely wrapped in `describe.skip()`

This creates a vicious cycle: tests break → thresholds lowered → developers treat tests as obstacles → more tests break.

## Acceptance Criteria

### Track 1: Remove `|| true` from CI

- [ ] AC1: Remove `|| true` from frontend test command in `.github/workflows/tests.yml`
- [ ] AC2: Frontend CI now **fails** when tests fail (true enforcement)
- [ ] AC3: All currently-passing tests continue to pass

### Track 2: Quarantine Pre-existing Failures

- [ ] AC4: Create `frontend/__tests__/quarantine/` directory
- [ ] AC5: Move all 70 pre-existing frontend test failures into quarantine directory
- [ ] AC6: Add jest config to exclude quarantine directory from default test runs
- [ ] AC7: Add separate CI job `test:quarantine` that runs quarantined tests but does NOT block pipeline
- [ ] AC8: Create tracking document `docs/test-quarantine-inventory.md` listing each quarantined test with category and estimated fix effort

### Track 3: Restore Coverage Threshold

- [ ] AC9: Raise coverage thresholds back to 60% target (or whatever level passes after quarantine)
- [ ] AC10: Remove "TEMPORARY" comment from `jest.config.js` lines 62-69
- [ ] AC11: Set thresholds to actual post-quarantine levels (e.g., branches: 50%, functions: 55%, lines: 55%, statements: 55%) as stepping stone

### Track 4: Un-skip Download Test

- [ ] AC12: Rewrite `frontend/__tests__/api/download.test.ts` to properly mock `fs/promises` instead of deprecated `downloadCache`
- [ ] AC13: Remove `describe.skip()` wrapper
- [ ] AC14: Test covers: valid download, invalid UUID, non-existent file, open redirect prevention

### Backend Pre-existing Failures

- [ ] AC15: Triage 21 backend pre-existing failures — categorize as: import error, stale mock, missing module, placeholder
- [ ] AC16: Fix import-path failures (estimated ~12 of 21)
- [ ] AC17: Mark truly stale tests with `@pytest.mark.skip(reason="Placeholder — STORY-215")` pointing to the story that will fix them

## Validation Metric

- CI pipeline fails when a NEW test fails (no `|| true`)
- Quarantined tests separated from main suite
- Coverage threshold > 50% enforced
- `describe.skip()` count = 0 in non-quarantine test files

## Risk Mitigated

- P1: New regressions invisible due to `|| true`
- P1: Coverage threshold erosion (35% branches is unacceptable for payment-processing app)
- P2: 91 pre-existing failures mask new regressions

## File References

| File | Change |
|------|--------|
| `.github/workflows/tests.yml` | Remove `\|\| true` |
| `frontend/jest.config.js` | Raise thresholds, exclude quarantine |
| `frontend/__tests__/quarantine/` | NEW directory for quarantined tests |
| `frontend/__tests__/api/download.test.ts` | Rewrite, un-skip |
| `docs/test-quarantine-inventory.md` | NEW tracking doc |
