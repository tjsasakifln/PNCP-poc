"""STORY-BIZ-001: side-effect handlers that keep `founding_leads` in sync with
Stripe checkout-session lifecycle events.

Invoked from `webhooks.handlers.checkout.handle_checkout_session_completed`
and from the webhook dispatcher in `webhooks.stripe` when session metadata
contains `source='founding'`. Keeping the founding logic isolated lets the
main checkout handler stay readable and lets us unit-test the founding
bookkeeping in isolation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from log_sanitizer import get_sanitized_logger

logger = get_sanitized_logger(__name__)


def _is_founding_session(session: Any) -> bool:
    """Return True if the checkout session originated from /founding landing."""
    metadata = (session.get("metadata") or {}) if hasattr(session, "get") else {}
    return metadata.get("source") == "founding"


def _session_id(session: Any) -> str | None:
    sid = session.get("id") if hasattr(session, "get") else None
    return str(sid) if sid else None


def mark_founding_lead_completed(sb, session: Any) -> None:
    """Update founding_leads row when Stripe confirms checkout completion.

    Idempotent: if no row matches the session id, logs a warning and returns.
    Silent on DB errors so it never breaks the main checkout flow.
    """
    if not _is_founding_session(session):
        return

    sid = _session_id(session)
    if not sid:
        logger.warning("Founding completed event missing session id — skipping")
        return

    payload = {
        "checkout_status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "stripe_customer_id": session.get("customer"),
    }

    try:
        result = (
            sb.table("founding_leads")
            .update(payload)
            .eq("checkout_session_id", sid)
            .execute()
        )
        updated = len(result.data or [])
        if updated == 0:
            logger.warning(
                f"Founding lead row not found for session_id={sid} — Stripe fired "
                f"completed before our backend persisted the lead. Metadata may be missing."
            )
        else:
            logger.info(f"Founding lead marked completed: session_id={sid} rows={updated}")
    except Exception as e:
        logger.error(f"Failed to mark founding lead completed: session_id={sid} err={e}")


def mark_founding_lead_abandoned(sb, session: Any) -> None:
    """Update founding_leads when Stripe times out / abandons the session."""
    if not _is_founding_session(session):
        return

    sid = _session_id(session)
    if not sid:
        logger.warning("Founding expired event missing session id — skipping")
        return

    try:
        result = (
            sb.table("founding_leads")
            .update({"checkout_status": "abandoned"})
            .eq("checkout_session_id", sid)
            .eq("checkout_status", "pending")
            .execute()
        )
        updated = len(result.data or [])
        logger.info(f"Founding lead marked abandoned: session_id={sid} rows={updated}")
    except Exception as e:
        logger.error(f"Failed to mark founding lead abandoned: session_id={sid} err={e}")
