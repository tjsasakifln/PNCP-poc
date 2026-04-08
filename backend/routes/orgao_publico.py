"""SEO Onda 2: Public stats endpoint for órgão comprador pages.

Aggregates bid statistics for a single government buying organization
from the local pncp_raw_bids datalake. Queries only local DB — no
external API calls. Public (no auth). Cache: InMemory 24h TTL per CNPJ.
"""

import logging
import re
import time
from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["orgao-publico"])

_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h
_orgao_cache: dict[str, tuple[dict, float]] = {}

_CNPJ_RE = re.compile(r"^\d{14}$")

_ESFERA_LABELS = {"F": "Federal", "E": "Estadual", "M": "Municipal", "D": "Distrital"}

_STOPWORDS = frozenset({
    "de", "do", "da", "dos", "das", "para", "com", "por", "em", "a", "o", "e",
    "ou", "que", "na", "no", "nas", "nos", "um", "uma", "uns", "umas", "ao",
    "aos", "às", "se", "seu", "sua", "seus", "suas", "mais", "como", "mas",
    "foi", "não", "pelo", "pela", "pelos", "pelas", "este", "essa", "esse",
    "esta", "são", "ser", "ter", "tem", "num", "numa", "entre", "sobre",
    "quando", "também", "até", "já", "foi", "era", "está", "seu", "sua",
    "tipo", "cada", "todo", "toda", "todos", "todas", "outros", "outras",
    "outro", "outra", "cujo", "cuja", "qual", "quais", "cujos", "cujas",
})


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class LicitacaoRecente(BaseModel):
    objeto_compra: str
    modalidade_nome: str
    valor_total_estimado: Optional[float] = None
    data_publicacao: str
    uf: str


class ModalidadeCount(BaseModel):
    nome: str
    count: int


class OrgaoStatsResponse(BaseModel):
    nome: str
    cnpj: str
    esfera: str
    uf: str
    municipio: str
    total_licitacoes: int
    licitacoes_30d: int
    licitacoes_90d: int
    licitacoes_365d: int
    valor_medio_estimado: float
    valor_total_estimado: float
    top_modalidades: list[ModalidadeCount]
    top_setores: list[str]
    ultimas_licitacoes: list[LicitacaoRecente]
    aviso_legal: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/orgao/{cnpj}/stats",
    response_model=OrgaoStatsResponse,
    summary="Estatísticas públicas de um órgão comprador por CNPJ",
)
async def orgao_stats(cnpj: str):
    cnpj_clean = re.sub(r"\D", "", cnpj)

    if not _CNPJ_RE.match(cnpj_clean):
        raise HTTPException(status_code=400, detail="CNPJ inválido — informe 14 dígitos numéricos")

    cached = _get_cached(cnpj_clean)
    if cached:
        return OrgaoStatsResponse(**cached)

    data = await _build_orgao_stats(cnpj_clean)
    _set_cached(cnpj_clean, data)
    return OrgaoStatsResponse(**data)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _get_cached(key: str) -> Optional[dict]:
    if key not in _orgao_cache:
        return None
    data, ts = _orgao_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _orgao_cache[key]
        return None
    return data


def _set_cached(key: str, data: dict) -> None:
    _orgao_cache[key] = (data, time.time())


# ---------------------------------------------------------------------------
# Top-setores extraction (word-frequency heuristic)
# ---------------------------------------------------------------------------

def _extract_top_setores(rows: list[dict], top_n: int = 5) -> list[str]:
    """Extract top meaningful words from objeto_compra across all bids."""
    word_counts: Counter = Counter()
    for row in rows:
        texto = (row.get("objeto_compra") or "").lower()
        # Remove punctuation / numbers
        texto = re.sub(r"[^\w\s]", " ", texto)
        texto = re.sub(r"\d+", " ", texto)
        for word in texto.split():
            if len(word) >= 4 and word not in _STOPWORDS:
                word_counts[word] += 1

    return [word for word, _ in word_counts.most_common(top_n)]


# ---------------------------------------------------------------------------
# Build stats
# ---------------------------------------------------------------------------

async def _build_orgao_stats(cnpj: str) -> dict:
    """Query pncp_raw_bids and aggregate stats for a single órgão."""
    try:
        from supabase_client import get_supabase

        sb = get_supabase()
        resp = (
            sb.table("pncp_raw_bids")
            .select(
                "orgao_razao_social,"
                "esfera_id,"
                "uf,"
                "municipio,"
                "modalidade_nome,"
                "objeto_compra,"
                "valor_total_estimado,"
                "data_publicacao"
            )
            .eq("orgao_cnpj", cnpj)
            .eq("is_active", True)
            .limit(5000)
            .execute()
        )
    except Exception as e:
        logger.error("orgao_stats DB query failed for %s: %s", cnpj, e)
        raise HTTPException(status_code=502, detail="Erro ao consultar o datalake")

    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Órgão não encontrado no datalake")

    # Basic info from first row
    first = rows[0]
    nome = (first.get("orgao_razao_social") or "").strip() or "Não informado"
    esfera_raw = (first.get("esfera_id") or "").strip().upper()
    esfera = _ESFERA_LABELS.get(esfera_raw, esfera_raw or "Não informado")
    uf = (first.get("uf") or "").strip().upper()
    municipio = (first.get("municipio") or "").strip() or "Não informado"

    # Date windows
    now = datetime.now(timezone.utc)
    cutoff_30d = now - timedelta(days=30)
    cutoff_90d = now - timedelta(days=90)
    cutoff_365d = now - timedelta(days=365)

    licitacoes_30d = 0
    licitacoes_90d = 0
    licitacoes_365d = 0
    valores: list[float] = []
    modalidade_counter: Counter = Counter()

    # Sort for ultimas_licitacoes (desc by data_publicacao)
    rows_sorted = sorted(
        rows,
        key=lambda r: (r.get("data_publicacao") or ""),
        reverse=True,
    )

    for row in rows:
        # Date-window counts
        data_pub_str = (row.get("data_publicacao") or "")[:10]  # YYYY-MM-DD
        if data_pub_str:
            try:
                data_pub = datetime.fromisoformat(data_pub_str).replace(tzinfo=timezone.utc)
                if data_pub >= cutoff_365d:
                    licitacoes_365d += 1
                if data_pub >= cutoff_90d:
                    licitacoes_90d += 1
                if data_pub >= cutoff_30d:
                    licitacoes_30d += 1
            except ValueError:
                pass

        # Valor
        v = row.get("valor_total_estimado")
        if v is not None:
            try:
                fv = float(v)
                if fv > 0:
                    valores.append(fv)
            except (ValueError, TypeError):
                pass

        # Modalidade
        mod = (row.get("modalidade_nome") or "Não informado").strip()
        if mod:
            modalidade_counter[mod] += 1

    total_licitacoes = len(rows)
    valor_total = round(sum(valores), 2)
    valor_medio = round(valor_total / len(valores), 2) if valores else 0.0

    # Top 5 modalidades
    top_modalidades = [
        {"nome": nome_mod, "count": cnt}
        for nome_mod, cnt in modalidade_counter.most_common(5)
    ]

    # Top setores (word-frequency heuristic)
    top_setores = _extract_top_setores(rows, top_n=5)

    # Last 10 bids
    ultimas_licitacoes = []
    for row in rows_sorted[:10]:
        objeto = (row.get("objeto_compra") or "").strip()
        if len(objeto) > 200:
            objeto = objeto[:197] + "..."
        v = row.get("valor_total_estimado")
        valor_bid: Optional[float] = None
        if v is not None:
            try:
                fv = float(v)
                if fv > 0:
                    valor_bid = fv
            except (ValueError, TypeError):
                pass
        ultimas_licitacoes.append({
            "objeto_compra": objeto or "Não informado",
            "modalidade_nome": (row.get("modalidade_nome") or "Não informado").strip(),
            "valor_total_estimado": valor_bid,
            "data_publicacao": (row.get("data_publicacao") or "")[:10],
            "uf": (row.get("uf") or uf or "").strip().upper(),
        })

    return {
        "nome": nome,
        "cnpj": cnpj,
        "esfera": esfera,
        "uf": uf,
        "municipio": municipio,
        "total_licitacoes": total_licitacoes,
        "licitacoes_30d": licitacoes_30d,
        "licitacoes_90d": licitacoes_90d,
        "licitacoes_365d": licitacoes_365d,
        "valor_medio_estimado": valor_medio,
        "valor_total_estimado": valor_total,
        "top_modalidades": top_modalidades,
        "top_setores": top_setores,
        "ultimas_licitacoes": ultimas_licitacoes,
        "aviso_legal": (
            "Dados de fontes públicas: Portal Nacional de Contratações Públicas (PNCP). "
            "Atualização diária."
        ),
    }
