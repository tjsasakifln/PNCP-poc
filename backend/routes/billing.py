"""Billing routes - plans and checkout.

Extracted from main.py as part of STORY-202 monolith decomposition.
"""

import logging
import os

from fastapi import APIRouter, HTTPException, Depends, Query
from auth import require_auth
from database import get_db
from log_sanitizer import mask_user_id, log_user_action
from schemas import BillingPlansResponse, CheckoutResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["billing"])


@router.get("/plans", response_model=BillingPlansResponse)
async def get_plans(db=Depends(get_db)):
    """Get available subscription plans."""
    result = (
        db.table("plans")
        .select("id, name, description, max_searches, price_brl, duration_days, stripe_price_id_monthly, stripe_price_id_annual")
        .eq("is_active", True)
        .order("price_brl")
        .execute()
    )
    return {"plans": result.data}


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    plan_id: str = Query(...),
    billing_period: str = Query("monthly"),
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """Create Stripe Checkout session for a plan purchase."""
    import stripe as stripe_lib

    if billing_period not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="billing_period deve ser 'monthly' ou 'annual'")

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    # NOTE: stripe_lib.api_key NOT set globally (thread safety - STORY-221 Track 2)
    # Pass api_key= parameter to Stripe API calls instead

    plan_result = db.table("plans").select("*").eq("id", plan_id).eq("is_active", True).single().execute()
    if not plan_result.data:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")

    plan = plan_result.data

    price_id_key = f"stripe_price_id_{billing_period}"
    stripe_price_id = plan.get(price_id_key) or plan.get("stripe_price_id")
    if not stripe_price_id:
        raise HTTPException(status_code=400, detail="Plano sem preco Stripe configurado")

    is_subscription = plan_id in ("consultor_agil", "maquina", "sala_guerra")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    session_params = {
        "payment_method_types": ["card"],
        "line_items": [{"price": stripe_price_id, "quantity": 1}],
        "mode": "subscription" if is_subscription else "payment",
        "success_url": f"{frontend_url}/planos/obrigado?plan={plan_id}",
        "cancel_url": f"{frontend_url}/planos?cancelled=true",
        "client_reference_id": user["id"],
        "metadata": {"plan_id": plan_id, "user_id": user["id"], "billing_period": billing_period},
    }

    session_params["customer_email"] = user["email"]

    checkout_session = stripe_lib.checkout.Session.create(**session_params, api_key=stripe_key)
    return {"checkout_url": checkout_session.url}


def _activate_plan(user_id: str, plan_id: str, stripe_session: dict):
    """Activate a plan for a user after successful payment."""
    from supabase_client import get_supabase
    from datetime import datetime, timezone, timedelta
    sb = get_supabase()

    plan = sb.table("plans").select("*").eq("id", plan_id).single().execute()
    if not plan.data:
        logger.error(f"Plan {plan_id} not found during activation")
        return

    p = plan.data
    expires_at = None
    if p["duration_days"]:
        expires_at = (datetime.now(timezone.utc) + timedelta(days=p["duration_days"])).isoformat()

    sb.table("user_subscriptions").update({"is_active": False}).eq("user_id", user_id).eq("is_active", True).execute()

    sb.table("user_subscriptions").insert({
        "user_id": user_id,
        "plan_id": plan_id,
        "credits_remaining": p["max_searches"],
        "expires_at": expires_at,
        "stripe_subscription_id": stripe_session.get("subscription"),
        "stripe_customer_id": stripe_session.get("customer"),
        "is_active": True,
    }).execute()

    sb.table("profiles").update({"plan_type": plan_id}).eq("id", user_id).execute()

    log_user_action(logger, "plan-activated", user_id, details={"plan_id": plan_id})
