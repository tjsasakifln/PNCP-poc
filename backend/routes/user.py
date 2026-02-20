"""User profile, password management, account deletion, and data export routes.

Extracted from main.py as part of STORY-202 monolith decomposition.
STORY-213: Added DELETE /me (account deletion) and GET /me/export (data portability).
"""

import hashlib
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import Response
from auth import require_auth
from authorization import check_user_roles, get_admin_ids, get_master_quota_info
from config import ENABLE_NEW_PRICING
from database import get_db
from schemas import (
    UserProfileResponse, SuccessResponse, DeleteAccountResponse,
    PerfilContexto, PerfilContextoResponse, validate_password,
)
from log_sanitizer import mask_user_id, log_user_action
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["user"])


# ============================================================================
# GTM-010: Trial Status Response Model
# ============================================================================

class TrialStatusResponse(BaseModel):
    plan: str
    days_remaining: int
    searches_used: int
    searches_limit: int
    expires_at: str | None = None
    is_expired: bool

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


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    request: Request,
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """Change current user's password."""
    # STORY-210 AC12: Rate limit — 5 attempts per 15 minutes
    _check_change_password_rate_limit(user["id"])

    body = await request.json()
    new_password = body.get("new_password", "")

    # STORY-226 AC17: Validate password policy
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        db.auth.admin.update_user_by_id(user["id"], {"password": new_password})
    except Exception:
        log_user_action(logger, "password-change-failed", user["id"], level=logging.ERROR)
        raise HTTPException(status_code=500, detail="Erro ao alterar senha")

    log_user_action(logger, "password-changed", user["id"])
    return {"success": True}


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(user: dict = Depends(require_auth), db=Depends(get_db)):
    """
    Get current user profile with plan capabilities and quota status.
    """
    from quota import check_quota, create_fallback_quota_info, create_legacy_quota_info

    is_admin_flag, is_master = await check_user_roles(user["id"])
    if user["id"].lower() in get_admin_ids():
        is_admin_flag = True
        is_master = True

    if is_admin_flag or is_master:
        role = "ADMIN" if is_admin_flag else "MASTER"
        logger.info(f"{role} user detected: {mask_user_id(user['id'])} - granting sala_guerra access")
        quota_info = get_master_quota_info(is_admin=is_admin_flag)
    elif ENABLE_NEW_PRICING:
        try:
            quota_info = check_quota(user["id"])
        except Exception as e:
            logger.error(f"Failed to check quota for user {user['id']}: {e}")
            quota_info = create_fallback_quota_info(user["id"])
    else:
        logger.debug("New pricing disabled, using legacy behavior")
        quota_info = create_legacy_quota_info()

    try:
        user_data = db.auth.admin.get_user_by_id(user["id"])
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
        is_admin=is_admin_flag,
    )


@router.get("/trial-status", response_model=TrialStatusResponse)
async def get_trial_status(user: dict = Depends(require_auth), db=Depends(get_db)):
    """Get detailed trial status for conversion flow (GTM-010 AC3).

    Returns days remaining, usage stats, and expiration info.
    """
    from quota import check_quota, PLAN_CAPABILITIES

    user_id = user["id"]

    try:
        quota_info = check_quota(user_id)
    except Exception as e:
        # CRIT-005 AC24: Surface error instead of swallowing with defaults
        logger.error(f"Failed to check quota for trial status: {e}")
        raise HTTPException(
            status_code=503,
            detail="Informacao de trial temporariamente indisponivel"
        )

    plan_id = quota_info.plan_id
    caps = PLAN_CAPABILITIES.get(plan_id, PLAN_CAPABILITIES["free_trial"])

    days_remaining = 0
    is_expired = True
    expires_at_str = None

    if quota_info.trial_expires_at:
        expires_at_str = quota_info.trial_expires_at.isoformat()
        now = datetime.now(timezone.utc)
        diff = quota_info.trial_expires_at - now
        days_remaining = max(0, diff.days + (1 if diff.seconds > 0 else 0))
        is_expired = now > quota_info.trial_expires_at
    elif plan_id != "free_trial":
        # Paid plan — not expired, not a trial
        is_expired = False
        days_remaining = 999  # Sentinel for "not applicable"

    return TrialStatusResponse(
        plan=plan_id,
        days_remaining=days_remaining,
        searches_used=quota_info.quota_used,
        searches_limit=caps.get("max_requests_per_month", 3),
        expires_at=expires_at_str,
        is_expired=is_expired,
    )


@router.put("/profile/context", response_model=PerfilContextoResponse)
async def save_profile_context(
    context: PerfilContexto,
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """Save business context from onboarding wizard (STORY-247 AC2).

    Stores context_data as JSONB in profiles table.
    """
    user_id = user["id"]

    try:
        context_dict = context.model_dump(exclude_none=True)
        db.table("profiles").update({
            "context_data": context_dict,
        }).eq("id", user_id).execute()

        log_user_action(logger, "profile_context_saved", user_id)
        return PerfilContextoResponse(
            context_data=context_dict,
            completed=True,
        )
    except Exception as e:
        logger.error(f"Failed to save profile context for {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar perfil de contexto")


@router.get("/profile/context", response_model=PerfilContextoResponse)
async def get_profile_context(
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """Get business context from profile (STORY-247 AC3)."""
    user_id = user["id"]

    try:
        result = db.table("profiles").select("context_data").eq("id", user_id).single().execute()
        context_data = (result.data or {}).get("context_data") or {}

        # Consider completed if at least porte_empresa is set
        completed = bool(context_data.get("porte_empresa"))

        return PerfilContextoResponse(
            context_data=context_data,
            completed=completed,
        )
    except Exception as e:
        logger.error(f"Failed to get profile context for {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar perfil de contexto")


@router.delete("/me", response_model=DeleteAccountResponse)
async def delete_account(user: dict = Depends(require_auth), db=Depends(get_db)):
    """Delete entire user account and all associated data (LGPD Art. 18 VI).

    Cascade order:
    1. Cancel active Stripe subscription (if any)
    2. Delete from: search_sessions, monthly_quota, user_subscriptions,
       user_oauth_tokens, messages, profiles
    3. Delete auth user via Supabase admin API
    4. Log anonymized audit entry
    """
    import stripe

    user_id = user["id"]
    hashed_id = hashlib.sha256(user_id.encode()).hexdigest()[:16]

    logger.info(f"Account deletion requested: {mask_user_id(user_id)}")

    # Step 1: Cancel active Stripe subscription if any
    try:
        subs_result = (
            db.table("user_subscriptions")
            .select("stripe_subscription_id, is_active")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )
        if subs_result.data:
            for sub in subs_result.data:
                stripe_sub_id = sub.get("stripe_subscription_id")
                if stripe_sub_id:
                    try:
                        stripe.Subscription.cancel(stripe_sub_id)
                        logger.info(f"Cancelled Stripe subscription {stripe_sub_id} for account deletion")
                    except stripe.InvalidRequestError as e:
                        # Subscription may already be cancelled
                        logger.warning(f"Stripe subscription cancel failed (may be already cancelled): {e}")
                    except Exception as e:
                        logger.error(f"Failed to cancel Stripe subscription {stripe_sub_id}: {e}")
    except Exception as e:
        logger.warning(f"Failed to check Stripe subscriptions during account deletion: {e}")

    # Step 2: Cascade delete from all tables
    tables_to_delete = [
        "search_sessions",
        "monthly_quota",
        "user_subscriptions",
        "user_oauth_tokens",
        "messages",
    ]

    for table in tables_to_delete:
        try:
            db.table(table).delete().eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"Failed to delete from {table} for user {mask_user_id(user_id)}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao excluir dados de {table}. Tente novamente.",
            )

    # Delete profile (id column, not user_id)
    try:
        db.table("profiles").delete().eq("id", user_id).execute()
    except Exception as e:
        logger.error(f"Failed to delete profile for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao excluir perfil. Tente novamente.",
        )

    # Step 3: Delete auth user
    try:
        db.auth.admin.delete_user(user_id)
    except Exception as e:
        logger.error(f"Failed to delete auth user {mask_user_id(user_id)}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao excluir conta de autenticação. Tente novamente.",
        )

    # Step 4: Anonymized audit log
    log_user_action(logger, "account_deleted", hashed_id)
    logger.info(f"Account deleted successfully: hashed_id={hashed_id}")

    return {"success": True, "message": "Conta excluída com sucesso."}


@router.get("/me/export")
async def export_user_data(user: dict = Depends(require_auth), db=Depends(get_db)):
    """Export all user data as JSON file (LGPD Art. 18 V — data portability).

    Returns a downloadable JSON file containing:
    - Profile information
    - Search history (sessions)
    - Subscription history
    - Messages
    """
    user_id = user["id"]
    now = datetime.now(timezone.utc)

    logger.info(f"Data export requested: {mask_user_id(user_id)}")

    export_data: dict = {
        "exported_at": now.isoformat(),
        "user_id": user_id,
    }

    # Profile
    try:
        profile_result = db.table("profiles").select("*").eq("id", user_id).execute()
        export_data["profile"] = profile_result.data[0] if profile_result.data else None
    except Exception as e:
        logger.warning(f"Failed to export profile: {e}")
        export_data["profile"] = None

    # Search sessions
    try:
        sessions_result = (
            db.table("search_sessions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        export_data["search_history"] = sessions_result.data or []
    except Exception as e:
        logger.warning(f"Failed to export search sessions: {e}")
        export_data["search_history"] = []

    # Subscriptions
    try:
        subs_result = (
            db.table("user_subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        export_data["subscriptions"] = subs_result.data or []
    except Exception as e:
        logger.warning(f"Failed to export subscriptions: {e}")
        export_data["subscriptions"] = []

    # Messages
    try:
        messages_result = (
            db.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        export_data["messages"] = messages_result.data or []
    except Exception as e:
        logger.warning(f"Failed to export messages: {e}")
        export_data["messages"] = []

    # Monthly quota
    try:
        quota_result = (
            db.table("monthly_quota")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        export_data["quota_history"] = quota_result.data or []
    except Exception as e:
        logger.warning(f"Failed to export quota history: {e}")
        export_data["quota_history"] = []

    log_user_action(logger, "data_exported", user_id)

    # Build filename: smartlic_dados_{user_id_prefix}_{date}.json
    user_id_prefix = user_id[:8]
    date_str = now.strftime("%Y-%m-%d")
    filename = f"smartlic_dados_{user_id_prefix}_{date_str}.json"

    content = json.dumps(export_data, ensure_ascii=False, indent=2, default=str)

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
