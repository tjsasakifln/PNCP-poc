"""Rate limiting with Redis + in-memory fallback.

STORY-203 SYS-M03: In-memory rate limiter with max size limit
STORY-217: Uses unified redis_pool for Redis connections
B-06: RedisRateLimiter — shared token bucket for PNCP/PCP API requests
"""

import asyncio
import logging
import time as _time
from datetime import datetime, timezone

from redis_pool import get_redis_pool

logger = logging.getLogger(__name__)

MAX_MEMORY_STORE_SIZE = 10_000


class RateLimiter:
    """Token bucket rate limiter using shared Redis pool + in-memory fallback.

    STORY-217: No longer creates its own Redis connection.
    """

    def __init__(self):
        self._memory_store: dict[str, tuple[int, float]] = {}

    async def check_rate_limit(self, user_id: str, max_requests_per_min: int) -> tuple[bool, int]:
        """Check if user is within rate limit.

        Returns:
            tuple: (allowed: bool, retry_after_seconds: int)
        """
        minute_key = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
        key = f"rate_limit:{user_id}:{minute_key}"

        redis = await get_redis_pool()
        if redis:
            return await self._check_redis(redis, key, max_requests_per_min)
        else:
            return self._check_memory(key, max_requests_per_min)

    async def _check_redis(self, redis, key: str, limit: int) -> tuple[bool, int]:
        """Check rate limit using shared Redis pool."""
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 60)

            if count > limit:
                ttl = await redis.ttl(key)
                return (False, max(1, ttl))

            return (True, 0)

        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e} — allowing request")
            return (True, 0)

    def _check_memory(self, key: str, limit: int) -> tuple[bool, int]:
        """Check rate limit using in-memory dict (fallback)."""
        now = datetime.now(timezone.utc).timestamp()

        cleaned_store = {
            k: (count, ts)
            for k, (count, ts) in self._memory_store.items()
            if now - ts < 60
        }

        if len(cleaned_store) > MAX_MEMORY_STORE_SIZE:
            sorted_items = sorted(cleaned_store.items(), key=lambda item: item[1][1])
            cleaned_store = dict(sorted_items[-MAX_MEMORY_STORE_SIZE:])
            logger.warning(
                f"In-memory rate limiter exceeded {MAX_MEMORY_STORE_SIZE} entries. "
                f"Evicted oldest entries (LRU)."
            )

        self._memory_store = cleaned_store

        if key in self._memory_store:
            count, timestamp = self._memory_store[key]
            if now - timestamp >= 60:
                self._memory_store[key] = (1, now)
                return (True, 0)
            elif count >= limit:
                retry_after = int(60 - (now - timestamp))
                return (False, max(1, retry_after))
            else:
                self._memory_store[key] = (count + 1, timestamp)
                return (True, 0)
        else:
            self._memory_store[key] = (1, now)
            return (True, 0)


# Global instance
rate_limiter = RateLimiter()


# ============================================================================
# B-06: Shared Token Bucket Rate Limiter (PNCP/PCP API requests)
# ============================================================================

class RedisRateLimiter:
    """Shared token bucket rate limiter via Redis (B-06 AC6).

    Ensures total request rate across all Gunicorn workers stays within limits.
    Uses atomic Lua script for token bucket implementation.

    Fallback: returns True (allows request) when Redis is unavailable,
    letting the per-worker local rate limiter handle it.

    Redis keys:
        rate_limiter:{name}:bucket          → HASH {tokens, last_refill}
        rate_limiter:{name}:requests_count  → INT (requests in current minute)
    """

    _BUCKET_SCRIPT = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or max_tokens
local last_refill = tonumber(bucket[2]) or now

local elapsed = now - last_refill
local new_tokens = math.min(max_tokens, tokens + elapsed * refill_rate)

if new_tokens >= 1 then
    redis.call('HMSET', key, 'tokens', new_tokens - 1, 'last_refill', now)
    redis.call('EXPIRE', key, 60)
    return 1
else
    redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 60)
    return 0
end
"""

    def __init__(
        self,
        name: str = "pncp",
        max_tokens: int = 10,
        refill_rate: float = 10.0,
    ):
        self.name = name
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self._key = f"rate_limiter:{name}:bucket"
        self._requests_key = f"rate_limiter:{name}:requests_count"

    async def acquire(self, timeout: float = 5.0) -> bool:
        """Acquire a token from the shared bucket.

        Returns True if token acquired or Redis unavailable (fail-open).
        Waits with exponential backoff up to ``timeout`` seconds if rate limited.
        """
        redis = await get_redis_pool()
        if not redis:
            return True  # Fail open — per-worker limiter handles it

        start = _time.time()
        backoff = 0.05  # 50ms initial

        while True:
            try:
                now = _time.time()
                result = await redis.eval(
                    self._BUCKET_SCRIPT,
                    1,
                    self._key,
                    str(self.max_tokens),
                    str(self.refill_rate),
                    str(now),
                )

                if int(result) == 1:
                    # Token acquired — track request count for metrics
                    try:
                        pipe = redis.pipeline()
                        pipe.incr(self._requests_key)
                        pipe.expire(self._requests_key, 60)
                        await pipe.execute()
                    except Exception:
                        pass
                    return True

                # Rate limited — check timeout
                elapsed = _time.time() - start
                if elapsed >= timeout:
                    return False

                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 0.5)

            except Exception as e:
                logger.debug(f"Redis rate limiter error: {e} — allowing request")
                return True  # Fail open

    async def get_stats(self) -> dict:
        """Get rate limiter statistics for health endpoint (AC10)."""
        redis = await get_redis_pool()
        if not redis:
            return {
                "backend": "local",
                "tokens_available": None,
                "requests_last_minute": None,
            }

        try:
            bucket = await redis.hmget(self._key, "tokens", "last_refill")
            tokens = float(bucket[0]) if bucket[0] else float(self.max_tokens)
            requests = await redis.get(self._requests_key)
            return {
                "backend": "redis",
                "tokens_available": round(tokens, 1),
                "requests_last_minute": int(requests) if requests else 0,
            }
        except Exception:
            return {
                "backend": "error",
                "tokens_available": None,
                "requests_last_minute": None,
            }


# Global shared rate limiter instances (B-06)
pncp_rate_limiter = RedisRateLimiter(name="pncp", max_tokens=10, refill_rate=10.0)
pcp_rate_limiter = RedisRateLimiter(name="pcp", max_tokens=5, refill_rate=5.0)
