"""SEO Wave 2: Public stats endpoints for /contratos and /fornecedores programmatic pages.

Two public (no auth) endpoints that aggregate contract data from pncp_supplier_contracts
by sector (keyword matching on objeto_contrato) and UF. Cache: InMemory 24h TTL.

Endpoints:
  GET /contratos/{setor}/{uf}/stats  — spending transparency (12.2.1)
  GET /fornecedores/{setor}/{uf}/stats — supplier directory (12.2.2)
"""

import logging
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sectors import SECTORS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["contratos-publicos"])

_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h
_contratos_cache: dict[str, tuple[dict, float]] = {}
_fornecedores_cache: dict[str, tuple[dict, float]] = {}

ALL_UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]


# ---------------------------------------------------------------------------
# Response models — Contratos
# ---------------------------------------------------------------------------

class OrgaoRank(BaseModel):
    nome: str
    cnpj: str
    total_contratos: int
    valor_total: float


class FornecedorRank(BaseModel):
    nome: str
    cnpj: str
    total_contratos: int
    valor_total: float


class MonthlyTrend(BaseModel):
    month: str  # YYYY-MM
    count: int
    value: float


class SampleContract(BaseModel):
    objeto: str
    orgao: str
    fornecedor: str
    valor: Optional[float] = None
    data_assinatura: str


class ContratosStatsResponse(BaseModel):
    sector_id: str
    sector_name: str
    uf: str
    total_contracts: int
    total_value: float
    avg_value: float
    top_orgaos: list[OrgaoRank]
    top_fornecedores: list[FornecedorRank]
    monthly_trend: list[MonthlyTrend]
    sample_contracts: list[SampleContract]
    last_updated: str
    aviso_legal: str


# ---------------------------------------------------------------------------
# Response models — Fornecedores
# ---------------------------------------------------------------------------

class SupplierEntry(BaseModel):
    nome: str
    cnpj: str
    total_contratos: int
    valor_total: float


class FornecedoresStatsResponse(BaseModel):
    sector_id: str
    sector_name: str
    uf: str
    total_suppliers: int
    supplier_ranking: list[SupplierEntry]
    top_orgaos_compradores: list[OrgaoRank]
    last_updated: str
    aviso_legal: str


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _get_cached(cache: dict, key: str) -> Optional[dict]:
    if key not in cache:
        return None
    data, ts = cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del cache[key]
        return None
    return data


def _set_cached(cache: dict, key: str, data: dict) -> None:
    cache[key] = (data, time.time())


# ---------------------------------------------------------------------------
# Shared: fetch + filter contracts by sector keywords + UF
# ---------------------------------------------------------------------------

async def _fetch_sector_contracts(sector_id_clean: str, uf_upper: str) -> list[dict]:
    """Fetch contracts from pncp_supplier_contracts for a given UF,
    then filter by sector keywords on objeto_contrato."""
    sector = SECTORS[sector_id_clean]
    keywords_lower = {kw.lower() for kw in sector.keywords}

    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        resp = (
            sb.table("pncp_supplier_contracts")
            .select(
                "ni_fornecedor,nome_fornecedor,orgao_cnpj,orgao_nome,"
                "valor_global,data_assinatura,objeto_contrato"
            )
            .eq("uf", uf_upper)
            .eq("is_active", True)
            .order("data_assinatura", desc=True)
            .limit(5000)
            .execute()
        )
    except Exception as e:
        logger.error("contratos_publicos DB query failed for %s/%s: %s", sector_id_clean, uf_upper, e)
        raise HTTPException(status_code=502, detail="Erro ao consultar o datalake de contratos")

    rows = resp.data or []

    # Filter by sector keywords (substring match on objeto_contrato)
    matched = []
    for row in rows:
        text = (row.get("objeto_contrato") or "").lower()
        if any(kw in text for kw in keywords_lower):
            matched.append(row)

    return matched


# ---------------------------------------------------------------------------
# Endpoint: Contratos Stats
# ---------------------------------------------------------------------------

@router.get(
    "/contratos/{setor}/{uf}/stats",
    response_model=ContratosStatsResponse,
    summary="Estatisticas de contratos publicos por setor e UF",
)
async def contratos_stats(setor: str, uf: str):
    sector_id_clean = setor.replace("-", "_")
    if sector_id_clean not in SECTORS:
        raise HTTPException(status_code=404, detail=f"Setor '{setor}' nao encontrado")

    uf_upper = uf.upper()
    if uf_upper not in ALL_UFS:
        raise HTTPException(status_code=404, detail=f"UF '{uf}' nao encontrada")

    cache_key = f"contratos:{sector_id_clean}:{uf_upper}"
    cached = _get_cached(_contratos_cache, cache_key)
    if cached:
        return ContratosStatsResponse(**cached)

    sector = SECTORS[sector_id_clean]
    matched = await _fetch_sector_contracts(sector_id_clean, uf_upper)

    # Aggregations
    total_value = 0.0
    orgao_agg: dict[str, dict] = defaultdict(lambda: {"nome": "", "cnpj": "", "contratos": 0, "valor": 0.0})
    forn_agg: dict[str, dict] = defaultdict(lambda: {"nome": "", "cnpj": "", "contratos": 0, "valor": 0.0})
    monthly: Counter = Counter()

    for row in matched:
        valor = _safe_float(row.get("valor_global"))
        total_value += valor

        # Orgao aggregation
        org_cnpj = row.get("orgao_cnpj") or ""
        if org_cnpj:
            orgao_agg[org_cnpj]["cnpj"] = org_cnpj
            orgao_agg[org_cnpj]["nome"] = row.get("orgao_nome") or org_cnpj
            orgao_agg[org_cnpj]["contratos"] += 1
            orgao_agg[org_cnpj]["valor"] += valor

        # Fornecedor aggregation
        ni = row.get("ni_fornecedor") or ""
        if ni:
            forn_agg[ni]["cnpj"] = ni
            forn_agg[ni]["nome"] = row.get("nome_fornecedor") or ni
            forn_agg[ni]["contratos"] += 1
            forn_agg[ni]["valor"] += valor

        # Monthly trend
        data_str = (row.get("data_assinatura") or "")[:7]  # YYYY-MM
        if data_str:
            monthly[data_str] += 1

    total_contracts = len(matched)
    avg_value = round(total_value / total_contracts, 2) if total_contracts else 0.0

    # Top 10 orgaos by value
    top_orgaos = sorted(orgao_agg.values(), key=lambda x: x["valor"], reverse=True)[:10]
    # Top 10 fornecedores by value
    top_fornecedores = sorted(forn_agg.values(), key=lambda x: x["valor"], reverse=True)[:10]

    # Monthly trend (last 12 months)
    now = datetime.now(timezone.utc)
    trend = []
    for i in range(12):
        d = now - timedelta(days=30 * i)
        month_key = d.strftime("%Y-%m")
        cnt = monthly.get(month_key, 0)
        # Sum values for that month
        month_val = sum(
            _safe_float(r.get("valor_global"))
            for r in matched
            if (r.get("data_assinatura") or "")[:7] == month_key
        )
        trend.append({"month": month_key, "count": cnt, "value": round(month_val, 2)})
    trend.reverse()

    # Sample contracts (10 most recent)
    sample_contracts = []
    for row in matched[:10]:
        obj = (row.get("objeto_contrato") or "").strip()
        if len(obj) > 200:
            obj = obj[:197] + "..."
        sample_contracts.append({
            "objeto": obj or "Nao informado",
            "orgao": (row.get("orgao_nome") or "").strip() or "Nao informado",
            "fornecedor": (row.get("nome_fornecedor") or "").strip() or "Nao informado",
            "valor": _safe_float(row.get("valor_global")) or None,
            "data_assinatura": (row.get("data_assinatura") or "")[:10],
        })

    response_data = {
        "sector_id": sector_id_clean,
        "sector_name": sector.name,
        "uf": uf_upper,
        "total_contracts": total_contracts,
        "total_value": round(total_value, 2),
        "avg_value": avg_value,
        "top_orgaos": [
            {"nome": o["nome"], "cnpj": o["cnpj"], "total_contratos": o["contratos"], "valor_total": round(o["valor"], 2)}
            for o in top_orgaos if o["valor"] > 0
        ],
        "top_fornecedores": [
            {"nome": f["nome"], "cnpj": f["cnpj"], "total_contratos": f["contratos"], "valor_total": round(f["valor"], 2)}
            for f in top_fornecedores if f["valor"] > 0
        ],
        "monthly_trend": trend,
        "sample_contracts": sample_contracts,
        "last_updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aviso_legal": (
            "Dados de fontes publicas: Portal Nacional de Contratacoes Publicas (PNCP). "
            "Atualizacao diaria."
        ),
    }

    _set_cached(_contratos_cache, cache_key, response_data)
    return ContratosStatsResponse(**response_data)


# ---------------------------------------------------------------------------
# Endpoint: Fornecedores Stats
# ---------------------------------------------------------------------------

@router.get(
    "/fornecedores/{setor}/{uf}/stats",
    response_model=FornecedoresStatsResponse,
    summary="Ranking de fornecedores do governo por setor e UF",
)
async def fornecedores_stats(setor: str, uf: str):
    sector_id_clean = setor.replace("-", "_")
    if sector_id_clean not in SECTORS:
        raise HTTPException(status_code=404, detail=f"Setor '{setor}' nao encontrado")

    uf_upper = uf.upper()
    if uf_upper not in ALL_UFS:
        raise HTTPException(status_code=404, detail=f"UF '{uf}' nao encontrada")

    cache_key = f"fornecedores:{sector_id_clean}:{uf_upper}"
    cached = _get_cached(_fornecedores_cache, cache_key)
    if cached:
        return FornecedoresStatsResponse(**cached)

    sector = SECTORS[sector_id_clean]
    matched = await _fetch_sector_contracts(sector_id_clean, uf_upper)

    # Aggregate by supplier
    forn_agg: dict[str, dict] = defaultdict(lambda: {"nome": "", "cnpj": "", "contratos": 0, "valor": 0.0})
    orgao_agg: dict[str, dict] = defaultdict(lambda: {"nome": "", "cnpj": "", "contratos": 0, "valor": 0.0})

    for row in matched:
        valor = _safe_float(row.get("valor_global"))

        ni = row.get("ni_fornecedor") or ""
        if ni:
            forn_agg[ni]["cnpj"] = ni
            forn_agg[ni]["nome"] = row.get("nome_fornecedor") or ni
            forn_agg[ni]["contratos"] += 1
            forn_agg[ni]["valor"] += valor

        org_cnpj = row.get("orgao_cnpj") or ""
        if org_cnpj:
            orgao_agg[org_cnpj]["cnpj"] = org_cnpj
            orgao_agg[org_cnpj]["nome"] = row.get("orgao_nome") or org_cnpj
            orgao_agg[org_cnpj]["contratos"] += 1
            orgao_agg[org_cnpj]["valor"] += valor

    # Top 50 suppliers by value
    supplier_ranking = sorted(forn_agg.values(), key=lambda x: x["valor"], reverse=True)[:50]
    # Top 10 buying orgs
    top_orgaos = sorted(orgao_agg.values(), key=lambda x: x["valor"], reverse=True)[:10]

    now = datetime.now(timezone.utc)
    response_data = {
        "sector_id": sector_id_clean,
        "sector_name": sector.name,
        "uf": uf_upper,
        "total_suppliers": len(forn_agg),
        "supplier_ranking": [
            {"nome": s["nome"], "cnpj": s["cnpj"], "total_contratos": s["contratos"], "valor_total": round(s["valor"], 2)}
            for s in supplier_ranking if s["valor"] > 0
        ],
        "top_orgaos_compradores": [
            {"nome": o["nome"], "cnpj": o["cnpj"], "total_contratos": o["contratos"], "valor_total": round(o["valor"], 2)}
            for o in top_orgaos if o["valor"] > 0
        ],
        "last_updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aviso_legal": (
            "Dados de fontes publicas: Portal Nacional de Contratacoes Publicas (PNCP). "
            "Atualizacao diaria."
        ),
    }

    _set_cached(_fornecedores_cache, cache_key, response_data)
    return FornecedoresStatsResponse(**response_data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0
