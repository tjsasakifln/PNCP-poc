"""SEO Onda 1 + Sprint 3 Parte 13: Public endpoints for sitemap CNPJ expansion.

/sitemap/cnpjs: top orgao_cnpj de pncp_raw_bids (compradores, Onda 1)
/sitemap/fornecedores-cnpj: top ni_fornecedor de pncp_supplier_contracts (Sprint 3 Parte 13)

Publico (sem auth). Cache: InMemory 24h TTL.

Layers de implementacao (/sitemap/cnpjs):
1. get_sitemap_cnpjs_json RPC (RETURNS json scalar — bypassa PostgREST max-rows=1000)
2. Fallback: paginated table query (loop 1k/page ate esgotar)
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel

from metrics import record_sitemap_count
from routes._sitemap_cache_headers import SITEMAP_CACHE_HEADERS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sitemap"])

_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h success
# Negative cache: when DB query saturates and we time out, cache an empty
# response for 5 min so the next ISR rebuild / crawler hit returns instantly
# instead of re-saturating the pool. Same pattern as PR #529 perfil-b2g hotfix.
_NEGATIVE_CACHE_TTL_SECONDS = 5 * 60
# Hard async budget: must respond within this window or fall through to
# negative cache. supabase-py is sync, so the actual DB call runs in a
# worker thread (asyncio.to_thread) — the budget bounds total async wait.
_BUDGET_S = 25.0
_sitemap_cache: dict[str, tuple[dict, float, float]] = {}  # key -> (data, stored_at, ttl)

_MAX_CNPJS = 5000

# Seed list: CNPJs de empresas fornecedoras (B2G suppliers) com relatórios intel gerados.
# Estes aparecem PRIMEIRO no sitemap (prioridade sobre compradores/órgãos)
# para garantir indexação de fornecedores com conteúdo rico de contratos.
_SEED_SUPPLIER_CNPJS: list[str] = [
    "01721078000168",  # LCM Construções
    "07186297000170",  # CRV Construtora Rezende & Alvarenga
    "09225035000101",  # GJS Construções
    "18742098000118",  # Trena Terraplenagem
    "24515063000149",  # Extra Empreiteira
    "26420889000150",  # Gamarra Construtora
    "27735305000106",  # Infrainga Engenharia
    "33256335000124",  # Distriminas
    "39336452000184",  # Construsol Sobralense
    "42192677000119",  # LCA Infraestrutura
    "47673948000171",  # Borges Gomes
]


class SitemapCnpjsResponse(BaseModel):
    cnpjs: list[str]
    total: int
    updated_at: str


class SitemapFornecedoresCnpjResponse(BaseModel):
    cnpjs: list[str]
    total: int
    updated_at: str


_MAX_FORNECEDORES_CNPJS = 5000

_fornecedores_sitemap_cache: dict[str, tuple[dict, float, float]] = {}  # key -> (data, stored_at, ttl)


def _get_cached(key: str) -> Optional[dict]:
    if key not in _sitemap_cache:
        return None
    data, ts, ttl = _sitemap_cache[key]
    if time.time() - ts >= ttl:
        del _sitemap_cache[key]
        return None
    return data


def _set_cached(key: str, data: dict, ttl: float = _CACHE_TTL_SECONDS) -> None:
    _sitemap_cache[key] = (data, time.time(), ttl)


def _get_fornecedores_cached(key: str) -> Optional[dict]:
    if key not in _fornecedores_sitemap_cache:
        return None
    data, ts, ttl = _fornecedores_sitemap_cache[key]
    if time.time() - ts >= ttl:
        del _fornecedores_sitemap_cache[key]
        return None
    return data


def _set_fornecedores_cached(key: str, data: dict, ttl: float = _CACHE_TTL_SECONDS) -> None:
    _fornecedores_sitemap_cache[key] = (data, time.time(), ttl)


@router.get(
    "/sitemap/cnpjs",
    response_model=SitemapCnpjsResponse,
    summary="CNPJs com ≥1 licitação no datalake (para sitemap)",
)
async def sitemap_cnpjs(response: Response):
    response.headers.update(SITEMAP_CACHE_HEADERS)
    cached = _get_cached("cnpjs")
    if cached:
        record_sitemap_count("cnpjs", len(cached.get("cnpjs", [])))
        return SitemapCnpjsResponse(**cached)

    try:
        data = await asyncio.wait_for(
            asyncio.to_thread(_fetch_top_cnpjs),
            timeout=_BUDGET_S,
        )
        _set_cached("cnpjs", data, ttl=_CACHE_TTL_SECONDS)
    except asyncio.TimeoutError:
        logger.warning(
            "sitemap_cnpjs: budget %.0fs exceeded — returning empty negative cache",
            _BUDGET_S,
        )
        data = _empty_cnpjs_response()
        _set_cached("cnpjs", data, ttl=_NEGATIVE_CACHE_TTL_SECONDS)
    except Exception as exc:
        logger.error("sitemap_cnpjs unexpected error: %s", exc)
        data = _empty_cnpjs_response()
        _set_cached("cnpjs", data, ttl=_NEGATIVE_CACHE_TTL_SECONDS)

    record_sitemap_count("cnpjs", len(data.get("cnpjs", [])))
    return SitemapCnpjsResponse(**data)


def _empty_cnpjs_response() -> dict:
    return {
        "cnpjs": [],
        "total": 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _merge_with_seed(buyer_cnpjs: list[str]) -> list[str]:
    """Merge seed supplier CNPJs (priority) with buyer CNPJs, dedup, cap at _MAX_CNPJS."""
    seen: set[str] = set()
    result: list[str] = []
    # Seed suppliers first — they have richer contract content
    for cnpj in _SEED_SUPPLIER_CNPJS:
        if cnpj not in seen:
            seen.add(cnpj)
            result.append(cnpj)
    # Then buyer CNPJs (orgaos)
    for cnpj in buyer_cnpjs:
        if cnpj not in seen:
            seen.add(cnpj)
            result.append(cnpj)
    return result[:_MAX_CNPJS]


def _fetch_top_cnpjs() -> dict:
    """Query pncp_raw_bids for distinct orgao_cnpj with ≥1 active bid.

    Sync — supabase-py is sync, so caller wraps this in asyncio.to_thread
    to keep the event loop free. Uses get_sitemap_cnpjs_json RPC
    (RETURNS json scalar) which bypasses PostgREST max-rows=1000. Falls
    back to paginated table query if RPC doesn't exist yet.
    """
    try:
        from supabase_client import get_supabase

        sb = get_supabase()

        # Primary: JSON scalar RPC — not subject to max-rows limit
        try:
            resp = sb.rpc("get_sitemap_cnpjs_json", {"max_results": _MAX_CNPJS}).execute()
            if resp.data is not None:
                # resp.data is a JSON array of CNPJ strings
                raw = resp.data if isinstance(resp.data, list) else []
                buyer_list = [
                    c for c in raw
                    if c and isinstance(c, str) and len(c) >= 11
                ]
                cnpj_list = _merge_with_seed(buyer_list)
                logger.info(
                    "sitemap_cnpjs (JSON RPC): %d buyers + %d seed suppliers = %d total",
                    len(buyer_list),
                    len(_SEED_SUPPLIER_CNPJS),
                    len(cnpj_list),
                )
                return {
                    "cnpjs": cnpj_list,
                    "total": len(cnpj_list),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as rpc_err:
            logger.warning(
                "sitemap_cnpjs JSON RPC failed (%s), falling back to paginated query",
                rpc_err,
            )

        # Fallback: paginated table query (1k rows/page, full scan)
        counts: dict[str, int] = {}
        page_size = 1000
        offset = 0
        while True:
            resp = (
                sb.table("pncp_raw_bids")
                .select("orgao_cnpj")
                .eq("is_active", True)
                .not_.is_("orgao_cnpj", "null")
                .neq("orgao_cnpj", "")
                .range(offset, offset + page_size - 1)
                .execute()
            )
            if not resp.data:
                break
            for row in resp.data:
                cnpj = (row.get("orgao_cnpj") or "").strip()
                if cnpj and len(cnpj) >= 11:
                    counts[cnpj] = counts.get(cnpj, 0) + 1
            if len(resp.data) < page_size:
                break
            offset += page_size

        buyer_list = [
            cnpj
            for cnpj, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ]
        cnpj_list = _merge_with_seed(buyer_list)

        logger.info(
            "sitemap_cnpjs (paginated): %d CNPJs from %d distinct, %d pages",
            len(cnpj_list),
            len(counts),
            (offset // page_size) + 1,
        )

        return {
            "cnpjs": cnpj_list,
            "total": len(cnpj_list),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("sitemap_cnpjs failed: %s", e)
        return {
            "cnpjs": [],
            "total": 0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Sprint 3 Parte 13: sitemap de fornecedores por CNPJ (/fornecedores/{cnpj})
# ---------------------------------------------------------------------------

@router.get(
    "/sitemap/fornecedores-cnpj",
    response_model=SitemapFornecedoresCnpjResponse,
    summary="Top CNPJs de fornecedores com contratos no datalake (para sitemap)",
)
async def sitemap_fornecedores_cnpj(response: Response):
    """Retorna os CNPJs de fornecedores com mais contratos em pncp_supplier_contracts.

    Usado pelo frontend para gerar /fornecedores/{cnpj} no sitemap.xml.
    Limite: 5.000 CNPJs por volume de contratos (mais contratos = maior valor SEO).
    Cache: 24h em memoria sucesso, 5min em falha (negative cache PR #529 pattern).
    """
    response.headers.update(SITEMAP_CACHE_HEADERS)
    cached = _get_fornecedores_cached("fornecedores_cnpj")
    if cached:
        record_sitemap_count("fornecedores-cnpj", len(cached.get("cnpjs", [])))
        return SitemapFornecedoresCnpjResponse(**cached)

    try:
        data = await asyncio.wait_for(
            asyncio.to_thread(_fetch_top_fornecedores_cnpjs),
            timeout=_BUDGET_S,
        )
        _set_fornecedores_cached("fornecedores_cnpj", data, ttl=_CACHE_TTL_SECONDS)
    except asyncio.TimeoutError:
        logger.warning(
            "sitemap_fornecedores_cnpj: budget %.0fs exceeded — returning empty negative cache",
            _BUDGET_S,
        )
        data = _empty_cnpjs_response()
        _set_fornecedores_cached("fornecedores_cnpj", data, ttl=_NEGATIVE_CACHE_TTL_SECONDS)
    except Exception as exc:
        logger.error("sitemap_fornecedores_cnpj unexpected error: %s", exc)
        data = _empty_cnpjs_response()
        _set_fornecedores_cached("fornecedores_cnpj", data, ttl=_NEGATIVE_CACHE_TTL_SECONDS)

    record_sitemap_count("fornecedores-cnpj", len(data.get("cnpjs", [])))
    return SitemapFornecedoresCnpjResponse(**data)


def _fetch_top_fornecedores_cnpjs() -> dict:
    """Busca os CNPJs de fornecedores mais ativos em pncp_supplier_contracts.

    Estrategia: paginated scan para contar contratos por ni_fornecedor,
    ordenar por volume e retornar os top _MAX_FORNECEDORES_CNPJS.
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        counts: dict[str, int] = {}
        page_size = 1000
        offset = 0
        while len(counts) < _MAX_FORNECEDORES_CNPJS * 5:
            resp = (
                sb.table("pncp_supplier_contracts")
                .select("ni_fornecedor")
                .eq("is_active", True)
                .not_.is_("ni_fornecedor", "null")
                .neq("ni_fornecedor", "")
                .range(offset, offset + page_size - 1)
                .execute()
            )
            if not resp.data:
                break
            for row in resp.data:
                cnpj = (row.get("ni_fornecedor") or "").strip()
                # Aceitar apenas CNPJs de 14 digitos numericos
                if cnpj and len(cnpj) == 14 and cnpj.isdigit():
                    counts[cnpj] = counts.get(cnpj, 0) + 1
            if len(resp.data) < page_size:
                break
            offset += page_size

        cnpj_list = [
            cnpj
            for cnpj, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ][:_MAX_FORNECEDORES_CNPJS]

        logger.info(
            "sitemap_fornecedores_cnpj: %d CNPJs de %d distintos",
            len(cnpj_list),
            len(counts),
        )

        return {
            "cnpjs": cnpj_list,
            "total": len(cnpj_list),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("sitemap_fornecedores_cnpj failed: %s", e)
        return {
            "cnpjs": [],
            "total": 0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
