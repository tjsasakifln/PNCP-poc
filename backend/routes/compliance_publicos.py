"""Sprint 5 Parte 13: due diligence B2G por CNPJ (CEIS + CNEP).

Endpoint publico (sem auth) que agrega dados de sancoes do Portal da
Transparencia para a pagina /compliance/{cnpj}.

Estrategia:
  - On-demand ISR (nao ha generateStaticParams no frontend)
  - Cache in-memory 24h por CNPJ
  - Se Portal Transparencia falhar: retorna dados parciais (sem levantar 502)
  - Razao social: enriched_entities (entity_type='fornecedor') ou BrasilAPI live

Endpoint:
  GET /v1/compliance/{cnpj}/profile  — perfil de due diligence B2G
"""

import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["compliance-publicos"])

_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h
_compliance_cache: dict[str, tuple[dict, float]] = {}

_CNPJ_RE = re.compile(r"^\d{14}$")
_HTTP_TIMEOUT = 10.0

_PORTAL_BASE = "https://api.portaldatransparencia.gov.br"


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
# Response models
# ---------------------------------------------------------------------------

class SancaoEntry(BaseModel):
    tipo: str           # "CEIS" | "CNEP"
    orgao_sancionador: str
    data_inicio: str
    data_fim: Optional[str] = None
    motivo: str
    valor_multa: Optional[float] = None


class ComplianceProfileResponse(BaseModel):
    cnpj: str
    razao_social: str
    situacao_geral: str   # "Sem registros" | "Sancoes ativas" | "Sancoes encerradas"
    total_sancoes_ceis: int
    total_sancoes_cnep: int
    sancoes: list[SancaoEntry]
    fonte_dados: str
    last_updated: str
    aviso_legal: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/compliance/{cnpj}/profile",
    response_model=ComplianceProfileResponse,
    summary="Perfil de due diligence B2G: CEIS + CNEP por CNPJ",
)
async def compliance_profile(cnpj: str):
    """Agrega registros CEIS e CNEP do Portal da Transparencia para um CNPJ.

    Publico, sem auth. Cache: 24h por CNPJ.
    Em caso de falha do Portal da Transparencia, retorna dados parciais.
    """
    cnpj_clean = cnpj.strip()
    if not _CNPJ_RE.match(cnpj_clean):
        raise HTTPException(status_code=400, detail="CNPJ invalido (esperado 14 digitos numericos)")

    cache_key = f"compliance:{cnpj_clean}"
    cached = _get_cached(_compliance_cache, cache_key)
    if cached:
        return ComplianceProfileResponse(**cached)

    # Razao social: tenta enriched_entities primeiro, depois BrasilAPI
    razao_social = await _fetch_razao_social(cnpj_clean)

    # Dados de sancao do Portal da Transparencia
    ceis_records, cnep_records = await _fetch_sancoes(cnpj_clean)

    sancoes: list[dict] = []
    for rec in ceis_records:
        sancoes.append(_normalize_ceis(rec))
    for rec in cnep_records:
        sancoes.append(_normalize_cnep(rec))

    # Determina situacao geral
    hoje = datetime.now(timezone.utc).date()
    tem_ativa = False
    tem_encerrada = False
    for s in sancoes:
        data_fim_str = s.get("data_fim") or ""
        if data_fim_str:
            try:
                data_fim = datetime.strptime(data_fim_str[:10], "%Y-%m-%d").date()
                if data_fim >= hoje:
                    tem_ativa = True
                else:
                    tem_encerrada = True
            except ValueError:
                tem_encerrada = True
        else:
            # Sem data_fim = ainda vigente
            tem_ativa = True

    if not sancoes:
        situacao_geral = "Sem registros"
    elif tem_ativa:
        situacao_geral = "Sancoes ativas"
    else:
        situacao_geral = "Sancoes encerradas"

    response_data = {
        "cnpj": cnpj_clean,
        "razao_social": razao_social,
        "situacao_geral": situacao_geral,
        "total_sancoes_ceis": len(ceis_records),
        "total_sancoes_cnep": len(cnep_records),
        "sancoes": sancoes,
        "fonte_dados": "Portal da Transparencia do Governo Federal (CEIS, CNEP)",
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aviso_legal": (
            "Dados extraidos do Portal da Transparencia do Governo Federal "
            "(portaldatransparencia.gov.br). As informacoes sao de carater publico e "
            "podem estar sujeitas a atualizacao. Esta pagina nao substitui consulta "
            "direta ao Portal da Transparencia. SmartLic nao se responsabiliza por "
            "decisoes tomadas com base exclusivamente nestes dados."
        ),
    }

    _set_cached(_compliance_cache, cache_key, response_data)
    return ComplianceProfileResponse(**response_data)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

async def _fetch_razao_social(cnpj: str) -> str:
    """Tenta obter a razao social de enriched_entities (Supabase) ou BrasilAPI."""
    # 1. enriched_entities
    try:
        from supabase_client import get_supabase
        sb = get_supabase()
        resp = (
            sb.table("enriched_entities")
            .select("data")
            .eq("entity_type", "fornecedor")
            .eq("entity_id", cnpj)
            .limit(1)
            .execute()
        )
        if resp.data:
            data = resp.data[0].get("data") or {}
            nome = data.get("razao_social") or ""
            if nome:
                return nome
    except Exception as e:
        logger.debug("[Compliance] enriched_entities lookup falhou para %s: %s", cnpj, e)

    # 2. BrasilAPI (fallback)
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            r = await client.get(
                f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
                follow_redirects=True,
            )
        if r.status_code == 200:
            raw = r.json()
            nome = raw.get("razao_social") or raw.get("nome") or ""
            if nome:
                return nome
    except Exception as e:
        logger.debug("[Compliance] BrasilAPI lookup falhou para %s: %s", cnpj, e)

    return cnpj


async def _fetch_sancoes(cnpj: str) -> tuple[list[dict], list[dict]]:
    """Busca registros CEIS e CNEP no Portal da Transparencia.

    Retorna (ceis_records, cnep_records). Em caso de falha, retorna listas vazias.
    """
    import config as cfg
    api_key = getattr(cfg, "PORTAL_TRANSPARENCIA_API_KEY", None) or ""
    headers = {"accept": "application/json"}
    if api_key:
        headers["chave-api-dados"] = api_key

    params = {"cnpjSancionado": cnpj, "pagina": 1, "tamanhoPagina": 20}

    ceis: list[dict] = []
    cnep: list[dict] = []

    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        # CEIS
        try:
            r = await client.get(
                f"{_PORTAL_BASE}/api-de-dados/ceis",
                params=params,
                headers=headers,
            )
            if r.status_code == 200:
                body = r.json()
                ceis = body if isinstance(body, list) else (body.get("data") or [])
        except Exception as e:
            logger.warning("[Compliance] CEIS fetch falhou para %s: %s", cnpj, e)

        # CNEP
        try:
            r = await client.get(
                f"{_PORTAL_BASE}/api-de-dados/cnep",
                params=params,
                headers=headers,
            )
            if r.status_code == 200:
                body = r.json()
                cnep = body if isinstance(body, list) else (body.get("data") or [])
        except Exception as e:
            logger.warning("[Compliance] CNEP fetch falhou para %s: %s", cnpj, e)

    return ceis, cnep


def _normalize_ceis(rec: dict) -> dict:
    return {
        "tipo": "CEIS",
        "orgao_sancionador": _str(rec.get("orgaoSancionador") or rec.get("nomeOrgaoSancionador") or ""),
        "data_inicio": _date(rec.get("dataInicioSancao") or rec.get("dataPublicacaoDou") or ""),
        "data_fim": _date(rec.get("dataFimSancao") or ""),
        "motivo": _str(rec.get("fundamentacaoLegal") or rec.get("tipoPenalidade") or ""),
        "valor_multa": None,
    }


def _normalize_cnep(rec: dict) -> dict:
    valor = None
    try:
        valor = float(rec.get("valorMulta") or 0.0) or None
    except (ValueError, TypeError):
        pass
    return {
        "tipo": "CNEP",
        "orgao_sancionador": _str(rec.get("orgaoSancionador") or rec.get("nomeOrgaoSancionador") or ""),
        "data_inicio": _date(rec.get("dataInicioSancao") or rec.get("dataPublicacaoDou") or ""),
        "data_fim": _date(rec.get("dataFimSancao") or ""),
        "motivo": _str(rec.get("fundamentacaoLegal") or rec.get("tipoPenalidade") or ""),
        "valor_multa": valor,
    }


def _str(val) -> str:
    return str(val).strip() if val else "Nao informado"


def _date(val) -> str:
    if not val:
        return ""
    s = str(val).strip()
    # Normaliza para YYYY-MM-DD
    if len(s) >= 10:
        return s[:10]
    return s
