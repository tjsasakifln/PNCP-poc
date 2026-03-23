"""
Subscription webhook handlers.

Events:
- customer.subscription.updated
- customer.subscription.deleted
"""

import stripe

from log_sanitizer import get_sanitized_logger
from webhooks.handlers._shared import invalidate_user_caches

logger = get_sanitized_logger(__name__)


async def handle_subscription_updated(sb, event: stripe.Event) -> None:
    """
    Handle customer.subscription.updated event.

    Updates billing_period and syncs profiles.plan_type.
    """
    subscription_data = event.data.object
    stripe_sub_id = subscription_data.id

    # Determine billing_period from Stripe interval
    stripe_interval = (
        subscription_data.get("plan", {}).get("interval")
        or subscription_data.get("items", {}).get("data", [{}])[0].get("plan", {}).get("interval")
    )
    # GTM-002: Support monthly, semiannual, annual billing periods
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

    await invalidate_user_caches(user_id, f"Subscription updated: billing_period={billing_period}")


async def handle_subscription_deleted(sb, event: stripe.Event) -> None:
    """
    Handle customer.subscription.deleted event.

    Marks subscription as inactive and syncs profiles.plan_type to free_trial.
    STORY-225 AC14: Sends cancellation confirmation email.
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

    await invalidate_user_caches(user_id, "Subscription deactivated")

    # STORY-323 AC7: Mark partner referral as churned
    _mark_partner_referral_churned(user_id)

    # STORY-225 AC14: Send cancellation confirmation email
    _send_cancellation_email(sb, user_id, local_sub)


# ============================================================================
# Helpers (fire-and-forget)
# ============================================================================

def _mark_partner_referral_churned(user_id: str) -> None:
    """STORY-323 AC7: Mark partner referral as churned on subscription deletion. Never raises."""
    try:
        import asyncio
        from services.partner_service import mark_referral_churned

        loop = asyncio.get_event_loop()
        loop.create_task(mark_referral_churned(user_id))
    except Exception as e:
        logger.warning(f"STORY-323: Failed to mark partner referral churned for {user_id[:8]}: {e}")


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
