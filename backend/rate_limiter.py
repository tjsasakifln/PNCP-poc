"""Rate limiting with Redis + in-memory fallback.

STORY-203 SYS-M03: In-memory rate limiter with max size limit
STORY-217: Uses unified redis_pool for Redis connections
"""

import logging
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
