"""Billing and checkout schemas."""

from pydantic import BaseModel
from typing import Any, Dict, List


class BillingPlansResponse(BaseModel):
    """Response for GET /plans (billing.py)."""
    plans: List[Dict[str, Any]]


class CheckoutResponse(BaseModel):
    """Response for POST /checkout."""
    checkout_url: str
