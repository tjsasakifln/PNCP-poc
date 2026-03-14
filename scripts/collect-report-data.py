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
    if status == "API" and data:
        items = data if isinstance(data, list) else data.get("data", data.get("contratos", []))
        if isinstance(items, list):
            for c in items[:20]:
                result["historico_contratos"].append({
                    "orgao": c.get("orgaoVinculado", {}).get("nome", "") or c.get("orgao", ""),
                    "valor": _safe_float(c.get("valorFinal") or c.get("valor") or c.get("valorInicial")),
                    "data": c.get("dataInicioVigencia") or c.get("dataAssinatura") or "",
                    "objeto": c.get("objeto", "")[:200],
                })
        result["historico_source"] = _source_tag("API")
    elif status == "API_FAILED":
        result["historico_source"] = _source_tag("API_FAILED", "Consulta de contratos falhou")

    return result


# ============================================================
# SECTOR MAPPING
# ============================================================

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
    elif "ATENÇÃO" in statuses:
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

    # 5. Concorrência presencial (travel cost)
    modalidade = (edital.get("modalidade") or "").lower()
    if "presencial" in modalidade:
        dist = edital.get("distancia", {})
        km = dist.get("km") if isinstance(dist, dict) else None
        if km and km > 200:
            flags.append({
                "flag": f"Licitação presencial a {km:.0f}km — custo de deslocamento relevante",
                "severity": "MEDIA",
                "category": "logistica",
            })

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

        if hab_status == "INAPTA":
            ed["strategic_category"] = "INACESSÍVEL"
            inaccessible += 1
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
                edital = _parse_pncp_item(item, keywords, ufs)
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
                          f"{source_meta['total_raw']} raw, {source_meta['total_filtered']} filtered, "
                          f"{source_meta['pages_fetched']} pages, {source_meta['errors']} errors")

    print(f"\n  PNCP: {source_meta['total_raw']} raw → {source_meta['total_filtered']} filtrados")
    return all_editais, _source


def _parse_pncp_item(item: dict, keywords: list[str], ufs: list[str]) -> dict | None:
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

    # Keyword filter (case-insensitive)
    objeto_lower = objeto.lower()
    if not any(kw.lower() in objeto_lower for kw in keywords):
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
            edital = _parse_pcp_item(item, keywords, ufs)
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
        f"{source_meta['total_raw']} raw, {source_meta['total_filtered']} filtered",
    )

    print(f"  PCP v2: {source_meta['total_raw']} raw → {source_meta['total_filtered']} filtrados")
    return all_editais, _source


def _parse_pcp_item(item: dict, keywords: list[str], ufs: list[str]) -> dict | None:
    """Parse a PCP v2 result."""
    resumo = item.get("resumo") or ""
    uc = item.get("unidadeCompradora") or {}
    uf = (uc.get("uf") or "").upper()

    if ufs and uf not in ufs:
        return None

    resumo_lower = resumo.lower()
    if not any(kw.lower() in resumo_lower for kw in keywords):
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
) -> tuple[list[dict], dict]:
    """Search municipal gazettes via Querido Diário."""
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
        data, status = api.get(
            QD_BASE,
            params={
                "querystring": q,
                "published_since": since,
                "published_until": until,
                "excerpt_size": 500,
                "number_of_excerpts": 3,
                "size": 20,
                "sort_by": "descending_date",
            },
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

    data_fim = _today()
    data_ini = data_fim - timedelta(days=meses * 30)

    # PNCP requires codigoModalidadeContratacao — iterate over useful modalities
    # 4=Concorrência, 5=Pregão Eletrônico, 6=Pregão Presencial, 8=Inexigibilidade
    _MODALIDADES_COMPETITIVAS = [5, 4, 6, 8]

    for cnpj_orgao, orgao_editais in orgao_map.items():
        orgao_nome = orgao_editais[0].get("orgao", cnpj_orgao)
        contracts: list[dict] = []

        for modalidade_cod in _MODALIDADES_COMPETITIVAS:
            for page in range(1, 3):  # Max 2 pages per modality
                data, status = api.get(
                    f"{PNCP_BASE}/contratacoes/publicacao",
                    params={
                        "dataInicial": _date_compact(data_ini),
                        "dataFinal": _date_compact(data_fim),
                        "cnpjOrgao": cnpj_orgao,
                        "codigoModalidadeContratacao": modalidade_cod,
                        "pagina": page,
                        "tamanhoPagina": PNCP_MAX_PAGE_SIZE,
                    },
                    label=f"Competitiva: {orgao_nome[:30]}... mod{modalidade_cod} p{page}",
                )

                if status != "API" or not isinstance(data, list):
                    break

                for item in data:
                    # Extract from contratos sub-array if present
                    contratos_arr = item.get("contratos") or []
                    found_contract = False
                    if contratos_arr and isinstance(contratos_arr, list):
                        for c in contratos_arr:
                            fn = c.get("nomeRazaoSocialFornecedor", "")
                            vl = _safe_float(c.get("valorFinal") or c.get("valorInicial"))
                            if fn:
                                contracts.append({
                                    "fornecedor": fn,
                                    "cnpj_fornecedor": c.get("cnpjCpfFornecedor", ""),
                                    "objeto": (item.get("objetoCompra") or "")[:150],
                                    "valor": vl,
                                    "data": c.get("dataVigenciaInicio") or item.get("dataPublicacaoPncp") or "",
                                })
                                found_contract = True

                    # Fallback: extract procurement-level data even without contratos
                    if not found_contract:
                        obj = (item.get("objetoCompra") or "")[:150]
                        val_est = _safe_float(item.get("valorTotalEstimado"))
                        val_hom = _safe_float(item.get("valorTotalHomologado"))
                        pub_date = (item.get("dataPublicacaoPncp") or "")[:10]
                        if obj and (val_est > 0 or val_hom > 0):
                            contracts.append({
                                "fornecedor": "",  # Unknown winner
                                "cnpj_fornecedor": "",
                                "objeto": obj,
                                "valor": val_hom if val_hom > 0 else val_est,
                                "valor_estimado": val_est,
                                "valor_homologado": val_hom,
                                "data": pub_date,
                            })

                if len(data) < PNCP_MAX_PAGE_SIZE:
                    break
                time.sleep(0.3)

            # Stop iterating modalities if we already have enough data
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


def compute_risk_score(edital: dict, empresa: dict, sicaf: dict, sector_key: str = "") -> dict:
    """Compute composite opportunity risk score 0-100 (higher = better opportunity).

    Uses sector-specific weight profiles from _SECTOR_WEIGHT_PROFILES.
    Components: habilitacao, financeiro, geografico, prazo, competitivo.
    """
    # Habilitação (30%)
    hab_score = 100
    sancoes = empresa.get("sancoes", {})
    if any(sancoes.get(k) for k in ["ceis", "cnep", "cepim", "ceaf"]):
        hab_score = 0  # Hard block — sanctioned company

    sicaf_status = sicaf.get("status", "NÃO CONSULTADO") if isinstance(sicaf, dict) else "NÃO CONSULTADO"
    crc = sicaf.get("crc", {}) if isinstance(sicaf, dict) else {}
    restricao = sicaf.get("restricao", {}) if isinstance(sicaf, dict) else {}

    if restricao.get("possui_restricao"):
        hab_score = min(hab_score, 30)
    elif crc.get("status_cadastral") == "CADASTRADO":
        hab_score = min(hab_score, 100)
    elif sicaf_status == "NÃO CONSULTADO":
        hab_score = min(hab_score, 60)  # Unknown = moderate risk

    capital = _safe_float(empresa.get("capital_social"))
    valor = _safe_float(edital.get("valor_estimado"))
    if valor > 0 and capital > 0:
        ratio = capital / valor
        if ratio < 0.1:  # Capital < 10% of contract
            hab_score = min(hab_score, 40)
        elif ratio < 0.3:
            hab_score = min(hab_score, 70)

    # Financeiro (25%)
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

    # Geográfico (20%)
    dist = edital.get("distancia", {})
    km = dist.get("km") if isinstance(dist, dict) else None
    if km is None:
        geo_score = 50
    elif km <= 50:
        geo_score = 100
    elif km <= 200:
        geo_score = 70
    elif km <= 500:
        geo_score = 40
    else:
        geo_score = 10

    # Prazo (15%)
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

    # Competitivo — default, refined by competitive analysis later
    comp_score = 50

    # Use sector-specific weight profile
    weights = _SECTOR_WEIGHT_PROFILES.get(sector_key, _SECTOR_WEIGHT_PROFILES["_default"])

    total = (
        hab_score * weights["hab"]
        + fin_score * weights["fin"]
        + geo_score * weights["geo"]
        + prazo_score * weights["prazo"]
        + comp_score * weights["comp"]
    )

    return {
        "total": round(total),
        "habilitacao": hab_score,
        "financeiro": fin_score,
        "geografico": geo_score,
        "prazo": prazo_score,
        "competitivo": comp_score,
        "weights": weights,
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

    Returns dict with probability (0.0-1.0), confidence, and decomposition.
    """
    base_rate = _SECTOR_BASE_WIN_RATES.get(sector_key, _SECTOR_BASE_WIN_RATES["_default"])

    # Analyze competitive landscape from historical contracts
    unique_suppliers: set[str] = set()
    supplier_counts: dict[str, int] = {}
    for c in competitive_intel:
        cnpj = (c.get("cnpj_fornecedor") or "").strip()
        name = (c.get("fornecedor") or "").strip().upper()
        key = cnpj if len(cnpj) >= 11 else name
        if key:
            unique_suppliers.add(key)
            supplier_counts[key] = supplier_counts.get(key, 0) + 1

    n_suppliers = len(unique_suppliers)
    n_contracts = len(competitive_intel)

    # HHI (Herfindahl-Hirschman Index) — 0=perfect competition, 1=monopoly
    hhi = 0.0
    top_share = 0.0
    if n_contracts > 0 and supplier_counts:
        shares = [count / n_contracts for count in supplier_counts.values()]
        hhi = sum(s ** 2 for s in shares)
        top_share = max(shares)

    # Competition-adjusted probability
    if n_suppliers == 0:
        # No data — use sector base rate
        competition_prob = base_rate
        confidence = "baixa"
    elif n_suppliers == 1:
        # Single supplier = incumbent monopoly, very hard to break in
        competition_prob = 0.05
        confidence = "media"
    elif n_suppliers <= 3:
        # Low competition
        competition_prob = 0.25
        confidence = "media"
    elif n_suppliers <= 7:
        # Moderate — fair share estimate
        competition_prob = 1.0 / n_suppliers
        confidence = "alta"
    else:
        # High competition
        competition_prob = 1.0 / n_suppliers
        confidence = "alta"

    # Incumbency bonus — does the company already supply this organ?
    empresa_cnpj = re.sub(r"[^0-9]", "", empresa.get("cnpj", ""))
    incumbency_bonus = 0.0
    if empresa_cnpj and len(empresa_cnpj) >= 11:
        for c in competitive_intel:
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

    # Viability discount — risk_score tempers probability
    # Floor at 0.3 so viability doesn't crush probability to zero
    viability_factor = max(risk_score / 100.0, 0.3)

    # Final probability with bounds
    raw_prob = competition_prob * mod_mult + incumbency_bonus
    final_prob = raw_prob * viability_factor
    final_prob = max(0.02, min(0.85, final_prob))  # Clamp [2%, 85%]

    return {
        "probability": round(final_prob, 3),
        "confidence": confidence,
        "base_rate": base_rate,
        "n_unique_suppliers": n_suppliers,
        "n_contracts_analyzed": n_contracts,
        "hhi": round(hhi, 4),
        "top_supplier_share": round(top_share, 3),
        "incumbency_bonus": incumbency_bonus,
        "modality_multiplier": mod_mult,
        "viability_factor": round(viability_factor, 2),
        "_source": _source_tag("CALCULATED", f"{n_contracts} contratos, {n_suppliers} fornecedores"),
    }


def compute_roi_potential(edital: dict, sector_key: str, win_prob: dict) -> dict:
    """Calculate ROI potential per edital.

    Formula: valor × probability × margin_range
    - probability from win_probability engine (Bayesian-inspired)
    - margin varies by sector
    """
    valor = _safe_float(edital.get("valor_estimado"))
    if valor <= 0:
        return {
            "roi_min": 0, "roi_max": 0, "probability": 0.0,
            "margin_range": "N/A",
            "confidence": win_prob.get("confidence", "baixa"),
            "_source": _source_tag("CALCULATED", "Valor estimado indisponível"),
        }

    margin_min, margin_max = _SECTOR_MARGINS.get(sector_key, (0.08, 0.15))
    probability = win_prob.get("probability", 0.10)

    return {
        "roi_min": round(valor * probability * margin_min),
        "roi_max": round(valor * probability * margin_max),
        "probability": round(probability, 3),
        "margin_range": f"{margin_min * 100:.0f}%-{margin_max * 100:.0f}%",
        "confidence": win_prob.get("confidence", "baixa"),
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


def compute_all_deterministic(
    editais: list[dict],
    empresa: dict,
    sicaf: dict,
    sector_key: str,
) -> None:
    """Compute all deterministic intelligence for editais. Mutates in place.

    Chain: risk_score → win_probability → roi_potential → chronogram
           + object_compatibility, habilitacao, competitive_analysis, risk_analysis
    Portfolio analysis runs after per-edital loop (needs aggregate view).
    """
    print(f"\n📊 Calculando inteligência estratégica ({len(editais)} editais)")

    empresa_cnaes = empresa.get("cnaes_secundarios", "")
    if isinstance(empresa_cnaes, list):
        empresa_cnaes = " ".join(str(c) for c in empresa_cnaes)
    historico = empresa.get("historico_contratos", [])

    for ed in editais:
        # --- Core scoring chain ---
        rs = compute_risk_score(ed, empresa, sicaf, sector_key)
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

        # --- Competitive analysis (per-edital) ---
        contracts = ed.get("competitive_intel", [])
        ed["competitive_analysis"] = compute_competitive_analysis(contracts)

        # --- Systemic risk flags ---
        ed["risk_analysis"] = compute_risk_analysis(
            ed, ed["competitive_analysis"], sector_key,
        )

    # --- Portfolio analysis (cross-edital, sets ed["strategic_category"]) ---
    portfolio = compute_portfolio_analysis(editais, empresa, sector_key)

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

    sicaf_script = Path(__file__).parent / "collect-sicaf.py"
    if not sicaf_script.exists():
        if verbose:
            print("  ⚠ collect-sicaf.py não encontrado — pulando SICAF")
        return {
            "status": "NÃO CONSULTADO",
            "_source": _source_tag("UNAVAILABLE", "collect-sicaf.py não encontrado"),
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
                "status": "NÃO CONSULTADO",
                "_source": _source_tag("API_FAILED", detail),
            }

        # Read the output JSON
        tmp_file = Path(tmp_path)
        if not tmp_file.exists() or tmp_file.stat().st_size == 0:
            if verbose:
                print("  ⚠ SICAF: arquivo de saída vazio")
            return {
                "status": "NÃO CONSULTADO",
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
            "status": "NÃO CONSULTADO",
            "_source": _source_tag("API_FAILED", "Timeout — captcha não resolvido em 5 min"),
        }
    except Exception as e:
        if verbose:
            print(f"  ⚠ SICAF erro: {e}")
        return {
            "status": "NÃO CONSULTADO",
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
    for ed in editais_pcp:
        if ed.get("link") not in pncp_links:
            all_editais.append(ed)

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
            },
        },
        "empresa": empresa_full,
        "setor": setor,
        "keywords": keywords,
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
    parser.add_argument("--cnpj", required=True, help="CNPJ da empresa (com ou sem formatação)")
    parser.add_argument("--dias", type=int, default=30, help="Período de busca em dias (default: 30)")
    parser.add_argument("--ufs", default="", help="UFs para filtrar, separadas por vírgula (default: UF da sede)")
    parser.add_argument("--output", help="Caminho do JSON de saída (default: auto)")
    parser.add_argument("--quiet", action="store_true", help="Suprimir output verbose")
    parser.add_argument("--skip-distances", action="store_true", help="Pular cálculo de distâncias (mais rápido)")
    parser.add_argument("--skip-docs", action="store_true", help="Pular listagem de documentos PNCP")
    parser.add_argument("--skip-links", action="store_true", help="Pular validação de links PNCP")
    parser.add_argument("--skip-pcp", action="store_true", help="Pular busca PCP v2")
    parser.add_argument("--skip-qd", action="store_true", help="Pular busca Querido Diário")
    parser.add_argument("--skip-sicaf", action="store_true", help="Pular verificação SICAF (Playwright)")
    parser.add_argument("--skip-competitive", action="store_true", help="Pular coleta de inteligência competitiva")

    args = parser.parse_args()

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

    # ---- Sector Mapping ----
    print("\n📋 Mapeando setor via CNAE")
    setor, keywords, sector_key = map_sector(empresa.get("cnae_principal", ""))
    print(f"  Setor: {setor}")
    print(f"  Keywords: {', '.join(keywords[:8])}{'...' if len(keywords) > 8 else ''}")

    # ---- UFs ----
    if args.ufs:
        ufs = [u.strip().upper() for u in args.ufs.split(",") if u.strip()]
    else:
        uf_sede = empresa.get("uf_sede", "")
        ufs = [uf_sede] if uf_sede else []
    if ufs:
        print(f"  UFs: {', '.join(ufs)}")
    else:
        print("  UFs: todas (sem filtro)")

    # ---- Phase 2a: Edital Search ----
    editais_pncp, pncp_source = collect_pncp(api, keywords, ufs, args.dias)

    editais_pcp = []
    pcp_source = _source_tag("UNAVAILABLE", "Skipped")
    if not args.skip_pcp:
        editais_pcp, pcp_source = collect_pcp(api, keywords, ufs, args.dias)

    qd_mencoes = []
    qd_source = _source_tag("UNAVAILABLE", "Skipped")
    if not args.skip_qd:
        nome_empresa = empresa.get("nome_fantasia") or empresa.get("razao_social") or ""
        qd_mencoes, qd_source = collect_querido_diario(api, keywords, nome_empresa, args.dias)

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

    # ---- SICAF ----
    if args.skip_sicaf:
        sicaf = {
            "status": "NÃO CONSULTADO",
            "_source": _source_tag("UNAVAILABLE", "Skipped via --skip-sicaf"),
        }
    else:
        sicaf = collect_sicaf(cnpj14, verbose=verbose)

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
    )

    # ---- Deterministic Calculations (risk score, ROI, chronogram) ----
    compute_all_deterministic(data["editais"], data["empresa"], sicaf, sector_key)

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
