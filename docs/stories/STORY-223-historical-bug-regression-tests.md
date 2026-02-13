# STORY-223: Historical Bug Regression Tests — Logging, Features Fallback, Quota Locks

**Status:** Pending
**Priority:** P2 — Fix Before Paid Scale
**Sprint:** Sprint 3 (Weeks 4-5)
**Estimated Effort:** 3 days
**Source:** AUDIT-FRENTE-5-HISTORICAL-BUGS (Bugs 1, 3, 5, 6), AUDIT-CONSOLIDATED
**Squad:** team-bidiq-backend (dev, qa)

---

## Context

The historical bugs audit reviewed 7 production bugs. While all were fixed, **5 of 7 lack regression tests**. Additionally, three cross-cutting patterns were identified: silent failure anti-pattern, multiple sources of truth for user plan, and dead code.

## Acceptance Criteria

### Bug 1: Logging Cascade Regression Tests

- [ ] AC1: Test that `RequestIDFilter` injects `request_id="-"` for startup logs (no request context)
- [ ] AC2: Test that `RequestIDFilter` injects actual request ID during HTTP request
- [ ] AC3: Test that `setup_logging()` succeeds even if `middleware.py` import fails (graceful degradation)
- [ ] AC4: Test that module-level logging (`config.py` feature flags) works without crash
- [ ] AC5: Test that `CorrelationIDMiddleware` propagates `X-Request-ID` header in response

### Bug 3: Align /api/features/me with Multi-Layer Plan Fallback

- [ ] AC6: `routes/features.py:fetch_features_from_db()` uses `get_plan_from_profile()` fallback before defaulting to `free_trial`
- [ ] AC7: Grace period (3 days) is respected in features endpoint
- [ ] AC8: Test: active subscription → correct plan features
- [ ] AC9: Test: expired subscription within grace → correct plan features (not free_trial)
- [ ] AC10: Test: expired subscription + valid profile plan → profile plan features
- [ ] AC11: Test: no subscription + no profile plan → free_trial

### Bug 5: Search History Reliability

- [ ] AC12: Test: `save_search_session()` succeeds with valid data
- [ ] AC13: Test: `save_search_session()` when profile doesn't exist (triggers `_ensure_profile_exists`)
- [ ] AC14: Test: `save_search_session()` DB failure → error logged, search result still returned
- [ ] AC15: Test: History saved for zero-result searches
- [ ] AC16: Add retry (max 1) for transient DB errors on history save

### Bug 6: Fix Dead Quota Locks

- [ ] AC17: Either **use** `_quota_locks` in the fallback (non-RPC) path of `check_and_increment_quota_atomic()` and `increment_monthly_quota()`, OR **remove** the dead code entirely
- [ ] AC18: If keeping locks: test that lock is acquired during fallback
- [ ] AC19: If removing locks: verify `_quota_locks` and `_get_user_lock()` are completely removed
- [ ] AC20: Test: fallback path (no RPC) correctly increments quota without race conditions (within single process)

### Bug 4: LandingNavbar Auth-Aware CTA (Optional UX Fix)

- [ ] AC21: `LandingNavbar` checks auth state via `useAuth()`
- [ ] AC22: Logged-in user on `/` sees "Ir para Busca" button instead of Login/Criar conta
- [ ] AC23: Not-logged-in user on `/` sees Login/Criar conta (existing behavior)
- [ ] AC24: No layout shift during auth loading state (skeleton or null render)

### Bug 7: /buscar Header Regression Test

- [ ] AC25: Frontend test: `/buscar` page shows spinner during auth loading
- [ ] AC26: Frontend test: `/buscar` page shows correct header (UserMenu with avatar) after auth resolves
- [ ] AC27: Frontend test: `/buscar` page shows Entrar button when not authenticated

## Validation Metric

- Each historical bug (1-7) has at least one regression test
- `routes/features.py` uses multi-layer fallback (matching `/buscar` behavior)
- Zero dead code in `quota.py` (locks used or removed)

## Risk Mitigated

- P2: Logging cascade re-occurrence
- P2: Paid users see degraded UI on features endpoint
- P2: Quota bypass when RPC unavailable
- P3: Silent search history loss
- P3: UX confusion for logged-in users on landing page

## File References

| File | Change |
|------|--------|
| `backend/tests/test_middleware.py` | NEW — logging cascade regression tests |
| `backend/routes/features.py` | Add multi-layer fallback |
| `backend/tests/test_features.py` | NEW — plan fallback tests |
| `backend/quota.py` | Fix or remove dead locks |
| `backend/tests/test_sessions.py` | NEW — history save tests |
| `frontend/app/components/landing/LandingNavbar.tsx` | Auth-aware CTA |
| `frontend/__tests__/components/LandingNavbar.test.tsx` | NEW |
| `frontend/__tests__/pages/BuscarHeader.test.tsx` | NEW — header state tests |
