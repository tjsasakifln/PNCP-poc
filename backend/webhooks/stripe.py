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
- checkout.session.completed (initial subscription activation after payment)
- checkout.session.async_payment_succeeded (Boleto/PIX async payment confirmed — STORY-280)
- checkout.session.async_payment_failed (Boleto/PIX async payment failed — STORY-280)
- customer.subscription.updated (billing period changes, plan changes)
- customer.subscription.deleted (cancellation)
- invoice.payment_succeeded (renewal + dunning recovery — STORY-309 AC11)
- invoice.payment_failed (dunning email via dunning service — STORY-309 AC3)
- invoice.payment_action_required (3D Secure / SCA — STORY-309 AC10)

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
from datetime import datetime, timezone, timedelta

import stripe
from fastapi import APIRouter, Request, HTTPException

from supabase_client import get_supabase
from cache import redis_cache
from log_sanitizer import get_sanitized_logger

logger = get_sanitized_logger(__name__)
router = APIRouter()

# Stripe configuration
# NOTE: stripe.api_key removed for thread safety (STORY-221 Track 2)
# Webhook signature validation uses STRIPE_WEBHOOK_SECRET only
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if not STRIPE_WEBHOOK_SECRET:
    logger.error("STRIPE_WEBHOOK_SECRET not configured - webhook signature validation will fail")


def _resolve_user_id(sb, session_data: dict) -> str | None:
    """Resolve Supabase user_id from checkout session.

    Checks client_reference_id first (programmatic checkout).
    Falls back to customer_details.email lookup (Payment Links).

    MAYDAY-A2: Payment Links don't set client_reference_id,
    so we match by email in auth.users via profiles table.
    """
    user_id = session_data.get("client_reference_id")
    if user_id:
        return user_id

    # Fallback: look up user by email from checkout session
    customer_details = session_data.get("customer_details") or {}
    email = customer_details.get("email")
    if not email:
        # Also try customer_email (older Stripe API versions)
        email = session_data.get("customer_email")
    if not email:
        return None

    try:
        result = (
            sb.table("profiles")
            .select("id")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        if result.data:
            logger.info(f"Resolved user_id from email {email}: {result.data[0]['id']}")
            return result.data[0]["id"]

        logger.warning(f"No profile found for email {email} — user must sign up first")
        return None
    except Exception as e:
        logger.error(f"Failed to resolve user_id from email {email}: {e}")
        return None


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
        # If RETURNING is empty, event already exists (skip).
        # If RETURNING has data, we claimed exclusive processing rights.
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

        # Process event based on type
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

        # AC2: Mark event as completed after successful processing
        sb.table("stripe_webhook_events").update({
            "status": "completed",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "payload": event.data.object,
        }).eq("id", event.id).execute()

        logger.info(f"Webhook processed successfully: event_id={event.id}")
        return {"status": "success", "event_id": event.id}

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


async def _handle_checkout_session_completed(sb, event: stripe.Event):
    """
    Handle checkout.session.completed event.

    STORY-280 AC2: For async payment methods (Boleto/PIX), payment_status is "unpaid"
    at checkout completion. We must NOT activate — wait for async_payment_succeeded.

    For card payments (synchronous), payment_status is "paid" — activate immediately.

    Flow:
    1. Check payment_status: "paid" → activate now, "unpaid" → wait for async webhook
    2. Extract user_id from client_reference_id (set during checkout creation)
    3. Extract plan_id and billing_period from session metadata
    4. Look up plan details (duration_days, max_searches)
    5. Deactivate any existing active subscriptions for the user
    6. Insert new subscription row (active for paid, pending for unpaid)
    7. Sync profiles.plan_type for fallback reliability
    8. Invalidate Redis cache

    Args:
        sb: Supabase client
        event: Stripe event with checkout.session data
    """
    session_data = event.data.object
    user_id = _resolve_user_id(sb, session_data)
    metadata = session_data.get("metadata") or {}
    plan_id = metadata.get("plan_id")
    billing_period = metadata.get("billing_period", "monthly")
    stripe_subscription_id = session_data.get("subscription")
    stripe_customer_id = session_data.get("customer")
    payment_status = session_data.get("payment_status", "paid")

    if not user_id or not plan_id:
        logger.warning(
            f"Checkout session missing user_id or plan_id: "
            f"user_id={user_id}, metadata={metadata}"
        )
        return

    # STORY-280 AC2: Boleto/PIX → payment_status="unpaid" at checkout.session.completed
    # Do NOT activate — create subscription as "pending_payment", wait for async_payment_succeeded
    if payment_status == "unpaid":
        logger.info(
            f"Checkout completed with async payment (Boleto/PIX): user_id={user_id}, "
            f"plan_id={plan_id}, payment_status=unpaid — awaiting async_payment_succeeded"
        )

        # Create subscription row as pending (NOT active) so async handler can find it
        sb.table("user_subscriptions").insert({
            "user_id": user_id,
            "plan_id": plan_id,
            "billing_period": billing_period,
            "credits_remaining": 0,
            "expires_at": None,
            "stripe_subscription_id": stripe_subscription_id,
            "stripe_customer_id": stripe_customer_id,
            "is_active": False,
            "subscription_status": "pending_payment",
        }).execute()

        return

    # Card payment (synchronous) — activate immediately (existing behavior)
    logger.info(
        f"Checkout completed: user_id={user_id}, plan_id={plan_id}, "
        f"billing_period={billing_period}, stripe_sub={stripe_subscription_id}"
    )

    # Look up plan for duration_days and max_searches
    plan_result = sb.table("plans").select("duration_days, max_searches").eq("id", plan_id).single().execute()
    duration_days = 30
    max_searches = 1000
    if plan_result.data:
        duration_days = plan_result.data.get("duration_days", 30) or 30
        max_searches = plan_result.data.get("max_searches", 1000) or 1000

    expires_at = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()

    # Deactivate existing active subscriptions for this user
    sb.table("user_subscriptions").update(
        {"is_active": False}
    ).eq("user_id", user_id).eq("is_active", True).execute()

    # Create new active subscription
    sb.table("user_subscriptions").insert({
        "user_id": user_id,
        "plan_id": plan_id,
        "billing_period": billing_period,
        "credits_remaining": max_searches,
        "expires_at": expires_at,
        "stripe_subscription_id": stripe_subscription_id,
        "stripe_customer_id": stripe_customer_id,
        "is_active": True,
        "subscription_status": "active",
    }).execute()

    # Sync profiles.plan_type AND subscription_status (keeps fallback current — CRITICAL)
    # GTM-FIX-001 AC5+AC6: Both plan_type and subscription_status must be set on checkout
    sb.table("profiles").update({
        "plan_type": plan_id,
        "subscription_status": "active",
    }).eq("id", user_id).execute()

    # Invalidate Redis cache
    cache_key = f"features:{user_id}"
    try:
        await redis_cache.delete(cache_key)
        logger.info(f"Checkout activation complete: user_id={user_id}, plan={plan_id}, cache invalidated")
    except Exception as e:
        logger.warning(f"Cache invalidation failed on checkout activation (non-fatal): {e}")
        logger.info(f"Checkout activation complete: user_id={user_id}, plan={plan_id}")

    # STORY-323 AC6: Create partner referral on conversion
    _create_partner_referral_async(user_id, plan_result, session_data)


async def _handle_async_payment_succeeded(sb, event: stripe.Event):
    """
    Handle checkout.session.async_payment_succeeded event (STORY-280 AC2).

    Fired when a Boleto/PIX async payment is confirmed after checkout.
    Activates the pending subscription created by _handle_checkout_session_completed.

    Flow:
    1. Find pending subscription by stripe_subscription_id
    2. Look up plan details
    3. Activate subscription (is_active=True, subscription_status=active)
    4. Sync profiles.plan_type
    5. Invalidate Redis cache

    Args:
        sb: Supabase client
        event: Stripe event with checkout.session data
    """
    session_data = event.data.object
    user_id = _resolve_user_id(sb, session_data)
    metadata = session_data.get("metadata") or {}
    plan_id = metadata.get("plan_id")
    billing_period = metadata.get("billing_period", "monthly")
    stripe_subscription_id = session_data.get("subscription")
    stripe_customer_id = session_data.get("customer")

    if not user_id or not plan_id:
        logger.warning(
            f"Async payment succeeded missing user_id or plan_id: "
            f"user_id={user_id}, metadata={metadata}"
        )
        return

    logger.info(
        f"Async payment succeeded (Boleto/PIX): user_id={user_id}, plan_id={plan_id}, "
        f"stripe_sub={stripe_subscription_id}"
    )

    # Look up plan for duration_days and max_searches
    plan_result = sb.table("plans").select("duration_days, max_searches").eq("id", plan_id).single().execute()
    duration_days = 30
    max_searches = 1000
    if plan_result.data:
        duration_days = plan_result.data.get("duration_days", 30) or 30
        max_searches = plan_result.data.get("max_searches", 1000) or 1000

    expires_at = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()

    # Deactivate existing active subscriptions for this user
    sb.table("user_subscriptions").update(
        {"is_active": False}
    ).eq("user_id", user_id).eq("is_active", True).execute()

    # Find and activate the pending subscription (created at checkout.session.completed)
    pending_result = (
        sb.table("user_subscriptions")
        .select("id")
        .eq("stripe_subscription_id", stripe_subscription_id)
        .eq("subscription_status", "pending_payment")
        .limit(1)
        .execute()
    )

    if pending_result.data:
        # Update existing pending row to active
        sb.table("user_subscriptions").update({
            "is_active": True,
            "subscription_status": "active",
            "credits_remaining": max_searches,
            "expires_at": expires_at,
        }).eq("id", pending_result.data[0]["id"]).execute()
    else:
        # No pending row found — create new (edge case: webhook ordering)
        sb.table("user_subscriptions").insert({
            "user_id": user_id,
            "plan_id": plan_id,
            "billing_period": billing_period,
            "credits_remaining": max_searches,
            "expires_at": expires_at,
            "stripe_subscription_id": stripe_subscription_id,
            "stripe_customer_id": stripe_customer_id,
            "is_active": True,
            "subscription_status": "active",
        }).execute()

    # Sync profiles.plan_type AND subscription_status
    sb.table("profiles").update({
        "plan_type": plan_id,
        "subscription_status": "active",
    }).eq("id", user_id).execute()

    # Invalidate Redis cache
    cache_key = f"features:{user_id}"
    try:
        await redis_cache.delete(cache_key)
        logger.info(f"Async payment activation complete: user_id={user_id}, plan={plan_id}, cache invalidated")
    except Exception as e:
        logger.warning(f"Cache invalidation failed on async payment activation (non-fatal): {e}")
        logger.info(f"Async payment activation complete: user_id={user_id}, plan={plan_id}")


async def _handle_async_payment_failed(sb, event: stripe.Event):
    """
    Handle checkout.session.async_payment_failed event (STORY-280 AC2).

    Fired when a Boleto/PIX payment fails (e.g., boleto expired without payment).
    Sends notification email and maintains current access (grace period already implemented).

    Args:
        sb: Supabase client
        event: Stripe event with checkout.session data
    """
    session_data = event.data.object
    user_id = _resolve_user_id(sb, session_data)
    metadata = session_data.get("metadata") or {}
    plan_id = metadata.get("plan_id")
    stripe_subscription_id = session_data.get("subscription")

    if not user_id:
        logger.warning(f"Async payment failed missing user_id: metadata={metadata}")
        return

    logger.warning(
        f"Async payment failed (Boleto/PIX): user_id={user_id}, plan_id={plan_id}, "
        f"stripe_sub={stripe_subscription_id}"
    )

    # Clean up pending subscription row (mark as failed)
    if stripe_subscription_id:
        sb.table("user_subscriptions").update({
            "subscription_status": "payment_failed",
        }).eq("stripe_subscription_id", stripe_subscription_id).eq(
            "subscription_status", "pending_payment"
        ).execute()

    # Send notification email: "Seu boleto expirou. Gere um novo em /planos"
    _send_async_payment_failed_email(sb, user_id, plan_id)


def _send_async_payment_failed_email(sb, user_id: str, plan_id: str | None) -> None:
    """Send async payment failed email (STORY-280 AC2). Never raises."""
    try:
        from email_service import send_email_async
        from templates.emails.boleto_reminder import render_boleto_expired_email
        from quota import PLAN_NAMES

        profile = sb.table("profiles").select("email, full_name").eq("id", user_id).single().execute()
        if not profile.data or not profile.data.get("email"):
            return

        email = profile.data["email"]
        name = profile.data.get("full_name") or email.split("@")[0]
        plan_name = PLAN_NAMES.get(plan_id, plan_id) if plan_id else "SmartLic Pro"

        html = render_boleto_expired_email(
            user_name=name,
            plan_name=plan_name,
        )
        send_email_async(
            to=email,
            subject="Boleto expirado — Gere um novo para ativar seu plano",
            html=html,
            tags=[{"name": "category", "value": "boleto_expired"}],
        )
        logger.info(f"Boleto expired email queued for user_id={user_id}")
    except Exception as e:
        logger.warning(f"Failed to send boleto expired email: {e}")


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
    # GTM-002: Support monthly, semiannual, annual billing periods
    # Stripe uses "month" for both monthly and semiannual (6-month is month with interval_count=6)
    stripe_interval_count = (
        subscription_data.get("plan", {}).get("interval_count", 1)
        or subscription_data.get("items", {}).get("data", [{}])[0].get("plan", {}).get("interval_count", 1)
    )
    if stripe_interval == "year":
        billing_period = "annual"
    elif stripe_interval == "month" and stripe_interval_count == 6:
        billing_period = "semiannual"
    else:
        billing_period = "monthly"

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
        await redis_cache.delete(cache_key)
        logger.info(f"Cache invalidated: key={cache_key}")
    except Exception as e:
        logger.warning(f"Cache invalidation failed (non-fatal): {e}")


async def _handle_subscription_deleted(sb, event: stripe.Event):
    """
    Handle customer.subscription.deleted event.

    Marks subscription as inactive and syncs profiles.plan_type to free_trial.
    STORY-225 AC14: Sends cancellation confirmation email.

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
        .select("id, user_id, plan_id, expires_at")
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
        await redis_cache.delete(cache_key)
        logger.info(f"Subscription deactivated: user_id={user_id}, cache invalidated")
    except Exception as e:
        logger.warning(f"Cache invalidation failed on deletion (non-fatal): {e}")
        logger.info(f"Subscription deactivated: user_id={user_id}")

    # STORY-323 AC7: Mark partner referral as churned
    _mark_partner_referral_churned(user_id)

    # STORY-225 AC14: Send cancellation confirmation email
    _send_cancellation_email(sb, user_id, local_sub)


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

    # STORY-309 AC11: Check if this was a recovery from dunning (subscription was past_due)
    was_past_due = False
    try:
        profile_check = sb.table("profiles").select("subscription_status").eq("id", user_id).single().execute()
        if profile_check.data and profile_check.data.get("subscription_status") == "past_due":
            was_past_due = True
    except Exception as e:
        logger.warning(f"Failed to check past_due status for user_id={user_id}: {e}")

    # Reactivate, extend, and clear dunning state (first_failed_at → None)
    sb.table("user_subscriptions").update({
        "is_active": True,
        "expires_at": new_expires,
        "subscription_status": "active",
        "first_failed_at": None,
    }).eq("id", local_sub["id"]).execute()

    # Sync profiles.plan_type AND subscription_status (keeps fallback current)
    sb.table("profiles").update({
        "plan_type": plan_id,
        "subscription_status": "active",
    }).eq("id", user_id).execute()

    # Invalidate cache
    cache_key = f"features:{user_id}"
    try:
        await redis_cache.delete(cache_key)
        logger.info(f"Annual renewal processed: user_id={user_id}, new_expires={new_expires[:10]}")
    except Exception as e:
        logger.warning(f"Cache invalidation failed on renewal (non-fatal): {e}")
        logger.info(f"Annual renewal processed: user_id={user_id}, new_expires={new_expires[:10]}")

    # STORY-225 AC12: Send payment confirmation email
    _send_payment_confirmation_email(sb, user_id, plan_id, invoice_data, new_expires)

    # STORY-309 AC11: Send recovery email if was in dunning
    if was_past_due:
        try:
            from services.dunning import send_recovery_email
            await send_recovery_email(user_id, plan_id)
        except Exception as e:
            logger.warning(f"Failed to send dunning recovery email for user_id={user_id}: {e}")


async def _handle_invoice_payment_failed(sb, event: stripe.Event):
    """
    Handle invoice.payment_failed event (GTM-FIX-007 Track 1 AC2-AC5, AC15).

    Updates subscription status to past_due, logs to Sentry, sends email notification.

    Args:
        sb: Supabase client
        event: Stripe event object
    """
    invoice_data = event.data.object
    stripe_customer_id = invoice_data.get("customer")
    stripe_subscription_id = invoice_data.get("subscription")

    if not stripe_subscription_id:
        logger.debug("Invoice payment failed has no subscription_id, skipping")
        return

    logger.warning(
        f"Payment failed: subscription_id={stripe_subscription_id}, "
        f"customer={stripe_customer_id[:8] if stripe_customer_id else 'unknown'}***"
    )

    # Find subscription to get user_id and plan
    sub_result = (
        sb.table("user_subscriptions")
        .select("id, user_id, plan_id")
        .eq("stripe_subscription_id", stripe_subscription_id)
        .limit(1)
        .execute()
    )

    if not sub_result.data:
        logger.warning(f"No local subscription for failed payment stripe_sub {stripe_subscription_id[:8]}***")
        return

    local_sub = sub_result.data[0]
    user_id = local_sub["user_id"]
    plan_id = local_sub["plan_id"]

    # Extract attempt count and decline details (STORY-309 AC3)
    attempt_count = invoice_data.get("attempt_count", 1)
    amount = invoice_data.get("amount_due", 0)

    charge = invoice_data.get("charge") or {}
    decline_type = "soft"
    decline_code = ""
    if isinstance(charge, dict):
        outcome = charge.get("outcome") or {}
        if isinstance(outcome, dict) and outcome.get("type") == "blocked":
            decline_type = "hard"
        decline_code = charge.get("decline_code", "") or charge.get("failure_code", "") or ""

    # Set first_failed_at on first failure, update status to past_due (STORY-309 AC7)
    if attempt_count <= 1:
        sb.table("user_subscriptions").update({
            "subscription_status": "past_due",
            "first_failed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", local_sub["id"]).is_("first_failed_at", "null").execute()
    else:
        sb.table("user_subscriptions").update({
            "subscription_status": "past_due",
        }).eq("id", local_sub["id"]).execute()

    # Also update profiles.subscription_status
    sb.table("profiles").update({
        "subscription_status": "past_due",
    }).eq("id", user_id).execute()

    # Log to Sentry with customer context (AC4)
    try:
        import sentry_sdk
        sentry_sdk.capture_message(
            f"Payment failed: user_id={user_id}, plan={plan_id}, attempt={attempt_count}",
            level="warning",
            extras={
                "user_id": user_id,
                "plan_id": plan_id,
                "stripe_customer_id": stripe_customer_id,
                "stripe_subscription_id": stripe_subscription_id,
                "attempt_count": attempt_count,
                "amount_due": amount,
                "decline_type": decline_type,
                "decline_code": decline_code,
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send Sentry event: {e}")

    # AC15: Track payment failed event (using structured logging since Mixpanel is frontend-only)
    logger.info(
        "payment_failed_event",
        extra={
            "event": "payment_failed",
            "user_id": user_id,
            "plan": plan_id,
            "amount": amount / 100,  # Convert cents to BRL
            "attempt_count": attempt_count,
            "decline_type": decline_type,
            "decline_code": decline_code,
        }
    )

    # STORY-309 AC3: Send dunning email via dunning service (replaces generic _send_payment_failed_email)
    try:
        from services.dunning import send_dunning_email
        await send_dunning_email(user_id, attempt_count, invoice_data, decline_type)
    except Exception as e:
        logger.warning(f"Failed to send dunning email for user_id={user_id}: {e}")

    logger.info(f"Payment failed handling complete: user_id={user_id}, status=past_due, decline_type={decline_type}")


async def _handle_payment_action_required(sb, event: stripe.Event):
    """Handle invoice.payment_action_required event (STORY-309 AC10).

    Sent when payment requires 3D Secure / SCA authentication.
    Sends email with link to complete payment.
    """
    invoice_data = event.data.object
    stripe_subscription_id = invoice_data.get("subscription")

    if not stripe_subscription_id:
        return

    # Find user
    sub_result = (
        sb.table("user_subscriptions")
        .select("id, user_id, plan_id")
        .eq("stripe_subscription_id", stripe_subscription_id)
        .limit(1)
        .execute()
    )
    if not sub_result.data:
        logger.warning(
            f"No local subscription for payment_action_required: "
            f"stripe_sub={stripe_subscription_id[:8]}***"
        )
        return

    user_id = sub_result.data[0]["user_id"]

    # Extract hosted_invoice_url for 3DS completion
    hosted_url = invoice_data.get("hosted_invoice_url", "")

    logger.info(
        f"Payment action required (3DS/SCA): user_id={user_id}, "
        f"stripe_sub={stripe_subscription_id[:8]}***, has_hosted_url={bool(hosted_url)}"
    )

    # Send notification email
    _send_payment_action_required_email(sb, user_id, hosted_url)


# ============================================================================
# STORY-225: Email notification helpers (fire-and-forget)
# ============================================================================

def _send_payment_confirmation_email(sb, user_id: str, plan_id: str, invoice_data: dict, new_expires: str) -> None:
    """Send payment confirmation email (AC12). Never raises."""
    try:
        from email_service import send_email_async
        from templates.emails.billing import render_payment_confirmation_email
        from quota import PLAN_NAMES

        profile = sb.table("profiles").select("email, full_name").eq("id", user_id).single().execute()
        if not profile.data or not profile.data.get("email"):
            return

        email = profile.data["email"]
        name = profile.data.get("full_name") or email.split("@")[0]
        plan_name = PLAN_NAMES.get(plan_id, plan_id)

        # Format amount from Stripe (cents → BRL)
        amount_cents = invoice_data.get("amount_paid", 0)
        amount = f"R$ {amount_cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # Determine billing period
        billing_period = "mensal"
        lines = invoice_data.get("lines", {}).get("data", [])
        if lines:
            interval = lines[0].get("plan", {}).get("interval", "month")
            interval_count = lines[0].get("plan", {}).get("interval_count", 1)
            if interval == "year":
                billing_period = "anual"
            elif interval == "month" and interval_count == 6:
                billing_period = "semestral"
            else:
                billing_period = "mensal"

        # Format renewal date
        try:
            from datetime import datetime
            renewal_dt = datetime.fromisoformat(new_expires.replace("Z", "+00:00"))
            renewal_date = renewal_dt.strftime("%d/%m/%Y")
        except Exception:
            renewal_date = new_expires[:10]

        html = render_payment_confirmation_email(
            user_name=name,
            plan_name=plan_name,
            amount=amount,
            next_renewal_date=renewal_date,
            billing_period=billing_period,
        )
        send_email_async(
            to=email,
            subject=f"Pagamento confirmado — {plan_name}",
            html=html,
            tags=[{"name": "category", "value": "payment_confirmation"}],
        )
        logger.info(f"Payment confirmation email queued for user_id={user_id}")
    except Exception as e:
        logger.warning(f"Failed to send payment confirmation email: {e}")


def _send_cancellation_email(sb, user_id: str, subscription_data: dict) -> None:
    """Send cancellation confirmation email (AC14). Never raises."""
    try:
        from email_service import send_email_async
        from templates.emails.billing import render_cancellation_email
        from quota import PLAN_NAMES

        profile = sb.table("profiles").select("email, full_name").eq("id", user_id).single().execute()
        if not profile.data or not profile.data.get("email"):
            return

        email = profile.data["email"]
        name = profile.data.get("full_name") or email.split("@")[0]
        plan_id = subscription_data.get("plan_id", "")
        plan_name = PLAN_NAMES.get(plan_id, plan_id)

        # End date from subscription expires_at
        expires_at = subscription_data.get("expires_at", "")
        try:
            from datetime import datetime
            end_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            end_date = end_dt.strftime("%d/%m/%Y")
        except Exception:
            end_date = expires_at[:10] if expires_at else "N/A"

        html = render_cancellation_email(
            user_name=name,
            plan_name=plan_name,
            end_date=end_date,
        )
        send_email_async(
            to=email,
            subject="Cancelamento confirmado — SmartLic",
            html=html,
            tags=[{"name": "category", "value": "cancellation"}],
        )
        logger.info(f"Cancellation email queued for user_id={user_id}")
    except Exception as e:
        logger.warning(f"Failed to send cancellation email: {e}")


def _send_payment_action_required_email(sb, user_id: str, hosted_url: str) -> None:
    """Send 3D Secure authentication required email (STORY-309 AC10). Never raises."""
    try:
        from email_service import send_email_async
        from templates.emails.base import email_base, FRONTEND_URL

        profile = sb.table("profiles").select("email, full_name").eq("id", user_id).single().execute()
        if not profile.data or not profile.data.get("email"):
            return

        email = profile.data["email"]
        name = profile.data.get("full_name") or email.split("@")[0]

        action_url = hosted_url or f"{FRONTEND_URL}/conta"
        body = f'''
        <h1 style="color: #333; font-size: 22px; margin: 0 0 16px;">Autenticação necessária para pagamento</h1>
        <p style="color: #555; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
          Olá, {name}! Seu banco requer uma autenticação adicional (3D Secure) para processar o pagamento da sua assinatura SmartLic.
        </p>
        <p style="text-align: center; margin: 24px 0 16px;">
          <a href="{action_url}" class="btn" style="display: inline-block; padding: 14px 32px; background-color: #2E7D32; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">Completar Autenticação</a>
        </p>
        <p style="color: #888; font-size: 14px; line-height: 1.6; margin: 24px 0 0;">Basta clicar no botão acima e seguir as instruções do seu banco.</p>
        '''
        html = email_base(title="Autenticação necessária — SmartLic", body_html=body, is_transactional=True)
        send_email_async(
            to=email,
            subject="Autenticação necessária para pagamento — SmartLic",
            html=html,
            tags=[{"name": "category", "value": "payment_action_required"}],
        )
        logger.info(f"Payment action required email queued for user_id={user_id}")
    except Exception as e:
        logger.warning(f"Failed to send payment action required email: {e}")


def _send_payment_failed_email(sb, user_id: str, plan_id: str, invoice_data: dict) -> None:
    """Send payment failed email (GTM-FIX-007 AC5-AC6). Never raises. Kept for backward compatibility."""
    try:
        from email_service import send_email_async
        from templates.emails.billing import render_payment_failed_email
        from quota import PLAN_NAMES

        profile = sb.table("profiles").select("email, full_name").eq("id", user_id).single().execute()
        if not profile.data or not profile.data.get("email"):
            return

        email = profile.data["email"]
        name = profile.data.get("full_name") or email.split("@")[0]
        plan_name = PLAN_NAMES.get(plan_id, plan_id)

        # Format amount from Stripe (cents → BRL)
        amount_cents = invoice_data.get("amount_due", 0)
        amount = f"R$ {amount_cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # Extract failure reason
        failure_reason = "Não foi possível processar o pagamento"
        if invoice_data.get("charge"):
            charge = invoice_data.get("charge")
            if isinstance(charge, str):
                # Would need to fetch charge details from Stripe API, keep generic
                pass
            elif isinstance(charge, dict):
                failure_message = charge.get("failure_message", "")
                if failure_message:
                    failure_reason = failure_message

        # Extract next attempt info
        attempt_count = invoice_data.get("attempt_count", 1)
        # Stripe retries up to 4 times over 2 weeks (default)
        days_until_cancellation = max(0, 14 - (attempt_count * 3))

        html = render_payment_failed_email(
            user_name=name,
            plan_name=plan_name,
            amount=amount,
            failure_reason=failure_reason,
            days_until_cancellation=days_until_cancellation,
        )
        send_email_async(
            to=email,
            subject="⚠️ Falha no pagamento — SmartLic",
            html=html,
            tags=[{"name": "category", "value": "payment_failed"}],
        )
        logger.info(f"Payment failed email queued for user_id={user_id}")
    except Exception as e:
        logger.warning(f"Failed to send payment failed email: {e}")


# ============================================================================
# STORY-323: Partner referral helpers (fire-and-forget)
# ============================================================================

def _create_partner_referral_async(
    user_id: str, plan_result, session_data: dict
) -> None:
    """STORY-323 AC6: Create partner referral on checkout completion. Never raises."""
    try:
        import asyncio
        from services.partner_service import create_partner_referral

        # Estimate monthly revenue from plan price
        price_brl = 0.0
        if plan_result and plan_result.data:
            # Use plan's monthly price or derive from duration
            price_brl = float(plan_result.data.get("price_brl", 0) or 0)

        # Extract coupon from session (AC5)
        discount = session_data.get("total_details", {}).get("breakdown", {}).get("discounts", [])
        stripe_coupon_id = None
        if discount and isinstance(discount, list) and len(discount) > 0:
            stripe_coupon_id = discount[0].get("discount", {}).get("coupon", {}).get("id")

        # Also check session-level discount
        if not stripe_coupon_id:
            session_discount = session_data.get("discount")
            if session_discount and isinstance(session_discount, dict):
                stripe_coupon_id = session_discount.get("coupon", {}).get("id")

        # Schedule as background task
        loop = asyncio.get_event_loop()
        loop.create_task(
            create_partner_referral(user_id, price_brl, stripe_coupon_id)
        )
    except Exception as e:
        logger.warning(f"STORY-323: Failed to create partner referral for {user_id[:8]}: {e}")


def _mark_partner_referral_churned(user_id: str) -> None:
    """STORY-323 AC7: Mark partner referral as churned on subscription deletion. Never raises."""
    try:
        import asyncio
        from services.partner_service import mark_referral_churned

        loop = asyncio.get_event_loop()
        loop.create_task(mark_referral_churned(user_id))
    except Exception as e:
        logger.warning(f"STORY-323: Failed to mark partner referral churned for {user_id[:8]}: {e}")
