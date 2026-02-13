# STORY-217: Unify Triple Redis Architecture → Single Async Client

**Status:** Done
**Priority:** P1 — Pre-GTM Important
**Sprint:** Sprint 2 (Weeks 2-3)
**Estimated Effort:** 2 days
**Source:** AUDIT-FRENTE-1-CODEBASE (CRIT-02), AUDIT-CONSOLIDATED (REFACTOR-02)
**Squad:** team-bidiq-backend (architect, dev)

---

## Context

Three independent Redis connection strategies coexist, wasting connections and creating inconsistent behavior:

| File | Type | Purpose | Connection |
|------|------|---------|------------|
| `redis_client.py` | `redis.asyncio` | Progress pub/sub | Lazy singleton, async |
| `cache.py` | `redis` (sync) | Feature flags, Stripe cache | Eager singleton, sync, pool=10 |
| `routes/features.py` | `redis` (sync) | Feature flag cache | **New connection per request** |

**Critical issues:**
1. `routes/features.py:51` creates a **new Redis connection on every `GET /api/features/me`** call
2. `redis_client.py:56` uses `asyncio.run()` to test connection, which **crashes if called from within a running event loop** (FastAPI always has one)
3. `cache.py` and `redis_client.py` use incompatible client types (sync vs async)
4. Fallback behavior differs: None vs InMemoryCache vs direct DB query

## Acceptance Criteria

### Unification

- [x] AC1: Create single `backend/redis_pool.py` with one async Redis client and connection pool
- [x] AC2: Pool configuration: `max_connections=20`, `decode_responses=True`, `socket_timeout=5`
- [x] AC3: Lazy initialization via `get_redis_pool()` async function (no `asyncio.run()`)
- [x] AC4: Unified fallback: when Redis unavailable → `InMemoryCache` with LRU eviction (max 10K entries)
- [x] AC5: All modules use `get_redis_pool()` instead of their own connection logic

### Migration

- [x] AC6: `redis_client.py` — redirect to `redis_pool.py` (keep module for backward compat, deprecation warning)
- [x] AC7: `cache.py` — redirect `RedisCache` to use the async pool, keep `InMemoryCache` as fallback
- [x] AC8: `routes/features.py:51` — remove per-request Redis connection, use shared pool
- [x] AC9: `progress.py` — use shared pool for pub/sub operations

### Fix asyncio.run() Crash

- [x] AC10: Replace `asyncio.run(_redis_client.ping())` in `redis_client.py:56` with proper async health check
- [x] AC11: Health check runs during FastAPI lifespan startup (not at module import)

### Testing

- [x] AC12: Test: concurrent requests share the same connection pool
- [x] AC13: Test: Redis unavailable → fallback to InMemoryCache
- [x] AC14: Test: InMemoryCache has LRU eviction at 10K entries
- [x] AC15: Test: no `asyncio.run()` calls in production code (`grep -rn "asyncio.run" backend/ --include="*.py"` returns only test files)
- [x] AC16: All existing tests pass

## Validation Metric

- `grep -rn "redis.Redis\|redis.asyncio.Redis\|redis.StrictRedis" backend/ --include="*.py"` shows exactly 1 file (`redis_pool.py`)
- Zero `asyncio.run()` in production code
- No per-request Redis connection creation

## Risk Mitigated

- P1: Connection pool exhaustion under load
- P1: `asyncio.run()` crash in production
- P2: Inconsistent fallback behavior across modules

## File References

| File | Change |
|------|--------|
| `backend/redis_pool.py` | NEW — unified async pool + InMemoryCache LRU |
| `backend/redis_client.py` | Deprecated shim → redirects to redis_pool |
| `backend/cache.py` | Async RedisCacheClient using shared pool |
| `backend/routes/features.py` | Removed per-request connection, uses redis_cache |
| `backend/routes/subscriptions.py` | Removed ad-hoc connection, uses redis_cache |
| `backend/progress.py` | Uses get_redis_pool() for pub/sub |
| `backend/rate_limiter.py` | Async, uses shared pool |
| `backend/webhooks/stripe.py` | Updated to async redis_cache |
| `backend/main.py` | Added startup_redis/shutdown_redis lifecycle hooks |
| `backend/tests/test_redis_pool.py` | NEW — 39 tests (AC12-AC15) |
| `backend/tests/test_rate_limiter.py` | NEW — 8 async tests |
| `backend/tests/test_stripe_webhook.py` | Updated mock paths redis_client → redis_cache |
