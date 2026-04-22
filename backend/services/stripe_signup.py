"""Stripe integration for signup flow (STORY-CONV-003a AC1).

Encapsulates the "cartão obrigatório no trial" path:

1. Create Stripe Customer for the new user.
2. Attach the PaymentMethod coming from the frontend PaymentElement.
3. Set it as the Customer's default invoice payment method.
4. Create a Subscription with `trial_period_days=14` and
   `default_payment_method=pm_id` so Stripe auto-charges at trial end.

All Stripe calls use idempotency keys derived from `signup-{email}-{utc_date}`
to keep retries safe. The service does **not** touch Supabase — the caller
(route) is responsible for persisting `stripe_customer_id`,
`stripe_subscription_id`, `stripe_default_pm_id` on the `profiles` row.

Failure policy (AC2 line 33): callers MUST catch `StripeSignupError` and
still let the user log in — trial is tracked locally via the 14-day grace
period, and billing reconciliation (STORY-314) can retry later.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional, TypedDict

import stripe

logger = logging.getLogger(__name__)


class StripeSignupError(Exception):
    """Raised when any Stripe signup step fails.

    The route handler catches this and returns a 200 signup response with
    `stripe_customer_id=None` so the user can still access the app during
    the grace period.
    """

    def __init__(
        self,
        message: str,
        *,
        step: str,
        stripe_code: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.step = step
        self.stripe_code = stripe_code
        self.customer_id = customer_id


class SignupStripeResult(TypedDict):
    """Return shape from `create_customer_and_subscription`."""

    customer_id: str
    subscription_id: str
    trial_end_ts: Optional[int]
    default_pm_id: str


def _build_idempotency_key(email: str, step: str) -> str:
    """Generate a deterministic idempotency key.

    Format: ``signup-{step}-{email_lower}-{utc_date}``.
    Stripe accepts up to 255 chars — email-derived keys stay well under that.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"signup-{step}-{email.strip().lower()}-{today}"


def _require_api_key() -> str:
    """Fetch the Stripe secret key from env or raise."""
    api_key = os.getenv("STRIPE_SECRET_KEY")
    if not api_key:
        raise StripeSignupError(
            "STRIPE_SECRET_KEY not configured",
            step="config",
        )
    return api_key


def _require_price_id() -> str:
    """Fetch the Stripe price id for SmartLic Pro trial subscription."""
    price_id = (
        os.getenv("STRIPE_SMARTLIC_PRO_PRICE_ID")
        or os.getenv("STRIPE_PRICE_ID_SMARTLIC_PRO_MONTHLY")
    )
    if not price_id:
        raise StripeSignupError(
            "STRIPE_SMARTLIC_PRO_PRICE_ID not configured",
            step="config",
        )
    return price_id


def create_customer_and_subscription(
    email: str,
    payment_method_id: str,
    *,
    trial_period_days: int = 14,
    user_id: Optional[str] = None,
) -> SignupStripeResult:
    """Run the full Stripe signup dance and return identifiers.

    Steps (each idempotency-keyed):

    1. `stripe.Customer.create(email=email, payment_method=pm_id, invoice_settings=...)`
    2. `stripe.PaymentMethod.attach(pm_id, customer=cus_id)`
    3. `stripe.Customer.modify(cus_id, invoice_settings.default_payment_method=pm_id)`
    4. `stripe.Subscription.create(..., trial_period_days=14, default_payment_method=pm_id)`

    Args:
        email: New user's email (becomes Stripe Customer.email).
        payment_method_id: Stripe PaymentMethod ID (`pm_...`) collected from
            the frontend PaymentElement.
        trial_period_days: Free trial length. Defaults to 14 per AC1.
        user_id: Optional Supabase user id, stored in Customer metadata.

    Returns:
        SignupStripeResult with `customer_id`, `subscription_id`,
        `trial_end_ts` (Unix seconds; may be None if Stripe omits it), and
        `default_pm_id`.

    Raises:
        StripeSignupError: on any Stripe failure. Inspect `.step` and
            `.stripe_code` to classify — the route should fail open (create
            user but skip subscription) when this fires.
    """

    if not payment_method_id or not payment_method_id.startswith("pm_"):
        raise StripeSignupError(
            f"Invalid payment_method_id: {payment_method_id!r}",
            step="validate",
        )

    api_key = _require_api_key()
    price_id = _require_price_id()

    # 1. Create the Customer (idempotent by email+date).
    try:
        customer = stripe.Customer.create(
            email=email,
            metadata={"user_id": user_id} if user_id else {},
            api_key=api_key,
            idempotency_key=_build_idempotency_key(email, "customer"),
        )
    except stripe.error.StripeError as exc:
        logger.error(
            "Stripe customer creation failed: email=%s*** code=%s",
            email[:3],
            getattr(exc, "code", None),
        )
        raise StripeSignupError(
            f"Failed to create Stripe customer: {exc}",
            step="customer_create",
            stripe_code=getattr(exc, "code", None),
        ) from exc

    customer_id = customer["id"] if isinstance(customer, dict) else customer.id

    # 2. Attach PM to the customer.
    try:
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id,
            api_key=api_key,
            idempotency_key=_build_idempotency_key(email, "pm_attach"),
        )
    except stripe.error.StripeError as exc:
        logger.error(
            "Stripe PM attach failed: customer=%s*** pm=%s*** code=%s",
            customer_id[:6],
            payment_method_id[:6],
            getattr(exc, "code", None),
        )
        raise StripeSignupError(
            f"Failed to attach payment method: {exc}",
            step="pm_attach",
            stripe_code=getattr(exc, "code", None),
            customer_id=customer_id,
        ) from exc

    # 3. Set as default PM on the customer (for invoice charges post-trial).
    try:
        stripe.Customer.modify(
            customer_id,
            invoice_settings={"default_payment_method": payment_method_id},
            api_key=api_key,
            idempotency_key=_build_idempotency_key(email, "customer_default_pm"),
        )
    except stripe.error.StripeError as exc:
        logger.error(
            "Stripe customer default-PM modify failed: customer=%s*** code=%s",
            customer_id[:6],
            getattr(exc, "code", None),
        )
        raise StripeSignupError(
            f"Failed to set default payment method: {exc}",
            step="customer_default_pm",
            stripe_code=getattr(exc, "code", None),
            customer_id=customer_id,
        ) from exc

    # 4. Create the Subscription with trial.
    try:
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            trial_period_days=trial_period_days,
            default_payment_method=payment_method_id,
            metadata={
                "plan_id": "smartlic_pro",
                "source": "signup_with_card",
                "user_id": user_id or "",
            },
            api_key=api_key,
            idempotency_key=_build_idempotency_key(email, "subscription"),
        )
    except stripe.error.StripeError as exc:
        logger.error(
            "Stripe subscription create failed: customer=%s*** code=%s",
            customer_id[:6],
            getattr(exc, "code", None),
        )
        raise StripeSignupError(
            f"Failed to create subscription: {exc}",
            step="subscription_create",
            stripe_code=getattr(exc, "code", None),
            customer_id=customer_id,
        ) from exc

    subscription_id = (
        subscription["id"] if isinstance(subscription, dict) else subscription.id
    )
    trial_end_ts = (
        subscription.get("trial_end")
        if isinstance(subscription, dict)
        else getattr(subscription, "trial_end", None)
    )

    logger.info(
        "Stripe signup successful: customer=%s*** subscription=%s*** trial_end=%s",
        customer_id[:6],
        subscription_id[:6],
        trial_end_ts,
    )

    return SignupStripeResult(
        customer_id=customer_id,
        subscription_id=subscription_id,
        trial_end_ts=int(trial_end_ts) if trial_end_ts else None,
        default_pm_id=payment_method_id,
    )
