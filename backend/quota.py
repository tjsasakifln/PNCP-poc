"""Quota management with plan-based capabilities."""

import logging
from datetime import datetime, timezone
from typing import Optional, TypedDict
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)


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
        "max_requests_per_month": 999999,  # Unlimited during trial (quota by expiry)
        "max_requests_per_min": 2,
        "max_summary_tokens": 200,
        "priority": PlanPriority.LOW.value,
    },
    "consultor_agil": {
        "max_history_days": 30,
        "allow_excel": False,
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
        "max_requests_per_month": 1000,
        "max_requests_per_min": 60,
        "max_summary_tokens": 1000,
        "priority": PlanPriority.CRITICAL.value,
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
        logger.error(f"Error fetching monthly quota for user {user_id}: {e}")
        return 0  # Fail open (don't block user on DB errors)


def increment_monthly_quota(user_id: str) -> int:
    """
    Increment monthly quota by 1 (upsert pattern).

    Returns new count after increment.
    """
    from supabase_client import get_supabase
    sb = get_supabase()
    month_key = get_current_month_key()

    try:
        # Get current count
        current = get_monthly_quota_used(user_id)
        new_count = current + 1

        # Upsert: update if exists, insert if not
        sb.table("monthly_quota").upsert({
            "user_id": user_id,
            "month_year": month_key,
            "searches_count": new_count,
            "updated_at": datetime.utcnow().isoformat(),
        }, on_conflict="user_id,month_year").execute()

        logger.info(f"Incremented monthly quota for user {user_id}: {new_count}")
        return new_count

    except Exception as e:
        logger.error(f"Error incrementing monthly quota for user {user_id}: {e}")
        return current + 1  # Best effort


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
        logger.error(f"Error fetching subscription for user {user_id}: {e}")
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

    session_id = result.data[0]["id"]
    logger.info(f"Saved search session {session_id} for user {user_id}")
    return session_id
