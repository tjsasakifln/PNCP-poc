"""UX-303: Multi-level cache with Supabase → Redis/InMemory → Local file fallback.

Built on GTM-FIX-010 foundation. Adds:
  - 3-level save fallback: Supabase → Redis → Local file
  - 3-level read fallback: Supabase → Redis → Local file
  - CacheLevel / CacheStatus enums
  - Mixpanel tracking for cache hit rates (AC3)
  - Sentry alerting with structured context (AC6)
  - Local file cache management

STORY-306 — Cache Correctness & Data Integrity:
  - Cache key now includes date_from/date_to (AC1-AC4)
  - Dual-read: exact key → legacy key (without dates) for thundering herd mitigation (AC12)
  - Fallback explicitly marked with cache_fallback=True + cache_date_range (AC5/AC7)

TTL Policy (STORY-306 AC8-AC11 — single source of truth):
  ┌─────────────────────┬──────┬─────────────┬────────────────────────────────────┐
  │ Layer               │ TTL  │ Status      │ Behavior                           │
  ├─────────────────────┼──────┼─────────────┼────────────────────────────────────┤
  │ L1 InMemory/Redis   │ 4h   │ Fresh 0-4h  │ Serve directly, fastest            │
  │ L2 Supabase         │ 24h  │ Stale 4-24h │ Serve + trigger SWR revalidation   │
  │ L3 Local File       │ 24h  │ Emergency   │ Serve only if Supabase down        │
  └─────────────────────┴──────┴─────────────┴────────────────────────────────────┘
  - Fresh (0-4h): Serve directly from any layer
  - Stale (4-24h): Serve from L2/L3 + trigger background revalidation (SWR)
  - Expired (>24h): Not served; new fetch required (except allow_expired=True for last-resort)
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

from utils.error_reporting import report_error  # GTM-RESILIENCE-E02: centralized error emission
from metrics import CACHE_HITS as METRICS_CACHE_HITS, CACHE_MISSES as METRICS_CACHE_MISSES

logger = logging.getLogger(__name__)

# TTL boundaries (hours) — STORY-306 AC8/AC9: single source of truth
# AC9: L1 (InMemory) and Redis share the same TTL (4h)
CACHE_FRESH_HOURS = 4  # STORY-306: was 6, aligned with REDIS_CACHE_TTL_SECONDS
CACHE_STALE_HOURS = 24  # L2 Supabase / L3 Local file — SWR window

# Local cache directory (platform-aware)
LOCAL_CACHE_DIR = Path(
    os.getenv("SMARTLIC_CACHE_DIR", "/tmp/smartlic_cache")
    if platform.system() != "Windows"
    else os.getenv("SMARTLIC_CACHE_DIR", os.path.join(os.environ.get("TEMP", "C:\\Temp"), "smartlic_cache"))
)
LOCAL_CACHE_TTL_HOURS = 24  # Max age for local cache files
LOCAL_CACHE_MAX_SIZE_MB = 200  # HARDEN-018: max dir size before eviction
LOCAL_CACHE_TARGET_SIZE_MB = 100  # HARDEN-018: evict until below this
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


def _normalize_date(value) -> str | None:
    """STORY-306 AC2: Normalize date to ISO 8601 (YYYY-MM-DD) for cache key stability."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    # Accept common formats: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, DD/MM/YYYY
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%d/%m/%Y"):
        try:
            return datetime.strptime(s[:10] if "T" in s and fmt == "%Y-%m-%d" else s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Last resort: take first 10 chars if it looks like a date
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s


def compute_search_hash(params: dict) -> str:
    """STORY-306 AC1-AC4: Deterministic hash including ALL params that affect results.

    Now includes date_from/date_to so that different date ranges produce different
    cache keys. For legacy fallback (thundering herd mitigation), use
    compute_search_hash_without_dates().

    DEBT-018 SYS-021: Added termos_busca, valor_minimo, valor_maximo, esferas,
    municipios, exclusion_terms, show_all_matches — these all affect filtered results.
    """
    normalized = {
        "setor_id": params.get("setor_id"),
        "ufs": sorted(params.get("ufs", [])),
        "status": params.get("status"),
        "modalidades": sorted(params.get("modalidades") or []) or None,
        "modo_busca": params.get("modo_busca"),
        # STORY-306 AC1/AC2: Include dates, normalized to YYYY-MM-DD
        "date_from": _normalize_date(params.get("date_from") or params.get("data_inicio") or params.get("data_inicial")),
        "date_to": _normalize_date(params.get("date_to") or params.get("data_fim") or params.get("data_final")),
        # SYS-021: Additional filter parameters that affect results
        "termos_busca": params.get("termos_busca") or None,
        "valor_minimo": params.get("valor_minimo"),
        "valor_maximo": params.get("valor_maximo"),
        "esferas": sorted(params.get("esferas") or []) or None,
        "municipios": sorted(params.get("municipios") or []) or None,
        "exclusion_terms": sorted(params.get("exclusion_terms") or []) or None,
        "show_all_matches": params.get("show_all_matches") or False,
    }
    params_json = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(params_json.encode()).hexdigest()


def compute_search_hash_without_dates(params: dict) -> str:
    """STORY-306 AC12: Legacy hash WITHOUT dates for dual-read thundering herd mitigation.

    Used during deploy transition: if new key (with dates) misses, fall back to
    old key (without dates) which may still have cached data from before the deploy.
    Also used for AC5/AC7: fallback when all sources fail — serve any date range.
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


def compute_search_hash_per_uf(params: dict, uf: str) -> str:
    """CRIT-051 AC1: Deterministic hash for a SINGLE UF (composable cache).

    Same as compute_search_hash but always uses ufs=[single_uf].
    This allows warmup (which caches per-UF) and multi-UF searches
    (which compose from per-UF entries) to share the same cache keys.

    DEBT-018 SYS-021: Includes all filter parameters for cache key correctness.
    """
    normalized = {
        "setor_id": params.get("setor_id"),
        "ufs": [uf],  # Single UF, always sorted (just one element)
        "status": params.get("status"),
        "modalidades": sorted(params.get("modalidades") or []) or None,
        "modo_busca": params.get("modo_busca"),
        "date_from": _normalize_date(params.get("date_from") or params.get("data_inicio") or params.get("data_inicial")),
        "date_to": _normalize_date(params.get("date_to") or params.get("data_fim") or params.get("data_final")),
        # SYS-021: Additional filter parameters
        "termos_busca": params.get("termos_busca") or None,
        "valor_minimo": params.get("valor_minimo"),
        "valor_maximo": params.get("valor_maximo"),
        "esferas": sorted(params.get("esferas") or []) or None,
        "municipios": sorted(params.get("municipios") or []) or None,
        "exclusion_terms": sorted(params.get("exclusion_terms") or []) or None,
        "show_all_matches": params.get("show_all_matches") or False,
    }
    params_json = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(params_json.encode()).hexdigest()


def compute_global_hash(params: dict) -> str:
    """GTM-ARCH-002 AC2: Global cache hash — setor + ufs + dates, WITHOUT user_id.

    Used for cross-user cache fallback: when a trial user has no personal cache,
    the system falls back to any user's cache with the same global hash.
    """
    normalized = {
        "setor_id": params.get("setor_id"),
        "ufs": sorted(params.get("ufs", [])),
        "data_inicio": params.get("data_inicio") or params.get("data_inicial"),
        "data_fim": params.get("data_fim") or params.get("data_final"),
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
    GTM-ARCH-002 AC3: Also stores params_hash_global for cross-user fallback.
    """
    from supabase_client import get_supabase, sb_execute
    sb = get_supabase()

    now = datetime.now(timezone.utc).isoformat()
    row = {
        "user_id": user_id,
        "params_hash": params_hash,
        "params_hash_global": compute_global_hash(params),  # GTM-ARCH-002 AC2
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

    # STORY-265 AC2: Application-level JSONB size guard (2 MB limit)
    # Defense-in-depth: truncates results before DB CHECK constraint rejects the insert
    JSONB_MAX_BYTES = 2_097_152  # 2 MB — matches chk_results_max_size constraint
    results_size = len(json.dumps(results).encode("utf-8"))
    if results_size > JSONB_MAX_BYTES:
        original_count = len(results)
        # Truncate from the end until under limit
        while results and len(json.dumps(results).encode("utf-8")) > JSONB_MAX_BYTES:
            results = results[: len(results) * 3 // 4]  # Remove 25% each pass
        row["results"] = results
        row["total_results"] = len(results)
        logger.warning(
            "STORY-265: results JSONB truncated",
            extra={
                "original_count": original_count,
                "truncated_count": len(results),
                "original_bytes": results_size,
                "user_id": user_id,
                "params_hash": params_hash[:12],
            },
        )

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

    # PHASE-0: Retry once on transient Supabase errors + detailed error logging
    _max_retries = 1
    for _attempt in range(_max_retries + 1):
        try:
            await sb_execute(
                sb.table("search_results_cache").upsert(
                    row, on_conflict="user_id,params_hash"
                )
            )
            return  # Success
        except Exception as _upsert_err:
            _err_type = type(_upsert_err).__name__
            _err_msg = str(_upsert_err)[:300]
            if _attempt < _max_retries:
                logger.warning(
                    f"PHASE-0: _save_to_supabase attempt {_attempt + 1} failed "
                    f"({_err_type}: {_err_msg}), retrying in 1s..."
                )
                await asyncio.sleep(1)
            else:
                logger.error(
                    f"PHASE-0: _save_to_supabase FAILED after {_max_retries + 1} attempts — "
                    f"{_err_type}: {_err_msg} "
                    f"(user_id={user_id[:8]}, hash={params_hash[:12]}, "
                    f"n_results={len(results)}, row_keys={sorted(row.keys())})"
                )
                raise


async def _get_from_supabase(user_id: str, params_hash: str) -> Optional[dict]:
    """Read from Supabase cache (Level 1).

    B-02 AC8: Also returns priority, access_count, last_accessed_at for classification.
    """
    from supabase_client import get_supabase, sb_execute
    sb = get_supabase()

    response = await sb_execute(
        sb.table("search_results_cache")
        .select("results, total_results, sources_json, fetched_at, created_at, priority, access_count, last_accessed_at")
        .eq("user_id", user_id)
        .eq("params_hash", params_hash)
        .order("created_at", desc=True)
        .limit(1)
    )

    if not response.data:
        return None

    row = response.data[0]

    # CRIT-001 AC11: Validate expected fields are present, use defaults if missing
    try:
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
# GTM-ARCH-002 AC1/AC4: Global cross-user cache fallback
# ============================================================================


async def _get_global_fallback_from_supabase(params: dict) -> Optional[dict]:
    """GTM-ARCH-002 AC1/AC4: Cross-user global cache fallback.

    Queries ANY user's cache with the same params_hash_global.
    Used when a user (especially trial) has no personal cache.
    Read-only: does NOT write to the user's own cache.
    """
    from supabase_client import get_supabase, sb_execute
    sb = get_supabase()

    global_hash = compute_global_hash(params)

    response = await sb_execute(
        sb.table("search_results_cache")
        .select("results, total_results, sources_json, fetched_at, created_at, priority, access_count, last_accessed_at")
        .eq("params_hash_global", global_hash)
        .order("created_at", desc=True)
        .limit(1)
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


def _check_cache_dir_size() -> int:
    """HARDEN-018 AC1/AC2: Check local cache dir size, evict oldest files if > 200MB.

    Deletes oldest files (by mtime) until total size is below 100MB.
    Returns the number of files deleted.
    """
    if not LOCAL_CACHE_DIR.exists():
        return 0

    files = list(LOCAL_CACHE_DIR.glob("*.json"))
    if not files:
        return 0

    # AC1: Calculate total size
    file_stats = []
    total_size = 0
    for f in files:
        try:
            st = f.stat()
            file_stats.append((f, st.st_mtime, st.st_size))
            total_size += st.st_size
        except OSError:
            continue

    max_bytes = LOCAL_CACHE_MAX_SIZE_MB * 1024 * 1024
    if total_size <= max_bytes:
        return 0

    # AC2: Sort by mtime ascending (oldest first), delete until < 100MB
    target_bytes = LOCAL_CACHE_TARGET_SIZE_MB * 1024 * 1024
    file_stats.sort(key=lambda x: x[1])  # oldest first

    deleted = 0
    for file_path, _mtime, size in file_stats:
        if total_size <= target_bytes:
            break
        try:
            file_path.unlink()
            total_size -= size
            deleted += 1
        except OSError as e:
            logger.warning(f"HARDEN-018: Failed to evict cache file {file_path}: {e}")

    if deleted > 0:
        logger.info(
            f"HARDEN-018: Evicted {deleted} oldest cache files, "
            f"dir now ~{total_size / (1024 * 1024):.1f}MB"
        )

    return deleted


def _save_to_local(cache_key: str, results: list, sources: list[str]) -> None:
    """Save to local JSON file (Level 3)."""
    LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _check_cache_dir_size()  # HARDEN-018 AC3: enforce size limit before write

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

    STORY-271: System warming user (WARMING_USER_ID) skips L1 Supabase because
    the nil UUID cannot have a profiles row (profiles.id FK → auth.users).
    """
    params_hash = compute_search_hash(params)
    start = time.monotonic()

    # STORY-271: Skip L1 Supabase for system warming user (nil UUID has no profiles row)
    from config import WARMING_USER_ID
    skip_supabase = (user_id == WARMING_USER_ID)

    # Level 1: Supabase
    if skip_supabase:
        logger.debug(
            f"Cache SAVE skipping L1/supabase for warming user "
            f"(key={params_hash[:12]}, n={len(results)})"
        )
    else:
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
# CRIT-051: Per-UF composable cache save
# ============================================================================


async def save_to_cache_per_uf(
    user_id: str,
    params: dict,
    results: list,
    sources: list[str],
    *,
    fetch_duration_ms: Optional[int] = None,
    coverage: Optional[dict] = None,
) -> dict:
    """CRIT-051 AC1: Save results grouped by UF — one cache entry per UF.

    Groups results by their 'uf' field and saves each UF's results independently.
    Also saves the combined entry (retrocompatibility with old hash).
    Returns dict with {level, success, ufs_saved}.
    """

    # Group results by UF
    results_by_uf: dict[str, list] = {}
    no_uf_results = []
    for r in results:
        uf = r.get("uf", "").upper()
        if uf:
            results_by_uf.setdefault(uf, []).append(r)
        else:
            no_uf_results.append(r)

    ufs_saved = []
    first_result = {"level": CacheLevel.MISS, "success": False}

    # Save per-UF entries
    for uf, uf_results in results_by_uf.items():
        per_uf_params = {**params, "ufs": [uf]}
        try:
            result = await save_to_cache(
                user_id, per_uf_params, uf_results, sources,
                fetch_duration_ms=fetch_duration_ms, coverage=coverage,
            )
            if result.get("success"):
                ufs_saved.append(uf)
                if first_result["level"] == CacheLevel.MISS:
                    first_result = result
        except Exception as e:
            logger.warning(f"CRIT-051: Failed to save per-UF cache for {uf}: {e}")

    # Also save combined entry for retrocompatibility (AC6)
    try:
        await save_to_cache(
            user_id, params, results, sources,
            fetch_duration_ms=fetch_duration_ms, coverage=coverage,
        )
    except Exception as e:
        logger.debug(f"CRIT-051: Combined cache save failed (non-fatal, per-UF already saved): {e}")

    logger.info(
        f"CRIT-051: Per-UF cache saved {len(ufs_saved)}/{len(results_by_uf)} UFs "
        f"({len(results)} total results, {len(no_uf_results)} without UF)"
    )
    first_result["ufs_saved"] = ufs_saved
    return first_result


# ============================================================================
# CRIT-051: Per-UF composable cache read
# ============================================================================

# Configurable threshold for partial cache hits (AC2)
CACHE_PARTIAL_HIT_THRESHOLD = float(os.getenv("CACHE_PARTIAL_HIT_THRESHOLD", "0.5"))


async def get_from_cache_composed(
    user_id: str,
    params: dict,
) -> Optional[dict]:
    """CRIT-051 AC2: Compose cache results from individual UF entries.

    For each UF in the request, tries to find a per-UF cache entry.
    Returns composed results if >= CACHE_PARTIAL_HIT_THRESHOLD of UFs are cached.

    Returns dict with:
        results, cached_at, cached_sources, cache_age_hours, is_stale,
        cache_level, cached_ufs, missing_ufs, composition_coverage
    Returns None if insufficient cache coverage.
    """
    from metrics import CACHE_COMPOSITION_TOTAL, CACHE_COMPOSITION_COVERAGE

    ufs = sorted(params.get("ufs", []))
    if not ufs or len(ufs) <= 1:
        # Single UF — no composition needed, use regular cache
        return await get_from_cache(user_id, params)

    cached_ufs = []
    missing_ufs = []
    all_results = []
    oldest_cached_at = None
    worst_status = "fresh"
    sources_seen = set()
    cache_levels_seen = set()

    for uf in ufs:
        per_uf_params = {**params, "ufs": [uf]}
        try:
            entry = await get_from_cache(user_id, per_uf_params)
            if entry and entry.get("results"):
                cached_ufs.append(uf)
                all_results.extend(entry["results"])

                # Track oldest entry for freshness
                entry_cached_at = entry.get("cached_at")
                if entry_cached_at:
                    if oldest_cached_at is None or entry_cached_at < oldest_cached_at:
                        oldest_cached_at = entry_cached_at

                # Track worst status
                entry_status = entry.get("cache_status", "fresh")
                if entry_status == "expired" or (entry_status == "stale" and worst_status == "fresh"):
                    worst_status = entry_status

                # Collect sources and levels
                for src in (entry.get("cached_sources") or []):
                    sources_seen.add(src)
                if entry.get("cache_level"):
                    cache_levels_seen.add(entry["cache_level"])
            else:
                missing_ufs.append(uf)
        except Exception as e:
            logger.debug(f"CRIT-051: Per-UF cache read failed for {uf}: {e}")
            missing_ufs.append(uf)

    coverage = len(cached_ufs) / len(ufs) if ufs else 0
    coverage_pct = coverage * 100
    CACHE_COMPOSITION_COVERAGE.observe(coverage_pct)

    if coverage < CACHE_PARTIAL_HIT_THRESHOLD:
        CACHE_COMPOSITION_TOTAL.labels(result="miss").inc()
        logger.info(
            f"CRIT-051: Cache composition MISS — {len(cached_ufs)}/{len(ufs)} UFs "
            f"({coverage_pct:.0f}% < {CACHE_PARTIAL_HIT_THRESHOLD*100:.0f}% threshold)"
        )
        return None

    # CRIT-051 AC5: Dedup cross-UF
    all_results = _dedup_cross_uf(all_results)

    result_type = "full_hit" if not missing_ufs else "partial_hit"
    CACHE_COMPOSITION_TOTAL.labels(result=result_type).inc()

    logger.info(
        f"CRIT-051: Cache composition {result_type} — {len(cached_ufs)}/{len(ufs)} UFs, "
        f"{len(all_results)} results (deduped)"
    )

    return {
        "results": all_results,
        "cached_at": oldest_cached_at,
        "cached_sources": sorted(sources_seen),
        "cache_age_hours": _compute_age_hours(oldest_cached_at),
        "is_stale": worst_status != "fresh",
        "cache_level": "composed",
        "cache_status": worst_status,
        "cache_priority": "warm",
        "cache_fallback": False,
        "cache_date_range": None,
        # CRIT-051 specific fields
        "cached_ufs": cached_ufs,
        "missing_ufs": missing_ufs,
        "composition_coverage": coverage_pct,
    }


def _dedup_cross_uf(results: list) -> list:
    """CRIT-051 AC5: Deduplicate results that appear in multiple UFs.

    Uses codigoCompra (numeroControlePNCP) as primary dedup key,
    falls back to (nomeOrgao + objetoCompra[:100]) for PCP/ComprasGov.
    """
    seen: dict[str, dict] = {}
    deduped = []
    for r in results:
        # Primary key: codigoCompra / numeroControlePNCP
        key = r.get("codigoCompra") or r.get("numeroControlePNCP", "")
        if not key:
            # Fallback key for non-PNCP sources
            orgao = r.get("nomeOrgao", "")
            obj = (r.get("objetoCompra") or "")[:100]
            key = f"{orgao}|{obj}" if orgao and obj else ""

        if not key:
            deduped.append(r)
            continue

        if key not in seen:
            seen[key] = r
            deduped.append(r)

    return deduped


def _compute_age_hours(cached_at: Optional[str]) -> float:
    """Compute age in hours from an ISO timestamp string."""
    if not cached_at:
        return 0.0
    try:
        dt = datetime.fromisoformat(str(cached_at).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except (ValueError, TypeError):
        return 0.0


# ============================================================================
# Multi-level read (AC2)
# ============================================================================


async def get_from_cache(
    user_id: str,
    params: dict,
) -> Optional[dict]:
    """Retrieve cached results with 3-level fallback (AC2).

    STORY-306 AC7/AC12: Dual-read — tries exact key (with dates) first across all
    levels, then falls back to legacy key (without dates) if CACHE_LEGACY_KEY_FALLBACK
    is enabled. Legacy-key results are marked with cache_fallback=True.

    Cascade per key: Supabase → Redis/InMemory → Local file → Global.
    B-02 AC4: Increments access_count on Supabase after each hit.
    Returns dict with: results, cached_at, cached_sources, cache_age_hours,
                       is_stale, cache_level, cache_priority,
                       cache_fallback (bool), cache_date_range (str|None)
    Returns None if no valid cache entry exists.
    """
    params_hash = compute_search_hash(params)
    start = time.monotonic()

    # --- Try exact key (with dates) across all levels ---
    result = await _read_all_levels(user_id, params_hash, params, start)
    if result:
        return result

    # --- STORY-306 AC12: Dual-read — try legacy key (without dates) ---
    from config import CACHE_LEGACY_KEY_FALLBACK
    if CACHE_LEGACY_KEY_FALLBACK:
        legacy_hash = compute_search_hash_without_dates(params)
        if legacy_hash != params_hash:  # Only if key actually differs
            result = await _read_all_levels(user_id, legacy_hash, params, start)
            if result:
                # AC5: Mark as fallback with date range from cached entry
                result["cache_fallback"] = True
                cached_at = result.get("cached_at")
                result["cache_date_range"] = _format_cache_date_range(cached_at)
                logger.info(
                    f"Cache HIT via legacy key (without dates) for hash "
                    f"{legacy_hash[:12]}... (fallback from {params_hash[:12]})"
                )
                return result

    # Miss across all levels (including legacy fallback)
    elapsed = (time.monotonic() - start) * 1000
    from middleware import search_id_var
    _search_id_miss = search_id_var.get("-")
    logger.info(f"Cache MISS all levels [search={_search_id_miss}] for hash {params_hash[:12]}... ({elapsed:.0f}ms)")
    _track_cache_operation("read", False, CacheLevel.MISS, 0, elapsed)
    METRICS_CACHE_MISSES.labels(level="all").inc()
    return None


async def _read_all_levels(
    user_id: str,
    params_hash: str,
    params: dict,
    start: float,
) -> Optional[dict]:
    """STORY-306: Read cache across all levels for a given hash key.

    Extracted from get_from_cache to enable dual-read (exact + legacy key).
    Returns structured cache result or None.
    """
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
                await _increment_and_reclassify(user_id, params_hash, params, result)
                return result
    except Exception as e:
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

    # GTM-ARCH-002 AC1: Global cross-user fallback
    try:
        global_data = await _get_global_fallback_from_supabase(params)
        if global_data:
            result = _process_cache_hit(global_data, params_hash, CacheLevel.SUPABASE)
            if result:
                elapsed = (time.monotonic() - start) * 1000
                result["cache_level"] = "global"
                _track_cache_operation(
                    "read", True, CacheLevel.SUPABASE,
                    len(result["results"]), elapsed,
                    cache_age_seconds=result["cache_age_hours"] * 3600,
                )
                METRICS_CACHE_HITS.labels(level="global", freshness=result.get("cache_status", "stale")).inc()
                logger.info(
                    f"Cache HIT global fallback for hash {params_hash[:12]}... "
                    f"({elapsed:.0f}ms, {len(result['results'])} results)"
                )
                return result
    except Exception as e:
        logger.debug(f"Global cache fallback failed: {e}")

    return None


def _format_cache_date_range(cached_at: str | None) -> str | None:
    """STORY-306 AC5: Format cache date range for user display."""
    if not cached_at:
        return None
    try:
        dt = datetime.fromisoformat(cached_at.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return cached_at


# ============================================================================
# A-03 AC3: Unified cascade read (L2 → L1 → L3)
# ============================================================================


def _all_sources_down() -> bool:
    """CRIT-081: Check if all data source circuit breakers are open/degraded.

    Returns True only when PNCP, PCP, and ComprasGov are all degraded,
    meaning no live data is obtainable and expired cache should be served.
    Returns False on any error (fail-open — better to try live sources than
    refuse to serve).
    """
    try:
        from pncp_client import get_circuit_breaker
        cb_pncp = get_circuit_breaker("pncp")
        cb_pcp = get_circuit_breaker("pcp")
        cb_comprasgov = get_circuit_breaker("comprasgov")
        return (
            cb_pncp.is_degraded
            and cb_pcp.is_degraded
            and cb_comprasgov.is_degraded
        )
    except Exception:
        return False  # Fail-open: assume sources are up


async def get_from_cache_cascade(
    user_id: str,
    params: dict,
    *,
    allow_expired: bool = False,
) -> Optional[dict]:
    """Unified cache cascade: L2 (InMemory/Redis) → L1 (Supabase) → L3 (Local file).

    A-03 AC3: Tries all 3 levels in order of speed (no I/O → HTTP → disk).
    A-03 AC4: Returns cache_level as "memory" | "supabase" | "local".
    A-03 AC9: Logs event "cache_l3_served" when L3 provides the data.

    STORY-306 AC7/AC12: Dual-read — tries exact key first, then legacy key
    (without dates) if CACHE_LEGACY_KEY_FALLBACK is enabled.

    P1.3: allow_expired=True — serve entries older than CACHE_STALE_HOURS (>24h) as a
    last-resort fallback when all live sources have failed. Returned dict includes
    is_expired=True so callers can set response_state="degraded_expired".

    Returns dict with: results, cached_at, cached_sources, cache_age_hours,
                       is_stale, is_expired (when allow_expired=True), cache_level, cache_status,
                       cache_fallback (bool), cache_date_range (str|None)
    Returns None if no valid cache entry exists at any level.
    """
    params_hash = compute_search_hash(params)

    # Select the appropriate hit processor
    _hit_fn = _process_cache_hit_allow_expired if allow_expired else _process_cache_hit

    # --- Try exact key (with dates) across all cascade levels ---
    result = _cascade_read_levels(user_id, params_hash, params, _hit_fn)
    if asyncio.iscoroutine(result):
        result = await result
    if result:
        return result

    # --- STORY-306 AC12: Dual-read — try legacy key (without dates) ---
    from config import CACHE_LEGACY_KEY_FALLBACK
    if CACHE_LEGACY_KEY_FALLBACK:
        legacy_hash = compute_search_hash_without_dates(params)
        if legacy_hash != params_hash:
            result = _cascade_read_levels(user_id, legacy_hash, params, _hit_fn)
            if asyncio.iscoroutine(result):
                result = await result
            if result:
                result["cache_fallback"] = True
                cached_at = result.get("cached_at")
                result["cache_date_range"] = _format_cache_date_range(cached_at)
                logger.info(
                    f"Cascade HIT via legacy key (without dates) for hash "
                    f"{legacy_hash[:12]}... (fallback from {params_hash[:12]})"
                )
                return result

    # CRIT-081: If all sources are down and feature is enabled, auto-retry with allow_expired
    if not allow_expired:
        try:
            from config import SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE
            if SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE and _all_sources_down():
                logger.warning(
                    "CRIT-081: All sources down — retrying cascade with allow_expired=True "
                    "for hash %s...",
                    params_hash[:12],
                )
                result = _cascade_read_levels(
                    user_id, params_hash, params, _process_cache_hit_allow_expired
                )
                if asyncio.iscoroutine(result):
                    result = await result
                if result:
                    result["is_stale_fallback"] = True
                    METRICS_CACHE_HITS.labels(
                        level=str(result.get("cache_level", "unknown")),
                        freshness="expired_outage",
                    ).inc()
                    logger.warning(json.dumps({
                        "event": "cache_expired_served_total_outage",
                        "cache_key": params_hash[:12],
                        "cache_age_hours": result.get("cache_age_hours"),
                        "results_count": len(result.get("results", [])),
                    }))
                    return result
        except Exception as e:
            logger.debug("CRIT-081: total-outage expired fallback check failed: %s", e)

    METRICS_CACHE_MISSES.labels(level="cascade").inc()
    return None


async def _cascade_read_levels(
    user_id: str,
    params_hash: str,
    params: dict,
    _hit_fn,
) -> Optional[dict]:
    """STORY-306: Read cache across cascade levels (L2→L1→L3→Global) for a given hash key."""
    _level_str = {
        CacheLevel.REDIS: "memory",
        CacheLevel.SUPABASE: "supabase",
        CacheLevel.LOCAL: "local",
    }

    # L2: Redis/InMemory — O(1) lookup, no I/O
    try:
        data = _get_from_redis(params_hash)
        if data:
            result = _hit_fn(data, params_hash, CacheLevel.REDIS)
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
            result = _hit_fn(data, params_hash, CacheLevel.SUPABASE)
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
            result = _hit_fn(data, params_hash, CacheLevel.LOCAL)
            if result:
                result["cache_level"] = _level_str[CacheLevel.LOCAL]
                _freshness = result.get("cache_status", "stale")
                METRICS_CACHE_HITS.labels(level="local", freshness=_freshness).inc()
                logger.info(json.dumps({
                    "event": "cache_l3_served",
                    "cache_key": params_hash[:12],
                    "cache_age_hours": result["cache_age_hours"],
                    "results_count": len(result["results"]),
                }))
                return result
    except Exception as e:
        logger.error(f"Cascade L3/local read failed: {e}")

    # GTM-ARCH-002 AC1: Global cross-user fallback before cascade miss
    try:
        global_data = await _get_global_fallback_from_supabase(params)
        if global_data:
            result = _hit_fn(global_data, params_hash, CacheLevel.SUPABASE)
            if result:
                result["cache_level"] = "global"
                METRICS_CACHE_HITS.labels(level="global", freshness=result.get("cache_status", "stale")).inc()
                logger.info(json.dumps({
                    "event": "cache_global_fallback_served",
                    "cache_key": params_hash[:12],
                    "cache_age_hours": result["cache_age_hours"],
                    "results_count": len(result["results"]),
                }))
                return result
    except Exception as e:
        logger.debug(f"Cascade global fallback failed: {e}")

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
    from supabase_client import get_supabase, sb_execute
    sb = get_supabase()

    now = datetime.now(timezone.utc)

    # Read current fail_streak
    response = await sb_execute(
        sb.table("search_results_cache")
        .select("fail_streak")
        .eq("user_id", user_id)
        .eq("params_hash", params_hash)
        .limit(1)
    )

    if not response.data:
        logger.warning(f"record_cache_fetch_failure: no cache key found for hash {params_hash[:12]}")
        return {}

    current_streak = response.data[0].get("fail_streak", 0) or 0
    new_streak = current_streak + 1
    backoff_min = calculate_backoff_minutes(new_streak)
    degraded_until = (now + timedelta(minutes=backoff_min)).isoformat()

    # Update with new values
    await sb_execute(
        sb.table("search_results_cache").update({
            "fail_streak": new_streak,
            "last_attempt_at": now.isoformat(),
            "degraded_until": degraded_until,
        }).eq("user_id", user_id).eq("params_hash", params_hash)
    )

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
    from supabase_client import get_supabase, sb_execute
    sb = get_supabase()

    response = await sb_execute(
        sb.table("search_results_cache")
        .select("degraded_until")
        .eq("user_id", user_id)
        .eq("params_hash", params_hash)
        .limit(1)
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

    result = {
        "results": data.get("results", []),
        "cached_at": fetched_at_str,
        "cached_sources": data.get("sources_json") or ["pncp"],
        "cache_age_hours": round(age_hours, 1),
        "is_stale": is_stale,
        "cache_level": level,
        "cache_status": status,
        "cache_priority": cache_priority,
    }

    # CRIT-056 AC2: Check if L2 cache was written during degraded period
    # Coverage data reveals if sources were missing during the write
    coverage = data.get("coverage")
    if coverage and isinstance(coverage, dict):
        failed_ufs = coverage.get("failed_ufs", [])
        total_req = coverage.get("total_requested", 0)
        if failed_ufs and total_req > 0:
            # Partial coverage — check if PNCP has recovered
            try:
                from cron_jobs import get_pncp_cron_status
                pncp_status = get_pncp_cron_status().get("status")
                if pncp_status == "healthy" and not is_stale:
                    # Override freshness to stale to trigger revalidation
                    result["is_stale"] = True
                    result["cache_status"] = CacheStatus.STALE
            except Exception:
                pass

    return result


def _process_cache_hit_allow_expired(data: dict, params_hash: str, level: CacheLevel) -> Optional[dict]:
    """P1.3: Like _process_cache_hit but allows expired (>24h) entries as last-resort fallback.

    Returns a structured dict even when age > CACHE_STALE_HOURS. Sets is_expired=True so
    callers know this data is beyond the normal TTL boundary.
    Returns None only when fetched_at is missing (unrecoverable).
    """
    fetched_at_str = data.get("fetched_at")
    if not fetched_at_str:
        return None

    fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00"))
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    age_hours = (now - fetched_at).total_seconds() / 3600

    is_expired = age_hours > CACHE_STALE_HOURS
    is_stale = age_hours > CACHE_FRESH_HOURS

    from middleware import search_id_var
    _search_id = search_id_var.get("-")
    logger.info(
        f"Cache EXPIRED HIT L{_level_num(level)}/{level.value} "
        f"[search={_search_id}] "
        f"for hash {params_hash[:12]}... "
        f"(age={age_hours:.1f}h, expired={is_expired}) — allow_expired=True"
    )

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
        "is_expired": is_expired,
        "cache_level": level,
        "cache_status": CacheStatus.STALE if is_stale else CacheStatus.FRESH,
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

    # HARDEN-018 AC3: also enforce size limit after TTL cleanup
    _check_cache_dir_size()

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
    from supabase_client import get_supabase, sb_execute

    now = datetime.now(timezone.utc)

    try:
        sb = get_supabase()

        # Read current state
        resp = await sb_execute(
            sb.table("search_results_cache")
            .select("access_count, last_accessed_at, priority")
            .eq("user_id", user_id)
            .eq("params_hash", params_hash)
            .limit(1)
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

        await sb_execute(
            sb.table("search_results_cache").update(update_data).eq(
                "user_id", user_id
            ).eq("params_hash", params_hash)
        )

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

    GTM-ARCH-002 AC8/AC9: Uses ConsolidationService (multi-source) instead of PNCP-only.
    If PNCP fails, PCP+ComprasGov provide partial results (partial > nothing).

    1. Fetch fresh data from all sources via ConsolidationService (AC8)
    2. On success: save_to_cache() resets fail_streak
    3. On failure: record_cache_fetch_failure() increments fail_streak
    4. If SSE tracker active: emit 'revalidated' event
    5. Log structured JSON result
    """
    global _active_revalidations
    from config import REVALIDATION_TIMEOUT

    start = time.monotonic()
    result_status = "unknown"
    new_results_count = 0
    sources_used: list[str] = []

    try:
        # Independent timeout — does not affect active requests
        async with asyncio.timeout(REVALIDATION_TIMEOUT):
            results, sources_used = await _fetch_multi_source_for_revalidation(request_data)
            new_results_count = len(results)

            if results:
                duration_ms = int((time.monotonic() - start) * 1000)
                coverage = {
                    "succeeded_ufs": list(request_data["ufs"]),
                    "failed_ufs": [],
                    "total_requested": len(request_data["ufs"]),
                }
                await save_to_cache(
                    user_id=user_id,
                    params=params,
                    results=results,
                    sources=sources_used,
                    fetch_duration_ms=duration_ms,
                    coverage=coverage,
                )
                result_status = "success"

                # SSE notification if tracker still active
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
        # Release budget slot
        lock = _get_revalidation_lock()
        async with lock:
            _active_revalidations = max(0, _active_revalidations - 1)

        # Structured log — 1 JSON line per revalidation
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.info(json.dumps({
            "event": "revalidation_complete",
            "params_hash": params_hash[:12],
            "trigger": "stale_served",
            "duration_ms": duration_ms,
            "result": result_status,
            "new_results_count": new_results_count,
            "sources": sources_used,
        }))


async def _fetch_multi_source_for_revalidation(request_data: dict) -> tuple[list, list[str]]:
    """GTM-ARCH-002 AC8/AC9: Multi-source fetch for revalidation.

    Tries ConsolidationService with all enabled sources.
    If PNCP fails, PCP+ComprasGov provide partial results.
    Falls back to PNCP-only if ConsolidationService unavailable.

    Returns (results_list, sources_used_list).
    """

    # AC8: Try ConsolidationService (multi-source) first
    try:
        from consolidation import ConsolidationService
        from source_config.sources import get_source_config

        source_config = get_source_config()
        from source_config.sources import source_health_registry
        adapters = {}

        # Build adapters for all enabled sources
        # CRIT-047 AC7: Skip sources that are DOWN in health registry —
        # don't waste timeout budget on known-failed sources during revalidation
        if source_config.pncp.enabled:
            if source_health_registry.is_available("PNCP"):
                from pncp_client import PNCPLegacyAdapter
                adapters["PNCP"] = PNCPLegacyAdapter(
                    ufs=list(request_data["ufs"]),
                    modalidades=request_data.get("modalidades"),
                )
            else:
                logger.info("[REVALIDATION] Skipping PNCP — source is DOWN in health registry")

        if source_config.compras_gov.enabled:
            if source_health_registry.is_available("COMPRAS_GOV"):
                from clients.compras_gov_client import ComprasGovAdapter
                adapters["COMPRAS_GOV"] = ComprasGovAdapter(timeout=source_config.compras_gov.timeout)
            else:
                logger.info("[REVALIDATION] Skipping COMPRAS_GOV — source is DOWN in health registry")

        # GTM-FIX-024 T2: PCP v2 API is public — no API key required
        if source_config.portal.enabled:
            if source_health_registry.is_available("PORTAL_COMPRAS"):
                from clients.portal_compras_client import PortalComprasAdapter
                adapters["PORTAL_COMPRAS"] = PortalComprasAdapter(
                    timeout=source_config.portal.timeout,
                )
            else:
                logger.info("[REVALIDATION] Skipping PORTAL_COMPRAS — source is DOWN in health registry")

        if adapters:
            svc = ConsolidationService(
                adapters=adapters,
                timeout_per_source=60,
                timeout_global=120,
                fail_on_all_errors=False,  # AC9: partial results > nothing
            )
            try:
                consolidation_result = await svc.fetch_all(
                    data_inicial=request_data["data_inicial"],
                    data_final=request_data["data_final"],
                    ufs=set(request_data["ufs"]),
                )
                sources = [sr.source_code for sr in consolidation_result.source_results if sr.status == "success"]
                return consolidation_result.records, sources or ["consolidation"]
            finally:
                await svc.close()

    except ImportError:
        logger.debug("ConsolidationService not available, falling back to PNCP-only")
    except Exception as e:
        logger.warning(f"Multi-source revalidation failed, falling back to PNCP-only: {e}")

    # GTM-INFRA-003 AC4: Fallback — PCP+ComprasGov only (without PNCP)
    try:
        from consolidation import ConsolidationService
        from source_config.sources import get_source_config

        source_config = get_source_config()
        from source_config.sources import source_health_registry
        fallback_adapters = {}

        # CRIT-047 AC7: Skip DOWN sources in fallback revalidation too
        if source_config.compras_gov.enabled:
            if source_health_registry.is_available("COMPRAS_GOV"):
                from clients.compras_gov_client import ComprasGovAdapter
                fallback_adapters["COMPRAS_GOV"] = ComprasGovAdapter(timeout=source_config.compras_gov.timeout)
            else:
                logger.info("[REVALIDATION] Skipping COMPRAS_GOV fallback — source is DOWN")

        # GTM-FIX-024 T2: PCP v2 API is public — no API key required
        if source_config.portal.enabled:
            if source_health_registry.is_available("PORTAL_COMPRAS"):
                from clients.portal_compras_client import PortalComprasAdapter
                fallback_adapters["PORTAL_COMPRAS"] = PortalComprasAdapter(
                    timeout=source_config.portal.timeout,
                )
            else:
                logger.info("[REVALIDATION] Skipping PORTAL_COMPRAS fallback — source is DOWN")

        if fallback_adapters:
            logger.info(f"Revalidation fallback: trying {list(fallback_adapters.keys())} without PNCP")
            svc = ConsolidationService(
                adapters=fallback_adapters,
                timeout_per_source=60,
                timeout_global=120,
                fail_on_all_errors=False,
            )
            try:
                consolidation_result = await svc.fetch_all(
                    data_inicial=request_data["data_inicial"],
                    data_final=request_data["data_final"],
                    ufs=set(request_data["ufs"]),
                )
                sources = [sr.source_code for sr in consolidation_result.source_results if sr.status == "success"]
                if consolidation_result.records:
                    return consolidation_result.records, sources or ["fallback"]
            finally:
                await svc.close()

    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"PCP+ComprasGov fallback revalidation failed: {e}")

    # AC4 level 3: PNCP-only fallback (original behavior)
    try:
        import pncp_client as _pncp

        fetch_result = await _pncp.buscar_todas_ufs_paralelo(
            ufs=request_data["ufs"],
            data_inicial=request_data["data_inicial"],
            data_final=request_data["data_final"],
            modalidades=request_data.get("modalidades"),
        )

        if hasattr(fetch_result, "items"):
            results = fetch_result.items
        elif isinstance(fetch_result, list):
            results = fetch_result
        else:
            results = list(fetch_result)

        if results:
            return results, ["PNCP"]
    except Exception as e:
        logger.warning(f"PNCP-only fallback revalidation failed: {e}")

    # AC4 final fallback: return empty — caller keeps stale cache
    return [], []


# ============================================================================
# B-05: Admin Cache Metrics, Invalidation, Inspection
# ============================================================================


async def get_cache_metrics() -> dict:
    """B-05 AC3/AC4/AC10: Aggregate cache metrics for admin dashboard.

    Returns hit_rate_24h, miss_rate_24h, stale_served_24h, fresh_served_24h,
    total_entries, priority_distribution, age_distribution, degraded_keys,
    avg_fetch_duration_ms, top_keys.
    """
    from supabase_client import get_supabase, sb_execute
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
        all_entries = await sb_execute(
            sb.table("search_results_cache")
            .select("params_hash, priority, fetched_at, access_count, fail_streak, degraded_until, fetch_duration_ms")
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
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        await sb_execute(sb.table("search_results_cache").delete().eq("params_hash", params_hash))
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
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()
        # Delete all cache entries (use gte on created_at to match all)
        result = await sb_execute(
            sb.table("search_results_cache").delete().gte("created_at", "2000-01-01")
        )
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
        from supabase_client import get_supabase, sb_execute
        sb = get_supabase()

        response = await sb_execute(
            sb.table("search_results_cache")
            .select(
                "params_hash, user_id, search_params, total_results, sources_json, "
                "fetched_at, created_at, priority, access_count, last_accessed_at, "
                "fail_streak, degraded_until, coverage, fetch_duration_ms, "
                "last_success_at, last_attempt_at"
            )
            .eq("params_hash", params_hash)
            .limit(1)
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


# ============================================================================
# CRIT-032: Stale entries query for periodic cache refresh
# ============================================================================


async def get_stale_entries_for_refresh(batch_size: int = 25) -> list[dict]:
    """CRIT-032 AC4-9: Query cache entries eligible for periodic refresh.

    Selects:
      - HOT + WARM entries with fetched_at older than CACHE_FRESH_HOURS (6h)
      - Entries with total_results=0 (empty caches), regardless of priority
    Excludes:
      - Entries with degraded_until > now (respects backoff)
    Orders:
      - Empty (total_results=0) first, then HOT before WARM, then by access_count DESC
    Limits to batch_size.

    Returns list of dicts with: user_id, params_hash, search_params, total_results, priority.
    """
    from supabase_client import get_supabase, sb_execute

    sb = get_supabase()
    now = datetime.now(timezone.utc)
    stale_cutoff = (now - timedelta(hours=CACHE_FRESH_HOURS)).isoformat()

    # Query 1: Empty entries (total_results = 0), any priority
    empty_resp = await sb_execute(
        sb.table("search_results_cache")
        .select("user_id, params_hash, search_params, total_results, priority, access_count, degraded_until")
        .eq("total_results", 0)
    )

    # Query 2: HOT + WARM stale entries (fetched_at < stale_cutoff)
    hot_resp = await sb_execute(
        sb.table("search_results_cache")
        .select("user_id, params_hash, search_params, total_results, priority, access_count, degraded_until")
        .eq("priority", "hot")
        .lt("fetched_at", stale_cutoff)
        .gt("total_results", 0)
    )
    warm_resp = await sb_execute(
        sb.table("search_results_cache")
        .select("user_id, params_hash, search_params, total_results, priority, access_count, degraded_until")
        .eq("priority", "warm")
        .lt("fetched_at", stale_cutoff)
        .gt("total_results", 0)
    )

    # Merge and deduplicate by params_hash
    seen_hashes: set[str] = set()
    candidates: list[dict] = []

    all_rows = (empty_resp.data or []) + (hot_resp.data or []) + (warm_resp.data or [])

    for row in all_rows:
        ph = row.get("params_hash", "")
        if ph in seen_hashes:
            continue

        # AC8: Exclude entries with degraded_until in the future
        degraded_str = row.get("degraded_until")
        if degraded_str:
            try:
                degraded_until = datetime.fromisoformat(str(degraded_str).replace("Z", "+00:00"))
                if degraded_until.tzinfo is None:
                    degraded_until = degraded_until.replace(tzinfo=timezone.utc)
                if degraded_until > now:
                    continue
            except (ValueError, TypeError):
                pass

        seen_hashes.add(ph)
        candidates.append({
            "user_id": row.get("user_id"),
            "params_hash": ph,
            "search_params": row.get("search_params", {}),
            "total_results": row.get("total_results", 0),
            "priority": row.get("priority", "cold"),
            "access_count": row.get("access_count", 0) or 0,
        })

    # AC7: Sort — empty first, then HOT before WARM, then access_count DESC
    priority_order = {"hot": 0, "warm": 1, "cold": 2}
    candidates.sort(key=lambda e: (
        0 if e["total_results"] == 0 else 1,
        priority_order.get(e["priority"], 2),
        -e["access_count"],
    ))

    return candidates[:batch_size]


async def get_top_popular_params(limit: int = 10) -> list[dict]:
    """GTM-ARCH-002 AC6/AC7: Get top popular sector+UF combinations for warmup.

    Queries search_results_cache for the most accessed search_params combinations,
    ordered by access_count DESC. Returns deduplicated list of search_params.
    """
    from supabase_client import get_supabase, sb_execute
    sb = get_supabase()

    response = await sb_execute(
        sb.table("search_results_cache")
        .select("search_params, access_count, params_hash")
        .order("access_count", desc=True)
        .limit(limit * 3)  # Over-fetch to deduplicate
    )

    if not response.data:
        return []

    # Deduplicate by params_hash (same params across users)
    seen_hashes: set[str] = set()
    results: list[dict] = []

    for row in response.data:
        ph = row.get("params_hash", "")
        if ph in seen_hashes:
            continue
        seen_hashes.add(ph)

        search_params = row.get("search_params", {})
        if search_params and search_params.get("setor_id") and search_params.get("ufs"):
            results.append(search_params)

        if len(results) >= limit:
            break

    return results


async def get_popular_ufs_from_sessions(days: int = 7) -> list[str]:
    """CRIT-055 AC2: Get UFs ordered by popularity from recent search sessions.

    Queries search_sessions for the last N days, counts UF occurrences,
    and returns UFs sorted by frequency (most popular first).

    Returns empty list if no history or on error (caller should use default order).
    """
    from supabase_client import get_supabase, sb_execute
    from datetime import datetime, timezone, timedelta

    try:
        sb = get_supabase()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        response = await sb_execute(
            sb.table("search_sessions")
            .select("ufs")
            .gte("created_at", cutoff)
            .in_("status", ["completed", "completed_partial"])
            .limit(500)
        )

        if not response.data:
            return []

        # Count UF occurrences across all sessions
        uf_counts: dict[str, int] = {}
        for row in response.data:
            ufs = row.get("ufs") or []
            for uf in ufs:
                if isinstance(uf, str) and len(uf) == 2:
                    uf_counts[uf] = uf_counts.get(uf, 0) + 1

        # Sort by count descending
        sorted_ufs = sorted(uf_counts.keys(), key=lambda u: -uf_counts[u])
        return sorted_ufs

    except Exception as e:
        logging.getLogger(__name__).warning(
            "CRIT-055: Failed to get popular UFs from sessions: %s", e
        )
        return []
