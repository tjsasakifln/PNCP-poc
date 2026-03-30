"""Metrics API endpoints.

GET /v1/metrics/discard-rate — Returns 30-day moving average of filter discard rate.
GET /v1/metrics/daily-volume — Returns average bids/day over last 30 days (STORY-358 AC3).
POST /v1/metrics/sse-fallback — Increment SSE fallback counter (STORY-359 AC4).
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/discard-rate")
async def get_discard_rate(days: int = Query(30, ge=1, le=90)):
    """Return the moving-average filter discard rate.

    Public endpoint (no authentication required). Used by the landing page
    to display a verified discard rate instead of a hardcoded number.
    """
    from filter.stats import discard_rate_tracker

    data = discard_rate_tracker.get_discard_rate(days=days)
    logger.debug(
        f"discard-rate requested: {data['discard_rate_pct']}% "
        f"({data['sample_size']} searches, {data['period_days']}d window)"
    )
    return data


# ============================================================================
# STORY-358 AC3: Daily volume endpoint
# ============================================================================

class DailyVolumeResponse(BaseModel):
    avg_bids_per_day: float
    total_bids_30d: int
    total_sessions_30d: int
    days_with_data: int
    display_value: str  # formatted string for frontend (e.g. "1200+" or "centenas")


@router.get("/daily-volume", response_model=DailyVolumeResponse)
async def get_daily_volume(days: int = Query(30, ge=1, le=90)):
    """STORY-358 AC3: Return average bids processed per day.

    Public endpoint (no authentication required). Used by InstitutionalSidebar
    to display a verified bids/day count instead of a hardcoded number.

    Queries search_sessions for the specified window and computes daily average
    from total_raw (bids fetched before filtering).
    """
    try:
        from supabase_client import get_supabase, sb_execute

        sb = get_supabase()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        result = await sb_execute(
            sb.table("search_sessions")
            .select("total_raw, created_at")
            .gte("created_at", cutoff)
            .in_("status", ["completed", "completed_partial"])
        )

        sessions = result.data or []

        if not sessions:
            return DailyVolumeResponse(
                avg_bids_per_day=0,
                total_bids_30d=0,
                total_sessions_30d=0,
                days_with_data=0,
                display_value="centenas",
            )

        # Group by date and count unique days with data
        daily_totals: dict[str, int] = {}
        for s in sessions:
            raw = s.get("total_raw") or 0
            created = s.get("created_at", "")
            day_key = created[:10] if created else "unknown"
            daily_totals[day_key] = daily_totals.get(day_key, 0) + raw

        total_bids = sum(daily_totals.values())
        days_with_data = len(daily_totals)
        avg_per_day = total_bids / days_with_data if days_with_data > 0 else 0

        # Format display value
        if avg_per_day >= 1000:
            display_value = f"{int(avg_per_day)}+"
        elif avg_per_day >= 100:
            display_value = f"{int(avg_per_day)}+"
        else:
            display_value = "centenas"

        logger.info(
            "STORY-358 daily-volume: avg=%.0f/day, total=%d, sessions=%d, days=%d",
            avg_per_day, total_bids, len(sessions), days_with_data,
        )

        return DailyVolumeResponse(
            avg_bids_per_day=round(avg_per_day, 1),
            total_bids_30d=total_bids,
            total_sessions_30d=len(sessions),
            days_with_data=days_with_data,
            display_value=display_value,
        )

    except Exception as e:
        logger.error("STORY-358: daily-volume endpoint error: %s", e, exc_info=True)
        # Graceful fallback — return safe defaults instead of 500
        return DailyVolumeResponse(
            avg_bids_per_day=0,
            total_bids_30d=0,
            total_sessions_30d=0,
            days_with_data=0,
            display_value="centenas",
        )


@router.post("/sse-fallback", status_code=204)
async def report_sse_fallback():
    """STORY-359 AC4: Frontend reports SSE fallback to simulated progress.

    Lightweight fire-and-forget endpoint — no auth, no body, just increments counter.
    """
    from metrics import SSE_FALLBACK_SIMULATED_TOTAL

    SSE_FALLBACK_SIMULATED_TOTAL.inc()
    logger.info("sse_fallback_simulated: frontend reported SSE fallback to simulation")
    return Response(status_code=204)
