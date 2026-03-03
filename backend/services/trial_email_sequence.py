"""
STORY-321 AC1-AC6, AC12-AC14: Trial email sequence — 6 emails over 14 days.

Compressed sequence (replaces STORY-310 8-email sequence):
- Day 0:  Welcome (onboarding CTA)
- Day 3:  Engagement (stats de uso)
- Day 7:  Paywall alert (preview limitado amanha)
- Day 10: Valor acumulado (social proof R$X)
- Day 13: Ultimo dia (escassez)
- Day 16: Expirado (reengajamento 20% off)

Respects feature flags, conversion status, and unsubscribe preferences.
"""

import logging
import hmac
import hashlib
import os
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# HMAC secret for unsubscribe tokens (reuses WEBHOOK_SECRET or falls back)
_UNSUBSCRIBE_SECRET = os.getenv("WEBHOOK_SECRET", os.getenv("SECRET_KEY", "smartlic-trial-unsub"))

# ============================================================================
# AC1: Email sequence definition — 6 emails over 14-day trial
# ============================================================================

TRIAL_EMAIL_SEQUENCE = [
    {"number": 1, "day": 0,  "type": "welcome"},
    {"number": 2, "day": 3,  "type": "engagement"},
    {"number": 3, "day": 7,  "type": "paywall_alert"},
    {"number": 4, "day": 10, "type": "value"},
    {"number": 5, "day": 13, "type": "last_day"},
    {"number": 6, "day": 16, "type": "expired"},
]

# AC13: Stripe coupon for reengagement email (20% off first month)
TRIAL_COMEBACK_COUPON = os.getenv("TRIAL_COMEBACK_COUPON", "TRIAL_COMEBACK_20")


def _generate_unsubscribe_token(user_id: str) -> str:
    """Generate HMAC-based unsubscribe token for trial emails (AC2: RFC 8058)."""
    return hmac.new(
        _UNSUBSCRIBE_SECRET.encode(),
        f"trial-unsub:{user_id}".encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


def get_unsubscribe_url(user_id: str) -> str:
    """Build one-click unsubscribe URL for trial email footer (AC2)."""
    token = _generate_unsubscribe_token(user_id)
    backend_url = os.getenv(
        "BACKEND_URL",
        os.getenv("RAILWAY_PUBLIC_DOMAIN", "https://api.smartlic.tech"),
    )
    if not backend_url.startswith("http"):
        backend_url = f"https://{backend_url}"
    return f"{backend_url}/v1/trial-emails/unsubscribe?user_id={user_id}&token={token}"


def verify_unsubscribe_token(user_id: str, token: str) -> bool:
    """Verify HMAC-based unsubscribe token."""
    expected = _generate_unsubscribe_token(user_id)
    return hmac.compare_digest(token, expected)


# ============================================================================
# AC14: Coupon checkout URL
# ============================================================================

def get_coupon_checkout_url() -> str:
    """AC14: Build Stripe checkout URL with TRIAL_COMEBACK_20 coupon applied.

    Returns the /planos URL with coupon query param. The frontend handles
    passing the coupon to the checkout API.
    """
    from templates.emails.base import FRONTEND_URL
    return f"{FRONTEND_URL}/planos?coupon={TRIAL_COMEBACK_COUPON}"


# ============================================================================
# AC12: get_trial_user_stats(user_id) — stats with days_remaining
# ============================================================================

def get_trial_user_stats(user_id: str) -> dict:
    """AC12: Get trial user stats including days_remaining.

    Returns:
        dict with keys: searches_executed, opportunities_found,
        total_value_analyzed, pipeline_items, days_remaining
    """
    from services.trial_stats import get_trial_usage_stats
    from supabase_client import get_supabase

    # Get base stats from existing service
    base_stats = get_trial_usage_stats(user_id)
    stats_dict = base_stats.model_dump()

    # Calculate days_remaining from profile created_at
    days_remaining = 0
    try:
        sb = get_supabase()
        profile = (
            sb.table("profiles")
            .select("created_at")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if profile.data and len(profile.data) > 0:
            created_str = profile.data[0].get("created_at", "")
            if created_str:
                from config import TRIAL_DURATION_DAYS
                created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                trial_end = created_at + timedelta(days=TRIAL_DURATION_DAYS)
                now = datetime.now(timezone.utc)
                remaining = (trial_end - now).days
                days_remaining = max(0, remaining)
    except Exception as e:
        logger.debug(f"Could not calculate days_remaining for {user_id[:8]}***: {e}")

    return {
        "searches_executed": stats_dict.get("searches_count", 0),
        "opportunities_found": stats_dict.get("opportunities_found", 0),
        "total_value_analyzed": stats_dict.get("total_value_estimated", 0.0),
        "pipeline_items": stats_dict.get("pipeline_items_count", 0),
        "days_remaining": days_remaining,
        # Also include original keys for template compatibility
        "searches_count": stats_dict.get("searches_count", 0),
        "total_value_estimated": stats_dict.get("total_value_estimated", 0.0),
        "pipeline_items_count": stats_dict.get("pipeline_items_count", 0),
        "sectors_searched": stats_dict.get("sectors_searched", []),
    }


# ============================================================================
# AC1-AC6: Main dispatch logic
# ============================================================================

async def process_trial_emails(batch_size: int = 50) -> dict:
    """STORY-321 AC1/AC10: Process pending trial emails for all eligible users.

    Runs daily at 08:00 BRT. For each email in the sequence, identifies
    users who should receive it and dispatches the email.

    AC3: Respects TRIAL_EMAILS_ENABLED flag.
    AC4: Skips users who have already converted to paid.
    AC5: Skips users who have opted out of marketing emails.
    AC6: Dedup via trial_email_log table.
    AC10: Batch processing with max batch_size emails per execution.

    Args:
        batch_size: Maximum emails to send per execution (default 50).

    Returns:
        dict with counts: {"sent": N, "skipped": M, "errors": E, "converted_skipped": C}
    """
    from config import TRIAL_EMAILS_ENABLED

    if not TRIAL_EMAILS_ENABLED:
        logger.debug("Trial emails disabled (TRIAL_EMAILS_ENABLED=false)")
        return {"sent": 0, "skipped": 0, "errors": 0, "disabled": True}

    try:
        from supabase_client import get_supabase, sb_execute
        from email_service import send_email_async
        from metrics import TRIAL_EMAILS_SENT

        sb = get_supabase()
        now = datetime.now(timezone.utc)

        sent = 0
        skipped = 0
        errors = 0
        converted_skipped = 0
        unsubscribed_skipped = 0

        for email_def in TRIAL_EMAIL_SEQUENCE:
            if sent >= batch_size:
                logger.info(f"Batch limit reached ({batch_size}), stopping")
                break

            email_number = email_def["number"]
            day = email_def["day"]
            email_type = email_def["type"]

            try:
                # Calculate target date range: users created exactly `day` days ago
                # Use a 24h window to handle timezone differences
                target_start = (now - timedelta(days=day, hours=12)).isoformat()
                target_end = (now - timedelta(days=day - 1, hours=-12)).isoformat()

                # Find trial users at this milestone
                # AC4: Only free_trial users (converted users have different plan_type)
                # AC5: Only users with marketing_emails_enabled=true
                users_result = await sb_execute(
                    sb.table("profiles")
                    .select("id, email, full_name, plan_type, marketing_emails_enabled")
                    .eq("plan_type", "free_trial")
                    .gte("created_at", target_start)
                    .lt("created_at", target_end)
                )

                if not users_result.data:
                    continue

                for user in users_result.data:
                    if sent >= batch_size:
                        break

                    user_id = user["id"]
                    email_addr = user.get("email", "")
                    user_name = user.get("full_name") or (email_addr.split("@")[0] if email_addr else "Usuario")

                    if not email_addr:
                        continue

                    # AC4: Skip if user has converted (double-check plan_type)
                    plan_type = user.get("plan_type", "")
                    if plan_type != "free_trial":
                        converted_skipped += 1
                        continue

                    # AC5: Skip if user has unsubscribed from marketing emails
                    if user.get("marketing_emails_enabled") is False:
                        unsubscribed_skipped += 1
                        continue

                    # AC6: Idempotency check — skip if already sent this email_number
                    try:
                        existing = await sb_execute(
                            sb.table("trial_email_log")
                            .select("id")
                            .eq("user_id", user_id)
                            .eq("email_number", email_number)
                            .limit(1)
                        )
                        if existing.data and len(existing.data) > 0:
                            skipped += 1
                            continue
                    except Exception:
                        pass  # If check fails, proceed (better to send than skip)

                    # Collect stats for personalization (AC2)
                    try:
                        stats = get_trial_user_stats(user_id)
                    except Exception:
                        stats = {}

                    # Build unsubscribe URL (AC2)
                    unsub_url = get_unsubscribe_url(user_id)

                    # Render and send email
                    try:
                        subject, html = _render_email(
                            email_type=email_type,
                            user_name=user_name,
                            stats=stats,
                            unsubscribe_url=unsub_url,
                        )

                        # Fire-and-forget send
                        send_email_async(
                            to=email_addr,
                            subject=subject,
                            html=html,
                            tags=[
                                {"name": "category", "value": "trial_sequence"},
                                {"name": "type", "value": email_type},
                                {"name": "email_number", "value": str(email_number)},
                            ],
                        )

                        # Record in log for idempotency (AC6)
                        try:
                            await sb_execute(
                                sb.table("trial_email_log").insert({
                                    "user_id": user_id,
                                    "email_type": email_type,
                                    "email_number": email_number,
                                })
                            )
                        except Exception as log_err:
                            # UNIQUE constraint violation = already sent (race safe)
                            logger.debug(f"trial_email_log insert failed (likely dup): {log_err}")

                        # Prometheus metric
                        try:
                            TRIAL_EMAILS_SENT.labels(type=email_type).inc()
                        except Exception:
                            pass

                        logger.info(
                            "trial_sequence_email_sent",
                            extra={
                                "user_id": user_id[:8] + "***",
                                "email_type": email_type,
                                "email_number": email_number,
                                "day": day,
                            },
                        )
                        sent += 1

                    except Exception as render_err:
                        errors += 1
                        logger.error(
                            f"Failed to send trial email #{email_number} "
                            f"({email_type}) to {user_id[:8]}***: {render_err}"
                        )

            except Exception as milestone_err:
                errors += 1
                logger.error(f"Failed to process trial email #{email_number} day={day}: {milestone_err}")

        logger.info(
            f"Trial email sequence: sent={sent}, skipped={skipped}, "
            f"converted_skipped={converted_skipped}, "
            f"unsubscribed_skipped={unsubscribed_skipped}, errors={errors}"
        )
        return {
            "sent": sent,
            "skipped": skipped,
            "errors": errors,
            "converted_skipped": converted_skipped,
            "unsubscribed_skipped": unsubscribed_skipped,
        }

    except Exception as e:
        # SHIP-003 AC6: Downgrade to warning for connection/CB errors (don't abort batch)
        err_name = type(e).__name__
        err_str = str(e)
        if "CircuitBreaker" in err_name or "ConnectionError" in err_name or "ConnectError" in err_str:
            logger.warning("Trial email sequence skipped (DB unavailable): %s", e)
        else:
            logger.error(f"Trial email sequence failed: {e}", exc_info=True)
        return {"sent": 0, "skipped": 0, "errors": 1, "error": str(e)}


def _render_email(
    email_type: str,
    user_name: str,
    stats: dict,
    unsubscribe_url: str = "",
) -> tuple[str, str]:
    """Render the appropriate email template for the given type.

    Returns:
        tuple of (subject, html)
    """
    from templates.emails.trial import (
        render_trial_welcome_email,
        render_trial_engagement_email,
        render_trial_paywall_alert_email,
        render_trial_value_email,
        render_trial_last_day_email,
        render_trial_expired_email,
        _format_brl,
    )

    value = stats.get("total_value_estimated", 0.0)
    opps = stats.get("opportunities_found", 0)
    pipeline = stats.get("pipeline_items_count", 0)

    if email_type == "welcome":
        subject = "Bem-vindo ao SmartLic — seu trial de 14 dias comecou!"
        html = render_trial_welcome_email(user_name, unsubscribe_url=unsubscribe_url)

    elif email_type == "engagement":
        if value > 0:
            subject = f"Voce ja analisou {_format_brl(value)} em oportunidades"
        else:
            subject = "Descubra as oportunidades que esperam por voce"
        html = render_trial_engagement_email(user_name, stats, unsubscribe_url=unsubscribe_url)

    elif email_type == "paywall_alert":
        subject = "Metade do trial — a partir de amanha, preview limitado"
        html = render_trial_paywall_alert_email(user_name, stats, unsubscribe_url=unsubscribe_url)

    elif email_type == "value":
        if value > 0:
            subject = f"Voce ja analisou {_format_brl(value)} — nao perca esse progresso"
        elif opps > 0:
            subject = f"{opps} oportunidades encontradas — nao perca"
        else:
            subject = "Restam 4 dias no seu trial SmartLic"
        html = render_trial_value_email(user_name, stats, unsubscribe_url=unsubscribe_url)

    elif email_type == "last_day":
        subject = "Amanha seu acesso expira — assine agora"
        html = render_trial_last_day_email(user_name, stats, unsubscribe_url=unsubscribe_url)

    elif email_type == "expired":
        count = pipeline if pipeline > 0 else opps
        if count > 0:
            subject = f"Suas {count} oportunidades estao esperando — volte com 20% off"
        else:
            subject = "Sentimos sua falta — volte com 20% off"
        coupon_url = get_coupon_checkout_url()
        html = render_trial_expired_email(
            user_name, stats,
            unsubscribe_url=unsubscribe_url,
            coupon_checkout_url=coupon_url,
        )

    else:
        raise ValueError(f"Unknown email type: {email_type}")

    return subject, html


# ============================================================================
# AC11: Resend webhook handler for opens/clicks
# ============================================================================

async def handle_resend_webhook(event_type: str, data: dict) -> bool:
    """AC11: Process Resend webhook for email open/click tracking.

    Args:
        event_type: Resend event type (e.g., "email.opened", "email.clicked")
        data: Webhook payload data

    Returns:
        True if processed, False if skipped/error
    """
    try:
        from supabase_client import get_supabase, sb_execute

        email_id = data.get("email_id")
        if not email_id:
            return False

        sb = get_supabase()
        now = datetime.now(timezone.utc).isoformat()

        if event_type == "email.opened":
            await sb_execute(
                sb.table("trial_email_log")
                .update({"opened_at": now})
                .eq("resend_email_id", email_id)
                .is_("opened_at", "null")
            )
            return True

        elif event_type == "email.clicked":
            await sb_execute(
                sb.table("trial_email_log")
                .update({"clicked_at": now})
                .eq("resend_email_id", email_id)
                .is_("clicked_at", "null")
            )
            return True

        return False

    except Exception as e:
        logger.error(f"Resend webhook processing error: {e}")
        return False
