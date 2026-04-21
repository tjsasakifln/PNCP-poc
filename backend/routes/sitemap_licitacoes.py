"""SEO-471: Endpoint público para sitemap — combos setor×UF indexáveis.

Retorna a união de dois conjuntos:
1. Combos com bids >= MIN_ACTIVE_BIDS_FOR_INDEX no datalake (últimos 30 dias)
2. Combos com contracts >= MIN_CONTRACTS_FOR_INDEX em pncp_supplier_contracts

Usado por sitemap.ts para excluir thin content do sitemap.
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
from metrics import record_sitemap_count

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sitemap"])

_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h
_cache: Optional[tuple[dict, float]] = None

_DEFAULT_BIDS_THRESHOLD = 5
_DEFAULT_CONTRACTS_THRESHOLD = 1

_ALL_UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]


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
    """Retorna combos setor×UF com bids OR contracts suficientes."""
    global _cache

    if _cache is not None:
        data, ts = _cache
        if time.time() - ts < _CACHE_TTL_SECONDS:
            record_sitemap_count("licitacoes-indexable", len(data.get("combos", [])))
            return LicitacoesIndexableResponse(**data)

    bids_threshold = int(os.getenv("MIN_ACTIVE_BIDS_FOR_INDEX", str(_DEFAULT_BIDS_THRESHOLD)))
    combos = await _compute_indexable_combos(bids_threshold)

    from datetime import datetime, timezone
    result = {
        "combos": combos,
        "total": len(combos),
        "threshold": bids_threshold,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _cache = (result, time.time())
    record_sitemap_count("licitacoes-indexable", len(combos))
    return LicitacoesIndexableResponse(**result)


@router.post(
    "/admin/sitemap-cache/refresh",
    summary="Force-refresh sitemap combos cache (admin only)",
)
async def refresh_sitemap_cache(_admin=Depends(require_admin)):
    """Clears the 24h in-memory sitemap cache and recomputes indexable combos immediately."""
    global _cache
    _cache = None
    bids_threshold = int(os.getenv("MIN_ACTIVE_BIDS_FOR_INDEX", str(_DEFAULT_BIDS_THRESHOLD)))
    combos = await _compute_indexable_combos(bids_threshold)
    from datetime import datetime, timezone
    result = {
        "combos": combos,
        "total": len(combos),
        "threshold": bids_threshold,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _cache = (result, time.time())
    logger.info("sitemap_licitacoes: cache refreshed manually — %d combos", len(combos))
    return {"status": "refreshed", "total_combos": len(combos), "threshold": bids_threshold}


async def _compute_indexable_combos(bids_threshold: int) -> list[dict]:
    """Retorna a união de combos por bids e por contratos históricos.

    Executa as duas fontes em paralelo e faz dedup por (setor, uf).
    Loga quantos combos vieram de cada fonte (AC9).
    """
    contracts_threshold = int(os.getenv("MIN_CONTRACTS_FOR_INDEX", str(_DEFAULT_CONTRACTS_THRESHOLD)))

    # Paralelismo: bids como Task (inicia imediatamente) + contracts com timeout.
    # Sem timeout, 405 RPCs com ILIKE travam o event loop por >120s.
    _CONTRACTS_TIMEOUT_S = int(os.getenv("CONTRACTS_COMPUTE_TIMEOUT_S", "60"))
    bids_task = asyncio.create_task(_compute_bids_combos(bids_threshold))

    try:
        contracts_combos = await asyncio.wait_for(
            _compute_contracts_combos(contracts_threshold),
            timeout=_CONTRACTS_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "sitemap_licitacoes: _compute_contracts_combos excedeu %ds — retornando vazio",
            _CONTRACTS_TIMEOUT_S,
        )
        contracts_combos = []

    bids_combos = await bids_task

    # União dedup: bids têm precedência, contracts adicionam apenas combos novos
    seen: set[tuple[str, str]] = set()
    for c in bids_combos:
        seen.add((c["setor"], c["uf"]))

    contracts_only: list[dict] = []
    for c in contracts_combos:
        key = (c["setor"], c["uf"])
        if key not in seen:
            contracts_only.append(c)
            seen.add(key)

    all_combos = bids_combos + contracts_only

    logger.info(
        "sitemap_licitacoes: %d combos de bids + %d combos exclusivos de contratos = %d total "
        "(bids_threshold=%d, contracts_threshold=%d)",
        len(bids_combos),
        len(contracts_only),
        len(all_combos),
        bids_threshold,
        contracts_threshold,
    )
    return all_combos


async def _compute_bids_combos(threshold: int) -> list[dict]:
    """Consulta datalake por setor e conta resultados por UF.

    15 queries paralelas (uma por setor), cada uma retorna até 3000 resultados.
    Conta por UF e filtra combos com count >= threshold.
    """
    try:
        from datalake_query import query_datalake
        from sectors import SECTORS
    except ImportError:
        logger.warning("sitemap_licitacoes: importações de bids não disponíveis")
        return []

    from datetime import datetime, timedelta
    data_final = datetime.now().strftime("%Y-%m-%d")
    data_inicial = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    async def query_sector(setor_id: str, sector) -> list[dict]:
        keywords = list(sector.keywords)[:30]
        try:
            results = await query_datalake(
                ufs=_ALL_UFS,
                keywords=keywords,
                data_inicial=data_inicial,
                data_final=data_final,
                limit=3000,
            )
        except Exception as e:
            logger.warning("sitemap_licitacoes: falha ao consultar bids setor %s: %s", setor_id, e)
            return []

        uf_counts: dict[str, int] = {}
        for r in results:
            uf = (r.get("uf") or r.get("codigoUnidadeFederativa") or "").upper()
            if uf and len(uf) == 2:
                uf_counts[uf] = uf_counts.get(uf, 0) + 1

        return [
            {"setor": setor_id, "uf": uf.lower()}
            for uf, count in uf_counts.items()
            if count >= threshold
        ]

    tasks = [query_sector(setor_id, sector) for setor_id, sector in SECTORS.items()]
    results_by_sector = await asyncio.gather(*tasks, return_exceptions=True)

    combos: list[dict] = []
    for res in results_by_sector:
        if isinstance(res, list):
            combos.extend(res)
        elif isinstance(res, Exception):
            logger.warning("sitemap_licitacoes: exception em bids task: %s", res)

    return combos


async def _compute_contracts_combos(threshold: int) -> list[dict]:
    """Consulta pncp_supplier_contracts via RPC count_contracts_by_setor_uf.

    15 setores × 27 UFs = 405 RPCs disparadas com Semaphore(10) para limitar
    concorrência ao banco. Sem throttle, 405 conexões simultâneas travam o
    event loop e causam timeout em todos os outros endpoints.
    """
    try:
        from supabase_client import get_supabase
        from sectors import SECTORS
    except ImportError:
        logger.warning("sitemap_licitacoes: importações de contracts não disponíveis")
        return []

    try:
        sb = get_supabase()
    except Exception as e:
        logger.warning("sitemap_licitacoes: falha ao obter supabase client: %s", e)
        return []

    # Limite de concorrência: evita disparar 405 RPCs simultâneas ao Supabase,
    # o que travava o event loop (528s por tick observado em prod).
    _sem = asyncio.Semaphore(10)

    async def count_contracts(setor_id: str, keywords: list[str], uf: str) -> tuple[str, str, int]:
        """Chama RPC count_contracts_by_setor_uf para um par (setor, uf)."""
        async with _sem:
            try:
                resp = await asyncio.to_thread(
                    lambda: sb.rpc(
                        "count_contracts_by_setor_uf",
                        {"p_keywords": keywords, "p_uf": uf},
                    ).execute()
                )
                count = resp.data if isinstance(resp.data, int) else 0
                return setor_id, uf, count
            except Exception as e:
                logger.debug(
                    "sitemap_licitacoes: contracts RPC falhou setor=%s uf=%s: %s",
                    setor_id, uf, e,
                )
                return setor_id, uf, 0

    async def query_sector_contracts(setor_id: str, sector) -> list[dict]:
        """Consulta todos as UFs para um setor em paralelo (throttled pelo semaphore global)."""
        keywords = list(sector.keywords)[:20]
        uf_tasks = [count_contracts(setor_id, keywords, uf) for uf in _ALL_UFS]
        results = await asyncio.gather(*uf_tasks, return_exceptions=True)

        combos = []
        for r in results:
            if isinstance(r, tuple):
                _, uf, count = r
                if count >= threshold:
                    combos.append({"setor": setor_id, "uf": uf.lower()})
            elif isinstance(r, Exception):
                logger.debug("sitemap_licitacoes: exception em contracts uf task: %s", r)
        return combos

    sector_tasks = [
        query_sector_contracts(setor_id, sector)
        for setor_id, sector in SECTORS.items()
    ]
    results_by_sector = await asyncio.gather(*sector_tasks, return_exceptions=True)

    combos: list[dict] = []
    for res in results_by_sector:
        if isinstance(res, list):
            combos.extend(res)
        elif isinstance(res, Exception):
            logger.warning("sitemap_licitacoes: exception em contracts sector task: %s", res)

    return combos
