"""Pipeline operations: async search, cache/warmup, revalidation, state store, cron, business hours."""

import os

from config.base import str_to_bool

# ============================================
# B-01: Background Revalidation
# ============================================
REVALIDATION_TIMEOUT: int = int(os.getenv("REVALIDATION_TIMEOUT", "180"))
MAX_CONCURRENT_REVALIDATIONS: int = int(os.getenv("MAX_CONCURRENT_REVALIDATIONS", "3"))
REVALIDATION_COOLDOWN_S: int = int(os.getenv("REVALIDATION_COOLDOWN_S", "600"))

# ============================================
# CRIT-072: Async-first 202 pattern
# CRIT-SYNC-FIX: Default changed to "false" — async mode causes in-memory
# tracker mismatch with multi-worker (WEB_CONCURRENCY>1). Keep sync until
# tracker is externalised to Redis.
# ============================================
ASYNC_SEARCH_DEFAULT: bool = str_to_bool(os.getenv("ASYNC_SEARCH_DEFAULT", "false"))
SEARCH_ASYNC_ENABLED: bool = str_to_bool(os.getenv("SEARCH_ASYNC_ENABLED", str(ASYNC_SEARCH_DEFAULT).lower()))
SEARCH_JOB_TIMEOUT: int = int(os.getenv("SEARCH_JOB_TIMEOUT", "300"))
MAX_CONCURRENT_SEARCHES: int = int(os.getenv("MAX_CONCURRENT_SEARCHES", "3"))

# ============================================
# STORY-294: State Externalization to Redis
# ============================================
RESULTS_REDIS_TTL: int = int(os.getenv("RESULTS_REDIS_TTL", "14400"))
RESULTS_SUPABASE_TTL_HOURS: int = int(os.getenv("RESULTS_SUPABASE_TTL_HOURS", "24"))
ARBITER_REDIS_TTL: int = int(os.getenv("ARBITER_REDIS_TTL", "3600"))
STATE_STORE_REDIS_PREFIX: str = os.getenv("STATE_STORE_REDIS_PREFIX", "smartlic:")

# ============================================
# UF Brazilian list (used across cache + filters)
# ============================================
ALL_BRAZILIAN_UFS: list[str] = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]

DEFAULT_UF_PRIORITY: list[str] = [
    "SP", "RJ", "MG", "BA", "PR", "RS", "SC", "PE", "CE", "GO",
    "DF", "PA", "MA", "AM", "ES", "PB", "RN", "MT", "MS", "AL",
    "PI", "SE", "RO", "TO", "AC", "AP", "RR",
]

# ============================================
# STORY-306: Cache Correctness & Data Integrity
# ============================================
# Note: cache warming/refresh proactive jobs deprecated 2026-04-18
# (STORY-CIG-BE-cache-warming-deprecate). DataLake Supabase is primary
# query path. Associated flags removed: WARMUP_ENABLED, CACHE_WARMING_*,
# CACHE_REFRESH_*, WARMING_BATCH/BUDGET/PAUSE_*, CACHE_WARMING_POST_DEPLOY_*.
CACHE_LEGACY_KEY_FALLBACK: bool = str_to_bool(os.getenv("CACHE_LEGACY_KEY_FALLBACK", "true"))
SHOW_CACHE_FALLBACK_BANNER: bool = str_to_bool(os.getenv("SHOW_CACHE_FALLBACK_BANNER", "true"))

# STORY-271 / DEBT-009: Nil UUID reserved for legacy warming jobs. Kept as a
# defensive guard in cache save paths to short-circuit any accidental write
# by this identity. The owning account is permanently banned via
# migration supabase/migrations/20260308330000_debt009_ban_cache_warmer.sql.
WARMING_USER_ID: str = "00000000-0000-0000-0000-000000000000"

# ============================================
# CRIT-081: Serve expired cache on total outage
# ============================================
SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE: bool = os.environ.get("SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE", "true").lower() == "true"

# ============================================
# Cron Jobs & Email Digests
# ============================================
DIGEST_ENABLED: bool = str_to_bool(os.getenv("DIGEST_ENABLED", "false"))
DIGEST_HOUR_UTC: int = int(os.getenv("DIGEST_HOUR_UTC", "10"))
DIGEST_MAX_PER_EMAIL: int = int(os.getenv("DIGEST_MAX_PER_EMAIL", "10"))
DIGEST_BATCH_SIZE: int = 100

ALERTS_ENABLED: bool = str_to_bool(os.getenv("ALERTS_ENABLED", "true"))
ALERTS_HOUR_UTC: int = int(os.getenv("ALERTS_HOUR_UTC", "11"))
ALERTS_MAX_PER_EMAIL: int = int(os.getenv("ALERTS_MAX_PER_EMAIL", "10"))

RECONCILIATION_ENABLED: bool = str_to_bool(os.getenv("RECONCILIATION_ENABLED", "true"))
RECONCILIATION_HOUR_UTC: int = int(os.getenv("RECONCILIATION_HOUR_UTC", "6"))

# Health Canary & Status Page
HEALTH_CANARY_ENABLED: bool = str_to_bool(os.getenv("HEALTH_CANARY_ENABLED", "true"))
HEALTH_CANARY_INTERVAL_SECONDS: int = int(os.getenv("HEALTH_CANARY_INTERVAL_SECONDS", "300"))
HEALTH_CHECKS_RETENTION_DAYS: int = int(os.getenv("HEALTH_CHECKS_RETENTION_DAYS", "30"))

# SHIP-002: Feature gates for incomplete features
ORGANIZATIONS_ENABLED: bool = str_to_bool(os.getenv("ORGANIZATIONS_ENABLED", "false"))
MESSAGES_ENABLED: bool = str_to_bool(os.getenv("MESSAGES_ENABLED", "true"))
ALERTS_SYSTEM_ENABLED: bool = str_to_bool(os.getenv("ALERTS_SYSTEM_ENABLED", "false"))
PARTNERS_ENABLED: bool = str_to_bool(os.getenv("PARTNERS_ENABLED", "false"))

# STORY-353: Support SLA Business Hours
BUSINESS_HOURS_START: int = int(os.getenv("BUSINESS_HOURS_START", "8"))
BUSINESS_HOURS_END: int = int(os.getenv("BUSINESS_HOURS_END", "18"))
SUPPORT_SLA_CHECK_INTERVAL_SECONDS: int = 4 * 60 * 60
SUPPORT_SLA_ALERT_THRESHOLD_HOURS: int = 20

# ============================================
# DEBT-124: Graceful Shutdown
# ============================================
GRACEFUL_SHUTDOWN_TIMEOUT: int = int(os.getenv("GRACEFUL_SHUTDOWN_TIMEOUT", "30"))

# ============================================
# DEBT-04 AC2: Slow request detection
# Log + Sentry capture for requests exceeding this threshold (default 100s).
# Set to 0 to disable detection.
# ============================================
REQUEST_SLOW_THRESHOLD_S: float = float(os.getenv("REQUEST_SLOW_THRESHOLD_S", "100"))
