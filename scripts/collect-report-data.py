#!/usr/bin/env python3
"""
Coleta determinística de dados para o relatório B2G.

Faz TODAS as chamadas de API de forma determinística, com tratamento
explícito de falhas. Cada dado recebe um campo `_source`:
  - "API"          → dado obtido com sucesso via API
  - "API_PARTIAL"  → resposta parcial (timeout, paginação incompleta)
  - "API_FAILED"   → chamada falhou após retries
  - "API_CORRUPT"  → resposta 200 mas corpo não é JSON válido (após 1 retry)
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
import concurrent.futures
import io
import json
import hashlib
import os
import random
import re
import sys
import threading
import time
import statistics as _statistics
import uuid
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

# HARD-000: Extracted dedup module
from report_dedup import normalize_for_dedup as _normalize_for_dedup, jaccard_similarity as _jaccard_similarity, semantic_dedup as _semantic_dedup

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

import unicodedata


def _strip_accents(s: str) -> str:
    """Remove diacritical marks (accents) from a string. E.g. 'prestação' → 'prestacao'."""
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


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
OSRM_TABLE_BASE = "http://router.project-osrm.org/table/v1/driving"
OSRM_TABLE_BATCH_SIZE = 80  # Public OSRM limit ~100 coords; 80 is safe
NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"

# Persistent cache paths (relative to project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
GEOCODE_CACHE_FILE = str(_PROJECT_ROOT / "data" / "geocode_cache.json")
DISTANCE_CACHE_FILE = str(_PROJECT_ROOT / "data" / "distance_cache.json")
IBGE_CACHE_FILE = str(_PROJECT_ROOT / "data" / "ibge_cache.json")
COMPETITIVE_CACHE_FILE = str(_PROJECT_ROOT / "data" / "competitive_cache.json")
COMPETITIVE_CACHE_TTL_DAYS = 7
DOCS_CACHE_FILE = str(_PROJECT_ROOT / "data" / "docs_cache.json")
# No TTL for docs — document listings are immutable once published

# Static municipality coordinates (eliminates Nominatim dependency for known cities)
_MUNICIPIOS_COORDS: dict = {}
_MUNICIPIOS_COORDS_FILE = str(_PROJECT_ROOT / "data" / "municipios_coords.json")


def _load_municipios_coords() -> None:
    """Lazy-load static municipality coordinates from data/municipios_coords.json."""
    global _MUNICIPIOS_COORDS
    if _MUNICIPIOS_COORDS:
        return
    try:
        with open(_MUNICIPIOS_COORDS_FILE, "r", encoding="utf-8") as f:
            _MUNICIPIOS_COORDS = json.load(f)
    except FileNotFoundError:
        print("  [geocode] data/municipios_coords.json not found — falling back to Nominatim")
IBGE_CACHE_TTL_DAYS = 90  # Population/GDP data changes annually
BRASILAPI_BASE = "https://brasilapi.com.br/api/cnpj/v1"
IBGE_LOCALIDADES = "https://servicodados.ibge.gov.br/api/v1/localidades"
IBGE_SIDRA = "https://apisidra.ibge.gov.br/values"

# PNCP modalidade codes — aligned with /api/pncp/v1/modalidades (verified 2026-03-17)
MODALIDADES = {
    2: "Diálogo Competitivo",
    3: "Concurso",
    4: "Concorrência - Eletrônica",
    5: "Concorrência - Presencial",
    6: "Pregão - Eletrônico",
    7: "Pregão - Presencial",
    8: "Dispensa de Licitação",
    9: "Inexigibilidade",
    12: "Credenciamento",
    15: "Chamada Pública",
    16: "Concorrência - Eletrônica Internacional",
    17: "Concorrência - Presencial Internacional",
    18: "Pregão - Eletrônico Internacional",
    19: "Pregão - Presencial Internacional",
}

# Competitive modalidades — where OTHER companies can actually bid
MODALIDADES_COMPETITIVAS = {4, 5, 6, 7, 16, 17, 18, 19}  # Concorrências + Pregões

# Extended competitive — includes less common but still open processes
MODALIDADES_COMPETITIVAS_EXTENDED = {2, 3, 4, 5, 6, 7, 12, 15, 16, 17, 18, 19}

# NON-competitive — pre-determined winner or no bidding
MODALIDADES_EXCLUIDAS = {8, 9, 14}  # Dispensa + Inexigibilidade + Inaplicabilidade

# By procurement nature (ONLY competitive modalidades)
MODALIDADES_OBRAS = {4, 5, 6, 7}               # Concorrências + Pregões (removed 8!)
MODALIDADES_AQUISICAO = {6, 7}                 # Pregões only (Dispensa excluded — non-competitive)
MODALIDADES_SERVICOS = {4, 5, 6, 7}            # Concorrências + Pregões (removed 8!)

PNCP_MAX_PAGE_SIZE = 50
PNCP_MAX_PAGES = 10
PNCP_MAX_PAGES_UF = 40  # Per-UF: 40 pages × 50 = 2000 items (exhaustive for single UF)
PCP_PAGE_SIZE = 10
PCP_MAX_PAGES = 20

MAX_RETRIES = 3
RETRY_BACKOFF = [1.0, 3.0, 8.0]
REQUEST_TIMEOUT = 30.0

# CNAE-specific keyword refinements for CNAE fallback mode
# When contract history is unavailable, these refine the broad sector keywords
# to match the specific CNAE sub-activity. Only applied when _keywords_source == "cnae_fallback".
CNAE_KEYWORD_REFINEMENTS = {
    "4120": {  # Construção de edifícios
        "exclude_patterns": [
            "pavimentação", "pavimentacao", "pavimentação asfáltica", "pavimentacao asfaltica",
            "recapeamento", "recapeamento asfaltico", "recapeamento asfáltico",
            "asfalto", "asfaltamento",
            "ponte", "viaduto", "passarela",
            "barragem", "reservatório", "reservatorio",
            "saneamento básico", "saneamento basico",
            "esgoto", "estação de tratamento", "estacao de tratamento",
            "topografia", "sondagem geotécnica", "sondagem geotecnica", "sondagem spt", "sondagem de solo",
            "fiscalização de obra", "fiscalizacao de obra",
            "supervisão de obra", "supervisao de obra",
            "gerenciamento de obra",
            "laudo técnico", "laudo tecnico",
            "projeto arquitetônico", "projeto arquitetonico",
            "revitalização urbana", "revitalizacao urbana",
            "restauração de patrimônio", "restauracao de patrimonio",
            "restauração de fachada", "restauracao de fachada",
            "restauração de edifício", "restauracao de edificio",
        ],
        "extra_include": [
            "unidade habitacional", "casa popular", "habitação popular", "habitacao popular",
            "creche", "escola", "UBS", "posto de saúde", "posto de saude",
            "centro esportivo", "ginásio", "ginasio", "quadra coberta", "quadra poliesportiva",
            "prédio público", "predio publico", "sede administrativa",
            "centro comunitário", "centro comunitario",
            "unidade de saúde", "unidade de saude",
        ],
    },
    "4211": {  # Construção de rodovias, ferrovias, obras de urbanização e obras de arte especiais
        "exclude_patterns": [
            "edificação", "edificacao", "prédio", "predio",
            "escola", "creche", "UBS", "posto de saúde", "posto de saude",
            "elevador", "elevadores",
            "telhado", "cobertura metálica", "cobertura metalica",
            "pintura predial", "pintura de fachada",
            "instalação elétrica", "instalacao eletrica",
            "instalação hidráulica", "instalacao hidraulica",
        ],
        "extra_include": [
            "rodovia", "estrada", "via urbana",
            "ciclovia", "calçada", "calcada",
            "meio-fio", "meio fio", "guia",
            "sinalização viária", "sinalizacao viaria",
        ],
    },
    "4399": {  # Serviços especializados para construção
        "exclude_patterns": [],
        "extra_include": [
            "serviço especializado", "servico especializado",
            "manutenção predial", "manutencao predial",
        ],
    },
    "4322": {  # Instalações hidráulicas, de sistemas de ventilação e refrigeração
        "exclude_patterns": [
            "pavimentação", "pavimentacao", "asfalto", "ponte", "viaduto",
            "terraplanagem", "sondagem",
        ],
        "extra_include": [
            "instalação hidráulica", "instalacao hidraulica",
            "sistema de ventilação", "sistema de ventilacao",
            "ar condicionado", "refrigeração", "refrigeracao",
            "sprinkler", "hidrante",
        ],
    },
    "4330": {  # Obras de acabamento
        "exclude_patterns": [
            "pavimentação", "pavimentacao", "asfalto", "ponte", "viaduto",
            "terraplanagem", "sondagem",
        ],
        "extra_include": [
            "acabamento", "pintura", "revestimento",
            "piso", "forro", "gesso",
        ],
    },
}

# CNAE-object incompatibility patterns (A1: deterministic CNAE×Object check)
# Key: 4-digit CNAE prefix → list of INCOMPATIBLE object patterns (regex)
# When a company's CNAE matches a key and the edital's objeto matches any pattern,
# the edital is marked as incompatible and vetoed from recommendation.
CNAE_INCOMPATIBLE_OBJECTS: dict[str, list[str]] = {
    "4120": [  # Construção de edifícios — NOT compatible with:
        r"\bpavimenta[çc][ãa]o\b", r"\basfalto\b", r"\basfaltamento\b",
        r"\brecapeamento\b", r"\bcbuq\b",
        r"\bponte\b", r"\bviaduto\b", r"\bpassarela\b",
        r"\bbarragem\b", r"\breservat[oó]rio\b",
        r"\bsaneamento\b", r"\besgoto\b", r"\btratamento de [aáe]\b",
        r"\btopografia\b", r"\bsondagem\b", r"\bgeot[eé]cnic\b",
        r"\bconsultoria\b", r"\bsupervis[ãa]o\b", r"\bfiscaliza[çc][ãa]o\b",
        r"\btransporte\b", r"\bfrete\b", r"\bcaminh[ãa]o\b",
        r"\blavanderia\b", r"\blimpeza\b", r"\bzeladoria\b",
        r"\bmedicamento\b", r"\bhospitalar\b", r"\bsa[uú]de\b",
        r"\baliment[aío]\b", r"\bmerenda\b", r"\brefeição\b",
        r"\bmobili[aá]rio\b", r"\bm[oó]vel\b", r"\bm[oó]veis\b",
    ],
    "4211": [  # Rodovias/ferrovias — NOT compatible with:
        r"\bedifica[çc][ãa]o\b", r"\bpr[eé]dio\b", r"\bescola\b",
        r"\bcreche\b", r"\bubs\b", r"\bunidade\s+(habitacional|de sa[uú]de)\b",
    ],
}

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


def _safe_float(v: Any, default: float | None = None) -> float | None:
    """Convert value to float. Returns None (not 0.0) for invalid/missing values.

    F02: Changed default from 0.0 to None so callers can distinguish
    'missing data' from 'zero value'. valor_estimado=None enables
    downstream VALOR_SIGILOSO handling.
    """
    if v is None:
        return default
    try:
        if isinstance(v, str):
            v = v.replace(",", ".")
        return float(v)
    except (ValueError, TypeError):
        return default


def _parse_date_flexible(raw: str | None) -> str | None:
    """Parse date trying multiple formats. Returns YYYY-MM-DD or None. (F04)"""
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(raw[:max(10, len(raw))].strip(), fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return None


def _source_tag(status: str, detail: str = "", response_detail: str = "") -> dict:
    """Create a _source metadata tag."""
    tag = {"status": status, "timestamp": _date_iso(_today())}
    if detail:
        tag["detail"] = detail
    if response_detail:
        tag["response_detail"] = response_detail
    return tag


def _fmt_brl(v: float, decimals: int = 0) -> str:
    """Format number in Brazilian style: R$ 1.234.567,89"""
    if decimals == 0:
        formatted = f"{v:,.0f}"
    else:
        formatted = f"{v:,.{decimals}f}"
    # Swap: comma->X, dot->comma, X->dot
    return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


# ============================================================
# HTTP CLIENT WITH RETRY
# ============================================================

class ApiClient:
    """Simple HTTP client with retry and logging. Thread-safe."""

    def __init__(self, verbose: bool = True):
        self.client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "SmartLic-ReportCollector/1.0"},
        )
        self.verbose = verbose
        self.stats = {"calls": 0, "success": 0, "failed": 0, "retries": 0}
        self._stats_lock = threading.Lock()
        self._print_lock = threading.Lock()

    def _inc_stat(self, key: str) -> None:
        with self._stats_lock:
            self.stats[key] += 1

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
        self._inc_stat("calls")
        display = label or url[:80]

        for attempt in range(MAX_RETRIES):
            try:
                if self.verbose and attempt == 0:
                    with self._print_lock:
                        print(f"  → {display}", end="", flush=True)

                resp = self.client.get(url, params=params, headers=headers)

                if resp.status_code == 200:
                    self._inc_stat("success")
                    if self.verbose:
                        with self._print_lock:
                            print(f" ✓ ({resp.status_code})")
                    try:
                        return resp.json(), "API"
                    except (json.JSONDecodeError, Exception):
                        # F01: Retry once on corrupt JSON, then return API_CORRUPT
                        if attempt < MAX_RETRIES - 1:
                            self._inc_stat("retries")
                            wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)] * (0.5 + random.random())
                            if self.verbose:
                                with self._print_lock:
                                    print(f" ⟳ JSON parse error, retry in {wait:.1f}s", end="", flush=True)
                            time.sleep(wait)
                            continue
                        return None, "API_CORRUPT"

                if resp.status_code in (429, 500, 502, 503, 504, 422):
                    self._inc_stat("retries")
                    # F26: Add jitter to retry backoff (AWS recommended pattern)
                    wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)] * (0.5 + random.random())
                    if self.verbose:
                        with self._print_lock:
                            print(f" ⟳ {resp.status_code}, retry in {wait:.1f}s", end="", flush=True)
                    time.sleep(wait)
                    continue

                # Non-retryable error
                self._inc_stat("failed")
                if self.verbose:
                    with self._print_lock:
                        print(f" ✗ ({resp.status_code})")
                if resp.status_code == 400:
                    try:
                        body = resp.text[:300] if hasattr(resp, "text") else str(resp.content[:300])
                        print(f"    [DEBUG] 400 response: {body}")
                    except Exception:
                        pass
                return None, "API_FAILED"

            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
                self._inc_stat("retries")
                # F26: Add jitter to retry backoff
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)] * (0.5 + random.random())
                if self.verbose:
                    err_type = type(e).__name__
                    with self._print_lock:
                        print(f" ⟳ {err_type}, retry in {wait:.1f}s", end="", flush=True)
                time.sleep(wait)
                continue

        self._inc_stat("failed")
        if self.verbose:
            with self._print_lock:
                print(f" ✗ (max retries)")
        return None, "API_FAILED"

    def head(self, url: str, label: str = "") -> int | None:
        """HEAD request, returns status code or None. F29: 5s timeout."""
        try:
            resp = self.client.head(url, timeout=5.0, follow_redirects=True)
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
    """Fetch company data from OpenCNPJ, with BrasilAPI fallback.

    If OpenCNPJ fails, automatically tries BrasilAPI as secondary source.
    The report MUST have company data — we don't accept 'indisponível'.
    """
    print("\n📋 Phase 1a: Receita Federal — Perfil da empresa")
    data, status = api.get(
        f"{OPENCNPJ_BASE}/{cnpj14}",
        label=f"OpenCNPJ {cnpj14}",
    )
    if not data or status != "API":
        # FALLBACK: Try BrasilAPI before giving up
        print(f"  ⚠ OpenCNPJ falhou — tentando BrasilAPI como fallback...")
        data, status = api.get(
            f"{BRASILAPI_BASE}/{cnpj14}",
            label=f"BrasilAPI fallback {cnpj14}",
        )
        if not data or status != "API":
            print(f"  ✗ Ambas fontes falharam. Verifique conectividade e CNPJ.")
            return {
                "_source": _source_tag("API_FAILED",
                    "OpenCNPJ e BrasilAPI falharam. Verificar: "
                    f"(1) https://api.opencnpj.org/{cnpj14} "
                    f"(2) https://brasilapi.com.br/api/cnpj/v1/{cnpj14}"),
                "cnpj": _format_cnpj(cnpj14),
            }
        print(f"  ✓ BrasilAPI respondeu — usando como fonte primária")

    # Parse capital_social (string with comma: "1232000,00")
    capital = _safe_float(data.get("capital_social")) or 0.0

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
    # The /pessoa-juridica endpoint may return paginated results for ALL companies,
    # not filtered by the cnpj param. We must post-filter by target CNPJ.
    cnpj_clean = cnpj14.replace(".", "").replace("/", "").replace("-", "")
    data, status = api.get(
        f"{PT_BASE}/pessoa-juridica",
        params={"cnpj": cnpj14},
        headers=headers,
        label="Portal Transparência — sanções",
    )
    if status == "API":
        items = (data if isinstance(data, list) else [data]) if data else []
        for item in items:
            for key in ["ceis", "cnep", "cepim", "ceaf"]:
                val = item.get(key) or item.get(key.upper())
                if not val or str(val).lower() in ("false", "0", "none", "null", "[]", "{}"):
                    continue
                # If val is a list of sanctions, filter to only those matching target CNPJ
                if isinstance(val, list):
                    matching = []
                    for sanction in val:
                        if not isinstance(sanction, dict):
                            continue
                        # Check multiple possible CNPJ field names in the sanction record
                        sanc_cnpj = ""
                        for field in ["cnpjFormatado", "codigoCnpjCpf", "cpfCnpjSancionado",
                                      "cnpj", "cpfCnpj", "numeroCnpjCpf"]:
                            candidate = str(sanction.get(field, ""))
                            if candidate:
                                sanc_cnpj = candidate.replace(".", "").replace("/", "").replace("-", "")
                                break
                        # Also check nested sancionado/pessoa objects
                        if not sanc_cnpj:
                            for nested_key in ["sancionado", "pessoa", "pessoaJuridica"]:
                                nested = sanction.get(nested_key, {})
                                if isinstance(nested, dict):
                                    for field in ["cnpjFormatado", "codigoCnpjCpf", "cnpj",
                                                  "cpfCnpj", "numeroCnpjCpf", "cpfCnpjSancionado"]:
                                        candidate = str(nested.get(field, ""))
                                        if candidate:
                                            sanc_cnpj = candidate.replace(".", "").replace("/", "").replace("-", "")
                                            break
                                if sanc_cnpj:
                                    break
                        if sanc_cnpj == cnpj_clean:
                            matching.append(sanction)
                    if matching:
                        result["sancoes"][key] = True
                        print(f"  [PT] {key.upper()}: {len(matching)} sancao(oes) confirmada(s) para CNPJ {cnpj14}")
                    # else: list had items but none matched our CNPJ -- not sanctioned
                else:
                    # Scalar truthy value (legacy format) -- trust it
                    result["sancoes"][key] = True
        result["sancoes"]["sancionada"] = any(result["sancoes"][k] for k in ["ceis", "cnep", "cepim", "ceaf"])
        result["sancoes_source"] = _source_tag("API")
        sancoes_ativas = [k for k, v in result["sancoes"].items() if v and k != "sancionada"]
        if sancoes_ativas:
            print(f"  [PT] SANCOES ENCONTRADAS: {', '.join(s.upper() for s in sancoes_ativas)}")
        else:
            print(f"  [PT] Nenhuma sancao encontrada para CNPJ {cnpj14} (CEIS/CNEP/CEPIM/CEAF)")
    elif status == "API_CORRUPT":
        result["sancoes_source"] = _source_tag("API_CORRUPT", "Resposta inválida do servidor")
        result["sancoes"]["inconclusive"] = True
        print(f"  [PT] Resposta de sanções com formato inválido")
    elif status == "API_FAILED":
        result["sancoes_source"] = _source_tag("API_FAILED", "Consulta de sanções falhou")
        result["sancoes"]["inconclusive"] = True

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
                    "valor": _safe_float(c.get("valorFinal") or c.get("valor") or c.get("valorInicial")) or 0.0,
                    "data": c.get("dataInicioVigencia") or c.get("dataAssinatura") or "",
                    "objeto": c.get("objeto", "")[:200],
                })
        n = len(result["historico_contratos"])
        detail = f"{n} contrato(s) federal(is) identificado(s)" if n > 0 else "Nenhum contrato federal identificado"
        result["historico_source"] = _source_tag("API", detail)
        print(f"  [PT] Contratos federais: {n} encontrados")
    elif status == "API_CORRUPT":
        result["historico_source"] = _source_tag("API_CORRUPT", "Resposta de contratos com formato inválido")
    elif status == "API_FAILED":
        result["historico_source"] = _source_tag("API_FAILED", "Consulta de contratos falhou")

    return result


def collect_brasilapi(api: ApiClient, cnpj14: str) -> dict:
    """Fetch Simples Nacional status + fallback company data from BrasilAPI."""
    print("\n  BrasilAPI — Simples Nacional")
    data, status = api.get(f"{BRASILAPI_BASE}/{cnpj14}", label=f"BrasilAPI {cnpj14}")
    if not data or status != "API":
        src_detail = "Resposta inválida do servidor" if status == "API_CORRUPT" else "BrasilAPI indisponivel"
        src_status = status if status in ("API_CORRUPT", "API_FAILED") else "API_FAILED"
        return {"_source": _source_tag(src_status, src_detail), "simples_nacional": None, "mei": None}
    return {
        "_source": _source_tag("API"),
        "simples_nacional": data.get("opcao_pelo_simples"),
        "mei": data.get("opcao_pelo_mei"),
        "data_opcao_simples": data.get("data_opcao_pelo_simples", ""),
        "data_exclusao_simples": data.get("data_exclusao_do_simples", ""),
        "porte_fallback": data.get("porte", ""),
        "municipio": data.get("municipio", ""),
        "uf": data.get("uf", ""),
    }


_ibge_cache: dict = {}  # UF -> {nome_normalizado: cod_ibge}
_ibge_data_cache: dict = {}  # "{municipio}/{uf}" -> enriched data dict (persistent)
_ibge_cache_lock = threading.Lock()  # F27: Thread safety for IBGE caches


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



def _load_ibge_cache() -> None:
    """Load persistent IBGE data cache from disk, pruning expired entries."""
    global _ibge_data_cache
    with _ibge_cache_lock:
        try:
            with open(IBGE_CACHE_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            now = datetime.now(timezone.utc)
            _ibge_data_cache = {
                k: v for k, v in raw.items()
                if (now - datetime.fromisoformat(v.get("_cached_at", "2000-01-01T00:00:00+00:00"))).days < IBGE_CACHE_TTL_DAYS
            }
        except (FileNotFoundError, json.JSONDecodeError):
            _ibge_data_cache = {}


def _save_ibge_cache() -> None:
    """Persist IBGE data cache to disk."""
    with _ibge_cache_lock:
        os.makedirs(os.path.dirname(IBGE_CACHE_FILE), exist_ok=True)
        with open(IBGE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_ibge_data_cache, f, ensure_ascii=False, indent=2)


def collect_ibge_batch(api: ApiClient, municipios: list[tuple[str, str]]) -> dict[str, dict]:
    """Fetch population + GDP for multiple municipalities via batch SIDRA requests.

    Args:
        api: ApiClient instance
        municipios: list of (municipio, uf) tuples

    Returns:
        dict mapping "{municipio}|{uf}" -> {"populacao": int, "pib_mil_reais": float, ...}
    """
    _load_ibge_cache()

    result: dict[str, dict] = {}
    missing: list[tuple[str, str, int]] = []  # (municipio, uf, cod_ibge)

    # Split cached vs missing
    cached_count = 0
    for mun, uf in municipios:
        key = f"{mun}|{uf}"
        if key in _ibge_data_cache:
            result[key] = _ibge_data_cache[key]
            cached_count += 1
        else:
            cod = _get_cod_ibge(api, mun, uf)
            if cod:
                missing.append((mun, uf, cod))
            else:
                result[key] = {
                    "_source": _source_tag("API_FAILED", f"Codigo IBGE nao encontrado: {mun}/{uf}"),
                    "populacao": None,
                    "pib_mil_reais": None,
                    "pib_per_capita": None,
                }

    print(f"  -> IBGE: {cached_count} do cache, {len(missing)} novos")

    if not missing:
        return result

    # Build comma-separated codes for batch requests
    codes_str = ",".join(str(cod) for _, _, cod in missing)
    cod_to_key: dict[str, str] = {str(cod): f"{mun}|{uf}" for mun, uf, cod in missing}

    # --- Batch population request ---
    pop_values: dict[str, int | None] = {}
    pop_data, pop_status = api.get(
        f"{IBGE_SIDRA}/t/6579/n6/{codes_str}/v/9324/p/last",
        label=f"IBGE batch pop ({len(missing)} municipios)",
    )
    if pop_status == "API" and isinstance(pop_data, list):
        for item in pop_data:
            cod_key = str(item.get("D1C", ""))
            if cod_key in cod_to_key:
                try:
                    pop_values[cod_key] = int(item.get("V", 0))
                except (ValueError, TypeError):
                    pop_values[cod_key] = None
        print(f"  -> IBGE batch: {len(missing)} municipios (pop) OK")
    else:
        print(f"  IBGE batch pop falhou (status={pop_status}) -- usando fallback individual")

    time.sleep(0.3)

    # --- Batch GDP request ---
    pib_values: dict[str, float | None] = {}
    pib_data, pib_status = api.get(
        f"{IBGE_SIDRA}/t/5938/n6/{codes_str}/v/37/p/last",
        label=f"IBGE batch PIB ({len(missing)} municipios)",
    )
    if pib_status == "API" and isinstance(pib_data, list):
        for item in pib_data:
            cod_key = str(item.get("D1C", ""))
            if cod_key in cod_to_key:
                try:
                    pib_values[cod_key] = float(item.get("V", 0))
                except (ValueError, TypeError):
                    pib_values[cod_key] = None
        print(f"  -> IBGE batch: {len(missing)} municipios (PIB) OK")
    else:
        print(f"  IBGE batch PIB falhou (status={pib_status}) -- usando fallback individual")

    # --- Assemble results; fall back to individual calls on batch failure ---
    # F28: Cap individual fallback at 20 to prevent API abuse
    MAX_IBGE_INDIVIDUAL_FALLBACK = 20
    _individual_fallback_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    for mun, uf, cod in missing:
        key = f"{mun}|{uf}"
        cod_str_k = str(cod)

        pop: int | None = pop_values.get(cod_str_k)
        pib: float | None = pib_values.get(cod_str_k)

        # If batch failed entirely, attempt individual fallback (F28: capped at 20)
        if pop is None and pop_status != "API":
            if _individual_fallback_count < MAX_IBGE_INDIVIDUAL_FALLBACK:
                indiv = collect_ibge_municipio(api, mun, uf)
                pop = indiv.get("populacao")
                pib = indiv.get("pib_mil_reais")
                _individual_fallback_count += 1
            # else: leave pop/pib as None (API_PARTIAL)
        elif pib is None and pib_status != "API":
            if _individual_fallback_count < MAX_IBGE_INDIVIDUAL_FALLBACK:
                indiv = collect_ibge_municipio(api, mun, uf)
                pop = indiv.get("populacao") if pop is None else pop
                pib = indiv.get("pib_mil_reais")
                _individual_fallback_count += 1

        pib_per_capita: float | None = None
        if pop and pib:
            pib_per_capita = round((pib * 1000) / pop, 2)

        has_any = pop or pib
        entry: dict = {
            "cod_ibge": cod,
            "populacao": pop,
            "pib_mil_reais": pib,
            "pib_per_capita": pib_per_capita,
            "_source": _source_tag("API" if has_any else "API_FAILED", f"pop={'OK' if pop else 'N/A'}, pib={'OK' if pib else 'N/A'}"),
            "_cached_at": now_iso,
        }
        result[key] = entry
        _ibge_data_cache[key] = entry

    _save_ibge_cache()
    return result


def _parse_pncp_contract_item(c: dict, cnpj14: str, source_label: str = "PNCP") -> dict | None:
    """Parse a single PNCP contract item, filtering by niFornecedor.

    Returns None if the item does not belong to the target CNPJ.
    This is needed because PNCP /contratos ignores cnpjFornecedor server-side.
    """
    ni = (c.get("niFornecedor") or "").replace(".", "").replace("/", "").replace("-", "")
    if ni and ni != cnpj14:
        return None  # Belongs to a different supplier

    orgao = c.get("orgaoEntidade", {})
    unidade = c.get("unidadeOrgao", {})
    esfera_labels = {"F": "Federal", "E": "Estadual", "M": "Municipal", "D": "Distrital"}
    esfera_id = orgao.get("esferaId", "")
    esfera = esfera_labels.get(esfera_id, esfera_id)

    return {
        "orgao": unidade.get("nomeUnidade", "") or orgao.get("razaoSocial", ""),
        "esfera": esfera,
        "uf": unidade.get("ufSigla", ""),
        "municipio": unidade.get("municipioNome", ""),
        "valor": _safe_float(c.get("valorGlobal") or c.get("valorInicial")) or 0.0,
        "data": c.get("dataAssinatura", ""),
        "objeto": (c.get("objetoContrato") or c.get("informacaoComplementar") or "")[:300],
        "numero_contrato": c.get("numeroContratoEmpenho", ""),
        "vigencia_fim": c.get("dataVigenciaFim", ""),
        "fonte": source_label,
        "valor_aditivos": _safe_float(c.get("valorAcumuladoAditivos")) or 0.0,
        "tipo_contrato": c.get("tipoContratoNome", ""),
        "situacao_contrato": c.get("situacaoContratoCodigo", ""),
        "tem_subcontratacao": c.get("subcontratacao", False),
    }


def _collect_pncp_contratos_by_date_window(
    api: "ApiClient",
    cnpj14: str,
    data_ini: str,
    data_fim: str,
    max_pages: int = 10,
) -> tuple[list[dict], int, int]:
    """Fetch contracts from PNCP /contratos endpoint for a date window.

    FIX 4 — Strategy 1: /contratos with cnpjFornecedor (server-side filter
    may work in future PNCP versions; we always apply client-side filter too).

    Returns (contracts_matched, raw_total, errors).
    """
    matched: list[dict] = []
    raw_total = 0
    errors = 0

    page = 1
    while page <= max_pages:
        data, status = api.get(
            f"{PNCP_BASE}/contratos",
            params={
                "cnpjFornecedor": cnpj14,
                "dataInicial": data_ini,
                "dataFinal": data_fim,
                "pagina": page,
                "tamanhoPagina": 50,
            },
            label=f"PNCP contratos/date p={page}",
        )
        if status != "API" or not data:
            if status == "API_FAILED":
                errors += 1
            break

        items = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(items, list) or not items:
            break

        total_records = data.get("totalRegistros", 0) if isinstance(data, dict) else 0

        for c in items:
            raw_total += 1
            parsed = _parse_pncp_contract_item(c, cnpj14, "PNCP")
            if parsed:
                matched.append(parsed)

        total_pages = data.get("totalPaginas", 1) if isinstance(data, dict) else 1
        # AC1: When API clearly not filtering by supplier (very large result, 0 match so far),
        # probe a few more pages before giving up instead of aborting on page 1
        if total_records > 10_000 and not matched:
            if page >= min(5, total_pages):
                print(
                    f"  ⚠ {total_records:,} contratos no período mas 0 para CNPJ {cnpj14} "
                    f"após {page} página(s) — API pode estar ignorando cnpjFornecedor"
                )
                break
            page += 1
            time.sleep(0.3)
            continue

        if page >= total_pages:
            break
        page += 1
        time.sleep(0.3)

    return matched, raw_total, errors


def _collect_pncp_contratos_by_razao_social(
    api: "ApiClient",
    cnpj14: str,
    razao_social: str,
) -> tuple[list[dict], int]:
    """FIX 4 — Strategy 2: Search PNCP contratações/publicacao by company name.

    AC2: /contratacoes/publicacao requires codigoModalidadeContratacao. Queries
    each of modalidades 4 (Concorrência), 5 (Pregão Eletrônico), 6 (Pregão
    Presencial), 7 (Leilão) separately and merges results.
    Logs HTTP errors including response body for diagnostics (AC5).

    Returns (contracts, raw_total).
    """
    if not razao_social or len(razao_social) < 5:
        return [], 0

    matched: list[dict] = []
    raw_total = 0
    esfera_labels_rs = {"F": "Federal", "E": "Estadual", "M": "Municipal", "D": "Distrital"}

    # Use first 30 chars of razao_social (more specific = fewer false positives)
    query_name = razao_social[:30].strip()

    # AC2: iterate over required modalidades — API returns HTTP 400 without this param
    modalidades = [4, 5, 6, 7]  # Concorrência, Pregão Eletrônico, Pregão Presencial, Leilão
    for modalidade in modalidades:
        params = {
            "q": query_name,
            "codigoModalidadeContratacao": modalidade,
            "pagina": 1,
            "tamanhoPagina": 50,
        }
        data, status = api.get(
            f"{PNCP_BASE}/contratacoes/publicacao",
            params=params,
            label=f"PNCP contratos/razao-social modalidade={modalidade}",
        )
        if status != "API" or not data:
            # AC5: Detailed failure logging
            print(
                f"  ⚠ Strategy 2 (modalidade={modalidade}): status={status!r} "
                f"params={params}"
            )
            continue

        items = data if isinstance(data, list) else data.get("data", data.get("resultado", []))
        if not isinstance(items, list):
            continue

        for item in items:
            raw_total += 1
            # Only include if the item appears to reference this company as supplier/winner
            orgao = item.get("orgaoEntidade", {})
            unidade = item.get("unidadeOrgao", {})

            # Try to find supplier CNPJ in various fields
            fornecedor_cnpj = (
                re.sub(r"[^0-9]", "", str(item.get("cnpjFornecedor") or item.get("niFornecedor") or ""))
            )
            if fornecedor_cnpj and fornecedor_cnpj != cnpj14:
                continue  # Different supplier

            valor = _safe_float(item.get("valorTotalEstimado") or item.get("valorGlobal")) or 0.0
            data_assinatura = (item.get("dataAssinatura") or item.get("dataPublicacaoPncp") or "")[:10]

            matched.append({
                "orgao": (orgao.get("razaoSocial") or unidade.get("nomeUnidade") or ""),
                "esfera": esfera_labels_rs.get(orgao.get("esferaId", ""), ""),
                "uf": unidade.get("ufSigla", ""),
                "municipio": unidade.get("municipioNome", ""),
                "valor": valor,
                "data": data_assinatura,
                "objeto": (item.get("objetoCompra") or item.get("objeto") or "")[:300],
                "numero_contrato": item.get("numeroContratoEmpenho") or item.get("sequencialCompra") or "",
                "vigencia_fim": item.get("dataEncerramentoProposta") or "",
                "fonte": "PNCP_NOME",
                "valor_aditivos": 0.0,
                "tipo_contrato": item.get("modalidadeNome") or "",
                "situacao_contrato": "",
                "tem_subcontratacao": False,
            })

    return matched, raw_total


def _collect_pncp_contratos_fornecedor_wide(
    api: "ApiClient",
    cnpj14: str,
    razao_social: str = "",
) -> tuple[list[dict], int]:
    """AC3 — Strategy 4: PNCP /contratos without date window (wider search).

    Queries the PNCP /contratos endpoint with only cnpjFornecedor, no date
    filters, to maximise recall. Falls back to a short razao_social keyword
    query against /contratos if the CNPJ search returns nothing.

    Returns (contracts_matched, raw_total).
    """
    matched: list[dict] = []
    raw_total = 0

    # 4a: /contratos with only cnpjFornecedor — no date restriction
    for page in range(1, 4):
        data, status = api.get(
            f"{PNCP_BASE}/contratos",
            params={
                "cnpjFornecedor": cnpj14,
                "pagina": page,
                "tamanhoPagina": 50,
            },
            label=f"PNCP contratos/wide p={page}",
        )
        if status != "API" or not data:
            print(
                f"  ⚠ Strategy 4a (wide, page={page}): status={status!r} "
                f"cnpjFornecedor={cnpj14}"
            )
            break

        items = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(items, list) or not items:
            break

        total_records = data.get("totalRegistros", 0) if isinstance(data, dict) else 0
        for c in items:
            raw_total += 1
            parsed = _parse_pncp_contract_item(c, cnpj14, "PNCP")
            if parsed:
                matched.append(parsed)

        total_pages = data.get("totalPaginas", 1) if isinstance(data, dict) else 1
        # If API is not filtering by CNPJ (huge result set, 0 matches), stop early
        if total_records > 10_000 and not matched:
            print(
                f"  ⚠ Strategy 4a: {total_records:,} contratos mas 0 para CNPJ {cnpj14} "
                f"após {page} página(s)"
            )
            break
        if page >= total_pages:
            break
        import time as _time
        _time.sleep(0.3)

    if matched:
        print(f"  ✓ Strategy 4a (wide /contratos): {len(matched)} contratos ({raw_total} raw)")
        return matched, raw_total

    # 4b: Fallback — /contratos with short razao_social keyword (q= param)
    if razao_social:
        query_short = razao_social[:20].strip()
        data, status = api.get(
            f"{PNCP_BASE}/contratos",
            params={
                "q": query_short,
                "pagina": 1,
                "tamanhoPagina": 50,
            },
            label="PNCP contratos/wide-nome",
        )
        if status != "API" or not data:
            print(
                f"  ⚠ Strategy 4b (wide-nome): status={status!r} "
                f"q={query_short!r}"
            )
        else:
            items = data.get("data", data) if isinstance(data, dict) else data
            if isinstance(items, list):
                for c in items:
                    raw_total += 1
                    parsed = _parse_pncp_contract_item(c, cnpj14, "PNCP")
                    if parsed:
                        matched.append(parsed)
                if matched:
                    print(f"  ✓ Strategy 4b (wide-nome): {len(matched)} contratos ({raw_total} raw)")
                else:
                    print(
                        f"  Strategy 4b (wide-nome): {raw_total} raw, "
                        f"0 contratos para CNPJ {cnpj14}"
                    )

    return matched, raw_total


def collect_pncp_contratos_fornecedor(
    api: "ApiClient",
    cnpj14: str,
    razao_social: str = "",
) -> tuple[list[dict], dict]:
    """Fetch contract history from PNCP by supplier CNPJ.

    FIX 4: Multi-strategy contract collection:
      Strategy 1 — PNCP /contratos with cnpjFornecedor (date-windowed, client-side filter)
      Strategy 2 — PNCP /contratacoes/publicacao by razao_social (fallback)

    Covers ALL spheres: federal, state, municipal, autarchies, foundations.
    PNCP /contratos allows max 365-day window, so we query 2 consecutive years.

    CRITICAL FIX (2026-03-17): The PNCP /contratos endpoint IGNORES the
    cnpjFornecedor query parameter and returns ALL contracts for the date range.
    We MUST filter client-side by niFornecedor to avoid ingesting millions of
    unrelated contracts. A post-fetch integrity check aborts if >20% of raw
    results don't match the target CNPJ (indicates API is still not filtering).
    """
    print("\n📋 Phase 1c: PNCP — Histórico de contratos do fornecedor (todas as esferas)")

    all_contracts: list[dict] = []
    total_raw = 0
    total_errors = 0

    # FIX 4 — Strategy 1: PNCP /contratos endpoint (2-year window, date-windowed)
    today = _today()
    windows = [
        (_date_compact(today - timedelta(days=365)), _date_compact(today)),
        (_date_compact(today - timedelta(days=730)), _date_compact(today - timedelta(days=366))),
    ]

    strat1_matched = 0
    for data_ini, data_fim in windows:
        matched, raw, errs = _collect_pncp_contratos_by_date_window(api, cnpj14, data_ini, data_fim)
        all_contracts.extend(matched)
        total_raw += raw
        total_errors += errs
        strat1_matched += len(matched)

    # ── INTEGRITY CHECK ──────────────────────────────────────────────────────
    if total_raw > 0 and strat1_matched == 0:
        print(f"  ⚠ PNCP /contratos: {total_raw:,} itens recebidos, 0 pertencem ao CNPJ {cnpj14}")
        print(f"    (API ignora cnpjFornecedor — filtragem client-side descartou tudo)")
    elif total_raw > 0:
        pct = strat1_matched / total_raw * 100
        print(f"  ✓ PNCP /contratos strat1: {total_raw:,} recebidos → {strat1_matched} do CNPJ {cnpj14} ({pct:.1f}% match)")

    # FIX 4 — Strategy 2: Search by razao_social as fallback when strat1 returns 0
    strat2_matched = 0
    strat2_raw = 0
    if strat1_matched == 0 and razao_social:
        print(f"  Strategy 2: buscando por nome '{razao_social[:30]}...'")
        strat2_contracts, strat2_raw = _collect_pncp_contratos_by_razao_social(api, cnpj14, razao_social)
        all_contracts.extend(strat2_contracts)
        strat2_matched = len(strat2_contracts)
        if strat2_matched:
            print(f"  ✓ Strategy 2 (razao_social): {strat2_matched} contratos encontrados ({strat2_raw} raw)")
        else:
            print(f"  Strategy 2 (razao_social): {strat2_raw} raw, 0 contratos")

    # FIX-001 AC3 — Strategy 4: PNCP /contratos without date window (wider recall)
    strat4_matched = 0
    if strat1_matched == 0 and strat2_matched == 0:
        print(f"  Strategy 4: buscando sem janela de data (recall amplo)...")
        strat4_contracts, strat4_raw = _collect_pncp_contratos_fornecedor_wide(
            api, cnpj14, razao_social
        )
        all_contracts.extend(strat4_contracts)
        strat4_matched = len(strat4_contracts)
        if strat4_matched:
            print(f"  ✓ Strategy 4 (wide): {strat4_matched} contratos ({strat4_raw} raw)")
        else:
            print(f"  Strategy 4 (wide): {strat4_raw} raw, 0 contratos")

    # Strategy 3: ComprasGov v3 — módulo-contratos
    def _collect_comprasgov_contratos(cnpj_digits: str) -> list[dict]:
        """Query dadosabertos.compras.gov.br for supplier contracts."""
        contratos: list[dict] = []
        base = "https://dadosabertos.compras.gov.br"

        # 3a: Formal contracts
        try:
            url = f"{base}/modulo-contratos/1_consultarContratos"
            resp = httpx.get(url, params={"niFornecedor": cnpj_digits, "pagina": 1, "tamanhoPagina": 500}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", data.get("content", data)) if isinstance(data, dict) else data
                if isinstance(items, list):
                    for item in items:
                        contratos.append({
                            "orgao": (item.get("orgaoEntidade") or {}).get("razaoSocial", ""),
                            "uf": (item.get("unidadeOrgao") or {}).get("ufSigla", ""),
                            "objeto": (item.get("objetoContrato") or "")[:200],
                            "valor": _safe_float(item.get("valorInicial")),
                            "data": item.get("dataAssinatura", ""),
                            "fonte": "COMPRASGOV_CONTRATOS",
                        })
            print(f"  ComprasGov contratos: {len(contratos)} encontrados")
        except Exception as e:
            print(f"  ⚠ ComprasGov contratos falhou: {e}")

        # 3b: Procurement results (licitações ganhas)
        n_before = len(contratos)
        try:
            url = f"{base}/modulo-contratacoes/3_consultarResultadoItensContratacoes_PNCP_14133"
            resp = httpx.get(url, params={"niFornecedor": cnpj_digits, "pagina": 1, "tamanhoPagina": 500}, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data", data.get("content", data)) if isinstance(data, dict) else data
                if isinstance(items, list):
                    for item in items:
                        contratos.append({
                            "orgao": (item.get("orgaoEntidade") or {}).get("razaoSocial", ""),
                            "uf": (item.get("unidadeOrgao") or {}).get("ufSigla", ""),
                            "objeto": (item.get("descricao") or "")[:200],
                            "valor": _safe_float(item.get("valorTotalHomologado")),
                            "data": item.get("dataResultado", ""),
                            "fonte": "COMPRASGOV_RESULTADOS",
                        })
            print(f"  ComprasGov resultados: {len(contratos) - n_before} encontrados")
        except Exception as e:
            print(f"  ⚠ ComprasGov resultados falhou: {e}")

        return contratos

    cgov_contracts = _collect_comprasgov_contratos(cnpj14)
    if cgov_contracts:
        all_contracts.extend(cgov_contracts)
        print(f"  ✓ ComprasGov v3: {len(cgov_contracts)} contrato(s) adicionados")

    # AC2: Strategy failure summary — make 0-contract results loud, not silent
    if not all_contracts:
        print(f"  ⚠ HISTORICO VAZIO: 3 estratégias testadas, 0 contratos encontrados")
        print(f"    Strategy 1 (date window): {total_raw} raw, {strat1_matched} matched")
        print(f"    Strategy 2 (razao social): {strat2_raw} raw, {strat2_matched} matched")
        print(f"    Strategy 3 (ComprasGov): {len(cgov_contracts)}")

    # FIX 4 — Derive UFs from contract history (side effect stored in contracts themselves)
    # UF derivation happens downstream in extract_ufs_from_contracts() — no additional work needed here.

    # F03: Dedup by SHA-256 hash of structural fields (not truncated strings)
    def _contract_key(c: dict) -> str:
        raw = f"{c.get('orgao','')}\x00{c.get('numero_contrato','')}\x00{c.get('data','')}\x00{c.get('valor_contrato', c.get('valor',''))}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    seen: set[str] = set()
    unique: list[dict] = []
    for c in all_contracts:
        key = _contract_key(c)
        if key not in seen:
            seen.add(key)
            unique.append(c)
    all_contracts = unique

    # Stats
    by_esfera: dict[str, int] = {}
    for c in all_contracts:
        e = c.get("esfera", "N/I")
        by_esfera[e] = by_esfera.get(e, 0) + 1

    n = len(all_contracts)
    strategy_note = f"strat1={strat1_matched}"
    if strat2_matched:
        strategy_note += f" strat2={strat2_matched}"
    if strat4_matched:
        strategy_note += f" strat4={strat4_matched}"
    detail_parts = [f"{n} contrato(s) encontrado(s) ({strategy_note})"]
    for esfera, count in sorted(by_esfera.items()):
        detail_parts.append(f"{count} {esfera.lower()}")

    status_tag = "API" if total_errors == 0 else ("API_PARTIAL" if n > 0 else "API_FAILED")
    source = _source_tag(status_tag, ", ".join(detail_parts))

    print(f"  PNCP contratos: {n} encontrados ({', '.join(f'{v} {k}' for k, v in by_esfera.items())})")

    # AC4: Flag inconclusive history for established companies
    # (Returned directly as part of source metadata — caller merges into _metadata)
    _ac4_inconclusive = False
    if n == 0:
        import datetime as _dt
        _capital = 0.0  # Capital not available here; AC4 gate is applied downstream
        # Mark source as INCONCLUSIVE so downstream assemble() can detect it
        # The capital/age check happens in assemble() where empresa data is available
        pass  # see collect_pncp_contratos_fornecedor return value — caller checks

    return all_contracts, source


# ============================================================
# HARD-003: Acervo 3-Tier Classification (standalone, pre-enrichment)
# ============================================================

def classify_acervo_similarity(contratos: list[dict], editais: list[dict]) -> None:
    """Classify portfolio contracts by similarity to each edital (in-place mutation).

    Uses Jaccard similarity on normalized object tokens.
    ALTA: Jaccard >= 0.50 or prefix match (first 4 words identical)
    MÉDIA: Jaccard 0.30-0.49
    BAIXA: Jaccard < 0.30

    Adds to each edital:
      - acervo_status: CONFIRMADO (>=1 ALTA) | PARCIAL (>=1 MÉDIA, 0 ALTA) | NAO_VERIFICADO (0 contracts or all BAIXA)
      - acervo_similares_alta: int count
      - acervo_similares_media: int count
      - acervo_detalhes: list[dict] top 5 by similarity (contrato_objeto, similarity, tier, contrato_valor, contrato_data)
    """
    if not contratos:
        for ed in editais:
            ed["acervo_status"] = "NAO_VERIFICADO"
            ed["acervo_similares_alta"] = 0
            ed["acervo_similares_media"] = 0
            ed["acervo_detalhes"] = []
        return

    for ed in editais:
        edital_obj = ed.get("objeto", ed.get("objetoCompra", ""))
        if not edital_obj:
            ed["acervo_status"] = "NAO_VERIFICADO"
            ed["acervo_similares_alta"] = 0
            ed["acervo_similares_media"] = 0
            ed["acervo_detalhes"] = []
            continue

        edital_tokens = _normalize_for_dedup(edital_obj)
        edital_words = edital_obj.lower().split()[:4]
        edital_prefix = " ".join(edital_words)

        alta_count = 0
        media_count = 0
        all_matches: list[dict] = []

        for c in contratos:
            c_obj = (c.get("objeto") or "")
            if not c_obj:
                continue

            c_tokens = _normalize_for_dedup(c_obj)
            sim = _jaccard_similarity(edital_tokens, c_tokens)

            # Prefix match: first 4 words identical
            c_words = c_obj.lower().split()[:4]
            c_prefix = " ".join(c_words)
            prefix_match = len(edital_words) >= 4 and len(c_words) >= 4 and edital_prefix == c_prefix

            if prefix_match or sim >= 0.50:
                tier = "ALTA"
                alta_count += 1
                effective_sim = max(sim, 0.50) if prefix_match else sim
            elif sim >= 0.30:
                tier = "MÉDIA"
                media_count += 1
                effective_sim = sim
            else:
                tier = "BAIXA"
                effective_sim = sim

            if tier in ("ALTA", "MÉDIA"):
                all_matches.append({
                    "contrato_objeto": c_obj[:120],
                    "similarity": round(effective_sim, 2),
                    "tier": tier,
                    "contrato_valor": _safe_float(c.get("valor")) or 0.0,
                    "contrato_data": c.get("data_inicio") or c.get("data_assinatura") or c.get("data", ""),
                })

        # Sort by similarity descending, take top 5
        all_matches.sort(key=lambda x: -x["similarity"])
        acervo_detalhes = all_matches[:5]

        # Determine status
        if alta_count >= 1:
            acervo_status = "CONFIRMADO"
        elif media_count >= 1:
            acervo_status = "PARCIAL"
        else:
            acervo_status = "NAO_VERIFICADO"

        ed["acervo_status"] = acervo_status
        ed["acervo_similares_alta"] = alta_count
        ed["acervo_similares_media"] = media_count
        ed["acervo_detalhes"] = acervo_detalhes


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
                      "ambulânci", "ambulanci", "transporte", "frete", "locação veícul",
                      "lubrificant", "posto de combustív", "posto de combustiv",
                      "logístic", "logistic"],
        "search_keywords": ["veículo", "pneu", "combustível", "ambulância", "transporte",
                           "lubrificante", "logística"],
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
    "projetos_tecn": {
        "label": "Projetos Técnicos e Arquitetura",
        "prefixes": ["elaboração de projeto", "elaboracao de projeto",
                      "projeto executivo", "projeto básico", "projeto basico",
                      "projeto técnico", "projeto tecnico", "projeto arquitetônico",
                      "projeto arquitetonico", "plano diretor", "ppci", "clcb",
                      "levantamento topográf", "levantamento topograf",
                      "estudo de viabilidade técn", "estudo de viabilidade tecn",
                      "arquitetura e urbanism", "design de interior"],
        "search_keywords": ["elaboração de projetos", "projeto executivo",
                           "projeto arquitetônico", "plano diretor", "PPCI",
                           "levantamento topográfico", "arquitetura"],
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
                      "impressão gráfic", "banner", "sinaliz",
                      "propagand", "marketing", "agência de publicidad", "agencia de publicidad"],
        "search_keywords": ["publicidade", "comunicação", "sinalização", "material gráfico",
                           "propaganda", "marketing"],
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
                      "sonorizac", "buffet", "coffee",
                      "show artístic", "show artistic", "show musical",
                      "apresentação artístic", "apresentacao artistic",
                      "espetáculo", "espetaculo", "artístico", "artistico"],
        "search_keywords": ["evento", "locação", "tendas", "sonorização",
                           "show artístico", "apresentação artística"],
    },
    "alienacao": {
        "label": "Alienação e Leilão",
        "prefixes": ["alienação", "alienacao", "mercadorias apreendida", "leilão", "leilao",
                      "arrematação", "arremataçao"],
        "search_keywords": ["alienação", "mercadorias apreendidas", "leilão"],
    },
}

# ============================================================
# OBJECT NATURE CLASSIFICATION
# ============================================================

# Map cluster_key → default nature when text has no explicit signal
_CLUSTER_DEFAULT_NATURE: dict[str, str] = {
    "saude": "AQUISICAO",
    "alimentacao": "AQUISICAO",
    "limpeza_saneantes": "AQUISICAO",
    "expediente_escolar": "AQUISICAO",
    "informatica": "AQUISICAO",
    "moveis_eletro": "AQUISICAO",
    "veiculos": "AQUISICAO",
    "vestuario": "AQUISICAO",
    "engenharia": "OBRA",
    "manutencao": "SERVICO",
    "projetos_tecn": "SERVICO",
    "consultoria": "SERVICO",
    "vigilancia": "SERVICO",
    "comunicacao": "SERVICO",
    "residuos": "SERVICO",
    "eventos": "SERVICO",
    "alienacao": "ALIENACAO",
}

# Explicit nature signals — checked on the FIRST 150 chars of objeto (lowered)
_NATURE_SIGNALS: list[tuple[str, list[str]]] = [
    ("OBRA", [
        "construção", "construcao", "execução de obra", "execucao de obra",
        "reforma d", "reforma e ", "reforma da ", "reforma do ",
        "pavimentação", "pavimentacao", "implantação d", "implantacao d",
        "edificação", "edificacao", "terraplanagem", "urbanização", "urbanizacao",
        "drenagem", "recapeamento", "contenção", "contencao",
        # Additional construction signals (catches "fornecimento de materiais e mão de obra")
        "mão de obra", "mao de obra", "mão-de-obra", "mao-de-obra",
        "empreitada", "empresa de engenharia", "ramo de engenharia",
        "ramo de construção", "ramo de construcao",
        "ampliação d", "ampliacao d",  # building expansion
        "bloquetamento", "sinalização vi", "sinalizacao vi",
    ]),
    ("SERVICO", [
        "prestação de serviço", "prestacao de servico",
        "contratação de empresa especializada para a prestação",
        "contratacao de empresa especializada para a prestacao",
        "contratação de organização social", "contratacao de organizacao social",
        "credenciamento para", "chamamento público", "chamamento publico",
        "manutenção", "manutencao", "gerenciamento d", "assessoria",
        "consultoria", "desenvolvimento de sistema", "desenvolvimento de software",
        # Additional service signals (without "prestação" prefix)
        "serviço de", "servico de", "serviços de", "servicos de",
        "locação de veículo", "locacao de veiculo",
        "locação de mão", "locacao de mao",
        # Credenciamento signals (typically service, not acquisition)
        "credenciamento de pessoa",
        "credenciamento de profission",
        "credenciamento de prestador",
        "credenciamento médic",
        "credenciamento medic",
        "credenciamento de serviço",
        "credenciamento de servico",
        "pessoa física para prest",
        "pessoa fisica para prest",
        "profissionais de saúde",
        "profissionais de saude",
        "prestação de serviço médic",
        "prestacao de servico medic",
    ]),
    ("LOCACAO", [
        "locação de imóvel", "locacao de imovel", "locação de imóv",
        "aluguel de", "arrendamento",
    ]),
    ("ALIENACAO", [
        "alienação", "alienacao", "mercadorias apreendida", "leilão", "leilao",
    ]),
    ("AQUISICAO", [
        "aquisição de", "aquisicao de", "fornecimento de",
        "compra de", "registro de preço", "registro de preco",
        "chamada pública", "chamada publica",  # PPAIS = purchase from producers
        "material de", "materiais para", "materiais de",
        "medicamento", "equipamento", "mobiliário", "mobiliario",
        "uniforme", "gênero alimentício", "genero alimenticio",
    ]),
]

# Nature threshold: minimum share (%) in history to accept editais of that nature
NATURE_ACCEPTANCE_THRESHOLD_PCT = 5.0


def _matches_nature(signal: str, text: str) -> bool:
    """F25: Word-boundary matching for nature signals."""
    return bool(re.search(r'\b' + re.escape(signal.lower()) + r'\b', text.lower()))


def classify_object_nature(objeto: str, cluster_key: str = "") -> str:
    """Classify the nature of a procurement object (contract or edital).

    Layer 1: Explicit signals with word-boundary matching (F25).
    Layer 2: Default nature from the activity cluster (if no explicit signal).

    Returns: AQUISICAO, OBRA, SERVICO, LOCACAO, ALIENACAO, or INDEFINIDO.
    """
    obj_lower = (objeto or "").lower().strip()[:350]

    # Layer 1: Explicit signals with word boundary (order matters — first match wins)
    for nature, signals in _NATURE_SIGNALS:
        if any(_matches_nature(sig, obj_lower) for sig in signals):
            return nature

    # Layer 2: Cluster default
    if cluster_key and cluster_key in _CLUSTER_DEFAULT_NATURE:
        return _CLUSTER_DEFAULT_NATURE[cluster_key]

    return "INDEFINIDO"


def build_company_nature_profile(clusters: list[dict], contratos: list[dict]) -> dict[str, float]:
    """Build a nature profile from classified historical contracts.

    Returns dict like {"AQUISICAO": 85.0, "OBRA": 10.0, "SERVICO": 5.0}
    """
    if not contratos:
        return {}

    nature_counts: dict[str, int] = {}
    n = len(contratos)

    # Build reverse map: contract → cluster_key
    # (contracts are already classified in clusters by cluster_contract_activities)
    for c in contratos:
        cluster_key = c.get("_cluster_key", "")
        nature = classify_object_nature(c.get("objeto", ""), cluster_key)
        nature_counts[nature] = nature_counts.get(nature, 0) + 1

    # Convert to percentages
    return {k: round(100.0 * v / n, 1) for k, v in sorted(nature_counts.items(), key=lambda x: -x[1])}


def is_nature_compatible(edital_nature: str, nature_profile: dict[str, float]) -> bool:
    """Check if an edital's nature is compatible with the company's profile."""
    if not nature_profile:
        return True  # No profile = accept all
    if edital_nature == "INDEFINIDO":
        return True  # Can't classify = accept
    return nature_profile.get(edital_nature, 0) >= NATURE_ACCEPTANCE_THRESHOLD_PCT


def cluster_contract_activities(
    contratos: list[dict],
    max_clusters: int = 16,
    min_share_pct: float = 1.0,
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

    # F22: Sort categories by longest prefix first for accurate matching
    sorted_categories = sorted(_ACTIVITY_CATEGORIES.items(), key=lambda x: -max(len(p) for p in x[1]["prefixes"]))

    # Phase 1: Dictionary classification via prefix matching
    for c in contratos:
        obj = (c.get("objeto") or "").lower()
        matched = False
        for cat_key, cat_def in sorted_categories:
            if any(prefix in obj for prefix in cat_def["prefixes"]):
                category_contracts[cat_key].append(c)
                c["_cluster_key"] = cat_key  # Tag for nature classification
                matched = True
                break  # First match wins (categories ordered by specificity)
        if not matched:
            c["_cluster_key"] = "_outros"
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

        # Nature profile for this cluster's contracts
        cluster_nature_counts: dict[str, int] = {}
        for c in contracts:
            nat = classify_object_nature(c.get("objeto", ""), cat_key)
            cluster_nature_counts[nat] = cluster_nature_counts.get(nat, 0) + 1
        cluster_nature_pct = {
            k: round(100.0 * v / len(contracts), 1)
            for k, v in sorted(cluster_nature_counts.items(), key=lambda x: -x[1])
        }
        dominant_nature = max(cluster_nature_counts, key=cluster_nature_counts.get) if cluster_nature_counts else "INDEFINIDO"

        # Build user-facing label — sanitize internal "_outros" key
        if cat_key == "_outros":
            _top_kws = unmatched_keywords[:3]
            if _top_kws:
                _cluster_label = " / ".join(kw.title() for kw in _top_kws[:2])
                if len(_top_kws) > 2:
                    _cluster_label += " e outros"
            else:
                _cluster_label = "Atividade Diversificada"
        else:
            _cluster_label = cat_def.get("label", cat_key)

        clusters.append({
            "label": _cluster_label,
            "category_key": cat_key,
            "count": len(contracts),
            "share_pct": round(share, 1),
            "keywords": cat_def.get("search_keywords", unmatched_keywords if cat_key == "_outros" else []),
            "sample_objects": samples,
            "nature_profile": cluster_nature_pct,
            "dominant_nature": dominant_nature,
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
        # Administrative/procurement procedural (appear in ALL contract types)
        # Include BOTH accented and unaccented forms for robust matching
        "prestacao", "prestação", "servicos", "serviços", "servico", "serviço",
        "contratacao", "contratação", "aquisicao", "aquisição",
        "fornecimento", "registro", "precos", "preços", "preco", "preço",
        "item", "itens",
        "solicitado", "requisicao", "requisição", "empenho", "empenha", "despesas",
        "avulso", "nota", "fiscal", "importancia", "importância", "periodo", "período",
        "show", "artistico", "artístico", "artisticos", "artísticos",
        "artistica", "artística", "artisticas", "artísticas",
        "apresentacao", "apresentação", "musical",
        "credenciamento", "concessao", "concessão", "permissao", "permissão", "onerosa",
        "praca", "praça", "festa", "evento", "eventos",
        "publica", "pública", "publico", "público",
        "fundacao", "fundação", "consorcio", "consórcio",
        # Institutional (not product-specific)
        "ufes", "propaes", "campus", "reitoria", "instituto", "autarquia",
        # Dates
        "janeiro", "fevereiro", "marco", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
        "2024", "2025", "2026", "2023", "2022", "2021",
    }

    # Normalize accents for stop word matching (e.g., "prestação" → "prestacao")
    _STOP_NORMALIZED = {_strip_accents(w) for w in _STOP_WORDS}

    # Count word/bigram frequency across contract descriptions
    word_freq: dict[str, int] = {}
    bigram_freq: dict[str, int] = {}

    for c in contratos:
        obj = (c.get("objeto") or "").lower()
        obj = re.sub(r"[^a-záàâãéêíóôõúüç\s]", " ", obj)
        words = [w for w in obj.split() if len(w) >= 4 and _strip_accents(w) not in _STOP_NORMALIZED]

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
        "material", "materiais", "produtos", "itens", "compra",
        "aquisicao", "aquisição", "fornecimento",
        "prestacao", "prestação", "servicos", "serviços", "servico", "serviço",
        "registro", "precos", "preços",
        "municipal", "estadual", "federal", "publica", "publico", "pública", "público",
        "contratacao", "contratação", "empresa", "especializada", "especializado",
        "atendimento", "demandas", "demanda", "secretaria",
        "solicitado", "requisicao", "requisição", "empenho", "empenha",
        "despesas", "importancia", "importância", "periodo", "período", "avulso",
        "show", "artistico", "artístico", "artisticos", "artísticos",
        "artistica", "artística", "artisticas", "artísticas",
        "musical", "apresentacao", "apresentação",
        "credenciamento", "concessao", "concessão", "permissao", "permissão",
        "publica", "pública", "publico", "público",
        "fundacao", "fundação", "consorcio", "consórcio", "praça", "praca",
    }
    _GENERIC_NORMALIZED = {_strip_accents(w) for w in _GENERIC_WORDS}
    rare_but_specific = sorted(
        [(word, freq) for word, freq in word_freq.items()
         if freq == 1 and _strip_accents(word) not in _GENERIC_NORMALIZED and len(word) >= 5],
        key=lambda x: x[0],  # alphabetical for stability
    )

    # Build result: bigrams first (most specific), then frequent words, then rare specifics.
    result: list[str] = []
    seen_terms: set[str] = set()

    # Filter bigrams: reject if BOTH words are generic/stopwords (e.g., "prestação serviços")
    _ALL_GENERIC = _STOP_NORMALIZED | _GENERIC_NORMALIZED
    filtered_bigrams = [
        (bg, freq) for bg, freq in frequent_bigrams
        if not all(_strip_accents(w) in _ALL_GENERIC for w in bg.split())
    ]

    # Layer 1: Frequent bigrams (highest signal — e.g. "merenda escolar", "material limpeza")
    for term, _freq in filtered_bigrams:
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

    # Primary: keywords from dominant cluster
    for cluster in clusters:
        for kw in cluster["keywords"]:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                result.append(kw)
                seen.add(kw_lower)
            if len(result) >= max_keywords:
                return result

    # F23: Ensure at least top-2 keywords from each non-dominant (secondary) cluster
    if len(clusters) > 1:
        for cluster in clusters[1:]:
            cluster_kws = [kw for kw in cluster.get("keywords", [])[:2]]
            for kw in cluster_kws:
                kw_lower = kw.lower()
                if kw_lower not in seen:
                    result.append(kw)
                    seen.add(kw_lower)

    return result


def _modalidades_for_cluster(cluster_label: str,
                             nature_profile: dict[str, float] | None = None,
                             cluster_nature: dict[str, float] | None = None,
                             cluster_dominant: str = "") -> set[int]:
    """Select appropriate modalidades based on cluster activity type.

    For named clusters (e.g., "Saúde e Materiais Hospitalares"), uses indicator matching.
    For generic clusters ("_outros", "Móveis e Eletrodomésticos" without clear signals),
    uses the CLUSTER's own nature profile first (more accurate for mixed companies),
    then falls back to the company's global nature profile.

    Args:
        cluster_label: Human-readable cluster name.
        nature_profile: Company-wide nature profile (global fallback).
        cluster_nature: This cluster's own nature_profile from cluster_contract_activities().
        cluster_dominant: This cluster's dominant_nature (shortcut).
    """
    label_lower = cluster_label.lower()
    # Materials/supplies clusters -> include Dispensa
    supply_indicators = [
        "material", "medicamento", "hospitalar", "odontol", "saneante",
        "limpeza", "higiene", "aliment", "gênero", "expediente",
        "equipamento", "mobiliário", "vestuário", "uniforme",
        "informática", "tecnologia", "combustível", "lubrificante",
    ]
    # Construction/obras clusters -> traditional modalidades
    obras_indicators = [
        "construção", "obra", "paviment", "edificação", "reforma",
        "engenharia", "infraestrutura", "saneamento", "drenagem",
    ]

    if any(ind in label_lower for ind in supply_indicators):
        return MODALIDADES_AQUISICAO - MODALIDADES_EXCLUIDAS
    if any(ind in label_lower for ind in obras_indicators):
        return MODALIDADES_OBRAS - MODALIDADES_EXCLUIDAS

    # --- Nature-based fallback (cluster-level first, then global) ---
    _NATURE_TO_MODALIDADES = {
        "AQUISICAO": MODALIDADES_AQUISICAO,
        "OBRA": MODALIDADES_OBRAS,
        "SERVICO": MODALIDADES_SERVICOS,
    }

    # Priority 1: Use cluster's own nature profile (per-cluster accuracy)
    if cluster_dominant and cluster_dominant in _NATURE_TO_MODALIDADES:
        # If cluster has a clear dominant nature, use it directly
        cluster_dom_pct = (cluster_nature or {}).get(cluster_dominant, 0)
        if cluster_dom_pct >= 40:
            return _NATURE_TO_MODALIDADES[cluster_dominant] - MODALIDADES_EXCLUIDAS

    # Priority 2: Use cluster nature profile even below 40% — pick highest
    if cluster_nature:
        best_nature = max(cluster_nature, key=cluster_nature.get)
        if best_nature in _NATURE_TO_MODALIDADES:
            return _NATURE_TO_MODALIDADES[best_nature] - MODALIDADES_EXCLUIDAS

    # Priority 3: Global nature profile (for clusters without own nature data)
    if nature_profile:
        dominant_nature = max(nature_profile, key=nature_profile.get)
        dominant_pct = nature_profile.get(dominant_nature, 0)
        # Lowered from 50% to 40%; if still no winner, pick dominant anyway
        if dominant_pct >= 40 and dominant_nature in _NATURE_TO_MODALIDADES:
            return _NATURE_TO_MODALIDADES[dominant_nature] - MODALIDADES_EXCLUIDAS
        # Even below 40%, use dominant if it's a known nature type
        if dominant_nature in _NATURE_TO_MODALIDADES:
            return _NATURE_TO_MODALIDADES[dominant_nature] - MODALIDADES_EXCLUIDAS

    # Default: competitive modalidades only (never include non-competitive by default)
    return MODALIDADES_COMPETITIVAS - MODALIDADES_EXCLUIDAS


def extract_keywords_per_cluster(
    contratos: list[dict],
    max_per_cluster: int = 15,
    max_clusters: int = 16,
    nature_profile: dict[str, float] | None = None,
) -> list[dict]:
    """Extract keywords grouped by activity cluster.

    Returns list of dicts: [{"label": "Saúde/Hospitalar", "share_pct": 30.4,
                             "keywords": ["hospitalar", "medicamento", ...],
                             "modalidades": {4, 5, 6, 7}}]
    """
    clusters = cluster_contract_activities(contratos)
    if not clusters:
        return []

    result = []
    for cluster in clusters[:max_clusters]:
        kws = cluster.get("keywords", [])[:max_per_cluster]
        if not kws:
            continue
        label = cluster.get("label", "Outros")
        # Pass cluster's own nature data for per-cluster modalidade selection
        mods = _modalidades_for_cluster(
            label,
            nature_profile=nature_profile,
            cluster_nature=cluster.get("nature_profile"),
            cluster_dominant=cluster.get("dominant_nature", ""),
        )
        result.append({
            "label": label,
            "category_key": cluster.get("category_key", ""),
            "share_pct": cluster.get("share_pct", 0),
            "keywords": kws,
            "modalidades": mods,
            "nature_profile": cluster.get("nature_profile"),
            "dominant_nature": cluster.get("dominant_nature", ""),
        })

    return result


def extract_ufs_from_contracts(
    contratos: list[dict],
    uf_sede: str = "",
    max_ufs: int = 27,
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

    # Include ALL UFs where the company ever operated (at least 1 contract).
    # Only apply frequency threshold when there are many UFs to prevent scatter.
    n_total = sum(uf_counts.values())
    if len(uf_counts) <= 10:
        # 10 or fewer UFs — include ALL of them (every UF matters)
        effective_min = 1
    elif n_total <= 5:
        effective_min = 1
    elif n_total <= 20:
        effective_min = 1  # Even 1 contract signals presence
    else:
        effective_min = min(3, max(1, n_total // 100))  # ~1% prevalence, floor at 1, cap at 3

    # All UFs with at least effective_min contracts, sorted by count descending
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


def classify_edital_object_type(edital: dict) -> str:
    """Classify an edital's OBJECT into a sector key for habilitação/risk/cost.

    This determines what the EDITAL is about (not the company's CNAE).
    A construction company bidding on a materials supply pregão should get
    materials supply habilitação requirements, not construction requirements.

    Returns sector_key string to use for habilitação, risk flags, and cost profiles.
    """
    raw_objeto = (edital.get("objeto") or edital.get("objetoCompra") or "").lower()
    # Match both accented and unaccented text
    objeto = _strip_accents(raw_objeto)
    modalidade = (edital.get("modalidade") or "").lower()

    # NOTE: All keywords below are accent-stripped since `objeto` was processed by _strip_accents()

    # --- Credenciamento / Inexigibilidade for professional services ---
    if "inexigibilidade" in modalidade:
        if any(kw in objeto for kw in [
            "credenciamento de pessoa", "prestacao de servicos medic",
            "contratacao de medic", "atendimento fisiotera",
            "servico de saude", "profissionais de saude",
        ]):
            return "servicos_profissionais"

    # --- Fornecimento de materiais (non-construction supply) ---
    # These keywords indicate SUPPLY of goods, not execution of services/works.
    # Ordered: specific terms FIRST, generic terms ("fornecimento de", "aquisicao de",
    # "registro de precos") LAST with guard clause to avoid misclassifying services/obras.
    _SUPPLY_SPECIFIC = [
        "material medico", "material hospitalar", "materiais medico",
        "materiais hospitalar", "insumo hospitalar", "insumos hospitalar",
        "medicamento", "farmaco", "farmaceutic",
        "material de consumo", "materiais de consumo",
        "material de expediente", "material escolar", "material didatico",
        "genero alimentic", "alimento", "merenda",
        "material de limpeza", "saneante", "produto de limpeza",
        "equipamento ambulat", "equipamento hospitalar",
        "mobiliario", " movel", "estofamento",
        "eletrodomestic",
        "uniforme", "vestuario", "fardamento",
        "combustivel", "abastecimento",
        "material eletric",
        "material hidraulic",
        "papel", "toner", "cartucho",
    ]
    # Generic supply terms — only match if the object does NOT also contain service/obra words
    _SERVICE_GUARD = ["servico", "obra", "construcao", "reforma", "manutencao",
                      "consultoria", "assessoria", "treinamento", "capacitacao"]
    _SUPPLY_GENERIC = ["fornecimento de", "aquisicao de", "registro de precos"]
    _is_specific = any(kw in objeto for kw in _SUPPLY_SPECIFIC)
    _is_generic = (
        any(kw in objeto for kw in _SUPPLY_GENERIC)
        and not any(kw in objeto for kw in _SERVICE_GUARD)
    )
    if _is_specific or _is_generic:
        # Further classify supply type.
        # ORDER MATTERS: more specific categories first, catch-all last.
        # "merenda escolar" should match alimentos (not papelaria via "escolar").
        if any(kw in objeto for kw in ["hospitalar", "medico", "ambulat",
                                        "enfermagem", "medicamento", "farmac"]):
            return "fornecimento_saude"
        if any(kw in objeto for kw in ["limpeza", "saneante", "higieniza"]):
            return "fornecimento_limpeza"
        # Alimentos BEFORE papelaria — "merenda escolar" is food, not stationery
        if any(kw in objeto for kw in ["aliment", "merenda", "refeicao",
                                        "hortifruti", "cesta", "carne"]):
            return "fornecimento_alimentos"
        if any(kw in objeto for kw in ["expediente", "escolar", "didatic",
                                        "papel", "toner", "cartucho"]):
            return "fornecimento_papelaria"
        # Use " movel" (with space prefix) to avoid matching "imovel"
        if any(kw in objeto for kw in [" movel", "mobiliario", "estofamento",
                                        "eletrodomestic"]):
            return "fornecimento_mobiliario"
        return "fornecimento_geral"

    # --- Construction / engineering works ---
    if any(kw in objeto for kw in [
        "obra", "construcao", "edificac",
        "reforma", "ampliacao", "pavimentac",
        "drenagem", "terraplanagem", "terraplenagem", "fundacao",
        "instalacao eletric",
    ]):
        return "engenharia"

    # --- Services ---
    if any(kw in objeto for kw in [
        "prestacao de servico",
        "contratacao de empresa para",
        "manutencao", "limpeza e conserv",
        "consultoria", "assessoria",
    ]):
        return "servicos_gerais"

    # --- Software / IT ---
    if any(kw in objeto for kw in [
        "sistema", "software", "desenvolvimento", "tecnologia da informac",
    ]):
        return "software"

    # --- Concessão ---
    if any(kw in objeto for kw in ["concessao", "permissao"]):
        return "concessao"

    # Fallback: return empty to indicate "use company sector_key"
    return ""


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
    # --- Fornecimento (supply) sectors ---
    "fornecimento_saude": {
        "materiais_hospitalares": ["material hospitalar", "descartável", "epi hospitalar", "luva", "seringa", "gaze", "soro fisiológico"],
        "medicamentos": ["medicamento", "fármaco", "insumo farmacêutico", "vacina"],
        "equipamentos_medicos": ["equipamento hospitalar", "equipamento médico", "ambulatorial", "maca", "cama hospitalar"],
    },
    "fornecimento_limpeza": {
        "saneantes": ["saneante", "desinfetante", "detergente", "alvejante", "produto de limpeza"],
        "higiene": ["papel higiênico", "sabonete", "álcool", "higienização"],
    },
    "fornecimento_papelaria": {
        "escritorio": ["papel", "caneta", "toner", "cartucho", "material de escritório", "envelope"],
        "escolar": ["material escolar", "caderno", "lápis", "borracha", "material didático"],
    },
    "fornecimento_mobiliario": {
        "moveis_escritorio": ["mesa", "cadeira", "armário", "estante", "gaveteiro"],
        "moveis_hospitalares": ["cama hospitalar", "maca", "mesa cirúrgica"],
        "eletrodomesticos": ["geladeira", "fogão", "micro-ondas", "ar condicionado"],
        "estofamento": ["estofamento", "reforma de móvel", "tapeçaria"],
    },
    "fornecimento_alimentos": {
        "generos": ["gênero alimentício", "cesta básica", "hortifrúti", "alimento"],
        "refeicao": ["refeição", "merenda", "alimentação escolar"],
    },
    "fornecimento_geral": {
        "materiais_diversos": ["material de consumo", "registro de preços", "fornecimento"],
        "suprimentos": ["suprimento", "insumo", "material de expediente", "material de limpeza"],
    },
    "servicos_profissionais": {
        "medicos": ["serviço médico", "atendimento médico", "consulta", "plantão"],
        "enfermagem": ["enfermeiro", "técnico de enfermagem", "cuidador"],
        "outros_profissionais": ["fisioterapia", "psicologia", "nutrição", "odontologia"],
    },
    "servicos_gerais": {
        "manutencao": ["manutenção", "reparo", "conserto", "assistência técnica"],
        "consultoria": ["consultoria", "assessoria", "treinamento"],
        "eventos": ["evento", "organização", "cerimonial"],
    },
    "concessao": {
        "uso_espaco": ["concessão de uso", "cessão de espaço", "permissão de uso"],
        "exploracao": ["exploração comercial", "cantina", "bar", "restaurante"],
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
    # --- Fornecimento de materiais (supply sectors) ---
    "fornecimento_saude": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Atestado de fornecimento de materiais hospitalares ou similares"],
        "certifications": ["AFE/ANVISA (se medicamentos ou correlatos)", "Alvará Sanitário (se aplicável)"],
        "fiscal": ["CND Federal/Previdenciária", "CND Estadual", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "fornecimento_limpeza": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Atestado de fornecimento de produtos de limpeza ou similares"],
        "certifications": ["AFE/ANVISA (se saneantes domissanitários)"],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "fornecimento_papelaria": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Atestado de fornecimento de material de expediente ou similares"],
        "certifications": [],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "fornecimento_mobiliario": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Atestado de fornecimento de mobiliário ou similares"],
        "certifications": [],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "fornecimento_alimentos": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Atestado de fornecimento de gêneros alimentícios ou similares"],
        "certifications": ["Alvará Sanitário", "Licença da Vigilância Sanitária"],
        "fiscal": ["CND Federal/Previdenciária", "CND Estadual", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "fornecimento_geral": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Atestado de fornecimento de materiais similares"],
        "certifications": [],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "servicos_profissionais": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Registro profissional ativo no conselho de classe (CRM, CRF, COREN, etc.)"],
        "certifications": ["Conselho profissional (CRM/CRF/COREN)", "Alvará Sanitário (se aplicável)"],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "servicos_gerais": {
        "capital_minimo_pct": 0.05,
        "atestados": ["Atestado de prestação de serviço similar"],
        "certifications": [],
        "fiscal": ["CND Federal/Previdenciária", "CND Municipal", "CRF FGTS", "CNDT Trabalhista"],
    },
    "concessao": {
        "capital_minimo_pct": 0.10,
        "atestados": ["Atestado de capacidade técnica para exploração de atividade similar"],
        "certifications": [],
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
# NOTE: These flags are applied per-edital based on the EDITAL's effective sector,
# not the company's CNAE. A materials supply pregão should NOT get "aditivos em obras".
_SECTOR_RISK_FLAGS: dict[str, list[str]] = {
    "facilities": ["Subprecificação crônica em contratos de limpeza — margem real pode ser menor que estimada"],
    "engenharia": ["Aditivos contratuais frequentes (25-50%) em obras públicas — considerar margem de segurança"],
    "engenharia_rodoviaria": ["Obras rodoviárias frequentemente sofrem paralisações por questões ambientais ou orçamentárias"],
    "vigilancia": ["Convenção coletiva pode impactar custos — verificar dissídio da categoria na região"],
    "saude": ["Regulamentação ANVISA pode atrasar execução — verificar licenças necessárias"],
    "software": ["Editais de TI frequentemente exigem quadro técnico com certificações proprietárias específicas"],
    "alimentos": ["Contratos de alimentação têm reajuste atrelado a índices de preço — verificar cláusula de reequilíbrio"],
    "fornecimento_saude": ["Produtos hospitalares podem exigir registro ANVISA individual — verificar exigências do edital"],
    "fornecimento_limpeza": ["Saneantes domissanitários exigem AFE/ANVISA — verificar se edital lista produtos com registro obrigatório"],
    "fornecimento_papelaria": ["Mercado altamente commoditizado — margem comprimida por volume de concorrentes"],
    "fornecimento_alimentos": ["Contratos de alimentação têm reajuste atrelado a índices de preço — verificar cláusula de reequilíbrio"],
    "fornecimento_mobiliario": ["Mobiliário hospitalar pode exigir certificação INMETRO — verificar normas técnicas no edital"],
    "servicos_profissionais": ["Credenciamento exige registro profissional ativo (CRM, CRF, COREN) — verificar se empresa tem profissionais habilitados no quadro"],
    "concessao": ["Contratos de concessão têm cláusulas de desempenho e penalidades — analisar indicadores exigidos"],
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
    # Fornecimento (supply) — lower costs (electronic, no site visits)
    "fornecimento_saude": 800.0,
    "fornecimento_limpeza": 500.0,
    "fornecimento_papelaria": 500.0,
    "fornecimento_mobiliario": 800.0,
    "fornecimento_alimentos": 500.0,
    "fornecimento_geral": 600.0,
    "servicos_profissionais": 1000.0,
    "servicos_gerais": 1500.0,
    "concessao": 3000.0,
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
    capital = _safe_float(empresa.get("capital_social")) or 0.0
    valor = _safe_float(edital.get("valor_estimado")) or 0.0
    min_pct = reqs["capital_minimo_pct"]
    if valor > 0 and capital > 0:
        threshold = valor * min_pct
        if capital >= threshold:
            dimensions.append({
                "dimension": "Capital Mínimo",
                "status": "OK",
                "detail": f"Capital {_fmt_brl(capital)} >= {min_pct * 100:.0f}% do valor {_fmt_brl(valor)}",
            })
            dim_scores.append(100)
        elif capital >= threshold * 0.5:
            dimensions.append({
                "dimension": "Capital Mínimo",
                "status": "ATENÇÃO",
                "detail": f"Capital {_fmt_brl(capital)} abaixo do mínimo típico {_fmt_brl(threshold)} mas acima de 50%",
            })
            gaps.append(f"Capital social pode ser insuficiente ({_fmt_brl(capital)} vs mínimo {_fmt_brl(threshold)})")
            dim_scores.append(50)
        else:
            dimensions.append({
                "dimension": "Capital Mínimo",
                "status": "CRÍTICO",
                "detail": f"Capital {_fmt_brl(capital)} muito abaixo do mínimo típico {_fmt_brl(threshold)}",
            })
            gaps.append(f"Capital social insuficiente ({_fmt_brl(capital)} vs mínimo {_fmt_brl(threshold)})")
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

    # ================================================================
    # GAP-2: Expanded 25-item habilitação checklist
    # ================================================================
    # Derive statuses from available data
    cnpj_ativo = empresa.get("situacao_cadastral", "").upper() in ("ATIVA", "02", "2", "")
    cnpj_obj_compat = True  # Assume compatible unless we have specific info

    # Sanções
    sancoes = empresa.get("sancoes", {})
    has_ceis = bool(sancoes.get("ceis")) if isinstance(sancoes, dict) else False
    has_cnep = bool(sancoes.get("cnep")) if isinstance(sancoes, dict) else False

    # SICAF
    sicaf_status_val = sicaf.get("status", "") if isinstance(sicaf, dict) else ""
    sicaf_crc = sicaf.get("crc", {}) if isinstance(sicaf, dict) else {}
    sicaf_ok = sicaf_status_val in ("CADASTRADO", "ATIVO") or sicaf_crc.get("status_cadastral") == "CADASTRADO"
    sicaf_falhou = sicaf_status_val == "FALHA_COLETA"

    # Capital
    cap_ok = capital > 0 and valor > 0 and capital >= valor * min_pct
    cap_status = "OK" if cap_ok else ("PENDENTE" if (capital > 0 and valor > 0) else "NAO_VERIFICADO")

    # Acervo (from edital-level data if available)
    edital_acervo = edital.get("acervo_status", "NAO_VERIFICADO")
    acervo_op_status = "OK" if edital_acervo == "CONFIRMADO" else ("PENDENTE" if edital_acervo == "PARCIAL" else "NAO_VERIFICADO")

    # CAT check from habilitacao requirements
    has_certs = bool(reqs.get("certifications"))
    cat_status = "NAO_VERIFICADO"
    if has_certs:
        cnae_principal = empresa.get("cnae_principal", "")
        has_compatible_cnae = any(
            cnae_prefix in str(cnae_principal)
            for cnae_prefix in _CNAE_TO_SECTOR_KEY
            if _CNAE_TO_SECTOR_KEY[cnae_prefix] == sector_key
        )
        cat_status = "OK" if has_compatible_cnae else "PENDENTE"

    # Fiscal items from SICAF
    sicaf_fiscal_status = "OK" if sicaf_ok else ("PENDENTE" if sicaf_falhou else "NAO_VERIFICADO")

    checklist_25 = {
        "juridica": [
            {"item": "CNPJ ativo com objeto social compatível", "status": "OK" if cnpj_ativo else "PENDENTE",
             "detalhe": f"Situação: {empresa.get('situacao_cadastral', 'não informada')}"},
            {"item": "Contrato/estatuto social atualizado", "status": "NAO_VERIFICADO",
             "detalhe": "Verificar no SICAF ou junta comercial"},
            {"item": "Procuração do representante legal", "status": "NAO_VERIFICADO",
             "detalhe": "Necessária para assinatura de proposta"},
            {"item": "Alvará de funcionamento", "status": "NAO_VERIFICADO",
             "detalhe": "Emitido pela prefeitura do município sede"},
        ],
        "fiscal": [
            {"item": "CND Conjunta RFB/PGFN (Federal)", "status": sicaf_fiscal_status,
             "detalhe": "Via SICAF" if sicaf_ok else ("Coleta SICAF falhou" if sicaf_falhou else "Emitir no site da RFB")},
            {"item": "CND Estadual (ICMS)", "status": "NAO_VERIFICADO",
             "detalhe": "Emitir na Secretaria da Fazenda do estado sede"},
            {"item": "CND Municipal (ISS)", "status": "NAO_VERIFICADO",
             "detalhe": "Emitir na prefeitura do município sede"},
            {"item": "CRF/FGTS", "status": sicaf_fiscal_status,
             "detalhe": "Via SICAF" if sicaf_ok else ("Coleta SICAF falhou" if sicaf_falhou else "Emitir no site da CEF")},
            {"item": "CNDT (Certidão Negativa Débitos Trabalhistas)", "status": sicaf_fiscal_status,
             "detalhe": "Via SICAF" if sicaf_ok else ("Coleta SICAF falhou" if sicaf_falhou else "Emitir no portal do TST")},
            {"item": "Inscrição no cadastro de contribuintes", "status": "NAO_VERIFICADO",
             "detalhe": "Estadual e/ou municipal conforme atividade"},
            {"item": "SICAF ativo e regular", "status": "OK" if sicaf_ok else ("PENDENTE" if sicaf_falhou else "NAO_VERIFICADO"),
             "detalhe": f"Status: {sicaf_status_val}" if sicaf_status_val else "Não consultado"},
        ],
        "tecnica": [
            {"item": "Atestado de capacidade técnica operacional", "status": acervo_op_status,
             "detalhe": f"Acervo: {edital_acervo}" if edital_acervo != "NAO_VERIFICADO" else "Verificar atestados de obras/serviços similares"},
            {"item": "Atestado de capacidade técnica profissional", "status": "NAO_VERIFICADO",
             "detalhe": "RT com experiência comprovada no objeto"},
            {"item": "CAT/CREA ou RRT/CAU registrados", "status": cat_status,
             "detalhe": f"CNAE compatível com setor" if cat_status == "OK" else "Verificar registro profissional"},
            {"item": "Registro no conselho profissional", "status": "NAO_VERIFICADO",
             "detalhe": "CREA, CAU, CRM, CRO conforme atividade"},
            {"item": "Declaração de equipe técnica disponível", "status": "NAO_VERIFICADO",
             "detalhe": "Vínculo dos profissionais com a empresa"},
        ],
        "economico_financeira": [
            {"item": "Balanço patrimonial último exercício", "status": "NAO_VERIFICADO",
             "detalhe": "Registrado na junta comercial"},
            {"item": "Demonstrações contábeis", "status": "NAO_VERIFICADO",
             "detalhe": "DRE e balanço do último exercício social"},
            {"item": "Certidão negativa falência/recuperação judicial", "status": "NAO_VERIFICADO",
             "detalhe": "Emitir no fórum da comarca sede"},
            {"item": "Capital social mínimo compatível", "status": cap_status,
             "detalhe": f"Capital {_fmt_brl(capital)} vs mínimo {_fmt_brl(valor * min_pct)}" if (capital > 0 and valor > 0) else "Dados insuficientes"},
            {"item": "Patrimônio líquido compatível", "status": cap_status,
             "detalhe": f"Estimado a partir do capital social ({_fmt_brl(capital)})" if capital > 0 else "Capital social não disponível"},
        ],
        "declaracoes": [
            {"item": "Consulta CEIS (CGU)", "status": "PENDENTE" if has_ceis else "OK",
             "detalhe": "Sanção ativa no CEIS" if has_ceis else "Sem registros no CEIS"},
            {"item": "Consulta CNEP (CGU)", "status": "PENDENTE" if has_cnep else "OK",
             "detalhe": "Penalidade registrada no CNEP" if has_cnep else "Sem registros no CNEP"},
            {"item": "Lista de inidôneas TCU", "status": "NAO_VERIFICADO",
             "detalhe": "Consultar portal do TCU"},
            {"item": "Consulta TCE estadual", "status": "NAO_VERIFICADO",
             "detalhe": "Consultar tribunal de contas do estado"},
            {"item": "Declaração art. 7° CF (trabalho infantil)", "status": "NAO_VERIFICADO",
             "detalhe": "Declaratório — elaborar conforme modelo do edital"},
        ],
    }

    # Count totals
    total_ok = 0
    total_pendente = 0
    total_nao_verificado = 0
    for category_items in checklist_25.values():
        if not isinstance(category_items, list):
            continue
        for item in category_items:
            s = item.get("status", "")
            if s == "OK":
                total_ok += 1
            elif s == "PENDENTE":
                total_pendente += 1
            else:
                total_nao_verificado += 1

    checklist_25["total_ok"] = total_ok
    checklist_25["total_pendente"] = total_pendente
    checklist_25["total_nao_verificado"] = total_nao_verificado
    checklist_25["cobertura_pct"] = round(total_ok / 25 * 100, 1)

    return {
        "status": overall,
        "score": score,
        "dimensions": dimensions,
        "gaps": gaps,
        "habilitacao_checklist_25": checklist_25,
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
    valor = _safe_float(edital.get("valor_estimado")) or 0.0
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
                    + _fmt_brl(travel_cost) + " por sessão"
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
        supplier_values[key] = supplier_values.get(key, 0) + (_safe_float(c.get("valor")) or 0.0)
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
    capital = _safe_float(empresa.get("capital_social")) or 0.0
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
        elif prob < 0.10 and (valor or 0) > 0:
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
# PORTFOLIO OPTIMIZATION (capacity, correlation, optimal set)
# ============================================================

def _fmt_brl_portfolio(v: float) -> str:
    """Format value as R$ with Brazilian number separators."""
    return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def estimate_operational_capacity(empresa: dict, maturity_profile: dict) -> dict:
    """Estimate how many simultaneous bids the company can realistically handle.

    Uses capital_social, contract history, and maturity profile as proxies
    for operational bandwidth (team size, bonding capacity, cash flow).
    """
    capital = _safe_float(empresa.get("capital_social")) or 0.0
    total_contracts = maturity_profile.get("total_contract_count", 0)
    geo_spread = maturity_profile.get("geographic_spread", 0)
    profile = maturity_profile.get("profile", "ENTRANTE")

    # Base capacity — any company can handle at least 3 simultaneous bids
    base_capacity = 3

    # Experience bonus
    if total_contracts > 100:
        base_capacity += 3  # 50+ gives +2, 100+ gives +1 more
    elif total_contracts > 50:
        base_capacity += 2

    # Geographic reach bonus — operates in 4+ UFs
    if geo_spread > 3:
        base_capacity += 1

    # Maturity profile bonus
    if profile in ("ESTABELECIDO", "REGIONAL"):
        base_capacity += 1

    max_capacity = min(base_capacity, 10)

    # Max portfolio value — rough heuristic: capital × 5
    max_portfolio_value = capital * 5.0 if capital > 0 else 0.0

    # Confidence based on data quality
    if total_contracts >= 10 and capital > 0:
        confidence = "alta"
    elif total_contracts >= 3 or capital > 0:
        confidence = "media"
    else:
        confidence = "baixa"

    rationale_parts = [f"Capacidade base: 3 licitações simultâneas"]
    if total_contracts > 100:
        rationale_parts.append(f"+3 por histórico robusto ({total_contracts} contratos)")
    elif total_contracts > 50:
        rationale_parts.append(f"+2 por histórico sólido ({total_contracts} contratos)")
    if geo_spread > 3:
        rationale_parts.append(f"+1 por atuação em {geo_spread} UFs")
    if profile in ("ESTABELECIDO", "REGIONAL"):
        rationale_parts.append(f"+1 por perfil {profile.lower()}")
    rationale_parts.append(f"Capacidade final: {max_capacity} (cap: 10)")
    if max_portfolio_value > 0:
        rationale_parts.append(
            f"Valor máximo de carteira: {_fmt_brl_portfolio(max_portfolio_value)} "
            f"(capital social {_fmt_brl_portfolio(capital)} × 5)"
        )

    return {
        "max_simultaneous_bids": max_capacity,
        "max_portfolio_value": round(max_portfolio_value, 2),
        "confidence": confidence,
        "rationale": ". ".join(rationale_parts),
        "_source": _source_tag("CALCULATED", f"capital={capital}, contratos={total_contracts}, geo={geo_spread}"),
    }


def calculate_portfolio_correlation(editais: list[dict]) -> dict:
    """Identify correlated bids (same organ/municipality = correlated risk).

    Bidding for multiple editais from the same organ in the same municipality
    concentrates risk: if that organ delays payments or cancels, all bids
    are affected simultaneously.
    """
    # Group by (cnpj_orgao, municipio)
    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for i, ed in enumerate(editais):
        orgao_cnpj = ed.get("cnpj_orgao", ed.get("orgao", "N/I"))
        municipio = (ed.get("municipio") or ed.get("localidade") or "N/I")
        key = (orgao_cnpj, municipio)
        groups[key].append(i)

    correlated_groups = []
    max_group_size = 0
    for (orgao, mun), indices in groups.items():
        if len(indices) > 1:
            correlated_groups.append({
                "orgao": orgao,
                "municipio": mun,
                "edital_indices": indices,
                "n_editais": len(indices),
                "risk_note": (
                    f"{len(indices)} editais do mesmo órgão em {mun} — "
                    f"risco concentrado em caso de atraso de pagamento ou cancelamento"
                ),
            })
        if len(indices) > max_group_size:
            max_group_size = len(indices)

    total = len(editais)
    if total > 0:
        diversification_score = round(1.0 - (max_group_size / total), 3)
    else:
        diversification_score = 1.0

    n_in_groups = sum(g["n_editais"] for g in correlated_groups)
    n_independent = total - n_in_groups

    return {
        "diversification_score": diversification_score,
        "correlated_groups": correlated_groups,
        "n_independent": n_independent,
        "_source": _source_tag("CALCULATED", f"{total} editais, {len(correlated_groups)} grupos correlacionados"),
    }


def optimize_portfolio(
    editais: list[dict],
    capacity: dict,
    correlation: dict,
    participation_cost_per_edital: float,
) -> dict:
    """Select and rank the optimal set of bids under capacity constraints.

    Greedy selection by efficiency (ROI / custo), with correlation penalty
    for concentrated risk. Respects max_simultaneous_bids and max_portfolio_value.
    """
    # Build correlated-index lookup: edital_index -> group indices
    correlated_indices: dict[int, set[int]] = {}
    for group in correlation.get("correlated_groups", []):
        idx_set = set(group["edital_indices"])
        for idx in idx_set:
            correlated_indices[idx] = idx_set

    # Filter eligible editais (QUICK_WIN, OPORTUNIDADE, INVESTIMENTO)
    eligible_categories = {"QUICK_WIN", "OPORTUNIDADE", "INVESTIMENTO"}
    candidates = []
    for i, ed in enumerate(editais):
        cat = ed.get("strategic_category", "")
        if cat not in eligible_categories:
            continue

        valor = _safe_float(ed.get("valor_estimado")) or 0.0
        custo = _safe_float(ed.get("roi_potential", {}).get("custo_participacao")) or 0.0
        if custo <= 0:
            custo = participation_cost_per_edital

        roi_max = _safe_float(ed.get("roi_potential", {}).get("roi_max")) or 0.0
        roi_min = _safe_float(ed.get("roi_potential", {}).get("roi_min")) or 0.0

        # Use roi_max for efficiency unless negative, then use roi_min
        roi_ref = roi_max if roi_max > 0 else roi_min
        efficiency = roi_ref / custo if custo > 0 else 0.0

        objeto = (ed.get("objeto") or ed.get("objetoCompra") or "")[:80]
        candidates.append({
            "edital_idx": i,
            "objeto_resumo": objeto,
            "valor": valor,
            "custo": custo,
            "roi_max": roi_max,
            "roi_min": roi_min,
            "efficiency": efficiency,
            "strategic_category": cat,
        })

    if not candidates:
        return {
            "optimal_set": [],
            "total_expected_roi": 0.0,
            "capacity_utilization_pct": 0.0,
            "capacity_overflow_warning": "Nenhum edital elegível para otimização (todos inacessíveis ou baixa prioridade).",
            "_source": _source_tag("CALCULATED", "0 candidatos elegíveis"),
        }

    # Sort by efficiency descending
    candidates.sort(key=lambda c: c["efficiency"], reverse=True)

    max_bids = capacity.get("max_simultaneous_bids", 5)
    max_value = capacity.get("max_portfolio_value", float("inf"))

    selected = []
    selected_indices: set[int] = set()
    cumulative_value = 0.0
    cumulative_roi = 0.0
    overflow_warning = None

    for cand in candidates:
        if len(selected) >= max_bids:
            overflow_warning = (
                f"Capacidade atingida: {max_bids} licitações simultâneas. "
                f"{len(candidates) - len(selected)} editais elegíveis não incluídos."
            )
            break

        new_value = cumulative_value + cand["valor"]
        if max_value > 0 and new_value > max_value:
            overflow_warning = (
                f"Valor máximo de carteira atingido: "
                f"{_fmt_brl_portfolio(max_value)}. "
                f"Edital de {_fmt_brl_portfolio(cand['valor'])} não incluído."
            )
            break

        # Apply correlation penalty if another edital from same group already selected
        eff = cand["efficiency"]
        correlation_note = None
        edital_idx = cand["edital_idx"]
        if edital_idx in correlated_indices:
            overlap = correlated_indices[edital_idx] & selected_indices
            if overlap:
                eff *= 0.7
                correlation_note = (
                    f"Penalidade de correlação aplicada (×0.7) — "
                    f"mesmo órgão/município que edital(is) {sorted(overlap)}"
                )

        # Re-check ordering is still favorable (efficiency may have dropped)
        # But greedy keeps it simple — we just note it
        priority = len(selected) + 1
        roi_expected = (cand["roi_max"] + cand["roi_min"]) / 2.0 if cand["roi_min"] != 0 else cand["roi_max"]
        cumulative_roi += roi_expected
        cumulative_value = new_value

        selected.append({
            "edital_idx": edital_idx,
            "priority": priority,
            "objeto_resumo": cand["objeto_resumo"],
            "valor": cand["valor"],
            "custo": cand["custo"],
            "roi_expected": round(roi_expected),
            "roi_cumulative": round(cumulative_roi),
            "correlation_note": correlation_note,
        })
        selected_indices.add(edital_idx)

    utilization = round(100.0 * len(selected) / max_bids, 1) if max_bids > 0 else 0.0

    return {
        "optimal_set": selected,
        "total_expected_roi": round(cumulative_roi),
        "capacity_utilization_pct": utilization,
        "capacity_overflow_warning": overflow_warning,
        "_source": _source_tag("CALCULATED", f"{len(selected)}/{len(candidates)} selecionados, utilização {utilization}%"),
    }


# ============================================================
# FIX 2: 3-GATE SECTOR RELEVANCE FILTER
# ============================================================

# Hard exclusions for engenharia_civil sector (Gate 1).
# If ANY of these phrases appears (case-insensitive) in the edital objeto,
# the edital is IMMEDIATELY rejected regardless of keyword matches.
HARD_EXCLUSIONS_ENGENHARIA: frozenset[str] = frozenset({
    "buffet", "coffee break", "lavanderia", "limpeza predial", "limpeza hospitalar",
    "alimentação escolar", "alimentacao escolar", "merenda", "catering",
    "vigilância armada", "vigilancia armada",
    "vigilância desarmada", "vigilancia desarmada",
    "segurança patrimonial", "seguranca patrimonial",
    "material de escritório", "material de escritorio",
    "combustível", "abastecimento de combustivel", "recarga de toner", "cartuchos",
    "locação de veículos", "locacao de veiculos",
    "serviço de copa", "servico de copa",
    "jardinagem", "paisagismo ornamental",
    "coleta de lixo", "coleta de residuos solidos",
    "transporte escolar",
    "fornecimento de refeição", "fornecimento de refeicao",
    "fornecimento de refeições", "fornecimento de refeicoes",
    "quentinha", "marmitex",
    "uniforme", "fardamento",
    "material de limpeza",
    "detergente", "desinfetante", "papel higiênico", "papel higienico",
    "papel toalha",
    "ar condicionado", "aparelho de ar condicionado",
    "mobiliário", "mobiliario", "móveis", "moveis",
    "equipamento de informática", "equipamento de informatica",
    "computador", "notebook", "impressora",
    "medicamento", "material hospitalar", "material médico", "material medico",
    "ambulância", "ambulancia",
    "serviço funerário", "servico funerario",
    "seguro de vida", "plano de saúde", "plano de saude",
    # Odontologia/saúde
    "material odontológico", "material odontologico",
    "odontológico", "odontologico",
    "cadeira odontológica", "cadeira odontologica",
    # Gases
    "gás argônio", "gas argonio",
    "argônio", "argonio",
    "gás medicinal", "gas medicinal",
    "gases medicinais", "gases industriais",
    # Hospitalar expandido
    "material médico-hospitalar", "material medico-hospitalar",
    "insumo hospitalar", "equipamento hospitalar",
    "equipamento médico", "equipamento medico",
    "órtese", "ortese", "prótese", "protese",
})

# Map from sector_key prefix → hard exclusion set
_HARD_EXCLUSIONS_BY_SECTOR: dict[str, frozenset[str]] = {
    "engenharia": HARD_EXCLUSIONS_ENGENHARIA,
    "engenharia_civil": HARD_EXCLUSIONS_ENGENHARIA,
    "engenharia_rodoviaria": HARD_EXCLUSIONS_ENGENHARIA,
    "arquitetura": HARD_EXCLUSIONS_ENGENHARIA,
}

# Minimum keyword density required (Gate 2): fraction of words in objeto
# that must match sector keywords for the edital to pass.
_DENSITY_GATE_MIN_PCT = 0.02  # 2%


def _check_hard_exclusions(objeto_lower: str, sector_key: str = "") -> str | None:
    """Gate 1: Return the matched exclusion term if objeto contains a hard exclusion, else None.

    objeto_lower is expected to be already accent-stripped (via _strip_accents).
    We also normalize each exclusion term so accented variants match correctly.
    """
    exclusions = _HARD_EXCLUSIONS_BY_SECTOR.get(sector_key, frozenset())
    if not exclusions:
        # Try prefix match (e.g. sector_key="engenharia_ambiental" → base "engenharia")
        base = sector_key.split("_")[0] if sector_key else ""
        exclusions = _HARD_EXCLUSIONS_BY_SECTOR.get(base, frozenset())
    for term in exclusions:
        normalized_term = _strip_accents(term)
        if normalized_term in objeto_lower:
            return term
    return None


def _compute_keyword_density(objeto_lower: str, keyword_patterns: list[re.Pattern]) -> float:
    """Gate 2: Compute fraction of object words matched by keyword patterns."""
    words = objeto_lower.split()
    if not words:
        return 0.0
    matched = sum(1 for w in words if any(p.search(w) for p in keyword_patterns))
    return matched / len(words)


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


def _search_pncp_single(
    api: ApiClient,
    keywords: list[str],
    modalidades: dict[int, str] | set[int],
    ufs: list[str],
    dias: int,
    keyword_patterns: list[re.Pattern] | None = None,
    label_prefix: str = "",
    nature_profile: dict[str, float] | None = None,
    cluster_nature: str | None = None,
    cluster_nature_profile: dict[str, float] | None = None,
    sector_key: str = "",
) -> tuple[list[dict], dict]:
    """Core PNCP search loop for a set of keywords and modalidades.

    Returns (editais, source_meta_dict). Used by both collect_pncp() and
    collect_pncp_multi_cluster() to avoid duplicating HTTP call logic.
    """
    data_inicial = _date_compact(_today() - timedelta(days=dias))
    data_final = _date_compact(_today())

    if keyword_patterns is None:
        keyword_patterns = _compile_keyword_patterns(keywords)

    # Normalize modalidades to {code: name} dict
    if isinstance(modalidades, set):
        mod_dict = {code: MODALIDADES.get(code, f"Mod {code}") for code in sorted(modalidades)}
    else:
        mod_dict = modalidades

    all_editais: list[dict] = []
    seen_ids: set[str] = set()
    source_meta = {"total_raw": 0, "total_filtered": 0, "pages_fetched": 0, "errors": 0}

    # FIX-1: When 1-5 UFs, iterate per-UF with server-side uf param for focused results
    use_per_uf = 1 <= len(ufs) <= 5
    uf_iterations: list[str | None] = [uf for uf in ufs] if use_per_uf else [None]
    max_pages = PNCP_MAX_PAGES_UF if use_per_uf else PNCP_MAX_PAGES

    for mod_code, mod_name in mod_dict.items():
        if label_prefix:
            print(f"    {label_prefix} Modalidade {mod_code} ({mod_name}):")
        else:
            print(f"\n  Modalidade {mod_code} ({mod_name}):")

        for uf_filter in uf_iterations:
            if uf_filter:
                print(f"      UF {uf_filter}:")

            items = []  # Initialize for pagination exhaustion check after loop
            for page in range(1, max_pages + 1):
                params = {
                    "dataInicial": data_inicial,
                    "dataFinal": data_final,
                    "codigoModalidadeContratacao": mod_code,
                    "pagina": page,
                    "tamanhoPagina": PNCP_MAX_PAGE_SIZE,
                }
                if uf_filter:
                    params["uf"] = uf_filter

                uf_label = f" uf={uf_filter}" if uf_filter else ""
                data, status = api.get(
                    f"{PNCP_BASE}/contratacoes/publicacao",
                    params=params,
                    label=f"PNCP mod={mod_code}{uf_label} p={page}",
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
                    edital = _parse_pncp_item(item, keywords, ufs, keyword_patterns=keyword_patterns,
                                             nature_profile=nature_profile, cluster_nature=cluster_nature,
                                             cluster_nature_profile=cluster_nature_profile,
                                             sector_key=sector_key)
                    if edital:
                        eid = edital.get("_id", "")
                        if eid and eid not in seen_ids:
                            seen_ids.add(eid)
                            all_editais.append(edital)

                # If fewer results than page size, we have reached the end
                if len(items) < PNCP_MAX_PAGE_SIZE:
                    break

                time.sleep(0.5)  # Rate limiting

            # After the page loop for this uf_filter, check if we hit the page cap
            if page == max_pages and isinstance(items, list) and len(items) == PNCP_MAX_PAGE_SIZE:
                uf_label_warn = f" UF={uf_filter}" if uf_filter else ""
                print(f"    ⚠ PAGINAÇÃO EXAUSTIVA: Modalidade {mod_code}{uf_label_warn} atingiu "
                      f"{max_pages} páginas ({max_pages * PNCP_MAX_PAGE_SIZE} items) — "
                      f"podem existir editais não capturados. Considerar --dias menor ou UF mais específica.")
                source_meta.setdefault("pagination_warnings", []).append(
                    f"mod={mod_code}{uf_label_warn}: {max_pages} pages exhausted"
                )

    source_meta["total_filtered"] = len(all_editais)
    return all_editais, source_meta


def collect_pncp(
    api: ApiClient,
    keywords: list[str],
    ufs: list[str],
    dias: int = 30,
    nature_profile: dict[str, float] | None = None,
    sector_key: str = "",
) -> tuple[list[dict], dict]:
    """Search PNCP for open editais (single-sector, backward compatible)."""
    print(f"\n\U0001f50d Phase 2a-1: PNCP \u2014 Varredura de editais ({dias} dias)")

    # Skip non-competitive modalidades (Dispensa, Inexigibilidade, Inaplicabilidade)
    modalidades_scan = {k: v for k, v in MODALIDADES.items() if k not in MODALIDADES_EXCLUIDAS}
    all_editais, source_meta = _search_pncp_single(
        api, keywords, modalidades_scan, ufs, dias,
        nature_profile=nature_profile,
        sector_key=sector_key,
    )

    _source = _source_tag("API" if source_meta["errors"] == 0 else "API_PARTIAL",
                          f"{source_meta['total_raw']} obtidos, {source_meta['total_filtered']} relevantes, "
                          f"{source_meta['pages_fetched']} p\u00e1ginas consultadas")

    print(f"\n  PNCP: {source_meta['total_raw']} raw \u2192 {source_meta['total_filtered']} filtrados")
    return all_editais, _source


def _fetch_pncp_pages_cached(
    api: ApiClient,
    mod_code: int,
    data_inicial: str,
    data_final: str,
    raw_cache: dict[tuple[int, int, str], list[dict] | None],
    uf_filter: str | None = None,
) -> tuple[list[dict], int, int, bool]:
    """Fetch all pages for a single modalidade (optionally per-UF), using raw_cache.

    Cache key is (mod_code, page, uf_filter or "ALL"). When uf_filter is set,
    the PNCP API filters server-side by UF and we allow more pages (PNCP_MAX_PAGES_UF).
    PNCP doesn't filter by keyword server-side, so results for the same
    (mod, page, uf) are identical regardless of which cluster requests them.

    Returns (all_items, pages_fetched, errors, pagination_exhausted).
    A cached entry of None means the page was previously fetched and returned no/error data
    (sentinel to avoid re-fetching).
    """
    all_items: list[dict] = []
    pages_fetched = 0
    errors = 0
    max_pages = PNCP_MAX_PAGES_UF if uf_filter else PNCP_MAX_PAGES

    for page in range(1, max_pages + 1):
        cache_key = (mod_code, page, uf_filter or "ALL")

        if cache_key in raw_cache:
            cached = raw_cache[cache_key]
            if cached is None:
                # Genuinely empty — stop pagination
                break
            # F13: Distinguish error from empty — retry errors after 1 hour
            if isinstance(cached, dict) and cached.get("_status") == "error":
                cached_ts = cached.get("_ts", "")
                try:
                    age_s = (datetime.now(timezone.utc) - datetime.fromisoformat(cached_ts)).total_seconds()
                except (ValueError, TypeError):
                    age_s = 99999
                if age_s < 3600:
                    break  # Still within error TTL — don't retry
                # Expired error — fall through to retry
                del raw_cache[cache_key]
            else:
                all_items.extend(cached)
                # Reproduce early-termination: if cached page was partial, stop
                if len(cached) < PNCP_MAX_PAGE_SIZE:
                    break
                continue

        # Cache miss — call API
        params = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "codigoModalidadeContratacao": mod_code,
            "pagina": page,
            "tamanhoPagina": PNCP_MAX_PAGE_SIZE,
        }
        if uf_filter:
            params["uf"] = uf_filter
        uf_label = f" uf={uf_filter}" if uf_filter else ""
        data, status = api.get(
            f"{PNCP_BASE}/contratacoes/publicacao",
            params=params,
            label=f"PNCP mod={mod_code}{uf_label} p={page}",
        )
        if status != "API" or not data:
            errors += 1
            # F13: Mark as error (not empty) — will be retried after 1 hour
            raw_cache[cache_key] = {"_status": "error", "_ts": datetime.now(timezone.utc).isoformat()}
            break

        items = data if isinstance(data, list) else data.get("data", data.get("resultado", []))
        if not isinstance(items, list) or not items:
            raw_cache[cache_key] = None  # Genuinely empty
            break

        raw_cache[cache_key] = items
        pages_fetched += 1
        all_items.extend(items)

        if len(items) < PNCP_MAX_PAGE_SIZE:
            break

        time.sleep(0.5)  # Rate limiting

    pagination_exhausted = (page == max_pages and len(all_items) > 0 and
                            len(all_items) % PNCP_MAX_PAGE_SIZE == 0)
    return all_items, pages_fetched, errors, pagination_exhausted


def collect_pncp_multi_cluster(
    api: ApiClient,
    cluster_searches: list[dict],
    ufs: list[str],
    dias: int,
    nature_profile: dict[str, float] | None = None,
    sector_key: str = "",
) -> tuple[list[dict], dict]:
    """Search PNCP separately per activity cluster, then deduplicate.

    Uses a raw fetch cache: PNCP has no keyword parameter, so the same
    (modalidade, page) returns identical results regardless of cluster.
    We fetch each unique (mod, page) ONCE, then apply cluster-specific
    keyword + nature filtering locally.

    Results are tagged with _cluster_origin and _cluster_share_pct.
    Dedup: if same edital appears in multiple clusters, keep the one from higher-share cluster.
    """
    print(f"\n\U0001f50d Phase 2a-1: PNCP \u2014 Varredura multi-cluster ({dias} dias, {len(cluster_searches)} clusters)")

    data_inicial = _date_compact(_today() - timedelta(days=dias))
    data_final = _date_compact(_today())

    # --- Phase 1: Union all unique modalidades across all clusters ---
    all_mods: set[int] = set()
    for cs in cluster_searches:
        mods = cs["modalidades"]
        if isinstance(mods, dict):
            all_mods.update(mods.keys())
        else:
            all_mods.update(mods)
    all_mods -= MODALIDADES_EXCLUIDAS  # Defense in depth: never fetch non-competitive modalidades

    # --- Phase 2: Fetch each unique (mod, page, uf) ONCE ---
    # FIX-4: When 1-5 UFs, iterate per-UF with server-side uf param
    use_per_uf = 1 <= len(ufs) <= 5
    uf_iterations: list[str | None] = [uf for uf in ufs] if use_per_uf else [None]
    raw_cache: dict[tuple[int, int, str], list[dict] | None] = {}
    raw_by_mod: dict[int, list[dict]] = {}
    total_pages_fetched = 0
    total_errors = 0

    uf_desc = f", per-UF ({', '.join(ufs)})" if use_per_uf else ""
    print(f"\n  [CACHE] Fetching {len(all_mods)} unique modalidades (shared across {len(cluster_searches)} clusters{uf_desc})")

    for mod_code in sorted(all_mods):
        mod_name = MODALIDADES.get(mod_code, f"Mod {mod_code}")
        print(f"    Modalidade {mod_code} ({mod_name}):")
        mod_items: list[dict] = []
        for uf_filter in uf_iterations:
            if uf_filter:
                print(f"      UF {uf_filter}:")
            items, pf, errs, exhausted = _fetch_pncp_pages_cached(
                api, mod_code, data_inicial, data_final, raw_cache,
                uf_filter=uf_filter,
            )
            mod_items.extend(items)
            total_pages_fetched += pf
            total_errors += errs
            if exhausted:
                uf_label_warn = f" UF={uf_filter}" if uf_filter else ""
                print(f"    ⚠ PAGINAÇÃO: mod={mod_code}{uf_label_warn} atingiu limite de páginas")
        raw_by_mod[mod_code] = mod_items

    total_raw = sum(len(items) for items in raw_by_mod.values())
    cache_hits = sum(1 for k, v in raw_cache.items() if v is not None) - total_pages_fetched
    print(f"\n  [CACHE] Raw fetch complete: {total_raw} items across {len(all_mods)} modalidades, "
          f"{total_pages_fetched} API calls, {max(0, cache_hits)} cache hits saved")

    # --- Phase 3: For each cluster, filter raw items with cluster-specific keywords + nature ---
    all_results: list[dict] = []
    combined_meta = {"total_raw": total_raw, "total_filtered": 0, "pages_fetched": total_pages_fetched,
                     "errors": total_errors, "clusters": []}

    for cluster in cluster_searches:
        label = cluster["label"]
        share = cluster["share_pct"]
        kws = cluster["keywords"]
        mods = cluster["modalidades"]

        print(f"\n  [PNCP] Cluster '{label}' ({share:.0f}%) \u2014 {len(kws)} keywords, "
              f"modalidades {{{', '.join(str(m) for m in sorted(mods if isinstance(mods, set) else mods.keys()))}}}")

        cluster_key = cluster.get("category_key", "")
        cluster_nat = _CLUSTER_DEFAULT_NATURE.get(cluster_key)
        cluster_nat_profile = cluster.get("nature_profile")
        keyword_patterns = _compile_keyword_patterns(kws)

        # Normalize modalidades to set of codes
        if isinstance(mods, dict):
            mod_codes = set(mods.keys())
        else:
            mod_codes = set(mods)

        cluster_filtered = 0
        cluster_raw_seen = 0
        seen_ids: set[str] = set()

        try:
            for mod_code in sorted(mod_codes):
                for raw_item in raw_by_mod.get(mod_code, []):
                    cluster_raw_seen += 1
                    edital = _parse_pncp_item(
                        raw_item, kws, ufs,
                        keyword_patterns=keyword_patterns,
                        nature_profile=nature_profile,
                        cluster_nature=cluster_nat,
                        cluster_nature_profile=cluster_nat_profile,
                        sector_key=sector_key,
                    )
                    if edital:
                        eid = edital.get("_id", "")
                        if eid and eid not in seen_ids:
                            seen_ids.add(eid)
                            edital["_cluster_origin"] = label
                            edital["_cluster_share_pct"] = share
                            all_results.append(edital)
                            cluster_filtered += 1
        except Exception as exc:
            print(f"  [PNCP] ERRO no cluster '{label}': {exc} \u2014 continuando")
            combined_meta["errors"] += 1
            combined_meta["clusters"].append({
                "label": label, "share_pct": share,
                "raw": cluster_raw_seen, "filtered": cluster_filtered, "status": "FAILED",
            })
            continue

        combined_meta["total_filtered"] += cluster_filtered
        combined_meta["clusters"].append({
            "label": label, "share_pct": share,
            "raw": cluster_raw_seen, "filtered": cluster_filtered,
            "status": "OK",
        })

        print(f"  [PNCP] Cluster '{label}': {cluster_raw_seen} raw -> {cluster_filtered} filtrados")

    # Deduplicate: keep edital from highest-share cluster
    deduped: dict[str, dict] = {}  # key -> edital
    for ed in all_results:
        eid = ed.get("_id", "")
        if not eid:
            # Fallback dedup key from link
            eid = ed.get("link", "") or f"noid-{ed.get('objeto', '')[:50]}"
        if eid in deduped:
            existing = deduped[eid]
            if ed.get("_cluster_share_pct", 0) > existing.get("_cluster_share_pct", 0):
                deduped[eid] = ed
        else:
            deduped[eid] = ed

    deduped_list = list(deduped.values())
    n_dupes = len(all_results) - len(deduped_list)

    combined_meta["total_deduped"] = len(deduped_list)
    combined_meta["duplicates_removed"] = n_dupes

    _source = _source_tag(
        "API" if combined_meta["errors"] == 0 else "API_PARTIAL",
        f"{combined_meta['total_raw']} obtidos, {combined_meta['total_filtered']} pre-dedup, "
        f"{len(deduped_list)} apos dedup ({n_dupes} duplicatas removidas), "
        f"{combined_meta['pages_fetched']} paginas, {len(cluster_searches)} clusters (cached)",
    )

    print(f"\n  [PNCP] Multi-cluster: {combined_meta['total_raw']} raw -> "
          f"{combined_meta['total_filtered']} filtrados -> {len(deduped_list)} apos dedup "
          f"({n_dupes} duplicatas entre clusters)")

    return deduped_list, _source

def _parse_pncp_item(item: dict, keywords: list[str], ufs: list[str],
                     keyword_patterns: list[re.Pattern] | None = None,
                     nature_profile: dict[str, float] | None = None,
                     cluster_nature: str | None = None,
                     cluster_nature_profile: dict[str, float] | None = None,
                     sector_key: str = "") -> dict | None:
    """Parse a single PNCP result. Returns None if filtered out.

    PNCP response structure:
      - objetoCompra: string (may have Latin1 encoding issues)
      - orgaoEntidade: {cnpj, razaoSocial, poderId, esferaId}
      - unidadeOrgao: {ufSigla, ufNome, municipioNome, nomeUnidade, codigoIbge}
      - valorTotalEstimado: float
      - dataAberturaProposta, dataEncerramentoProposta: ISO datetime strings
      - anoCompra, sequencialCompra: for building PNCP link

    FIX 2: Applies 3-gate filter before keyword matching:
      Gate 1 - Hard exclusions (sector-specific blocklist)
      Gate 2 - Keyword density threshold (>=2% of words)
      Gate 3 - CNAE compatibility warning (non-blocking)
    """
    objeto = (item.get("objetoCompra") or item.get("objeto") or "").strip()

    # UF is inside unidadeOrgao, not at top level
    unidade = item.get("unidadeOrgao") or {}
    orgao_entity = item.get("orgaoEntidade") or {}
    uf = (unidade.get("ufSigla") or item.get("ufSigla") or "").upper()

    # UF filter
    if ufs and uf and uf not in ufs:
        return None

    objeto_lower = _strip_accents(objeto.lower())

    # FIX 2 — Gate 1: Hard exclusions (reject immediately if objeto matches blocklist)
    exclusion_hit = _check_hard_exclusions(objeto_lower, sector_key)
    if exclusion_hit:
        if os.environ.get("REPORT_DEBUG"):
            print(f"    [GATE1-EXCL] sector={sector_key} excl='{exclusion_hit}': {objeto[:80]}")
        return None

    # Keyword filter: word-boundary matching (not substring)
    # Uses pre-compiled regex patterns for performance.
    # Requires at least 1 keyword match with word boundaries to pass.
    if keyword_patterns:
        if not any(p.search(objeto_lower) for p in keyword_patterns):
            return None
    elif not any(kw.lower() in objeto_lower for kw in keywords):
        # Fallback to substring for backward compat if no patterns provided
        return None

    # FIX 2 — Gate 2: Keyword density threshold (>=2%)
    # Only apply when we have compiled patterns (not fallback mode)
    filter_gate = "passed"
    rejection_reason = None
    if keyword_patterns:
        density = _compute_keyword_density(objeto_lower, keyword_patterns)
        if density < _DENSITY_GATE_MIN_PCT:
            if os.environ.get("REPORT_DEBUG"):
                print(f"    [GATE2-DENSITY] density={density:.3f}<{_DENSITY_GATE_MIN_PCT}: {objeto[:80]}")
            return None
    else:
        density = 0.0

    # Nature filter — two-level: cluster-specific then global
    edital_nature = classify_object_nature(objeto)

    # Level 1: Cluster-specific nature gate (strongest signal)
    if cluster_nature and edital_nature not in ("INDEFINIDO",) and edital_nature != cluster_nature:
        # Allow through if this nature has meaningful presence (>=10%) in cluster history
        if cluster_nature_profile and cluster_nature_profile.get(edital_nature, 0) >= 10:
            pass  # Mixed cluster — tolerate secondary natures
        else:
            if os.environ.get("REPORT_DEBUG"):
                obj_short = (objeto or "")[:80]
                print(f"    [NATURE-REJECT] cluster={cluster_nature} vs edital={edital_nature}: {obj_short}")
            return None

    # Level 2: Global profile compatibility (fallback for non-cluster searches)
    if not cluster_nature and nature_profile and not is_nature_compatible(edital_nature, nature_profile):
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

    # F04: Parse dates with flexible format fallback
    data_abertura = _parse_date_flexible(item.get("dataAberturaProposta") or item.get("dataPublicacaoPncp")) or ""
    data_encerramento = _parse_date_flexible(item.get("dataEncerramentoProposta")) or ""

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

    # F05: Unique ID from structural fields (never free text)
    cnpj_clean = re.sub(r"[^0-9]", "", str(cnpj_compra)) if cnpj_compra else ""
    _id = f"PNCP-{cnpj_clean}-{ano}-{seq}" if (cnpj_clean and ano and seq) else f"PNCP-{uuid.uuid4().hex[:12]}"

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
        "status_edital": (
            "ENCERRADO" if (dias_restantes is not None and dias_restantes < 0)
            else "ABERTO" if (dias_restantes is not None and dias_restantes >= 0)
            else "PRAZO_INDEFINIDO"
        ),
        "_nature": edital_nature,
        # FIX 2: 3-gate filter metadata
        "filter_gate_passed": True,
        "rejection_reason": None,
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
        "valor_estimado": None,  # PCP v2 does not provide estimated values (F02/F12)
        "_valor_source": "PCP_SEM_VALOR",
        "modalidade": modalidade,
        "data_abertura": data_abertura,
        "data_encerramento": data_encerramento,
        "dias_restantes": dias_restantes,
        "fonte": "PCP",
        "link": link,
        "status_edital": (
            "ENCERRADO" if (dias_restantes is not None and dias_restantes < 0)
            else "ABERTO" if (dias_restantes is not None and dias_restantes >= 0)
            else "PRAZO_INDEFINIDO"
        ),
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
        # F14: Separate query per UF (QD API only accepts one state_code at a time)
        if ufs:
            all_gazettes: list[dict] = []
            for uf in ufs[:3]:
                params_uf = dict(params)
                params_uf["state_code"] = uf.upper()
                data, status = api.get(
                    QD_BASE,
                    params=params_uf,
                    label=f"Querido Diário: {q[:30]} UF={uf}",
                )
                if data and isinstance(data, dict):
                    all_gazettes.extend(data.get("gazettes", []))
                time.sleep(0.5)
            gazettes = all_gazettes
        else:
            data, status = api.get(
                QD_BASE,
                params=params,
                label=f"Querido Diário: {q[:40]}",
            )
            gazettes = data.get("gazettes", data) if isinstance(data, dict) and status == "API" else []
            if not isinstance(gazettes, list):
                gazettes = []

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
# DISTANCE CALCULATION (OSRM) — with persistent cache + Table API
# ============================================================

# --- Persistent JSON cache helpers ---

def _load_json_cache(path: str) -> dict:
    """Load a JSON cache file. Returns empty dict if missing/corrupt."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_json_cache(path: str, data: dict) -> None:
    """Save data to a JSON cache file atomically."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


# --- Geocode with persistent disk cache ---

_geocode_mem: dict[tuple[str, str], tuple[float, float] | None] = {}
_geocode_disk: dict | None = None  # lazy-loaded

# --- Competitive intel cache (7-day TTL) ---
_competitive_cache: dict = {}
_competitive_cache_lock = threading.Lock()

# --- Docs cache (permanent — immutable once published) ---
_docs_cache: dict = {}
_docs_cache_lock = threading.Lock()


def _geocode_disk_load() -> dict:
    global _geocode_disk
    if _geocode_disk is None:
        _geocode_disk = _load_json_cache(GEOCODE_CACHE_FILE)
    return _geocode_disk


def _geocode_disk_save() -> None:
    if _geocode_disk is not None:
        _save_json_cache(GEOCODE_CACHE_FILE, _geocode_disk)


# --- Competitive intel cache helpers ---

def _load_competitive_cache() -> None:
    """Load competitive intel cache from disk, discarding entries older than TTL."""
    global _competitive_cache
    with _competitive_cache_lock:
        try:
            raw = _load_json_cache(COMPETITIVE_CACHE_FILE)
            now = datetime.now(timezone.utc)
            fresh: dict = {}
            for k, v in raw.items():
                cached_at = v.get("_cached_at", "2000-01-01")
                try:
                    age = (now - datetime.fromisoformat(cached_at)).days
                except (ValueError, TypeError):
                    age = 999
                if age < COMPETITIVE_CACHE_TTL_DAYS:
                    fresh[k] = v
            _competitive_cache = fresh
            if fresh:
                print(f"  ✓ Competitive cache: {len(fresh)} órgãos carregados do disco")
        except Exception:
            _competitive_cache = {}


def _save_competitive_cache() -> None:
    """Persist competitive intel cache to disk."""
    with _competitive_cache_lock:
        _save_json_cache(COMPETITIVE_CACHE_FILE, _competitive_cache)


# --- Docs cache helpers ---

def _load_docs_cache() -> None:
    """Load docs cache from disk (permanent — no TTL)."""
    global _docs_cache
    with _docs_cache_lock:
        try:
            _docs_cache = _load_json_cache(DOCS_CACHE_FILE)
            if _docs_cache:
                print(f"  ✓ Docs cache: {len(_docs_cache)} editais carregados do disco")
        except Exception:
            _docs_cache = {}


def _save_docs_cache() -> None:
    """Persist docs cache to disk."""
    with _docs_cache_lock:
        _save_json_cache(DOCS_CACHE_FILE, _docs_cache)


def _geocode(api: ApiClient, cidade: str, uf: str) -> tuple[float, float] | None:
    """Geocode a city.

    Lookup priority:
      1. Memory cache (fastest, in-process)
      2. Static JSON (data/municipios_coords.json -- no API call, no sleep)
      3. Persistent disk cache (data/geocode_cache.json -- previous Nominatim results)
      4. Nominatim API (rate-limited: 1 req/s, last resort)
    """
    if not cidade or not uf:
        return None

    uf_upper = uf.strip().upper()
    key = (cidade.strip().lower(), uf_upper)

    # 1. Memory cache
    if key in _geocode_mem:
        return _geocode_mem[key]

    # 2. Static JSON lookup (covers all ~5571 IBGE municipalities -- no API call)
    _load_municipios_coords()
    if _MUNICIPIOS_COORDS:
        static_key = f"{_strip_accents(cidade).upper().strip()}/{uf_upper}"
        entry = _MUNICIPIOS_COORDS.get("by_name", {}).get(static_key)
        if entry:
            result: tuple[float, float] | None = (entry["lat"], entry["lon"])
            _geocode_mem[key] = result
            print(f"  Geocode: {cidade}/{uf_upper} (static)")
            return result

    # 3. Persistent disk cache (results from previous Nominatim calls)
    disk = _geocode_disk_load()
    disk_key = f"{key[0]}|{key[1]}"
    if disk_key in disk:
        val = disk[disk_key]
        result = (val[0], val[1]) if val is not None else None
        _geocode_mem[key] = result
        return result

    # 4. Nominatim API (rate-limited: 1 req/s)
    time.sleep(1.1)
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
        result = float(data[0]["lat"]), float(data[0]["lon"])
        _geocode_mem[key] = result
        disk[disk_key] = [result[0], result[1]]
        return result

    # Retry once on failure
    if status == "API_FAILED":
        time.sleep(2.0)
        data, status = api.get(
            NOMINATIM_BASE,
            params={
                "q": f"{cidade}, {uf}, Brasil",
                "format": "json",
                "limit": 1,
                "countrycodes": "br",
            },
            headers={"User-Agent": "SmartLic-ReportCollector/1.0 (report@smartlic.tech)"},
            label=f"Geocode retry: {cidade}/{uf}",
        )
        if status == "API" and data and isinstance(data, list) and len(data) > 0:
            result = float(data[0]["lat"]), float(data[0]["lon"])
            _geocode_mem[key] = result
            disk[disk_key] = [result[0], result[1]]
            return result

    _geocode_mem[key] = None
    disk[disk_key] = None
    return None

def _calculate_distances_table(
    api: ApiClient,
    origin: tuple[float, float],
    destinations: dict[str, tuple[float, float]],
) -> dict[str, dict]:
    """Calculate distances from origin to all destinations using OSRM Table API.

    Returns dict[destination_key, {km, duracao_horas, _source}].
    Falls back to serial /route calls if Table API fails.
    """
    results: dict[str, dict] = {}
    dest_items = list(destinations.items())

    for batch_start in range(0, len(dest_items), OSRM_TABLE_BATCH_SIZE):
        batch = dest_items[batch_start:batch_start + OSRM_TABLE_BATCH_SIZE]

        # Build coords: origin (index 0) + destinations — OSRM expects lon,lat
        parts = [f"{origin[1]},{origin[0]}"]
        for _key, (lat, lon) in batch:
            parts.append(f"{lon},{lat}")

        coords_str = ";".join(parts)
        data, status = api.get(
            f"{OSRM_TABLE_BASE}/{coords_str}",
            params={"sources": "0", "annotations": "distance,duration"},
            label=f"OSRM Table batch ({len(batch)} destinos)",
        )

        if status == "API" and data and data.get("distances") and data.get("durations"):
            dists_row = data["distances"][0]
            durs_row = data["durations"][0]

            for i, (dest_key, _) in enumerate(batch):
                idx = i + 1  # index 0 is the origin itself
                d = dists_row[idx] if idx < len(dists_row) else None
                t = durs_row[idx] if idx < len(durs_row) else None
                if d is not None and t is not None:
                    results[dest_key] = {
                        "km": round(d / 1000, 1),
                        "duracao_horas": round(t / 3600, 1),
                        "_source": _source_tag("CALCULATED", "OSRM Table API"),
                    }
                else:
                    results[dest_key] = {
                        "km": None,
                        "duracao_horas": None,
                        "_source": _source_tag("API_FAILED", "OSRM Table null route"),
                    }
        else:
            # Table API failed for this batch — fall back to serial /route
            print(f"  ⚠ OSRM Table falhou — fallback serial para {len(batch)} destinos")
            for dest_key, (lat, lon) in batch:
                coords = f"{origin[1]},{origin[0]};{lon},{lat}"
                rdata, rstatus = api.get(
                    f"{OSRM_BASE}/{coords}",
                    params={"overview": "false"},
                    label=f"OSRM: →{dest_key}",
                )
                if rstatus == "API" and rdata and rdata.get("routes"):
                    route = rdata["routes"][0]
                    results[dest_key] = {
                        "km": round(route["distance"] / 1000, 1),
                        "duracao_horas": round(route["duration"] / 3600, 1),
                        "_source": _source_tag("CALCULATED", "OSRM route fallback"),
                    }
                else:
                    results[dest_key] = {
                        "km": None,
                        "duracao_horas": None,
                        "_source": _source_tag("API_FAILED", "OSRM routing falhou"),
                    }

    return results


# --- Legacy serial function (kept for backward compat) ---

def calculate_distance(
    api: ApiClient,
    cidade_sede: str,
    uf_sede: str,
    cidade_destino: str,
    uf_destino: str,
) -> dict:
    """Calculate driving distance between two cities using OSRM (serial, legacy)."""
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
    """Validate PNCP links with HEAD requests. Mutates editais in place — parallel (F29)."""
    print(f"\n🔗 Validando links PNCP ({len(editais)} editais)")

    _fail_count = [0]
    _total_count = [0]
    _counter_lock = threading.Lock()

    def _validate_single(ed: dict) -> None:
        link = ed.get("link", "")
        if not link or "pncp.gov.br" not in link:
            ed["link_valid"] = None
            return
        with _counter_lock:
            _total_count[0] += 1
        status_code = api.head(link, label=f"HEAD {link[-40:]}")
        ed["link_valid"] = status_code == 200 if status_code else None
        if not status_code or status_code != 200:
            with _counter_lock:
                _fail_count[0] += 1
            if status_code and status_code != 200:
                with api._print_lock:
                    print(f"  ⚠ Link HTTP {status_code}: {link}")

    # F29: parallel with ThreadPoolExecutor(max_workers=10)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(_validate_single, editais))

    # F29: If >50% fail, mark all as unvalidated
    if _total_count[0] > 0 and _fail_count[0] > _total_count[0] * 0.5:
        for ed in editais:
            ed["links_unvalidated"] = True
        print(f"  ⚠ >50% links falharam ({_fail_count[0]}/{_total_count[0]}) — marcando como não validados")


# ============================================================
# PNCP DOCUMENT LISTING
# ============================================================

def collect_pncp_documents(api: ApiClient, editais: list[dict]) -> None:
    """List available documents for each PNCP edital. Mutates editais in place — parallel.

    Document listings are immutable once published — results are cached permanently.
    Capped to Top 50 editais by valor_estimado to limit API calls.
    """
    # Cap to Top 50 by valor_estimado — mark excluded editais immediately
    DOCS_TOP_N = 50
    pncp_editais = [ed for ed in editais if ed.get("fonte") == "PNCP"]
    pncp_sorted = sorted(pncp_editais, key=lambda e: _safe_float(e.get("valor_estimado")) or 0.0, reverse=True)
    top_pncp_ids = {id(ed) for ed in pncp_sorted[:DOCS_TOP_N]}

    for ed in editais:
        if ed.get("fonte") == "PNCP" and id(ed) not in top_pncp_ids:
            ed["documentos"] = []
            ed["documentos_source"] = _source_tag("UNAVAILABLE", "Edital fora do Top 50 por valor estimado")

    n_excluded = len(pncp_editais) - min(len(pncp_editais), DOCS_TOP_N)
    print(f"\n📄 Phase 2b: Listando documentos PNCP ({len(editais)} editais, top {DOCS_TOP_N} por valor, {n_excluded} excluídos)")
    _counter_lock = threading.Lock()
    counters = {"cached": 0, "fetched": 0}

    def _fetch_docs_single(ed: dict) -> None:
        if ed.get("fonte") != "PNCP":
            ed["documentos"] = []
            ed["documentos_source"] = _source_tag("UNAVAILABLE", "Apenas PNCP tem API de documentos")
            return
        # Skip editais outside Top 50 (already marked above)
        if id(ed) not in top_pncp_ids:
            return

        cnpj_orgao = ed.get("cnpj_orgao", "")
        ano = ed.get("ano_compra", "")
        seq = ed.get("sequencial_compra", "")

        if not (cnpj_orgao and ano and seq):
            ed["documentos"] = []
            ed["documentos_source"] = _source_tag("UNAVAILABLE", "Dados insuficientes para buscar docs")
            return

        cache_key = f"{cnpj_orgao}/{ano}/{seq}"

        # Check cache first (document listings are immutable)
        with _docs_cache_lock:
            cached = _docs_cache.get(cache_key)

        if cached is not None:
            ed["documentos"] = cached
            ed["documentos_source"] = _source_tag("API", f"{len(cached)} documentos (cache)")
            with _counter_lock:
                counters["cached"] += 1
            return

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
            # Cache permanently (immutable)
            with _docs_cache_lock:
                _docs_cache[cache_key] = docs
            with _counter_lock:
                counters["fetched"] += 1
        else:
            ed["documentos"] = []
            ed["documentos_source"] = _source_tag("API_FAILED")
            # Do NOT cache failed responses

        time.sleep(0.05)

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pool:
        list(pool.map(_fetch_docs_single, editais))

    print(f"  Documentos: {counters['cached']} do cache, {counters['fetched']} da API")
    _save_docs_cache()


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
    Deduplicates by orgão CNPJ to avoid redundant API calls. Parallel across orgãos.
    Results cached with 7-day TTL (data changes slowly).
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

    # Cap to Top 15 organs by number of editais they serve (performance win)
    TOP_ORGANS_LIMIT = 15
    sorted_organs = sorted(orgao_map.items(), key=lambda kv: len(kv[1]), reverse=True)
    top_organs: dict[str, list[dict]] = dict(sorted_organs[:TOP_ORGANS_LIMIT])
    excluded_organs: dict[str, list[dict]] = dict(sorted_organs[TOP_ORGANS_LIMIT:])

    # Mark excluded organs immediately so they don't block processing
    for _exc_editais in excluded_organs.values():
        for ed in _exc_editais:
            ed["competitive_intel"] = []
            ed["competitive_intel_source"] = _source_tag(
                "UNAVAILABLE", "Órgão fora do Top 15 de inteligência competitiva"
            )

    # Replace orgao_map with capped version
    orgao_map = top_organs

    print(f"\n🏢 Inteligência competitiva — {len(orgao_map)} órgãos (top {TOP_ORGANS_LIMIT} de {len(sorted_organs)} únicos)")

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

    # Per-organ counters (thread-safe via list)
    _n_cached = [0]
    _n_fetched = [0]
    _counter_lock = threading.Lock()

    def _fetch_organ_intel(item: tuple) -> None:
        cnpj_orgao, orgao_editais = item
        orgao_nome = orgao_editais[0].get("orgao", cnpj_orgao)

        # Check cache first (7-day TTL)
        with _competitive_cache_lock:
            cached_entry = _competitive_cache.get(cnpj_orgao)

        if cached_entry is not None:
            contracts = cached_entry["contracts"]
            print(f"  → Competitiva: {orgao_nome[:40]}... ✓ (cache)")
            source = _source_tag("API", f"{len(contracts)} contratos (cache)")
            for ed in orgao_editais:
                ed["competitive_intel"] = contracts[:20]
                ed["competitive_intel_source"] = source
            with _counter_lock:
                _n_cached[0] += 1
            return

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
                    vl = _safe_float(c.get("valorGlobal") or c.get("valorInicial")) or 0.0
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
                time.sleep(0.1)

            # Stop if we already have enough data
            if len(contracts) >= 40:
                break
            time.sleep(0.1)

        # Store in cache (only on successful fetch -- do NOT cache API_FAILED)
        with _competitive_cache_lock:
            _competitive_cache[cnpj_orgao] = {
                "contracts": contracts,
                "_cached_at": datetime.now(timezone.utc).isoformat(),
            }

        with _counter_lock:
            _n_fetched[0] += 1

        # Assign to all editais of this orgão (raw + sector-filtered)
        source = _source_tag("API", f"{len(contracts)} contratos") if contracts else _source_tag("API", "0 contratos")
        for ed in orgao_editais:
            ed["competitive_intel"] = contracts[:20]  # Limit to 20 most recent
            ed["competitive_intel_source"] = source
            # Pre-filter by sector keywords for downstream analysis
            sector_key = ed.get("_sector_key", "")
            sector_kws = _SECTOR_COMPETITION_KEYWORDS.get(sector_key, []) if sector_key else []
            if sector_kws:
                ed["competitive_intel_filtered"] = [
                    c for c in contracts[:20]
                    if any(kw in (c.get("objeto", "") or "").lower() for kw in sector_kws)
                ]
            else:
                ed["competitive_intel_filtered"] = contracts[:20]
            # HARD-002: Audit trail for sector filtering
            ed["competitive_intel_stats"] = {
                "raw_count": len(contracts[:20]),
                "filtered_count": len(ed["competitive_intel_filtered"]),
                "filter_method": "SECTOR_KEYWORDS" if sector_kws and len(ed["competitive_intel_filtered"]) < len(contracts[:20]) else "UNFILTERED",
                "sector_key": sector_key,
            }

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(_fetch_organ_intel, orgao_map.items()))

    print(f"  Competitiva: {_n_cached[0]} do cache, {_n_fetched[0]} da API")
    _save_competitive_cache()

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
    # Fornecimento (supply) sectors — margins are higher than construction
    "fornecimento_saude": (0.15, 0.30),       # Hospital materials — commodity but regulated
    "fornecimento_limpeza": (0.15, 0.30),     # Cleaning products
    "fornecimento_papelaria": (0.15, 0.25),   # Office/school supplies
    "fornecimento_mobiliario": (0.15, 0.30),  # Furniture supply
    "fornecimento_alimentos": (0.05, 0.15),   # Food — low margin, high volume
    "fornecimento_geral": (0.12, 0.25),       # Generic materials
    "servicos_profissionais": (0.20, 0.40),   # Professional services (credenciamento)
    "servicos_gerais": (0.10, 0.25),          # General services
    "concessao": (0.10, 0.25),                # Concession
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
    # Fornecimento (supply): low qualification barriers, price-driven competition
    "fornecimento_saude": {"hab": 0.10, "fin": 0.25, "geo": 0.15, "prazo": 0.20, "comp": 0.30},
    "fornecimento_limpeza": {"hab": 0.10, "fin": 0.25, "geo": 0.15, "prazo": 0.20, "comp": 0.30},
    "fornecimento_papelaria": {"hab": 0.10, "fin": 0.25, "geo": 0.10, "prazo": 0.20, "comp": 0.35},
    "fornecimento_mobiliario": {"hab": 0.10, "fin": 0.25, "geo": 0.15, "prazo": 0.20, "comp": 0.30},
    "fornecimento_alimentos": {"hab": 0.15, "fin": 0.25, "geo": 0.20, "prazo": 0.20, "comp": 0.20},
    "fornecimento_geral": {"hab": 0.10, "fin": 0.25, "geo": 0.15, "prazo": 0.20, "comp": 0.30},
    "servicos_profissionais": {"hab": 0.35, "fin": 0.15, "geo": 0.15, "prazo": 0.15, "comp": 0.20},
    "servicos_gerais": {"hab": 0.20, "fin": 0.20, "geo": 0.20, "prazo": 0.20, "comp": 0.20},
    "concessao": {"hab": 0.20, "fin": 0.30, "geo": 0.25, "prazo": 0.15, "comp": 0.10},
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
    # Fornecimento (supply) sectors
    "fornecimento_saude": 0.08,      # ~12 bidders, commoditized hospital materials
    "fornecimento_limpeza": 0.08,    # ~12 bidders
    "fornecimento_papelaria": 0.06,  # ~15+ bidders, very commoditized
    "fornecimento_mobiliario": 0.10, # ~10 bidders
    "fornecimento_alimentos": 0.08,  # ~12 bidders
    "fornecimento_geral": 0.08,     # ~12 bidders
    "servicos_profissionais": 0.15, # ~7 professionals per credenciamento
    "servicos_gerais": 0.10,        # ~10 bidders
    "concessao": 0.15,              # ~7 bidders, barriers to entry
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
    # Fornecimento (supply) sectors
    "fornecimento_saude": ["hospitalar", "material hospitalar", "material médico", "insumo",
                            "descartável", "luva", "seringa", "gaze", "soro", "medicamento",
                            "ambulatorial", "equipamento médico", "enfermagem"],
    "fornecimento_limpeza": ["limpeza", "saneante", "produto de limpeza", "higienização",
                              "desinfetante", "detergente", "alvejante"],
    "fornecimento_papelaria": ["papel", "caneta", "toner", "cartucho", "material de escritório",
                                "material escolar", "expediente"],
    "fornecimento_mobiliario": ["móvel", "movel", "cadeira", "mesa", "armário", "estante",
                                 "eletrodoméstic", "eletrodomestic"],
    "fornecimento_alimentos": ["alimentação", "alimentacao", "gênero alimentício", "merenda",
                                "cesta básica", "hortifrúti"],
    "fornecimento_geral": ["fornecimento", "material", "aquisição", "registro de preços"],
    "servicos_profissionais": ["credenciamento", "serviço médico", "atendimento", "consulta",
                                "plantão", "profissional de saúde", "enfermeiro", "fisioterapia"],
    "servicos_gerais": ["serviço", "manutenção", "reparo", "conserto", "consultoria",
                         "assessoria", "treinamento", "evento"],
    "concessao": ["concessão", "cessão", "permissão", "exploração", "cantina", "restaurante"],
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
    valor = _safe_float(edital.get("valor_estimado")) or 0.0

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
            f"Município de {pop:,.0f} habitantes licitando {_fmt_brl(valor)} "
            f"— capacidade operacional e fiscal limitada"
        )
    elif 0 < pop < 20_000 and valor > 10_000_000:
        if risk_level != "ALTO":
            risk_level = "MEDIO"
        alertas.append(
            f"Município de {pop:,.0f} habitantes com edital de {_fmt_brl(valor)} "
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
    capital = _safe_float(empresa.get("capital_social")) or 0.0
    valor = _safe_float(edital.get("valor_estimado")) or 0.0

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

    # Gate 3: Capital < sector-specific % of contract value — insuficiente para habilitação econômico-financeira
    # Capital minimum: use sector-specific % (varies 5%-10%). 10% is the legal MAX (Lei 14.133, art. 69 §4).
    # The actual % is edital-specific — we use the sector default as approximation.
    sector_hab = _HABILITACAO_REQUIREMENTS.get(sector_key, _HABILITACAO_REQUIREMENTS.get("_default", {}))
    capital_min_pct = sector_hab.get("capital_minimo_pct", 0.10)
    if capital > 0 and valor > 0 and (capital / valor) < capital_min_pct:
        veto_gates.append(
            f"Capital social insuficiente: {_fmt_brl(capital)} = {capital/valor:.0%} do valor do edital "
            f"(estimativa usual do setor: {capital_min_pct:.0%}, verificar edital para % real)"
        )

    # Gate 4: REMOVED — R$81K is the MEI annual REVENUE ceiling (LC 128, art. 18-A §1),
    # NOT a procurement participation limit. A MEI can legally bid on contracts of any value.
    # The risk is that winning may push revenue above the ceiling, causing exit from MEI.
    # This is now handled as a WARNING in risk_score, not a veto.
    is_mei = empresa.get("mei") or empresa.get("opcao_pelo_mei")

    # Gate 5: REMOVED — R$4.8M is the Simples Nacional annual REVENUE ceiling (LC 123, art. 3, II),
    # NOT a procurement participation limit. A company can legally bid on contracts of any value.
    # The risk is that winning may push revenue above the ceiling, causing exit from Simples.
    # This is now handled as a WARNING in risk_score, not a veto.
    is_simples = empresa.get("simples_nacional") or empresa.get("opcao_pelo_simples")

    # Gate 6: REMOVED — Distance veto has no legal basis. Construction companies routinely
    # mobilize teams hundreds of km away. Distance already penalizes the geographic score.
    # Keeping as informational note in justificativa instead of veto.

    # Gate 7: REMOVED — No legal prohibition on any company size bidding long-term concessions.
    # This is a financial planning concern, not a legal barrier.
    # Long-term concessions already receive lower financial scores due to capacity ratio.

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
        # F08: Linear graduation instead of cliff at 0.3
        threshold_ratio = 0.3
        if ratio < threshold_ratio:
            hab_score = max(10, min(100, int(100 * ratio / threshold_ratio)))

    # ================================================================
    # FINANCEIRO (25%)
    # ================================================================
    if valor <= 0 or capital <= 0:
        fin_score = 50  # Unknown
    else:
        # Financial capacity approximation: capital x 5 (conservative multiplier accounting for
        # leverage, credit lines, and operational reserves). This is a heuristic, NOT an accounting metric.
        # Disclosed in methodology section as "estimativa heuristica de capacidade financeira".
        capacity = capital * 5  # Reduced from 10x to 5x for conservatism
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

    # F06: Single presencial multiplier (replaces double -15 fixed penalty)
    modalidade = (edital.get("modalidade") or "").lower()
    is_presencial = "presencial" in modalidade
    presencial_multiplier = 0.85 if is_presencial else 1.0

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

    # F06: Apply presencial multiplier ONCE after all decay/IBGE adjustments
    geo_score = int(geo_score * presencial_multiplier)
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

    # F07: Threshold gates — single min(caps) operation instead of sequential min()
    threshold_applied = None
    triggered_caps: list[int] = []
    if prazo_score <= 10:
        triggered_caps.append(20)
        threshold_applied = "prazo_critico"
    if fin_score <= 10:
        triggered_caps.append(25)
        threshold_applied = threshold_applied or "financeiro_critico"
    if hab_score <= 30:
        triggered_caps.append(30)
        threshold_applied = threshold_applied or "habilitacao_critica"
    if triggered_caps:
        total = min(total, min(triggered_caps))

    # Improvement D: Inexigibilidade penalty — reduces inflated PARTICIPAR count
    # Not a veto — just a 20-point penalty to reflect higher qualification barriers.
    if "inexigibilidade" in modalidade:
        total = max(0, total - 20)

    # ================================================================
    # HARD-003: 3-Tier Acervo Status (replaces binary acervo_confirmado)
    # CONFIRMADO: ≥2 contracts with ALTA similarity (prefix match or Jaccard≥0.50)
    # PARCIAL: 1 ALTA or ≥2 MÉDIA contracts (Jaccard 0.30-0.49)
    # NAO_VERIFICADO: insufficient data for inference
    # ================================================================
    acervo_status = "NAO_VERIFICADO"
    acervo_similares_alta = 0
    acervo_similares_media = 0
    acervo_detalhes: list[dict] = []

    historico_for_acervo = empresa.get("historico_contratos", [])
    if historico_for_acervo and sector_key:
        edital_tokens = _normalize_for_dedup(edital.get("objeto", ""))
        sector_prefixes = []
        _cat_def = _ACTIVITY_CATEGORIES.get(sector_key, {})
        if _cat_def:
            sector_prefixes = _cat_def.get("prefixes", [])

        for hc in historico_for_acervo:
            hc_obj = (hc.get("objeto") or "")
            if not hc_obj:
                continue
            hc_obj_lower = hc_obj.lower()

            # Check prefix match (high confidence)
            prefix_match = sector_prefixes and any(pfx in hc_obj_lower for pfx in sector_prefixes)

            # Jaccard similarity on normalized tokens
            hc_tokens = _normalize_for_dedup(hc_obj)
            sim = _jaccard_similarity(edital_tokens, hc_tokens)

            if prefix_match or sim >= 0.50:
                acervo_similares_alta += 1
                if len(acervo_detalhes) < 5:
                    acervo_detalhes.append({
                        "objeto": hc_obj[:120],
                        "similaridade": round(max(sim, 0.50 if prefix_match else sim), 2),
                        "match_type": "PREFIX" if prefix_match else "JACCARD",
                        "data": hc.get("data_inicio") or hc.get("data_assinatura") or "",
                    })
            elif sim >= 0.30:
                acervo_similares_media += 1

        # Determine status
        if acervo_similares_alta >= 2:
            acervo_status = "CONFIRMADO"
        elif acervo_similares_alta >= 1 or acervo_similares_media >= 2:
            acervo_status = "PARCIAL"
        # else: remains NAO_VERIFICADO

    # Backward compatibility: acervo_confirmado for existing code that reads it
    acervo_confirmado = acervo_status == "CONFIRMADO"

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
        "acervo_status": acervo_status,
        "acervo_similares_alta": acervo_similares_alta,
        "acervo_similares_media": acervo_similares_media,
        "acervo_detalhes": acervo_detalhes,
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
        # Always use sector-filtered contracts to avoid cross-sector noise
        filtered_intel = relevant if relevant else competitive_intel[:5]
        sector_filtered = len(relevant) > 0

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

    # F09: Force confidence="baixa" on unfiltered fallback + tag reason
    confidence_reason = None
    if not sector_filtered and n_contracts_raw > 0:
        confidence = "baixa"
        confidence_reason = "dados insuficientes no setor específico — análise usa base geral"

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

    # HARD-005: Expanded contextual multipliers for wider probability dispersion.
    # Target: ≥20pp spread between best and worst editais in a typical report.
    contextual_mult = 1.0
    multipliers_applied: list[str] = []

    # Timeline impact (amplified range)
    dias = edital.get("dias_restantes")
    if dias is not None:
        if dias < 7:
            contextual_mult *= 0.3   # <7 days: severe urgency
            multipliers_applied.append(f"prazo_critico(×0.3, {dias}d)")
        elif dias < 15:
            contextual_mult *= 0.6
            multipliers_applied.append(f"prazo_curto(×0.6, {dias}d)")
        elif dias > 30:
            contextual_mult *= 1.3   # Comfortable timeline
            multipliers_applied.append(f"prazo_confortavel(×1.3, {dias}d)")

    # Financial capacity impact (amplified range)
    capital = _safe_float(empresa.get("capital_social")) or 0.0
    valor = _safe_float(edital.get("valor_estimado")) or 0.0
    if capital > 0 and valor > 0:
        cap_ratio = valor / (capital * 5)
        if cap_ratio > 5:
            contextual_mult *= 0.3   # Extreme stretch
            multipliers_applied.append(f"capacidade_extrema(×0.3, ratio={cap_ratio:.1f})")
        elif cap_ratio > 2:
            contextual_mult *= 0.6   # Significant stretch
            multipliers_applied.append(f"capacidade_alta(×0.6, ratio={cap_ratio:.1f})")
        elif cap_ratio < 0.3:
            contextual_mult *= 1.3   # Very comfortable
            multipliers_applied.append(f"capacidade_folgada(×1.3, ratio={cap_ratio:.1f})")
        elif cap_ratio < 0.5:
            contextual_mult *= 1.15  # Comfortable
            multipliers_applied.append(f"capacidade_ok(×1.15, ratio={cap_ratio:.1f})")

        # HARD-005: Value adequacy sweet spot
        raw_ratio = valor / capital if capital > 0 else 999
        if 0.5 <= raw_ratio <= 3.0:
            contextual_mult *= 1.2   # Sweet spot
            multipliers_applied.append(f"valor_ideal(×1.2, v/c={raw_ratio:.1f})")
        elif raw_ratio > 10:
            contextual_mult *= 0.4   # Way over capacity
            multipliers_applied.append(f"valor_excessivo(×0.4, v/c={raw_ratio:.1f})")

    # Distance impact (applies to ALL modalities, amplified for presencial)
    dist = edital.get("distancia", {})
    km = dist.get("km") if isinstance(dist, dict) else None
    if km is not None:
        if km < 50:
            contextual_mult *= 1.4    # Local advantage
            multipliers_applied.append(f"local(×1.4, {km:.0f}km)")
        elif km < 200:
            contextual_mult *= 1.1    # Regional proximity
            multipliers_applied.append(f"regional(×1.1, {km:.0f}km)")
        elif km > 500:
            contextual_mult *= 0.5    # Long distance penalty
            multipliers_applied.append(f"distante(×0.5, {km:.0f}km)")
        elif km > 300:
            contextual_mult *= 0.7    # Moderate distance penalty
            multipliers_applied.append(f"moderado(×0.7, {km:.0f}km)")
        # Extra penalty for presencial + distant
        if "presencial" in modalidade and km > 200:
            contextual_mult *= 0.8
            multipliers_applied.append(f"presencial_distante(×0.8, {km:.0f}km)")

    # HARD-005: Acervo bonus (uses edital-level acervo_status from HARD-003)
    # Check both edital-level field (from classify_acervo_similarity) and risk_score field
    acervo_status = edital.get("acervo_status") or (edital.get("risk_score") or {}).get("acervo_status", "NAO_VERIFICADO")
    if acervo_status == "CONFIRMADO":
        contextual_mult *= 1.3   # Proven technical portfolio
        multipliers_applied.append("acervo_confirmado(×1.3)")
    elif acervo_status == "PARCIAL":
        contextual_mult *= 1.1   # Partial match
        multipliers_applied.append("acervo_parcial(×1.1)")
    elif acervo_status == "NAO_VERIFICADO":
        contextual_mult *= 0.8   # Risk of disqualification
        multipliers_applied.append("acervo_nao_verificado(×0.8)")

    # Incumbency amplification (replace additive bonus with multiplicative)
    if incumbency_bonus > 0:
        contextual_mult *= 1.4   # Strong relationship signal
        multipliers_applied.append("incumbente(×1.4)")
        incumbency_bonus = 0.0   # Absorbed into contextual_mult (avoid double-counting)

    # Final probability with confidence band
    raw_prob = competition_prob * mod_mult + incumbency_bonus
    final_prob = raw_prob * viability_factor * contextual_mult
    final_prob = max(0.01, min(0.45, final_prob))  # Capped at 45% (no customer relationship data)

    # HARD-005: Confidence band: ±30% of point estimate
    prob_pct = round(final_prob * 100, 1)
    prob_min = max(1.0, prob_pct * 0.7)
    prob_max = min(60.0, prob_pct * 1.3)
    confidence_band = f"{prob_min:.0f}%-{prob_max:.0f}%"

    result = {
        "probability": round(final_prob, 3),
        "prob_min": round(prob_min, 1),
        "prob_max": round(prob_max, 1),
        "confidence_band": confidence_band,
        "probability_low": round(final_prob * 0.7, 3),
        "probability_high": min(0.60, round(final_prob * 1.3, 3)),
        "confidence": confidence,
        "base_rate": base_rate,
        "n_unique_suppliers": n_suppliers,
        "n_contracts_analyzed": n_contracts,
        "n_contracts_raw": n_contracts_raw,
        "sector_filtered": sector_filtered,
        "hhi": round(hhi, 4),
        "top_supplier_share": round(top_share, 3),
        "incumbency_bonus": round(incumbency_bonus, 3),
        "modality_multiplier": mod_mult,
        "viability_factor": round(viability_factor, 2),
        "contextual_multiplier": round(contextual_mult, 2),
        "multipliers_applied": multipliers_applied,
        "_source": _source_tag("CALCULATED", f"{n_contracts} contratos{'(filtrados)' if sector_filtered else ''}, {n_suppliers} fornecedores"),
    }
    # F09: Include confidence_reason when unfiltered fallback was used
    if confidence_reason:
        result["confidence_reason"] = confidence_reason
    return result


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
    # Fornecimento (supply) — low cost, mostly electronic, no site visits
    ("fornecimento_saude", "pregão eletrônico"): {"base": 800, "km_rate": 0, "value_pct": 0.002, "cap": 5000, "label": "fornec_saúde/pregão_eletrônico"},
    ("fornecimento_saude", "concorrência"): {"base": 1500, "km_rate": 0, "value_pct": 0.003, "cap": 8000, "label": "fornec_saúde/concorrência"},
    ("fornecimento_limpeza", "pregão eletrônico"): {"base": 500, "km_rate": 0, "value_pct": 0.002, "cap": 3000, "label": "fornec_limpeza/pregão_eletrônico"},
    ("fornecimento_papelaria", "pregão eletrônico"): {"base": 500, "km_rate": 0, "value_pct": 0.002, "cap": 3000, "label": "fornec_papelaria/pregão_eletrônico"},
    ("fornecimento_mobiliario", "pregão eletrônico"): {"base": 800, "km_rate": 0, "value_pct": 0.003, "cap": 5000, "label": "fornec_mobiliário/pregão_eletrônico"},
    ("fornecimento_alimentos", "pregão eletrônico"): {"base": 500, "km_rate": 0, "value_pct": 0.002, "cap": 3000, "label": "fornec_alimentos/pregão_eletrônico"},
    ("fornecimento_geral", "pregão eletrônico"): {"base": 600, "km_rate": 0, "value_pct": 0.002, "cap": 4000, "label": "fornec_geral/pregão_eletrônico"},
    ("fornecimento_geral", "concorrência"): {"base": 1000, "km_rate": 0, "value_pct": 0.003, "cap": 6000, "label": "fornec_geral/concorrência"},
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
    valor = _safe_float(edital.get("valor_estimado")) or 0.0
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
    # F11: Mark margin source as ESTIMATED when using fallback
    margin_is_fallback = sector_key not in _SECTOR_MARGINS
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
    # F42: Clamp fiscal risk discount to [0.0, 1.0]
    fiscal_discount = max(0.0, min(1.0, float(fiscal_risk.get("roi_discount", 1.0)))) if isinstance(fiscal_risk, dict) else 1.0

    # Dual ROI: roi_if_win (lucro se vencer) and roi_expected (esperança matemática)
    roi_if_win_min = round(valor * margin_min * fiscal_discount - participation_cost)
    roi_if_win_max = round(valor * margin_max * fiscal_discount - participation_cost)
    roi_expected_min = round(roi_if_win_min * probability)
    roi_expected_max = round(roi_if_win_max * probability)

    # Backward-compat: roi_min/roi_max now show if-win (not expected)
    roi_min = roi_if_win_min
    roi_max = roi_if_win_max

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
        "formula": f"(valor × margem{fiscal_note}) − custo de participação = ROI se vencer; × probabilidade = ROI esperado",
        "roi_if_win_min_calc": (
            f"({_fmt_brl(valor)} × {margin_min:.2f}"
            f"{f' × {fiscal_discount:.2f}' if fiscal_discount < 1.0 else ''}"
            f") − {_fmt_brl(participation_cost)} = {_fmt_brl(roi_if_win_min)}"
        ),
        "roi_if_win_max_calc": (
            f"({_fmt_brl(valor)} × {margin_max:.2f}"
            f"{f' × {fiscal_discount:.2f}' if fiscal_discount < 1.0 else ''}"
            f") − {_fmt_brl(participation_cost)} = {_fmt_brl(roi_if_win_max)}"
        ),
        "roi_expected_min_calc": f"{_fmt_brl(roi_if_win_min)} × {probability:.4f} = {_fmt_brl(roi_expected_min)}",
        "roi_expected_max_calc": f"{_fmt_brl(roi_if_win_max)} × {probability:.4f} = {_fmt_brl(roi_expected_max)}",
    }

    # Strategic classification based on dual ROI
    if roi_if_win_max > 0 and roi_expected_max < 0:
        strategic_classification = "INVESTIMENTO_ESTRATEGICO"
    elif roi_if_win_max > 0 and roi_expected_max > 0:
        strategic_classification = "OPORTUNIDADE"
    else:
        strategic_classification = "INVIAVEL"

    # F10: ROI reclassification gradient (not cliff at R$10k)
    strategic_reclassification = None
    reclassification_rationale = None
    acervo_weight = max(0.0, 1.0 - roi_max / 50000.0)
    has_acervo_potential = valor > 100_000
    if acervo_weight > 0.5 and has_acervo_potential:
        strategic_reclassification = "INVESTIMENTO_ESTRATEGICO_ACERVO"
        reclassification_rationale = (
            f"Retorno financeiro direto marginal ({_fmt_brl(roi_max)}) em contrato de "
            f"{_fmt_brl(valor)} — valor principal é acervo técnico e relacionamento institucional "
            f"(peso acervo: {acervo_weight:.0%})"
        )

    return {
        "roi_if_win_min": roi_if_win_min,
        "roi_if_win_max": roi_if_win_max,
        "roi_expected_min": roi_expected_min,
        "roi_expected_max": roi_expected_max,
        "roi_min": roi_min,  # Backward compat: now shows if-win, not expected
        "roi_max": roi_max,
        "probability": round(probability, 3),
        "margin_range": f"{margin_min * 100:.0f}%-{margin_max * 100:.0f}%",
        "margin_source": "ESTIMATED" if margin_is_fallback else "SECTOR_SPECIFIC",
        "confidence": win_prob.get("confidence", "baixa"),
        "strategic_classification": strategic_classification,
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
        val = _safe_float(c.get("valor", c.get("valorInicial", 0))) or 0.0
        total_contract_value += val
        if val > max_contract_value:
            max_contract_value = val
        obj = c.get("objeto", "")
        if obj:
            acervo_objetos.append(obj[:150])

    geo_spread = len(ufs_set)
    capital = _safe_float(empresa.get("capital_social")) or 0.0
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
# FIX 1: MULTI-DIMENSIONAL MATURITY SCORING
# ============================================================

# Target-sector keyword set used for Gate 3 CNAE check (market axis)
_ENGENHARIA_CNAE_CODES: frozenset[str] = frozenset({
    "4120", "4211", "4212", "4213", "4221", "4222", "4223", "4291", "4292", "4299",
    "4311", "4312", "4313", "4319", "4321", "4322", "4329", "4330", "4391", "4399",
    "7112", "7119",
})


def compute_maturity_score(empresa: dict, sector_key: str = "") -> dict:
    """4-axis maturity scoring replacing the legacy 3-level contract-count model.

    Axes:
      - Financial capacity  (35%): capital_social + porte
      - Government history  (25%): contract count from historico_contratos
      - Operational maturity(25%): company age from data_inicio_atividade
      - Market signals      (15%): CNAE specialization + QSA count + secondary CNAEs

    Returns:
        {
            "profile": "ENTRANTE" | "CRESCIMENTO" | "ESTABELECIDO" | "CONSOLIDADO",
            "score": 0-100,
            "breakdown": {"financeiro": X, "historico": Y, "operacional": Z, "mercado": W},
            "confidence": "LOW" | "MEDIUM" | "HIGH",
            "nota": "explanation string",
            # Legacy compat fields preserved from detect_maturity_profile():
            "total_contract_count": int,
            "esferas": dict,
            "geographic_spread": int,
            "max_contract_ratio": float,
            "total_contract_value": float,
            "acervo_objetos": list,
            "federal_contract_count": int,
            "_source": dict,
        }
    """
    historico = empresa.get("historico_contratos", [])
    historico_list = historico if isinstance(historico, list) else []
    total_count = len(historico_list)

    # --- Extract contract stats (also needed for legacy compat fields) ---
    ufs_set: set[str] = set()
    esferas: dict[str, int] = {}
    max_contract_value = 0.0
    total_contract_value = 0.0
    acervo_objetos: list[str] = []
    for c in historico_list:
        uf = c.get("uf", "")
        if uf:
            ufs_set.add(uf)
        esfera = c.get("esfera", "N/I")
        esferas[esfera] = esferas.get(esfera, 0) + 1
        val = _safe_float(c.get("valor", c.get("valorInicial", 0))) or 0.0
        total_contract_value += val
        if val > max_contract_value:
            max_contract_value = val
        obj = c.get("objeto", "")
        if obj:
            acervo_objetos.append(obj[:150])

    geo_spread = len(ufs_set)
    capital = _safe_float(empresa.get("capital_social")) or 0.0
    max_ratio = max_contract_value / capital if capital > 0 else 0.0

    # ─── AXIS 1: Financial capacity (35%) ───────────────────────────────────
    if capital <= 0:
        fin_raw = 5  # Unknown capital
    elif capital < 100_000:
        fin_raw = 10
    elif capital < 500_000:
        fin_raw = 40
    elif capital < 1_000_000:
        fin_raw = 60
    elif capital < 2_000_000:
        fin_raw = 75
    elif capital < 5_000_000:
        fin_raw = 85
    else:
        fin_raw = 100

    # Small boost for EPP/ME (shows formal registration maturity)
    porte = (empresa.get("porte") or "").upper()
    if "EPP" in porte or "MICRO" in porte or "MEI" in porte:
        fin_raw = min(fin_raw + 5, 100)

    fin_score = round(fin_raw * 0.35, 2)

    # ─── AXIS 2: Government history (25%) ───────────────────────────────────
    if total_count == 0:
        hist_raw = 0
    elif total_count <= 2:
        hist_raw = 30
    elif total_count <= 5:
        hist_raw = 60
    elif total_count <= 10:
        hist_raw = 80
    else:
        hist_raw = 100

    hist_score = round(hist_raw * 0.25, 2)

    # ─── AXIS 3: Operational maturity (25%) — age from data_inicio_atividade ─
    op_raw = 10  # Default: unknown age
    data_inicio_str = (empresa.get("data_inicio_atividade") or "").strip()
    if data_inicio_str:
        try:
            # Handles YYYY-MM-DD and DD/MM/YYYY
            if "/" in data_inicio_str:
                dt_parts = data_inicio_str.split("/")
                if len(dt_parts) == 3:
                    data_inicio = datetime(int(dt_parts[2]), int(dt_parts[1]), int(dt_parts[0]))
                else:
                    data_inicio = None
            else:
                data_inicio = datetime.strptime(data_inicio_str[:10], "%Y-%m-%d")

            if data_inicio:
                age_years = (_today().replace(tzinfo=None) - data_inicio).days / 365.25
                if age_years < 1:
                    op_raw = 10
                elif age_years < 3:
                    op_raw = 30
                elif age_years < 5:
                    op_raw = 50
                elif age_years < 10:
                    op_raw = 80
                else:
                    op_raw = 100
        except (ValueError, TypeError):
            op_raw = 10  # Parse failure → unknown

    op_score = round(op_raw * 0.25, 2)

    # ─── AXIS 4: Market signals (15%) ──────────────────────────────────────
    mkt_raw = 0

    # CNAE specialization: does primary CNAE match target sector?
    cnae_principal = str(empresa.get("cnae_principal") or "")
    cnae_code_4 = re.sub(r"[^0-9]", "", cnae_principal)[:4]
    target_cnaes = _ENGENHARIA_CNAE_CODES if ("engenharia" in sector_key or "arquitetura" in sector_key) else frozenset()
    if target_cnaes and cnae_code_4 in target_cnaes:
        mkt_raw += 50

    # QSA count (management depth)
    qsa = empresa.get("qsa") or []
    qsa_count = len(qsa) if isinstance(qsa, list) else 0
    if qsa_count > 3:
        mkt_raw += 25
    elif qsa_count > 1:
        mkt_raw += 15

    # Secondary CNAEs relevant to sector
    cnaes_sec_raw = empresa.get("cnaes_secundarios", "")
    if isinstance(cnaes_sec_raw, list):
        cnaes_sec_str = " ".join(str(c) for c in cnaes_sec_raw)
    else:
        cnaes_sec_str = str(cnaes_sec_raw or "")
    if target_cnaes:
        sec_codes = re.findall(r"\d{4}", cnaes_sec_str)
        if any(c in target_cnaes for c in sec_codes):
            mkt_raw += 10

    mkt_raw = min(mkt_raw, 100)
    mkt_score = round(mkt_raw * 0.15, 2)

    # ─── Composite score (0-100) ───────────────────────────────────────────
    total_score = round(fin_score + hist_score + op_score + mkt_score)

    # ─── Profile thresholds ────────────────────────────────────────────────
    if total_score <= 25:
        profile = "ENTRANTE"
    elif total_score <= 55:
        profile = "CRESCIMENTO"
    elif total_score <= 80:
        profile = "ESTABELECIDO"
    else:
        profile = "CONSOLIDADO"

    # Hard cap: 0 government contracts → max CRESCIMENTO
    profile_capped = False
    if total_count == 0 and profile in ("ESTABELECIDO", "CONSOLIDADO"):
        profile = "CRESCIMENTO"
        profile_capped = True

    # ─── Confidence: based on how many data sources contributed ─────────────
    data_sources_ok = 0
    if capital > 0:
        data_sources_ok += 1  # Financial data present
    if total_count > 0:
        data_sources_ok += 1  # Contract history present
    if data_inicio_str:
        data_sources_ok += 1  # Age data present
    if qsa_count > 0:
        data_sources_ok += 1  # QSA data present

    if data_sources_ok >= 3:
        confidence = "HIGH"
    elif data_sources_ok == 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # ─── Human-readable explanation ────────────────────────────────────────
    nota_parts = [f"Score {total_score}/100 ({confidence})"]
    nota_parts.append(f"Capital: R${capital:,.0f}" if capital > 0 else "Capital: não informado")
    nota_parts.append(f"{total_count} contrato(s) gov.")
    if profile_capped:
        nota_parts.append("perfil limitado a CRESCIMENTO por ausência de contratos governamentais")
    if data_inicio_str:
        nota_parts.append(f"Atividade desde {data_inicio_str[:10]}")
    nota = ". ".join(nota_parts)

    return {
        "profile": profile,
        "score": total_score,
        "breakdown": {
            "financeiro": round(fin_raw),
            "historico": round(hist_raw),
            "operacional": round(op_raw),
            "mercado": round(mkt_raw),
        },
        "confidence": confidence,
        "nota": nota,
        # Legacy compat fields from detect_maturity_profile()
        "total_contract_count": total_count,
        "esferas": esferas,
        "geographic_spread": geo_spread,
        "max_contract_ratio": round(max_ratio, 2),
        "total_contract_value": round(total_contract_value, 2),
        "acervo_objetos": acervo_objetos[:20],
        "rationale": nota,
        "federal_contract_count": esferas.get("Federal", 0),
        "profile_capped": profile_capped,
        "_source": _source_tag("CALCULATED", f"4-axis score: fin={round(fin_raw)} hist={round(hist_raw)} op={round(op_raw)} mkt={round(mkt_raw)}"),
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
    total_api_calls = 0
    failed_calls = 0

    for uf in ufs:
        uf_captured = sum(1 for e in captured_editais if (e.get("uf", "") or "").upper() == uf.upper())
        uf_estimated = 0

        # Query PNCP for total count (page 1 only, read totalRegistros)
        for mod_code in MODALIDADES:  # All known modalidades (skip excluded)
            if mod_code in MODALIDADES_EXCLUIDAS:
                continue
            total_api_calls += 1
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
                else:
                    failed_calls += 1
                    print(f"    [COVERAGE] {uf} mod {mod_code}: resposta vazia")
            except Exception as e:
                failed_calls += 1
                print(f"    [COVERAGE] {uf} mod {mod_code}: falha ({type(e).__name__})")

        total_estimated += uf_estimated
        rate = uf_captured / uf_estimated if uf_estimated > 0 else None
        per_uf.append({
            "uf": uf,
            "captured": uf_captured,
            "estimated_total": uf_estimated,
            "rate": round(rate, 2) if rate is not None else None,
        })

    successful_calls = total_api_calls - failed_calls
    verified = successful_calls > 0

    if total_api_calls > 0 and failed_calls == total_api_calls:
        # ALL API calls failed — coverage is not verifiable
        overall_rate = None
        print(f"    [COVERAGE] {successful_calls}/{total_api_calls} chamadas bem-sucedidas — cobertura NAO verificavel")
    else:
        overall_rate = captured_count / total_estimated if total_estimated > 0 else None
        print(f"    [COVERAGE] {successful_calls}/{total_api_calls} chamadas bem-sucedidas — cobertura {'verificada' if verified else 'NAO verificavel'}")

    warning = None
    if overall_rate is not None:
        low_ufs = [p for p in per_uf if p["rate"] is not None and p["rate"] < 0.70 and p["estimated_total"] > 0]
        if overall_rate < 0.70:
            warning = (
                f"Cobertura geral abaixo de 70% ({overall_rate:.0%}). "
                f"UFs com baixa cobertura: {', '.join(p['uf'] for p in low_ufs)}. "
                "Possivel subrepresentacao de oportunidades."
            )
        elif low_ufs:
            warning = (
                "Cobertura abaixo de 70% em: " + ", ".join(p["uf"] + f" ({p['rate']:.0%})" for p in low_ufs) + "."
            )
    else:
        warning = "Cobertura nao verificavel — todas as chamadas PNCP falharam."

    return {
        "coverage_rate": round(overall_rate, 2) if overall_rate is not None else None,
        "captured_count": captured_count,
        "total_estimated": total_estimated,
        "per_uf": per_uf,
        "warning": warning,
        "_verified": verified,
        "methodology": (
            "Total estimado via contagem PNCP (todas as modalidades relevantes, "
            "ultimos 30 dias por UF). Taxa = editais capturados / total publicado."
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
    # Fornecimento (supply) sectors
    "fornecimento_saude": {
        "certifications": ["AFE/ANVISA (se medicamentos/correlatos)", "Alvará Sanitário"],
        "atestados": ["Atestado de fornecimento de materiais hospitalares"],
        "capital_pct": 0.05,
    },
    "fornecimento_limpeza": {
        "certifications": ["AFE/ANVISA (se saneantes domissanitários)"],
        "atestados": ["Atestado de fornecimento de produtos de limpeza"],
        "capital_pct": 0.05,
    },
    "fornecimento_papelaria": {
        "certifications": [],
        "atestados": ["Atestado de fornecimento de material de expediente"],
        "capital_pct": 0.05,
    },
    "fornecimento_mobiliario": {
        "certifications": [],
        "atestados": ["Atestado de fornecimento de mobiliário"],
        "capital_pct": 0.05,
    },
    "fornecimento_alimentos": {
        "certifications": ["Alvará Sanitário", "Licença Vigilância Sanitária"],
        "atestados": ["Atestado de fornecimento de gêneros alimentícios"],
        "capital_pct": 0.05,
    },
    "fornecimento_geral": {
        "certifications": [],
        "atestados": ["Atestado de fornecimento de materiais similares"],
        "capital_pct": 0.05,
    },
    "servicos_profissionais": {
        "certifications": ["Registro no conselho profissional (CRM/CRF/COREN)"],
        "atestados": ["Atestado de prestação de serviço profissional"],
        "capital_pct": 0.05,
    },
    "servicos_gerais": {
        "certifications": [],
        "atestados": ["Atestado de prestação de serviço similar"],
        "capital_pct": 0.05,
    },
    "concessao": {
        "certifications": [],
        "atestados": ["Atestado de exploração de atividade similar"],
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
    valor = _safe_float(edital.get("valor_estimado")) or 0.0
    capital = _safe_float(empresa.get("capital_social")) or 0.0
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
        val_fmt = _fmt_brl(_safe_float(best_match_info['valor']) or 0.0)
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
        valor_est = _safe_float(c.get("valor_estimado", 0)) or 0.0
        valor_hom = _safe_float(c.get("valor", c.get("valor_homologado", 0))) or 0.0
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
    adjudicated = sum(1 for c in organ_contracts if (_safe_float(c.get("valor", 0)) or 0.0) > 0)
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
    valor = _safe_float(edital.get("valor_estimado")) or 0.0
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
        risk_flags.append(f"Prazo insuficiente: {dias} dias para contrato de {_fmt_brl(valor)}")

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
    geo_editais.sort(key=lambda x: _safe_float(x["ed"].get("valor_estimado", 0)) or 0.0, reverse=True)

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
            total_valor = sum((_safe_float(m["ed"].get("valor_estimado", 0)) or 0.0) for m in cluster_members)

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
# TRACK C: SCENARIOS, SENSITIVITY ANALYSIS, AND TRIGGERS
# ============================================================

def _parse_margin_range(margin_str: str) -> tuple[float, float]:
    """Parse margin_range string like '8%-15%' into (0.08, 0.15)."""
    if not margin_str or margin_str == "N/A":
        return (0.08, 0.15)  # Safe default
    try:
        parts = margin_str.replace("%", "").split("-")
        if len(parts) == 2:
            return (float(parts[0]) / 100.0, float(parts[1]) / 100.0)
    except (ValueError, IndexError):
        pass
    return (0.08, 0.15)


def calculate_scenarios(edital: dict, sector_key: str = "") -> dict:
    """Compute base/optimistic/pessimistic scenarios for an edital.

    Uses existing win_probability and roi_potential data to project
    3 deterministic scenarios with different competitive assumptions.
    Returns dict with base, optimistic, pessimistic scenarios.
    """
    wp = edital.get("win_probability", {})
    roi = edital.get("roi_potential", {})
    prob = wp.get("probability", 0)
    valor = _safe_float(edital.get("valor_estimado")) or 0.0

    # Skip if no win_probability data
    if not wp or prob <= 0 or valor <= 0:
        return {
            "base": {"prob": 0, "roi_min": 0, "roi_max": 0},
            "optimistic": {"prob": 0, "roi_min": 0, "roi_max": 0, "trigger": "Dados insuficientes"},
            "pessimistic": {"prob": 0, "roi_min": 0, "roi_max": 0, "trigger": "Dados insuficientes"},
            "_source": _source_tag("CALCULATED", "Dados insuficientes para cenários"),
        }

    n_suppliers = wp.get("n_unique_suppliers", 0)
    incumbency_bonus = wp.get("incumbency_bonus", 0)
    top_share = wp.get("top_supplier_share", 0)

    # Parse margins
    margin_str = roi.get("margin_range", "8%-15%")
    margin_min, margin_max = _parse_margin_range(margin_str)

    # Participation cost from calculation_memory
    calc_mem = roi.get("calculation_memory", {})
    custo = _safe_float(calc_mem.get("custo_participacao", 0)) or 0.0

    # Base scenario — use existing values as-is
    base = {
        "prob": round(prob, 4),
        "roi_min": roi.get("roi_min", 0),
        "roi_max": roi.get("roi_max", 0),
    }

    # Optimistic scenario
    if n_suppliers <= 3 and n_suppliers > 0:
        prob_opt = min(prob * 2.5, 0.5)
        trigger_opt = "Menos de 3 propostas registradas"
    elif incumbency_bonus > 0:
        prob_opt = min(prob + 0.10, 0.5)
        trigger_opt = "Empresa é incumbente no órgão"
    else:
        prob_opt = min(prob * 1.8, 0.4)
        trigger_opt = "Cenário favorável — competição reduzida"

    roi_opt_min = round(valor * prob_opt * margin_min - custo)
    roi_opt_max = round(valor * prob_opt * margin_max - custo)
    optimistic = {
        "prob": round(prob_opt, 4),
        "roi_min": roi_opt_min,
        "roi_max": roi_opt_max,
        "trigger": trigger_opt,
    }

    # Pessimistic scenario
    if n_suppliers > 10:
        prob_pes = prob * 0.4
        trigger_pes = "Mais de 10 concorrentes"
    elif top_share > 0.3:
        prob_pes = prob * 0.3
        trigger_pes = "Incumbente forte com >30% de market share"
    else:
        prob_pes = prob * 0.5
        trigger_pes = "Cenário adverso — competição intensa"

    prob_pes = max(prob_pes, 0.001)  # Floor to avoid zero
    roi_pes_min = round(valor * prob_pes * margin_min - custo)
    roi_pes_max = round(valor * prob_pes * margin_max - custo)
    pessimistic = {
        "prob": round(prob_pes, 4),
        "roi_min": roi_pes_min,
        "roi_max": roi_pes_max,
        "trigger": trigger_pes,
    }

    return {
        "base": base,
        "optimistic": optimistic,
        "pessimistic": pessimistic,
        "_source": _source_tag("CALCULATED"),
    }


def sensitivity_analysis(edital: dict) -> dict:
    """Test if recommendation changes when risk_score weights are perturbed +/-10%.

    For each of the 5 dimensions, perturbs its weight by +10% and -10%,
    redistributing proportionally to other dimensions so they still sum to 1.0.
    If ANY perturbation changes the recommendation category -> "FRAGIL".
    If NONE changes -> "ROBUSTA".
    """
    rs = edital.get("risk_score", {})
    if not rs or rs.get("vetoed"):
        return {
            "stability": "N/A",
            "sensitive_to": None,
            "original_score": rs.get("total", 0) if rs else 0,
            "score_range": [0, 0],
            "_source": _source_tag("CALCULATED", "Edital vetado ou sem risk_score"),
        }

    weights = rs.get("weights", {})
    if not weights:
        return {
            "stability": "N/A",
            "sensitive_to": None,
            "original_score": rs.get("total", 0),
            "score_range": [0, 0],
            "_source": _source_tag("CALCULATED", "Sem pesos de risk_score"),
        }

    # Dimension scores
    dim_map = {
        "hab": rs.get("habilitacao", 50),
        "fin": rs.get("financeiro", 50),
        "geo": rs.get("geografico", 50),
        "prazo": rs.get("prazo", 50),
        "comp": rs.get("competitivo", 50),
    }
    original_total = rs.get("total", 0)

    # Recommendation thresholds (consistent with portfolio analysis categories)
    def _get_rec(score: float) -> str:
        if score >= 60:
            return "PARTICIPAR"
        elif score >= 30:
            return "AVALIAR"
        else:
            return "NAO_RECOMENDADO"

    original_rec = _get_rec(original_total)
    perturbed_scores: list[float] = []
    sensitive_dim = None

    for dim_key in dim_map:
        w_orig = weights.get(dim_key, 0.2)
        if w_orig <= 0:
            continue

        for delta in [0.10, -0.10]:
            # Perturbed weight for this dimension
            w_new = w_orig * (1 + delta)
            # Sum of other original weights
            other_sum = sum(weights.get(k, 0) for k in dim_map if k != dim_key)
            if other_sum <= 0:
                continue
            # Redistribution factor for other weights (so total still sums to 1.0)
            redistrib = (1.0 - w_new) / other_sum

            # Recompute total with perturbed weights
            total_perturbed = 0.0
            for k, score_val in dim_map.items():
                if k == dim_key:
                    total_perturbed += score_val * w_new
                else:
                    total_perturbed += score_val * (weights.get(k, 0.2) * redistrib)

            # Apply threshold gates (same as original)
            threshold = rs.get("threshold_applied")
            if threshold:
                if "prazo" in threshold:
                    total_perturbed = min(total_perturbed, 20)
                if "financeiro" in threshold:
                    total_perturbed = min(total_perturbed, 25)
                if "habilitacao" in threshold:
                    total_perturbed = min(total_perturbed, 30)

            total_perturbed = round(total_perturbed)
            perturbed_scores.append(total_perturbed)

            # Check if recommendation changes
            if _get_rec(total_perturbed) != original_rec and sensitive_dim is None:
                dim_labels = {
                    "hab": "habilitação",
                    "fin": "financeiro",
                    "geo": "geográfico",
                    "prazo": "prazo",
                    "comp": "competitivo",
                }
                sensitive_dim = dim_labels.get(dim_key, dim_key)

    stability = "FRAGIL" if sensitive_dim else "ROBUSTA"
    score_range = [
        min(perturbed_scores) if perturbed_scores else original_total,
        max(perturbed_scores) if perturbed_scores else original_total,
    ]

    return {
        "stability": stability,
        "sensitive_to": sensitive_dim,
        "original_score": original_total,
        "score_range": score_range,
        "_source": _source_tag("CALCULATED"),
    }


def identify_triggers(edital: dict) -> list[dict]:
    """Generate actionable trigger points for monitoring an edital.

    Based on edital characteristics, generates 1-3 triggers that
    represent conditions under which the opportunity assessment
    should be revisited.
    """
    triggers: list[dict] = []

    rs = edital.get("risk_score", {})
    wp = edital.get("win_probability", {})
    dias = edital.get("dias_restantes")
    n_suppliers = wp.get("n_unique_suppliers", 0)
    category = edital.get("strategic_category", "")
    qual_gap = edital.get("qualification_gap", {})
    ci = edital.get("competitive_intel", [])

    # Trigger 1: Esclarecimento ou errata (applicable when there's time)
    if dias is not None and dias > 10:
        triggers.append({
            "condition": "Se publicado esclarecimento ou errata",
            "action": "Reavaliar prazos e requisitos",
            "impact": "Prazo pode ser estendido",
        })

    # Trigger 2: Low competition day-of
    if n_suppliers > 5:
        triggers.append({
            "condition": "Se menos de 3 propostas registradas no dia",
            "action": "Reavaliar — probabilidade sobe significativamente",
            "impact": "Chance pode triplicar",
        })

    # Trigger 3: Qualification gap can be addressed
    gaps = qual_gap.get("operational_gaps", []) if isinstance(qual_gap, dict) else []
    has_addressable_gap = any(g.get("addressable") for g in gaps if isinstance(g, dict))
    if category in ("AVALIAR COM CAUTELA", "INVESTIMENTO", "OPORTUNIDADE") and has_addressable_gap:
        triggers.append({
            "condition": "Se a empresa obtiver atestado técnico complementar",
            "action": "Reclassificar para PARTICIPAR",
            "impact": "Score de habilitação sobe ~20 pontos",
        })

    # Trigger 4: Low financial score
    fin_score = rs.get("financeiro", 50) if isinstance(rs, dict) else 50
    if fin_score < 40:
        triggers.append({
            "condition": "Se o órgão publicar valor estimado revisado para baixo",
            "action": "Reavaliar viabilidade financeira",
            "impact": "Pode tornar-se viável",
        })

    # Trigger 5: Incumbency disruption
    has_rescisoes = False
    for c in (ci if isinstance(ci, list) else []):
        sit = (c.get("situacao") or c.get("status") or "").lower()
        if any(kw in sit for kw in ["rescisão", "rescisao", "cancelad", "anulad"]):
            has_rescisoes = True
            break
    if has_rescisoes:
        triggers.append({
            "condition": "Se incumbente perder contrato vigente (rescisão)",
            "action": "Oportunidade de substituição",
            "impact": "Campo limpo para novos fornecedores",
        })

    # Sort by actionability (most actionable first) and limit to 3
    priority_order = {
        "Se a empresa obtiver atestado técnico complementar": 1,
        "Se menos de 3 propostas registradas no dia": 2,
        "Se incumbente perder contrato vigente (rescisão)": 3,
        "Se o órgão publicar valor estimado revisado para baixo": 4,
        "Se publicado esclarecimento ou errata": 5,
    }
    triggers.sort(key=lambda t: priority_order.get(t["condition"], 99))
    return triggers[:3]


def enrich_scenarios_and_triggers(
    editais: list[dict],
    sector_key: str,
    skip_scenarios: bool = False,
) -> None:
    """Enrich each edital with scenarios, sensitivity analysis, and triggers.

    Must be called AFTER risk_score, win_probability, roi_potential, and
    strategic_category are all set on each edital.
    Mutates editais in place.
    """
    if skip_scenarios:
        return

    n = len(editais)
    if n == 0:
        return

    print(f"\n  [SCENARIOS] Calculando cenários e sensibilidade para {n} editais...")

    n_fragil = 0
    n_triggers = 0
    for ed in editais:
        ed["scenarios"] = calculate_scenarios(ed, sector_key)
        ed["sensitivity"] = sensitivity_analysis(ed)
        ed["triggers"] = identify_triggers(ed)

        if ed["sensitivity"].get("stability") == "FRAGIL":
            n_fragil += 1
        n_triggers += len(ed["triggers"])

    print(f"  [SCENARIOS] Concluído: {n_fragil}/{n} análises frágeis, {n_triggers} triggers gerados")


# ============================================================
# A1: CNAE × OBJECT COMPATIBILITY CHECK
# ============================================================

def _check_cnae_object_compatibility(editais: list, empresa: dict) -> None:
    """Check if company's CNAE is compatible with each edital's object.

    Sets ed["_cnae_compatible"] = True/False and ed["_cnae_incompatibility_detail"]
    when incompatible. Mutates editais in place.
    """
    cnae_principal = str(empresa.get("cnae_principal", "") or "")
    # Extract 4-digit prefix (e.g. "4120-4" -> "4120", "41204" -> "4120")
    cnae_digits = re.sub(r"[^0-9]", "", cnae_principal)
    cnae_prefix = cnae_digits[:4] if len(cnae_digits) >= 4 else ""

    patterns = CNAE_INCOMPATIBLE_OBJECTS.get(cnae_prefix)
    if not patterns:
        # No incompatibility rules for this CNAE — all compatible
        for ed in editais:
            ed["_cnae_compatible"] = True
            ed["_cnae_incompatibility_detail"] = None
        return

    # Compile all patterns once
    compiled = [(p, re.compile(p, re.IGNORECASE)) for p in patterns]

    for ed in editais:
        objeto = (ed.get("objeto", ed.get("objetoCompra", "")) or "").lower()
        matched_pattern = None
        for raw_pat, cpat in compiled:
            if cpat.search(objeto):
                matched_pattern = raw_pat
                break

        if matched_pattern:
            ed["_cnae_compatible"] = False
            # Extract a readable snippet of what matched
            match_obj = re.search(matched_pattern, objeto, re.IGNORECASE)
            matched_term = match_obj.group(0) if match_obj else "termo incompatível"
            ed["_cnae_incompatibility_detail"] = (
                f"Objeto do edital ({matched_term}) incompatível com "
                f"CNAE {cnae_principal} da empresa. "
                f"Empresa não possui atividade registrada neste segmento."
            )
        else:
            ed["_cnae_compatible"] = True
            ed["_cnae_incompatibility_detail"] = None


# ============================================================
# A2: HABILITAÇÃO DETERMINÍSTICA CHECKLIST
# ============================================================

def _compute_habilitacao_checklist(editais: list, empresa: dict, sicaf: dict, sector_key: str = "") -> None:
    """Compute structured habilitação checklist for each edital.

    Sets ed["habilitacao_checklist"] dict with boolean flags and thresholds.
    Mutates editais in place.
    """
    empresa_capital = _safe_float(empresa.get("capital_social")) or 0.0
    is_simples = bool(empresa.get("simples_nacional"))
    is_mei = bool(empresa.get("mei"))
    has_acervo = bool(empresa.get("maturity_profile", {}).get("acervo_objetos"))
    _sancoes_raw = empresa.get("sancoes") if isinstance(empresa.get("sancoes"), dict) else {}
    has_sancoes = any(
        v for k, v in _sancoes_raw.items()
        if k != "sancionada" and isinstance(v, (bool, int)) and v
    )
    sicaf_status = sicaf.get("status_crc") if sicaf else None

    # Sector-specific capital minimum percentage (Lei 14.133, art. 69 §4: max 10%)
    sector_hab = _HABILITACAO_REQUIREMENTS.get(sector_key, _HABILITACAO_REQUIREMENTS.get("_default", {}))
    capital_min_pct = sector_hab.get("capital_minimo_pct", 0.10)

    for ed in editais:
        valor = _safe_float(ed.get("valor_estimado")) or 0.0
        modalidade = ed.get("modalidade", "") or ""
        capital_minimo_exigido = valor * capital_min_pct

        # Any modality can require atestados tecnicos for works/engineering (Lei 14.133, art. 67).
        # Concorrencia almost always requires them; Pregao for engineering frequently does too.
        is_obra = ed.get("_nature") in ("OBRA", "SERVICO_ENGENHARIA")
        cat_required = is_obra and valor > 80_000  # Most engineering works above dispensa threshold require CAT

        ed["habilitacao_checklist"] = {
            "capital_minimo_ok": empresa_capital >= capital_minimo_exigido,
            "capital_minimo_exigido": capital_minimo_exigido,
            "capital_empresa": empresa_capital,
            # No legal prohibition on Simples Nacional bidding any value
            "simples_ok": True,
            "simples_revenue_warning": is_simples and valor > 4_800_000,  # Tax planning alert
            # No legal prohibition on MEI bidding any value
            "mei_ok": True,
            "mei_revenue_warning": is_mei and valor > 81_000,  # Tax planning alert
            "cat_required": cat_required,
            "cat_available": has_acervo,
            "sancoes_ok": not has_sancoes,
            "sicaf_ok": sicaf_status in ("CADASTRADO", None),
            # Items NOT verified by automated analysis (explicit for transparency)
            "fiscal_federal_verificado": False,  # CND Federal — requer consulta manual
            "fiscal_estadual_verificado": False,  # CND Estadual — requer consulta manual
            "fiscal_municipal_verificado": False,  # CND Municipal — requer consulta manual
            "fgts_verificado": False,  # CRF FGTS — requer consulta manual
            "trabalhista_verificado": False,  # CNDT Trabalhista — requer consulta manual
            "falencia_verificado": False,  # Certidao negativa de falencia — requer consulta manual
            "crea_cau_verificado": False,  # Registro CREA/CAU — requer consulta manual
        }


# ============================================================
# A5: RICH JUSTIFICATIVAS
# ============================================================

def _build_rich_justificativa(ed: dict, empresa: dict) -> str:
    """Build a rich, edital-specific justificativa that answers 'por quê?'.

    Uses habilitacao_checklist, _cnae_compatible, distance, timeline,
    competitive intel, and financial data to produce concrete explanations
    instead of generic labels.
    """
    rs = ed.get("risk_score", {})
    hab = ed.get("habilitacao_checklist", {})
    valor = _safe_float(ed.get("valor_estimado")) or 0.0
    dist_info = ed.get("distancia") or {}
    dist_km = dist_info.get("km") if isinstance(dist_info, dict) else None
    dias = ed.get("dias_restantes")
    municipio = ed.get("municipio", "") or ""
    modalidade = ed.get("modalidade", "") or ""

    parts: list[str] = []

    # CNAE compatibility — advisory, not veto (Lei 14.133 does not reference CNAE)
    if not ed.get("_cnae_compatible", True):
        detail = ed.get("_cnae_incompatibility_detail", "")
        parts.append(
            f"CNAE principal ({empresa.get('cnae_principal', '')}) diverge do objeto do edital"
            f"{': ' + detail if detail else ''}. "
            f"CNAE nao e requisito legal de habilitacao (Lei 14.133 exige atestados tecnicos, nao CNAE) — "
            f"participacao viavel se empresa possuir atestados e objeto social compativel"
        )

    # Financial fit — capital social
    if hab.get("capital_minimo_ok") is True:
        capital = hab.get("capital_empresa", 0)
        exigido = hab.get("capital_minimo_exigido", 0)
        if exigido > 0:
            parts.append(f"Capital social R$ {capital:,.0f} atende mínimo de R$ {exigido:,.0f}")
    elif hab.get("capital_minimo_ok") is False:
        capital = hab.get("capital_empresa", 0)
        exigido = hab.get("capital_minimo_exigido", 0)
        parts.append(
            f"Capital social R$ {capital:,.0f} insuficiente para minimo estimado de "
            f"R$ {exigido:,.0f} (verificar edital para % real — maximo legal: 10%)"
        )

    # Simples Nacional / MEI revenue warnings (advisory, not legal barrier)
    if hab.get("simples_revenue_warning"):
        parts.append(
            f"ALERTA TRIBUTARIO: contrato de {_fmt_brl(valor)} pode levar faturamento anual "
            f"acima do teto do Simples Nacional (R$ 4,8M) — avaliar impacto tributario antes de participar"
        )
    if hab.get("mei_revenue_warning"):
        parts.append(
            f"ALERTA TRIBUTARIO: contrato de {_fmt_brl(valor)} pode levar faturamento anual "
            f"acima do teto MEI (R$ 81.000) — avaliar enquadramento tributario antes de participar"
        )

    # Sanções
    if not hab.get("sancoes_ok", True):
        parts.append("Empresa possui sanções ativas — impedimento legal à participação")

    # Distance
    if dist_km is not None:
        try:
            dist_km = float(dist_km)
        except (TypeError, ValueError):
            dist_km = None
    if dist_km is not None:
        if dist_km < 100:
            parts.append(f"Proximidade favorável ({dist_km:.0f}km de {municipio})")
        elif dist_km < 300:
            parts.append(f"Distância viável ({dist_km:.0f}km de {municipio})")
        elif dist_km < 500 and "Presencial" in modalidade:
            parts.append(f"Distância moderada ({dist_km:.0f}km) para licitação presencial")
        elif dist_km >= 500 and "Presencial" in modalidade:
            parts.append(f"Distância elevada ({dist_km:.0f}km) para licitação presencial — logística desafiadora")
        elif dist_km >= 500:
            parts.append(f"Distância elevada ({dist_km:.0f}km de {municipio})")

    # Timeline
    if dias is not None:
        try:
            dias = int(dias)
        except (TypeError, ValueError):
            dias = None
    if dias is not None:
        if dias <= 3:
            parts.append(f"Prazo crítico: apenas {dias} dia(s) restante(s)")
        elif dias <= 7:
            parts.append(f"Prazo curto: {dias} dias para encerramento")
        elif dias <= 14:
            parts.append(f"Prazo adequado: {dias} dias para preparação")
        else:
            parts.append(f"Prazo confortável: {dias} dias restantes")

    # CAT / Acervo
    if hab.get("cat_required") and not hab.get("cat_available"):
        parts.append(
            "Exige atestado técnico (CAT) que a empresa não possui — "
            "participação condicionada a acervo do responsável técnico"
        )
    elif hab.get("cat_required") and hab.get("cat_available"):
        parts.append("Atestado técnico (CAT) disponível via histórico de contratos")

    # Competition
    comp = rs.get("competitivo", 50)
    if comp >= 80:
        parts.append("Baixa concorrência identificada neste órgão")
    elif comp <= 20:
        parts.append("Alta concorrência — órgão com muitos fornecedores ativos")

    # Fiscal risk
    fiscal = rs.get("fiscal_risk", {})
    if isinstance(fiscal, dict) and fiscal.get("nivel") == "ALTO":
        parts.append("Risco fiscal elevado do município")

    # Acervo
    if rs.get("acervo_confirmado"):
        _hist = empresa.get("historico_contratos", [])
        _n_similar = len(_hist) if _hist else 0
        parts.append(f"Acervo técnico inferido: {_n_similar} contratos similares no histórico")

    if not parts:
        parts.append("Análise baseada em scoring multifatorial")

    return ". ".join(parts) + "."


# ============================================================
# RECOMMENDATION ASSIGNMENT
# ============================================================

def assign_recommendations(editais: list, empresa: dict) -> None:
    """Assign recomendacao + justificativa to each edital based on risk_score.

    Must be called AFTER compute_all_deterministic() so that risk_score.total
    is fully computed (including threshold gates and Inexigibilidade penalty).
    Also uses _cnae_compatible and habilitacao_checklist (set by compute_all_deterministic).
    Mutates editais in place.
    """
    for ed in editais:
        rs = ed.get("risk_score", {})
        total = rs.get("total", 0)
        vetoed = rs.get("vetoed", False)
        veto_reasons = rs.get("veto_reasons", [])
        hab_check = ed.get("habilitacao_checklist", {})

        # Existing veto from risk_score
        if vetoed:
            ed["recomendacao"] = "NÃO RECOMENDADO"
            ed["justificativa"] = "; ".join(veto_reasons) if veto_reasons else "Edital vetado por impedimento legal."
            continue

        # A1: CNAE incompatibility — NOT a legal disqualification (Lei 14.133 does not reference CNAE).
        # What matters is technical qualification (atestados) and social contract object clause.
        # Downgrade to AVALIAR COM CAUTELA with advisory, not hard veto.
        if not ed.get("_cnae_compatible", True):
            if total >= 40:
                ed["recomendacao"] = "AVALIAR COM CAUTELA"
            else:
                ed["recomendacao"] = "NÃO RECOMENDADO"
            ed["justificativa"] = _build_rich_justificativa(ed, empresa)
            continue

        # A2: Habilitação checklist — capital check (simples/mei are now warnings, not vetoes)
        if hab_check.get("capital_minimo_ok") is False:
            ed["recomendacao"] = "NÃO RECOMENDADO"
            ed["justificativa"] = _build_rich_justificativa(ed, empresa)
            continue

        # Standard threshold-based recommendation
        if total >= 70:
            ed["recomendacao"] = "PARTICIPAR"
        elif total >= 40:
            ed["recomendacao"] = "AVALIAR COM CAUTELA"
        else:
            ed["recomendacao"] = "NÃO RECOMENDADO"

        # A5: Rich justificativa replaces generic labels
        ed["justificativa"] = _build_rich_justificativa(ed, empresa)


# ============================================================
# FIX 3: DETERMINISTIC PRÓXIMOS PASSOS GENERATION
# ============================================================

_HAB_DOC_LABELS: dict[str, str] = {
    "sicaf_ok": "Cadastro SICAF ativo e atualizado",
    "fiscal_federal_verificado": "CND Federal (Receita Federal + Dívida Ativa da União)",
    "fgts_verificado": "CRF FGTS (Caixa Econômica Federal)",
    "fiscal_estadual_verificado": "CND Estadual",
    "fiscal_municipal_verificado": "CND Municipal",
    "trabalhista_verificado": "CNDT — Certidão Negativa de Débitos Trabalhistas",
    "falencia_verificado": "Certidão Negativa de Falência e Concordata",
    "crea_cau_verificado": "Registro CREA/CAU — profissional responsável técnico",
    "cat_required": "Atestado de Capacidade Técnica (CAT) compatível com o objeto",
    "capital_minimo_ok": "Balanço Patrimonial — capital mínimo de 10% do valor do edital",
}


def generate_proximos_passos(editais: list[dict], empresa: dict) -> dict:
    """Generate deterministic action plan from PARTICIPAR/AVALIAR editais.

    HARD-006: Maps each action item to specific editais that require it.
    Priority scoring: count_affected_editais x urgency_factor.
    Must be called AFTER assign_recommendations() and build_alertas_criticos().

    Returns:
        {
            "acao_imediata": [...],        # <=7 days remaining
            "medio_prazo": [...],          # 8-21 days
            "desenvolvimento_estrategico": [...],  # 22-30 days
            "desenvolvimento_plan": [...], # HARD-006: grouped by action category
            "checklist_habilitacao": [...],
            "_source": {...},
        }

    Each item:
        {
            "acao": str,
            "edital_ref": str,
            "editais_afetados": list[str],
            "prioridade": int,
            "prazo_sugerido": str,
            "categoria": str,
            "orgao": str,
            "valor": float,
            "prazo_proposta": str (DD/MM/YYYY),
            "dias_restantes": int,
            "documentos_necessarios": list[str],
        }
    """
    acao_imediata: list[dict] = []
    medio_prazo: list[dict] = []
    desenvolvimento_estrategico: list[dict] = []

    target_recs = {"PARTICIPAR", "AVALIAR COM CAUTELA"}

    # HARD-006: Track action categories across all editais for development plan
    action_categories: dict[str, dict] = {}  # category -> {editais, min_dias, acao, ...}

    for ed in editais:
        rec = (ed.get("recomendacao") or "").upper()
        if rec not in target_recs:
            continue

        dias = ed.get("dias_restantes")
        if dias is None or dias < 0:
            continue  # Already expired

        # Build required documents list from habilitacao_checklist
        hab = ed.get("habilitacao_checklist") or {}
        docs_necessarios: list[str] = []
        for key, label in _HAB_DOC_LABELS.items():
            val = hab.get(key)
            # Include items that are False (not OK) or explicitly required (True for cat_required)
            if key == "cat_required" and val is True:
                docs_necessarios.append(label)
            elif key not in ("cat_required",) and val is False:
                docs_necessarios.append(label)

        # Format prazo_proposta as DD/MM/YYYY
        prazo_raw = ed.get("data_encerramento") or ""
        try:
            if prazo_raw:
                dt_prazo = datetime.strptime(prazo_raw[:10], "%Y-%m-%d")
                prazo_br = dt_prazo.strftime("%d/%m/%Y")
            else:
                prazo_br = ""
        except ValueError:
            prazo_br = prazo_raw[:10] if prazo_raw else ""

        valor = _safe_float(ed.get("valor_estimado")) or 0.0
        edital_ref = (
            ed.get("numero_controle")
            or ed.get("_id")
            or ed.get("sequencial_compra")
            or "—"
        )
        orgao = (ed.get("orgao") or "").strip()[:80]
        objeto_resumo = (ed.get("objeto") or "")[:120]
        uf = ed.get("uf") or ""
        municipio = ed.get("municipio") or ""
        loc = f"{municipio}/{uf}" if municipio and uf else (uf or municipio)

        if dias <= 7:
            prioridade_label = "ALTA"
        elif dias <= 14:
            prioridade_label = "MEDIA"
        else:
            prioridade_label = "NORMAL"

        # HARD-006: Urgency factor for priority scoring
        if dias <= 7:
            urgency_factor = 3
        elif dias <= 15:
            urgency_factor = 2
        else:
            urgency_factor = 1

        # ROI gate
        roi = ed.get("roi_potential") or {}
        roi_min = roi.get("roi_min") if isinstance(roi, dict) else None
        roi_max = roi.get("roi_max") if isinstance(roi, dict) else None

        # Skip if both min AND max ROI are negative (guaranteed loss)
        if roi_min is not None and roi_max is not None and roi_max < 0:
            continue

        # Build alerts
        alertas: list[str] = []
        if roi_min is not None and roi_min < 0:
            alertas.append("Retorno potencialmente negativo no cenário pessimista")

        hab_chk = ed.get("habilitacao_checklist") or {}
        if hab_chk.get("cat_required") and not hab_chk.get("cat_available"):
            alertas.append("Atestado técnico (CAT) exigido e não verificado")

        # Downgrade priority label if alerts exist
        if alertas:
            if prioridade_label == "ALTA":
                prioridade_label = "MEDIA"
            elif prioridade_label == "MEDIA":
                prioridade_label = "NORMAL"

        acao_str = (
            f"{'⚡ URGENTE: ' if dias <= 3 else ''}"
            f"Preparar proposta para {orgao}"
            f"{f' ({loc})' if loc else ''}"
            f" — {objeto_resumo}"
        )

        # HARD-006: Determine categoria
        acervo_status = ed.get("acervo_status") or (ed.get("risk_score") or {}).get("acervo_status", "NAO_VERIFICADO")
        if acervo_status != "CONFIRMADO" and hab_chk.get("cat_required"):
            categoria = "DOCUMENTACAO_TECNICA"
        elif not hab_chk.get("capital_minimo_ok", True):
            categoria = "ADEQUACAO_FINANCEIRA"
        elif dias <= 7:
            categoria = "PROPOSTA_URGENTE"
        elif dias <= 15:
            categoria = "PROPOSTA_PLANEJADA"
        else:
            categoria = "PREPARACAO_ESTRATEGICA"

        item = {
            "acao": acao_str,
            "edital_ref": edital_ref,
            "editais_afetados": [edital_ref],
            "orgao": orgao,
            "uf": uf,
            "municipio": municipio,
            "valor": valor,
            "prazo_proposta": prazo_br,
            "dias_restantes": dias,
            "prioridade": urgency_factor,  # HARD-006: numeric priority
            "prioridade_label": prioridade_label,
            "recomendacao": rec,
            "link": ed.get("link") or "",
            "documentos_necessarios": docs_necessarios,
            "alertas": alertas,
            "categoria": categoria,
            "prazo_sugerido": prazo_br if prazo_br else f"{dias} dias",
        }

        if dias <= 7:
            acao_imediata.append(item)
        elif dias <= 21:
            medio_prazo.append(item)
        else:
            desenvolvimento_estrategico.append(item)

        # HARD-006: Aggregate by action category for development plan
        if categoria not in action_categories:
            action_categories[categoria] = {
                "editais_afetados": [],
                "min_dias": dias,
                "count": 0,
                "max_urgency": urgency_factor,
            }
        cat_data = action_categories[categoria]
        cat_data["editais_afetados"].append(edital_ref)
        cat_data["count"] += 1
        cat_data["min_dias"] = min(cat_data["min_dias"], dias)
        cat_data["max_urgency"] = max(cat_data["max_urgency"], urgency_factor)

    # Sort each bucket by priority (highest numeric first) then valor descending
    for bucket in (acao_imediata, medio_prazo, desenvolvimento_estrategico):
        bucket.sort(key=lambda x: (-x["prioridade"], -(x["valor"] or 0)))

    # HARD-006: Build development plan grouped by category
    _CATEGORY_LABELS = {
        "DOCUMENTACAO_TECNICA": "Preparar documentação técnica (CAT/atestados)",
        "ADEQUACAO_FINANCEIRA": "Adequar capacidade financeira (capital/garantias)",
        "PROPOSTA_URGENTE": "Elaborar propostas urgentes",
        "PROPOSTA_PLANEJADA": "Elaborar propostas com prazo adequado",
        "PREPARACAO_ESTRATEGICA": "Preparação estratégica de longo prazo",
    }
    desenvolvimento_plan: list[dict] = []
    for cat_key, cat_data in action_categories.items():
        priority_score = cat_data["count"] * cat_data["max_urgency"]
        desenvolvimento_plan.append({
            "acao": _CATEGORY_LABELS.get(cat_key, cat_key),
            "editais_afetados": cat_data["editais_afetados"],
            "prioridade": priority_score,
            "prazo_sugerido": f"{cat_data['min_dias']} dias (edital mais próximo)",
            "categoria": cat_key,
        })
    desenvolvimento_plan.sort(key=lambda x: -x["prioridade"])

    # ─── Checklist de habilitação (company-level, not per-edital) ────────────
    sicaf = empresa.get("sicaf") or {}
    _pp_sancoes_raw = empresa.get("sancoes") if isinstance(empresa.get("sancoes"), dict) else {}
    has_sancoes = any(
        v for k, v in _pp_sancoes_raw.items()
        if k != "sancionada" and isinstance(v, (bool, int)) and v
    )
    is_simples = bool(empresa.get("simples_nacional"))
    is_mei = "MEI" in (empresa.get("porte") or "").upper()

    checklist_habilitacao: list[str] = []

    sicaf_status = sicaf.get("status", "") if isinstance(sicaf, dict) else ""
    if sicaf_status not in ("CADASTRADO", "ATIVO"):
        checklist_habilitacao.append("Cadastro SICAF: verificar ou realizar cadastro no Portal de Compras do Governo Federal")

    checklist_habilitacao.append("CND Federal: emitir no site da Receita Federal / PGFN (validade 180 dias)")
    checklist_habilitacao.append("CRF FGTS: emitir no site da Caixa Econômica Federal (validade 30 dias)")
    checklist_habilitacao.append("CND Estadual: emitir na Secretaria da Fazenda do estado sede")
    checklist_habilitacao.append("CND Municipal: emitir na Prefeitura do município sede")
    checklist_habilitacao.append("CNDT: emitir no portal do TST (validade 180 dias)")
    checklist_habilitacao.append("Certidão Negativa de Falência: emitir no fórum da comarca sede")

    # CREA/CAU if engineering/architecture sector (indicated by any edital requiring it)
    any_crea = any(
        ed.get("habilitacao_checklist", {}).get("crea_cau_verificado") is False
        for ed in editais
        if (ed.get("recomendacao") or "").upper() in target_recs
    )
    if any_crea:
        checklist_habilitacao.append("Registro CREA/CAU: confirmar registro do responsável técnico")

    any_cat = any(
        ed.get("habilitacao_checklist", {}).get("cat_required") is True
        for ed in editais
        if (ed.get("recomendacao") or "").upper() in target_recs
    )
    if any_cat:
        checklist_habilitacao.append("Atestado de Capacidade Técnica (CAT): reunir atestados de obras/serviços similares registrados em CREA/CAU")

    if has_sancoes:
        checklist_habilitacao.append("ATENÇÃO: sanções registradas — verificar situação junto ao CEIS/CNEP antes de participar")

    total_actionable = len(acao_imediata) + len(medio_prazo) + len(desenvolvimento_estrategico)
    return {
        "acao_imediata": acao_imediata,
        "medio_prazo": medio_prazo,
        "desenvolvimento_estrategico": desenvolvimento_estrategico,
        "desenvolvimento_plan": desenvolvimento_plan,
        "checklist_habilitacao": checklist_habilitacao,
        "_total_editais_acionaveis": total_actionable,
        "_source": _source_tag(
            "CALCULATED",
            f"{total_actionable} editais acionáveis: {len(acao_imediata)} urgentes, "
            f"{len(medio_prazo)} médio prazo, {len(desenvolvimento_estrategico)} estratégicos"
        ),
    }


def build_alertas_criticos(editais: list[dict], empresa: dict) -> None:
    """HARD-004: Build critical alerts linked to specific editais (in-place).

    Adds alertas_criticos: list[dict] to each edital.
    Each alert: {tipo, severidade (CRITICO/ALERTA/INFO), descricao, acao_requerida, prazo_sugerido}

    Alert types:
    - CAT_REQUIRED: If habilitacao_analysis shows technical requirement unmet
    - CAPITAL_LIMITROFE: If valor_estimado > 3x capital_social
    - PRAZO_CRITICO: If dias_restantes <= 7
    - SANCAO_ATIVA: If empresa has active sanctions
    - SIMPLES_LIMITE: If empresa.simples and valor_estimado implies revenue > R$4.8M/year
    - SETOR_DIVERGENTE: If gap_type == "ACERVO_SETOR_DIVERGENTE"
    - FISCAL_RISK: If risk_score.fiscal_risk.nivel == "ALTO"
    - DISTANCIA_ELEVADA: If distancia_km > 500
    """
    capital = _safe_float(empresa.get("capital_social")) or 0.0
    is_simples = bool(empresa.get("simples_nacional"))
    _sancoes_raw = empresa.get("sancoes") if isinstance(empresa.get("sancoes"), dict) else {}
    has_sancoes = any(
        v for k, v in _sancoes_raw.items()
        if k != "sancionada" and isinstance(v, (bool, int)) and v
    )

    for ed in editais:
        alertas: list[dict] = []
        risk = ed.get("risk_score", {})
        qual_gap = ed.get("qualification_gap", {})
        rec = (ed.get("recomendacao") or "").upper()
        valor = _safe_float(ed.get("valor_estimado")) or 0.0
        dias = ed.get("dias_restantes")

        # Alert 1: Acervo/CAT verification needed
        acervo_status = ed.get("acervo_status") or risk.get("acervo_status", "NAO_VERIFICADO")
        if acervo_status != "CONFIRMADO" and rec in ("PARTICIPAR", "AVALIAR COM CAUTELA"):
            alertas.append({
                "tipo": "CAT_REQUIRED",
                "severidade": "CRITICO" if acervo_status == "NAO_VERIFICADO" else "ALERTA",
                "descricao": "Verificação de atestados técnicos necessária",
                "acao_requerida": f"Verificar acervo técnico compatível com: {(ed.get('objeto') or '')[:80]}",
                "prazo_sugerido": "Antes da data de encerramento do edital",
            })

        # Alert 2: Capital insuficiente (limítrofe) — 3x threshold
        if capital > 0 and valor > 0 and valor > 3 * capital:
            alertas.append({
                "tipo": "CAPITAL_LIMITROFE",
                "severidade": "CRITICO" if valor > 5 * capital else "ALERTA",
                "descricao": f"Valor estimado ({_fmt_brl(valor)}) supera {valor/capital:.0f}× o capital social ({_fmt_brl(capital)})",
                "acao_requerida": "Avaliar consórcio, carta de fiança bancária ou aumento de capital",
                "prazo_sugerido": "Antes da habilitação",
            })

        # Alert 3: Prazo crítico
        if dias is not None and dias <= 7 and rec in ("PARTICIPAR", "AVALIAR COM CAUTELA"):
            alertas.append({
                "tipo": "PRAZO_CRITICO",
                "severidade": "CRITICO",
                "descricao": f"Apenas {dias} dia(s) restante(s) para submissão",
                "acao_requerida": "Mobilizar equipe imediatamente — risco de perda por prazo",
                "prazo_sugerido": f"{dias} dia(s)",
            })

        # Alert 4: Sanção ativa
        if has_sancoes:
            alertas.append({
                "tipo": "SANCAO_ATIVA",
                "severidade": "CRITICO",
                "descricao": "Empresa possui sanção ativa (CEIS/CNEP) — impedimento legal à participação",
                "acao_requerida": "Verificar situação junto aos órgãos competentes antes de qualquer participação",
                "prazo_sugerido": "Imediato",
            })

        # Alert 5: Simples Nacional revenue limit
        if is_simples and valor > 4_800_000:
            alertas.append({
                "tipo": "SIMPLES_LIMITE",
                "severidade": "ALERTA",
                "descricao": f"Contrato de {_fmt_brl(valor)} pode ultrapassar o teto do Simples Nacional (R$ 4,8M/ano)",
                "acao_requerida": "Avaliar impacto tributário e possível desenquadramento antes de participar",
                "prazo_sugerido": "Antes da proposta",
            })

        # Alert 6: Setor divergente (from qualification gap)
        for gap in qual_gap.get("operational_gaps", []):
            if gap.get("gap_type") == "ACERVO_SETOR_DIVERGENTE":
                alertas.append({
                    "tipo": "SETOR_DIVERGENTE",
                    "severidade": "ALERTA",
                    "descricao": (gap.get("description") or "Setor do edital diverge do histórico da empresa")[:120],
                    "acao_requerida": (gap.get("action_required") or "Verificar compatibilidade do objeto social")[:120],
                    "prazo_sugerido": "Antes da habilitação",
                })
                break  # One alert per type

        # Alert 7: Fiscal risk
        fiscal_risk = risk.get("fiscal_risk", {})
        if isinstance(fiscal_risk, dict) and fiscal_risk.get("nivel") == "ALTO":
            alertas.append({
                "tipo": "FISCAL_RISK",
                "severidade": "ALERTA",
                "descricao": "Risco fiscal elevado do município — possível atraso em pagamentos",
                "acao_requerida": "Verificar histórico de pagamentos do órgão e considerar cláusulas de reajuste",
                "prazo_sugerido": "Antes da proposta",
            })

        # Alert 8: Distância elevada
        dist = ed.get("distancia", {})
        dist_km = dist.get("km") if isinstance(dist, dict) else None
        if dist_km is not None and dist_km > 500:
            alertas.append({
                "tipo": "DISTANCIA_ELEVADA",
                "severidade": "ALERTA" if dist_km <= 800 else "CRITICO",
                "descricao": f"Distância de {dist_km:.0f}km da sede — logística desafiadora",
                "acao_requerida": "Avaliar custos de mobilização, hospedagem e deslocamento na composição de preços",
                "prazo_sugerido": "Antes da proposta comercial",
            })

        # Alert 9: Remaining qualification gaps (addressable)
        for gap in qual_gap.get("operational_gaps", []):
            if gap.get("addressable") and gap.get("gap_type") not in ("ACERVO_EXISTENTE", "ACERVO_SETOR_DIVERGENTE"):
                alertas.append({
                    "tipo": gap.get("gap_type", "GAP"),
                    "severidade": "ALERTA",
                    "descricao": (gap.get("description") or "")[:120],
                    "acao_requerida": (gap.get("action_required") or "Verificar requisito")[:120],
                    "prazo_sugerido": "Antes da habilitação",
                })

        ed["alertas_criticos"] = alertas


# Keep backward-compatible alias
def _compute_alertas_criticos(editais: list[dict]) -> None:
    """Legacy wrapper — delegates to build_alertas_criticos with empty empresa."""
    build_alertas_criticos(editais, {})


# ============================================================
# MAIN DETERMINISTIC CALCULATION CHAIN
# ============================================================

def compute_all_deterministic(
    editais: list[dict],
    empresa: dict,
    sicaf: dict,
    sector_key: str,
    sector_keywords: list[str] | None = None,
    skip_portfolio_optimization: bool = False,
    skip_scenarios: bool = False,
) -> dict:
    """Compute all deterministic intelligence for editais. Mutates in place.

    Chain: risk_score → win_probability → roi_potential → chronogram
           + object_compatibility, habilitacao, competitive_analysis, risk_analysis
           + E4 qualification gaps, E6 organ risk, E8 maturity
           + Track C: scenarios, sensitivity, triggers
    Portfolio analysis + E7 regional clusters run after per-edital loop.
    Returns dict with portfolio, maturity, dispute_stats, regional_clusters.
    """
    print(f"\n📊 Calculando inteligência estratégica ({len(editais)} editais)")

    # E8: Compute multi-dimensional maturity profile (FIX 1)
    # Uses compute_maturity_score (4 axes) instead of legacy contract-count-only model.
    maturity = compute_maturity_score(empresa, sector_key=sector_key)
    empresa["maturity_profile"] = maturity
    score_info = f"score={maturity['score']}, conf={maturity['confidence']}"
    print(f"  Perfil de maturidade: {maturity['profile']} ({score_info}) — {maturity['nota']}")

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

    # A1: CNAE × Object compatibility (pre-loop, sets ed["_cnae_compatible"])
    _check_cnae_object_compatibility(editais, empresa)
    n_incompat = sum(1 for ed in editais if not ed.get("_cnae_compatible", True))
    if n_incompat:
        print(f"  [A1] CNAE incompatível: {n_incompat}/{len(editais)} editais vetados por CNAE×Objeto")

    # A2: Habilitação determinística checklist (pre-loop, sets ed["habilitacao_checklist"])
    _compute_habilitacao_checklist(editais, empresa, sicaf, sector_key=sector_key)
    n_cap_fail = sum(1 for ed in editais if not ed.get("habilitacao_checklist", {}).get("capital_minimo_ok", True))
    n_simples_warn = sum(1 for ed in editais if ed.get("habilitacao_checklist", {}).get("simples_revenue_warning"))
    n_mei_warn = sum(1 for ed in editais if ed.get("habilitacao_checklist", {}).get("mei_revenue_warning"))
    if n_cap_fail or n_simples_warn or n_mei_warn:
        print(f"  [A2] Habilitação: {n_cap_fail} capital insuficiente, {n_simples_warn} alerta Simples, {n_mei_warn} alerta MEI")

    # E5: Collect all competitive intel contracts for dispute stats
    all_competitive_contracts: list[dict] = []

    for ed in editais:
        # --- Classify edital object type for per-edital sector override ---
        edital_object_type = classify_edital_object_type(ed)
        # Use edital's object type for habilitação/risk/cost when available,
        # fall back to company's CNAE-based sector_key when classification is empty
        effective_sk = edital_object_type if edital_object_type else sector_key
        ed["_effective_sector_key"] = effective_sk

        # --- Core scoring chain ---
        rs = compute_risk_score(ed, empresa, sicaf, effective_sk)

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
            if maturity["profile"] == "ENTRANTE" and (valor or 0) > _MATURITY_HIGH_VALUE_THRESHOLD:
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
                ed, empresa, ed.get("competitive_intel", []), effective_sk, rs["total"],
            )
            ed["win_probability"] = win_prob

            ed["roi_potential"] = compute_roi_potential(ed, effective_sk, win_prob)
            ed["cronograma"] = build_reverse_chronogram(ed)

        # --- Object compatibility (spectral) ---
        objeto = ed.get("objeto", ed.get("objetoCompra", ""))
        ed["object_compatibility"] = compute_object_compatibility(
            objeto, empresa_cnaes, sector_key, historico,
        )

        # --- Habilitação gap analysis (uses EDITAL's effective sector, not company's) ---
        ed["habilitacao_analysis"] = compute_habilitacao_analysis(
            ed, empresa, sicaf, effective_sk,
        )

        # --- E4: Qualification gap analysis (sector compat vs operational) ---
        ed["qualification_gap"] = compute_qualification_gap_analysis(
            ed, empresa, ed["object_compatibility"], effective_sk,
        )

        # --- Competitive analysis (per-edital) ---
        contracts = ed.get("competitive_intel", [])
        ed["competitive_analysis"] = compute_competitive_analysis(contracts)
        all_competitive_contracts.extend(contracts)

        # --- E6: Organ risk profile ---
        ed["organ_risk"] = compute_organ_risk_profile(ed, contracts, effective_sk)

        # --- Systemic risk flags (uses EDITAL's effective sector) ---
        ed["risk_analysis"] = compute_risk_analysis(
            ed, ed["competitive_analysis"], effective_sk,
        )

    # --- Portfolio analysis (cross-edital, sets ed["strategic_category"]) ---
    portfolio = compute_portfolio_analysis(editais, empresa, sector_key)

    # --- Portfolio optimization (capacity → correlation → optimal set) ---
    if not skip_portfolio_optimization:
        print("  [PORTFOLIO] Otimizando portfólio de participações...")
        capacity = estimate_operational_capacity(empresa, maturity)
        print(f"    Capacidade: {capacity['max_simultaneous_bids']} simultâneas, "
              f"valor máx: {_fmt_brl_portfolio(capacity['max_portfolio_value'])}")

        correlation = calculate_portfolio_correlation(editais)
        print(f"    Diversificação: {correlation['diversification_score']:.2f} "
              f"({len(correlation['correlated_groups'])} grupos correlacionados, "
              f"{correlation['n_independent']} independentes)")

        part_cost = portfolio.get("participation_cost_per_edital", 3000.0)
        optimal = optimize_portfolio(editais, capacity, correlation, part_cost)
        n_optimal = len(optimal.get("optimal_set", []))
        print(f"    Set ótimo: {n_optimal} editais, "
              f"ROI esperado: {_fmt_brl_portfolio(optimal['total_expected_roi'])}, "
              f"utilização: {optimal['capacity_utilization_pct']:.0f}%")
        if optimal.get("capacity_overflow_warning"):
            print(f"    ⚠ {optimal['capacity_overflow_warning']}")

        portfolio["capacity"] = capacity
        portfolio["correlation"] = correlation
        portfolio["optimal_set"] = optimal

    # --- E5: Historical dispute stats (aggregate) ---
    dispute_stats = compute_historical_dispute_stats(all_competitive_contracts)

    # --- E7: Regional cluster analysis ---
    regional_clusters = compute_regional_clusters(editais)
    if regional_clusters["clusters"]:
        print(f"  Clusters regionais: {len(regional_clusters['clusters'])} identificados")
        for cl in regional_clusters["clusters"]:
            print(f"    → {cl['center_municipio']}/{cl['center_uf']}: {cl['n_editais']} editais, raio {cl['radius_km']}km")

    # --- Track C: Scenarios, sensitivity analysis, and triggers ---
    enrich_scenarios_and_triggers(editais, sector_key, skip_scenarios=skip_scenarios)

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
# STRATEGIC MARKET THESIS (Track A — Big Four Intelligence)
# ============================================================

def collect_market_trend(
    api: ApiClient,
    keywords: list[str],
    ufs: list[str],
    sector_name: str,
) -> dict:
    """Query PNCP for edital volume in 3 time windows to detect market trend.

    Uses the company's top 3 UFs and 3-5 representative keywords to measure
    whether the sector is expanding, stable, or contracting.

    Returns: {volume_6m, volume_12m, volume_24m, valor_total_6m, ..., growth_rate_pct, trend}
    """
    print("\n[THESIS] Coletando tendência de mercado (PNCP volume 6m/12m/24m)")

    # Select representative keywords: top 3-5 (most specific first)
    rep_keywords = keywords[:5] if len(keywords) >= 5 else keywords[:max(1, len(keywords))]
    # Select top 3 UFs
    rep_ufs = ufs[:3] if len(ufs) >= 3 else ufs

    today = _today()
    windows = {
        "6m":  (_date_compact(today - timedelta(days=180)), _date_compact(today)),
        "12m": (_date_compact(today - timedelta(days=365)), _date_compact(today)),
        "24m": (_date_compact(today - timedelta(days=730)), _date_compact(today)),
    }

    result: dict[str, Any] = {}
    errors = 0

    for label, (dt_ini, dt_fin) in windows.items():
        vol = 0
        val_total = 0.0

        for kw in rep_keywords:
            for mod_code in [4, 5]:  # Concorrência + Pregão Eletrônico (highest volume)
                params: dict[str, Any] = {
                    "dataInicial": dt_ini,
                    "dataFinal": dt_fin,
                    "codigoModalidadeContratacao": mod_code,
                    "pagina": 1,
                    "tamanhoPagina": PNCP_MAX_PAGE_SIZE,
                }

                data, status = api.get(
                    f"{PNCP_BASE}/contratacoes/publicacao",
                    params=params,
                    label=f"PNCP trend {label} kw={kw[:15]} mod={mod_code}",
                )

                if status != "API" or not data:
                    errors += 1
                    continue

                items = data if isinstance(data, list) else data.get("data", data.get("resultado", []))
                if not isinstance(items, list):
                    continue

                # Filter by UF + keyword presence in objeto
                kw_lower = kw.lower()
                for item in items:
                    unidade = item.get("unidadeOrgao") or {}
                    uf_item = (unidade.get("ufSigla") or "").upper()
                    if rep_ufs and uf_item not in rep_ufs:
                        continue
                    objeto = (item.get("objetoCompra") or "").lower()
                    if kw_lower not in objeto:
                        continue
                    vol += 1
                    val_total += _safe_float(item.get("valorTotalEstimado")) or 0.0

                time.sleep(0.3)

        result[f"volume_{label}"] = vol
        result[f"valor_total_{label}"] = round(val_total, 2)

    # Calculate growth rate: annualized 6m vs annualized 24m
    vol_6m = result.get("volume_6m", 0)
    vol_24m = result.get("volume_24m", 0)
    vol_6m_ann = vol_6m * 2  # annualize 6-month volume

    vol_12m = result.get("volume_12m", 0)
    if vol_24m > 0:
        vol_24m_ann = vol_24m / 2  # annualize 24-month volume
        growth_rate = (vol_6m_ann - vol_24m_ann) / vol_24m_ann
    elif vol_6m > 0:
        growth_rate = 1.0  # New market (no 24m data but has 6m)
    elif vol_6m == 0 and vol_12m < 3 and vol_24m < 3:
        growth_rate = None  # No data — not stability, just absence of data
    else:
        growth_rate = 0.0

    result["growth_rate_pct"] = round(growth_rate * 100, 1) if growth_rate is not None else 0.0

    # Classify trend
    if growth_rate is None:
        trend = "DADOS_INSUFICIENTES"
    elif growth_rate > 0.15:
        trend = "EXPANSAO"
    elif growth_rate < -0.15:
        trend = "CONTRACAO"
    else:
        trend = "ESTAVEL"

    result["trend"] = trend
    result["sector_name"] = sector_name
    result["keywords_used"] = rep_keywords
    result["ufs_used"] = rep_ufs

    status_tag = "API" if errors == 0 else ("API_PARTIAL" if (vol_6m + vol_24m) > 0 else "API_FAILED")
    result["_source"] = _source_tag(
        status_tag,
        f"6m={vol_6m}, 12m={result.get('volume_12m', 0)}, 24m={vol_24m}, trend={trend}, growth={result['growth_rate_pct']}%",
    )

    growth_br = f"{result['growth_rate_pct']:.1f}".replace(".", ",")
    print(f"  Volumes: 6m={vol_6m}, 12m={result.get('volume_12m', 0)}, 24m={vol_24m}")
    print(f"  Crescimento anualizado: {growth_br}% → {trend}")
    return result


def collect_price_benchmarks(editais: list[dict]) -> dict:
    """Analyze price benchmarks from competitive_intel already collected per edital.

    For each edital that has competitive_intel with contracts: calculate avg award price
    and compare against valor_estimado.

    Returns: {avg_discount_pct, editais_with_benchmark, price_insights}
    """
    print("\n[THESIS] Calculando benchmarks de preço (editais vs contratos históricos do órgão)")

    insights: list[dict] = []
    all_discounts: list[float] = []

    for idx, ed in enumerate(editais):
        valor_est = _safe_float(ed.get("valor_estimado")) or 0.0
        if valor_est <= 0:
            continue

        # HARD-002: Use sector-filtered competitive intel for price benchmarks
        # Raw intel may include off-sector contracts with wildly different price ranges
        contracts = ed.get("competitive_intel_filtered", ed.get("competitive_intel", []))
        if not contracts:
            continue

        # Calculate average award price from competitive intel contracts
        valores_award = [(_safe_float(c.get("valor")) or 0.0) for c in contracts if (_safe_float(c.get("valor")) or 0.0) > 0]
        if not valores_award:
            continue

        avg_award = sum(valores_award) / len(valores_award)
        if avg_award <= 0:
            continue

        discount_pct = ((valor_est - avg_award) / valor_est) * 100

        # Bounds check: discard outliers where competitive intel is for a different scope
        # (e.g., org awarded R$50M contract vs. R$50k edital produces nonsensical %)
        if abs(discount_pct) > 200:
            continue

        # Outlier rejection: >60% or <-10% likely means comparing different object types
        if discount_pct > 60 or discount_pct < -10:
            discount_pct = None

        # Interpretation
        if discount_pct is None:
            interpretation = "Benchmark não disponível (dados incomparáveis)"
        elif discount_pct > 20:
            interpretation = "Margem ampla para lance agressivo"
        elif discount_pct >= 10:
            interpretation = "Desconto moderado esperado"
        else:
            interpretation = "Margens comprimidas"

        insights.append({
            "edital_idx": idx,
            "objeto": (ed.get("objeto") or "")[:80],
            "valor_estimado": valor_est,
            "avg_award_price": round(avg_award, 2),
            "discount_pct": round(discount_pct, 1) if discount_pct is not None else None,
            "n_contracts_base": len(valores_award),
            "interpretation": interpretation,
        })
        if discount_pct is not None:
            all_discounts.append(discount_pct)

    # Clamp final average to [-100, 100] to guard against any residual outliers
    raw_avg = sum(all_discounts) / len(all_discounts) if all_discounts else 0.0
    avg_discount = round(max(-100.0, min(100.0, raw_avg)), 1)

    result = {
        "avg_discount_pct": avg_discount,
        "editais_with_benchmark": len(insights),
        "price_insights": insights,
        "_source": _source_tag(
            "CALCULATED" if insights else "UNAVAILABLE",
            f"{len(insights)} editais com benchmark de preço, desconto médio {f'{avg_discount:.1f}'.replace('.', ',')}%",
        ),
    }

    avg_br = f"{avg_discount:.1f}".replace(".", ",")
    print(f"  Editais com benchmark: {len(insights)}/{len(editais)}")
    print(f"  Desconto médio estimado: {avg_br}%")
    return result


def compute_price_benchmark(editais: list[dict]) -> None:
    """GAP-3: Compute price benchmarks from competitive intelligence data (in-place).

    For each edital that has competitive_intel or competitive_intel_filtered:
    - Compute min, median, max, count of historical contract values
    - Compute suggested_range (25th-75th percentile)
    - Add price_benchmark dict to edital

    Fields added to each edital:
      price_benchmark: {
        min: float, median: float, max: float, count: int,
        p25: float, p75: float,
        suggested_range: str,  # "R$ 150.000 - R$ 280.000"
        vs_estimado: str,  # "ABAIXO" | "DENTRO" | "ACIMA" (valor_estimado vs range)
        _source: str  # "competitive_intel_filtered" or "competitive_intel"
      }
    """
    benchmarked = 0
    for ed in editais:
        # Prefer sector-filtered intel over raw intel
        source_field = "competitive_intel_filtered"
        contracts = ed.get("competitive_intel_filtered")
        if not contracts:
            source_field = "competitive_intel"
            contracts = ed.get("competitive_intel", [])

        if not contracts:
            ed["price_benchmark"] = {
                "_source": _source_tag("UNAVAILABLE", "Sem dados competitivos para benchmark"),
            }
            continue

        # Extract valid values
        valores = [
            v for c in contracts
            if (v := _safe_float(c.get("valor"))) is not None and v > 0
        ]

        if len(valores) < 2:
            ed["price_benchmark"] = {
                "_source": _source_tag("UNAVAILABLE", f"Apenas {len(valores)} valor(es) — mínimo 2 para benchmark"),
            }
            continue

        valores.sort()
        count = len(valores)
        val_min = valores[0]
        val_max = valores[-1]
        val_median = _statistics.median(valores)

        # Percentile calculation (linear interpolation)
        def _percentile(sorted_vals: list[float], pct: float) -> float:
            n = len(sorted_vals)
            idx = (n - 1) * pct / 100.0
            lo = int(idx)
            hi = min(lo + 1, n - 1)
            frac = idx - lo
            return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac

        p25 = _percentile(valores, 25)
        p75 = _percentile(valores, 75)

        suggested_range = f"R$ {_fmt_brl(p25)} - R$ {_fmt_brl(p75)}"

        # Compare valor_estimado against range
        valor_est = _safe_float(ed.get("valor_estimado")) or 0.0
        if valor_est > 0:
            if valor_est < p25:
                vs_estimado = "ABAIXO"
            elif valor_est > p75:
                vs_estimado = "ACIMA"
            else:
                vs_estimado = "DENTRO"
        else:
            vs_estimado = "NAO_DISPONIVEL"

        ed["price_benchmark"] = {
            "min": round(val_min, 2),
            "median": round(val_median, 2),
            "max": round(val_max, 2),
            "count": count,
            "p25": round(p25, 2),
            "p75": round(p75, 2),
            "suggested_range": suggested_range,
            "vs_estimado": vs_estimado,
            "_source": _source_tag("CALCULATED", f"{count} contratos via {source_field}"),
        }
        benchmarked += 1

    print(f"  [BENCHMARK] Price benchmark: {benchmarked}/{len(editais)} editais com dados suficientes")


def calculate_market_hhi(dispute_stats: dict) -> dict:
    """Calculate Herfindahl-Hirschman Index from dispute_stats.recurring_suppliers.

    HHI = sum(share_i^2) for all suppliers. Measures market concentration.

    Returns: {hhi, classification, n_suppliers, top_supplier_share}
    """
    print("\n[THESIS] Calculando HHI (concentração de mercado)")

    recurring = dispute_stats.get("recurring_suppliers", [])
    total_analyzed = dispute_stats.get("total_contracts_analyzed", 0)

    if not recurring or total_analyzed == 0:
        result = {
            "hhi": 0.0,
            "classification": "INDETERMINADO",
            "n_suppliers": 0,
            "top_supplier_share": 0.0,
            "_source": _source_tag("UNAVAILABLE", "Sem dados de fornecedores recorrentes para calcular HHI"),
        }
        print("  Dados insuficientes para cálculo de HHI")
        return result

    # Calculate HHI from market shares
    shares = [s.get("market_share", 0) for s in recurring]
    hhi = sum(s ** 2 for s in shares)

    # The shares from recurring_suppliers may not sum to 1.0 (only suppliers with 3+ contracts).
    # Remaining market share is distributed across small players, which adds minimal HHI.
    total_share_captured = sum(shares)
    if total_share_captured < 1.0:
        # Remaining share spread across many small players — negligible HHI contribution
        pass

    hhi = round(hhi, 4)
    top_share = max(shares) if shares else 0.0

    # Classification
    if hhi < 0.15:
        classification = "COMPETITIVO"
    elif hhi <= 0.25:
        classification = "MODERADO"
    else:
        classification = "CONCENTRADO"

    result = {
        "hhi": hhi,
        "classification": classification,
        "n_suppliers": len(recurring),
        "top_supplier_share": round(top_share, 3),
        "_source": _source_tag("CALCULATED", f"HHI={hhi}, {len(recurring)} fornecedores recorrentes"),
    }

    hhi_br = f"{hhi:.4f}".replace(".", ",")
    top_br = f"{top_share * 100:.1f}".replace(".", ",")
    print(f"  HHI: {hhi_br} → {classification}")
    print(f"  Fornecedores recorrentes: {len(recurring)}, maior fatia: {top_br}%")
    return result


def assemble_strategic_thesis(
    market_trend: dict,
    price_benchmarks: dict,
    market_hhi: dict,
    maturity_profile: dict,
) -> dict:
    """Combine market signals into a deterministic strategic thesis.

    Rules (no LLM):
    - EXPANDIR: trend=EXPANSAO AND (hhi=COMPETITIVO|MODERADO) AND maturity >= INTERMEDIARIA
    - REDUZIR: trend=CONTRACAO AND hhi=CONCENTRADO
    - MANTER: everything else

    Returns: {thesis, rationale, signals, confidence}
    """
    print("\n[THESIS] Montando tese estratégica")

    trend = market_trend.get("trend", "ESTAVEL")
    hhi_class = market_hhi.get("classification", "INDETERMINADO")
    maturity = maturity_profile.get("profile", "ENTRANTE")
    growth_pct = market_trend.get("growth_rate_pct", 0)
    avg_discount = price_benchmarks.get("avg_discount_pct", 0)
    hhi_val = market_hhi.get("hhi", 0)

    # Deterministic rules
    if trend == "EXPANSAO" and hhi_class in ("COMPETITIVO", "MODERADO") and maturity in ("REGIONAL", "ESTABELECIDO"):
        thesis = "EXPANDIR"
    elif trend == "CONTRACAO" and hhi_class == "CONCENTRADO":
        thesis = "REDUZIR"
    else:
        thesis = "MANTER"

    # Confidence: based on data quality
    has_trend = market_trend.get("_source", {}).get("status") != "API_FAILED"
    has_hhi = market_hhi.get("_source", {}).get("status") != "UNAVAILABLE"
    has_price = price_benchmarks.get("editais_with_benchmark", 0) > 0

    signals_available = sum([has_trend, has_hhi, has_price])
    if signals_available >= 3:
        confidence = "alta"
    elif signals_available >= 2:
        confidence = "media"
    else:
        confidence = "baixa"

    # Build rationale in Portuguese with Brazilian number formatting
    growth_br = f"{abs(growth_pct):.1f}".replace(".", ",")
    hhi_br = f"{hhi_val:.4f}".replace(".", ",")
    discount_br = f"{avg_discount:.1f}".replace(".", ",")

    rationale_parts: list[str] = []
    if trend == "DADOS_INSUFICIENTES":
        rationale_parts.append("Dados insuficientes para análise de tendência de mercado")
    elif trend == "EXPANSAO":
        rationale_parts.append(f"Mercado em expansão (crescimento de {growth_br}% anualizado)")
    elif trend == "CONTRACAO":
        rationale_parts.append(f"Mercado em contração ({growth_br}% de queda anualizada)")
    else:
        rationale_parts.append(f"Mercado estável (variação de {growth_br}%)")

    if hhi_class == "COMPETITIVO":
        rationale_parts.append(f"ambiente competitivo (HHI {hhi_br})")
    elif hhi_class == "MODERADO":
        rationale_parts.append(f"concentração moderada (HHI {hhi_br})")
    elif hhi_class == "CONCENTRADO":
        rationale_parts.append(f"mercado concentrado (HHI {hhi_br} — poucos players dominam)")
    else:
        rationale_parts.append("concentração indeterminada (dados insuficientes)")

    if has_price:
        if avg_discount is None or avg_discount > 60 or avg_discount < -10:
            rationale_parts.append("benchmark de preço não disponível (poucos contratos comparáveis)")
        elif avg_discount > 20:
            rationale_parts.append(f"desconto médio de {discount_br}% indica margens saudáveis para competir")
        elif avg_discount >= 10:
            rationale_parts.append(f"desconto médio de {discount_br}% sugere competição moderada de preço")
        else:
            rationale_parts.append(f"desconto médio de apenas {discount_br}% — margens comprimidas")

    rationale_parts.append(f"perfil de maturidade {maturity.lower()}")

    rationale = ". ".join(rationale_parts) + "."
    rationale = rationale[0].upper() + rationale[1:]  # Capitalize first letter

    result = {
        "thesis": thesis,
        "rationale": rationale,
        "signals": {
            "trend": trend,
            "growth_rate_pct": growth_pct,
            "hhi": hhi_class,
            "hhi_value": hhi_val,
            "avg_discount_pct": avg_discount,
            "maturity": maturity,
        },
        "confidence": confidence,
        "_source": _source_tag("CALCULATED", f"thesis={thesis}, confidence={confidence}"),
    }

    print(f"  Tese: {thesis} (confiança: {confidence})")
    print(f"  {rationale}")
    return result


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
# HARD-001: Semantic deduplication — extracted to report_dedup.py
# Functions: _normalize_for_dedup, _jaccard_similarity, _semantic_dedup
# ============================================================


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

    # Merge + dedup editais (PNCP priority) — HARD-001: Semantic dedup
    all_editais_raw = list(editais_pncp) + list(editais_pcp)
    # Tag sources for dedup priority
    for ed in editais_pncp:
        ed.setdefault("_source_name", "PNCP")
    for ed in editais_pcp:
        ed.setdefault("_source_name", "PCP")

    all_editais, dedup_stats = _semantic_dedup(all_editais_raw)
    pcp_dedup_count = dedup_stats["exact_removed"] + dedup_stats["semantic_removed"]
    pcp_added_count = sum(1 for ed in all_editais if ed.get("_source_name") == "PCP")

    if dedup_stats["semantic_removed"] > 0:
        print(f"  HARD-001 Semantic dedup: {dedup_stats['semantic_removed']} duplicados semânticos removidos "
              f"({dedup_stats['candidates_evaluated']} pares avaliados)")
    if dedup_stats["semantic_warnings"]:
        for w in dedup_stats["semantic_warnings"][:3]:
            print(f"    ⚠ Match zona cinzenta ({w['score']}): '{w['objeto_a'][:50]}...' vs '{w['objeto_b'][:50]}...'")


    # Update source details with dedup info (HARD-001: includes semantic dedup stats)
    if isinstance(pncp_source, dict):
        old = pncp_source.get("detail", "")
        n_pncp_final = sum(1 for ed in all_editais if ed.get("_source_name") == "PNCP")
        pncp_source["detail"] = f"{old}, {n_pncp_final} incluídos no relatório" if old else f"{n_pncp_final} editais incluídos"
    if isinstance(pcp_source, dict):
        old = pcp_source.get("detail", "")
        if editais_pcp:
            pcp_source["detail"] = (
                f"{len(editais_pcp)} obtidos, {dedup_stats['exact_removed']} duplicados exatos + "
                f"{dedup_stats['semantic_removed']} semânticos removidos, {pcp_added_count} complementares incluídos"
            )
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
            "contract_search_exhaustive": transparencia.get("_contract_search_exhaustive", True),
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
            "coverage": {
                "ufs_searched": ufs_meta.get("ufs", list(ufs_meta.get("counts", {}).keys())) if ufs_meta else [],
                "ufs_source": ufs_meta.get("source", "unknown") if ufs_meta else "unknown",
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

_TIMEOUT_REACHED = False  # F40: Global timeout flag


def main():
    global _TIMEOUT_REACHED
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
    parser.add_argument("--skip-thesis", action="store_true", help="Pular análise de tese estratégica de mercado")
    parser.add_argument("--skip-ibge", action="store_true", help="Skip IBGE enrichment")
    parser.add_argument("--skip-brasilapi", action="store_true", help="Skip BrasilAPI query")
    parser.add_argument("--skip-portfolio-optimization", action="store_true", help="Pular otimização de portfólio (capacity, correlation, optimal set)")
    parser.add_argument("--skip-scenarios", action="store_true", help="Pular cálculo de cenários, sensibilidade e triggers")
    parser.add_argument("--coverage", action="store_true", help="Habilitar diagnóstico de cobertura PNCP (112 chamadas extras — desativado por padrão)")
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

        # HARD-003: Acervo classification (re-enrich uses existing contratos)
        re_contratos = data.get("transparencia", {}).get("historico_contratos", [])
        classify_acervo_similarity(re_contratos, editais)

        # Run all deterministic computations
        skip_scen = getattr(args, "skip_scenarios", False)
        analysis_results = compute_all_deterministic(
            editais, empresa, sicaf, sector_key,
            sector_keywords=re_keywords,
            skip_scenarios=skip_scen,
        )

        # Assign recomendacao + justificativa after all scores are computed
        assign_recommendations(editais, empresa)
        compute_price_benchmark(editais)  # GAP-3
        build_alertas_criticos(editais, empresa)  # HARD-004

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
        print(f"   qualification_gap, habilitacao_analysis, object_compatibility, risk_analysis,")
        print(f"   scenarios, sensitivity, triggers")
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

    # F40: Global timeout for collection pipeline (300s = 5 minutes)
    GLOBAL_TIMEOUT_S = 300

    def _timeout_handler():
        global _TIMEOUT_REACHED
        print(f"\n⚠ Global timeout ({GLOBAL_TIMEOUT_S}s) reached. Saving partial data...")
        _TIMEOUT_REACHED = True

    _global_timer = threading.Timer(GLOBAL_TIMEOUT_S, _timeout_handler)
    _global_timer.daemon = True
    _global_timer.start()

    # ---- Phase 0: SICAF (first — user resolves captcha, then pipeline runs hands-free) ----
    # GAP-G: While user resolves SICAF captcha, start independent API calls in parallel
    print("\n\U0001f510 SICAF: Resolva o captcha agora — o restante da coleta será automático.")

    # Pre-load Portal da Transparência API key (no API call, just env var)
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

    # GAP-G Group 1: SICAF + OpenCNPJ + BrasilAPI in parallel
    # SICAF requires user interaction (captcha), while OpenCNPJ and BrasilAPI are pure API calls.
    # Running them concurrently saves ~2-5s that would otherwise be wasted waiting for captcha.
    print("  [parallel] Collecting SICAF + company profile concurrently...")
    _skip_brasilapi = hasattr(args, 'skip_brasilapi') and args.skip_brasilapi
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as g1_pool:
        future_sicaf = g1_pool.submit(collect_sicaf, cnpj14, verbose)
        future_opencnpj = g1_pool.submit(collect_opencnpj, api, cnpj14)
        if not _skip_brasilapi:
            future_brasilapi = g1_pool.submit(collect_brasilapi, api, cnpj14)

        # Wait for results — SICAF may take longest (user captcha)
        empresa = future_opencnpj.result()
        if not _skip_brasilapi:
            brasilapi = future_brasilapi.result()
        else:
            brasilapi = {"_source": _source_tag("UNAVAILABLE", "Skipped via --skip-brasilapi")}
        sicaf = future_sicaf.result()

    print("  \u2705 SICAF concluído — pipeline automático a partir daqui.\n")

    # Merge BrasilAPI data into empresa
    if not _skip_brasilapi:
        empresa["simples_nacional"] = brasilapi.get("simples_nacional")
        empresa["mei"] = brasilapi.get("mei")
        empresa["data_opcao_simples"] = brasilapi.get("data_opcao_simples", "")
        if not empresa.get("porte") and brasilapi.get("porte_fallback"):
            empresa["porte"] = brasilapi["porte_fallback"]
        # Fallback: if OpenCNPJ didn't return cidade_sede, try BrasilAPI data
        if not empresa.get("cidade_sede") and brasilapi:
            empresa["cidade_sede"] = brasilapi.get("municipio", "")
            empresa["uf_sede"] = brasilapi.get("uf", "")
            if empresa["cidade_sede"]:
                print(f"  [SEDE] Cidade obtida via BrasilAPI: {empresa['cidade_sede']}/{empresa['uf_sede']}")

    # GAP-G Group 2: Portal Transparência + PNCP Contratos in parallel
    # Both need CNPJ (available), contratos also needs razao_social from empresa (available now).
    # These two are independent of each other.
    print("  [parallel] Collecting transparency + contract history concurrently...")
    _razao_social_for_contracts = (empresa.get("razao_social") or empresa.get("nome_fantasia") or "")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as g2_pool:
        future_transparencia = g2_pool.submit(collect_portal_transparencia, api, cnpj14, pt_key)
        future_contratos = g2_pool.submit(
            collect_pncp_contratos_fornecedor, api, cnpj14,
            razao_social=_razao_social_for_contracts
        )

        transparencia = future_transparencia.result()
        pncp_contratos, pncp_contratos_source = future_contratos.result()

    # Merge sanctions into empresa for downstream
    empresa["sancoes"] = transparencia["sancoes"]

    # ---- Phase 1b: Contract History merging (data already collected in Group 2) ----
    # RATIONALE: Companies often win bids outside their CNAE classification.
    # By fetching actual contract history first, we extract keywords from what
    # the company REALLY does, then use those keywords (enriched with CNAE)
    # to search for open bids. This produces results aligned with the company's
    # actual field of work, not just their registered CNAE.
    print("\n\U0001f4cb Phase 1b: Histórico de contratos (ANTES do mapeamento de setor)")

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

    # AC4: Warn when no contracts found for an established company
    _merged_total = len(merged_contratos)
    if _merged_total == 0:
        import datetime as _dt2
        _cap = _safe_float(empresa.get("capital_social")) or 0.0
        _inicio = empresa.get("data_inicio_atividade", "") or ""
        _anos = 0
        if len(_inicio) >= 4:
            try:
                _ano_fundacao = int(_inicio[:4])
                _anos = _dt2.date.today().year - _ano_fundacao
            except (ValueError, TypeError):
                _anos = 0
        if _cap > 100_000 and _anos >= 5:
            print(
                f"  ⚠ Empresa com capital > R$100K e fundação > 5 anos mas "
                f"0 contratos encontrados — histórico pode estar incompleto"
            )
            # Mark metadata so downstream report can flag this
            transparencia["_contract_search_exhaustive"] = False
            transparencia["historico_source"] = _source_tag(
                "INCONCLUSIVE",
                "0 contratos encontrados após 4 estratégias "
                f"(capital R${_cap:,.0f}, {_anos} anos de operação)",
            )
    n_merged = len(merged_contratos)
    transparencia["historico_source"] = _source_tag(
        "API",
        f"{n_merged} contrato(s): {n_pncp} via PNCP (todas as esferas) + {n_pt} via Portal da Transparência (federal)"
    )
    print(f"  Histórico consolidado: {n_merged} contratos ({n_pncp} PNCP + {n_pt} PT)")

    # F39: Filter cancelled contracts before clustering (keep all for risk flags)
    EXCLUDED_CONTRACT_STATUSES = {"CANCELADO", "RESCINDIDO", "ANULADO"}
    active_contracts = [c for c in merged_contratos if c.get("situacao_contrato", "").upper() not in EXCLUDED_CONTRACT_STATUSES]
    n_excluded_contracts = len(merged_contratos) - len(active_contracts)
    if n_excluded_contracts > 0:
        print(f"  F39: {n_excluded_contracts} contratos cancelados/rescindidos filtrados para clustering")

    # ---- Cluster contract activities (replaces flat keyword extraction) ----
    contract_clusters = cluster_contract_activities(active_contracts)
    if contract_clusters:
        labels = [f"{c['label']}({c['count']}, {c['share_pct']}%)" for c in contract_clusters]
        print(f"  Clusters de atividade ({len(contract_clusters)}): {', '.join(labels)}")
        # Flatten keywords for backward-compatible search
        contract_keywords = extract_keywords_from_contracts(active_contracts)
        print(f"  Keywords extraídas dos clusters ({len(contract_keywords)}): {', '.join(contract_keywords[:10])}{'...' if len(contract_keywords) > 10 else ''}")
        # Build company nature profile from classified contracts (F39: uses active only)
        company_nature_profile = build_company_nature_profile(contract_clusters, active_contracts)
        if company_nature_profile:
            accepted = [f"{k}({v:.0f}%)" for k, v in company_nature_profile.items()
                        if v >= NATURE_ACCEPTANCE_THRESHOLD_PCT]
            print(f"  Perfil de natureza: {', '.join(f'{k}({v:.0f}%)' for k, v in company_nature_profile.items())}")
            print(f"  Naturezas aceitas (≥{NATURE_ACCEPTANCE_THRESHOLD_PCT:.0f}%): {', '.join(accepted) or 'TODAS'}")
    else:
        contract_keywords = []
        company_nature_profile = {}
        print("  Sem histórico de contratos — keywords serão derivadas apenas do CNAE")

    # ---- Sector Mapping (CNAE) ----
    print("\n\U0001f4cb Mapeando setor via CNAE")
    setor, cnae_keywords, sector_key = map_sector(empresa.get("cnae_principal", ""))
    print(f"  Setor: {setor}")
    print(f"  Keywords CNAE: {', '.join(cnae_keywords[:8])}{'...' if len(cnae_keywords) > 8 else ''}")

    # ---- Merge keywords: Contract history (primary) + CNAE (secondary) ----
    # Contract-derived keywords go first (higher relevance), then CNAE keywords
    # that aren't already covered by contract keywords.
    _cnae_refinement_applied: str | None = None  # Tracks whether CNAE refinement was used
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

        # Apply CNAE-specific keyword refinements for fallback mode
        cnae_raw = str(empresa.get("cnae_principal", "")).split("-")[0].split(" ")[0]
        cnae_prefix = re.sub(r"[^0-9]", "", cnae_raw)[:4]
        refinement = CNAE_KEYWORD_REFINEMENTS.get(cnae_prefix)
        if refinement:
            original_count = len(keywords)
            # Remove excluded patterns
            exclude_set = set(p.lower() for p in refinement.get("exclude_patterns", []))
            keywords = [kw for kw in keywords if kw.lower() not in exclude_set]
            excluded_count = original_count - len(keywords)
            # Add extra includes (avoid duplicates)
            existing_lower = {k.lower() for k in keywords}
            added = []
            for extra in refinement.get("extra_include", []):
                if extra.lower() not in existing_lower:
                    keywords.append(extra)
                    existing_lower.add(extra.lower())
                    added.append(extra)
            _cnae_refinement_applied = cnae_prefix
            print(f"  CNAE refinement ({cnae_prefix}): {original_count} → {len(keywords)} keywords "
                  f"(-{excluded_count} excluídas, +{len(added)} adicionadas)")
            if exclude_set:
                print(f"  Excluídas: {', '.join(sorted(exclude_set)[:5])}{'...' if len(exclude_set) > 5 else ''}")
            if added:
                print(f"  Adicionadas: {', '.join(added[:5])}{'...' if len(added) > 5 else ''}")

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
    else:
        print(f"  \U0001f4cd Cobertura geográfica: {len(ufs)} UF(s) — {', '.join(ufs)}")
        if len(ufs) > 5:
            print(f"     (>5 UFs: busca nacional com filtro client-side — considerar --ufs para focar)")

    # F40: Check global timeout before expensive phases
    if _TIMEOUT_REACHED:
        print("  \u26a0 TIMEOUT: Pulando busca de editais")
        editais_pncp, pncp_source = [], _source_tag("UNAVAILABLE", "Global timeout reached")
        editais_pcp, pcp_source = [], _source_tag("UNAVAILABLE", "Global timeout reached")
        qd_mencoes, qd_source = [], _source_tag("UNAVAILABLE", "Global timeout reached")
        # Jump to assembly
    else:
        pass  # Continue with search

    # ---- GAP-G Group 3: Edital Search — PNCP + PCP + Querido Diário in parallel ----
    # All three sources need keywords + UFs (available now) and are independent of each other.
    # If company has multiple activity clusters, use per-cluster search for PNCP.
    cluster_searches = extract_keywords_per_cluster(active_contracts, nature_profile=company_nature_profile) if active_contracts else []

    if not _TIMEOUT_REACHED:
        print("  [parallel] Collecting edital sources concurrently...")
        nome_empresa = empresa.get("nome_fantasia") or empresa.get("razao_social") or ""
        _g3_workers = 1  # At least PNCP

        # Define wrapper functions to handle skip flags and return defaults
        def _g3_collect_pncp():
            if len(cluster_searches) >= 2:
                print(f"\n[SEARCH] Empresa diversificada — {len(cluster_searches)} clusters de atividade")
                for cs in cluster_searches:
                    print(f"  \u2022 {cs['label']} ({cs['share_pct']:.0f}%) — {len(cs['keywords'])} keywords, modalidades {cs['modalidades']}")
                return collect_pncp_multi_cluster(api, cluster_searches, ufs, args.dias,
                                                  nature_profile=company_nature_profile,
                                                  sector_key=sector_key)
            else:
                return collect_pncp(api, keywords, ufs, args.dias,
                                    nature_profile=company_nature_profile,
                                    sector_key=sector_key)

        def _g3_collect_pcp():
            if args.skip_pcp:
                return [], _source_tag("UNAVAILABLE", "Skipped")
            return collect_pcp(api, keywords, ufs, args.dias)

        def _g3_collect_qd():
            if args.skip_qd:
                return [], _source_tag("UNAVAILABLE", "Skipped")
            return collect_querido_diario(api, keywords, nome_empresa, args.dias, ufs=ufs)

        if not args.skip_pcp:
            _g3_workers += 1
        if not args.skip_qd:
            _g3_workers += 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=_g3_workers) as g3_pool:
            future_pncp = g3_pool.submit(_g3_collect_pncp)
            future_pcp = g3_pool.submit(_g3_collect_pcp)
            future_qd = g3_pool.submit(_g3_collect_qd)

            editais_pncp, pncp_source = future_pncp.result()
            editais_pcp, pcp_source = future_pcp.result()
            qd_mencoes, qd_source = future_qd.result()



    # ---- Filter: remove expired editais BEFORE expensive API calls ----
    all_editais = editais_pncp + editais_pcp
    before_filter = len(all_editais)
    all_editais = [e for e in all_editais if e.get("status_edital") != "ENCERRADO"]
    editais_pncp = [e for e in editais_pncp if e.get("status_edital") != "ENCERRADO"]
    editais_pcp = [e for e in editais_pcp if e.get("status_edital") != "ENCERRADO"]
    dropped = before_filter - len(all_editais)

    # Also remove PRAZO_INDEFINIDO unless it's a credenciamento/chamada publica (continuous opportunities)
    _PRAZO_INDEF_ALLOWED = {"Credenciamento", "Chamada Pública", "Chamada Publica"}
    before_indef = len(all_editais)
    all_editais = [e for e in all_editais if e.get("status_edital") != "PRAZO_INDEFINIDO" or e.get("modalidade", "") in _PRAZO_INDEF_ALLOWED]
    editais_pncp = [e for e in editais_pncp if e.get("status_edital") != "PRAZO_INDEFINIDO" or e.get("modalidade", "") in _PRAZO_INDEF_ALLOWED]
    editais_pcp = [e for e in editais_pcp if e.get("status_edital") != "PRAZO_INDEFINIDO" or e.get("modalidade", "") in _PRAZO_INDEF_ALLOWED]
    dropped_indef = before_indef - len(all_editais)

    print(f"\n  ⚡ Removidos {dropped} encerrados + {dropped_indef} sem prazo definido (restam {len(all_editais)} abertos)")

    # Defense in depth: remove non-competitive modalidades regardless of how they entered
    # Derived from MODALIDADES_EXCLUIDAS so changes to excluded set are automatically reflected
    _MODALIDADES_BLOQUEADAS = {MODALIDADES[code] for code in MODALIDADES_EXCLUIDAS if code in MODALIDADES}
    # Also cover names not in MODALIDADES dict (e.g., code 14 "Inaplicabilidade" variants)
    _MODALIDADES_BLOQUEADAS |= {"Inaplicabilidade da Licitação", "Inaplicabilidade"}
    before_modal = len(all_editais)
    all_editais = [e for e in all_editais if e.get("modalidade", "") not in _MODALIDADES_BLOQUEADAS]
    editais_pncp = [e for e in editais_pncp if e.get("modalidade", "") not in _MODALIDADES_BLOQUEADAS]
    editais_pcp = [e for e in editais_pcp if e.get("modalidade", "") not in _MODALIDADES_BLOQUEADAS]
    dropped_modal = before_modal - len(all_editais)
    if dropped_modal:
        print(f"  ⚡ Removidos {dropped_modal} editais não competitivos (inexigibilidade/inaplicabilidade)")

    # F40: Check timeout before enrichment
    if _TIMEOUT_REACHED:
        print("\n  ⚠ TIMEOUT: Pulando enriquecimento paralelo")

    # ---- Phase 2b: Enrichment (parallel) ----
    print("\n" + "=" * 60)
    print("⚡ Phase 2b: Enriquecimento paralelo")
    print("=" * 60)

    # Pre-load caches before entering pool (cache I/O is not thread-safe on its own)
    if not args.skip_docs:
        _load_docs_cache()
    if not args.skip_competitive:
        _load_competitive_cache()

    # --- Distance calculation wrapped as a local function ---
    distancias: dict[str, dict] = {}

    def _run_distances() -> None:
        if args.skip_distances:
            return
        cidade_sede = empresa.get("cidade_sede", "")
        uf_sede = empresa.get("uf_sede", "")
        if not (cidade_sede and uf_sede):
            print("\n📍 Distâncias: cidade/UF da sede não disponível — pulando")
            return

        destinos: set = set()
        for ed in all_editais:
            mun = ed.get("municipio", "")
            uf = ed.get("uf", "")
            if mun and uf:
                destinos.add((mun, uf))

        print(f"\n📍 Calculando distâncias ({len(destinos)} destinos)")

        # Step 1: Load persistent distance cache
        dist_cache = _load_json_cache(DISTANCE_CACHE_FILE)
        origin_cache_key = f"{cidade_sede.strip().lower()}|{uf_sede.strip().upper()}"
        cached_count = 0
        uncached_destinos: list[tuple[str, str]] = []

        for mun, uf in sorted(destinos):
            dest_cache_key = f"{mun.strip().lower()}|{uf.strip().upper()}"
            full_key = f"{origin_cache_key}→{dest_cache_key}"
            if full_key in dist_cache:
                distancias[f"{mun}|{uf}"] = dist_cache[full_key]
                cached_count += 1
            else:
                uncached_destinos.append((mun, uf))

        if cached_count:
            print(f"  ✓ {cached_count} distâncias do cache persistente")

        if uncached_destinos:
            print(f"  → {len(uncached_destinos)} novas distâncias a calcular")

            # Step 2: Geocode origin + all uncached destinations
            origin_coords = _geocode(api, cidade_sede, uf_sede)
            if origin_coords:
                dest_coords: dict[str, tuple[float, float]] = {}
                geocode_failed = 0
                for mun, uf in uncached_destinos:
                    coords = _geocode(api, mun, uf)
                    key = f"{mun}|{uf}"
                    if coords:
                        dest_coords[key] = coords
                    else:
                        geocode_failed += 1
                        distancias[key] = {
                            "km": None,
                            "duracao_horas": None,
                            "_source": _source_tag("API_FAILED", f"Geocode falhou para {mun}/{uf}"),
                        }
                if geocode_failed:
                    print(f"  ⚠ Geocode falhou para {geocode_failed} destinos")

                # Step 3: Batch OSRM Table API
                if dest_coords:
                    print(f"  → OSRM Table API: {len(dest_coords)} rotas em {(len(dest_coords) - 1) // OSRM_TABLE_BATCH_SIZE + 1} batch(es)")
                    batch_results = _calculate_distances_table(api, origin_coords, dest_coords)

                    # Merge results + update persistent cache
                    for key, result in batch_results.items():
                        distancias[key] = result
                        # Normalize key for cache
                        parts = key.split("|")
                        if len(parts) == 2:
                            norm_dest = f"{parts[0].strip().lower()}|{parts[1].strip().upper()}"
                        else:
                            norm_dest = key
                        full_key = f"{origin_cache_key}→{norm_dest}"
                        dist_cache[full_key] = result

                # Step 4: Persist both caches
                _geocode_disk_save()
                _save_json_cache(DISTANCE_CACHE_FILE, dist_cache)
                print(f"  ✓ Caches persistidos ({len(_geocode_disk_load())} geocodes, {len(dist_cache)} distâncias)")
            else:
                print(f"  ⚠ Geocode da sede falhou — pulando distâncias")
        else:
            print(f"  ✓ Todas as {cached_count} distâncias servidas do cache")

    # --- IBGE wrapped as a local function ---
    ibge_data: dict = {}

    def _run_ibge() -> None:
        if getattr(args, "skip_ibge", False):
            return
        nonlocal ibge_data
        print(f"\n  IBGE — Enriquecendo municipios")
        municipios_unicos: set = set()
        for ed in all_editais:
            mun = ed.get("municipio", "")
            uf_ed = ed.get("uf", "")
            if mun and uf_ed:
                municipios_unicos.add((mun, uf_ed))
        try:
            ibge_data = collect_ibge_batch(api, sorted(municipios_unicos))
        except Exception as e:
            print(f"  ⚠ IBGE batch falhou completamente: {e} — usando fallback individual")
            for mun, uf_ed in sorted(municipios_unicos):
                key = f"{mun}|{uf_ed}"
                try:
                    ibge_data[key] = collect_ibge_municipio(api, mun, uf_ed)
                except Exception as e2:
                    print(f"  ⚠ IBGE falhou para {mun}/{uf_ed}: {e2}")
                    ibge_data[key] = {
                        "_source": _source_tag("API_FAILED", f"Exception: {e2}"),
                        "populacao": None,
                        "pib_mil_reais": None,
                    }
                time.sleep(0.5)
        for ed in all_editais:
            mun = ed.get("municipio", "")
            uf_ed = ed.get("uf", "")
            key = f"{mun}|{uf_ed}"
            if key in ibge_data:
                ed["ibge"] = ibge_data[key]

    # --- Dispatch all enrichment phases concurrently ---
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as phase_pool:
        futures: dict[str, concurrent.futures.Future] = {}

        if not args.skip_docs:
            futures["docs"] = phase_pool.submit(collect_pncp_documents, api, all_editais)

        if not args.skip_links:
            futures["links"] = phase_pool.submit(validate_pncp_links, api, all_editais)

        if not args.skip_distances:
            futures["distances"] = phase_pool.submit(_run_distances)

        if not getattr(args, "skip_ibge", False):
            futures["ibge"] = phase_pool.submit(_run_ibge)

        if not args.skip_competitive:
            futures["competitive"] = phase_pool.submit(collect_competitive_intel, api, all_editais)

        # SICAF runs separately (uses subprocess/browser) — submitted after pool

        # Wait for all and report
        for name, fut in futures.items():
            try:
                fut.result()
                print(f"  ✅ {name} concluído")
            except Exception as e:
                print(f"  ❌ {name} falhou: {e}")

    # ---- SICAF: já coletado no Phase 0 (captcha-first UX) ----

    # NOTE: Contract history (PNCP + PT) already collected in Phase 1b (before edital search)
    # and merged into transparencia["historico_contratos"]. No need to repeat here.

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

    # AC4: contract_search_exhaustive — distinguishes "no contracts found" from "search failed"
    _pncp_contratos_status = (pncp_contratos_source or {}).get("status", "MISSING")
    _all_strategies_succeeded = _pncp_contratos_status != "API_FAILED"
    data["_metadata"]["contract_search_exhaustive"] = (
        len(merged_contratos) > 0 or _all_strategies_succeeded
    )

    # ---- HARD-003: Acervo 3-Tier Classification (before deterministic scoring) ----
    classify_acervo_similarity(merged_contratos, data["editais"])
    acervo_counts = Counter(ed.get("acervo_status", "NAO_VERIFICADO") for ed in data["editais"])
    print(f"  [ACERVO] Classificação: {dict(acervo_counts)}")

    # ---- Deterministic Calculations (risk score, ROI, chronogram, E4-E8) ----
    skip_opt = getattr(args, "skip_portfolio_optimization", False)
    skip_scen = getattr(args, "skip_scenarios", False)
    analysis_results = compute_all_deterministic(
        data["editais"], data["empresa"], sicaf, sector_key,
        sector_keywords=keywords,
        skip_portfolio_optimization=skip_opt,
        skip_scenarios=skip_scen,
    )

    # Assign recomendacao + justificativa after all scores are computed
    assign_recommendations(data["editais"], data["empresa"])

    # ---- GAP-3: Price benchmark per edital ----
    compute_price_benchmark(data["editais"])

    # ---- HARD-004: Per-edital critical alerts ----
    build_alertas_criticos(data["editais"], data["empresa"])

    # Store cross-edital analysis at top level
    data["portfolio"] = analysis_results["portfolio"]
    data["maturity_profile"] = analysis_results["maturity_profile"]
    data["dispute_stats"] = analysis_results["dispute_stats"]
    data["regional_clusters"] = analysis_results["regional_clusters"]

    # Store activity clusters and keyword source metadata
    data["activity_clusters"] = contract_clusters if contract_clusters else []
    data["_keywords_source"] = "historico" if contract_clusters else "cnae_fallback"
    if _cnae_refinement_applied:
        data["_keywords_refined"] = True
        data["_cnae_refinement_applied"] = _cnae_refinement_applied
    data["nature_profile"] = company_nature_profile if company_nature_profile else {}

    # ---- Strategic Market Thesis ----
    if not args.skip_thesis:
        print(f"\n{'='*60}")
        print("[THESIS] Analisando posicionamento estratégico...")

        # 1. Market trend (PNCP volume analysis)
        thesis_market_trend = collect_market_trend(api, keywords, ufs, setor)

        # 2. Price benchmarks (from competitive_intel already on editais)
        thesis_price_benchmarks = collect_price_benchmarks(data["editais"])

        # 3. Market HHI (from dispute_stats)
        thesis_market_hhi = calculate_market_hhi(data["dispute_stats"])

        # 4. Assemble thesis
        thesis = assemble_strategic_thesis(
            market_trend=thesis_market_trend,
            price_benchmarks=thesis_price_benchmarks,
            market_hhi=thesis_market_hhi,
            maturity_profile=data["maturity_profile"],
        )

        data["strategic_thesis"] = thesis

        # Add thesis sub-sources to metadata
        data["_metadata"]["sources"]["market_trend"] = thesis_market_trend.get("_source", {})
        data["_metadata"]["sources"]["price_benchmarks"] = thesis_price_benchmarks.get("_source", {})
        data["_metadata"]["sources"]["market_hhi"] = thesis_market_hhi.get("_source", {})
        data["_metadata"]["sources"]["strategic_thesis"] = thesis.get("_source", {})

    # ---- E3: Coverage Diagnostic (opt-in via --coverage flag) ----
    if getattr(args, "coverage", False):
        print("\n📊 Diagnóstico de cobertura")
        data["coverage_diagnostic"] = compute_coverage_diagnostic(
            api, data["editais"], keywords, ufs, sector_key,
        )
        cov = data["coverage_diagnostic"]
        if cov.get("coverage_rate") is not None:
            print(f"  Cobertura: {cov['coverage_rate']:.0%} ({cov['captured_count']}/{cov['total_estimated']})")
        else:
            print("  Cobertura: não verificável (APIs de cobertura indisponíveis)")
        if cov.get("warning"):
            print(f"  ⚠ {cov['warning']}")
    else:
        print("\n📊 Diagnóstico de cobertura: desativado (use --coverage para habilitar)")
        data["coverage_diagnostic"] = {
            "coverage_rate": None,
            "note": "Diagnóstico de cobertura desativado",
            "_source": _source_tag("UNAVAILABLE", "Use --coverage para habilitar"),
        }

    # ---- FIX 3: Generate deterministic Próximos Passos ----
    print("\n📋 Gerando plano de ação (próximos passos)...")
    proximos_passos = generate_proximos_passos(data["editais"], data["empresa"])
    data["proximos_passos"] = proximos_passos
    n_imediato = len(proximos_passos["acao_imediata"])
    n_medio = len(proximos_passos["medio_prazo"])
    n_estrat = len(proximos_passos["desenvolvimento_estrategico"])
    print(f"  Ações imediatas (≤7 dias): {n_imediato}")
    print(f"  Médio prazo (8-21 dias): {n_medio}")
    print(f"  Estratégico (22-30 dias): {n_estrat}")
    print(f"  Plano de desenvolvimento: {len(proximos_passos.get('desenvolvimento_plan', []))} categorias")
    print(f"  Checklist habilitação: {len(proximos_passos['checklist_habilitacao'])} itens")

    # ---- Output ----
    if args.output:
        output_path = Path(args.output)
    else:
        date_str = _today().strftime("%Y-%m-%d")
        output_path = Path("docs/reports") / f"data-{cnpj14}-{date_str}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # F40: Cancel global timer
    _global_timer.cancel()

    print(f"\n✅ Dados salvos em: {output_path}")
    print(f"   Editais: {len(data['editais'])} ({len(editais_pncp)} PNCP + {len(editais_pcp)} PCP)")
    print(f"   Menções QD: {len(qd_mencoes)}")
    print(f"   Distâncias: {len(distancias)}")
    if _TIMEOUT_REACHED:
        print("   ⚠ PARTIAL DATA: Global timeout was reached — some phases were skipped")
    api.print_stats()
    api.close()


if __name__ == "__main__":
    main()
