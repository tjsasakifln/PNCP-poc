#!/usr/bin/env python3
"""
Audit script: fetch real PNCP data and analyze false positives/negatives.

Usage:
    cd backend
    python scripts/audit_filter.py

Outputs:
    scripts/audit_results.json  — raw audit data
    scripts/audit_report.md     — human-readable report
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import RetryConfig, setup_logging
from pncp_client import PNCPClient
from filter import (
    KEYWORDS_UNIFORMES,
    KEYWORDS_EXCLUSAO,
    normalize_text,
    match_keywords,
    filter_licitacao,
)

setup_logging("INFO")

# --- Config ---
UFS_SAMPLE = ["SP", "MG", "RJ", "BA", "PR"]
DATE_END = date.today()
DATE_START = DATE_END - timedelta(days=15)
# Only Pregão Eletrônico (most volume)
MODALIDADES = [6]
MAX_ITEMS = 500  # cap to avoid very long runs


def fetch_raw_data() -> list[dict]:
    """Fetch raw PNCP data (all items, unfiltered)."""
    config = RetryConfig(max_retries=3, jitter=True)
    items: list[dict] = []

    with PNCPClient(config=config) as client:
        for item in client.fetch_all(
            data_inicial=DATE_START.isoformat(),
            data_final=DATE_END.isoformat(),
            ufs=UFS_SAMPLE,
            modalidades=MODALIDADES,
        ):
            items.append(item)
            if len(items) >= MAX_ITEMS:
                break

    print(f"\n=== Fetched {len(items)} raw items from PNCP ===\n")
    return items


def audit_filter(items: list[dict]) -> dict:
    """Run filter and classify each item."""
    ufs_set = set(UFS_SAMPLE)
    results = {
        "approved": [],
        "rejected_keyword": [],
        "rejected_value": [],
        "rejected_other": [],
    }

    for item in items:
        objeto = item.get("objetoCompra", "")
        valor = item.get("valorTotalEstimado")
        uf = item.get("uf", "")

        # Run keyword match separately for analysis
        kw_match, kw_found = match_keywords(objeto, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)

        # Also check if it would match WITHOUT exclusions (to detect exclusion effectiveness)
        kw_match_no_exc, kw_found_no_exc = match_keywords(objeto, KEYWORDS_UNIFORMES, None)

        # Run full filter
        approved, reason = filter_licitacao(item, ufs_set)

        entry = {
            "objeto": objeto[:300],
            "valor": valor,
            "uf": uf,
            "orgao": item.get("nomeOrgao", "")[:100],
            "approved": approved,
            "reason": reason,
            "keywords_found": kw_found,
            "keywords_without_exclusion": kw_found_no_exc,
            "blocked_by_exclusion": (not kw_match and kw_match_no_exc),
        }

        if approved:
            results["approved"].append(entry)
        elif reason and "keyword" in reason.lower():
            results["rejected_keyword"].append(entry)
        elif reason and "valor" in reason.lower():
            results["rejected_value"].append(entry)
        else:
            results["rejected_other"].append(entry)

    return results


def find_potential_false_negatives(rejected_items: list[dict]) -> list[dict]:
    """
    Scan rejected-by-keyword items for potential false negatives.
    Look for objects that mention clothing-adjacent terms not in our keyword list.
    """
    clothing_hints = [
        "epi", "equipamento de proteção individual", "equipamento de protecao individual",
        "vestir", "tecido", "malha", "algodão", "algodao", "poliéster", "poliester",
        "tnt", "não tecido", "nao tecido", "bordado", "serigrafia", "silk",
        "crachá", "cracha", "luva", "luvas", "touca", "toucas",
        "pijama", "pijamas", "roupão", "roupao", "lençol", "lencol",
        "capa de chuva", "impermeável", "impermeavel",
        "tênis", "tenis", "sandália", "sandalia", "chinelo",
        "gravata", "cinto", "suspensório", "suspensorio",
        "protetor", "manga", "perneira", "caneleira",
    ]

    potential_fn = []
    for item in rejected_items:
        obj_norm = normalize_text(item["objeto"])
        hints_found = [h for h in clothing_hints if h in obj_norm]
        if hints_found:
            item["fn_hints"] = hints_found
            potential_fn.append(item)

    return potential_fn


def find_suspicious_approvals(approved_items: list[dict]) -> list[dict]:
    """
    Scan approved items for potential false positives.
    Check if the matched keyword seems out of context.
    """
    suspicious = []
    ambiguous_keywords = {
        "camisa", "camisas", "bota", "botas", "colete", "coletes",
        "avental", "aventais", "meia", "meias", "saia", "saias",
        "boné", "bonés", "confecção", "confecções", "confeccao", "confeccoes",
        "costura", "roupa", "roupas", "blusa", "blusas",
        "calça", "calças", "bermuda", "bermudas", "sapato", "sapatos",
    }

    non_uniform_hints = [
        "roupa de cama", "roupa de mesa", "roupa hospitalar de cama",
        "colete salva", "colete balístico", "colete balistico",
        "bota de borracha", "bota de segurança", "bota de seguranca",
        "avental de chumbo", "avental radiológico", "avental radiologico",
        "material de limpeza", "material hospitalar",
        "enxoval", "cama mesa e banho", "toalha",
    ]

    for item in approved_items:
        obj_norm = normalize_text(item["objeto"])
        kw = set(item.get("keywords_found", []))

        # Flag 1: only ambiguous keywords matched
        if kw and kw.issubset(ambiguous_keywords):
            for hint in non_uniform_hints:
                if hint in obj_norm:
                    item["fp_reason"] = f"ambiguous keyword + non-uniform context: '{hint}'"
                    suspicious.append(item)
                    break

        # Flag 2: keyword matched but object is very generic
        if len(obj_norm) < 30 and kw:
            item["fp_reason"] = "very short description with keyword match"
            if item not in suspicious:
                suspicious.append(item)

    return suspicious


def generate_report(results: dict, false_negatives: list, false_positives: list) -> str:
    """Generate markdown audit report."""
    total = sum(len(v) for v in results.values())
    n_approved = len(results["approved"])
    n_rej_kw = len(results["rejected_keyword"])
    n_rej_val = len(results["rejected_value"])
    n_rej_other = len(results["rejected_other"])

    lines = [
        "# Auditoria de Filtro — Falsos Positivos/Negativos",
        "",
        f"**Data:** {date.today().isoformat()}",
        f"**Período buscado:** {DATE_START} a {DATE_END}",
        f"**UFs:** {', '.join(UFS_SAMPLE)}",
        f"**Modalidades:** {MODALIDADES}",
        "",
        "## Resumo",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
        f"| Total de itens analisados | {total} |",
        f"| Aprovados pelo filtro | {n_approved} ({100*n_approved/max(total,1):.1f}%) |",
        f"| Rejeitados por keyword | {n_rej_kw} ({100*n_rej_kw/max(total,1):.1f}%) |",
        f"| Rejeitados por valor | {n_rej_val} ({100*n_rej_val/max(total,1):.1f}%) |",
        f"| Rejeitados por outros | {n_rej_other} ({100*n_rej_other/max(total,1):.1f}%) |",
        f"| **Suspeita de falso positivo** | **{len(false_positives)}** |",
        f"| **Suspeita de falso negativo** | **{len(false_negatives)}** |",
        "",
        "## Itens Aprovados (amostra)",
        "",
    ]

    for i, item in enumerate(results["approved"][:30]):
        lines.append(f"### {i+1}. {item['uf']} — R$ {item['valor']:,.2f}" if item['valor'] else f"### {i+1}. {item['uf']}")
        lines.append(f"**Objeto:** {item['objeto'][:200]}")
        lines.append(f"**Keywords:** {', '.join(item['keywords_found'])}")
        lines.append(f"**Órgão:** {item['orgao']}")
        lines.append("")

    lines.append("## Suspeitas de Falso Positivo")
    lines.append("")

    if false_positives:
        for i, item in enumerate(false_positives[:20]):
            lines.append(f"### FP-{i+1}. {item['uf']}")
            lines.append(f"**Objeto:** {item['objeto'][:200]}")
            lines.append(f"**Keywords matched:** {', '.join(item['keywords_found'])}")
            lines.append(f"**Razão da suspeita:** {item.get('fp_reason', 'N/A')}")
            lines.append("")
    else:
        lines.append("Nenhuma suspeita detectada automaticamente.")
        lines.append("")

    lines.append("## Suspeitas de Falso Negativo")
    lines.append("")

    if false_negatives:
        for i, item in enumerate(false_negatives[:30]):
            lines.append(f"### FN-{i+1}. {item['uf']}")
            lines.append(f"**Objeto:** {item['objeto'][:200]}")
            lines.append(f"**Hints encontrados:** {', '.join(item.get('fn_hints', []))}")
            lines.append(f"**Bloqueado por exclusão:** {'Sim' if item.get('blocked_by_exclusion') else 'Não'}")
            lines.append("")
    else:
        lines.append("Nenhuma suspeita detectada automaticamente.")
        lines.append("")

    # Keyword frequency analysis
    lines.append("## Frequência de Keywords nos Aprovados")
    lines.append("")
    kw_freq: dict[str, int] = {}
    for item in results["approved"]:
        for kw in item["keywords_found"]:
            kw_freq[kw] = kw_freq.get(kw, 0) + 1
    for kw, count in sorted(kw_freq.items(), key=lambda x: -x[1])[:20]:
        lines.append(f"- **{kw}**: {count}x")
    lines.append("")

    # Blocked by exclusion analysis
    blocked = [item for item in results["rejected_keyword"] if item.get("blocked_by_exclusion")]
    if blocked:
        lines.append("## Itens Bloqueados por Exclusão (teriam matchado sem exclusão)")
        lines.append("")
        for i, item in enumerate(blocked[:20]):
            lines.append(f"### EXC-{i+1}. {item['uf']}")
            lines.append(f"**Objeto:** {item['objeto'][:200]}")
            lines.append(f"**Keywords que teriam matchado:** {', '.join(item.get('keywords_without_exclusion', []))}")
            lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("  AUDITORIA DE FILTRO — FALSOS POSITIVOS/NEGATIVOS")
    print("=" * 60)

    # Step 1: Fetch
    items = fetch_raw_data()
    if not items:
        print("ERRO: Nenhum item retornado do PNCP. Verifique conectividade.")
        sys.exit(1)

    # Step 2: Audit
    results = audit_filter(items)

    # Step 3: Detect anomalies
    false_negatives = find_potential_false_negatives(results["rejected_keyword"])
    false_positives = find_suspicious_approvals(results["approved"])

    # Step 4: Save results
    output_dir = Path(__file__).parent

    with open(output_dir / "audit_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nRaw results saved to: {output_dir / 'audit_results.json'}")

    report = generate_report(results, false_negatives, false_positives)
    with open(output_dir / "audit_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved to: {output_dir / 'audit_report.md'}")

    # Summary
    total = sum(len(v) for v in results.values())
    print(f"\n{'='*60}")
    print("  RESUMO")
    print(f"{'='*60}")
    print(f"  Total analisados:           {total}")
    print(f"  Aprovados:                  {len(results['approved'])}")
    print(f"  Rejeitados (keyword):       {len(results['rejected_keyword'])}")
    print(f"  Rejeitados (valor):         {len(results['rejected_value'])}")
    print(f"  Suspeita falso positivo:    {len(false_positives)}")
    print(f"  Suspeita falso negativo:    {len(false_negatives)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
