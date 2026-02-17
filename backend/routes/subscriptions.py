"""Subscription management routes.

Handles billing period updates and subscription modifications.
GTM-002: Removed pro-rata calculations — Stripe handles proration automatically.
"""

import logging
import os
from typing import Literal
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import stripe as stripe_lib

from auth import require_auth
from services.billing import (
    update_stripe_subscription_billing_period,
    get_next_billing_date,
)
from log_sanitizer import mask_user_id, log_user_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


class UpdateBillingPeriodRequest(BaseModel):
    """Request to update subscription billing period."""
    new_billing_period: Literal["monthly", "semiannual", "annual"] = Field(
        ...,
        description="Target billing period"
    )


class UpdateBillingPeriodResponse(BaseModel):
    """Response for billing period update."""
    success: bool
    new_billing_period: str
    next_billing_date: str
    message: str


class CancelSubscriptionResponse(BaseModel):
    """Response for subscription cancellation."""
    success: bool
    ends_at: str
    message: str


@router.post("/update-billing-period", response_model=UpdateBillingPeriodResponse)
async def update_billing_period(
    request: UpdateBillingPeriodRequest,
    user: dict = Depends(require_auth),
):
    """Update subscription billing period (monthly / semiannual / annual).

    GTM-002: Simplified flow — Stripe handles proration automatically.
    No deferral logic, no manual credit calculations.
    """
    from supabase_client import get_supabase

    user_id = user["id"]
    logger.info(
        f"Updating billing period for user {mask_user_id(user_id)} to {request.new_billing_period}"
    )

    sb = get_supabase()

    # Step 1: Fetch current active subscription
    try:
        result = (
            sb.table("user_subscriptions")
            .select("id, plan_id, billing_period, stripe_subscription_id, expires_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Nenhuma assinatura ativa encontrada")

        subscription = result.data[0]
        current_billing_period = subscription["billing_period"]
        plan_id = subscription["plan_id"]
        stripe_subscription_id = subscription.get("stripe_subscription_id")

        if current_billing_period == request.new_billing_period:
            raise HTTPException(
                status_code=400,
                detail=f"Já está no período {request.new_billing_period}"
            )

        if not stripe_subscription_id:
            raise HTTPException(status_code=400, detail="Assinatura sem Stripe subscription_id")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch subscription for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar assinatura ativa")

    # Step 2: Get plan Stripe price IDs
    try:
        plan_result = (
            sb.table("plans")
            .select("stripe_price_id_monthly, stripe_price_id_semiannual, stripe_price_id_annual")
            .eq("id", plan_id)
            .single()
            .execute()
        )

        if not plan_result.data:
            raise HTTPException(status_code=404, detail=f"Plano {plan_id} não encontrado")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar informações do plano")

    # Step 3: Update Stripe subscription (Stripe handles proration)
    try:
        update_stripe_subscription_billing_period(
            stripe_subscription_id=stripe_subscription_id,
            new_billing_period=request.new_billing_period,
            stripe_price_id_monthly=plan_result.data.get("stripe_price_id_monthly", ""),
            stripe_price_id_semiannual=plan_result.data.get("stripe_price_id_semiannual", ""),
            stripe_price_id_annual=plan_result.data.get("stripe_price_id_annual", ""),
        )
        logger.info(f"Updated Stripe subscription for user {mask_user_id(user_id)}")
    except Exception as e:
        logger.error(f"Stripe update failed for user {mask_user_id(user_id)}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao atualizar no Stripe")

    # Step 4: Update Supabase subscription
    try:
        sb.table("user_subscriptions").update({
            "billing_period": request.new_billing_period,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", subscription["id"]).execute()
    except Exception as e:
        logger.error(f"DB update failed for user {mask_user_id(user_id)}: {e}", exc_info=True)
        logger.critical(
            f"DATA INCONSISTENCY: Stripe updated but Supabase failed for user {mask_user_id(user_id)}"
        )
        raise HTTPException(status_code=500, detail="Erro ao atualizar no banco de dados")

    # Step 5: Invalidate feature cache
    try:
        from cache import redis_cache
        await redis_cache.delete(f"features:{user_id}")
    except Exception as e:
        logger.warning(f"Cache invalidation failed (non-critical): {e}")

    # Step 6: Get next billing date for response
    next_billing = get_next_billing_date(user_id)
    next_billing_str = next_billing.isoformat() if next_billing else ""

    return UpdateBillingPeriodResponse(
        success=True,
        new_billing_period=request.new_billing_period,
        next_billing_date=next_billing_str,
        message=f"Período de cobrança atualizado para {request.new_billing_period}.",
    )


@router.post("/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    user: dict = Depends(require_auth),
):
    """Cancel subscription at period end.

    GTM-FIX-006: User-initiated cancellation flow.
    Sets cancel_at_period_end=True in Stripe, updates status to 'canceling'.
    """
    from supabase_client import get_supabase

    user_id = user["id"]
    logger.info(f"Cancellation requested for user {mask_user_id(user_id)}")

    sb = get_supabase()
    stripe_key = os.getenv("STRIPE_SECRET_KEY")

    if not stripe_key:
        logger.error("STRIPE_SECRET_KEY not configured")
        raise HTTPException(status_code=500, detail="Configuração de pagamento ausente")

    # Step 1: Fetch current active subscription
    try:
        result = (
            sb.table("user_subscriptions")
            .select("id, stripe_subscription_id, expires_at")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Nenhuma assinatura ativa encontrada")

        subscription = result.data[0]
        stripe_subscription_id = subscription.get("stripe_subscription_id")

        if not stripe_subscription_id:
            raise HTTPException(status_code=400, detail="Assinatura sem Stripe subscription_id")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch subscription for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar assinatura ativa")

    # Step 2: Cancel subscription at period end in Stripe
    try:
        stripe_subscription = stripe_lib.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=True,
            api_key=stripe_key,
        )

        # Get the period end timestamp and convert to ISO string
        current_period_end = stripe_subscription.current_period_end
        ends_at_iso = datetime.fromtimestamp(current_period_end, tz=timezone.utc).isoformat()

        logger.info(f"Stripe subscription {stripe_subscription_id} set to cancel at {ends_at_iso}")
    except stripe_lib.error.StripeError as e:
        logger.error(f"Stripe cancellation failed for user {mask_user_id(user_id)}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao cancelar no Stripe")
    except Exception as e:
        logger.error(f"Unexpected error during Stripe cancellation for user {mask_user_id(user_id)}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao processar cancelamento")

    # Step 3: Update profiles table with canceling status and end date
    try:
        sb.table("profiles").update({
            "subscription_status": "canceling",
            "subscription_end_date": ends_at_iso,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id).execute()

        logger.info(f"Updated profiles for user {mask_user_id(user_id)} to canceling status")
    except Exception as e:
        logger.error(f"Failed to update profiles for user {mask_user_id(user_id)}: {e}", exc_info=True)
        logger.critical(
            f"DATA INCONSISTENCY: Stripe canceled but profiles update failed for user {mask_user_id(user_id)}"
        )
        raise HTTPException(status_code=500, detail="Erro ao atualizar status de cancelamento")

    # Step 4: Log the action
    log_user_action(
        logger,
        "subscription-cancel-requested",
        user_id,
        details={
            "stripe_subscription_id": stripe_subscription_id,
            "ends_at": ends_at_iso,
        }
    )

    return CancelSubscriptionResponse(
        success=True,
        ends_at=ends_at_iso,
        message=f"Sua assinatura foi cancelada e permanecerá ativa até {datetime.fromisoformat(ends_at_iso).strftime('%d/%m/%Y')}.",
    )
