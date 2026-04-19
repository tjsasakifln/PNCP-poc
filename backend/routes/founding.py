"""STORY-BIZ-001: Founding customer Stripe coupon landing.

Endpoint: POST /v1/founding/checkout

Takes a qualifying form submission from /founding landing, creates a Stripe
Checkout Session with the FOUNDING30 coupon pre-applied, persists the lead
in `founding_leads` for follow-up, and returns the checkout URL.

The FOUNDING30 coupon itself is provisioned out-of-band in the Stripe
Dashboard (30% off for 12 months, 10 uses, first_time_transaction only) —
see `docs/runbooks/stripe-coupons.md`.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from rate_limiter import require_rate_limit
from supabase_client import get_supabase


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/founding", tags=["founding"])


FOUNDING_COUPON_ID = os.getenv("FOUNDING_COUPON_ID", "FOUNDING30")
FOUNDING_PLAN_ID = os.getenv("FOUNDING_PLAN_ID", "smartlic_pro")
FOUNDING_BILLING_PERIOD = os.getenv("FOUNDING_BILLING_PERIOD", "annual")


class FoundingCheckoutRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=320)
    nome: str = Field(..., min_length=2, max_length=200)
    cnpj: str = Field(..., min_length=11, max_length=18)
    razao_social: str | None = Field(default=None, max_length=300)
    motivo: str = Field(..., min_length=140, max_length=1000)

    @field_validator("cnpj")
    @classmethod
    def _validate_cnpj(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos")
        if not _is_valid_cnpj_check_digits(digits):
            raise ValueError("CNPJ inválido (dígito verificador)")
        return digits

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@", 1)[1]:
            raise ValueError("Email inválido")
        return v


class FoundingCheckoutResponse(BaseModel):
    checkout_url: str
    lead_id: str


def _is_valid_cnpj_check_digits(cnpj: str) -> bool:
    """Validate Brazilian CNPJ check digits. `cnpj` must be 14 digits already."""
    if len(cnpj) != 14 or not cnpj.isdigit():
        return False
    # Trivial rejection: all identical digits ("00000000000000" etc.)
    if cnpj == cnpj[0] * 14:
        return False

    def _compute(digits: str, weights: list[int]) -> int:
        total = sum(int(d) * w for d, w in zip(digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6] + w1
    d1 = _compute(cnpj[:12], w1)
    if d1 != int(cnpj[12]):
        return False
    d2 = _compute(cnpj[:13], w2)
    return d2 == int(cnpj[13])


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _already_registered(sb, email: str) -> bool:
    """Return True if the email already owns a profile. Best-effort, non-blocking."""
    try:
        res = sb.table("profiles").select("id").eq("email", email).limit(1).execute()
        return bool(res.data)
    except Exception as e:
        logger.warning(f"founding: profile lookup failed (non-blocking): {e}")
        return False


def _lookup_promotion_code(stripe_lib, api_key: str) -> dict | None:
    """Resolve the FOUNDING30 coupon into a promotion_code for use in discounts.

    Prefer PromotionCode (user-facing) over raw Coupon so Stripe enforces
    `restrictions.first_time_transaction=true` configured at promo-code level.
    """
    try:
        promos = stripe_lib.PromotionCode.list(
            code=FOUNDING_COUPON_ID,
            active=True,
            limit=1,
            api_key=api_key,
        )
        if promos.data:
            return {"promotion_code": promos.data[0].id}
    except Exception as e:
        logger.warning(f"founding: promotion_code lookup failed: {e}")

    # Fall back to the coupon id directly (still valid for discounts=)
    return {"coupon": FOUNDING_COUPON_ID}


@router.post("/checkout", response_model=FoundingCheckoutResponse)
async def founding_checkout(
    payload: FoundingCheckoutRequest,
    request: Request,
    _rl=Depends(require_rate_limit(3, 3600)),
) -> Any:
    """Create a founding-customer Stripe Checkout Session with FOUNDING30 applied.

    Side effects:
    - Inserts a `founding_leads` row with `checkout_status='pending'`.
    - Later webhook events (`checkout.session.completed` / `expired`) update it.
    """
    import stripe as stripe_lib

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        logger.error("founding: STRIPE_SECRET_KEY not configured")
        raise HTTPException(status_code=500, detail="Erro ao processar pagamento. Tente novamente.")

    sb = get_supabase()

    if _already_registered(sb, payload.email):
        raise HTTPException(
            status_code=409,
            detail="Este email já possui conta SmartLic. Faça login para gerenciar sua assinatura.",
        )

    bp_result = (
        sb.table("plan_billing_periods")
        .select("stripe_price_id")
        .eq("plan_id", FOUNDING_PLAN_ID)
        .eq("billing_period", FOUNDING_BILLING_PERIOD)
        .limit(1)
        .execute()
    )
    stripe_price_id = (bp_result.data[0] or {}).get("stripe_price_id") if bp_result.data else None
    if not stripe_price_id:
        logger.error(
            f"founding: no stripe_price_id for plan={FOUNDING_PLAN_ID} "
            f"billing_period={FOUNDING_BILLING_PERIOD}"
        )
        raise HTTPException(status_code=400, detail="Plano sem configuração de preço")

    lead_row = {
        "email": payload.email,
        "nome": payload.nome,
        "cnpj": payload.cnpj,
        "razao_social": payload.razao_social,
        "motivo": payload.motivo,
        "ip_address": _client_ip(request),
        "user_agent": request.headers.get("user-agent", "")[:500],
    }

    lead_insert = sb.table("founding_leads").insert(lead_row).execute()
    lead_record = (lead_insert.data or [{}])[0]
    lead_id = lead_record.get("id")
    if not lead_id:
        logger.error("founding: Supabase insert returned no id")
        raise HTTPException(status_code=500, detail="Erro ao registrar sua solicitação.")

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    discount = _lookup_promotion_code(stripe_lib, stripe_key)

    session_params = {
        "payment_method_types": ["card"],
        "line_items": [{"price": stripe_price_id, "quantity": 1}],
        "mode": "subscription",
        "success_url": f"{frontend_url}/founding/obrigado?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{frontend_url}/founding?cancelled=true",
        "customer_email": payload.email,
        "metadata": {
            "source": "founding",
            "founding_lead_id": lead_id,
            "cnpj": payload.cnpj,
            "plan_id": FOUNDING_PLAN_ID,
            "billing_period": FOUNDING_BILLING_PERIOD,
        },
        "discounts": [discount],
    }

    try:
        session = stripe_lib.checkout.Session.create(**session_params, api_key=stripe_key)
    except stripe_lib.error.InvalidRequestError as e:
        logger.error(
            f"founding: Stripe InvalidRequestError — cnpj={payload.cnpj} "
            f"lead_id={lead_id} err={e}"
        )
        raise HTTPException(
            status_code=400,
            detail="Não foi possível iniciar o checkout. Verifique os dados e tente novamente.",
        )
    except stripe_lib.error.StripeError as e:
        logger.error(f"founding: Stripe error — lead_id={lead_id} err={e}")
        raise HTTPException(
            status_code=503,
            detail="Serviço de pagamento temporariamente indisponível. Tente novamente em instantes.",
        )

    try:
        sb.table("founding_leads").update({
            "checkout_session_id": session.id,
        }).eq("id", lead_id).execute()
    except Exception as e:
        logger.warning(f"founding: failed to persist session_id — lead_id={lead_id} err={e}")

    logger.info(
        f"founding: checkout session created — lead_id={lead_id} "
        f"session_id={session.id} email={payload.email} cnpj={payload.cnpj[:4]}***"
    )

    return FoundingCheckoutResponse(checkout_url=session.url, lead_id=lead_id)
