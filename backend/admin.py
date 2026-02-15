"""Admin endpoints for user management (system admin only).

Security hardened in Issue #203:
- All user IDs validated as UUID v4 format
- Plan IDs validated against allowed pattern
- Admin IDs from env validated before use

Security hardened in Issue #205:
- Search queries sanitized to prevent SQL/PostgREST injection
- Dangerous characters removed (quotes, semicolons, commas, etc.)
- SQL comment markers (--) removed
- PostgREST operators (.eq., .ilike., etc.) stripped
- Input length limited to prevent DoS

Security hardened in Issue #168:
- PII sanitized in logs (emails masked)
- User IDs partially masked in logs
- No sensitive data in plain text logs
"""

import logging
import os
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Request, Path
from pydantic import BaseModel, Field
from auth import require_auth
from schemas import (
    validate_uuid, validate_plan_id, validate_password,
    AdminUsersListResponse, AdminCreateUserResponse, AdminDeleteUserResponse,
    AdminUpdateUserResponse, AdminResetPasswordResponse, AdminAssignPlanResponse,
    AdminUpdateCreditsResponse,
)
from log_sanitizer import sanitize_dict, log_admin_action
from filter_stats import filter_stats_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


def _sanitize_search_input(search: str) -> str:
    """
    Sanitize search input to prevent SQL injection attacks.

    Removes or escapes dangerous characters that could manipulate PostgREST queries.
    Only allows alphanumeric characters, spaces, hyphens, underscores, dots, and @ symbols.

    Args:
        search: Raw user input from query parameter

    Returns:
        Sanitized string safe for use in Supabase filter queries
    """
    if not search:
        return ""

    # Remove any characters that could be used for SQL injection or PostgREST manipulation
    # PostgREST uses special characters like: . , ( ) for query syntax
    # We only allow safe characters for search terms
    sanitized = re.sub(r'[^\w\s\-_.@]', '', search, flags=re.UNICODE)

    # SECURITY: Remove SQL comment patterns (Issue #205)
    # Double-dash (--) is used for SQL line comments and must be removed
    sanitized = re.sub(r'--+', '', sanitized)

    # Limit length to prevent DoS
    sanitized = sanitized[:100]

    # Remove any potential PostgREST operators that snuck through
    # These patterns could manipulate the query structure
    dangerous_patterns = [
        r'\.eq\.',
        r'\.neq\.',
        r'\.gt\.',
        r'\.gte\.',
        r'\.lt\.',
        r'\.lte\.',
        r'\.like\.',
        r'\.ilike\.',
        r'\.is\.',
        r'\.in\.',
        r'\.cs\.',
        r'\.cd\.',
        r'\.sl\.',
        r'\.sr\.',
        r'\.nxl\.',
        r'\.nxr\.',
        r'\.adj\.',
        r'\.ov\.',
        r'\.fts\.',
        r'\.plfts\.',
        r'\.phfts\.',
        r'\.wfts\.',
        r'\.or\.',
        r'\.and\.',
        r'\.not\.',
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

    return sanitized.strip()

def _get_admin_ids() -> set[str]:
    """
    Get validated admin user IDs from environment variable.

    Admin IDs are stored in ADMIN_USER_IDS env var as comma-separated UUIDs.
    Each ID is validated against UUID v4 format for security.

    Returns:
        set[str]: Set of validated admin UUIDs (lowercase normalized)

    Note:
        Invalid UUIDs are logged and skipped (fail-safe behavior).
    """
    raw = os.getenv("ADMIN_USER_IDS", "")
    valid_ids = set()

    for uid in raw.split(","):
        uid = uid.strip()
        if not uid:
            continue

        try:
            # Validate each admin ID as UUID v4
            validated = validate_uuid(uid, "admin_id")
            valid_ids.add(validated)
        except ValueError as e:
            # Log invalid IDs but don't fail (security: don't expose which IDs are invalid)
            logger.warning(f"Invalid admin ID in ADMIN_USER_IDS skipped: {e}")

    return valid_ids


def _validate_user_id_param(user_id: str) -> str:
    """
    Validate user_id path parameter as UUID v4.

    Args:
        user_id: The user ID from path parameter

    Returns:
        str: Validated and normalized user ID

    Raises:
        HTTPException: 400 if user_id is not valid UUID v4
    """
    try:
        return validate_uuid(user_id, "user_id")
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"ID de usuario invalido: {e}"
        )


def _validate_plan_id_param(plan_id: str) -> str:
    """
    Validate plan_id parameter.

    Args:
        plan_id: The plan ID to validate

    Returns:
        str: Validated and normalized plan ID

    Raises:
        HTTPException: 400 if plan_id format is invalid
    """
    try:
        return validate_plan_id(plan_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"ID de plano invalido: {e}"
        )


def _is_admin_from_supabase(user_id: str) -> bool:
    """
    Check if user has is_admin = true in Supabase profiles.

    Args:
        user_id: The user's UUID

    Returns:
        True if profiles.is_admin = true, False otherwise
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        try:
            profile = (
                sb.table("profiles")
                .select("is_admin")
                .eq("id", user_id)
                .single()
                .execute()
            )

            if profile.data and profile.data.get("is_admin"):
                return True
        except Exception:
            # is_admin column might not exist yet - that's OK
            # Fall back to ADMIN_USER_IDS env var only
            pass

        return False
    except Exception as e:
        logger.warning(f"Failed to check admin status from Supabase: {e}")
        return False


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    """
    Require system admin role.

    Checks multiple sources:
    1. ADMIN_USER_IDS environment variable (fast path)
    2. Supabase profiles.is_admin = true

    User ID is normalized to lowercase for comparison.
    """
    user_id = str(user.get("id", "")).strip()

    # Fast path: check env var first (no DB call)
    admin_ids = _get_admin_ids()
    if user_id.lower() in admin_ids:
        return user

    # Check Supabase for is_admin flag
    if _is_admin_from_supabase(user_id):
        return user

    raise HTTPException(status_code=403, detail="Acesso restrito a administradores")


class CreateUserRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password (min 8 chars, 1 uppercase, 1 digit)")
    full_name: Optional[str] = None
    plan_id: Optional[str] = Field(default="free_trial", description="Initial plan")
    company: Optional[str] = None


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    company: Optional[str] = None
    plan_id: Optional[str] = None


@router.get("/users", response_model=AdminUsersListResponse)
async def list_users(
    admin: dict = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None, max_length=100),
):
    """List all users with profiles and subscription info."""
    from supabase_client import get_supabase
    from quota import PLAN_CAPABILITIES, get_monthly_quota_used
    sb = get_supabase()

    query = sb.table("profiles").select("*, user_subscriptions(id, plan_id, credits_remaining, expires_at, is_active)", count="exact")

    if search:
        # SECURITY: Sanitize search input to prevent SQL injection / PostgREST manipulation
        sanitized_search = _sanitize_search_input(search)
        if sanitized_search:
            # Use parameterized-style filter with sanitized input
            query = query.or_(f"email.ilike.%{sanitized_search}%,full_name.ilike.%{sanitized_search}%,company.ilike.%{sanitized_search}%")

    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    # Enrich user data with computed credits for users without active subscriptions
    users = result.data or []
    for user in users:
        subscriptions = user.get("user_subscriptions", [])
        active_sub = next((s for s in subscriptions if s.get("is_active")), None)

        if active_sub is None:
            # User has no active subscription - compute credits from plan capabilities
            plan_id = user.get("plan_type", "free_trial")
            caps = PLAN_CAPABILITIES.get(plan_id, PLAN_CAPABILITIES.get("free_trial", {}))
            max_requests = caps.get("max_requests_per_month", 3)

            # Get monthly quota used to compute remaining credits
            user_id = user.get("id")
            if user_id:
                quota_used = get_monthly_quota_used(user_id)
                credits_remaining = max(0, max_requests - quota_used)
            else:
                credits_remaining = max_requests

            # Create a synthetic subscription entry for the frontend
            user["user_subscriptions"] = [{
                "id": None,
                "plan_id": plan_id,
                "credits_remaining": credits_remaining,
                "expires_at": None,
                "is_active": True,
            }]
        else:
            # User has active subscription - if credits_remaining is None, it means unlimited
            # Keep as-is (frontend handles None as infinity correctly)
            pass

    return {
        "users": users,
        "total": result.count or 0,
        "limit": limit,
        "offset": offset,
    }


@router.post("/users", response_model=AdminCreateUserResponse)
async def create_user(
    req: CreateUserRequest,
    admin: dict = Depends(require_admin),
):
    """Create a new user with optional plan assignment."""
    # STORY-226 AC17: Validate password policy
    is_valid, error_msg = validate_password(req.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    from supabase_client import get_supabase
    sb = get_supabase()

    # Create auth user via admin API
    try:
        user_response = sb.auth.admin.create_user({
            "email": req.email,
            "password": req.password,
            "email_confirm": True,  # Skip email verification for admin-created users
            "user_metadata": {"full_name": req.full_name},
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao criar usuario: {e}")

    user_id = str(user_response.user.id)

    # Update profile with extra fields
    if req.company or req.plan_id != "free_trial":
        updates = {}
        if req.company:
            updates["company"] = req.company
        if req.plan_id:
            updates["plan_type"] = req.plan_id
        sb.table("profiles").update(updates).eq("id", user_id).execute()

    # Assign plan if not free_trial
    if req.plan_id and req.plan_id != "free_trial":
        _assign_plan(sb, user_id, req.plan_id)

    # SECURITY: Sanitize PII before logging (Issue #168)
    log_admin_action(
        logger,
        admin_id=admin['id'],
        action="create-user",
        target_user_id=user_id,
        details={"plan": req.plan_id},
    )

    return {"user_id": user_id, "email": req.email, "plan_id": req.plan_id}


@router.delete("/users/{user_id}", response_model=AdminDeleteUserResponse)
async def delete_user(
    user_id: str = Path(..., description="User UUID to delete"),
    admin: dict = Depends(require_admin),
):
    """Delete a user and all their data."""
    # SECURITY: Validate user_id as UUID v4 (Issue #203)
    user_id = _validate_user_id_param(user_id)

    from supabase_client import get_supabase
    sb = get_supabase()

    # Check user exists
    profile = sb.table("profiles").select("email").eq("id", user_id).single().execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    # Delete from auth (cascades to profiles, sessions, subscriptions via FK)
    try:
        sb.auth.admin.delete_user(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir usuario: {e}")

    # SECURITY: Sanitize PII before logging (Issue #168)
    log_admin_action(
        logger,
        admin_id=admin['id'],
        action="delete-user",
        target_user_id=user_id,
    )

    return {"deleted": True, "user_id": user_id}


@router.put("/users/{user_id}", response_model=AdminUpdateUserResponse)
async def update_user(
    req: UpdateUserRequest,
    user_id: str = Path(..., description="User UUID to update"),
    admin: dict = Depends(require_admin),
):
    """Update user profile or plan."""
    # SECURITY: Validate user_id as UUID v4 (Issue #203)
    user_id = _validate_user_id_param(user_id)

    # Validate plan_id if provided
    validated_plan_id = None
    if req.plan_id is not None:
        validated_plan_id = _validate_plan_id_param(req.plan_id)

    from supabase_client import get_supabase
    sb = get_supabase()

    updates = {}
    if req.full_name is not None:
        updates["full_name"] = req.full_name
    if req.company is not None:
        updates["company"] = req.company
    if validated_plan_id is not None:
        updates["plan_type"] = validated_plan_id

    if updates:
        sb.table("profiles").update(updates).eq("id", user_id).execute()

    if validated_plan_id:
        _assign_plan(sb, user_id, validated_plan_id)

    # SECURITY: Sanitize update data before logging (Issue #168)
    log_admin_action(
        logger,
        admin_id=admin['id'],
        action="update-user",
        target_user_id=user_id,
        details=sanitize_dict(updates),
    )
    return {"updated": True, "user_id": user_id}


@router.post("/users/{user_id}/reset-password", response_model=AdminResetPasswordResponse)
async def reset_user_password(
    request: Request,
    user_id: str = Path(..., description="User UUID to reset password for"),
    admin: dict = Depends(require_admin),
):
    """Reset a user's password (admin only)."""
    # SECURITY: Validate user_id as UUID v4 (Issue #203)
    user_id = _validate_user_id_param(user_id)

    body = await request.json()
    new_password = body.get("new_password", "")

    # STORY-226 AC17: Validate password policy
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    from supabase_client import get_supabase
    sb = get_supabase()
    try:
        sb.auth.admin.update_user_by_id(user_id, {"password": new_password})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao resetar senha: {e}")

    # SECURITY: Never log password content (Issue #168)
    log_admin_action(
        logger,
        admin_id=admin['id'],
        action="reset-password",
        target_user_id=user_id,
    )
    return {"success": True, "user_id": user_id}


@router.post("/users/{user_id}/assign-plan", response_model=AdminAssignPlanResponse)
async def assign_plan(
    user_id: str = Path(..., description="User UUID to assign plan to"),
    plan_id: str = Query(..., description="Plan ID to assign"),
    admin: dict = Depends(require_admin),
):
    """Manually assign a plan to a user (bypasses payment)."""
    # SECURITY: Validate user_id and plan_id (Issue #203)
    user_id = _validate_user_id_param(user_id)
    plan_id = _validate_plan_id_param(plan_id)

    from supabase_client import get_supabase
    sb = get_supabase()

    try:
        _assign_plan(sb, user_id, plan_id)

        sb.table("profiles").update({"plan_type": plan_id}).eq("id", user_id).execute()
    except HTTPException:
        # Re-raise HTTPException as-is (e.g., 404 for plan not found)
        raise
    except Exception as e:
        error_msg = str(e)
        # Handle database constraint violations (e.g., invalid plan_type)
        if "check constraint" in error_msg.lower() or "23514" in error_msg:
            logger.warning(f"Invalid plan_id '{plan_id}' for user {user_id}: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"Plano '{plan_id}' nao e valido. Planos disponiveis: free_trial, consultor_agil, maquina, sala_guerra"
            )
        # Handle other database errors
        logger.error(f"Failed to assign plan {plan_id} to user {user_id}: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atribuir plano: {error_msg}"
        )

    # SECURITY: Sanitize IDs before logging (Issue #168)
    log_admin_action(
        logger,
        admin_id=admin['id'],
        action="assign-plan",
        target_user_id=user_id,
        details={"plan_id": plan_id},
    )
    return {"assigned": True, "user_id": user_id, "plan_id": plan_id}


class UpdateCreditsRequest(BaseModel):
    """Request body for manual credit adjustment."""
    credits: int = Field(..., ge=0, description="New credit value (must be >= 0)")


@router.put("/users/{user_id}/credits", response_model=AdminUpdateCreditsResponse)
async def update_user_credits(
    req: UpdateCreditsRequest,
    user_id: str = Path(..., description="User UUID to update credits for"),
    admin: dict = Depends(require_admin),
):
    """
    Manually adjust a user's credits (admin only).

    Sets the credits_remaining value directly on the user's active subscription.
    If no active subscription exists, creates one based on user's current plan.

    Args:
        user_id: UUID of the user
        req.credits: New credit value (must be >= 0)

    Returns:
        Updated user info with new credit value
    """
    # SECURITY: Validate user_id as UUID v4 (Issue #203)
    user_id = _validate_user_id_param(user_id)

    from supabase_client import get_supabase
    sb = get_supabase()

    # Verify user exists
    profile = sb.table("profiles").select("email, plan_type").eq("id", user_id).single().execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    # Get active subscription
    sub_result = (
        sb.table("user_subscriptions")
        .select("id, plan_id, credits_remaining")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .execute()
    )

    if sub_result.data and len(sub_result.data) > 0:
        # Update existing subscription
        subscription = sub_result.data[0]
        old_credits = subscription.get("credits_remaining")

        sb.table("user_subscriptions").update({
            "credits_remaining": req.credits
        }).eq("id", subscription["id"]).execute()

        log_admin_action(
            logger,
            admin_id=admin['id'],
            action="update-credits",
            target_user_id=user_id,
            details={"old_credits": old_credits, "new_credits": req.credits},
        )

        return {
            "success": True,
            "user_id": user_id,
            "credits": req.credits,
            "previous_credits": old_credits,
        }
    else:
        # No active subscription - create one based on user's plan_type
        plan_id = profile.data.get("plan_type", "free_trial")

        # Get plan details for expiration
        plan = sb.table("plans").select("*").eq("id", plan_id).execute()
        plan_data = plan.data[0] if plan.data else None

        from datetime import datetime, timezone, timedelta

        expires_at = None
        if plan_data and plan_data.get("duration_days"):
            expires_at = (datetime.now(timezone.utc) + timedelta(days=plan_data["duration_days"])).isoformat()

        # Create new subscription with specified credits
        sb.table("user_subscriptions").insert({
            "user_id": user_id,
            "plan_id": plan_id,
            "credits_remaining": req.credits,
            "expires_at": expires_at,
            "is_active": True,
        }).execute()

        log_admin_action(
            logger,
            admin_id=admin['id'],
            action="create-subscription-with-credits",
            target_user_id=user_id,
            details={"plan_id": plan_id, "credits": req.credits},
        )

        return {
            "success": True,
            "user_id": user_id,
            "credits": req.credits,
            "previous_credits": None,
            "subscription_created": True,
        }


@router.post("/feature-flags/reload")
async def reload_feature_flags_endpoint(
    admin: dict = Depends(require_admin),
):
    """Reload all feature flags from environment variables (admin only).

    STORY-226 AC16: Clears the feature flag cache, forcing re-read from
    environment on next access. Returns current values after reload.
    """
    from config import reload_feature_flags

    current_values = reload_feature_flags()

    log_admin_action(
        logger,
        admin_id=admin['id'],
        action="reload-feature-flags",
        target_user_id=admin['id'],
        details={"flags": current_values},
    )

    return {"success": True, "flags": current_values}


@router.get("/admin/filter-stats")
async def get_filter_stats(
    request: Request,
    days: int = Query(default=7, ge=1, le=90, description="Number of days to look back"),
    admin: dict = Depends(require_admin),
):
    """
    STORY-248 AC10: Filter rejection statistics.

    Returns counts of each rejection reason code for the specified period.
    Admin-only endpoint.

    Reason codes:
    - keyword_miss: No sector keyword found in procurement description
    - exclusion_hit: Exclusion keyword matched (false-positive prevention)
    - llm_reject: LLM arbiter rejected the contract
    - density_low: Term density below minimum threshold
    - value_exceed: Contract value exceeds sector maximum
    - uf_mismatch: State (UF) not in selected set
    - status_mismatch: Procurement status does not match filter
    """
    stats = filter_stats_tracker.get_stats(days=days)
    return {
        "status": "ok",
        "data": stats,
    }


def _assign_plan(sb, user_id: str, plan_id: str):
    """Internal: assign plan creating subscription record."""
    from datetime import datetime, timezone, timedelta

    plan = sb.table("plans").select("*").eq("id", plan_id).single().execute()
    if not plan.data:
        raise HTTPException(status_code=404, detail=f"Plano '{plan_id}' nao encontrado")

    p = plan.data
    expires_at = None
    if p["duration_days"]:
        expires_at = (datetime.now(timezone.utc) + timedelta(days=p["duration_days"])).isoformat()

    # Deactivate previous
    sb.table("user_subscriptions").update({"is_active": False}).eq("user_id", user_id).eq("is_active", True).execute()

    # Create new
    sb.table("user_subscriptions").insert({
        "user_id": user_id,
        "plan_id": plan_id,
        "credits_remaining": p["max_searches"],
        "expires_at": expires_at,
        "is_active": True,
    }).execute()
