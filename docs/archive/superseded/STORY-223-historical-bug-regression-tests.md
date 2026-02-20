# STORY-223: Historical Bug Regression Tests — Logging, Features Fallback, Quota Locks

**Status:** Done
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

- [x] AC1: Test that `RequestIDFilter` injects `request_id="-"` for startup logs (no request context)
- [x] AC2: Test that `RequestIDFilter` injects actual request ID during HTTP request
- [x] AC3: Test that `setup_logging()` succeeds even if `middleware.py` import fails (graceful degradation)
- [x] AC4: Test that module-level logging (`config.py` feature flags) works without crash
- [x] AC5: Test that `CorrelationIDMiddleware` propagates `X-Request-ID` header in response

### Bug 3: Align /api/features/me with Multi-Layer Plan Fallback

- [x] AC6: `routes/features.py:fetch_features_from_db()` uses `get_plan_from_profile()` fallback before defaulting to `free_trial`
- [x] AC7: Grace period (3 days) is respected in features endpoint
- [x] AC8: Test: active subscription → correct plan features
- [x] AC9: Test: expired subscription within grace → correct plan features (not free_trial)
- [x] AC10: Test: expired subscription + valid profile plan → profile plan features
- [x] AC11: Test: no subscription + no profile plan → free_trial

### Bug 5: Search History Reliability

- [x] AC12: Test: `save_search_session()` succeeds with valid data
- [x] AC13: Test: `save_search_session()` when profile doesn't exist (triggers `_ensure_profile_exists`)
- [x] AC14: Test: `save_search_session()` DB failure → error logged, search result still returned
- [x] AC15: Test: History saved for zero-result searches
- [x] AC16: Add retry (max 1) for transient DB errors on history save

### Bug 6: Fix Dead Quota Locks

- [x] AC17: Dead code removed — `_quota_locks` dict and `_get_user_lock()` function deleted from quota.py
- [x] AC18: N/A — locks removed (option: remove dead code)
- [x] AC19: Verified `_quota_locks` and `_get_user_lock()` are completely removed from codebase
- [x] AC20: Test: fallback path (no RPC) correctly increments quota without race conditions (within single process)

### Bug 4: LandingNavbar Auth-Aware CTA (Optional UX Fix)

- [x] AC21: `LandingNavbar` checks auth state via `useAuth()`
- [x] AC22: Logged-in user on `/` sees "Ir para Busca" button instead of Login/Criar conta
- [x] AC23: Not-logged-in user on `/` sees Login/Criar conta (existing behavior)
- [x] AC24: No layout shift during auth loading state (placeholder div render)

### Bug 7: /buscar Header Regression Test

- [x] AC25: Frontend test: `/buscar` page shows spinner during auth loading
- [x] AC26: Frontend test: `/buscar` page shows correct header (UserMenu with avatar) after auth resolves
- [x] AC27: Frontend test: `/buscar` page shows Entrar button when not authenticated

## Validation Metric

- [x] Each historical bug (1-7) has at least one regression test
- [x] `routes/features.py` uses multi-layer fallback (matching `/buscar` behavior)
- [x] Zero dead code in `quota.py` (locks removed)

## Cross-Validation Results (2026-02-13)

| Suite | Result | Baseline | Regression? |
|-------|--------|----------|-------------|
| Backend | 1846 passed, 2 failed, 55 skipped | 2 pre-existing failures | NO |
| Frontend | 1220 passed, 4 failed | 4 pre-existing failures (download.test.ts) | NO |
| STORY-223 Backend | 74/74 passed | N/A (new) | N/A |
| STORY-223 Frontend | 21/21 passed | N/A (new) | N/A |

**Total new tests added: 95** (74 backend + 21 frontend)

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
