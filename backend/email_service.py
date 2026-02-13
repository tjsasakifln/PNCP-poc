"""
Transactional Email Service — STORY-225

Provides send_email() function with:
- Resend SDK integration
- Retry logic (3 retries, exponential backoff)
- Fire-and-forget async sending (never blocks caller)
- Structured logging

Usage:
    from email_service import send_email, EmailTemplate

    send_email(
        to="user@example.com",
        subject="Bem-vindo ao SmartLic!",
        html=render_welcome_template(name="João", plan="Consultor Ágil"),
        tags=[{"name": "category", "value": "welcome"}],
    )

Config:
    RESEND_API_KEY: Required. Set in .env / Railway.
    EMAIL_FROM: Optional. Defaults to "SmartLic <noreply@smartlic.tech>"
    EMAIL_ENABLED: Optional. Set to "false" to disable sending (dev mode).
"""

import logging
import os
import time
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "SmartLic <noreply@smartlic.tech>")
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "true").lower() in ("true", "1", "yes", "on")

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 10.0  # seconds


def _is_configured() -> bool:
    """Check if email service is properly configured."""
    if not EMAIL_ENABLED:
        return False
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — email sending disabled")
        return False
    return True


def send_email(
    to: str,
    subject: str,
    html: str,
    tags: Optional[list[dict[str, str]]] = None,
    reply_to: Optional[str] = None,
) -> Optional[str]:
    """
    Send a transactional email via Resend.

    AC3: Core send function with retry logic.
    AC4: Max 3 retries with exponential backoff.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        html: HTML body content.
        tags: Optional Resend tags for tracking.
        reply_to: Optional reply-to address.

    Returns:
        Email ID string on success, None on failure.
        Never raises — logs errors instead.
    """
    if not _is_configured():
        logger.debug(f"Email not sent (disabled/unconfigured): to={to}, subject={subject}")
        return None

    import resend
    resend.api_key = RESEND_API_KEY

    params: dict = {
        "from": EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if tags:
        params["tags"] = tags
    if reply_to:
        params["reply_to"] = reply_to

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            result = resend.Emails.send(params)
            email_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
            logger.info(f"Email sent: to={to}, subject={subject}, id={email_id}")
            return email_id
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                logger.warning(
                    f"Email send failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"Email send failed after {MAX_RETRIES} attempts: to={to}, "
                    f"subject={subject}, error={last_error}"
                )

    return None


def send_email_async(
    to: str,
    subject: str,
    html: str,
    tags: Optional[list[dict[str, str]]] = None,
    reply_to: Optional[str] = None,
) -> None:
    """
    Fire-and-forget email send in a background thread.

    AC22: Email send failure does not crash the triggering operation.
    Use this for non-critical emails (welcome, notifications) where
    we don't need to wait for the result.

    Args:
        Same as send_email().
    """
    def _send():
        try:
            send_email(to=to, subject=subject, html=html, tags=tags, reply_to=reply_to)
        except Exception as e:
            # Belt-and-suspenders: send_email already catches, but just in case
            logger.error(f"Async email send unexpected error: {e}")

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
