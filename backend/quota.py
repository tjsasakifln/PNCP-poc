"""Quota management for search credits and subscriptions."""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class QuotaExceededError(Exception):
    """Raised when user has no remaining search credits."""
    pass


def check_quota(user_id: str) -> dict:
    """Check if user has available search credits.

    Returns:
        dict with keys: allowed (bool), plan_id (str), credits_remaining (int|None),
        subscription_id (str|None)

    Raises:
        QuotaExceededError: If no credits remaining.
    """
    from supabase_client import get_supabase
    sb = get_supabase()

    # Get active subscription
    result = (
        sb.table("user_subscriptions")
        .select("id, plan_id, credits_remaining, expires_at")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        # Check if free tier still has credits
        return _check_free_tier(user_id, sb)

    sub = result.data[0]

    # Check expiry for time-based plans
    if sub["expires_at"]:
        expires = datetime.fromisoformat(sub["expires_at"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            # Deactivate expired subscription
            sb.table("user_subscriptions").update({"is_active": False}).eq("id", sub["id"]).execute()
            logger.info(f"Subscription {sub['id']} expired for user {user_id}")
            raise QuotaExceededError("Sua assinatura expirou. Renove para continuar buscando.")

    # Unlimited plans (monthly, annual, master)
    if sub["credits_remaining"] is None:
        return {
            "allowed": True,
            "plan_id": sub["plan_id"],
            "credits_remaining": None,
            "subscription_id": sub["id"],
        }

    # Credit-based plans (packs)
    if sub["credits_remaining"] <= 0:
        raise QuotaExceededError(
            "Suas buscas acabaram. Adquira um novo pacote para continuar."
        )

    return {
        "allowed": True,
        "plan_id": sub["plan_id"],
        "credits_remaining": sub["credits_remaining"],
        "subscription_id": sub["id"],
    }


def _check_free_tier(user_id: str, sb) -> dict:
    """Check free tier usage (3 searches lifetime)."""
    result = (
        sb.table("search_sessions")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )
    used = result.count or 0
    remaining = max(0, 3 - used)

    if remaining <= 0:
        raise QuotaExceededError(
            "Voce usou suas 3 buscas gratuitas. Escolha um plano para continuar."
        )

    return {
        "allowed": True,
        "plan_id": "free",
        "credits_remaining": remaining,
        "subscription_id": None,
    }


def decrement_credits(subscription_id: Optional[str], user_id: str) -> None:
    """Decrement one search credit after successful search.

    Only decrements for credit-based plans (packs). Skips for unlimited plans.
    """
    if subscription_id is None:
        # Free tier — no subscription record to update, session count is the limit
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
