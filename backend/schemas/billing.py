"""Billing and checkout schemas."""

from pydantic import BaseModel
from typing import Any, Dict, List


class BillingPlansResponse(BaseModel):
    """Response for GET /plans (billing.py)."""
    plans: List[Dict[str, Any]]


class CheckoutResponse(BaseModel):
    """Response for POST /checkout."""
    checkout_url: str


class SetupIntentResponse(BaseModel):
    """Response for POST /v1/billing/setup-intent (STORY-CONV-003b AC2).

    Anonymous pre-signup flow: frontend creates a SetupIntent to collect
    the user's card via Stripe PaymentElement BEFORE the Supabase user
    exists. After `stripe.confirmSetup()` returns a `payment_method`,
    that id is sent to POST /v1/auth/signup.
    """
    client_secret: str
    publishable_key: str
