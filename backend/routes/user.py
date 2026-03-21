"""User profile, password management, account deletion, and data export routes.

Extracted from main.py as part of STORY-202 monolith decomposition.
STORY-213: Added DELETE /me (account deletion) and GET /me/export (data portability).
SYS-023: Profile context endpoints migrated to user-scoped Supabase client.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import Response
from auth import require_auth
from authorization import check_user_roles, get_admin_ids, get_master_quota_info
from supabase_client import sb_execute
from config import ENABLE_NEW_PRICING
from database import get_db, get_user_db
from schemas import (
    UserProfileResponse, SuccessResponse, DeleteAccountResponse,
    PerfilContexto, PerfilContextoResponse, ProfileCompletenessResponse, validate_password,
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
    plan_features: list[str] = []  # STORY-264 AC6
    # STORY-320 AC2: Trial phase for soft paywall
    trial_phase: str = "full_access"  # "full_access" | "limited_access" | "not_trial"
    trial_day: int = 0

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
    db=Depends(get_db),  # Admin client — uses db.auth.admin
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

    Uses admin client (get_db) because it needs db.auth.admin.get_user_by_id()
    to fetch the user's email from auth.users — an admin-only operation.
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
            quota_info = await asyncio.to_thread(check_quota, user["id"])
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

    # STORY-309: Determine subscription_status with dunning awareness
    dunning_phase = getattr(quota_info, "dunning_phase", "healthy")
    days_since_failure = getattr(quota_info, "days_since_failure", None)

    if dunning_phase in ("active_retries", "grace_period", "blocked"):
        subscription_status = "past_due"
    elif quota_info.trial_expires_at:
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
        dunning_phase=dunning_phase,
        days_since_failure=days_since_failure,
    )


@router.get("/trial-status", response_model=TrialStatusResponse)
async def get_trial_status(user: dict = Depends(require_auth), db=Depends(get_db)):
    """Get detailed trial status for conversion flow (GTM-010 AC3).

    Returns days remaining, usage stats, and expiration info.
    """
    from quota import check_quota, PLAN_CAPABILITIES

    user_id = user["id"]

    try:
        quota_info = await asyncio.to_thread(check_quota, user_id)
    except Exception as e:
        # CRIT-005 AC24: Surface error instead of swallowing with defaults
        logger.error(f"Failed to check quota for trial status: {e}")
        raise HTTPException(
            status_code=503,
            detail="Informação de trial temporariamente indisponível"
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

    # STORY-264 AC6: Build plan_features list from capabilities
    plan_features: list[str] = []
    if caps.get("max_requests_per_month", 0) >= 1000:
        plan_features.append("busca_ilimitada")
    if caps.get("allow_excel"):
        plan_features.append("excel_export")
    if caps.get("allow_pipeline"):
        plan_features.append("pipeline")
    if caps.get("max_summary_tokens", 0) >= 10000:
        plan_features.append("ia_resumo")

    # STORY-320 AC2: Get trial phase for soft paywall
    from quota import get_trial_phase
    trial_phase_info = get_trial_phase(user_id)

    return TrialStatusResponse(
        plan=plan_id,
        days_remaining=days_remaining,
        searches_used=quota_info.quota_used,
        searches_limit=caps.get("max_requests_per_month", 1000),  # STORY-264 AC5
        expires_at=expires_at_str,
        is_expired=is_expired,
        plan_features=plan_features,  # STORY-264 AC6
        trial_phase=trial_phase_info["phase"],
        trial_day=trial_phase_info["day"],
    )


# ============================================================================
# SYS-023: Profile context — uses user-scoped client (RLS-enforced)
# ============================================================================

@router.put("/profile/context", response_model=PerfilContextoResponse)
async def save_profile_context(
    context: PerfilContexto,
    user: dict = Depends(require_auth),
    user_db=Depends(get_user_db),  # SYS-023: User-scoped client (respects RLS)
):
    """Save business context from onboarding wizard (STORY-247 AC2).

    SYS-023: Uses user-scoped Supabase client. RLS policy on profiles
    ensures users can only update their own profile row.
    Stores context_data as JSONB in profiles table.
    """
    user_id = user["id"]

    try:
        context_dict = context.model_dump(exclude_none=True)
        await sb_execute(
            user_db.table("profiles").update({
                "context_data": context_dict,
            }).eq("id", user_id)
        )

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
    user_db=Depends(get_user_db),  # SYS-023: User-scoped client (respects RLS)
):
    """Get business context from profile (STORY-247 AC3).

    SYS-023: Uses user-scoped Supabase client. RLS policy on profiles
    ensures users can only read their own profile row.
    """
    user_id = user["id"]

    try:
        result = await sb_execute(
            user_db.table("profiles").select("context_data").eq("id", user_id).single()
        )
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


# ============================================================================
# STORY-260: Profile Completeness
# ============================================================================

# Fields tracked for completeness (priority order)
_PROFILE_FIELDS = [
    "ufs_atuacao",
    "porte_empresa",
    "experiencia_licitacoes",
    "faixa_valor_min",
    "capacidade_funcionarios",
    "faturamento_anual",
    "atestados",
]

# Priority order for next_question (highest impact first)
_QUESTION_PRIORITY = [
    "porte_empresa",
    "experiencia_licitacoes",
    "capacidade_funcionarios",
    "atestados",
]


@router.get("/profile/completeness", response_model=ProfileCompletenessResponse)
async def get_profile_completeness(
    user: dict = Depends(require_auth),
    user_db=Depends(get_user_db),  # SYS-023: User-scoped client (respects RLS)
):
    """STORY-260 AC3: Calculate profile completeness and suggest next question.

    SYS-023: Uses user-scoped Supabase client. RLS ensures user can only
    read their own profile.
    """
    user_id = user["id"]

    try:
        result = await sb_execute(
            user_db.table("profiles").select("context_data").eq("id", user_id).single()
        )
        context_data = (result.data or {}).get("context_data") or {}
    except Exception as e:
        logger.error(f"Failed to get profile for completeness: {e}")
        raise HTTPException(status_code=500, detail="Erro ao calcular completude do perfil")

    total_fields = len(_PROFILE_FIELDS)
    filled = 0
    missing = []

    for field_name in _PROFILE_FIELDS:
        val = context_data.get(field_name)
        if val is not None and val != "" and val != []:
            filled += 1
        else:
            missing.append(field_name)

    completeness_pct = round((filled / total_fields) * 100) if total_fields > 0 else 0
    is_complete = filled == total_fields

    # Determine next question based on priority order
    next_question = None
    if not is_complete:
        for q in _QUESTION_PRIORITY:
            if q in missing:
                next_question = q
                break
        # Fallback to first missing field
        if not next_question and missing:
            next_question = missing[0]

    return ProfileCompletenessResponse(
        completeness_pct=completeness_pct,
        total_fields=total_fields,
        filled_fields=filled,
        missing_fields=missing,
        next_question=next_question,
        is_complete=is_complete,
    )


# ============================================================================
# STORY-278: Alert Preferences — uses user-scoped client (SYS-023)
# ============================================================================

class AlertPreferencesRequest(BaseModel):
    frequency: str = "daily"  # daily, twice_weekly, weekly, off
    enabled: bool = True


class AlertPreferencesResponse(BaseModel):
    frequency: str
    enabled: bool
    last_digest_sent_at: str | None = None


@router.get("/profile/alert-preferences", response_model=AlertPreferencesResponse)
async def get_alert_preferences(
    user: dict = Depends(require_auth),
    user_db=Depends(get_user_db),  # SYS-023: User-scoped client (respects RLS)
):
    """Get user's alert preferences (STORY-278 AC6).

    SYS-023: Uses user-scoped Supabase client. RLS on alert_preferences
    ensures users can only read their own preferences.
    """
    user_id = user["id"]

    try:
        result = await sb_execute(
            user_db.table("alert_preferences").select(
                "frequency, enabled, last_digest_sent_at"
            ).eq("user_id", user_id).single()
        )

        if result.data:
            return AlertPreferencesResponse(
                frequency=result.data["frequency"],
                enabled=result.data["enabled"],
                last_digest_sent_at=result.data.get("last_digest_sent_at"),
            )
    except Exception:
        pass

    # Default if no record exists
    return AlertPreferencesResponse(
        frequency="daily",
        enabled=True,
        last_digest_sent_at=None,
    )


@router.put("/profile/alert-preferences", response_model=AlertPreferencesResponse)
async def update_alert_preferences(
    prefs: AlertPreferencesRequest,
    user: dict = Depends(require_auth),
    user_db=Depends(get_user_db),  # SYS-023: User-scoped client (respects RLS)
):
    """Update user's alert preferences (STORY-278 AC6).

    SYS-023: Uses user-scoped Supabase client. RLS on alert_preferences
    ensures users can only modify their own preferences.
    """
    user_id = user["id"]

    valid_frequencies = ("daily", "twice_weekly", "weekly", "off")
    if prefs.frequency not in valid_frequencies:
        raise HTTPException(
            status_code=400,
            detail=f"Frequencia invalida. Opcoes: {', '.join(valid_frequencies)}"
        )

    try:
        # Upsert: insert or update
        result = await sb_execute(
            user_db.table("alert_preferences").upsert({
                "user_id": user_id,
                "frequency": prefs.frequency,
                "enabled": prefs.enabled,
            }, on_conflict="user_id")
        )

        data = result.data[0] if result.data else {}

        log_user_action(logger, "alert_preferences_updated", user_id)
        return AlertPreferencesResponse(
            frequency=data.get("frequency", prefs.frequency),
            enabled=data.get("enabled", prefs.enabled),
            last_digest_sent_at=data.get("last_digest_sent_at"),
        )
    except Exception as e:
        logger.error(f"Failed to update alert preferences for {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao salvar preferencias de alerta")


# ============================================================================
# Account management — uses admin client (get_db) for auth.admin operations
# ============================================================================

@router.delete("/me", response_model=DeleteAccountResponse)
async def delete_account(user: dict = Depends(require_auth), db=Depends(get_db)):
    """Delete entire user account and all associated data (LGPD Art. 18 VI).

    Uses admin client (get_db) because it needs db.auth.admin.delete_user()
    and must delete across multiple tables regardless of RLS.

    Strategy:
    1. Cancel active Stripe subscription (external side-effect, must be first)
    2. Delete from profiles (CASCADE propagates to most child tables)
    3. Delete from remaining tables that reference auth.users directly
    4. Delete auth user via Supabase admin API
    5. Log anonymized audit entry

    If auth user deletion fails (step 4), we do NOT roll back the profile
    deletion — the user's data is already gone and a dangling auth entry
    is preferable to leaving personal data behind (LGPD Art. 18 VI).
    """
    import stripe

    user_id = user["id"]
    hashed_id = hashlib.sha256(user_id.encode()).hexdigest()[:16]

    logger.info(f"Account deletion requested: {mask_user_id(user_id)}")

    # Step 1: Cancel active Stripe subscription if any
    try:
        subs_result = await sb_execute(
            db.table("user_subscriptions")
            .select("stripe_subscription_id, is_active")
            .eq("user_id", user_id)
            .eq("is_active", True)
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

    # Step 2: Delete profile — CASCADE propagates to child tables:
    #   pipeline_items, classification_feedback, trial_email_log,
    #   alert_preferences, alerts, search_state_transitions,
    #   messages, search_sessions (via FK standardization migrations)
    try:
        await sb_execute(db.table("profiles").delete().eq("id", user_id))
    except Exception as e:
        logger.error(f"Failed to delete profile for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao excluir perfil. Tente novamente.",
        )

    # Step 3: Delete from tables that reference auth.users directly
    # (not covered by profiles CASCADE). Each is best-effort — if the
    # table doesn't exist or has no rows, that's fine.
    auth_user_tables = [
        "monthly_quota",
        "user_subscriptions",
        "user_oauth_tokens",
        "google_sheets_exports",
        "search_results_cache",
        "mfa_recovery_codes",
        "mfa_trusted_devices",
        "search_results_store",
    ]

    failed_tables: list[str] = []
    for table in auth_user_tables:
        try:
            await sb_execute(db.table(table).delete().eq("user_id", user_id))
        except Exception as e:
            # Log but don't abort — auth user deletion CASCADE will clean up
            logger.warning(f"Failed to delete from {table} for user {mask_user_id(user_id)}: {e}")
            failed_tables.append(table)

    if failed_tables:
        logger.warning(
            f"Account deletion: {len(failed_tables)} tables had errors "
            f"(will rely on auth CASCADE): {failed_tables}"
        )

    # Step 4: Delete auth user (cascades to any remaining FK references)
    try:
        db.auth.admin.delete_user(user_id)
    except Exception as e:
        logger.error(f"Failed to delete auth user {mask_user_id(user_id)}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao excluir conta de autenticação. Tente novamente.",
        )

    # Step 5: Anonymized audit log
    log_user_action(logger, "account_deleted", hashed_id)
    logger.info(f"Account deleted successfully: hashed_id={hashed_id}")

    return {"success": True, "message": "Conta excluída com sucesso."}


@router.get("/me/export")
async def export_user_data(user: dict = Depends(require_auth), db=Depends(get_db)):
    """Export all user data as JSON file (LGPD Art. 18 V — data portability).

    Uses admin client (get_db) because it queries across multiple tables
    and needs unrestricted access to gather all user data for export.

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
        profile_result = await sb_execute(
            db.table("profiles").select("*").eq("id", user_id)
        )
        export_data["profile"] = profile_result.data[0] if profile_result.data else None
    except Exception as e:
        logger.warning(f"Failed to export profile: {e}")
        export_data["profile"] = None

    # Search sessions
    try:
        sessions_result = await sb_execute(
            db.table("search_sessions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )
        export_data["search_history"] = sessions_result.data or []
    except Exception as e:
        logger.warning(f"Failed to export search sessions: {e}")
        export_data["search_history"] = []

    # Subscriptions
    try:
        subs_result = await sb_execute(
            db.table("user_subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )
        export_data["subscriptions"] = subs_result.data or []
    except Exception as e:
        logger.warning(f"Failed to export subscriptions: {e}")
        export_data["subscriptions"] = []

    # Messages
    try:
        messages_result = await sb_execute(
            db.table("messages")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )
        export_data["messages"] = messages_result.data or []
    except Exception as e:
        logger.warning(f"Failed to export messages: {e}")
        export_data["messages"] = []

    # Monthly quota
    try:
        quota_result = await sb_execute(
            db.table("monthly_quota")
            .select("*")
            .eq("user_id", user_id)
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
