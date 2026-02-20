"""UX-303: Multi-level cache with Supabase → Redis/InMemory → Local file fallback.

Built on GTM-FIX-010 foundation. Adds:
  - 3-level save fallback: Supabase → Redis → Local file
  - 3-level read fallback: Supabase → Redis → Local file
  - CacheLevel / CacheStatus enums
  - Mixpanel tracking for cache hit rates (AC3)
  - Sentry alerting with structured context (AC6)
  - Local file cache management

TTL policy (unchanged from GTM-FIX-010):
  - Fresh (0-6h): Serve directly
  - Stale (6-24h): Serve as fallback when live sources fail
  - Expired (>24h): Not served
"""

import asyncio
import hashlib
import json
import logging
import os
import platform
import time
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

import sentry_sdk
from utils.error_reporting import report_error  # GTM-RESILIENCE-E02: centralized error emission
from metrics import CACHE_HITS as METRICS_CACHE_HITS, CACHE_MISSES as METRICS_CACHE_MISSES

logger = logging.getLogger(__name__)

# TTL boundaries (hours)
CACHE_FRESH_HOURS = 6
CACHE_STALE_HOURS = 24

# Local cache directory (platform-aware)
LOCAL_CACHE_DIR = Path(
    os.getenv("SMARTLIC_CACHE_DIR", "/tmp/smartlic_cache")
    if platform.system() != "Windows"
    else os.getenv("SMARTLIC_CACHE_DIR", os.path.join(os.environ.get("TEMP", "C:\\Temp"), "smartlic_cache"))
)
LOCAL_CACHE_TTL_HOURS = 24  # Max age for local cache files
REDIS_CACHE_TTL_SECONDS = 14400  # 4 hours


class CacheLevel(str, Enum):
    """Cache storage level for tracking hit metrics."""
    SUPABASE = "supabase"
    REDIS = "redis"
    LOCAL = "local"
    MISS = "miss"


class CacheStatus(str, Enum):
    """Cache age classification per SWR policy."""
    FRESH = "fresh"
    STALE = "stale"
    EXPIRED = "expired"


class CachePriority(str, Enum):
    """B-02 AC1: Cache entry priority classification for hot/warm/cold tiering."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


# B-02 AC6: Redis TTL by priority (seconds)
REDIS_TTL_BY_PRIORITY = {
    CachePriority.HOT: 7200,    # 2h
    CachePriority.WARM: 21600,  # 6h
    CachePriority.COLD: 3600,   # 1h
}


def classify_priority(
    access_count: int,
    last_accessed_at: Optional[datetime],
    is_saved_search: bool = False,
) -> CachePriority:
    """B-02 AC2: Deterministic priority classification.

    Returns:
        HOT if access_count >= 3 in last 24h OR is_saved_search with recent access
        WARM if access_count >= 1 in last 24h
        COLD otherwise
    """
    now = datetime.now(timezone.utc)

    recent_access = False
    if last_accessed_at:
        if last_accessed_at.tzinfo is None:
            last_accessed_at = last_accessed_at.replace(tzinfo=timezone.utc)
        age_hours = (now - last_accessed_at).total_seconds() / 3600
        recent_access = age_hours <= 24

    if recent_access and access_count >= 3:
        return CachePriority.HOT
    if is_saved_search and recent_access:
        return CachePriority.HOT
    if recent_access and access_count >= 1:
        return CachePriority.WARM

    return CachePriority.COLD


def compute_search_hash(params: dict) -> str:
    """Deterministic hash from search params for deduplication.

    Excludes dates intentionally — stale cache should serve regardless of
    date range since it's better than nothing when all sources are down.
    """
    normalized = {
        "setor_id": params.get("setor_id"),
        "ufs": sorted(params.get("ufs", [])),
        "status": params.get("status"),
        "modalidades": sorted(params.get("modalidades") or []) or None,
        "modo_busca": params.get("modo_busca"),
    }
    params_json = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(params_json.encode()).hexdigest()


def calculate_backoff_minutes(fail_streak: int) -> int:
    """B-03 AC4: Exponential backoff for cache key degradation.

    Returns minutes to degrade: 1 (streak=1), 5 (streak=2), 15 (streak=3), 30 (streak>=4).
    Returns 0 for streak=0 (no degradation).
    """
    if fail_streak <= 0:
        return 0
    backoff_schedule = [1, 5, 15, 30]
    idx = min(fail_streak - 1, len(backoff_schedule) - 1)
    return backoff_schedule[idx]


def get_cache_status(fetched_at) -> CacheStatus:
    """Classify cache age into Fresh/Stale/Expired (AC4)."""
    if isinstance(fetched_at, str):
        fetched_at = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))

    # Ensure timezone-aware comparison
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)

    age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600

    if age_hours <= CACHE_FRESH_HOURS:
        return CacheStatus.FRESH
    elif age_hours <= CACHE_STALE_HOURS:
        return CacheStatus.STALE
    else:
        return CacheStatus.EXPIRED


# ============================================================================
# Level 1: Supabase (persistent, 24h TTL)
# ============================================================================


async def _save_to_supabase(
    user_id: str, params_hash: str, params: dict, results: list, sources: list[str],
    *, fetch_duration_ms: Optional[int] = None, coverage: Optional[dict] = None,
) -> None:
    """Save to Supabase cache (Level 1).

    B-03 AC2: On successful fetch, also writes health metadata fields.
    """
    from supabase_client import get_supabase
    sb = get_supabase()

    now = datetime.now(timezone.utc).isoformat()
    row = {
        "user_id": user_id,
        "params_hash": params_hash,
        "search_params": params,
        "results": results,
        "total_results": len(results),
        "sources_json": sources,
        "fetched_at": now,
        "created_at": now,
        # B-03 AC2: Health metadata — reset on successful fetch
        "last_success_at": now,
        "last_attempt_at": now,
        "fail_streak": 0,
        "degraded_until": None,
    }
    # B-03 AC6: Structured coverage JSONB
    if coverage is not None:
        row["coverage"] = coverage
    # B-03 AC7: Fetch duration tracking
    if fetch_duration_ms is not None:
        row["fetch_duration_ms"] = fetch_duration_ms

    # CRIT-001 AC12: Filter payload to only known columns
    try:
        from models.cache import SearchResultsCacheRow
        expected = SearchResultsCacheRow.expected_columns()
        unknown_keys = set(row.keys()) - expected
        if unknown_keys:
            logger.warning(f"CRIT-001: _save_to_supabase payload has unknown keys: {sorted(unknown_keys)}")
        # Columns validated against SearchResultsCacheRow
    except ImportError:
        pass

    sb.table("search_results_cache").upsert(
        row, on_conflict="user_id,params_hash"
    ).execute()


async def _get_from_supabase(user_id: str, params_hash: str) -> Optional[dict]:
    """Read from Supabase cache (Level 1).

    B-02 AC8: Also returns priority, access_count, last_accessed_at for classification.
    """
    from supabase_client import get_supabase
    sb = get_supabase()

    response = (
        sb.table("search_results_cache")
        .select("results, total_results, sources_json, fetched_at, created_at, priority, access_count, last_accessed_at")
        .eq("user_id", user_id)
        .eq("params_hash", params_hash)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    row = response.data[0]

    # CRIT-001 AC11: Validate expected fields are present, use defaults if missing
    try:
        from models.cache import SearchResultsCacheRow
        expected_fields = {"results", "total_results", "sources_json", "fetched_at", "priority", "access_count", "last_accessed_at"}
        missing_fields = expected_fields - set(row.keys())
        if missing_fields:
            logger.warning(f"CRIT-001: _get_from_supabase row missing fields: {sorted(missing_fields)}")
        # Columns validated against SearchResultsCacheRow
    except ImportError:
        pass

    fetched_at_str = row.get("fetched_at") or row.get("created_at")
    return {
        "results": row.get("results", []),
        "total_results": row.get("total_results", 0),
        "sources_json": row.get("sources_json"),
        "fetched_at": fetched_at_str,
        # B-02 fields
        "priority": row.get("priority", "cold"),
        "access_count": row.get("access_count", 0),
        "last_accessed_at": row.get("last_accessed_at"),
    }


# ============================================================================
# Level 2: Redis / InMemoryCache (volatile, 4h TTL)
# ============================================================================


def _save_to_redis(
    cache_key: str, results: list, sources: list[str],
    *, priority: CachePriority = CachePriority.COLD,
) -> None:
    """Save to Redis/InMemory cache (Level 2).

    B-02 AC6: Uses priority-based TTL instead of fixed 4h.
    """
    from redis_pool import get_fallback_cache
    cache = get_fallback_cache()

    ttl = REDIS_TTL_BY_PRIORITY.get(priority, REDIS_CACHE_TTL_SECONDS)
    cache_data = json.dumps({
        "results": results,
        "sources_json": sources,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    })
    cache.setex(f"search_cache:{cache_key}", ttl, cache_data)


def _get_from_redis(cache_key: str) -> Optional[dict]:
    """Read from Redis/InMemory cache (Level 2)."""
    from redis_pool import get_fallback_cache
    cache = get_fallback_cache()

    cached = cache.get(f"search_cache:{cache_key}")
    if not cached:
        return None

    return json.loads(cached)


# ============================================================================
# Level 3: Local file (last resort, 24h TTL)
# ============================================================================


def _save_to_local(cache_key: str, results: list, sources: list[str]) -> None:
    """Save to local JSON file (Level 3)."""
    LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_data = {
        "results": results,
        "sources_json": sources,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

    cache_file = LOCAL_CACHE_DIR / f"{cache_key[:32]}.json"
    cache_file.write_text(json.dumps(cache_data), encoding="utf-8")


def _get_from_local(cache_key: str) -> Optional[dict]:
    """Read from local JSON file (Level 3).

    A-03 AC1: Validates TTL — returns None if fetched_at + 24h < now(UTC).
    A-03 AC2: Includes _cache_age_hours in returned dict when valid.
    """
    cache_file = LOCAL_CACHE_DIR / f"{cache_key[:32]}.json"
    if not cache_file.exists():
        return None

    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    # AC1: Validate TTL based on fetched_at timestamp
    fetched_at_str = data.get("fetched_at")
    if not fetched_at_str:
        return None  # No freshness info — treat as expired

    try:
        fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00"))
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
    except (ValueError, TypeError):
        return None

    if age_hours > LOCAL_CACHE_TTL_HOURS:
        return None  # AC1: Expired (>24h)

    # AC2: Include freshness metadata for callers
    data["_cache_age_hours"] = round(age_hours, 1)
    return data


# ============================================================================
# Multi-level save (AC2)
# ============================================================================


async def save_to_cache(
    user_id: str,
    params: dict,
    results: list,
    sources: list[str],
    *,
    fetch_duration_ms: Optional[int] = None,
    coverage: Optional[dict] = None,
) -> dict:
    """Save results to cache with 3-level fallback (AC2).

    Cascade: Supabase → Redis/InMemory → Local file.
    B-03 AC2/AC6/AC7: Accepts fetch_duration_ms and coverage for health metadata.
    Returns dict with {level, success}.
    """
    params_hash = compute_search_hash(params)
    start = time.monotonic()

    # Level 1: Supabase
    try:
        await _save_to_supabase(
            user_id, params_hash, params, results, sources,
            fetch_duration_ms=fetch_duration_ms, coverage=coverage,
        )
        elapsed = (time.monotonic() - start) * 1000
        logger.info(
            f"Cache SAVE L1/supabase: {len(results)} results "
            f"for hash {params_hash[:12]}... ({elapsed:.0f}ms, sources: {sources})"
        )
        _track_cache_operation("save", True, CacheLevel.SUPABASE, len(results), elapsed)
        return {"level": CacheLevel.SUPABASE, "success": True}
    except Exception as e:
        # GTM-RESILIENCE-E02: centralized reporting (cache save is expected/transient)
        report_error(
            e, f"Supabase cache save failed (key={params_hash[:12]}, n={len(results)})",
            expected=True, tags={"cache_operation": "save", "cache_level": "supabase"}, log=logger,
        )

    # Level 2: Redis/InMemory
    try:
        _save_to_redis(params_hash, results, sources)
        elapsed = (time.monotonic() - start) * 1000
        logger.warning(
            f"Cache SAVE L2/redis fallback: {len(results)} results "
            f"for hash {params_hash[:12]}... ({elapsed:.0f}ms)"
        )
        _track_cache_operation("save", True, CacheLevel.REDIS, len(results), elapsed)
        return {"level": CacheLevel.REDIS, "success": True}
    except Exception as e:
        logger.error(f"Redis cache save failed: {e}")

    # Level 3: Local file
    try:
        _save_to_local(params_hash, results, sources)
        elapsed = (time.monotonic() - start) * 1000
        logger.warning(
            f"Cache SAVE L3/local fallback: {len(results)} results "
            f"for hash {params_hash[:12]}... ({elapsed:.0f}ms)"
        )
        _track_cache_operation("save", True, CacheLevel.LOCAL, len(results), elapsed)
        return {"level": CacheLevel.LOCAL, "success": True}
    except Exception as e:
        logger.error(f"All cache levels failed for save: {e}")
        _track_cache_operation("save", False, CacheLevel.MISS, len(results), 0)
        return {"level": CacheLevel.MISS, "success": False}


# ============================================================================
# Multi-level read (AC2)
# ============================================================================


async def get_from_cache(
    user_id: str,
    params: dict,
) -> Optional[dict]:
    """Retrieve cached results with 3-level fallback (AC2).

    Cascade: Supabase → Redis/InMemory → Local file.
    B-02 AC4: Increments access_count on Supabase after each hit.
    B-02 AC5: Reclassifies priority if it changed.
    B-02 AC8: Includes cache_priority in result.
    B-02 AC9: Triggers proactive refresh for hot keys near expiry.
    Returns dict with: results, cached_at, cached_sources, cache_age_hours,
                       is_stale, cache_level, cache_priority
    Returns None if no valid cache entry exists.
    """
    params_hash = compute_search_hash(params)
    start = time.monotonic()

    # Level 1: Supabase
    try:
        data = await _get_from_supabase(user_id, params_hash)
        if data:
            result = _process_cache_hit(data, params_hash, CacheLevel.SUPABASE)
            if result:
                elapsed = (time.monotonic() - start) * 1000
                _track_cache_operation(
                    "read", True, CacheLevel.SUPABASE,
                    len(result["results"]), elapsed,
                    cache_age_seconds=result["cache_age_hours"] * 3600,
                )
                _freshness = result.get("cache_status", "stale")
                METRICS_CACHE_HITS.labels(level="supabase", freshness=_freshness).inc()
                # B-02 AC4/AC5: Increment access_count and reclassify
                await _increment_and_reclassify(user_id, params_hash, params, result)
                return result
    except Exception as e:
        # GTM-RESILIENCE-E02: centralized reporting (cache read is expected/transient)
        report_error(
            e, f"Supabase cache read failed (key={params_hash[:12]})",
            expected=True, tags={"cache_operation": "read", "cache_level": "supabase"}, log=logger,
        )

    # Level 2: Redis/InMemory
    try:
        data = _get_from_redis(params_hash)
        if data:
            result = _process_cache_hit(data, params_hash, CacheLevel.REDIS)
            if result:
                elapsed = (time.monotonic() - start) * 1000
                _track_cache_operation(
                    "read", True, CacheLevel.REDIS,
                    len(result["results"]), elapsed,
                    cache_age_seconds=result["cache_age_hours"] * 3600,
                )
                _freshness = result.get("cache_status", "stale")
                METRICS_CACHE_HITS.labels(level="memory", freshness=_freshness).inc()
                # B-02 AC4/AC5: Track access in Supabase (best-effort)
                try:
                    await _increment_and_reclassify(user_id, params_hash, params, result)
                except Exception:
                    pass
                return result
    except Exception as e:
        logger.error(f"Redis cache read failed: {e}")

    # Level 3: Local file
    try:
        data = _get_from_local(params_hash)
        if data:
            result = _process_cache_hit(data, params_hash, CacheLevel.LOCAL)
            if result:
                elapsed = (time.monotonic() - start) * 1000
                _track_cache_operation(
                    "read", True, CacheLevel.LOCAL,
                    len(result["results"]), elapsed,
                    cache_age_seconds=result["cache_age_hours"] * 3600,
                )
                _freshness = result.get("cache_status", "stale")
                METRICS_CACHE_HITS.labels(level="local", freshness=_freshness).inc()
                return result
    except Exception as e:
        logger.error(f"Local cache read failed: {e}")

    # Miss across all levels
    elapsed = (time.monotonic() - start) * 1000
    # CRIT-004 AC14: Include search_id in cache miss log for correlation
    from middleware import search_id_var
    _search_id_miss = search_id_var.get("-")
    logger.info(f"Cache MISS all levels [search={_search_id_miss}] for hash {params_hash[:12]}... ({elapsed:.0f}ms)")
    _track_cache_operation("read", False, CacheLevel.MISS, 0, elapsed)
    METRICS_CACHE_MISSES.labels(level="all").inc()
    return None


# ============================================================================
# A-03 AC3: Unified cascade read (L2 → L1 → L3)
# ============================================================================


async def get_from_cache_cascade(
    user_id: str,
    params: dict,
) -> Optional[dict]:
    """Unified cache cascade: L2 (InMemory/Redis) → L1 (Supabase) → L3 (Local file).

    A-03 AC3: Tries all 3 levels in order of speed (no I/O → HTTP → disk).
    A-03 AC4: Returns cache_level as "memory" | "supabase" | "local".
    A-03 AC9: Logs event "cache_l3_served" when L3 provides the data.

    Returns dict with: results, cached_at, cached_sources, cache_age_hours,
                       is_stale, cache_level, cache_status
    Returns None if no valid cache entry exists at any level.
    """
    params_hash = compute_search_hash(params)

    # AC4: Map internal enum to story-specified string values
    _level_str = {
        CacheLevel.REDIS: "memory",
        CacheLevel.SUPABASE: "supabase",
        CacheLevel.LOCAL: "local",
    }

    # L2: Redis/InMemory — O(1) lookup, no I/O
    try:
        data = _get_from_redis(params_hash)
        if data:
            result = _process_cache_hit(data, params_hash, CacheLevel.REDIS)
            if result:
                result["cache_level"] = _level_str[CacheLevel.REDIS]
                _freshness = result.get("cache_status", "stale")
                METRICS_CACHE_HITS.labels(level="memory", freshness=_freshness).inc()
                return result
    except Exception as e:
        logger.warning(f"Cascade L2/redis read failed: {e}")

    # L1: Supabase — HTTP roundtrip (~100-300ms)
    try:
        data = await _get_from_supabase(user_id, params_hash)
        if data:
            result = _process_cache_hit(data, params_hash, CacheLevel.SUPABASE)
            if result:
                result["cache_level"] = _level_str[CacheLevel.SUPABASE]
                _freshness = result.get("cache_status", "stale")
                METRICS_CACHE_HITS.labels(level="supabase", freshness=_freshness).inc()
                return result
    except Exception as e:
        report_error(
            e, f"Cascade L1/supabase read failed (key={params_hash[:12]})",
            expected=True, tags={"cache_operation": "cascade_read", "cache_level": "supabase"}, log=logger,
        )

    # L3: Local file — disk I/O (~5-20ms)
    try:
        data = _get_from_local(params_hash)
        if data:
            result = _process_cache_hit(data, params_hash, CacheLevel.LOCAL)
            if result:
                result["cache_level"] = _level_str[CacheLevel.LOCAL]
                _freshness = result.get("cache_status", "stale")
                METRICS_CACHE_HITS.labels(level="local", freshness=_freshness).inc()
                # AC9: Specific log when L3 serves data
                logger.info(json.dumps({
                    "event": "cache_l3_served",
                    "cache_key": params_hash[:12],
                    "cache_age_hours": result["cache_age_hours"],
                    "results_count": len(result["results"]),
                }))
                return result
    except Exception as e:
        logger.error(f"Cascade L3/local read failed: {e}")

    METRICS_CACHE_MISSES.labels(level="cascade").inc()
    return None


# ============================================================================
# B-03 AC3/AC5: Cache key degradation tracking
# ============================================================================


async def record_cache_fetch_failure(user_id: str, params_hash: str) -> dict:
    """B-03 AC3: Record a fetch failure for a cache key.

    Increments fail_streak and calculates degraded_until with exponential backoff.
    Does NOT update last_success_at, results, or sources_json.

    Returns dict with {fail_streak, degraded_until} or empty dict if key not found.
    """
    from supabase_client import get_supabase
    sb = get_supabase()

    now = datetime.now(timezone.utc)

    # Read current fail_streak
    response = (
        sb.table("search_results_cache")
        .select("fail_streak")
        .eq("user_id", user_id)
        .eq("params_hash", params_hash)
        .limit(1)
        .execute()
    )

    if not response.data:
        logger.warning(f"record_cache_fetch_failure: no cache key found for hash {params_hash[:12]}")
        return {}

    current_streak = response.data[0].get("fail_streak", 0) or 0
    new_streak = current_streak + 1
    backoff_min = calculate_backoff_minutes(new_streak)
    degraded_until = (now + timedelta(minutes=backoff_min)).isoformat()

    # Update with new values
    sb.table("search_results_cache").update({
        "fail_streak": new_streak,
        "last_attempt_at": now.isoformat(),
        "degraded_until": degraded_until,
    }).eq("user_id", user_id).eq("params_hash", params_hash).execute()

    logger.info(
        f"Cache key {params_hash[:12]} fail_streak={new_streak}, "
        f"degraded for {backoff_min}min"
    )

    return {"fail_streak": new_streak, "degraded_until": degraded_until}


async def is_cache_key_degraded(user_id: str, params_hash: str) -> bool:
    """B-03 AC5: Check if a cache key is currently degraded.

    Returns True if degraded_until > now(), meaning callers should
    avoid triggering a new fetch for this key.
    """
    from supabase_client import get_supabase
    sb = get_supabase()

    response = (
        sb.table("search_results_cache")
        .select("degraded_until")
        .eq("user_id", user_id)
        .eq("params_hash", params_hash)
        .limit(1)
        .execute()
    )

    if not response.data:
        return False

    degraded_until_str = response.data[0].get("degraded_until")
    if not degraded_until_str:
        return False

    try:
        degraded_until = datetime.fromisoformat(degraded_until_str.replace("Z", "+00:00"))
        if degraded_until.tzinfo is None:
            degraded_until = degraded_until.replace(tzinfo=timezone.utc)
        return degraded_until > datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return False


def _process_cache_hit(data: dict, params_hash: str, level: CacheLevel) -> Optional[dict]:
    """Process raw cache data, check TTL, return structured result or None."""
    fetched_at_str = data.get("fetched_at")
    if not fetched_at_str:
        return None

    fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00"))
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    age_hours = (now - fetched_at).total_seconds() / 3600

    # Expired entries are not served
    if age_hours > CACHE_STALE_HOURS:
        logger.info(
            f"Cache EXPIRED at L{_level_num(level)}/{level.value} "
            f"for hash {params_hash[:12]}... "
            f"(age={age_hours:.1f}h > {CACHE_STALE_HOURS}h)"
        )
        return None

    is_stale = age_hours > CACHE_FRESH_HOURS
    status = CacheStatus.STALE if is_stale else CacheStatus.FRESH

    # CRIT-004 AC14: Include search_id in cache hit/miss logs for correlation
    from middleware import search_id_var
    _search_id = search_id_var.get("-")
    logger.info(
        f"Cache HIT L{_level_num(level)}/{level.value} "
        f"[search={_search_id}] "
        f"for hash {params_hash[:12]}... "
        f"(age={age_hours:.1f}h, status={status.value})"
    )

    # B-02 AC8: Determine cache_priority from data if available
    priority_str = data.get("priority", "cold")
    access_count = data.get("access_count", 0)
    last_accessed_str = data.get("last_accessed_at")
    last_accessed = None
    if last_accessed_str:
        try:
            last_accessed = datetime.fromisoformat(str(last_accessed_str).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
    cache_priority = classify_priority(access_count, last_accessed)
    # If DB has a stored priority, prefer it for consistency
    try:
        cache_priority = CachePriority(priority_str)
    except (ValueError, KeyError):
        pass

    return {
        "results": data.get("results", []),
        "cached_at": fetched_at_str,
        "cached_sources": data.get("sources_json") or ["pncp"],
        "cache_age_hours": round(age_hours, 1),
        "is_stale": is_stale,
        "cache_level": level,
        "cache_status": status,
        "cache_priority": cache_priority,
    }


def _level_num(level: CacheLevel) -> int:
    """Map CacheLevel to numeric level for logging."""
    return {"supabase": 1, "redis": 2, "local": 3, "miss": 0}.get(level.value, 0)


# ============================================================================
# AC8: Local cache cleanup
# ============================================================================


def cleanup_local_cache() -> int:
    """Delete local cache files older than LOCAL_CACHE_TTL_HOURS (AC8).

    Returns the number of files deleted.
    """
    if not LOCAL_CACHE_DIR.exists():
        return 0

    now = datetime.now(timezone.utc)
    deleted_count = 0

    for file_path in LOCAL_CACHE_DIR.glob("*.json"):
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
            age_hours = (now - mtime).total_seconds() / 3600

            if age_hours > LOCAL_CACHE_TTL_HOURS:
                file_path.unlink()
                deleted_count += 1
        except OSError as e:
            logger.warning(f"Failed to clean up cache file {file_path}: {e}")

    if deleted_count > 0:
        logger.info(f"Cache cleanup: deleted {deleted_count} expired local files")

    return deleted_count


def get_local_cache_stats() -> dict:
    """Get statistics about local cache files for health check (AC7)."""
    if not LOCAL_CACHE_DIR.exists():
        return {"files_count": 0, "total_size_mb": 0.0}

    files = list(LOCAL_CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in files if f.exists())

    return {
        "files_count": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
    }


# ============================================================================
# AC3: Mixpanel tracking
# ============================================================================


def _track_cache_operation(
    operation: str,
    success: bool,
    level: CacheLevel,
    results_count: int,
    latency_ms: float,
    cache_age_seconds: float = 0,
) -> None:
    """Emit analytics event + increment counters for cache operations (B-05 AC2/AC4)."""
    try:
        from analytics_events import track_event
        track_event("cache_operation", {
            "operation": operation,
            "hit": success,
            "level": level.value,
            "cache_age_seconds": round(cache_age_seconds),
            "results_count": results_count,
            "latency_ms": round(latency_ms),
        })
    except Exception:
        pass  # Analytics failures are silent

    # B-05 AC4: Increment Redis/InMemory counters for metrics aggregation
    try:
        from redis_pool import get_fallback_cache
        cache = get_fallback_cache()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if operation == "read" or operation == "get":
            if success:
                cache.incr(f"cache_counter:hits:{today}")
                if cache_age_seconds > CACHE_FRESH_HOURS * 3600:
                    cache.incr(f"cache_counter:stale_served:{today}")
                else:
                    cache.incr(f"cache_counter:fresh_served:{today}")
            else:
                cache.incr(f"cache_counter:misses:{today}")
    except Exception:
        pass


# ============================================================================
# B-02 AC4/AC5/AC9: Access tracking, reclassification, proactive refresh
# ============================================================================


async def _increment_and_reclassify(
    user_id: str,
    params_hash: str,
    params: dict,
    result: dict,
) -> None:
    """B-02 AC4/AC5/AC9: Increment access_count, reclassify, trigger proactive refresh.

    Called after every cache hit. Updates Supabase with:
      - access_count + 1
      - last_accessed_at = now()
      - priority (if reclassified)
    AC9: If hot key is within 30min of expiry, dispatches proactive revalidation.
    """
    from supabase_client import get_supabase

    now = datetime.now(timezone.utc)

    try:
        sb = get_supabase()

        # Read current state
        resp = (
            sb.table("search_results_cache")
            .select("access_count, last_accessed_at, priority")
            .eq("user_id", user_id)
            .eq("params_hash", params_hash)
            .limit(1)
            .execute()
        )

        if not resp.data:
            return

        row = resp.data[0]
        old_count = row.get("access_count", 0) or 0
        old_priority = row.get("priority", "cold")
        new_count = old_count + 1

        # AC2: Reclassify with updated access_count
        new_priority = classify_priority(new_count, now)

        update_data = {
            "access_count": new_count,
            "last_accessed_at": now.isoformat(),
        }

        # AC5: Only update priority if it changed
        if new_priority.value != old_priority:
            update_data["priority"] = new_priority.value
            logger.info(
                f"Cache key {params_hash[:12]} reclassified: "
                f"{old_priority} → {new_priority.value} (access_count={new_count})"
            )

        sb.table("search_results_cache").update(update_data).eq(
            "user_id", user_id
        ).eq("params_hash", params_hash).execute()

        # Update result dict with current priority
        result["cache_priority"] = new_priority

        # AC9: Proactive refresh for hot keys near expiry
        cache_age_hours = result.get("cache_age_hours", 0)
        if new_priority == CachePriority.HOT and cache_age_hours >= (CACHE_FRESH_HOURS - 0.5):
            # Hot key within 30min of going stale — trigger proactive refresh
            try:
                dispatched = await trigger_background_revalidation(
                    user_id=user_id,
                    params=params,
                    request_data=params,
                )
                if dispatched:
                    logger.info(json.dumps({
                        "event": "proactive_refresh_dispatched",
                        "params_hash": params_hash[:12],
                        "cache_age_hours": cache_age_hours,
                        "priority": new_priority.value,
                    }))
            except Exception:
                pass  # Proactive refresh is best-effort

    except Exception as e:
        logger.debug(f"Access tracking failed for {params_hash[:12]}: {e}")


# ============================================================================
# B-01: Background Stale-While-Revalidate
# ============================================================================

# Module-level state for revalidation budget control (AC4)
_active_revalidations: int = 0
_revalidation_lock: Optional[asyncio.Lock] = None


def _get_revalidation_lock() -> asyncio.Lock:
    """Lazy init of revalidation lock (must be created inside event loop)."""
    global _revalidation_lock
    if _revalidation_lock is None:
        _revalidation_lock = asyncio.Lock()
    return _revalidation_lock


async def _is_revalidating(params_hash: str) -> bool:
    """AC3: Check if a revalidation is already in progress for this key."""
    from redis_pool import get_redis_pool, get_fallback_cache

    redis_key = f"revalidating:{params_hash}"

    redis = await get_redis_pool()
    if redis:
        try:
            return bool(await redis.exists(redis_key))
        except Exception:
            pass

    cache = get_fallback_cache()
    return cache.get(redis_key) is not None


async def _mark_revalidating(params_hash: str, ttl_seconds: int) -> bool:
    """AC3: Mark a key as being revalidated. Returns False if already marked."""
    from redis_pool import get_redis_pool, get_fallback_cache

    redis_key = f"revalidating:{params_hash}"

    redis = await get_redis_pool()
    if redis:
        try:
            acquired = await redis.set(redis_key, "1", ex=ttl_seconds, nx=True)
            return bool(acquired)
        except Exception:
            pass

    cache = get_fallback_cache()
    if cache.get(redis_key) is not None:
        return False
    cache.setex(redis_key, ttl_seconds, "1")
    return True


async def _clear_revalidating(params_hash: str) -> None:
    """Clear the revalidation dedup lock for a key."""
    from redis_pool import get_redis_pool, get_fallback_cache

    redis_key = f"revalidating:{params_hash}"

    redis = await get_redis_pool()
    if redis:
        try:
            await redis.delete(redis_key)
            return
        except Exception:
            pass

    cache = get_fallback_cache()
    cache.delete(redis_key)


async def trigger_background_revalidation(
    user_id: str,
    params: dict,
    request_data: dict,
    search_id: Optional[str] = None,
) -> bool:
    """B-01 AC1: Dispatch background revalidation after serving stale cache.

    Pre-checks (fast, no I/O beyond Redis):
      - AC6: PNCP circuit breaker not degraded
      - AC3: No concurrent revalidation for same params_hash (10min cooldown)
      - AC4: Worker revalidation budget not exceeded (max 3)

    If all pass, dispatches asyncio.Task for the actual revalidation.

    Args:
        user_id: Supabase user ID for cache key.
        params: Normalized search params (same dict used by compute_search_hash).
        request_data: Full request data for re-fetch (ufs, data_inicial, data_final, etc.).
        search_id: Optional SSE search_id for AC7 notification.

    Returns:
        True if background task was dispatched, False if skipped.
    """
    global _active_revalidations
    from config import REVALIDATION_COOLDOWN_S, MAX_CONCURRENT_REVALIDATIONS

    params_hash = compute_search_hash(params)

    # AC6: Check circuit breaker before wasting resources
    try:
        from pncp_client import get_circuit_breaker
        cb = get_circuit_breaker("pncp")
        if hasattr(cb, "is_degraded") and cb.is_degraded:
            logger.info(json.dumps({
                "event": "revalidation_skipped",
                "params_hash": params_hash[:12],
                "reason": "circuit_breaker_degraded",
            }))
            return False
    except Exception:
        pass  # If CB check fails, proceed anyway

    # AC3: Dedup — only one revalidation per key at a time
    if not await _mark_revalidating(params_hash, REVALIDATION_COOLDOWN_S):
        logger.info(json.dumps({
            "event": "revalidation_skipped",
            "params_hash": params_hash[:12],
            "reason": "already_revalidating",
        }))
        return False

    # AC4: Budget — max N concurrent revalidations per worker
    lock = _get_revalidation_lock()
    async with lock:
        if _active_revalidations >= MAX_CONCURRENT_REVALIDATIONS:
            await _clear_revalidating(params_hash)
            logger.info(json.dumps({
                "event": "revalidation_skipped",
                "params_hash": params_hash[:12],
                "reason": "budget_exceeded",
                "active": _active_revalidations,
                "max": MAX_CONCURRENT_REVALIDATIONS,
            }))
            return False
        _active_revalidations += 1

    # AC1: Dispatch background task
    asyncio.create_task(
        _do_revalidation(user_id, params, params_hash, request_data, search_id),
        name=f"revalidate:{params_hash[:12]}",
    )

    logger.info(json.dumps({
        "event": "revalidation_dispatched",
        "params_hash": params_hash[:12],
        "search_id": search_id,
    }))

    return True


async def _do_revalidation(
    user_id: str,
    params: dict,
    params_hash: str,
    request_data: dict,
    search_id: Optional[str],
) -> None:
    """Execute background revalidation (fire-and-forget task).

    1. Fetch fresh data from PNCP with independent timeout (AC5)
    2. On success: save_to_cache() resets fail_streak (AC2, AC9)
    3. On failure: record_cache_fetch_failure() increments fail_streak (AC9)
    4. If SSE tracker active: emit 'revalidated' event (AC7)
    5. Log structured JSON result (AC8)
    """
    global _active_revalidations
    from config import REVALIDATION_TIMEOUT

    start = time.monotonic()
    result_status = "unknown"
    new_results_count = 0

    try:
        # AC5: Independent timeout — does not affect active requests
        async with asyncio.timeout(REVALIDATION_TIMEOUT):
            import pncp_client as _pncp

            fetch_result = await _pncp.buscar_todas_ufs_paralelo(
                ufs=request_data["ufs"],
                data_inicial=request_data["data_inicial"],
                data_final=request_data["data_final"],
                modalidades=request_data.get("modalidades"),
            )

            # Handle ParallelFetchResult or plain list
            if hasattr(fetch_result, "items"):
                results = fetch_result.items
            elif isinstance(fetch_result, list):
                results = fetch_result
            else:
                results = list(fetch_result)

            new_results_count = len(results)

            if results:
                # AC2: Save to all cache levels
                sources = ["PNCP"]
                duration_ms = int((time.monotonic() - start) * 1000)
                coverage = {
                    "succeeded_ufs": list(request_data["ufs"]),
                    "failed_ufs": [],
                    "total_requested": len(request_data["ufs"]),
                }
                # AC9: save_to_cache resets fail_streak=0, last_success_at=now
                await save_to_cache(
                    user_id=user_id,
                    params=params,
                    results=results,
                    sources=sources,
                    fetch_duration_ms=duration_ms,
                    coverage=coverage,
                )
                result_status = "success"

                # AC7: SSE notification if tracker still active
                if search_id:
                    try:
                        from progress import get_tracker
                        tracker = await get_tracker(search_id)
                        if tracker and not tracker._is_complete:
                            await tracker.emit_revalidated(
                                total_results=new_results_count,
                                fetched_at=datetime.now(timezone.utc).isoformat(),
                            )
                    except Exception:
                        pass  # SSE notification is best-effort
            else:
                result_status = "empty"

    except asyncio.TimeoutError:
        result_status = "timeout"
        try:
            await record_cache_fetch_failure(user_id, params_hash)
        except Exception:
            pass

    except Exception as e:
        result_status = "error"
        try:
            await record_cache_fetch_failure(user_id, params_hash)
        except Exception:
            pass
        logger.debug(f"Revalidation fetch failed: {e}")

    finally:
        # Release budget slot (AC4)
        lock = _get_revalidation_lock()
        async with lock:
            _active_revalidations = max(0, _active_revalidations - 1)

        # AC8: Structured log — 1 JSON line per revalidation
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info(json.dumps({
            "event": "revalidation_complete",
            "params_hash": params_hash[:12],
            "trigger": "stale_served",
            "duration_ms": duration_ms,
            "result": result_status,
            "new_results_count": new_results_count,
        }))


# ============================================================================
# B-05: Admin Cache Metrics, Invalidation, Inspection
# ============================================================================


async def get_cache_metrics() -> dict:
    """B-05 AC3/AC4/AC10: Aggregate cache metrics for admin dashboard.

    Returns hit_rate_24h, miss_rate_24h, stale_served_24h, fresh_served_24h,
    total_entries, priority_distribution, age_distribution, degraded_keys,
    avg_fetch_duration_ms, top_keys.
    """
    from supabase_client import get_supabase
    from redis_pool import get_fallback_cache

    metrics: dict = {}

    # --- Counter-based metrics (AC4) ---
    try:
        cache = get_fallback_cache()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

        hits = int(cache.get(f"cache_counter:hits:{today}") or "0") + int(
            cache.get(f"cache_counter:hits:{yesterday}") or "0"
        )
        misses = int(cache.get(f"cache_counter:misses:{today}") or "0") + int(
            cache.get(f"cache_counter:misses:{yesterday}") or "0"
        )
        stale = int(cache.get(f"cache_counter:stale_served:{today}") or "0") + int(
            cache.get(f"cache_counter:stale_served:{yesterday}") or "0"
        )
        fresh = int(cache.get(f"cache_counter:fresh_served:{today}") or "0") + int(
            cache.get(f"cache_counter:fresh_served:{yesterday}") or "0"
        )

        total = hits + misses
        metrics["hit_rate_24h"] = round(hits / total, 2) if total > 0 else 0.0
        metrics["miss_rate_24h"] = round(misses / total, 2) if total > 0 else 0.0
        metrics["stale_served_24h"] = stale
        metrics["fresh_served_24h"] = fresh
    except Exception as e:
        logger.debug(f"Counter metrics failed: {e}")
        metrics.update({"hit_rate_24h": 0.0, "miss_rate_24h": 0.0, "stale_served_24h": 0, "fresh_served_24h": 0})

    # --- Supabase-based metrics ---
    try:
        sb = get_supabase()

        # Total entries
        all_entries = (
            sb.table("search_results_cache")
            .select("params_hash, priority, fetched_at, access_count, fail_streak, degraded_until, fetch_duration_ms")
            .execute()
        )
        rows = all_entries.data or []
        metrics["total_entries"] = len(rows)

        # Priority distribution (B-02 data)
        priority_dist = {"hot": 0, "warm": 0, "cold": 0}
        for row in rows:
            p = row.get("priority", "cold")
            if p in priority_dist:
                priority_dist[p] += 1
        metrics["priority_distribution"] = priority_dist

        # Age distribution (AC10)
        now = datetime.now(timezone.utc)
        age_dist = {"0-1h": 0, "1-6h": 0, "6-12h": 0, "12-24h": 0}
        for row in rows:
            fetched_str = row.get("fetched_at")
            if not fetched_str:
                continue
            try:
                fetched = datetime.fromisoformat(str(fetched_str).replace("Z", "+00:00"))
                if fetched.tzinfo is None:
                    fetched = fetched.replace(tzinfo=timezone.utc)
                age_h = (now - fetched).total_seconds() / 3600
                if age_h <= 1:
                    age_dist["0-1h"] += 1
                elif age_h <= 6:
                    age_dist["1-6h"] += 1
                elif age_h <= 12:
                    age_dist["6-12h"] += 1
                elif age_h <= 24:
                    age_dist["12-24h"] += 1
            except (ValueError, TypeError):
                continue
        metrics["age_distribution"] = age_dist

        # Degraded keys
        degraded = 0
        for row in rows:
            deg_str = row.get("degraded_until")
            if not deg_str:
                continue
            try:
                deg = datetime.fromisoformat(str(deg_str).replace("Z", "+00:00"))
                if deg.tzinfo is None:
                    deg = deg.replace(tzinfo=timezone.utc)
                if deg > now:
                    degraded += 1
            except (ValueError, TypeError):
                continue
        metrics["degraded_keys"] = degraded

        # Avg fetch duration
        durations = [
            row.get("fetch_duration_ms") for row in rows
            if row.get("fetch_duration_ms") is not None
        ]
        metrics["avg_fetch_duration_ms"] = (
            round(sum(float(d) for d in durations) / len(durations))
            if durations else 0
        )

        # Top keys (top 10 by access_count)
        sorted_rows = sorted(rows, key=lambda r: r.get("access_count", 0) or 0, reverse=True)[:10]
        top_keys = []
        for row in sorted_rows:
            fetched_str = row.get("fetched_at", "")
            age_h = 0.0
            if fetched_str:
                try:
                    fetched = datetime.fromisoformat(str(fetched_str).replace("Z", "+00:00"))
                    if fetched.tzinfo is None:
                        fetched = fetched.replace(tzinfo=timezone.utc)
                    age_h = round((now - fetched).total_seconds() / 3600, 1)
                except (ValueError, TypeError):
                    pass
            top_keys.append({
                "params_hash": row.get("params_hash", ""),
                "access_count": row.get("access_count", 0) or 0,
                "priority": row.get("priority", "cold"),
                "age_hours": age_h,
            })
        metrics["top_keys"] = top_keys

    except Exception as e:
        logger.warning(f"Supabase cache metrics query failed: {e}")
        metrics.setdefault("total_entries", 0)
        metrics.setdefault("priority_distribution", {"hot": 0, "warm": 0, "cold": 0})
        metrics.setdefault("age_distribution", {"0-1h": 0, "1-6h": 0, "6-12h": 0, "12-24h": 0})
        metrics.setdefault("degraded_keys", 0)
        metrics.setdefault("avg_fetch_duration_ms", 0)
        metrics.setdefault("top_keys", [])

    return metrics


async def invalidate_cache_entry(params_hash: str) -> dict:
    """B-05 AC5: Invalidate a specific cache entry across all 3 levels.

    Returns {"deleted_levels": [...]} listing which levels were successfully purged.
    """
    deleted_levels: list[str] = []

    # Level 1: Supabase
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        sb.table("search_results_cache").delete().eq("params_hash", params_hash).execute()
        deleted_levels.append("supabase")
    except Exception as e:
        logger.warning(f"Supabase invalidation failed for {params_hash[:12]}: {e}")

    # Level 2: Redis/InMemory
    try:
        from redis_pool import get_fallback_cache
        cache = get_fallback_cache()
        cache.delete(f"search_cache:{params_hash}")
        deleted_levels.append("redis")
    except Exception as e:
        logger.warning(f"Redis invalidation failed for {params_hash[:12]}: {e}")

    # Level 3: Local file
    try:
        cache_file = LOCAL_CACHE_DIR / f"{params_hash[:32]}.json"
        if cache_file.exists():
            cache_file.unlink()
        deleted_levels.append("local")
    except Exception as e:
        logger.warning(f"Local invalidation failed for {params_hash[:12]}: {e}")

    logger.info(f"Cache entry {params_hash[:12]} invalidated from: {deleted_levels}")
    return {"deleted_levels": deleted_levels}


async def invalidate_all_cache() -> dict:
    """B-05 AC6: Invalidate ALL cache entries across all levels.

    Returns {"deleted_counts": {"supabase": N, "redis": N, "local": N}}.
    """
    counts = {"supabase": 0, "redis": 0, "local": 0}

    # Level 1: Supabase — delete all rows
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        # Delete all cache entries (use gte on created_at to match all)
        result = sb.table("search_results_cache").delete().gte(
            "created_at", "2000-01-01"
        ).execute()
        counts["supabase"] = len(result.data) if result.data else 0
    except Exception as e:
        logger.warning(f"Supabase bulk invalidation failed: {e}")

    # Level 2: Redis/InMemory — clear search_cache:* keys
    try:
        from redis_pool import get_fallback_cache
        cache = get_fallback_cache()
        keys = cache.keys_by_prefix("search_cache:")
        for k in keys:
            cache.delete(k)
        counts["redis"] = len(keys)
    except Exception as e:
        logger.warning(f"Redis bulk invalidation failed: {e}")

    # Level 3: Local files
    try:
        if LOCAL_CACHE_DIR.exists():
            files = list(LOCAL_CACHE_DIR.glob("*.json"))
            for f in files:
                f.unlink(missing_ok=True)
            counts["local"] = len(files)
    except Exception as e:
        logger.warning(f"Local bulk invalidation failed: {e}")

    logger.info(f"All cache invalidated: {counts}")
    return {"deleted_counts": counts}


async def inspect_cache_entry(params_hash: str) -> Optional[dict]:
    """B-05 AC7: Return full details of a specific cache entry.

    Returns all fields: search_params, results_count, sources, fetched_at,
    priority, fail_streak, degraded_until, coverage, access_count, last_accessed_at.
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        response = (
            sb.table("search_results_cache")
            .select(
                "params_hash, user_id, search_params, total_results, sources_json, "
                "fetched_at, created_at, priority, access_count, last_accessed_at, "
                "fail_streak, degraded_until, coverage, fetch_duration_ms, "
                "last_success_at, last_attempt_at"
            )
            .eq("params_hash", params_hash)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        row = response.data[0]

        # Calculate age
        fetched_str = row.get("fetched_at") or row.get("created_at")
        age_hours = 0.0
        cache_status = "unknown"
        if fetched_str:
            try:
                fetched = datetime.fromisoformat(str(fetched_str).replace("Z", "+00:00"))
                if fetched.tzinfo is None:
                    fetched = fetched.replace(tzinfo=timezone.utc)
                age_hours = round((datetime.now(timezone.utc) - fetched).total_seconds() / 3600, 1)
                status = get_cache_status(fetched)
                cache_status = status.value
            except (ValueError, TypeError):
                pass

        return {
            "params_hash": row.get("params_hash"),
            "user_id": row.get("user_id"),
            "search_params": row.get("search_params"),
            "results_count": row.get("total_results", 0),
            "sources": row.get("sources_json", []),
            "fetched_at": row.get("fetched_at"),
            "created_at": row.get("created_at"),
            "priority": row.get("priority", "cold"),
            "access_count": row.get("access_count", 0) or 0,
            "last_accessed_at": row.get("last_accessed_at"),
            "fail_streak": row.get("fail_streak", 0) or 0,
            "degraded_until": row.get("degraded_until"),
            "coverage": row.get("coverage"),
            "fetch_duration_ms": row.get("fetch_duration_ms"),
            "last_success_at": row.get("last_success_at"),
            "last_attempt_at": row.get("last_attempt_at"),
            "age_hours": age_hours,
            "cache_status": cache_status,
        }
    except Exception as e:
        logger.warning(f"Cache inspection failed for {params_hash[:12]}: {e}")
        return None
