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
# STORY-417: Timeout reduced 15→8s so a BrasilAPI hang cannot blow the
# 120s Railway proxy budget when combined with the downstream PNCP
# lookup. 8s still comfortably covers p99 BrasilAPI latency (<2s).
_BRASILAPI_TIMEOUT = 8
_PT_TIMEOUT = 20
_PNCP_TIMEOUT = 25
_PNCP_BASE = "https://pncp.gov.br/api/consulta/v1"
_ESFERA_LABELS = {"F": "Federal", "E": "Estadual", "M": "Municipal", "D": "Distrital"}

# ---------------------------------------------------------------------------
# STORY-417: Lightweight per-host circuit breaker for BrasilAPI
# ---------------------------------------------------------------------------
#
# We intentionally do NOT reuse the Supabase CB here — BrasilAPI is a
# different upstream with different failure characteristics (public,
# rate-limited, no SLA). A dedicated process-local counter is enough to
# stop hammering a downed host without adding Redis coupling to an
# endpoint that must stay cheap and public. The counter is reset on a
# successful call or after a 60s cooldown window.

_BRASILAPI_CB_THRESHOLD = 3           # consecutive failures to trip
_BRASILAPI_CB_COOLDOWN_S = 60.0       # stay OPEN this long before a probe
_brasilapi_cb_state: dict[str, float] = {
    "consecutive_failures": 0,
    "opened_at": 0.0,
}


def _brasilapi_cb_should_skip() -> bool:
    """Return True if the BrasilAPI CB is currently OPEN (fast-fail)."""
    if _brasilapi_cb_state["opened_at"] == 0.0:
        return False
    age = time.time() - _brasilapi_cb_state["opened_at"]
    if age >= _BRASILAPI_CB_COOLDOWN_S:
        # Cooldown expired — let the next probe through (HALF_OPEN).
        _brasilapi_cb_state["opened_at"] = 0.0
        _brasilapi_cb_state["consecutive_failures"] = 0
        return False
    return True


def _brasilapi_cb_record_failure() -> None:
    _brasilapi_cb_state["consecutive_failures"] += 1
    if _brasilapi_cb_state["consecutive_failures"] >= _BRASILAPI_CB_THRESHOLD:
        _brasilapi_cb_state["opened_at"] = time.time()
        logger.warning(
            "STORY-417: BrasilAPI CB OPEN after %d consecutive failures",
            _brasilapi_cb_state["consecutive_failures"],
        )


def _brasilapi_cb_record_success() -> None:
    _brasilapi_cb_state["consecutive_failures"] = 0
    _brasilapi_cb_state["opened_at"] = 0.0


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ContratoPublico(BaseModel):
    orgao: str
    orgao_cnpj: Optional[str] = None
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


class EditaisAmostra(BaseModel):
    orgao: str
    descricao: str
    valor_estimado: Optional[float] = None
    data_encerramento: Optional[str] = None
    uf: Optional[str] = None
    modalidade: Optional[str] = None


class PerfilB2GResponse(BaseModel):
    empresa: EmpresaInfo
    contratos: list[ContratoPublico]
    score: str  # "ATIVO" | "INICIANTE" | "SEM_HISTORICO"
    setor_detectado: str
    setor_nome: str
    editais_abertos_setor: int
    editais_amostra: list[EditaisAmostra] = []
    total_contratos_24m: int
    valor_total_24m: float
    ufs_atuacao: list[str]
    aviso_legal: str
    # STORY-417: "ok" when BrasilAPI returned data; "unavailable" when
    # the circuit breaker is open or the call timed out. The frontend
    # uses this to render a partial/degraded company card instead of a
    # hard 502.
    brasilapi_status: str = "ok"


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

class BrasilAPIUnavailable(Exception):
    """STORY-417: BrasilAPI is unavailable (timeout / 5xx / CB open)."""


async def _fetch_brasilapi(cnpj: str) -> dict:
    """Fetch company data from BrasilAPI (public, no auth).

    STORY-417: adds a 3-state failure handling:
      * 404 → surface as HTTP 404 (CNPJ truly not found).
      * transient (timeout, 5xx, CB open) → raise ``BrasilAPIUnavailable``
        so the caller can fall back to a partial response.
      * 200 → record success, return payload.
    """
    if _brasilapi_cb_should_skip():
        logger.warning("STORY-417: BrasilAPI CB open — skipping call for %s", cnpj)
        raise BrasilAPIUnavailable("BrasilAPI CB OPEN")

    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    try:
        async with httpx.AsyncClient(timeout=_BRASILAPI_TIMEOUT) as client:
            resp = await client.get(url)
    except (httpx.TimeoutException, httpx.TransportError) as e:
        _brasilapi_cb_record_failure()
        logger.warning("STORY-417: BrasilAPI transport error for %s: %s", cnpj, e)
        raise BrasilAPIUnavailable(f"BrasilAPI transport error: {e}")

    if resp.status_code == 404:
        # 404 is a meaningful business signal, not a transport failure —
        # it must surface as HTTP 404 to the client and must NOT advance
        # the CB counter (otherwise a burst of bad CNPJs would trip us).
        raise HTTPException(status_code=404, detail="CNPJ não encontrado na base de dados")

    if resp.status_code >= 500:
        _brasilapi_cb_record_failure()
        logger.warning("BrasilAPI 5xx %d for %s", resp.status_code, cnpj)
        raise BrasilAPIUnavailable(f"BrasilAPI {resp.status_code}")

    if resp.status_code != 200:
        logger.warning("BrasilAPI error %d for %s", resp.status_code, cnpj)
        raise HTTPException(status_code=502, detail="Erro ao consultar dados da empresa")

    _brasilapi_cb_record_success()
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

                    orgao_cnpj_raw = orgao.get("cnpjCompra") or orgao.get("cnpj") or ""
                    orgao_cnpj_clean = re.sub(r"\D", "", orgao_cnpj_raw) or None

                    matched.append({
                        "orgao": unidade.get("nomeUnidade", "") or orgao.get("razaoSocial", "Não informado"),
                        "orgao_cnpj": orgao_cnpj_clean,
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

    url = "https://api.portaldatransparencia.gov.br/api-de-dados/contratos/cpf-cnpj"
    params = {"cpfCnpj": cnpj, "pagina": 1}
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
# Local Supabase index — primary source for supplier contracts (all spheres)
# ---------------------------------------------------------------------------

async def _fetch_contratos_local(cnpj: str) -> tuple[list[dict], str]:
    """Query pncp_supplier_contracts table — O(1) lookup by ni_fornecedor index.

    Primary source covering all government spheres (Federal, Estadual, Municipal,
    Distrital) once the contracts crawler has populated the table.

    Falls back to Portal da Transparência (federal only, Fase 0 fix) when the
    table is empty or the feature is not yet populated.

    Returns:
        (contracts_list, fonte_label)
    """
    import os
    if os.getenv("CONTRACTS_INGESTION_ENABLED", "true").lower() not in ("true", "1"):
        return await _fetch_contratos_pt_normalized(cnpj), "PT"

    try:
        from supabase_client import get_supabase
        sb = get_supabase()

        cutoff = (datetime.now(timezone.utc) - timedelta(days=730)).date().isoformat()

        resp = (
            sb.table("pncp_supplier_contracts")
            .select("orgao_cnpj,orgao_nome,uf,esfera,valor_global,data_assinatura,objeto_contrato")
            .eq("ni_fornecedor", cnpj)
            .eq("is_active", True)
            .gte("data_assinatura", cutoff)
            .order("data_assinatura", desc=True)
            .limit(20)
            .execute()
        )

        if resp.data:
            logger.debug("[Perfil] Local DB: %d contracts for %s", len(resp.data), cnpj)
            return resp.data, "PNCP_LOCAL"

    except Exception as exc:
        logger.warning("[Perfil] Local DB query failed for %s: %s", cnpj, exc)

    # Fallback to Portal da Transparência (federal contracts only)
    return await _fetch_contratos_pt_normalized(cnpj), "PT"


async def _fetch_contratos_pt_normalized(cnpj: str) -> list[dict]:
    """Fetch and normalize Portal da Transparência contracts (federal only)."""
    raw = await _fetch_contratos_pt(cnpj)
    result = []
    for c in raw:
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
        result.append({
            "orgao": orgao_data.get("nome") or orgao_data.get("nomeOrgao") or "Não informado",
            "valor": valor,
            "data_inicio": data_inicio,
            "descricao": descricao,
            "esfera": "Federal",
            "uf": orgao_data.get("uf") or "",
        })
    return result


# ---------------------------------------------------------------------------
# Datalake — open bids count
# ---------------------------------------------------------------------------

async def _fetch_editais_abertos(setor_id: str, uf: str) -> tuple[int, list[dict]]:
    """Count + sample open bids in detected sector/UF from datalake (last 30 days).

    Returns (count, sample) where sample contains up to 5 bid dicts.
    No extra API call — same single query_datalake call as before.
    """
    try:
        from datalake_query import query_datalake

        sector = SECTORS.get(setor_id)
        if not sector:
            return 0, []

        now = datetime.now(timezone.utc)
        results = await query_datalake(
            ufs=[uf],
            data_inicial=(now - timedelta(days=30)).strftime("%Y-%m-%d"),
            data_final=now.strftime("%Y-%m-%d"),
            keywords=list(sector.keywords),
            limit=2000,
        )
        return len(results), results[:5]
    except Exception as e:
        logger.warning("Datalake fetch failed for %s/%s: %s", setor_id, uf, e)
        return 0, []


def _to_edital_amostra(bid: dict) -> dict:
    """Map a normalized datalake bid to EditaisAmostra fields."""
    desc = bid.get("objetoCompra") or "Sem descrição"
    if len(desc) > 200:
        desc = desc[:197] + "..."
    data_enc = bid.get("dataEncerramentoProposta")
    if data_enc and len(data_enc) > 10:
        data_enc = data_enc[:10]
    valor = bid.get("valorTotalEstimado")
    return {
        "orgao": bid.get("nomeOrgao") or "Não informado",
        "descricao": desc,
        "valor_estimado": float(valor) if valor is not None else None,
        "data_encerramento": data_enc,
        "uf": bid.get("uf"),
        "modalidade": bid.get("modalidadeNome"),
    }


# ---------------------------------------------------------------------------
# Build profile
# ---------------------------------------------------------------------------

async def _build_perfil(cnpj: str) -> dict:
    # 1. Company data — STORY-417: if BrasilAPI is unavailable we fall
    # through with placeholder company fields and a ``brasilapi_status``
    # flag in the response. The rest of the profile (contracts + open
    # bids) is still valuable even without company metadata, and the
    # frontend can render a degraded card instead of crashing with 502.
    brasilapi_status = "ok"
    try:
        bapi = await _fetch_brasilapi(cnpj)
    except BrasilAPIUnavailable as e:
        logger.warning("STORY-417: BrasilAPI unavailable for %s: %s", cnpj, e)
        bapi = {}
        brasilapi_status = "unavailable"

    razao_social = bapi.get("razao_social") or bapi.get("nome_fantasia") or "Empresa"
    cnae_raw = bapi.get("cnae_fiscal") or bapi.get("cnae_fiscal_principal") or ""
    cnae_str = str(cnae_raw)
    porte_raw = bapi.get("porte") or bapi.get("descricao_porte") or ""
    uf = bapi.get("uf") or ""
    situacao = bapi.get("descricao_situacao_cadastral") or bapi.get("situacao_cadastral") or ""

    # 2. Detect sector from CNAE
    setor_id = map_cnae_to_setor(cnae_str)
    setor_nome = get_setor_name(setor_id)

    # 3. Contracts — Local Supabase index (primary), PT API fallback (federal only)
    contratos_all, fonte = await _fetch_contratos_local(cnpj)

    ufs_set: set[str] = set()
    valor_total = 0.0
    contratos_parsed: list[dict] = []

    for c in contratos_all:
        uf_contrato = c.get("uf") or ""
        if uf_contrato:
            ufs_set.add(uf_contrato)
        if c.get("valor"):
            try:
                valor_total += float(c["valor"])
            except (ValueError, TypeError):
                pass
        contratos_parsed.append({
            "orgao": c.get("orgao") or c.get("orgao_nome") or "Não informado",
            "orgao_cnpj": c.get("orgao_cnpj") or None,
            "valor": c.get("valor") or c.get("valor_global"),
            "data_inicio": c.get("data_inicio") or c.get("data_assinatura"),
            "descricao": c.get("descricao") or c.get("objeto_contrato") or "Sem descrição",
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
    if uf:
        editais_count, editais_raw = await _fetch_editais_abertos(setor_id, uf)
    else:
        editais_count, editais_raw = 0, []

    editais_amostra = [_to_edital_amostra(b) for b in editais_raw[:5]]

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
        "editais_amostra": editais_amostra,
        "total_contratos_24m": total_24m,
        "valor_total_24m": round(valor_total, 2),
        "ufs_atuacao": sorted(ufs_set),
        "aviso_legal": "Dados de fontes públicas: CNPJ aberto (BrasilAPI) e PNCP/Portal da Transparência.",
        # STORY-417: expose upstream availability so the frontend can
        # render a "company info temporariamente indisponível" banner
        # instead of the usual full-detail card.
        "brasilapi_status": brasilapi_status,
    }
