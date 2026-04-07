"""Trial extension service — Zero-Churn P2 §8.2.

Allows trial users to earn extra days by completing actions:
- profile_complete: +3 days (all profile fields filled)
- feedback_given: +2 days (at least 1 feedback submitted)
- referral_signup: +7 days (at least 1 referral converted)

Max total extension: 7 days (configurable via TRIAL_EXTENSION_MAX_DAYS).
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from supabase_client import get_supabase, sb_execute

logger = logging.getLogger(__name__)

EXTENSION_CONDITIONS = {
    "profile_complete": {"days": 3, "label": "Completar perfil"},
    "feedback_given": {"days": 2, "label": "Dar feedback"},
    "referral_signup": {"days": 7, "label": "Indicar um colega"},
}

# Minimum profile fields required for "profile_complete" condition
_PROFILE_REQUIRED_FIELDS = ["full_name", "company", "sector", "phone_whatsapp"]


async def _check_profile_complete(user_id: str) -> bool:
    """Check if user has filled all required profile fields."""
    sb = get_supabase()
    result = await sb_execute(
        sb.table("profiles")
        .select("full_name, company, sector, phone_whatsapp, context_data")
        .eq("id", user_id)
        .single()
    )
    if not result.data:
        return False
    profile = result.data
    for field in _PROFILE_REQUIRED_FIELDS:
        val = profile.get(field)
        if not val or (isinstance(val, str) and not val.strip()):
            return False
    # Also check context_data has at least UFs selected
    ctx = profile.get("context_data") or {}
    if not ctx.get("ufs"):
        return False
    return True


async def _check_feedback_given(user_id: str) -> bool:
    """Check if user has submitted at least one feedback."""
    sb = get_supabase()
    result = await sb_execute(
        sb.table("user_feedback")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .limit(1)
    )
    return (result.count or 0) > 0


async def _check_referral_signup(user_id: str) -> bool:
    """Check if user has at least one converted referral."""
    sb = get_supabase()
    result = await sb_execute(
        sb.table("referral_codes")
        .select("redemptions_count")
        .eq("owner_id", user_id)
        .limit(1)
    )
    if not result.data:
        return False
    return (result.data[0].get("redemptions_count") or 0) > 0


_CONDITION_CHECKS = {
    "profile_complete": _check_profile_complete,
    "feedback_given": _check_feedback_given,
    "referral_signup": _check_referral_signup,
}


async def get_extension_status(user_id: str) -> dict:
    """Return checklist of available/claimed extensions for a user."""
    from config.features import (
        TRIAL_EXTENSION_ENABLED,
        TRIAL_EXTENSION_MAX_DAYS,
    )

    if not TRIAL_EXTENSION_ENABLED:
        return {"enabled": False, "extensions": [], "total_extended": 0, "max_extension": 0, "remaining": 0}

    sb = get_supabase()
    result = await sb_execute(
        sb.table("trial_extensions")
        .select("condition, days_added")
        .eq("user_id", user_id)
    )
    claimed = {row["condition"]: row["days_added"] for row in (result.data or [])}
    total_extended = sum(claimed.values())

    extensions = []
    for cond, info in EXTENSION_CONDITIONS.items():
        is_claimed = cond in claimed
        # Check eligibility only if not claimed
        eligible = False
        if not is_claimed:
            check_fn = _CONDITION_CHECKS.get(cond)
            if check_fn:
                try:
                    eligible = await check_fn(user_id)
                except Exception:
                    logger.warning("Failed to check condition %s for %s", cond, user_id)
                    eligible = False

        days = min(info["days"], TRIAL_EXTENSION_MAX_DAYS - total_extended) if not is_claimed else claimed[cond]
        extensions.append({
            "condition": cond,
            "label": info["label"],
            "days": days,
            "claimed": is_claimed,
            "eligible": eligible,
        })

    return {
        "enabled": True,
        "extensions": extensions,
        "total_extended": total_extended,
        "max_extension": TRIAL_EXTENSION_MAX_DAYS,
        "remaining": max(0, TRIAL_EXTENSION_MAX_DAYS - total_extended),
    }


async def extend_trial(user_id: str, condition: str) -> dict:
    """Extend a user's trial by completing a condition.

    Returns dict with extension result or raises ValueError/RuntimeError.
    """
    from config.features import (
        TRIAL_EXTENSION_ENABLED,
        TRIAL_EXTENSION_MAX_DAYS,
    )

    if not TRIAL_EXTENSION_ENABLED:
        raise ValueError("Trial extensions are disabled")

    if condition not in EXTENSION_CONDITIONS:
        raise ValueError(f"Invalid condition: {condition}")

    # Verify user is on free_trial
    sb = get_supabase()
    profile_result = await sb_execute(
        sb.table("profiles")
        .select("plan_type, trial_expires_at")
        .eq("id", user_id)
        .single()
    )
    if not profile_result.data:
        raise ValueError("User profile not found")
    if profile_result.data.get("plan_type") != "free_trial":
        raise ValueError("Only trial users can extend their trial")

    # Check if trial has expired (beyond 48h grace)
    trial_expires = profile_result.data.get("trial_expires_at")
    if trial_expires:
        if isinstance(trial_expires, str):
            try:
                expires_dt = datetime.fromisoformat(trial_expires.replace("Z", "+00:00"))
            except ValueError:
                expires_dt = datetime.fromisoformat(trial_expires)
        else:
            expires_dt = trial_expires
        if expires_dt.tzinfo is None:
            expires_dt = expires_dt.replace(tzinfo=timezone.utc)
        grace_deadline = expires_dt + timedelta(hours=48)
        if datetime.now(timezone.utc) > grace_deadline:
            raise ValueError("Trial has expired beyond grace period")

    # Verify condition is met
    check_fn = _CONDITION_CHECKS.get(condition)
    if check_fn and not await check_fn(user_id):
        raise ValueError(f"Condition not met: {condition}")

    days = EXTENSION_CONDITIONS[condition]["days"]

    # Call atomic RPC
    result = await sb_execute(
        sb.rpc("extend_trial_atomic", {
            "p_user_id": user_id,
            "p_condition": condition,
            "p_days": days,
            "p_max_total": TRIAL_EXTENSION_MAX_DAYS,
        })
    )

    data = result.data
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    if not data:
        raise RuntimeError("Extension RPC returned no data")

    # Handle JSONB string return
    if isinstance(data, str):
        data = json.loads(data)

    if "error" in data:
        raise ValueError(data["error"])

    logger.info(
        "Trial extended: user=%s condition=%s days=%d total=%d",
        user_id, condition, data.get("days_added", days),
        data.get("total_extended", 0),
    )
    return data
