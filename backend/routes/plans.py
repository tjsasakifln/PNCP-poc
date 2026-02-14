"""Plans API routes - GET /api/plans endpoint.

STORY-203 CROSS-M01: Serves plan details from database to frontend.

This endpoint provides comprehensive plan information including:
- Plan metadata (name, description, prices)
- Capabilities (search limits, Excel export, history retention)
- Stripe integration details

Data source: `plans` table in database (via SYS-M04 infrastructure)
"""

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["plans"])


class PlanDetails(BaseModel):
    """Complete plan details for frontend display.

    STORY-210 AC11: Stripe Price IDs removed from public response
    to prevent enumeration attacks on pricing infrastructure.
    """
    id: str
    name: str
    description: str
    price_brl: float
    duration_days: int
    max_searches: int
    capabilities: Dict[str, Any]
    is_active: bool


class PlansResponse(BaseModel):
    """Response model for GET /api/plans."""
    plans: List[PlanDetails]
    total: int


@router.get("/api/plans", response_model=PlansResponse)
async def get_plans_with_capabilities(db=Depends(get_db)):
    """Get all active plans with capabilities and pricing.

    STORY-203 CROSS-M01: Combines plan metadata from database with
    capabilities from SYS-M04 infrastructure. This provides a single
    endpoint for frontend to fetch all plan-related data.

    Returns:
        PlansResponse: List of plans with full details

    Raises:
        HTTPException 500: If database query fails
    """
    from quota import get_plan_capabilities

    try:
        # Fetch all active plans from database
        result = (
            db.table("plans")
            .select(
                "id, name, description, price_brl, duration_days, max_searches, is_active"
            )
            .eq("is_active", True)
            .order("price_brl")
            .execute()
        )

        if not result.data:
            logger.warning("No active plans found in database")
            return PlansResponse(plans=[], total=0)

        # Get plan capabilities (with 5min cache from SYS-M04)
        plan_capabilities = get_plan_capabilities()

        # Combine database plans with capabilities
        enriched_plans: List[PlanDetails] = []

        for plan in result.data:
            plan_id = plan["id"]
            capabilities = plan_capabilities.get(plan_id, {})

            # STORY-210 AC11: Stripe Price IDs excluded from public response
            enriched_plan = PlanDetails(
                id=plan_id,
                name=plan["name"],
                description=plan["description"],
                price_brl=plan["price_brl"],
                duration_days=plan["duration_days"] or 30,
                max_searches=plan["max_searches"],
                capabilities={
                    "max_history_days": capabilities.get("max_history_days", 30),
                    "allow_excel": capabilities.get("allow_excel", False),
                    "max_requests_per_month": capabilities.get("max_requests_per_month", plan["max_searches"]),
                    "max_requests_per_min": capabilities.get("max_requests_per_min", 10),
                    "max_summary_tokens": capabilities.get("max_summary_tokens", 200),
                    "priority": capabilities.get("priority", "normal"),
                },
                is_active=plan["is_active"],
            )
            enriched_plans.append(enriched_plan)

        logger.info(f"Successfully fetched {len(enriched_plans)} active plans")
        return PlansResponse(plans=enriched_plans, total=len(enriched_plans))

    except Exception as e:
        logger.error(f"Failed to fetch plans: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao buscar planos. Tente novamente mais tarde."
        )
