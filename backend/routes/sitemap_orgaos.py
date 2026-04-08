"""SEO Onda 2: Public endpoint for sitemap órgão expansion.

Returns top órgãos compradores (by orgao_cnpj) from pncp_raw_bids with ≥5 bids,
enabling the frontend sitemap to generate /orgao/{cnpj} URLs for
Google discovery. Public (no auth). Cache: InMemory 24h TTL.
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

_MIN_BIDS = 5
_MAX_ORGAOS = 2000


class SitemapOrgaosResponse(BaseModel):
    orgaos: list[str]
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
    "/sitemap/orgaos",
    response_model=SitemapOrgaosResponse,
    summary="Órgãos compradores com ≥5 licitações no datalake (para sitemap)",
)
async def sitemap_orgaos():
    cached = _get_cached("orgaos")
    if cached:
        return SitemapOrgaosResponse(**cached)

    data = await _fetch_top_orgaos()
    _set_cached("orgaos", data)
    return SitemapOrgaosResponse(**data)


async def _fetch_top_orgaos() -> dict:
    """Query pncp_raw_bids for distinct orgao_cnpj with ≥5 active bids."""
    try:
        from supabase_client import get_supabase

        sb = get_supabase()
        resp = (
            sb.table("pncp_raw_bids")
            .select("orgao_cnpj")
            .eq("is_active", True)
            .not_.is_("orgao_cnpj", "null")
            .neq("orgao_cnpj", "")
            .limit(50000)
            .execute()
        )

        # Count occurrences per CNPJ de órgão
        counts: dict[str, int] = {}
        for row in resp.data or []:
            cnpj = (row.get("orgao_cnpj") or "").strip()
            if cnpj and len(cnpj) >= 11:  # Valid CNPJ length
                counts[cnpj] = counts.get(cnpj, 0) + 1

        # Filter ≥ _MIN_BIDS and sort by count desc
        filtered = sorted(
            ((cnpj, cnt) for cnpj, cnt in counts.items() if cnt >= _MIN_BIDS),
            key=lambda x: x[1],
            reverse=True,
        )[:_MAX_ORGAOS]

        orgao_list = [cnpj for cnpj, _ in filtered]
        logger.info(
            "sitemap_orgaos: %d órgãos with ≥%d bids (from %d total distinct)",
            len(orgao_list),
            _MIN_BIDS,
            len(counts),
        )

        return {
            "orgaos": orgao_list,
            "total": len(orgao_list),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("sitemap_orgaos failed: %s", e)
        return {
            "orgaos": [],
            "total": 0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
