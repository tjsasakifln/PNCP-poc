"""Billing routes - plans and checkout.

Extracted from main.py as part of STORY-202 monolith decomposition.
"""

import logging
import os

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from auth import require_auth
from database import get_db
from rate_limiter import require_rate_limit, SIGNUP_RATE_LIMIT_PER_10MIN
from schemas import BillingPlansResponse, CheckoutResponse
from schemas.billing import SetupIntentResponse
from supabase_client import sb_execute

logger = logging.getLogger(__name__)

router = APIRouter(tags=["billing"])


@router.get("/plans", response_model=BillingPlansResponse)
async def get_plans(db=Depends(get_db)):
    """Get available subscription plans with billing period pricing.

    STORY-360 AC1: Single source of truth — DB (synced from Stripe) is master.
    Returns per-period pricing from plan_billing_periods table.
    Stripe price IDs stripped from response (STORY-210 AC11).
    """
    result = await sb_execute(
        db.table("plans")
        .select("id, name, description, max_searches, price_brl, duration_days")
        .eq("is_active", True)
        .order("price_brl")
    )

    # STORY-360 AC1: Fetch billing period pricing
    billing_periods_result = await sb_execute(
        db.table("plan_billing_periods")
        .select("plan_id, billing_period, price_cents, discount_percent")
        .order("plan_id")
    )

    # Index billing periods by plan_id
    bp_by_plan: dict = {}
    for bp in (billing_periods_result.data or []):
        plan_id = bp["plan_id"]
        if plan_id not in bp_by_plan:
            bp_by_plan[plan_id] = {}
        bp_by_plan[plan_id][bp["billing_period"]] = {
            "price_cents": bp["price_cents"],
            "discount_percent": bp["discount_percent"],
        }

    # Enrich plans with billing periods (no Stripe IDs)
    enriched = []
    for plan in (result.data or []):
        plan_data = {
            "id": plan["id"],
            "name": plan["name"],
            "description": plan["description"],
            "max_searches": plan["max_searches"],
            "price_brl": plan["price_brl"],
            "duration_days": plan["duration_days"],
            "billing_periods": bp_by_plan.get(plan["id"], {}),
        }
        enriched.append(plan_data)

    return {"plans": enriched}


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    plan_id: str = Query(...),
    billing_period: str = Query("monthly"),
    coupon: str | None = Query(None),
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """Create Stripe Checkout session for a plan purchase."""
    import stripe as stripe_lib

    if billing_period not in ("monthly", "semiannual", "annual"):
        raise HTTPException(status_code=400, detail="billing_period deve ser 'monthly', 'semiannual' ou 'annual'")

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Erro ao processar pagamento. Tente novamente.")
    # NOTE: stripe_lib.api_key NOT set globally (thread safety - STORY-221 Track 2)
    # Pass api_key= parameter to Stripe API calls instead

    plan_result = await sb_execute(db.table("plans").select("id, name, is_active").eq("id", plan_id).eq("is_active", True).single())
    if not plan_result.data:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")

    plan = plan_result.data  # noqa: F841

    # DEBT-114 AC1: Use plan_billing_periods as sole source of truth for stripe_price_id
    bp_result = await sb_execute(
        db.table("plan_billing_periods")
        .select("stripe_price_id")
        .eq("plan_id", plan_id)
        .eq("billing_period", billing_period)
        .single()
    )

    stripe_price_id = (bp_result.data or {}).get("stripe_price_id") if bp_result.data else None

    if not stripe_price_id:
        # DEBT-114 AC2: WARNING log for missing billing period config (safety net)
        logger.warning(
            f"DEBT-114: No stripe_price_id in plan_billing_periods for "
            f"plan_id={plan_id}, billing_period={billing_period}. "
            f"Legacy plans.stripe_price_id fallback has been removed."
        )
        raise HTTPException(status_code=400, detail="Plano sem configuração de preço")

    is_subscription = plan_id in ("smartlic_pro", "consultoria", "consultor_agil", "maquina", "sala_guerra")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # STORY-280 AC1: Boleto enabled for subscriptions
    # STORY-420 (EPIC-INCIDENT-2026-04-10): PIX removed — Stripe Brasil does not
    # accept "pix" in payment_method_types for subscription mode. Previous value
    # caused InvalidRequestError + HTTP 500 (Sentry 7397513115/7397513088/7397513083),
    # bloqueando trial → pro conversion. Follow-up em STORY-424 (Q2/2026) via
    # payment_method_options.pix path quando Stripe suportar subscriptions + PIX.
    session_params = {
        "payment_method_types": ["card", "boleto"],
        "line_items": [{"price": stripe_price_id, "quantity": 1}],
        "mode": "subscription" if is_subscription else "payment",
        "success_url": f"{frontend_url}/planos/obrigado?plan={plan_id}",
        "cancel_url": f"{frontend_url}/planos?cancelled=true",
        "client_reference_id": user["id"],
        "metadata": {"plan_id": plan_id, "user_id": user["id"], "billing_period": billing_period},
        "payment_method_options": {
            "boleto": {"expires_after_days": 3},
        },
    }

    session_params["customer_email"] = user["email"]

    # STORY-323 AC5: Apply partner coupon if partner_slug provided
    partner_slug = None  # noqa: F841
    try:
        # Check query param (passed from frontend partner cookie)
        # Note: partner_slug comes as an additional query param
        pass  # Coupon applied via allow_promotion_codes below
    except Exception:
        pass

    # Zero-churn P1 §3.2: Auto-apply coupon from URL if provided
    if coupon:
        try:
            promo_codes = stripe_lib.PromotionCode.list(code=coupon, active=True, limit=1, api_key=stripe_key)
            if promo_codes.data:
                session_params["discounts"] = [{"promotion_code": promo_codes.data[0].id}]
                logger.info(f"Auto-applied coupon '{coupon}' as promotion_code={promo_codes.data[0].id}")
            else:
                logger.warning(f"Coupon '{coupon}' not found or inactive in Stripe")
                session_params["allow_promotion_codes"] = True
        except Exception as e:
            logger.warning(f"Failed to lookup coupon '{coupon}': {e}")
            session_params["allow_promotion_codes"] = True
    else:
        # STORY-323 AC5: Allow promotion codes at checkout (partner coupons)
        session_params["allow_promotion_codes"] = True

    # STORY-420 (EPIC-INCIDENT-2026-04-10): Surface Stripe config errors as HTTP 400
    # so client can render actionable message instead of generic 500.
    try:
        checkout_session = stripe_lib.checkout.Session.create(**session_params, api_key=stripe_key)
    except stripe_lib.error.InvalidRequestError as e:
        stripe_request_id = getattr(e, "request_id", None)
        logger.error(
            "Stripe InvalidRequestError on checkout session create: "
            f"user_id={user['id']} plan_id={plan_id} billing_period={billing_period} "
            f"stripe_request_id={stripe_request_id} error={e}"
        )
        raise HTTPException(
            status_code=400,
            detail="Não foi possível iniciar o checkout. Verifique os dados e tente novamente em instantes.",
        )
    except stripe_lib.error.StripeError as e:
        logger.error(f"Stripe error on checkout session create: {e}")
        raise HTTPException(
            status_code=503,
            detail="Serviço de pagamento temporariamente indisponível. Tente novamente em instantes.",
        )
    return {"checkout_url": checkout_session.url}


# GTM-FIX-001: _activate_plan() removed — was dead code never called from any handler.
# Plan activation is handled by _handle_checkout_session_completed() in webhooks/stripe.py,
# which is the canonical path: Stripe checkout.session.completed webhook -> activate subscription.
# That handler includes billing_period, subscription_status sync, and Redis cache invalidation.


@router.post("/billing-portal")
async def create_billing_portal_session(
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """
    Create Stripe Billing Portal session (GTM-FIX-007 AC6-AC7).

    Allows users to update payment methods, view invoices, and manage subscriptions.

    Returns:
        dict: {"url": "https://billing.stripe.com/..."}
    """
    import stripe as stripe_lib

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Erro ao processar pagamento. Tente novamente.")

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Get user's stripe_customer_id from active subscription
    sub_result = await sb_execute(
        db.table("user_subscriptions")
        .select("stripe_customer_id")
        .eq("user_id", user["id"])
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
    )

    if not sub_result.data or not sub_result.data[0].get("stripe_customer_id"):
        raise HTTPException(
            status_code=404,
            detail="Nenhuma assinatura ativa encontrada. Assine um plano primeiro."
        )

    stripe_customer_id = sub_result.data[0]["stripe_customer_id"]

    try:
        # Create Stripe Billing Portal session
        portal_session = stripe_lib.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{frontend_url}/conta",
            api_key=stripe_key,
        )

        logger.info(f"Billing portal session created for user_id={user['id']}")
        return {"url": portal_session.url}

    except stripe_lib.error.StripeError as e:
        logger.error(f"Stripe billing portal error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar sessão do portal de cobrança")


@router.get("/subscription/status")
async def get_subscription_status(
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """
    Check subscription activation status (GTM-FIX-016).

    Used by obrigado page to poll for webhook completion.
    Returns current subscription state from DB, with Stripe API fallback.
    """
    import stripe as stripe_lib

    user_id = user["id"]

    # CRIT-005 AC25: Surface DB errors instead of silently returning defaults
    try:
        # Check DB first (webhook already processed?)
        sub_result = await sb_execute(
            db.table("user_subscriptions")
            .select("plan_id, subscription_status, stripe_subscription_id, created_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
        )
    except Exception as e:
        logger.error(f"Failed to check subscription status: {e}")
        raise HTTPException(status_code=503, detail="Status de assinatura temporariamente indisponível")

    if sub_result.data and sub_result.data[0].get("subscription_status") == "active":
        sub = sub_result.data[0]
        return {
            "status": "active",
            "plan_id": sub.get("plan_id"),
            "activated_at": sub.get("created_at"),
        }

    # Check profile plan_type as secondary source
    try:
        profile_result = await sb_execute(
            db.table("profiles")
            .select("plan_type")
            .eq("id", user_id)
            .single()
        )
    except Exception as e:
        logger.error(f"Failed to check profile plan_type: {e}")
        raise HTTPException(status_code=503, detail="Status de assinatura temporariamente indisponível")

    if profile_result.data and profile_result.data.get("plan_type") not in (None, "free_trial"):
        return {
            "status": "active",
            "plan_id": profile_result.data["plan_type"],
            "activated_at": None,
        }

    # Stripe API fallback: check if there's a recent checkout session
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if stripe_key and sub_result.data:
        stripe_sub_id = sub_result.data[0].get("stripe_subscription_id")
        if stripe_sub_id:
            try:
                stripe_sub = stripe_lib.Subscription.retrieve(
                    stripe_sub_id, api_key=stripe_key
                )
                if stripe_sub.status == "active":
                    return {
                        "status": "active",
                        "plan_id": sub_result.data[0].get("plan_id"),
                        "activated_at": None,
                    }
            except Exception as e:
                # CRIT-005 AC25: Surface Stripe errors instead of swallowing
                logger.warning(f"Stripe subscription check failed: {e}")
                raise HTTPException(status_code=503, detail="Status de assinatura temporariamente indisponível")

    return {
        "status": "pending",
        "plan_id": None,
        "activated_at": None,
    }


@router.post("/billing/setup-intent", response_model=SetupIntentResponse)
async def create_setup_intent(
    request: Request,
    _rl=Depends(require_rate_limit(SIGNUP_RATE_LIMIT_PER_10MIN, 600)),
):
    """Create a Stripe SetupIntent for pre-signup card capture (CONV-003b AC2).

    Anonymous endpoint: called before the Supabase user exists, so we cannot
    attach a customer yet. The returned ``payment_method`` (from
    ``stripe.confirmSetup()`` client-side) is forwarded to
    ``POST /v1/auth/signup`` which then creates the Customer and attaches
    the PM server-side via ``services.stripe_signup``.

    Rate-limited via the same bucket as signup (3 req / 10 min per IP) to
    block abuse. Returns the publishable key alongside the client secret so
    the frontend does not need a second round-trip to ``/config`` (keeps
    the signup flow to 2 network calls: setup-intent → signup).
    """
    import stripe as stripe_lib

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
    if not stripe_key or not publishable_key:
        logger.error("Stripe keys not configured for setup-intent")
        raise HTTPException(
            status_code=503,
            detail="Serviço de pagamento temporariamente indisponível.",
        )

    try:
        setup_intent = stripe_lib.SetupIntent.create(
            usage="off_session",
            payment_method_types=["card"],
            metadata={"flow": "pre_signup_trial"},
            api_key=stripe_key,
        )
    except stripe_lib.error.StripeError as exc:
        logger.error("Stripe SetupIntent.create failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Não foi possível preparar a coleta do cartão. Tente novamente em instantes.",
        ) from exc

    return SetupIntentResponse(
        client_secret=setup_intent.client_secret,
        publishable_key=publishable_key,
    )
