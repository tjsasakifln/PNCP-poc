"""Email notification routes — STORY-225

AC7: Welcome email trigger after signup.
AC15-AC16: Unsubscribe mechanism for marketing emails.
"""

import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from auth import require_auth
from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["emails"])

# Secret for unsubscribe token verification
UNSUBSCRIBE_SECRET = os.getenv("UNSUBSCRIBE_SECRET", "smartlic-unsub-default-key")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://smartlic.tech")


class WelcomeEmailResponse(BaseModel):
    sent: bool
    message: str


def _generate_unsubscribe_token(user_id: str) -> str:
    """Generate HMAC-based unsubscribe token for a user."""
    return hmac.new(
        UNSUBSCRIBE_SECRET.encode(),
        user_id.encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


def get_unsubscribe_url(user_id: str) -> str:
    """Build unsubscribe URL for email footer."""
    token = _generate_unsubscribe_token(user_id)
    backend_url = os.getenv("BACKEND_URL", "https://bidiq-backend-production.up.railway.app")
    return f"{backend_url}/emails/unsubscribe?user_id={user_id}&token={token}"


@router.post("/emails/send-welcome", response_model=WelcomeEmailResponse)
async def send_welcome_email(user: dict = Depends(require_auth)):
    """
    Send welcome email to authenticated user (idempotent).

    AC7: Triggered after successful signup (both email and Google OAuth).
    Frontend calls this after signup confirmation.
    Idempotent: checks profiles.welcome_email_sent_at before sending.
    """
    from supabase_client import get_supabase
    from email_service import send_email_async
    from templates.emails.welcome import render_welcome_email
    from quota import PLAN_NAMES

    user_id = user["id"]
    sb = get_supabase()

    # Idempotency check: don't send if already sent
    try:
        profile = (
            sb.table("profiles")
            .select("email, full_name, plan_type, welcome_email_sent_at")
            .eq("id", user_id)
            .single()
            .execute()
        )

        if not profile.data:
            raise HTTPException(status_code=404, detail="Perfil não encontrado")

        if profile.data.get("welcome_email_sent_at"):
            return WelcomeEmailResponse(sent=False, message="Email de boas-vindas já enviado")

        email = profile.data.get("email", "")
        full_name = profile.data.get("full_name") or email.split("@")[0]
        plan_type = profile.data.get("plan_type", "free_trial")
        plan_name = PLAN_NAMES.get(plan_type, "FREE Trial")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check profile for welcome email: {e}")
        raise HTTPException(status_code=500, detail="Erro ao verificar perfil")

    if not email:
        return WelcomeEmailResponse(sent=False, message="Email não encontrado no perfil")

    # Mark as sent BEFORE sending (prevents duplicates on retry)
    try:
        sb.table("profiles").update({
            "welcome_email_sent_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id).execute()
    except Exception as e:
        logger.warning(f"Failed to mark welcome email as sent: {e}")
        # Continue anyway — better to send twice than never

    # Fire and forget
    html = render_welcome_email(
        user_name=full_name,
        plan_name=plan_name,
    )
    send_email_async(
        to=email,
        subject="Bem-vindo ao SmartLic!",
        html=html,
        tags=[{"name": "category", "value": "welcome"}],
    )

    logger.info(f"Welcome email queued for user {mask_user_id(user_id)}")
    return WelcomeEmailResponse(sent=True, message="Email de boas-vindas enviado")


@router.get("/emails/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_email(
    user_id: str = Query(..., description="User ID"),
    token: str = Query(..., description="Verification token"),
):
    """
    Unsubscribe from marketing emails.

    AC15: Unsubscribe mechanism in all marketing emails (LGPD + CAN-SPAM).
    AC16: Updates user preference in database.
    AC17: Transactional emails exempt (payment, security).
    """
    # Verify token
    expected_token = _generate_unsubscribe_token(user_id)
    if not hmac.compare_digest(token, expected_token):
        return HTMLResponse(
            content=_unsubscribe_page("Token inválido", success=False),
            status_code=400,
        )

    from supabase_client import get_supabase

    try:
        sb = get_supabase()
        sb.table("profiles").update({
            "email_unsubscribed": True,
            "email_unsubscribed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id).execute()

        logger.info(f"User {mask_user_id(user_id)} unsubscribed from marketing emails")

        return HTMLResponse(
            content=_unsubscribe_page(
                "Você foi removido dos emails promocionais. "
                "Ainda receberá emails transacionais (confirmações de pagamento, alertas de segurança).",
                success=True,
            )
        )

    except Exception as e:
        logger.error(f"Failed to process unsubscribe for user {mask_user_id(user_id)}: {e}")
        return HTMLResponse(
            content=_unsubscribe_page("Erro ao processar. Tente novamente.", success=False),
            status_code=500,
        )


def _unsubscribe_page(message: str, success: bool) -> str:
    """Render simple unsubscribe confirmation page."""
    icon = "&#10003;" if success else "&#10007;"
    color = "#2E7D32" if success else "#d32f2f"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SmartLic — Cancelar inscrição</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           display: flex; justify-content: center; align-items: center;
           min-height: 100vh; margin: 0; background: #f4f4f4; }}
    .card {{ background: white; padding: 48px; border-radius: 12px;
             box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; max-width: 480px; }}
    .icon {{ font-size: 48px; color: {color}; margin-bottom: 16px; }}
    h1 {{ font-size: 20px; color: #333; margin-bottom: 12px; }}
    p {{ color: #666; line-height: 1.6; }}
    a {{ color: #2E7D32; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">{icon}</div>
    <h1>{"Inscrição cancelada" if success else "Erro"}</h1>
    <p>{message}</p>
    <p style="margin-top: 24px;"><a href="{FRONTEND_URL}">Voltar para o SmartLic</a></p>
  </div>
</body>
</html>"""
