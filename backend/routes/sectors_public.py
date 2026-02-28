"""STORY-324: Public sector stats endpoint for SEO landing pages.

Public (no auth) endpoint that returns sector statistics for
programmatic landing pages at /licitacoes/[setor].

Cache: InMemory 6h TTL (AC2).
Data: Lightweight PNCP query per sector (AC1).
Safety: No internal IDs or direct links in sample_items (AC4).
"""

import logging
import time
from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sectors import SECTORS, SectorConfig

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sectors-public"])

# AC2: 6h InMemory cache
_CACHE_TTL_SECONDS = 6 * 60 * 60
_stats_cache: dict[str, tuple[dict, float]] = {}


# ---------------------------------------------------------------------------
# Slug ↔ sector_id helpers (AC8)
# ---------------------------------------------------------------------------

def sector_id_from_slug(slug: str) -> Optional[str]:
    """Convert URL slug to sector ID.

    'manutencao-predial' → 'manutencao_predial'
    """
    sector_id = slug.replace("-", "_")
    if sector_id in SECTORS:
        return sector_id
    return None


def sector_slug(sector_id: str) -> str:
    """Convert sector ID to URL slug."""
    return sector_id.replace("_", "-")


def get_all_sector_slugs() -> list[dict]:
    """Return list of {id, slug, name, description} for all sectors."""
    return [
        {
            "id": s.id,
            "slug": sector_slug(s.id),
            "name": s.name,
            "description": s.description,
        }
        for s in SECTORS.values()
    ]


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class SampleItem(BaseModel):
    titulo: str
    orgao: str
    valor: Optional[float] = None
    uf: str
    data: str


class TopEntry(BaseModel):
    name: str
    count: int


class SectorStatsResponse(BaseModel):
    sector_id: str
    sector_name: str
    sector_description: str
    slug: str
    total_open: int
    total_value: float
    avg_value: float
    top_ufs: list[TopEntry]
    top_modalidades: list[TopEntry]
    sample_items: list[SampleItem]
    last_updated: str


class SectorListItem(BaseModel):
    id: str
    slug: str
    name: str
    description: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/sectors", response_model=list[SectorListItem])
async def list_all_sectors():
    """List all sectors with slug mapping (public, no auth)."""
    return get_all_sector_slugs()


@router.get("/sectors/{slug}/stats", response_model=SectorStatsResponse)
async def get_sector_stats(slug: str):
    """Public sector stats for SEO landing pages (AC1).

    No auth required. Returns cached stats (6h TTL).
    """
    sector_id = sector_id_from_slug(slug)
    if not sector_id:
        raise HTTPException(status_code=404, detail=f"Setor '{slug}' não encontrado")

    sector = SECTORS[sector_id]

    # Check cache (AC2)
    cached = _get_cached_stats(sector_id)
    if cached:
        return SectorStatsResponse(**cached)

    # Generate on-demand if cache miss
    stats = await _generate_sector_stats(sector_id, sector)
    _set_cached_stats(sector_id, stats)

    return SectorStatsResponse(**stats)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _get_cached_stats(sector_id: str) -> Optional[dict]:
    """Return cached stats if still fresh (< 6h)."""
    if sector_id not in _stats_cache:
        return None
    data, ts = _stats_cache[sector_id]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _stats_cache[sector_id]
        return None
    return data


def _set_cached_stats(sector_id: str, data: dict) -> None:
    _stats_cache[sector_id] = (data, time.time())


def invalidate_all_stats() -> None:
    """Clear all cached stats (used by cron to force refresh)."""
    _stats_cache.clear()


# ---------------------------------------------------------------------------
# Stats generation
# ---------------------------------------------------------------------------

async def _generate_sector_stats(sector_id: str, sector: SectorConfig) -> dict:
    """Generate sector stats via lightweight PNCP query.

    Queries top 5 UFs (SP, RJ, MG, DF, PR) for last 10 days,
    filters by sector keywords, and aggregates stats.
    """
    from pncp_client import PNCPClient

    now = datetime.now(timezone.utc)
    data_final = now.strftime("%Y%m%d")
    data_inicial = (now - timedelta(days=10)).strftime("%Y%m%d")

    # Top 5 UFs by procurement volume
    target_ufs = ["SP", "RJ", "MG", "DF", "PR"]
    all_results: list[dict] = []

    try:
        client = PNCPClient()
        for uf in target_ufs:
            try:
                raw = await client.buscar(
                    uf=uf,
                    data_inicial=data_inicial,
                    data_final=data_final,
                    pagina=1,
                    tam_pagina=50,
                )
                items = raw if isinstance(raw, list) else raw.get("data", [])
                all_results.extend(items)
            except Exception as e:
                logger.debug("PNCP query failed for UF=%s sector=%s: %s", uf, sector_id, e)
                continue
    except Exception as e:
        logger.warning("Failed to create PNCPClient for sector %s: %s", sector_id, e)

    # Filter by sector keywords (lightweight — substring match on title/description)
    keywords_lower = {kw.lower() for kw in sector.keywords}
    matched = []
    for item in all_results:
        text = _extract_text(item).lower()
        if any(kw in text for kw in keywords_lower):
            matched.append(item)

    # Compute stats
    return _compute_stats(sector_id, sector, matched, now)


def _extract_text(item: dict) -> str:
    """Extract searchable text from a PNCP result item."""
    parts = [
        item.get("objetoCompra", ""),
        item.get("descricao", ""),
        item.get("objeto", ""),
        item.get("title", ""),
    ]
    return " ".join(p for p in parts if p)


def _compute_stats(
    sector_id: str,
    sector: SectorConfig,
    results: list[dict],
    now: datetime,
) -> dict:
    """Aggregate matched results into sector stats."""
    total = len(results)

    # Value aggregation
    values = []
    for r in results:
        v = r.get("valorTotalEstimado") or r.get("valorEstimado") or r.get("valor_estimado")
        if v and isinstance(v, (int, float)) and v > 0:
            values.append(float(v))

    total_value = sum(values)
    avg_value = total_value / len(values) if values else 0.0

    # Top UFs
    uf_counter: Counter = Counter()
    for r in results:
        uf = r.get("uf") or r.get("unidadeFederativa") or r.get("ufSigla") or ""
        if uf:
            uf_counter[uf] += 1
    top_ufs = [{"name": uf, "count": c} for uf, c in uf_counter.most_common(5)]

    # Top modalidades
    mod_counter: Counter = Counter()
    for r in results:
        mod = r.get("modalidadeNome") or r.get("modalidade") or "Não informada"
        mod_counter[mod] += 1
    top_modalidades = [{"name": m, "count": c} for m, c in mod_counter.most_common(3)]

    # Sample items (AC4: no internal IDs, no direct links)
    sample_items = []
    for r in results[:5]:
        titulo = r.get("objetoCompra") or r.get("objeto") or r.get("title") or "Sem título"
        # Truncate long titles
        if len(titulo) > 120:
            titulo = titulo[:117] + "..."
        orgao = r.get("orgaoEntidade", {}).get("razaoSocial") or r.get("orgao") or r.get("nomeOrgao") or "Não informado"
        valor = r.get("valorTotalEstimado") or r.get("valorEstimado") or r.get("valor_estimado")
        uf = r.get("uf") or r.get("unidadeFederativa") or r.get("ufSigla") or "N/A"
        data = r.get("dataPublicacaoPncp") or r.get("dataAbertura") or r.get("data_publicacao") or ""
        if data and len(data) > 10:
            data = data[:10]  # Keep only YYYY-MM-DD

        sample_items.append({
            "titulo": titulo,
            "orgao": orgao,
            "valor": float(valor) if valor and isinstance(valor, (int, float)) else None,
            "uf": uf,
            "data": data,
        })

    return {
        "sector_id": sector_id,
        "sector_name": sector.name,
        "sector_description": sector.description,
        "slug": sector_slug(sector_id),
        "total_open": total,
        "total_value": round(total_value, 2),
        "avg_value": round(avg_value, 2),
        "top_ufs": top_ufs,
        "top_modalidades": top_modalidades,
        "sample_items": sample_items,
        "last_updated": now.isoformat(),
    }


# ---------------------------------------------------------------------------
# Cron helper (AC3)
# ---------------------------------------------------------------------------

async def refresh_all_sector_stats() -> int:
    """Refresh stats for all 15 sectors. Called by cron job.

    Returns number of sectors successfully refreshed.
    """
    refreshed = 0
    for sector_id, sector in SECTORS.items():
        try:
            stats = await _generate_sector_stats(sector_id, sector)
            _set_cached_stats(sector_id, stats)
            refreshed += 1
            logger.info("Refreshed sector stats: %s (%d items)", sector_id, stats["total_open"])
        except Exception as e:
            logger.error("Failed to refresh sector %s: %s", sector_id, e)
    return refreshed
