"""Redis Cache Client for Feature Flags and General Caching.

STORY-217: Uses unified redis_pool for connections.
Provides async interface over the shared pool.

Usage:
    from cache import redis_cache

    await redis_cache.get("features:user123")
    await redis_cache.setex("features:user123", 300, json_data)
    await redis_cache.delete("features:user123")
"""

import logging
from typing import Optional

from redis_pool import get_redis_pool, get_fallback_cache

logger = logging.getLogger(__name__)


class RedisCacheClient:
    """Async Redis client wrapper with InMemoryCache fallback.

    STORY-217: All operations go through the shared redis_pool.
    Falls back to InMemoryCache when Redis is unavailable.
    """

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        redis = await get_redis_pool()
        if redis is None:
            return get_fallback_cache().get(key)
        try:
            return await redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed: {e} — using fallback")
            return get_fallback_cache().get(key)

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set value with TTL (seconds)."""
        redis = await get_redis_pool()
        if redis is None:
            return get_fallback_cache().setex(key, ttl, value)
        try:
            await redis.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Redis SETEX failed: {e} — using fallback")
            return get_fallback_cache().setex(key, ttl, value)

    async def set(self, key: str, value: str) -> bool:
        """Set value without TTL."""
        redis = await get_redis_pool()
        if redis is None:
            return get_fallback_cache().set(key, value)
        try:
            await redis.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET failed: {e} — using fallback")
            return get_fallback_cache().set(key, value)

    async def delete(self, key: str) -> int:
        """Delete key from cache."""
        redis = await get_redis_pool()
        if redis is None:
            return get_fallback_cache().delete(key)
        try:
            return await redis.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE failed: {e} — using fallback")
            return get_fallback_cache().delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        redis = await get_redis_pool()
        if redis is None:
            return get_fallback_cache().exists(key)
        try:
            return await redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS failed: {e} — using fallback")
            return get_fallback_cache().exists(key)

    async def ping(self) -> bool:
        """Health check."""
        redis = await get_redis_pool()
        if redis is None:
            return get_fallback_cache().ping()
        try:
            return await redis.ping()
        except Exception as e:
            logger.error(f"Redis PING failed: {e}")
            return False


# Global singleton instance
redis_cache = RedisCacheClient()

# Backward compatibility alias (deprecated)
redis_client = redis_cache
