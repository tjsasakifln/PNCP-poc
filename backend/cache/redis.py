"""cache/redis.py — Redis/InMemory cache layer (L2, 4h TTL).

STORY-5.1 (TD-SYS-010): L1 cache now backed by shared Redis when available,
with transparent fallback to InMemoryCache for single-worker / test environments.

Redis keys use namespace ``l1:search_cache:{cache_key}`` (AC1).
InMemoryCache fallback keys keep legacy ``search_cache:{cache_key}`` format.

redis_pool imports are lazy (inside functions) for testability.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from cache.enums import CachePriority, REDIS_TTL_BY_PRIORITY, REDIS_CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)

# Lazy import — resolved at call time so tests can patch before first call.
def _get_l1_metrics():
    from metrics import L1_CACHE_HITS_TOTAL, L1_CACHE_MISSES_TOTAL
    return L1_CACHE_HITS_TOTAL, L1_CACHE_MISSES_TOTAL


def _save_to_redis(
    cache_key: str, results: list, sources: list,
    *, priority: CachePriority = CachePriority.COLD,
) -> None:
    """Save to shared Redis L1 cache (with InMemoryCache fallback).

    STORY-5.1: Tries actual Redis first (shared across Gunicorn workers) so
    that a warm result from worker A is visible to worker B.
    Falls back to per-process InMemoryCache when Redis is unavailable.

    B-02 AC6: Uses priority-based TTL instead of fixed 4h.
    """
    from redis_pool import get_sync_redis, get_fallback_cache

    ttl = REDIS_TTL_BY_PRIORITY.get(priority, REDIS_CACHE_TTL_SECONDS)
    cache_data = json.dumps({
        "results": results,
        "sources_json": sources,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    })

    sync_redis = get_sync_redis()
    if sync_redis is not None:
        try:
            sync_redis.setex(f"l1:search_cache:{cache_key}", ttl, cache_data)
            return
        except Exception as e:
            logger.warning("Redis L1 save failed, falling back to InMemory: %s", e)

    # Fallback: per-process InMemoryCache (legacy key format for backward compat)
    get_fallback_cache().setex(f"search_cache:{cache_key}", ttl, cache_data)


def _get_from_redis(cache_key: str) -> Optional[dict]:
    """Read from shared Redis L1 cache (with InMemoryCache fallback).

    STORY-5.1: Tries actual Redis first; falls back to per-process
    InMemoryCache when Redis is unavailable or returns an error.
    """
    from redis_pool import get_sync_redis, get_fallback_cache

    L1_HITS, L1_MISSES = _get_l1_metrics()

    sync_redis = get_sync_redis()
    if sync_redis is not None:
        try:
            cached = sync_redis.get(f"l1:search_cache:{cache_key}")
            if cached:
                L1_HITS.labels(backend="redis").inc()
                return json.loads(cached)
            L1_MISSES.labels(backend="redis").inc()
            return None
        except Exception as e:
            logger.warning("Redis L1 get failed, falling back to InMemory: %s", e)

    # Fallback: per-process InMemoryCache
    cached = get_fallback_cache().get(f"search_cache:{cache_key}")
    if cached:
        L1_HITS.labels(backend="memory").inc()
        return json.loads(cached)
    L1_MISSES.labels(backend="memory").inc()
    return None
