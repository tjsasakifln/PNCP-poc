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

    sb.table("search_results_cache").upsert(
        row, on_conflict="user_id,params_hash"
    ).execute()


async def _get_from_supabase(user_id: str, params_hash: str) -> Optional[dict]:
    """Read from Supabase cache (Level 1)."""
    from supabase_client import get_supabase
    sb = get_supabase()

    response = (
        sb.table("search_results_cache")
        .select("results, total_results, sources_json, fetched_at, created_at")
        .eq("user_id", user_id)
        .eq("params_hash", params_hash)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    row = response.data[0]
    fetched_at_str = row.get("fetched_at") or row.get("created_at")
    return {
        "results": row.get("results", []),
        "total_results": row.get("total_results", 0),
        "sources_json": row.get("sources_json"),
        "fetched_at": fetched_at_str,
    }


# ============================================================================
# Level 2: Redis / InMemoryCache (volatile, 4h TTL)
# ============================================================================


def _save_to_redis(cache_key: str, results: list, sources: list[str]) -> None:
    """Save to Redis/InMemory cache (Level 2)."""
    from redis_pool import get_fallback_cache
    cache = get_fallback_cache()

    cache_data = json.dumps({
        "results": results,
        "sources_json": sources,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    })
    cache.setex(f"search_cache:{cache_key}", REDIS_CACHE_TTL_SECONDS, cache_data)


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
    Returns dict with: results, cached_at, cached_sources, cache_age_hours,
                       is_stale, cache_level
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
                return result
    except Exception as e:
        logger.error(f"Local cache read failed: {e}")

    # Miss across all levels
    elapsed = (time.monotonic() - start) * 1000
    logger.info(f"Cache MISS all levels for hash {params_hash[:12]}... ({elapsed:.0f}ms)")
    _track_cache_operation("read", False, CacheLevel.MISS, 0, elapsed)
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

    logger.info(
        f"Cache HIT L{_level_num(level)}/{level.value} "
        f"for hash {params_hash[:12]}... "
        f"(age={age_hours:.1f}h, status={status.value})"
    )

    return {
        "results": data.get("results", []),
        "cached_at": fetched_at_str,
        "cached_sources": data.get("sources_json") or ["pncp"],
        "cache_age_hours": round(age_hours, 1),
        "is_stale": is_stale,
        "cache_level": level,
        "cache_status": status,
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
    """Emit Mixpanel event for cache operations (AC3). Fire-and-forget."""
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
