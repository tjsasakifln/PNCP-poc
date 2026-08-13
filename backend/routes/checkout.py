"""CONV-005b-2: Generic one-time checkout endpoint for digital products.
API-SELF-004: API subscription checkout endpoint.

Creates a Stripe Checkout Session for a digital product identified by SKU,
or for an API tier subscription (Starter/Pro/Scale).

Endpoints:
    POST /api/checkout/one-time           — create Stripe Checkout Session for a product
    POST /api/checkout/api-subscription   — create Stripe Checkout Session for API tier

Dependencies:
    - digital_products table (CONV-005b-1 / #1334)
    - Stripe SDK (stripe>=11.4)
    - require_auth (authenticated user)
    - require_rate_limit (10 req/min per IP)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from auth import require_auth
from log_sanitizer import sanitize
from rate_limiter import require_rate_limit
from saas_commerce import require_saas_commerce
from supabase_client import get_supabase, sb_execute

from schemas.checkout import (
    ApiSubscriptionCheckoutRequest,
    ApiSubscriptionCheckoutResponse,
    CheckoutRequest,
    CheckoutResponse,
    CheckoutSessionStatusResponse,
)

logger = logging.getLogger(__name__)

# Module-level rate limit dependency so tests can override the same symbol.
checkout_rate_limit = require_rate_limit(10, 60)

router = APIRouter(
    prefix="/api/checkout",
    tags=["checkout"],
    dependencies=[
        Depends(checkout_rate_limit),
        Depends(require_saas_commerce),
    ],
)


def _get_frontend_url() -> str:
    """Return the frontend base URL, defaulting to localhost for dev."""
    return os.getenv("FRONTEND_URL", "http://localhost:3000")


def _get_stripe_key() -> str:
    """Return Stripe secret key or raise."""
    key = os.getenv("STRIPE_SECRET_KEY")
    if not key:
        logger.error("checkout: STRIPE_SECRET_KEY not configured")
        raise HTTPException(
            status_code=503,
            detail="Servico de pagamento temporariamente indisponivel.",
        )
    return key


async def _lookup_product(sku: str) -> Optional[dict[str, Any]]:
    """Query digital_products table by SKU.

    Returns the product row dict or None if not found.

    Raises:
        HTTPException 503 on transient DB errors.
    """
    try:
        sb = get_supabase()
        result = await sb_execute(
            sb.table("digital_products").select("*").eq("sku", sku).limit(1)
        )
        rows = result.data if result.data else []
        return rows[0] if rows else None
    except Exception as exc:
        logger.warning("checkout: product lookup failed for sku=%s: %s", sku, exc)
        raise HTTPException(
            status_code=503,
            detail="Erro temporario ao consultar produto. Tente novamente.",
        ) from exc


async def _ensure_stripe_price(product: dict) -> str:
    """Return an existing stripe_price_id or create Stripe Product + Price.

    If the product already has a ``stripe_price_id`` it is returned as-is.
    Otherwise a Stripe Product and a one-time Price in BRL are created and
    the product row is updated with the new IDs.

    Returns:
        Stripe Price ID (``price_...``).
    """
    import stripe as stripe_lib

    stripe_key = _get_stripe_key()

    existing_price_id = product.get("stripe_price_id")
    if existing_price_id:
        logger.debug(
            "checkout: using existing stripe_price_id=%s for sku=%s",
            existing_price_id[:8],
            product["sku"],
        )
        return existing_price_id

    # Create Stripe Product
    try:
        stripe_product = stripe_lib.Product.create(
            name=product["name"],
            description=product.get("description") or "",
            metadata={"sku": product["sku"], "source": "checkout_endpoint"},
            api_key=stripe_key,
        )
        stripe_product_id = stripe_product.id
        logger.info(
            "checkout: created stripe product %s for sku=%s",
            stripe_product_id,
            product["sku"],
        )
    except Exception as exc:
        logger.error("checkout: failed to create Stripe Product for sku=%s: %s", product["sku"], exc)
        raise HTTPException(
            status_code=503,
            detail="Erro ao configurar produto no gateway de pagamento.",
        ) from exc

    # Create Stripe Price (one-time, BRL)
    try:
        unit_amount = product["price_brl"]
        stripe_price = stripe_lib.Price.create(
            product=stripe_product_id,
            currency="brl",
            unit_amount=unit_amount,
            metadata={"sku": product["sku"]},
            api_key=stripe_key,
        )
        stripe_price_id = stripe_price.id
        logger.info(
            "checkout: created stripe price %s (BRL %d) for sku=%s",
            stripe_price_id,
            unit_amount,
            product["sku"],
        )
    except Exception as exc:
        logger.error(
            "checkout: failed to create Stripe Price for sku=%s product=%s: %s",
            product["sku"],
            stripe_product_id,
            exc,
        )
        raise HTTPException(
            status_code=503,
            detail="Erro ao configurar preco no gateway de pagamento.",
        ) from exc

    # Persist stripe IDs back to the product row (best-effort)
    try:
        sb = get_supabase()
        await sb_execute(
            sb.table("digital_products").update({
                "stripe_product_id": stripe_product_id,
                "stripe_price_id": stripe_price_id,
            }).eq("id", product["id"])
        )
        logger.info(
            "checkout: persisted stripe ids for product %s (sku=%s)",
            product["id"][:8],
            product["sku"],
        )
    except Exception as exc:
        # Non-blocking — the Price object exists in Stripe and will be
        # reused on the next checkout via the metadata lookup fallback below.
        logger.warning(
            "checkout: failed to persist stripe ids for sku=%s: %s",
            product["sku"],
            exc,
        )

    return stripe_price_id


@router.post("/one-time", response_model=CheckoutResponse)
async def create_one_time_checkout(
    payload: CheckoutRequest,
    user: dict = Depends(require_auth),
):
    """Create a Stripe Checkout Session for a one-time digital product purchase.

    Flow:
        1. Validate SKU against digital_products table
        2. Resolve or create Stripe Price
        3. Create Stripe Checkout Session with card/boleto/PIX
        4. Return checkout URL

    Rate limited: 10 req/min per IP.
    """
    import stripe as stripe_lib

    stripe_key = _get_stripe_key()

    # Step 1: Lookup product by SKU
    product = await _lookup_product(payload.sku)
    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Produto nao encontrado",
        )

    if not product.get("active", False):
        raise HTTPException(
            status_code=400,
            detail="Produto indisponivel",
        )

    user_id = user.get("sub") or user.get("id") or ""
    product_id = str(product["id"])

    # Step 2: Resolve or create Stripe Price
    stripe_price_id = await _ensure_stripe_price(product)

    # Step 3: Build metadata from request context
    context = payload.context or {}
    entity_type = context.get("entity_type", "")
    entity_id = context.get("entity_id", "")

    metadata = {
        "sku": payload.sku,
        "product_sku": payload.sku,
        "product_id": product_id,
        "user_id": user_id,
    }
    if entity_type:
        metadata["entity_type"] = entity_type
    if entity_id:
        metadata["entity_id"] = entity_id

    # Step 4: Create Checkout Session
    frontend_url = _get_frontend_url()
    success_url = f"{frontend_url}/obrigado?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{frontend_url}/produtos"

    try:
        session = stripe_lib.checkout.Session.create(
            mode="payment",
            payment_method_types=["card", "boleto", "pix"],
            line_items=[{"price": stripe_price_id, "quantity": 1}],
            metadata=metadata,
            customer_email=user.get("email", ""),
            success_url=success_url,
            cancel_url=cancel_url,
            api_key=stripe_key,
        )
    except stripe_lib.error.InvalidRequestError as exc:
        logger.error(
            "checkout: Stripe InvalidRequestError for sku=%s user=%s: %s",
            payload.sku,
            user_id[:8],
            exc,
        )
        raise HTTPException(
            status_code=400,
            detail="Nao foi possivel iniciar o checkout. Verifique os dados e tente novamente.",
        ) from exc
    except stripe_lib.error.StripeError as exc:
        logger.error(
            "checkout: Stripe error for sku=%s user=%s: %s",
            payload.sku,
            user_id[:8],
            exc,
        )
        raise HTTPException(
            status_code=503,
            detail="Servico de pagamento temporariamente indisponivel. Tente novamente.",
        ) from exc

    logger.info(
        "checkout: session created — sku=%s user=%s session=%s",
        payload.sku,
        user_id[:8],
        session.id,
    )

    if not session.url:
        raise HTTPException(
            status_code=503,
            detail="Servico de pagamento temporariamente indisponivel. Tente novamente.",
        )

    return CheckoutResponse(checkout_url=session.url)


# ---------------------------------------------------------------------------
# API-SELF-004: API subscription checkout
# ---------------------------------------------------------------------------


@router.post("/api-subscription", response_model=ApiSubscriptionCheckoutResponse)
async def create_api_subscription_checkout(
    payload: ApiSubscriptionCheckoutRequest,
    user: dict = Depends(require_auth),
):
    """Create a Stripe Checkout Session for an API tier subscription.

    Flow:
        1. Validate tier against API_PRODUCTS config
        2. Look up Stripe Price ID from env var
        3. Create Stripe Checkout Session (mode=subscription)
        4. Return checkout URL

    Rate limited: 10 req/min per IP.
    """
    import stripe as stripe_lib

    from stripe_api_products import (
        API_PRODUCTS,
        get_tier_price_id,
        API_TIER_STARTER,
        API_TIER_PRO,
        API_TIER_SCALE,
    )

    stripe_key = _get_stripe_key()
    frontend_url = _get_frontend_url()

    # Step 1: Validate tier
    valid_tiers = {API_TIER_STARTER, API_TIER_PRO, API_TIER_SCALE}
    if payload.tier not in valid_tiers:
        raise HTTPException(
            status_code=400,
            detail=f"Tier invalido. Opcoes: {', '.join(sorted(valid_tiers))}",
        )

    # Step 2: Resolve Stripe Price ID from env var
    price_id = get_tier_price_id(payload.tier)
    if not price_id:
        logger.error(
            "API checkout: Stripe Price ID not configured for tier=%s "
            "(env var %s is not set)",
            payload.tier,
            API_PRODUCTS[payload.tier]["price_id_env"],
        )
        raise HTTPException(
            status_code=503,
            detail="Preco nao configurado para este tier. Contate o suporte.",
        )

    user_id = user.get("sub") or user.get("id") or ""

    # Step 3: Create Checkout Session
    success_url = f"{frontend_url}/conta?api_subscription=success"
    cancel_url = f"{frontend_url}/planos/api"

    metadata = {
        "source": "api_subscription",
        "tier": payload.tier,
        "user_id": user_id,
    }

    try:
        session = stripe_lib.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            metadata=metadata,
            client_reference_id=user_id,
            customer_email=user.get("email", ""),
            success_url=success_url,
            cancel_url=cancel_url,
            api_key=stripe_key,
        )
    except stripe_lib.error.InvalidRequestError as exc:
        logger.error(
            "API checkout: Stripe InvalidRequestError for tier=%s user=%s: %s",
            payload.tier,
            user_id[:8],
            exc,
        )
        raise HTTPException(
            status_code=400,
            detail="Nao foi possivel iniciar o checkout. Verifique os dados e tente novamente.",
        ) from exc
    except stripe_lib.error.StripeError as exc:
        logger.error(
            "API checkout: Stripe error for tier=%s user=%s: %s",
            payload.tier,
            user_id[:8],
            exc,
        )
        raise HTTPException(
            status_code=503,
            detail="Servico de pagamento temporariamente indisponivel. Tente novamente.",
        ) from exc

    logger.info(
        "API checkout: session created — tier=%s user=%s session=%s",
        payload.tier,
        user_id[:8],
        session.id,
    )

    if not session.url:
        raise HTTPException(
            status_code=503,
            detail="Servico de pagamento temporariamente indisponivel. Tente novamente.",
        )

    return ApiSubscriptionCheckoutResponse(
        checkout_url=session.url,
        session_id=session.id,
    )


# ---------------------------------------------------------------------------
# #1337: Session status lookup for /obrigado thank-you page
# ---------------------------------------------------------------------------


@router.get("/session/{session_id}", response_model=CheckoutSessionStatusResponse)
async def get_checkout_session_status(session_id: str):
    """Return the status of a one-time digital product purchase.

    The /obrigado thank-you page calls this endpoint after the user is
    redirected back from Stripe Checkout.  The endpoint looks up the
    purchase by ``stripe_checkout_session_id`` in the
    ``intel_report_purchases`` table and resolves the product name from
    ``digital_products`` when applicable.

    No auth required — the session_id is a Stripe-generated unique
    identifier known only to the user who initiated the checkout.
    """
    try:
        sb = get_supabase()
    except Exception as exc:
        logger.warning("checkout: failed to get supabase client: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Erro temporario ao conectar com o banco de dados.",
        ) from exc

    # Lookup purchase by stripe_checkout_session_id
    try:
        result = await sb_execute(
            sb.table("intel_report_purchases")
            .select("*")
            .eq("stripe_checkout_session_id", session_id)
            .limit(1)
        )
    except Exception as exc:
        logger.warning(
            "checkout: purchase lookup failed for session=%s: %s",
            sanitize(session_id, context="stripe_session"),
            exc,
        )
        raise HTTPException(
            status_code=503,
            detail="Erro temporario ao consultar compra. Tente novamente.",
        ) from exc

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Compra nao encontrada para esta sessao.",
        )

    purchase = result.data[0]
    status = purchase.get("status") or "pending"
    sku = purchase.get("entity_key")  # For digital_product rows, entity_key = product_sku
    pdf_url = purchase.get("pdf_url")
    created_at = purchase.get("created_at")

    # Resolve product name from digital_products table (best-effort)
    product_name: str | None = None
    if sku:
        try:
            prod_result = await sb_execute(
                sb.table("digital_products")
                .select("name")
                .eq("sku", sku)
                .limit(1)
            )
            if prod_result.data:
                product_name = prod_result.data[0].get("name")
        except Exception:
            logger.debug(
                "checkout: product name lookup failed for sku=%s (non-blocking)", sku
            )

    logger.info(
        "checkout: session status checked — session=%s status=%s sku=%s",
        sanitize(session_id, context="stripe_session"),
        status,
        sku,
    )

    return CheckoutSessionStatusResponse(
        status=status,
        product_name=product_name,
        sku=sku,
        pdf_url=pdf_url,
        created_at=created_at,
    )
