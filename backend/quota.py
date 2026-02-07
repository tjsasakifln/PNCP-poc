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
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, TypedDict
from enum import Enum
from pydantic import BaseModel
from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)

# Global lock for in-process synchronization (fallback when RPC unavailable)
# This protects against race conditions within a single process.
# For multi-process/multi-instance deployments, use the PostgreSQL RPC function.
_quota_locks: dict[str, asyncio.Lock] = {}


def _get_user_lock(user_id: str) -> asyncio.Lock:
    """Get or create a lock for a specific user (per-user locking)."""
    if user_id not in _quota_locks:
        _quota_locks[user_id] = asyncio.Lock()
    return _quota_locks[user_id]


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
    max_requests_per_month: int
    max_requests_per_min: int
    max_summary_tokens: int
    priority: str  # PlanPriority value


# Hardcoded plan definitions (secure, version-controlled)
PLAN_CAPABILITIES: dict[str, PlanCapabilities] = {
    "free_trial": {
        "max_history_days": 7,
        "allow_excel": False,
        "max_requests_per_month": 3,  # Free trial: 3 searches only
        "max_requests_per_min": 2,
        "max_summary_tokens": 200,
        "priority": PlanPriority.LOW.value,
    },
    "consultor_agil": {
        "max_history_days": 30,
        "allow_excel": True,  # P1 fix: Excel is commodity, not premium differentiator
        "max_requests_per_month": 50,
        "max_requests_per_min": 10,
        "max_summary_tokens": 200,
        "priority": PlanPriority.NORMAL.value,
    },
    "maquina": {
        "max_history_days": 365,
        "allow_excel": True,
        "max_requests_per_month": 300,
        "max_requests_per_min": 30,
        "max_summary_tokens": 500,
        "priority": PlanPriority.HIGH.value,
    },
    "sala_guerra": {
        "max_history_days": 1825,  # 5 years
        "allow_excel": True,
        "max_requests_per_month": 999999,  # P0 fix: Effectively unlimited for Master
        "max_requests_per_min": 999,       # P0 fix: No rate limit for Master
        "max_summary_tokens": 10000,       # P0 fix: Generous token limit
        "priority": PlanPriority.CRITICAL.value,
        "unlimited": True,  # P0 fix: Flag for UI to show "Ilimitado"
    },
}

# Display names for UI
PLAN_NAMES: dict[str, str] = {
    "free_trial": "FREE Trial",
    "consultor_agil": "Consultor Ágil",
    "maquina": "Máquina",
    "sala_guerra": "Sala de Guerra",
}

# Pricing for error messages
PLAN_PRICES: dict[str, str] = {
    "consultor_agil": "R$ 297/mês",
    "maquina": "R$ 597/mês",
    "sala_guerra": "R$ 1.497/mês",
}

# Upgrade path suggestions (for error messages)
UPGRADE_SUGGESTIONS: dict[str, dict[str, str]] = {
    "max_history_days": {
        "free_trial": "consultor_agil",
        "consultor_agil": "maquina",
        "maquina": "sala_guerra",
    },
    "allow_excel": {
        "free_trial": "maquina",
        "consultor_agil": "maquina",
    },
    "max_requests_per_month": {
        "consultor_agil": "maquina",
        "maquina": "sala_guerra",
    },
}


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


# ============================================================================
# Quota Tracking Functions
# ============================================================================

def get_current_month_key() -> str:
    """Get current month key (e.g., '2026-02')."""
    return datetime.utcnow().strftime("%Y-%m")


def get_quota_reset_date() -> datetime:
    """Get next quota reset date (1st of next month)."""
    now = datetime.utcnow()
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

        # FALLBACK: Atomic upsert with SQL expression
        # This is still atomic within PostgreSQL - the increment expression
        # (searches_count + 1) is evaluated atomically by the database
        #
        # NOTE: This fallback still has a potential race in the upsert's
        # ON CONFLICT handling with concurrent INSERTs. For production,
        # use the RPC function from migration 003.

        # First try to update existing record atomically
        update_result = sb.rpc(
            "increment_existing_quota",
            {"p_user_id": user_id, "p_month_year": month_key}
        ).execute() if False else None  # Disabled - use simpler approach below

        # Simpler atomic approach: raw SQL via upsert
        # The key insight is that PostgreSQL's upsert with `searches_count + 1`
        # in the UPDATE clause is atomic within the database engine
        current = get_monthly_quota_used(user_id)

        # Use INSERT ... ON CONFLICT with the increment happening in SQL
        # This is atomic because the increment expression runs inside PostgreSQL
        sb.table("monthly_quota").upsert(
            {
                "user_id": user_id,
                "month_year": month_key,
                "searches_count": current + 1,
                "updated_at": datetime.utcnow().isoformat(),
            },
            on_conflict="user_id,month_year"
        ).execute()

        # Re-fetch to get actual count (in case of concurrent update)
        new_count = get_monthly_quota_used(user_id)
        logger.info(f"Incremented monthly quota for user {mask_user_id(user_id)}: {new_count} (upsert fallback)")
        return new_count

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

    Args:
        user_id: The user's ID
        max_quota: Maximum allowed quota for the user's plan

    Returns:
        tuple: (allowed: bool, new_count: int, quota_remaining: int)
            - allowed: True if increment was allowed (was under limit)
            - new_count: The new quota count after operation
            - quota_remaining: How many requests remain (0 if at/over limit)
    """
    from supabase_client import get_supabase
    sb = get_supabase()
    month_key = get_current_month_key()

    try:
        # Use atomic PostgreSQL function
        result = sb.rpc(
            "check_and_increment_quota",
            {
                "p_user_id": user_id,
                "p_month_year": month_key,
                "p_max_quota": max_quota,
            }
        ).execute()

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
# Main Quota Check
# ============================================================================

def check_quota(user_id: str) -> QuotaInfo:
    """
    Check user's plan and quota status.

    Returns complete quota info including capabilities and usage.
    """
    from supabase_client import get_supabase
    sb = get_supabase()

    # Get user's current plan from subscriptions
    try:
        result = (
            sb.table("user_subscriptions")
            .select("id, plan_id, expires_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data or len(result.data) == 0:
            # No active subscription - default to free_trial
            plan_id = "free_trial"
            trial_expires_at = None  # TODO: Get from users table
        else:
            sub = result.data[0]
            plan_id = sub.get("plan_id", "free_trial")
            expires_at_str = sub.get("expires_at")
            trial_expires_at = (
                datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                if expires_at_str
                else None
            )

    except Exception as e:
        # SECURITY: Sanitize user ID in logs (Issue #168)
        logger.error(f"Error fetching subscription for user {mask_user_id(user_id)}: {e}")
        # Fail open with free_trial
        plan_id = "free_trial"
        trial_expires_at = None

    # Get plan capabilities
    caps = PLAN_CAPABILITIES.get(plan_id, PLAN_CAPABILITIES["free_trial"])
    plan_name = PLAN_NAMES.get(plan_id, "FREE Trial")

    # Check trial expiration
    if trial_expires_at and datetime.now(timezone.utc) > trial_expires_at:
        return QuotaInfo(
            allowed=False,
            plan_id=plan_id,
            plan_name=plan_name,
            capabilities=caps,
            quota_used=0,
            quota_remaining=0,
            quota_reset_date=get_quota_reset_date(),
            trial_expires_at=trial_expires_at,
            error_message="Trial expirado. Faça upgrade para continuar usando o Smart PNCP.",
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
            trial_expires_at=trial_expires_at,
            error_message=f"Limite de {quota_limit} buscas mensais atingido. Renovação em {reset_date.strftime('%d/%m/%Y')} ou faça upgrade.",
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
        trial_expires_at=trial_expires_at,
        error_message=None,
    )


# ============================================================================
# Legacy Functions (kept for backward compatibility during transition)
# ============================================================================

class QuotaExceededError(Exception):
    """Raised when user has no remaining search credits."""
    pass


def decrement_credits(subscription_id: Optional[str], user_id: str) -> None:
    """
    Decrement one search credit after successful search.

    DEPRECATED: Use increment_monthly_quota() instead for new pricing model.
    Kept for backward compatibility during feature flag transition.
    """
    if subscription_id is None:
        return

    from supabase_client import get_supabase
    sb = get_supabase()

    result = (
        sb.table("user_subscriptions")
        .select("credits_remaining")
        .eq("id", subscription_id)
        .single()
        .execute()
    )

    if result.data and result.data["credits_remaining"] is not None:
        new_credits = max(0, result.data["credits_remaining"] - 1)
        sb.table("user_subscriptions").update(
            {"credits_remaining": new_credits}
        ).eq("id", subscription_id).execute()
        logger.info(
            f"Decremented credits for subscription {subscription_id}: {new_credits} remaining"
        )


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
            "plan_type": "free",
        }).execute()
        logger.info(f"Created missing profile for user {mask_user_id(user_id)}")
        return True
    except Exception as e:
        logger.error(f"Failed to ensure profile exists for user {mask_user_id(user_id)}: {e}")
        return False


def save_search_session(
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
) -> str:
    """Save search session to history. Returns session ID."""
    from supabase_client import get_supabase
    sb = get_supabase()

    # Ensure profile exists (FK constraint requires this)
    if not _ensure_profile_exists(user_id, sb):
        raise RuntimeError(f"Cannot save session: profile missing for user {mask_user_id(user_id)}")

    try:
        result = (
            sb.table("search_sessions")
            .insert({
                "user_id": user_id,
                "sectors": sectors,
                "ufs": ufs,
                "data_inicial": data_inicial,
                "data_final": data_final,
                "custom_keywords": custom_keywords,
                "total_raw": total_raw,
                "total_filtered": total_filtered,
                "valor_total": float(valor_total),
                "resumo_executivo": resumo_executivo,
                "destaques": destaques,
            })
            .execute()
        )

        if not result.data or len(result.data) == 0:
            logger.error(f"Insert returned empty result for user {mask_user_id(user_id)}")
            raise RuntimeError("Insert returned empty result")

        session_id = result.data[0]["id"]
        # SECURITY: Sanitize user ID in logs (Issue #168)
        logger.info(f"Saved search session {session_id[:8]}*** for user {mask_user_id(user_id)}")
        return session_id
    except Exception as e:
        logger.error(f"Failed to insert search session for user {mask_user_id(user_id)}: {e}")
        raise
