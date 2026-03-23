"""
Checkout session webhook handlers.

Events:
- checkout.session.completed
- checkout.session.async_payment_succeeded (Boleto/PIX — STORY-280)
- checkout.session.async_payment_failed (Boleto/PIX — STORY-280)
"""

import stripe
from datetime import datetime, timezone, timedelta

from log_sanitizer import get_sanitized_logger
from webhooks.handlers._shared import resolve_user_id, invalidate_user_caches

logger = get_sanitized_logger(__name__)


async def handle_checkout_session_completed(sb, event: stripe.Event) -> None:
    """
    Handle checkout.session.completed event.

    STORY-280 AC2: For async payment methods (Boleto/PIX), payment_status is "unpaid"
    at checkout completion. We must NOT activate — wait for async_payment_succeeded.

    For card payments (synchronous), payment_status is "paid" — activate immediately.
    """
    session_data = event.data.object
    user_id = resolve_user_id(sb, session_data)
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

    # STORY-280 AC2: Boleto/PIX -> payment_status="unpaid" at checkout.session.completed
    if payment_status == "unpaid":
        logger.info(
            f"Checkout completed with async payment (Boleto/PIX): user_id={user_id}, "
            f"plan_id={plan_id}, payment_status=unpaid — awaiting async_payment_succeeded"
        )

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

    # Card payment (synchronous) — activate immediately
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
    sb.table("profiles").update({
        "plan_type": plan_id,
        "subscription_status": "active",
    }).eq("id", user_id).execute()

    await invalidate_user_caches(user_id, "Checkout activation complete")

    # STORY-323 AC6: Create partner referral on conversion
    _create_partner_referral_async(user_id, plan_result, session_data)


async def handle_async_payment_succeeded(sb, event: stripe.Event) -> None:
    """
    Handle checkout.session.async_payment_succeeded event (STORY-280 AC2).

    Fired when a Boleto/PIX async payment is confirmed after checkout.
    Activates the pending subscription created by handle_checkout_session_completed.
    """
    session_data = event.data.object
    user_id = resolve_user_id(sb, session_data)
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
        sb.table("user_subscriptions").update({
            "is_active": True,
            "subscription_status": "active",
            "credits_remaining": max_searches,
            "expires_at": expires_at,
        }).eq("id", pending_result.data[0]["id"]).execute()
    else:
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

    await invalidate_user_caches(user_id, "Async payment activation complete")


async def handle_async_payment_failed(sb, event: stripe.Event) -> None:
    """
    Handle checkout.session.async_payment_failed event (STORY-280 AC2).

    Fired when a Boleto/PIX payment fails (e.g., boleto expired without payment).
    """
    session_data = event.data.object
    user_id = resolve_user_id(sb, session_data)
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

    # Send notification email
    _send_async_payment_failed_email(sb, user_id, plan_id)


# ============================================================================
# Helpers (fire-and-forget)
# ============================================================================

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


def _create_partner_referral_async(
    user_id: str, plan_result, session_data: dict
) -> None:
    """STORY-323 AC6: Create partner referral on checkout completion. Never raises."""
    try:
        import asyncio
        from services.partner_service import create_partner_referral

        price_brl = 0.0
        if plan_result and plan_result.data:
            price_brl = float(plan_result.data.get("price_brl", 0) or 0)

        discount = session_data.get("total_details", {}).get("breakdown", {}).get("discounts", [])
        stripe_coupon_id = None
        if discount and isinstance(discount, list) and len(discount) > 0:
            stripe_coupon_id = discount[0].get("discount", {}).get("coupon", {}).get("id")

        if not stripe_coupon_id:
            session_discount = session_data.get("discount")
            if session_discount and isinstance(session_discount, dict):
                stripe_coupon_id = session_discount.get("coupon", {}).get("id")

        loop = asyncio.get_event_loop()
        loop.create_task(
            create_partner_referral(user_id, price_brl, stripe_coupon_id)
        )
    except Exception as e:
        logger.warning(f"STORY-323: Failed to create partner referral for {user_id[:8]}: {e}")
