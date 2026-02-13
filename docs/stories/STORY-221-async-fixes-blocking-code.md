# STORY-221: Async Architecture Fixes — Blocking Code, Stripe, Lifespan

**Status:** Pending
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

- [ ] AC1: Replace `time.sleep(0.3)` with `await asyncio.sleep(0.3)` in `authorization.py:87`
- [ ] AC2: Make `_check_user_roles()` async (update all callers)
- [ ] AC3: Audit all other `time.sleep()` calls in async-reachable code paths

### Fix asyncio.run() Crash (if not already fixed by STORY-217)

- [ ] AC4: Remove `asyncio.run(_redis_client.ping())` from `redis_client.py:56`
- [ ] AC5: Replace with async health check during FastAPI lifespan startup

### Fix Stripe Thread Safety

- [ ] AC6: Replace global `stripe.api_key = os.getenv(...)` with per-request Stripe client:
  ```python
  import stripe
  client = stripe.StripeClient(os.getenv("STRIPE_SECRET_KEY"))
  ```
- [ ] AC7: Update all Stripe API calls in `webhooks/stripe.py` and `routes/billing.py` to use client instance
- [ ] AC8: Validate `STRIPE_WEBHOOK_SECRET` at startup (not first-use)

### Migrate to Lifespan

- [ ] AC9: Replace `@app.on_event("startup")` and `@app.on_event("shutdown")` with FastAPI lifespan context manager:
  ```python
  @asynccontextmanager
  async def lifespan(app: FastAPI):
      # startup
      await initialize_health_tracking()
      yield
      # shutdown (if needed)

  app = FastAPI(lifespan=lifespan)
  ```
- [ ] AC10: Move Redis pool initialization to lifespan startup
- [ ] AC11: Move env var validation to lifespan startup

### Env Var Validation at Startup

- [ ] AC12: Add startup check for required env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- [ ] AC13: Add startup WARNING for recommended env vars: `OPENAI_API_KEY`, `STRIPE_SECRET_KEY`, `SENTRY_DSN`
- [ ] AC14: Raise `RuntimeError` if critical env vars missing AND `ENVIRONMENT=production`

### Testing

- [ ] AC15: Test: `_check_user_roles()` does NOT call `time.sleep()` (use `@pytest.mark.asyncio`)
- [ ] AC16: Test: Stripe webhook processing works with per-request client
- [ ] AC17: Test: Missing `SUPABASE_JWT_SECRET` in production raises error at startup
- [ ] AC18: All existing tests pass

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
