# STORY-258 — Fix 7 Pre-existing Backend Test Failures

**Status:** DONE
**Priority:** Medium
**Sprint:** Current
**Estimate:** 2-3h
**Squad:** @dev + @qa

---

## Context

The backend test suite has **7 failing tests** accepted as "baseline" since various refactorings (CRIT-009 structured errors, STORY-216 search pipeline extraction, STORY-254 Portal Transparencia adapter). These failures are NOT billing/critical-path but they mask real regressions and erode CI trust.

**Current baseline:** 7 failed, 4307 passed, 55 skipped (12m33s)

**Goal:** Reduce to **0 failed** without changing production behavior. The 55 skipped tests (STORY-224 stale mocks) are out of scope.

---

## Test Failures & Root Causes

### Group A — Structured Error Format Mismatch (2 tests)

**File:** `backend/tests/test_api_buscar.py`

| # | Test | Line | Symptom | Root Cause |
|---|------|------|---------|------------|
| 1 | `TestBuscarFeatureFlagEnabled::test_enforces_quota_when_feature_flag_enabled` | 72 | `assert "..." in response.json()["detail"]` fails — `detail` is now a dict, not a string | CRIT-009 changed error responses from `{"detail": "string"}` to `{"detail": {"detail": "string", "error_code": "...", ...}}` |
| 2 | `TestBuscarFeatureFlagDisabled::test_no_quota_enforcement_when_disabled` | 163 | `assert 429 == 200` — expects no quota when flag disabled | `ENABLE_NEW_PRICING` flag is no longer respected; quota is always enforced via `check_and_increment_quota_atomic` |

**Fix A1:** Update assertion at line 72 to extract nested detail:
```python
# Before:
assert "Limite de 50 buscas mensais atingido" in response.json()["detail"]
# After:
detail = response.json()["detail"]
if isinstance(detail, dict):
    assert detail.get("error_code") == "QUOTA_EXCEEDED"
    assert "Limite de 50 buscas mensais atingido" in detail["detail"]
else:
    assert "Limite de 50 buscas mensais atingido" in detail
```

**Fix A2:** Test 2 tests obsolete behavior (ENABLE_NEW_PRICING=False skipping quota). Since quota is now always enforced, update test to:
- Either mock `check_and_increment_quota_atomic` to return `(True, 1, 49)` (quota allowed) and verify the search proceeds
- Or delete the test if `ENABLE_NEW_PRICING` flag is fully deprecated

### Group B — Portal Transparencia Env Leak (1 test)

**File:** `backend/tests/test_portal_transparencia.py`

| # | Test | Line | Symptom | Root Cause |
|---|------|------|---------|------------|
| 3 | `TestHealthCheck::test_no_api_key_returns_unavailable` | 442 | Gets `DEGRADED` instead of `UNAVAILABLE` | `adapter_no_key` fixture passes `api_key=""` but `__init__` uses `api_key or os.environ.get(...)` — empty string is falsy, so env var `PORTAL_TRANSPARENCIA_API_KEY` (loaded from `.env` via config.py) leaks in |

**Root cause detail:**
```python
# portal_transparencia_client.py:114
self._api_key = api_key or os.environ.get("PORTAL_TRANSPARENCIA_API_KEY", "")
#                ^^^^^^^^ empty string is falsy → falls through to env var
```

When `.env` has `PORTAL_TRANSPARENCIA_API_KEY` set, the adapter gets a real key, tries an HTTP call without mocks, gets a non-200 → returns DEGRADED.

**Fix B:** Patch the env var in the fixture:
```python
@pytest.fixture
def adapter_no_key(monkeypatch):
    """Adapter without an API key."""
    monkeypatch.delenv("PORTAL_TRANSPARENCIA_API_KEY", raising=False)
    return PortalTransparenciaAdapter(api_key="", timeout=5)
```

Or change `__init__` to use `api_key if api_key is not None else os.environ.get(...)` (preferred — semantic fix).

### Group C — Profile Context Mock Chain Mismatch (4 tests)

**File:** `backend/tests/test_profile_context.py`

| # | Test | Line | Symptom | Root Cause |
|---|------|------|---------|------------|
| 4 | `TestSaveProfileContext::test_save_context_db_error` | 202 | Gets 200 instead of 500 | Mock `side_effect` on update chain doesn't match actual DB call chain |
| 5 | `TestGetProfileContext::test_get_context_with_data` | 214 | Gets 500 instead of 200 | Mock chain for select/eq/single/execute doesn't match actual route |
| 6 | `TestGetProfileContext::test_get_context_empty` | 225 | Gets 500 instead of 200 | Same as #5 |
| 7 | `TestGetProfileContext::test_get_context_null` | 236 | Gets 500 instead of 200 | Same as #5 |

**Investigation needed:** The route at `routes/user.py:205-254` uses `db=Depends(get_db)` and the test overrides `get_db` with a mock. The mock chain structure looks correct syntactically. Likely causes:

1. **`get_db` import path changed** — test imports `from database import get_db` but route might use a different import
2. **Additional middleware** intercepting the request and failing before the route handler
3. **Missing mock for `log_user_action` or `mask_user_id`** causing import-time error in route module

**Fix C:** Debug by running a single failing test with `-s` flag to see the actual traceback, then update the mock chain or dependency override to match current code structure.

---

## Acceptance Criteria

- [x] **AC1:** `test_enforces_quota_when_feature_flag_enabled` passes — assertion updated for CRIT-009 structured error format (detail is now a dict, check `error_code` and nested `detail`)
- [x] **AC2:** `test_no_quota_enforcement_when_disabled` passes — already self-healed (quota flow works with live Supabase)
- [x] **AC3:** `test_no_api_key_returns_unavailable` passes — env var leak fixed via `monkeypatch.delenv` in fixture
- [x] **AC4:** All 4 `test_profile_context` tests pass — already self-healed (mock chain matches current route)
- [x] **AC5:** Zero regressions — `pytest` shows 0 failed (down from 7→2 actual failures)
- [x] **AC6:** No production code changes — test-only fixes (2 files: test_api_buscar.py, test_portal_transparencia.py)
- [x] **AC7:** Baseline numbers updated in `MEMORY.md`

---

## Implementation Notes

### Priority order
1. **Group C first** (4 tests, biggest win, needs investigation)
2. **Group A** (2 tests, straightforward assertion fixes)
3. **Group B** (1 test, simple fixture fix)

### Verification command
```bash
cd backend
python -m pytest tests/test_api_buscar.py::TestBuscarFeatureFlagEnabled::test_enforces_quota_when_feature_flag_enabled tests/test_api_buscar.py::TestBuscarFeatureFlagDisabled::test_no_quota_enforcement_when_disabled tests/test_portal_transparencia.py::TestHealthCheck::test_no_api_key_returns_unavailable tests/test_profile_context.py -v
```

### Full suite verification
```bash
python -m pytest --tb=short -q  # Should show 0 failed
```

---

## Files to Modify

| File | Change |
|------|--------|
| `tests/test_api_buscar.py` | Lines 72, 131-169 — update assertion format + fix/delete legacy test |
| `tests/test_portal_transparencia.py` | Lines 40-43 — fix `adapter_no_key` fixture |
| `tests/test_profile_context.py` | Lines 20-29, 156-244 — fix mock chain + dependency override |
| `MEMORY.md` | Update baseline numbers |

**Optionally:**
| `clients/portal_transparencia_client.py` | Line 114 — change `or` to `if is not None` (semantic fix) |

---

## Out of Scope

- The 55 skipped tests (STORY-224 — stale mocks from STORY-216 refactoring)
- Frontend test baseline
- New test coverage
