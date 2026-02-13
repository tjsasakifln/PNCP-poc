"""Unified Redis connection pool for all backend modules.

STORY-217: Single async Redis client with connection pool.
All modules MUST use get_redis_pool() instead of creating their own connections.

Configuration:
- REDIS_URL env var: Redis connection URL (redis://host:port/db)
- Pool: max_connections=20, decode_responses=True, socket_timeout=5
- Fallback: InMemoryCache with LRU eviction (max 10K entries)

Usage:
    from redis_pool import get_redis_pool, get_fallback_cache, is_redis_available

    # In async context:
    redis = await get_redis_pool()
    if redis:
        await redis.get("key")
    else:
        cache = get_fallback_cache()
        cache.get("key")
"""

import logging
import os
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Pool configuration (AC2)
POOL_MAX_CONNECTIONS = 20
POOL_SOCKET_TIMEOUT = 5
POOL_SOCKET_CONNECT_TIMEOUT = 5

# InMemoryCache configuration (AC4)
INMEMORY_MAX_ENTRIES = 10_000

# Singleton state
_redis_pool = None
_pool_initialized = False


class InMemoryCache:
    """LRU in-memory cache with TTL support.

    Unified fallback when Redis is unavailable (AC4).
    Max 10K entries with LRU eviction.
    """

    def __init__(self, max_entries: int = INMEMORY_MAX_ENTRIES):
        self._store: OrderedDict[str, tuple[Any, Optional[datetime]]] = OrderedDict()
        self._max_entries = max_entries

    def get(self, key: str) -> Optional[str]:
        """Get value (returns None if expired or missing)."""
        if key not in self._store:
            return None

        value, expiry = self._store[key]

        if expiry and datetime.now(timezone.utc) > expiry:
            del self._store[key]
            return None

        # Move to end (most recently used)
        self._store.move_to_end(key)
        return value

    def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set value with TTL (seconds)."""
        expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        self._store[key] = (value, expiry)
        self._store.move_to_end(key)
        self._evict_if_needed()
        return True

    def set(self, key: str, value: str) -> bool:
        """Set value without TTL."""
        self._store[key] = (value, None)
        self._store.move_to_end(key)
        self._evict_if_needed()
        return True

    def delete(self, key: str) -> int:
        """Delete key (returns 1 if deleted, 0 if not found)."""
        if key in self._store:
            del self._store[key]
            return 1
        return 0

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def ping(self) -> bool:
        """Health check (always True for in-memory)."""
        return True

    def _evict_if_needed(self) -> None:
        """LRU eviction: remove oldest entries when exceeding max_entries."""
        while len(self._store) > self._max_entries:
            self._store.popitem(last=False)  # Remove oldest (front of OrderedDict)

    def __len__(self) -> int:
        return len(self._store)


# Singleton fallback cache
_fallback_cache: Optional[InMemoryCache] = None


def get_fallback_cache() -> InMemoryCache:
    """Get the shared InMemoryCache fallback instance."""
    global _fallback_cache
    if _fallback_cache is None:
        _fallback_cache = InMemoryCache()
    return _fallback_cache


async def get_redis_pool():
    """Get the shared async Redis connection pool (AC1, AC3).

    Lazy initialization — creates pool on first call.
    Thread-safe within a single event loop.

    Returns:
        redis.asyncio.Redis instance if available, None otherwise.
        When None, callers should use get_fallback_cache().
    """
    global _redis_pool, _pool_initialized

    if _pool_initialized:
        return _redis_pool

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.warning(
            "REDIS_URL not set — Redis disabled, using InMemoryCache fallback"
        )
        _pool_initialized = True
        return None

    try:
        import redis.asyncio as aioredis

        _redis_pool = aioredis.from_url(
            redis_url,
            decode_responses=True,
            max_connections=POOL_MAX_CONNECTIONS,
            socket_timeout=POOL_SOCKET_TIMEOUT,
            socket_connect_timeout=POOL_SOCKET_CONNECT_TIMEOUT,
        )

        # Async ping — safe inside running event loop (no asyncio.run!)
        await _redis_pool.ping()
        logger.info(
            "Redis pool connected: %s (max_connections=%d)",
            redis_url.split("@")[-1],
            POOL_MAX_CONNECTIONS,
        )
        _pool_initialized = True
        return _redis_pool

    except Exception as e:
        logger.warning(
            "Redis connection failed: %s — using InMemoryCache fallback", e
        )
        _redis_pool = None
        _pool_initialized = True
        return None


async def is_redis_available() -> bool:
    """Check if Redis pool is available and healthy (AC10, AC11)."""
    pool = await get_redis_pool()
    if pool is None:
        return False
    try:
        await pool.ping()
        return True
    except Exception:
        return False


async def startup_redis() -> None:
    """Initialize Redis pool during FastAPI lifespan startup (AC11)."""
    pool = await get_redis_pool()
    if pool:
        logger.info("Redis pool initialized during startup")
    else:
        logger.warning("Redis unavailable at startup — InMemoryCache active")


async def shutdown_redis() -> None:
    """Close Redis pool during FastAPI lifespan shutdown."""
    global _redis_pool, _pool_initialized
    if _redis_pool:
        await _redis_pool.aclose()
        logger.info("Redis pool closed")
    _redis_pool = None
    _pool_initialized = False
