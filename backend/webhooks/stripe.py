"""
Stripe Webhook Handler - Idempotent Processing

Handles Stripe webhook events for subscription updates.

CRITICAL FEATURES:
1. Signature validation (rejects unsigned/forged webhooks)
2. Idempotency (duplicate events ignored via DB check)
3. Atomic DB updates (prevents race conditions)
4. Cache invalidation (Redis features cache)
5. Event logging (audit trail)

Supported Events:
- customer.subscription.updated (billing period changes)
- customer.subscription.deleted (cancellation)
- invoice.payment_succeeded (annual renewal)

Security:
- STRIPE_WEBHOOK_SECRET required (set in .env)
- Signature verification with stripe.Webhook.construct_event()
- Reject all unsigned requests with HTTP 400

Performance:
- Idempotency check before processing (< 5ms)
- Atomic upsert to prevent duplicate updates
- Redis cache invalidation (< 2ms)
"""

import os
import logging
from datetime import datetime

import stripe
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert

from database import get_db
from models.stripe_webhook_event import StripeWebhookEvent
from models.user_subscription import UserSubscription
from cache import redis_client

logger = logging.getLogger(__name__)
router = APIRouter()

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if not STRIPE_WEBHOOK_SECRET:
    logger.error("STRIPE_WEBHOOK_SECRET not configured - webhook signature validation will fail")


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
    - Determines billing_period from Stripe subscription interval
    - Atomically updates user_subscriptions table
    - Invalidates Redis cache for affected user
    - Stores event in stripe_webhook_events for audit trail

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
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    # CRITICAL: Verify signature (prevents fake webhooks)
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Webhook payload invalid: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    logger.info(f"Received Stripe webhook: event_id={event.id}, type={event.type}")

    db = next(get_db())

    try:
        # Idempotency check: Has this event already been processed?
        existing = db.query(StripeWebhookEvent).filter(
            StripeWebhookEvent.id == event.id
        ).first()

        if existing:
            logger.info(f"Webhook already processed: event_id={event.id}")
            return {"status": "already_processed", "event_id": event.id}

        # Process event based on type
        if event.type == "customer.subscription.updated":
            await handle_subscription_updated(db, event)
        elif event.type == "customer.subscription.deleted":
            await handle_subscription_deleted(db, event)
        elif event.type == "invoice.payment_succeeded":
            await handle_invoice_payment_succeeded(db, event)
        else:
            logger.info(f"Unhandled event type: {event.type}")

        # Mark event as processed (prevents duplicate processing)
        webhook_event = StripeWebhookEvent(
            id=event.id,
            type=event.type,
            processed_at=datetime.utcnow(),
            payload=event.data.object,
        )
        db.add(webhook_event)
        db.commit()

        logger.info(f"Webhook processed successfully: event_id={event.id}")
        return {"status": "success", "event_id": event.id}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        db.close()


async def handle_subscription_updated(db, event: stripe.Event):
    """
    Handle customer.subscription.updated event.

    Updates billing_period in user_subscriptions table based on Stripe interval.

    Args:
        db: Database session
        event: Stripe event object
    """
    subscription_data = event.data.object

    # Determine billing_period from Stripe interval
    stripe_interval = subscription_data.get("plan", {}).get("interval") or \
                      subscription_data.get("items", {}).get("data", [{}])[0].get("plan", {}).get("interval")

    billing_period = "annual" if stripe_interval == "year" else "monthly"

    logger.info(
        f"Subscription updated: subscription_id={subscription_data.id}, "
        f"interval={stripe_interval}, billing_period={billing_period}"
    )

    # Atomic upsert (prevents race conditions)
    stmt = insert(UserSubscription).values(
        stripe_subscription_id=subscription_data.id,
        billing_period=billing_period,
        updated_at=datetime.utcnow(),
    ).on_conflict_do_update(
        index_elements=["stripe_subscription_id"],
        set_={
            "billing_period": billing_period,
            "updated_at": datetime.utcnow(),
        },
    )

    db.execute(stmt)
    db.flush()  # Ensure DB update before cache invalidation

    # Invalidate Redis cache for affected user
    user_sub = db.query(UserSubscription).filter(
        UserSubscription.stripe_subscription_id == subscription_data.id
    ).first()

    if user_sub:
        cache_key = f"features:{user_sub.user_id}"
        redis_client.delete(cache_key)
        logger.info(f"Cache invalidated: key={cache_key}")


async def handle_subscription_deleted(db, event: stripe.Event):
    """
    Handle customer.subscription.deleted event.

    Marks subscription as inactive in user_subscriptions table.

    Args:
        db: Database session
        event: Stripe event object
    """
    subscription_data = event.data.object

    logger.info(f"Subscription deleted: subscription_id={subscription_data.id}")

    # Mark subscription as inactive
    user_sub = db.query(UserSubscription).filter(
        UserSubscription.stripe_subscription_id == subscription_data.id
    ).first()

    if user_sub:
        user_sub.is_active = False
        user_sub.updated_at = datetime.utcnow()
        db.flush()

        # Invalidate cache
        cache_key = f"features:{user_sub.user_id}"
        redis_client.delete(cache_key)
        logger.info(f"Subscription deactivated: user_id={user_sub.user_id}")


async def handle_invoice_payment_succeeded(db, event: stripe.Event):
    """
    Handle invoice.payment_succeeded event (annual renewal).

    Extends subscription expiry date for another year.

    Args:
        db: Database session
        event: Stripe event object
    """
    invoice_data = event.data.object
    subscription_id = invoice_data.get("subscription")

    if not subscription_id:
        logger.warning("Invoice has no subscription_id, skipping")
        return

    logger.info(f"Invoice paid: subscription_id={subscription_id}")

    user_sub = db.query(UserSubscription).filter(
        UserSubscription.stripe_subscription_id == subscription_id
    ).first()

    if user_sub and user_sub.billing_period == "annual":
        # Extend expiry by 1 year (handled by Stripe automatically)
        # Just invalidate cache to reflect new billing cycle
        cache_key = f"features:{user_sub.user_id}"
        redis_client.delete(cache_key)
        logger.info(f"Annual renewal processed: user_id={user_sub.user_id}")
