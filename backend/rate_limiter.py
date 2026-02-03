"""Rate limiting with Redis + in-memory fallback."""

import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with Redis + in-memory fallback.

    Uses Redis for distributed rate limiting across API instances.
    Falls back to in-memory dict for local development or degraded mode.
    """

    def __init__(self):
        self.redis_client = self._connect_redis()
        self._memory_store: dict[str, tuple[int, float]] = {}  # {key: (count, timestamp)}

    def _connect_redis(self) -> Optional[any]:
        """Connect to Redis (fallback to None if unavailable)."""
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.warning("REDIS_URL not set - using in-memory rate limiting")
            return None

        try:
            import redis
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            logger.info("Redis connected for rate limiting")
            return client
        except ImportError:
            logger.warning("redis library not installed - using in-memory rate limiting")
            return None
        except Exception as e:
            logger.error(f"Redis connection failed: {e} - fallback to in-memory")
            return None

    def check_rate_limit(self, user_id: str, max_requests_per_min: int) -> tuple[bool, int]:
        """
        Check if user is within rate limit.

        Args:
            user_id: User identifier
            max_requests_per_min: Maximum requests allowed per minute

        Returns:
            tuple: (allowed: bool, retry_after_seconds: int)
        """
        minute_key = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
        key = f"rate_limit:{user_id}:{minute_key}"

        if self.redis_client:
            return self._check_redis(key, max_requests_per_min)
        else:
            return self._check_memory(key, max_requests_per_min)

    def _check_redis(self, key: str, limit: int) -> tuple[bool, int]:
        """Check rate limit using Redis."""
        try:
            count = self.redis_client.incr(key)
            if count == 1:
                self.redis_client.expire(key, 60)  # TTL 60 seconds

            if count > limit:
                # Calculate retry-after
                ttl = self.redis_client.ttl(key)
                return (False, max(1, ttl))

            return (True, 0)

        except Exception as e:
            logger.error(f"Redis error in rate limiting: {e} - allowing request")
            return (True, 0)  # Fail open (don't block on Redis errors)

    def _check_memory(self, key: str, limit: int) -> tuple[bool, int]:
        """Check rate limit using in-memory dict (local dev only)."""
        now = datetime.utcnow().timestamp()

        # Cleanup old entries (simple garbage collection)
        self._memory_store = {
            k: (count, ts)
            for k, (count, ts) in self._memory_store.items()
            if now - ts < 60
        }

        if key in self._memory_store:
            count, timestamp = self._memory_store[key]
            if now - timestamp >= 60:
                # Expired, reset
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
