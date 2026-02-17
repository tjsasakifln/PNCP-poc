"""
Email confirmation recovery endpoints.

GTM-FIX-009: Fix email confirmation dead end.

Endpoints:
- POST /auth/resend-confirmation — Resend signup confirmation email (60s rate limit)
- GET  /auth/status              — Check if email has been confirmed
"""

import logging
import time
from typing import Dict, Tuple

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth-email"])

# In-memory rate-limit store: email -> last_resend_timestamp
_resend_timestamps: Dict[str, float] = {}
RESEND_COOLDOWN = 60  # seconds


class ResendRequest(BaseModel):
    email: EmailStr


class ResendResponse(BaseModel):
    success: bool
    message: str


class AuthStatusResponse(BaseModel):
    confirmed: bool
    user_id: str | None = None


@router.post("/resend-confirmation", response_model=ResendResponse)
async def resend_confirmation(request: ResendRequest):
    """Resend signup confirmation email with 60s rate limiting.

    AC4: Calls Supabase auth.resend({ type: 'signup', email }).
    AC1-AC6: Frontend uses this with countdown timer.
    """
    email_lower = request.email.lower().strip()
    now = time.time()

    # Check rate limit
    last_sent = _resend_timestamps.get(email_lower)
    if last_sent and (now - last_sent) < RESEND_COOLDOWN:
        remaining = int(RESEND_COOLDOWN - (now - last_sent))
        raise HTTPException(
            status_code=429,
            detail=f"Aguarde {remaining}s antes de reenviar."
        )

    try:
        from supabase_client import get_supabase
        supabase = get_supabase()
        supabase.auth.resend({"type": "signup", "email": email_lower})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resend confirmation: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Erro ao reenviar email.")

    _resend_timestamps[email_lower] = now
    logger.info(f"Confirmation email resent for {email_lower[:4]}***")

    return ResendResponse(
        success=True,
        message="Email reenviado! Verifique sua caixa de entrada."
    )


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(email: str = Query(..., description="Email to check")):
    """Check if a signup email has been confirmed.

    AC8: Returns { confirmed: boolean, user_id?: string }.
    AC7/AC9: Frontend polls this every 5s for auto-redirect.
    """
    email_lower = email.lower().strip()

    try:
        from supabase_client import get_supabase
        supabase = get_supabase()

        # Use admin API to list users filtered by email
        response = supabase.auth.admin.list_users()

        for user in response:
            user_email = getattr(user, "email", None)
            if user_email and user_email.lower() == email_lower:
                confirmed_at = getattr(user, "email_confirmed_at", None)
                if confirmed_at:
                    return AuthStatusResponse(
                        confirmed=True,
                        user_id=user.id
                    )
                return AuthStatusResponse(confirmed=False)

        return AuthStatusResponse(confirmed=False)

    except Exception as e:
        logger.error(f"Failed to check auth status: {type(e).__name__}")
        return AuthStatusResponse(confirmed=False)
