"""P3 SEO: Public CNPJ B2G profile endpoint for /cnpj/[cnpj].

Aggregates BrasilAPI (company data) + Portal da Transparência (contracts)
+ datalake (open bids in detected sector) into a single public profile.

Public (no auth). Cache: InMemory 24h TTL.
"""

import logging
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sectors import SECTORS
from utils.cnae_mapping import map_cnae_to_setor, get_setor_name

logger = logging.getLogger(__name__)
router = APIRouter(tags=["empresa-publica"])

_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24h
_perfil_cache: dict[str, tuple[dict, float]] = {}

_CNPJ_RE = re.compile(r"^\d{14}$")
_BRASILAPI_TIMEOUT = 15
_PT_TIMEOUT = 20
_PNCP_TIMEOUT = 25
_PNCP_BASE = "https://pncp.gov.br/api/consulta/v1"
_ESFERA_LABELS = {"F": "Federal", "E": "Estadual", "M": "Municipal", "D": "Distrital"}


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ContratoPublico(BaseModel):
    orgao: str
    valor: Optional[float] = None
    data_inicio: Optional[str] = None
    descricao: str
    esfera: Optional[str] = None
    uf: Optional[str] = None


class EmpresaInfo(BaseModel):
    razao_social: str
    cnpj: str
    cnae_principal: str
    porte: str
    uf: str
    situacao: str


class PerfilB2GResponse(BaseModel):
    empresa: EmpresaInfo
    contratos: list[ContratoPublico]
    score: str  # "ATIVO" | "INICIANTE" | "SEM_HISTORICO"
    setor_detectado: str
    setor_nome: str
    editais_abertos_setor: int
    total_contratos_24m: int
    valor_total_24m: float
    ufs_atuacao: list[str]
    aviso_legal: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/empresa/{cnpj}/perfil-b2g",
    response_model=PerfilB2GResponse,
    summary="Perfil B2G público de uma empresa por CNPJ",
)
async def perfil_b2g(cnpj: str):
    cnpj_clean = re.sub(r"\D", "", cnpj)

    if not _CNPJ_RE.match(cnpj_clean):
        raise HTTPException(status_code=400, detail="CNPJ inválido — informe 14 dígitos numéricos")

    cached = _get_cached(cnpj_clean)
    if cached:
        return PerfilB2GResponse(**cached)

    data = await _build_perfil(cnpj_clean)
    _set_cached(cnpj_clean, data)
    return PerfilB2GResponse(**data)


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _get_cached(key: str) -> Optional[dict]:
    if key not in _perfil_cache:
        return None
    data, ts = _perfil_cache[key]
    if time.time() - ts >= _CACHE_TTL_SECONDS:
        del _perfil_cache[key]
        return None
    return data


def _set_cached(key: str, data: dict) -> None:
    _perfil_cache[key] = (data, time.time())


# ---------------------------------------------------------------------------
# BrasilAPI
# ---------------------------------------------------------------------------

async def _fetch_brasilapi(cnpj: str) -> dict:
    """Fetch company data from BrasilAPI (public, no auth)."""
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    async with httpx.AsyncClient(timeout=_BRASILAPI_TIMEOUT) as client:
        resp = await client.get(url)

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="CNPJ não encontrado na base de dados")
    if resp.status_code != 200:
        logger.warning("BrasilAPI error %d for %s", resp.status_code, cnpj)
        raise HTTPException(status_code=502, detail="Erro ao consultar dados da empresa")

    return resp.json()


# ---------------------------------------------------------------------------
# PNCP — contracts (all spheres: Federal, Estadual, Municipal, Distrital)
# ---------------------------------------------------------------------------

def _normalize_cnpj(raw: str) -> str:
    return raw.replace(".", "").replace("/", "").replace("-", "")


async def _fetch_contratos_pncp(cnpj: str) -> list[dict]:
    """Fetch contracts from PNCP (all government spheres).

    PNCP /contratos ignores cnpjFornecedor server-side, so we filter
    client-side by niFornecedor. See collect-report-data.py for details.
    """
    now = datetime.now(timezone.utc)
    data_fim = now.strftime("%Y%m%d")
    data_ini = (now - timedelta(days=730)).strftime("%Y%m%d")

    matched: list[dict] = []
    max_pages = 5

    try:
        async with httpx.AsyncClient(timeout=_PNCP_TIMEOUT) as client:
            page = 1
            while page <= max_pages:
                resp = await client.get(
                    f"{_PNCP_BASE}/contratos",
                    params={
                        "cnpjFornecedor": cnpj,
                        "dataInicial": data_ini,
                        "dataFinal": data_fim,
                        "pagina": page,
                        "tamanhoPagina": 50,
                    },
                )
                if resp.status_code != 200:
                    logger.warning("PNCP contratos %d for %s p=%d", resp.status_code, cnpj, page)
                    break

                body = resp.json()
                items = body.get("data", body) if isinstance(body, dict) else body
                if not isinstance(items, list) or not items:
                    break

                total_records = body.get("totalRegistros", 0) if isinstance(body, dict) else 0

                for c in items:
                    ni = _normalize_cnpj(c.get("niFornecedor") or "")
                    if ni and ni != cnpj:
                        continue

                    orgao = c.get("orgaoEntidade", {})
                    unidade = c.get("unidadeOrgao", {})
                    esfera_id = orgao.get("esferaId", "")

                    valor = None
                    for vf in ("valorGlobal", "valorInicial"):
                        v = c.get(vf)
                        if v is not None:
                            try:
                                fv = float(v)
                                if fv > 0:
                                    valor = fv
                                    break
                            except (ValueError, TypeError):
                                pass

                    data_assinatura = c.get("dataAssinatura") or ""
                    if len(data_assinatura) > 10:
                        data_assinatura = data_assinatura[:10]

                    descricao = c.get("objetoContrato") or c.get("informacaoComplementar") or "Sem descrição"
                    if len(descricao) > 200:
                        descricao = descricao[:197] + "..."

                    matched.append({
                        "orgao": unidade.get("nomeUnidade", "") or orgao.get("razaoSocial", "Não informado"),
                        "valor": valor,
                        "data_inicio": data_assinatura,
                        "descricao": descricao,
                        "esfera": _ESFERA_LABELS.get(esfera_id, esfera_id),
                        "uf": unidade.get("ufSigla", ""),
                    })

                total_pages = body.get("totalPaginas", 1) if isinstance(body, dict) else 1

                # Early termination: API not filtering, too many unrelated records
                if total_records > 5000 and not matched and page >= 3:
                    logger.warning(
                        "PNCP %d records but 0 matches for %s after %d pages — aborting",
                        total_records, cnpj, page,
                    )
                    break

                if page >= total_pages:
                    break
                page += 1

    except Exception as e:
        logger.warning("PNCP contratos error for %s: %s", cnpj, e)

    return matched


# ---------------------------------------------------------------------------
# Portal da Transparência — contracts (federal only, fallback)
# ---------------------------------------------------------------------------

async def _fetch_contratos_pt(cnpj: str) -> list[dict]:
    """Fetch government contracts from Portal da Transparência."""
    import os

    api_key = os.getenv("PORTAL_TRANSPARENCIA_API_KEY", "")
    if not api_key:
        logger.warning("PORTAL_TRANSPARENCIA_API_KEY not set — skipping contracts")
        return []

    url = "https://api.portaldatransparencia.gov.br/api-de-dados/contratos"
    params = {"cpfCnpj": cnpj, "pagina": 1, "quantidade": 20}
    headers = {"chave-api-dados": api_key}

    try:
        async with httpx.AsyncClient(timeout=_PT_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=headers)

        if resp.status_code == 429:
            logger.warning("Portal Transparência rate limited for %s", cnpj)
            return []
        if resp.status_code != 200:
            logger.warning("Portal Transparência %d for %s", resp.status_code, cnpj)
            return []

        return resp.json() if isinstance(resp.json(), list) else []
    except Exception as e:
        logger.warning("Portal Transparência error for %s: %s", cnpj, e)
        return []


# ---------------------------------------------------------------------------
# Datalake — open bids count
# ---------------------------------------------------------------------------

async def _count_editais_abertos(setor_id: str, uf: str) -> int:
    """Count open bids in detected sector/UF from datalake (last 30 days)."""
    try:
        from datalake_query import query_datalake

        sector = SECTORS.get(setor_id)
        if not sector:
            return 0

        now = datetime.now(timezone.utc)
        results = await query_datalake(
            ufs=[uf],
            data_inicial=(now - timedelta(days=30)).strftime("%Y-%m-%d"),
            data_final=now.strftime("%Y-%m-%d"),
            keywords=list(sector.keywords),
            limit=2000,
        )
        return len(results)
    except Exception as e:
        logger.warning("Datalake count failed for %s/%s: %s", setor_id, uf, e)
        return 0


# ---------------------------------------------------------------------------
# Build profile
# ---------------------------------------------------------------------------

async def _build_perfil(cnpj: str) -> dict:
    # 1. Company data
    bapi = await _fetch_brasilapi(cnpj)

    razao_social = bapi.get("razao_social") or bapi.get("nome_fantasia") or "Empresa"
    cnae_raw = bapi.get("cnae_fiscal") or bapi.get("cnae_fiscal_principal") or ""
    cnae_str = str(cnae_raw)
    porte_raw = bapi.get("porte") or bapi.get("descricao_porte") or ""
    uf = bapi.get("uf") or ""
    situacao = bapi.get("descricao_situacao_cadastral") or bapi.get("situacao_cadastral") or ""

    # 2. Detect sector from CNAE
    setor_id = map_cnae_to_setor(cnae_str)
    setor_nome = get_setor_name(setor_id)

    # 3. Contracts — PNCP primary (all spheres), PT fallback (federal only)
    contratos_pncp = await _fetch_contratos_pncp(cnpj)

    if contratos_pncp:
        contratos_all = contratos_pncp
        fonte = "PNCP"
    else:
        # Fallback to Portal da Transparência (federal only)
        contratos_pt_raw = await _fetch_contratos_pt(cnpj)
        contratos_all = []
        for c in contratos_pt_raw:
            orgao_data = c.get("unidadeGestora", {})
            valor = None
            for vf in ("valorFinalCompra", "valorInicial", "valorInicialCompra"):
                if c.get(vf):
                    try:
                        fv = float(c[vf])
                        if fv > 0:
                            valor = fv
                            break
                    except (ValueError, TypeError):
                        pass
            data_inicio = c.get("dataInicioVigencia") or c.get("dataFimCompra") or ""
            if data_inicio and len(data_inicio) > 10:
                data_inicio = data_inicio[:10]
            descricao = c.get("objeto") or c.get("descricaoObjeto") or "Sem descrição"
            if len(descricao) > 200:
                descricao = descricao[:197] + "..."
            contratos_all.append({
                "orgao": orgao_data.get("nome") or orgao_data.get("nomeOrgao") or "Não informado",
                "valor": valor,
                "data_inicio": data_inicio,
                "descricao": descricao,
                "esfera": "Federal",
                "uf": orgao_data.get("uf") or "",
            })
        fonte = "PT"

    ufs_set: set[str] = set()
    valor_total = 0.0
    contratos_parsed: list[dict] = []

    for c in contratos_all:
        uf_contrato = c.get("uf") or ""
        if uf_contrato:
            ufs_set.add(uf_contrato)
        if c.get("valor"):
            valor_total += c["valor"]
        contratos_parsed.append({
            "orgao": c["orgao"],
            "valor": c.get("valor"),
            "data_inicio": c.get("data_inicio"),
            "descricao": c["descricao"],
            "esfera": c.get("esfera"),
            "uf": uf_contrato or None,
        })

    contratos_parsed = contratos_parsed[:10]
    total_24m = len(contratos_all)

    # 4. Score
    if total_24m >= 5:
        score = "ATIVO"
    elif total_24m >= 1:
        score = "INICIANTE"
    else:
        score = "SEM_HISTORICO"

    # 5. Open bids in detected sector
    editais_count = await _count_editais_abertos(setor_id, uf) if uf else 0

    return {
        "empresa": {
            "razao_social": razao_social,
            "cnpj": cnpj,
            "cnae_principal": cnae_str,
            "porte": str(porte_raw),
            "uf": uf,
            "situacao": str(situacao),
        },
        "contratos": contratos_parsed,
        "score": score,
        "setor_detectado": setor_id,
        "setor_nome": setor_nome,
        "editais_abertos_setor": editais_count,
        "total_contratos_24m": total_24m,
        "valor_total_24m": round(valor_total, 2),
        "ufs_atuacao": sorted(ufs_set),
        "aviso_legal": "Dados de fontes públicas: CNPJ aberto (BrasilAPI) e PNCP/Portal da Transparência.",
    }
