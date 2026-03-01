"""Unified Redis connection pool for all backend modules.

STORY-217: Single async Redis client with connection pool.
All modules MUST use get_redis_pool() instead of creating their own connections.

Configuration:
- REDIS_URL env var: Redis connection URL (redis://host:port/db)
- Pool: max_connections=50, decode_responses=True, socket_timeout=30
- Fallback: InMemoryCache with LRU eviction (max 10K entries)

CRIT-026-ROOT: socket_timeout increased from 5→30s to prevent redis-py from killing
XREAD and other long operations. See https://github.com/redis/redis-py/issues/2807
and https://github.com/redis/redis-py/issues/3454 — redis-py async applies
socket_timeout to the ENTIRE response parse, not per-read. 5s was incompatible
with any operation > 5s (XREAD BLOCK, large SCAN, slow XADD under load).

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
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

# STORY-332: Fallback tracking state
_fallback_since: Optional[float] = None  # monotonic timestamp when fallback started
_last_fallback_warning: float = 0.0  # monotonic timestamp of last periodic warning
_FALLBACK_WARNING_THRESHOLD_S = 300  # 5 minutes before first warning
_FALLBACK_WARNING_INTERVAL_S = 60  # warn every 60s after threshold

# Pool configuration (AC2)
# CRIT-026-ROOT: Increased from 20→50 connections (2 Gunicorn workers + ARQ + SSE)
POOL_MAX_CONNECTIONS = 50
# CRIT-026-ROOT: Increased from 5→30s — redis-py #2807: socket_timeout MUST exceed
# any blocking command timeout. SSE XREAD polled at 1s, but other ops can be slow
# under Railway network latency or Redis load. 30s is safe for all operations.
POOL_SOCKET_TIMEOUT = 30
# CRIT-026-ROOT: Increased from 5→10s — connection establishment under load
POOL_SOCKET_CONNECT_TIMEOUT = 10

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

    def incr(self, key: str) -> int:
        """Increment value by 1 (returns new value). Creates key with value 1 if missing.

        B-05 AC4: Used for cache hit/miss counters.
        """
        if key in self._store:
            value, expiry = self._store[key]
            if expiry and datetime.now(timezone.utc) > expiry:
                del self._store[key]
                self._evict_if_needed()
                self._store[key] = ("1", None)
                return 1
            new_val = int(value or "0") + 1
            self._store[key] = (str(new_val), expiry)
            self._store.move_to_end(key)
            return new_val
        else:
            self._evict_if_needed()
            self._store[key] = ("1", None)
            return 1

    def keys_by_prefix(self, prefix: str) -> list[str]:
        """Return all keys matching a prefix (for metrics aggregation)."""
        now = datetime.now(timezone.utc)
        return [
            k for k, (_, expiry) in self._store.items()
            if k.startswith(prefix) and (expiry is None or expiry > now)
        ]

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
        _mark_fallback_started()
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
        _mark_redis_connected()
        return _redis_pool

    except Exception as e:
        logger.warning(
            "Redis connection failed: %s — using InMemoryCache fallback", e
        )
        _redis_pool = None
        _pool_initialized = True
        _mark_fallback_started()
        return None


# ---------------------------------------------------------------------------
# CRIT-048 AC5: SSE-specific Redis pool with extended socket timeout
# ---------------------------------------------------------------------------
# Railway Redis has latency spikes (shared infra) that cause socket_timeout=30s
# to be exceeded during SSE XREAD polling. A separate small pool with 60s timeout
# prevents TimeoutError on SSE reads without affecting other Redis operations.

SSE_SOCKET_TIMEOUT = 60

_sse_redis_pool = None
_sse_pool_initialized = False


async def get_sse_redis_pool():
    """Get Redis pool with extended timeout for SSE reads (CRIT-048 AC5).

    Returns a separate Redis pool with socket_timeout=60s (vs 30s global).
    Falls back to the regular pool if SSE pool initialization fails.

    Returns:
        redis.asyncio.Redis instance if available, None otherwise.
    """
    global _sse_redis_pool, _sse_pool_initialized

    if _sse_pool_initialized:
        return _sse_redis_pool

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        _sse_pool_initialized = True
        return None

    try:
        import redis.asyncio as aioredis

        _sse_redis_pool = aioredis.from_url(
            redis_url,
            decode_responses=True,
            max_connections=10,  # Small pool — SSE only
            socket_timeout=SSE_SOCKET_TIMEOUT,
            socket_connect_timeout=POOL_SOCKET_CONNECT_TIMEOUT,
        )

        await _sse_redis_pool.ping()
        logger.info(
            "SSE Redis pool connected (socket_timeout=%ds, max_connections=10)",
            SSE_SOCKET_TIMEOUT,
        )
        _sse_pool_initialized = True
        return _sse_redis_pool

    except Exception as e:
        logger.warning("SSE Redis pool failed: %s — falling back to regular pool", e)
        _sse_redis_pool = None
        _sse_pool_initialized = True
        # Fall back to regular pool (better than None)
        return await get_redis_pool()


def _mark_fallback_started() -> None:
    """STORY-332: Record when Redis fallback mode began and update metrics."""
    global _fallback_since
    if _fallback_since is None:
        _fallback_since = time.monotonic()
    _update_redis_metrics(available=False)


def _mark_redis_connected() -> None:
    """STORY-332: Clear fallback state when Redis reconnects."""
    global _fallback_since, _last_fallback_warning
    _fallback_since = None
    _last_fallback_warning = 0.0
    _update_redis_metrics(available=True)


def _update_redis_metrics(available: bool) -> None:
    """STORY-332 AC1+AC2: Update Prometheus gauges for Redis status."""
    try:
        from metrics import REDIS_AVAILABLE, REDIS_FALLBACK_DURATION
        REDIS_AVAILABLE.set(1 if available else 0)
        if available or _fallback_since is None:
            REDIS_FALLBACK_DURATION.set(0)
        else:
            REDIS_FALLBACK_DURATION.set(time.monotonic() - _fallback_since)
    except Exception:
        pass  # metrics may not be available (graceful degradation)


def _emit_fallback_warning_if_needed() -> None:
    """STORY-332 AC5: Emit WARNING every 60s when fallback > 5min."""
    global _last_fallback_warning
    if _fallback_since is None:
        return
    now = time.monotonic()
    elapsed = now - _fallback_since
    if elapsed < _FALLBACK_WARNING_THRESHOLD_S:
        return
    if (now - _last_fallback_warning) < _FALLBACK_WARNING_INTERVAL_S:
        return
    _last_fallback_warning = now
    logger.warning(
        "Redis in fallback mode for %.0fs (InMemoryCache active) — "
        "check Redis connectivity",
        elapsed,
    )


def get_redis_status() -> str:
    """STORY-332 AC3: Return 'connected' or 'fallback' based on current Redis state."""
    return "fallback" if _redis_pool is None else "connected"


def get_fallback_duration_seconds() -> float:
    """STORY-332 AC2: Return seconds since fallback started (0 if connected)."""
    if _fallback_since is None:
        return 0.0
    return time.monotonic() - _fallback_since


async def is_redis_available() -> bool:
    """Check if Redis pool is available and healthy (AC10, AC11).

    STORY-332: Also updates Prometheus metrics and emits periodic warnings.
    """
    pool = await get_redis_pool()
    if pool is None:
        _update_redis_metrics(available=False)
        _emit_fallback_warning_if_needed()
        return False
    try:
        await pool.ping()
        _update_redis_metrics(available=True)
        return True
    except Exception:
        _update_redis_metrics(available=False)
        _emit_fallback_warning_if_needed()
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


# ============================================================================
# STORY-294: Sync Redis client for thread-offloaded operations (LLM arbiter)
# ============================================================================

_sync_redis = None
_sync_redis_initialized = False

# Small pool — arbiter cache hits are mostly served from L1 in-memory
_SYNC_POOL_MAX_CONNECTIONS = 5


def get_sync_redis():
    """Get a sync Redis client for use in ThreadPoolExecutor contexts.

    STORY-294 AC3: The LLM arbiter runs in asyncio.to_thread() and needs
    sync Redis access for cross-worker cache sharing.

    Returns:
        redis.Redis instance if available, None otherwise.
    """
    global _sync_redis, _sync_redis_initialized

    if _sync_redis_initialized:
        return _sync_redis

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        _sync_redis_initialized = True
        return None

    try:
        import redis as sync_redis

        _sync_redis = sync_redis.from_url(
            redis_url,
            decode_responses=True,
            max_connections=_SYNC_POOL_MAX_CONNECTIONS,
            socket_timeout=POOL_SOCKET_TIMEOUT,
            socket_connect_timeout=POOL_SOCKET_CONNECT_TIMEOUT,
        )
        _sync_redis.ping()
        logger.info(
            "Sync Redis client connected (max_connections=%d)",
            _SYNC_POOL_MAX_CONNECTIONS,
        )
        _sync_redis_initialized = True
        return _sync_redis

    except Exception as e:
        logger.warning("Sync Redis connection failed: %s — arbiter cache L2 disabled", e)
        _sync_redis = None
        _sync_redis_initialized = True
        return None
