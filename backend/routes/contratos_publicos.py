"""SEO Wave 2+: Public stats endpoints for /contratos and /fornecedores programmatic pages.

Public (no auth) endpoints that aggregate contract data from pncp_supplier_contracts
by sector (keyword matching on objeto_contrato) and UF. Cache: InMemory 24h TTL.

Endpoints:
  GET /contratos/{setor}/{uf}/stats       — spending transparency (12.2.1)
  GET /fornecedores/{setor}/{uf}/stats    — supplier directory (12.2.2)
  GET /contratos/orgao/{cnpj}/stats       — org contract profile (12.2.3)
  GET /fornecedores/{cnpj}/profile        — supplier profile page (Sprint 3 Parte 13)
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
_orgao_contratos_cache: dict[str, tuple[dict, float]] = {}
_fornecedor_profile_cache: dict[str, tuple[dict, float]] = {}

_CNPJ_RE = re.compile(r"^\d{14}$")

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
# Response model — Orgao Contratos (Wave 2.3)
# ---------------------------------------------------------------------------

class OrgaoContratosStatsResponse(BaseModel):
    orgao_nome: str
    orgao_cnpj: str
    total_contracts: int
    total_value: float
    avg_value: float
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
# Endpoint: Orgao Contratos Stats (Wave 2.3)
# MUST be defined BEFORE /contratos/{setor}/{uf}/stats to avoid route conflict
# ---------------------------------------------------------------------------

@router.get(
    "/contratos/orgao/{cnpj}/stats",
    response_model=OrgaoContratosStatsResponse,
    summary="Perfil de contratos de um orgao publico (por CNPJ)",
)
async def orgao_contratos_stats(cnpj: str):
    cnpj_clean = cnpj.strip()
    if not _CNPJ_RE.match(cnpj_clean):
        raise HTTPException(status_code=400, detail="CNPJ invalido (esperado 14 digitos)")

    cache_key = f"orgao_contratos:{cnpj_clean}"
    cached = _get_cached(_orgao_contratos_cache, cache_key)
    if cached:
        return OrgaoContratosStatsResponse(**cached)

    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        resp = (
            sb.table("pncp_supplier_contracts")
            .select(
                "ni_fornecedor,nome_fornecedor,orgao_cnpj,orgao_nome,"
                "valor_global,data_assinatura,objeto_contrato"
            )
            .eq("orgao_cnpj", cnpj_clean)
            .eq("is_active", True)
            .order("data_assinatura", desc=True)
            .limit(5000)
            .execute()
        )
    except Exception as e:
        logger.error("orgao_contratos DB query failed for %s: %s", cnpj_clean, e)
        raise HTTPException(status_code=502, detail="Erro ao consultar o datalake de contratos")

    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Nenhum contrato encontrado para este orgao")

    orgao_nome = (rows[0].get("orgao_nome") or cnpj_clean).strip()

    total_value = 0.0
    forn_agg: dict[str, dict] = defaultdict(lambda: {"nome": "", "cnpj": "", "contratos": 0, "valor": 0.0})
    monthly: Counter = Counter()
    monthly_values: dict[str, float] = defaultdict(float)

    for row in rows:
        valor = _safe_float(row.get("valor_global"))
        total_value += valor

        ni = row.get("ni_fornecedor") or ""
        if ni:
            forn_agg[ni]["cnpj"] = ni
            forn_agg[ni]["nome"] = row.get("nome_fornecedor") or ni
            forn_agg[ni]["contratos"] += 1
            forn_agg[ni]["valor"] += valor

        data_str = (row.get("data_assinatura") or "")[:7]
        if data_str:
            monthly[data_str] += 1
            monthly_values[data_str] += valor

    total_contracts = len(rows)
    avg_value = round(total_value / total_contracts, 2) if total_contracts else 0.0

    top_fornecedores = sorted(forn_agg.values(), key=lambda x: x["valor"], reverse=True)[:20]

    now = datetime.now(timezone.utc)
    trend = []
    for i in range(12):
        d = now - timedelta(days=30 * i)
        month_key = d.strftime("%Y-%m")
        trend.append({
            "month": month_key,
            "count": monthly.get(month_key, 0),
            "value": round(monthly_values.get(month_key, 0.0), 2),
        })
    trend.reverse()

    sample_contracts = []
    for row in rows[:10]:
        obj = (row.get("objeto_contrato") or "").strip()
        if len(obj) > 200:
            obj = obj[:197] + "..."
        sample_contracts.append({
            "objeto": obj or "Nao informado",
            "orgao": orgao_nome,
            "fornecedor": (row.get("nome_fornecedor") or "").strip() or "Nao informado",
            "valor": _safe_float(row.get("valor_global")) or None,
            "data_assinatura": (row.get("data_assinatura") or "")[:10],
        })

    response_data = {
        "orgao_nome": orgao_nome,
        "orgao_cnpj": cnpj_clean,
        "total_contracts": total_contracts,
        "total_value": round(total_value, 2),
        "avg_value": avg_value,
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

    _set_cached(_orgao_contratos_cache, cache_key, response_data)
    return OrgaoContratosStatsResponse(**response_data)


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


# ---------------------------------------------------------------------------
# Response models — Fornecedor Profile (Sprint 3 Parte 13)
# ---------------------------------------------------------------------------

class FaqItem(BaseModel):
    question: str
    answer: str


class RecentContract(BaseModel):
    objeto: str
    orgao: str
    valor: Optional[float] = None
    data_assinatura: str
    uf: str


class FornecedorProfileResponse(BaseModel):
    cnpj: str
    razao_social: str
    cnae_descricao: str
    municipio: str
    uf_sede: str
    simples_nacional: bool
    mei: bool
    total_contratos: int
    valor_total: float
    ufs_atuantes: list[str]
    anos_atividade: list[int]
    top_compradores: list[OrgaoRank]
    contratos_recentes: list[RecentContract]
    faq_items: list[FaqItem]
    last_updated: str
    aviso_legal: str


# ---------------------------------------------------------------------------
# Endpoint: Fornecedor Profile (Sprint 3 Parte 13)
# DEVE ser declarado ANTES de /fornecedores/{setor}/{uf}/stats para evitar
# conflito de rota — "cnpj" (14 digitos) colide com "setor" (slug) no FastAPI.
# ---------------------------------------------------------------------------

@router.get(
    "/fornecedores/{cnpj}/profile",
    response_model=FornecedorProfileResponse,
    summary="Perfil completo de um fornecedor do governo (por CNPJ)",
)
async def fornecedor_profile(cnpj: str):
    """Agrega historico de contratos do PNCP + dados cadastrais (BrasilAPI via
    enriched_entities) para a pagina /fornecedores/{cnpj}.

    Publico, sem auth. Cache: 24h TTL em memoria.
    """
    cnpj_clean = cnpj.strip()
    if not _CNPJ_RE.match(cnpj_clean):
        raise HTTPException(status_code=400, detail="CNPJ invalido (esperado 14 digitos numericos)")

    cache_key = f"fornecedor_profile:{cnpj_clean}"
    cached = _get_cached(_fornecedor_profile_cache, cache_key)
    if cached:
        return FornecedorProfileResponse(**cached)

    from supabase_client import get_supabase
    sb = get_supabase()

    # --- Contratos do fornecedor (pncp_supplier_contracts) ---
    try:
        resp = (
            sb.table("pncp_supplier_contracts")
            .select(
                "ni_fornecedor,nome_fornecedor,orgao_cnpj,orgao_nome,"
                "valor_global,data_assinatura,objeto_contrato,uf"
            )
            .eq("ni_fornecedor", cnpj_clean)
            .eq("is_active", True)
            .order("data_assinatura", desc=True)
            .limit(500)
            .execute()
        )
    except Exception as e:
        logger.error("fornecedor_profile contratos query falhou para %s: %s", cnpj_clean, e)
        raise HTTPException(status_code=502, detail="Erro ao consultar o datalake de contratos")

    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado no datalake de contratos")

    # --- Dados cadastrais (enriched_entities — opcional) ---
    enriched_data: dict = {}
    try:
        enrich_resp = (
            sb.table("enriched_entities")
            .select("data")
            .eq("entity_type", "fornecedor")
            .eq("entity_id", cnpj_clean)
            .limit(1)
            .execute()
        )
        if enrich_resp.data:
            enriched_data = enrich_resp.data[0].get("data") or {}
    except Exception as e:
        logger.warning("enriched_entities query falhou para %s (continuando sem enrichment): %s", cnpj_clean, e)

    # --- Agregacoes ---
    total_value = 0.0
    ufs_set: set[str] = set()
    anos_set: set[int] = set()
    orgao_agg: dict[str, dict] = defaultdict(lambda: {"nome": "", "cnpj": "", "contratos": 0, "valor": 0.0})

    razao_social = ""
    for row in rows:
        valor = _safe_float(row.get("valor_global"))
        total_value += valor

        if not razao_social:
            razao_social = (row.get("nome_fornecedor") or "").strip()

        uf = (row.get("uf") or "").strip().upper()
        if uf:
            ufs_set.add(uf)

        data_str = (row.get("data_assinatura") or "")[:4]
        if data_str.isdigit():
            anos_set.add(int(data_str))

        org_cnpj = row.get("orgao_cnpj") or ""
        if org_cnpj:
            orgao_agg[org_cnpj]["cnpj"] = org_cnpj
            orgao_agg[org_cnpj]["nome"] = (row.get("orgao_nome") or org_cnpj).strip()
            orgao_agg[org_cnpj]["contratos"] += 1
            orgao_agg[org_cnpj]["valor"] += valor

    top_compradores = sorted(orgao_agg.values(), key=lambda x: x["valor"], reverse=True)[:10]

    # Contratos recentes (top 20 por data)
    contratos_recentes = []
    for row in rows[:20]:
        obj = (row.get("objeto_contrato") or "").strip()
        if len(obj) > 200:
            obj = obj[:197] + "..."
        contratos_recentes.append({
            "objeto": obj or "Nao informado",
            "orgao": (row.get("orgao_nome") or "").strip() or "Nao informado",
            "valor": _safe_float(row.get("valor_global")) or None,
            "data_assinatura": (row.get("data_assinatura") or "")[:10],
            "uf": (row.get("uf") or "").strip().upper(),
        })

    # Enriquecimento cadastral (prioriza dados da BrasilAPI se disponivel)
    razao_social = enriched_data.get("razao_social") or razao_social or cnpj_clean
    cnae_descricao = enriched_data.get("cnae_fiscal_descricao") or ""
    municipio = enriched_data.get("municipio") or ""
    uf_sede = enriched_data.get("uf") or ""
    simples_nacional = bool(enriched_data.get("simples_nacional", False))
    mei = bool(enriched_data.get("mei", False))

    # FAQ dinamico
    ufs_label = ", ".join(sorted(ufs_set)[:5]) or "todo o Brasil"
    faq_items = [
        {
            "question": f"Quantos contratos o fornecedor {razao_social} tem com o governo?",
            "answer": (
                f"{razao_social} possui {len(rows)} contrato{'s' if len(rows) != 1 else ''} "
                f"registrado{'s' if len(rows) != 1 else ''} no PNCP, "
                f"totalizando {_format_brl(total_value)} em valor global."
            ),
        },
        {
            "question": f"Em quais estados o fornecedor {razao_social} atua?",
            "answer": (
                f"{razao_social} possui contratos publicos nos seguintes estados: {ufs_label}."
                " Os dados sao atualizados diariamente a partir do PNCP."
            ),
        },
        {
            "question": f"Como consultar os contratos de {razao_social} com o governo?",
            "answer": (
                "Todos os contratos listados nesta pagina sao dados publicos do Portal Nacional "
                "de Contratacoes Publicas (PNCP). Para monitorar novos editais deste setor, "
                "o SmartLic oferece alertas automaticos com trial gratuito de 14 dias."
            ),
        },
    ]

    now = datetime.now(timezone.utc)
    response_data = {
        "cnpj": cnpj_clean,
        "razao_social": razao_social,
        "cnae_descricao": cnae_descricao,
        "municipio": municipio,
        "uf_sede": uf_sede,
        "simples_nacional": simples_nacional,
        "mei": mei,
        "total_contratos": len(rows),
        "valor_total": round(total_value, 2),
        "ufs_atuantes": sorted(ufs_set),
        "anos_atividade": sorted(anos_set),
        "top_compradores": [
            {"nome": o["nome"], "cnpj": o["cnpj"], "total_contratos": o["contratos"], "valor_total": round(o["valor"], 2)}
            for o in top_compradores if o["valor"] > 0
        ],
        "contratos_recentes": contratos_recentes,
        "faq_items": faq_items,
        "last_updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aviso_legal": (
            "Dados de fontes publicas: Portal Nacional de Contratacoes Publicas (PNCP). "
            "Atualizacao diaria. CNPJ e dados cadastrais via BrasilAPI."
        ),
    }

    _set_cached(_fornecedor_profile_cache, cache_key, response_data)
    return FornecedorProfileResponse(**response_data)


def _format_brl(value: float) -> str:
    """Formata valor monetario em BRL para exibicao em texto (FAQ, descricoes)."""
    if value >= 1_000_000:
        return f"R$ {value / 1_000_000:.1f} milhoes"
    if value >= 1_000:
        return f"R$ {value / 1_000:.0f} mil"
    return f"R$ {value:.2f}"
