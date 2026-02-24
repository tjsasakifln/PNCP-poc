"""STORY-258 AC11-AC12, AC15: Pre-signup validation endpoints.

Endpoints:
- GET /auth/check-email — Validate email (disposable check, no enumeration leak)
- GET /auth/check-phone — Validate phone uniqueness (boolean only)

Both endpoints are rate-limited: 10 req/min/IP.
"""

import logging
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request, Query

from utils.disposable_emails import is_disposable_email, is_corporate_email
from utils.email_normalizer import normalize_email
from utils.phone_normalizer import normalize_phone

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth-check"])

# ---------------------------------------------------------------------------
# Rate limiting (in-memory, per-IP)
# ---------------------------------------------------------------------------
_CHECK_RATE_LIMIT = 10  # requests per minute
_CHECK_WINDOW_S = 60

_rate_limits: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(ip: str) -> None:
    """Enforce rate limit: 10 req/min/IP."""
    now = time.time()
    cutoff = now - _CHECK_WINDOW_S
    attempts = _rate_limits[ip]
    _rate_limits[ip] = [t for t in attempts if t > cutoff]

    if len(_rate_limits[ip]) >= _CHECK_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Muitas verificações. Aguarde 1 minuto.",
        )
    _rate_limits[ip].append(now)


def _get_ip(request: Request) -> str:
    """Extract client IP from request headers."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.headers.get("x-real-ip", request.client.host if request.client else "unknown")


# ---------------------------------------------------------------------------
# GET /auth/check-email
# ---------------------------------------------------------------------------

@router.get("/check-email")
async def check_email(
    request: Request,
    email: str = Query(..., min_length=5, max_length=320),
):
    """AC15: Pre-signup email validation.

    Returns { available: bool, disposable: bool, corporate: bool }.

    Security:
    - Does NOT reveal if email already exists (always available=true for disposable).
    - Rate limited: 10 req/min/IP.
    """
    ip = _get_ip(request)
    _check_rate_limit(ip)

    email_lower = email.strip().lower()
    disposable = is_disposable_email(email_lower)
    corporate = is_corporate_email(email_lower)

    if disposable:
        # AC15: Don't reveal that email was blocked — return available=true
        # to prevent enumeration (blocked vs already-exists is indistinguishable)
        logger.info(f"AUDIT: Disposable email check — domain blocked (ip={ip})")
        return {
            "available": True,
            "disposable": True,
            "corporate": False,
        }

    return {
        "available": True,
        "disposable": False,
        "corporate": corporate,
    }


# ---------------------------------------------------------------------------
# GET /auth/check-phone
# ---------------------------------------------------------------------------

async def _check_fingerprint_abuse(phone: str, company: str | None, request: Request):
    """AC13: Log warning if same phone+company combination exists with different email."""
    if not phone or not company:
        return
    try:
        from supabase_client import get_supabase
        db = get_supabase()
        result = db.table("profiles").select("id, email").eq("phone_whatsapp", phone).eq("company", company).execute()
        if result.data:
            logger.warning(
                f"AUDIT: Potential duplicate account detected — "
                f"phone={phone[:4]}****, company={company}, "
                f"existing_accounts={len(result.data)}, ip={request.client.host if request.client else 'unknown'}"
            )
    except Exception as e:
        logger.debug(f"Fingerprint check failed (non-blocking): {e}")


@router.get("/check-phone")
async def check_phone(
    request: Request,
    phone: str = Query(..., min_length=8, max_length=20),
    company: str | None = Query(default=None, max_length=200),
):
    """AC11-AC12: Pre-signup phone uniqueness check.

    Returns { available: bool } only — no data leakage.
    AC13: Optional company param triggers fingerprint abuse detection (non-blocking).
    Rate limited: 10 req/min/IP.
    """
    ip = _get_ip(request)
    _check_rate_limit(ip)

    normalized = normalize_phone(phone)
    if not normalized:
        return {"available": True}  # Invalid format — don't block, let form validation handle

    try:
        from supabase_client import get_supabase
        db = get_supabase()

        result = (
            db.table("profiles")
            .select("id")
            .eq("phone_whatsapp", normalized)
            .limit(1)
            .execute()
        )

        available = not bool(result.data)

        # AC13: Non-blocking fingerprint abuse detection when company is provided
        if available and company:
            await _check_fingerprint_abuse(normalized, company, request)

        return {"available": available}

    except Exception as e:
        logger.warning(f"Phone check failed (returning available=true): {e}")
        # Fail open — don't block signup on DB errors
        return {"available": True}
