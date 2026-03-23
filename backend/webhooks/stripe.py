"""
Stripe Webhook Dispatcher — Thin Router (DEBT-307 Decomposition)

Validates signature, checks idempotency, routes to handler modules.

Handler logic lives in webhooks/handlers/:
- checkout.py: checkout.session.completed, async_payment_succeeded/failed
- subscription.py: customer.subscription.updated/deleted
- invoice.py: invoice.payment_succeeded/failed, payment_action_required

CRITICAL FEATURES:
1. Signature validation (rejects unsigned/forged webhooks)
2. Idempotency (duplicate events ignored via DB check)
3. Timeout protection (SYS-024: 30s asyncio.wait_for)
4. Event logging (audit trail in stripe_webhook_events)
5. Stuck event recovery (>5min reprocessing)

BACKWARD COMPATIBILITY:
All handler functions are re-exported here so existing tests that patch
`webhooks.stripe._handle_*` or `webhooks.stripe.redis_cache` continue to work.
"""

import asyncio
import os
from datetime import datetime, timezone, timedelta

import stripe
from fastapi import APIRouter, Request, HTTPException

from supabase_client import get_supabase
from cache import redis_cache  # noqa: F401 — re-exported for test patches
from log_sanitizer import get_sanitized_logger
from quota import invalidate_plan_status_cache, clear_plan_capabilities_cache  # noqa: F401

# Re-export handler functions for backward compatibility with test patches.
# Tests do: @patch('webhooks.stripe._handle_checkout_session_completed')
# This works because Python patches the NAME in THIS module's namespace.
from webhooks.handlers.checkout import (  # noqa: F401
    handle_checkout_session_completed as _handle_checkout_session_completed,
    handle_async_payment_succeeded as _handle_async_payment_succeeded,
    handle_async_payment_failed as _handle_async_payment_failed,
    _send_async_payment_failed_email,
    _create_partner_referral_async,
)
from webhooks.handlers.subscription import (  # noqa: F401
    handle_subscription_updated as _handle_subscription_updated,
    handle_subscription_deleted as _handle_subscription_deleted,
    _mark_partner_referral_churned,
    _send_cancellation_email,
)
from webhooks.handlers.invoice import (  # noqa: F401
    handle_invoice_payment_succeeded as _handle_invoice_payment_succeeded,
    handle_invoice_payment_failed as _handle_invoice_payment_failed,
    handle_payment_action_required as _handle_payment_action_required,
    _send_payment_confirmation_email,
    _send_payment_action_required_email,
    _send_payment_failed_email,
)
from webhooks.handlers._shared import resolve_user_id as _resolve_user_id  # noqa: F401

logger = get_sanitized_logger(__name__)
router = APIRouter()

# Stripe configuration
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# SYS-024: Timeout for webhook event processing (seconds)
WEBHOOK_DB_TIMEOUT_S = 30

if not STRIPE_WEBHOOK_SECRET:
    logger.error(
        "STRIPE_WEBHOOK_SECRET not configured — webhook signature validation will fail. "
        "Set STRIPE_WEBHOOK_SECRET in .env (get from Stripe Dashboard > Developers > Webhooks > Signing secret)"
    )


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events with idempotency and signature validation.

    Security:
    - Verifies Stripe signature to prevent fake webhooks
    - Rejects unsigned/invalid requests with HTTP 400

    Idempotency:
    - Checks stripe_webhook_events table for duplicate event IDs
    - Returns "already_processed" for duplicate webhooks

    Processing:
    - Routes to handler in webhooks/handlers/ based on event.type
    - Wraps in asyncio.wait_for() with 30s timeout (SYS-024)
    - Marks event status in stripe_webhook_events for audit trail

    Args:
        request: FastAPI Request object with Stripe event payload

    Returns:
        dict: {"status": "success"} or {"status": "already_processed"}

    Raises:
        HTTPException 400: Invalid payload or signature verification failed
        HTTPException 500: Database error during processing
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        logger.warning("Webhook rejected: Missing stripe-signature header")
        raise HTTPException(status_code=400, detail="Assinatura de webhook inválida")

    # CRITICAL: Verify signature (prevents fake webhooks)
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Webhook payload invalid: {e}")
        raise HTTPException(status_code=400, detail="Dados de webhook inválidos")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Assinatura de webhook inválida")

    logger.info(f"Received Stripe webhook: event_id={event.id}, type={event.type}")

    sb = get_supabase()

    try:
        # STORY-307 AC1: Atomic idempotency — INSERT ON CONFLICT DO NOTHING
        now = datetime.now(timezone.utc)
        claim_result = sb.table("stripe_webhook_events").upsert(
            {
                "id": event.id,
                "type": event.type,
                "status": "processing",
                "received_at": now.isoformat(),
            },
            on_conflict="id",
            ignore_duplicates=True,
        ).execute()

        # If upsert returned no data, the event already exists
        if not claim_result.data:
            # AC6: Check if event is stuck in 'processing' for >5 minutes
            stuck_check = (
                sb.table("stripe_webhook_events")
                .select("id, status, received_at")
                .eq("id", event.id)
                .limit(1)
                .execute()
            )
            if stuck_check.data:
                existing = stuck_check.data[0]
                if existing.get("status") == "processing" and existing.get("received_at"):
                    received_at = datetime.fromisoformat(
                        existing["received_at"].replace("Z", "+00:00")
                    )
                    if (now - received_at) > timedelta(minutes=5):
                        # AC7: Log WARNING and allow reprocessing
                        logger.warning(
                            f"Stripe webhook {event.id} stuck in processing "
                            f"for >5min — reprocessing"
                        )
                        sb.table("stripe_webhook_events").update({
                            "status": "processing",
                            "received_at": now.isoformat(),
                        }).eq("id", event.id).execute()
                    else:
                        logger.info(f"Webhook already processing: event_id={event.id}")
                        return {"status": "already_processed", "event_id": event.id}
                else:
                    logger.info(f"Webhook already processed: event_id={event.id}")
                    return {"status": "already_processed", "event_id": event.id}

        # SYS-024: Wrap event routing in asyncio.wait_for() to prevent DB hangs
        # NOTE: References module-level names so @patch('webhooks.stripe._handle_*') works
        async def _process_event():
            """Route event to appropriate handler."""
            if event.type == "checkout.session.completed":
                await _handle_checkout_session_completed(sb, event)
            elif event.type == "checkout.session.async_payment_succeeded":
                await _handle_async_payment_succeeded(sb, event)
            elif event.type == "checkout.session.async_payment_failed":
                await _handle_async_payment_failed(sb, event)
            elif event.type == "customer.subscription.updated":
                await _handle_subscription_updated(sb, event)
            elif event.type == "customer.subscription.deleted":
                await _handle_subscription_deleted(sb, event)
            elif event.type == "invoice.payment_succeeded":
                await _handle_invoice_payment_succeeded(sb, event)
            elif event.type == "invoice.payment_failed":
                await _handle_invoice_payment_failed(sb, event)
            elif event.type == "invoice.payment_action_required":
                await _handle_payment_action_required(sb, event)
            else:
                logger.info(f"Unhandled event type: {event.type}")

        try:
            await asyncio.wait_for(_process_event(), timeout=WEBHOOK_DB_TIMEOUT_S)
        except asyncio.TimeoutError:
            logger.error(
                f"Webhook processing timed out after {WEBHOOK_DB_TIMEOUT_S}s: "
                f"event_id={event.id}, type={event.type}"
            )
            try:
                sb.table("stripe_webhook_events").update({
                    "status": "timeout",
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "payload": {"error": f"Processing timed out after {WEBHOOK_DB_TIMEOUT_S}s"},
                }).eq("id", event.id).execute()
            except Exception:
                pass
            raise HTTPException(status_code=504, detail="Webhook processing timed out")

        # AC2: Mark event as completed after successful processing
        sb.table("stripe_webhook_events").update({
            "status": "completed",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "payload": event.data.object,
        }).eq("id", event.id).execute()

        logger.info(f"Webhook processed successfully: event_id={event.id}")
        return {"status": "success", "event_id": event.id}

    except HTTPException:
        raise
    except Exception as e:
        # AC3: Mark event as failed on processing error
        try:
            sb.table("stripe_webhook_events").update({
                "status": "failed",
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "payload": {"error": str(e)},
            }).eq("id", event.id).execute()
        except Exception as update_err:
            logger.error(f"Failed to mark webhook as failed: {update_err}")
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error")
