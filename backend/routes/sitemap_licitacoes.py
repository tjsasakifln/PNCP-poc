"""STORY-430 AC4: Endpoint público para sitemap — combos setor×UF indexáveis.

Retorna somente as combinações (setor, uf) que possuem >= MIN_ACTIVE_BIDS_FOR_INDEX
editais ativos no datalake. Usado por sitemap.ts para excluir thin content do sitemap.

Público (sem auth). Cache InMemory 24h.
"""

import asyncio
import logging
import os
import time
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from admin import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sitemap"])

_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h
_cache: Optional[tuple[dict, float]] = None

_DEFAULT_THRESHOLD = 5


class LicitacoesIndexableResponse(BaseModel):
    combos: list[dict]  # [{setor: str, uf: str}, ...]
    total: int
    threshold: int
    updated_at: str


@router.get(
    "/sitemap/licitacoes-indexable",
    response_model=LicitacoesIndexableResponse,
    summary="Combos setor×UF indexáveis (público — sitemap)",
)
async def get_licitacoes_indexable():
    """Retorna combos setor×UF com >= threshold editais ativos (últimos 30 dias)."""
    global _cache

    if _cache is not None:
        data, ts = _cache
        if time.time() - ts < _CACHE_TTL_SECONDS:
            return LicitacoesIndexableResponse(**data)

    threshold = int(os.getenv("MIN_ACTIVE_BIDS_FOR_INDEX", str(_DEFAULT_THRESHOLD)))
    combos = await _compute_indexable_combos(threshold)

    from datetime import datetime, timezone
    result = {
        "combos": combos,
        "total": len(combos),
        "threshold": threshold,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _cache = (result, time.time())
    return LicitacoesIndexableResponse(**result)


@router.post(
    "/admin/sitemap-cache/refresh",
    summary="Force-refresh sitemap combos cache (admin only)",
)
async def refresh_sitemap_cache(_admin=Depends(require_admin)):
    """Clears the 24h in-memory sitemap cache and recomputes indexable combos immediately."""
    global _cache
    _cache = None
    threshold = int(os.getenv("MIN_ACTIVE_BIDS_FOR_INDEX", str(_DEFAULT_THRESHOLD)))
    combos = await _compute_indexable_combos(threshold)
    from datetime import datetime, timezone
    result = {
        "combos": combos,
        "total": len(combos),
        "threshold": threshold,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _cache = (result, time.time())
    logger.info("sitemap_licitacoes: cache refreshed manually — %d combos", len(combos))
    return {"status": "refreshed", "total_combos": len(combos), "threshold": threshold}


async def _compute_indexable_combos(threshold: int) -> list[dict]:
    """Consulta datalake por setor e conta resultados por UF.

    15 queries paralelas (uma por setor), cada uma retorna até 3000 resultados.
    Conta por UF e filtra combos com count >= threshold.
    """
    try:
        from datalake_query import query_datalake
        from sectors import SECTORS
    except ImportError:
        logger.warning("sitemap_licitacoes: importações não disponíveis")
        return []

    from datetime import datetime, timedelta
    data_final = datetime.now().strftime("%Y-%m-%d")
    data_inicial = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    all_ufs = [
        "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
        "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
        "RO", "RR", "RS", "SC", "SE", "SP", "TO",
    ]

    async def query_sector(setor_id: str, sector) -> list[dict]:
        """Consulta um setor e retorna lista de {setor, uf} com count >= threshold."""
        keywords = list(sector.keywords)[:30]  # limitar keywords para performance
        try:
            results = await query_datalake(
                ufs=all_ufs,
                keywords=keywords,
                data_inicial=data_inicial,
                data_final=data_final,
                limit=3000,
            )
        except Exception as e:
            logger.warning("sitemap_licitacoes: falha ao consultar setor %s: %s", setor_id, e)
            return []

        # Contar por UF
        uf_counts: dict[str, int] = {}
        for r in results:
            uf = (r.get("uf") or r.get("codigoUnidadeFederativa") or "").upper()
            if uf and len(uf) == 2:
                uf_counts[uf] = uf_counts.get(uf, 0) + 1

        # Retornar combos acima do limiar
        return [
            {"setor": setor_id, "uf": uf.lower()}
            for uf, count in uf_counts.items()
            if count >= threshold
        ]

    # Executar todos os setores em paralelo
    tasks = [query_sector(setor_id, sector) for setor_id, sector in SECTORS.items()]
    results_by_sector = await asyncio.gather(*tasks, return_exceptions=True)

    combos: list[dict] = []
    for res in results_by_sector:
        if isinstance(res, list):
            combos.extend(res)
        elif isinstance(res, Exception):
            logger.warning("sitemap_licitacoes: exception em task: %s", res)

    logger.info("sitemap_licitacoes: %d combos indexáveis (threshold=%d)", len(combos), threshold)
    return combos
