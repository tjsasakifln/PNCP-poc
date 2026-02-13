# STORY-214: Rewrite Stale Auth Test Suite for JWT Validation

**Status:** Done
**Priority:** P0 — Blocks GTM Launch (Test Safety)
**Sprint:** Sprint 2 (Weeks 2-3)
**Estimated Effort:** 2 days
**Completed:** 2026-02-13
**Source:** AUDIT-FRENTE-5-HISTORICAL-BUGS (Bug-2, Pattern-1), AUDIT-FRENTE-3-TESTS, AUDIT-CONSOLIDATED (QA-03)
**Squad:** team-bidiq-backend (dev, qa)

---

## Context

**This is the most dangerous finding of the entire audit.**

Backend auth was rewritten from Supabase API validation (`sb.auth.get_user()`) to local JWT validation (`jwt.decode()`) on 2026-02-11 (commit `8c8c19d`). However, **all 29 auth tests still mock the old API**:

```python
# test_auth.py line 59 — STALE:
mock_supabase.auth.get_user.return_value = mock_user_response

# ACTUAL production code uses:
payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
```

These 29 tests pass but cover **zero lines of production code**. They provide false confidence while the actual JWT validation path has no tests. This is the exact bug pattern that caused the original P0 JWT outage.

Additionally, `test_auth_cache.py` uses `hash()` (Python built-in) for cache key assertions, but actual code now uses `hashlib.sha256()`.

## Acceptance Criteria

### Rewrite test_auth.py (17 → 42 tests)

- [x] AC1: All tests mock `jwt.decode()` and `os.getenv("SUPABASE_JWT_SECRET")` instead of `sb.auth.get_user()`
- [x] AC2: Test: Valid HS256 JWT decoded successfully — returns correct `user_id`, `email`, `role`
- [x] AC3: Test: Expired JWT raises 401 with "Token expirado"
- [x] AC4: Test: Invalid/malformed JWT raises 401 with "Token invalido"
- [x] AC5: Test: Missing `SUPABASE_JWT_SECRET` env var raises 500
- [x] AC6: Test: JWT without `sub` claim raises 401
- [x] AC7: Test: JWT with missing `email` defaults to "unknown"
- [x] AC8: Test: JWT with `role` = "authenticated" (normal user)
- [x] AC9: Test: JWT with `role` = "service_role" (service accounts)
- [x] AC10: Integration test with real JWT creation using PyJWT library

### Rewrite test_auth_cache.py (12 → 23 tests)

- [x] AC11: Cache key assertions use `hashlib.sha256(full_token.encode()).hexdigest()` (not `hash()` or `token[:16]`)
- [x] AC12: Test: Same token returns cached result within TTL
- [x] AC13: Test: Different tokens produce different cache entries (no collision)
- [x] AC14: Test: Cache expires after TTL (60s)
- [x] AC15: Test: Failed auth is NOT cached (only successful validations)
- [x] AC16: Test: Concurrent requests for same token — only one `jwt.decode()` call

### Cleanup

- [x] AC17: No test mocks `supabase_client.get_supabase` in auth context (this API is no longer used for auth)
- [x] AC18: Remove any references to `sb.auth.get_user()` in test files

### Coverage Gate

- [x] AC19: `pytest tests/test_auth.py tests/test_auth_cache.py --cov=auth --cov-report=term-missing` shows >90% coverage of `auth.py` lines 72-137
- [x] AC20: All 65 rewritten tests pass (expanded from original 29)

## Validation Results (2026-02-13)

```
65 passed in 2.97s
auth.py: 66 statements, 12 branches, 0 miss → 100.00% coverage
Zero mocks of supabase_client.get_supabase in test_auth.py (0 matches)
Zero mocks of supabase_client.get_supabase in test_auth_cache.py (0 matches)
Zero uses of hash() or token[:16] in test_auth_cache.py (0 matches)
```

## Risk Mitigated

- P0: Undetected JWT validation regression (same bug pattern as original P0 outage)
- P0: False confidence from 29 passing-but-stale tests
- Test Safety Grade: Backend Auth A- → A+

## File References

| File | Lines | Change |
|------|-------|--------|
| `backend/tests/test_auth.py` | ALL | Complete rewrite — 42 tests mocking jwt.decode() |
| `backend/tests/test_auth_cache.py` | ALL | Complete rewrite — 23 tests using hashlib.sha256() |
| `backend/auth.py` | 72-137 | Target coverage area — 100% covered |
