# DEBT-128: Feature Flag Cleanup
**Priority:** P2
**Effort:** 8h
**Owner:** @dev
**Sprint:** Week 5

## Context

The backend has 50+ feature flags in `config.py` with no admin UI, no documentation of which are permanent vs. temporary, and no lifecycle management. Some flags guard features that shipped months ago (e.g., `LLM_ZERO_MATCH_ENABLED` has been `True` since February). Others may be dead code. For a product charging R$397-997/month, undocumented flags are an operational risk -- a misconfigured flag could silently disable core functionality with no alerting.

## Acceptance Criteria

### Triage and Categorization

- [ ] AC1: Every feature flag in `config.py` is categorized as one of: PERMANENT (operational toggle), TEMPORARY (shipped, remove code path), EXPERIMENTAL (actively being tested), DEAD (no references in codebase)
- [ ] AC2: Categorization documented in a `FEATURE_FLAGS.md` file or as comments in `config.py`
- [ ] AC3: At least 5 TEMPORARY flags identified and their dead code paths removed

### Cleanup

- [ ] AC4: Dead code paths for removed flags are deleted (not just the flag -- the `if flag:` branches too)
- [ ] AC5: Each removed flag has a corresponding test verifying the feature works without the flag
- [ ] AC6: No regressions in test suite after cleanup

### Documentation

- [ ] AC7: Remaining flags documented with: name, purpose, default value, when to toggle, owner
- [ ] AC8: Process documented for adding new flags (naming convention, required documentation)

## Technical Notes

**Known flags to investigate:**
- `LLM_ZERO_MATCH_ENABLED` -- Has been True for months. If stable, remove flag and keep feature always on.
- `LLM_ARBITER_ENABLED` -- Same question.
- `VIABILITY_ASSESSMENT_ENABLED` -- Same question.
- `SYNONYM_MATCHING_ENABLED` -- Same question.
- Check `config.py` for the full list of flags.

**Approach:**
1. `grep -r "FLAG_NAME" backend/` for each flag to find all references
2. Check git blame to see when flag was last changed
3. If flag has been True/False for 30+ days with no toggles, candidate for removal
4. Remove the flag, the `if flag:` check, and the dead branch (keep the active branch)

**Risk mitigation:** Remove flags one at a time with individual commits. Run full test suite after each removal. If tests fail, the specific flag removal can be reverted independently.

## Test Requirements

- [ ] Full backend test suite passes after each flag removal
- [ ] Specific tests for each removed flag's feature (verify feature still works)
- [ ] `pytest -k "flag"` to find flag-specific tests that may need updating

## Files to Modify

- `backend/config.py` -- Remove temporary flags, document permanent ones
- `backend/llm_arbiter.py` -- Remove flag checks for shipped features
- `backend/filter.py` -- Remove flag checks for shipped features
- `backend/viability.py` -- Remove flag checks for shipped features
- Various test files -- Update tests that mock removed flags

## Definition of Done

- [ ] All ACs pass
- [ ] Tests pass (existing + new)
- [ ] No regressions in CI
- [ ] FEATURE_FLAGS.md or equivalent documentation exists
- [ ] Code reviewed
