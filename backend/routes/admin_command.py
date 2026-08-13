"""GAP-002 (#1579) — Admin route for Command plan provisioning (Fase 1 MVP).

POST /api/v1/admin/subscriptions/command
  Creates a Stripe Checkout Session for the SmartLic Command (enterprise) tier.

Admin-only. The existing webhook ``checkout.session.completed`` handler already
recognises ``plan_id=smartlic_command`` (see TIER-COMMAND-002 in
webhooks/handlers/checkout.py) and activates the subscription via the generic
subscription-activation path — no webhook changes needed for Fase 1.

Fase 2 (future issue) will implement the self-serve Command checkout flow.

RBAC Phase 2 (#1954): requires ``admin:ops`` role.
"""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from admin import require_admin_ops
from saas_commerce import require_saas_commerce

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin/subscriptions", tags=["admin", "command"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class CommandProvisionRequest(BaseModel):
    """Request body for provisioning a Command subscription checkout."""

    email: str = Field(
        ...,
        min_length=5,
        max_length=320,
        description="Customer email for the Stripe Checkout session.",
    )
    org_id: str | None = Field(
        default=None,
        description="Optional organisation identifier for metadata tracking.",
    )


class CommandProvisionResponse(BaseModel):
    """Response returned after creating the Command checkout session."""

    checkout_url: str
    session_id: str
    plan_id: str = Field(default="smartlic_command")


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post("/command", response_model=CommandProvisionResponse)
async def provision_command_subscription(
    req: CommandProvisionRequest,
    admin: dict = Depends(require_admin_ops),
    _frozen=Depends(require_saas_commerce),
) -> CommandProvisionResponse:
    """Create a Stripe Checkout session for the SmartLic Command (enterprise) tier.

    Uses the price ID from the ``COMMAND_PRICE_ID`` environment variable.
    The session is created in ``mode='subscription'`` with metadata that
    the existing ``checkout.session.completed`` webhook handler recognises
    (see TIER-COMMAND-002 in webhooks/handlers/checkout.py).

    Returns the Stripe Checkout URL and session ID.
    """
    actor_email = admin.get("email", "admin@unknown")
    logger.info(
        "Admin provisioning Command checkout — "
        "email=%s org_id=%s actor=%s",
        req.email,
        req.org_id,
        actor_email,
    )

    command_price_id = os.getenv("COMMAND_PRICE_ID", "")
    if not command_price_id:
        logger.error("COMMAND_PRICE_ID not configured")
        raise HTTPException(
            status_code=500,
            detail="Preco Command nao configurado. Contate o suporte.",
        )

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        logger.error("STRIPE_SECRET_KEY not configured for Command checkout")
        raise HTTPException(
            status_code=500,
            detail="Servico de pagamento nao configurado. Contate o suporte.",
        )

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    import stripe as stripe_lib

    session_params = {
        "payment_method_types": ["card", "boleto"],
        "line_items": [{"price": command_price_id, "quantity": 1}],
        "mode": "subscription",
        "success_url": f"{frontend_url}/planos/obrigado?plan=smartlic_command",
        "cancel_url": f"{frontend_url}/admin/command?cancelled=true",
        "customer_email": req.email,
        "metadata": {
            "plan_id": "smartlic_command",
            "source": "admin_command",
            "provisioned_by": actor_email,
            "org_id": req.org_id or "",
        },
        "payment_method_options": {
            "boleto": {"expires_after_days": 3},
        },
    }

    try:
        session = stripe_lib.checkout.Session.create(**session_params, api_key=stripe_key)
    except stripe_lib.error.InvalidRequestError as e:
        logger.error(
            "Stripe InvalidRequestError on Command checkout: %s",
            e,
        )
        raise HTTPException(
            status_code=400,
            detail="Nao foi possivel iniciar o checkout Command. Verifique os dados e tente novamente.",
        )
    except stripe_lib.error.StripeError as e:
        logger.error("Stripe error on Command checkout: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Servico de pagamento temporariamente indisponivel. Tente novamente.",
        )

    logger.info(
        "Command checkout session created — session_id=%s email=%s actor=%s",
        session.id,
        req.email,
        actor_email,
    )

    return CommandProvisionResponse(
        checkout_url=session.url,
        session_id=session.id,
        plan_id="smartlic_command",
    )
