"""Analytics endpoints for Personal Dashboard feature.

Provides aggregated user statistics from search_sessions table:
1. GET /analytics/summary - Overall user statistics
2. GET /analytics/searches-over-time - Time-series search data
3. GET /analytics/top-dimensions - Top UFs and sectors
4. GET /analytics/new-opportunities - New opportunities since last search (DEBT-127)
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from auth import require_auth
from database import get_db
from log_sanitizer import mask_user_id
from supabase_client import sb_execute, CircuitBreakerOpenError

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


class NewOpportunitiesResponse(BaseModel):
    """DEBT-127 AC6-AC9: New opportunities since last search."""
    count: int
    has_previous_search: bool
    last_search_at: str | None = None
    days_since_last_search: int | None = None


# ============================================================================
# GET /analytics/summary
# ============================================================================

@router.get("/summary", response_model=SummaryResponse)
async def get_analytics_summary(user: dict = Depends(require_auth), db=Depends(get_db)):
    """Get overall user analytics summary."""
    user_id = user["id"]

    try:
        # STORY-202 DB-M07: Use RPC to avoid full-table scan (single optimized query)
        result = await sb_execute(db.rpc("get_analytics_summary", {
            "p_user_id": user_id,
            "p_start_date": None,
            "p_end_date": None,
        }))

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

    except CircuitBreakerOpenError:
        # STORY-416 AC4: CB open — return degraded empty response instead of 503
        logger.warning("Analytics summary CB open — returning degraded response for %s", mask_user_id(user_id))
        return JSONResponse(
            status_code=200,
            content=SummaryResponse(
                total_searches=0,
                total_downloads=0,
                total_opportunities=0,
                total_value_discovered=0.0,
                estimated_hours_saved=0.0,
                avg_results_per_search=0.0,
                success_rate=0.0,
                member_since=datetime.now(timezone.utc).isoformat(),
            ).model_dump(mode="json"),
            headers={"X-Cache-Status": "stale-due-to-cb-open"},
        )
    except Exception as e:
        logger.error(f"Error calling get_analytics_summary RPC for {mask_user_id(user_id)}: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Dados temporariamente indisponiveis")


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

        sessions_result = await sb_execute(
            db.table("search_sessions")
            .select("created_at, total_filtered, valor_total")
            .eq("user_id", user_id)
            .gte("created_at", start_date.isoformat())
            .order("created_at")
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

    except CircuitBreakerOpenError:
        # STORY-416 AC4: CB open — return degraded empty time series
        logger.warning("Analytics time-series CB open — returning degraded response for %s", mask_user_id(user_id))
        return JSONResponse(
            status_code=200,
            content={"period": period, "data": [], "degraded": True},
            headers={"X-Cache-Status": "stale-due-to-cb-open"},
        )
    except Exception as e:
        logger.error(f"Error fetching time series for {mask_user_id(user_id)}: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Dados temporariamente indisponiveis")


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
        sessions_result = await sb_execute(
            db.table("search_sessions")
            .select("ufs, sectors, valor_total")
            .eq("user_id", user_id)
        )
        sessions = sessions_result.data or []

        ufs_agg: dict[str, dict] = {}
        sectors_agg: dict[str, dict] = {}

        for s in sessions:
            try:
                raw_valor = s.get("valor_total")
                valor = float(Decimal(str(raw_valor))) if raw_valor else 0.0
            except Exception:
                valor = 0.0
                logger.warning(
                    f"ISSUE-024: Malformed valor_total={s.get('valor_total')!r} "
                    f"in session {s.get('id', '?')}, defaulting to 0"
                )

            raw_ufs = s.get("ufs") or []
            if isinstance(raw_ufs, str):
                raw_ufs = [raw_ufs]

            for uf in raw_ufs:
                if not isinstance(uf, str) or not uf:
                    continue
                if uf not in ufs_agg:
                    ufs_agg[uf] = {"count": 0, "value": 0.0}
                ufs_agg[uf]["count"] += 1
                ufs_agg[uf]["value"] += valor

            raw_sectors = s.get("sectors") or []
            if isinstance(raw_sectors, str):
                raw_sectors = [raw_sectors]

            for sector in raw_sectors:
                if not isinstance(sector, str) or not sector:
                    continue
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

    except CircuitBreakerOpenError:
        # STORY-416 AC4: CB open — return degraded empty dimensions
        logger.warning("Analytics top-dimensions CB open — returning degraded response for %s", mask_user_id(user_id))
        return JSONResponse(
            status_code=200,
            content={"top_ufs": [], "top_sectors": [], "degraded": True},
            headers={"X-Cache-Status": "stale-due-to-cb-open"},
        )
    except Exception as e:
        logger.error(f"Error fetching top dimensions for {mask_user_id(user_id)}: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Dados temporariamente indisponiveis")


# ============================================================================
# GTM-010: Trial Conversion Analytics
# ============================================================================

class TopOpportunity(BaseModel):
    title: str
    value: float
    # STORY-371: Real edital fields
    objeto: str | None = None
    orgao_nome: str | None = None
    numero_controle: str | None = None
    data_encerramento: str | None = None
    dias_ate_encerramento: int | None = None
    setor: str | None = None
    modalidade: str | None = None

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
        profile_result = await sb_execute(db.table("profiles").select("created_at, trial_expires_at").eq("id", user_id).single())
        profile = profile_result.data if profile_result.data else {}
        trial_start = profile.get("created_at")
        trial_end = profile.get("trial_expires_at")

        # Query search sessions within trial period.
        # STORY-371: Include optional top_result_* columns for personalization.
        # These columns may not exist on older DB versions — if the query fails,
        # the outer try/except will surface a 503 which is the existing behavior.
        query = db.table("search_sessions").select(
            "total_filtered, valor_total, created_at, sectors, top_result_objeto, top_result_orgao, top_result_numero_controle, top_result_data_encerramento, top_result_modalidade"
        ).eq("user_id", user_id)

        if trial_start:
            query = query.gte("created_at", trial_start)
        if trial_end:
            query = query.lte("created_at", trial_end)

        sessions_result = await sb_execute(query.order("valor_total", desc=True))
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

        # Top opportunity = session with highest valor_total.
        # STORY-412: ``objeto_resumo`` removed from the query above, so
        # the title is always the literal fallback. Keeping the literal
        # here (instead of interpolating any session field) avoids
        # accidental PII leakage through search titles and matches the
        # copy already reviewed by product.
        top_session = sessions[0] if sessions else None
        top_opportunity = None
        if top_session and float(Decimal(str(top_session.get("valor_total") or 0))) > 0:
            top_value = float(Decimal(str(top_session.get("valor_total") or 0)))
            # STORY-371 AC1: Use real edital fields if available
            objeto_raw = top_session.get("top_result_objeto") or "Oportunidade identificada"
            from utils.formatters import truncate_text, dias_ate_data
            data_enc = top_session.get("top_result_data_encerramento")
            top_opportunity = TopOpportunity(
                title=truncate_text(objeto_raw, 120),
                value=top_value,
                objeto=truncate_text(objeto_raw, 120),
                orgao_nome=top_session.get("top_result_orgao"),
                numero_controle=top_session.get("top_result_numero_controle"),
                data_encerramento=data_enc,
                dias_ate_encerramento=dias_ate_data(data_enc),
                setor=(top_session.get("sectors") or [None])[0],
                modalidade=top_session.get("top_result_modalidade"),
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
            detail="Informação de valor do trial temporariamente indisponível"
        )


# ============================================================================
# DEBT-127 AC6-AC9: New opportunities since last search
# ============================================================================

@router.get("/new-opportunities", response_model=NewOpportunitiesResponse)
async def get_new_opportunities(user: dict = Depends(require_auth), db=Depends(get_db)):
    """Get count of opportunities from user's most recent search.

    DEBT-127 AC6-AC9: Drives users back to /buscar by showing how many
    opportunities were found in their latest search and how long ago it was.
    If no previous search exists, returns has_previous_search=False for
    onboarding prompt (AC9).
    """
    user_id = user["id"]

    # UX-431: Always send no-cache headers so dashboard shows fresh data
    no_cache_headers = {"Cache-Control": "no-store, no-cache, must-revalidate"}

    try:
        result = await sb_execute(
            db.table("search_sessions")
            .select("created_at, total_filtered")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
        )

        sessions = result.data or []

        if not sessions:
            return JSONResponse(
                content=NewOpportunitiesResponse(
                    count=0,
                    has_previous_search=False,
                ).model_dump(mode="json"),
                headers=no_cache_headers,
            )

        last_session = sessions[0]
        created_at = last_session["created_at"]
        if isinstance(created_at, str):
            last_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        else:
            last_dt = created_at

        days_since = (datetime.now(timezone.utc) - last_dt).days

        return JSONResponse(
            content=NewOpportunitiesResponse(
                count=last_session.get("total_filtered") or 0,
                has_previous_search=True,
                last_search_at=created_at,
                days_since_last_search=max(days_since, 0),
            ).model_dump(mode="json"),
            headers=no_cache_headers,
        )

    except Exception as e:
        logger.error(f"Error fetching new opportunities for user {mask_user_id(user_id)}: {e}")
        return JSONResponse(
            content=NewOpportunitiesResponse(count=0, has_previous_search=False).model_dump(mode="json"),
            headers=no_cache_headers,
        )


# ============================================================================
# STORY-312 AC11: CTA conversion tracking
# ============================================================================

VALID_CTA_ACTIONS = {"shown", "clicked", "dismissed"}
VALID_CTA_VARIANTS = {"post-search", "post-download", "post-pipeline", "dashboard", "quota"}


class CTAEventRequest(BaseModel):
    action: str  # "shown" | "clicked" | "dismissed"
    variant: str  # "post-search" | "post-download" | "post-pipeline" | "dashboard" | "quota"


@router.post("/track-cta", status_code=204)
async def track_cta_event(event: CTAEventRequest, user: dict = Depends(require_auth)):
    """Track CTA conversion events for admin dashboard (STORY-312 AC11).

    Increments Prometheus counters for shown/clicked/dismissed by variant.
    Fire-and-forget — always returns 204.
    """
    if event.action not in VALID_CTA_ACTIONS or event.variant not in VALID_CTA_VARIANTS:
        return  # Silently ignore invalid events

    try:
        import metrics
        if event.action == "shown":
            metrics.CTA_SHOWN.labels(variant=event.variant).inc()
        elif event.action == "clicked":
            metrics.CTA_CLICKED.labels(variant=event.variant).inc()
        elif event.action == "dismissed":
            metrics.CTA_DISMISSED.labels(variant=event.variant).inc()
    except Exception:
        pass  # Fire-and-forget
