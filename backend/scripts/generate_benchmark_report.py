#!/usr/bin/env python3
"""CRIT-FLT-009: Generate precision/recall benchmark report.

Runs the keyword matching pipeline against the ground truth dataset
and generates a Markdown report at docs/audit/precision-recall-benchmark-YYYY-MM-DD.md

Usage:
    python scripts/generate_benchmark_report.py
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from filter import match_keywords
from sectors import SECTORS, get_sector

# Import ground truth from test file
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests"))
from test_precision_recall_benchmark import GROUND_TRUTH, ALL_SECTORS


def check_match(sector_id: str, objeto: str) -> Tuple[bool, List[str]]:
    """Run match_keywords for a sector against a procurement description."""
    sector = get_sector(sector_id)
    matched, keywords = match_keywords(
        objeto=objeto,
        keywords=sector.keywords,
        exclusions=sector.exclusions,
        context_required=sector.context_required_keywords,
    )
    return matched, keywords


def calculate_metrics(sector_id: str) -> Dict:
    """Calculate precision/recall metrics for a sector."""
    gt = GROUND_TRUTH[sector_id]
    tp = fp = fn = tn = 0
    fp_items = []
    fn_items = []

    for item in gt["relevant"]:
        matched, kws = check_match(sector_id, item)
        if matched:
            tp += 1
        else:
            fn += 1
            fn_items.append(item)

    for item in gt["irrelevant"]:
        matched, kws = check_match(sector_id, item)
        if matched:
            fp += 1
            fp_items.append({"objeto": item, "matched_keywords": kws})
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall,
        "fp_items": fp_items, "fn_items": fn_items,
        "sample_size": len(gt["relevant"]) + len(gt["irrelevant"]),
    }


def calculate_cross_sector_collisions() -> Tuple[float, Dict]:
    """Calculate cross-sector collision rate."""
    total_items = 0
    cross_sector_matches = 0
    collision_pairs: Dict = {}

    for sector_id, gt in GROUND_TRUTH.items():
        for item in gt["relevant"]:
            total_items += 1
            for other_id in ALL_SECTORS:
                if other_id == sector_id:
                    continue
                matched, _ = check_match(other_id, item)
                if matched:
                    cross_sector_matches += 1
                    pair = tuple(sorted([sector_id, other_id]))
                    collision_pairs[pair] = collision_pairs.get(pair, 0) + 1
                    break  # Count once per item

    collision_rate = cross_sector_matches / total_items if total_items > 0 else 0
    return collision_rate, collision_pairs


def generate_report() -> str:
    """Generate the full Markdown report."""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    lines = []
    lines.append(f"# CRIT-FLT-009: Precision/Recall Benchmark — {date_str}")
    lines.append("")
    lines.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Pipeline:** Keyword matching (`filter.py:match_keywords`)")
    lines.append(f"**Dataset:** 450 labeled procurement descriptions (15 relevant + 15 irrelevant per sector)")
    lines.append(f"**Sectors:** {len(ALL_SECTORS)}")
    lines.append("")

    # Targets
    lines.append("## Targets")
    lines.append("")
    lines.append("| Metric | Minimum | Ideal |")
    lines.append("|--------|---------|-------|")
    lines.append("| Precision | >= 85% | >= 95% |")
    lines.append("| Recall | >= 70% | >= 85% |")
    lines.append("| Cross-sector FP rate | < 30% | < 10% |")
    lines.append("")

    # Consolidated table
    lines.append("## Consolidated Results")
    lines.append("")
    lines.append("| Sector | Precision | Recall | TP | FP | FN | TN | Sample | Status |")
    lines.append("|--------|-----------|--------|----|----|----|----|--------|--------|")

    all_results = {}
    total_tp = total_fp = total_fn = total_tn = 0
    all_pass = True

    for sector_id in ALL_SECTORS:
        result = calculate_metrics(sector_id)
        all_results[sector_id] = result
        total_tp += result["tp"]
        total_fp += result["fp"]
        total_fn += result["fn"]
        total_tn += result["tn"]

        status = "PASS" if result["precision"] >= 0.85 and result["recall"] >= 0.70 else "FAIL"
        if status == "FAIL":
            all_pass = False

        sector = get_sector(sector_id)
        lines.append(
            f"| {sector.name} (`{sector_id}`) "
            f"| {result['precision']:.1%} "
            f"| {result['recall']:.1%} "
            f"| {result['tp']} "
            f"| {result['fp']} "
            f"| {result['fn']} "
            f"| {result['tn']} "
            f"| {result['sample_size']} "
            f"| **{status}** |"
        )

    # Aggregates
    agg_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 1.0
    agg_rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 1.0
    total_sample = sum(r["sample_size"] for r in all_results.values())
    lines.append(
        f"| **AGGREGATE** "
        f"| **{agg_prec:.1%}** "
        f"| **{agg_rec:.1%}** "
        f"| **{total_tp}** "
        f"| **{total_fp}** "
        f"| **{total_fn}** "
        f"| **{total_tn}** "
        f"| **{total_sample}** "
        f"| **{'ALL PASS' if all_pass else 'HAS FAILURES'}** |"
    )
    lines.append("")

    passing = sum(
        1 for r in all_results.values()
        if r["precision"] >= 0.85 and r["recall"] >= 0.70
    )
    lines.append(f"**Sectors passing:** {passing}/{len(ALL_SECTORS)}")
    lines.append(f"**Aggregate precision:** {agg_prec:.1%}")
    lines.append(f"**Aggregate recall:** {agg_rec:.1%}")
    lines.append("")

    # Cross-sector collisions
    collision_rate, collision_pairs = calculate_cross_sector_collisions()
    lines.append("## Cross-Sector Collision Analysis")
    lines.append("")
    lines.append(f"**Collision rate:** {collision_rate:.1%}")
    lines.append("")
    lines.append("Cross-sector overlap is expected behavior — real procurement descriptions")
    lines.append("naturally mention multiple domains (e.g., \"construção de UBS\" matches both")
    lines.append("engenharia and saúde). In the live pipeline, users search for ONE sector at")
    lines.append("a time, so cross-sector matches don't affect user-facing precision.")
    lines.append("")

    if collision_pairs:
        lines.append("### Top Collision Pairs")
        lines.append("")
        lines.append("| Sector A | Sector B | Items |")
        lines.append("|----------|----------|-------|")
        for pair, count in sorted(collision_pairs.items(), key=lambda x: -x[1])[:15]:
            lines.append(f"| `{pair[0]}` | `{pair[1]}` | {count} |")
        lines.append("")

    # Per-sector detail
    lines.append("## Per-Sector Detail")
    lines.append("")

    for sector_id in ALL_SECTORS:
        result = all_results[sector_id]
        sector = get_sector(sector_id)
        lines.append(f"### {sector.name} (`{sector_id}`)")
        lines.append("")
        lines.append(f"- **Precision:** {result['precision']:.1%}")
        lines.append(f"- **Recall:** {result['recall']:.1%}")
        lines.append(f"- **Keywords:** {len(sector.keywords)}")
        lines.append(f"- **Exclusions:** {len(sector.exclusions)}")
        lines.append(f"- **Context gates:** {len(sector.context_required_keywords)}")
        lines.append("")

        if result["fp_items"]:
            lines.append("**False Positives:**")
            for fp in result["fp_items"][:5]:
                lines.append(f"- `{fp['objeto'][:100]}` → matched: {fp['matched_keywords']}")
            lines.append("")

        if result["fn_items"]:
            lines.append("**False Negatives:**")
            for fn_item in result["fn_items"][:5]:
                lines.append(f"- `{fn_item[:100]}`")
            lines.append("")

        if not result["fp_items"] and not result["fn_items"]:
            lines.append("**No false positives or false negatives detected.**")
            lines.append("")

    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append("1. **Dataset:** 450 manually curated procurement descriptions (30 per sector)")
    lines.append("2. **Pipeline:** `filter.py:match_keywords()` — keyword matching with exclusions, context gates, and word boundaries")
    lines.append("3. **Classification:** Each item labeled as relevant (should match) or irrelevant (should not match)")
    lines.append("4. **Metrics:** Precision = TP/(TP+FP), Recall = TP/(TP+FN)")
    lines.append("5. **Threshold:** Precision >= 85%, Recall >= 70% per sector")
    lines.append("")
    lines.append("## Changes Made (CRIT-FLT-009)")
    lines.append("")
    lines.append("### sectors_data.yaml")
    lines.append("")
    lines.append("1. **alimentos:** Added 8 animal feed exclusions (ração, alimentos para animais, etc.)")
    lines.append("2. **engenharia_rodoviaria:** Added 14 traffic infrastructure keywords (rotatória, semáforo, ciclovia, etc.)")
    lines.append("3. **materiais_hidraulicos:** Added 16 plural form keywords (tubos PVC, torneiras, mangueiras, etc.)")
    lines.append("4. **facilities:** Added 10 services keywords (copeiragem, dedetização, lavanderia, etc.)")
    lines.append("5. **facilities:** Removed pest control terms from exclusions (they are legitimate facilities services)")
    lines.append("6. **manutencao_predial:** Added 9 building maintenance keywords (esquadrias, pintura interna/externa, etc.)")
    lines.append("")
    lines.append("### Tests")
    lines.append("")
    lines.append("- `backend/tests/test_precision_recall_benchmark.py` — 78 tests (15 parametrized + 63 edge cases)")
    lines.append("- Ground truth: 450 labeled items (15 relevant + 15 irrelevant × 15 sectors)")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by `scripts/generate_benchmark_report.py` on {date_str}*")

    return "\n".join(lines)


if __name__ == "__main__":
    report = generate_report()

    # Ensure output directory exists
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "audit"
    )
    os.makedirs(output_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(output_dir, f"precision-recall-benchmark-{date_str}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report written to: {output_path}")
    print(f"Report size: {len(report)} bytes")
