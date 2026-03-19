#!/usr/bin/env python3
"""intel-llm-gate.py — Gate de ruído: classifica editais ambíguos por keyword matching.

Usage:
    python scripts/intel-llm-gate.py --input docs/intel/intel-CNPJ-slug-YYYY-MM-DD.json
    python scripts/intel-llm-gate.py --input data.json --neg-keywords-file my_neg.yaml

The script loads sector keywords dynamically from backend/sectors_data.yaml based on
the sector_keys stored in the JSON (data["busca"]["sector_keys"]).
Falls back to the built-in POS_KW list if sectors_data.yaml is not found.
"""

import argparse
import json
import sys
from pathlib import Path

# ============================================================
# UNIVERSAL NEGATIVE KEYWORDS (never construction/engineering,
# regardless of sector — applies to ALL companies by default)
# ============================================================

NEG_KW_DEFAULT = [
    "aliment", "refeic", "merenda", "genero", "pereciv", "cesta basica", "carne",
    "medicament", "farmac", "hospitalar", "ambulatori", "medico", "saude", "enfermag",
    "odontolog", "laboratori", "protese", "curativo", "ortoped", "colostomia", "nutric",
    "formula", "contraste", "hemoderivado", "oxigenio",
    "veiculo zero", "automovel", "van/", "minibus",
    "aquisicao de caminho", "aquisicao de veiculo", "aquisicao de onibus",
    "combustivel", "gasolina", "diesel", "etanol", "lubrificant", "pneu",
    "informatica", "computador", "notebook", "software", "tecnologia da informac",
    "impressora", "servidor de", "antivirus", "telecom", "telefon", "internet",
    "switch", " tic", "transceptor",
    "mobiliario", "movel", "cadeira", "mesa de escritorio", "estante", "armario",
    "uniforme", "vestuario", "calcado", "epi ",
    "seguro ", "seguradora", "apolice",
    "vigilancia", "vigia", "monitorament", "cftv", "alarme", "videomonitor",
    "transporte escolar", "transporte coletivo", "frete", "servico de transporte",
    "publicidade", "propaganda", "comunicacao visual", "sonorizac",
    "locacao de som", "trelica",
    "contabil", "auditoria", "consultoria em", "assessoria jur",
    "educacao", "capacitacao", "treinamento", "curso", "didatico", "educacional",
    "fornecimento de agua", "energia eletrica", "gas canalizado",
    "cartao", "vale transporte", "vale alimentac", "vale refeic",
    "locacao de veiculo", "locacao de automovel", "locacao de onibus",
    "papelaria", "material de escritorio", "expediente",
    "veterinar", "racao", "animal",
    "lavanderia", "roupa",
    "brinquedo",
    "grafica", "material grafico",
    "condicionad", "refrigerac",
    "ginastica", "academia",
    "foto", "filmagem",
    "pecas e acessorios", "pecas para",
    "material esportivo", "esportivo",
    "terceirizad",
    "residuo solido", "coleta de residuo", "coleta de lixo",
    "mecanica", "borracharia",
    "marcenaria", "divisoria", "cortina",
    "sinalizacao", "placa de sinalizacao",
    "servicos medicos", "atendimento medico", "plantao",
    "teleatendimento", "telemedicina",
]

# Built-in POS_KW fallback (used when sectors_data.yaml is unavailable)
POS_KW_FALLBACK = [
    "obra", "construc", "edificac", "edificio", "predio",
    "reform", "ampliac", "revitaliz", "requalific", "restaurac",
    "paviment", "asfalto", "recapeamento", "terraplanag", "drenag",
    "saneamento", "esgoto", "rede de agua", "abastecimento de agua",
    "ponte", "pontilh", "viaduto", "passarela",
    "calcad", "meio-fio", "meio fio", "sarjeta",
    "muro de", "cerca de", "cercamento", "alambrado",
    "telhado", "cobertura", "fachada", "pintura predial", "impermeabiliz",
    "demolicao", "demolir",
    "instalac hidraul", "instalac eletric", "instalac sanitar",
    "rede eletrica", "iluminacao publica",
    "manutencao predial", "conservacao predial",
    "manutencao de via", "manutenc de via", "manutencao em via",
    "tapa-buraco", "tapa buraco",
    "deck", "trapiche", "pier",
    "quadra esportiva", "ginasio esportivo",
    "habitac", "casa popular", "moradia",
    "concreto", "argamassa", "cimento", "tijolo", "bloco de concreto",
    "tubo de", "tubulac", "pead", "pvc ",
    "paisag", "jardinag", "arborizac", "podas",
    "limpeza urbana", "limpeza publica", "capina", "rocada",
    "contencao", "muro de arrimo", "gabiao", "geotextil",
    "estrada", "rodovia", "acostamento",
    "infraestrutura", "urbaniz",
    "galeria", "bueiro", "bocas de lobo",
    "aterro", "escavac", "movimentacao de terra",
    "piso", "revestimento", "porcelanato", "ceramica",
    "estrutura metalica", "estrutura de aco",
    "engenharia", "projeto basico", "projeto executivo",
    "topografia", "levantamento topog", "sondagem",
    "limpeza de terreno", "desmatamento", "supressao vegetal",
    "locacao de maquina", "hora maquina", "hora/maquina", "horas maquina",
    "escavadeira", "retroescavadeira", "rolo compactador", "motoniveladora",
    "caminhao basculante", "caminhao pipa",
    "melhoramento fluvial", "dragag", "desassoreamento",
    "poco artesiano", "pocos artesianos", "perfuracao de poco",
    "gramado sintetico", "campo sintetico",
    "tinta", "materiais eletric",
    "lona", "telha", "cumeeira",
    "vias e logradouro", "logradouros publicos",
    "maquinas pesadas",
    "servicos de manutencao",
]


# ============================================================
# SECTOR KEYWORD LOADER
# ============================================================

def _load_sectors_yaml() -> dict:
    """Load sectors_data.yaml from the backend directory.

    Returns parsed YAML dict, or empty dict on failure.
    """
    try:
        import yaml
    except ImportError:
        return {}

    candidates = [
        Path(__file__).resolve().parent.parent / "backend" / "sectors_data.yaml",
        Path("backend") / "sectors_data.yaml",
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                pass
    return {}


def _build_pos_kw_from_sectors(sector_keys: list[str], sectors_yaml: dict) -> list[str]:
    """Collect keywords for the given sector keys from sectors_data.yaml.

    Returns a deduplicated list of lowercase keyword strings.
    """
    sectors = sectors_yaml.get("sectors", {})
    collected: list[str] = []
    matched_keys: list[str] = []

    for key in sector_keys:
        sector = sectors.get(key)
        if sector and isinstance(sector.get("keywords"), list):
            kws = [str(k).lower() for k in sector["keywords"] if k]
            collected.extend(kws)
            matched_keys.append(key)

    # Deduplicate preserving order
    seen: set[str] = set()
    result: list[str] = []
    for kw in collected:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)

    return result, matched_keys


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Gate de ruído: reclassifica editais 'needs_llm_review' por keyword matching.",
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="JSON de entrada (output do intel-collect.py / intel-llm-classify.py)",
    )
    parser.add_argument(
        "--neg-keywords-file", default=None,
        help="YAML com lista 'neg_keywords' customizada (substitui a lista universal padrão)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Arquivo não encontrado: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ── Load negative keywords ──
    if args.neg_keywords_file:
        try:
            import yaml
            with open(args.neg_keywords_file, "r", encoding="utf-8") as nf:
                neg_data = yaml.safe_load(nf) or {}
            NEG_KW = [str(k).lower() for k in neg_data.get("neg_keywords", []) if k]
            print(f"Negative keywords: {len(NEG_KW)} loaded from {args.neg_keywords_file}")
        except Exception as e:
            print(f"WARNING: Falha ao carregar --neg-keywords-file: {e} — usando lista universal padrão")
            NEG_KW = NEG_KW_DEFAULT
    else:
        NEG_KW = NEG_KW_DEFAULT

    # ── Load positive keywords (dynamic from sector_keys) ──
    sector_keys = data.get("busca", {}).get("sector_keys", [])
    sectors_yaml = _load_sectors_yaml()
    POS_KW = []
    matched_keys = []

    if sector_keys and sectors_yaml:
        POS_KW, matched_keys = _build_pos_kw_from_sectors(sector_keys, sectors_yaml)
        if POS_KW:
            print(f"Positive keywords: {len(POS_KW)} loaded from sectors_data.yaml "
                  f"(sectors: {', '.join(matched_keys)})")
        else:
            print(f"WARNING: Sector keys {sector_keys} não encontrados em sectors_data.yaml "
                  "— usando lista fallback embutida")
            POS_KW = POS_KW_FALLBACK
    else:
        if not sectors_yaml:
            print("WARNING: sectors_data.yaml não encontrado — usando lista fallback embutida")
        else:
            print("WARNING: sector_keys não encontrado no JSON — usando lista fallback embutida")
        POS_KW = POS_KW_FALLBACK

    # ── Gate logic ──
    llm_review = [e for e in data["editais"] if e.get("needs_llm_review")]
    print(f"\nPending LLM review: {len(llm_review)}")

    compat_count = 0
    incompat_count = 0

    for e in llm_review:
        obj = (e.get("objeto", "") or "").lower()
        is_neg = any(kw in obj for kw in NEG_KW)
        is_pos = any(kw in obj for kw in POS_KW)

        if is_pos and not is_neg:
            e["cnae_compatible"] = True
            e["needs_llm_review"] = False
            e["llm_review_result"] = "compatible_keyword_v2"
            compat_count += 1
        else:
            # Conservative: zero noise > zero loss
            e["cnae_compatible"] = False
            e["needs_llm_review"] = False
            e["llm_review_result"] = "incompatible_conservative"
            incompat_count += 1

    total_compat = sum(1 for e in data["editais"] if e.get("cnae_compatible"))
    total_incompat = sum(1 for e in data["editais"] if not e.get("cnae_compatible"))
    still_review = sum(1 for e in data["editais"] if e.get("needs_llm_review"))

    print(f"\nV2 pass results:")
    print(f"  New compatible:   {compat_count}")
    print(f"  New incompatible: {incompat_count}")
    print(f"\nFinal totals:")
    print(f"  Total compatible:   {total_compat}")
    print(f"  Total incompatible: {total_incompat}")
    print(f"  Still needs review: {still_review}")

    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nJSON atualizado: {input_path}")

    # Show top compatible by value
    compat = sorted(
        [e for e in data["editais"] if e.get("cnae_compatible")],
        key=lambda x: float(x.get("valor_estimado") or 0),
        reverse=True,
    )
    print(f"\n--- Top 30 compativeis por valor ---")
    for i, e in enumerate(compat[:30]):
        val = float(e.get("valor_estimado", 0) or 0)
        obj = (e.get("objeto", "") or "")[:130]
        print(f"{i+1:3d}. [{e['uf']}] R${val:>14,.2f} | {obj}")


if __name__ == "__main__":
    main()
