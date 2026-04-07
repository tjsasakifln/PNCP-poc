"""Trial extension routes — Zero-Churn P2 §8.2."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trial", tags=["trial"])


class ExtendRequest(BaseModel):
    condition: str = Field(
        ...,
        description="Extension condition: profile_complete, feedback_given, or referral_signup",
    )


class ExtendResponse(BaseModel):
    days_added: int
    total_extended: int
    new_expires_at: str | None = None


class ExtensionItem(BaseModel):
    condition: str
    label: str
    days: int
    claimed: bool
    eligible: bool


class ExtensionsStatusResponse(BaseModel):
    enabled: bool
    extensions: list[ExtensionItem]
    total_extended: int
    max_extension: int
    remaining: int = 0


@router.post("/extend", response_model=ExtendResponse)
async def extend_trial_endpoint(
    body: ExtendRequest,
    user: dict = Depends(require_auth),
):
    """Extend trial by completing a condition."""
    from services.trial_extension import extend_trial

    try:
        result = await extend_trial(user["id"], body.condition)
        return ExtendResponse(
            days_added=result.get("days_added", 0),
            total_extended=result.get("total_extended", 0),
            new_expires_at=str(result.get("new_expires_at")) if result.get("new_expires_at") else None,
        )
    except ValueError as e:
        error_msg = str(e)
        if "already" in error_msg.lower() or "max_extension" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error("Trial extension failed: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao estender trial")


@router.get("/extensions", response_model=ExtensionsStatusResponse)
async def get_extensions_status(
    user: dict = Depends(require_auth),
):
    """Get trial extension checklist status."""
    from services.trial_extension import get_extension_status

    status = await get_extension_status(user["id"])
    return ExtensionsStatusResponse(**status)
