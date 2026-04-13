"""P2 SEO: Public calculator endpoint for /calculadora conversion tool.

Returns real PNCP stats (last 30 days) for a given sector + UF,
enabling the frontend to show the 'shock moment' — how much money
the user's company is leaving on the table.

Public (no auth). Cache: InMemory 1h TTL.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from rate_limiter import require_rate_limit
from sectors import SECTORS
from unified_schemas.unified import VALID_UFS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["calculadora"])

_CACHE_TTL_SECONDS = 60 * 60  # 1h
_calc_cache: dict[str, tuple[dict, float]] = {}


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------

class CalculadoraDadosResponse(BaseModel):
    total_editais_mes: int
    avg_value: float
    p25_value: float
    p75_value: float
    setor_name: str
    uf: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/calculadora/dados",
    response_model=CalculadoraDadosResponse,
    summary="Dados reais PNCP para a calculadora de oportunidades (público)",
)
async def calculadora_dados(
    setor: str = Query(..., description="Sector ID (e.g. 'saude')"),
    uf: str = Query(..., min_length=2, max_length=2, description="UF sigla (e.g. 'SP')"),
    _rl: None = Depends(require_rate_limit(60, 60)),
):
    uf = uf.upper()

    if setor not in SECTORS:
        raise HTTPException(status_code=400, detail=f"Setor '{setor}' não encontrado")
    if uf not in VALID_UFS:
        raise HTTPException(status_code=400, detail=f"UF '{uf}' inválida")

    cache_key = f"{setor}:{uf}"
    cached = _get_cached(cache_key)
    if cached:
        return CalculadoraDadosResponse(**cached)

    data = await _generate_dados(setor, uf)
    _set_cached(cache_key, data)
    return CalculadoraDadosResponse(**data)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _get_cached(key: str) -> Optional[dict]:
    if key not in _calc_cache:
        return None
    data, ts = _calc_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _calc_cache[key]
        return None
    return data


def _set_cached(key: str, data: dict) -> None:
    _calc_cache[key] = (data, time.time())


# ---------------------------------------------------------------------------
# Data generation (datalake query)
# ---------------------------------------------------------------------------

async def _generate_dados(setor: str, uf: str) -> dict:
    sector = SECTORS[setor]
    now = datetime.now(timezone.utc)
    data_final = now.strftime("%Y-%m-%d")
    data_inicial = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    results: list[dict] = []
    try:
        from datalake_query import query_datalake

        results = await query_datalake(
            ufs=[uf],
            data_inicial=data_inicial,
            data_final=data_final,
            keywords=list(sector.keywords),
            limit=2000,
        )
    except Exception as e:
        logger.warning("Calculadora: datalake query failed for %s/%s: %s", setor, uf, e)

    # Extract numeric values
    values = []
    for r in results:
        v = r.get("valorTotalEstimado") or r.get("valorEstimado") or r.get("valor_estimado")
        if v and isinstance(v, (int, float)) and v > 0:
            values.append(float(v))

    values.sort()
    total = len(results)
    avg_value = sum(values) / len(values) if values else 0.0

    if len(values) >= 4:
        p25_idx = len(values) // 4
        p75_idx = (3 * len(values)) // 4
        p25_value = values[p25_idx]
        p75_value = values[p75_idx]
    elif values:
        p25_value = values[0]
        p75_value = values[-1]
    else:
        p25_value = 0.0
        p75_value = 0.0

    return {
        "total_editais_mes": total,
        "avg_value": round(avg_value, 2),
        "p25_value": round(p25_value, 2),
        "p75_value": round(p75_value, 2),
        "setor_name": sector.name,
        "uf": uf,
    }
