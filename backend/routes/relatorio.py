"""Report lead capture routes — SEO-PLAYBOOK Panorama 2026 T1.

Endpoints:
- POST /v1/relatorio-2026-t1/request — Captures a lead (email, empresa, cargo),
  persists to `report_leads`, and sends the delivery email with the PDF link.

The endpoint is public (no auth) because the report is a lead-gen asset.
Dedup is enforced via a UNIQUE(email, source) constraint, upserted on conflict.
Email delivery is best-effort — if Resend fails, the lead is still captured
and `email_queued=False` is returned so the frontend can surface a retry hint.
"""

import hashlib
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/relatorio-2026-t1", tags=["relatorio"])

# Public download URL — Supabase Storage. Update after uploading the real PDF.
PDF_PUBLIC_URL = "https://smartlic.tech/downloads/panorama-2026-t1.pdf"
REPORT_SOURCE = "panorama-2026-t1"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RelatorioRequest(BaseModel):
    email: EmailStr
    empresa: str = Field(..., min_length=2, max_length=100)
    cargo: Literal["diretor", "gerente", "analista", "consultor", "outro"]
    newsletter_opt_in: bool = False


class RelatorioResponse(BaseModel):
    download_url: str
    email_queued: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hash_ip(ip: str) -> str:
    if not ip:
        return ""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    client = getattr(request, "client", None)
    return getattr(client, "host", "") or ""


def _email_domain(email: str) -> str:
    return email.split("@", 1)[-1] if "@" in email else ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/request", response_model=RelatorioResponse)
async def request_relatorio(payload: RelatorioRequest, request: Request):
    """Capture a report lead and dispatch the delivery email.

    Flow:
      1. Upsert row into `report_leads` on (email, source).
      2. Attempt to send the delivery email via Resend (best-effort).
      3. Return the download URL + email_queued flag.

    Persistence failure -> 500. Email failure -> 200 with email_queued=False.
    """
    from supabase_client import get_supabase

    supabase = get_supabase()
    ip_hash = _hash_ip(_client_ip(request))

    row = {
        "email": payload.email.lower(),
        "empresa": payload.empresa.strip(),
        "cargo": payload.cargo,
        "newsletter_opt_in": payload.newsletter_opt_in,
        "source": REPORT_SOURCE,
        "ip_hash": ip_hash,
    }

    try:
        supabase.table("report_leads").upsert(
            row, on_conflict="email,source"
        ).execute()
    except Exception:
        logger.exception(
            "report_lead_db_error email_domain=%s", _email_domain(payload.email)
        )
        raise HTTPException(status_code=500, detail="persistence_failed")

    # Best-effort email delivery — never blocks lead capture.
    email_queued = False
    try:
        from email_service import send_email
        from templates.emails.panorama_t1_delivery import render_panorama_t1_delivery

        html = render_panorama_t1_delivery(
            empresa=payload.empresa.strip(),
            download_url=PDF_PUBLIC_URL,
        )
        send_email(
            to=payload.email,
            subject="Panorama Licitações Brasil 2026 T1 — seu download",
            html=html,
            tags=[{"name": "category", "value": "report_delivery"}],
        )
        email_queued = True
    except Exception as e:
        logger.warning(
            "report_lead_email_failed email_domain=%s error=%s",
            _email_domain(payload.email),
            str(e),
        )

    logger.info(
        "analytics.report_lead_captured source=%s cargo=%s newsletter=%s "
        "email_domain=%s email_queued=%s",
        REPORT_SOURCE,
        payload.cargo,
        payload.newsletter_opt_in,
        _email_domain(payload.email),
        email_queued,
    )

    return RelatorioResponse(download_url=PDF_PUBLIC_URL, email_queued=email_queued)
