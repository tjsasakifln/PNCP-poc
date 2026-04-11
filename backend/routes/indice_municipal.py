"""STORY-435: Índice SmartLic de Transparência Municipal.

Endpoints públicos (sem auth) para ranking de municípios por transparência
em compras públicas. Dados derivados de pncp_raw_bids (PNCP via SmartLic).

Público. Cache: InMemory 1h TTL.
CORS: Access-Control-Allow-Origin: * (link bait embeddável).
"""

import logging
import re
import time
import unicodedata
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["indice-municipal"])

_CACHE_TTL_SECONDS = 60 * 60  # 1h
_route_cache: dict[str, tuple[dict | list, float]] = {}

UF_NAMES: dict[str, str] = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}

VALID_UFS = set(UF_NAMES.keys())

# Período corrente padrão (atualizar trimestralmente)
PERIODO_CORRENTE = "2026-Q1"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class IndiceResult(BaseModel):
    municipio_nome: str
    municipio_slug: str
    uf: str
    uf_nome: str
    periodo: str
    score_total: float
    score_volume_publicacao: float
    score_eficiencia_temporal: float
    score_diversidade_mercado: float
    score_transparencia_digital: float
    score_consistencia: float
    total_editais: int
    ranking_nacional: Optional[int] = None
    ranking_uf: Optional[int] = None
    percentil: Optional[int] = None
    calculado_em: str


class RankingResponse(BaseModel):
    periodo: str
    total: int
    resultados: list[IndiceResult]
    fonte: str
    license: str


class PeriodosResponse(BaseModel):
    periodos: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    """'São Paulo' + 'SP' → 'sao-paulo-sp'"""
    # Normalize unicode (NFD removes accents)
    nfkd = unicodedata.normalize("NFD", text)
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    # lowercase, replace spaces with hyphens, remove non-alphanumeric
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_str.lower()).strip("-")
    return slug


def _parse_slug(slug: str) -> Optional[tuple[str, str]]:
    """'sao-paulo-sp' → (municipio_name_slug, uf) or None if invalid.

    Returns the municipio portion (slug) and uf portion.
    Assumes slug ends with '-{UF}' where UF is 2 uppercase chars.
    """
    if len(slug) < 4 or slug[-3] != "-":
        return None
    uf = slug[-2:].upper()
    if uf not in VALID_UFS:
        return None
    municipio_slug = slug[:-3]
    if not municipio_slug:
        return None
    return municipio_slug, uf


def _get_cached(key: str) -> Optional[dict | list]:
    if key not in _route_cache:
        return None
    data, ts = _route_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _route_cache[key]
        return None
    return data


def _set_cached(key: str, data: dict | list) -> None:
    _route_cache[key] = (data, time.time())


def _add_cors(response: Optional[Response]) -> None:
    if response is not None:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"


def _enrich_result(row: dict, position: int = 0) -> IndiceResult:
    """Converte row do Supabase em IndiceResult com slug e uf_nome."""
    municipio_nome = row.get("municipio_nome", "")
    uf = row.get("uf", "")
    slug = f"{_slugify(municipio_nome)}-{uf.lower()}"
    return IndiceResult(
        municipio_nome=municipio_nome,
        municipio_slug=slug,
        uf=uf,
        uf_nome=UF_NAMES.get(uf, uf),
        periodo=row.get("periodo", ""),
        score_total=float(row.get("score_total") or 0),
        score_volume_publicacao=float(row.get("score_volume_publicacao") or 0),
        score_eficiencia_temporal=float(row.get("score_eficiencia_temporal") or 0),
        score_diversidade_mercado=float(row.get("score_diversidade_mercado") or 0),
        score_transparencia_digital=float(row.get("score_transparencia_digital") or 0),
        score_consistencia=float(row.get("score_consistencia") or 0),
        total_editais=int(row.get("total_editais") or 0),
        ranking_nacional=row.get("ranking_nacional"),
        ranking_uf=row.get("ranking_uf"),
        percentil=row.get("percentil"),
        calculado_em=str(row.get("calculado_em", "")),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/indice-municipal/periodos",
    response_model=PeriodosResponse,
    summary="Períodos disponíveis no Índice Municipal (público)",
)
async def get_periodos(response: Response = None):
    """Lista trimestres com dados calculados no índice."""
    _add_cors(response)
    cached = _get_cached("periodos")
    if cached is not None:
        return PeriodosResponse(periodos=cached)  # type: ignore[arg-type]

    from services.indice_municipal import listar_periodos_disponiveis
    periodos = await listar_periodos_disponiveis()
    if not periodos:
        periodos = [PERIODO_CORRENTE]
    _set_cached("periodos", periodos)
    return PeriodosResponse(periodos=periodos)


@router.get(
    "/indice-municipal",
    response_model=RankingResponse,
    summary="Ranking de transparência municipal em compras públicas (público)",
)
async def get_ranking(
    periodo: str = Query(
        default=PERIODO_CORRENTE,
        description="Período trimestral (ex: 2026-Q1)",
        pattern=r"^\d{4}-Q[1-4]$",
    ),
    uf: Optional[str] = Query(None, min_length=2, max_length=2, description="Filtrar por UF"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    response: Response = None,
):
    """Ranking nacional ou por UF de transparência municipal. Dados do PNCP."""
    _add_cors(response)

    uf_upper = uf.upper() if uf else None
    if uf_upper and uf_upper not in VALID_UFS:
        raise HTTPException(status_code=400, detail=f"UF '{uf}' inválida")

    cache_key = f"ranking:{periodo}:{uf_upper or 'ALL'}:{limit}:{offset}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return RankingResponse(**cached)  # type: ignore[arg-type]

    from services.indice_municipal import listar_ranking_por_uf, listar_ranking_nacional

    if uf_upper:
        rows = await listar_ranking_por_uf(uf_upper, periodo, limit=limit)
    else:
        rows = await listar_ranking_nacional(periodo, limit=limit, offset=offset)

    resultados = [_enrich_result(row, i + 1 + offset) for i, row in enumerate(rows)]

    data: dict = {
        "periodo": periodo,
        "total": len(resultados),
        "resultados": [r.model_dump() for r in resultados],
        "fonte": "PNCP via SmartLic Observatório",
        "license": "CC BY 4.0",
    }
    _set_cached(cache_key, data)
    return RankingResponse(**data)


@router.get(
    "/indice-municipal/{municipio_slug}",
    response_model=IndiceResult,
    summary="Índice de transparência de um município (público)",
)
async def get_municipio(
    municipio_slug: str,
    periodo: str = Query(
        default=PERIODO_CORRENTE,
        description="Período trimestral (ex: 2026-Q1)",
        pattern=r"^\d{4}-Q[1-4]$",
    ),
    response: Response = None,
):
    """Retorna índice de transparência de um município (slug: sao-paulo-sp)."""
    _add_cors(response)

    parsed = _parse_slug(municipio_slug)
    if not parsed:
        raise HTTPException(
            status_code=400,
            detail="Slug inválido. Use formato: nome-do-municipio-uf (ex: sao-paulo-sp)",
        )
    municipio_part, uf = parsed

    cache_key = f"municipio:{municipio_slug}:{periodo}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return IndiceResult(**cached)  # type: ignore[arg-type]

    # Busca no banco primeiro
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        resp = (
            sb.table("indice_municipal")
            .select("*")
            .eq("uf", uf)
            .eq("periodo", periodo)
            .ilike("municipio_nome", f"%{municipio_part.replace('-', '%')}%")
            .order("score_total", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
    except Exception as e:
        logger.warning("indice_municipal: lookup failed for %s: %s", municipio_slug, e)
        rows = []

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Município '{municipio_slug}' não encontrado no índice para o período {periodo}. "
                   "O município precisa ter pelo menos 10 editais publicados no PNCP.",
        )

    result = _enrich_result(rows[0])
    _set_cached(cache_key, result.model_dump())
    return result
