# STORY-223 Track 2 - Quick Reference

## ✅ Status: COMPLETE

All 10 acceptance criteria (AC6-AC11, AC17-AC20) implemented and tested.

## What Was Done

### 1. Fixed `/api/features/me` Fallback Logic

**Problem:** Features endpoint fell back to `free_trial` too eagerly, downgrading paid users during transient errors.

**Solution:** Implemented 4-layer fallback in `backend/routes/features.py:fetch_features_from_db()`:
1. Active subscription (primary)
2. Grace-period subscription (3-day tolerance)
3. `profiles.plan_type` (last known plan)
4. `free_trial` (last resort only)

### 2. Removed Dead Lock Code

**Removed from `backend/quota.py`:**
- `_quota_locks: dict[str, asyncio.Lock] = {}` (line 35)
- `_get_user_lock(user_id: str) -> asyncio.Lock` (lines 43-47)

**Reason:** Never called, RPC functions handle atomicity.

## Files Changed

```
backend/
├── routes/features.py         # Added multi-layer fallback
├── quota.py                    # Removed dead locks
└── tests/
    ├── test_features.py        # NEW: 7 tests (AC6-AC11)
    └── test_quota.py           # ENHANCED: +4 tests (AC20)
```

## Test Coverage

```bash
# Run Track 2 tests
cd backend
pytest tests/test_features.py -v                              # 7 tests
pytest tests/test_quota.py::TestCheckAndIncrementQuotaAtomic -v  # 4 tests

# All 11 tests pass ✅
```

## Acceptance Criteria Mapping

| AC | Description | Implementation |
|----|-------------|----------------|
| AC6 | Features endpoint uses `get_plan_from_profile()` fallback | ✅ `routes/features.py` lines 107-117 |
| AC7 | Grace period (3 days) respected | ✅ `routes/features.py` lines 87-104 |
| AC8 | Test: active subscription → correct plan | ✅ `test_features.py` line 15 |
| AC9 | Test: expired + grace → correct plan | ✅ `test_features.py` line 30 |
| AC10 | Test: expired + profile → profile plan | ✅ `test_features.py` line 48 |
| AC11 | Test: no subscription → free_trial | ✅ `test_features.py` line 69 |
| AC17 | Remove dead lock code | ✅ `quota.py` lines 32-47 deleted |
| AC18 | N/A (locks removed) | - |
| AC19 | Verify locks completely removed | ✅ Grep confirms 0 refs |
| AC20 | Test: fallback quota increment | ✅ `test_quota.py` line 16 |

## Key Code Snippets

### Multi-Layer Fallback Pattern

```python
# Layer 1: Active subscription
sub_result = sb.table("user_subscriptions").select(...).eq("is_active", True).execute()

# Layer 2: Grace-period subscription
if not plan_id:
    grace_cutoff = (datetime.now(timezone.utc) - timedelta(days=SUBSCRIPTION_GRACE_DAYS)).isoformat()
    grace_result = sb.table("user_subscriptions").select(...).gte("expires_at", grace_cutoff).execute()

# Layer 3: Profile fallback
if not plan_id:
    profile_plan = get_plan_from_profile(user_id, sb)
    if profile_plan and profile_plan != "free_trial":
        plan_id = profile_plan

# Layer 4: Last resort
if not plan_id:
    plan_id = "free_trial"
```

### Test Pattern for Fallback

```python
@patch("routes.features.get_plan_from_profile")  # Patch where imported!
@patch("supabase_client.get_supabase")
def test_fallback_to_profile(mock_sb, mock_get_plan):
    # Mock no active subscription
    mock_sb.table(...).execute.return_value.data = []

    # Mock no grace-period subscription
    mock_sb.table(...).execute.return_value.data = []

    # Mock profile returns plan
    mock_get_plan.return_value = "maquina"

    result = fetch_features_from_db("user-123")
    assert result.plan_id == "maquina"  # NOT free_trial!
```

## Verification Commands

```bash
# Verify no references to removed locks
cd backend
grep -r "_quota_locks" .    # Should return nothing
grep -r "_get_user_lock" .  # Should return nothing

# Run all tests
pytest tests/test_features.py tests/test_quota.py -v
# Expected: 48 passed

# Check for regressions
pytest tests/test_plan_capabilities.py -v
# Expected: 37 passed, 5 skipped (pre-existing)
```

## Next Steps

- **Track 1:** Apply same fallback to `routes/search.py` and `routes/user.py`
- **Track 3:** Fix plan loading race condition
- **Track 4:** E2E testing

## Documentation

- Full implementation details: `STORY-223-TRACK-2-IMPLEMENTATION.md`
- Story definition: `docs/stories/STORY-223-features-fallback-quota-locks.md` (to be created)

---
**Completed:** 2026-02-13
