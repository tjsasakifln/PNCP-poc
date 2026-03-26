"""
STORY-309 AC1: Dunning email sequence service.

Sends escalating emails based on Stripe attempt_count:
- Attempt 1 (day 0):  Friendly "Isso acontece"
- Attempt 2 (day 3):  Gentle reminder "Ação necessária"
- Attempt 3 (day 7):  Urgent "Sua assinatura está em risco"
- Attempt 4 (day 14): Final warning "Aviso final"

Also handles:
- Recovery email when payment succeeds after dunning
- Pre-dunning email 7 days before card expiry
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from email_service import send_email_async
from log_sanitizer import get_sanitized_logger, mask_user_id
from metrics import (
    DUNNING_EMAILS_SENT,
    DUNNING_RECOVERY,
    PAYMENT_FAILURE,
)
from quota import PLAN_NAMES
from supabase_client import get_supabase
from templates.emails.base import FRONTEND_URL
from templates.emails.dunning import (
    render_dunning_final_email,
    render_dunning_friendly_email,
    render_dunning_reminder_email,
    render_dunning_urgent_email,
    render_pre_dunning_email,
    render_dunning_recovery_email,
)

logger = get_sanitized_logger(__name__)

# Billing portal redirect URL — generates a Stripe-hosted portal session
BILLING_PORTAL_URL = f"{FRONTEND_URL}/api/billing-portal"

# Days-remaining estimates for each Stripe attempt (approximate, for email copy).
# Stripe retries at day 0, 3, 7, 14 by default (Smart Retries may vary).
# We map attempt_count to remaining days within the 21-day dunning window.
_DAYS_REMAINING_BY_ATTEMPT: dict[int, int] = {
    1: 21,  # Day 0: full 21 days remaining
    2: 18,  # Day 3: ~18 days remaining
    3: 14,  # Day 7: 14 days remaining
    4: 7,   # Day 14: ~7 days remaining
}

# Email subjects per attempt number
_SUBJECTS: dict[int, str] = {
    1: "Isso acontece — atualize seu pagamento",
    2: "Ação necessária: pagamento pendente",
    3: "Sua assinatura está em risco",
    4: "Aviso final — sua assinatura será cancelada",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _format_amount(invoice_data: dict) -> str:
    """Extract and format invoice amount as 'R$ X.XXX,XX'."""
    # Stripe stores amounts in centavos (smallest currency unit)
    amount_cents = invoice_data.get("amount_due", 0) or 0
    try:
        amount_brl = int(amount_cents) / 100
        # Brazilian formatting: period as thousands separator, comma as decimal
        formatted = f"R$ {amount_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except (TypeError, ValueError):
        return "R$ --"


def _extract_failure_reason(invoice_data: dict) -> str:
    """Extract human-readable failure reason from invoice charge data."""
    # Stripe invoice may nest charge -> failure_message
    charge = invoice_data.get("charge") or {}
    if isinstance(charge, dict):
        reason = charge.get("failure_message", "")
        if reason:
            return reason
    # Fallback: look at last_payment_error on payment_intent
    payment_intent = invoice_data.get("payment_intent") or {}
    if isinstance(payment_intent, dict):
        last_error = payment_intent.get("last_payment_error") or {}
        if isinstance(last_error, dict):
            return last_error.get("message", "Falha no processamento")
    return "Falha no processamento do cartão"


async def _fetch_user_profile(user_id: str, db=None) -> Optional[dict]:
    """Fetch email and full_name for a user from the profiles table.

    Returns dict with keys 'email' and 'full_name', or None on failure.
    """
    try:
        if db is None:
            db = get_supabase()
        result = (
            db.table("profiles")
            .select("email, full_name")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
        logger.warning(
            "dunning_profile_not_found",
            extra={"user_id": mask_user_id(user_id)},
        )
        return None
    except Exception as exc:
        logger.warning(
            "dunning_profile_fetch_error",
            extra={
                "user_id": mask_user_id(user_id),
                "error": str(exc),
            },
        )
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def send_dunning_email(
    user_id: str,
    attempt_count: int,
    invoice_data: dict,
    decline_type: str = "soft",
) -> None:
    """Send the appropriate dunning email based on payment attempt number.

    Maps attempt_count → email template:
        1 → Friendly   "Isso acontece"
        2 → Reminder   "Ação necessária"
        3 → Urgent     "Sua assinatura está em risco"
        4 → Final      "Aviso final"
        5+ → reuses final template (Stripe may retry beyond 4)

    Args:
        user_id:       Supabase auth user ID.
        attempt_count: Stripe invoice attempt_count (1-based).
        invoice_data:  Stripe Invoice object serialised as dict.
        decline_type:  "soft" or "hard" — from Stripe charge outcome.

    Never raises — all exceptions are caught and logged as warnings.
    """
    try:
        profile = await _fetch_user_profile(user_id)
        if not profile:
            return

        email = profile.get("email", "")
        full_name = profile.get("full_name") or email.split("@")[0]

        plan_id = invoice_data.get("metadata", {}).get("plan_id", "") or ""
        plan_name = PLAN_NAMES.get(plan_id, "SmartLic Pro")
        amount = _format_amount(invoice_data)
        failure_reason = _extract_failure_reason(invoice_data)
        days_remaining = _DAYS_REMAINING_BY_ATTEMPT.get(
            attempt_count,
            _DAYS_REMAINING_BY_ATTEMPT[4],  # cap at attempt 4 behaviour
        )
        days_since_failure = get_days_since_failure(user_id) or 0

        # Select template renderer and subject
        normalized_attempt = min(attempt_count, 4)
        subject = _SUBJECTS.get(normalized_attempt, _SUBJECTS[4])

        # Each template has a different signature — call explicitly
        if normalized_attempt == 1:
            html = render_dunning_friendly_email(
                user_name=full_name,
                plan_name=plan_name,
                amount=amount,
                failure_reason=failure_reason,
                billing_portal_url=BILLING_PORTAL_URL,
            )
        elif normalized_attempt == 2:
            html = render_dunning_reminder_email(
                user_name=full_name,
                plan_name=plan_name,
                amount=amount,
                days_remaining=days_remaining,
                billing_portal_url=BILLING_PORTAL_URL,
            )
        elif normalized_attempt == 3:
            html = render_dunning_urgent_email(
                user_name=full_name,
                plan_name=plan_name,
                amount=amount,
                days_remaining=days_remaining,
                billing_portal_url=BILLING_PORTAL_URL,
            )
        else:  # 4+
            html = render_dunning_final_email(
                user_name=full_name,
                plan_name=plan_name,
                amount=amount,
                billing_portal_url=BILLING_PORTAL_URL,
            )

        tags = [
            {"name": "category", "value": "dunning"},
            {"name": "email_number", "value": str(attempt_count)},
        ]

        send_email_async(to=email, subject=subject, html=html, tags=tags)

        # Prometheus metric
        DUNNING_EMAILS_SENT.labels(
            email_number=str(attempt_count),
            plan_type=plan_id or "unknown",
        ).inc()

        # Increment PAYMENT_FAILURE counter on first attempt
        if attempt_count == 1:
            # Extract decline_code from charge data
            charge = invoice_data.get("charge") or {}
            decline_code = "unknown"
            if isinstance(charge, dict):
                decline_code = charge.get("decline_code") or charge.get("failure_code") or "unknown"
            PAYMENT_FAILURE.labels(
                decline_type=decline_type,
                decline_code=decline_code,
            ).inc()

        logger.info(
            "dunning_email_sent",
            extra={
                "user_id": mask_user_id(user_id),
                "plan_type": plan_id,
                "attempt_count": attempt_count,
                "decline_type": decline_type,
                "days_since_failure": days_since_failure,
            },
        )

    except Exception as exc:
        logger.warning(
            "dunning_email_send_failed",
            extra={
                "user_id": mask_user_id(user_id),
                "attempt_count": attempt_count,
                "error": str(exc),
            },
        )


async def send_recovery_email(user_id: str, plan_id: str) -> None:
    """Send a payment recovery confirmation email after successful charge.

    Called when Stripe fires `invoice.payment_succeeded` following prior
    dunning attempts, indicating the user resolved the payment issue.

    Args:
        user_id: Supabase auth user ID.
        plan_id: Active plan ID used to display the plan name.

    Never raises.
    """
    try:
        profile = await _fetch_user_profile(user_id)
        if not profile:
            return

        email = profile.get("email", "")
        full_name = profile.get("full_name") or email.split("@")[0]
        plan_name = PLAN_NAMES.get(plan_id, "SmartLic Pro")

        html = render_dunning_recovery_email(
            user_name=full_name,
            plan_name=plan_name,
        )

        tags = [
            {"name": "category", "value": "dunning"},
            {"name": "email_type", "value": "recovery"},
        ]

        send_email_async(
            to=email,
            subject="Pagamento processado — bem-vindo de volta!",
            html=html,
            tags=tags,
        )

        DUNNING_RECOVERY.labels(recovered_via="webhook").inc()

        logger.info(
            "dunning_recovery_email_sent",
            extra={
                "user_id": mask_user_id(user_id),
                "plan_type": plan_id,
            },
        )

    except Exception as exc:
        logger.warning(
            "dunning_recovery_email_failed",
            extra={
                "user_id": mask_user_id(user_id),
                "error": str(exc),
            },
        )


async def send_pre_dunning_email(
    user_id: str,
    card_last4: str,
    card_exp_month: int,
    card_exp_year: int,
) -> None:
    """Send a proactive card-expiry warning email 7 days before card expires.

    This fires before a payment failure occurs, giving the user time to
    update their payment method without entering the dunning sequence.

    Args:
        user_id:        Supabase auth user ID.
        card_last4:     Last 4 digits of the card (display only).
        card_exp_month: Card expiry month (1-12).
        card_exp_year:  Card expiry year (e.g. 2026).

    Never raises.
    """
    try:
        profile = await _fetch_user_profile(user_id)
        if not profile:
            return

        email = profile.get("email", "")
        full_name = profile.get("full_name") or email.split("@")[0]

        html = render_pre_dunning_email(
            user_name=full_name,
            card_last4=card_last4,
            card_exp_month=card_exp_month,
            card_exp_year=card_exp_year,
            billing_portal_url=BILLING_PORTAL_URL,
        )

        tags = [
            {"name": "category", "value": "dunning"},
            {"name": "email_type", "value": "pre_dunning"},
        ]

        send_email_async(
            to=email,
            subject="Seu cartão expira em breve — atualize agora",
            html=html,
            tags=tags,
        )

        logger.info(
            "pre_dunning_email_sent",
            extra={
                "user_id": mask_user_id(user_id),
                "card_last4": card_last4,
                "card_exp_month": card_exp_month,
                "card_exp_year": card_exp_year,
            },
        )

    except Exception as exc:
        logger.warning(
            "pre_dunning_email_failed",
            extra={
                "user_id": mask_user_id(user_id),
                "error": str(exc),
            },
        )


def get_days_since_failure(user_id: str, db=None) -> Optional[int]:
    """Return the number of days since the first payment failure for a user.

    Queries ``user_subscriptions.first_failed_at`` for the user's active
    subscription.  Returns ``None`` if no failure has been recorded, or if
    the query fails.

    Args:
        user_id: Supabase auth user ID.
        db:      Supabase client (fetched lazily if not supplied).

    Returns:
        Integer days >= 0, or None.
    """
    try:
        if db is None:
            db = get_supabase()

        result = (
            db.table("user_subscriptions")
            .select("first_failed_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )

        if not result.data:
            return None

        first_failed_at_raw = result.data[0].get("first_failed_at")
        if not first_failed_at_raw:
            return None

        # Parse ISO-8601 timestamp (Supabase always returns UTC)
        first_failed_at = datetime.fromisoformat(
            str(first_failed_at_raw).replace("Z", "+00:00")
        )
        now = datetime.now(timezone.utc)
        delta = now - first_failed_at
        return max(0, delta.days)

    except Exception as exc:
        logger.warning(
            "dunning_days_since_failure_error",
            extra={
                "user_id": mask_user_id(user_id),
                "error": str(exc),
            },
        )
        return None


def get_dunning_phase(days_since_failure: Optional[int]) -> str:
    """Classify the user's dunning phase based on days since first failure.

    Phases control access restrictions in the quota layer:

        "healthy"        — No failure recorded (days_since_failure is None).
        "active_retries" — 0–13 days: full access, Stripe still retrying.
        "grace_period"   — 14–20 days: read-only access (view pipeline, etc.).
        "blocked"        — 21+ days: access blocked until payment or cancellation.

    Args:
        days_since_failure: Output of :func:`get_days_since_failure`, or None.

    Returns:
        One of: "healthy", "active_retries", "grace_period", "blocked".
    """
    if days_since_failure is None:
        return "healthy"
    if days_since_failure < 14:
        return "active_retries"
    if days_since_failure < 21:
        return "grace_period"
    return "blocked"
