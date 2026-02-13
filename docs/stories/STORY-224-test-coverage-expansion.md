# STORY-224: Test Coverage Expansion — SSE, OAuth, Middleware, Routes

**Status:** Pending
**Priority:** P2 — Fix Before Paid Scale
**Sprint:** Sprint 3 (Weeks 4-5)
**Estimated Effort:** 5 days
**Source:** AUDIT-FRENTE-3-TESTS (C2-C5, H6, QA-07, QA-08), AUDIT-CONSOLIDATED
**Squad:** team-bidiq-backend + team-bidiq-frontend (qa, dev)

---

## Context

The test audit identified 11 backend modules with zero test coverage and critical coverage gaps in security, SSE, and OAuth code. The backend core (filter, PNCP, Excel) has Grade A coverage, but the surrounding infrastructure has Grade D.

**Zero test coverage:**
- `middleware.py` (correlation IDs, request logging) — security-critical
- `authorization.py` (role checks, admin guard) — security-critical
- SSE progress tracking (`progress.py`) — complex async code
- Google OAuth E2E (`auth_oauth.py`, `oauth.py`) — primary login method
- Lead prospecting (5 modules, 500+ LOC)
- 6 of 12 backend route modules have no test files

## Acceptance Criteria

### Track 1: SSE Progress Tests (1 day)

- [ ] AC1: Test `ProgressTracker` creates queue and tracks progress correctly
- [ ] AC2: Test `update_progress()` sends correct SSE event format
- [ ] AC3: Test `get_progress_stream()` yields events as Server-Sent Events
- [ ] AC4: Test cleanup: tracker removed after search completes
- [ ] AC5: Test timeout: stale trackers cleaned up after TTL
- [ ] AC6: Test concurrent searches create independent trackers
- [ ] AC7: Test SSE reconnection handles missing tracker gracefully

### Track 2: Google OAuth Tests (1 day)

- [ ] AC8: Test `initiate_google_oauth()` generates correct authorization URL
- [ ] AC9: Test OAuth state parameter includes nonce (after STORY-210 fix)
- [ ] AC10: Test `complete_google_oauth()` exchanges code for tokens
- [ ] AC11: Test OAuth callback rejects invalid state parameter
- [ ] AC12: Test token encryption with ENCRYPTION_KEY (not fallback)
- [ ] AC13: Test token decryption retrieves original tokens

### Track 3: Middleware & Authorization Tests (1 day)

- [ ] AC14: Test `CorrelationIDMiddleware` generates UUID for requests without `X-Request-ID`
- [ ] AC15: Test `CorrelationIDMiddleware` passes through existing `X-Request-ID`
- [ ] AC16: Test `CorrelationIDMiddleware` logs request summary with correct format
- [ ] AC17: Test `require_auth` dependency rejects missing token (401)
- [ ] AC18: Test `require_auth` dependency rejects expired token (401)
- [ ] AC19: Test `require_admin` dependency rejects non-admin users (403)
- [ ] AC20: Test `require_admin` accepts users in `ADMIN_USER_IDS` env var
- [ ] AC21: Test `_check_user_roles()` retry logic (1 retry, 0.3s delay)

### Track 4: Route Module Coverage (2 days)

- [ ] AC22: `backend/tests/test_routes_sessions.py` — GET sessions, empty history, pagination
- [ ] AC23: `backend/tests/test_routes_analytics.py` — summary, timeseries, export
- [ ] AC24: `backend/tests/test_routes_messages.py` — send message, list messages, categories
- [ ] AC25: `backend/tests/test_routes_subscriptions.py` — list subscriptions, cancel, billing period
- [ ] AC26: `backend/tests/test_routes_features.py` — get features, plan mapping, cache behavior
- [ ] AC27: `backend/tests/test_routes_plans.py` — list plans, plan detail

### Track 5: Lead Prospecting Tests (if applicable)

- [ ] AC28: Test lead extraction from search results
- [ ] AC29: Test lead deduplication logic
- [ ] AC30: Test lead scoring algorithm

### Coverage Gate

- [ ] AC31: Backend coverage remains ≥ 70% overall (currently 96.69%)
- [ ] AC32: Previously-untested modules have ≥ 60% individual coverage
- [ ] AC33: All new tests pass on CI

## Validation Metric

- Zero modules with zero test files (every `.py` module in `routes/` and core has a corresponding test)
- SSE progress tracking covered
- Middleware/authorization security code covered
- `pytest --cov --cov-report=term-missing` shows coverage for all route modules

## Risk Mitigated

- P2: Security bypass in authorization undetected by tests
- P2: SSE progress breaking silently
- P2: OAuth flow regression (primary login method)
- P3: Route-level regressions invisible

## File References

| File | Status |
|------|--------|
| `backend/tests/test_progress.py` | NEW — SSE tests |
| `backend/tests/test_oauth.py` | NEW — OAuth encryption tests |
| `backend/tests/test_middleware_integration.py` | NEW — correlation ID tests |
| `backend/tests/test_authorization.py` | NEW — role check tests |
| `backend/tests/test_routes_sessions.py` | NEW |
| `backend/tests/test_routes_analytics.py` | NEW |
| `backend/tests/test_routes_messages.py` | NEW |
| `backend/tests/test_routes_subscriptions.py` | NEW |
| `backend/tests/test_routes_features.py` | NEW |
| `backend/tests/test_routes_plans.py` | NEW |
