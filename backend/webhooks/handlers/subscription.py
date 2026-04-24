"""
Subscription webhook handlers.

Events:
- customer.subscription.created
- customer.subscription.updated
- customer.subscription.deleted
- customer.subscription.trial_will_end (STORY-CONV-003a AC4)
"""

import stripe

from log_sanitizer import get_sanitized_logger
from webhooks.handlers._shared import invalidate_user_caches

logger = get_sanitized_logger(__name__)


# STORY-CONV-003a AC4: Redis dedup TTL for trial_will_end events (7 days).
_TRIAL_WILL_END_DEDUP_TTL_S = 7 * 24 * 3600


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


async def handle_subscription_created(sb, event: stripe.Event) -> None:
    """
    Handle customer.subscription.created event.

    1. Emit `trial_started` Mixpanel funnel event when subscription.status="trialing"
       — completes signup → trial_started → paywall_hit → checkout_completed funnel.
    2. SEO-PLAYBOOK Referral: If `metadata.referral_code` is present, mark the
       matching referral row as converted and credit the referrer with 30 extra
       days of trial_end on their active subscription (Stripe handles the rest
       of the prorata automatically on the next invoice).
    """
    subscription_data = event.data.object

    # 1. Emit trial_started analytics event (fire-and-forget, never breaks webhook)
    try:
        if subscription_data.get("status") == "trialing":
            _emit_trial_started_event(sb, subscription_data)
    except Exception:
        logger.exception("Failed to emit trial_started analytics event")

    # 2. Referral crediting (existing)
    metadata = subscription_data.get("metadata") or {}
    referral_code = (metadata.get("referral_code") or "").strip().upper()

    if not referral_code:
        return

    logger.info(f"Subscription created with referral_code={referral_code}")

    try:
        _credit_referral_conversion(sb, referral_code, subscription_data)
    except Exception:
        # Never let referral crediting break the webhook
        logger.exception("Failed to credit referral for code %s", referral_code)


def _emit_trial_started_event(sb, subscription_data) -> None:
    """Emit `trial_started` Mixpanel funnel event for trial subscriptions.

    Resolves user_id via stripe_subscription_id then stripe_customer_id lookup.
    Fire-and-forget: failures logged, never raised.
    """
    from analytics_events import track_funnel_event

    stripe_sub_id = subscription_data.get("id")
    stripe_customer_id = subscription_data.get("customer")

    user_id = None
    if stripe_sub_id:
        sub_result = (
            sb.table("user_subscriptions")
            .select("user_id, plan_id")
            .eq("stripe_subscription_id", stripe_sub_id)
            .limit(1)
            .execute()
        )
        if sub_result.data:
            user_id = sub_result.data[0]["user_id"]
            plan_id = sub_result.data[0].get("plan_id")
        else:
            plan_id = None
    else:
        plan_id = None

    if not user_id and stripe_customer_id:
        cust_result = (
            sb.table("user_subscriptions")
            .select("user_id, plan_id")
            .eq("stripe_customer_id", stripe_customer_id)
            .limit(1)
            .execute()
        )
        if cust_result.data:
            user_id = cust_result.data[0]["user_id"]
            plan_id = plan_id or cust_result.data[0].get("plan_id")

    if not user_id:
        masked = (stripe_sub_id or "")[:8]
        logger.warning(f"trial_started: cannot resolve user_id for sub {masked}***")
        return

    plan_id = plan_id or (subscription_data.get("metadata") or {}).get("plan_id")
    trial_end = subscription_data.get("trial_end")

    stripe_interval = (
        subscription_data.get("plan", {}).get("interval")
        or (subscription_data.get("items", {}).get("data") or [{}])[0].get("plan", {}).get("interval")
    )
    stripe_interval_count = (
        subscription_data.get("plan", {}).get("interval_count", 1)
        or (subscription_data.get("items", {}).get("data") or [{}])[0].get("plan", {}).get("interval_count", 1)
    )
    if stripe_interval == "year":
        billing_period = "annual"
    elif stripe_interval == "month" and stripe_interval_count == 6:
        billing_period = "semiannual"
    else:
        billing_period = "monthly"

    track_funnel_event("trial_started", user_id, {
        "plan_id": plan_id,
        "trial_end_unix": trial_end,
        "stripe_subscription_id": stripe_sub_id,
        "billing_period": billing_period,
    })
    logger.info(f"trial_started event emitted: user={user_id[:8]}***, plan={plan_id}")


def _credit_referral_conversion(sb, referral_code: str, subscription_data) -> None:
    """Mark referral row converted + extend referrer's trial_end by 30 days.

    Defensive: if referrer has no active Stripe subscription we still mark
    the row as ``converted`` so the credit can be applied on their next
    subscription (the app-level UI will show the accumulated credit).
    """
    # 1. Look up the referral row
    row_result = (
        sb.table("referrals")
        .select("id, referrer_user_id, status, referred_user_id")
        .eq("code", referral_code)
        .limit(1)
        .execute()
    )
    rows = getattr(row_result, "data", []) or []
    if not rows:
        logger.info("Referral code not found at conversion: %s", referral_code)
        return

    row = rows[0]
    if row["status"] in ("converted", "credited"):
        logger.info("Referral already credited: %s", referral_code)
        return

    from datetime import datetime, timezone

    sb.table("referrals").update(
        {
            "status": "converted",
            "converted_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", row["id"]).execute()

    # Playbook §7.4 viral loop instrumentation — structured log that can be
    # piped to Mixpanel via log-sink. The conversion is the furthest-funnel
    # event of the referral program and the one that maps directly to MRR.
    logger.info(
        "analytics.referral_converted",
        extra={
            "event": "referral_converted",
            "code": referral_code,
            "referrer_user_id": row.get("referrer_user_id"),
            "referred_user_id": row.get("referred_user_id"),
            "stripe_subscription_id": subscription_data.get("id") if hasattr(subscription_data, "get") else None,
        },
    )

    referrer_user_id = row["referrer_user_id"]

    # 2. Find referrer's active Stripe subscription
    ref_sub_result = (
        sb.table("user_subscriptions")
        .select("stripe_subscription_id")
        .eq("user_id", referrer_user_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    ref_sub_rows = getattr(ref_sub_result, "data", []) or []
    if not ref_sub_rows or not ref_sub_rows[0].get("stripe_subscription_id"):
        logger.info(
            "Referrer %s has no active Stripe subscription — credit queued for next cycle",
            referrer_user_id,
        )
        return

    stripe_sub_id = ref_sub_rows[0]["stripe_subscription_id"]

    # 3. Extend trial_end by 30 days on the referrer's subscription.
    #    Stripe applies this as a free-period extension automatically.
    try:
        import stripe as stripe_mod
        existing = stripe_mod.Subscription.retrieve(stripe_sub_id)
        base = existing.get("trial_end") or existing.get("current_period_end")
        if not base:
            logger.warning(
                "Cannot determine base timestamp for trial extension on %s", stripe_sub_id
            )
            return
        new_trial_end = int(base) + 30 * 24 * 60 * 60
        stripe_mod.Subscription.modify(
            stripe_sub_id,
            trial_end=new_trial_end,
            proration_behavior="none",
        )
        logger.info(
            "Extended trial_end by 30d on %s for referrer %s",
            stripe_sub_id,
            referrer_user_id,
        )

        sb.table("referrals").update({"status": "credited"}).eq("id", row["id"]).execute()

        _send_referral_converted_email(sb, referrer_user_id)
    except Exception:
        logger.exception("Stripe trial extension failed for %s", stripe_sub_id)


def _send_referral_converted_email(sb, referrer_user_id: str) -> None:
    """Fire-and-forget: notify the referrer they earned 1 free month."""
    try:
        from email_service import send_email_async
        from templates.emails.referral_converted import render_referral_converted_email

        profile = (
            sb.table("profiles")
            .select("email, full_name")
            .eq("id", referrer_user_id)
            .single()
            .execute()
        )
        if not profile.data or not profile.data.get("email"):
            return

        email = profile.data["email"]
        name = profile.data.get("full_name") or email.split("@")[0]

        credits_result = (
            sb.table("referrals")
            .select("id", count="exact")
            .eq("referrer_user_id", referrer_user_id)
            .eq("status", "credited")
            .execute()
        )
        credits_total = getattr(credits_result, "count", None) or 1

        send_email_async(
            to=email,
            subject="Parabéns! Você ganhou 1 mês grátis no SmartLic",
            html=render_referral_converted_email(user_name=name, credits_total=credits_total),
            tags=[{"name": "category", "value": "referral_converted"}],
        )
    except Exception:
        logger.exception("Failed to send referral converted email to %s", referrer_user_id)


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

    # Emit subscription_canceled funnel event (fire-and-forget, never breaks webhook)
    try:
        _emit_subscription_canceled_event(user_id, local_sub, subscription_data)
    except Exception:
        logger.exception("Failed to emit subscription_canceled analytics event")


def _emit_subscription_canceled_event(user_id: str, local_sub: dict, subscription_data) -> None:
    """Emit `subscription_canceled` Mixpanel funnel event.

    Closes churn cohort tracking — without this, churn is invisible in Mixpanel.
    Fire-and-forget: failures logged, never raised.
    """
    from analytics_events import track_funnel_event

    def _get(d, key, default=None):
        if hasattr(d, "get"):
            return d.get(key, default)
        return getattr(d, key, default)

    cancellation_details = _get(subscription_data, "cancellation_details", {}) or {}
    cancellation_reason = _get(cancellation_details, "reason", None)

    stripe_interval = (
        _get(_get(subscription_data, "plan", {}) or {}, "interval", None)
        or _get(
            (_get(_get(subscription_data, "items", {}) or {}, "data", []) or [{}])[0].get("plan", {}) if isinstance(
                (_get(_get(subscription_data, "items", {}) or {}, "data", []) or [{}])[0], dict
            ) else {},
            "interval",
            None,
        )
    )
    stripe_interval_count = (
        _get(_get(subscription_data, "plan", {}) or {}, "interval_count", 1)
        or 1
    )
    if stripe_interval == "year":
        billing_period = "annual"
    elif stripe_interval == "month" and stripe_interval_count == 6:
        billing_period = "semiannual"
    else:
        billing_period = "monthly"

    track_funnel_event("subscription_canceled", user_id, {
        "plan_id": local_sub.get("plan_id"),
        "stripe_subscription_id": _get(subscription_data, "id", None),
        "billing_period": billing_period,
        "cancellation_reason": cancellation_reason,
        "expires_at": local_sub.get("expires_at"),
    })
    logger.info(
        f"subscription_canceled event emitted: user={user_id[:8]}***, "
        f"plan={local_sub.get('plan_id')}, reason={cancellation_reason}"
    )


async def handle_subscription_trial_will_end(sb, event: stripe.Event) -> None:
    """
    Handle customer.subscription.trial_will_end event (STORY-CONV-003a AC4).

    Stripe fires this 3 days before trial_end. Used to:
    - Dedup via Redis (7-day TTL) against duplicate Stripe retries
    - Emit Sentry breadcrumb for observability
    - Log a structured event; email/notification is a future story

    Never raises — webhook acks must be idempotent. Non-fatal errors logged.
    """
    event_id = getattr(event, "id", None) or event.get("id", "unknown")
    subscription_data = event.data.object
    stripe_sub_id = (
        subscription_data.get("id")
        if isinstance(subscription_data, dict)
        else subscription_data.id
    )
    stripe_customer_id = (
        subscription_data.get("customer")
        if isinstance(subscription_data, dict)
        else getattr(subscription_data, "customer", None)
    )

    # Redis dedup (7-day TTL) — best-effort. If Redis is down, proceed anyway:
    # duplicate handling is safe (log + breadcrumb only, no side effects).
    try:
        from redis_pool import get_redis_pool

        redis = await get_redis_pool()
        dedup_key = f"trial_will_end:{event_id}"
        existing = await redis.get(dedup_key)
        if existing:
            logger.info(
                f"trial_will_end already processed: event_id={event_id[:16]}***"
            )
            return
        await redis.setex(dedup_key, _TRIAL_WILL_END_DEDUP_TTL_S, "1")
    except Exception:
        logger.warning(
            "Redis dedup check failed for trial_will_end — proceeding", exc_info=True
        )

    # Resolve local user_id for logs/breadcrumb
    user_id: str = ""
    try:
        sub_result = (
            sb.table("user_subscriptions")
            .select("user_id")
            .eq("stripe_subscription_id", stripe_sub_id)
            .limit(1)
            .execute()
        )
        if sub_result.data:
            user_id = sub_result.data[0]["user_id"]
    except Exception:
        logger.debug("user_subscriptions lookup failed (non-fatal)", exc_info=True)

    logger.info(
        "Trial ending in 3 days: subscription_id=%s, customer_id=%s, user_id=%s",
        (stripe_sub_id or "")[:16] + "***",
        (stripe_customer_id or "")[:8] + "***" if stripe_customer_id else "unknown",
        (user_id or "unknown")[:8] + ("***" if user_id else ""),
    )

    # Sentry breadcrumb — best-effort, never raises.
    try:
        import sentry_sdk

        sentry_sdk.add_breadcrumb(
            category="billing",
            message="customer.subscription.trial_will_end",
            level="info",
            data={
                "subscription_id": (stripe_sub_id or "")[:16] + "***",
                "user_id": (user_id or "unknown")[:8] + ("***" if user_id else ""),
            },
        )
    except Exception:
        pass


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
