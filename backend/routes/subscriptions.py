"""Subscription management routes.

Handles billing period updates, subscription modifications, and
Stripe integration (STORY-171).
"""

import logging
from typing import Literal
from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from auth import require_auth
from services.billing import (
    calculate_prorata_credit,
    update_stripe_subscription_billing_period,
    get_next_billing_date,
)
from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


class UpdateBillingPeriodRequest(BaseModel):
    """Request to update subscription billing period."""
    new_billing_period: Literal["monthly", "annual"] = Field(
        ...,
        description="Target billing period"
    )
    user_timezone: str = Field(
        default="America/Sao_Paulo",
        description="User's timezone for accurate pro-rata calculations"
    )


class UpdateBillingPeriodResponse(BaseModel):
    """Response for billing period update."""
    success: bool
    new_billing_period: str
    next_billing_date: str  # ISO 8601 format
    prorated_credit: str  # BRL (formatted as string for precision)
    deferred: bool
    message: str


@router.post("/update-billing-period", response_model=UpdateBillingPeriodResponse)
async def update_billing_period(
    request: UpdateBillingPeriodRequest,
    user: dict = Depends(require_auth),
):
    """Update subscription billing period (monthly ↔ annual).

    CRITICAL FLOW:
    1. Fetch current subscription from Supabase
    2. Calculate pro-rata credit (with defer logic if < 7 days to renewal)
    3. Update Stripe subscription
    4. Update Supabase (billing_period, updated_at)
    5. Invalidate Redis feature cache
    6. Return next billing date and credit info

    EDGE CASES:
    - Defer if < 7 days to renewal (avoid complex pro-rata + Stripe edge cases)
    - Prevent downgrade (annual → monthly) via UX validation
    - Handle timezone-aware date calculations

    Args:
        request: UpdateBillingPeriodRequest with new billing period
        user: Authenticated user from require_auth dependency

    Returns:
        UpdateBillingPeriodResponse with billing details

    Raises:
        HTTPException 404: No active subscription found
        HTTPException 400: Invalid billing period or downgrade attempt
        HTTPException 500: Database or Stripe API error
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
            raise HTTPException(
                status_code=404,
                detail="Nenhuma assinatura ativa encontrada"
            )

        subscription = result.data[0]
        current_billing_period = subscription["billing_period"]
        plan_id = subscription["plan_id"]
        stripe_subscription_id = subscription.get("stripe_subscription_id")

        # Validate: Can't update if already on target billing period
        if current_billing_period == request.new_billing_period:
            raise HTTPException(
                status_code=400,
                detail=f"Assinatura já está no período de cobrança {request.new_billing_period}"
            )

        # Validate: Stripe subscription required for billing changes
        if not stripe_subscription_id:
            raise HTTPException(
                status_code=400,
                detail="Assinatura não tem Stripe subscription_id associado"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch subscription for user {mask_user_id(user_id)}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao buscar assinatura ativa"
        )

    # Step 2: Get plan pricing from plans table
    try:
        plan_result = (
            sb.table("plans")
            .select("price_brl, stripe_price_id")
            .eq("id", plan_id)
            .single()
            .execute()
        )

        if not plan_result.data:
            raise HTTPException(
                status_code=404,
                detail=f"Plano {plan_id} não encontrado"
            )

        current_price = Decimal(str(plan_result.data["price_brl"]))
        stripe_price_id = plan_result.data.get("stripe_price_id")

        # For now, assume same plan (just billing period change)
        # Future: Support plan upgrades with billing period change
        new_price = current_price

        # Get annual price (if switching to annual, need annual Stripe price ID)
        # ASSUMPTION: Annual price = monthly * 9.6 (20% discount on 12-month commitment)
        # TODO: Store separate annual_price_brl or stripe_annual_price_id in plans table
        if request.new_billing_period == "annual":
            # For now, calculate annual price (future: fetch from plans table)
            _ = current_price * Decimal("9.6")
        else:
            _ = current_price

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch plan pricing for {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao buscar informações do plano"
        )

    # Step 3: Calculate pro-rata credit
    next_billing_date = get_next_billing_date(user_id)
    if not next_billing_date:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível determinar próxima data de cobrança"
        )

    try:
        prorata_result = calculate_prorata_credit(
            current_billing_period=current_billing_period,
            new_billing_period=request.new_billing_period,
            current_price_brl=current_price,
            new_price_brl=new_price,
            next_billing_date=next_billing_date,
            user_timezone=request.user_timezone,
        )
    except ValueError as e:
        logger.error(f"Pro-rata calculation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in pro-rata calculation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Erro ao calcular crédito proporcional"
        )

    # If deferred, return early without updating Stripe/DB
    if prorata_result.deferred:
        logger.info(
            f"Billing period update deferred for user {mask_user_id(user_id)}: {prorata_result.reason}"
        )
        return UpdateBillingPeriodResponse(
            success=True,
            new_billing_period=request.new_billing_period,
            next_billing_date=prorata_result.next_billing_date.isoformat(),
            prorated_credit="0.00",
            deferred=True,
            message=prorata_result.reason or "Mudança agendada para próximo ciclo",
        )

    # Step 4: Update Stripe subscription
    # TODO: Fetch stripe_price_id_monthly and stripe_price_id_annual from plans table
    # For now, use placeholder (requires migration to add these columns)
    stripe_price_id_monthly = stripe_price_id  # Placeholder
    stripe_price_id_annual = stripe_price_id   # Placeholder

    try:
        update_stripe_subscription_billing_period(
            stripe_subscription_id=stripe_subscription_id,
            new_billing_period=request.new_billing_period,
            stripe_price_id_monthly=stripe_price_id_monthly,
            stripe_price_id_annual=stripe_price_id_annual,
            prorated_credit=prorata_result.prorated_credit if not prorata_result.deferred else None,
        )
        logger.info(f"Updated Stripe subscription for user {mask_user_id(user_id)}")
    except Exception as e:
        logger.error(f"Stripe update failed for user {mask_user_id(user_id)}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Erro ao atualizar assinatura no Stripe"
        )

    # Step 5: Update Supabase subscription
    try:
        sb.table("user_subscriptions").update({
            "billing_period": request.new_billing_period,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", subscription["id"]).execute()

        logger.info(
            f"Updated billing_period to {request.new_billing_period} for subscription {subscription['id']}"
        )
    except Exception as e:
        logger.error(
            f"Failed to update user_subscriptions for user {mask_user_id(user_id)}: {e}",
            exc_info=True
        )
        # CRITICAL: Stripe was updated but DB failed - log for manual reconciliation
        logger.critical(
            f"DATA INCONSISTENCY: Stripe updated but Supabase failed for user {mask_user_id(user_id)}, "
            f"subscription {stripe_subscription_id}"
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao atualizar assinatura no banco de dados"
        )

    # Step 6: Invalidate Redis feature cache
    try:
        import os
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            import redis
            r = redis.from_url(redis_url)
            cache_key = f"features:{user_id}"
            r.delete(cache_key)
            logger.info(f"Invalidated Redis cache for user {mask_user_id(user_id)}")
    except Exception as e:
        # Non-critical: Cache invalidation failure doesn't block the operation
        logger.warning(f"Failed to invalidate Redis cache (non-critical): {e}")

    # Step 7: Return success response
    return UpdateBillingPeriodResponse(
        success=True,
        new_billing_period=request.new_billing_period,
        next_billing_date=prorata_result.next_billing_date.isoformat(),
        prorated_credit=str(prorata_result.prorated_credit),
        deferred=False,
        message=f"Período de cobrança atualizado para {request.new_billing_period}. "
                f"Crédito de R$ {prorata_result.prorated_credit} aplicado.",
    )
