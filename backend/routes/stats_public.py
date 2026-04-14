"""Public statistics endpoint for /estatisticas SEO page.

Returns ~15-20 aggregate stats from the PNCP datalake (last 30 days).
Public (no auth). Cache: InMemory 6h TTL.
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from public_rate_limit import rate_limit_public

logger = logging.getLogger(__name__)
router = APIRouter(
    tags=["stats_public"],
    # STORY-2.10 (EPIC-TD-2026Q2 P0): Rate limit público (60/min por IP).
    dependencies=[
        Depends(
            rate_limit_public(
                limit_unauth=60,
                limit_auth=600,
                endpoint_name="stats_public",
            )
        )
    ],
)

_CACHE_TTL_SECONDS = 6 * 60 * 60  # 6h
_stats_cache: dict[str, tuple[dict, float]] = {}

_MODALIDADE_NAMES: dict[int, str] = {
    4: "Concorrência",
    5: "Pregão Eletrônico",
    6: "Pregão Presencial",
    7: "Leilão",
    8: "Dispensa",
    12: "Credenciamento",
}


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class PublicStat(BaseModel):
    id: str
    label: str
    value: float
    formatted_value: str
    unit: str
    context: str
    source: str
    period: str
    sector: Optional[str] = None
    uf: Optional[str] = None


class DataDownloadSchema(BaseModel):
    type: str = "DataDownload"
    encoding_format: str = "application/json"
    content_url: str = "https://smartlic.tech/v1/stats/public"


class PublicStatsResponse(BaseModel):
    updated_at: str
    total_stats: int
    stats: list[PublicStat]
    data_download: dict | None = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/stats/public",
    summary="Estatísticas públicas agregadas do PNCP (sem auth)",
)
async def stats_public(
    format: str = Query(default="json", description="json | embed | badge"),
):
    cached = _get_cached("global")
    if not cached:
        cached = await _generate_stats()
        _set_cached("global", cached)

    if format == "embed":
        return _build_embed_html(cached)
    if format == "badge":
        return _build_badge_svg(cached)

    # JSON (default) — include DataDownload schema
    cached["data_download"] = {
        "@type": "DataDownload",
        "encodingFormat": "application/json",
        "contentUrl": "https://smartlic.tech/v1/stats/public",
    }
    return PublicStatsResponse(**cached)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _get_cached(key: str) -> Optional[dict]:
    if key not in _stats_cache:
        return None
    data, ts = _stats_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _stats_cache[key]
        return None
    return data


def _set_cached(key: str, data: dict) -> None:
    _stats_cache[key] = (data, time.time())


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _fmt_int(n: float) -> str:
    """Format integer with dot-separated thousands (Brazilian locale)."""
    return f"{int(n):,}".replace(",", ".")


def _fmt_brl(v: float) -> str:
    """Format BRL value abbreviating large numbers."""
    if v >= 1_000_000_000:
        return f"R$ {v / 1_000_000_000:.1f} bi".replace(".", ",")
    if v >= 1_000_000:
        return f"R$ {v / 1_000_000:.1f} mi".replace(".", ",")
    if v >= 1_000:
        return f"R$ {v / 1_000:.0f} mil"
    return f"R$ {v:.0f}"


def _fmt_pct(v: float) -> str:
    return f"{v:.1f}%".replace(".", ",")


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------


async def _generate_stats() -> dict:
    from datalake_query import query_datalake
    from sectors import SECTORS

    now = datetime.now(timezone.utc)
    updated_at = now.isoformat()
    data_final = now.strftime("%Y-%m-%d")
    data_inicial = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    all_results: list[dict] = []
    try:
        from unified_schemas.unified import VALID_UFS
        all_results = await query_datalake(
            ufs=list(VALID_UFS),
            data_inicial=data_inicial,
            data_final=data_final,
            limit=5000,
        )
    except Exception as exc:
        logger.warning("stats_public: datalake query failed: %s", exc)

    source_label = "PNCP — Portal Nacional de Contratações Públicas"
    period_label = "Últimos 30 dias"
    context_base = "Dados do PNCP processados pelo SmartLic"

    stats: list[dict] = []
    total = len(all_results)

    # ------------------------------------------------------------------
    # 1. Total bids this month
    # ------------------------------------------------------------------
    stats.append({
        "id": "total_bids_month",
        "label": "Editais publicados no último mês",
        "value": float(total),
        "formatted_value": _fmt_int(total),
        "unit": "editais",
        "context": f"Total de contratações publicadas no PNCP nos últimos 30 dias",
        "source": source_label,
        "period": period_label,
    })

    # ------------------------------------------------------------------
    # Value extraction
    # ------------------------------------------------------------------
    values: list[float] = []
    for r in all_results:
        v = r.get("valorTotalEstimado") or r.get("valorEstimado") or r.get("valor_estimado")
        if v and isinstance(v, (int, float)) and float(v) > 0:
            values.append(float(v))

    values.sort()

    # 2. Total estimated value
    total_value = sum(values)
    stats.append({
        "id": "total_value_month",
        "label": "Valor total estimado no último mês",
        "value": round(total_value, 2),
        "formatted_value": _fmt_brl(total_value),
        "unit": "R$",
        "context": "Soma dos valores estimados de todas as contratações publicadas",
        "source": source_label,
        "period": period_label,
    })

    # 3. Average value per bid
    avg_value = total_value / len(values) if values else 0.0
    stats.append({
        "id": "avg_value_month",
        "label": "Valor médio por edital",
        "value": round(avg_value, 2),
        "formatted_value": _fmt_brl(avg_value),
        "unit": "R$",
        "context": "Média dos valores estimados dos editais com valor informado",
        "source": source_label,
        "period": period_label,
    })

    # 4. Median value
    if values:
        mid = len(values) // 2
        median_value = (
            (values[mid - 1] + values[mid]) / 2
            if len(values) % 2 == 0
            else values[mid]
        )
    else:
        median_value = 0.0
    stats.append({
        "id": "median_value_month",
        "label": "Valor mediano por edital",
        "value": round(median_value, 2),
        "formatted_value": _fmt_brl(median_value),
        "unit": "R$",
        "context": "Valor mediano — metade dos editais está abaixo deste valor",
        "source": source_label,
        "period": period_label,
    })

    # 5. % bids with value > R$1M
    count_1m = sum(1 for v in values if v >= 1_000_000)
    pct_1m = (count_1m / total * 100) if total > 0 else 0.0
    stats.append({
        "id": "pct_bids_over_1m",
        "label": "Editais com valor acima de R$ 1 milhão",
        "value": round(pct_1m, 1),
        "formatted_value": _fmt_pct(pct_1m),
        "unit": "%",
        "context": f"{_fmt_int(count_1m)} de {_fmt_int(total)} editais superam R$ 1 milhão",
        "source": source_label,
        "period": period_label,
    })

    # ------------------------------------------------------------------
    # 6. Top UFs by count
    # ------------------------------------------------------------------
    uf_counts: dict[str, int] = {}
    for r in all_results:
        uf = r.get("uf") or r.get("siglaUf") or r.get("ufSigla") or ""
        if isinstance(uf, str) and len(uf) == 2:
            uf_counts[uf.upper()] = uf_counts.get(uf.upper(), 0) + 1

    if uf_counts:
        top_uf, top_uf_count = max(uf_counts.items(), key=lambda x: x[1])
        stats.append({
            "id": "top_uf_count",
            "label": f"UF com mais editais publicados",
            "value": float(top_uf_count),
            "formatted_value": f"{top_uf} — {_fmt_int(top_uf_count)}",
            "unit": "editais",
            "context": f"{top_uf} lidera o ranking de publicações no período",
            "source": source_label,
            "period": period_label,
            "uf": top_uf,
        })

    # 7-11. Top 5 UFs
    top5_ufs = sorted(uf_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for rank, (uf, cnt) in enumerate(top5_ufs, 1):
        pct_uf = (cnt / total * 100) if total > 0 else 0.0
        stats.append({
            "id": f"uf_rank_{rank}_{uf.lower()}",
            "label": f"Editais publicados — {uf}",
            "value": float(cnt),
            "formatted_value": _fmt_int(cnt),
            "unit": "editais",
            "context": f"{_fmt_pct(pct_uf)} do total nacional no período",
            "source": source_label,
            "period": period_label,
            "uf": uf,
        })

    # ------------------------------------------------------------------
    # 12. Top sectors (keyword match against SECTORS)
    # ------------------------------------------------------------------
    sector_counts: dict[str, int] = {}
    for r in all_results:
        objeto = (r.get("objeto") or r.get("descricaoObjeto") or "").lower()
        if not objeto:
            continue
        for sector_id, sector in SECTORS.items():
            for kw in list(sector.keywords)[:30]:  # limit per-bid check
                if kw.lower() in objeto:
                    sector_counts[sector_id] = sector_counts.get(sector_id, 0) + 1
                    break  # count each bid once per sector

    top5_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for rank, (sector_id, cnt) in enumerate(top5_sectors, 1):
        sector_name = SECTORS[sector_id].name if sector_id in SECTORS else sector_id
        pct_s = (cnt / total * 100) if total > 0 else 0.0
        stats.append({
            "id": f"sector_rank_{rank}_{sector_id}",
            "label": f"Editais do setor — {sector_name}",
            "value": float(cnt),
            "formatted_value": _fmt_int(cnt),
            "unit": "editais",
            "context": f"{_fmt_pct(pct_s)} dos editais com keywords deste setor",
            "source": source_label,
            "period": period_label,
            "sector": sector_name,
        })

    # ------------------------------------------------------------------
    # 13. Modalidade distribution
    # ------------------------------------------------------------------
    modal_counts: dict[int, int] = {}
    for r in all_results:
        code = r.get("codigoModalidadeContratacao")
        if isinstance(code, int) and code in _MODALIDADE_NAMES:
            modal_counts[code] = modal_counts.get(code, 0) + 1

    if modal_counts:
        top_modal_code, top_modal_count = max(modal_counts.items(), key=lambda x: x[1])
        top_modal_name = _MODALIDADE_NAMES.get(top_modal_code, f"Código {top_modal_code}")
        pct_modal = (top_modal_count / total * 100) if total > 0 else 0.0
        stats.append({
            "id": "top_modalidade",
            "label": f"Modalidade mais utilizada — {top_modal_name}",
            "value": float(top_modal_count),
            "formatted_value": _fmt_int(top_modal_count),
            "unit": "editais",
            "context": f"{_fmt_pct(pct_modal)} dos editais são via {top_modal_name}",
            "source": source_label,
            "period": period_label,
        })

    return {
        "updated_at": updated_at,
        "total_stats": len(stats),
        "stats": stats,
    }


# ---------------------------------------------------------------------------
# Embed / Badge renderers (S9)
# ---------------------------------------------------------------------------


def _build_embed_html(data: dict) -> HTMLResponse:
    """Return a self-contained HTML snippet for embedding."""
    stats_list = data.get("stats", [])

    total = next((s for s in stats_list if s["id"] == "total_bids_month"), None)
    total_val = next((s for s in stats_list if s["id"] == "total_value_month"), None)
    avg_val = next((s for s in stats_list if s["id"] == "avg_value_month"), None)
    top_uf = next((s for s in stats_list if s["id"] == "top_uf_count"), None)

    total_txt = total["formatted_value"] if total else "—"
    value_txt = total_val["formatted_value"] if total_val else "—"
    avg_txt = avg_val["formatted_value"] if avg_val else "—"
    uf_txt = top_uf["formatted_value"] if top_uf else "—"
    updated = data.get("updated_at", "")[:10]

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
.sl-embed{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:480px;border:1px solid #e5e7eb;border-radius:12px;padding:20px;background:#fafafa}}
.sl-embed h3{{margin:0 0 12px;font-size:14px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em}}
.sl-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.sl-stat{{padding:12px;background:#fff;border-radius:8px;border:1px solid #f3f4f6}}
.sl-stat .val{{font-size:20px;font-weight:700;color:#1e3a5f}}
.sl-stat .lbl{{font-size:12px;color:#6b7280;margin-top:2px}}
.sl-foot{{margin-top:12px;font-size:11px;color:#9ca3af;text-align:center}}
.sl-foot a{{color:#3b82f6;text-decoration:none}}
</style></head><body>
<div class="sl-embed">
<h3>Licitações Públicas — Brasil</h3>
<div class="sl-grid">
<div class="sl-stat"><div class="val">{total_txt}</div><div class="lbl">Editais (30 dias)</div></div>
<div class="sl-stat"><div class="val">{value_txt}</div><div class="lbl">Valor Total</div></div>
<div class="sl-stat"><div class="val">{avg_txt}</div><div class="lbl">Valor Médio</div></div>
<div class="sl-stat"><div class="val">{uf_txt}</div><div class="lbl">UF Líder</div></div>
</div>
<div class="sl-foot">Dados: <a href="https://smartlic.tech/estatisticas" target="_blank" rel="noopener">SmartLic</a> · PNCP · Atualizado {updated}</div>
</div></body></html>"""

    return HTMLResponse(content=html, headers={"Cache-Control": "public, max-age=3600"})


def _build_badge_svg(data: dict) -> Response:
    """Return an SVG badge with total bids count."""
    stats_list = data.get("stats", [])
    total = next((s for s in stats_list if s["id"] == "total_bids_month"), None)
    count_txt = total["formatted_value"] if total else "—"
    updated = data.get("updated_at", "")[:10]

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="280" height="28" role="img"
  aria-label="SmartLic: {count_txt} editais">
  <title>SmartLic: {count_txt} editais</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="280" height="28" rx="5" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="100" height="28" fill="#1e3a5f"/>
    <rect x="100" width="180" height="28" fill="#3b82f6"/>
    <rect width="280" height="28" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,sans-serif" font-size="11">
    <text x="50" y="19" fill="#fff">SmartLic</text>
    <text x="190" y="19" fill="#fff">{count_txt} editais · PNCP · {updated}</text>
  </g>
</svg>"""

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )
