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
# P1.2: Startup Cache Warm-up
# ============================================
WARMUP_ENABLED: bool = str_to_bool(os.getenv("WARMUP_ENABLED", "true"))

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

WARMUP_UFS: list[str] = [
    uf.strip() for uf in os.getenv("WARMUP_UFS", ",".join(ALL_BRAZILIAN_UFS)).split(",") if uf.strip()
]
WARMUP_SECTORS: list[str] = [
    s.strip()
    for s in os.getenv("WARMUP_SECTORS", "software,informatica,engenharia,saude,facilities").split(",")
    if s.strip()
]
WARMUP_STARTUP_DELAY_SECONDS: int = int(os.getenv("WARMUP_STARTUP_DELAY_SECONDS", "120"))
WARMUP_BATCH_DELAY_SECONDS: float = float(os.getenv("WARMUP_BATCH_DELAY_SECONDS", "2"))
WARMUP_PERIODIC_INTERVAL_HOURS: int = int(os.getenv("WARMUP_PERIODIC_INTERVAL_HOURS", "2"))
WARMUP_RATE_LIMIT_RPS: float = float(os.getenv("WARMUP_RATE_LIMIT_RPS", "2.0"))
WARMUP_PNCP_DEGRADED_PAUSE_S: float = float(os.getenv("WARMUP_PNCP_DEGRADED_PAUSE_S", "300.0"))
WARMUP_UF_BATCH_SIZE: int = int(os.getenv("WARMUP_UF_BATCH_SIZE", "5"))

# ============================================
# GTM-STAB-007: Cache Warming
# ============================================
# CRIT-081: default true — cache warming is critical for resilience (cache-first strategy)
CACHE_WARMING_ENABLED: bool = str_to_bool(os.getenv("CACHE_WARMING_ENABLED", "true"))
CACHE_WARMING_INTERVAL_HOURS: int = int(os.getenv("CACHE_WARMING_INTERVAL_HOURS", "4"))
CACHE_WARMING_CONCURRENCY: int = int(os.getenv("CACHE_WARMING_CONCURRENCY", "2"))
CACHE_WARMING_BUDGET_MINUTES: int = int(os.getenv("CACHE_WARMING_BUDGET_MINUTES", "30"))
WARMING_BATCH_DELAY_S: float = float(os.getenv("WARMING_BATCH_DELAY_S", "3.0"))
WARMING_BUDGET_TIMEOUT_S: float = float(os.getenv("WARMING_BUDGET_TIMEOUT_S", "1800"))
WARMING_PAUSE_ON_ACTIVE_S: float = float(os.getenv("WARMING_PAUSE_ON_ACTIVE_S", "10.0"))
WARMING_MAX_PAUSE_CYCLES: int = int(os.getenv("WARMING_MAX_PAUSE_CYCLES", "3"))
WARMING_USER_ID: str = "00000000-0000-0000-0000-000000000000"
WARMING_RATE_LIMIT_BACKOFF_S: float = float(os.getenv("WARMING_RATE_LIMIT_BACKOFF_S", "60.0"))

# ============================================
# CRIT-032: Periodic Cache Refresh
# ============================================
CACHE_REFRESH_ENABLED: bool = str_to_bool(os.getenv("CACHE_REFRESH_ENABLED", "true"))
CACHE_REFRESH_INTERVAL_HOURS: int = int(os.getenv("CACHE_REFRESH_INTERVAL_HOURS", "4"))
CACHE_REFRESH_BATCH_SIZE: int = int(os.getenv("CACHE_REFRESH_BATCH_SIZE", "50"))
CACHE_REFRESH_STAGGER_SECONDS: int = int(os.getenv("CACHE_REFRESH_STAGGER_SECONDS", "5"))

# STORY-306: Cache Correctness & Data Integrity
CACHE_LEGACY_KEY_FALLBACK: bool = str_to_bool(os.getenv("CACHE_LEGACY_KEY_FALLBACK", "true"))
SHOW_CACHE_FALLBACK_BANNER: bool = str_to_bool(os.getenv("SHOW_CACHE_FALLBACK_BANNER", "true"))
CACHE_WARMING_POST_DEPLOY_ENABLED: bool = str_to_bool(os.getenv("CACHE_WARMING_POST_DEPLOY_ENABLED", "true"))
CACHE_WARMING_POST_DEPLOY_TOP_N: int = int(os.getenv("CACHE_WARMING_POST_DEPLOY_TOP_N", "10"))
CACHE_WARMING_POST_DEPLOY_DELAY_S: int = int(os.getenv("CACHE_WARMING_POST_DEPLOY_DELAY_S", "30"))

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
