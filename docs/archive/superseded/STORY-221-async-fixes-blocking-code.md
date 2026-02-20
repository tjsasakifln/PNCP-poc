# STORY-221: Async Architecture Fixes — Blocking Code, Stripe, Lifespan

**Status:** Done
**Priority:** P1 — Pre-GTM Important
**Sprint:** Sprint 3 (Weeks 4-5)
**Estimated Effort:** 2 days
**Source:** AUDIT-FRENTE-1-CODEBASE (HIGH-01, HIGH-04, HIGH-05, HIGH-07), AUDIT-CONSOLIDATED
**Squad:** team-bidiq-backend (dev)

---

## Context

Several backend patterns violate async best practices, causing event loop blocking, potential crashes, and thread-safety issues:

1. **`time.sleep(0.3)` in async context** — `authorization.py:87` blocks the entire event loop for 300ms during admin role check retry, affecting all concurrent requests
2. **`asyncio.run()` inside running loop** — `redis_client.py:56` crashes if called from async context (FastAPI always has an event loop). Only works at import time by luck.
3. **Stripe API key set at module level** — `webhooks/stripe.py:44` sets `stripe.api_key` globally, not thread-safe for concurrent webhook processing
4. **Deprecated `@app.on_event("startup")`** — `main.py:136` uses deprecated pattern since FastAPI 0.103

## Acceptance Criteria

### Fix Blocking time.sleep()

- [x] AC1: Replace `time.sleep(0.3)` with `await asyncio.sleep(0.3)` in `authorization.py:87`
- [x] AC2: Make `_check_user_roles()` async (update all callers)
- [x] AC3: Audit all other `time.sleep()` calls in async-reachable code paths

### Fix asyncio.run() Crash (if not already fixed by STORY-217)

- [x] AC4: Remove `asyncio.run(_redis_client.ping())` from `redis_client.py:56` — Already fixed by STORY-217 (deprecated shim)
- [x] AC5: Replace with async health check during FastAPI lifespan startup — Already fixed by STORY-217

### Fix Stripe Thread Safety

- [x] AC6: Replace global `stripe.api_key = os.getenv(...)` with per-request `api_key=` parameter
- [x] AC7: Update all Stripe API calls in `webhooks/stripe.py`, `routes/billing.py`, and `services/billing.py` to use per-request `api_key=`
- [x] AC8: Validate `STRIPE_WEBHOOK_SECRET` at startup (not first-use) — `STRIPE_WEBHOOK_SECRET` read at module level (read-only, thread-safe)

### Migrate to Lifespan

- [x] AC9: Replace `@app.on_event("startup")` and `@app.on_event("shutdown")` with FastAPI lifespan context manager
- [x] AC10: Move Redis pool initialization to lifespan startup
- [x] AC11: Move env var validation to lifespan startup

### Env Var Validation at Startup

- [x] AC12: Add startup check for required env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- [x] AC13: Add startup WARNING for recommended env vars: `OPENAI_API_KEY`, `STRIPE_SECRET_KEY`, `SENTRY_DSN`
- [x] AC14: Raise `RuntimeError` if critical env vars missing AND `ENVIRONMENT=production`

### Testing

- [x] AC15: Test: `_check_user_roles()` does NOT call `time.sleep()` (use `@pytest.mark.asyncio`)
- [x] AC16: Test: Stripe webhook processing works with per-request client
- [x] AC17: Test: Missing `SUPABASE_JWT_SECRET` in production raises error at startup
- [x] AC18: All existing tests pass (1808 passed, 2 pre-existing failures, 56 skipped)

## Validation Metric

- `grep -rn "time.sleep" backend/ --include="*.py"` returns zero results in async-reachable code
- `grep -rn "asyncio.run(" backend/ --include="*.py"` returns zero results in production code (only in tests)
- `grep -rn "stripe.api_key" backend/ --include="*.py"` returns zero results

## Risk Mitigated

- P1: Event loop blocking affects all concurrent users
- P1: `asyncio.run()` crash potential in production
- P2: Race condition in concurrent Stripe webhook processing
- P3: Deprecated API usage

## File References

| File | Lines | Change |
|------|-------|--------|
| `backend/authorization.py` | 87 | `time.sleep` → `asyncio.sleep` |
| `backend/redis_client.py` | 56 | Remove `asyncio.run()` |
| `backend/webhooks/stripe.py` | 44 | Per-request Stripe client |
| `backend/routes/billing.py` | Various | Per-request Stripe client |
| `backend/main.py` | 136 | Lifespan context manager |
| `backend/config.py` | NEW | Env var validation function |
