#!/usr/bin/env python3
"""
Complete Pipeline Audit — 15 sectors × 8 stages × density distributions × cross-sector analysis.

Covers CRIT-FLT-005 AC1–AC10:
  AC1: Full pipeline (8 stages + LLM + viability) for all 15 sectors
  AC2: 100+ items per sector, density distributions, classification breakdown
  AC3: Markdown report with summary table + precision/recall estimates
  AC4: Cross-sector collision analysis (pair heatmap + heuristic resolution)
  AC5: PCP v2 analysis (50 items, compare descriptions vs PNCP)
  AC6: 3 output formats (markdown, data JSON, metrics JSON)
  AC7: CI/CD threshold validation (via test_audit_pipeline.py)
  AC8: CLI: --sectors all --ufs SP,MG,RJ --days 10
  AC9: --dry-run mode using saved data
  AC10: --sector vestuario for single sector

Usage:
    cd backend
    python scripts/audit_pipeline_complete.py                                    # All 15 sectors
    python scripts/audit_pipeline_complete.py --sector vestuario                 # Single sector (AC10)
    python scripts/audit_pipeline_complete.py --sectors all --ufs SP,MG,RJ --days 10  # Custom (AC8)
    python scripts/audit_pipeline_complete.py --dry-run                          # Use saved data (AC9)
    python scripts/audit_pipeline_complete.py --dry-run --sector informatica     # Dry-run single sector

Outputs (AC6):
    scripts/audit_pipeline_report.md       — human-readable report
    scripts/audit_pipeline_data.json       — raw data for analysis
    scripts/audit_pipeline_metrics.json    — summarized metrics (CI/CD)
"""

import argparse
import json
import logging
import sys
import time
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    TERM_DENSITY_HIGH_THRESHOLD,
    TERM_DENSITY_MEDIUM_THRESHOLD,
    TERM_DENSITY_LOW_THRESHOLD,
    setup_logging,
)
from filter import (
    aplicar_todos_filtros,
    match_keywords,
    normalize_text,
)
from sectors import SECTORS, SectorConfig
from synonyms import find_synonym_matches

setup_logging("WARNING")
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_UFS = ["SP", "MG", "RJ", "BA", "PR"]
DEFAULT_DAYS = 10
DEFAULT_MODALIDADES = [6]  # Pregão Eletrônico (highest volume)
PNCP_BASE = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
PCP_V2_BASE = "https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos"
ITEMS_PER_PAGE = 50  # PNCP max
PCP_PAGE_SIZE = 10   # PCP v2 fixed

# Sector-specific false-negative hints (AC2: identifying potential false negatives)
SECTOR_FN_HINTS: dict[str, list[str]] = {
    "vestuario": ["tecido", "algodao", "poliester", "bordado", "serigrafia", "tinturaria", "costura", "malha"],
    "alimentos": ["merenda", "refeicao", "cozinha", "nutricional", "dieta", "alimentacao escolar"],
    "informatica": ["processador", "memoria", "hard disk", "ssd", "placa-mae", "placa mae"],
    "software": ["licenca", "saas", "cloud", "hospedagem", "api", "sistema de informacao"],
    "engenharia": ["projeto executivo", "art", "crea", "topografia", "projeto basico"],
    "facilities": ["limpeza", "conservacao", "jardinagem", "portaria", "zeladoria"],
    "saude": ["medicamento", "insumo hospitalar", "ambulancia", "protese", "ortese"],
    "vigilancia": ["vigilante", "cftv", "alarme", "cerca eletrica", "monitoramento"],
    "transporte_servicos": ["frete", "transporte escolar", "locacao de veiculo", "onibus", "van"],
    "frota_veicular": ["veiculo", "combustivel", "gasolina", "diesel", "pneu", "frota"],
    "mobiliario": ["cadeira", "mesa", "estante", "armario", "movel", "birô", "biro"],
    "papelaria": ["papel a4", "caneta", "toner", "cartucho", "material de escritorio"],
    "manutencao_predial": ["pintura", "hidraulica", "eletrica predial", "telhado", "impermeabilizacao"],
    "engenharia_rodoviaria": ["asfalto", "sinalizacao viaria", "guard rail", "pavimento", "rodovia"],
    "materiais_eletricos": ["cabo", "disjuntor", "quadro eletrico", "luminaria", "lampada"],
    "materiais_hidraulicos": ["tubo pvc", "registro", "valvula", "caixa dagua", "caixa d'agua"],
}


# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_pncp_items(
    ufs: list[str],
    days: int,
    max_items: int = 600,
    modalidades: list[int] | None = None,
) -> list[dict]:
    """Fetch raw PNCP items using sync PNCPClient (AC2: 100+ items)."""
    import httpx

    date_end = date.today()
    date_start = date_end - timedelta(days=days)
    mods = modalidades or DEFAULT_MODALIDADES
    items: list[dict] = []
    seen_ids: set[str] = set()

    print(f"  Fetching PNCP: {date_start} to {date_end}, UFs={ufs}, modalidades={mods}")

    for uf in ufs:
        for mod in mods:
            page = 1
            while len(items) < max_items:
                params = {
                    "dataInicial": date_start.strftime("%Y%m%d"),
                    "dataFinal": date_end.strftime("%Y%m%d"),
                    "codigoModalidadeContratacao": mod,
                    "uf": uf,
                    "pagina": page,
                    "tamanhoPagina": ITEMS_PER_PAGE,
                }
                try:
                    with httpx.Client(timeout=30) as client:
                        resp = client.get(PNCP_BASE, params=params)
                        if resp.status_code == 400:
                            break
                        resp.raise_for_status()
                        data = resp.json()

                    page_items = data.get("data", [])
                    if not page_items:
                        break

                    for item in page_items:
                        item_id = item.get("numeroControlePNCP", "") or item.get("codigoCompra", "")
                        if item_id and item_id not in seen_ids:
                            seen_ids.add(item_id)
                            item["uf"] = item.get("uf", uf)
                            items.append(item)

                    if not data.get("temProximaPagina", False):
                        break
                    page += 1
                    time.sleep(0.15)  # Rate limit
                except Exception as e:
                    logger.warning(f"PNCP fetch error UF={uf} mod={mod} page={page}: {e}")
                    break

            if len(items) >= max_items:
                break
        if len(items) >= max_items:
            break

    print(f"  Fetched {len(items)} unique PNCP items")
    return items


def fetch_pcp_v2_items(max_items: int = 50) -> list[dict]:
    """Fetch PCP v2 items for comparison (AC5)."""
    import httpx

    date_end = date.today()
    date_start = date_end - timedelta(days=10)
    items: list[dict] = []

    print(f"  Fetching PCP v2: {date_start} to {date_end}")

    params = {
        "dataInicial": date_start.isoformat(),
        "dataFinal": date_end.isoformat(),
    }

    try:
        page = 1
        while len(items) < max_items:
            params["pagina"] = page
            with httpx.Client(timeout=30) as client:
                resp = client.get(PCP_V2_BASE, params=params)
                resp.raise_for_status()
                data = resp.json()

            result = data.get("result", [])
            if not result:
                break

            for item in result:
                # Normalize to PNCP-like structure for comparison
                normalized = {
                    "objetoCompra": item.get("resumo", "") or item.get("objeto", ""),
                    "valorTotalEstimado": 0.0,  # PCP v2 has no value data
                    "uf": (item.get("endereco", {}) or {}).get("uf", ""),
                    "_source": "pcp_v2",
                    "_raw_pcp": item,
                }
                items.append(normalized)

            next_page = data.get("nextPage")
            if not next_page:
                break
            page = next_page
            time.sleep(0.2)  # Rate limit
    except Exception as e:
        logger.warning(f"PCP v2 fetch error: {e}")

    print(f"  Fetched {len(items)} PCP v2 items")
    return items


# ============================================================================
# SECTOR AUDIT (AC1, AC2)
# ============================================================================

def calculate_density(objeto: str, keywords: set[str]) -> float:
    """Calculate term density ratio for a given object description."""
    obj_norm = normalize_text(objeto)
    total_words = len(obj_norm.split())
    if total_words == 0:
        return 0.0

    term_count = 0
    for kw in keywords:
        kw_norm = normalize_text(kw)
        term_count += obj_norm.count(kw_norm)

    return term_count / total_words


def classify_density_zone(density: float) -> str:
    """Classify a density value into a zone."""
    if density > TERM_DENSITY_HIGH_THRESHOLD:
        return ">5%"
    elif density >= TERM_DENSITY_MEDIUM_THRESHOLD:
        return "2-5%"
    elif density >= TERM_DENSITY_LOW_THRESHOLD:
        return "1-2%"
    elif density > 0:
        return "<1%"
    else:
        return "0%"


def detect_false_positives(approved: list[dict], sector: SectorConfig) -> list[dict]:
    """Detect suspected false positives among approved items (AC2)."""
    suspicious = []
    for item in approved:
        obj_norm = normalize_text(item.get("objetoCompra", ""))
        kw_found = item.get("_matched_terms", [])
        density = item.get("_term_density", 0)

        reasons = []

        # FP1: Only generic keywords matched
        generic_kw = {"material", "servico", "servicos", "aquisicao", "fornecimento", "contratacao"}
        if kw_found and set(normalize_text(k) for k in kw_found).issubset(generic_kw):
            reasons.append("only_generic_keywords")

        # FP2: LLM approved with low confidence
        confidence = item.get("_confidence_score", 100)
        if confidence < 60:
            reasons.append(f"low_confidence_{confidence}")

        # FP3: Very short description
        if len(obj_norm) < 25 and density > 0:
            reasons.append("short_description")

        if reasons:
            suspicious.append({
                "objeto": item.get("objetoCompra", "")[:250],
                "density": density,
                "keywords": kw_found[:5],
                "confidence": confidence,
                "reasons": reasons,
                "relevance_source": item.get("_relevance_source", "unknown"),
            })

    return suspicious


def detect_false_negatives(
    rejected_items: list[dict],
    sector: SectorConfig,
) -> list[dict]:
    """Detect suspected false negatives among rejected items (AC2)."""
    hints = SECTOR_FN_HINTS.get(sector.id, [])
    if not hints:
        return []

    suspicious = []
    for item in rejected_items:
        obj_norm = normalize_text(item.get("objetoCompra", ""))
        hints_found = [h for h in hints if h in obj_norm]

        if hints_found:
            # Also check synonym matches
            syn_matches = find_synonym_matches(obj_norm, sector.keywords, sector.id)
            suspicious.append({
                "objeto": item.get("objetoCompra", "")[:250],
                "hints_found": hints_found,
                "synonym_matches": [f"{c}≈{s}" for c, s in syn_matches],
            })

    return suspicious


def audit_single_sector(
    items: list[dict],
    sector: SectorConfig,
    ufs: list[str],
) -> dict:
    """Run complete pipeline audit for one sector (AC1, AC2)."""
    ufs_set = set(ufs)

    # Step 1: Apply full filter pipeline
    approved, stats = aplicar_todos_filtros(
        licitacoes=items,
        ufs_selecionadas=ufs_set,
        keywords=sector.keywords,
        exclusions=sector.exclusions,
        context_required=sector.context_required_keywords or None,
        setor=sector.id,
    )

    # Step 2: Calculate density distribution for ALL items
    density_zones = Counter()
    all_densities = []
    for item in items:
        obj = item.get("objetoCompra", "")
        d = calculate_density(obj, sector.keywords)
        zone = classify_density_zone(d)
        density_zones[zone] += 1
        all_densities.append(d)

    # Step 3: Classify approved items by relevance source
    source_breakdown = Counter()
    for item in approved:
        src = item.get("_relevance_source", "keyword")
        source_breakdown[src] += 1

    # Step 4: Detect false positives/negatives
    # Build rejected list (items not in approved)
    approved_ids = {id(x) for x in approved}
    rejected = [x for x in items if id(x) not in approved_ids]

    fp_suspects = detect_false_positives(approved, sector)
    fn_suspects = detect_false_negatives(rejected, sector)

    # Step 5: Co-occurrence analysis
    co_occurrence_rejections = stats.get("co_occurrence_rejections", 0)

    # Step 6: Precision/recall estimates (heuristic)
    precision_est = 1.0 - (len(fp_suspects) / max(len(approved), 1))
    recall_est = 1.0 - (len(fn_suspects) / max(len(fn_suspects) + len(approved), 1))

    return {
        "sector_id": sector.id,
        "sector_name": sector.name,
        "total_items": len(items),
        "approved_count": len(approved),
        "rejected_count": len(rejected),
        "filter_stats": {k: v for k, v in stats.items() if isinstance(v, (int, float, bool))},
        "density_distribution": dict(density_zones),
        "source_breakdown": dict(source_breakdown),
        "co_occurrence_rejections": co_occurrence_rejections,
        "false_positive_suspects": fp_suspects[:20],
        "false_positive_count": len(fp_suspects),
        "false_negative_suspects": fn_suspects[:20],
        "false_negative_count": len(fn_suspects),
        "precision_estimated": round(precision_est, 3),
        "recall_estimated": round(recall_est, 3),
        "approved_sample": [
            {
                "objeto": a.get("objetoCompra", "")[:200],
                "valor": a.get("valorTotalEstimado"),
                "uf": a.get("uf", ""),
                "density": a.get("_term_density", 0),
                "source": a.get("_relevance_source", "keyword"),
                "confidence": a.get("_confidence_score", 0),
                "keywords": a.get("_matched_terms", [])[:5],
            }
            for a in approved[:20]
        ],
    }


# ============================================================================
# CROSS-SECTOR ANALYSIS (AC4)
# ============================================================================

def analyze_cross_sector(
    items: list[dict],
    sector_ids: list[str],
    ufs: list[str],
) -> dict:
    """Analyze items that match multiple sectors (AC4)."""
    collision_items = []
    pair_counts: Counter = Counter()
    sector_match_counts: Counter = Counter()

    for item in items:
        obj = item.get("objetoCompra", "")
        matching = []

        for sid in sector_ids:
            sector = SECTORS[sid]
            kw_match, kw_found = match_keywords(obj, sector.keywords, sector.exclusions)
            if kw_match:
                matching.append(sid)
                sector_match_counts[sid] += 1

        if len(matching) > 1:
            collision_items.append({
                "objeto": obj[:200],
                "sectors": matching,
                "sector_count": len(matching),
            })
            # Count pairs
            for i in range(len(matching)):
                for j in range(i + 1, len(matching)):
                    pair = tuple(sorted([matching[i], matching[j]]))
                    pair_counts[pair] += 1

    # Heuristic: determine "correct" sector per collision
    for item in collision_items:
        # Simple heuristic: sector with highest keyword density wins
        best_sector = None
        best_density = -1
        for sid in item["sectors"]:
            d = calculate_density(item["objeto"], SECTORS[sid].keywords)
            if d > best_density:
                best_density = d
                best_sector = sid
        item["likely_correct_sector"] = best_sector
        item["best_density"] = round(best_density, 4)

    return {
        "total_collisions": len(collision_items),
        "collision_rate": round(len(collision_items) / max(len(items), 1), 4),
        "top_collision_pairs": [
            {"pair": list(pair), "count": count}
            for pair, count in pair_counts.most_common(15)
        ],
        "collision_items_sample": collision_items[:30],
    }


# ============================================================================
# PCP V2 ANALYSIS (AC5)
# ============================================================================

def analyze_pcp_v2(
    pcp_items: list[dict],
    sector_ids: list[str],
) -> dict:
    """Analyze PCP v2 items (AC5)."""
    if not pcp_items:
        return {"skipped": True, "reason": "no_pcp_items_fetched"}

    results = {
        "total_items": len(pcp_items),
        "items_with_description": 0,
        "avg_description_length": 0,
        "valor_zero_count": 0,
        "sector_matches": {},
    }

    desc_lengths = []
    for item in pcp_items:
        obj = item.get("objetoCompra", "")
        if obj:
            results["items_with_description"] += 1
            desc_lengths.append(len(obj))
        if item.get("valorTotalEstimado", 0) == 0:
            results["valor_zero_count"] += 1

    results["avg_description_length"] = round(sum(desc_lengths) / max(len(desc_lengths), 1), 1)

    # Test density calculation with short descriptions
    short_desc_issues = 0
    for item in pcp_items:
        obj = item.get("objetoCompra", "")
        if len(obj) < 20:
            short_desc_issues += 1
    results["short_description_count"] = short_desc_issues

    # Per-sector keyword match rates
    for sid in sector_ids:
        sector = SECTORS[sid]
        matched = 0
        for item in pcp_items:
            obj = item.get("objetoCompra", "")
            kw_match, _ = match_keywords(obj, sector.keywords, sector.exclusions)
            if kw_match:
                matched += 1
        if matched > 0:
            results["sector_matches"][sid] = matched

    return results


# ============================================================================
# REPORT GENERATION (AC3, AC6)
# ============================================================================

def generate_markdown_report(
    sector_results: list[dict],
    cross_sector: dict,
    pcp_analysis: dict,
    config: dict,
) -> str:
    """Generate comprehensive markdown report (AC3)."""
    lines = [
        "# Auditoria Completa do Pipeline — 15 Setores",
        "",
        f"**Data:** {date.today().isoformat()}",
        f"**Período:** {config['days']} dias",
        f"**UFs:** {', '.join(config['ufs'])}",
        f"**Setores auditados:** {len(sector_results)}",
        f"**Total de itens PNCP:** {sector_results[0]['total_items'] if sector_results else 0}",
        "",
    ]

    # ---- Summary Table (AC3) ----
    lines.extend([
        "## Resumo por Setor",
        "",
        "| Setor | Aprov | Rej KW | Rej Dens | Rej Excl | LLM Calls | FP Susp | FN Susp | Precision | Recall |",
        "|-------|------:|-------:|---------:|---------:|----------:|--------:|--------:|----------:|-------:|",
    ])

    for r in sector_results:
        s = r["filter_stats"]
        lines.append(
            f"| {r['sector_name'][:25]} "
            f"| {r['approved_count']} "
            f"| {s.get('rejeitadas_keyword', 0)} "
            f"| {s.get('rejeitadas_baixa_densidade', 0)} "
            f"| {s.get('co_occurrence_rejections', 0)} "
            f"| {s.get('llm_arbiter_calls', 0) + s.get('llm_zero_match_calls', 0)} "
            f"| {r['false_positive_count']} "
            f"| {r['false_negative_count']} "
            f"| {r['precision_estimated']:.1%} "
            f"| {r['recall_estimated']:.1%} |"
        )

    lines.append("")

    # ---- Density Distribution (AC2) ----
    lines.extend([
        "## Distribuição de Densidade por Setor",
        "",
        "| Setor | >5% | 2-5% | 1-2% | <1% | 0% |",
        "|-------|----:|-----:|-----:|----:|---:|",
    ])

    for r in sector_results:
        dd = r["density_distribution"]
        lines.append(
            f"| {r['sector_id']} "
            f"| {dd.get('>5%', 0)} "
            f"| {dd.get('2-5%', 0)} "
            f"| {dd.get('1-2%', 0)} "
            f"| {dd.get('<1%', 0)} "
            f"| {dd.get('0%', 0)} |"
        )

    lines.append("")

    # ---- Classification Source Breakdown (AC2) ----
    lines.extend([
        "## Classificação por Fonte de Relevância",
        "",
        "| Setor | keyword | llm_standard | llm_conservative | llm_zero_match | synonym |",
        "|-------|--------:|-------------:|-----------------:|---------------:|--------:|",
    ])

    for r in sector_results:
        sb = r["source_breakdown"]
        lines.append(
            f"| {r['sector_id']} "
            f"| {sb.get('keyword', 0)} "
            f"| {sb.get('llm_standard', 0)} "
            f"| {sb.get('llm_conservative', 0)} "
            f"| {sb.get('llm_zero_match', 0)} "
            f"| {sb.get('synonym_auto_approve', 0)} |"
        )

    lines.append("")

    # ---- Cross-Sector Collisions (AC4) ----
    lines.extend([
        "## Análise Cross-Setor (AC4)",
        "",
        f"**Total de colisões:** {cross_sector.get('total_collisions', 0)}",
        f"**Taxa de colisão:** {cross_sector.get('collision_rate', 0):.2%}",
        "",
    ])

    top_pairs = cross_sector.get("top_collision_pairs", [])
    if top_pairs:
        lines.extend([
            "### Top 15 Pares com Mais Colisões",
            "",
            "| Par de Setores | Colisões |",
            "|----------------|------:|",
        ])
        for p in top_pairs:
            lines.append(f"| {p['pair'][0]} × {p['pair'][1]} | {p['count']} |")
        lines.append("")

    collision_samples = cross_sector.get("collision_items_sample", [])
    if collision_samples:
        lines.extend([
            "### Amostras de Colisões",
            "",
        ])
        for i, c in enumerate(collision_samples[:10]):
            lines.append(
                f"**{i+1}.** Setores: {', '.join(c['sectors'])} "
                f"(provável: **{c.get('likely_correct_sector', '?')}** "
                f"density={c.get('best_density', 0):.4f})"
            )
            lines.append(f"  {c['objeto'][:180]}")
            lines.append("")

    # ---- PCP v2 Analysis (AC5) ----
    lines.extend([
        "## Análise PCP v2 (AC5)",
        "",
    ])

    if pcp_analysis.get("skipped"):
        lines.append(f"Análise PCP v2 pulada: {pcp_analysis.get('reason', 'N/A')}")
    else:
        lines.extend([
            f"**Total itens PCP v2:** {pcp_analysis['total_items']}",
            f"**Com descrição:** {pcp_analysis['items_with_description']}",
            f"**Comprimento médio descrição:** {pcp_analysis['avg_description_length']} chars",
            f"**valor_estimado = 0:** {pcp_analysis['valor_zero_count']} ({100 * pcp_analysis['valor_zero_count'] / max(pcp_analysis['total_items'], 1):.0f}%)",
            f"**Descrições curtas (<20 chars):** {pcp_analysis['short_description_count']}",
            "",
        ])

        matches = pcp_analysis.get("sector_matches", {})
        if matches:
            lines.extend([
                "### Matches por Setor (PCP v2)",
                "",
                "| Setor | Items Matched |",
                "|-------|-------------:|",
            ])
            for sid, count in sorted(matches.items(), key=lambda x: -x[1]):
                lines.append(f"| {sid} | {count} |")
            lines.append("")

    # ---- Per-Sector Details ----
    lines.extend([
        "## Detalhes por Setor",
        "",
    ])

    for r in sector_results:
        lines.append(f"### {r['sector_name']} (`{r['sector_id']}`)")
        lines.append("")
        lines.append(
            f"Aprovados: {r['approved_count']} | "
            f"FP suspeitos: {r['false_positive_count']} | "
            f"FN suspeitos: {r['false_negative_count']}"
        )
        lines.append("")

        # Approved sample
        if r["approved_sample"]:
            lines.append("**Aprovados (amostra):**")
            lines.append("")
            for i, a in enumerate(r["approved_sample"][:5]):
                val = f"R$ {a['valor']:,.2f}" if a.get("valor") else "N/A"
                lines.append(
                    f"{i+1}. [{a['uf']}] {val} | "
                    f"density={a['density']:.3f} | "
                    f"src={a['source']} | "
                    f"conf={a['confidence']}"
                )
                lines.append(f"   {a['objeto'][:150]}")
                lines.append("")

        # FP suspects
        if r["false_positive_suspects"]:
            lines.append(f"**Falsos Positivos Suspeitos ({r['false_positive_count']}):**")
            lines.append("")
            for i, fp in enumerate(r["false_positive_suspects"][:5]):
                lines.append(
                    f"FP-{i+1}. reasons={fp['reasons']} | "
                    f"density={fp['density']:.3f} | "
                    f"src={fp['relevance_source']}"
                )
                lines.append(f"   {fp['objeto'][:150]}")
                lines.append("")

        # FN suspects
        if r["false_negative_suspects"]:
            lines.append(f"**Falsos Negativos Suspeitos ({r['false_negative_count']}):**")
            lines.append("")
            for i, fn in enumerate(r["false_negative_suspects"][:5]):
                lines.append(
                    f"FN-{i+1}. hints={fn['hints_found']} | "
                    f"synonyms={fn['synonym_matches']}"
                )
                lines.append(f"   {fn['objeto'][:150]}")
                lines.append("")

    return "\n".join(lines)


def build_metrics(
    sector_results: list[dict],
    cross_sector: dict,
    pcp_analysis: dict,
    elapsed_seconds: float,
) -> dict:
    """Build summarized metrics JSON for CI/CD validation (AC6, AC7)."""
    total_approved = sum(r["approved_count"] for r in sector_results)
    total_items = sector_results[0]["total_items"] if sector_results else 0
    avg_precision = (
        sum(r["precision_estimated"] for r in sector_results) / len(sector_results)
        if sector_results else 0
    )
    avg_recall = (
        sum(r["recall_estimated"] for r in sector_results) / len(sector_results)
        if sector_results else 0
    )

    per_sector = {}
    for r in sector_results:
        per_sector[r["sector_id"]] = {
            "approved": r["approved_count"],
            "false_positive_suspects": r["false_positive_count"],
            "false_negative_suspects": r["false_negative_count"],
            "precision_estimated": r["precision_estimated"],
            "recall_estimated": r["recall_estimated"],
            "density_distribution": r["density_distribution"],
            "source_breakdown": r["source_breakdown"],
        }

    return {
        "timestamp": date.today().isoformat(),
        "total_items_analyzed": total_items,
        "total_approved": total_approved,
        "sectors_audited": len(sector_results),
        "avg_precision_estimated": round(avg_precision, 3),
        "avg_recall_estimated": round(avg_recall, 3),
        "cross_sector_collision_rate": cross_sector.get("collision_rate", 0),
        "cross_sector_collisions": cross_sector.get("total_collisions", 0),
        "pcp_v2_items": pcp_analysis.get("total_items", 0),
        "elapsed_seconds": round(elapsed_seconds, 1),
        "per_sector": per_sector,
        # Thresholds for CI/CD (AC7)
        "thresholds": {
            "min_precision": 0.70,
            "min_recall": 0.50,
            "max_collision_rate": 0.15,
            "min_items_analyzed": 50,
        },
        "passes_thresholds": (
            avg_precision >= 0.70
            and avg_recall >= 0.50
            and cross_sector.get("collision_rate", 0) <= 0.15
            and total_items >= 50
        ),
    }


# ============================================================================
# MAIN
# ============================================================================

def parse_args() -> argparse.Namespace:
    """Parse CLI arguments (AC8, AC9, AC10)."""
    parser = argparse.ArgumentParser(
        description="Complete Pipeline Audit — 15 sectors × 8 stages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/audit_pipeline_complete.py                          # All 15 sectors
  python scripts/audit_pipeline_complete.py --sector vestuario       # Single sector
  python scripts/audit_pipeline_complete.py --sectors all --ufs SP,MG --days 5
  python scripts/audit_pipeline_complete.py --dry-run                # Use saved data
  python scripts/audit_pipeline_complete.py --no-pcp                 # Skip PCP v2
        """,
    )
    parser.add_argument(
        "--sectors",
        default="all",
        help="Comma-separated sector IDs or 'all' (default: all)",
    )
    parser.add_argument(
        "--sector",
        default=None,
        help="Single sector ID (shorthand for --sectors <id>)",
    )
    parser.add_argument(
        "--ufs",
        default=",".join(DEFAULT_UFS),
        help=f"Comma-separated UF codes (default: {','.join(DEFAULT_UFS)})",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"Days back to search (default: {DEFAULT_DAYS})",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=600,
        help="Max PNCP items to fetch (default: 600)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use saved data from audit_pipeline_data.json instead of fetching (AC9)",
    )
    parser.add_argument(
        "--no-pcp",
        action="store_true",
        help="Skip PCP v2 analysis",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: scripts/)",
    )

    args = parser.parse_args()

    # AC10: --sector shorthand
    if args.sector:
        args.sectors = args.sector

    return args


def resolve_sector_ids(sectors_arg: str) -> list[str]:
    """Resolve sector IDs from CLI argument."""
    if sectors_arg == "all":
        return list(SECTORS.keys())

    ids = [s.strip() for s in sectors_arg.split(",")]
    for sid in ids:
        if sid not in SECTORS:
            print(f"ERROR: Unknown sector '{sid}'. Available: {list(SECTORS.keys())}")
            sys.exit(1)
    return ids


def main():
    args = parse_args()
    sector_ids = resolve_sector_ids(args.sectors)
    ufs = [u.strip() for u in args.ufs.split(",")]
    output_dir = Path(args.output_dir) if args.output_dir else Path(__file__).parent

    print("=" * 70)
    print("  AUDITORIA COMPLETA DO PIPELINE — CRIT-FLT-005")
    print("=" * 70)
    print(f"  Setores: {len(sector_ids)} ({', '.join(sector_ids[:5])}{'...' if len(sector_ids) > 5 else ''})")
    print(f"  UFs: {ufs}")
    print(f"  Dias: {args.days}")
    print(f"  Dry-run: {args.dry_run}")
    print(f"  Max items: {args.max_items}")
    print("=" * 70)

    start_time = time.time()

    # ---- Step 1: Fetch or load data ----
    if args.dry_run:
        data_file = output_dir / "audit_pipeline_data.json"
        if not data_file.exists():
            print(f"ERROR: --dry-run requires {data_file} to exist. Run without --dry-run first.")
            sys.exit(1)
        print("\n[DRY-RUN] Loading saved data...")
        with open(data_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        # In dry-run, we re-run the analysis on saved raw items
        pncp_items = saved.get("raw_pncp_items", [])
        pcp_items = saved.get("raw_pcp_items", [])
        print(f"  Loaded {len(pncp_items)} PNCP items, {len(pcp_items)} PCP items")
    else:
        print("\n[1/5] Fetching PNCP data...")
        pncp_items = fetch_pncp_items(ufs, args.days, args.max_items)

        pcp_items = []
        if not args.no_pcp:
            print("\n[2/5] Fetching PCP v2 data...")
            pcp_items = fetch_pcp_v2_items()
        else:
            print("\n[2/5] PCP v2 skipped (--no-pcp)")

    if not pncp_items:
        print("ERROR: No PNCP items fetched. Aborting.")
        sys.exit(1)

    # ---- Step 2: Per-sector audit ----
    print(f"\n[3/5] Auditing {len(sector_ids)} sectors against {len(pncp_items)} items...")
    sector_results = []
    for i, sid in enumerate(sector_ids):
        sector = SECTORS[sid]
        print(f"  [{i+1}/{len(sector_ids)}] {sector.name}...", end=" ", flush=True)
        result = audit_single_sector(pncp_items, sector, ufs)
        sector_results.append(result)
        print(
            f"approved={result['approved_count']} "
            f"fp={result['false_positive_count']} "
            f"fn={result['false_negative_count']} "
            f"precision={result['precision_estimated']:.1%}"
        )

    # ---- Step 3: Cross-sector analysis ----
    print("\n[4/5] Cross-sector collision analysis...")
    cross_sector = analyze_cross_sector(pncp_items, sector_ids, ufs)
    print(f"  Collisions: {cross_sector['total_collisions']} ({cross_sector['collision_rate']:.2%})")

    # ---- Step 4: PCP v2 analysis ----
    print("\n[5/5] PCP v2 analysis...")
    pcp_analysis = analyze_pcp_v2(pcp_items, sector_ids)

    elapsed = time.time() - start_time

    # ---- Step 5: Generate outputs (AC6) ----
    print("\nGenerating outputs...")

    # Output 1: Markdown report (AC3)
    config_info = {"ufs": ufs, "days": args.days, "sectors": sector_ids}
    report = generate_markdown_report(sector_results, cross_sector, pcp_analysis, config_info)
    report_path = output_dir / "audit_pipeline_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  Report: {report_path}")

    # Output 2: Raw data JSON (AC6)
    data_out = {
        "raw_pncp_items": pncp_items,
        "raw_pcp_items": pcp_items,
        "sector_results": sector_results,
        "cross_sector": cross_sector,
        "pcp_analysis": pcp_analysis,
        "config": config_info,
    }
    data_path = output_dir / "audit_pipeline_data.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, indent=2, default=str)
    print(f"  Data: {data_path}")

    # Output 3: Metrics JSON (AC6, AC7)
    metrics = build_metrics(sector_results, cross_sector, pcp_analysis, elapsed)
    metrics_path = output_dir / "audit_pipeline_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"  Metrics: {metrics_path}")

    # ---- Summary ----
    print(f"\n{'=' * 70}")
    print(f"  RESUMO — {elapsed:.1f}s")
    print(f"{'=' * 70}")
    print(f"  {'Setor':<30} {'Aprov':>6} {'FP':>4} {'FN':>4} {'Prec':>6} {'Recall':>6}")
    print(f"  {'-' * 56}")
    for r in sector_results:
        print(
            f"  {r['sector_name'][:30]:<30} "
            f"{r['approved_count']:>6} "
            f"{r['false_positive_count']:>4} "
            f"{r['false_negative_count']:>4} "
            f"{r['precision_estimated']:>6.1%} "
            f"{r['recall_estimated']:>6.1%}"
        )
    print(f"  {'-' * 56}")
    print(f"  Cross-sector collisions: {cross_sector['total_collisions']} ({cross_sector['collision_rate']:.2%})")
    print(f"  PCP v2 items: {pcp_analysis.get('total_items', 0)}")
    print(f"  CI/CD thresholds: {'PASS' if metrics['passes_thresholds'] else 'FAIL'}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
