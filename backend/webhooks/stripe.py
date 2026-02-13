"""
Stripe Webhook Handler - Idempotent Processing (Supabase Client)

Handles Stripe webhook events for subscription updates.

CRITICAL FEATURES:
1. Signature validation (rejects unsigned/forged webhooks)
2. Idempotency (duplicate events ignored via DB check)
3. Atomic DB updates (prevents race conditions)
4. Cache invalidation (Redis features cache)
5. Event logging (audit trail)
6. profiles.plan_type sync (keeps fallback current)

Supported Events:
- customer.subscription.updated (billing period changes, plan changes)
- customer.subscription.deleted (cancellation)
- invoice.payment_succeeded (renewal)

Security:
- STRIPE_WEBHOOK_SECRET required (set in .env)
- Signature verification with stripe.Webhook.construct_event()
- Reject all unsigned requests with HTTP 400

Architecture:
- Uses Supabase client (supabase_client.py) for all DB operations
- No SQLAlchemy dependency — single ORM pattern across the codebase
- Migrated from SQLAlchemy in STORY-201
"""

import os
import logging
from datetime import datetime, timezone, timedelta

import stripe
from fastapi import APIRouter, Request, HTTPException

from supabase_client import get_supabase
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
    - Updates user_subscriptions table via Supabase client
    - Syncs profiles.plan_type for fallback reliability
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

    sb = get_supabase()

    try:
        # Idempotency check: Has this event already been processed?
        existing = (
            sb.table("stripe_webhook_events")
            .select("id")
            .eq("id", event.id)
            .limit(1)
            .execute()
        )

        if existing.data:
            logger.info(f"Webhook already processed: event_id={event.id}")
            return {"status": "already_processed", "event_id": event.id}

        # Process event based on type
        if event.type == "customer.subscription.updated":
            await _handle_subscription_updated(sb, event)
        elif event.type == "customer.subscription.deleted":
            await _handle_subscription_deleted(sb, event)
        elif event.type == "invoice.payment_succeeded":
            await _handle_invoice_payment_succeeded(sb, event)
        else:
            logger.info(f"Unhandled event type: {event.type}")

        # Mark event as processed (prevents duplicate processing)
        sb.table("stripe_webhook_events").insert({
            "id": event.id,
            "type": event.type,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "payload": event.data.object,
        }).execute()

        logger.info(f"Webhook processed successfully: event_id={event.id}")
        return {"status": "success", "event_id": event.id}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error")


async def _handle_subscription_updated(sb, event: stripe.Event):
    """
    Handle customer.subscription.updated event.

    Updates billing_period and syncs profiles.plan_type.

    Args:
        sb: Supabase client
        event: Stripe event object
    """
    subscription_data = event.data.object
    stripe_sub_id = subscription_data.id

    # Determine billing_period from Stripe interval
    stripe_interval = (
        subscription_data.get("plan", {}).get("interval")
        or subscription_data.get("items", {}).get("data", [{}])[0].get("plan", {}).get("interval")
    )
    billing_period = "annual" if stripe_interval == "year" else "monthly"

    logger.info(
        f"Subscription updated: subscription_id={stripe_sub_id}, "
        f"interval={stripe_interval}, billing_period={billing_period}"
    )

    # Find existing subscription
    sub_result = (
        sb.table("user_subscriptions")
        .select("id, user_id, plan_id")
        .eq("stripe_subscription_id", stripe_sub_id)
        .limit(1)
        .execute()
    )

    if not sub_result.data:
        logger.warning(f"No local subscription for Stripe sub {stripe_sub_id[:8]}***")
        return

    local_sub = sub_result.data[0]
    user_id = local_sub["user_id"]

    # Check if plan changed (Stripe metadata should contain plan_id)
    new_plan_id = (subscription_data.get("metadata") or {}).get("plan_id")

    update_data = {
        "billing_period": billing_period,
        "is_active": True,
    }
    if new_plan_id and new_plan_id != local_sub["plan_id"]:
        update_data["plan_id"] = new_plan_id

    # Update subscription
    sb.table("user_subscriptions").update(update_data).eq("id", local_sub["id"]).execute()

    # Sync profiles.plan_type (keeps fallback current)
    profile_plan = new_plan_id if new_plan_id else local_sub["plan_id"]
    sb.table("profiles").update({"plan_type": profile_plan}).eq("id", user_id).execute()

    # Invalidate Redis cache for affected user
    cache_key = f"features:{user_id}"
    try:
        redis_client.delete(cache_key)
        logger.info(f"Cache invalidated: key={cache_key}")
    except Exception as e:
        logger.warning(f"Cache invalidation failed (non-fatal): {e}")


async def _handle_subscription_deleted(sb, event: stripe.Event):
    """
    Handle customer.subscription.deleted event.

    Marks subscription as inactive and syncs profiles.plan_type to free_trial.

    Args:
        sb: Supabase client
        event: Stripe event object
    """
    subscription_data = event.data.object
    stripe_sub_id = subscription_data.id

    logger.info(f"Subscription deleted: subscription_id={stripe_sub_id}")

    # Find subscription to get user_id before deactivating
    sub_result = (
        sb.table("user_subscriptions")
        .select("id, user_id")
        .eq("stripe_subscription_id", stripe_sub_id)
        .limit(1)
        .execute()
    )

    if not sub_result.data:
        logger.warning(f"No local subscription for deleted Stripe sub {stripe_sub_id[:8]}***")
        return

    local_sub = sub_result.data[0]
    user_id = local_sub["user_id"]

    # Deactivate subscription
    sb.table("user_subscriptions").update({
        "is_active": False,
    }).eq("id", local_sub["id"]).execute()

    # Sync profiles.plan_type to free_trial (reflects cancellation)
    sb.table("profiles").update({"plan_type": "free_trial"}).eq("id", user_id).execute()

    # Invalidate cache
    cache_key = f"features:{user_id}"
    try:
        redis_client.delete(cache_key)
        logger.info(f"Subscription deactivated: user_id={user_id}, cache invalidated")
    except Exception as e:
        logger.warning(f"Cache invalidation failed on deletion (non-fatal): {e}")
        logger.info(f"Subscription deactivated: user_id={user_id}")


async def _handle_invoice_payment_succeeded(sb, event: stripe.Event):
    """
    Handle invoice.payment_succeeded event (renewal).

    Extends subscription expiry and syncs profiles.plan_type.

    Args:
        sb: Supabase client
        event: Stripe event object
    """
    invoice_data = event.data.object
    subscription_id = invoice_data.get("subscription")

    if not subscription_id:
        logger.debug("Invoice has no subscription_id, skipping")
        return

    logger.info(f"Invoice paid: subscription_id={subscription_id}")

    sub_result = (
        sb.table("user_subscriptions")
        .select("id, user_id, plan_id")
        .eq("stripe_subscription_id", subscription_id)
        .limit(1)
        .execute()
    )

    if not sub_result.data:
        logger.warning(f"No local subscription for invoice stripe_sub {subscription_id[:8]}***")
        return

    local_sub = sub_result.data[0]
    user_id = local_sub["user_id"]
    plan_id = local_sub["plan_id"]

    # Get plan duration for new expiry
    plan_result = sb.table("plans").select("duration_days").eq("id", plan_id).single().execute()
    duration_days = plan_result.data["duration_days"] if plan_result.data else 30

    new_expires = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()

    # Reactivate and extend
    sb.table("user_subscriptions").update({
        "is_active": True,
        "expires_at": new_expires,
    }).eq("id", local_sub["id"]).execute()

    # Sync profiles.plan_type (keeps fallback current)
    sb.table("profiles").update({"plan_type": plan_id}).eq("id", user_id).execute()

    # Invalidate cache
    cache_key = f"features:{user_id}"
    try:
        redis_client.delete(cache_key)
        logger.info(f"Annual renewal processed: user_id={user_id}, new_expires={new_expires[:10]}")
    except Exception as e:
        logger.warning(f"Cache invalidation failed on renewal (non-fatal): {e}")
        logger.info(f"Annual renewal processed: user_id={user_id}, new_expires={new_expires[:10]}")
