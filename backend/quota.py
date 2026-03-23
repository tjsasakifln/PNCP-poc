"""Quota management with plan-based capabilities.

SECURITY NOTE (Issue #189):
The quota check/increment operations use atomic database operations to prevent
race conditions. The check_and_increment_quota_atomic() function performs both
check and increment in a single database transaction, eliminating the TOCTOU
(time-of-check-to-time-of-use) vulnerability.

For environments without the PostgreSQL function, an asyncio.Lock fallback
provides in-process synchronization (sufficient for single-instance deployments).

SECURITY NOTE (Issue #168):
All user IDs in logs are sanitized to prevent PII exposure.

STORY-203 SYS-M04: Database-driven plan capabilities
- Plan capabilities loaded from database `plans` table
- In-memory cache with 5-minute TTL to reduce DB load
- Automatic fallback to hardcoded values if DB unavailable

STORY-291: Circuit breaker integration for Supabase calls.
- AC3: Plan status cached in-memory with 5min TTL (fallback when CB open)
- AC4: Fail-open on CB open — allow search, log for reconciliation
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, TypedDict
from enum import Enum
from pydantic import BaseModel
from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)

# STORY-203 SYS-M04: Plan capabilities cache
_plan_capabilities_cache: Optional[dict[str, "PlanCapabilities"]] = None
_plan_capabilities_cache_time: float = 0
PLAN_CAPABILITIES_CACHE_TTL = 300  # 5 minutes in seconds

# STORY-291 AC3: In-memory plan status cache (fallback when Supabase CB open)
# Key: user_id, Value: (plan_id, cached_at)
# DEBT-323: Bounded to prevent unbounded memory growth under high-cardinality user IDs.
# When maxsize is exceeded, the oldest entry (by insertion order) is evicted.
PLAN_STATUS_CACHE_MAXSIZE = 1000
_plan_status_cache: dict[str, tuple[str, float]] = {}
_plan_status_cache_lock = threading.Lock()
PLAN_STATUS_CACHE_TTL = 300  # 5 minutes


def _cache_plan_status(user_id: str, plan_id: str) -> None:
    """Cache plan status for fallback when Supabase is unavailable.

    DEBT-323: Enforces maxsize — evicts oldest entries when full.
    """
    with _plan_status_cache_lock:
        # If key already exists, remove it first so re-insertion goes to end
        _plan_status_cache.pop(user_id, None)
        _plan_status_cache[user_id] = (plan_id, time.monotonic())
        # Evict oldest entries if over maxsize
        while len(_plan_status_cache) > PLAN_STATUS_CACHE_MAXSIZE:
            _plan_status_cache.pop(next(iter(_plan_status_cache)))


def _get_cached_plan_status(user_id: str) -> Optional[str]:
    """Get cached plan status. Returns None if expired or missing."""
    with _plan_status_cache_lock:
        entry = _plan_status_cache.get(user_id)
        if entry is None:
            return None
        plan_id, cached_at = entry
        if time.monotonic() - cached_at > PLAN_STATUS_CACHE_TTL:
            del _plan_status_cache[user_id]
            return None
        return plan_id


def invalidate_plan_status_cache(user_id: str) -> None:
    """Remove a specific user from the plan status cache.

    HARDEN-008: Called by Stripe webhook handlers after plan_type updates
    to prevent stale quota bypass (up to 5 min window).
    """
    with _plan_status_cache_lock:
        removed = _plan_status_cache.pop(user_id, None)
    if removed:
        logger.info(f"Plan status cache invalidated for user {mask_user_id(user_id)}")
    else:
        logger.debug(f"Plan status cache miss (no entry) for user {mask_user_id(user_id)}")


# ============================================================================
# Plan Capabilities System
# ============================================================================

class PlanPriority(str, Enum):
    """Processing priority for background jobs (future use)."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class PlanCapabilities(TypedDict):
    """Immutable plan capabilities - DO NOT modify without PR review."""
    max_history_days: int
    allow_excel: bool
    allow_pipeline: bool  # STORY-250: Pipeline de Oportunidades
    max_requests_per_month: int
    max_requests_per_min: int
    max_summary_tokens: int
    priority: str  # PlanPriority value


# Hardcoded plan definitions (secure, version-controlled)
PLAN_CAPABILITIES: dict[str, PlanCapabilities] = {
    "free_trial": {
        "max_history_days": 365,  # GTM-003: 1 year (same as smartlic_pro)
        "allow_excel": True,  # GTM-003: Full product during trial
        "allow_pipeline": True,  # GTM-003: Full product during trial
        "max_requests_per_month": 1000,  # STORY-264 AC1: Full access (same as smartlic_pro)
        "max_requests_per_min": 2,  # STORY-264 AC2: Anti-abuse rate limit kept
        "max_summary_tokens": 10000,  # GTM-003: Full AI analysis (same as smartlic_pro)
        "priority": PlanPriority.NORMAL.value,  # GTM-003: Normal speed (same as smartlic_pro)
    },
    "consultor_agil": {
        "max_history_days": 30,
        "allow_excel": False,
        "allow_pipeline": False,  # STORY-250
        "max_requests_per_month": 50,
        "max_requests_per_min": 10,
        "max_summary_tokens": 200,
        "priority": PlanPriority.NORMAL.value,
    },
    "maquina": {
        "max_history_days": 365,
        "allow_excel": True,
        "allow_pipeline": True,  # STORY-250
        "max_requests_per_month": 300,
        "max_requests_per_min": 30,
        "max_summary_tokens": 500,
        "priority": PlanPriority.HIGH.value,
    },
    "sala_guerra": {
        "max_history_days": 1825,  # 5 years
        "allow_excel": True,
        "allow_pipeline": True,  # STORY-250
        "max_requests_per_month": 1000,
        "max_requests_per_min": 60,
        "max_summary_tokens": 10000,
        "priority": PlanPriority.CRITICAL.value,
    },
    "smartlic_pro": {
        "max_history_days": 1825,  # 5 years
        "allow_excel": True,
        "allow_pipeline": True,
        "max_requests_per_month": 1000,
        "max_requests_per_min": 60,
        "max_summary_tokens": 10000,
        "priority": PlanPriority.NORMAL.value,
    },
    # MAYDAY-A2: Founding Member — same capabilities as smartlic_pro, 50% off price
    "founding_member": {
        "max_history_days": 1825,  # 5 years
        "allow_excel": True,
        "allow_pipeline": True,
        "max_requests_per_month": 1000,
        "max_requests_per_min": 60,
        "max_summary_tokens": 10000,
        "priority": PlanPriority.NORMAL.value,
    },
    # STORY-322: Plano Consultoria — multi-user org plan
    "consultoria": {
        "max_history_days": 1825,  # 5 years
        "allow_excel": True,
        "allow_pipeline": True,
        "max_requests_per_month": 5000,  # 1000 x 5 members
        "max_requests_per_min": 10,  # Rate limit per org
        "max_summary_tokens": 10000,
        "priority": PlanPriority.HIGH.value,
    },
    # STORY-283 AC1: Map plan_ids found in production database
    "free": {
        "max_history_days": 7,
        "allow_excel": False,
        "allow_pipeline": False,
        "max_requests_per_month": 10,
        "max_requests_per_min": 2,
        "max_summary_tokens": 200,
        "priority": PlanPriority.LOW.value,
    },
    "master": {
        "max_history_days": 99999,
        "allow_excel": True,
        "allow_pipeline": True,
        "max_requests_per_month": 99999,
        "max_requests_per_min": 120,
        "max_summary_tokens": 10000,
        "priority": PlanPriority.HIGH.value,
    },
}

# Display names for UI
PLAN_NAMES: dict[str, str] = {
    "free_trial": "FREE Trial",
    "consultor_agil": "Consultor Ágil (legacy)",
    "maquina": "Máquina (legacy)",
    "sala_guerra": "Sala de Guerra (legacy)",
    "smartlic_pro": "SmartLic Pro",
    "founding_member": "SmartLic Founding Member",
    "consultoria": "SmartLic Consultoria",
    "free": "Free",
    "master": "Master",
}

# Pricing for error messages
PLAN_PRICES: dict[str, str] = {
    "consultor_agil": "R$ 297/mês",
    "maquina": "R$ 597/mês",
    "sala_guerra": "R$ 1.497/mês",
    "smartlic_pro": "R$ 397/mês",
    "founding_member": "R$ 197/mês",
    "consultoria": "R$ 997/mês",
}

# Upgrade path suggestions (for error messages)
UPGRADE_SUGGESTIONS: dict[str, dict[str, str]] = {
    "max_history_days": {
        "free_trial": "smartlic_pro",
        "consultor_agil": "smartlic_pro",
        "maquina": "smartlic_pro",
    },
    "allow_excel": {
        "free_trial": "smartlic_pro",
        "consultor_agil": "smartlic_pro",
    },
    "allow_pipeline": {
        "free_trial": "smartlic_pro",
        "consultor_agil": "smartlic_pro",
    },
    "max_requests_per_month": {
        "free_trial": "smartlic_pro",
        "consultor_agil": "smartlic_pro",
        "maquina": "smartlic_pro",
    },
}


# ============================================================================
# STORY-203 SYS-M04: Database-driven Plan Capabilities Loader
# ============================================================================

# Conservative defaults for unknown plans discovered at runtime
_UNKNOWN_PLAN_DEFAULTS = PlanCapabilities(
    max_history_days=30,
    allow_excel=False,
    allow_pipeline=False,  # STORY-250
    max_requests_per_month=10,
    max_requests_per_min=5,
    max_summary_tokens=200,
    priority=PlanPriority.NORMAL.value,
)


def _load_plan_capabilities_from_db() -> dict[str, PlanCapabilities]:
    """Load plan capabilities from database.

    STORY-203 SYS-M04: Loads plan definitions from `plans` table and converts
    to PlanCapabilities format. Falls back to hardcoded PLAN_CAPABILITIES on error.

    STORY-226 AC9: Uses data-driven lookup via PLAN_CAPABILITIES dict instead of
    if/elif chain. The DB's max_searches overrides max_requests_per_month when present.

    Returns:
        dict[str, PlanCapabilities]: Plan capabilities indexed by plan_id
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        # Fetch all active plans from database
        result = (
            sb.table("plans")
            .select("id, max_searches, price_brl, duration_days, description")
            .eq("is_active", True)
            .execute()
        )

        if not result.data:
            logger.warning("No plans found in database, using hardcoded fallback")
            return PLAN_CAPABILITIES

        # Convert database plans to PlanCapabilities format
        db_capabilities: dict[str, PlanCapabilities] = {}

        for plan in result.data:
            plan_id = plan["id"]
            max_searches = plan.get("max_searches", 0)

            # Data-driven lookup: use PLAN_CAPABILITIES as the source of truth
            # for non-DB fields, override max_requests_per_month from DB
            base_caps = PLAN_CAPABILITIES.get(plan_id)

            if base_caps is not None:
                # Known plan: merge DB max_searches into hardcoded capabilities
                caps = PlanCapabilities(
                    max_history_days=base_caps["max_history_days"],
                    allow_excel=base_caps["allow_excel"],
                    allow_pipeline=base_caps["allow_pipeline"],
                    max_requests_per_month=max_searches or base_caps["max_requests_per_month"],
                    max_requests_per_min=base_caps["max_requests_per_min"],
                    max_summary_tokens=base_caps["max_summary_tokens"],
                    priority=base_caps["priority"],
                )
            else:
                # Unknown plan - use conservative defaults with DB max_searches
                logger.warning(f"Unknown plan_id '{plan_id}' in database, using conservative defaults")
                caps = PlanCapabilities(
                    max_history_days=_UNKNOWN_PLAN_DEFAULTS["max_history_days"],
                    allow_excel=_UNKNOWN_PLAN_DEFAULTS["allow_excel"],
                    allow_pipeline=_UNKNOWN_PLAN_DEFAULTS["allow_pipeline"],
                    max_requests_per_month=max_searches or _UNKNOWN_PLAN_DEFAULTS["max_requests_per_month"],
                    max_requests_per_min=_UNKNOWN_PLAN_DEFAULTS["max_requests_per_min"],
                    max_summary_tokens=_UNKNOWN_PLAN_DEFAULTS["max_summary_tokens"],
                    priority=_UNKNOWN_PLAN_DEFAULTS["priority"],
                )

            db_capabilities[plan_id] = caps

        logger.info(
            f"Loaded {len(db_capabilities)} plan capabilities from database: "
            f"{list(db_capabilities.keys())}"
        )
        return db_capabilities

    except Exception as e:
        logger.error(f"Failed to load plan capabilities from database: {e}")
        logger.info("Falling back to hardcoded PLAN_CAPABILITIES")
        return PLAN_CAPABILITIES


def get_plan_capabilities() -> dict[str, PlanCapabilities]:
    """Get plan capabilities with caching.

    STORY-203 SYS-M04: Returns plan capabilities from in-memory cache (5min TTL)
    or loads from database. Falls back to hardcoded values on DB errors.

    Returns:
        dict[str, PlanCapabilities]: Plan capabilities indexed by plan_id
    """
    global _plan_capabilities_cache, _plan_capabilities_cache_time

    now = time.time()
    cache_age = now - _plan_capabilities_cache_time

    # Return cached data if still valid
    if _plan_capabilities_cache is not None and cache_age < PLAN_CAPABILITIES_CACHE_TTL:
        logger.debug(f"Plan capabilities cache HIT (age={cache_age:.1f}s)")
        return _plan_capabilities_cache

    # Cache miss or expired - reload from DB
    logger.debug("Plan capabilities cache MISS - loading from database")
    _plan_capabilities_cache = _load_plan_capabilities_from_db()
    _plan_capabilities_cache_time = now

    return _plan_capabilities_cache


def clear_plan_capabilities_cache() -> None:
    """Clear plan capabilities cache (useful for testing or after plan updates).

    STORY-203 SYS-M04: Forces next get_plan_capabilities() call to reload from DB.
    """
    global _plan_capabilities_cache, _plan_capabilities_cache_time
    _plan_capabilities_cache = None
    _plan_capabilities_cache_time = 0
    logger.info("Plan capabilities cache cleared")


# ============================================================================
# Quota Info Model
# ============================================================================

class QuotaInfo(BaseModel):
    """Complete quota information for a user."""
    allowed: bool
    plan_id: str
    plan_name: str
    capabilities: dict
    quota_used: int
    quota_remaining: int
    quota_reset_date: datetime
    trial_expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
    # STORY-309 AC5: Dunning degradation fields
    dunning_phase: str = "healthy"  # "healthy" | "active_retries" | "grace_period" | "blocked"
    days_since_failure: Optional[int] = None


# ============================================================================
# STORY-320: Trial Phase (Paywall Suave)
# ============================================================================

class TrialPhaseInfo(TypedDict):
    phase: str  # "full_access" | "limited_access" | "not_trial"
    day: int
    days_remaining: int


def get_trial_phase(user_id: str) -> TrialPhaseInfo:
    """Determine trial phase for soft paywall (STORY-320 AC1).

    - full_access (days 1 to TRIAL_PAYWALL_DAY): all features unrestricted
    - limited_access (day TRIAL_PAYWALL_DAY+1 to end): soft paywall active
    - not_trial: paid user or no trial

    Uses check_quota() to get trial_expires_at, then calculates current day.
    """
    from config import (
        TRIAL_PAYWALL_ENABLED,
        TRIAL_PAYWALL_DAY,
        TRIAL_DURATION_DAYS,
    )

    if not TRIAL_PAYWALL_ENABLED:
        return TrialPhaseInfo(phase="full_access", day=0, days_remaining=999)

    try:
        quota_info = check_quota(user_id)
    except Exception as e:
        logger.warning(f"STORY-320: Failed to check quota for trial phase: {e}")
        return TrialPhaseInfo(phase="full_access", day=0, days_remaining=999)

    # Not a trial user → no paywall
    if quota_info.plan_id != "free_trial":
        return TrialPhaseInfo(phase="not_trial", day=0, days_remaining=999)

    if not quota_info.trial_expires_at:
        return TrialPhaseInfo(phase="full_access", day=0, days_remaining=999)

    now = datetime.now(timezone.utc)

    # Calculate trial start from expires_at - duration
    trial_start = quota_info.trial_expires_at - timedelta(days=TRIAL_DURATION_DAYS)
    elapsed = now - trial_start
    current_day = max(1, elapsed.days + 1)  # Day 1 on first day

    diff = quota_info.trial_expires_at - now
    days_remaining = max(0, diff.days + (1 if diff.seconds > 0 else 0))

    if current_day > TRIAL_PAYWALL_DAY:
        phase = "limited_access"
    else:
        phase = "full_access"

    return TrialPhaseInfo(phase=phase, day=current_day, days_remaining=days_remaining)


# ============================================================================
# Quota Tracking Functions
# ============================================================================

def get_current_month_key() -> str:
    """Get current month key (e.g., '2026-02')."""
    return datetime.now(timezone.utc).strftime("%Y-%m")


def get_quota_reset_date() -> datetime:
    """Get next quota reset date (1st of next month)."""
    now = datetime.now(timezone.utc)
    if now.month == 12:
        return datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        return datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)


def get_monthly_quota_used(user_id: str) -> int:
    """
    Get searches used this month (lazy reset).

    If no record exists for current month, returns 0.
    Old month records are ignored (automatic reset).
    """
    from supabase_client import get_supabase
    sb = get_supabase()
    month_key = get_current_month_key()

    try:
        result = (
            sb.table("monthly_quota")
            .select("searches_count")
            .eq("user_id", user_id)
            .eq("month_year", month_key)
            .execute()
        )

        if result.data and len(result.data) > 0:
            return result.data[0]["searches_count"]
        else:
            return 0
    except Exception as e:
        logger.error(f"Error fetching monthly quota for user {mask_user_id(user_id)}: {e}")
        return 0  # Fail open (don't block user on DB errors)


def increment_monthly_quota(user_id: str, max_quota: Optional[int] = None) -> int:
    """
    Atomically increment monthly quota by 1.

    SECURITY (Issue #189): Uses atomic database operation to prevent race conditions.
    The increment is performed using PostgreSQL's ON CONFLICT DO UPDATE with
    atomic increment expression (searches_count + 1), ensuring no lost updates
    even under concurrent requests.

    Args:
        user_id: The user's ID
        max_quota: Optional maximum quota (if provided, won't increment past this)

    Returns:
        New count after increment.
    """
    from supabase_client import get_supabase
    sb = get_supabase()
    month_key = get_current_month_key()

    try:
        # ATOMIC OPERATION: Use PostgreSQL RPC function if available
        # This eliminates race condition by doing check+increment in single transaction
        try:
            result = sb.rpc(
                "increment_quota_atomic",
                {
                    "p_user_id": user_id,
                    "p_month_year": month_key,
                    "p_max_quota": max_quota,
                }
            ).execute()

            if result.data and len(result.data) > 0:
                new_count = result.data[0].get("new_count", 0)
                was_at_limit = result.data[0].get("was_at_limit", False)
                if was_at_limit:
                    logger.warning(f"User {mask_user_id(user_id)} quota increment blocked (at limit)")
                else:
                    logger.info(f"Incremented monthly quota for user {mask_user_id(user_id)}: {new_count} (atomic RPC)")
                return new_count

        except Exception as rpc_error:
            # RPC function might not exist yet (migration not applied)
            # Fall back to atomic upsert pattern
            logger.debug(f"RPC increment_quota_atomic not available, using fallback: {rpc_error}")

        # STORY-307 AC13-AC15: Atomic fallback using RPC for SQL-level increment
        # Eliminates read-modify-write race condition by using
        # searches_count = searches_count + 1 directly in SQL
        #
        # AC14: If row doesn't exist, INSERT with searches_count = 1 (ON CONFLICT)
        # AC15: No read-modify-write — single atomic operation
        try:
            # Use RPC to execute atomic increment with ON CONFLICT
            result = sb.rpc(
                "increment_quota_fallback_atomic",
                {"p_user_id": user_id, "p_month_year": month_key, "p_max_quota": max_quota or 999999}
            ).execute()
            if result.data is not None:
                new_count = result.data if isinstance(result.data, int) else (
                    result.data[0].get("new_count", 0) if isinstance(result.data, list) and result.data else 0
                )
                logger.info(f"Incremented monthly quota for user {mask_user_id(user_id)}: {new_count} (atomic fallback RPC)")
                return new_count
        except Exception as fallback_rpc_err:
            logger.debug(f"Atomic fallback RPC not available: {fallback_rpc_err}")

        # DEBT-DB-022: Last-resort fallback removed.
        # The previous upsert with searches_count=1 was NOT atomic:
        # - ON CONFLICT would overwrite count to 1 (losing real count)
        # - Separate read after upsert was a TOCTOU race
        # Both RPC functions failed, so log clearly and fall through
        # to the outer except block which returns best-effort estimate.
        logger.warning(
            f"All atomic quota increment methods failed for user {mask_user_id(user_id)}. "
            f"RPC increment_quota_atomic and increment_quota_fallback_atomic both unavailable. "
            f"Returning current count without increment (fail-open)."
        )
        return get_monthly_quota_used(user_id)

    except Exception as e:
        logger.error(f"Error incrementing monthly quota for user {mask_user_id(user_id)}: {e}")
        # Return best-effort estimate
        try:
            return get_monthly_quota_used(user_id)
        except Exception:
            return 0


def check_and_increment_quota_atomic(
    user_id: str,
    max_quota: int
) -> tuple[bool, int, int]:
    """
    Atomically check quota limit and increment if allowed.

    SECURITY (Issue #189): This function eliminates the TOCTOU race condition
    by performing check and increment in a single atomic database operation.
    There is no window between check and increment where another request
    could slip through.

    STORY-291 AC4: When Supabase CB is open, allows the search (fail-open)
    and logs for reconciliation. Better to over-count than to block a user.

    Args:
        user_id: The user's ID
        max_quota: Maximum allowed quota for the user's plan

    Returns:
        tuple: (allowed: bool, new_count: int, quota_remaining: int)
            - allowed: True if increment was allowed (was under limit)
            - new_count: The new quota count after operation
            - quota_remaining: How many requests remain (0 if at/over limit)
    """
    from supabase_client import get_supabase, supabase_cb, CircuitBreakerOpenError
    sb = get_supabase()
    month_key = get_current_month_key()

    try:
        # Use atomic PostgreSQL function (wrapped with CB)
        result = supabase_cb.call_sync(
            sb.rpc(
                "check_and_increment_quota",
                {
                    "p_user_id": user_id,
                    "p_month_year": month_key,
                    "p_max_quota": max_quota,
                }
            ).execute
        )

        if result.data and len(result.data) > 0:
            row = result.data[0]
            allowed = row.get("allowed", False)
            new_count = row.get("new_count", 0)
            quota_remaining = row.get("quota_remaining", 0)
            logger.info(
                f"Atomic quota check for user {mask_user_id(user_id)}: allowed={allowed}, "
                f"count={new_count}, remaining={quota_remaining}"
            )
            return (allowed, new_count, quota_remaining)

        # Unexpected empty result
        logger.warning(f"Empty result from check_and_increment_quota for user {mask_user_id(user_id)}")
        return (True, 0, max_quota)  # Fail open

    except CircuitBreakerOpenError:
        # STORY-291 AC4: Fail open — allow search, reconcile later
        logger.warning(
            f"STORY-291 CB OPEN: Quota check skipped for user {mask_user_id(user_id)} "
            f"(fail-open). Will reconcile quota later."
        )
        return (True, 0, max_quota)

    except Exception as e:
        logger.error(f"Error in atomic quota check for user {mask_user_id(user_id)}: {e}")
        # Fall back to non-atomic check (better than blocking user)
        current = get_monthly_quota_used(user_id)
        if current >= max_quota:
            return (False, current, 0)
        # Increment using fallback
        new_count = increment_monthly_quota(user_id, max_quota)
        return (True, new_count, max(0, max_quota - new_count))


# ============================================================================
# STORY-322 AC5/AC6: Organization-level quota helpers
# ============================================================================


def get_user_org_plan(user_id: str) -> Optional[tuple[str, str, int]]:
    """Check if user belongs to an org with consultoria plan.

    Returns (org_id, plan_type, max_requests_per_month) or None.
    Used by check_quota to switch from per-user to per-org quota pool.
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        member = (
            sb.table("organization_members")
            .select("org_id, accepted_at")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if not member.data or not member.data[0].get("accepted_at"):
            return None

        org_id = member.data[0]["org_id"]
        org = (
            sb.table("organizations")
            .select("plan_type")
            .eq("id", org_id)
            .single()
            .execute()
        )
        if not org.data:
            return None

        org_plan = org.data.get("plan_type", "")
        if org_plan not in PLAN_CAPABILITIES:
            return None

        caps = PLAN_CAPABILITIES[org_plan]
        return (org_id, org_plan, caps["max_requests_per_month"])

    except Exception as e:
        logger.warning(f"Failed to check org plan for user {mask_user_id(user_id)}: {e}")
        return None


def check_and_increment_org_quota_atomic(
    org_id: str,
    user_id: str,
    max_quota: int,
) -> tuple[bool, int, int]:
    """Atomically check and increment quota at the org level.

    STORY-322 AC6: Quota is shared across all org members.
    Uses the same RPC function but with org_id as the user_id key
    (the quota table tracks by a generic subject_id).
    """
    # Reuse the same function with org_id as the "user" identifier
    # The monthly_quota table uses user_id column but semantically it's the quota subject
    return check_and_increment_quota_atomic(org_id, max_quota)


# ============================================================================
# Profile-Based Plan Fallback (prevents "fail to free" anti-pattern)
# ============================================================================

# STORY-309 AC6: Extended grace period (was 3, now 7 for post-retry dunning)
SUBSCRIPTION_GRACE_DAYS = 7


def get_plan_from_profile(user_id: str, sb=None) -> Optional[str]:
    """Get user's plan from profiles.plan_type (reliable fallback).

    This is the safety net: profiles.plan_type is updated synchronously
    during plan activation (_activate_plan) and by admin actions, so it
    reflects the user's LAST KNOWN paid plan even when user_subscriptions
    has transient issues (billing gaps, Stripe webhook delays, DB errors).

    Returns valid plan_id or None if lookup fails.
    """
    try:
        if sb is None:
            from supabase_client import get_supabase
            sb = get_supabase()

        result = (
            sb.table("profiles")
            .select("plan_type")
            .eq("id", user_id)
            .single()
            .execute()
        )

        if not result.data:
            return None

        plan_type = result.data.get("plan_type", "free_trial")

        # Map legacy profile values to current plan IDs
        PLAN_TYPE_MAP = {
            "master": "sala_guerra",
            "premium": "maquina",
            "basic": "consultor_agil",
            "free": "free_trial",
        }
        mapped = PLAN_TYPE_MAP.get(plan_type, plan_type)

        # STORY-203 SYS-M04: Check against dynamic plan capabilities
        plan_caps = get_plan_capabilities()
        if mapped in plan_caps:
            return mapped

        logger.warning(
            f"Unknown plan_type '{plan_type}' in profile for user {mask_user_id(user_id)}, "
            f"mapped to '{mapped}' which is not in plan capabilities"
        )
        return None

    except Exception as e:
        logger.warning(f"Failed to get plan from profile for user {mask_user_id(user_id)}: {e}")
        return None


# ============================================================================
# Main Quota Check
# ============================================================================

def check_quota(user_id: str) -> QuotaInfo:
    """
    Check user's plan and quota status.

    Returns complete quota info including capabilities and usage.

    RESILIENCE: Uses a multi-layer lookup to prevent paid users from
    being downgraded to free_trial due to transient errors:
      1. Active subscription in user_subscriptions (primary)
      2. Recently-expired subscription within grace period (billing gap)
      3. profiles.plan_type (last known plan - reliable fallback)
      4. free_trial (absolute last resort - only for truly new users)

    STORY-291 AC3/AC4: When Supabase CB is open, uses in-memory plan cache
    as fallback. If cache miss, allows search (fail-open) with logging.
    """
    from supabase_client import get_supabase, supabase_cb, CircuitBreakerOpenError
    sb = get_supabase()

    plan_id = None
    expires_at_dt: Optional[datetime] = None
    subscription_found = False
    cb_open = False

    # --- Layer 0 (STORY-291): Check if CB is open — use cache fallback ---
    if supabase_cb.state == "OPEN":
        cb_open = True
        cached_plan = _get_cached_plan_status(user_id)
        if cached_plan:
            logger.info(
                f"STORY-291 CB OPEN: Using cached plan '{cached_plan}' for user {mask_user_id(user_id)}"
            )
            plan_id = cached_plan
            subscription_found = True
        else:
            # AC4: No cached plan — fail open with last known plan
            logger.warning(
                f"STORY-291 CB OPEN + CACHE MISS for user {mask_user_id(user_id)}: "
                f"Allowing search (fail-open). Will reconcile later."
            )
            plan_id = "smartlic_pro"  # Generous fail-open default
            subscription_found = True

    # --- Layer 1: Active subscription ---
    if not subscription_found:
        try:
            result = supabase_cb.call_sync(
                sb.table("user_subscriptions")
                .select("id, plan_id, expires_at")
                .eq("user_id", user_id)
                .eq("is_active", True)
                .order("created_at", desc=True)
                .limit(1)
                .execute
            )

            if result.data and len(result.data) > 0:
                sub = result.data[0]
                plan_id = sub.get("plan_id", None)
                expires_at_str = sub.get("expires_at")
                expires_at_dt = (
                    datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                    if expires_at_str
                    else None
                )
                subscription_found = True

        except CircuitBreakerOpenError:
            cb_open = True
            logger.warning(f"STORY-291 CB OPEN during subscription check for user {mask_user_id(user_id)}")
        except Exception as e:
            logger.error(f"Error fetching active subscription for user {mask_user_id(user_id)}: {e}")

    # --- Layer 2: Recently-expired subscription (grace period for billing gaps) ---
    if not subscription_found and not cb_open:
        try:
            grace_cutoff = (datetime.now(timezone.utc) - timedelta(days=SUBSCRIPTION_GRACE_DAYS)).isoformat()
            result = supabase_cb.call_sync(
                sb.table("user_subscriptions")
                .select("id, plan_id, expires_at")
                .eq("user_id", user_id)
                .gte("expires_at", grace_cutoff)
                .order("expires_at", desc=True)
                .limit(1)
                .execute
            )

            if result.data and len(result.data) > 0:
                sub = result.data[0]
                plan_id = sub.get("plan_id", None)
                expires_at_str = sub.get("expires_at")
                expires_at_dt = (
                    datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                    if expires_at_str
                    else None
                )
                subscription_found = True
                logger.info(
                    f"Using grace-period subscription for user {mask_user_id(user_id)}: "
                    f"plan={plan_id}, expires_at={expires_at_str}"
                )
        except CircuitBreakerOpenError:
            cb_open = True
            logger.warning(f"STORY-291 CB OPEN during grace-period check for user {mask_user_id(user_id)}")
        except Exception as e:
            logger.warning(f"Error fetching grace-period subscription for user {mask_user_id(user_id)}: {e}")

    # --- Layer 2.5 (STORY-291): CB opened mid-flow — check cache ---
    if cb_open and not subscription_found:
        cached_plan = _get_cached_plan_status(user_id)
        if cached_plan:
            logger.info(f"STORY-291 CB OPEN mid-flow: Using cached plan '{cached_plan}' for {mask_user_id(user_id)}")
            plan_id = cached_plan
            subscription_found = True
        else:
            logger.warning(
                f"STORY-291 CB OPEN + CACHE MISS for user {mask_user_id(user_id)}: fail-open"
            )
            plan_id = "smartlic_pro"
            subscription_found = True

    # --- Layer 3: Profile-based fallback (last known plan) ---
    if not subscription_found or not plan_id:
        profile_plan = get_plan_from_profile(user_id, sb)
        if profile_plan and profile_plan != "free_trial":
            logger.warning(
                f"FALLBACK ACTIVATED for user {mask_user_id(user_id)}: "
                f"no active subscription found, using profiles.plan_type='{profile_plan}'. "
                f"This may indicate a Stripe billing gap or webhook failure."
            )
            plan_id = profile_plan
            expires_at_dt = None  # No expiry data available from profile
        elif not plan_id:
            # Layer 4: Absolute last resort
            plan_id = "free_trial"
            expires_at_dt = None

    # STORY-291 AC3: Cache plan status for future CB-open fallback
    if plan_id and not cb_open:
        _cache_plan_status(user_id, plan_id)

    # STORY-203 SYS-M04: Get plan capabilities from database-driven cache
    plan_caps = get_plan_capabilities()
    caps = plan_caps.get(plan_id, plan_caps.get("free_trial", PLAN_CAPABILITIES["free_trial"]))
    plan_name = PLAN_NAMES.get(plan_id, "FREE Trial")

    # Check expiry — ONLY for free_trial (trial expiry) vs paid (billing grace)
    if expires_at_dt and datetime.now(timezone.utc) > expires_at_dt:
        if plan_id == "free_trial":
            # Free trial expired: block immediately
            return QuotaInfo(
                allowed=False,
                plan_id=plan_id,
                plan_name=plan_name,
                capabilities=caps,
                quota_used=0,
                quota_remaining=0,
                quota_reset_date=get_quota_reset_date(),
                trial_expires_at=expires_at_dt,
                error_message="Seu trial expirou. Veja o valor que você analisou e continue tendo vantagem.",
            )
        else:
            # Paid plan expired: allow grace period before blocking
            grace_end = expires_at_dt + timedelta(days=SUBSCRIPTION_GRACE_DAYS)
            if datetime.now(timezone.utc) > grace_end:
                return QuotaInfo(
                    allowed=False,
                    plan_id=plan_id,
                    plan_name=plan_name,
                    capabilities=caps,
                    quota_used=0,
                    quota_remaining=0,
                    quota_reset_date=get_quota_reset_date(),
                    trial_expires_at=expires_at_dt,
                    error_message=(
                        f"Sua assinatura {plan_name} expirou. "
                        f"Renove para continuar com acesso completo."
                    ),
                )
            # Within grace period: allow with full capabilities
            logger.info(
                f"User {mask_user_id(user_id)} in billing grace period "
                f"(plan={plan_id}, expired={expires_at_dt.isoformat()}, "
                f"grace_until={grace_end.isoformat()})"
            )

    # Check monthly quota
    quota_used = get_monthly_quota_used(user_id)
    quota_limit = caps["max_requests_per_month"]
    quota_remaining = max(0, quota_limit - quota_used)

    if quota_used >= quota_limit:
        reset_date = get_quota_reset_date()
        return QuotaInfo(
            allowed=False,
            plan_id=plan_id,
            plan_name=plan_name,
            capabilities=caps,
            quota_used=quota_used,
            quota_remaining=0,
            quota_reset_date=reset_date,
            trial_expires_at=expires_at_dt,
            error_message=f"Você atingiu {quota_limit} análises este mês. Seu limite renova em {reset_date.strftime('%d/%m/%Y')}.",
        )

    # STORY-309 AC5: Dunning degradation — restrict access based on days since first failure
    subscription_status_for_dunning = None
    try:
        if not cb_open:
            status_result = supabase_cb.call_sync(
                sb.table("profiles")
                .select("subscription_status")
                .eq("id", user_id)
                .single()
                .execute
            )
            if status_result.data:
                subscription_status_for_dunning = status_result.data.get("subscription_status")
    except Exception:
        pass  # Non-fatal — degrade gracefully

    if subscription_status_for_dunning == "past_due":
        from services.dunning import get_days_since_failure, get_dunning_phase
        days = get_days_since_failure(user_id)
        phase = get_dunning_phase(days)

        if phase == "blocked":
            # Day 21+: Fully blocked — redirect to /planos
            return QuotaInfo(
                allowed=False,
                plan_id=plan_id,
                plan_name=plan_name,
                capabilities=caps,
                quota_used=0,
                quota_remaining=0,
                quota_reset_date=get_quota_reset_date(),
                trial_expires_at=None,
                error_message="Seu pagamento falhou há mais de 21 dias. Atualize seu método de pagamento para continuar.",
                dunning_phase=phase,
                days_since_failure=days,
            )
        elif phase == "grace_period":
            # Days 14-21: Read-only — can view pipeline/historico but no new searches
            # Set quota_remaining to 0 to block new searches
            return QuotaInfo(
                allowed=False,
                plan_id=plan_id,
                plan_name=plan_name,
                capabilities=caps,
                quota_used=0,
                quota_remaining=0,
                quota_reset_date=get_quota_reset_date(),
                trial_expires_at=None,
                error_message="Seu pagamento está pendente. Acesso somente leitura até a regularização.",
                dunning_phase=phase,
                days_since_failure=days,
            )

    # All checks passed
    return QuotaInfo(
        allowed=True,
        plan_id=plan_id,
        plan_name=plan_name,
        capabilities=caps,
        quota_used=quota_used,
        quota_remaining=quota_remaining,
        quota_reset_date=get_quota_reset_date(),
        trial_expires_at=expires_at_dt,
        error_message=None,
    )


# ============================================================================
# Exception Types
# ============================================================================

class QuotaExceededError(Exception):
    """Raised when user has no remaining search credits."""
    pass


# ============================================================================
# STORY-265 AC7-AC9: require_active_plan dependency
# ============================================================================

async def require_active_plan(user: dict) -> dict:
    """FastAPI dependency: ensures user has an active plan (valid trial OR paid subscription).

    STORY-265 AC7: Encapsulates verification of active plan status.
    STORY-265 AC8: Returns HTTP 403 with structured body on expired trial/plan.
    STORY-265 AC9: Read-only endpoints (GET /pipeline, GET /sessions, GET /me)
                   should NOT use this dependency.
    STORY-291 AC4: When Supabase CB is open, allows user through (fail-open).
    STORY-309 AC5: Returns HTTP 402 when user is in dunning grace_period or blocked phase.

    Usage:
        @router.post("/endpoint")
        async def my_endpoint(user: dict = Depends(require_active_plan)):
            ...

    Note: Must be composed with require_auth. Use as:
        from auth import require_auth
        from fastapi import Depends
        user = Depends(require_active_plan)
        # This dependency receives a pre-authenticated user dict.
        # It should be used via _require_active_plan_dep() which chains with require_auth.

    Returns:
        dict: The authenticated user dict (pass-through on success).

    Raises:
        HTTPException(402): If user is in dunning grace_period or blocked phase.
        HTTPException(403): If trial expired or plan inactive.
    """
    from fastapi import HTTPException
    from authorization import has_master_access
    from supabase_client import CircuitBreakerOpenError

    user_id = user["id"]

    # Admins/masters always bypass plan checks
    try:
        if await has_master_access(user_id):
            return user
    except CircuitBreakerOpenError:
        # STORY-291 AC4: CB open — can't check roles, allow through
        logger.warning(
            f"STORY-291 CB OPEN: Bypassing master check for user {mask_user_id(user_id)} (fail-open)"
        )
        return user
    except Exception:
        pass

    try:
        quota_info = await asyncio.to_thread(check_quota, user_id)
    except CircuitBreakerOpenError:
        # STORY-291 AC4: CB open — allow user through
        logger.warning(
            f"STORY-291 CB OPEN: Bypassing plan check for user {mask_user_id(user_id)} (fail-open)"
        )
        return user

    # STORY-309 AC5: Dunning phase enforcement
    _dunning_phase = getattr(quota_info, "dunning_phase", "healthy")
    _days_since_failure = getattr(quota_info, "days_since_failure", None)
    if _dunning_phase == "blocked":
        logger.info(
            "dunning_blocked",
            extra={
                "user_id": mask_user_id(user_id),
                "dunning_phase": "blocked",
                "days_since_failure": _days_since_failure,
                "plan_id": quota_info.plan_id,
            },
        )
        raise HTTPException(
            status_code=402,
            detail={
                "error": "dunning_blocked",
                "message": getattr(quota_info, "error_message", "") or "Atualize seu método de pagamento para continuar.",
                "upgrade_url": "/planos",
                "dunning_phase": "blocked",
                "days_since_failure": _days_since_failure,
            },
        )
    elif _dunning_phase == "grace_period":
        logger.info(
            "dunning_grace_period_blocked",
            extra={
                "user_id": mask_user_id(user_id),
                "dunning_phase": "grace_period",
                "days_since_failure": _days_since_failure,
                "plan_id": quota_info.plan_id,
            },
        )
        raise HTTPException(
            status_code=402,
            detail={
                "error": "dunning_grace_period",
                "message": getattr(quota_info, "error_message", "") or "Seu pagamento está pendente. Acesso somente leitura.",
                "upgrade_url": "/planos",
                "dunning_phase": "grace_period",
                "days_since_failure": _days_since_failure,
            },
        )

    if not quota_info.allowed:
        # STORY-265 AC12: Structured logging for trial blocks
        is_trial = quota_info.plan_id == "free_trial"
        error_type = "trial_expired" if is_trial else "plan_expired"

        days_overdue = 0
        if quota_info.trial_expires_at:
            delta = datetime.now(timezone.utc) - quota_info.trial_expires_at
            days_overdue = max(0, delta.days)

        logger.info(
            "trial_blocked",
            extra={
                "user_id": mask_user_id(user_id),
                "error_type": error_type,
                "plan_id": quota_info.plan_id,
                "expired_at": quota_info.trial_expires_at.isoformat() if quota_info.trial_expires_at else None,
                "days_overdue": days_overdue,
            },
        )

        # STORY-265 AC8: Structured 403 response
        raise HTTPException(
            status_code=403,
            detail={
                "error": error_type,
                "message": quota_info.error_message or "Seu acesso expirou. Reative para continuar analisando oportunidades.",
                "upgrade_url": "/planos",
            },
        )

    return user


async def _require_active_plan_dep(user: dict = None) -> dict:
    """Internal: chains require_auth + require_active_plan for use as Depends().

    Usage in routes:
        from quota import get_active_plan_dependency
        @router.post("/endpoint")
        async def my_endpoint(user: dict = Depends(get_active_plan_dependency())):
            ...
    """
    return await require_active_plan(user)


def get_active_plan_dependency():
    """Create a FastAPI dependency that chains require_auth → require_active_plan.

    STORY-265 AC7: Use this on endpoints that must block expired trials.
    STORY-265 AC9: Do NOT use on read-only endpoints.

    Returns:
        A FastAPI Depends-compatible callable.
    """
    from fastapi import Depends
    from auth import require_auth

    async def _dep(user: dict = Depends(require_auth)):
        return await require_active_plan(user)

    return _dep


def _ensure_profile_exists(user_id: str, sb) -> bool:
    """Ensure user profile exists in the profiles table.

    Creates a minimal profile if one doesn't exist (handles cases where
    the trigger on auth.users didn't fire or failed).

    Returns True if profile exists or was created, False on error.
    """
    try:
        # Check if profile exists
        result = sb.table("profiles").select("id").eq("id", user_id).execute()
        if result.data and len(result.data) > 0:
            return True

        # Profile doesn't exist - try to get user email from auth
        try:
            user_data = sb.auth.admin.get_user_by_id(user_id)
            email = user_data.user.email if user_data and user_data.user else f"{user_id[:8]}@placeholder.local"
        except Exception as e:
            logger.warning(f"Could not fetch user email for profile creation: {e}")
            email = f"{user_id[:8]}@placeholder.local"

        # Create minimal profile
        sb.table("profiles").insert({
            "id": user_id,
            "email": email,
            "plan_type": "free_trial",
        }).execute()
        logger.info(f"Created missing profile for user {mask_user_id(user_id)}")
        return True
    except Exception as e:
        logger.error(f"Failed to ensure profile exists for user {mask_user_id(user_id)}: {e}")
        return False


# ============================================================================
# Shared Fallback Builders (AC7: eliminate duplication across routes)
# ============================================================================

def create_fallback_quota_info(user_id: str) -> "QuotaInfo":
    """Create QuotaInfo from profile's plan_type when subscription check fails.

    Shared by routes/search.py and routes/user.py to eliminate duplication.
    Prevents the "fail to free_trial" anti-pattern by using profiles.plan_type
    as a reliable last-known-plan fallback.
    """
    fallback_plan = get_plan_from_profile(user_id) or "free_trial"
    fallback_caps = PLAN_CAPABILITIES.get(fallback_plan, PLAN_CAPABILITIES["free_trial"])
    fallback_name = PLAN_NAMES.get(fallback_plan, "FREE Trial") if fallback_plan != "free_trial" else "FREE Trial"
    if fallback_plan != "free_trial":
        logger.warning(
            f"PLAN FALLBACK for user {mask_user_id(user_id)}: "
            f"subscription check failed, using profiles.plan_type='{fallback_plan}'"
        )
    return QuotaInfo(
        allowed=True,
        plan_id=fallback_plan,
        plan_name=fallback_name,
        capabilities=fallback_caps,
        quota_used=0,
        quota_remaining=999999,
        quota_reset_date=datetime.now(timezone.utc),
        trial_expires_at=None,
        error_message=None,
    )


def create_legacy_quota_info() -> "QuotaInfo":
    """Create QuotaInfo for legacy mode (ENABLE_NEW_PRICING=false).

    Shared by routes/search.py and routes/user.py to eliminate duplication.
    """
    return QuotaInfo(
        allowed=True,
        plan_id="legacy",
        plan_name="Legacy",
        capabilities=PLAN_CAPABILITIES["free_trial"],
        quota_used=0,
        quota_remaining=999999,
        quota_reset_date=datetime.now(timezone.utc),
        trial_expires_at=None,
        error_message=None,
    )


async def register_search_session(
    user_id: str,
    sectors: list[str],
    ufs: list[str],
    data_inicial: str,
    data_final: str,
    custom_keywords: Optional[list[str]],
    search_id: Optional[str] = None,
) -> Optional[str]:
    """Register a search session BEFORE quota consumption.

    CRIT-002 AC4: Creates a session record with status='created' as the
    FIRST operation after authentication, ensuring every quota-consuming
    search has a corresponding record in the user's history.

    Returns session_id (str) on success, None on failure.
    Retry: 1 attempt after 0.3s on transient errors.
    """
    import json as _json
    from supabase_client import get_supabase, sb_execute

    sb = get_supabase()

    if not await asyncio.to_thread(_ensure_profile_exists, user_id, sb):
        logger.error(f"Cannot register session: profile missing for user {mask_user_id(user_id)}")
        return None

    # UX-351 AC1: Prevent duplicate entries — if search_id already registered, return existing
    if search_id:
        try:
            existing = await sb_execute(
                sb.table("search_sessions")
                .select("id")
                .eq("search_id", search_id)
                .eq("user_id", user_id)
                .limit(1)
            )
            if existing.data and len(existing.data) > 0:
                logger.info(f"Session already exists for search_id={search_id[:8]}***, reusing")
                return existing.data[0]["id"]
        except Exception:
            pass  # Fall through to insert

    # CRIT-029 AC1-AC3: Parameter-based dedup — prevent duplicate history entries
    # when same search params are executed within 5 minutes (e.g. cache hits, retries).
    # Checks (user_id + sectors + ufs + date_range) instead of search_id only.
    # NOTE: Uses .filter() with PostgreSQL array literal format ({val1,val2}) because
    # supabase-py .eq() serializes Python lists as "['a','b']" which PostgREST
    # doesn't understand as array comparison — the dedup query silently returns empty.
    try:
        from datetime import datetime, timezone, timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        sorted_sectors = sorted(sectors)
        sorted_ufs = sorted(ufs)
        # PostgreSQL array literal: {val1,val2}
        sectors_pg = "{" + ",".join(sorted_sectors) + "}"
        ufs_pg = "{" + ",".join(sorted_ufs) + "}"
        existing_params = await sb_execute(
            sb.table("search_sessions")
            .select("id, created_at")
            .eq("user_id", user_id)
            .filter("sectors", "eq", sectors_pg)
            .filter("ufs", "eq", ufs_pg)
            .eq("data_inicial", data_inicial)
            .eq("data_final", data_final)
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .limit(1)
        )
        if existing_params.data and len(existing_params.data) > 0:
            existing_id = existing_params.data[0]["id"]
            logger.info(
                f"CRIT-029: Dedup match on params for user {mask_user_id(user_id)}, "
                f"reusing session {existing_id[:8]}***"
            )
            return existing_id
    except Exception as dedup_err:
        logger.debug(f"CRIT-029: Param dedup check failed (proceeding to insert): {dedup_err}")
        pass  # Fall through to insert

    for attempt in range(2):
        try:
            data = {
                "user_id": user_id,
                "sectors": sorted(sectors),
                "ufs": sorted(ufs),
                "data_inicial": data_inicial,
                "data_final": data_final,
                "custom_keywords": custom_keywords,
                "status": "created",
                "total_raw": 0,
                "total_filtered": 0,
                "valor_total": 0.0,
            }
            if search_id:
                data["search_id"] = search_id

            result = await sb_execute(sb.table("search_sessions").insert(data))

            if not result.data or len(result.data) == 0:
                raise RuntimeError("Insert returned empty result")

            session_id = result.data[0]["id"]

            # AC21: Prometheus counter
            try:
                from metrics import SESSION_STATUS
                SESSION_STATUS.labels(status="created").inc()
            except Exception:
                pass

            # AC22: Structured logging
            logger.info(_json.dumps({
                "event": "search_session_status_change",
                "session_id": session_id[:8] + "***",
                "search_id": search_id or "no_id",
                "old_status": None,
                "new_status": "created",
                "pipeline_stage": None,
                "elapsed_ms": 0,
                "user_id": mask_user_id(user_id),
            }))

            return session_id
        except Exception as e:
            if attempt == 0:
                logger.warning(
                    f"Transient error registering session for user "
                    f"{mask_user_id(user_id)}, retrying: {e}"
                )
                await asyncio.sleep(0.3)
                continue
            logger.error(
                f"Failed to register search session after retry "
                f"for user {mask_user_id(user_id)}: {e}"
            )
            return None


async def update_search_session_status(
    session_id: str,
    status: Optional[str] = None,
    pipeline_stage: Optional[str] = None,
    error_message: Optional[str] = None,
    error_code: Optional[str] = None,
    raw_count: Optional[int] = None,
    response_state: Optional[str] = None,
    completed_at: Optional[str] = None,
    duration_ms: Optional[int] = None,
    total_filtered: Optional[int] = None,
    valor_total: Optional[float] = None,
    resumo_executivo: Optional[str] = None,
    destaques: Optional[list[str]] = None,
) -> None:
    """Update search session status (fire-and-forget, non-blocking).

    CRIT-002 AC6: Dynamic UPDATE — only sets non-None fields.
    Logs errors but NEVER propagates exceptions (AC24).
    Retry: 1 attempt after 0.3s on transient errors.
    """
    import json as _json
    from supabase_client import get_supabase, sb_execute

    update_data = {}
    if status is not None:
        update_data["status"] = status
    if pipeline_stage is not None:
        update_data["pipeline_stage"] = pipeline_stage
    if error_message is not None:
        update_data["error_message"] = error_message[:500]
    if error_code is not None:
        update_data["error_code"] = error_code
    if raw_count is not None:
        update_data["raw_count"] = raw_count
    if response_state is not None:
        update_data["response_state"] = response_state
    if completed_at is not None:
        update_data["completed_at"] = completed_at
    if duration_ms is not None:
        update_data["duration_ms"] = duration_ms
    if total_filtered is not None:
        update_data["total_filtered"] = total_filtered
    if valor_total is not None:
        update_data["valor_total"] = float(valor_total)
    if resumo_executivo is not None:
        update_data["resumo_executivo"] = resumo_executivo
    if destaques is not None:
        update_data["destaques"] = destaques

    if not update_data:
        return

    for attempt in range(2):
        try:
            sb = get_supabase()
            await sb_execute(sb.table("search_sessions").update(update_data).eq("id", session_id))

            # AC21: Prometheus counter
            if status:
                try:
                    from metrics import SESSION_STATUS
                    SESSION_STATUS.labels(status=status).inc()
                except Exception:
                    pass

            # AC22: Structured logging
            logger.info(_json.dumps({
                "event": "search_session_status_change",
                "session_id": session_id[:8] + "***",
                "new_status": status,
                "pipeline_stage": pipeline_stage,
                "error_code": error_code,
            }))

            return
        except Exception as e:
            if attempt == 0:
                logger.warning(
                    f"Transient error updating session {session_id[:8]}***, retrying: {e}"
                )
                await asyncio.sleep(0.3)
                continue
            logger.error(f"Failed to update session {session_id[:8]}*** after retry: {e}")


async def save_search_session(
    user_id: str,
    sectors: list[str],
    ufs: list[str],
    data_inicial: str,
    data_final: str,
    custom_keywords: Optional[list[str]],
    total_raw: int,
    total_filtered: int,
    valor_total: float,
    resumo_executivo: Optional[str],
    destaques: Optional[list[str]],
) -> Optional[str]:
    """Save search session to history. Returns session ID or None on failure.

    AC16: Implements retry (max 1) for transient DB errors. Failure to save
    session does NOT break the search request — always returns None on error.

    Race condition analysis (TD-007/CR-09): Each call performs a single INSERT
    with unique user_id + session data. No shared mutable state between calls.
    Supabase client handles connection pooling internally. Safe for interleaving
    — no asyncio.Lock needed.
    """
    from supabase_client import get_supabase, sb_execute

    sb = get_supabase()

    # Ensure profile exists (FK constraint requires this)
    if not await asyncio.to_thread(_ensure_profile_exists, user_id, sb):
        logger.error(f"Cannot save session: profile missing for user {mask_user_id(user_id)}")
        return None

    for attempt in range(2):  # max 1 retry (0, 1)
        try:
            result = await sb_execute(
                sb.table("search_sessions")
                .insert({
                    "user_id": user_id,
                    "sectors": sorted(sectors),
                    "ufs": sorted(ufs),
                    "data_inicial": data_inicial,
                    "data_final": data_final,
                    "custom_keywords": custom_keywords,
                    "total_raw": total_raw,
                    "total_filtered": total_filtered,
                    "valor_total": float(valor_total),
                    "resumo_executivo": resumo_executivo,
                    "destaques": destaques,
                })
            )

            if not result.data or len(result.data) == 0:
                logger.error(f"Insert returned empty result for user {mask_user_id(user_id)}")
                raise RuntimeError("Insert returned empty result")

            session_id = result.data[0]["id"]
            # SECURITY: Sanitize user ID in logs (Issue #168)
            logger.info(f"Saved search session {session_id[:8]}*** for user {mask_user_id(user_id)}")
            return session_id
        except Exception as e:
            if attempt == 0:
                logger.warning(f"Transient error saving session for user {mask_user_id(user_id)}, retrying: {e}")
                await asyncio.sleep(0.3)
                continue
            logger.error(f"Failed to save search session after retry for user {mask_user_id(user_id)}: {e}")
            return None  # silent fail - don't break search results
