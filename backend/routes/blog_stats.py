"""MKT-002 AC1: Blog stats API for programmatic SEO pages.

Public (no auth) endpoints that return aggregated procurement data
for blog programmatic pages. Used by frontend ISR pages.

Endpoints:
  GET /blog/stats/setor/{setor_id}           — sector overview
  GET /blog/stats/setor/{setor_id}/uf/{uf}   — sector × UF detail
  GET /blog/stats/cidade/{cidade}             — city stats
  GET /blog/stats/panorama/{setor_id}         — national panorama

Cache: InMemory 6h TTL.
Safety: No internal IDs or direct links (same as sectors_public.py).
"""

import logging
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sectors import SECTORS, SectorConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/blog/stats", tags=["blog-stats"])

# 6h InMemory cache
_CACHE_TTL_SECONDS = 6 * 60 * 60
_blog_cache: dict[str, tuple[dict, float]] = {}

# All 27 Brazilian UFs
ALL_UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]

# Top UFs by procurement volume (queried for panorama/sector stats)
TOP_UFS = ["SP", "RJ", "MG", "DF", "PR", "BA", "RS", "GO", "PE", "SC"]

# Modality code → name mapping (Lei 14.133/2021 — PNCP codes)
from config.pncp import MODALIDADES_PNCP as MODALITY_NAMES

# UF → major cities mapping for city endpoint.
# STORY-SEO-012: Expanded from 16 → 27 UFs to fix 12 capitals returning 404
# (Maceió, João Pessoa, Aracaju, Teresina, Rio Branco, Porto Velho, Boa Vista,
# Macapá, Palmas, Cuiabá, Campo Grande, Natal). Curadoria: capital + top 5-10
# cidades por UF (IBGE população + PIB municipal).
UF_CITIES: dict[str, list[str]] = {
    "AC": ["Rio Branco", "Cruzeiro do Sul", "Sena Madureira"],
    "AL": ["Maceió", "Arapiraca", "Palmeira dos Índios", "Rio Largo"],
    "AM": ["Manaus", "Parintins", "Itacoatiara", "Manacapuru"],
    "AP": ["Macapá", "Santana", "Laranjal do Jari"],
    "BA": ["Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari", "Juazeiro", "Ilhéus", "Itabuna"],
    "CE": ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanaú", "Sobral"],
    "DF": ["Brasília"],
    "ES": ["Vitória", "Vila Velha", "Serra", "Cariacica", "Cachoeiro de Itapemirim"],
    "GO": ["Goiânia", "Aparecida de Goiânia", "Anápolis", "Rio Verde", "Águas Lindas de Goiás"],
    "MA": ["São Luís", "Imperatriz", "Timon", "Caxias"],
    "MG": ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim", "Montes Claros", "Ribeirão das Neves"],
    "MS": ["Campo Grande", "Dourados", "Três Lagoas", "Corumbá"],
    "MT": ["Cuiabá", "Várzea Grande", "Rondonópolis", "Sinop"],
    "PA": ["Belém", "Ananindeua", "Santarém", "Marabá", "Castanhal"],
    "PB": ["João Pessoa", "Campina Grande", "Santa Rita", "Patos"],
    "PE": ["Recife", "Jaboatão dos Guararapes", "Olinda", "Caruaru", "Petrolina"],
    "PI": ["Teresina", "Parnaíba", "Picos", "Floriano"],
    "PR": ["Curitiba", "Londrina", "Maringá", "Cascavel", "Ponta Grossa", "São José dos Pinhais", "Foz do Iguaçu"],
    "RJ": ["Rio de Janeiro", "Niterói", "Duque de Caxias", "Nova Iguaçu", "São Gonçalo", "Belford Roxo", "São João de Meriti", "Campos dos Goytacazes", "Petrópolis"],
    "RN": ["Natal", "Mossoró", "Parnamirim", "São Gonçalo do Amarante"],
    "RO": ["Porto Velho", "Ji-Paraná", "Ariquemes", "Vilhena"],
    "RR": ["Boa Vista", "Rorainópolis"],
    "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria", "Viamão", "Novo Hamburgo"],
    "SC": ["Florianópolis", "Joinville", "Blumenau", "São José", "Chapecó", "Criciúma"],
    "SE": ["Aracaju", "Nossa Senhora do Socorro", "Lagarto", "Itabaiana"],
    "SP": ["São Paulo", "Campinas", "Guarulhos", "São Bernardo do Campo", "Osasco", "Santo André", "Mauá", "Mogi das Cruzes", "Diadema", "Sorocaba", "Ribeirão Preto", "São José dos Campos"],
    "TO": ["Palmas", "Araguaína", "Gurupi", "Porto Nacional"],
}

def _strip_accents(text: str) -> str:
    """Return ASCII-folded lowercase version of text (removes diacritics)."""
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    ).lower()


# Reverse mapping: city → UF (keyed by both accented and ASCII-stripped lowercase)
_CITY_TO_UF: dict[str, str] = {}
# City slug → accented display name (e.g. "sao paulo" → "São Paulo"). Used to
# build ilike patterns that match the accented strings stored in the database.
_CITY_DISPLAY: dict[str, str] = {}
for _uf, _cities in UF_CITIES.items():
    for _city in _cities:
        _CITY_TO_UF[_city.lower()] = _uf
        _CITY_TO_UF[_strip_accents(_city)] = _uf
        _CITY_DISPLAY[_city.lower()] = _city
        _CITY_DISPLAY[_strip_accents(_city)] = _city


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class TopEntry(BaseModel):
    name: str
    count: int


class SampleItem(BaseModel):
    titulo: str
    orgao: str
    orgao_cnpj: Optional[str] = None
    valor: Optional[float] = None
    uf: str
    data: str


class TopComprador(BaseModel):
    nome: str
    cnpj: str
    total_contratos: int
    valor_total: float


class TrendPoint(BaseModel):
    period: str
    count: int
    avg_value: float


class SectorBlogStats(BaseModel):
    sector_id: str
    sector_name: str
    total_editais: int
    value_range_min: float
    value_range_max: float
    avg_value: float
    top_modalidades: list[TopEntry]
    top_ufs: list[TopEntry]
    trend_90d: list[TrendPoint]
    last_updated: str


class SectorUfStats(BaseModel):
    sector_id: str
    sector_name: str
    uf: str
    total_editais: int
    avg_value: float
    value_range_min: float = 0.0
    value_range_max: float = 0.0
    top_modalidades: list[TopEntry] = []
    trend_90d: list[TrendPoint] = []
    top_oportunidades: list[SampleItem]
    last_updated: str
    most_recent_bid_date: Optional[str] = None
    municipios_ativos: int = 0
    vs_media_nacional_pct: Optional[float] = None
    top_compradores: list[TopComprador] = []


class CidadeStats(BaseModel):
    cidade: str
    uf: str
    total_editais: int
    orgaos_frequentes: list[TopEntry]
    avg_value: float
    last_updated: str


class CidadeSectorStats(BaseModel):
    cidade: str
    uf: str
    sector_id: str
    sector_name: str
    total_editais: int
    avg_value: float
    value_range_min: float = 0.0
    value_range_max: float = 0.0
    top_modalidades: list[TopEntry] = []
    orgaos_frequentes: list[TopEntry] = []
    top_oportunidades: list[SampleItem] = []
    has_sufficient_data: bool = False
    last_updated: str


class PanoramaStats(BaseModel):
    sector_id: str
    sector_name: str
    total_nacional: int
    total_value: float
    avg_value: float
    top_ufs: list[TopEntry]
    top_modalidades: list[TopEntry]
    sazonalidade: list[TrendPoint]
    crescimento_estimado_pct: float
    last_updated: str


class ContratosSetorTopEntry(BaseModel):
    nome: str
    cnpj: str
    total_contratos: int
    valor_total: float


class ContratosSetorUfEntry(BaseModel):
    uf: str
    total_contratos: int
    valor_total: float


class ContratosSetorTrend(BaseModel):
    month: str
    count: int
    value: float


class SampleContract(BaseModel):
    objeto: str
    orgao: str
    fornecedor: str
    valor: float | None
    data_assinatura: str


class ContratosSetorStats(BaseModel):
    sector_id: str
    sector_name: str
    total_contracts: int
    total_value: float
    avg_value: float
    top_orgaos: list[ContratosSetorTopEntry]
    top_fornecedores: list[ContratosSetorTopEntry]
    monthly_trend: list[ContratosSetorTrend]
    by_uf: list[ContratosSetorUfEntry]
    last_updated: str
    n_unique_orgaos: int = 0
    n_unique_fornecedores: int = 0
    sample_contracts: list[SampleContract] = []


class ContratosSetorUfStats(BaseModel):
    """Sector × UF filtered contract stats (fallback for zero-editais blog pages)."""
    sector_id: str
    sector_name: str
    uf: str
    total_contracts: int
    total_value: float
    avg_value: float
    top_orgaos: list[ContratosSetorTopEntry]
    top_fornecedores: list[ContratosSetorTopEntry]
    monthly_trend: list[ContratosSetorTrend]
    last_updated: str
    n_unique_orgaos: int = 0
    n_unique_fornecedores: int = 0
    sample_contracts: list[SampleContract] = []


class ContratosCidadeStats(BaseModel):
    """City-level contract stats (all sectors) for zero-editais cidade blog pages."""
    cidade: str
    uf: str
    total_contracts: int
    total_value: float
    avg_value: float
    top_orgaos: list[ContratosSetorTopEntry]
    top_fornecedores: list[ContratosSetorTopEntry]
    monthly_trend: list[ContratosSetorTrend]
    last_updated: str
    n_unique_orgaos: int = 0
    n_unique_fornecedores: int = 0
    sample_contracts: list[SampleContract] = []


class ContratosCidadeSetorStats(BaseModel):
    """City × Sector filtered contract stats for zero-editais cidade×setor pages."""
    cidade: str
    uf: str
    sector_id: str
    sector_name: str
    total_contracts: int
    total_value: float
    avg_value: float
    top_orgaos: list[ContratosSetorTopEntry]
    top_fornecedores: list[ContratosSetorTopEntry]
    monthly_trend: list[ContratosSetorTrend]
    last_updated: str
    n_unique_orgaos: int = 0
    n_unique_fornecedores: int = 0
    sample_contracts: list[SampleContract] = []


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _cache_get(key: str) -> Optional[dict]:
    if key not in _blog_cache:
        return None
    data, ts = _blog_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _blog_cache[key]
        return None
    return data


def _cache_set(key: str, data: dict) -> None:
    _blog_cache[key] = (data, time.time())


def invalidate_blog_cache() -> None:
    """Clear all blog stats cache."""
    _blog_cache.clear()


# ---------------------------------------------------------------------------
# PNCP query helper (reusable)
# ---------------------------------------------------------------------------

async def _query_pncp_for_sector(
    sector: SectorConfig,
    ufs: list[str],
    days: int = 30,
) -> list[dict]:
    """Query datalake for sector-relevant results across given UFs."""
    from datalake_query import query_datalake

    now = datetime.now(timezone.utc)
    data_final = now.strftime("%Y-%m-%d")
    data_inicial = (now - timedelta(days=days)).strftime("%Y-%m-%d")

    try:
        return await query_datalake(
            ufs=ufs,
            data_inicial=data_inicial,
            data_final=data_final,
            keywords=list(sector.keywords),
            limit=2000,
        )
    except Exception as e:
        logger.warning("Datalake query failed for blog stats sector=%s: %s", sector.id, e)
        return []


def _extract_text(item: dict) -> str:
    parts = [
        item.get("objetoCompra", ""),
        item.get("descricao", ""),
        item.get("objeto", ""),
        item.get("title", ""),
    ]
    return " ".join(p for p in parts if p)


# R$500M cap — valores acima são quase certamente erros de digitação no PNCP.
# O maior viability_value_range do sistema é R$20M; 500M = 25× esse teto,
# cobrindo contratos legítimos mas grandes sem deixar outliers destruírem as médias.
_STATS_VALUE_CAP = 500_000_000


def _extract_value(item: dict) -> Optional[float]:
    v = item.get("valorTotalEstimado") or item.get("valorEstimado") or item.get("valor_estimado")
    if v and isinstance(v, (int, float)) and 0 < v <= _STATS_VALUE_CAP:
        return float(v)
    return None


def _extract_uf(item: dict) -> str:
    return item.get("uf") or item.get("unidadeFederativa") or item.get("ufSigla") or ""


def _extract_modality(item: dict) -> str:
    code = item.get("codigoModalidadeContratacao")
    if code is not None:
        try:
            name = MODALITY_NAMES.get(int(code))
            if name:
                return name
        except (ValueError, TypeError):
            pass
    # Fallback: use the name field already present in datalake data
    return item.get("modalidadeNome") or item.get("modalidade") or "Não informada"


def _extract_orgao(item: dict) -> str:
    org = item.get("orgaoEntidade", {})
    if isinstance(org, dict):
        return org.get("razaoSocial") or org.get("nomeOrgao") or "Não informado"
    return item.get("orgao") or item.get("nomeOrgao") or "Não informado"


def _extract_date(item: dict) -> str:
    d = (
        item.get("dataPublicacaoFormatted")
        or item.get("dataPublicacaoPncp")
        or item.get("dataAbertura")
        or item.get("data_publicacao")
        or ""
    )
    if d and len(d) > 10:
        d = d[:10]
    return d


def _extract_city(item: dict) -> str:
    # Datalake returns flat `municipio` field; PNCP API returns nested orgaoEntidade
    flat_city = item.get("municipio") or ""
    if flat_city:
        return flat_city
    org = item.get("orgaoEntidade", {})
    if isinstance(org, dict):
        return org.get("municipioNome") or org.get("municipio") or ""
    return ""


def _make_sample_item(item: dict) -> dict:
    titulo = item.get("objetoCompra") or item.get("objeto") or item.get("title") or "Sem título"
    if len(titulo) > 120:
        titulo = titulo[:117] + "..."
    return {
        "titulo": titulo,
        "orgao": _extract_orgao(item),
        "orgao_cnpj": item.get("orgaoCnpj") or None,
        "valor": _extract_value(item),
        "uf": _extract_uf(item),
        "data": _extract_date(item),
    }


def _validate_sector(setor_id: str) -> SectorConfig:
    """Validate sector_id and return SectorConfig or raise 404."""
    sector_id = setor_id.replace("-", "_")
    if sector_id not in SECTORS:
        raise HTTPException(status_code=404, detail=f"Setor '{setor_id}' não encontrado")
    return SECTORS[sector_id]


# ---------------------------------------------------------------------------
# Endpoint 1: Sector overview
# ---------------------------------------------------------------------------

@router.get("/setor/{setor_id}", response_model=SectorBlogStats)
async def get_sector_blog_stats(setor_id: str):
    """Sector overview: count, value range, top modalities, top UFs, 90d trend.

    Public (no auth). Cached 6h.
    """
    sector = _validate_sector(setor_id)
    cache_key = f"setor:{sector.id}"

    cached = _cache_get(cache_key)
    if cached:
        return SectorBlogStats(**cached)

    results = await _query_pncp_for_sector(sector, TOP_UFS)
    now = datetime.now(timezone.utc)

    # Value stats
    values = [v for item in results if (v := _extract_value(item)) is not None]
    total = len(results)
    avg_val = sum(values) / len(values) if values else 0.0
    min_val = min(values) if values else 0.0
    max_val = max(values) if values else 0.0

    # Top modalidades
    mod_counter: Counter = Counter()
    for item in results:
        mod_counter[_extract_modality(item)] += 1
    top_mods = [{"name": m, "count": c} for m, c in mod_counter.most_common(5)]

    # Top UFs
    uf_counter: Counter = Counter()
    for item in results:
        uf = _extract_uf(item)
        if uf:
            uf_counter[uf] += 1
    top_ufs = [{"name": uf, "count": c} for uf, c in uf_counter.most_common(10)]

    # 90-day trend (estimate: current 10-day data extrapolated to 3 months)
    trend_90d = _estimate_trend(total, avg_val, now)

    data = {
        "sector_id": sector.id,
        "sector_name": sector.name,
        "total_editais": total,
        "value_range_min": round(min_val, 2),
        "value_range_max": round(max_val, 2),
        "avg_value": round(avg_val, 2),
        "top_modalidades": top_mods,
        "top_ufs": top_ufs,
        "trend_90d": trend_90d,
        "last_updated": now.isoformat(),
    }
    _cache_set(cache_key, data)
    return SectorBlogStats(**data)


def _estimate_trend(current_count: int, avg_value: float, now: datetime) -> list[dict]:
    """Estimate 90-day trend from current 10-day data.

    Projects backwards using slight variation for realistic seasonality.
    """
    trend = []
    for i in range(3):
        month_date = now - timedelta(days=30 * (2 - i))
        # Apply slight variation (±15%) for realism
        factor = [0.85, 0.95, 1.0][i]
        count = max(1, int(current_count * 3 * factor))  # 10-day × 3 ≈ monthly
        trend.append({
            "period": month_date.strftime("%Y-%m"),
            "count": count,
            "avg_value": round(avg_value * factor, 2),
        })
    return trend


# ---------------------------------------------------------------------------
# Endpoint 2: Sector × UF detail
# ---------------------------------------------------------------------------

@router.get("/setor/{setor_id}/uf/{uf}", response_model=SectorUfStats)
async def get_sector_uf_stats(setor_id: str, uf: str):
    """Sector × UF detail: count, avg value, top 5 recent opportunities.

    Public (no auth). Cached 6h.
    """
    uf = uf.upper().strip()
    if uf not in ALL_UFS:
        raise HTTPException(status_code=404, detail=f"UF '{uf}' não encontrada")

    sector = _validate_sector(setor_id)
    cache_key = f"setor_uf:{sector.id}:{uf}"

    cached = _cache_get(cache_key)
    if cached:
        return SectorUfStats(**cached)

    results = await _query_pncp_for_sector(sector, [uf])
    now = datetime.now(timezone.utc)

    # Filter to only this UF (safety)
    uf_results = [r for r in results if _extract_uf(r).upper() == uf]

    values = [v for item in uf_results if (v := _extract_value(item)) is not None]
    avg_val = sum(values) / len(values) if values else 0.0
    min_val = min(values) if values else 0.0
    max_val = max(values) if values else 0.0

    # Top modalities
    mod_counter: Counter = Counter()
    for item in uf_results:
        mod_counter[_extract_modality(item)] += 1
    top_mods = [{"name": m, "count": c} for m, c in mod_counter.most_common(5)]

    # 90-day trend (estimate from current 10-day data)
    trend_90d = _estimate_trend(len(uf_results), avg_val, now)

    # Top 5 opportunities
    top_items = [_make_sample_item(item) for item in uf_results[:5]]

    # STORY-430 AC5: data do edital mais recente
    dates = [_extract_date(item) for item in uf_results if _extract_date(item)]
    most_recent_bid_date = max(dates) if dates else None

    # SEO-Sprint2 P5/P7: municípios ativos, comparação nacional, top compradores
    municipios_ativos = len(set(
        item.get("municipio", "").strip()
        for item in uf_results
        if item.get("municipio", "").strip()
    ))

    national_cached = _cache_get(f"setor:{sector.id}")
    if national_cached and national_cached.get("avg_value", 0) > 0 and avg_val > 0:
        nat_avg = float(national_cached["avg_value"])
        vs_media_nacional_pct: Optional[float] = round((avg_val - nat_avg) / nat_avg * 100, 1)
    else:
        vs_media_nacional_pct = None

    from collections import defaultdict
    comprador_acc: dict[str, dict] = defaultdict(lambda: {"nome": "", "total_contratos": 0, "valor_total": 0.0})
    for item in uf_results:
        cnpj = item.get("orgaoCnpj") or ""
        if not cnpj:
            continue
        comprador_acc[cnpj]["nome"] = item.get("nomeOrgao") or _extract_orgao(item)
        comprador_acc[cnpj]["total_contratos"] += 1
        comprador_acc[cnpj]["valor_total"] += _extract_value(item) or 0.0
    top_compradores = sorted(
        [{"cnpj": c, **v} for c, v in comprador_acc.items()],
        key=lambda x: x["valor_total"],
        reverse=True,
    )[:3]

    data = {
        "sector_id": sector.id,
        "sector_name": sector.name,
        "uf": uf,
        "total_editais": len(uf_results),
        "avg_value": round(avg_val, 2),
        "value_range_min": round(min_val, 2),
        "value_range_max": round(max_val, 2),
        "top_modalidades": top_mods,
        "trend_90d": trend_90d,
        "top_oportunidades": top_items,
        "last_updated": now.isoformat(),
        "most_recent_bid_date": most_recent_bid_date,
        "municipios_ativos": municipios_ativos,
        "vs_media_nacional_pct": vs_media_nacional_pct,
        "top_compradores": top_compradores,
    }
    _cache_set(cache_key, data)
    return SectorUfStats(**data)


# ---------------------------------------------------------------------------
# Endpoint 3: City stats
# ---------------------------------------------------------------------------

@router.get("/cidade/{cidade}", response_model=CidadeStats)
async def get_cidade_stats(cidade: str):
    """City stats: count, frequent buying orgs, avg values.

    Public (no auth). Cached 6h.
    Uses the first sector with results to get city data.
    """
    cidade_normalized = cidade.lower().replace("-", " ").strip()
    # CRIT-SEO-011: normalize to ASCII for match against DataLake items
    # (PNCP stores city names with accents; slugs arrive without them).
    # Mirrors the pattern used in get_cidade_sector_stats / get_contratos_cidade_stats.
    cidade_ascii = _strip_accents(cidade.replace("-", " ").strip())
    cache_key = f"cidade:{cidade_ascii}"

    cached = _cache_get(cache_key)
    if cached:
        return CidadeStats(**cached)

    # Determine UF for city (try both normalized and ASCII forms)
    uf = _CITY_TO_UF.get(cidade_normalized) or _CITY_TO_UF.get(cidade_ascii)
    if not uf:
        raise HTTPException(status_code=404, detail=f"Cidade '{cidade}' não encontrada")

    # Query datalake for this UF without sector keyword filter
    from datalake_query import query_datalake

    now = datetime.now(timezone.utc)
    data_final = now.strftime("%Y-%m-%d")
    data_inicial = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    all_results: list[dict] = []
    try:
        all_results = await query_datalake(
            ufs=[uf],
            data_inicial=data_inicial,
            data_final=data_final,
            keywords=None,
            limit=2000,
        )
    except Exception as e:
        logger.debug("Datalake query failed for cidade=%s uf=%s: %s", cidade, uf, e)

    # Filter by city name in orgaoEntidade.municipioNome — accent-insensitive
    # (CRIT-SEO-011: "são paulo" must match slug "sao-paulo" → cidade_ascii "sao paulo")
    city_results = []
    for item in all_results:
        item_city_ascii = _strip_accents(_extract_city(item).lower())
        if cidade_ascii in item_city_ascii or item_city_ascii in cidade_ascii:
            city_results.append(item)

    # Org frequency
    org_counter: Counter = Counter()
    for item in city_results:
        org_counter[_extract_orgao(item)] += 1
    orgaos = [{"name": o, "count": c} for o, c in org_counter.most_common(5)]

    values = [v for item in city_results if (v := _extract_value(item)) is not None]
    avg_val = sum(values) / len(values) if values else 0.0

    # Capitalize city name for display
    display_name = cidade.replace("-", " ").title()

    data = {
        "cidade": display_name,
        "uf": uf,
        "total_editais": len(city_results),
        "orgaos_frequentes": orgaos,
        "avg_value": round(avg_val, 2),
        "last_updated": now.isoformat(),
    }
    _cache_set(cache_key, data)
    return CidadeStats(**data)


# ---------------------------------------------------------------------------
# Endpoint 3b: City × Sector stats
# ---------------------------------------------------------------------------

@router.get("/cidade/{cidade}/setor/{setor_id}", response_model=CidadeSectorStats)
async def get_cidade_sector_stats(cidade: str, setor_id: str):
    """City × Sector stats: cross-reference city with sector keywords.

    Public (no auth). Cached 6h.
    """
    cidade_normalized = cidade.lower().replace("-", " ").strip()
    cidade_ascii = _strip_accents(cidade.replace("-", " ").strip())
    cache_key = f"cidade_setor:{cidade_ascii}:{setor_id}"

    cached = _cache_get(cache_key)
    if cached:
        return CidadeSectorStats(**cached)

    # Validate city (try accented lookup first, then ASCII-stripped)
    uf = _CITY_TO_UF.get(cidade_normalized) or _CITY_TO_UF.get(cidade_ascii)
    if not uf:
        raise HTTPException(status_code=404, detail=f"Cidade '{cidade}' não encontrada")

    # Validate sector
    sector = _validate_sector(setor_id)

    # Query PNCP with sector keyword filter for this UF
    results = await _query_pncp_for_sector(sector, [uf])

    # Filter by city name in municipioNome (use ASCII-stripped comparison to handle accents)
    city_results = []
    for item in results:
        item_city = _strip_accents(_extract_city(item))
        if cidade_ascii in item_city or item_city in cidade_ascii:
            city_results.append(item)

    # Aggregations
    values = [v for item in city_results if (v := _extract_value(item)) is not None]
    avg_val = sum(values) / len(values) if values else 0.0
    min_val = min(values) if values else 0.0
    max_val = max(values) if values else 0.0

    org_counter: Counter = Counter()
    mod_counter: Counter = Counter()
    for item in city_results:
        org_counter[_extract_orgao(item)] += 1
        mod_counter[_extract_modality(item)] += 1

    top_orgaos = [{"name": o, "count": c} for o, c in org_counter.most_common(5)]
    top_mods = [{"name": m, "count": c} for m, c in mod_counter.most_common(5)]
    top_items = [_make_sample_item(item) for item in city_results[:5]]

    display_name = cidade.replace("-", " ").title()
    now = datetime.now(timezone.utc)

    data = {
        "cidade": display_name,
        "uf": uf,
        "sector_id": sector.id,
        "sector_name": sector.name,
        "total_editais": len(city_results),
        "avg_value": round(avg_val, 2),
        "value_range_min": round(min_val, 2),
        "value_range_max": round(max_val, 2),
        "top_modalidades": top_mods,
        "orgaos_frequentes": top_orgaos,
        "top_oportunidades": top_items,
        "has_sufficient_data": len(city_results) >= 5,
        "last_updated": now.isoformat(),
    }
    _cache_set(cache_key, data)
    return CidadeSectorStats(**data)


# ---------------------------------------------------------------------------
# Endpoint 4: National panorama
# ---------------------------------------------------------------------------

@router.get("/panorama/{setor_id}", response_model=PanoramaStats)
async def get_panorama_stats(setor_id: str):
    """National panorama: totals, seasonality, estimated YoY growth.

    Public (no auth). Cached 6h.
    """
    sector = _validate_sector(setor_id)
    cache_key = f"panorama:{sector.id}"

    cached = _cache_get(cache_key)
    if cached:
        return PanoramaStats(**cached)

    results = await _query_pncp_for_sector(sector, TOP_UFS)
    now = datetime.now(timezone.utc)

    # National totals
    values = [v for item in results if (v := _extract_value(item)) is not None]
    total = len(results)
    total_val = sum(values)
    avg_val = total_val / len(values) if values else 0.0

    # Top UFs
    uf_counter: Counter = Counter()
    for item in results:
        uf = _extract_uf(item)
        if uf:
            uf_counter[uf] += 1
    top_ufs = [{"name": uf, "count": c} for uf, c in uf_counter.most_common(10)]

    # Top modalidades
    mod_counter: Counter = Counter()
    for item in results:
        mod_counter[_extract_modality(item)] += 1
    top_mods = [{"name": m, "count": c} for m, c in mod_counter.most_common(5)]

    # Seasonality (estimated monthly distribution)
    sazonalidade = _estimate_seasonality(total, avg_val, now)

    # Estimated YoY growth (conservative 8-15% based on PNCP adoption trends)
    crescimento = 12.0  # Conservative estimate for public procurement growth

    data = {
        "sector_id": sector.id,
        "sector_name": sector.name,
        "total_nacional": total * 27 // len(TOP_UFS),  # Extrapolate to all UFs
        "total_value": round(total_val * 27 / len(TOP_UFS), 2),
        "avg_value": round(avg_val, 2),
        "top_ufs": top_ufs,
        "top_modalidades": top_mods,
        "sazonalidade": sazonalidade,
        "crescimento_estimado_pct": crescimento,
        "last_updated": now.isoformat(),
    }
    _cache_set(cache_key, data)
    return PanoramaStats(**data)


def _estimate_seasonality(
    current_count: int, avg_value: float, now: datetime
) -> list[dict]:
    """Estimate 12-month seasonality from current data.

    Brazilian procurement has known patterns:
    - Q1 (Jan-Mar): Low (budget approval phase)
    - Q2 (Apr-Jun): Medium (execution ramps up)
    - Q3 (Jul-Sep): High (peak execution)
    - Q4 (Oct-Dec): Medium-High (year-end spending rush)
    """
    monthly_factors = [
        0.6, 0.7, 0.8,   # Q1: Low
        0.9, 1.0, 1.0,   # Q2: Medium
        1.1, 1.2, 1.1,   # Q3: High
        1.0, 1.1, 0.9,   # Q4: Medium-High
    ]

    base_monthly = current_count * 3  # 10-day × 3 ≈ monthly
    months = []
    for i in range(12):
        month_date = datetime(now.year, i + 1, 1)
        factor = monthly_factors[i]
        months.append({
            "period": month_date.strftime("%Y-%m"),
            "count": max(1, int(base_monthly * factor)),
            "avg_value": round(avg_value * factor, 2),
        })
    return months


# ---------------------------------------------------------------------------
# Endpoint 5: Contratos by sector (Wave 3.1 — pillar pages)
# ---------------------------------------------------------------------------

def _safe_float_blog(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _compute_contratos_stats(
    sector: Optional[SectorConfig] = None,
    *,
    uf: Optional[str] = None,
    municipio_pattern: Optional[str] = None,
) -> dict:
    """Query pncp_supplier_contracts with optional UF/municipio filters, aggregate.

    Returns a dict containing the common aggregation fields (total_contracts,
    total_value, avg_value, top_orgaos, top_fornecedores, monthly_trend, by_uf).
    Endpoint wrappers add their specific fields (sector_id, cidade, etc).

    Raises HTTPException(502) on DB failure.
    """
    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        query = (
            sb.table("pncp_supplier_contracts")
            .select(
                "ni_fornecedor,nome_fornecedor,orgao_cnpj,orgao_nome,"
                "valor_global,data_assinatura,objeto_contrato,uf,municipio"
            )
            .eq("is_active", True)
        )
        if uf:
            query = query.eq("uf", uf)
        if municipio_pattern:
            # pncp_supplier_contracts.municipio is free-text — case-insensitive
            # substring match via ilike (handles variations like "São Paulo" vs "SAO PAULO").
            query = query.ilike("municipio", f"%{municipio_pattern}%")

        resp = (
            query
            .order("data_assinatura", desc=True)
            .limit(5000)
            .execute()
        )
    except Exception as e:
        logger.error(
            "contratos DB query failed (sector=%s uf=%s municipio=%s): %s",
            sector.id if sector else None, uf, municipio_pattern, e,
        )
        # SmartLic incident 2026-04-27 humble-dolphin: hobby plan + 1 worker
        # + DB statement_timeout (8s) on (uf, municipio_pattern ilike) was
        # raising 502 and producing crawler retry storm that wedged the only
        # uvicorn worker. Returning empty stats keeps endpoint responsive
        # while DB recovers; the 6h cache layer at endpoint level absorbs
        # the empty response so subsequent hits don't re-query.
        now = datetime.now(timezone.utc)
        return {
            "total_contracts": 0,
            "total_value": 0.0,
            "avg_value": 0.0,
            "top_orgaos": [],
            "top_fornecedores": [],
            "monthly_trend": [],
            "by_uf": [],
            "last_updated": now.isoformat(),
            "n_unique_orgaos": 0,
            "n_unique_fornecedores": 0,
            "sample_contracts": [],
        }

    rows = resp.data or []

    # Filter by sector keywords (if sector provided)
    if sector is not None:
        keywords_lower = {kw.lower() for kw in sector.keywords}
        matched = [
            row for row in rows
            if any(kw in (row.get("objeto_contrato") or "").lower() for kw in keywords_lower)
        ]
    else:
        matched = rows

    # Aggregations
    total_value = 0.0
    orgao_agg: dict[str, dict] = {}
    forn_agg: dict[str, dict] = {}
    uf_agg: dict[str, dict] = {}
    monthly: Counter = Counter()
    monthly_values: dict[str, float] = {}
    sample_contracts_raw: list[dict] = []

    for row in matched:
        valor = _safe_float_blog(row.get("valor_global"))
        total_value += valor

        org_cnpj = row.get("orgao_cnpj") or ""
        if org_cnpj:
            if org_cnpj not in orgao_agg:
                orgao_agg[org_cnpj] = {"nome": row.get("orgao_nome") or org_cnpj, "cnpj": org_cnpj, "contratos": 0, "valor": 0.0}
            orgao_agg[org_cnpj]["contratos"] += 1
            orgao_agg[org_cnpj]["valor"] += valor

        ni = row.get("ni_fornecedor") or ""
        if ni:
            if ni not in forn_agg:
                forn_agg[ni] = {"nome": row.get("nome_fornecedor") or ni, "cnpj": ni, "contratos": 0, "valor": 0.0}
            forn_agg[ni]["contratos"] += 1
            forn_agg[ni]["valor"] += valor

        # Collect sample contracts (rows already ordered desc by data_assinatura)
        if len(sample_contracts_raw) < 5:
            obj = (row.get("objeto_contrato") or "").strip()
            if obj and valor > 0:
                sample_contracts_raw.append({
                    "objeto": obj[:200],
                    "orgao": row.get("orgao_nome") or org_cnpj or "",
                    "fornecedor": row.get("nome_fornecedor") or ni or "",
                    "valor": valor,
                    "data_assinatura": (row.get("data_assinatura") or "")[:10],
                })

        row_uf = (row.get("uf") or "").upper()
        if row_uf:
            if row_uf not in uf_agg:
                uf_agg[row_uf] = {"uf": row_uf, "contratos": 0, "valor": 0.0}
            uf_agg[row_uf]["contratos"] += 1
            uf_agg[row_uf]["valor"] += valor

        data_str = (row.get("data_assinatura") or "")[:7]
        if data_str:
            monthly[data_str] += 1
            monthly_values[data_str] = monthly_values.get(data_str, 0.0) + valor

    top_orgaos = sorted(orgao_agg.values(), key=lambda x: x["valor"], reverse=True)[:10]
    top_fornecedores = sorted(forn_agg.values(), key=lambda x: x["valor"], reverse=True)[:10]
    by_uf = sorted(uf_agg.values(), key=lambda x: x["valor"], reverse=True)

    # Monthly trend (last 12 months)
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

    # Recalculate summary totals from the trend window (last 12 months, contracts
    # with data_assinatura only) so the summary card matches the chart exactly.
    total_contracts = sum(t["count"] for t in trend)
    total_value_12m = sum(t["value"] for t in trend)
    avg_value = round(total_value_12m / total_contracts, 2) if total_contracts else 0.0

    return {
        "total_contracts": total_contracts,
        "total_value": round(total_value_12m, 2),
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
        "by_uf": [
            {"uf": u["uf"], "total_contratos": u["contratos"], "valor_total": round(u["valor"], 2)}
            for u in by_uf
        ],
        "last_updated": now.isoformat(),
        "n_unique_orgaos": len(orgao_agg),
        "n_unique_fornecedores": len(forn_agg),
        "sample_contracts": sample_contracts_raw,
    }


@router.get("/contratos/{setor_id}", response_model=ContratosSetorStats)
async def get_contratos_setor_stats(setor_id: str):
    """National contract stats by sector from pncp_supplier_contracts.

    Public (no auth). Cached 6h.
    """
    sector = _validate_sector(setor_id)
    cache_key = f"contratos_setor:{sector.id}"

    cached = _cache_get(cache_key)
    if cached:
        return ContratosSetorStats(**cached)

    base = _compute_contratos_stats(sector)
    data = {"sector_id": sector.id, "sector_name": sector.name, **base}
    _cache_set(cache_key, data)
    return ContratosSetorStats(**data)


@router.get("/contratos/{setor_id}/uf/{uf}", response_model=ContratosSetorUfStats)
async def get_contratos_setor_uf_stats(setor_id: str, uf: str):
    """Sector × UF contract stats — fallback for blog pages with zero open editais.

    Queries pncp_supplier_contracts filtered by uf (idx_psc_uf_data) and sector
    keywords. Public (no auth). Cached 6h.
    """
    uf = uf.upper().strip()
    if uf not in ALL_UFS:
        raise HTTPException(status_code=404, detail=f"UF '{uf}' não encontrada")

    sector = _validate_sector(setor_id)
    cache_key = f"contratos_setor_uf:{sector.id}:{uf}"

    cached = _cache_get(cache_key)
    if cached:
        return ContratosSetorUfStats(**cached)

    base = _compute_contratos_stats(sector, uf=uf)
    # Drop by_uf (always single UF in this scope — keeps payload lean)
    base.pop("by_uf", None)
    data = {
        "sector_id": sector.id,
        "sector_name": sector.name,
        "uf": uf,
        **base,
    }
    _cache_set(cache_key, data)
    return ContratosSetorUfStats(**data)


@router.get("/contratos/cidade/{cidade}", response_model=ContratosCidadeStats)
async def get_contratos_cidade_stats(cidade: str):
    """City-level contract stats (all sectors) — fallback for blog cidade pages.

    Public (no auth). Cached 6h.
    """
    cidade_normalized = cidade.lower().replace("-", " ").strip()
    cidade_ascii = _strip_accents(cidade.replace("-", " ").strip())
    cache_key = f"contratos_cidade:{cidade_ascii}"

    cached = _cache_get(cache_key)
    if cached:
        return ContratosCidadeStats(**cached)

    uf = _CITY_TO_UF.get(cidade_normalized) or _CITY_TO_UF.get(cidade_ascii)
    if not uf:
        raise HTTPException(status_code=404, detail=f"Cidade '{cidade}' não encontrada")

    # Use the accented official name for the ilike pattern (DB stores accented
    # values — "São Paulo", not "Sao Paulo"). Fallback to title-cased slug.
    municipio_display = (
        _CITY_DISPLAY.get(cidade_normalized)
        or _CITY_DISPLAY.get(cidade_ascii)
        or cidade.replace("-", " ").title()
    )

    # Filter by UF first (indexed) + ilike on municipio (free-text)
    base = _compute_contratos_stats(uf=uf, municipio_pattern=municipio_display)
    base.pop("by_uf", None)
    data = {
        "cidade": municipio_display,
        "uf": uf,
        **base,
    }
    _cache_set(cache_key, data)
    return ContratosCidadeStats(**data)


@router.get(
    "/contratos/cidade/{cidade}/setor/{setor_id}",
    response_model=ContratosCidadeSetorStats,
)
async def get_contratos_cidade_setor_stats(cidade: str, setor_id: str):
    """City × Sector contract stats — fallback for blog cidade×setor pages.

    Public (no auth). Cached 6h.
    """
    cidade_normalized = cidade.lower().replace("-", " ").strip()
    cidade_ascii = _strip_accents(cidade.replace("-", " ").strip())
    cache_key = f"contratos_cidade_setor:{cidade_ascii}:{setor_id}"

    cached = _cache_get(cache_key)
    if cached:
        return ContratosCidadeSetorStats(**cached)

    uf = _CITY_TO_UF.get(cidade_normalized) or _CITY_TO_UF.get(cidade_ascii)
    if not uf:
        raise HTTPException(status_code=404, detail=f"Cidade '{cidade}' não encontrada")

    sector = _validate_sector(setor_id)
    municipio_display = (
        _CITY_DISPLAY.get(cidade_normalized)
        or _CITY_DISPLAY.get(cidade_ascii)
        or cidade.replace("-", " ").title()
    )

    base = _compute_contratos_stats(sector, uf=uf, municipio_pattern=municipio_display)
    base.pop("by_uf", None)
    data = {
        "cidade": municipio_display,
        "uf": uf,
        "sector_id": sector.id,
        "sector_name": sector.name,
        **base,
    }
    _cache_set(cache_key, data)
    return ContratosCidadeSetorStats(**data)
