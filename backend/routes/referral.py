"""Referral program routes — 1 month free per conversion.

Endpoints:
- GET  /v1/referral/code   — Returns the authenticated user's referral code
                             (creates one lazily if missing).
- GET  /v1/referral/stats  — Returns aggregate stats for the authenticated user.
- POST /v1/referral/redeem — Called during signup to register that a new user
                             is being referred via a code.
"""

import logging
import secrets
import string
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/referral", tags=["referral"])

_CODE_ALPHABET = string.ascii_uppercase + string.digits
_CODE_LENGTH = 8
_MAX_CODE_GENERATION_ATTEMPTS = 6


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ReferralCodeResponse(BaseModel):
    code: str = Field(..., description="8-char alphanumeric referral code")
    share_url: str = Field(..., description="Full signup URL with ?ref= param")


class ReferralStatsResponse(BaseModel):
    code: str
    total_signups: int = 0
    total_converted: int = 0
    credits_earned_months: int = 0


class ReferralRedeemRequest(BaseModel):
    code: str = Field(..., min_length=8, max_length=8)
    referred_user_id: str = Field(..., min_length=1)


class ReferralRedeemResponse(BaseModel):
    status: str
    code: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


def _get_or_create_code_for_user(sb, user_id: str) -> str:
    """Return existing referral code for *user_id*, or create a new one.

    Idempotent: if the user already has a row we return it; otherwise we
    insert a new row, retrying on unique-collision of the generated code.
    """
    existing = (
        sb.table("referrals")
        .select("code")
        .eq("referrer_user_id", user_id)
        .is_("referred_user_id", "null")
        .eq("status", "pending")
        .limit(1)
        .execute()
    )
    if getattr(existing, "data", None):
        return existing.data[0]["code"]

    # Fallback: any row owned by the user (if only non-pending rows exist,
    # keep using the same code for display consistency).
    any_existing = (
        sb.table("referrals")
        .select("code")
        .eq("referrer_user_id", user_id)
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    if getattr(any_existing, "data", None):
        return any_existing.data[0]["code"]

    last_error: Optional[Exception] = None
    for _ in range(_MAX_CODE_GENERATION_ATTEMPTS):
        code = _generate_code()
        try:
            sb.table("referrals").insert(
                {
                    "referrer_user_id": user_id,
                    "code": code,
                    "status": "pending",
                }
            ).execute()
            return code
        except Exception as e:  # pragma: no cover — unique collisions rare
            last_error = e
            logger.warning("Referral code collision or insert failure; retrying: %s", e)

    raise HTTPException(
        status_code=500,
        detail="Não foi possível gerar código de indicação. Tente novamente.",
    ) from last_error


def _maybe_send_welcome_email(user: dict, code: str) -> None:
    try:
        from email_service import send_email_async
        from templates.emails.referral_welcome import render_referral_welcome_email

        email = user.get("email")
        if not email:
            return
        share_url = f"https://smartlic.tech/signup?ref={code}"
        html = render_referral_welcome_email(
            user_name=user.get("user_metadata", {}).get("full_name", "")
            or email.split("@")[0],
            code=code,
            share_url=share_url,
        )
        send_email_async(
            to=email,
            subject="Indique o SmartLic e ganhe 1 mês grátis",
            html=html,
            tags=[{"name": "category", "value": "referral_welcome"}],
        )
    except Exception:
        logger.exception("Failed to dispatch referral welcome email")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/code", response_model=ReferralCodeResponse)
async def get_referral_code(user: dict = Depends(require_auth)):
    """Return the authenticated user's referral code (create if missing)."""
    from supabase_client import get_supabase

    sb = get_supabase()
    user_id = user["id"]

    # Check if a code already exists before we decide to send welcome email
    pre_existing = (
        sb.table("referrals")
        .select("code")
        .eq("referrer_user_id", user_id)
        .limit(1)
        .execute()
    )
    had_code = bool(getattr(pre_existing, "data", None))

    try:
        code = _get_or_create_code_for_user(sb, user_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch/create referral code for user")
        raise HTTPException(status_code=500, detail="Erro ao obter código de indicação.")

    if not had_code:
        _maybe_send_welcome_email(user, code)

    return ReferralCodeResponse(
        code=code,
        share_url=f"https://smartlic.tech/signup?ref={code}",
    )


@router.get("/stats", response_model=ReferralStatsResponse)
async def get_referral_stats(user: dict = Depends(require_auth)):
    """Aggregate stats for the authenticated user's referrals."""
    from supabase_client import get_supabase

    sb = get_supabase()
    user_id = user["id"]

    try:
        code = _get_or_create_code_for_user(sb, user_id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get referral code for stats")
        raise HTTPException(status_code=500, detail="Erro ao obter estatísticas.")

    try:
        rows = (
            sb.table("referrals")
            .select("status")
            .eq("referrer_user_id", user_id)
            .execute()
        )
        data = getattr(rows, "data", []) or []
    except Exception:
        logger.exception("Failed to fetch referral stats")
        data = []

    # A row with a referred_user_id that made it past 'pending' counts as a signup.
    signed_up_statuses = {"signed_up", "converted", "credited"}
    converted_statuses = {"converted", "credited"}

    total_signups = sum(1 for r in data if r.get("status") in signed_up_statuses)
    total_converted = sum(1 for r in data if r.get("status") in converted_statuses)
    credits_earned = sum(1 for r in data if r.get("status") == "credited")

    return ReferralStatsResponse(
        code=code,
        total_signups=total_signups,
        total_converted=total_converted,
        credits_earned_months=credits_earned,
    )


@router.post("/redeem", response_model=ReferralRedeemResponse)
async def redeem_referral(
    body: ReferralRedeemRequest,
    user: dict = Depends(require_auth),
):
    """Register a referral redemption during signup.

    The authenticated user is the *referred* user. We look up the row
    owned by the referrer (matched by code) and link the referred_user_id
    while promoting status to 'signed_up'. If no such row exists we
    silently succeed to avoid leaking code existence.
    """
    from supabase_client import get_supabase

    sb = get_supabase()
    code = body.code.strip().upper()

    if body.referred_user_id != user["id"]:
        # The caller can only redeem on their own behalf.
        raise HTTPException(status_code=403, detail="Identidade inválida.")

    try:
        match = (
            sb.table("referrals")
            .select("id, referrer_user_id, status, referred_user_id")
            .eq("code", code)
            .limit(1)
            .execute()
        )
    except Exception:
        logger.exception("Referral lookup failed for code redeem")
        raise HTTPException(status_code=500, detail="Erro ao validar código.")

    rows = getattr(match, "data", []) or []
    if not rows:
        logger.info("Referral code not found on redeem: %s", code)
        return ReferralRedeemResponse(status="ignored")

    row = rows[0]
    if row["referrer_user_id"] == body.referred_user_id:
        # Can't self-refer
        return ReferralRedeemResponse(status="ignored")
    if row.get("referred_user_id"):
        # Already claimed (one-time per code row)
        return ReferralRedeemResponse(status="already_redeemed")

    try:
        sb.table("referrals").update(
            {
                "referred_user_id": body.referred_user_id,
                "status": "signed_up",
            }
        ).eq("id", row["id"]).execute()
    except Exception:
        logger.exception("Failed to mark referral as signed_up")
        raise HTTPException(status_code=500, detail="Erro ao registrar indicação.")

    logger.info("Referral redeemed: code=%s referrer=%s referred=%s",
                code, row["referrer_user_id"], body.referred_user_id)
    return ReferralRedeemResponse(status="signed_up", code=code)
