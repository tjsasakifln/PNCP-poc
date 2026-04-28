"""
STORY-310: Trial email sequence routes.

AC2:  GET  /trial-emails/unsubscribe     — One-click unsubscribe (RFC 8058)
AC11: POST /trial-emails/webhook         — Resend webhook for opens/clicks (Svix HMAC verified)
AC13: GET  /admin/trial-emails/preview   — Preview all templates (admin)
AC14: POST /admin/trial-emails/test-send — Send test email (admin)
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
import time

from fastapi import APIRouter, Query, Request, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(tags=["trial-emails"])


# ============================================================================
# AC2: One-click unsubscribe (RFC 8058)
# ============================================================================

@router.get("/trial-emails/unsubscribe")
async def unsubscribe_trial_emails(
    user_id: str = Query(..., description="User ID"),
    token: str = Query(..., description="HMAC unsubscribe token"),
):
    """AC2/AC5: One-click unsubscribe from trial marketing emails.
    Zero-churn P2 §1.2: Only disables marketing/promotional emails.
    Critical conversion emails (Day 7/10/13/16) remain active unless
    user explicitly opts out of those too.
    """
    from services.trial_email_sequence import verify_unsubscribe_token
    from supabase_client import get_supabase, sb_execute

    if not verify_unsubscribe_token(user_id, token):
        raise HTTPException(status_code=403, detail="Invalid unsubscribe token")

    try:
        sb = get_supabase()
        # P2 §1.2: Only disable marketing emails; keep conversion emails active
        await sb_execute(
            sb.table("profiles")
            .update({"marketing_emails_enabled": False})
            .eq("id", user_id)
        )
        logger.info(f"User {user_id[:8]}*** unsubscribed from marketing emails (conversion emails remain active)")

        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head><meta charset="UTF-8"><title>Cancelado — SmartLic</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 60px;">
          <h1 style="color: #333;">Emails promocionais cancelados</h1>
          <p style="color: #666;">Você não receberá mais emails promocionais do SmartLic.</p>
          <p style="color: #555; font-size: 14px;">
            Emails sobre prazos e status do seu trial continuam ativos para que você não perca informações importantes.
          </p>
          <p style="color: #999; font-size: 14px;">
            Se mudar de ideia, acesse
            <a href="https://smartlic.tech/conta">suas configurações</a>.
          </p>
        </body>
        </html>
        """)

    except Exception as e:
        logger.error(f"Unsubscribe failed for {user_id[:8]}***: {e}")
        raise HTTPException(status_code=500, detail="Erro ao cancelar inscrição")


# ============================================================================
# AC11: Resend webhook for opens/clicks (Svix HMAC verified)
# ============================================================================

# Svix signature spec: https://docs.svix.com/receiving/verifying-payloads/how-manual
# Resend uses Svix under the hood — secret format `whsec_<base64>`.
_SVIX_TIMESTAMP_TOLERANCE_SECONDS = 300  # 5 min (Svix recommended)


def _verify_svix_signature(
    body: bytes,
    svix_id: Optional[str],
    svix_timestamp: Optional[str],
    svix_signature: Optional[str],
) -> bool:
    """Verify Resend/Svix webhook signature.

    Fail-closed: missing secret, header, or invalid signature → False.
    Constant-time comparison via secrets.compare_digest.
    """
    secret_raw = os.getenv("RESEND_WEBHOOK_SECRET", "")
    if not secret_raw or not svix_id or not svix_timestamp or not svix_signature:
        return False

    # Strip Svix prefix if present (`whsec_<base64>`)
    if secret_raw.startswith("whsec_"):
        secret_raw = secret_raw[len("whsec_"):]

    try:
        secret_bytes = base64.b64decode(secret_raw)
    except Exception:
        return False

    # Replay protection — reject events outside tolerance window
    try:
        ts = int(svix_timestamp)
    except (ValueError, TypeError):
        return False
    if abs(int(time.time()) - ts) > _SVIX_TIMESTAMP_TOLERANCE_SECONDS:
        return False

    # Construct signed payload exactly as Svix specifies
    signed_payload = f"{svix_id}.{svix_timestamp}.".encode("utf-8") + body
    expected_b64 = base64.b64encode(
        hmac.new(secret_bytes, signed_payload, hashlib.sha256).digest()
    ).decode("ascii")

    # Header format: "v1,sig1 v1,sig2 ..." (Svix supports rotated keys)
    candidate_sigs = [
        token.split(",", 1)[1]
        for token in svix_signature.split(" ")
        if "," in token and token.startswith("v1,")
    ]
    return any(secrets.compare_digest(expected_b64, sig) for sig in candidate_sigs)


@router.post("/trial-emails/webhook")
async def resend_webhook(
    request: Request,
    svix_id: Optional[str] = Header(default=None, alias="svix-id"),
    svix_timestamp: Optional[str] = Header(default=None, alias="svix-timestamp"),
    svix_signature: Optional[str] = Header(default=None, alias="svix-signature"),
):
    """Handle Resend webhook events for email tracking.

    Security: Svix HMAC-SHA256 signature verified against `RESEND_WEBHOOK_SECRET`.
    Replay protection: timestamp must be within 5 minutes of now.
    Fail-closed — missing secret or invalid signature returns 401.

    Accepts the full delivery lifecycle (sent → delivered → opened → clicked)
    plus failure paths (bounced, complained, delivery_delayed, failed) so the
    admin funnel dashboard can distinguish "email never arrived" from "email
    arrived but wasn't engaged". Service handler
    (`services.trial_email_sequence.handle_resend_webhook`) populates the
    columns added in migration 20260424180000_trial_email_delivery_tracking.

    Returns 200 for processed/ignored/skipped so Resend doesn't retry; 401 on
    signature failure (Resend will retry — desired so legitimate events aren't
    lost during transient secret rotation).
    """
    raw_body = await request.body()

    if not _verify_svix_signature(raw_body, svix_id, svix_timestamp, svix_signature):
        logger.warning(
            "Resend webhook signature verification failed (svix-id=%s)",
            (svix_id or "<missing>")[:16],
        )
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        import json
        body = json.loads(raw_body) if raw_body else {}
        event_type = body.get("type", "")
        data = body.get("data", {})

        from services.trial_email_sequence import RESEND_STATUS_MAP, handle_resend_webhook
        if event_type not in RESEND_STATUS_MAP:
            return JSONResponse({"status": "ignored", "event_type": event_type})

        processed = await handle_resend_webhook(event_type, data)

        return JSONResponse({"status": "processed" if processed else "skipped"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend webhook error: {e}")
        return JSONResponse({"status": "error"}, status_code=200)  # Always 200 for processing errors


# ============================================================================
# AC13-AC14: Admin email preview and test send
# ============================================================================

@router.get("/admin/trial-emails/preview")
async def preview_trial_emails(request: Request):
    """AC15: Preview all 6 trial email templates."""
    from auth import require_auth
    from authorization import require_admin

    user = await require_auth(request)
    require_admin(user)

    from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE, _render_email

    sample_stats = {
        "searches_count": 12,
        "opportunities_found": 47,
        "total_value_estimated": 2_350_000,
        "pipeline_items_count": 8,
        "sectors_searched": ["software", "medicamentos", "construcao"],
        "days_remaining": 15,
    }

    previews = []
    for email_def in TRIAL_EMAIL_SEQUENCE:
        try:
            subject, html = _render_email(
                email_type=email_def["type"],
                user_name="Usuário Teste",
                stats=sample_stats,
                unsubscribe_url="https://smartlic.tech/unsubscribe?test=true",
            )
            previews.append({
                "number": email_def["number"],
                "day": email_def["day"],
                "type": email_def["type"],
                "subject": subject,
                "html": html,
            })
        except Exception as e:
            previews.append({
                "number": email_def["number"],
                "day": email_def["day"],
                "type": email_def["type"],
                "error": str(e),
            })

    return JSONResponse(previews)


@router.post("/admin/trial-emails/test-send")
async def test_send_trial_email(request: Request):
    """AC14: Send a test trial email to the admin's own email."""
    from auth import require_auth
    from authorization import require_admin

    user = await require_auth(request)
    require_admin(user)

    body = await request.json()
    email_type = body.get("email_type", "welcome")
    target_email = body.get("email", user.get("email", ""))

    if not target_email:
        raise HTTPException(status_code=400, detail="No target email specified")

    from services.trial_email_sequence import _render_email
    from email_service import send_email

    sample_stats = {
        "searches_count": 12,
        "opportunities_found": 47,
        "total_value_estimated": 2_350_000,
        "pipeline_items_count": 8,
        "sectors_searched": ["software", "medicamentos", "construcao"],
        "days_remaining": 15,
    }

    try:
        subject, html = _render_email(
            email_type=email_type,
            user_name="Admin Teste",
            stats=sample_stats,
            unsubscribe_url="https://smartlic.tech/unsubscribe?test=true",
        )

        email_id = send_email(
            to=target_email,
            subject=f"[TESTE] {subject}",
            html=html,
            tags=[
                {"name": "category", "value": "test"},
                {"name": "type", "value": email_type},
            ],
        )

        return JSONResponse({
            "status": "sent",
            "email_id": email_id,
            "to": target_email,
            "type": email_type,
            "subject": subject,
        })

    except Exception as e:
        logger.error(f"Test send failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
