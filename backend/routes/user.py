"""User profile and password management routes.

Extracted from main.py as part of STORY-202 monolith decomposition.
"""

import logging
import os
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Depends, Request
from auth import require_auth
from authorization import _check_user_roles, _get_admin_ids, _get_master_quota_info
from config import ENABLE_NEW_PRICING
from schemas import UserProfileResponse
from log_sanitizer import mask_user_id, log_user_action

logger = logging.getLogger(__name__)

router = APIRouter(tags=["user"])

# STORY-210 AC12: Per-user rate limiting for /change-password
# 5 attempts per 15 minutes (900 seconds)
_CHANGE_PASSWORD_MAX_ATTEMPTS = 5
_CHANGE_PASSWORD_WINDOW_SECONDS = 900
_change_password_attempts: dict[str, list[float]] = defaultdict(list)


def _check_change_password_rate_limit(user_id: str) -> None:
    """Check and enforce rate limit for password change.

    Raises HTTPException 429 if limit exceeded.
    """
    now = time.time()
    cutoff = now - _CHANGE_PASSWORD_WINDOW_SECONDS

    # Prune old attempts
    attempts = _change_password_attempts[user_id]
    _change_password_attempts[user_id] = [t for t in attempts if t > cutoff]

    if len(_change_password_attempts[user_id]) >= _CHANGE_PASSWORD_MAX_ATTEMPTS:
        logger.warning(f"Rate limit exceeded for password change: {mask_user_id(user_id)}")
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas de alteração de senha. Tente novamente em 15 minutos."
        )

    _change_password_attempts[user_id].append(now)


@router.post("/change-password")
async def change_password(
    request: Request,
    user: dict = Depends(require_auth),
):
    """Change current user's password."""
    # STORY-210 AC12: Rate limit — 5 attempts per 15 minutes
    _check_change_password_rate_limit(user["id"])

    body = await request.json()
    new_password = body.get("new_password", "")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter no minimo 6 caracteres")

    from supabase_client import get_supabase
    sb = get_supabase()
    try:
        sb.auth.admin.update_user_by_id(user["id"], {"password": new_password})
    except Exception:
        log_user_action(logger, "password-change-failed", user["id"], level=logging.ERROR)
        raise HTTPException(status_code=500, detail="Erro ao alterar senha")

    log_user_action(logger, "password-changed", user["id"])
    return {"success": True}


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(user: dict = Depends(require_auth)):
    """
    Get current user profile with plan capabilities and quota status.
    """
    from quota import check_quota, QuotaInfo, PLAN_CAPABILITIES, get_plan_from_profile, PLAN_NAMES
    from supabase_client import get_supabase
    from datetime import datetime, timezone

    is_admin, is_master = _check_user_roles(user["id"])
    if user["id"].lower() in _get_admin_ids():
        is_admin = True
        is_master = True

    if is_admin or is_master:
        role = "ADMIN" if is_admin else "MASTER"
        logger.info(f"{role} user detected: {mask_user_id(user['id'])} - granting sala_guerra access")
        quota_info = _get_master_quota_info(is_admin=is_admin)
    elif ENABLE_NEW_PRICING:
        try:
            quota_info = check_quota(user["id"])
        except Exception as e:
            logger.error(f"Failed to check quota for user {user['id']}: {e}")
            fallback_plan = get_plan_from_profile(user["id"]) or "free_trial"
            fallback_caps = PLAN_CAPABILITIES.get(fallback_plan, PLAN_CAPABILITIES["free_trial"])
            fallback_name = PLAN_NAMES.get(fallback_plan, "FREE Trial") if fallback_plan != "free_trial" else "FREE Trial"
            if fallback_plan != "free_trial":
                logger.warning(
                    f"PLAN FALLBACK for user {mask_user_id(user['id'])}: "
                    f"subscription check failed, using profiles.plan_type='{fallback_plan}'"
                )
            quota_info = QuotaInfo(
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
    else:
        logger.debug("New pricing disabled, using legacy behavior")
        from quota import PLAN_CAPABILITIES as PC
        quota_info = QuotaInfo(
            allowed=True,
            plan_id="legacy",
            plan_name="Legacy",
            capabilities=PC["free_trial"],
            quota_used=0,
            quota_remaining=999999,
            quota_reset_date=datetime.now(timezone.utc),
            trial_expires_at=None,
            error_message=None,
        )

    try:
        sb = get_supabase()
        user_data = sb.auth.admin.get_user_by_id(user["id"])
        email = user_data.user.email if user_data and user_data.user else user.get("email", "unknown@example.com")
    except Exception as e:
        logger.warning(f"Failed to fetch user email: {e}")
        email = user.get("email", "unknown@example.com")

    if quota_info.trial_expires_at:
        if datetime.now(timezone.utc) > quota_info.trial_expires_at:
            subscription_status = "expired"
        else:
            subscription_status = "trial"
    else:
        subscription_status = "active"

    return UserProfileResponse(
        user_id=user["id"],
        email=email,
        plan_id=quota_info.plan_id,
        plan_name=quota_info.plan_name,
        capabilities=quota_info.capabilities,
        quota_used=quota_info.quota_used,
        quota_remaining=quota_info.quota_remaining,
        quota_reset_date=quota_info.quota_reset_date.isoformat(),
        trial_expires_at=quota_info.trial_expires_at.isoformat() if quota_info.trial_expires_at else None,
        subscription_status=subscription_status,
        is_admin=is_admin,
    )
