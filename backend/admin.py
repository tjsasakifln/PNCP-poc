"""Admin endpoints for user management (system admin only)."""

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Admin user IDs — set via ADMIN_USER_IDS env var (comma-separated UUIDs)
def _get_admin_ids() -> set[str]:
    raw = os.getenv("ADMIN_USER_IDS", "")
    return {uid.strip() for uid in raw.split(",") if uid.strip()}


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    """Require system admin role."""
    admin_ids = _get_admin_ids()
    if user["id"] not in admin_ids:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return user


class CreateUserRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")
    full_name: Optional[str] = None
    plan_id: Optional[str] = Field(default="free", description="Initial plan")
    company: Optional[str] = None


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    company: Optional[str] = None
    plan_id: Optional[str] = None


@router.get("/users")
async def list_users(
    admin: dict = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
):
    """List all users with profiles and subscription info."""
    from supabase_client import get_supabase
    sb = get_supabase()

    query = sb.table("profiles").select("*, user_subscriptions(id, plan_id, credits_remaining, expires_at, is_active)", count="exact")

    if search:
        query = query.or_(f"email.ilike.%{search}%,full_name.ilike.%{search}%,company.ilike.%{search}%")

    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    return {
        "users": result.data,
        "total": result.count or 0,
        "limit": limit,
        "offset": offset,
    }


@router.post("/users")
async def create_user(
    req: CreateUserRequest,
    admin: dict = Depends(require_admin),
):
    """Create a new user with optional plan assignment."""
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
    if req.company or req.plan_id != "free":
        updates = {}
        if req.company:
            updates["company"] = req.company
        if req.plan_id:
            updates["plan_type"] = req.plan_id
        sb.table("profiles").update(updates).eq("id", user_id).execute()

    # Assign plan if not free
    if req.plan_id and req.plan_id != "free":
        _assign_plan(sb, user_id, req.plan_id)

    logger.info(f"Admin {admin['id']} created user {user_id} ({req.email}) with plan {req.plan_id}")

    return {"user_id": user_id, "email": req.email, "plan_id": req.plan_id}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(require_admin),
):
    """Delete a user and all their data."""
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

    logger.info(f"Admin {admin['id']} deleted user {user_id} ({profile.data['email']})")

    return {"deleted": True, "user_id": user_id}


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    req: UpdateUserRequest,
    admin: dict = Depends(require_admin),
):
    """Update user profile or plan."""
    from supabase_client import get_supabase
    sb = get_supabase()

    updates = {}
    if req.full_name is not None:
        updates["full_name"] = req.full_name
    if req.company is not None:
        updates["company"] = req.company
    if req.plan_id is not None:
        updates["plan_type"] = req.plan_id

    if updates:
        sb.table("profiles").update(updates).eq("id", user_id).execute()

    if req.plan_id:
        _assign_plan(sb, user_id, req.plan_id)

    logger.info(f"Admin {admin['id']} updated user {user_id}: {updates}")
    return {"updated": True, "user_id": user_id}


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    request: Request,
    admin: dict = Depends(require_admin),
):
    """Reset a user's password (admin only)."""
    body = await request.json()
    new_password = body.get("new_password", "")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter no minimo 6 caracteres")

    from supabase_client import get_supabase
    sb = get_supabase()
    try:
        sb.auth.admin.update_user_by_id(user_id, {"password": new_password})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao resetar senha: {e}")

    logger.info(f"Admin {admin['id']} reset password for user {user_id}")
    return {"success": True, "user_id": user_id}


@router.post("/users/{user_id}/assign-plan")
async def assign_plan(
    user_id: str,
    plan_id: str = Query(...),
    admin: dict = Depends(require_admin),
):
    """Manually assign a plan to a user (bypasses payment)."""
    from supabase_client import get_supabase
    sb = get_supabase()

    _assign_plan(sb, user_id, plan_id)

    sb.table("profiles").update({"plan_type": plan_id}).eq("id", user_id).execute()

    logger.info(f"Admin {admin['id']} assigned plan {plan_id} to user {user_id}")
    return {"assigned": True, "user_id": user_id, "plan_id": plan_id}


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
