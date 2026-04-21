"""
STORY-321 AC1-AC6, AC12-AC14: Trial email sequence — 6 emails over 14 days.

Compressed sequence (replaces STORY-310 8-email sequence):
- Day 0:  Welcome (onboarding CTA)
- Day 3:  Engagement (stats de uso)
- Day 7:  Paywall alert (preview limitado a partir de hoje)
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
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# HMAC secret for unsubscribe tokens (reuses WEBHOOK_SECRET or falls back)
_UNSUBSCRIBE_SECRET = os.getenv("WEBHOOK_SECRET", os.getenv("SECRET_KEY", "smartlic-trial-unsub"))


TIMEZONE_SCHEDULING_ENABLED = os.getenv("TIMEZONE_SCHEDULING_ENABLED", "true").lower() == "true"


def _is_in_send_window(user_tz_str: str, window_start: int = 8, window_end: int = 11) -> bool:
    """Check if current UTC time falls within send window in user's local timezone.

    Default window: 8am-11am local time (covers morning business hours).
    Disabled when TIMEZONE_SCHEDULING_ENABLED=false (e.g., in tests).
    """
    if not TIMEZONE_SCHEDULING_ENABLED:
        return True
    try:
        user_tz = ZoneInfo(user_tz_str or "America/Sao_Paulo")
    except (KeyError, ValueError):
        user_tz = ZoneInfo("America/Sao_Paulo")
    now_local = datetime.now(timezone.utc).astimezone(user_tz)
    return window_start <= now_local.hour < window_end

# ============================================================================
# AC1: Email sequence definition — 6 emails over 14-day trial
# ============================================================================

TRIAL_EMAIL_SEQUENCE = [
    {"number": 1, "day": 0,  "type": "welcome"},
    {"number": 2, "day": 3,  "type": "engagement"},
    {"number": 3, "day": 7,  "type": "paywall_alert"},  # Day 7: paywall ativa HOJE (current_day > 7 = Day 8)
    {"number": 4, "day": 10, "type": "value"},
    {"number": 5, "day": 13, "type": "last_day"},
    {"number": 6, "day": 16, "type": "expired"},
]

# SEO-PLAYBOOK §7.4 / §Day-3 Activation — opt-in extensions to the core
# sequence above. These are appended only when their feature flags are on,
# so toggling them off returns the sequence to its baseline production
# behavior without code changes. Numbers 7/8 are reserved for these.
#
# - referral_invitation (day 8): viral loop activation, sent 1 day after
#   the paywall alert so it doesn't crowd that email in the inbox.
# - activation_nudge (day 2): conditional on stats.searches_count == 0,
#   filtered at dispatch time inside process_trial_emails.
TRIAL_EMAIL_SEQUENCE_OPTIONAL = [
    {"number": 7, "day": 1, "type": "activation_nudge"},
    {"number": 8, "day": 8, "type": "referral_invitation"},
    {"number": 9, "day": 3, "type": "share_activation"},
    {"number": 10, "day": 2, "type": "feature_pipeline"},
    {"number": 11, "day": 5, "type": "feature_excel"},
    {"number": 12, "day": 8, "type": "feature_ai"},
]


def _active_sequence() -> list[dict]:
    """Return the trial email sequence with opt-in entries appended.

    Feature flags are read lazily so tests that monkeypatch config values at
    import time still take effect.
    """
    from config import (
        DAY3_ACTIVATION_EMAIL_ENABLED,
        REFERRAL_EMAIL_ENABLED,
        SHARE_ACTIVATION_EMAIL_ENABLED,
    )

    from config.features import FEATURE_DISCOVERY_EMAILS_ENABLED

    sequence = list(TRIAL_EMAIL_SEQUENCE)
    if DAY3_ACTIVATION_EMAIL_ENABLED:
        sequence.append(
            {"number": 7, "day": 1, "type": "activation_nudge"}
        )
    if REFERRAL_EMAIL_ENABLED:
        sequence.append(
            {"number": 8, "day": 8, "type": "referral_invitation"}
        )
    if SHARE_ACTIVATION_EMAIL_ENABLED:
        sequence.append(
            {"number": 9, "day": 3, "type": "share_activation"}
        )
    if FEATURE_DISCOVERY_EMAILS_ENABLED:
        sequence.extend([
            {"number": 10, "day": 2, "type": "feature_pipeline"},
            {"number": 11, "day": 5, "type": "feature_excel"},
            {"number": 12, "day": 8, "type": "feature_ai"},
        ])
    return sorted(sequence, key=lambda x: x["day"])

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

def _get_top_trial_opportunity(user_id: str) -> dict | None:
    """STORY-371 AC1: Get the highest-value trial opportunity for email personalization."""
    from supabase_client import get_supabase
    from utils.formatters import truncate_text, dias_ate_data, format_brl
    try:
        sb = get_supabase()
        result = (
            sb.table("search_sessions")
            .select("valor_total, top_result_objeto, top_result_orgao, top_result_numero_controle, top_result_data_encerramento")
            .eq("user_id", user_id)
            .gt("valor_total", 0)
            .order("valor_total", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        row = result.data[0]
        valor = float(row.get("valor_total") or 0)
        if valor <= 0:
            return None
        data_enc = row.get("top_result_data_encerramento")
        dias = dias_ate_data(data_enc)
        objeto = truncate_text(row.get("top_result_objeto") or "", 120)
        return {
            "objeto": objeto,
            "orgao_nome": row.get("top_result_orgao") or "",
            "valor_formatado": format_brl(valor),
            "valor": valor,
            "data_encerramento": data_enc,
            "dias_ate_encerramento": dias,
            "numero_controle": row.get("top_result_numero_controle") or "",
        }
    except Exception as e:
        logger.debug(f"Could not fetch top opportunity for email: {e}")
        return None


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
        "top_opportunity": None,  # STORY-371: populated by _get_top_trial_opportunity
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

        for email_def in _active_sequence():
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
                # AC5: Respect unsubscribe preferences (marketing vs conversion)
                # STORY-CONV-003c AC1: include `stripe_default_pm_id` so Day 13
                # dispatch can branch its copy. Users with a payment method in
                # file (rollout branch=card) auto-convert tomorrow without any
                # action; they need a compliance notice + one-click cancel link,
                # not the "your access expires — subscribe now" legacy copy.
                # `created_at` is included to compute the concrete charge date
                # (trial_end = created_at + 14d) displayed to the user.
                users_result = await sb_execute(
                    sb.table("profiles")
                    .select(
                        "id, email, full_name, plan_type, marketing_emails_enabled, "
                        "trial_conversion_emails_enabled, timezone, "
                        "stripe_default_pm_id, created_at"
                    )
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

                    # Zero-Churn P2 §1.2: Only send during user's local business hours (8-11am)
                    # The loop runs every 2h so all timezones are covered within the day
                    user_tz = user.get("timezone") or "America/Sao_Paulo"
                    if not _is_in_send_window(user_tz):
                        # Will be picked up in next cron run (every 2h)
                        skipped += 1
                        continue

                    # AC4: Skip if user has converted (double-check plan_type)
                    plan_type = user.get("plan_type", "")
                    if plan_type != "free_trial":
                        converted_skipped += 1
                        continue

                    # AC5 + P2 §1.2: Differentiate marketing vs conversion emails
                    # Conversion-critical emails: paywall_alert (Day 7), value (Day 10),
                    # last_day (Day 13), expired (Day 16)
                    is_conversion_email = email_type in ("paywall_alert", "value", "last_day", "expired")

                    if is_conversion_email:
                        # Only skip if user explicitly opted out of conversion emails
                        if user.get("trial_conversion_emails_enabled") is False:
                            unsubscribed_skipped += 1
                            continue
                    else:
                        # Marketing/engagement emails — respect marketing preference
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
                        top_opp = _get_top_trial_opportunity(user_id)
                        stats["top_opportunity"] = top_opp
                    except Exception:
                        stats = {}

                    # SEO-PLAYBOOK §Day-3 Activation: the activation nudge is
                    # only valuable for users who have NOT yet searched. If
                    # they already searched, the "aha moment" is ahead of
                    # them — we want the engagement email instead, not this
                    # one. Skip silently (counts as skipped to keep the
                    # batch metric honest).
                    if email_type == "activation_nudge":
                        if stats.get("searches_count", 0) > 0:
                            skipped += 1
                            continue

                    # SEO-PLAYBOOK §7.1 / P6: share activation fires only
                    # when (a) the user has something worth sharing, and
                    # (b) they have not shared anything yet. Both checks
                    # are strict — we never pressure empty trials and we
                    # never re-pressure users who already activated the
                    # viral loop.
                    if email_type == "share_activation":
                        if stats.get("opportunities_found", 0) == 0:
                            skipped += 1
                            continue
                        try:
                            shares = await sb_execute(
                                sb.table("shared_analyses")
                                .select("id")
                                .eq("user_id", user_id)
                                .limit(1)
                            )
                            if shares.data and len(shares.data) > 0:
                                skipped += 1
                                continue
                        except Exception:
                            # On transient DB error, proceed — the
                            # trial_email_log UNIQUE constraint keeps us
                            # idempotent if we re-enter this path later.
                            pass

                    # Pass user_id into stats so _render_email can look up
                    # the referral code for referral_invitation type.
                    if isinstance(stats, dict):
                        stats["user_id"] = user_id

                    # Build unsubscribe URL (AC2)
                    unsub_url = get_unsubscribe_url(user_id)

                    # STORY-CONV-003c AC1: Detect rollout branch via payment
                    # method presence. Users with a card on file (branch=card)
                    # get a compliance-correct copy + one-click cancel link
                    # on Day 13; users without (branch=legacy) keep the
                    # scarcity "assine agora" copy.
                    has_payment_method = bool(user.get("stripe_default_pm_id"))
                    user_created_at = user.get("created_at")

                    # Render and send email
                    try:
                        subject, html = _render_email(
                            email_type=email_type,
                            user_name=user_name,
                            stats=stats,
                            unsubscribe_url=unsub_url,
                            user_id=user_id,
                            has_payment_method=has_payment_method,
                            user_created_at=user_created_at,
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

                        # Record in log for idempotency.
                        # STORY-418 AC5: use upsert ON CONFLICT DO NOTHING instead of
                        # plain insert so duplicate-key violations are handled cleanly
                        # at the SQL level without raising Python exceptions.
                        try:
                            await sb_execute(
                                sb.table("trial_email_log").upsert(
                                    {
                                        "user_id": user_id,
                                        "email_type": email_type,
                                        "email_number": email_number,
                                    },
                                    on_conflict="user_id,email_number",
                                    ignore_duplicates=True,
                                ),
                                category="write",
                            )
                        except Exception as log_err:
                            logger.debug(f"trial_email_log upsert failed: {log_err}")

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
                        # STORY-418: enqueue into the DLQ so the daily
                        # reprocess cron can retry with exponential
                        # backoff. Best-effort — the helper never raises.
                        try:
                            from services.trial_email_dlq import enqueue as _dlq_enqueue

                            await _dlq_enqueue(
                                user_id=user_id,
                                email_address=email_addr,
                                email_type=email_type,
                                email_number=email_number,
                                payload={
                                    "user_name": user_name,
                                    "stats": stats if isinstance(stats, dict) else {},
                                    "day": day,
                                },
                                error=render_err,
                            )
                        except Exception as dlq_err:
                            logger.error(
                                "STORY-418: DLQ enqueue failed for "
                                f"user={user_id[:8]}*** email_type={email_type}: {dlq_err}"
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


def _format_charge_date_display(user_created_at: str | None) -> str:
    """STORY-CONV-003c AC1 helper: human-friendly charge date for the Day 13
    card-branch email. Trial is 14 days from ``created_at``; the charge fires
    on Day 14 = ``created_at + 14d``. Returns e.g. "amanhã, 21/04".

    Falls back to "amanhã" if the timestamp is missing or unparseable — the
    word "amanhã" is the load-bearing piece; the date is garnish.
    """
    if not user_created_at:
        return "amanhã"
    try:
        from config import TRIAL_DURATION_DAYS
    except Exception:
        TRIAL_DURATION_DAYS = 14  # conservative default; never blocks render
    try:
        # Supabase returns ISO 8601 with trailing "Z" or offset. ``fromisoformat``
        # in Python 3.11+ accepts both.
        created_dt = datetime.fromisoformat(user_created_at.replace("Z", "+00:00"))
        charge_dt = created_dt + timedelta(days=TRIAL_DURATION_DAYS)
        return f"amanhã, {charge_dt.strftime('%d/%m')}"
    except Exception:
        return "amanhã"


def _render_email(
    email_type: str,
    user_name: str,
    stats: dict,
    unsubscribe_url: str = "",
    *,
    user_id: str = "",
    has_payment_method: bool = False,
    user_created_at: str | None = None,
) -> tuple[str, str]:
    """Render the appropriate email template for the given type.

    Args:
        email_type: Email type from TRIAL_EMAIL_SEQUENCE (e.g. "welcome").
        user_name: User's display name.
        stats: Dict with trial-usage counters.
        unsubscribe_url: One-click unsubscribe URL (RFC 8058).
        user_id: Supabase user id. Required only when ``email_type=="last_day"``
            and ``has_payment_method`` is True, to mint the cancel-trial JWT.
        has_payment_method: STORY-CONV-003c AC1 — True when
            ``profiles.stripe_default_pm_id`` is set, indicating the user is
            on the card rollout branch and their trial will auto-convert
            tomorrow. Drives the Day 13 copy branch.
        user_created_at: ISO8601 trial start timestamp. Used to compute the
            human-readable charge date for the Day 13 card variant.

    Returns:
        tuple of (subject, html)
    """
    from templates.emails.base import FRONTEND_URL
    from templates.emails.trial import (
        render_trial_welcome_email,
        render_trial_engagement_email,
        render_trial_paywall_alert_email,
        render_trial_value_email,
        render_trial_last_day_email,
        render_trial_last_day_card_email,
        render_trial_expired_email,
        _format_brl,
    )

    value = stats.get("total_value_estimated", 0.0)
    opps = stats.get("opportunities_found", 0)
    pipeline = stats.get("pipeline_items_count", 0)

    # 2C: Compute engagement tier for subject personalization
    tier = "high_value" if stats.get("total_value_estimated", 0) > 100_000 else \
           "active" if stats.get("searches_count", 0) > 0 else "dormant"

    if email_type == "welcome":
        subject = "Bem-vindo ao SmartLic — seu trial de 14 dias comecou!"
        html = render_trial_welcome_email(user_name, unsubscribe_url=unsubscribe_url)

    elif email_type == "engagement":
        if tier == "dormant":
            subject = "Empresas do seu setor estão encontrando oportunidades — e você?"
        elif value > 0:
            subject = f"Voce ja analisou {_format_brl(value)} em oportunidades"
        else:
            subject = "Descubra as oportunidades que esperam por voce"
        html = render_trial_engagement_email(user_name, stats, unsubscribe_url=unsubscribe_url)

    elif email_type == "paywall_alert":
        if value > 0:
            subject = f"Metade do trial — {_format_brl(value)} em oportunidades até agora"
        else:
            subject = "Metade do trial — preview limitado a partir de hoje"
        html = render_trial_paywall_alert_email(user_name, stats, unsubscribe_url=unsubscribe_url)

    elif email_type == "value":
        if tier == "dormant":
            subject = "Milhares de oportunidades publicadas esta semana — descubra as suas"
        elif value > 0:
            subject = f"Voce ja analisou {_format_brl(value)} — nao perca esse progresso"
        elif opps > 0:
            subject = f"{opps} oportunidades encontradas — nao perca"
        else:
            subject = "Restam 4 dias no seu trial SmartLic"
        html = render_trial_value_email(user_name, stats, unsubscribe_url=unsubscribe_url)

    elif email_type == "last_day":
        # STORY-CONV-003c AC1: branch by rollout cohort.
        # - has_payment_method=True (card branch): trial auto-converts
        #   tomorrow. Copy must be compliance-correct (explicit charge
        #   notice + one-click cancel link). Legacy "access expires —
        #   subscribe now" is incorrect for this cohort.
        # - has_payment_method=False (legacy branch): access expires
        #   without any charge. Keep scarcity copy that drives manual
        #   subscription.
        if has_payment_method and user_id:
            try:
                from services.trial_cancel_token import create_cancel_trial_token

                token = create_cancel_trial_token(user_id)
                cancel_url = f"{FRONTEND_URL}/conta/cancelar-trial?token={token}"
            except Exception as token_err:
                # Token minting must not break the send loop. If we cannot
                # mint, fall back to a plain cancel-trial URL (still works
                # via in-app auth) so the email is never blocked.
                logger.warning(
                    "AC1: cancel-trial token mint failed for user=%s***, "
                    "falling back to unauthenticated cancel URL: %s",
                    user_id[:8], token_err,
                )
                cancel_url = f"{FRONTEND_URL}/conta/cancelar-trial"

            charge_date_display = _format_charge_date_display(user_created_at)
            plan_name = "SmartLic Pro"
            amount_display = "R$ 397/mês"

            if value > 0:
                opps = stats.get("opportunities_found", 0) or 0
                if opps > 0:
                    subject = (
                        f"{opps} oportunidades em 14 dias — amanhã vira {plan_name}"
                    )
                else:
                    subject = (
                        f"Amanhã sua trial vira {plan_name} — {amount_display}"
                    )
            else:
                subject = (
                    f"Amanhã sua trial vira {plan_name} — {amount_display}"
                )

            html = render_trial_last_day_card_email(
                user_name=user_name,
                stats=stats,
                charge_date_display=charge_date_display,
                plan_name=plan_name,
                amount_display=amount_display,
                cancel_url=cancel_url,
                unsubscribe_url=unsubscribe_url,
            )
        else:
            if value > 0:
                subject = f"Amanhã você perde acesso a {_format_brl(value)} em oportunidades"
            else:
                subject = "Amanhã seu acesso expira — assine agora"
            html = render_trial_last_day_email(
                user_name, stats, unsubscribe_url=unsubscribe_url
            )

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

    elif email_type == "activation_nudge":
        # SEO-PLAYBOOK §Day-3 Activation — short, action-oriented nudge for
        # users that have not searched yet. Fires on Day 2 of trial.
        from templates.emails.day3_activation import render_day3_activation_email
        subject = "Sua primeira análise está a 30 segundos"
        html = render_day3_activation_email(user_name, unsubscribe_url=unsubscribe_url)

    elif email_type == "share_activation":
        # SEO-PLAYBOOK §7.1 / P6 — Day-3 share activation. Fires when user
        # has analyzed editais but has not shared any analysis yet. Completes
        # the viral loop (analyst → decision maker in the same conversation).
        from templates.emails.share_activation import render_share_activation_email
        subject = "Seu score pode acelerar a decisão do seu diretor"
        html = render_share_activation_email(
            user_name,
            opportunities_found=opps,
            unsubscribe_url=unsubscribe_url,
        )

    elif email_type == "feature_pipeline":
        from templates.emails.trial import render_trial_feature_pipeline_email
        subject = "Organize suas oportunidades no Pipeline"
        html = render_trial_feature_pipeline_email(user_name, stats, unsubscribe_url=unsubscribe_url)

    elif email_type == "feature_excel":
        from templates.emails.trial import render_trial_feature_excel_email
        subject = "Exporte análises para Excel com 1 clique"
        html = render_trial_feature_excel_email(user_name, stats, unsubscribe_url=unsubscribe_url)

    elif email_type == "feature_ai":
        from templates.emails.trial import render_trial_feature_ai_email
        subject = "IA classifica oportunidades para você"
        html = render_trial_feature_ai_email(user_name, stats, unsubscribe_url=unsubscribe_url)

    elif email_type == "referral_invitation":
        # SEO-PLAYBOOK §7.4 — Day-8 viral loop email. Reuses the existing
        # referral_welcome template with the user's actual referral code.
        # We must look up (or lazily generate) their code here since the
        # standard trial stats dict does not include it.
        from templates.emails.referral_welcome import render_referral_welcome_email
        from supabase_client import get_supabase
        try:
            sb_inner = get_supabase()
            existing = (
                sb_inner.table("referrals")
                .select("code")
                .eq("referrer_user_id", stats.get("user_id", ""))
                .limit(1)
                .execute()
            )
            code = (existing.data[0]["code"] if existing.data else "").upper()
        except Exception:
            code = ""

        share_url = f"{FRONTEND_URL}/signup?ref={code}" if code else f"{FRONTEND_URL}/indicar"
        subject = "Você ganha 1 mês grátis por cada amigo que converter"
        html = render_referral_welcome_email(
            user_name=user_name,
            code=code or "—",
            share_url=share_url,
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
