"""Analytics endpoints for Personal Dashboard feature.

Provides aggregated user statistics from search_sessions table:
1. GET /analytics/summary - Overall user statistics
2. GET /analytics/searches-over-time - Time-series search data
3. GET /analytics/top-dimensions - Top UFs and sectors
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from auth import require_auth
from database import get_db
from log_sanitizer import mask_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


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
async def get_analytics_summary(user: dict = Depends(require_auth), db=Depends(get_db)):
    """Get overall user analytics summary."""
    user_id = user["id"]

    try:
        # STORY-202 DB-M07: Use RPC to avoid full-table scan (single optimized query)
        result = db.rpc("get_analytics_summary", {
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
                member_since=datetime.now(timezone.utc).isoformat(),
            )

        row = result.data[0]
        total_searches = row["total_searches"] or 0
        total_downloads = row["total_downloads"] or 0
        total_opportunities = row["total_opportunities"] or 0
        total_value_discovered = float(row["total_value_discovered"] or 0)
        member_since = row["member_since"] or datetime.now(timezone.utc).isoformat()

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
        # CRIT-004 AC8: Graceful degradation — return zeros instead of 500
        return SummaryResponse(
            total_searches=0,
            total_downloads=0,
            total_opportunities=0,
            total_value_discovered=0.0,
            estimated_hours_saved=0.0,
            avg_results_per_search=0.0,
            success_rate=0.0,
            member_since=datetime.now(timezone.utc).isoformat(),
        )


# ============================================================================
# GET /analytics/searches-over-time
# ============================================================================

@router.get("/searches-over-time", response_model=SearchesOverTimeResponse)
async def get_searches_over_time(
    user: dict = Depends(require_auth),
    period: str = Query("week", pattern="^(day|week|month)$"),
    range_days: int = Query(90, ge=1, le=365),
    db=Depends(get_db),
):
    """Get time-series search data grouped by period."""
    user_id = user["id"]

    try:
        start_date = (datetime.now(timezone.utc) - timedelta(days=range_days)).date()

        sessions_result = (
            db.table("search_sessions")
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
        # CRIT-004 AC8: Graceful degradation — return empty series instead of 500
        return SearchesOverTimeResponse(period=period, data=[])


# ============================================================================
# GET /analytics/top-dimensions
# ============================================================================

@router.get("/top-dimensions", response_model=TopDimensionsResponse)
async def get_top_dimensions(
    user: dict = Depends(require_auth),
    limit: int = Query(5, ge=1, le=50),
    db=Depends(get_db),
):
    """Get top UFs and sectors by search count."""
    user_id = user["id"]

    try:
        sessions_result = (
            db.table("search_sessions")
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
        # CRIT-004 AC8: Graceful degradation — return empty dimensions instead of 500
        return TopDimensionsResponse(top_ufs=[], top_sectors=[])


# ============================================================================
# GTM-010: Trial Conversion Analytics
# ============================================================================

class TopOpportunity(BaseModel):
    title: str
    value: float

class TrialValueResponse(BaseModel):
    total_opportunities: int
    total_value: float
    searches_executed: int
    avg_opportunity_value: float
    top_opportunity: TopOpportunity | None = None


@router.get("/trial-value", response_model=TrialValueResponse)
async def get_trial_value(user: dict = Depends(require_auth), db=Depends(get_db)):
    """Get value generated during trial period (GTM-010 AC1).

    Returns aggregated statistics of opportunities analyzed during the user's trial.
    Used by TrialConversionScreen to show personalized conversion messaging.
    """
    user_id = user["id"]

    try:
        # Get user's trial period dates from profile
        profile_result = db.table("profiles").select("created_at, trial_expires_at").eq("id", user_id).single().execute()
        profile = profile_result.data if profile_result.data else {}
        trial_start = profile.get("created_at")
        trial_end = profile.get("trial_expires_at")

        # Query search sessions within trial period
        query = db.table("search_sessions").select(
            "total_filtered, valor_total, objeto_resumo, created_at"
        ).eq("user_id", user_id)

        if trial_start:
            query = query.gte("created_at", trial_start)
        if trial_end:
            query = query.lte("created_at", trial_end)

        sessions_result = query.order("valor_total", desc=True).execute()
        sessions = sessions_result.data or []

        if not sessions:
            return TrialValueResponse(
                total_opportunities=0,
                total_value=0.0,
                searches_executed=0,
                avg_opportunity_value=0.0,
                top_opportunity=None,
            )

        total_opportunities = sum(s.get("total_filtered") or 0 for s in sessions)
        total_value = sum(float(Decimal(str(s.get("valor_total") or 0))) for s in sessions)
        searches_executed = len(sessions)
        avg_opportunity_value = total_value / total_opportunities if total_opportunities > 0 else 0.0

        # Top opportunity = session with highest valor_total
        top_session = sessions[0] if sessions else None
        top_opportunity = None
        if top_session and float(Decimal(str(top_session.get("valor_total") or 0))) > 0:
            top_opportunity = TopOpportunity(
                title=top_session.get("objeto_resumo") or "Oportunidade identificada",
                value=float(Decimal(str(top_session.get("valor_total") or 0))),
            )

        logger.info(
            f"Trial value for {mask_user_id(user_id)}: "
            f"{searches_executed} searches, {total_opportunities} opportunities, R${total_value:,.2f}"
        )

        return TrialValueResponse(
            total_opportunities=total_opportunities,
            total_value=total_value,
            searches_executed=searches_executed,
            avg_opportunity_value=round(avg_opportunity_value, 2),
            top_opportunity=top_opportunity,
        )

    except Exception as e:
        # CRIT-005 AC26: Surface error instead of swallowing with zero defaults
        logger.error(f"Error fetching trial value for {mask_user_id(user_id)}: {e}")
        from fastapi import HTTPException as _HTTPException
        raise _HTTPException(
            status_code=503,
            detail="Informacao de valor do trial temporariamente indisponivel"
        )
