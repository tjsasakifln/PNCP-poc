"""Analytics endpoints for Personal Dashboard feature.

Provides aggregated user statistics from search_sessions table:
1. GET /analytics/summary - Overall user statistics
2. GET /analytics/searches-over-time - Time-series search data
3. GET /analytics/top-dimensions - Top UFs and sectors
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from auth import require_auth
from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _get_sb():
    from supabase_client import get_supabase
    return get_supabase()


# ============================================================================
# Response Models
# ============================================================================

class SummaryResponse(BaseModel):
    total_searches: int
    total_downloads: int
    total_opportunities: int
    total_value_discovered: float
    estimated_hours_saved: float
    avg_results_per_search: float
    success_rate: float
    member_since: str


class TimeSeriesDataPoint(BaseModel):
    label: str
    searches: int
    opportunities: int
    value: float


class SearchesOverTimeResponse(BaseModel):
    period: str
    data: list[TimeSeriesDataPoint]


class DimensionItem(BaseModel):
    name: str
    count: int
    value: float


class TopDimensionsResponse(BaseModel):
    top_ufs: list[DimensionItem]
    top_sectors: list[DimensionItem]


# ============================================================================
# GET /analytics/summary
# ============================================================================

@router.get("/summary", response_model=SummaryResponse)
async def get_analytics_summary(user: dict = Depends(require_auth)):
    """Get overall user analytics summary."""
    sb = _get_sb()
    user_id = user["id"]

    try:
        # STORY-202 DB-M07: Use RPC to avoid full-table scan (single optimized query)
        result = sb.rpc("get_analytics_summary", {
            "p_user_id": user_id,
            "p_start_date": None,
            "p_end_date": None,
        }).execute()

        if not result.data or len(result.data) == 0:
            # No data - return zeros with current timestamp
            return SummaryResponse(
                total_searches=0,
                total_downloads=0,
                total_opportunities=0,
                total_value_discovered=0.0,
                estimated_hours_saved=0.0,
                avg_results_per_search=0.0,
                success_rate=0.0,
                member_since=datetime.utcnow().isoformat(),
            )

        row = result.data[0]
        total_searches = row["total_searches"] or 0
        total_downloads = row["total_downloads"] or 0
        total_opportunities = row["total_opportunities"] or 0
        total_value_discovered = float(row["total_value_discovered"] or 0)
        member_since = row["member_since"] or datetime.utcnow().isoformat()

        # Calculate derived metrics
        estimated_hours_saved = float(total_searches * 2)
        avg_results_per_search = (
            total_opportunities / total_searches if total_searches > 0 else 0.0
        )
        success_rate = (
            (total_downloads / total_searches * 100) if total_searches > 0 else 0.0
        )

        logger.info(
            f"Analytics summary for user {mask_user_id(user_id)}: "
            f"{total_searches} searches, {total_opportunities} opportunities"
        )

        return SummaryResponse(
            total_searches=total_searches,
            total_downloads=total_downloads,
            total_opportunities=total_opportunities,
            total_value_discovered=total_value_discovered,
            estimated_hours_saved=estimated_hours_saved,
            avg_results_per_search=round(avg_results_per_search, 1),
            success_rate=round(success_rate, 1),
            member_since=member_since,
        )

    except Exception as e:
        logger.error(f"Error calling get_analytics_summary RPC for {mask_user_id(user_id)}: {e}")
        raise


# ============================================================================
# GET /analytics/searches-over-time
# ============================================================================

@router.get("/searches-over-time", response_model=SearchesOverTimeResponse)
async def get_searches_over_time(
    user: dict = Depends(require_auth),
    period: str = Query("week", pattern="^(day|week|month)$"),
    range_days: int = Query(90, ge=1, le=365),
):
    """Get time-series search data grouped by period."""
    sb = _get_sb()
    user_id = user["id"]

    try:
        start_date = (datetime.utcnow() - timedelta(days=range_days)).date()

        sessions_result = (
            sb.table("search_sessions")
            .select("created_at, total_filtered, valor_total")
            .eq("user_id", user_id)
            .gte("created_at", start_date.isoformat())
            .order("created_at")
            .execute()
        )
        sessions = sessions_result.data or []

        grouped: dict[str, dict] = {}
        for s in sessions:
            created_at = s["created_at"]
            if isinstance(created_at, str):
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")).date()
            else:
                dt = created_at

            if period == "day":
                key = dt.isoformat()
                label = dt.strftime("%d %b")
            elif period == "week":
                week_start = dt - timedelta(days=dt.weekday())
                key = week_start.isoformat()
                label = week_start.strftime("%d %b")
            else:
                key = dt.strftime("%Y-%m")
                label = dt.strftime("%b %Y")

            if key not in grouped:
                grouped[key] = {"label": label, "searches": 0, "opportunities": 0, "value": 0.0}

            grouped[key]["searches"] += 1
            grouped[key]["opportunities"] += s.get("total_filtered") or 0
            grouped[key]["value"] += float(Decimal(str(s.get("valor_total") or 0)))

        data = [TimeSeriesDataPoint(**grouped[k]) for k in sorted(grouped.keys())]

        return SearchesOverTimeResponse(period=period, data=data)

    except Exception as e:
        logger.error(f"Error fetching time series for {mask_user_id(user_id)}: {e}")
        raise


# ============================================================================
# GET /analytics/top-dimensions
# ============================================================================

@router.get("/top-dimensions", response_model=TopDimensionsResponse)
async def get_top_dimensions(
    user: dict = Depends(require_auth),
    limit: int = Query(5, ge=1, le=50),
):
    """Get top UFs and sectors by search count."""
    sb = _get_sb()
    user_id = user["id"]

    try:
        sessions_result = (
            sb.table("search_sessions")
            .select("ufs, sectors, valor_total")
            .eq("user_id", user_id)
            .execute()
        )
        sessions = sessions_result.data or []

        ufs_agg: dict[str, dict] = {}
        sectors_agg: dict[str, dict] = {}

        for s in sessions:
            valor = float(Decimal(str(s.get("valor_total") or 0)))

            for uf in (s.get("ufs") or []):
                if uf not in ufs_agg:
                    ufs_agg[uf] = {"count": 0, "value": 0.0}
                ufs_agg[uf]["count"] += 1
                ufs_agg[uf]["value"] += valor

            for sector in (s.get("sectors") or []):
                if sector not in sectors_agg:
                    sectors_agg[sector] = {"count": 0, "value": 0.0}
                sectors_agg[sector]["count"] += 1
                sectors_agg[sector]["value"] += valor

        top_ufs = [
            DimensionItem(name=uf, count=d["count"], value=d["value"])
            for uf, d in sorted(ufs_agg.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]
        ]
        top_sectors = [
            DimensionItem(name=sec, count=d["count"], value=d["value"])
            for sec, d in sorted(sectors_agg.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]
        ]

        return TopDimensionsResponse(top_ufs=top_ufs, top_sectors=top_sectors)

    except Exception as e:
        logger.error(f"Error fetching top dimensions for {mask_user_id(user_id)}: {e}")
        raise
