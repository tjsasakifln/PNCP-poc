# STORY-BTS-014 — Remove xfail Markers After Runtime Override Fix (Post-#487)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P2 — Cleanup (follows naturally from #487)
**Effort:** S (30-60 min — mechanical removal + CI verification)
**Agents:** @dev + @qa
**Status:** Ready (depends on #487 merge)

---

## Context

PR #487 fixes the feature flag runtime override architectural bug:
`_runtime_overrides` was in `routes/feature_flags.py` and `get_feature_flag()`
didn't consult it, so any admin toggle was silently rolled back on next read.
The fix makes `_runtime_overrides` authoritative in `config/features.py`.

While running the full feature-flag-related test suite against the fix branch,
**32 tests in `test_feature_flag_matrix.py` went from XFAIL (strict=False) to
XPASS**. These tests had been marked as xfail with reason:

> "STORY-BTS-FOLLOWUP: batch-only failure (passes in isolation). get_feature_flag
> returns registry default instead of env var value — polluter test writing
> os.environ directly without teardown suspected."

The actual root cause was NOT polluter tests writing `os.environ` — it was the
runtime override architecture bug. With `_runtime_overrides` now canonical
in `config.features` and consulted first by `get_feature_flag`, the polluter
pattern no longer leaks across tests.

Removing the xfail markers makes CI fail-closed on future regressions of this
cluster, consistent with the Zero Quarentena principle.

---

## Acceptance Criteria

### AC1: Remove xfail markers from `test_feature_flag_matrix.py`

Search for `STORY-BTS-FOLLOWUP` or `batch-only failure` in the file and remove
the `@pytest.mark.xfail(...)` decorator from each matching test. Affected
tests (32 total, per #487 discovery):

- `TestCriticalFlagsOnOff::test_flag_default` (parametrized — multiple)
- `TestCriticalCombinations::test_combo*` (combo1..5)
- Others with the same xfail reason

### AC2: Verify green in isolation + batch

```bash
# In isolation
pytest tests/test_feature_flag_matrix.py -q

# With adjacent polluters
pytest tests/test_feature_flag_matrix.py tests/test_feature_flags_admin.py tests/test_features.py -q
```

Both must report: no XFAIL, no XPASS, all pass as regular PASS.

### AC3: CI green post-merge

- [ ] Backend Tests (PR Gate) passes
- [ ] Backend Tests (3.12) from tests.yml matrix passes

---

## Scope

**IN:**
- `backend/tests/test_feature_flag_matrix.py` — remove xfail markers only (no logic changes)

**OUT:**
- Any modification to `config/features.py` (already done in #487)
- Adding new tests
- Refactoring test structure

---

## Dependencies

- **#487 merged** (required). Without the runtime override fix in main,
  removing xfail here may still show XPASS → XFAIL regression on some
  test orderings.

---

## Risks

- **Low.** If #487 properly merged into main, these tests pass deterministically.
  If a corner case is found, re-add xfail for ONLY that test with a new
  concrete reason (not the generic polluter suspicion).

---

## Dev Notes

The xfail markers have a common shape:

```python
@pytest.mark.xfail(
    strict=False,
    reason=(
        "STORY-BTS-FOLLOWUP: batch-only failure (passes in isolation). "
        "get_feature_flag returns registry default instead of env var value "
        "— polluter test writing os.environ directly without teardown suspected."
    ),
)
```

Use a single regex-based removal or IDE refactor. Verify each affected test
still compiles (no dangling decorator references).

---

## Files

- `backend/tests/test_feature_flag_matrix.py` (modify — removal only)

---

## Success Metrics

- 32 tests move from XPASS to PASS
- Zero xfail/xpass markers remain with `STORY-BTS-FOLLOWUP` reason
- CI Backend Tests green post-merge

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-22 | @sm (zippy-star) | Story criada como follow-up natural do #487 (feature flag _runtime_overrides architectural fix). 32 XPASS tests discovered durante manual testing de #487 — root cause was not polluter pattern, but the runtime override architecture bug. Removal unblocks Zero Quarentena on this cluster. |
