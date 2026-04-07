"""S3: Public bid comparison tool for SEO comparador pages.

Public (no auth) endpoints for searching and comparing bids from datalake.

Endpoints:
  GET /comparador/buscar?q=termo&uf=XX — search bids by text query
  GET /comparador/bids?ids=id1,id2,id3 — fetch specific bids by pncp_id

Cache: InMemory 1h TTL.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/comparador", tags=["comparador"])

# 1h InMemory cache (matches ISR revalidation period)
_CACHE_TTL_SECONDS = 60 * 60
_comparador_cache: dict[str, tuple[dict, float]] = {}

ALL_UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]


class ComparadorBid(BaseModel):
    pncp_id: str
    titulo: str
    orgao: str
    valor: Optional[float] = None
    uf: str
    municipio: str = ""
    modalidade: str = ""
    data_publicacao: str
    data_abertura: Optional[str] = None
    link_pncp: str = ""


class ComparadorSearchResponse(BaseModel):
    query: str
    uf: Optional[str]
    bids: list[ComparadorBid]
    total: int


class ComparadorBidsResponse(BaseModel):
    bids: list[ComparadorBid]
    total: int


def _get_cached(key: str) -> Optional[dict]:
    if key not in _comparador_cache:
        return None
    data, ts = _comparador_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _comparador_cache[key]
        return None
    return data


def _set_cached(key: str, data: dict) -> None:
    _comparador_cache[key] = (data, time.time())


def _item_to_bid(item: dict) -> ComparadorBid:
    """Convert a datalake dict to ComparadorBid."""
    return ComparadorBid(
        pncp_id=item.get("pncp_id", item.get("id", "")),
        titulo=item.get("titulo", "Sem título"),
        orgao=item.get("orgao", item.get("nomeOrgao", "")),
        valor=item.get("valor_estimado") or item.get("valorEstimado"),
        uf=item.get("uf", ""),
        municipio=item.get("municipio", item.get("municipioOrgao", "")),
        modalidade=item.get("modalidade", item.get("modalidadeNome", "")),
        data_publicacao=item.get("data_publicacao", item.get("dataPublicacao", "")),
        data_abertura=item.get("data_abertura", item.get("dataAbertura")),
        link_pncp=item.get("link_pncp", item.get("linkPncp", "")),
    )


@router.get("/buscar", response_model=ComparadorSearchResponse)
async def buscar_editais(
    q: str = Query(..., min_length=3, description="Termo de busca (mínimo 3 caracteres)"),
    uf: Optional[str] = Query(None, description="Filtrar por UF (ex: SP, RJ)"),
):
    """Search bids by text query from datalake (public, no auth)."""
    uf_upper: Optional[str] = None
    if uf:
        uf_upper = uf.upper()
        if uf_upper not in ALL_UFS:
            raise HTTPException(status_code=404, detail=f"UF '{uf}' não encontrada")

    # Check cache
    cache_key = f"comparador:search:{q}:{uf_upper}"
    cached = _get_cached(cache_key)
    if cached:
        return ComparadorSearchResponse(**cached)

    # Query datalake
    from datalake_query import query_datalake

    now = datetime.now(timezone.utc)
    data_final = now.strftime("%Y-%m-%d")
    data_inicial = (now - timedelta(days=10)).strftime("%Y-%m-%d")

    try:
        results = await query_datalake(
            custom_terms=[q],
            ufs=[uf_upper] if uf_upper else ALL_UFS,
            limit=50,
            data_inicial=data_inicial,
            data_final=data_final,
        )
    except Exception as e:
        logger.warning("Failed to query datalake for comparador search q=%s uf=%s: %s", q, uf_upper, e)
        results = []

    # Sort by date descending (copy to avoid mutating caller's list), take top 10
    results = sorted(results, key=lambda x: x.get("data_publicacao", ""), reverse=True)[:10]

    bids = [_item_to_bid(item) for item in results]

    response_data = {
        "query": q,
        "uf": uf_upper,
        "bids": [b.model_dump() for b in bids],
        "total": len(bids),
    }

    _set_cached(cache_key, response_data)
    return ComparadorSearchResponse(**response_data)


@router.get("/bids", response_model=ComparadorBidsResponse)
async def get_bids_by_ids(
    ids: str = Query(..., description="Comma-separated pncp_ids (max 5)"),
):
    """Fetch specific bids by pncp_id from datalake (public, no auth)."""
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    if len(id_list) > 5:
        raise HTTPException(status_code=400, detail="Máximo de 5 IDs permitidos por requisição")
    if not id_list:
        return ComparadorBidsResponse(bids=[], total=0)

    # Check cache
    sorted_ids = ",".join(sorted(id_list))
    cache_key = f"comparador:bids:{sorted_ids}"
    cached = _get_cached(cache_key)
    if cached:
        return ComparadorBidsResponse(**cached)

    # Query supabase directly for exact pncp_id matches
    try:
        sb = get_supabase()
        result = sb.table("pncp_raw_bids").select("*").in_("pncp_id", id_list).execute()
        rows = result.data or []
    except Exception as e:
        logger.warning("Failed to query pncp_raw_bids for ids=%s: %s", id_list, e)
        rows = []

    bids = [_item_to_bid(row) for row in rows]

    response_data = {
        "bids": [b.model_dump() for b in bids],
        "total": len(bids),
    }

    _set_cached(cache_key, response_data)
    return ComparadorBidsResponse(**response_data)
