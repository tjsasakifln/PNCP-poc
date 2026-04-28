"""STORY-SEO-017: Sitemap endpoint p/ datas indexaveis de /blog/licitacoes-do-dia.

Substitui geracao hardcoded `Array.from({length: 30})` em frontend/app/sitemap.ts
que gerava 42 URLs 404 (datas sem dados em pncp_raw_bids). Retorna apenas datas
da janela 30d com COUNT(bids) >= MIN_BIDS_PER_DAY (default 5), garantindo que
URLs no sitemap sempre retornam 200.

Pattern segue sitemap_orgaos.py (RPC primary com fallback paginado + InMemory cache).
TTL 1h (dia corrente muda durante o dia).
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Response
from pydantic import BaseModel

from metrics import record_sitemap_count
from routes._sitemap_cache_headers import SITEMAP_CACHE_HEADERS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sitemap"])

_CACHE_TTL_SECONDS = 60 * 60  # 1h success — dia corrente muda durante o dia
# Negative cache TTL — same pattern as PR #529 perfil-b2g hotfix.
_NEGATIVE_CACHE_TTL_SECONDS = 5 * 60
_BUDGET_S = 25.0
_cache: dict[str, tuple[dict, float, float]] = {}  # key -> (data, stored_at, ttl)

_WINDOW_DAYS = 30
_MIN_BIDS_PER_DAY = 5  # threshold para considerar dia indexavel


class SitemapLicitacoesDoDiaResponse(BaseModel):
    dates: list[str]  # ISO YYYY-MM-DD, ordenado DESC
    total: int
    updated_at: str


def _get_cached(key: str) -> Optional[dict]:
    entry = _cache.get(key)
    if entry is None:
        return None
    data, ts, ttl = entry
    if time.time() - ts >= ttl:
        del _cache[key]
        return None
    return data


def _set_cached(key: str, data: dict, ttl: float = _CACHE_TTL_SECONDS) -> None:
    _cache[key] = (data, time.time(), ttl)


def _empty_dates_response() -> dict:
    return {
        "dates": [],
        "total": 0,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/sitemap/licitacoes-do-dia-indexable",
    response_model=SitemapLicitacoesDoDiaResponse,
    summary="Datas dos ultimos 30d com >=5 bids ativos (sitemap /blog/licitacoes-do-dia/)",
)
async def sitemap_licitacoes_do_dia_indexable(response: Response):
    """Retorna apenas datas com bids suficientes para ter pagina renderizavel.

    Elimina os 42 URLs 404 reportados no GSC sweep 2026-04-24.
    """
    response.headers.update(SITEMAP_CACHE_HEADERS)
    cached = _get_cached("dates")
    if cached:
        record_sitemap_count("licitacoes-do-dia-indexable", len(cached.get("dates", [])))
        return SitemapLicitacoesDoDiaResponse(**cached)

    try:
        data = await asyncio.wait_for(
            asyncio.to_thread(_fetch_indexable_dates),
            timeout=_BUDGET_S,
        )
        _set_cached("dates", data, ttl=_CACHE_TTL_SECONDS)
    except asyncio.TimeoutError:
        logger.warning(
            "sitemap_licitacoes_do_dia: budget %.0fs exceeded — empty negative cache",
            _BUDGET_S,
        )
        data = _empty_dates_response()
        _set_cached("dates", data, ttl=_NEGATIVE_CACHE_TTL_SECONDS)
    except Exception as exc:
        logger.error("sitemap_licitacoes_do_dia unexpected error: %s", exc)
        data = _empty_dates_response()
        _set_cached("dates", data, ttl=_NEGATIVE_CACHE_TTL_SECONDS)

    record_sitemap_count("licitacoes-do-dia-indexable", len(data.get("dates", [])))
    return SitemapLicitacoesDoDiaResponse(**data)


def _fetch_indexable_dates() -> dict:
    """Scan pncp_raw_bids janela 30d, conta por data, filtra HAVING >=5.

    Implementa client-side aggregation: paginated fetch de data_publicacao
    apenas (1 col) -> Counter -> filter -> sort DESC.

    50K rows tipico em 30d / 1k per page = ~50 round-trips. Tolerante porque
    cache TTL 1h reduz para 1x/h por worker.
    """
    try:
        from supabase_client import get_supabase

        sb = get_supabase()

        cutoff = (datetime.now(timezone.utc) - timedelta(days=_WINDOW_DAYS)).date().isoformat()

        date_counts: dict[str, int] = {}
        page_size = 1000
        offset = 0
        page_count = 0

        while True:
            resp = (
                sb.table("pncp_raw_bids")
                .select("data_publicacao")
                .eq("is_active", True)
                .gte("data_publicacao", cutoff)
                .not_.is_("data_publicacao", "null")
                .range(offset, offset + page_size - 1)
                .execute()
            )
            page_count += 1
            if not resp.data:
                break

            for row in resp.data:
                raw = row.get("data_publicacao")
                if not raw:
                    continue
                # data_publicacao pode ser ISO datetime ou date — extrair YYYY-MM-DD
                date_str = str(raw)[:10]
                if len(date_str) == 10 and date_str[4] == "-" and date_str[7] == "-":
                    date_counts[date_str] = date_counts.get(date_str, 0) + 1

            if len(resp.data) < page_size:
                break
            offset += page_size

            # safety: nao iterar alem de 200 paginas (200K rows) — anomalia
            if page_count >= 200:
                logger.warning(
                    "sitemap_licitacoes_do_dia: stopped at 200 pages — investigate"
                )
                break

        indexable = sorted(
            (date for date, count in date_counts.items() if count >= _MIN_BIDS_PER_DAY),
            reverse=True,
        )

        logger.info(
            "sitemap_licitacoes_do_dia (paginated): %d distinct dates, %d indexable (>=%d bids), %d pages",
            len(date_counts),
            len(indexable),
            _MIN_BIDS_PER_DAY,
            page_count,
        )

        return {
            "dates": indexable,
            "total": len(indexable),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("sitemap_licitacoes_do_dia failed: %s", e)
        return {
            "dates": [],
            "total": 0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
