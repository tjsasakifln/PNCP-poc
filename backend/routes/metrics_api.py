"""Metrics API endpoints.

GET /v1/metrics/discard-rate — Returns 30-day moving average of filter discard rate.
POST /v1/metrics/sse-fallback — Increment SSE fallback counter (STORY-359 AC4).
"""

import logging

from fastapi import APIRouter, Query, Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/discard-rate")
async def get_discard_rate(days: int = Query(30, ge=1, le=90)):
    """Return the moving-average filter discard rate.

    Public endpoint (no authentication required). Used by the landing page
    to display a verified discard rate instead of a hardcoded number.
    """
    from filter_stats import discard_rate_tracker

    data = discard_rate_tracker.get_discard_rate(days=days)
    logger.debug(
        f"discard-rate requested: {data['discard_rate_pct']}% "
        f"({data['sample_size']} searches, {data['period_days']}d window)"
    )
    return data


@router.post("/sse-fallback", status_code=204)
async def report_sse_fallback():
    """STORY-359 AC4: Frontend reports SSE fallback to simulated progress.

    Lightweight fire-and-forget endpoint — no auth, no body, just increments counter.
    """
    from metrics import SSE_FALLBACK_SIMULATED_TOTAL

    SSE_FALLBACK_SIMULATED_TOTAL.inc()
    logger.info("sse_fallback_simulated: frontend reported SSE fallback to simulation")
    return Response(status_code=204)
