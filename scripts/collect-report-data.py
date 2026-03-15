#!/usr/bin/env python3
"""
Coleta determinística de dados para o relatório B2G.

Faz TODAS as chamadas de API de forma determinística, com tratamento
explícito de falhas. Cada dado recebe um campo `_source`:
  - "API"          → dado obtido com sucesso via API
  - "API_PARTIAL"  → resposta parcial (timeout, paginação incompleta)
  - "API_FAILED"   → chamada falhou após retries
  - "CALCULATED"   → dado calculado localmente (ex: distância OSRM)
  - "UNAVAILABLE"  → fonte não disponível / não implementada

Usage:
    python scripts/collect-report-data.py --cnpj 12345678000190
    python scripts/collect-report-data.py --cnpj 12.345.678/0001-90 --output data.json
    python scripts/collect-report-data.py --cnpj 12345678000190 --dias 30 --ufs SC,PR

Requires:
    pip install httpx pyyaml
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)


# ============================================================
# CONSTANTS
# ============================================================

PNCP_BASE = "https://pncp.gov.br/api/consulta/v1"
PNCP_FILES_BASE = "https://pncp.gov.br/api/pncp/v1"
PCP_BASE = "https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos"
QD_BASE = "https://api.queridodiario.ok.org.br/gazettes"
OPENCNPJ_BASE = "https://api.opencnpj.org"
PT_BASE = "https://api.portaldatransparencia.gov.br/api-de-dados"
OSRM_BASE = "http://router.project-osrm.org/route/v1/driving"
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"
BRASILAPI_BASE = "https://brasilapi.com.br/api/cnpj/v1"
IBGE_LOCALIDADES = "https://servicodados.ibge.gov.br/api/v1/localidades"
IBGE_SIDRA = "https://apisidra.ibge.gov.br/values"

# PNCP modalidades relevantes para construção
MODALIDADES = {
    4: "Concorrência",
    5: "Pregão Eletrônico",
    6: "Pregão Presencial",
    8: "Inexigibilidade",
}

PNCP_MAX_PAGE_SIZE = 50
PNCP_MAX_PAGES = 10
PCP_PAGE_SIZE = 10
PCP_MAX_PAGES = 20

MAX_RETRIES = 3
RETRY_BACKOFF = [1.0, 3.0, 8.0]
REQUEST_TIMEOUT = 30.0

# ============================================================
# HELPERS
# ============================================================

def _clean_cnpj(cnpj: str) -> str:
    """Remove formatting from CNPJ, return 14 digits."""
    return re.sub(r"[^0-9]", "", cnpj).zfill(14)


def _format_cnpj(cnpj14: str) -> str:
    """Format 14-digit CNPJ as XX.XXX.XXX/XXXX-XX."""
    c = cnpj14
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"


def _today() -> datetime:
    return datetime.now(timezone.utc)


def _date_br(dt: datetime) -> str:
    """DD/MM/YYYY format."""
    return dt.strftime("%d/%m/%Y")


def _date_iso(dt: datetime) -> str:
    """YYYY-MM-DD format."""
    return dt.strftime("%Y-%m-%d")


def _date_compact(dt: datetime) -> str:
    """YYYYMMDD format."""
    return dt.strftime("%Y%m%d")


def _safe_float(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        if isinstance(v, str):
            v = v.replace(",", ".")
        return float(v)
    except (ValueError, TypeError):
        return default


def _source_tag(status: str, detail: str = "") -> dict:
    """Create a _source metadata tag."""
    tag = {"status": status, "timestamp": _date_iso(_today())}
    if detail:
        tag["detail"] = detail
    return tag


# ============================================================
# HTTP CLIENT WITH RETRY
# ============================================================

class ApiClient:
    """Simple HTTP client with retry and logging."""

    def __init__(self, verbose: bool = True):
        self.client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "SmartLic-ReportCollector/1.0"},
        )
        self.verbose = verbose
        self.stats = {"calls": 0, "success": 0, "failed": 0, "retries": 0}

    def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        label: str = "",
    ) -> tuple[dict | list | None, str]:
        """
        GET request with retry. Returns (data, source_status).
        source_status is "API" on success, "API_FAILED" on failure.
        """
        self.stats["calls"] += 1
        display = label or url[:80]

        for attempt in range(MAX_RETRIES):
            try:
                if self.verbose and attempt == 0:
                    print(f"  → {display}", end="", flush=True)

                resp = self.client.get(url, params=params, headers=headers)

                if resp.status_code == 200:
                    self.stats["success"] += 1
                    if self.verbose:
                        print(f" ✓ ({resp.status_code})")
                    try:
                        return resp.json(), "API"
                    except Exception:
                        return None, "API_FAILED"

                if resp.status_code in (429, 500, 502, 503, 504, 422):
                    self.stats["retries"] += 1
                    wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                    if self.verbose:
                        print(f" ⟳ {resp.status_code}, retry in {wait}s", end="", flush=True)
                    time.sleep(wait)
                    continue

                # Non-retryable error
                self.stats["failed"] += 1
                if self.verbose:
                    print(f" ✗ ({resp.status_code})")
                return None, "API_FAILED"

            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
                self.stats["retries"] += 1
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                if self.verbose:
                    err_type = type(e).__name__
                    print(f" ⟳ {err_type}, retry in {wait}s", end="", flush=True)
                time.sleep(wait)
                continue

        self.stats["failed"] += 1
        if self.verbose:
            print(f" ✗ (max retries)")
        return None, "API_FAILED"

    def head(self, url: str, label: str = "") -> int | None:
        """HEAD request, returns status code or None."""
        try:
            resp = self.client.head(url, timeout=10.0)
            return resp.status_code
        except Exception:
            return None

    def print_stats(self):
        s = self.stats
        print(f"\n📊 API Stats: {s['calls']} calls, {s['success']} success, "
              f"{s['failed']} failed, {s['retries']} retries")

    def close(self):
        self.client.close()


# ============================================================
# PHASE 1: COMPANY PROFILE
# ============================================================

def collect_opencnpj(api: ApiClient, cnpj14: str) -> dict:
    """Fetch company data from OpenCNPJ."""
    print("\n📋 Phase 1a: OpenCNPJ — Perfil da empresa")
    data, status = api.get(
        f"{OPENCNPJ_BASE}/{cnpj14}",
        label=f"OpenCNPJ {cnpj14}",
    )
    if not data or status != "API":
        return {
            "_source": _source_tag("API_FAILED", "OpenCNPJ indisponível"),
            "cnpj": _format_cnpj(cnpj14),
        }

    # Parse capital_social (string with comma: "1232000,00")
    capital = _safe_float(data.get("capital_social"))

    # Parse QSA
    qsa_raw = data.get("QSA") or data.get("qsa") or []
    qsa = []
    for s in qsa_raw:
        if isinstance(s, dict):
            qsa.append({
                "nome": s.get("nome_socio") or s.get("nome", ""),
                "qualificacao": s.get("qualificacao_socio") or s.get("qualificacao", ""),
            })

    # Parse telefones
    tel_raw = data.get("telefones") or []
    telefones = []
    for t in tel_raw:
        if isinstance(t, dict):
            ddd = t.get("ddd", "")
            num = t.get("numero", "")
            if ddd and num:
                telefones.append(f"({ddd}) {num}")
        elif isinstance(t, str):
            telefones.append(t)

    # CNAEs secundários
    cnaes_sec_raw = data.get("cnaes_secundarios") or []
    if isinstance(cnaes_sec_raw, list):
        cnaes_sec = ", ".join(str(c) for c in cnaes_sec_raw[:20])
    else:
        cnaes_sec = str(cnaes_sec_raw)

    cnae_principal = data.get("cnae_fiscal") or data.get("cnae_principal") or ""
    cnae_desc = data.get("cnae_fiscal_descricao") or data.get("cnae_principal_descricao") or ""
    if cnae_principal and cnae_desc:
        cnae_full = f"{cnae_principal} - {cnae_desc}"
    elif cnae_principal:
        cnae_full = str(cnae_principal)
    else:
        cnae_full = ""

    return {
        "_source": _source_tag("API"),
        "cnpj": _format_cnpj(cnpj14),
        "razao_social": data.get("razao_social", ""),
        "nome_fantasia": data.get("nome_fantasia") or data.get("razao_social", ""),
        "cnae_principal": cnae_full,
        "cnaes_secundarios": cnaes_sec,
        "porte": data.get("porte") or data.get("descricao_porte") or "",
        "capital_social": capital,
        "cidade_sede": data.get("municipio") or data.get("cidade", ""),
        "uf_sede": data.get("uf") or "",
        "situacao_cadastral": data.get("situacao_cadastral") or data.get("descricao_situacao_cadastral") or "",
        "data_inicio_atividade": data.get("data_inicio_atividade") or "",
        "natureza_juridica": data.get("natureza_juridica") or data.get("descricao_natureza_juridica") or "",
        "email": data.get("email") or "",
        "telefones": telefones,
        "qsa": qsa,
    }


def collect_portal_transparencia(api: ApiClient, cnpj14: str, pt_key: str) -> dict:
    """Fetch sanctions + contract history from Portal da Transparência."""
    print("\n📋 Phase 1b: Portal da Transparência — Sanções e contratos")
    result = {
        "sancoes": {"ceis": False, "cnep": False, "cepim": False, "ceaf": False},
        "sancoes_source": _source_tag("UNAVAILABLE", "Sem chave API"),
        "historico_contratos": [],
        "historico_source": _source_tag("UNAVAILABLE", "Sem chave API"),
    }

    if not pt_key:
        print("  ⚠ PORTAL_TRANSPARENCIA_API_KEY não configurada — pulando")
        return result

    headers = {"chave-api-dados": pt_key}

    # Sanções
    data, status = api.get(
        f"{PT_BASE}/pessoa-juridica",
        params={"cnpj": cnpj14},
        headers=headers,
        label="Portal Transparência — sanções",
    )
    if status == "API" and data:
        items = data if isinstance(data, list) else [data]
        for item in items:
            for key in ["ceis", "cnep", "cepim", "ceaf"]:
                val = item.get(key) or item.get(key.upper())
                if val and str(val).lower() not in ("false", "0", "none", "null", "[]", "{}"):
                    result["sancoes"][key] = True
        result["sancoes_source"] = _source_tag("API")
    elif status == "API_FAILED":
        result["sancoes_source"] = _source_tag("API_FAILED", "Consulta de sanções falhou")

    # Contratos
    data, status = api.get(
        f"{PT_BASE}/contratos/cpf-cnpj",
        params={"cpfCnpj": cnpj14, "pagina": 1},
        headers=headers,
        label="Portal Transparência — contratos",
    )
    if status == "API" and data is not None:
        items = data if isinstance(data, list) else data.get("data", data.get("contratos", []))
        if isinstance(items, list):
            for c in items[:20]:
                result["historico_contratos"].append({
                    "orgao": c.get("orgaoVinculado", {}).get("nome", "") or c.get("orgao", ""),
                    "valor": _safe_float(c.get("valorFinal") or c.get("valor") or c.get("valorInicial")),
                    "data": c.get("dataInicioVigencia") or c.get("dataAssinatura") or "",
                    "objeto": c.get("objeto", "")[:200],
                })
        n = len(result["historico_contratos"])
        detail = f"{n} contrato(s) federal(is) identificado(s)" if n > 0 else "Nenhum contrato federal identificado"
        result["historico_source"] = _source_tag("API", detail)
    elif status == "API_FAILED":
        result["historico_source"] = _source_tag("API_FAILED", "Consulta de contratos falhou")

    return result


def collect_brasilapi(api: ApiClient, cnpj14: str) -> dict:
    """Fetch Simples Nacional status + fallback company data from BrasilAPI."""
    print("\n  BrasilAPI — Simples Nacional")
    data, status = api.get(f"{BRASILAPI_BASE}/{cnpj14}", label=f"BrasilAPI {cnpj14}")
    if not data or status != "API":
        return {"_source": _source_tag("API_FAILED", "BrasilAPI indisponivel"), "simples_nacional": None, "mei": None}
    return {
        "_source": _source_tag("API"),
        "simples_nacional": data.get("opcao_pelo_simples"),
        "mei": data.get("opcao_pelo_mei"),
        "data_opcao_simples": data.get("data_opcao_pelo_simples", ""),
        "data_exclusao_simples": data.get("data_exclusao_do_simples", ""),
        "porte_fallback": data.get("porte", ""),
    }


_ibge_cache: dict = {}  # UF -> {nome_normalizado: cod_ibge}


def _normalize_municipio(nome: str) -> str:
    import unicodedata
    nome = unicodedata.normalize("NFD", nome.lower())
    return "".join(c for c in nome if unicodedata.category(c) != "Mn").strip()


def _get_cod_ibge(api: ApiClient, municipio: str, uf: str) -> int | None:
    uf = uf.upper()
    if uf not in _ibge_cache:
        data, status = api.get(f"{IBGE_LOCALIDADES}/estados/{uf}/municipios", label=f"IBGE localidades {uf}")
        if status == "API" and isinstance(data, list):
            _ibge_cache[uf] = {_normalize_municipio(m.get("nome", "")): m.get("id") for m in data}
        else:
            _ibge_cache[uf] = {}
    return _ibge_cache.get(uf, {}).get(_normalize_municipio(municipio))


def collect_ibge_municipio(api: ApiClient, municipio: str, uf: str) -> dict:
    """Fetch population + GDP for a municipality from IBGE SIDRA."""
    cod = _get_cod_ibge(api, municipio, uf)
    if not cod:
        return {"_source": _source_tag("API_FAILED", f"Codigo IBGE nao encontrado: {municipio}/{uf}"), "populacao": None, "pib_mil_reais": None}

    result: dict = {"cod_ibge": cod}

    # Population (tabela 6579)
    data, status = api.get(f"{IBGE_SIDRA}/t/6579/n6/{cod}/v/9324/p/last", label=f"IBGE pop {municipio}")
    if status == "API" and isinstance(data, list) and len(data) > 1:
        try:
            result["populacao"] = int(data[1].get("V", 0))
        except (ValueError, IndexError):
            result["populacao"] = None
    else:
        result["populacao"] = None

    time.sleep(0.3)

    # GDP (tabela 5938)
    data, status = api.get(f"{IBGE_SIDRA}/t/5938/n6/{cod}/v/37/p/last", label=f"IBGE PIB {municipio}")
    if status == "API" and isinstance(data, list) and len(data) > 1:
        try:
            result["pib_mil_reais"] = float(data[1].get("V", 0))
        except (ValueError, IndexError):
            result["pib_mil_reais"] = None
    else:
        result["pib_mil_reais"] = None

    # Derived
    if result.get("populacao") and result.get("pib_mil_reais"):
        result["pib_per_capita"] = round((result["pib_mil_reais"] * 1000) / result["populacao"], 2)
    else:
        result["pib_per_capita"] = None

    has_any = result.get("populacao") or result.get("pib_mil_reais")
    result["_source"] = _source_tag("API" if has_any else "API_FAILED", f"pop={'OK' if result.get('populacao') else 'N/A'}, pib={'OK' if result.get('pib_mil_reais') else 'N/A'}")
    return result


def collect_pncp_contratos_fornecedor(api: ApiClient, cnpj14: str) -> tuple[list[dict], dict]:
    """Fetch contract history from PNCP by supplier CNPJ.

    Covers ALL spheres: federal, state, municipal, autarchies, foundations.
    PNCP /contratos allows max 365-day window, so we query 2 consecutive years.
    """
    print("\n📋 Phase 1c: PNCP — Histórico de contratos do fornecedor (todas as esferas)")

    all_contracts: list[dict] = []
    errors = 0

    esfera_labels = {"F": "Federal", "E": "Estadual", "M": "Municipal", "D": "Distrital"}

    # Query 2 windows of 365 days each (covers ~2 years)
    today = _today()
    windows = [
        (_date_compact(today - timedelta(days=365)), _date_compact(today)),
        (_date_compact(today - timedelta(days=730)), _date_compact(today - timedelta(days=366))),
    ]

    for data_ini, data_fim in windows:
        page = 1
        while page <= 10:  # Max 10 pages per window
            data, status = api.get(
                f"{PNCP_BASE}/contratos",
                params={
                    "cnpjFornecedor": cnpj14,
                    "dataInicial": data_ini,
                    "dataFinal": data_fim,
                    "pagina": page,
                    "tamanhoPagina": 50,
                },
                label=f"PNCP contratos fornecedor p={page}",
            )
            if status != "API" or not data:
                if status == "API_FAILED":
                    errors += 1
                break

            items = data.get("data", data) if isinstance(data, dict) else data
            if not isinstance(items, list) or not items:
                break

            for c in items:
                orgao = c.get("orgaoEntidade", {})
                unidade = c.get("unidadeOrgao", {})
                esfera_id = orgao.get("esferaId", "")
                esfera = esfera_labels.get(esfera_id, esfera_id)

                all_contracts.append({
                    "orgao": unidade.get("nomeUnidade", "") or orgao.get("razaoSocial", ""),
                    "esfera": esfera,
                    "uf": unidade.get("ufSigla", ""),
                    "municipio": unidade.get("municipioNome", ""),
                    "valor": _safe_float(c.get("valorGlobal") or c.get("valorInicial")),
                    "data": c.get("dataAssinatura", ""),
                    "objeto": (c.get("objetoContrato") or c.get("informacaoComplementar") or "")[:300],
                    "numero_contrato": c.get("numeroContratoEmpenho", ""),
                    "vigencia_fim": c.get("dataVigenciaFim", ""),
                    "fonte": "PNCP",
                    "valor_aditivos": _safe_float(c.get("valorAcumuladoAditivos")),
                    "tipo_contrato": c.get("tipoContratoNome", ""),
                    "situacao_contrato": c.get("situacaoContratoCodigo", ""),
                    "tem_subcontratacao": c.get("subcontratacao", False),
                })

            # Pagination
            total_pages = data.get("totalPaginas", 1) if isinstance(data, dict) else 1
            if page >= total_pages:
                break
            page += 1
            time.sleep(0.5)

    # Dedup by (orgao, numero_contrato, data)
    seen = set()
    unique = []
    for c in all_contracts:
        key = (c["orgao"][:30], c["numero_contrato"], c["data"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    all_contracts = unique

    # Stats
    by_esfera = {}
    for c in all_contracts:
        e = c.get("esfera", "N/I")
        by_esfera[e] = by_esfera.get(e, 0) + 1

    n = len(all_contracts)
    detail_parts = [f"{n} contrato(s) encontrado(s)"]
    for esfera, count in sorted(by_esfera.items()):
        detail_parts.append(f"{count} {esfera.lower()}")

    status_tag = "API" if errors == 0 else ("API_PARTIAL" if n > 0 else "API_FAILED")
    source = _source_tag(status_tag, ", ".join(detail_parts))

    print(f"  PNCP contratos: {n} encontrados ({', '.join(f'{v} {k}' for k, v in by_esfera.items())})")
    return all_contracts, source


# ============================================================
# ACTIVITY CLUSTERING (replaces flat keyword extraction)
# ============================================================

_ACTIVITY_CATEGORIES: dict[str, dict] = {
    "engenharia": {
        "label": "Engenharia e Obras",
        "prefixes": ["construç", "construc", "edifici", "obra", "paviment", "infraestrutura",
                      "urbaniz", "drenag", "terrapl", "reforma", "saneamento", "fundaç"],
        "search_keywords": ["obra", "construção", "pavimentação", "reforma", "engenharia",
                           "edificação", "drenagem", "terraplanagem", "saneamento"],
    },
    "saude": {
        "label": "Saúde e Materiais Hospitalares",
        "prefixes": ["medicament", "hospitalar", "odontol", "ambulatori", "farmac",
                      "laborat", "cirúrg", "cirurg", "curativ", "fórmula", "formula",
                      "insumos hospitalar", "saúde", "saude"],
        "search_keywords": ["hospitalar", "medicamento", "odontológico", "ambulatorial",
                           "farmacêutico", "laboratorial", "cirúrgico", "saúde"],
    },
    "alimentacao": {
        "label": "Alimentação e Gêneros Alimentícios",
        "prefixes": ["aliment", "merenda", "refeic", "refeição", "nutriç", "nutric",
                      "gêneros", "generos", "hortifrut", "cesta", "panific", "café",
                      "pnae", "buffet"],
        "search_keywords": ["gêneros alimentícios", "merenda escolar", "alimentação",
                           "refeição", "nutrição", "hortifruti", "cesta básica"],
    },
    "limpeza_saneantes": {
        "label": "Saneantes e Produtos de Limpeza",
        "prefixes": ["saneant", "limpeza", "higien", "desinfet", "detergent",
                      "descartáv", "descartav", "álcool", "alcool"],
        "search_keywords": ["saneantes", "limpeza", "higienização", "descartáveis",
                           "desinfetante", "álcool"],
    },
    "expediente_escolar": {
        "label": "Material de Expediente e Escolar",
        "prefixes": ["expedient", "escolar", "caderno", "papéi", "papei", "papel",
                      "didátic", "didatic", "artesanat"],
        "search_keywords": ["material expediente", "material escolar", "papelaria",
                           "material didático"],
    },
    "informatica": {
        "label": "Informática e Tecnologia",
        "prefixes": ["informátic", "informatic", "computador", "hardware", "software",
                      "impressão", "impressao", "suprimento", "toner", "cartucho"],
        "search_keywords": ["informática", "computador", "equipamento TI", "software"],
    },
    "moveis_eletro": {
        "label": "Móveis e Eletrodomésticos",
        "prefixes": ["móve", "move", "mobili", "eletrodoméstic", "eletrodomestic",
                      "condicionado", "refrigerad", "fogão", "fogao"],
        "search_keywords": ["móveis", "eletrodomésticos", "ar condicionado", "mobiliário"],
    },
    "veiculos": {
        "label": "Veículos e Transporte",
        "prefixes": ["veícul", "veicul", "automotiv", "pneu", "combustív", "combustiv",
                      "ambulânci", "ambulanci", "transporte", "frete", "locação veícul"],
        "search_keywords": ["veículo", "pneu", "combustível", "ambulância", "transporte"],
    },
    "vestuario": {
        "label": "Vestuário e Uniformes",
        "prefixes": ["vestuári", "vestuari", "uniforme", "fardament", "jaleco",
                      "confecç", "confeccao", "calçado", "calcado"],
        "search_keywords": ["uniforme", "vestuário", "fardamento", "confecção", "calçado"],
    },
    "vigilancia": {
        "label": "Vigilância e Segurança",
        "prefixes": ["vigilânci", "vigilanci", "segurança", "seguranca", "monitoramento",
                      "alarme", "câmera", "camera", "cftv"],
        "search_keywords": ["vigilância", "segurança", "monitoramento", "CFTV"],
    },
    "manutencao": {
        "label": "Manutenção Predial e Elétrica",
        "prefixes": ["manutenção predial", "manutencao predial", "elétr", "eletr",
                      "hidráulic", "hidraulic", "encanamento", "instalações", "instalacoes"],
        "search_keywords": ["manutenção predial", "instalação elétrica", "hidráulica"],
    },
    "consultoria": {
        "label": "Consultoria e Assessoria",
        "prefixes": ["consultori", "assessori", "perícia", "pericia", "laudo",
                      "auditoria", "contábil", "contabil", "jurídic", "juridic"],
        "search_keywords": ["consultoria", "assessoria", "auditoria", "perícia"],
    },
    "comunicacao": {
        "label": "Comunicação e Publicidade",
        "prefixes": ["publicidad", "comunicaçã", "comunicaca", "gráfic", "grafic",
                      "impressão gráfic", "banner", "sinaliz"],
        "search_keywords": ["publicidade", "comunicação", "sinalização", "material gráfico"],
    },
    "residuos": {
        "label": "Resíduos e Meio Ambiente",
        "prefixes": ["resíduo", "residuo", "coleta seletiv", "reciclage", "ambiental",
                      "licenciamento ambiental", "descontaminaç"],
        "search_keywords": ["resíduos", "coleta seletiva", "meio ambiente", "reciclagem"],
    },
    "eventos": {
        "label": "Eventos e Locação",
        "prefixes": ["evento", "locação", "locacao", "tendas", "palco", "sonorizaç",
                      "sonorizac", "buffet", "coffee"],
        "search_keywords": ["evento", "locação", "tendas", "sonorização"],
    },
    "alienacao": {
        "label": "Alienação e Leilão",
        "prefixes": ["alienação", "alienacao", "mercadorias apreendida", "leilão", "leilao",
                      "arrematação", "arremataçao"],
        "search_keywords": ["alienação", "mercadorias apreendidas", "leilão"],
    },
}


def cluster_contract_activities(
    contratos: list[dict],
    max_clusters: int = 5,
    min_share_pct: float = 3.0,
) -> list[dict]:
    """Cluster historical contracts into thematic activity groups.

    Returns list of dicts, each:
    {
        "label": "Materiais Hospitalares",
        "category_key": "saude",
        "count": 266,
        "share_pct": 26.5,
        "keywords": ["hospitalar", "odontológico", "ambulatorial"],
        "sample_objects": ["Medicamentos Suplementos Alimentares Correlatos", ...],
    }
    Sorted by count descending. Max max_clusters clusters.
    Only clusters with >= min_share_pct% of contracts are returned.
    """
    if not contratos:
        return []

    n = len(contratos)
    category_contracts: dict[str, list[dict]] = {k: [] for k in _ACTIVITY_CATEGORIES}
    unmatched: list[dict] = []

    # Phase 1: Dictionary classification via prefix matching
    for c in contratos:
        obj = (c.get("objeto") or "").lower()
        matched = False
        for cat_key, cat_def in _ACTIVITY_CATEGORIES.items():
            if any(prefix in obj for prefix in cat_def["prefixes"]):
                category_contracts[cat_key].append(c)
                matched = True
                break  # First match wins (categories ordered by specificity)
        if not matched:
            unmatched.append(c)

    # Phase 2: Frequency extraction on unmatched (using FIXED min_freq)
    unmatched_keywords: list[str] = []
    if unmatched:
        unmatched_keywords = _extract_keywords_flat(unmatched, max_keywords=15)
        if unmatched_keywords:
            category_contracts["_outros"] = unmatched

    # Phase 3: Build clusters
    clusters: list[dict] = []
    for cat_key, contracts in category_contracts.items():
        if not contracts:
            continue
        share = 100.0 * len(contracts) / n
        if share < min_share_pct:
            continue

        cat_def = _ACTIVITY_CATEGORIES.get(cat_key, {})

        # Extract top 3 sample objects
        obj_counter = Counter(c.get("objeto", "")[:60] for c in contracts)
        samples = [obj for obj, _ in obj_counter.most_common(3)]

        clusters.append({
            "label": cat_def.get("label", cat_key),
            "category_key": cat_key,
            "count": len(contracts),
            "share_pct": round(share, 1),
            "keywords": cat_def.get("search_keywords", unmatched_keywords if cat_key == "_outros" else []),
            "sample_objects": samples,
        })

    # Sort by count descending, cap at max_clusters
    clusters.sort(key=lambda x: -x["count"])
    return clusters[:max_clusters]


# ============================================================
# SECTOR MAPPING
# ============================================================

def _extract_keywords_flat(contratos: list[dict], max_keywords: int = 30) -> list[str]:
    """Extract high-frequency keywords from contract descriptions (internal helper).

    Used by cluster_contract_activities() Phase 2 for unmatched contracts,
    and as fallback via the backward-compat extract_keywords_from_contracts() wrapper.
    """
    if not contratos:
        return []

    n_contracts = len(contratos)

    # Adaptive min_freq: with few contracts, even freq=1 is a signal.
    # With many contracts, require higher frequency to filter noise.
    if n_contracts <= 3:
        min_freq = 1  # Accept any term that appears at least once
    elif n_contracts <= 8:
        min_freq = 2  # Appear in at least 2 contracts
    else:
        min_freq = min(10, max(2, n_contracts // 50))  # ~2% prevalence, cap at 10

    # MINIMAL stop words — ONLY bureaucratic/procedural terms.
    # Rule: if a word could appear in a bid search query, it is NOT a stop word.
    # "limpeza", "uniforme", "veículo", "saúde", "escolar" etc. are KEPT.
    _STOP_WORDS = {
        # Grammatical particles
        "para", "com", "dos", "das", "nos", "nas", "por", "uma", "num", "numa",
        "que", "como", "mais", "este", "esta", "estes", "estas", "esse", "essa",
        "aquele", "aquela", "entre", "cada", "todo", "toda", "todos", "todas",
        "sobre", "sob", "sem", "seu", "sua", "seus", "suas",
        "muito", "menos", "ainda",
        # Procurement procedural (never differentiate what is being bought)
        "contrato", "contratacao", "objeto", "referente", "relativo",
        "conforme", "mediante", "decorrente", "processo",
        # Modality names (not product descriptors)
        "pregao", "licitacao", "dispensa", "inexigibilidade", "concorrencia",
        # Legal entities
        "empresa", "ltda", "eireli", "cnpj",
        # Admin/payment
        "valor", "prazo", "vigencia", "pagamento", "parcela",
        # Government hierarchy
        "prefeitura", "governo", "secretaria", "ministerio", "departamento",
        # True filler (never useful as search keywords)
        "tipo", "diversos", "demais", "necessidades", "atender", "outros",
        # Dates
        "janeiro", "fevereiro", "marco", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
        "2024", "2025", "2026", "2023", "2022", "2021",
    }

    # Count word/bigram frequency across contract descriptions
    word_freq: dict[str, int] = {}
    bigram_freq: dict[str, int] = {}

    for c in contratos:
        obj = (c.get("objeto") or "").lower()
        obj = re.sub(r"[^a-záàâãéêíóôõúüç\s]", " ", obj)
        words = [w for w in obj.split() if len(w) >= 4 and w not in _STOP_WORDS]

        # Count unique words per contract (not total occurrences)
        seen_words: set[str] = set()
        for w in words:
            if w not in seen_words:
                word_freq[w] = word_freq.get(w, 0) + 1
                seen_words.add(w)

        # Bigrams (consecutive meaningful words)
        for i in range(len(words) - 1):
            bg = f"{words[i]} {words[i+1]}"
            if bg not in seen_words:
                bigram_freq[bg] = bigram_freq.get(bg, 0) + 1
                seen_words.add(bg)

    # Filter by adaptive minimum frequency and sort by relevance
    frequent_words = sorted(
        [(word, freq) for word, freq in word_freq.items() if freq >= min_freq],
        key=lambda x: -x[1],
    )
    frequent_bigrams = sorted(
        [(bg, freq) for bg, freq in bigram_freq.items() if freq >= min_freq],
        key=lambda x: -x[1],
    )

    # Phase 3 (commerce rescue): for supply/commerce companies, individual product
    # names appear in only 1 contract each (e.g., "detergente" in one, "desinfetante"
    # in another). These are valuable search terms but fail the min_freq filter.
    # Solution: collect freq=1 words that are NOT procedural/generic — they represent
    # the product specificity of the company.
    _GENERIC_WORDS = {
        "material", "materiais", "produtos", "itens", "compra", "aquisicao",
        "fornecimento", "prestacao", "servicos", "registro", "precos",
        "municipal", "estadual", "federal", "publica", "publico",
    }
    rare_but_specific = sorted(
        [(word, freq) for word, freq in word_freq.items()
         if freq == 1 and word not in _GENERIC_WORDS and len(word) >= 5],
        key=lambda x: x[0],  # alphabetical for stability
    )

    # Build result: bigrams first (most specific), then frequent words, then rare specifics.
    result: list[str] = []
    seen_terms: set[str] = set()

    # Layer 1: Frequent bigrams (highest signal — e.g. "merenda escolar", "material limpeza")
    for term, _freq in frequent_bigrams:
        if len(result) >= max_keywords:
            break
        if term not in seen_terms:
            result.append(term)
            seen_terms.add(term)

    # Layer 2: Frequent single words NOT already in a bigram
    bigram_words = set()
    for bg in result:
        bigram_words.update(bg.split())

    for word, _freq in frequent_words:
        if len(result) >= max_keywords:
            break
        if word not in seen_terms and word not in bigram_words:
            result.append(word)
            seen_terms.add(word)

    # Layer 3: Rare but specific product/service terms (commerce rescue layer)
    # Only added if we have room and haven't exceeded max_keywords.
    # Capped at 10 rare terms to avoid noise explosion.
    rare_added = 0
    for word, _freq in rare_but_specific:
        if len(result) >= max_keywords or rare_added >= 10:
            break
        if word not in seen_terms and word not in bigram_words:
            result.append(word)
            seen_terms.add(word)
            rare_added += 1

    return result


def extract_keywords_from_contracts(contratos: list[dict], max_keywords: int = 30) -> list[str]:
    """Backward-compatible wrapper — returns flat keyword list from clusters."""
    clusters = cluster_contract_activities(contratos)
    if not clusters:
        # No clusters formed — fall back to flat extraction directly
        return _extract_keywords_flat(contratos, max_keywords=max_keywords)
    result: list[str] = []
    seen: set[str] = set()
    for cluster in clusters:
        for kw in cluster["keywords"]:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                result.append(kw)
                seen.add(kw_lower)
            if len(result) >= max_keywords:
                return result
    return result


def extract_ufs_from_contracts(
    contratos: list[dict],
    uf_sede: str = "",
    max_ufs: int = 5,
    min_contracts: int = 3,
) -> tuple[list[str], dict]:
    """Derive target UFs from contract history (geographic intelligence).

    Same philosophy as extract_keywords_from_contracts: what the company
    ACTUALLY does (where it operates) is a better signal than where its
    headquarters is located.

    Returns:
        (ordered_ufs, metadata_dict) where:
        - ordered_ufs: list of UF codes ordered by contract count (descending),
          uf_sede always included even with 0 contracts there.
          Capped at max_ufs.
        - metadata_dict: {uf: count} for all UFs found, plus uf_sede entry.
    """
    if not contratos:
        return ([uf_sede] if uf_sede else []), {"uf_sede": uf_sede, "counts": {uf_sede: 0} if uf_sede else {}, "source": "fallback_sede"}

    # Count contracts per UF
    uf_counts: dict[str, int] = {}
    for c in contratos:
        uf = (c.get("uf") or "").upper().strip()
        if uf and len(uf) == 2:
            uf_counts[uf] = uf_counts.get(uf, 0) + 1

    if not uf_counts:
        return ([uf_sede] if uf_sede else []), {"uf_sede": uf_sede, "counts": {uf_sede: 0} if uf_sede else {}, "source": "fallback_sede"}

    # Adaptive min_contracts threshold (like keywords)
    n_total = sum(uf_counts.values())
    if n_total <= 5:
        effective_min = 1
    elif n_total <= 20:
        effective_min = 2
    else:
        effective_min = min(10, max(min_contracts, n_total // 100))  # ~1% prevalence, cap at 10

    # Filter UFs with enough contracts, sorted by count descending
    qualified = sorted(
        [(uf, cnt) for uf, cnt in uf_counts.items() if cnt >= effective_min],
        key=lambda x: -x[1],
    )

    result_ufs = [uf for uf, _cnt in qualified[:max_ufs]]

    # Ensure uf_sede is always included (even if 0 contracts there)
    if uf_sede and uf_sede.upper() not in [u.upper() for u in result_ufs]:
        result_ufs.append(uf_sede.upper())

    meta = {
        "uf_sede": uf_sede,
        "counts": dict(sorted(uf_counts.items(), key=lambda x: -x[1])),
        "effective_min": effective_min,
        "total_contracts": n_total,
        "source": "historico_contratos",
    }

    return result_ufs, meta


def map_sector(cnae_principal: str, sectors_path: str | None = None) -> tuple[str, list[str], str]:
    """Map CNAE to sector name, keywords, and sector_key from sectors_data.yaml.

    Returns: (sector_name, keywords_list, sector_key)
    sector_key is the YAML key (e.g. "engenharia", "software") used for margin lookup.
    """
    if not sectors_path:
        candidates = [
            Path("backend/sectors_data.yaml"),
            Path("../backend/sectors_data.yaml"),
            Path(__file__).parent.parent / "backend" / "sectors_data.yaml",
        ]
        for c in candidates:
            if c.exists():
                sectors_path = str(c)
                break

    if not sectors_path or not Path(sectors_path).exists():
        print("  !! sectors_data.yaml não encontrado — usando keywords genéricas")
        return "Geral", ["licitação"], "geral"

    with open(sectors_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # YAML: top-level "sectors" dict, each value is a sector dict
    sectors_dict = {}
    if isinstance(data, dict):
        sectors_dict = data.get("sectors") or data.get("setores") or data

    cnae_lower = cnae_principal.lower()
    # Extract pure numeric CNAE code (e.g. "4120400" from "4120-4/00 - Construção de edifícios")
    cnae_digits = re.sub(r"[^0-9]", "", cnae_principal.split("-")[0].split(" ")[0])[:7]
    cnae_prefix = cnae_digits[:4]

    # Strategy 1: CNAE code → sector key via hardcoded map
    sk = _CNAE_TO_SECTOR_KEY.get(cnae_prefix)
    if sk and sk in sectors_dict:
        sector = sectors_dict[sk]
        if isinstance(sector, dict):
            name = sector.get("name") or sk
            kws = sector.get("keywords") or [cnae_lower]
            print(f"  Match: CNAE {cnae_prefix}* → {name}")
            return name, kws, sk

    # Strategy 2: Match CNAE description text against sector keywords
    best_match = None
    best_score = 0
    best_key = "geral"
    for key, sector in sectors_dict.items():
        if not isinstance(sector, dict):
            continue
        name = sector.get("name") or sector.get("nome") or key
        desc = (sector.get("description") or "").lower()
        kws = sector.get("keywords") or []

        score = 0
        for kw in kws[:20]:
            if kw.lower() in cnae_lower:
                score += 2
        for word in cnae_lower.split():
            if len(word) > 3 and word in desc:
                score += 1

        if score > best_score:
            best_score = score
            best_match = (name, kws)
            best_key = key

    if best_match and best_score >= 2:
        return best_match[0], best_match[1], best_key

    # Strategy 3: Keyword-based sector matching from CNAE description
    _SECTOR_HINTS: dict[str, list[str]] = {
        "engenharia": ["construç", "construc", "edifici", "obra", "engenharia", "paviment", "infraestrutura", "urbaniz"],
        "vestuario": ["vestuário", "vestuario", "uniforme", "confecç", "confeccao", "roupa", "têxtil", "textil"],
        "alimentos": ["aliment", "merenda", "refeição", "refeicao", "nutriç", "nutricao", "panifica"],
        "informatica": ["informática", "informatica", "computador", "hardware", "equipamento de ti"],
        "software": ["software", "sistema", "desenvolvimento de programa", "tecnologia da informaç"],
        "facilities": ["limpeza", "conservaç", "conservacao", "zeladoria", "jardinagem", "paisagis"],
        "vigilancia": ["vigilância", "vigilancia", "segurança", "seguranca", "monitoramento"],
        "saude": ["saúde", "saude", "farmac", "médic", "medic", "hospitalar", "laborat"],
        "transporte": ["transporte", "veículo", "veiculo", "logística", "logistica", "frete"],
        "mobiliario": ["móvel", "movel", "mobiliário", "mobiliario", "mobília", "mobilia"],
        "papelaria": ["papelaria", "papel", "escritório", "escritorio", "material escolar"],
        "manutencao_predial": ["manutenção predial", "manutencao predial", "instalações", "instalacoes"],
        "engenharia_rodoviaria": ["rodovia", "rodoviári", "rodoviario", "estrada", "pavimentaç"],
        "materiais_eletricos": ["elétric", "eletric", "eletroeletrônic", "eletroeletronico"],
        "materiais_hidraulicos": ["hidráulic", "hidraulic", "saneamento", "encanamento", "tubos"],
    }
    for sk, hints in _SECTOR_HINTS.items():
        if any(h in cnae_lower for h in hints):
            sector = sectors_dict.get(sk, {})
            if sector and isinstance(sector, dict):
                return sector.get("name", sk), sector.get("keywords", [cnae_lower]), sk
            break

    # Strategy 4: Generic fallback — use CNAE description as keyword
    cnae_words = [w.strip().lower() for w in cnae_principal.split("-")[-1].split("/")[-1].split(",") if w.strip()]
    fallback_kw = [w for w in cnae_words if len(w) > 3] if cnae_words else ["licitação"]
    return "Geral", fallback_kw, "geral"


# CNAE 4-digit prefix → YAML sector key mapping (all 15 B2G sectors)
_CNAE_TO_SECTOR_KEY: dict[str, str] = {
    # --- Engenharia, Projetos e Obras ---
    "4120": "engenharia",  # Construção de edifícios
    "4110": "engenharia",  # Incorporação de empreendimentos imobiliários
    "4212": "engenharia",  # Construção de ferrovias
    "4221": "engenharia",  # Construção de redes (água, esgoto)
    "4222": "engenharia",  # Construção de redes (eletricidade, telecom)
    "4223": "engenharia",  # Construção de obras de arte especiais
    "4291": "engenharia",  # Obras portuárias/marítimas
    "4292": "engenharia",  # Montagem industrial
    "4299": "engenharia",  # Outras obras de engenharia civil
    "4311": "engenharia",  # Demolição
    "4312": "engenharia",  # Preparação de terreno
    "4313": "engenharia",  # Sondagem
    "4319": "engenharia",  # Outros serviços especializados
    "4391": "engenharia",  # Obras de fundações
    "4399": "engenharia",  # Serviços especializados construção
    "7112": "engenharia",  # Engenharia (escritórios)
    "7119": "engenharia",  # Atividades técnicas (ensaios)
    # --- Engenharia Rodoviária e Infraestrutura Viária ---
    "4211": "engenharia_rodoviaria",  # Construção de rodovias e ferrovias
    "4213": "engenharia_rodoviaria",  # Obras de urbanização — ruas e praças
    # --- Manutenção e Conservação Predial ---
    "4321": "manutencao_predial",  # Instalações elétricas
    "4322": "manutencao_predial",  # Instalações hidráulicas, gás, etc.
    "4329": "manutencao_predial",  # Outras instalações em construções
    "4330": "manutencao_predial",  # Obras de acabamento
    # --- Vestuário e Uniformes ---
    "4781": "vestuario",  # Comércio varejista de artigos de vestuário
    "4782": "vestuario",  # Comércio varejista de calçados
    "1411": "vestuario",  # Confecção de roupas íntimas
    "1412": "vestuario",  # Confecção de peças do vestuário (exceto roupas íntimas)
    "1413": "vestuario",  # Confecção de roupas profissionais
    "1414": "vestuario",  # Fabricação de acessórios do vestuário
    "1421": "vestuario",  # Fabricação de meias
    "1422": "vestuario",  # Fabricação de artigos do vestuário produzidos em malharias
    "1531": "vestuario",  # Fabricação de calçados de couro
    # --- Alimentos e Merenda ---
    "1011": "alimentos",  # Abate de reses, exceto suínos
    "1012": "alimentos",  # Abate de suínos, aves e outros
    "1061": "alimentos",  # Fabricação de produtos do arroz
    "1091": "alimentos",  # Fabricação de produtos de panificação
    "1092": "alimentos",  # Fabricação de biscoitos e bolachas
    "1099": "alimentos",  # Fabricação de outros produtos alimentícios
    "5611": "alimentos",  # Restaurantes e similares
    "5612": "alimentos",  # Serviços ambulantes de alimentação
    "5620": "alimentos",  # Serviços de catering, bufê e outros
    "4729": "alimentos",  # Comércio varejista de produtos alimentícios em geral
    "4721": "alimentos",  # Padaria e confeitaria
    # --- Hardware e Equipamentos de TI ---
    "4751": "informatica",  # Comércio varejista de equipamentos de informática
    "4752": "informatica",  # Comércio varejista de equipamentos de telefonia
    "2621": "informatica",  # Fabricação de equipamentos de informática
    "2622": "informatica",  # Fabricação de periféricos para equipamentos de informática
    "9511": "informatica",  # Reparação e manutenção de computadores
    "2631": "informatica",  # Fabricação de equipamentos transmissores de comunicação
    # --- Software e Sistemas ---
    "6201": "software",  # Desenvolvimento de programas sob encomenda
    "6202": "software",  # Desenvolvimento e licenciamento de programas
    "6203": "software",  # Desenvolvimento e licenciamento de programas não-customizáveis
    "6204": "software",  # Consultoria em tecnologia da informação
    "6209": "software",  # Suporte técnico, manutenção em TI
    "6311": "software",  # Tratamento de dados, provedores de serviços
    "6319": "software",  # Portais, provedores de conteúdo e outros serviços de informação
    "6190": "software",  # Outras atividades de telecomunicações
    # --- Facilities e Manutenção ---
    "8111": "facilities",  # Serviços combinados para apoio a edifícios
    "8112": "facilities",  # Condomínios prediais
    "8121": "facilities",  # Limpeza em prédios e em domicílios
    "8122": "facilities",  # Imunização e controle de pragas urbanas
    "8129": "facilities",  # Atividades de limpeza não especificadas
    "8130": "facilities",  # Atividades paisagísticas
    # --- Vigilância e Segurança Patrimonial ---
    "8011": "vigilancia",  # Atividades de vigilância e segurança privada
    "8012": "vigilancia",  # Atividades de transporte de valores
    "8020": "vigilancia",  # Atividades de monitoramento de sistemas de segurança
    "8030": "vigilancia",  # Atividades de investigação particular
    # --- Saúde ---
    "2110": "saude",  # Fabricação de produtos farmoquímicos
    "2121": "saude",  # Fabricação de medicamentos para uso humano
    "2123": "saude",  # Fabricação de preparações farmacêuticas
    "3250": "saude",  # Fabricação de instrumentos e materiais para uso médico
    "4771": "saude",  # Comércio varejista de produtos farmacêuticos
    "4773": "saude",  # Comércio varejista de artigos médicos e ortopédicos
    "8610": "saude",  # Atividades de atendimento hospitalar
    "8630": "saude",  # Atividades de atenção ambulatorial
    "8640": "saude",  # Atividades de serviços de complementação diagnóstica
    # --- Transporte e Veículos ---
    "4511": "transporte",  # Comércio de automóveis e utilitários novos
    "4512": "transporte",  # Comércio de automóveis e utilitários usados
    "4912": "transporte",  # Transporte ferroviário de carga
    "4921": "transporte",  # Transporte rodoviário coletivo de passageiros
    "4922": "transporte",  # Transporte rodoviário de passageiros sob regime de fretamento
    "4923": "transporte",  # Transporte rodoviário de táxi
    "4924": "transporte",  # Transporte escolar
    "4930": "transporte",  # Transporte rodoviário de carga
    "7711": "transporte",  # Locação de automóveis sem condutor
    "7719": "transporte",  # Locação de outros meios de transporte
    # --- Mobiliário ---
    "3101": "mobiliario",  # Fabricação de móveis com predominância de madeira
    "3102": "mobiliario",  # Fabricação de móveis com predominância de metal
    "3103": "mobiliario",  # Fabricação de colchões
    "3104": "mobiliario",  # Fabricação de móveis de outros materiais
    "4754": "mobiliario",  # Comércio varejista de móveis
    # --- Papelaria e Material de Escritório ---
    "4761": "papelaria",  # Comércio varejista de livros, jornais, papelaria
    "1721": "papelaria",  # Fabricação de papel
    "1731": "papelaria",  # Fabricação de embalagens de papel
    "1741": "papelaria",  # Fabricação de produtos de papel para uso doméstico
    "4647": "papelaria",  # Comércio atacadista de artigos de escritório
    # --- Materiais Elétricos e Instalações ---
    "2710": "materiais_eletricos",  # Fabricação de geradores, transformadores e motores
    "2731": "materiais_eletricos",  # Fabricação de fios, cabos e condutores elétricos
    "2732": "materiais_eletricos",  # Fabricação de dispositivos para instalação elétrica
    "2733": "materiais_eletricos",  # Fabricação de aparelhos para distribuição de energia
    "4742": "materiais_eletricos",  # Comércio varejista de material elétrico
    "2740": "materiais_eletricos",  # Fabricação de lâmpadas e aparelhos de iluminação
    # --- Materiais Hidráulicos e Saneamento ---
    "2222": "materiais_hidraulicos",  # Fabricação de tubos e acessórios plásticos
    "2449": "materiais_hidraulicos",  # Metalurgia de metais não-ferrosos
    "4744": "materiais_hidraulicos",  # Comércio varejista de materiais de construção (hidráulicos)
    "3600": "materiais_hidraulicos",  # Captação, tratamento e distribuição de água
    "3701": "materiais_hidraulicos",  # Gestão de redes de esgoto
    "3702": "materiais_hidraulicos",  # Atividades relacionadas a esgoto
}


# Subcategories per sector for spectral object compatibility (P2)
_SECTOR_SUBCATEGORIES: dict[str, dict[str, list[str]]] = {
    "engenharia": {
        "edificacoes": ["construção de edifício", "edificação", "reforma predial", "ampliação de prédio", "construção civil"],
        "pavimentacao": ["pavimentação", "recapeamento", "cbuq", "asfalto", "bloquete", "intertravado", "calçamento"],
        "drenagem_saneamento": ["drenagem", "esgoto", "saneamento", "rede de água", "adutora", "estação de tratamento"],
        "projeto_executivo": ["projeto executivo", "projeto básico", "contratação integrada", "bim"],
        "demolicao_terraplanagem": ["demolição", "terraplanagem", "terraplenagem", "sondagem", "fundação", "estaca"],
        "instalacoes": ["instalação elétrica", "instalação hidráulica", "spda", "climatização", "cabeamento"],
    },
    "engenharia_rodoviaria": {
        "rodovias": ["rodovia", "estrada", "pista", "acostamento", "sinalização viária"],
        "pontes_viadutos": ["ponte", "viaduto", "passarela", "obra de arte especial"],
        "urbanizacao": ["urbanização", "praça", "calçada", "acessibilidade", "paisagismo"],
    },
    "software": {
        "desenvolvimento": ["desenvolvimento de sistema", "fábrica de software", "software sob demanda", "aplicativo", "portal"],
        "licenciamento": ["licença de software", "subscription", "saas", "erp", "sistema pronto"],
        "consultoria_ti": ["consultoria em ti", "análise de requisitos", "arquitetura de sistemas", "lgpd"],
        "suporte_manutencao": ["suporte técnico", "manutenção de sistema", "sustentação", "help desk de sistema"],
    },
    "informatica": {
        "equipamentos": ["computador", "notebook", "servidor", "storage", "switch", "rack"],
        "impressao": ["impressora", "multifuncional", "outsourcing de impressão"],
        "rede": ["rede de dados", "cabeamento estruturado", "fibra óptica", "wi-fi", "firewall"],
        "manutencao": ["manutenção de equipamento", "reparo", "assistência técnica"],
    },
    "saude": {
        "equipamentos_medicos": ["equipamento hospitalar", "equipamento médico", "aparelho", "raio-x", "tomógrafo"],
        "medicamentos": ["medicamento", "fármaco", "insumo farmacêutico", "vacina", "soro"],
        "servicos_medicos": ["serviço médico", "atendimento", "consulta", "exame", "cirurgia", "uti"],
        "manutencao_equipamentos": ["manutenção de equipamento", "calibração", "reparo de equipamento médico"],
        "materiais_hospitalares": ["material hospitalar", "descartável", "epi hospitalar", "luva", "seringa"],
    },
    "facilities": {
        "limpeza": ["limpeza", "conservação", "higienização", "desinfecção"],
        "manutencao_predial_geral": ["manutenção predial", "manutenção preventiva", "manutenção corretiva"],
        "jardinagem": ["jardinagem", "paisagismo", "roçagem", "poda", "capina"],
        "controle_pragas": ["controle de pragas", "desinsetização", "desratização", "dedetização"],
    },
    "vigilancia": {
        "vigilancia_armada": ["vigilância armada", "segurança armada", "posto de vigilância armada"],
        "vigilancia_desarmada": ["vigilância desarmada", "portaria", "controlador de acesso", "recepcionista"],
        "monitoramento": ["monitoramento eletrônico", "cftv", "câmera", "alarme", "cerca elétrica"],
        "transporte_valores": ["transporte de valores", "carro-forte", "custódia de numerário"],
    },
    "alimentos": {
        "refeicao": ["refeição", "alimentação", "marmitex", "restaurante", "cozinha industrial", "self-service"],
        "generos_alimenticios": ["gênero alimentício", "alimento", "hortifrúti", "cesta básica", "merenda"],
        "agua_bebidas": ["água mineral", "café", "bebida", "galão"],
    },
    "vestuario": {
        "uniformes": ["uniforme", "fardamento", "farda", "vestimenta profissional"],
        "epi_vestuario": ["jaleco", "avental", "colete", "bota", "calçado de segurança"],
        "confeccao": ["confecção", "camiseta", "camisa", "calça", "roupa"],
    },
    "transporte": {
        "locacao_veiculos": ["locação de veículo", "aluguel de veículo", "frota", "veículo"],
        "frete": ["frete", "transporte de carga", "mudança", "logística"],
        "transporte_passageiros": ["transporte escolar", "transporte de passageiro", "ônibus", "van"],
    },
    "mobiliario": {
        "moveis_escritorio": ["mesa", "cadeira", "armário", "estante", "gaveteiro", "móvel de escritório"],
        "moveis_escolares": ["carteira escolar", "quadro", "lousa", "mesa escolar"],
        "moveis_hospitalares": ["cama hospitalar", "maca", "mesa cirúrgica"],
    },
    "papelaria": {
        "material_escritorio": ["papel", "caneta", "toner", "cartucho", "material de escritório"],
        "impressos": ["impressão gráfica", "banner", "folder", "adesivo", "placa"],
    },
    "manutencao_predial": {
        "eletrica": ["instalação elétrica", "quadro elétrico", "iluminação", "gerador"],
        "hidraulica": ["instalação hidráulica", "encanamento", "bomba", "reservatório"],
        "civil_menor": ["pintura", "revestimento", "forro", "piso", "alvenaria menor"],
        "ar_condicionado": ["ar condicionado", "climatização", "split", "chiller"],
    },
    "materiais_eletricos": {
        "cabos_fios": ["cabo elétrico", "fio", "condutor", "eletroduto"],
        "iluminacao": ["lâmpada", "luminária", "refletor", "led"],
        "equipamentos_eletricos": ["transformador", "disjuntor", "quadro de distribuição", "nobreak"],
    },
    "materiais_hidraulicos": {
        "tubulacao": ["tubo", "conexão", "registro", "válvula", "flange"],
        "equipamentos_hidraulicos": ["bomba d'água", "hidrômetro", "filtro", "pressurizador"],
    },
}

# Typical habilitação requirements per sector (P3)
_HABILITACAO_REQUIREMENTS: dict[str, dict] = {
    "engenharia": {
        "capital_minimo_pct": 0.10,
        "atestados": ["Atestado técnico de execução de obra similar (acervo CREA/CAU)"],
        "certifications": ["CREA (registro ativo)", "CAU (se arquitetura)"],
        "fiscal": ["CND Federal/Previdenciária", "CND Estadual", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "engenharia_rodoviaria": {
        "capital_minimo_pct": 0.10,
        "atestados": ["Atestado técnico de pavimentação ou obra rodoviária similar"],
        "certifications": ["CREA (registro ativo)"],
        "fiscal": ["CND Federal/Previdenciária", "CND Estadual", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "software": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Atestado técnico de desenvolvimento/implantação de sistema similar"],
        "certifications": ["ISO 27001 (frequente)", "LGPD compliance (crescente)"],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "informatica": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Atestado de fornecimento de equipamentos de TI similares"],
        "certifications": ["Autorização de fabricante/distribuidor (quando exigido)"],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "saude": {
        "capital_minimo_pct": 0.10,
        "atestados": ["Atestado de fornecimento/serviço similar na área de saúde"],
        "certifications": ["ANVISA (AFE — Autorização de Funcionamento)", "CRM (se serviço médico)", "CRF (se farmacêutico)"],
        "fiscal": ["CND Federal/Previdenciária", "CND Estadual", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "facilities": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Atestado de prestação de serviço continuado similar"],
        "certifications": [],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "vigilancia": {
        "capital_minimo_pct": 0.10,
        "atestados": ["Atestado de prestação de serviço de vigilância similar"],
        "certifications": ["Autorização de Funcionamento (Polícia Federal)", "Alvará de Funcionamento"],
        "fiscal": ["CND Federal/Previdenciária", "CND Estadual", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "_default": {
        "capital_minimo_pct": 0.10,
        "atestados": ["Atestado técnico de execução de serviço similar"],
        "certifications": [],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
}

# Sector-specific systemic risk warnings (P5)
_SECTOR_RISK_FLAGS: dict[str, list[str]] = {
    "facilities": ["Subprecificação crônica em contratos de limpeza — margem real pode ser menor que estimada"],
    "engenharia": ["Aditivos contratuais frequentes (25-50%) em obras públicas — considerar margem de segurança"],
    "engenharia_rodoviaria": ["Obras rodoviárias frequentemente sofrem paralisações por questões ambientais ou orçamentárias"],
    "vigilancia": ["Convenção coletiva pode impactar custos — verificar dissídio da categoria na região"],
    "saude": ["Regulamentação ANVISA pode atrasar execução — verificar licenças necessárias"],
    "software": ["Editais de TI frequentemente exigem quadro técnico com certificações proprietárias específicas"],
    "alimentos": ["Contratos de alimentação têm reajuste atrelado a índices de preço — verificar cláusula de reequilíbrio"],
}

# Estimated participation cost per sector (P6)
_PARTICIPATION_COST: dict[str, float] = {
    "engenharia": 5000.0,
    "engenharia_rodoviaria": 6000.0,
    "software": 3000.0,
    "informatica": 2000.0,
    "saude": 3000.0,
    "facilities": 2000.0,
    "vigilancia": 2500.0,
    "alimentos": 1500.0,
    "vestuario": 1500.0,
    "transporte": 2000.0,
    "mobiliario": 1500.0,
    "papelaria": 1000.0,
    "manutencao_predial": 3000.0,
    "materiais_eletricos": 1500.0,
    "materiais_hidraulicos": 1500.0,
    "_default": 3000.0,
}


def compute_object_compatibility(
    edital_objeto: str,
    empresa_cnaes: str,
    sector_key: str,
    historico_contratos: list[dict],
) -> dict:
    """Compute spectral compatibility between edital object and company profile.

    Returns compatibility level (ALTA/MEDIA/BAIXA), detected subcategories,
    and human-readable rationale.
    """
    subcats = _SECTOR_SUBCATEGORIES.get(sector_key, {})
    if not subcats:
        return {
            "compatibility": "MEDIA",
            "score": 0.5,
            "edital_subcategory": None,
            "company_subcategories": [],
            "rationale": f"Setor '{sector_key}' sem subcategorias definidas — compatibilidade presumida",
            "_source": _source_tag("CALCULATED"),
        }

    objeto_lower = edital_objeto.lower()

    # Detect edital subcategory
    edital_subcat = None
    edital_subcat_score = 0
    for subcat_name, keywords in subcats.items():
        matches = sum(1 for kw in keywords if kw.lower() in objeto_lower)
        if matches > edital_subcat_score:
            edital_subcat_score = matches
            edital_subcat = subcat_name

    # Detect company subcategories from CNAEs + historical contracts
    company_subcats: set[str] = set()
    # From CNAE descriptions
    cnaes_lower = empresa_cnaes.lower() if empresa_cnaes else ""
    for subcat_name, keywords in subcats.items():
        if any(kw.lower() in cnaes_lower for kw in keywords):
            company_subcats.add(subcat_name)

    # From historical contract objects
    for contrato in historico_contratos:
        obj = (contrato.get("objeto") or "").lower()
        for subcat_name, keywords in subcats.items():
            if any(kw.lower() in obj for kw in keywords):
                company_subcats.add(subcat_name)

    # Score calculation
    if edital_subcat and edital_subcat in company_subcats:
        score = 1.0
        compatibility = "ALTA"
        rationale = (
            f"Objeto do edital corresponde à subcategoria '{edital_subcat}' "
            f"onde a empresa tem experiência comprovada"
        )
    elif edital_subcat and company_subcats:
        score = 0.6
        compatibility = "MEDIA"
        rationale = (
            f"Edital na subcategoria '{edital_subcat}', empresa atua em "
            f"{', '.join(sorted(company_subcats))} — mesmo setor, especialidade diferente"
        )
    elif edital_subcat and not company_subcats:
        score = 0.3
        compatibility = "BAIXA"
        rationale = (
            f"Edital na subcategoria '{edital_subcat}', "
            f"sem evidência de atuação da empresa nesta especialidade"
        )
    else:
        score = 0.5
        compatibility = "MEDIA"
        rationale = "Subcategoria do edital não identificada — compatibilidade avaliada no nível setorial"

    return {
        "compatibility": compatibility,
        "score": round(score, 2),
        "edital_subcategory": edital_subcat,
        "company_subcategories": sorted(company_subcats),
        "rationale": rationale,
        "_source": _source_tag("CALCULATED"),
    }


def compute_habilitacao_analysis(
    edital: dict,
    empresa: dict,
    sicaf: dict,
    sector_key: str,
) -> dict:
    """Cross-reference company profile against typical habilitação requirements.

    Returns per-dimension status and overall qualification assessment.
    """
    reqs = _HABILITACAO_REQUIREMENTS.get(sector_key, _HABILITACAO_REQUIREMENTS["_default"])
    dimensions: list[dict] = []
    gaps: list[str] = []
    dim_scores: list[int] = []

    # 1. Capital mínimo
    capital = _safe_float(empresa.get("capital_social"))
    valor = _safe_float(edital.get("valor_estimado"))
    min_pct = reqs["capital_minimo_pct"]
    if valor > 0 and capital > 0:
        threshold = valor * min_pct
        if capital >= threshold:
            dimensions.append({
                "dimension": "Capital Mínimo",
                "status": "OK",
                "detail": f"Capital R$ {capital:,.0f} >= {min_pct * 100:.0f}% do valor R$ {valor:,.0f}",
            })
            dim_scores.append(100)
        elif capital >= threshold * 0.5:
            dimensions.append({
                "dimension": "Capital Mínimo",
                "status": "ATENÇÃO",
                "detail": f"Capital R$ {capital:,.0f} abaixo do mínimo típico R$ {threshold:,.0f} mas acima de 50%",
            })
            gaps.append(f"Capital social pode ser insuficiente (R$ {capital:,.0f} vs mínimo R$ {threshold:,.0f})")
            dim_scores.append(50)
        else:
            dimensions.append({
                "dimension": "Capital Mínimo",
                "status": "CRÍTICO",
                "detail": f"Capital R$ {capital:,.0f} muito abaixo do mínimo típico R$ {threshold:,.0f}",
            })
            gaps.append(f"Capital social insuficiente (R$ {capital:,.0f} vs mínimo R$ {threshold:,.0f})")
            dim_scores.append(10)
    else:
        dimensions.append({
            "dimension": "Capital Mínimo",
            "status": "VERIFICAR",
            "detail": "Valor estimado ou capital social indisponível para análise",
        })
        dim_scores.append(50)

    # 2. Sanções
    sancoes = empresa.get("sancoes", {})
    active_sanctions = [k for k in ["ceis", "cnep", "cepim", "ceaf"] if sancoes.get(k)]
    if active_sanctions:
        dimensions.append({
            "dimension": "Sanções",
            "status": "CRÍTICO",
            "detail": f"Sanção ativa: {', '.join(s.upper() for s in active_sanctions)} — INABILITAÇÃO AUTOMÁTICA",
        })
        gaps.append(f"Sanção ativa ({', '.join(s.upper() for s in active_sanctions)}) impede participação")
        dim_scores.append(0)
    else:
        dimensions.append({
            "dimension": "Sanções",
            "status": "OK",
            "detail": "Sem sanções (CEIS, CNEP, CEPIM, CEAF)",
        })
        dim_scores.append(100)

    # 3. Regularidade fiscal (SICAF)
    sicaf_status = sicaf.get("status", "NÃO CONSULTADO") if isinstance(sicaf, dict) else "NÃO CONSULTADO"
    restricao = sicaf.get("restricao", {}) if isinstance(sicaf, dict) else {}
    if restricao.get("possui_restricao"):
        dimensions.append({
            "dimension": "Regularidade Fiscal",
            "status": "CRÍTICO",
            "detail": "SICAF indica restrição cadastral — verificar pendências",
        })
        gaps.append("Restrição cadastral no SICAF — regularizar antes de licitar")
        dim_scores.append(10)
    elif sicaf_status == "FALHA_COLETA":
        # E2: SICAF failure is distinct from "not checked" — analysis is incomplete
        attempted_at = sicaf.get("attempted_at", "")
        error_detail = sicaf.get("error_detail", "erro desconhecido")
        dimensions.append({
            "dimension": "Regularidade Fiscal",
            "status": "INCOMPLETO",
            "detail": (
                f"Coleta SICAF falhou em {attempted_at}: {error_detail}. "
                "Análise de habilitação incompleta por falha de coleta, não por ausência de relevância."
            ),
        })
        gaps.append(f"Regularidade fiscal não verificada — coleta SICAF falhou em {attempted_at}")
        dim_scores.append(40)
    elif sicaf_status == "NÃO CONSULTADO":
        fiscal_reqs = ", ".join(reqs.get("fiscal", [])[:3])
        dimensions.append({
            "dimension": "Regularidade Fiscal",
            "status": "VERIFICAR",
            "detail": f"SICAF não consultado — verificar: {fiscal_reqs}",
        })
        dim_scores.append(50)
    else:
        dimensions.append({
            "dimension": "Regularidade Fiscal",
            "status": "OK",
            "detail": "SICAF sem restrições identificadas",
        })
        dim_scores.append(100)

    # 4. Qualificação técnica (certifications)
    certs = reqs.get("certifications", [])
    if certs:
        # Check if sector-required certifications match CNAE profile
        cnae_principal = empresa.get("cnae_principal", "")
        has_compatible_cnae = any(
            cnae_prefix in str(cnae_principal)
            for cnae_prefix in _CNAE_TO_SECTOR_KEY
            if _CNAE_TO_SECTOR_KEY[cnae_prefix] == sector_key
        )
        if has_compatible_cnae:
            dimensions.append({
                "dimension": "Qualificação Técnica",
                "status": "ATENÇÃO",
                "detail": f"CNAE compatível com setor. Verificar: {', '.join(certs)}",
            })
            dim_scores.append(70)
        else:
            dimensions.append({
                "dimension": "Qualificação Técnica",
                "status": "ATENÇÃO",
                "detail": f"CNAE principal pode não cobrir exigências. Verificar: {', '.join(certs)}",
            })
            gaps.append(f"Verificar registros/certificações: {', '.join(certs)}")
            dim_scores.append(40)
    else:
        dimensions.append({
            "dimension": "Qualificação Técnica",
            "status": "OK",
            "detail": "Setor sem certificações específicas obrigatórias",
        })
        dim_scores.append(100)

    # 5. Atestados técnicos
    atestados = reqs.get("atestados", [])
    if atestados:
        dimensions.append({
            "dimension": "Atestados Técnicos",
            "status": "VERIFICAR",
            "detail": f"Necessário: {'; '.join(atestados)}",
        })
        gaps.append(f"Verificar acervo: {atestados[0]}")
        dim_scores.append(50)

    # Overall status
    statuses = [d["status"] for d in dimensions]
    if "CRÍTICO" in statuses:
        overall = "INAPTA"
    elif "INCOMPLETO" in statuses or "ATENÇÃO" in statuses:
        overall = "PARCIALMENTE_APTA"
    else:
        overall = "APTA"

    score = round(sum(dim_scores) / len(dim_scores)) if dim_scores else 50

    return {
        "status": overall,
        "score": score,
        "dimensions": dimensions,
        "gaps": gaps,
        "_source": _source_tag("CALCULATED"),
    }


def compute_risk_analysis(
    edital: dict,
    competitive_analysis: dict,
    sector_key: str,
) -> dict:
    """Compute systemic risk flags per edital."""
    flags: list[dict] = []

    # 1. Valor sigiloso
    valor = _safe_float(edital.get("valor_estimado"))
    if valor <= 0:
        flags.append({
            "flag": "Valor estimado sigiloso ou não informado — impossível avaliar adequação financeira",
            "severity": "ALTA",
            "category": "valor",
        })

    # 2. Timeline
    dias = edital.get("dias_restantes")
    if dias is not None:
        if dias < 7:
            flags.append({
                "flag": f"Prazo muito apertado ({dias} dias) — risco de proposta apressada",
                "severity": "ALTA",
                "category": "prazo",
            })
        elif dias < 15:
            flags.append({
                "flag": f"Prazo curto ({dias} dias) — preparação acelerada necessária",
                "severity": "MEDIA",
                "category": "prazo",
            })

    # 3. Organ concentration (if competitive data available)
    hhi = competitive_analysis.get("hhi", 0)
    if hhi > 0.5:
        flags.append({
            "flag": "Órgão com alta concentração de fornecedores (HHI > 0.5) — incumbente forte",
            "severity": "MEDIA",
            "category": "competitivo",
        })

    # 4. Sector-specific chronic risks
    sector_risks = _SECTOR_RISK_FLAGS.get(sector_key, [])
    for risk_text in sector_risks:
        flags.append({
            "flag": risk_text,
            "severity": "BAIXA",
            "category": "setor",
        })

    # 5. Concorrência presencial (travel cost + regional preference)
    modalidade = (edital.get("modalidade") or "").lower()
    if "presencial" in modalidade:
        dist = edital.get("distancia", {})
        km = dist.get("km") if isinstance(dist, dict) else None
        if km and km > 200:
            travel_cost = km * 6  # R$6/km round trip estimate
            flags.append({
                "flag": (
                    f"Licitação presencial a {km:.0f}km — custo estimado de deslocamento "
                    f"R$ {travel_cost:,.0f} por sessão".replace(",", ".")
                ),
                "severity": "MEDIA",
                "category": "logistica",
                "margin_impact_pct": round(travel_cost / valor * 100, 1) if valor > 0 else 0,
            })
        # Regional preference penalty for distant companies
        if km and km > 300:
            flags.append({
                "flag": "Licitação presencial com possível preferência regional — empresas locais têm vantagem logística e de relacionamento",
                "severity": "MEDIA",
                "category": "competitivo",
            })

    # 6. Long contract without price adjustment (margin erosion)
    objeto = (edital.get("objeto") or "").lower()
    # Check for multi-year indicators
    for duration_marker, months in [
        ("12 meses", 12), ("18 meses", 18), ("24 meses", 24), ("36 meses", 36),
        ("1 ano", 12), ("2 anos", 24), ("3 anos", 36),
    ]:
        if duration_marker in objeto:
            if months >= 12:
                # Estimate inflation erosion: ~5% annual
                erosion_pct = round(months / 12 * 5, 1)
                flags.append({
                    "flag": (
                        f"Contrato de {months} meses sem garantia de reajuste — "
                        f"erosão estimada de {erosion_pct}% na margem "
                        f"(inflação acumulada projetada)"
                    ),
                    "severity": "MEDIA" if months <= 18 else "ALTA",
                    "category": "financeiro",
                    "margin_impact_pct": erosion_pct,
                })
            break

    # Aggregate risk level
    severities = [f["severity"] for f in flags]
    if "ALTA" in severities:
        risk_level = "ALTO"
    elif "MEDIA" in severities:
        risk_level = "MEDIO"
    elif flags:
        risk_level = "BAIXO"
    else:
        risk_level = "MÍNIMO"

    # Risk score (inverted: more flags = lower score)
    penalty = sum(30 if f["severity"] == "ALTA" else 15 if f["severity"] == "MEDIA" else 5 for f in flags)
    risk_score = max(0, 100 - penalty)

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "flags": flags,
        "_source": _source_tag("CALCULATED"),
    }


def compute_competitive_analysis(contracts: list[dict]) -> dict:
    """Compute aggregate competitive landscape statistics from historical contracts."""
    if not contracts:
        return {
            "unique_suppliers": 0,
            "hhi": 0.0,
            "top_3_share": 0.0,
            "top_supplier": None,
            "competition_level": "DESCONHECIDA",
            "risk_signals": [],
            "_source": _source_tag("CALCULATED", "Sem dados históricos"),
        }

    supplier_counts: dict[str, int] = {}
    supplier_values: dict[str, float] = {}
    supplier_names: dict[str, str] = {}
    for c in contracts:
        cnpj = (c.get("cnpj_fornecedor") or "").strip()
        name = (c.get("fornecedor") or "").strip()
        key = cnpj if len(cnpj) >= 11 else name.upper()
        if not key:
            continue
        supplier_counts[key] = supplier_counts.get(key, 0) + 1
        supplier_values[key] = supplier_values.get(key, 0) + _safe_float(c.get("valor"))
        if name:
            supplier_names[key] = name

    n_suppliers = len(supplier_counts)
    n_contracts = sum(supplier_counts.values())

    if n_contracts == 0:
        return {
            "unique_suppliers": 0, "hhi": 0.0, "top_3_share": 0.0,
            "top_supplier": None, "competition_level": "DESCONHECIDA",
            "risk_signals": [],
            "_source": _source_tag("CALCULATED", "Sem dados históricos"),
        }

    # HHI
    shares = sorted([count / n_contracts for count in supplier_counts.values()], reverse=True)
    hhi = sum(s ** 2 for s in shares)
    top_3_share = sum(shares[:3])

    # Top supplier
    top_key = max(supplier_counts, key=lambda k: supplier_counts[k])
    top_supplier = {
        "nome": supplier_names.get(top_key, top_key),
        "cnpj": top_key if len(top_key) >= 11 else "",
        "share": round(shares[0], 3),
        "n_contracts": supplier_counts[top_key],
        "valor_total": round(supplier_values.get(top_key, 0), 2),
    }

    # Competition level
    if n_suppliers <= 2:
        level = "BAIXA"
    elif n_suppliers <= 5:
        level = "MEDIA"
    elif n_suppliers <= 10:
        level = "ALTA"
    else:
        level = "MUITO_ALTA"

    # Risk signals
    risk_signals = []
    if n_suppliers == 1:
        risk_signals.append(f"Fornecedor único nos últimos 24 meses ({supplier_names.get(top_key, top_key)})")
    if hhi > 0.5:
        risk_signals.append(f"HHI = {hhi:.2f} — concentração excessiva de mercado")
    if shares[0] > 0.6:
        risk_signals.append(f"Fornecedor dominante com {shares[0] * 100:.0f}% dos contratos")

    return {
        "unique_suppliers": n_suppliers,
        "hhi": round(hhi, 4),
        "top_3_share": round(top_3_share, 3),
        "top_supplier": top_supplier,
        "competition_level": level,
        "risk_signals": risk_signals,
        "_source": _source_tag("CALCULATED", f"{n_contracts} contratos, {n_suppliers} fornecedores"),
    }


def compute_portfolio_analysis(
    editais: list[dict],
    empresa: dict,
    sector_key: str,
) -> dict:
    """Portfolio-level strategic analysis across all editais."""
    capital = _safe_float(empresa.get("capital_social"))
    quick_wins = []
    investments = []
    opportunities = []
    inaccessible = 0
    low_priority = 0

    for i, ed in enumerate(editais):
        prob = ed.get("win_probability", {}).get("probability", 0)
        risk = ed.get("risk_score", {}).get("total", 50)
        hab_status = ed.get("habilitacao_analysis", {}).get("status", "DADOS_INSUFICIENTES")
        valor = _safe_float(ed.get("valor_estimado"))
        obj = (ed.get("objeto") or "")[:80]
        roi_max = ed.get("roi_potential", {}).get("roi_max", 0)

        summary = {
            "index": i + 1,
            "objeto": obj,
            "valor": valor,
            "probability": prob,
            "roi_max": roi_max,
        }

        # E1: respect strategic reclassification from ROI engine
        roi_reclass = ed.get("roi_potential", {}).get("strategic_reclassification")

        if hab_status == "INAPTA":
            ed["strategic_category"] = "INACESSÍVEL"
            inaccessible += 1
        elif roi_reclass == "INVESTIMENTO_ESTRATEGICO_ACERVO":
            ed["strategic_category"] = "INVESTIMENTO"
            investments.append(summary)
        elif prob >= 0.15 and risk >= 50:
            ed["strategic_category"] = "QUICK_WIN"
            quick_wins.append(summary)
        elif prob < 0.10 and valor > 0:
            ed["strategic_category"] = "INVESTIMENTO"
            investments.append(summary)
        elif prob >= 0.08 and risk >= 30:
            ed["strategic_category"] = "OPORTUNIDADE"
            opportunities.append(summary)
        else:
            ed["strategic_category"] = "BAIXA_PRIORIDADE"
            low_priority += 1

    # Aggregate metrics
    participation_cost = _PARTICIPATION_COST.get(sector_key, _PARTICIPATION_COST["_default"])
    viable_count = len(quick_wins) + len(opportunities)
    total_cost = viable_count * participation_cost
    total_revenue = sum(e["roi_max"] for e in quick_wins + opportunities)

    # Organ priority map — group by organ, rank by opportunity count
    organ_map: dict[str, int] = {}
    for ed in editais:
        if ed.get("strategic_category") in ("QUICK_WIN", "OPORTUNIDADE", "INVESTIMENTO"):
            orgao = ed.get("orgao", "")
            if orgao:
                organ_map[orgao] = organ_map.get(orgao, 0) + 1
    top_organs = sorted(organ_map.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "quick_wins": quick_wins,
        "strategic_investments": investments,
        "opportunities": opportunities,
        "inaccessible": inaccessible,
        "low_priority": low_priority,
        "total_potential_revenue": round(total_revenue),
        "estimated_participation_cost": round(total_cost),
        "participation_cost_per_edital": participation_cost,
        "organ_priority_map": [{"orgao": o, "count": c} for o, c in top_organs],
        "_source": _source_tag("CALCULATED"),
    }


# ============================================================
# PHASE 2a: PNCP SEARCH
# ============================================================


def _compile_keyword_patterns(keywords: list[str]) -> list[re.Pattern]:
    """Pre-compile word-boundary regex patterns for keyword matching.

    Uses \\b (word boundary) to avoid false positives like "água" matching
    "desaguamento" or "material" matching "imaterial".

    For multi-word keywords (bigrams like "merenda escolar"), each word
    must appear with word boundaries but not necessarily adjacent —
    this handles word order variations in procurement text.
    """
    patterns: list[re.Pattern] = []
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if not kw_lower:
            continue
        words = kw_lower.split()
        if len(words) == 1:
            # Single word: exact word boundary match
            try:
                patterns.append(re.compile(rf"\b{re.escape(kw_lower)}\b"))
            except re.error:
                pass  # Skip invalid patterns
        else:
            # Multi-word (bigram): both words must appear with boundaries
            # Use lookahead so order doesn't matter
            try:
                parts = [rf"(?=.*\b{re.escape(w)}\b)" for w in words]
                patterns.append(re.compile("".join(parts), re.DOTALL))
            except re.error:
                pass
    return patterns


def collect_pncp(
    api: ApiClient,
    keywords: list[str],
    ufs: list[str],
    dias: int = 30,
) -> tuple[list[dict], dict]:
    """Search PNCP for open editais."""
    print(f"\n🔍 Phase 2a-1: PNCP — Varredura de editais ({dias} dias)")

    data_inicial = _date_compact(_today() - timedelta(days=dias))
    data_final = _date_compact(_today())

    # Pre-compile word-boundary regex patterns for keyword matching (performance)
    keyword_patterns = _compile_keyword_patterns(keywords)

    all_editais = []
    seen_ids = set()
    source_meta = {"total_raw": 0, "total_filtered": 0, "pages_fetched": 0, "errors": 0}

    for mod_code, mod_name in MODALIDADES.items():
        print(f"\n  Modalidade {mod_code} ({mod_name}):")
        for page in range(1, PNCP_MAX_PAGES + 1):
            data, status = api.get(
                f"{PNCP_BASE}/contratacoes/publicacao",
                params={
                    "dataInicial": data_inicial,
                    "dataFinal": data_final,
                    "codigoModalidadeContratacao": mod_code,
                    "pagina": page,
                    "tamanhoPagina": PNCP_MAX_PAGE_SIZE,
                },
                label=f"PNCP mod={mod_code} p={page}",
            )
            if status != "API" or not data:
                source_meta["errors"] += 1
                break

            items = data if isinstance(data, list) else data.get("data", data.get("resultado", []))
            if not isinstance(items, list) or not items:
                break

            source_meta["pages_fetched"] += 1
            source_meta["total_raw"] += len(items)

            for item in items:
                edital = _parse_pncp_item(item, keywords, ufs, keyword_patterns=keyword_patterns)
                if edital:
                    eid = edital.get("_id", "")
                    if eid and eid not in seen_ids:
                        seen_ids.add(eid)
                        all_editais.append(edital)

            # If fewer results than page size, we've reached the end
            if len(items) < PNCP_MAX_PAGE_SIZE:
                break

            time.sleep(0.5)  # Rate limiting

    source_meta["total_filtered"] = len(all_editais)
    _source = _source_tag("API" if source_meta["errors"] == 0 else "API_PARTIAL",
                          f"{source_meta['total_raw']} obtidos, {source_meta['total_filtered']} relevantes, "
                          f"{source_meta['pages_fetched']} páginas consultadas")

    print(f"\n  PNCP: {source_meta['total_raw']} raw → {source_meta['total_filtered']} filtrados")
    return all_editais, _source


def _parse_pncp_item(item: dict, keywords: list[str], ufs: list[str],
                     keyword_patterns: list[re.Pattern] | None = None) -> dict | None:
    """Parse a single PNCP result. Returns None if filtered out.

    PNCP response structure:
      - objetoCompra: string (may have Latin1 encoding issues)
      - orgaoEntidade: {cnpj, razaoSocial, poderId, esferaId}
      - unidadeOrgao: {ufSigla, ufNome, municipioNome, nomeUnidade, codigoIbge}
      - valorTotalEstimado: float
      - dataAberturaProposta, dataEncerramentoProposta: ISO datetime strings
      - anoCompra, sequencialCompra: for building PNCP link
    """
    objeto = (item.get("objetoCompra") or item.get("objeto") or "").strip()

    # UF is inside unidadeOrgao, not at top level
    unidade = item.get("unidadeOrgao") or {}
    orgao_entity = item.get("orgaoEntidade") or {}
    uf = (unidade.get("ufSigla") or item.get("ufSigla") or "").upper()

    # UF filter
    if ufs and uf and uf not in ufs:
        return None

    # Keyword filter: word-boundary matching (not substring)
    # Uses pre-compiled regex patterns for performance.
    # Requires at least 1 keyword match with word boundaries to pass.
    objeto_lower = objeto.lower()
    if keyword_patterns:
        if not any(p.search(objeto_lower) for p in keyword_patterns):
            return None
    elif not any(kw.lower() in objeto_lower for kw in keywords):
        # Fallback to substring for backward compat if no patterns provided
        return None

    # Build PNCP link from orgaoEntidade.cnpj + anoCompra + sequencialCompra
    cnpj_compra = orgao_entity.get("cnpj") or item.get("cnpjCompra") or ""
    ano = item.get("anoCompra") or ""
    seq = item.get("sequencialCompra") or ""
    link_sistema = item.get("linkSistemaOrigem") or ""

    if cnpj_compra and ano and seq:
        cnpj_clean = re.sub(r"[^0-9]", "", str(cnpj_compra))
        link = f"https://pncp.gov.br/app/editais/{cnpj_clean}/{ano}/{seq}"
    elif link_sistema:
        link = link_sistema
    else:
        link = ""

    # Parse dates
    data_abertura = (item.get("dataAberturaProposta") or item.get("dataPublicacaoPncp") or "")[:10]
    data_encerramento = (item.get("dataEncerramentoProposta") or "")[:10]

    # Calculate dias_restantes
    dias_restantes = None
    if data_encerramento:
        try:
            dt_enc = datetime.strptime(data_encerramento[:10], "%Y-%m-%d")
            dias_restantes = (dt_enc - _today().replace(tzinfo=None)).days
        except ValueError:
            pass

    valor = _safe_float(item.get("valorTotalEstimado") or item.get("valorEstimado"))

    modalidade = item.get("modalidadeNome") or ""
    orgao = (orgao_entity.get("razaoSocial") or
             unidade.get("nomeUnidade") or
             item.get("nomeOrgao") or "")
    municipio = unidade.get("municipioNome") or ""

    # Unique ID for dedup
    cnpj_clean = re.sub(r"[^0-9]", "", str(cnpj_compra)) if cnpj_compra else ""
    _id = f"PNCP-{cnpj_clean}-{ano}-{seq}" if cnpj_clean else f"PNCP-{objeto[:50]}"

    return {
        "_id": _id,
        "_source": _source_tag("API"),
        "objeto": objeto,
        "orgao": orgao,
        "uf": uf,
        "municipio": municipio,
        "valor_estimado": valor,
        "modalidade": modalidade,
        "data_abertura": data_abertura,
        "data_encerramento": data_encerramento,
        "dias_restantes": dias_restantes,
        "fonte": "PNCP",
        "link": link,
        "cnpj_orgao": cnpj_clean,
        "ano_compra": str(ano),
        "sequencial_compra": str(seq),
        "status_edital": "ENCERRADO" if (dias_restantes is not None and dias_restantes < 0) else "ABERTO",
    }


# ============================================================
# PHASE 2a-2: PCP v2
# ============================================================

def collect_pcp(
    api: ApiClient,
    keywords: list[str],
    ufs: list[str],
    dias: int = 30,
) -> tuple[list[dict], dict]:
    """Search PCP v2 for complementary editais."""
    print(f"\n🔍 Phase 2a-2: PCP v2 — Editais complementares")

    data_inicial = _date_br(_today() - timedelta(days=dias))
    data_final = _date_br(_today())

    keyword_patterns = _compile_keyword_patterns(keywords)

    all_editais = []
    source_meta = {"total_raw": 0, "total_filtered": 0, "pages": 0, "errors": 0}

    for page in range(1, PCP_MAX_PAGES + 1):
        data, status = api.get(
            PCP_BASE,
            params={
                "pagina": page,
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "tipoData": 1,
            },
            label=f"PCP v2 p={page}",
        )
        if status != "API" or not data:
            source_meta["errors"] += 1
            break

        items = data if isinstance(data, list) else data.get("resultado", data.get("data", []))
        if not isinstance(items, list) or not items:
            break

        source_meta["pages"] += 1
        source_meta["total_raw"] += len(items)

        for item in items:
            edital = _parse_pcp_item(item, keywords, ufs, keyword_patterns=keyword_patterns)
            if edital:
                all_editais.append(edital)

        # Check pagination
        page_count = data.get("pageCount", 0) if isinstance(data, dict) else 0
        if page >= page_count:
            break

        time.sleep(0.5)

    source_meta["total_filtered"] = len(all_editais)
    _source = _source_tag(
        "API" if source_meta["errors"] == 0 else "API_PARTIAL",
        f"{source_meta['total_raw']} obtidos, {source_meta['total_filtered']} relevantes",
    )

    print(f"  PCP v2: {source_meta['total_raw']} raw → {source_meta['total_filtered']} filtrados")
    return all_editais, _source


def _parse_pcp_item(item: dict, keywords: list[str], ufs: list[str],
                    keyword_patterns: list[re.Pattern] | None = None) -> dict | None:
    """Parse a PCP v2 result."""
    resumo = item.get("resumo") or ""
    uc = item.get("unidadeCompradora") or {}
    uf = (uc.get("uf") or "").upper()

    if ufs and uf not in ufs:
        return None

    resumo_lower = resumo.lower()
    if keyword_patterns:
        if not any(p.search(resumo_lower) for p in keyword_patterns):
            return None
    elif not any(kw.lower() in resumo_lower for kw in keywords):
        return None

    url_ref = item.get("urlReferencia") or ""
    link = f"https://www.portaldecompraspublicas.com.br{url_ref}" if url_ref else ""

    data_abertura = (item.get("dataHoraInicioPropostas") or "")[:10]
    data_encerramento = (item.get("dataHoraFinalPropostas") or "")[:10]

    dias_restantes = None
    if data_encerramento:
        try:
            dt_enc = datetime.strptime(data_encerramento[:10], "%Y-%m-%d")
            dias_restantes = (dt_enc - _today().replace(tzinfo=None)).days
        except ValueError:
            pass

    modalidade_info = item.get("tipoLicitacao", {})
    modalidade = modalidade_info.get("modalidadeLicitacao", "") if isinstance(modalidade_info, dict) else ""

    return {
        "_id": f"PCP-{item.get('codigoLicitacao', resumo[:50])}",
        "_source": _source_tag("API"),
        "objeto": resumo,
        "orgao": item.get("razaoSocial") or uc.get("nome") or "",
        "uf": uf,
        "municipio": uc.get("cidade") or "",
        "valor_estimado": 0.0,  # PCP v2 has no value data
        "modalidade": modalidade,
        "data_abertura": data_abertura,
        "data_encerramento": data_encerramento,
        "dias_restantes": dias_restantes,
        "fonte": "PCP",
        "link": link,
        "status_edital": "ENCERRADO" if (dias_restantes is not None and dias_restantes < 0) else "ABERTO",
    }


# ============================================================
# PHASE 2a-3: QUERIDO DIÁRIO
# ============================================================

def collect_querido_diario(
    api: ApiClient,
    keywords: list[str],
    empresa_nome: str,
    dias: int = 30,
    ufs: list[str] | None = None,
) -> tuple[list[dict], dict]:
    """Search municipal gazettes via Querido Diário. Filters by UFs if provided."""
    print(f"\n🔍 Phase 2a-3: Querido Diário — Diários oficiais")

    since = _date_iso(_today() - timedelta(days=dias))
    until = _date_iso(_today())

    mencoes = []
    queries = [
        " ".join(f'"{kw}"' if " " in kw else kw for kw in keywords[:5]),
    ]
    if empresa_nome:
        queries.append(f'"{empresa_nome}"')

    for q in queries:
        params = {
            "querystring": q,
            "published_since": since,
            "published_until": until,
            "excerpt_size": 500,
            "number_of_excerpts": 3,
            "size": 20,
            "sort_by": "descending_date",
        }
        # Filter by UFs to reduce noise from unrelated municipalities
        if ufs:
            # QD API accepts state_code (2-letter UF)
            for uf in ufs[:3]:  # Max 3 UFs per query
                params["state_code"] = uf.upper()
        data, status = api.get(
            QD_BASE,
            params=params,
            label=f"Querido Diário: {q[:40]}",
        )
        if status == "API" and data:
            gazettes = data.get("gazettes", data) if isinstance(data, dict) else data
            if isinstance(gazettes, list):
                for g in gazettes[:10]:
                    mencoes.append({
                        "_source": _source_tag("API"),
                        "data": g.get("date", ""),
                        "territorio": f"{g.get('territory_name', '')} - {g.get('state_code', '')}",
                        "excerpts": [
                            {"text": e} if isinstance(e, str) else e
                            for e in (g.get("excerpts") or [])[:3]
                        ],
                    })

        time.sleep(1.0)  # Rate limit

    _source = _source_tag("API" if mencoes else "API_PARTIAL",
                          f"{len(mencoes)} menções encontradas")
    return mencoes, _source


# ============================================================
# DISTANCE CALCULATION (OSRM)
# ============================================================

def _geocode(api: ApiClient, cidade: str, uf: str) -> tuple[float, float] | None:
    """Geocode a city using Nominatim. Returns (lat, lon) or None."""
    if not cidade or not uf:
        return None

    data, status = api.get(
        NOMINATIM_BASE,
        params={
            "q": f"{cidade}, {uf}, Brasil",
            "format": "json",
            "limit": 1,
            "countrycodes": "br",
        },
        headers={"User-Agent": "SmartLic-ReportCollector/1.0 (report@smartlic.tech)"},
        label=f"Geocode: {cidade}/{uf}",
    )
    if status == "API" and data and isinstance(data, list) and len(data) > 0:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None


def calculate_distance(
    api: ApiClient,
    cidade_sede: str,
    uf_sede: str,
    cidade_destino: str,
    uf_destino: str,
) -> dict:
    """Calculate driving distance between two cities using OSRM."""
    origin = _geocode(api, cidade_sede, uf_sede)
    if not origin:
        return {
            "km": None,
            "duracao_horas": None,
            "_source": _source_tag("API_FAILED", f"Geocode falhou para {cidade_sede}/{uf_sede}"),
        }

    dest = _geocode(api, cidade_destino, uf_destino)
    if not dest:
        return {
            "km": None,
            "duracao_horas": None,
            "_source": _source_tag("API_FAILED", f"Geocode falhou para {cidade_destino}/{uf_destino}"),
        }

    # OSRM expects lon,lat (not lat,lon)
    coords = f"{origin[1]},{origin[0]};{dest[1]},{dest[0]}"
    data, status = api.get(
        f"{OSRM_BASE}/{coords}",
        params={"overview": "false"},
        label=f"OSRM: {cidade_sede}→{cidade_destino}",
    )
    if status == "API" and data and data.get("routes"):
        route = data["routes"][0]
        km = round(route["distance"] / 1000, 1)
        hours = round(route["duration"] / 3600, 1)
        return {
            "km": km,
            "duracao_horas": hours,
            "_source": _source_tag("CALCULATED", f"OSRM driving distance"),
        }

    return {
        "km": None,
        "duracao_horas": None,
        "_source": _source_tag("API_FAILED", "OSRM routing falhou"),
    }


# ============================================================
# PNCP LINK VALIDATION
# ============================================================

def validate_pncp_links(api: ApiClient, editais: list[dict]) -> None:
    """Validate PNCP links with HEAD requests. Mutates editais in place."""
    print(f"\n🔗 Validando links PNCP ({len(editais)} editais)")
    for ed in editais:
        link = ed.get("link", "")
        if not link or "pncp.gov.br" not in link:
            ed["link_valid"] = None
            continue
        status_code = api.head(link, label=f"HEAD {link[-40:]}")
        ed["link_valid"] = status_code == 200 if status_code else None
        if status_code and status_code != 200:
            print(f"  ⚠ Link HTTP {status_code}: {link}")
        time.sleep(0.3)


# ============================================================
# PNCP DOCUMENT LISTING
# ============================================================

def collect_pncp_documents(api: ApiClient, editais: list[dict]) -> None:
    """List available documents for each PNCP edital. Mutates editais in place."""
    print(f"\n📄 Phase 2b: Listando documentos PNCP")
    for ed in editais:
        if ed.get("fonte") != "PNCP":
            ed["documentos"] = []
            ed["documentos_source"] = _source_tag("UNAVAILABLE", "Apenas PNCP tem API de documentos")
            continue

        cnpj_orgao = ed.get("cnpj_orgao", "")
        ano = ed.get("ano_compra", "")
        seq = ed.get("sequencial_compra", "")

        if not (cnpj_orgao and ano and seq):
            ed["documentos"] = []
            ed["documentos_source"] = _source_tag("UNAVAILABLE", "Dados insuficientes para buscar docs")
            continue

        data, status = api.get(
            f"{PNCP_FILES_BASE}/orgaos/{cnpj_orgao}/compras/{ano}/{seq}/arquivos",
            label=f"Docs: {cnpj_orgao}/{ano}/{seq}",
        )

        if status == "API" and isinstance(data, list):
            docs = []
            for d in data:
                docs.append({
                    "tipo": d.get("tipoDocumentoNome") or d.get("tipoDocumentoDescricao") or "",
                    "tipo_id": d.get("tipoDocumentoId"),
                    "titulo": d.get("titulo", ""),
                    "sequencial": d.get("sequencialDocumento"),
                    "download_url": (
                        f"https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj_orgao}/compras/{ano}/{seq}"
                        f"/arquivos/{d.get('sequencialDocumento')}"
                    ) if d.get("sequencialDocumento") else None,
                    "ativo": d.get("statusAtivo", True),
                })
            ed["documentos"] = docs
            ed["documentos_source"] = _source_tag("API", f"{len(docs)} documentos encontrados")
        else:
            ed["documentos"] = []
            ed["documentos_source"] = _source_tag("API_FAILED")

        time.sleep(0.5)


# ============================================================
# COMPETITIVE INTELLIGENCE COLLECTION
# ============================================================

def collect_competitive_intel(
    api: ApiClient,
    editais: list[dict],
    meses: int = 24,
) -> None:
    """Fetch historical contracts for each edital's orgão to identify incumbents.

    Mutates editais in place, adding `competitive_intel` field.
    Deduplicates by orgão CNPJ to avoid redundant API calls.
    """
    # Collect unique orgão CNPJs
    orgao_map: dict[str, list[dict]] = {}  # cnpj_orgao → [editais]
    for ed in editais:
        cnpj_orgao = ed.get("cnpj_orgao", "")
        if cnpj_orgao and len(cnpj_orgao) == 14:
            orgao_map.setdefault(cnpj_orgao, []).append(ed)

    if not orgao_map:
        print("  ⚠ Nenhum edital com cnpj_orgao — pulando inteligência competitiva")
        for ed in editais:
            ed["competitive_intel"] = []
            ed["competitive_intel_source"] = _source_tag("UNAVAILABLE", "Sem cnpj_orgao")
        return

    print(f"\n🏢 Inteligência competitiva — {len(orgao_map)} órgãos únicos")

    # Use /contratos endpoint with cnpjOrgao (more reliable than /contratacoes/publicacao)
    # Max period: 365 days — split into yearly chunks for 24-month coverage
    today = _today()
    _windows = []
    for i in range(0, meses, 12):
        days_end = i * 30
        days_start = min((i + 12) * 30, meses * 30)
        w_end = today - timedelta(days=days_end)
        w_start = today - timedelta(days=days_start)
        _windows.append((_date_compact(w_start), _date_compact(w_end)))

    for cnpj_orgao, orgao_editais in orgao_map.items():
        orgao_nome = orgao_editais[0].get("orgao", cnpj_orgao)
        contracts: list[dict] = []

        for data_ini_str, data_fim_str in _windows:
            for page in range(1, 5):  # Max 4 pages per window
                data, status = api.get(
                    f"{PNCP_BASE}/contratos",
                    params={
                        "dataInicial": data_ini_str,
                        "dataFinal": data_fim_str,
                        "cnpjOrgao": cnpj_orgao,
                        "pagina": page,
                        "tamanhoPagina": PNCP_MAX_PAGE_SIZE,
                    },
                    label=f"Competitiva: {orgao_nome[:30]}... p{page}",
                )

                if status != "API":
                    break

                # /contratos returns {"data": [...], "totalRegistros": N}
                items = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

                if not items:
                    break

                for c in items:
                    fn = c.get("nomeRazaoSocialFornecedor", "")
                    vl = _safe_float(c.get("valorGlobal") or c.get("valorInicial"))
                    obj = (c.get("objetoContrato") or "")[:150]
                    if fn or obj:
                        contracts.append({
                            "fornecedor": fn,
                            "cnpj_fornecedor": c.get("niFornecedor", ""),
                            "objeto": obj,
                            "valor": vl,
                            "data": c.get("dataAssinatura") or c.get("dataPublicacaoPncp", ""),
                        })

                if len(items) < PNCP_MAX_PAGE_SIZE:
                    break
                time.sleep(0.3)

            # Stop if we already have enough data
            if len(contracts) >= 40:
                break
            time.sleep(0.3)

        # Assign to all editais of this orgão
        source = _source_tag("API", f"{len(contracts)} contratos") if contracts else _source_tag("API", "0 contratos")
        for ed in orgao_editais:
            ed["competitive_intel"] = contracts[:20]  # Limit to 20 most recent
            ed["competitive_intel_source"] = source

        time.sleep(0.3)

    # Mark editais without orgao data
    for ed in editais:
        if "competitive_intel" not in ed:
            ed["competitive_intel"] = []
            ed["competitive_intel_source"] = _source_tag("UNAVAILABLE", "Orgão sem CNPJ")


# ============================================================
# DETERMINISTIC CALCULATIONS (risk score, ROI, chronogram)
# ============================================================

# Estimated profit margins by sector (min, max) for ROI calculation
_SECTOR_MARGINS: dict[str, tuple[float, float]] = {
    "engenharia": (0.08, 0.15),
    "engenharia_rodoviaria": (0.08, 0.15),
    "software": (0.20, 0.40),
    "informatica": (0.10, 0.25),
    "vestuario": (0.10, 0.25),
    "alimentos": (0.05, 0.15),
    "facilities": (0.08, 0.20),
    "vigilancia": (0.08, 0.18),
    "saude": (0.10, 0.25),
    "transporte": (0.05, 0.15),
    "mobiliario": (0.10, 0.25),
    "papelaria": (0.10, 0.20),
    "manutencao_predial": (0.10, 0.20),
    "materiais_eletricos": (0.10, 0.20),
    "materiais_hidraulicos": (0.10, 0.20),
}

# Sector-specific viability weight profiles (must sum to 1.0)
# Rationale: weights reflect what matters most for each sector's competitive dynamics
_SECTOR_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    # Construction: capital-intensive, on-site, fewer bidders per municipality
    "engenharia": {"hab": 0.25, "fin": 0.30, "geo": 0.25, "prazo": 0.15, "comp": 0.05},
    "engenharia_rodoviaria": {"hab": 0.25, "fin": 0.30, "geo": 0.25, "prazo": 0.15, "comp": 0.05},
    # IT/Software: remote execution, commoditized, many bidders
    "software": {"hab": 0.15, "fin": 0.15, "geo": 0.05, "prazo": 0.25, "comp": 0.40},
    "informatica": {"hab": 0.15, "fin": 0.20, "geo": 0.10, "prazo": 0.20, "comp": 0.35},
    # Facilities/Security: local presence needed, moderate competition
    "facilities": {"hab": 0.25, "fin": 0.20, "geo": 0.20, "prazo": 0.15, "comp": 0.20},
    "vigilancia": {"hab": 0.25, "fin": 0.20, "geo": 0.20, "prazo": 0.15, "comp": 0.20},
    # Health: regulatory-heavy (ANVISA, CRM, certifications dominate)
    "saude": {"hab": 0.30, "fin": 0.20, "geo": 0.15, "prazo": 0.15, "comp": 0.20},
    # Food/Transport: logistics matter, moderate barriers
    "alimentos": {"hab": 0.25, "fin": 0.20, "geo": 0.20, "prazo": 0.20, "comp": 0.15},
    "transporte": {"hab": 0.20, "fin": 0.25, "geo": 0.15, "prazo": 0.15, "comp": 0.25},
    # Commerce/Supply: lower barriers, more competition
    "vestuario": {"hab": 0.20, "fin": 0.25, "geo": 0.10, "prazo": 0.20, "comp": 0.25},
    "mobiliario": {"hab": 0.20, "fin": 0.25, "geo": 0.10, "prazo": 0.20, "comp": 0.25},
    "papelaria": {"hab": 0.20, "fin": 0.25, "geo": 0.10, "prazo": 0.20, "comp": 0.25},
    # Maintenance: on-site, moderate capital
    "manutencao_predial": {"hab": 0.25, "fin": 0.20, "geo": 0.25, "prazo": 0.15, "comp": 0.15},
    # Materials: supply chain, moderate geography importance
    "materiais_eletricos": {"hab": 0.20, "fin": 0.25, "geo": 0.15, "prazo": 0.20, "comp": 0.20},
    "materiais_hidraulicos": {"hab": 0.20, "fin": 0.25, "geo": 0.15, "prazo": 0.20, "comp": 0.20},
    # Default fallback — preserves original behavior
    "_default": {"hab": 0.30, "fin": 0.25, "geo": 0.20, "prazo": 0.15, "comp": 0.10},
}

# Sector-typical base win rates (derived from average number of bidders per procurement)
_SECTOR_BASE_WIN_RATES: dict[str, float] = {
    "engenharia": 0.15,              # ~7 bidders typical
    "engenharia_rodoviaria": 0.12,   # ~8 bidders, larger contracts
    "software": 0.08,                # ~12 bidders, commoditized
    "informatica": 0.10,             # ~10 bidders
    "facilities": 0.06,              # ~15+ bidders, very competitive
    "vigilancia": 0.08,              # ~12 bidders
    "saude": 0.10,                   # ~10 bidders, regulatory barriers
    "vestuario": 0.10,               # ~10 bidders
    "alimentos": 0.08,               # ~12 bidders
    "transporte": 0.10,              # ~10 bidders
    "mobiliario": 0.12,              # ~8 bidders
    "papelaria": 0.08,               # ~12 bidders, commodity
    "manutencao_predial": 0.12,      # ~8 bidders
    "materiais_eletricos": 0.10,     # ~10 bidders
    "materiais_hidraulicos": 0.10,   # ~10 bidders
    "_default": 0.10,
}

# Modality multipliers for win probability — adjusts base rate by competition intensity
_MODALITY_MULTIPLIERS: dict[str, float] = {
    "pregão eletrônico": 0.80,       # Most bidders (electronic = easy access)
    "pregão presencial": 0.90,       # Slightly fewer (travel barrier)
    "concorrência eletrônica": 1.00, # Moderate
    "concorrência": 1.00,
    "concorrência presencial": 1.10, # Fewer (complex + travel)
    "inexigibilidade": 1.50,         # Much fewer (pre-qualified)
    "credenciamento": 1.30,          # Limited pool
    "dispensa": 1.20,                # Small value, fewer bidders
    "dispensa eletrônica": 1.10,
    "dispensa de licitação": 1.20,
}

# CRÍTICA 6: Sector-specific keywords for filtering competitive_intel.
# Only contracts whose objeto matches these keywords are considered "sector-relevant"
# when calculating HHI, n_suppliers, and incumbency. Prevents noise from unrelated contracts.
_SECTOR_COMPETITION_KEYWORDS: dict[str, list[str]] = {
    "engenharia": ["obra", "construção", "construcao", "reforma", "pavimentação", "pavimentacao",
                    "edificação", "edificacao", "engenharia", "drenagem", "terraplenagem",
                    "saneamento", "infraestrutura", "ponte", "viaduto"],
    "engenharia_rodoviaria": ["rodovia", "estrada", "pavimentação", "pavimentacao", "asfalto",
                               "terraplenagem", "sinalização", "sinalizacao", "ponte", "viaduto",
                               "drenagem", "engenharia rodoviária"],
    "software": ["software", "sistema", "desenvolvimento", "tecnologia da informação",
                  "informática", "informatica", "plataforma", "aplicativo", "licença"],
    "informatica": ["informática", "informatica", "computador", "equipamento", "hardware",
                     "impressora", "notebook", "servidor", "rede", "cabeamento"],
    "facilities": ["limpeza", "conservação", "conservacao", "jardinagem", "portaria",
                    "recepção", "recepcao", "facilities", "manutenção predial"],
    "vigilancia": ["vigilância", "vigilancia", "segurança", "seguranca", "monitoramento",
                    "alarme", "cftv", "controle de acesso"],
    "saude": ["saúde", "saude", "medicamento", "hospitalar", "laborat", "clínic",
              "ambulância", "ambulancia", "médic", "enferm"],
    "vestuario": ["uniforme", "fardamento", "vestuário", "vestuario", "roupa", "camiseta",
                   "calçado", "calcado", "epi", "proteção individual"],
    "alimentos": ["alimentação", "alimentacao", "refeição", "refeicao", "merenda",
                   "gênero alimentício", "cesta básica", "nutrição"],
    "transporte": ["transporte", "veículo", "veiculo", "locação de veículo", "frete",
                    "combustível", "combustivel", "ônibus", "onibus"],
}


def _compute_fiscal_risk(edital: dict, competitive_intel: list[dict]) -> dict:
    """CRÍTICA 8: Estimate fiscal risk of the contracting municipality.

    Uses IBGE population/GDP data + historical contract terminations to assess
    whether the municipality has the fiscal capacity to honor the contract.
    Returns {"nivel": "BAIXO"|"MEDIO"|"ALTO", "alertas": [...], "roi_discount": float}.

    The roi_discount factor (0.0-1.0) is applied to ROI calculations:
    - BAIXO: 1.0 (no discount)
    - MEDIO: 0.85
    - ALTO: 0.70
    """
    ibge = edital.get("ibge", {}) or {}
    pop = ibge.get("populacao", 0) or 0
    pib = ibge.get("pib_mil_reais", 0) or 0
    valor = _safe_float(edital.get("valor_estimado"))

    alertas: list[str] = []
    risk_level = "BAIXO"

    # Check 1: Contract value as % of municipal GDP
    if pib > 0 and valor > 0 and valor / (pib * 1000) > 0.05:
        risk_level = "ALTO"
        alertas.append(
            f"Valor do edital = {valor / (pib * 1000) * 100:.1f}% do PIB municipal "
            f"— risco elevado de dependência orçamentária"
        )

    # Check 2: Small municipality + large contract
    if 0 < pop < 10_000 and valor > 5_000_000:
        risk_level = "ALTO"
        alertas.append(
            f"Município de {pop:,.0f} habitantes licitando R$ {valor:,.0f} "
            f"— capacidade operacional e fiscal limitada"
        )
    elif 0 < pop < 20_000 and valor > 10_000_000:
        if risk_level != "ALTO":
            risk_level = "MEDIO"
        alertas.append(
            f"Município de {pop:,.0f} habitantes com edital de R$ {valor:,.0f} "
            f"— atenção à capacidade fiscal"
        )

    # Check 3: Contract terminations in organ history
    rescisoes = sum(1 for c in competitive_intel if str(c.get("situacao_contrato", "")) == "3")
    if rescisoes >= 2:
        if risk_level == "BAIXO":
            risk_level = "MEDIO"
        alertas.append(
            f"{rescisoes} rescisão(ões) de contrato identificada(s) no histórico do órgão"
        )
    elif rescisoes == 1:
        alertas.append("1 rescisão contratual no histórico do órgão — monitorar")

    roi_discount = {"BAIXO": 1.0, "MEDIO": 0.85, "ALTO": 0.70}.get(risk_level, 1.0)

    return {"nivel": risk_level, "alertas": alertas, "roi_discount": roi_discount}


def compute_risk_score(edital: dict, empresa: dict, sicaf: dict, sector_key: str = "") -> dict:
    """Compute composite opportunity risk score 0-100 (higher = better opportunity).

    Uses sector-specific weight profiles from _SECTOR_WEIGHT_PROFILES.
    Components: habilitacao, financeiro, geografico, prazo, competitivo.

    CRÍTICA 2: Veto gates — binary elimination for hard requirements.
    CRÍTICA 4: Non-linear threshold gates — dimensions below critical
               thresholds impose hard ceilings on total score.
    CRÍTICA 5: Acervo confirmation flag — distinguishes volume from
               proven technical capacity.
    CRÍTICA 7: Operational viability — IBGE pop/PIB integrated into
               geographic scoring for infrastructure adequacy.
    CRÍTICA 8: Fiscal risk — municipality financial health discount.
    """
    capital = _safe_float(empresa.get("capital_social"))
    valor = _safe_float(edital.get("valor_estimado"))

    # ================================================================
    # CRÍTICA 2: VETO GATES — binary elimination before any scoring
    # Eliminatory requirements cannot be compensated by other dimensions.
    # If ANY veto fires, total=0 and edital is flagged for NÃO RECOMENDADO (ELIMINATÓRIO).
    # ================================================================
    veto_gates: list[str] = []

    # Gate 1: Active sanctions (CEIS/CNEP/CEPIM/CEAF) — absolute disqualification
    sancoes = empresa.get("sancoes", {})
    if any(sancoes.get(k) for k in ["ceis", "cnep", "cepim", "ceaf"]):
        veto_gates.append("Empresa possui sanção ativa (CEIS/CNEP/CEPIM/CEAF) — impedida de licitar")

    # Gate 2: SICAF restriction — cadastral impediment
    sicaf_status = sicaf.get("status", "NÃO CONSULTADO") if isinstance(sicaf, dict) else "NÃO CONSULTADO"
    crc = sicaf.get("crc", {}) if isinstance(sicaf, dict) else {}
    restricao = sicaf.get("restricao", {}) if isinstance(sicaf, dict) else {}
    if restricao.get("possui_restricao"):
        veto_gates.append("Restrição cadastral SICAF ativa — inabilitação provável")

    # Gate 3: Capital < 10% of contract value — insuficiente para habilitação econômico-financeira
    if capital > 0 and valor > 0 and (capital / valor) < 0.10:
        veto_gates.append(
            f"Capital social insuficiente: R$ {capital:,.0f} = {capital/valor:.0%} do valor do edital "
            f"(mínimo usual: 10%)"
        )

    # Gate 4: MEI + valor > R$81k — legal limit
    is_mei = empresa.get("mei") or empresa.get("opcao_pelo_mei")
    if is_mei and valor > 81_000:
        veto_gates.append(
            f"Limite MEI excedido: edital R$ {valor:,.0f} > R$ 81.000 (teto MEI)"
        )

    # Gate 5: Simples Nacional + valor > R$4.8M — legal limit
    is_simples = empresa.get("simples_nacional") or empresa.get("opcao_pelo_simples")
    if is_simples and valor > 4_800_000:
        veto_gates.append(
            f"Limite Simples Nacional excedido: edital R$ {valor:,.0f} > R$ 4.800.000"
        )

    if veto_gates:
        weights = _SECTOR_WEIGHT_PROFILES.get(sector_key, _SECTOR_WEIGHT_PROFILES["_default"])
        return {
            "total": 0,
            "vetoed": True,
            "veto_reasons": veto_gates,
            "habilitacao": 0,
            "financeiro": 0,
            "geografico": 0,
            "prazo": 0,
            "competitivo": 0,
            "weights": weights,
            "threshold_applied": None,
            "acervo_confirmado": False,
            "fiscal_risk": {"nivel": "N/A", "alertas": []},
            "_source": _source_tag("CALCULATED", f"VETADO: {len(veto_gates)} impedimento(s)"),
        }

    # ================================================================
    # HABILITAÇÃO (30%) — no veto, but penalties still apply
    # ================================================================
    hab_score = 100

    if crc.get("status_cadastral") == "CADASTRADO":
        hab_score = 100
    elif sicaf_status == "NÃO CONSULTADO":
        hab_score = 60  # Unknown = moderate risk

    if valor > 0 and capital > 0:
        ratio = capital / valor
        # Already passed veto (ratio >= 0.10), apply graduated penalty
        if ratio < 0.3:
            hab_score = min(hab_score, 70)

    # ================================================================
    # FINANCEIRO (25%)
    # ================================================================
    if valor <= 0 or capital <= 0:
        fin_score = 50  # Unknown
    else:
        capacity = capital * 10
        if valor <= capacity * 0.5:
            fin_score = 100
        elif valor <= capacity:
            fin_score = 70
        elif valor <= capacity * 2:
            fin_score = 40
        else:
            fin_score = 10

    # ================================================================
    # GEOGRÁFICO (20%) — continuous decay + CRÍTICA 7: IBGE operational viability
    # ================================================================
    dist = edital.get("distancia", {})
    km = dist.get("km") if isinstance(dist, dict) else None
    if km is None:
        geo_score = 50
    elif km <= 50:
        geo_score = 100
    elif km <= 100:
        geo_score = 90 - (km - 50) * 0.4  # 90→70
    elif km <= 300:
        geo_score = 70 - (km - 100) * 0.2  # 70→30
    elif km <= 800:
        geo_score = 30 - (km - 300) * 0.04  # 30→10
    else:
        geo_score = max(5, 10 - (km - 800) * 0.005)  # Slow decay below 10, floor at 5

    # Presencial penalty: presencial editais far away get extra penalty
    modalidade = (edital.get("modalidade") or "").lower()
    if "presencial" in modalidade and km is not None and km > 200:
        geo_score = max(5, geo_score - 15)  # -15 penalty for presencial >200km

    # CRÍTICA 7: IBGE operational viability — municipality infrastructure adequacy
    ibge = edital.get("ibge", {}) or {}
    pop = ibge.get("populacao", 0) or 0
    pib_pc = ibge.get("pib_per_capita", 0) or 0
    if pop > 0 and pop < 5_000 and valor > 1_000_000:
        geo_score *= 0.7  # Município muito pequeno para contrato grande — supply chain frágil
    elif pop > 0 and pop < 15_000 and valor > 3_000_000:
        geo_score *= 0.8  # Infraestrutura limitada para contratos de alta complexidade
    if pib_pc > 0 and pib_pc < 15_000 and valor > 500_000:
        geo_score *= 0.85  # Capacidade fiscal/infraestrutura frágil

    geo_score = round(max(5, min(100, geo_score)))

    # ================================================================
    # PRAZO (15%)
    # ================================================================
    dias = edital.get("dias_restantes")
    if dias is None:
        prazo_score = 50
    elif dias > 30:
        prazo_score = 100
    elif dias > 15:
        prazo_score = 70
    elif dias > 7:
        prazo_score = 40
    else:
        prazo_score = 10

    # ================================================================
    # COMPETITIVO — derived from competitive_intel if available
    # ================================================================
    ci = edital.get("competitive_intel", [])
    n_sup = len(set(
        (c.get("cnpj_fornecedor") or c.get("fornecedor", ""))[:20]
        for c in ci if c.get("cnpj_fornecedor") or c.get("fornecedor")
    ))
    if n_sup == 0:
        comp_score = 50  # No data — neutral
    elif n_sup == 1:
        comp_score = 15  # Monopoly incumbent — hard to enter
    elif n_sup <= 3:
        comp_score = 35  # Oligopoly
    elif n_sup <= 6:
        comp_score = 65  # Moderate competition — fair chance
    elif n_sup <= 10:
        comp_score = 80  # Fragmented — good odds
    else:
        comp_score = 90  # Very fragmented — open market

    # ================================================================
    # CRÍTICA 8: FISCAL RISK — municipality financial health
    # ================================================================
    fiscal_risk = _compute_fiscal_risk(edital, ci)

    # ================================================================
    # WEIGHTED TOTAL + CRÍTICA 4: NON-LINEAR THRESHOLD GATES
    # ================================================================
    weights = _SECTOR_WEIGHT_PROFILES.get(sector_key, _SECTOR_WEIGHT_PROFILES["_default"])

    total = (
        hab_score * weights["hab"]
        + fin_score * weights["fin"]
        + geo_score * weights["geo"]
        + prazo_score * weights["prazo"]
        + comp_score * weights["comp"]
    )

    # CRÍTICA 4: Threshold gates — dimensions below critical values impose hard ceilings.
    # A linear model allows geo=100 to compensate prazo=10. These gates prevent that.
    threshold_applied = None
    if prazo_score <= 10:
        # <7 days: impossible to prepare quality proposal regardless of other factors
        total = min(total, 20)
        threshold_applied = "prazo_critico"
    if fin_score <= 10:
        # Valor >2x capacity: financial disqualification likely
        total = min(total, 25)
        threshold_applied = threshold_applied or "financeiro_critico"
    if hab_score <= 30:
        # Severe qualification risk (SICAF restriction survived veto check = possible resolution)
        total = min(total, 30)
        threshold_applied = threshold_applied or "habilitacao_critica"

    # ================================================================
    # CRÍTICA 5: ACERVO CONFIRMATION FLAG
    # Historical contract volume ≠ proven technical capacity.
    # ================================================================
    acervo_confirmado = False  # Default: NOT confirmed (requires manual verification)

    return {
        "total": round(total),
        "vetoed": False,
        "veto_reasons": [],
        "habilitacao": hab_score,
        "financeiro": fin_score,
        "geografico": geo_score,
        "prazo": prazo_score,
        "competitivo": comp_score,
        "weights": weights,
        "threshold_applied": threshold_applied,
        "acervo_confirmado": acervo_confirmado,
        "fiscal_risk": fiscal_risk,
        "_source": _source_tag("CALCULATED"),
    }


def compute_win_probability(
    edital: dict,
    empresa: dict,
    competitive_intel: list[dict],
    sector_key: str,
    risk_score: int,
) -> dict:
    """Compute Bayesian-inspired win probability based on competitive landscape.

    Factors:
    1. Base rate: sector-typical competition density
    2. Competition level: unique suppliers in organ's history
    3. Concentration: HHI and top-supplier share
    4. Incumbency: company's own history with organ
    5. Modality adjustment: pregão (more bidders) vs inexigibilidade (fewer)
    6. Viability discount: risk_score adjusts final probability
    7. Contextual multipliers: per-edital adjustments (CRÍTICA 1)

    CRÍTICA 1: Reduced floor on viability_factor (0.05 not 0.3) + contextual
               multipliers per edital to increase probability dispersion.
    CRÍTICA 6: Filter competitive_intel by sector keywords before HHI/supplier
               analysis — incumbency in office supplies ≠ incumbency in construction.

    Returns dict with probability (0.0-1.0), confidence, and decomposition.
    """
    base_rate = _SECTOR_BASE_WIN_RATES.get(sector_key, _SECTOR_BASE_WIN_RATES["_default"])

    # CRÍTICA 6: Filter competitive_intel by sector keyword relevance.
    # An incumbent in office supplies is NOT an incumbent in construction.
    sector_kw_list = _SECTOR_COMPETITION_KEYWORDS.get(sector_key, [])
    filtered_intel = competitive_intel
    sector_filtered = False
    if sector_kw_list and competitive_intel:
        relevant = [
            c for c in competitive_intel
            if any(kw in (c.get("objeto", "") or "").lower() for kw in sector_kw_list)
        ]
        # Use filtered set if we retain at least 20% of data (else too noisy to filter)
        if len(relevant) >= max(1, len(competitive_intel) * 0.2):
            filtered_intel = relevant
            sector_filtered = True

    # Analyze competitive landscape from sector-filtered historical contracts
    unique_suppliers: set[str] = set()
    supplier_counts: dict[str, int] = {}
    for c in filtered_intel:
        cnpj = (c.get("cnpj_fornecedor") or "").strip()
        name = (c.get("fornecedor") or "").strip().upper()
        key = cnpj if len(cnpj) >= 11 else name
        if key:
            unique_suppliers.add(key)
            supplier_counts[key] = supplier_counts.get(key, 0) + 1

    n_suppliers = len(unique_suppliers)
    n_contracts = len(filtered_intel)
    n_contracts_raw = len(competitive_intel)

    # HHI (Herfindahl-Hirschman Index) — 0=perfect competition, 1=monopoly
    hhi = 0.0
    top_share = 0.0
    if n_contracts > 0 and supplier_counts:
        shares = [count / n_contracts for count in supplier_counts.values()]
        hhi = sum(s ** 2 for s in shares)
        top_share = max(shares)

    # Competition-adjusted probability — varies by supplier count AND concentration
    if n_suppliers == 0:
        # No data — use sector base rate
        competition_prob = base_rate
        confidence = "baixa"
    elif n_suppliers == 1:
        # Single supplier monopoly — difficulty depends on contract age
        competition_prob = 0.05
        confidence = "media"
    elif n_suppliers == 2:
        # Duopoly — hard but possible
        competition_prob = 0.15
        confidence = "media"
    elif n_suppliers <= 5:
        # Moderate competition — fair share with HHI adjustment
        fair_share = 1.0 / (n_suppliers + 1)  # +1 for entrant
        # HHI penalty: concentrated market reduces probability
        hhi_adj = 1.0 - (hhi * 0.3) if hhi > 0.25 else 1.0
        competition_prob = fair_share * hhi_adj
        confidence = "media" if hhi > 0.4 else "alta"
    elif n_suppliers <= 10:
        # Good competition — fragmented market favors new entrants
        competition_prob = 1.0 / (n_suppliers + 1)
        # Low concentration bonus
        if hhi < 0.15:
            competition_prob *= 1.2
        confidence = "alta"
    else:
        # Very competitive — many bidders, price pressure
        competition_prob = 1.0 / (n_suppliers + 2)  # Harder with many competitors
        confidence = "alta"

    # Lower confidence when using unfiltered (noisy) data
    if not sector_filtered and n_contracts_raw > 0:
        confidence = "baixa"

    # Top supplier dominance penalty
    if top_share > 0.60:
        competition_prob *= 0.6  # Dominant incumbent reduces chances significantly
    elif top_share > 0.40:
        competition_prob *= 0.8

    # Incumbency bonus — does the company already supply this organ?
    empresa_cnpj = re.sub(r"[^0-9]", "", empresa.get("cnpj", ""))
    incumbency_bonus = 0.0
    if empresa_cnpj and len(empresa_cnpj) >= 11:
        for c in filtered_intel:
            c_cnpj = re.sub(r"[^0-9]", "", c.get("cnpj_fornecedor", ""))
            if c_cnpj == empresa_cnpj:
                incumbency_bonus = 0.10  # 10pp bonus for existing relationship
                break

    # Modality adjustment
    modalidade = (edital.get("modalidade") or "").lower()
    mod_mult = 1.0
    for key, mult in _MODALITY_MULTIPLIERS.items():
        if key in modalidade:
            mod_mult = mult
            break

    # CRÍTICA 1: Reduced viability floor (0.05 not 0.3) for real discrimination.
    # A risk_score of 20 should produce meaningfully different probability than 70.
    viability_factor = max(risk_score / 100.0, 0.05)

    # CRÍTICA 1: Per-edital contextual multipliers — increase dispersion.
    # These capture edital-specific conditions that the base model misses.
    contextual_mult = 1.0

    # Tight deadline reduces probability (hard to prepare quality proposal)
    dias = edital.get("dias_restantes")
    if dias is not None and dias < 7:
        contextual_mult *= 0.5  # <7 days: halved chance
    elif dias is not None and dias < 15:
        contextual_mult *= 0.75  # <15 days: reduced chance

    # Contract value >> company capacity = lower probability (financial disqualification risk)
    capital = _safe_float(empresa.get("capital_social"))
    valor = _safe_float(edital.get("valor_estimado"))
    if capital > 0 and valor > 0:
        cap_ratio = valor / (capital * 10)  # value vs capacity
        if cap_ratio > 5:
            contextual_mult *= 0.5  # Extreme financial stretch
        elif cap_ratio > 2:
            contextual_mult *= 0.7  # Significant stretch

    # Presencial + distant = reduced chance (travel barrier)
    if "presencial" in modalidade:
        dist = edital.get("distancia", {})
        km = dist.get("km") if isinstance(dist, dict) else None
        if km is not None and km > 300:
            contextual_mult *= 0.8

    # Final probability with widened bounds (CRÍTICA 1)
    raw_prob = competition_prob * mod_mult + incumbency_bonus
    final_prob = raw_prob * viability_factor * contextual_mult
    final_prob = max(0.01, min(0.90, final_prob))  # Widened clamp [1%, 90%]

    return {
        "probability": round(final_prob, 3),
        "confidence": confidence,
        "base_rate": base_rate,
        "n_unique_suppliers": n_suppliers,
        "n_contracts_analyzed": n_contracts,
        "n_contracts_raw": n_contracts_raw,
        "sector_filtered": sector_filtered,
        "hhi": round(hhi, 4),
        "top_supplier_share": round(top_share, 3),
        "incumbency_bonus": incumbency_bonus,
        "modality_multiplier": mod_mult,
        "viability_factor": round(viability_factor, 2),
        "contextual_multiplier": round(contextual_mult, 2),
        "_source": _source_tag("CALCULATED", f"{n_contracts} contratos{'(filtrados)' if sector_filtered else ''}, {n_suppliers} fornecedores"),
    }


# CRÍTICA 3: Participation cost profiles by (sector × modality).
# The cost of competing varies dramatically — a pregão eletrônico for commodity items
# costs ~R$1.5K (online, no travel), while a concorrência presencial for construction
# with mandatory site visit + BDI composition + detailed cost breakdown costs R$30K+.
_PARTICIPATION_COST_PROFILES: dict[tuple[str, str], dict] = {
    # Construction — concorrência (site visit, BDI, detailed budget, technical team)
    ("engenharia", "concorrência"): {"base": 8000, "km_rate": 8, "value_pct": 0.015, "cap": 50000, "label": "engenharia/concorrência"},
    ("engenharia", "concorrência presencial"): {"base": 10000, "km_rate": 10, "value_pct": 0.015, "cap": 50000, "label": "engenharia/concorrência_presencial"},
    ("engenharia", "pregão eletrônico"): {"base": 3000, "km_rate": 0, "value_pct": 0.005, "cap": 15000, "label": "engenharia/pregão_eletrônico"},
    ("engenharia_rodoviaria", "concorrência"): {"base": 12000, "km_rate": 10, "value_pct": 0.015, "cap": 60000, "label": "eng_rodoviária/concorrência"},
    ("engenharia_rodoviaria", "concorrência presencial"): {"base": 15000, "km_rate": 12, "value_pct": 0.02, "cap": 80000, "label": "eng_rodoviária/concorrência_presencial"},
    ("engenharia_rodoviaria", "pregão eletrônico"): {"base": 4000, "km_rate": 0, "value_pct": 0.008, "cap": 20000, "label": "eng_rodoviária/pregão_eletrônico"},
    # Software — predominantly electronic, low travel
    ("software", "pregão eletrônico"): {"base": 1500, "km_rate": 0, "value_pct": 0.003, "cap": 8000, "label": "software/pregão_eletrônico"},
    ("software", "concorrência"): {"base": 3000, "km_rate": 2, "value_pct": 0.005, "cap": 15000, "label": "software/concorrência"},
    ("informatica", "pregão eletrônico"): {"base": 1500, "km_rate": 0, "value_pct": 0.003, "cap": 8000, "label": "informatica/pregão_eletrônico"},
    # Facilities/Security — moderate, local presence
    ("facilities", "pregão eletrônico"): {"base": 2000, "km_rate": 2, "value_pct": 0.005, "cap": 10000, "label": "facilities/pregão_eletrônico"},
    ("vigilancia", "pregão eletrônico"): {"base": 2500, "km_rate": 3, "value_pct": 0.005, "cap": 12000, "label": "vigilância/pregão_eletrônico"},
    # Health — regulatory overhead
    ("saude", "pregão eletrônico"): {"base": 2500, "km_rate": 2, "value_pct": 0.005, "cap": 12000, "label": "saúde/pregão_eletrônico"},
}

_DEFAULT_COST_PROFILE = {"base": 2000, "km_rate": 3, "value_pct": 0.005, "cap": 15000, "label": "default"}


def _get_participation_cost_profile(sector_key: str, modalidade: str) -> dict:
    """Get participation cost profile for (sector, modality) pair.

    Falls back: exact match → sector + generic modality → default.
    """
    # Try exact (sector, modality) match
    for key, profile in _PARTICIPATION_COST_PROFILES.items():
        if key[0] == sector_key and key[1] in modalidade:
            return profile

    # Try sector with "pregão eletrônico" as most common default
    for key, profile in _PARTICIPATION_COST_PROFILES.items():
        if key[0] == sector_key:
            return profile  # Return first match for sector

    return _DEFAULT_COST_PROFILE


def compute_roi_potential(edital: dict, sector_key: str, win_prob: dict) -> dict:
    """Calculate ROI potential per edital.

    Formula: (valor × probability × margin) − participation_cost, discounted by fiscal risk.

    CRÍTICA 3: Participation cost now varies by (sector × modality) — a concorrência
               presencial for construction has 5-8x the cost of a pregão eletrônico for software.
    CRÍTICA 8: Fiscal risk discount applied to final ROI (municipality health).
    """
    valor = _safe_float(edital.get("valor_estimado"))
    if valor <= 0:
        return {
            "roi_min": 0, "roi_max": 0, "probability": 0.0,
            "margin_range": "N/A",
            "confidence": win_prob.get("confidence", "baixa"),
            "strategic_reclassification": None,
            "reclassification_rationale": None,
            "calculation_memory": {
                "valor_edital": 0,
                "probabilidade_vitoria": 0.0,
                "margem_min_pct": "N/A",
                "margem_max_pct": "N/A",
                "formula": "valor × probabilidade × margem",
                "roi_min_calc": "Valor estimado indisponível",
                "roi_max_calc": "Valor estimado indisponível",
            },
            "_source": _source_tag("CALCULATED", "Valor estimado indisponível"),
        }

    margin_min, margin_max = _SECTOR_MARGINS.get(sector_key, (0.08, 0.15))
    probability = win_prob.get("probability", 0.10)

    # CRÍTICA 3: Sector × modality participation cost profiles.
    # Cost of competing in a pregão eletrônico for software is ~R$1.5K.
    # Cost of competing in a concorrência presencial for construction is ~R$30K+.
    modalidade = (edital.get("modalidade") or "").lower()
    dist_info = edital.get("distancia", {})
    km = dist_info.get("km", 0) if isinstance(dist_info, dict) else 0

    cost_profile = _get_participation_cost_profile(sector_key, modalidade)
    mobilization_cost = cost_profile["base"] + (km or 0) * cost_profile["km_rate"]
    proposal_cost = min(valor * cost_profile["value_pct"], cost_profile["cap"])
    participation_cost = round(mobilization_cost + proposal_cost)

    # CRÍTICA 8: Fiscal risk discount from risk_score output
    fiscal_risk = edital.get("risk_score", {}).get("fiscal_risk", {})
    fiscal_discount = fiscal_risk.get("roi_discount", 1.0) if isinstance(fiscal_risk, dict) else 1.0

    gross_min = round(valor * probability * margin_min)
    gross_max = round(valor * probability * margin_max)
    # Net ROI = (gross ROI × fiscal discount) - participation cost (always incurred)
    roi_min = round(gross_min * fiscal_discount - participation_cost)
    roi_max = round(gross_max * fiscal_discount - participation_cost)

    # Auditable calculation memory — every factor explicit for manual reproduction
    def _fmt_brl(v: float) -> str:
        return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    fiscal_note = f" × {fiscal_discount:.2f} risco fiscal" if fiscal_discount < 1.0 else ""
    calculation_memory = {
        "valor_edital": valor,
        "probabilidade_vitoria": round(probability, 4),
        "margem_min_pct": f"{margin_min * 100:.0f}%",
        "margem_max_pct": f"{margin_max * 100:.0f}%",
        "custo_participacao": participation_cost,
        "custo_mobilizacao": round(mobilization_cost),
        "custo_proposta": round(proposal_cost),
        "cost_profile_used": cost_profile.get("label", "default"),
        "fiscal_risk_discount": fiscal_discount,
        "formula": f"(valor × probabilidade × margem{fiscal_note}) − custo de participação",
        "roi_min_calc": (
            f"({_fmt_brl(valor)} × {probability:.4f} × {margin_min:.2f}"
            f"{f' × {fiscal_discount:.2f}' if fiscal_discount < 1.0 else ''}"
            f") − {_fmt_brl(participation_cost)} = {_fmt_brl(roi_min)}"
        ),
        "roi_max_calc": (
            f"({_fmt_brl(valor)} × {probability:.4f} × {margin_max:.2f}"
            f"{f' × {fiscal_discount:.2f}' if fiscal_discount < 1.0 else ''}"
            f") − {_fmt_brl(participation_cost)} = {_fmt_brl(roi_max)}"
        ),
    }

    # Auto-reclassification: marginal ROI on substantial contracts
    strategic_reclassification = None
    reclassification_rationale = None
    if roi_max < 10_000 and valor > 100_000:
        strategic_reclassification = "INVESTIMENTO_ESTRATEGICO_ACERVO"
        reclassification_rationale = (
            f"Retorno financeiro direto marginal ({_fmt_brl(roi_max)}) em contrato de "
            f"{_fmt_brl(valor)} — valor principal é acervo técnico e relacionamento institucional"
        )

    return {
        "roi_min": roi_min,
        "roi_max": roi_max,
        "probability": round(probability, 3),
        "margin_range": f"{margin_min * 100:.0f}%-{margin_max * 100:.0f}%",
        "confidence": win_prob.get("confidence", "baixa"),
        "strategic_reclassification": strategic_reclassification,
        "reclassification_rationale": reclassification_rationale,
        "calculation_memory": calculation_memory,
        "_source": _source_tag("CALCULATED"),
    }


def build_reverse_chronogram(edital: dict) -> list[dict]:
    """Build reverse chronogram from edital deadline.

    Milestones work backwards from encerramento date:
    - D-0: Deadline (encerramento)
    - D-5: Documentação final
    - D-10: Proposta comercial
    - D-15: Visita técnica (if applicable)
    - D-20: Decisão go/no-go

    Adapts spacing for tight deadlines.
    """
    enc_str = edital.get("data_encerramento", "")
    if not enc_str:
        return []

    # Parse date
    enc_date = None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y"):
        try:
            enc_date = datetime.strptime(str(enc_str)[:10], fmt)
            break
        except ValueError:
            continue
    if not enc_date:
        return []

    hoje = _today().replace(tzinfo=None)
    dias = (enc_date - hoje).days

    if dias < 0:
        return []  # Already past

    # Adaptive milestone spacing
    if dias >= 25:
        offsets = [
            (0, "Encerramento / Deadline"),
            (5, "Entrega documentação final"),
            (10, "Finalizar proposta comercial"),
            (15, "Visita técnica / vistoria"),
            (20, "Decisão go/no-go"),
        ]
    elif dias >= 15:
        offsets = [
            (0, "Encerramento / Deadline"),
            (3, "Entrega documentação final"),
            (7, "Finalizar proposta comercial"),
            (10, "Decisão go/no-go"),
        ]
    elif dias >= 7:
        offsets = [
            (0, "Encerramento / Deadline"),
            (2, "Entrega documentação final"),
            (4, "Finalizar proposta"),
            (6, "Decisão go/no-go"),
        ]
    else:
        offsets = [
            (0, "Encerramento / Deadline"),
            (1, "Entrega documentação final"),
            (2, "Decisão URGENTE go/no-go"),
        ]

    cronograma = []
    for offset_days, marco in offsets:
        target = enc_date - timedelta(days=offset_days)
        dias_ate = (target - hoje).days

        if dias_ate < 0:
            status = "ATRASADO"
        elif dias_ate <= 3:
            status = "URGENTE"
        elif dias_ate <= 7:
            status = "ATENÇÃO"
        else:
            status = "NO PRAZO"

        cronograma.append({
            "data": target.strftime("%Y-%m-%d"),
            "marco": marco,
            "dias_ate_marco": max(dias_ate, 0),
            "status": status,
        })

    return cronograma


# ============================================================
# E8: MATURITY PROFILE DETECTION
# ============================================================

_MATURITY_HIGH_VALUE_THRESHOLD = 500_000  # above this, ENTRANTE gets hab penalty


def detect_maturity_profile(empresa: dict) -> dict:
    """Detect company maturity profile from federal contract history.

    Three profiles:
    - ENTRANTE: 0-2 federal contracts, new to government market
    - REGIONAL: 3-10 contracts, ≤3 UFs, regional experience
    - ESTABELECIDO: 10+ contracts OR 4+ UFs, diversified portfolio
    """
    historico = empresa.get("historico_contratos", [])
    total_count = len(historico) if isinstance(historico, list) else 0

    # Extract unique UFs, esferas, and value stats from contracts
    ufs_set: set[str] = set()
    esferas: dict[str, int] = {}
    max_contract_value = 0.0
    total_contract_value = 0.0
    acervo_objetos: list[str] = []  # Contract objects = implicit technical portfolio
    for c in (historico if isinstance(historico, list) else []):
        uf = c.get("uf", "")
        if uf:
            ufs_set.add(uf)
        esfera = c.get("esfera", "N/I")
        esferas[esfera] = esferas.get(esfera, 0) + 1
        val = _safe_float(c.get("valor", c.get("valorInicial", 0)))
        total_contract_value += val
        if val > max_contract_value:
            max_contract_value = val
        obj = c.get("objeto", "")
        if obj:
            acervo_objetos.append(obj[:150])

    geo_spread = len(ufs_set)
    capital = _safe_float(empresa.get("capital_social"))
    max_ratio = max_contract_value / capital if capital > 0 else 0.0

    # Classification considers ALL spheres (not just federal)
    if total_count >= 10 or geo_spread >= 4:
        profile = "ESTABELECIDO"
        esfera_detail = ", ".join(f"{v} {k.lower()}" for k, v in sorted(esferas.items(), key=lambda x: -x[1]))
        rationale = (
            f"Portfólio diversificado: {total_count} contratos governamentais"
            f" em {geo_spread} UF(s) ({esfera_detail})"
        )
    elif total_count >= 3:
        profile = "REGIONAL"
        esfera_detail = ", ".join(f"{v} {k.lower()}" for k, v in sorted(esferas.items(), key=lambda x: -x[1]))
        rationale = (
            f"Experiência regional: {total_count} contratos governamentais"
            f" em {geo_spread} UF(s) ({esfera_detail})"
        )
    else:
        profile = "ENTRANTE"
        rationale = (
            f"Novo no mercado governamental: {total_count} contrato(s) identificado(s)"
        )

    return {
        "profile": profile,
        "total_contract_count": total_count,
        "esferas": esferas,
        "geographic_spread": geo_spread,
        "max_contract_ratio": round(max_ratio, 2),
        "total_contract_value": round(total_contract_value, 2),
        "acervo_objetos": acervo_objetos[:20],  # Top 20 contract objects as implicit portfolio
        "rationale": rationale,
        "_source": _source_tag("CALCULATED"),
        # Backward compat
        "federal_contract_count": esferas.get("Federal", 0),
    }


# ============================================================
# E3: COVERAGE DIAGNOSTIC
# ============================================================

def compute_coverage_diagnostic(
    api: "ApiClient",
    captured_editais: list[dict],
    keywords: list[str],
    ufs: list[str],
    sector_key: str,
) -> dict:
    """Compute collection coverage diagnostic.

    Queries PNCP for total matching editais in each UF for 30/60/90 day
    windows and compares against captured count to detect under-representation.
    """
    captured_count = len(captured_editais)
    per_uf: list[dict] = []
    total_estimated = 0

    for uf in ufs:
        uf_captured = sum(1 for e in captured_editais if (e.get("uf", "") or "").upper() == uf.upper())
        uf_estimated = 0

        # Query PNCP for total count (page 1 only, read totalRegistros)
        for mod_code in [4, 5, 6, 8]:  # Concorrência, Pregão E/P, Inexigibilidade
            try:
                data_fim = _today()
                data_ini = data_fim - timedelta(days=30)
                params = {
                    "dataInicial": _date_compact(data_ini),
                    "dataFinal": _date_compact(data_fim),
                    "uf": uf,
                    "codigoModalidadeContratacao": mod_code,
                    "pagina": 1,
                    "tamanhoPagina": 1,
                }
                resp = api.get(f"{PNCP_BASE}/contratacoes/publicacao", params=params)
                if resp and isinstance(resp, dict):
                    uf_estimated += resp.get("totalRegistros", 0)
            except Exception:
                pass

        total_estimated += uf_estimated
        rate = uf_captured / uf_estimated if uf_estimated > 0 else 1.0
        per_uf.append({
            "uf": uf,
            "captured": uf_captured,
            "estimated_total": uf_estimated,
            "rate": round(rate, 2),
        })

    overall_rate = captured_count / total_estimated if total_estimated > 0 else 1.0

    warning = None
    low_ufs = [p for p in per_uf if p["rate"] < 0.70 and p["estimated_total"] > 0]
    if overall_rate < 0.70:
        warning = (
            f"Cobertura geral abaixo de 70% ({overall_rate:.0%}). "
            f"UFs com baixa cobertura: {', '.join(p['uf'] for p in low_ufs)}. "
            "Possível subrepresentação de oportunidades."
        )
    elif low_ufs:
        warning = (
            "Cobertura abaixo de 70% em: " + ", ".join(p["uf"] + f" ({p['rate']:.0%})" for p in low_ufs) + "."
        )

    return {
        "coverage_rate": round(overall_rate, 2),
        "captured_count": captured_count,
        "total_estimated": total_estimated,
        "per_uf": per_uf,
        "warning": warning,
        "methodology": (
            "Total estimado via contagem PNCP (todas as modalidades relevantes, "
            "últimos 30 dias por UF). Taxa = editais capturados / total publicado."
        ),
        "_source": _source_tag("CALCULATED"),
    }


# ============================================================
# E4: QUALIFICATION GAP ANALYSIS (sector compat vs operational gaps)
# ============================================================

# Sector-specific requirements for gap analysis
_SECTOR_REQUIREMENTS_DETAILED: dict[str, dict] = {
    "engenharia": {
        "certifications": ["Registro CREA", "ISO 9001 (desejável)"],
        "atestados": ["Atestado de obra similar (CREA/CAU)", "CAT de responsável técnico"],
        "capital_pct": 0.10,
    },
    "engenharia_rodoviaria": {
        "certifications": ["Registro CREA", "Certificação DNIT (desejável)"],
        "atestados": ["Atestado de obra rodoviária", "CAT de engenheiro"],
        "capital_pct": 0.15,
    },
    "software": {
        "certifications": ["ISO 27001 (desejável)", "Certificação LGPD"],
        "atestados": ["Atestado de fornecimento de software similar"],
        "capital_pct": 0.05,
    },
    "informatica": {
        "certifications": ["ISO 27001 (desejável)"],
        "atestados": ["Atestado de fornecimento de equipamentos/serviços de TI"],
        "capital_pct": 0.05,
    },
    "facilities": {
        "certifications": ["Alvará de funcionamento", "ISO 41001 (desejável)"],
        "atestados": ["Atestado de prestação de serviços de facilities"],
        "capital_pct": 0.08,
    },
    "vigilancia": {
        "certifications": ["Autorização PF para vigilância", "Alvará"],
        "atestados": ["Atestado de prestação de serviço de vigilância"],
        "capital_pct": 0.10,
    },
    "saude": {
        "certifications": ["ANVISA", "CRM/CRF", "ISO 13485 (desejável)"],
        "atestados": ["Atestado de fornecimento na área de saúde"],
        "capital_pct": 0.10,
    },
    "_default": {
        "certifications": [],
        "atestados": ["Atestado de fornecimento similar"],
        "capital_pct": 0.05,
    },
}


def compute_qualification_gap_analysis(
    edital: dict,
    empresa: dict,
    object_compat: dict,
    sector_key: str,
) -> dict:
    """Separate sector incompatibility from addressable operational gaps.

    Category 1: INCOMPATÍVEL_CNAE — permanent discard (object outside all company CNAEs)
    Category 2: LACUNA_OPERACIONAL — compatible but can't participate NOW (with remediation plan)
    """
    compat_score = object_compat.get("score", 0.5)
    compat_level = object_compat.get("compatibility", "DESCONHECIDA")

    # Category 1: CNAE incompatibility
    if compat_score < 0.2 and compat_level == "BAIXA":
        obj_text = (edital.get("objeto", "") or "")[:120]
        cnae_principal = empresa.get("cnae_principal", "N/I")
        return {
            "filter_result": "INCOMPATÍVEL_CNAE",
            "incompatibility_rationale": (
                f"Objeto \"{obj_text}\" é incompatível com o CNAE principal "
                f"({cnae_principal}) e secundários da empresa"
            ),
            "operational_gaps": [],
            "readiness_score": 0,
            "development_plan": [],
            "_source": _source_tag("CALCULATED"),
        }

    # Category 2: Compatible but operational gaps exist
    reqs = _SECTOR_REQUIREMENTS_DETAILED.get(sector_key, _SECTOR_REQUIREMENTS_DETAILED["_default"])
    valor = _safe_float(edital.get("valor_estimado"))
    capital = _safe_float(empresa.get("capital_social"))
    gaps: list[dict] = []

    # Capital gap
    capital_pct = reqs.get("capital_pct", 0.05)
    min_capital = valor * capital_pct
    if capital > 0 and valor > 0 and capital < min_capital:
        deficit = min_capital - capital
        def _fmt(v: float) -> str:
            return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        gaps.append({
            "gap_type": "CAPITAL",
            "description": f"Capital social ({_fmt(capital)}) abaixo do mínimo estimado ({_fmt(min_capital)}) para edital de {_fmt(valor)}",
            "addressable": True,
            "estimated_timeline": "3-6 meses (alteração contratual)",
            "action_required": f"Integralizar capital adicional de {_fmt(deficit)}",
        })

    # Certification gaps — skip mandatory professional registrations if company
    # already has government contracts or matching CNAE (registration is implicit:
    # you can't win gov contracts without the sector's professional council registration)
    historico_pre = empresa.get("historico_contratos", [])
    has_gov_contracts = len(historico_pre) > 0 if isinstance(historico_pre, list) else False

    # Registrations that are prerequisites for operating in the sector —
    # if the company exists and has CNAE in the sector, it necessarily holds these
    _IMPLICIT_IF_OPERATING = {
        "crea", "cau",        # Engineering / Architecture
        "crm", "crf",         # Medicine / Pharmacy
        "crc",                # Accounting
        "oab",                # Law
        "coren", "cofen",     # Nursing
        "crn",                # Nutrition
        "crmv",               # Veterinary
        "confea",             # Engineering (federal)
        "crt",                # Technicians
        "registro ativo",     # Generic "active registration"
        "registro profissional",
    }

    for cert in reqs.get("certifications", []):
        cert_lower = cert.lower()
        # If company has gov contracts OR is in a matching sector,
        # mandatory professional registrations are implied
        if has_gov_contracts:
            if any(reg in cert_lower for reg in _IMPLICIT_IF_OPERATING):
                continue  # Skip — implied by operational history
        gaps.append({
            "gap_type": "CERTIFICAÇÃO",
            "description": f"Verificar se possui: {cert}",
            "addressable": True,
            "estimated_timeline": "3-12 meses" if "ISO" in cert else "1-3 meses",
            "action_required": f"Obter ou renovar {cert}",
        })

    # Atestado gaps — semantic cross-reference edital vs historical contracts
    historico = empresa.get("historico_contratos", [])
    historico_list = historico if isinstance(historico, list) else []

    # Stop words: generic terms that don't indicate technical similarity
    _ACERVO_STOP = {
        "contratação", "contratacao", "empresa", "serviço", "servico", "serviços",
        "servicos", "execução", "execucao", "objeto", "municipal", "município",
        "municipio", "prefeitura", "estado", "federal", "governo", "público",
        "publica", "publico", "valor", "prazo", "conforme", "mediante", "através",
        "forma", "acordo", "termo", "referência", "referencia", "edital",
        "fornecimento", "material", "diversos", "demais", "necessário", "necessario",
    }

    obj_edital = (edital.get("objeto", "") or "").lower()
    obj_edital_words = {
        w.rstrip(".,;:()") for w in obj_edital.split()
        if len(w) >= 6 and w.rstrip(".,;:()") not in _ACERVO_STOP
    }

    best_match_info = None
    best_score = 0
    for c in historico_list:
        obj_hist = (c.get("objeto", "") or "").lower()
        hist_words = {
            w.rstrip(".,;:()") for w in obj_hist.split()
            if len(w) >= 6 and w.rstrip(".,;:()") not in _ACERVO_STOP
        }
        if not hist_words or not obj_edital_words:
            continue
        overlap = hist_words & obj_edital_words
        jaccard = len(overlap) / len(hist_words | obj_edital_words)
        score = len(overlap) * (1 + jaccard)
        # Require ≥3 meaningful keywords AND ≥15% Jaccard similarity
        if score > best_score and len(overlap) >= 3 and jaccard >= 0.15:
            best_score = score
            best_match_info = {
                "orgao": c.get("orgao", "")[:50],
                "esfera": c.get("esfera", ""),
                "valor": c.get("valor", 0),
                "objeto": (c.get("objeto", "") or "")[:80],
                "overlap": sorted(overlap)[:5],
                "jaccard": round(jaccard, 2),
            }

    n_historico = len(historico_list)
    n_sector_relevant = empresa.get("_sector_relevant_contracts", 0)

    if best_match_info:
        # Semantic match found — cite the specific contract
        val_fmt = f"R$ {_safe_float(best_match_info['valor']):,.0f}".replace(",", ".")
        gaps.append({
            "gap_type": "ACERVO_EXISTENTE",
            "description": (
                f"Acervo técnico inferido: \"{best_match_info['objeto']}\" em "
                f"{best_match_info['orgao']} ({best_match_info['esfera']}, {val_fmt}). "
                f"Termos em comum: {', '.join(best_match_info['overlap'])}"
            ),
            "addressable": False,
            "estimated_timeline": "Já disponível",
            "action_required": "Confirmar que atestados e CATs estão disponíveis para juntada célere na habilitação",
        })
    elif n_historico >= 10 and n_sector_relevant < 3:
        # CRITICAL: Company has many contracts but very few/none in the target sector.
        # This is NOT "acervo presumido" — it's a sector mismatch.
        if n_sector_relevant == 0:
            detail = "NENHUM no setor de atuação dos editais analisados"
        else:
            detail = f"apenas {n_sector_relevant} no setor (de {n_historico} total)"
        gaps.append({
            "gap_type": "ACERVO_SETOR_DIVERGENTE",
            "description": (
                f"ALERTA: CNAE inconsistente com histórico — verificar acervo. "
                f"Empresa possui {n_historico} contrato(s) governamental(is), "
                f"porém {detail}. "
                f"O histórico registrado no PNCP indica atuação em segmento distinto. "
                f"Acervo técnico no setor NÃO pode ser presumido."
            ),
            "addressable": True,
            "estimated_timeline": "6-12 meses (execução de contrato no setor + obtenção de CAT)",
            "action_required": (
                "Verificar se a empresa possui contratos no setor não registrados no PNCP. "
                "Se confirmada ausência, iniciar construção de acervo via obras de menor porte "
                "ou consórcio com empresa que possua atestados no setor."
            ),
        })
    elif n_historico >= 10 and n_sector_relevant >= 3:
        # Extensive contract history WITH sector-relevant contracts.
        # Safely presume acervo.
        gaps.append({
            "gap_type": "ACERVO_PRESUMIDO",
            "description": (
                f"Empresa com {n_historico} contrato(s) governamental(is) no histórico, "
                f"dos quais {n_sector_relevant} no setor de atuação — "
                f"acervo técnico e atestados presumidos pela experiência setorial acumulada"
            ),
            "addressable": False,
            "estimated_timeline": "Já disponível",
            "action_required": (
                "Confirmar disponibilidade dos atestados de capacidade técnica e CATs "
                "dos responsáveis técnicos para juntada célere na fase de habilitação"
            ),
        })
    else:
        # Few or no contracts — flag specific missing attestations
        for atestado in reqs.get("atestados", []):
            gaps.append({
                "gap_type": "ATESTADO",
                "description": f"Sem acervo comprovado: {atestado}",
                "addressable": True,
                "estimated_timeline": "6-12 meses (execução de contrato similar)",
                "action_required": f"Executar obra/serviço similar e obter {atestado}",
            })

    # Readiness score: 100 if no gaps, decreases with each gap
    readiness = max(0, 100 - len(gaps) * 20)

    # Development plan: prioritized list of actions
    development_plan = []
    for i, g in enumerate(sorted(gaps, key=lambda x: x["gap_type"]), 1):
        development_plan.append({
            "priority": i,
            "action": g["action_required"],
            "timeline": g["estimated_timeline"],
            "gap_type": g["gap_type"],
        })

    return {
        "filter_result": "COMPATÍVEL",
        "incompatibility_rationale": None,
        "operational_gaps": gaps,
        "readiness_score": readiness,
        "development_plan": development_plan,
        "_source": _source_tag("CALCULATED"),
    }


# ============================================================
# E5: HISTORICAL DISPUTE STATISTICS
# ============================================================

_VALUE_BRACKETS = [
    (0, 100_000, "0-100K"),
    (100_000, 500_000, "100K-500K"),
    (500_000, 2_000_000, "500K-2M"),
    (2_000_000, float("inf"), "2M+"),
]


def _value_bracket(valor: float) -> str:
    for low, high, label in _VALUE_BRACKETS:
        if low <= valor < high:
            return label
    return "2M+"


def compute_historical_dispute_stats(all_contracts: list[dict]) -> dict:
    """Aggregate historical dispute statistics from competitive intel contracts.

    Groups by modality × value bracket to produce:
    - avg participants, avg discount, adjudication rate, desert/failed rate
    """
    from collections import Counter, defaultdict

    stats: dict[str, dict] = defaultdict(lambda: {
        "n_procurements": 0, "suppliers": [], "discounts": [],
        "adjudicated": 0, "desert": 0, "failed": 0,
    })

    # Build supplier frequency for recurring detection
    supplier_counts: dict[str, dict] = defaultdict(lambda: {"n": 0, "ufs": set()})

    for c in all_contracts:
        fornecedor = c.get("fornecedor", "") or c.get("cnpj_fornecedor", "")
        valor_est = _safe_float(c.get("valor_estimado", 0))
        valor_hom = _safe_float(c.get("valor", c.get("valor_homologado", 0)))
        modalidade = (c.get("modalidade", "") or "").lower().strip()
        bracket = _value_bracket(max(valor_est, valor_hom))
        key = f"{modalidade}_{bracket}" if modalidade else f"outro_{bracket}"

        bucket = stats[key]
        bucket["n_procurements"] += 1
        if fornecedor:
            bucket["suppliers"].append(fornecedor)
            cnpj_f = c.get("cnpj_fornecedor", fornecedor)
            supplier_counts[cnpj_f]["n"] += 1
            uf = c.get("uf", "")
            if uf:
                supplier_counts[cnpj_f]["ufs"].add(uf)

        # Discount calculation
        if valor_est > 0 and valor_hom > 0:
            discount = (valor_est - valor_hom) / valor_est
            if -0.5 <= discount <= 0.9:  # Sanity check
                bucket["discounts"].append(discount)

        # Outcome (simplified: if valor_hom > 0 = adjudicated)
        if valor_hom > 0:
            bucket["adjudicated"] += 1
        # Note: desert/failed detection requires status field which may not be available

    # Aggregate
    stats_by_typology = {}
    for key, bucket in stats.items():
        n = bucket["n_procurements"]
        if n == 0:
            continue
        unique_suppliers = len(set(bucket["suppliers"]))
        stats_by_typology[key] = {
            "avg_participants": round(unique_suppliers / max(n, 1), 1),
            "avg_discount_pct": round(
                sum(bucket["discounts"]) / len(bucket["discounts"]) * 100, 1
            ) if bucket["discounts"] else None,
            "adjudication_rate": round(bucket["adjudicated"] / n, 2),
            "sample_size": n,
        }

    # Recurring suppliers (3+ contracts) with market_share
    total_supplier_contracts = sum(v["n"] for v in supplier_counts.values())
    recurring = [
        {
            "nome_ou_cnpj": k,
            "n_contracts": v["n"],
            "ufs": sorted(v["ufs"]),
            "market_share": round(v["n"] / total_supplier_contracts, 3) if total_supplier_contracts > 0 else 0,
        }
        for k, v in sorted(supplier_counts.items(), key=lambda x: x[1]["n"], reverse=True)
        if v["n"] >= 3
    ][:10]  # Top 10

    return {
        "stats_by_typology": stats_by_typology,
        "recurring_suppliers": recurring,
        "total_contracts_analyzed": len(all_contracts),
        "_source": _source_tag("CALCULATED"),
    }


# ============================================================
# E6: ORGAN RISK PROFILE
# ============================================================

def compute_organ_risk_profile(
    edital: dict,
    organ_contracts: list[dict],
    sector_key: str,
) -> dict:
    """Analyze risk from the EDITAL perspective (not company perspective).

    Checks: organ track record, timeline adequacy, amendment patterns.
    """
    n_contracts = len(organ_contracts)
    if n_contracts == 0:
        return {
            "organ_track_record": "INDETERMINADO",
            "similar_published": 0,
            "adjudication_rate": None,
            "desert_rate": None,
            "has_prior_similar": False,
            "timeline_assessment": "INDETERMINADO",
            "timeline_rationale": "Sem histórico do órgão para avaliar",
            "amendment_history": None,
            "risk_flags": [],
            "_source": _source_tag("CALCULATED", "Sem contratos do órgão"),
        }

    # Count adjudicated (has valor > 0) vs likely desert (no valor)
    adjudicated = sum(1 for c in organ_contracts if _safe_float(c.get("valor", 0)) > 0)
    adj_rate = adjudicated / n_contracts if n_contracts > 0 else 0
    desert_rate = 1.0 - adj_rate

    # Check if organ has published similar object before
    edital_obj = (edital.get("objeto", "") or "").lower()
    obj_words = set(w for w in edital_obj.split() if len(w) > 4)
    similar_count = 0
    for c in organ_contracts:
        c_obj = (c.get("objeto", "") or "").lower()
        matches = sum(1 for w in obj_words if w in c_obj)
        if matches >= 2:
            similar_count += 1

    has_prior_similar = similar_count > 0

    # Timeline assessment
    valor = _safe_float(edital.get("valor_estimado"))
    dias = edital.get("dias_restantes")
    if dias is not None and valor > 0:
        # Simple heuristic: complex projects need more time
        if sector_key in ("engenharia", "engenharia_rodoviaria"):
            min_days = 30 if valor < 500_000 else (60 if valor < 2_000_000 else 90)
        else:
            min_days = 15 if valor < 500_000 else 30
        if dias >= min_days:
            timeline = "ADEQUADO"
            timeline_rationale = f"Prazo de {dias} dias adequado para o porte/complexidade"
        elif dias >= min_days * 0.5:
            timeline = "APERTADO"
            timeline_rationale = f"Prazo de {dias} dias apertado (recomendável {min_days}+ dias)"
        else:
            timeline = "INSUFICIENTE"
            timeline_rationale = f"Prazo de {dias} dias insuficiente (mínimo recomendável: {min_days} dias)"
    else:
        timeline = "INDETERMINADO"
        timeline_rationale = "Prazo ou valor indisponível para avaliação"

    # Risk flags
    risk_flags = []
    if desert_rate > 0.20:
        risk_flags.append(f"Órgão com histórico de licitações desertas ({desert_rate:.0%})")
    if not has_prior_similar:
        risk_flags.append("Órgão nunca publicou contratação similar — risco de especificação inadequada")
    if timeline == "INSUFICIENTE":
        risk_flags.append(f"Prazo insuficiente: {dias} dias para contrato de R$ {valor:,.0f}")

    # Track record classification
    if adj_rate >= 0.80 and has_prior_similar:
        track_record = "BOM"
    elif adj_rate >= 0.50:
        track_record = "REGULAR"
    else:
        track_record = "RISCO"

    return {
        "organ_track_record": track_record,
        "similar_published": similar_count,
        "adjudication_rate": round(adj_rate, 2),
        "desert_rate": round(desert_rate, 2),
        "has_prior_similar": has_prior_similar,
        "timeline_assessment": timeline,
        "timeline_rationale": timeline_rationale,
        "amendment_history": None,  # Future: extract from Portal da Transparência
        "risk_flags": risk_flags,
        "_source": _source_tag("CALCULATED", f"{n_contracts} contratos do órgão"),
    }


# ============================================================
# E7: REGIONAL CLUSTER ANALYSIS
# ============================================================

def compute_regional_clusters(editais: list[dict]) -> dict:
    """Cluster editais by geographic proximity for shared mobilization detection.

    Uses lat/lon from distance calculations (Nominatim) and greedy 150km clustering.
    """
    import math

    # Extract editais with coordinates
    geo_editais = []
    for i, ed in enumerate(editais):
        dist = ed.get("distancia", {})
        if isinstance(dist, dict):
            lat = dist.get("dest_lat")
            lon = dist.get("dest_lon")
            if lat is not None and lon is not None:
                geo_editais.append({"index": i, "lat": lat, "lon": lon, "ed": ed})

    if len(geo_editais) < 2:
        return {
            "clusters": [],
            "isolated_editais": list(range(len(editais))),
            "clustering_method": "greedy_150km_radius",
            "_source": _source_tag("CALCULATED", "Menos de 2 editais com coordenadas"),
        }

    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    CLUSTER_RADIUS_KM = 150.0
    used = set()
    clusters = []

    # Sort by value (highest first) to use as cluster centers
    geo_editais.sort(key=lambda x: _safe_float(x["ed"].get("valor_estimado", 0)), reverse=True)

    for ge in geo_editais:
        if ge["index"] in used:
            continue

        # Start new cluster with this edital as center
        cluster_members = [ge]
        used.add(ge["index"])

        for other in geo_editais:
            if other["index"] in used:
                continue
            dist_km = _haversine_km(ge["lat"], ge["lon"], other["lat"], other["lon"])
            if dist_km <= CLUSTER_RADIUS_KM:
                cluster_members.append(other)
                used.add(other["index"])

        if len(cluster_members) >= 2:
            # Compute cluster metrics
            center_mun = cluster_members[0]["ed"].get("municipio", "")
            center_uf = cluster_members[0]["ed"].get("uf", "")
            total_valor = sum(_safe_float(m["ed"].get("valor_estimado", 0)) for m in cluster_members)

            # Max radius from center
            max_radius = max(
                _haversine_km(ge["lat"], ge["lon"], m["lat"], m["lon"])
                for m in cluster_members
            )

            # Timeline overlap check
            deadlines = []
            for m in cluster_members:
                enc = m["ed"].get("data_encerramento")
                if enc:
                    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                        try:
                            deadlines.append(datetime.strptime(str(enc)[:10], fmt))
                            break
                        except ValueError:
                            continue

            timeline_overlap = False
            if len(deadlines) >= 2:
                deadlines.sort()
                span_days = (deadlines[-1] - deadlines[0]).days
                timeline_overlap = span_days <= 180  # Within 6 months

            clusters.append({
                "id": len(clusters) + 1,
                "center_municipio": center_mun,
                "center_uf": center_uf,
                "radius_km": round(max_radius),
                "editais_indices": [m["index"] for m in cluster_members],
                "n_editais": len(cluster_members),
                "total_valor": round(total_valor),
                "timeline_overlap": timeline_overlap,
                "recommendation": (
                    f"Mobilização única para {len(cluster_members)} editais "
                    f"na região de {center_mun}/{center_uf} "
                    f"(raio de {max_radius:.0f}km)"
                ),
            })

    # Isolated editais (not in any cluster)
    all_clustered = set()
    for cl in clusters:
        all_clustered.update(cl["editais_indices"])
    isolated = [i for i in range(len(editais)) if i not in all_clustered]

    return {
        "clusters": clusters,
        "isolated_editais": isolated,
        "clustering_method": "greedy_150km_radius",
        "_source": _source_tag("CALCULATED"),
    }


# ============================================================
# MAIN DETERMINISTIC CALCULATION CHAIN
# ============================================================

def compute_all_deterministic(
    editais: list[dict],
    empresa: dict,
    sicaf: dict,
    sector_key: str,
    sector_keywords: list[str] | None = None,
) -> dict:
    """Compute all deterministic intelligence for editais. Mutates in place.

    Chain: risk_score → win_probability → roi_potential → chronogram
           + object_compatibility, habilitacao, competitive_analysis, risk_analysis
           + E4 qualification gaps, E6 organ risk, E8 maturity
    Portfolio analysis + E7 regional clusters run after per-edital loop.
    Returns dict with portfolio, maturity, dispute_stats, regional_clusters.
    """
    print(f"\n📊 Calculando inteligência estratégica ({len(editais)} editais)")

    # E8: Detect maturity profile once for the company
    maturity = detect_maturity_profile(empresa)
    empresa["maturity_profile"] = maturity
    print(f"  Perfil de maturidade: {maturity['profile']} ({maturity['rationale']})")

    # Sector-relevant contract count — critical for acervo gap analysis
    # Use word boundary matching (not substring) to avoid false positives
    _sector_kw = [k.lower() for k in (sector_keywords or []) if len(k) >= 5]
    import re as _re
    _sector_pattern = _re.compile(
        r"\b(" + "|".join(_re.escape(k) for k in _sector_kw) + r")", _re.IGNORECASE
    ) if _sector_kw else None
    historico = empresa.get("historico_contratos", [])
    historico_list = historico if isinstance(historico, list) else []
    sector_relevant_count = 0
    if _sector_pattern and historico_list:
        for c in historico_list:
            obj = (c.get("objeto", "") or "")
            if _sector_pattern.search(obj):
                sector_relevant_count += 1
    empresa["_sector_relevant_contracts"] = sector_relevant_count
    empresa["_sector_divergence"] = None  # Top-level alert for report rendering
    if historico_list:
        pct = round(100 * sector_relevant_count / len(historico_list), 1)
        print(f"  Contratos setoriais: {sector_relevant_count}/{len(historico_list)} ({pct}%)")
        if sector_relevant_count < 3 and len(historico_list) >= 10:
            empresa["_sector_divergence"] = {
                "total_contracts": len(historico_list),
                "sector_contracts": sector_relevant_count,
                "pct": pct,
                "alert": (
                    f"CNAE inconsistente com histórico: empresa possui {len(historico_list)} "
                    f"contratos governamentais, porém {'NENHUM' if sector_relevant_count == 0 else f'apenas {sector_relevant_count}'} "
                    f"no setor de atuação dos editais. O histórico registrado indica atuação "
                    f"em segmento distinto. Verificar acervo técnico antes de qualquer participação."
                ),
            }
            print(f"  ⚠ ALERTA CRÍTICO: {len(historico_list)} contratos mas {'ZERO' if sector_relevant_count == 0 else f'apenas {sector_relevant_count}'} no setor — CNAE diverge do histórico")

    empresa_cnaes = empresa.get("cnaes_secundarios", "")
    if isinstance(empresa_cnaes, list):
        empresa_cnaes = " ".join(str(c) for c in empresa_cnaes)
    historico = empresa.get("historico_contratos", [])

    # E5: Collect all competitive intel contracts for dispute stats
    all_competitive_contracts: list[dict] = []

    for ed in editais:
        # --- Core scoring chain ---
        rs = compute_risk_score(ed, empresa, sicaf, sector_key)

        # CRÍTICA 2: If vetoed, skip maturity adjustments and set minimal outputs
        if rs.get("vetoed"):
            rs["maturity_adjustment"] = {"profile": maturity["profile"], "hab_delta": 0, "geo_delta": 0}
            ed["risk_score"] = rs
            ed["win_probability"] = {
                "probability": 0.0, "confidence": "alta", "base_rate": 0,
                "n_unique_suppliers": 0, "n_contracts_analyzed": 0, "n_contracts_raw": 0,
                "sector_filtered": False, "hhi": 0, "top_supplier_share": 0,
                "incumbency_bonus": 0, "modality_multiplier": 0, "viability_factor": 0,
                "contextual_multiplier": 0,
                "_source": _source_tag("CALCULATED", "VETADO — probabilidade zero"),
            }
            ed["roi_potential"] = {
                "roi_min": 0, "roi_max": 0, "probability": 0.0,
                "margin_range": "N/A", "confidence": "alta",
                "strategic_reclassification": None, "reclassification_rationale": None,
                "calculation_memory": {"formula": "VETADO — ROI não calculado"},
                "_source": _source_tag("CALCULATED", "VETADO"),
            }
            ed["cronograma"] = build_reverse_chronogram(ed)
        else:
            # E8: Apply maturity adjustments (only for non-vetoed editais)
            valor = _safe_float(ed.get("valor_estimado"))
            mat_hab_delta = 0
            mat_geo_delta = 0
            if maturity["profile"] == "ENTRANTE" and valor > _MATURITY_HIGH_VALUE_THRESHOLD:
                mat_hab_delta = -15
                rs["habilitacao"] = max(0, rs["habilitacao"] + mat_hab_delta)
            elif maturity["profile"] == "REGIONAL":
                uf_sede = (empresa.get("uf", "") or "").upper()
                uf_edital = (ed.get("uf", "") or "").upper()
                if uf_sede and uf_edital and uf_sede == uf_edital:
                    mat_geo_delta = 10
                    rs["geografico"] = min(100, rs["geografico"] + mat_geo_delta)
            elif maturity["profile"] == "ESTABELECIDO":
                mat_hab_delta = 10
                rs["habilitacao"] = min(100, rs["habilitacao"] + mat_hab_delta)

            # Recompute total with maturity adjustments (respecting threshold gates)
            weights = rs["weights"]
            total_recomputed = round(
                rs["habilitacao"] * weights["hab"]
                + rs["financeiro"] * weights["fin"]
                + rs["geografico"] * weights["geo"]
                + rs["prazo"] * weights["prazo"]
                + rs["competitivo"] * weights["comp"]
            )
            # Re-apply threshold gates after maturity adjustment
            if rs.get("threshold_applied"):
                if "prazo" in (rs.get("threshold_applied") or ""):
                    total_recomputed = min(total_recomputed, 20)
                if "financeiro" in (rs.get("threshold_applied") or ""):
                    total_recomputed = min(total_recomputed, 25)
                if "habilitacao" in (rs.get("threshold_applied") or ""):
                    total_recomputed = min(total_recomputed, 30)
            rs["total"] = total_recomputed
            rs["maturity_adjustment"] = {
                "profile": maturity["profile"],
                "hab_delta": mat_hab_delta,
                "geo_delta": mat_geo_delta,
            }
            ed["risk_score"] = rs

            win_prob = compute_win_probability(
                ed, empresa, ed.get("competitive_intel", []), sector_key, rs["total"],
            )
            ed["win_probability"] = win_prob

            ed["roi_potential"] = compute_roi_potential(ed, sector_key, win_prob)
            ed["cronograma"] = build_reverse_chronogram(ed)

        # --- Object compatibility (spectral) ---
        objeto = ed.get("objeto", ed.get("objetoCompra", ""))
        ed["object_compatibility"] = compute_object_compatibility(
            objeto, empresa_cnaes, sector_key, historico,
        )

        # --- Habilitação gap analysis ---
        ed["habilitacao_analysis"] = compute_habilitacao_analysis(
            ed, empresa, sicaf, sector_key,
        )

        # --- E4: Qualification gap analysis (sector compat vs operational) ---
        ed["qualification_gap"] = compute_qualification_gap_analysis(
            ed, empresa, ed["object_compatibility"], sector_key,
        )

        # --- Competitive analysis (per-edital) ---
        contracts = ed.get("competitive_intel", [])
        ed["competitive_analysis"] = compute_competitive_analysis(contracts)
        all_competitive_contracts.extend(contracts)

        # --- E6: Organ risk profile ---
        ed["organ_risk"] = compute_organ_risk_profile(ed, contracts, sector_key)

        # --- Systemic risk flags ---
        ed["risk_analysis"] = compute_risk_analysis(
            ed, ed["competitive_analysis"], sector_key,
        )

    # --- Portfolio analysis (cross-edital, sets ed["strategic_category"]) ---
    portfolio = compute_portfolio_analysis(editais, empresa, sector_key)

    # --- E5: Historical dispute stats (aggregate) ---
    dispute_stats = compute_historical_dispute_stats(all_competitive_contracts)

    # --- E7: Regional cluster analysis ---
    regional_clusters = compute_regional_clusters(editais)
    if regional_clusters["clusters"]:
        print(f"  Clusters regionais: {len(regional_clusters['clusters'])} identificados")
        for cl in regional_clusters["clusters"]:
            print(f"    → {cl['center_municipio']}/{cl['center_uf']}: {cl['n_editais']} editais, raio {cl['radius_km']}km")

    # Summary
    scores = [ed["risk_score"]["total"] for ed in editais]
    probs = [ed["win_probability"]["probability"] for ed in editais]
    habs = [ed.get("habilitacao_analysis", {}).get("status", "?") for ed in editais]
    comps = [ed.get("object_compatibility", {}).get("compatibility", "?") for ed in editais]
    if scores:
        print(f"  Risk scores: min={min(scores)}, max={max(scores)}, avg={sum(scores) / len(scores):.0f}")
        print(f"  Win probs:   min={min(probs):.1%}, max={max(probs):.1%}, avg={sum(probs) / len(probs):.1%}")
        hab_counts = {k: habs.count(k) for k in set(habs)}
        comp_counts = {k: comps.count(k) for k in set(comps)}
        print(f"  Habilitação: {hab_counts}")
        print(f"  Compat.:     {comp_counts}")
        qw = len(portfolio.get("quick_wins", []))
        inv = len(portfolio.get("strategic_investments", []))
        opp = len(portfolio.get("opportunities", []))
        print(f"  Portfolio:   {qw} quick wins, {inv} investimentos, {opp} oportunidades")

    return {
        "portfolio": portfolio,
        "maturity_profile": maturity,
        "dispute_stats": dispute_stats,
        "regional_clusters": regional_clusters,
    }


# ============================================================
# SICAF COLLECTION (via collect-sicaf.py subprocess)
# ============================================================

def collect_sicaf(cnpj14: str, verbose: bool = True) -> dict:
    """Collect SICAF data by invoking collect-sicaf.py as a subprocess.

    Opens a headed browser for the user to solve the captcha,
    then extracts CRC + restriction data automatically.
    """
    import subprocess
    import tempfile

    attempted_at = _today().strftime("%d/%m/%Y %H:%M")

    sicaf_script = Path(__file__).parent / "collect-sicaf.py"
    if not sicaf_script.exists():
        if verbose:
            print("  ⚠ collect-sicaf.py não encontrado")
        return {
            "status": "FALHA_COLETA",
            "attempted_at": attempted_at,
            "error_type": "SCRIPT_NOT_FOUND",
            "error_detail": "Arquivo collect-sicaf.py não encontrado no diretório scripts/",
            "_source": _source_tag("API_FAILED", "collect-sicaf.py não encontrado"),
        }

    # Use a temp file for output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as tmp:
        tmp_path = tmp.name

    try:
        if verbose:
            print("\n🔐 SICAF — Abrindo navegador para verificação cadastral")
            print("   ➜ Resolva o captcha quando o navegador abrir (~5s por consulta)")

        cmd = [
            sys.executable,
            str(sicaf_script),
            "--cnpj", cnpj14,
            "--output", tmp_path,
            "--skip-linhas",
        ]

        result = subprocess.run(
            cmd,
            timeout=300,  # 5 min max (includes captcha wait time)
            capture_output=not verbose,
            text=True,
        )

        if result.returncode != 0:
            detail = "Subprocess falhou"
            if result.stderr:
                detail += f": {result.stderr[:200]}"
            if verbose:
                print(f"  ⚠ SICAF falhou (exit code {result.returncode})")
            return {
                "status": "FALHA_COLETA",
                "attempted_at": attempted_at,
                "error_type": "SUBPROCESS_FAILED",
                "error_detail": detail,
                "_source": _source_tag("API_FAILED", detail),
            }

        # Read the output JSON
        tmp_file = Path(tmp_path)
        if not tmp_file.exists() or tmp_file.stat().st_size == 0:
            if verbose:
                print("  ⚠ SICAF: arquivo de saída vazio")
            return {
                "status": "FALHA_COLETA",
                "attempted_at": attempted_at,
                "error_type": "EMPTY_OUTPUT",
                "error_detail": "Arquivo de saída do SICAF vazio ou inexistente",
                "_source": _source_tag("API_FAILED", "Output file empty"),
            }

        with open(tmp_path, "r", encoding="utf-8") as f:
            sicaf_data = json.load(f)

        if verbose:
            status = sicaf_data.get("status", "desconhecido")
            print(f"  ✅ SICAF coletado: {status}")

        return sicaf_data

    except subprocess.TimeoutExpired:
        if verbose:
            print("  ⚠ SICAF: timeout (5 min) — captcha não resolvido?")
        return {
            "status": "FALHA_COLETA",
            "attempted_at": attempted_at,
            "error_type": "TIMEOUT",
            "error_detail": "Captcha não resolvido em 5 minutos",
            "_source": _source_tag("API_FAILED", "Timeout — captcha não resolvido em 5 min"),
        }
    except Exception as e:
        if verbose:
            print(f"  ⚠ SICAF erro: {e}")
        return {
            "status": "FALHA_COLETA",
            "attempted_at": attempted_at,
            "error_type": "EXCEPTION",
            "error_detail": str(e)[:200],
            "_source": _source_tag("API_FAILED", str(e)[:200]),
        }
    finally:
        # Cleanup temp file
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


# ============================================================
# ASSEMBLE FINAL JSON
# ============================================================

def assemble_report_data(
    empresa: dict,
    transparencia: dict,
    setor: str,
    keywords: list[str],
    editais_pncp: list[dict],
    pncp_source: dict,
    editais_pcp: list[dict],
    pcp_source: dict,
    querido_diario: list[dict],
    qd_source: dict,
    distancias: dict[str, dict],
    sicaf: dict,
    brasilapi: dict | None = None,
    ibge_data: dict | None = None,
    ufs_meta: dict | None = None,
) -> dict:
    """Assemble all collected data into the final JSON structure."""

    # Merge empresa + transparencia
    empresa_full = {**empresa}
    empresa_full["sancoes"] = transparencia["sancoes"]
    empresa_full["sancoes_source"] = transparencia["sancoes_source"]
    empresa_full["historico_contratos"] = transparencia["historico_contratos"]
    empresa_full["historico_source"] = transparencia["historico_source"]

    # Merge + dedup editais (PNCP priority)
    all_editais = list(editais_pncp)  # PNCP first (priority)
    pncp_links = {ed.get("link") for ed in editais_pncp if ed.get("link")}
    pcp_dedup_count = 0
    pcp_added_count = 0
    for ed in editais_pcp:
        if ed.get("link") not in pncp_links:
            all_editais.append(ed)
            pcp_added_count += 1
        else:
            pcp_dedup_count += 1

    # Update source details with dedup info
    if isinstance(pncp_source, dict):
        old = pncp_source.get("detail", "")
        pncp_source["detail"] = f"{old}, {len(editais_pncp)} incluídos no relatório" if old else f"{len(editais_pncp)} editais incluídos"
    if isinstance(pcp_source, dict):
        old = pcp_source.get("detail", "")
        if editais_pcp:
            pcp_source["detail"] = f"{len(editais_pcp)} obtidos, {pcp_dedup_count} duplicados removidos, {pcp_added_count} complementares incluídos"
        elif old:
            pcp_source["detail"] = old
        else:
            pcp_source["detail"] = "Nenhum edital complementar encontrado"

    # Sort by dias_restantes ascending (most urgent first)
    all_editais.sort(key=lambda e: (
        e.get("dias_restantes") if e.get("dias_restantes") is not None else 999,
    ))

    # Attach distances
    for ed in all_editais:
        mun = ed.get("municipio", "")
        uf = ed.get("uf", "")
        key = f"{mun}|{uf}"
        if key in distancias:
            ed["distancia"] = distancias[key]

    # Remove internal dedup field only — keep cnpj_orgao/ano_compra/sequencial_compra
    # for competitive intel and document download in downstream phases
    for ed in all_editais:
        ed.pop("_id", None)

    _brasilapi = brasilapi or {}
    _ibge_data = ibge_data or {}
    return {
        "_metadata": {
            "generated_at": _date_iso(_today()),
            "generator": "collect-report-data.py v1.0",
            "sources": {
                "opencnpj": empresa.get("_source", {}),
                "portal_transparencia_sancoes": transparencia["sancoes_source"],
                "portal_transparencia_contratos": transparencia["historico_source"],
                "pncp": pncp_source,
                "pcp_v2": pcp_source,
                "querido_diario": qd_source,
                "sicaf": sicaf.get("_source", {}),
                "brasilapi": _brasilapi.get("_source", _source_tag("UNAVAILABLE")),
                "ibge": _source_tag("API", f"{len([d for d in _ibge_data.values() if d.get('populacao')])} municipios") if _ibge_data else _source_tag("UNAVAILABLE", "Skipped"),
            },
        },
        "empresa": empresa_full,
        "setor": setor,
        "keywords": keywords,
        "ufs_busca": ufs_meta,
        "editais": all_editais,
        "querido_diario": querido_diario,
        "sicaf": sicaf,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Coleta determinística de dados para relatório B2G",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/collect-report-data.py --cnpj 12345678000190
  python scripts/collect-report-data.py --cnpj 09.225.035/0001-01 --ufs MG,SP --dias 30
  python scripts/collect-report-data.py --cnpj 12345678000190 --output custom.json --quiet
        """,
    )
    parser.add_argument("--cnpj", required=False, help="CNPJ da empresa (com ou sem formatação). Obrigatório exceto com --re-enrich.")
    parser.add_argument("--dias", type=int, default=30, help="Período de busca em dias (default: 30)")
    parser.add_argument("--ufs", default="", help="UFs para filtrar, separadas por vírgula (default: UF da sede)")
    parser.add_argument("--output", help="Caminho do JSON de saída (default: auto)")
    parser.add_argument("--quiet", action="store_true", help="Suprimir output verbose")
    parser.add_argument("--skip-distances", action="store_true", help="Pular cálculo de distâncias (mais rápido)")
    parser.add_argument("--skip-docs", action="store_true", help="Pular listagem de documentos PNCP")
    parser.add_argument("--skip-links", action="store_true", help="Pular validação de links PNCP")
    parser.add_argument("--skip-pcp", action="store_true", help="Pular busca PCP v2")
    parser.add_argument("--skip-qd", action="store_true", help="Pular busca Querido Diário")
    parser.add_argument("--skip-competitive", action="store_true", help="Pular coleta de inteligência competitiva")
    parser.add_argument("--skip-ibge", action="store_true", help="Skip IBGE enrichment")
    parser.add_argument("--skip-brasilapi", action="store_true", help="Skip BrasilAPI query")
    parser.add_argument("--re-enrich", help=(
        "Re-enriquecer um JSON existente sem re-coletar APIs. "
        "Recalcula: risk_score, win_probability, roi_potential, cronograma, "
        "portfolio, maturity, dispute_stats, regional_clusters, organ_risk, "
        "qualification_gap, habilitacao_analysis, object_compatibility, risk_analysis. "
        "Uso: --re-enrich docs/reports/data-XXX.json"
    ))

    args = parser.parse_args()

    # ---- RE-ENRICH MODE: reprocess existing JSON without API calls ----
    if args.re_enrich:
        input_path = Path(args.re_enrich)
        if not input_path.exists():
            print(f"ERROR: Arquivo não encontrado: {input_path}")
            sys.exit(1)

        print(f"{'='*60}")
        print(f"🔄 Re-enriquecimento de JSON existente")
        print(f"   Input: {input_path}")
        print(f"{'='*60}")

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        empresa = data.get("empresa", {})
        sicaf = data.get("sicaf", {})

        # Detect sector from existing data or re-map from CNAE
        sector_key = data.get("_sector_key", "")
        re_keywords: list[str] = []
        if not sector_key:
            cnae = empresa.get("cnae_principal", "")
            if cnae:
                _, re_keywords, sector_key = map_sector(cnae)
                print(f"  Setor mapeado: {sector_key}")
            else:
                sector_key = "engineering"  # Safe default
                print(f"  Setor: usando default ({sector_key})")
        else:
            # Try to recover keywords from sector_key
            cnae = empresa.get("cnae_principal", "")
            if cnae:
                _, re_keywords, _ = map_sector(cnae)

        editais = data.get("editais", [])
        print(f"  Editais: {len(editais)}")

        # Run all deterministic computations
        analysis_results = compute_all_deterministic(editais, empresa, sicaf, sector_key, sector_keywords=re_keywords)

        # Store results
        data["portfolio"] = analysis_results["portfolio"]
        data["maturity_profile"] = analysis_results["maturity_profile"]
        data["dispute_stats"] = analysis_results["dispute_stats"]
        data["regional_clusters"] = analysis_results["regional_clusters"]
        data["_sector_key"] = sector_key

        # Coverage diagnostic: compute from local data (no API needed)
        if not data.get("coverage_diagnostic"):
            data["coverage_diagnostic"] = {
                "coverage_rate": 1.0,
                "captured_count": len(editais),
                "total_estimated": len(editais),
                "per_uf": [],
                "warning": None,
                "methodology": "Re-enriquecimento local — cobertura estimada dos editais existentes no JSON.",
                "_source": _source_tag("CALCULATED", "re-enrich mode, sem consulta PNCP"),
            }
            print("  Coverage diagnostic: estimado localmente (sem consulta PNCP)")

        # Output
        output_path = Path(args.output) if args.output else input_path
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ JSON re-enriquecido salvo em: {output_path}")
        print(f"   Campos atualizados: risk_score, win_probability, roi_potential, portfolio,")
        print(f"   maturity_profile, dispute_stats, regional_clusters, organ_risk,")
        print(f"   qualification_gap, habilitacao_analysis, object_compatibility, risk_analysis")
        sys.exit(0)

    if not args.cnpj:
        print("ERROR: --cnpj é obrigatório (exceto com --re-enrich)")
        sys.exit(1)

    cnpj14 = _clean_cnpj(args.cnpj)
    if len(cnpj14) != 14:
        print(f"ERROR: CNPJ inválido: {args.cnpj}")
        sys.exit(1)

    verbose = not args.quiet
    api = ApiClient(verbose=verbose)

    print(f"{'='*60}")
    print(f"📊 Coleta de Dados B2G — CNPJ {_format_cnpj(cnpj14)}")
    print(f"   Período: {args.dias} dias | Data: {_date_iso(_today())}")
    print(f"{'='*60}")

    # ---- Phase 1: Company Profile ----
    empresa = collect_opencnpj(api, cnpj14)

    # BrasilAPI — Simples Nacional
    if not (hasattr(args, 'skip_brasilapi') and args.skip_brasilapi):
        brasilapi = collect_brasilapi(api, cnpj14)
        empresa["simples_nacional"] = brasilapi.get("simples_nacional")
        empresa["mei"] = brasilapi.get("mei")
        empresa["data_opcao_simples"] = brasilapi.get("data_opcao_simples", "")
        if not empresa.get("porte") and brasilapi.get("porte_fallback"):
            empresa["porte"] = brasilapi["porte_fallback"]
    else:
        brasilapi = {"_source": _source_tag("UNAVAILABLE", "Skipped via --skip-brasilapi")}

    # Portal da Transparência
    pt_key = os.environ.get("PORTAL_TRANSPARENCIA_API_KEY", "")
    if not pt_key:
        # Try loading from .env
        env_path = Path("backend/.env")
        if not env_path.exists():
            env_path = Path(__file__).parent.parent / "backend" / ".env"
        if env_path.exists():
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("PORTAL_TRANSPARENCIA_API_KEY"):
                        pt_key = line.split("=", 1)[1].strip().strip("'\"")
                        break

    transparencia = collect_portal_transparencia(api, cnpj14, pt_key)

    # Merge sanctions into empresa for downstream
    empresa["sancoes"] = transparencia["sancoes"]

    # ---- Phase 1b: Contract History FIRST (before sector mapping) ----
    # RATIONALE: Companies often win bids outside their CNAE classification.
    # By fetching actual contract history first, we extract keywords from what
    # the company REALLY does, then use those keywords (enriched with CNAE)
    # to search for open bids. This produces results aligned with the company's
    # actual field of work, not just their registered CNAE.
    print("\n📋 Phase 1b: Histórico de contratos (ANTES do mapeamento de setor)")
    pncp_contratos, pncp_contratos_source = collect_pncp_contratos_fornecedor(api, cnpj14)

    # Merge PT federal + PNCP all-spheres into empresa.historico_contratos
    pt_contratos = transparencia.get("historico_contratos", [])
    merged_contratos = list(pncp_contratos)  # PNCP as base (all spheres)
    pncp_orgao_dates = {(c["orgao"][:30], c["data"][:10]) for c in pncp_contratos}
    for c in pt_contratos:
        key = (c.get("orgao", "")[:30], c.get("data", "")[:10])
        if key not in pncp_orgao_dates:
            c["esfera"] = "Federal"
            c["fonte"] = "Portal da Transparência"
            merged_contratos.append(c)
    transparencia["historico_contratos"] = merged_contratos
    n_pncp = len(pncp_contratos)
    n_pt = len(pt_contratos)
    n_merged = len(merged_contratos)
    transparencia["historico_source"] = _source_tag(
        "API",
        f"{n_merged} contrato(s): {n_pncp} via PNCP (todas as esferas) + {n_pt} via Portal da Transparência (federal)"
    )
    print(f"  Histórico consolidado: {n_merged} contratos ({n_pncp} PNCP + {n_pt} PT)")

    # ---- Cluster contract activities (replaces flat keyword extraction) ----
    contract_clusters = cluster_contract_activities(merged_contratos)
    if contract_clusters:
        labels = [f"{c['label']}({c['count']}, {c['share_pct']}%)" for c in contract_clusters]
        print(f"  Clusters de atividade ({len(contract_clusters)}): {', '.join(labels)}")
        # Flatten keywords for backward-compatible search
        contract_keywords = extract_keywords_from_contracts(merged_contratos)
        print(f"  Keywords extraídas dos clusters ({len(contract_keywords)}): {', '.join(contract_keywords[:10])}{'...' if len(contract_keywords) > 10 else ''}")
    else:
        contract_keywords = []
        print("  Sem histórico de contratos — keywords serão derivadas apenas do CNAE")

    # ---- Sector Mapping (CNAE) ----
    print("\n📋 Mapeando setor via CNAE")
    setor, cnae_keywords, sector_key = map_sector(empresa.get("cnae_principal", ""))
    print(f"  Setor: {setor}")
    print(f"  Keywords CNAE: {', '.join(cnae_keywords[:8])}{'...' if len(cnae_keywords) > 8 else ''}")

    # ---- Merge keywords: Contract history (primary) + CNAE (secondary) ----
    # Contract-derived keywords go first (higher relevance), then CNAE keywords
    # that aren't already covered by contract keywords.
    if contract_keywords:
        existing_lower = {kw.lower() for kw in contract_keywords}
        # Add CNAE keywords that aren't already represented
        for kw in cnae_keywords:
            if kw.lower() not in existing_lower:
                contract_keywords.append(kw)
                existing_lower.add(kw.lower())
        keywords = contract_keywords
        print(f"  Keywords finais ({len(keywords)} = {len(contract_keywords) - len(cnae_keywords) + len([k for k in cnae_keywords if k.lower() in existing_lower])} histórico + CNAE complementar): {', '.join(keywords[:10])}...")
    else:
        keywords = cnae_keywords
        print(f"  Keywords finais: CNAE apenas ({len(keywords)} termos)")

    # ---- UFs (contract-history-first, like keywords) ----
    ufs_meta = {}
    if args.ufs:
        ufs = [u.strip().upper() for u in args.ufs.split(",") if u.strip()]
        ufs_meta = {"source": "manual", "ufs": ufs}
        print(f"  UFs: {', '.join(ufs)} (manual)")
    else:
        uf_sede = empresa.get("uf_sede", "")
        ufs, ufs_meta = extract_ufs_from_contracts(
            merged_contratos,
            uf_sede=uf_sede,
        )
        if ufs_meta.get("source") == "historico_contratos":
            counts = ufs_meta.get("counts", {})
            top_display = ", ".join(f"{u}({counts.get(u, 0)})" for u in ufs)
            print(f"  UFs derivadas do histórico: {top_display}")
        else:
            print(f"  UFs: {', '.join(ufs)} (sede — sem histórico)")
    if not ufs:
        print("  UFs: todas (sem filtro)")

    # ---- Phase 2a: Edital Search (using contract-enriched keywords) ----
    editais_pncp, pncp_source = collect_pncp(api, keywords, ufs, args.dias)

    editais_pcp = []
    pcp_source = _source_tag("UNAVAILABLE", "Skipped")
    if not args.skip_pcp:
        editais_pcp, pcp_source = collect_pcp(api, keywords, ufs, args.dias)

    qd_mencoes = []
    qd_source = _source_tag("UNAVAILABLE", "Skipped")
    if not args.skip_qd:
        nome_empresa = empresa.get("nome_fantasia") or empresa.get("razao_social") or ""
        qd_mencoes, qd_source = collect_querido_diario(api, keywords, nome_empresa, args.dias, ufs=ufs)

    # ---- Filter: remove expired editais BEFORE expensive API calls ----
    all_editais = editais_pncp + editais_pcp
    before_filter = len(all_editais)
    all_editais = [e for e in all_editais if e.get("status_edital") != "ENCERRADO"]
    editais_pncp = [e for e in editais_pncp if e.get("status_edital") != "ENCERRADO"]
    editais_pcp = [e for e in editais_pcp if e.get("status_edital") != "ENCERRADO"]
    dropped = before_filter - len(all_editais)
    if dropped > 0:
        print(f"\n  ⚡ Removidos {dropped} editais já encerrados (restam {len(all_editais)} abertos)")

    # ---- Phase 2b: Document Listing ----
    if not args.skip_docs:
        collect_pncp_documents(api, all_editais)

    # ---- Link Validation ----
    if not args.skip_links:
        validate_pncp_links(api, all_editais)

    # ---- Distance Calculation ----
    distancias: dict[str, dict] = {}
    if not args.skip_distances:
        cidade_sede = empresa.get("cidade_sede", "")
        uf_sede = empresa.get("uf_sede", "")
        if cidade_sede and uf_sede:
            # Unique destinations
            destinos = set()
            for ed in all_editais:
                mun = ed.get("municipio", "")
                uf = ed.get("uf", "")
                if mun and uf:
                    destinos.add((mun, uf))

            print(f"\n📍 Calculando distâncias ({len(destinos)} destinos)")
            for mun, uf in sorted(destinos):
                dist = calculate_distance(api, cidade_sede, uf_sede, mun, uf)
                distancias[f"{mun}|{uf}"] = dist
                time.sleep(1.0)  # Nominatim rate limit
        else:
            print("\n📍 Distâncias: cidade/UF da sede não disponível — pulando")

    # ---- IBGE Municipal Data ----
    ibge_data: dict = {}
    if not (hasattr(args, 'skip_ibge') and args.skip_ibge):
        print(f"\n  IBGE — Enriquecendo municipios")
        municipios_unicos: set = set()
        for ed in all_editais:
            mun = ed.get("municipio", "")
            uf_ed = ed.get("uf", "")
            if mun and uf_ed:
                municipios_unicos.add((mun, uf_ed))
        for mun, uf_ed in sorted(municipios_unicos):
            key = f"{mun}|{uf_ed}"
            ibge_data[key] = collect_ibge_municipio(api, mun, uf_ed)
            time.sleep(0.5)
        for ed in all_editais:
            mun = ed.get("municipio", "")
            uf_ed = ed.get("uf", "")
            key = f"{mun}|{uf_ed}"
            if key in ibge_data:
                ed["ibge"] = ibge_data[key]

    # ---- SICAF (obrigatório — E2) ----
    sicaf = collect_sicaf(cnpj14, verbose=verbose)

    # NOTE: Contract history (PNCP + PT) already collected in Phase 1b (before edital search)
    # and merged into transparencia["historico_contratos"]. No need to repeat here.

    # ---- Competitive Intelligence ----
    if not args.skip_competitive:
        collect_competitive_intel(api, all_editais)

    # ---- Assemble ----
    print(f"\n{'='*60}")
    print("📦 Montando JSON final")

    data = assemble_report_data(
        empresa=empresa,
        transparencia=transparencia,
        setor=setor,
        keywords=keywords,
        editais_pncp=editais_pncp,
        pncp_source=pncp_source,
        editais_pcp=editais_pcp,
        pcp_source=pcp_source,
        querido_diario=qd_mencoes,
        qd_source=qd_source,
        distancias=distancias,
        sicaf=sicaf,
        brasilapi=brasilapi,
        ibge_data=ibge_data,
        ufs_meta=ufs_meta,
    )

    # ---- Deterministic Calculations (risk score, ROI, chronogram, E4-E8) ----
    analysis_results = compute_all_deterministic(data["editais"], data["empresa"], sicaf, sector_key, sector_keywords=keywords)

    # Store cross-edital analysis at top level
    data["portfolio"] = analysis_results["portfolio"]
    data["maturity_profile"] = analysis_results["maturity_profile"]
    data["dispute_stats"] = analysis_results["dispute_stats"]
    data["regional_clusters"] = analysis_results["regional_clusters"]

    # Store activity clusters and keyword source metadata
    data["activity_clusters"] = contract_clusters if contract_clusters else []
    data["_keywords_source"] = "historico" if contract_clusters else "cnae_fallback"

    # ---- E3: Coverage Diagnostic ----
    print("\n📊 Diagnóstico de cobertura")
    data["coverage_diagnostic"] = compute_coverage_diagnostic(
        api, data["editais"], keywords, ufs, sector_key,
    )
    cov = data["coverage_diagnostic"]
    print(f"  Cobertura: {cov['coverage_rate']:.0%} ({cov['captured_count']}/{cov['total_estimated']})")
    if cov["warning"]:
        print(f"  ⚠ {cov['warning']}")

    # ---- Output ----
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = _today().strftime("%Y-%m-%d")
        output_path = Path("docs/reports") / f"data-{cnpj14}-{date_str}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Dados salvos em: {output_path}")
    print(f"   Editais: {len(data['editais'])} ({len(editais_pncp)} PNCP + {len(editais_pcp)} PCP)")
    print(f"   Menções QD: {len(qd_mencoes)}")
    print(f"   Distâncias: {len(distancias)}")
    api.print_stats()
    api.close()


if __name__ == "__main__":
    main()
