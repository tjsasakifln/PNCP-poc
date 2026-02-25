"""STORY-259 AC7-AC12: Deep bid analysis on-demand endpoint.

POST /v1/bid-analysis/{bid_id} — Detailed analysis of a single bid.
"""

import logging
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from auth import require_auth
from bid_analyzer import deep_analyze_bid, DeepBidAnalysis
from config import get_feature_flag

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bid-analysis"])

# ---------------------------------------------------------------------------
# Rate limiting: 20 deep analyses per hour per user (AC10)
# ---------------------------------------------------------------------------
_DEEP_ANALYSIS_RATE_LIMIT = 20
_DEEP_ANALYSIS_WINDOW_S = 3600

_rate_limits: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(user_id: str) -> None:
    """AC10: Enforce per-user rate limit for deep analysis."""
    now = time.time()
    cutoff = now - _DEEP_ANALYSIS_WINDOW_S
    attempts = _rate_limits[user_id]
    _rate_limits[user_id] = [t for t in attempts if t > cutoff]

    if len(_rate_limits[user_id]) >= _DEEP_ANALYSIS_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Limite de análises detalhadas atingido (20/hora). Tente novamente em breve.",
        )
    _rate_limits[user_id].append(now)


class DeepAnalysisRequest(BaseModel):
    """Request body for deep analysis."""
    search_id: str
    bid_data: dict | None = None  # Full bid data (optional — can come from cache)


# ---------------------------------------------------------------------------
# POST /v1/bid-analysis/{bid_id}
# ---------------------------------------------------------------------------

@router.post("/bid-analysis/{bid_id}", response_model=DeepBidAnalysis)
async def analyze_bid(
    bid_id: str,
    body: DeepAnalysisRequest,
    user: dict = Depends(require_auth),
):
    """AC7: Deep on-demand analysis for a single bid.

    Checks cache first (AC11), then calls LLM.
    Rate limited: 20/hour/user (AC10).
    """
    user_id = user["id"]

    # AC10: Rate limit
    _check_rate_limit(user_id)

    # AC11: Check Redis cache first
    cache_key = f"smartlic:deep_analysis:{user_id}:{bid_id}"
    cached_result = await _get_cached_analysis(cache_key)
    if cached_result:
        logger.debug(f"Deep analysis cache hit: {bid_id}")
        return DeepBidAnalysis(**cached_result)

    # Get bid data from request or from search session cache
    bid_data = body.bid_data
    if not bid_data:
        bid_data = await _get_bid_from_session(body.search_id, bid_id)

    if not bid_data:
        # AC12: Bid not found
        raise HTTPException(
            status_code=404,
            detail="Edital não encontrado. Execute uma nova busca.",
        )

    # Load user profile
    user_profile = await _get_user_profile(user_id)

    # Get sector name
    sector_name = ""
    if user_profile:
        sector_id = user_profile.get("setor_id") or user_profile.get("cnae")
        if sector_id:
            try:
                from sectors import get_sector
                sector = get_sector(sector_id)
                sector_name = sector.name
            except (KeyError, Exception):
                pass

    # Execute deep analysis
    result = deep_analyze_bid(
        bid=bid_data,
        user_profile=user_profile,
        sector_name=sector_name,
    )
    result.bid_id = bid_id

    # AC11: Cache result for 24h
    await _cache_analysis(cache_key, result.model_dump())

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_cached_analysis(key: str) -> dict | None:
    """Get cached deep analysis from Redis."""
    try:
        from redis_pool import get_redis_pool
        import json
        redis = await get_redis_pool()
        if redis is None:
            return None
        raw = await redis.get(key)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


async def _cache_analysis(key: str, data: dict) -> None:
    """Cache deep analysis in Redis for 24h."""
    try:
        from redis_pool import get_redis_pool
        import json
        redis = await get_redis_pool()
        if redis is None:
            return
        await redis.set(key, json.dumps(data), ex=86400)  # 24h
    except Exception:
        pass


async def _get_bid_from_session(search_id: str, bid_id: str) -> dict | None:
    """Try to retrieve bid data from search session cache."""
    try:
        from job_queue import get_job_result
        result = await get_job_result(search_id, "search_result")
        if result and isinstance(result, dict):
            licitacoes = result.get("licitacoes", [])
            for lic in licitacoes:
                lic_id = str(lic.get("id") or lic.get("numeroControlePNCP") or "")
                if lic_id == bid_id:
                    return lic
    except Exception:
        pass
    return None


async def _get_user_profile(user_id: str) -> dict | None:
    """Load user profile context data."""
    try:
        from supabase_client import get_supabase
        db = get_supabase()
        result = db.table("profiles").select("context_data").eq("id", user_id).single().execute()
        return (result.data or {}).get("context_data") or {}
    except Exception:
        return None
