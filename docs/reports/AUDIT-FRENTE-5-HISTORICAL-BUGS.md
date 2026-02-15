# FRENTE 5: Historical Bugs Deep Dive

**Author:** @dev (Opus 4.6 agent)
**Date:** 2026-02-12
**Scope:** 7 production bugs from beta testing logs
**Files Analyzed:** 32 source files, 6 test files, 20 git commits

---

## Executive Summary

All 7 bugs have been partially or fully addressed in the codebase, but **critical regression test gaps remain**. The existing test suite for `auth.py` is **completely stale** -- all 17 tests mock the old `sb.auth.get_user()` Supabase API approach that was replaced by local JWT validation on 2026-02-11. These tests pass only because they never touch the actual implementation path. The `test_auth_cache.py` (12 tests) also mocks the old API pattern.

| Bug | Status | Root Cause Identified | Fix Verified | Regression Test Exists |
|-----|--------|----------------------|-------------|----------------------|
| 1. Logging Cascade | **FIXED** | `%(request_id)s` formatter without filter | Yes | **NO** |
| 2. JWT InvalidAlgorithm | **FIXED** | Supabase API-based validation | Yes | **NO** (tests stale) |
| 3. Paid Users as Free | **FIXED** | No profile fallback + no grace period | Yes (multi-layer) | Partial |
| 4. Login Button Visible | **FIXED** | Separate layouts for public/protected | Yes | **NO** |
| 5. Search History Not Saved | **FIXED** | History save is in code | Yes | **NO** |
| 6. Inconsistent Quota | **FIXED** | TOCTOU race condition | Yes | Partial |
| 7. Incorrect Header State | **ARCHITECTURE RISK** | /buscar has own header, not using (protected) layout | Yes (intentional) | **NO** |

**Urgency:** The stale auth tests (Bugs 1+2) represent a **P0 test debt** -- they provide false confidence while covering zero lines of the current production code path.

---

## Bug 1: Login Google Cascade Failure

### Root Cause

The logging formatter in `backend/config.py` (line 98-101) requires a `%(request_id)s` field:

```python
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
```

When this formatter was first introduced, there was no `RequestIDFilter` to inject `request_id` into log records. Any log statement emitted before the middleware ran (startup logs, module-level logs, or logs from non-request contexts like Google OAuth callbacks) would fail with `ValueError: Formatting field not found in record: 'request_id'`, causing a cascade where every subsequent log statement also failed.

### Current Status: FIXED

The fix was implemented in STORY-202 (commit `eeafb66`, 2026-02-11) via `backend/middleware.py`:

```python
class RequestIDFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = request_id_var.get("-")
        return True
```

This filter is attached to both the handler AND the root logger in `setup_logging()` (config.py lines 106-116):

```python
from middleware import RequestIDFilter
request_id_filter = RequestIDFilter()
handler.addFilter(request_id_filter)
root_logger.addFilter(request_id_filter)
```

The `ContextVar` default of `"-"` ensures non-request contexts (startup, callbacks, background tasks) get a safe fallback value.

### Evidence from Code

- `backend/config.py` line 99: Formatter requires `%(request_id)s`
- `backend/config.py` lines 106-116: `RequestIDFilter` added to handler AND root logger
- `backend/middleware.py` lines 16-26: `RequestIDFilter` class with `ContextVar` fallback
- `backend/middleware.py` line 13: `request_id_var: ContextVar[str] = ContextVar("request_id", default="-")`

### Remaining Risk

The `RequestIDFilter` is imported inside `setup_logging()` to avoid circular dependencies (`from middleware import RequestIDFilter`). If `middleware.py` fails to import (e.g., syntax error), `setup_logging()` will crash and ALL logging will break again. This is fragile.

Additionally, `config.py` lines 223-227 emit log statements at module import time (before `setup_logging()` is called):

```python
logger = logging.getLogger(__name__)
logger.info(f"Feature Flag - ENABLE_NEW_PRICING: {ENABLE_NEW_PRICING}")
```

These logs fire before `RequestIDFilter` is attached. They currently succeed only because they go to the default stderr handler (which has no formatter requiring `request_id`). But if someone adds a handler with the custom formatter at module level, it would break.

### Regression Test Needed

**YES -- MISSING**. The existing `test_config.py` line 92 only verifies the formatter *string* contains `%(request_id)s`. There is NO test that:

1. Verifies `RequestIDFilter` injects `request_id` into log records during requests
2. Verifies `request_id` defaults to `"-"` outside request context (startup logs)
3. Verifies module-level logging (before `setup_logging()`) does not crash
4. Verifies the `CorrelationIDMiddleware` propagates `X-Request-ID` header

---

## Bug 2: JWT InvalidAlgorithmError

### Root Cause

The original `auth.py` used Supabase's remote API to validate JWT tokens:

```python
# OLD CODE (pre-commit 8c8c19d):
mock_supabase.auth.get_user(token)
```

This approach had two fatal flaws:

1. **AuthApiError**: The `SERVICE_ROLE_KEY` client cannot validate user tokens via `sb.auth.get_user(token)`. This endpoint is designed for the user's own client, not the service role client.
2. **InvalidAlgorithmError**: When the code was modified to use `jwt.decode()` without specifying the correct algorithm, PyJWT would reject the token because Supabase uses `HS256` but the code either specified no algorithm or a different one.

### Current Status: FIXED

Commit `8c8c19d` (2026-02-11) completely replaced the Supabase API validation with local JWT validation:

```python
# CURRENT CODE (auth.py lines 88-95):
payload = jwt.decode(
    token,
    jwt_secret,
    algorithms=["HS256"],
    audience="authenticated",
    options={"verify_aud": False}
)
```

Key design decisions:
- Algorithm explicitly set to `["HS256"]` (Supabase default)
- JWT secret loaded from `SUPABASE_JWT_SECRET` env var
- Audience verification relaxed for compatibility (`verify_aud: False`)
- User claims extracted from JWT payload (sub, email, role) -- no API call needed

### Evidence from Code

- `backend/auth.py` lines 78-81: Loads `SUPABASE_JWT_SECRET` from env
- `backend/auth.py` line 90: `algorithms=["HS256"]` explicitly set
- `backend/auth.py` lines 96-101: Catches `ExpiredSignatureError` and `InvalidTokenError` separately
- `backend/auth.py` lines 104-116: Extracts `sub`, `email`, `role` from JWT claims
- `backend/requirements.txt`: `PyJWT==2.9.0` added

### Critical Test Debt: ALL AUTH TESTS ARE STALE

**This is the most serious finding of this audit.**

`backend/tests/test_auth.py` (17 tests) and `backend/tests/test_auth_cache.py` (12 tests) -- **29 total tests** -- all mock the OLD Supabase API pattern:

```python
# test_auth.py line 59:
mock_supabase.auth.get_user.return_value = mock_user_response

# test_auth_cache.py line 43:
mock_sb_instance.auth.get_user.return_value = mock_user_response
```

The current `auth.py` code NEVER calls `sb.auth.get_user()`. It uses `jwt.decode()`. These tests exercise a code path that no longer exists in production. They pass because the mocks short-circuit execution before reaching the actual JWT validation logic.

**Impact:** Zero test coverage for:
- `jwt.decode()` with correct algorithm (HS256)
- `SUPABASE_JWT_SECRET` missing/empty handling
- Expired token detection
- Malformed token handling
- JWT claims extraction (sub, email, role)
- Cache key generation with `hashlib.sha256` (STORY-203 SYS-M02)
- Token cache TTL behavior with SHA256-based keys

The `test_auth_cache.py` line 92 even uses `hash()` (Python's built-in) for cache key calculation, but the actual code now uses `hashlib.sha256()`. These tests literally cannot detect if the cache is broken.

### Regression Test Needed

**YES -- ALL 29 EXISTING TESTS MUST BE REWRITTEN** to mock `jwt.decode()` and `os.getenv("SUPABASE_JWT_SECRET")` instead of `sb.auth.get_user()`. Required test cases:

1. Valid HS256 JWT token decoded successfully
2. Expired JWT raises 401 with "Token expirado"
3. Invalid JWT raises 401 with "Token invalido"
4. Missing `SUPABASE_JWT_SECRET` raises 500
5. JWT without `sub` claim raises 401
6. JWT with missing `email` defaults to "unknown"
7. Token cache uses SHA256 hash (not Python `hash()`)
8. Cache TTL works correctly with SHA256 keys
9. Google OAuth JWT tokens are accepted (same HS256 algorithm)

---

## Bug 3: Paid Users Treated as Free

### Root Cause

The original code determined plan type solely from `user_subscriptions` table. When:
- Stripe webhook was delayed (billing gap between cycles)
- Supabase query failed transiently (network timeout)
- `is_active` was not yet set by webhook
...the code would default to `free_trial`, immediately downgrading paid users.

### Current Status: FIXED (Multi-Layer Defense)

The fix was implemented across multiple commits (primarily `624fe41` and subsequent STORY-203 work). The current `quota.py` implements a 4-layer lookup in `check_quota()` (lines 563-655):

**Layer 1** (lines 583-607): Active subscription in `user_subscriptions`
```python
sb.table("user_subscriptions").select("id, plan_id, expires_at")
  .eq("user_id", user_id).eq("is_active", True)
```

**Layer 2** (lines 609-638): Grace period for recently-expired subscriptions
```python
SUBSCRIPTION_GRACE_DAYS = 3  # line 503
grace_cutoff = datetime.now(timezone.utc) - timedelta(days=SUBSCRIPTION_GRACE_DAYS)
sb.table("user_subscriptions").select(...).gte("expires_at", grace_cutoff)
```

**Layer 3** (lines 640-649): Profile-based fallback (`profiles.plan_type`)
```python
profile_plan = get_plan_from_profile(user_id, sb)
if profile_plan and profile_plan != "free_trial":
    plan_id = profile_plan  # Use last known paid plan
```

**Layer 4** (lines 650-654): Free trial (absolute last resort, only for truly new users)

**Additional Defenses:**

- `routes/billing.py` `_activate_plan()` line 112: Syncs `profiles.plan_type` on plan activation
- `webhooks/stripe.py` lines 198-200: Syncs `profiles.plan_type` on subscription.updated
- `webhooks/stripe.py` line 245: Syncs `profiles.plan_type` on subscription.deleted
- `webhooks/stripe.py` line 301: Syncs `profiles.plan_type` on invoice.payment_succeeded
- `frontend/hooks/usePlan.ts` lines 83-111: localStorage cache (1hr TTL) prevents UI downgrade
- `routes/search.py` lines 384-405: Fallback uses `get_plan_from_profile()` instead of hardcoding `free_trial`

### Evidence from Code

- `backend/quota.py` lines 506-556: `get_plan_from_profile()` with legacy value mapping
- `backend/quota.py` line 503: `SUBSCRIPTION_GRACE_DAYS = 3`
- `backend/webhooks/stripe.py` lines 198-200, 245, 301: All 3 webhook handlers sync `profiles.plan_type`
- `frontend/hooks/usePlan.ts` lines 83-106: Client-side localStorage cache for paid plan protection

### Remaining Risk

The `routes/features.py` `fetch_features_from_db()` (lines 86-110) does NOT use the multi-layer fallback. It falls back directly to `free_trial` if no active subscription is found:

```python
if not sub_result.data or len(sub_result.data) == 0:
    return UserFeaturesResponse(features=[], plan_id="free_trial", ...)
```

This means the `/api/features/me` endpoint (used by frontend for feature gating) can still return `free_trial` for paid users during transient DB errors, even though `/buscar` correctly identifies them as paid. This creates an inconsistency where a user can search (correctly) but may see feature-gated UI elements locked.

### Regression Test Needed

Tests exist in `test_quota.py` for plan capabilities but **no test covers the 4-layer fallback logic**. Missing tests:

1. Layer 1 failure falls to Layer 2 (grace period)
2. Layer 2 failure falls to Layer 3 (profile fallback)
3. Layer 3 failure falls to Layer 4 (free_trial)
4. All Stripe webhook handlers sync `profiles.plan_type`
5. `features.py` should use multi-layer fallback (currently does not -- this is a latent bug)
6. Frontend localStorage cache prevents transient downgrade

---

## Bug 4: "Login" Button Visible to Logged-in Users

### Root Cause

The application has two distinct navigation patterns:

1. **Landing page** (`/`) uses `LandingNavbar.tsx` which **always** shows Login/Criar conta buttons
2. **Protected pages** (`(protected)/layout.tsx`) use `AppHeader.tsx` which shows `UserMenu` (avatar)
3. **Search page** (`/buscar/page.tsx`) has its **own inline header** with `UserMenu`

The "Login button visible to logged-in users" bug occurred because:
- The landing page (`/`) ALWAYS shows Login/Criar conta regardless of auth state
- This is **architecturally intentional** -- the landing page is public marketing content
- The bug was likely reported when users navigated to `/` while logged in and saw the Login button

### Current Status: FIXED (by design)

The `LandingNavbar.tsx` (lines 72-84) unconditionally renders Login/Criar conta links:

```tsx
<Link href="/login" ...>Login</Link>
<Link href="/signup?source=landing-cta" ...>Criar conta</Link>
```

The `UserMenu.tsx` (lines 27-48) correctly handles auth state:
```tsx
if (loading) return null;
if (!user) {
  return (/* Entrar + Criar conta buttons */);
}
// ... shows avatar/dropdown for logged-in users
```

The `AppHeader.tsx` (used by `(protected)/layout.tsx`) always shows `UserMenu`, which is correct since protected pages require auth.

### Evidence from Code

- `frontend/app/page.tsx`: Landing page imports `LandingNavbar`, not `AppHeader`
- `frontend/app/components/landing/LandingNavbar.tsx` lines 72-84: Static Login/Criar conta links
- `frontend/app/(protected)/layout.tsx` lines 24-30: Auth guard redirects to `/` if not logged in
- `frontend/app/components/UserMenu.tsx` lines 27-48: Conditional rendering based on auth state
- `frontend/app/buscar/page.tsx` lines 90-122: Inline header with `UserMenu`

### Remaining Risk

The `LandingNavbar.tsx` does not check auth state. If a logged-in user navigates to `/`, they see "Login" and "Criar conta" buttons. This is a **UX issue**, not a functional bug. Best practice would be to show the user's avatar or a "Dashboard" CTA instead.

### Regression Test Needed

**YES -- MISSING**. No frontend test verifies:

1. `LandingNavbar` shows Login/Criar conta when not authenticated
2. `LandingNavbar` behavior when user IS authenticated (currently shows Login anyway)
3. `UserMenu` shows Entrar/Criar conta when `user` is null
4. `UserMenu` shows avatar when `user` is present
5. `AppHeader` renders `UserMenu` on protected pages
6. `(protected)/layout.tsx` redirects to `/` when not authenticated

---

## Bug 5: Search History Not Saved

### Root Cause

Search history saving is implemented in `routes/search.py` via the `save_search_session()` function from `quota.py`. The save happens at two points:

1. **Zero results path** (lines 910-932): Saves session even for empty results
2. **Results path** (lines 1057-1080): Saves session after successful search

The `save_search_session()` function in `quota.py` (lines 809-859) inserts into the `search_sessions` table.

The original bug was likely caused by one of:
- **Missing profile** (FK constraint): The insert fails if the user has no profile row. Fixed by `_ensure_profile_exists()` (quota.py lines 774-806)
- **Silent failure**: The save is wrapped in try/except (search.py lines 1075-1080) and NEVER propagates errors to the user:
  ```python
  except Exception as e:
      logger.error(f"Failed to save search session...")
  ```
  This means history could silently fail to save without the user knowing.

### Current Status: FIXED (with caveats)

The `_ensure_profile_exists()` function (quota.py lines 774-806) creates a profile if one doesn't exist:

```python
def _ensure_profile_exists(user_id: str, sb) -> bool:
    result = sb.table("profiles").select("id").eq("id", user_id).execute()
    if result.data and len(result.data) > 0:
        return True
    # Create minimal profile
    sb.table("profiles").insert({...}).execute()
```

The `save_search_session()` function calls this before inserting:
```python
if not _ensure_profile_exists(user_id, sb):
    raise RuntimeError(f"Cannot save session: profile missing...")
```

The retrieval is handled by `routes/sessions.py` `get_sessions()` endpoint, which queries `search_sessions` directly.

### Evidence from Code

- `backend/routes/search.py` lines 910-932: Zero-results history save
- `backend/routes/search.py` lines 1057-1080: Normal results history save
- `backend/quota.py` lines 809-859: `save_search_session()` implementation
- `backend/quota.py` lines 774-806: `_ensure_profile_exists()` safety net
- `backend/routes/sessions.py` lines 16-40: History retrieval endpoint

### Remaining Risk

1. **Silent failures**: If the DB insert fails after profile exists, the error is logged but swallowed. The user gets their search results but history is not saved. No retry mechanism exists.
2. **No frontend indicator**: The frontend does not show whether history was saved successfully.
3. **Race condition**: Two concurrent searches by the same user could both try to `_ensure_profile_exists()` simultaneously, potentially causing a unique constraint violation on the second insert.

### Regression Test Needed

**YES -- MISSING**. No tests exist for:

1. `save_search_session()` with valid data
2. `save_search_session()` when profile doesn't exist (triggers `_ensure_profile_exists`)
3. `save_search_session()` DB failure (should log error, not crash search)
4. GET `/sessions` returns correct history data
5. History saved for zero-result searches
6. Concurrent profile creation race condition

---

## Bug 6: Inconsistent Quota Consumption

### Root Cause

The original code had a classic TOCTOU (time-of-check-to-time-of-use) race condition:

```python
# OLD PATTERN (vulnerable):
current = get_monthly_quota_used(user_id)     # CHECK
if current >= max_quota:
    raise QuotaExceeded
increment_monthly_quota(user_id)               # USE (increment)
# Between CHECK and USE, another request could also pass the check
```

This allowed concurrent requests to exceed the quota limit because multiple requests could read the same `searches_count`, all pass the check, and all increment.

### Current Status: FIXED (with fallback)

The fix uses a PostgreSQL RPC function for atomic check-and-increment (Issue #189). In `routes/search.py` (lines 359-369):

```python
allowed, new_quota_used, quota_remaining_after = check_and_increment_quota_atomic(
    user["id"],
    quota_info.capabilities["max_requests_per_month"]
)
```

The `check_and_increment_quota_atomic()` function in `quota.py` (lines 435-495) uses:

```python
result = sb.rpc(
    "check_and_increment_quota",
    {"p_user_id": user_id, "p_month_year": month_key, "p_max_quota": max_quota}
).execute()
```

This is a single PostgreSQL transaction that atomically checks AND increments, eliminating the race window.

**Fallback path** (lines 487-495): If the RPC function doesn't exist, falls back to non-atomic check + increment with `asyncio.Lock` per-user (quota.py line 35: `_quota_locks: dict[str, asyncio.Lock] = {}`). However, this fallback is only per-process and would not protect against multi-instance race conditions.

### Evidence from Code

- `backend/quota.py` lines 435-495: `check_and_increment_quota_atomic()` with RPC call
- `backend/quota.py` lines 343-432: `increment_monthly_quota()` with RPC + upsert fallback
- `backend/quota.py` lines 35-47: Per-user `asyncio.Lock` for in-process synchronization
- `backend/routes/search.py` lines 345-369: Atomic quota check happens BEFORE search execution

### Remaining Risk

1. **Fallback path is not truly atomic**: The upsert fallback (quota.py lines 407-422) does `current = get_monthly_quota_used()` then `sb.table("monthly_quota").upsert({searches_count: current + 1})`. This is NOT atomic -- two concurrent requests can read the same `current` value.
2. **No lock in fallback**: The `_quota_locks` dictionary is defined but NEVER used in the actual `increment_monthly_quota()` or `check_and_increment_quota_atomic()` functions. The lock acquisition code is missing.
3. **Multi-instance vulnerability**: `asyncio.Lock` only protects within a single process. If multiple Railway instances serve the same user, the lock provides no protection.

### Regression Test Needed

Tests exist in `test_quota_race_condition.py` but only cover:
- Unit test for RPC call pattern
- Fallback when RPC doesn't exist

**Missing tests:**
1. Concurrent quota consumption stress test (multiple async tasks)
2. Fallback path race condition verification
3. `_quota_locks` are actually used (currently they are NOT used -- dead code)
4. Multi-instance race condition scenario (requires integration test)
5. Atomic function returns correct `(allowed, new_count, remaining)` tuple

---

## Bug 7: Incorrect Header State on /buscar

### Root Cause

The `/buscar` page (`frontend/app/buscar/page.tsx`) does NOT use the `(protected)/layout.tsx` layout. It has its own inline header (lines 90-122) with its own auth check (line 33):

```tsx
const { session, loading: authLoading } = useAuth();
```

However, the page is NOT inside the `(protected)` route group. This means:
- No automatic auth redirect (unlike pages in `(protected)/`)
- The page relies on `authLoading` state to show a spinner
- If `authLoading` is slow or gets stuck, the header may flash incorrect state

The `AuthProvider.tsx` has a 10-second timeout (line 56-59):
```tsx
const authTimeout = setTimeout(() => {
  console.warn("[AuthProvider] Auth check timeout - forcing loading=false");
  setLoading(false);
}, 10000);
```

If auth check times out, `loading` becomes `false` but `session` is `null`, causing the `UserMenu` to show "Entrar" buttons briefly even for a logged-in user.

### Current Status: ARCHITECTURE RISK (not a direct bug)

The current implementation works correctly in the happy path:
1. `authLoading` is true -> spinner shown
2. `getUser()` resolves -> `user` and `session` set
3. `UserMenu` renders avatar for logged-in users

The timeout (10s) handles the edge case where `getUser()` hangs. This was added in commit `74cd025` ("fix auth loading loop").

### Evidence from Code

- `frontend/app/buscar/page.tsx` lines 32-33: Uses `useAuth()` directly (not protected layout)
- `frontend/app/buscar/page.tsx` lines 76-85: Shows spinner while `authLoading` is true
- `frontend/app/buscar/page.tsx` lines 90-122: Inline header with UserMenu
- `frontend/app/components/AuthProvider.tsx` lines 56-59: 10-second auth timeout
- `frontend/app/components/AuthProvider.tsx` lines 63-67: `getUser()` then `getSession()` sequencing
- `frontend/app/(protected)/layout.tsx`: Separate auth guard that /buscar does NOT use

### Remaining Risk

1. **No redirect for unauthenticated users on /buscar**: If a user navigates directly to `/buscar` without being logged in, they see the page (with Entrar button) rather than being redirected. The `(protected)` layout has this redirect but `/buscar` does not use it.
2. **Stale session state**: The `usePlan` hook (usePlan.ts) depends on `session?.access_token`. If the session object is populated before the user object (due to `getUser()` -> `getSession()` ordering in AuthProvider), there could be a brief window where `usePlan` fetches with a valid token but `user` is still null.
3. **Missing auth redirect**: There is no explicit redirect on `/buscar` if the user is not authenticated. The `require_auth` backend dependency will reject the search, but the page renders.

### Regression Test Needed

**YES -- MISSING**. No frontend test covers:

1. `/buscar` page shows spinner during auth loading
2. `/buscar` page shows correct header state after auth resolves
3. `/buscar` page behavior when auth times out (10s)
4. `/buscar` page behavior for unauthenticated users
5. `UserMenu` transitions from loading to authenticated state

---

## Cross-Bug Patterns

### Pattern 1: Stale Test Suite

**Severity: CRITICAL**

The auth test suite (`test_auth.py` + `test_auth_cache.py`) is entirely stale. All 29 tests mock an API that is no longer called. This provides false confidence. The same pattern could exist in other test files.

**Action:** Audit ALL test files for mocks that target deprecated code paths.

### Pattern 2: Silent Failure Anti-Pattern

**Severity: HIGH**

Multiple systems catch exceptions and silently continue:
- Search history save (search.py line 1075-1080): `except Exception: logger.error(...)`
- Quota fallback (search.py line 383-405): Falls back to profile on any exception
- Feature flags (features.py line 86-110): Falls back to `free_trial` on any error
- Admin check (authorization.py line 84-93): Falls back to non-admin after 2 retries

While this improves resilience, it makes debugging production issues very difficult because errors are swallowed. Consider adding error counters or metrics.

### Pattern 3: Multiple Sources of Truth for User Plan

**Severity: MEDIUM**

User plan information comes from at least 4 sources:
1. `user_subscriptions` table (primary)
2. `profiles.plan_type` column (fallback)
3. Frontend localStorage cache (1hr TTL)
4. Redis features cache (5min TTL)

These can diverge, causing inconsistent behavior across different UI elements and API endpoints. The `/buscar` endpoint uses the 4-layer lookup but `/api/features/me` only checks `user_subscriptions`.

### Pattern 4: Lack of Frontend Auth Integration Tests

**Severity: MEDIUM**

No frontend tests verify the auth flow end-to-end:
- AuthProvider initialization
- Session persistence across page loads
- Auth state propagation to child components
- Redirect behavior on protected pages
- Auth timeout handling

### Pattern 5: Request Correlation Only Partially Implemented

**Severity: LOW**

The `CorrelationIDMiddleware` generates `request_id` for HTTP requests, but:
- Background tasks (Stripe webhooks) don't get correlation IDs
- The SSE progress stream doesn't propagate the parent request's correlation ID
- Database operations don't include the correlation ID

---

## Proposed Stories

### STORY-XXX: Rewrite Auth Test Suite for JWT Validation

**Context:** Backend auth was rewritten from Supabase API to local JWT validation on 2026-02-11 (commit `8c8c19d`), but the test suite still mocks the old API.

**Problem:** 29 auth tests provide zero coverage of the production code path. Tests pass but cover dead code.

**Impact:** Any regression in JWT validation (algorithm mismatch, missing secret, claim extraction) will NOT be caught by tests. This is the exact bug pattern that caused the original P0 outage.

**Acceptance Criteria:**
- [ ] AC1: All tests in `test_auth.py` mock `jwt.decode()` and `os.getenv("SUPABASE_JWT_SECRET")` instead of `sb.auth.get_user()`
- [ ] AC2: All tests in `test_auth_cache.py` use `hashlib.sha256()` for cache key assertions (not `hash()`)
- [ ] AC3: Test coverage for: valid JWT, expired JWT, invalid JWT, missing secret, missing sub claim, missing email fallback
- [ ] AC4: Test coverage for Google OAuth JWT tokens (same HS256 algorithm)
- [ ] AC5: Integration test with real JWT creation using PyJWT
- [ ] AC6: No test mocks `supabase_client.get_supabase` in auth context (this API is no longer used)

**Validation Metric:** `pytest tests/test_auth.py tests/test_auth_cache.py --cov=auth --cov-report=term-missing` shows >90% coverage of `auth.py` lines 72-137.

**Risk Mitigated:** P0 -- Authenticated users cannot access the application due to undetected JWT validation regression.

---

### STORY-XXX: Add Logging Cascade Regression Tests

**Context:** Logging cascade failure (Bug 1) was fixed by adding `RequestIDFilter`, but no test verifies the filter works correctly.

**Problem:** If `middleware.py` breaks or `setup_logging()` changes, ALL logging will silently fail.

**Acceptance Criteria:**
- [ ] AC1: Test that `RequestIDFilter` injects `request_id="-"` for startup logs (no request context)
- [ ] AC2: Test that `RequestIDFilter` injects actual request ID during HTTP request
- [ ] AC3: Test that `setup_logging()` succeeds even if `middleware.py` import fails (graceful degradation)
- [ ] AC4: Test that module-level logging (config.py feature flags) works without crash

**Validation Metric:** `pytest tests/test_middleware.py --cov=middleware --cov-report=term-missing` shows >95% coverage.

**Risk Mitigated:** P1 -- All application logging breaks, masking real errors.

---

### STORY-XXX: Align /api/features/me with Multi-Layer Plan Fallback

**Context:** The `/buscar` endpoint uses a 4-layer fallback (subscription -> grace period -> profile -> free_trial), but `/api/features/me` only checks `user_subscriptions` and falls back directly to `free_trial`.

**Problem:** Paid users may see feature-locked UI (Excel export disabled, limited history) while being able to search successfully. Inconsistent experience.

**Acceptance Criteria:**
- [ ] AC1: `fetch_features_from_db()` uses `get_plan_from_profile()` fallback before defaulting to `free_trial`
- [ ] AC2: Grace period is respected in features endpoint
- [ ] AC3: Test covers: active subscription, grace period, profile fallback, free_trial default
- [ ] AC4: Frontend `usePlan` cache prevents transient feature downgrade (already implemented)

**Validation Metric:** No paid user should see `free_trial` features when their `profiles.plan_type` indicates a paid plan.

**Risk Mitigated:** P2 -- Paid users see degraded UI during transient backend issues.

---

### STORY-XXX: LandingNavbar Auth-Aware CTA

**Context:** The landing page always shows "Login" and "Criar conta" even for logged-in users (Bug 4).

**Problem:** Logged-in users navigating to `/` see login buttons, which is confusing.

**Acceptance Criteria:**
- [ ] AC1: `LandingNavbar` checks auth state via `useAuth()`
- [ ] AC2: If user is logged in, show "Dashboard" button instead of Login/Criar conta
- [ ] AC3: If user is not logged in, show Login/Criar conta (existing behavior)
- [ ] AC4: No layout shift during auth loading state

**Validation Metric:** Manual test -- logged-in user navigating to `/` sees "Dashboard" CTA.

**Risk Mitigated:** P3 -- UX confusion for returning users.

---

### STORY-XXX: Fix Dead Code in Quota Locking

**Context:** `_quota_locks` dictionary (quota.py line 35) and `_get_user_lock()` function (lines 43-47) are defined but NEVER called.

**Problem:** The per-user locking mechanism intended as fallback for multi-process synchronization is dead code. If the RPC function is unavailable, the fallback path has no locking.

**Acceptance Criteria:**
- [ ] AC1: `increment_monthly_quota()` acquires per-user lock in the fallback (non-RPC) path
- [ ] AC2: `check_and_increment_quota_atomic()` uses lock in fallback path
- [ ] AC3: Tests verify lock is acquired during fallback
- [ ] AC4: OR remove dead code if locking is not needed (RPC is always available in production)

**Validation Metric:** `grep -n "_quota_locks\|_get_user_lock" backend/quota.py` shows locks are either used in fallback or removed.

**Risk Mitigated:** P2 -- Quota bypass under concurrent requests when RPC is unavailable.

---

### STORY-XXX: Search History Reliability

**Context:** Search history save is wrapped in silent try/except (Bug 5). Failed saves are logged but never retried or reported to users.

**Problem:** Users may lose search history without knowing it. No monitoring for history save failures.

**Acceptance Criteria:**
- [ ] AC1: Add structured metric for history save success/failure rate
- [ ] AC2: Add retry (max 1) for transient DB errors on history save
- [ ] AC3: Frontend shows toast notification if history save fails (optional, low priority)
- [ ] AC4: Tests for `save_search_session()` with DB success, DB failure, profile creation

**Validation Metric:** History save success rate visible in application logs or monitoring.

**Risk Mitigated:** P3 -- Silent data loss in search history.
