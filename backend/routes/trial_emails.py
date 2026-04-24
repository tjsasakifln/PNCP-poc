"""
STORY-310: Trial email sequence routes.

AC2:  GET  /trial-emails/unsubscribe     — One-click unsubscribe (RFC 8058)
AC11: POST /trial-emails/webhook         — Resend webhook for opens/clicks
AC13: GET  /admin/trial-emails/preview   — Preview all templates (admin)
AC14: POST /admin/trial-emails/test-send — Send test email (admin)
"""

import logging
from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

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
# AC11: Resend webhook for opens/clicks
# ============================================================================

@router.post("/trial-emails/webhook")
async def resend_webhook(request: Request):
    """Handle Resend webhook events for email tracking.

    Accepts the full delivery lifecycle (sent → delivered → opened → clicked)
    plus failure paths (bounced, complained, delivery_delayed, failed) so the
    admin funnel dashboard can distinguish "email never arrived" from "email
    arrived but wasn't engaged". Service handler
    (`services.trial_email_sequence.handle_resend_webhook`) populates the
    columns added in migration 20260424180000_trial_email_delivery_tracking.
    Always returns 200 so Resend doesn't retry on transient server errors.
    """
    try:
        body = await request.json()
        event_type = body.get("type", "")
        data = body.get("data", {})

        from services.trial_email_sequence import RESEND_STATUS_MAP, handle_resend_webhook
        if event_type not in RESEND_STATUS_MAP:
            return JSONResponse({"status": "ignored", "event_type": event_type})

        processed = await handle_resend_webhook(event_type, data)

        return JSONResponse({"status": "processed" if processed else "skipped"})

    except Exception as e:
        logger.error(f"Resend webhook error: {e}")
        return JSONResponse({"status": "error"}, status_code=200)  # Always 200 for webhooks


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
