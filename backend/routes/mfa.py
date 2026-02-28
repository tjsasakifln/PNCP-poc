"""MFA (Multi-Factor Authentication) routes for SmartLic.

STORY-317: TOTP MFA with recovery codes.
- GET /v1/mfa/status — MFA status for current user
- POST /v1/mfa/recovery-codes — Generate recovery codes after MFA enrollment
- POST /v1/mfa/verify-recovery — Verify a recovery code (brute force protected)
- POST /v1/mfa/regenerate-recovery — Regenerate recovery codes (requires aal2)
"""

import logging
import secrets
from datetime import datetime, timezone, timedelta

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import require_auth
from authorization import check_user_roles

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mfa", tags=["MFA"])

# Constants
RECOVERY_CODE_COUNT = 10
RECOVERY_CODE_LENGTH = 8  # 8 hex chars = 4 bytes = 2^32 possibilities
MAX_FAILED_ATTEMPTS_PER_HOUR = 3


# ─── Schemas ───────────────────────────────────────────────────────────────────

class MfaStatusResponse(BaseModel):
    mfa_enabled: bool
    factors: list[dict] = Field(default_factory=list)
    aal_level: str = "aal1"
    mfa_required: bool = False


class RecoveryCodesResponse(BaseModel):
    codes: list[str]
    message: str = "Salve estes códigos em local seguro. Cada código só pode ser usado uma vez."


class VerifyRecoveryRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=20)


class VerifyRecoveryResponse(BaseModel):
    success: bool
    remaining_codes: int = 0
    message: str = ""


class RegenerateRecoveryResponse(BaseModel):
    codes: list[str]
    message: str = "Novos códigos gerados. Os códigos anteriores foram invalidados."


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _generate_recovery_codes(count: int = RECOVERY_CODE_COUNT) -> list[str]:
    """Generate cryptographically secure recovery codes.

    Returns list of uppercase hex strings formatted as XXXX-XXXX.
    """
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(RECOVERY_CODE_LENGTH // 2).upper()
        formatted = f"{raw[:4]}-{raw[4:]}"
        codes.append(formatted)
    return codes


def _hash_code(code: str) -> str:
    """Hash a recovery code with bcrypt."""
    clean = code.replace("-", "").upper()
    return bcrypt.hashpw(clean.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_code(code: str, code_hash: str) -> bool:
    """Verify a recovery code against its bcrypt hash."""
    clean = code.replace("-", "").upper()
    return bcrypt.checkpw(clean.encode("utf-8"), code_hash.encode("utf-8"))


async def _get_supabase():
    """Get Supabase client (lazy import to avoid circular deps)."""
    from supabase_client import get_supabase
    return get_supabase()


async def _check_brute_force(user_id: str) -> int:
    """Check failed recovery attempts in the last hour.

    Returns the number of failed attempts. Raises 429 if limit exceeded.
    """
    sb = await _get_supabase()
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    result = (
        sb.table("mfa_recovery_attempts")
        .select("id")
        .eq("user_id", user_id)
        .eq("success", False)
        .gte("attempted_at", one_hour_ago)
        .execute()
    )

    failed_count = len(result.data) if result.data else 0

    if failed_count >= MAX_FAILED_ATTEMPTS_PER_HOUR:
        logger.warning(f"MFA recovery brute force limit hit for user {user_id[:8]}...")
        raise HTTPException(
            status_code=429,
            detail=f"Muitas tentativas. Tente novamente em 1 hora. ({failed_count}/{MAX_FAILED_ATTEMPTS_PER_HOUR})",
        )

    return failed_count


async def _record_attempt(user_id: str, success: bool) -> None:
    """Record a recovery code attempt for brute force tracking."""
    sb = await _get_supabase()
    sb.table("mfa_recovery_attempts").insert({
        "user_id": user_id,
        "success": success,
    }).execute()


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.get("/status", response_model=MfaStatusResponse)
async def get_mfa_status(user: dict = Depends(require_auth)):
    """AC4: Get MFA status for the current user.

    Returns whether MFA is enabled, enrolled factors, current AAL level,
    and whether MFA is required for this user's role.
    """
    user_id = user["id"]

    # Check if user is admin/master (MFA required for these roles)
    is_admin, is_master = await check_user_roles(user_id)
    mfa_required = is_admin or is_master

    # Get AAL from JWT claims (stored in user dict by auth.py)
    aal_level = user.get("aal", "aal1")

    # Get enrolled factors from Supabase auth.mfa_factors table
    factors = []
    try:
        sb = await _get_supabase()
        result = (
            sb.table("mfa_factors")
            .select("id, factor_type, friendly_name, status, created_at")
            .eq("user_id", user_id)
            .execute()
        )

        if result.data:
            for f in result.data:
                factors.append({
                    "id": f["id"],
                    "type": f.get("factor_type", "totp"),
                    "friendly_name": f.get("friendly_name", ""),
                    "verified": f.get("status") == "verified",
                })
    except Exception as e:
        # If we can't read factors, use mfa_amr_claims or default
        logger.warning(f"Failed to read MFA factors for user {user_id[:8]}: {type(e).__name__}")

    mfa_enabled = any(f.get("verified") for f in factors)

    return MfaStatusResponse(
        mfa_enabled=mfa_enabled,
        factors=factors,
        aal_level=aal_level,
        mfa_required=mfa_required,
    )


@router.post("/recovery-codes", response_model=RecoveryCodesResponse)
async def generate_recovery_codes(user: dict = Depends(require_auth)):
    """AC5: Generate 10 recovery codes after MFA enrollment.

    This should be called immediately after successful MFA enrollment.
    Stores bcrypt-hashed codes in the database, returns plaintext once.
    """
    user_id = user["id"]
    sb = await _get_supabase()

    # Delete any existing codes for this user (fresh set on each enrollment)
    sb.table("mfa_recovery_codes").delete().eq("user_id", user_id).execute()

    # Generate and store codes
    plaintext_codes = _generate_recovery_codes()

    rows = []
    for code in plaintext_codes:
        rows.append({
            "user_id": user_id,
            "code_hash": _hash_code(code),
        })

    sb.table("mfa_recovery_codes").insert(rows).execute()

    logger.info(f"Generated {len(plaintext_codes)} recovery codes for user {user_id[:8]}...")

    return RecoveryCodesResponse(codes=plaintext_codes)


@router.post("/verify-recovery", response_model=VerifyRecoveryResponse)
async def verify_recovery_code(
    body: VerifyRecoveryRequest,
    user: dict = Depends(require_auth),
):
    """AC7: Verify a recovery code for MFA bypass.

    Brute force protection: max 3 failed attempts per hour.
    On success: marks code as used, returns remaining count.
    """
    user_id = user["id"]

    # AC7: Check brute force limit
    await _check_brute_force(user_id)

    sb = await _get_supabase()

    # Get unused codes for this user
    result = (
        sb.table("mfa_recovery_codes")
        .select("id, code_hash")
        .eq("user_id", user_id)
        .is_("used_at", "null")
        .execute()
    )

    stored_codes = result.data or []

    # Try to match the provided code against stored hashes
    for stored in stored_codes:
        if _verify_code(body.code, stored["code_hash"]):
            # Mark as used
            sb.table("mfa_recovery_codes").update({
                "used_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", stored["id"]).execute()

            # Record successful attempt
            await _record_attempt(user_id, success=True)

            remaining = len(stored_codes) - 1
            logger.info(f"Recovery code verified for user {user_id[:8]}. Remaining: {remaining}")

            msg = "Código verificado com sucesso."
            if remaining <= 2:
                msg += f" Atenção: restam apenas {remaining} códigos. Regenere seus códigos."

            return VerifyRecoveryResponse(
                success=True,
                remaining_codes=remaining,
                message=msg,
            )

    # No match — record failed attempt
    await _record_attempt(user_id, success=False)

    failed_count = len(
        (sb.table("mfa_recovery_attempts")
         .select("id")
         .eq("user_id", user_id)
         .eq("success", False)
         .gte("attempted_at", (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat())
         .execute()).data or []
    )

    remaining_attempts = MAX_FAILED_ATTEMPTS_PER_HOUR - failed_count

    return VerifyRecoveryResponse(
        success=False,
        remaining_codes=0,
        message=f"Código inválido ou já utilizado. Tentativas restantes: {remaining_attempts}",
    )


@router.post("/regenerate-recovery", response_model=RegenerateRecoveryResponse)
async def regenerate_recovery_codes(user: dict = Depends(require_auth)):
    """AC8: Regenerate recovery codes (requires aal2).

    Invalidates all existing codes and generates a fresh set.
    """
    user_id = user["id"]
    aal = user.get("aal", "aal1")

    # Require aal2 for regeneration (user must have verified MFA this session)
    if aal != "aal2":
        raise HTTPException(
            status_code=403,
            detail="Verificação MFA necessária para regenerar códigos. Faça login com seu código TOTP primeiro.",
        )

    sb = await _get_supabase()

    # Delete all existing codes
    sb.table("mfa_recovery_codes").delete().eq("user_id", user_id).execute()

    # Generate fresh codes
    plaintext_codes = _generate_recovery_codes()

    rows = [{"user_id": user_id, "code_hash": _hash_code(code)} for code in plaintext_codes]
    sb.table("mfa_recovery_codes").insert(rows).execute()

    logger.info(f"Regenerated recovery codes for user {user_id[:8]}...")

    return RegenerateRecoveryResponse(codes=plaintext_codes)
