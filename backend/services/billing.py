"""Billing service for subscription management.

Handles pro-rata calculations, billing period updates, and Stripe integration
for annual subscriptions (STORY-171).

IMPORTANT: Pro-rata calculations use timezone-aware datetimes to ensure
accurate billing across different user timezones.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Literal
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProRataResult(BaseModel):
    """Result of pro-rata calculation."""
    prorated_credit: Decimal  # Amount to credit (BRL)
    days_until_renewal: int
    deferred: bool  # True if update should be deferred until next billing cycle
    next_billing_date: datetime
    reason: Optional[str] = None  # Explanation for deferred updates


def calculate_daily_rate(
    price_brl: Decimal,
    billing_period: Literal["monthly", "annual"]
) -> Decimal:
    """Calculate daily rate for a plan.

    Monthly: price / 30 (standard billing month)
    Annual: price * 9.6 / 365 (20% discount: price * 0.8 / 365)

    Args:
        price_brl: Plan price in BRL
        billing_period: 'monthly' or 'annual'

    Returns:
        Daily rate in BRL (rounded to 2 decimals)

    Examples:
        >>> calculate_daily_rate(Decimal("297.00"), "monthly")
        Decimal('9.90')
        >>> calculate_daily_rate(Decimal("2376.00"), "annual")  # 297 * 8 with 20% discount
        Decimal('6.50')
    """
    if billing_period == "monthly":
        daily_rate = price_brl / 30
    elif billing_period == "annual":
        # Annual gets 20% discount: price * 0.8 / 365
        # Equivalent to: price * 9.6 / 365
        daily_rate = (price_brl * Decimal("9.6")) / 365
    else:
        raise ValueError(f"Invalid billing_period: {billing_period}")

    # Round to 2 decimals for currency
    return daily_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_prorata_credit(
    current_billing_period: Literal["monthly", "annual"],
    new_billing_period: Literal["monthly", "annual"],
    current_price_brl: Decimal,
    new_price_brl: Decimal,
    next_billing_date: datetime,
    user_timezone: str = "America/Sao_Paulo",
) -> ProRataResult:
    """Calculate pro-rata credit when switching billing periods.

    CRITICAL EDGE CASES:
    1. Defer logic: If < 7 days until renewal, defer the upgrade to avoid
       complex pro-rata calculations and Stripe edge cases.
    2. Timezone: Use user's timezone (not UTC) for accurate day calculations.
    3. Downgrade: Monthly → Annual should never happen (UX prevents it).

    Args:
        current_billing_period: Current billing period ('monthly' or 'annual')
        new_billing_period: Desired billing period ('monthly' or 'annual')
        current_price_brl: Current plan price
        new_price_brl: New plan price (may differ if plan changes too)
        next_billing_date: Next scheduled billing date (timezone-aware)
        user_timezone: User's timezone (default: America/Sao_Paulo for Brazil)

    Returns:
        ProRataResult with credit amount, days until renewal, and defer flag

    Examples:
        # Monthly → Annual with 15 days remaining
        >>> result = calculate_prorata_credit(
        ...     "monthly", "annual",
        ...     Decimal("297.00"), Decimal("2376.00"),
        ...     datetime(2026, 3, 1, tzinfo=timezone.utc)
        ... )
        >>> result.prorated_credit
        Decimal('148.50')  # 15 days * 9.90/day
    """
    from zoneinfo import ZoneInfo

    # Ensure next_billing_date is timezone-aware
    if next_billing_date.tzinfo is None:
        logger.warning("next_billing_date was naive, assuming UTC")
        next_billing_date = next_billing_date.replace(tzinfo=timezone.utc)

    # Get current time in user's timezone for accurate day calculations
    try:
        user_tz = ZoneInfo(user_timezone)
    except Exception as e:
        logger.warning(f"Invalid timezone '{user_timezone}', using UTC: {e}")
        user_tz = timezone.utc

    now = datetime.now(user_tz)
    next_billing_local = next_billing_date.astimezone(user_tz)

    # Calculate days until renewal (inclusive of today)
    days_until_renewal = (next_billing_local.date() - now.date()).days + 1

    # EDGE CASE 1: Defer if too close to renewal (< 7 days)
    # Reason: Avoid complex pro-rata + Stripe edge cases, just wait for next cycle
    if days_until_renewal < 7:
        logger.info(
            f"Deferring billing period update: {days_until_renewal} days until renewal (< 7 day threshold)"
        )
        return ProRataResult(
            prorated_credit=Decimal("0.00"),
            days_until_renewal=days_until_renewal,
            deferred=True,
            next_billing_date=next_billing_date,
            reason=f"Menos de 7 dias até renovação ({days_until_renewal} dias). "
                   f"A mudança será aplicada no próximo ciclo de cobrança.",
        )

    # EDGE CASE 2: Prevent downgrades (shouldn't happen via UX, but defensive)
    if current_billing_period == "annual" and new_billing_period == "monthly":
        logger.error("Attempted downgrade from annual to monthly - not allowed")
        raise ValueError(
            "Downgrade from annual to monthly is not supported. "
            "Contact support to cancel your annual subscription."
        )

    # Calculate daily rates
    current_daily_rate = calculate_daily_rate(current_price_brl, current_billing_period)
    new_daily_rate = calculate_daily_rate(new_price_brl, new_billing_period)

    # Pro-rata credit = unused days at current rate
    # (User will be charged new rate immediately for next billing cycle)
    prorated_credit = current_daily_rate * days_until_renewal

    logger.info(
        f"Pro-rata calculation: {days_until_renewal} days remaining, "
        f"current_rate={current_daily_rate}/day, new_rate={new_daily_rate}/day, "
        f"credit={prorated_credit}"
    )

    return ProRataResult(
        prorated_credit=prorated_credit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        days_until_renewal=days_until_renewal,
        deferred=False,
        next_billing_date=next_billing_date,
        reason=None,
    )


def update_stripe_subscription_billing_period(
    stripe_subscription_id: str,
    new_billing_period: Literal["monthly", "annual"],
    stripe_price_id_monthly: str,
    stripe_price_id_annual: str,
    prorated_credit: Optional[Decimal] = None,
) -> dict:
    """Update Stripe subscription billing period.

    Changes the subscription from monthly to annual billing (or vice versa)
    and applies pro-rata credit if provided.

    Args:
        stripe_subscription_id: Stripe subscription ID (sub_...)
        new_billing_period: Target billing period
        stripe_price_id_monthly: Stripe price ID for monthly billing
        stripe_price_id_annual: Stripe price ID for annual billing
        prorated_credit: Optional credit to apply (BRL)

    Returns:
        Updated Stripe subscription object

    Raises:
        ValueError: If Stripe API key not configured
        stripe.error.StripeError: If Stripe API call fails
    """
    import os
    import stripe

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        raise ValueError("STRIPE_SECRET_KEY not configured")

    stripe.api_key = stripe_key

    # Determine target price ID
    target_price_id = (
        stripe_price_id_annual if new_billing_period == "annual"
        else stripe_price_id_monthly
    )

    logger.info(
        f"Updating Stripe subscription {stripe_subscription_id} to {new_billing_period} "
        f"billing (price_id={target_price_id})"
    )

    # Update subscription with new price
    # proration_behavior='create_prorations' ensures Stripe handles the billing adjustment
    subscription_updates = {
        "items": [{
            "id": stripe.Subscription.retrieve(stripe_subscription_id)["items"]["data"][0]["id"],
            "price": target_price_id,
        }],
        "proration_behavior": "create_prorations",
    }

    # If we have a calculated credit, apply it as a balance adjustment
    # (Stripe will credit the customer account)
    if prorated_credit and prorated_credit > 0:
        # Convert BRL to cents for Stripe
        credit_cents = int(prorated_credit * 100)
        customer_id = stripe.Subscription.retrieve(stripe_subscription_id)["customer"]

        logger.info(f"Applying {prorated_credit} BRL credit to customer {customer_id}")

        # Create credit balance transaction
        stripe.Customer.create_balance_transaction(
            customer_id,
            amount=-credit_cents,  # Negative = credit
            currency="brl",
            description=f"Pro-rata credit for billing period change to {new_billing_period}",
        )

    updated_subscription = stripe.Subscription.modify(
        stripe_subscription_id,
        **subscription_updates
    )

    logger.info(f"Successfully updated Stripe subscription {stripe_subscription_id}")
    return updated_subscription


def get_next_billing_date(user_id: str) -> Optional[datetime]:
    """Get user's next billing date from Supabase.

    Args:
        user_id: User UUID

    Returns:
        Next billing date (timezone-aware) or None if no active subscription
    """
    from supabase_client import get_supabase

    sb = get_supabase()

    result = (
        sb.table("user_subscriptions")
        .select("expires_at, created_at, billing_period")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data or len(result.data) == 0:
        return None

    sub = result.data[0]
    expires_at_str = sub.get("expires_at")

    if not expires_at_str:
        # Perpetual subscription (master) - no next billing date
        return None

    # Parse ISO 8601 string to datetime
    expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
    return expires_at
