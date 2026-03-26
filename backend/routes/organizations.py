"""Organization routes for multi-user consultancy management.

STORY-322: Plano Consultoria — organization CRUD and member management.
STORY-331 AC3: Defensive guard — PGRST205 → HTTP 503.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import require_auth
from config import ORGANIZATIONS_ENABLED
from log_sanitizer import mask_user_id
from services.organization_service import (
    accept_invite,
    create_organization,
    get_org_dashboard,
    get_organization,
    get_user_org,
    invite_member,
    remove_member,
    update_org_logo,
)
from supabase_client import _is_schema_error

logger = logging.getLogger(__name__)

router = APIRouter(tags=["organizations"])


# ── Request body schemas ──────────────────────────────────────────────────────


class CreateOrgRequest(BaseModel):
    name: str


class InviteMemberRequest(BaseModel):
    email: str


class UpdateLogoRequest(BaseModel):
    logo_url: str


# ── Routes ────────────────────────────────────────────────────────────────────

# IMPORTANT: /organizations/me MUST be declared BEFORE /organizations/{org_id}
# to prevent FastAPI from treating "me" as an org_id path parameter.


# Helper: GET /v1/organizations/me — get current user's org
@router.get("/organizations/me")
async def get_my_org(
    user: dict = Depends(require_auth),
):
    """Get the organization the current user belongs to."""
    if not ORGANIZATIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    user_id = user["id"]
    logger.debug("get_my_org user=%s", mask_user_id(user_id))
    try:
        org = await get_user_org(user_id=user_id)
    except Exception as e:
        if _is_schema_error(e):
            raise HTTPException(status_code=503, detail="Feature not yet available")
        raise
    if not org:
        return {"organization": None}
    return {"organization": org}


# AC11: POST /v1/organizations — create org
@router.post("/organizations", status_code=201)
async def create_org(
    body: CreateOrgRequest,
    user: dict = Depends(require_auth),
):
    """Create organization (owner = current user)."""
    if not ORGANIZATIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    user_id = user["id"]
    logger.info("create_org user=%s name=%r", mask_user_id(user_id), body.name)
    try:
        org = await create_organization(owner_id=user_id, name=body.name)
        return org
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if _is_schema_error(e):
            raise HTTPException(status_code=503, detail="Feature not yet available")
        logger.error("Failed to create organization user=%s: %s", mask_user_id(user_id), e)
        raise HTTPException(status_code=500, detail="Erro ao criar organizacao")


# AC12: GET /v1/organizations/{org_id} — org details
@router.get("/organizations/{org_id}")
async def get_org(
    org_id: str,
    user: dict = Depends(require_auth),
):
    """Get organization details (must be a member)."""
    if not ORGANIZATIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    user_id = user["id"]
    logger.debug("get_org org_id=%s user=%s", org_id, mask_user_id(user_id))
    try:
        org = await get_organization(org_id=org_id, user_id=user_id)
    except Exception as e:
        if _is_schema_error(e):
            raise HTTPException(status_code=503, detail="Feature not yet available")
        raise
    if not org:
        raise HTTPException(status_code=404, detail="Organizacao nao encontrada")
    return org


# AC13: POST /v1/organizations/{org_id}/invite — invite member
@router.post("/organizations/{org_id}/invite")
async def invite_org_member(
    org_id: str,
    body: InviteMemberRequest,
    user: dict = Depends(require_auth),
):
    """Invite a member to the organization (owner/admin only)."""
    if not ORGANIZATIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    user_id = user["id"]
    logger.info(
        "invite_org_member org_id=%s inviter=%s email=%r",
        org_id,
        mask_user_id(user_id),
        body.email,
    )
    try:
        result = await invite_member(org_id=org_id, inviter_id=user_id, email=body.email)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if _is_schema_error(e):
            raise HTTPException(status_code=503, detail="Feature not yet available")
        logger.error(
            "Failed to invite member org_id=%s inviter=%s: %s",
            org_id,
            mask_user_id(user_id),
            e,
        )
        raise HTTPException(status_code=500, detail="Erro ao convidar membro")


# AC14: POST /v1/organizations/{org_id}/accept — accept invite
@router.post("/organizations/{org_id}/accept")
async def accept_org_invite(
    org_id: str,
    user: dict = Depends(require_auth),
):
    """Accept a pending organization invite."""
    if not ORGANIZATIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    user_id = user["id"]
    logger.info("accept_org_invite org_id=%s user=%s", org_id, mask_user_id(user_id))
    try:
        result = await accept_invite(org_id=org_id, user_id=user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if _is_schema_error(e):
            raise HTTPException(status_code=503, detail="Feature not yet available")
        logger.error(
            "Failed to accept invite org_id=%s user=%s: %s",
            org_id,
            mask_user_id(user_id),
            e,
        )
        raise HTTPException(status_code=500, detail="Erro ao aceitar convite")


# AC15: DELETE /v1/organizations/{org_id}/members/{target_user_id} — remove member
@router.delete("/organizations/{org_id}/members/{target_user_id}")
async def remove_org_member(
    org_id: str,
    target_user_id: str,
    user: dict = Depends(require_auth),
):
    """Remove a member from the organization (owner/admin only)."""
    if not ORGANIZATIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    user_id = user["id"]
    logger.info(
        "remove_org_member org_id=%s remover=%s target=%s",
        org_id,
        mask_user_id(user_id),
        mask_user_id(target_user_id),
    )
    try:
        result = await remove_member(
            org_id=org_id,
            remover_id=user_id,
            target_user_id=target_user_id,
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if _is_schema_error(e):
            raise HTTPException(status_code=503, detail="Feature not yet available")
        logger.error(
            "Failed to remove member org_id=%s remover=%s target=%s: %s",
            org_id,
            mask_user_id(user_id),
            mask_user_id(target_user_id),
            e,
        )
        raise HTTPException(status_code=500, detail="Erro ao remover membro")


# AC16: GET /v1/organizations/{org_id}/dashboard — consolidated stats
@router.get("/organizations/{org_id}/dashboard")
async def get_org_dashboard_endpoint(
    org_id: str,
    user: dict = Depends(require_auth),
):
    """Get consolidated dashboard for organization (owner/admin only)."""
    if not ORGANIZATIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    user_id = user["id"]
    logger.debug("get_org_dashboard org_id=%s user=%s", org_id, mask_user_id(user_id))
    try:
        result = await get_org_dashboard(org_id=org_id, user_id=user_id)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        if _is_schema_error(e):
            raise HTTPException(status_code=503, detail="Feature not yet available")
        logger.error(
            "Failed to get org dashboard org_id=%s user=%s: %s",
            org_id,
            mask_user_id(user_id),
            e,
        )
        raise HTTPException(status_code=500, detail="Erro ao obter dashboard da organizacao")


# AC17: PUT /v1/organizations/{org_id}/logo — update logo URL
@router.put("/organizations/{org_id}/logo")
async def upload_org_logo(
    org_id: str,
    body: UpdateLogoRequest,
    user: dict = Depends(require_auth),
):
    """Update organization logo URL (owner/admin only).

    Note: Actual file upload to Supabase Storage is handled client-side.
    This endpoint receives the public storage URL after the client-side upload.
    """
    if not ORGANIZATIONS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    user_id = user["id"]
    logger.info("upload_org_logo org_id=%s user=%s", org_id, mask_user_id(user_id))
    try:
        result = await update_org_logo(org_id=org_id, user_id=user_id, logo_url=body.logo_url)
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if _is_schema_error(e):
            raise HTTPException(status_code=503, detail="Feature not yet available")
        logger.error(
            "Failed to update org logo org_id=%s user=%s: %s",
            org_id,
            mask_user_id(user_id),
            e,
        )
        raise HTTPException(status_code=500, detail="Erro ao atualizar logo da organizacao")
