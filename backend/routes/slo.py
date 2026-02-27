"""STORY-299: SLO dashboard API endpoints.

GET /v1/admin/slo — Returns SLO compliance data for admin dashboard.
GET /v1/admin/slo/alerts — Returns current alert evaluation results.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends

from admin import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin", tags=["admin-slo"])


@router.get("/slo")
async def get_slo_dashboard(user=Depends(require_admin)) -> dict[str, Any]:
    """AC7-AC9: SLO compliance data for admin dashboard.

    Returns all SLO statuses, alert evaluations, and metadata.
    """
    from slo import (
        SLOS,
        RECORDING_RULES,
        compute_all_slo_statuses,
        evaluate_all_alerts,
        SENTRY_ALERTS,
    )

    statuses = compute_all_slo_statuses()
    alerts = evaluate_all_alerts()

    # Compute summary
    all_met = all(s.is_met for s in statuses.values())
    any_data = any(s.sli_value is not None for s in statuses.values())
    firing_count = sum(1 for a in alerts if a["firing"])

    return {
        "compliance": "no_data" if not any_data else ("compliant" if all_met else "violation"),
        "slos": {key: s.to_dict() for key, s in statuses.items()},
        "alerts": alerts,
        "firing_count": firing_count,
        "slo_definitions": {
            key: {
                "name": slo.name,
                "target": slo.target,
                "window_days": slo.window_days,
                "unit": slo.unit,
                "error_budget": slo.error_budget,
            }
            for key, slo in SLOS.items()
        },
        "recording_rules": RECORDING_RULES,
        "sentry_alerts": SENTRY_ALERTS,
    }


@router.get("/slo/alerts")
async def get_slo_alerts(user=Depends(require_admin)) -> dict[str, Any]:
    """Return current alert evaluation results."""
    from slo import evaluate_all_alerts

    alerts = evaluate_all_alerts()
    return {
        "alerts": alerts,
        "firing_count": sum(1 for a in alerts if a["firing"]),
    }
