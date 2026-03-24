"""
Build proposta JSON for any CNPJ — company profile + service presentation only.

NO edital searches, NO market metrics, NO PNCP queries.
The proposal sells the monitoring SERVICE, not specific opportunities.

Usage:
    python scripts/build-proposta-data.py 09225035000101
    python scripts/build-proposta-data.py 09225035000101 --pacote semanal
"""

import argparse
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRASILAPI_CNPJ = "https://brasilapi.com.br/api/cnpj/v1"
REQUEST_TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (SmartLic/1.0)"

# Sector-agnostic authority examples
AUTORIDADE_EXEMPLOS = [
    (
        "Análise de centenas de processos licitatórios — identificação dos "
        "documentos que pregoeiros verificam primeiro e onde a maioria das "
        "inabilitações acontecem"
    ),
    (
        "Conhecimento dos critérios não escritos das comissões: como avaliam "
        "atestados, o que configura experiência similar, quando uma exigência "
        "é restritiva o suficiente para impugnar"
    ),
    (
        "Acompanhamento de dezenas de contratos públicos — conhecimento de "
        "quais órgãos pagam em dia e como funciona o fluxo real de medição "
        "e pagamento"
    ),
    (
        "Identificação de cláusulas restritivas disfarçadas: requisitos de "
        "capital desproporcionais, índices contábeis eliminatórios, exigências "
        "de atestado acima do razoável"
    ),
]

# Geographic neighbors for each Brazilian UF
UF_NEIGHBORS: dict[str, list[str]] = {
    "AC": ["AM", "RO"],
    "AL": ["PE", "SE", "BA"],
    "AM": ["AC", "RO", "RR", "PA", "MT"],
    "AP": ["PA"],
    "BA": ["MG", "GO", "TO", "PI", "PE", "AL", "SE", "ES"],
    "CE": ["PI", "RN", "PB", "PE"],
    "DF": ["GO", "MG"],
    "ES": ["MG", "BA", "RJ"],
    "GO": ["MG", "BA", "TO", "MT", "MS", "DF"],
    "MA": ["PI", "TO", "PA"],
    "MG": ["ES", "RJ", "SP", "BA", "GO", "DF", "MS"],
    "MS": ["MT", "GO", "MG", "SP", "PR"],
    "MT": ["AM", "PA", "TO", "GO", "MS", "RO"],
    "PA": ["AM", "MT", "TO", "MA", "AP", "RR"],
    "PB": ["RN", "CE", "PE"],
    "PE": ["PB", "CE", "PI", "AL", "BA"],
    "PI": ["MA", "CE", "PE", "BA", "TO"],
    "PR": ["SP", "SC", "MS"],
    "RJ": ["MG", "ES", "SP"],
    "RN": ["CE", "PB"],
    "RO": ["AC", "AM", "MT"],
    "RR": ["AM", "PA"],
    "RS": ["SC"],
    "SC": ["PR", "RS"],
    "SE": ["AL", "BA"],
    "SP": ["MG", "RJ", "PR", "MS"],
    "TO": ["MA", "PI", "BA", "GO", "MT", "PA"],
}

# Extended CNAE→sector mapping (4-digit prefix → sector key in sectors_data.yaml)
CNAE_TO_SECTOR: dict[str, str] = {
    # Vestuário
    "4781": "vestuario", "1412": "vestuario", "1411": "vestuario",
    "1413": "vestuario", "1414": "vestuario",
    # Alimentos
    "1011": "alimentos", "1091": "alimentos", "1092": "alimentos",
    "1093": "alimentos", "5611": "alimentos", "5612": "alimentos",
    "5620": "alimentos",
    # Informática / TI
    "6201": "informatica", "6202": "informatica", "6203": "informatica",
    "6204": "informatica", "4751": "informatica",
    # Software
    "6209": "software", "6311": "software",
    # Engenharia / Construção
    "4120": "engenharia", "4211": "engenharia", "4212": "engenharia",
    "4213": "engenharia", "4221": "engenharia", "4222": "engenharia",
    "4223": "engenharia", "4291": "engenharia", "4292": "engenharia",
    "4299": "engenharia", "4311": "engenharia", "4312": "engenharia",
    "4313": "engenharia", "4319": "engenharia", "4321": "engenharia",
    "4322": "engenharia", "4329": "engenharia", "4330": "engenharia",
    "4391": "engenharia", "4399": "engenharia", "7111": "engenharia",
    "7112": "engenharia",
    # Facilities
    "8121": "facilities", "8122": "facilities", "8129": "facilities",
    "8130": "facilities",
    # Vigilância / Segurança
    "8011": "vigilancia", "8012": "vigilancia", "8020": "vigilancia",
    # Saúde
    "8610": "saude", "8621": "saude", "8622": "saude", "8630": "saude",
    "3250": "saude", "4644": "saude", "4645": "saude", "4664": "saude",
    # Transporte
    "4921": "transporte", "4922": "transporte", "4923": "transporte",
    "4930": "transporte", "4950": "transporte",
    # Mobiliário
    "3101": "mobiliario", "3102": "mobiliario", "3103": "mobiliario",
    "3104": "mobiliario",
    # Papelaria / Material de Escritório
    "4761": "papelaria", "1710": "papelaria", "1721": "papelaria",
    # Manutenção Predial
    "8111": "manutencao_predial",
    # Materiais Elétricos
    "2710": "materiais_eletricos", "2731": "materiais_eletricos",
    "2732": "materiais_eletricos", "2733": "materiais_eletricos",
    "4742": "materiais_eletricos",
    # Materiais Hidráulicos
    "2223": "materiais_hidraulicos", "4744": "materiais_hidraulicos",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _http_get_json(url: str) -> dict | list | None:
    """Fetch JSON from URL, return None on error."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [WARN] HTTP error: {e}")
        return None


def _extract_cnae_prefix(cnae_str: str) -> str:
    """Extract first 4 digits from a CNAE code string."""
    digits = ""
    for ch in cnae_str.strip():
        if ch.isdigit():
            digits += ch
            if len(digits) == 4:
                return digits
    return digits


def _load_sectors_yaml() -> dict:
    """Load sectors_data.yaml from the backend directory."""
    yaml_path = Path(__file__).resolve().parent.parent / "backend" / "sectors_data.yaml"
    if not yaml_path.exists():
        print(f"  [WARN] sectors_data.yaml not found at {yaml_path}")
        return {}
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("sectors", {})


def _detect_sector(cnae_principal: str, sectors: dict) -> tuple[str, str]:
    """Detect sector from CNAE principal code. Returns (sector_key, sector_name)."""
    prefix = _extract_cnae_prefix(cnae_principal)
    sector_key = CNAE_TO_SECTOR.get(prefix)

    if sector_key and sector_key in sectors:
        sec = sectors[sector_key]
        return sector_key, sec["name"]

    # Fallback: extract name from CNAE description
    desc_part = cnae_principal.split("-", 1)[1].strip() if "-" in cnae_principal else ""
    sector_name = desc_part or "Geral"
    return "generico", sector_name


def _uf_abrangencia(uf_sede: str) -> dict[str, list[str]]:
    """Build UF coverage for semanal (sede + 2 neighbors) and diario (sede + 4)."""
    neighbors = UF_NEIGHBORS.get(uf_sede, [])
    semanal = [uf_sede] + neighbors[:2]
    diario = [uf_sede] + neighbors[:4]
    return {"semanal": semanal, "diario": diario}


# ---------------------------------------------------------------------------
# Data collection (company profile only — NO edital searches)
# ---------------------------------------------------------------------------


def fetch_empresa(cnpj: str) -> dict:
    """Fetch company data from BrasilAPI."""
    print(f"Fetching empresa {cnpj} from BrasilAPI...")
    data = _http_get_json(f"{BRASILAPI_CNPJ}/{cnpj}")
    if not data:
        print("  [ERROR] Could not fetch empresa data. Using minimal fallback.")
        return {"cnpj": cnpj}
    return data


# ---------------------------------------------------------------------------
# JSON building
# ---------------------------------------------------------------------------


def build_proposta_json(cnpj: str, pacote: str = "semanal") -> dict:
    """Build proposta JSON — company profile + service presentation only."""
    today = datetime.now()
    sectors = _load_sectors_yaml()

    # --- Empresa ---
    emp_raw = fetch_empresa(cnpj)

    cnae_principal = emp_raw.get("cnae_fiscal_descricao", "")
    cnae_code = str(emp_raw.get("cnae_fiscal", ""))
    if cnae_code and cnae_principal:
        cnae_display = f"{cnae_code} - {cnae_principal}"
    else:
        cnae_display = cnae_principal or cnae_code or ""

    nome = (emp_raw.get("nome_fantasia") or "").strip() or emp_raw.get(
        "razao_social", "Empresa"
    )
    razao_social = emp_raw.get("razao_social", nome)
    uf_sede = emp_raw.get("uf", "SP")
    cidade_sede = emp_raw.get("municipio", "")
    capital_str = emp_raw.get("capital_social", "0")
    if isinstance(capital_str, str):
        capital = float(capital_str.replace(",", ".").replace(".", "", capital_str.count(".") - 1)) if capital_str else 0.0
    else:
        capital = float(capital_str or 0)
    porte_raw = emp_raw.get("porte", "")
    data_abertura = emp_raw.get("data_inicio_atividade", "")

    # Build QSA
    qsa = []
    for s in emp_raw.get("qsa", []):
        if isinstance(s, dict):
            qsa.append({
                "nome": s.get("nome_socio", ""),
                "qualificacao": s.get("qualificacao_socio", ""),
            })

    # CNAEs secundários
    cnaes_sec_raw = emp_raw.get("cnaes_secundarios", [])
    if isinstance(cnaes_sec_raw, list):
        cnaes_sec = ", ".join(
            str(c.get("codigo", c) if isinstance(c, dict) else c)
            for c in cnaes_sec_raw[:50]
        )
    else:
        cnaes_sec = str(cnaes_sec_raw)

    empresa = {
        "razao_social": razao_social,
        "nome_fantasia": emp_raw.get("nome_fantasia", ""),
        "cnpj": f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}",
        "cnae_principal": cnae_display,
        "cnaes_secundarios": cnaes_sec,
        "porte": porte_raw,
        "capital_social": capital,
        "natureza_juridica": emp_raw.get("natureza_juridica", ""),
        "cidade_sede": cidade_sede,
        "uf_sede": uf_sede,
        "data_abertura": data_abertura,
        "email": emp_raw.get("email", ""),
        "telefone": emp_raw.get("ddd_telefone_1", ""),
        "situacao_cadastral": emp_raw.get("descricao_situacao_cadastral", ""),
        "qsa": qsa,
        "sancoes": {"ceis": None, "cnep": None, "cepim": None, "ceaf": None},
    }

    # --- Sector detection ---
    sector_key, sector_name = _detect_sector(cnae_display, sectors)
    print(f"Detected sector: {sector_name} (key={sector_key})")

    # --- UF coverage ---
    uf_cov = _uf_abrangencia(uf_sede)

    # --- Company age ---
    try:
        abertura = datetime.strptime(data_abertura, "%Y-%m-%d")
        anos_mercado = (today - abertura).days // 365
    except Exception:
        anos_mercado = 0

    n_cnaes = len([c.strip() for c in cnaes_sec.split(",") if c.strip()]) if cnaes_sec else 0

    # --- Build output (service presentation, NO editais) ---
    output = {
        "empresa": empresa,
        "setor": sector_name,
        "setor_intro": (
            f"Como consultor especializado em licitações públicas, acompanho "
            f"diariamente o volume de contratações no setor de {sector_name}. "
            f"Identifico, para empresas como a {nome}, quais oportunidades têm "
            f"aderência real ao perfil técnico e financeiro."
        ),
        "uf_abrangencia": uf_cov,
        "taxa_vitoria_setor": 0.20,
        "autoridade_exemplos": AUTORIDADE_EXEMPLOS,
        "anos_mercado": anos_mercado,
        "n_cnaes": n_cnaes + 1,  # principal + secondary
    }

    return output


# ---------------------------------------------------------------------------
# Quality Gate
# ---------------------------------------------------------------------------


def _run_quality_gates(output: dict) -> list[str]:
    """Validate proposta data quality. Returns list of failure messages."""
    failures: list[str] = []
    emp = output.get("empresa", {})

    if not emp.get("razao_social"):
        failures.append("G1: Razão social não encontrada — dados da empresa incompletos")

    if not emp.get("cnae_principal"):
        failures.append("G2: CNAE principal não detectado — setor pode estar impreciso")

    if output.get("setor") == "Geral":
        failures.append("G3: Setor genérico — CNAE não mapeado para setor específico")

    if emp.get("situacao_cadastral", "").upper() not in ("ATIVA", ""):
        failures.append(f"G4: Empresa com situação '{emp.get('situacao_cadastral')}' — verificar antes de enviar")

    return failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build proposta JSON — company profile + service presentation."
    )
    parser.add_argument("cnpj", help="CNPJ (digits only, e.g. 09225035000101)")
    parser.add_argument(
        "--pacote",
        choices=["mensal", "semanal", "diario"],
        default="semanal",
        help="Coverage package (default: semanal)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: docs/propostas/data-{cnpj}-{date}.json)",
    )

    args = parser.parse_args()
    cnpj = args.cnpj.replace(".", "").replace("/", "").replace("-", "")

    if len(cnpj) != 14 or not cnpj.isdigit():
        print(f"ERROR: Invalid CNPJ '{args.cnpj}'. Must be 14 digits.")
        sys.exit(1)

    print(f"=== Build Proposta Data: CNPJ {cnpj} | pacote={args.pacote} ===\n")

    output = build_proposta_json(cnpj, pacote=args.pacote)

    # Quality Gate
    failures = _run_quality_gates(output)
    if failures:
        print(f"\n[QUALITY GATE] {len(failures)} alerta(s):")
        for f in failures:
            print(f"  [!]  {f}")
    else:
        print("\n[QUALITY GATE] [OK] Todas as verificações passaram")

    today = datetime.now()
    out_path = args.output or (
        f"docs/propostas/data-{cnpj}-{today.strftime('%Y-%m-%d')}.json"
    )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nJSON salvo: {out_path}")
    print(f"Setor: {output['setor']}")
    print(f"UFs: {output['uf_abrangencia']}")


if __name__ == "__main__":
    main()
