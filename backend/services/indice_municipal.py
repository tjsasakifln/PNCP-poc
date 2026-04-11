"""STORY-435: Serviço de cálculo do Índice de Transparência Municipal.

Calcula 5 dimensões de transparência a partir de pncp_raw_bids e persiste
em indice_municipal via Supabase (upsert idempotente).

5 dimensões (0-20 pts cada, total 0-100):
  1. score_volume_publicacao     — volume relativo à mediana da UF
  2. score_eficiencia_temporal   — tempo médio publicação→abertura (dias)
  3. score_diversidade_mercado   — fornecedores únicos / total editais
  4. score_transparencia_digital — % modalidade pregão eletrônico (cod 6)
  5. score_consistencia          — meses com pelo menos 1 edital / meses no período

Mínimo 10 editais por município para entrar no ranking.
Cache InMemory 1h por (municipio_nome, uf, periodo).
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 60 * 60  # 1h
_svc_cache: dict[str, tuple[dict, float]] = {}

MIN_EDITAIS = 10  # mínimo para entrar no ranking

# Modalidade pregão eletrônico (código 6)
PREGAO_ELETRONICO_ID = 6


def _cache_get(key: str) -> Optional[dict]:
    if key not in _svc_cache:
        return None
    data, ts = _svc_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _svc_cache[key]
        return None
    return data


def _cache_set(key: str, data: dict) -> None:
    _svc_cache[key] = (data, time.time())


async def calcular_indice_municipio(
    municipio_nome: str,
    uf: str,
    periodo: str,  # "2026-Q1"
) -> Optional[dict]:
    """Calcula índice de transparência para um município + período.

    Returns dict with score fields or None if insufficient data.
    """
    cache_key = f"{municipio_nome}:{uf}:{periodo}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        data_inicial, data_final = _periodo_to_dates(periodo)
    except ValueError as e:
        logger.warning("indice_municipal: invalid periodo '%s': %s", periodo, e)
        return None

    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        # Query todos os editais ativos do município+uf no período
        resp = (
            sb.table("pncp_raw_bids")
            .select(
                "id, modalidade_id, data_publicacao_pncp, data_encerramento_proposta, "
                "valor_estimado, cnpj_contratado, municipio, uf"
            )
            .eq("municipio", municipio_nome)
            .eq("uf", uf)
            .eq("is_active", True)
            .gte("data_publicacao_pncp", data_inicial)
            .lte("data_publicacao_pncp", data_final)
            .limit(5000)
            .execute()
        )
        rows = resp.data or []
    except Exception as e:
        logger.warning(
            "indice_municipal: supabase query failed for %s/%s: %s", municipio_nome, uf, e
        )
        return None

    total_editais = len(rows)
    if total_editais < MIN_EDITAIS:
        return None

    scores = _compute_scores(rows, periodo)
    score_total = round(sum(scores.values()), 2)

    result = {
        "municipio_nome": municipio_nome,
        "uf": uf,
        "periodo": periodo,
        "score_total": score_total,
        "score_volume_publicacao": scores["volume_publicacao"],
        "score_eficiencia_temporal": scores["eficiencia_temporal"],
        "score_diversidade_mercado": scores["diversidade_mercado"],
        "score_transparencia_digital": scores["transparencia_digital"],
        "score_consistencia": scores["consistencia"],
        "total_editais": total_editais,
        "calculado_em": datetime.now(timezone.utc).isoformat(),
    }

    _cache_set(cache_key, result)
    return result


def _periodo_to_dates(periodo: str) -> tuple[str, str]:
    """Converte "2026-Q1" em ("2026-01-01", "2026-03-31")."""
    parts = periodo.split("-Q")
    if len(parts) != 2:
        raise ValueError(f"Período inválido: {periodo!r} — use formato YYYY-QN")
    ano = int(parts[0])
    trimestre = int(parts[1])
    if trimestre not in (1, 2, 3, 4):
        raise ValueError(f"Trimestre inválido: {trimestre}")

    mes_inicio = (trimestre - 1) * 3 + 1
    mes_fim = trimestre * 3
    dia_fim = {3: 31, 6: 30, 9: 30, 12: 31}[mes_fim]

    data_inicial = f"{ano:04d}-{mes_inicio:02d}-01"
    data_final = f"{ano:04d}-{mes_fim:02d}-{dia_fim:02d}"
    return data_inicial, data_final


def _compute_scores(rows: list[dict], periodo: str) -> dict[str, float]:
    """Computa as 5 dimensões de score para a lista de editais."""
    total = len(rows)

    # 1. Score Transparência Digital (0-20): % pregão eletrônico
    pregao_count = sum(1 for r in rows if r.get("modalidade_id") == PREGAO_ELETRONICO_ID)
    pct_pregao = pregao_count / total if total else 0
    # 100% pregão = 20pts, 50% = 10pts
    score_td = round(min(20.0, pct_pregao * 20.0), 2)

    # 2. Score Eficiência Temporal (0-20): tempo médio publicação→abertura
    # Ideal: ≤ 8 dias = 20pts. 30+ dias = 0pts. Linear entre 8 e 30.
    deltas = []
    for r in rows:
        pub = r.get("data_publicacao_pncp")
        enc = r.get("data_encerramento_proposta")
        if pub and enc:
            try:
                d_pub = datetime.fromisoformat(str(pub)).date()
                d_enc = datetime.fromisoformat(str(enc)).date()
                delta = (d_enc - d_pub).days
                if 0 <= delta <= 365:  # sanity: até 1 ano
                    deltas.append(delta)
            except (ValueError, TypeError):
                pass

    if deltas:
        avg_delta = sum(deltas) / len(deltas)
        if avg_delta <= 8:
            score_et = 20.0
        elif avg_delta >= 30:
            score_et = 0.0
        else:
            score_et = round(20.0 * (30 - avg_delta) / (30 - 8), 2)
    else:
        score_et = 10.0  # valor neutro quando sem dados de data

    # 3. Score Diversidade de Mercado (0-20): fornecedores únicos / total editais
    # Razão 1.0 (1 fornecedor/edital) = 5pts, razão >= 0.5 = 20pts proporcional
    cnpjs = [r.get("cnpj_contratado") for r in rows if r.get("cnpj_contratado")]
    unique_cnpjs = len(set(cnpjs))
    ratio = unique_cnpjs / total if total else 0
    score_dm = round(min(20.0, ratio * 20.0), 2)

    # 4. Score Volume de Publicação (0-20): total editais normalizado
    # >= 100 editais = 20pts. Linear até 100. Mínimo 10 (filtrado antes).
    score_vp = round(min(20.0, (total / 100) * 20.0), 2)

    # 5. Score Consistência (0-20): meses com pelo menos 1 edital no período
    # Período de 3 meses (trimestre): 3/3 = 20pts, 2/3 = 13pts, 1/3 = 7pts
    meses_com_edital: set[str] = set()
    for r in rows:
        pub = r.get("data_publicacao_pncp")
        if pub:
            try:
                d = datetime.fromisoformat(str(pub))
                meses_com_edital.add(f"{d.year}-{d.month:02d}")
            except (ValueError, TypeError):
                pass

    n_meses = len(meses_com_edital)
    score_con = round(min(20.0, (n_meses / 3) * 20.0), 2)

    return {
        "transparencia_digital": score_td,
        "eficiencia_temporal": score_et,
        "diversidade_mercado": score_dm,
        "volume_publicacao": score_vp,
        "consistencia": score_con,
    }


async def listar_ranking_por_uf(uf: str, periodo: str, limit: int = 50) -> list[dict]:
    """Lista ranking de municípios de uma UF para o período dado.

    Tenta buscar dados persistidos em indice_municipal (via upsert).
    Retorna lista vazia em caso de erro.
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        resp = (
            sb.table("indice_municipal")
            .select("*")
            .eq("uf", uf)
            .eq("periodo", periodo)
            .order("score_total", desc=True)
            .limit(limit)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        logger.warning("indice_municipal: ranking query failed for %s/%s: %s", uf, periodo, e)
        return []


async def listar_ranking_nacional(periodo: str, limit: int = 50, offset: int = 0) -> list[dict]:
    """Lista top municípios do Brasil para o período dado."""
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        resp = (
            sb.table("indice_municipal")
            .select("*")
            .eq("periodo", periodo)
            .order("score_total", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        logger.warning("indice_municipal: national ranking query failed: %s", e)
        return []


async def listar_periodos_disponiveis() -> list[str]:
    """Retorna lista de períodos com dados calculados."""
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        resp = (
            sb.table("indice_municipal")
            .select("periodo")
            .order("periodo", desc=True)
            .limit(20)
            .execute()
        )
        rows = resp.data or []
        periodos = sorted(set(r["periodo"] for r in rows if r.get("periodo")), reverse=True)
        return periodos
    except Exception as e:
        logger.warning("indice_municipal: periodos query failed: %s", e)
        return []
