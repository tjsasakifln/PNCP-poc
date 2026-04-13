"""STORY-431: Observatory public endpoint — monthly procurement stats.

Returns aggregated stats from the PNCP datalake for a specific month/year,
enabling the /observatorio monthly reports (data journalism / linkbait).

Public (no auth). Cache: InMemory 24h TTL per (mes, ano).
"""

import csv
import io
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["observatorio"])

_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h
_obs_cache: dict[str, tuple[dict, float]] = {}

MONTH_NAMES_PT = {
    1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
    5: "maio", 6: "junho", 7: "julho", 8: "agosto",
    9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro",
}

MODALIDADE_NAMES: dict[int, str] = {
    4: "Concorrência Eletrônica",
    5: "Concorrência Presencial",
    6: "Pregão Eletrônico",
    7: "Pregão Presencial",
    8: "Dispensa de Licitação",
    12: "Credenciamento",
}

UF_NAMES: dict[str, str] = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class UfCount(BaseModel):
    uf: str
    uf_name: str
    total: int
    pct: float


class ModalidadeCount(BaseModel):
    modalidade_id: int
    modalidade_name: str
    total: int
    pct: float


class SetorHighlight(BaseModel):
    setor_id: str
    setor_name: str
    total_atual: int
    total_anterior: int
    variacao_pct: float


class MonthlyTrend(BaseModel):
    semana: str
    total: int


class RelatorioMensal(BaseModel):
    mes: int
    ano: int
    mes_nome: str
    periodo: str
    total_editais: int
    valor_total: float
    valor_medio: float
    top_ufs: list[UfCount]
    modalidades: list[ModalidadeCount]
    tendencia_semanal: list[MonthlyTrend]
    setores_em_alta: list[SetorHighlight]
    gerado_em: str
    fonte: str
    license: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/observatorio/relatorio/{mes}/{ano}",
    response_model=RelatorioMensal,
    summary="Relatório mensal do Observatório de Licitações (público)",
)
async def get_relatorio_mensal(
    mes: int = Path(..., ge=1, le=12, description="Mês (1-12)"),
    ano: int = Path(..., ge=2024, le=2030, description="Ano"),
    response: Response = None,
):
    # STORY-431 AC5: CORS wildcard para permitir embed em domínios externos
    if response is not None:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"

    cache_key = f"{mes}:{ano}"
    cached = _get_cached(cache_key)
    if cached:
        return RelatorioMensal(**cached)

    data = await _generate_relatorio(mes, ano)
    _set_cached(cache_key, data)
    return RelatorioMensal(**data)


@router.get(
    "/observatorio/relatorio/{mes}/{ano}/csv",
    summary="Download CSV do relatório mensal (público)",
)
async def get_relatorio_csv(
    mes: int = Path(..., ge=1, le=12),
    ano: int = Path(..., ge=2024, le=2030),
    response: Response = None,
):
    cache_key = f"{mes}:{ano}"
    cached = _get_cached(cache_key)
    if not cached:
        cached = await _generate_relatorio(mes, ano)
        _set_cached(cache_key, cached)

    relatorio = RelatorioMensal(**cached)
    csv_content = _build_csv(relatorio)
    filename = f"smartlic-raio-x-{MONTH_NAMES_PT[mes].replace('ç', 'c').replace('ã', 'a')}-{ano}.csv"

    # STORY-431 AC5: CORS wildcard para embed/download em domínios externos
    cors_headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
    }
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8",
        headers=cors_headers,
    )


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _get_cached(key: str) -> Optional[dict]:
    if key not in _obs_cache:
        return None
    data, ts = _obs_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _obs_cache[key]
        return None
    return data


def _set_cached(key: str, data: dict) -> None:
    _obs_cache[key] = (data, time.time())


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def _query_historical_sync(data_inicial: str, data_final: str) -> list[dict]:
    """Direct Supabase query bypassing is_active filter — for historical months.

    Used when the requested month is >30 days ago and data may be soft-deleted
    (is_active=False) by the purge job. Queries pncp_raw_bids without the RPC
    search_datalake which filters is_active=true.
    """
    from supabase_client import get_supabase
    sb = get_supabase()
    resp = (
        sb.table("pncp_raw_bids")
        .select("pncp_id, objeto_compra, valor_total_estimado, modalidade_id, uf, data_publicacao")
        .gte("data_publicacao", data_inicial)
        .lte("data_publicacao", data_final + "T23:59:59")
        .limit(5000)
        .execute()
    )
    rows = resp.data or []
    # Normalize to keys expected by _generate_relatorio processing
    normalized: list[dict] = []
    for r in rows:
        dp = r.get("data_publicacao") or ""
        normalized.append({
            "uf": (r.get("uf") or "").upper(),
            "modalidade_id": r.get("modalidade_id") or 0,
            "valor_estimado": float(r.get("valor_total_estimado") or 0),
            "data_publicacao": str(dp)[:10] if dp else "",
            "titulo": r.get("objeto_compra") or "",
        })
    return normalized


async def _generate_relatorio(mes: int, ano: int) -> dict:
    from datalake_query import query_datalake
    from unified_schemas.unified import VALID_UFS
    import asyncio
    import calendar
    from datetime import date

    # Date range for the requested month
    _, last_day = calendar.monthrange(ano, mes)
    data_inicial = f"{ano:04d}-{mes:02d}-01"
    data_final = f"{ano:04d}-{mes:02d}-{last_day:02d}"

    # Date range for previous month (for growth comparison)
    prev_mes = mes - 1 if mes > 1 else 12
    prev_ano = ano if mes > 1 else ano - 1
    _, prev_last = calendar.monthrange(prev_ano, prev_mes)
    prev_inicial = f"{prev_ano:04d}-{prev_mes:02d}-01"
    prev_final = f"{prev_ano:04d}-{prev_mes:02d}-{prev_last:02d}"

    # Detect if month is historical (>30 days ago — data may be soft-deleted)
    today = date.today()
    is_historical = (today - date(ano, mes, 1)).days > 30

    # Query current month
    results: list[dict] = []
    prev_results: list[dict] = []

    if is_historical:
        try:
            results = await asyncio.to_thread(
                _query_historical_sync, data_inicial, data_final
            )
            logger.info(
                "observatorio: historical query for %d/%d returned %d rows",
                mes, ano, len(results),
            )
        except Exception as e:
            logger.warning("observatorio: historical query failed for %d/%d: %s", mes, ano, e)
    else:
        try:
            results = await query_datalake(
                ufs=list(VALID_UFS),
                data_inicial=data_inicial,
                data_final=data_final,
                limit=5000,
            )
        except Exception as e:
            logger.warning("observatorio: query failed for %d/%d: %s", mes, ano, e)

    # Previous month always via datalake (or historical if also old)
    prev_is_historical = (today - date(prev_ano, prev_mes, 1)).days > 30
    if prev_is_historical:
        try:
            prev_results = await asyncio.to_thread(
                _query_historical_sync, prev_inicial, prev_final
            )
        except Exception as e:
            logger.warning("observatorio: historical prev month query failed: %s", e)
    else:
        try:
            prev_results = await query_datalake(
                ufs=list(VALID_UFS),
                data_inicial=prev_inicial,
                data_final=prev_final,
                limit=5000,
            )
        except Exception as e:
            logger.warning("observatorio: prev month query failed: %s", e)

    total = len(results)
    mes_nome = MONTH_NAMES_PT[mes]
    periodo = f"Editais publicados de 1 a {last_day} de {mes_nome} de {ano}"

    # Extract values
    values: list[float] = []
    for r in results:
        v = r.get("valorTotalEstimado") or r.get("valorEstimado") or r.get("valor_estimado")
        if v and isinstance(v, (int, float)) and float(v) > 0:
            values.append(float(v))

    # Exclude P95+ outliers for average
    values_sorted = sorted(values)
    if values_sorted:
        p95_idx = int(len(values_sorted) * 0.95)
        values_filtered = values_sorted[:p95_idx] if p95_idx > 0 else values_sorted
    else:
        values_filtered = []

    valor_total = sum(values_sorted)
    valor_medio = sum(values_filtered) / len(values_filtered) if values_filtered else 0.0

    # Top UFs
    uf_counts: dict[str, int] = defaultdict(int)
    for r in results:
        uf = r.get("uf", "").upper()
        if uf:
            uf_counts[uf] += 1

    top_ufs_raw = sorted(uf_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_ufs = [
        UfCount(
            uf=uf,
            uf_name=UF_NAMES.get(uf, uf),
            total=count,
            pct=round(count / total * 100, 1) if total > 0 else 0.0,
        )
        for uf, count in top_ufs_raw
    ]

    # Modalidade distribution
    modalidade_counts: dict[int, int] = defaultdict(int)
    for r in results:
        mod_id = r.get("codigoModalidadeContratacao") or r.get("modalidade_id") or 0
        if mod_id:
            try:
                modalidade_counts[int(mod_id)] += 1
            except (ValueError, TypeError):
                pass

    modalidades = [
        ModalidadeCount(
            modalidade_id=mod_id,
            modalidade_name=MODALIDADE_NAMES.get(mod_id, f"Modalidade {mod_id}"),
            total=count,
            pct=round(count / total * 100, 1) if total > 0 else 0.0,
        )
        for mod_id, count in sorted(modalidade_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # Weekly trend
    week_counts: dict[str, int] = defaultdict(int)
    for r in results:
        pub_date = r.get("dataPublicacaoFormatted") or r.get("data_publicacao", "")
        if pub_date and len(pub_date) >= 10:
            try:
                d = datetime.strptime(pub_date[:10], "%Y-%m-%d")
                week_label = f"Semana {((d.day - 1) // 7) + 1}"
                week_counts[week_label] += 1
            except ValueError:
                pass

    tendencia = [
        MonthlyTrend(semana=week, total=count)
        for week, count in sorted(week_counts.items())
    ]

    # Sectors in high growth
    setores_em_alta = await _compute_setores_em_alta(results, prev_results)

    return {
        "mes": mes,
        "ano": ano,
        "mes_nome": mes_nome,
        "periodo": periodo,
        "total_editais": total,
        "valor_total": round(valor_total, 2),
        "valor_medio": round(valor_medio, 2),
        "top_ufs": [u.model_dump() for u in top_ufs],
        "modalidades": [m.model_dump() for m in modalidades],
        "tendencia_semanal": [t.model_dump() for t in tendencia],
        "setores_em_alta": [s.model_dump() for s in setores_em_alta],
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "fonte": "SmartLic Observatório — dados PNCP (Portal Nacional de Contratações Públicas)",
        "license": "Creative Commons BY 4.0 — https://creativecommons.org/licenses/by/4.0/",
    }


async def _compute_setores_em_alta(
    results: list[dict], prev_results: list[dict]
) -> list[SetorHighlight]:
    """Compare sector volumes: current vs previous month. Returns top 5 by growth."""
    try:
        from sectors import SECTORS
    except ImportError:
        return []

    def count_by_sector(records: list[dict]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for setor_id, sector in SECTORS.items():
            keywords_lower = {kw.lower() for kw in sector.keywords}
            count = 0
            for r in records:
                title = (r.get("objetoCompra") or r.get("titulo") or "").lower()
                if any(kw in title for kw in keywords_lower):
                    count += 1
            if count > 0:
                counts[setor_id] = count
        return counts

    current_counts = count_by_sector(results)
    prev_counts = count_by_sector(prev_results)

    highlights: list[SetorHighlight] = []
    for setor_id, sector in SECTORS.items():
        atual = current_counts.get(setor_id, 0)
        anterior = prev_counts.get(setor_id, 0)
        if anterior > 0:
            variacao = round((atual - anterior) / anterior * 100, 1)
        elif atual > 0:
            variacao = 100.0
        else:
            continue

        if variacao > 20 and atual > 10:
            highlights.append(SetorHighlight(
                setor_id=setor_id,
                setor_name=sector.name,
                total_atual=atual,
                total_anterior=anterior,
                variacao_pct=variacao,
            ))

    return sorted(highlights, key=lambda h: h.variacao_pct, reverse=True)[:5]


def _build_csv(relatorio: RelatorioMensal) -> str:
    output = io.StringIO()

    # Header comment with source attribution
    output.write(
        f"# Fonte: SmartLic Observatório (smartlic.tech/observatorio). "
        f"Dados PNCP processados por IA.\n"
        f"# Período: {relatorio.periodo}\n"
        f"# Gerado em: {relatorio.gerado_em}\n"
        f"# Licença: Creative Commons BY 4.0\n\n"
    )

    writer = csv.writer(output)

    # Section 1: Summary
    writer.writerow(["# RESUMO"])
    writer.writerow(["Total de editais", relatorio.total_editais])
    writer.writerow(["Valor total estimado (R$)", f"{relatorio.valor_total:.2f}"])
    writer.writerow(["Valor médio por edital (R$)", f"{relatorio.valor_medio:.2f}"])
    writer.writerow([])

    # Section 2: Top UFs
    writer.writerow(["# TOP UFS"])
    writer.writerow(["UF", "Nome", "Total de editais", "% do total"])
    for uf in relatorio.top_ufs:
        writer.writerow([uf.uf, uf.uf_name, uf.total, f"{uf.pct:.1f}%"])
    writer.writerow([])

    # Section 3: Modalidades
    writer.writerow(["# DISTRIBUIÇÃO POR MODALIDADE"])
    writer.writerow(["Modalidade", "Total", "% do total"])
    for m in relatorio.modalidades:
        writer.writerow([m.modalidade_name, m.total, f"{m.pct:.1f}%"])
    writer.writerow([])

    # Section 4: Sectors in growth
    if relatorio.setores_em_alta:
        writer.writerow(["# SETORES EM ALTA"])
        writer.writerow(["Setor", "Total (mês atual)", "Total (mês anterior)", "Variação (%)"])
        for s in relatorio.setores_em_alta:
            writer.writerow([s.setor_name, s.total_atual, s.total_anterior, f"{s.variacao_pct:+.1f}%"])

    return output.getvalue()
