"""search_cache — Backward-compatible facade for cache package.

All implementations now live in cache/ submodules:
  - cache.enums      — Enums, constants, hash utilities
  - cache.manager    — Multi-level save/read orchestration
  - cache._ops       — Hit processing, tracking, degradation
  - cache.swr        — Stale-While-Revalidate background revalidation
  - cache.admin      — Admin metrics, invalidation, inspection
  - cache.local_file — Local file cache L3 layer
  - cache.redis      — Redis L2 layer
  - cache.supabase   — Supabase L1 layer
  - cache.memory     — InMemoryCache re-export

Import paths like ``from search_cache import save_to_cache`` continue to work.

NOTE: _active_revalidations and _revalidation_lock live in cache.swr.
Tests that set these must use: import cache.swr; cache.swr._active_revalidations = 0
"""
# Enums and constants
from cache.enums import (
    CacheLevel, CacheStatus, CachePriority,
    CACHE_FRESH_HOURS, CACHE_STALE_HOURS,
    LOCAL_CACHE_DIR, LOCAL_CACHE_TTL_HOURS, LOCAL_CACHE_MAX_SIZE_MB, LOCAL_CACHE_TARGET_SIZE_MB,
    REDIS_CACHE_TTL_SECONDS, REDIS_TTL_BY_PRIORITY,
    classify_priority,
    _normalize_date,
    compute_search_hash, compute_search_hash_without_dates, compute_search_hash_per_uf,
    compute_global_hash, calculate_backoff_minutes, get_cache_status,
)

# Core operations
from cache.manager import (
    save_to_cache, save_to_cache_per_uf,
    get_from_cache_composed, get_from_cache,
    _dedup_cross_uf, _compute_age_hours,
    _read_all_levels,
    CACHE_PARTIAL_HIT_THRESHOLD,
)
# Cascade read (moved to cache.cascade in DEBT-203)
from cache.cascade import (
    get_from_cache_cascade, _cascade_read_levels,
    _format_cache_date_range, _all_sources_down,
)

# Ops (hit processing, tracking, degradation)
from cache._ops import (
    record_cache_fetch_failure, is_cache_key_degraded,
    _process_cache_hit, _process_cache_hit_allow_expired,
    _level_num, _track_cache_operation, _increment_and_reclassify,
)

# SWR revalidation
from cache.swr import (
    trigger_background_revalidation, _do_revalidation,
    _fetch_multi_source_for_revalidation,
    _mark_revalidating, _clear_revalidating, _is_revalidating, _get_revalidation_lock,
)

# Admin operations
from cache.admin import (
    get_cache_metrics, invalidate_cache_entry, invalidate_all_cache,
    inspect_cache_entry,
)

# Local file operations (includes private functions for backward compat)
from cache.local_file import (
    cleanup_local_cache, get_local_cache_stats,
    _check_cache_dir_size,
    _save_to_local, _get_from_local,
)

# Supabase/Redis internal ops (for backward compat with tests that import directly)
from cache.supabase import (
    _save_to_supabase, _get_from_supabase, _get_global_fallback_from_supabase,
)
from cache.redis import _save_to_redis, _get_from_redis

# Keep asyncio in namespace for backward-compat test patches
import asyncio  # noqa: F401

__all__ = [
    # Enums/constants
    "CacheLevel", "CacheStatus", "CachePriority",
    "CACHE_FRESH_HOURS", "CACHE_STALE_HOURS",
    "LOCAL_CACHE_DIR", "LOCAL_CACHE_TTL_HOURS", "LOCAL_CACHE_MAX_SIZE_MB", "LOCAL_CACHE_TARGET_SIZE_MB",
    "REDIS_CACHE_TTL_SECONDS", "REDIS_TTL_BY_PRIORITY",
    "classify_priority", "_normalize_date",
    "compute_search_hash", "compute_search_hash_without_dates", "compute_search_hash_per_uf",
    "compute_global_hash", "calculate_backoff_minutes", "get_cache_status",
    "CACHE_PARTIAL_HIT_THRESHOLD",
    # Core ops
    "save_to_cache", "save_to_cache_per_uf",
    "get_from_cache_composed", "get_from_cache", "get_from_cache_cascade",
    # Internal (for test patching via search_cache.X)
    "_dedup_cross_uf", "_compute_age_hours", "_format_cache_date_range", "_all_sources_down",
    "_read_all_levels", "_cascade_read_levels",
    # Ops
    "record_cache_fetch_failure", "is_cache_key_degraded",
    "_process_cache_hit", "_process_cache_hit_allow_expired",
    "_level_num", "_track_cache_operation", "_increment_and_reclassify",
    # SWR
    "trigger_background_revalidation", "_do_revalidation",
    "_fetch_multi_source_for_revalidation",
    "_mark_revalidating", "_clear_revalidating", "_is_revalidating", "_get_revalidation_lock",
    # Admin
    "get_cache_metrics", "invalidate_cache_entry", "invalidate_all_cache",
    "inspect_cache_entry",
    # Local file
    "cleanup_local_cache", "get_local_cache_stats",
    "_check_cache_dir_size", "_save_to_local", "_get_from_local",
    # Supabase/Redis internal (backward compat)
    "_save_to_supabase", "_get_from_supabase", "_get_global_fallback_from_supabase",
    "_save_to_redis", "_get_from_redis",
    # asyncio for patch compat
    "asyncio",
]
