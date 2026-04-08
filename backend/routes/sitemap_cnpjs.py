"""SEO Onda 1: Public endpoint for sitemap CNPJ expansion.

Returns top CNPJs (orgao_cnpj) from pncp_raw_bids with ≥1 bid,
enabling the frontend sitemap to generate /cnpj/{cnpj} URLs for
Google discovery. Public (no auth). Cache: InMemory 24h TTL.

Implementation layers:
1. get_sitemap_cnpjs_json RPC (RETURNS json scalar — bypasses PostgREST max-rows=1000)
2. Fallback: paginated table query (loop 1k/page until exhausted)
"""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sitemap"])

_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h
_sitemap_cache: dict[str, tuple[dict, float]] = {}

_MAX_CNPJS = 5000


class SitemapCnpjsResponse(BaseModel):
    cnpjs: list[str]
    total: int
    updated_at: str


def _get_cached(key: str) -> Optional[dict]:
    if key not in _sitemap_cache:
        return None
    data, ts = _sitemap_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _sitemap_cache[key]
        return None
    return data


def _set_cached(key: str, data: dict) -> None:
    _sitemap_cache[key] = (data, time.time())


@router.get(
    "/sitemap/cnpjs",
    response_model=SitemapCnpjsResponse,
    summary="CNPJs com ≥1 licitação no datalake (para sitemap)",
)
async def sitemap_cnpjs():
    cached = _get_cached("cnpjs")
    if cached:
        return SitemapCnpjsResponse(**cached)

    data = await _fetch_top_cnpjs()
    _set_cached("cnpjs", data)
    return SitemapCnpjsResponse(**data)


async def _fetch_top_cnpjs() -> dict:
    """Query pncp_raw_bids for distinct orgao_cnpj with ≥1 active bid.

    Uses get_sitemap_cnpjs_json RPC (RETURNS json scalar) which bypasses
    PostgREST max-rows=1000. Falls back to paginated table query if RPC
    doesn't exist yet (e.g., migration not yet applied).
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
                cnpj_list = [
                    c for c in raw
                    if c and isinstance(c, str) and len(c) >= 11
                ][:_MAX_CNPJS]
                logger.info(
                    "sitemap_cnpjs (JSON RPC): %d CNPJs returned", len(cnpj_list)
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

        cnpj_list = [
            cnpj
            for cnpj, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)
        ][:_MAX_CNPJS]

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
