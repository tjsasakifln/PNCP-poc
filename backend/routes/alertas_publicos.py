"""S3: Public alerts endpoint for SEO alertas-publicos pages.

Public (no auth) endpoints that return recent bids by sector+UF
from the pncp_raw_bids datalake. Used by frontend ISR alertas pages + RSS feeds.

Endpoint:
  GET /alertas/{setor_id}/uf/{uf} — latest 20 bids for sector × UF

Cache: InMemory 1h TTL.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sectors import SECTORS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alertas", tags=["alertas-publicos"])

# 1h InMemory cache (matches ISR revalidation period)
_CACHE_TTL_SECONDS = 60 * 60
_alertas_cache: dict[str, tuple[dict, float]] = {}

ALL_UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]


class AlertaBid(BaseModel):
    titulo: str
    orgao: str
    valor: Optional[float] = None
    uf: str
    municipio: str = ""
    modalidade: str = ""
    data_publicacao: str
    data_abertura: Optional[str] = None
    link_pncp: str = ""
    pncp_id: str = ""


class AlertasResponse(BaseModel):
    sector_id: str
    sector_name: str
    uf: str
    bids: list[AlertaBid]
    total: int
    last_updated: str


def _get_cached(key: str) -> Optional[dict]:
    if key not in _alertas_cache:
        return None
    data, ts = _alertas_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _alertas_cache[key]
        return None
    return data


def _set_cached(key: str, data: dict) -> None:
    _alertas_cache[key] = (data, time.time())


@router.get("/{setor_id}/uf/{uf}", response_model=AlertasResponse)
async def get_alertas(setor_id: str, uf: str):
    """Return latest 20 bids for sector × UF from datalake (public, no auth)."""
    # Validate sector
    sector_id_clean = setor_id.replace("-", "_")
    if sector_id_clean not in SECTORS:
        raise HTTPException(status_code=404, detail=f"Setor '{setor_id}' não encontrado")

    uf_upper = uf.upper()
    if uf_upper not in ALL_UFS:
        raise HTTPException(status_code=404, detail=f"UF '{uf}' não encontrada")

    sector = SECTORS[sector_id_clean]

    # Check cache
    cache_key = f"alertas:{sector_id_clean}:{uf_upper}"
    cached = _get_cached(cache_key)
    if cached:
        return AlertasResponse(**cached)

    # Query datalake
    from datalake_query import query_datalake

    now = datetime.now(timezone.utc)
    data_final = now.strftime("%Y-%m-%d")
    data_inicial = (now - timedelta(days=10)).strftime("%Y-%m-%d")

    try:
        results = await query_datalake(
            ufs=[uf_upper],
            data_inicial=data_inicial,
            data_final=data_final,
            keywords=list(sector.keywords),
            limit=50,
        )
    except Exception as e:
        logger.warning("Failed to query datalake for alertas %s/%s: %s", sector_id_clean, uf_upper, e)
        results = []

    # Filter by sector keywords (substring match, same as blog_stats.py)
    keywords_lower = {kw.lower() for kw in sector.keywords}
    matched = []
    for item in results:
        text = f"{item.get('titulo', '')} {item.get('objeto', '')} {item.get('descricao', '')}".lower()
        if any(kw in text for kw in keywords_lower):
            matched.append(item)

    # Sort by date descending, take top 20
    matched.sort(key=lambda x: x.get("data_publicacao", ""), reverse=True)
    matched = matched[:20]

    # Build response
    bids = []
    for item in matched:
        bids.append(AlertaBid(
            titulo=item.get("titulo", "Sem título"),
            orgao=item.get("orgao", item.get("nomeOrgao", "")),
            valor=item.get("valor_estimado") or item.get("valorEstimado"),
            uf=item.get("uf", uf_upper),
            municipio=item.get("municipio", item.get("municipioOrgao", "")),
            modalidade=item.get("modalidade", item.get("modalidadeNome", "")),
            data_publicacao=item.get("data_publicacao", item.get("dataPublicacao", "")),
            data_abertura=item.get("data_abertura", item.get("dataAbertura")),
            link_pncp=item.get("link_pncp", item.get("linkPncp", "")),
            pncp_id=item.get("pncp_id", item.get("id", "")),
        ))

    response_data = {
        "sector_id": sector_id_clean,
        "sector_name": sector.name,
        "uf": uf_upper,
        "bids": [b.model_dump() for b in bids],
        "total": len(bids),
        "last_updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    _set_cached(cache_key, response_data)
    return AlertasResponse(**response_data)
