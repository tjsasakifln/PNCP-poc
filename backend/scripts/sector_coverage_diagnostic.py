#!/usr/bin/env python3
"""
Sector Coverage Diagnostic — CRIT-FLT-007 AC1+AC2+AC3.

Parses sectors_data.yaml, synonyms.py, and filter.py to generate
a comprehensive coverage table for all 15 sectors and classify each
as Maduro (>80%), Parcial (50-80%), or Raso (<50%).

Usage:
    cd backend
    python scripts/sector_coverage_diagnostic.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from typing import Any


def load_sectors_data() -> dict:
    """Load sectors_data.yaml."""
    yaml_path = Path(__file__).resolve().parent.parent / "sectors_data.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["sectors"]


def get_synonym_sectors() -> dict[str, int]:
    """Get synonym dict coverage from synonyms.py."""
    from synonyms import SECTOR_SYNONYMS
    return {
        sector_id: len(canonical_dict)
        for sector_id, canonical_dict in SECTOR_SYNONYMS.items()
    }


def get_red_flag_exemptions() -> dict[str, list[str]]:
    """Get which sectors have red flag exemptions."""
    from filter import (
        _INFRA_EXEMPT_SECTORS,
        _MEDICAL_EXEMPT_SECTORS,
        _ADMIN_EXEMPT_SECTORS,
    )
    result: dict[str, list[str]] = {}
    for sector in _INFRA_EXEMPT_SECTORS:
        result.setdefault(sector, []).append("infrastructure")
    for sector in _MEDICAL_EXEMPT_SECTORS:
        result.setdefault(sector, []).append("medical")
    for sector in _ADMIN_EXEMPT_SECTORS:
        result.setdefault(sector, []).append("administrative")
    return result


def analyze_sector(sector_id: str, config: dict) -> dict[str, Any]:
    """Analyze a single sector's coverage layers."""
    keywords = config.get("keywords", [])
    exclusions = config.get("exclusions", [])
    context_gates = config.get("context_required_keywords", {})
    co_occurrence = config.get("co_occurrence_rules", [])
    signature_terms = config.get("signature_terms", [])
    domain_signals = config.get("domain_signals", {})

    # Domain signals breakdown
    ncm_prefixes = domain_signals.get("ncm_prefixes", [])
    unit_patterns = domain_signals.get("unit_patterns", [])
    size_patterns = domain_signals.get("size_patterns", [])

    return {
        "keywords_count": len(keywords),
        "exclusions_count": len(exclusions),
        "context_gates_count": len(context_gates),
        "co_occurrence_count": len(co_occurrence),
        "signature_terms_count": len(signature_terms),
        "has_domain_signals": bool(ncm_prefixes or unit_patterns or size_patterns),
        "ncm_count": len(ncm_prefixes),
        "unit_patterns_count": len(unit_patterns),
        "size_patterns_count": len(size_patterns),
    }


def classify_sector(analysis: dict, has_synonyms: bool, has_red_flag: bool) -> tuple[str, float]:
    """Classify sector as Maduro/Parcial/Raso based on 9-layer coverage."""
    layers_present = 0
    total_layers = 9

    # Layer 1: Keywords (always present)
    if analysis["keywords_count"] > 0:
        layers_present += 1
    # Layer 2: Exclusions (always present)
    if analysis["exclusions_count"] > 0:
        layers_present += 1
    # Layer 3: Context gates
    if analysis["context_gates_count"] > 0:
        layers_present += 1
    # Layer 4: Co-occurrence rules
    if analysis["co_occurrence_count"] > 0:
        layers_present += 1
    # Layer 5: Signature terms
    if analysis["signature_terms_count"] > 0:
        layers_present += 1
    # Layer 6: Domain signals
    if analysis["has_domain_signals"]:
        layers_present += 1
    # Layer 7: Synonym dictionaries
    if has_synonyms:
        layers_present += 1
    # Layer 8: Red flag exemptions
    if has_red_flag:
        layers_present += 1
    # Layer 9: LLM prompt examples (dynamic — always present via _build_zero_match_prompt)
    layers_present += 1

    pct = layers_present / total_layers * 100

    if pct > 80:
        return "Maduro", pct
    elif pct >= 50:
        return "Parcial", pct
    else:
        return "Raso", pct


def main():
    sectors = load_sectors_data()
    synonym_coverage = get_synonym_sectors()
    red_flag_exemptions = get_red_flag_exemptions()

    print("=" * 120)
    print("CRIT-FLT-007 — Sector Coverage Diagnostic")
    print("=" * 120)
    print()

    # Header
    header = (
        f"{'Sector':<25} {'KW':>4} {'Excl':>5} {'CTX':>4} {'CoOcc':>5} "
        f"{'Sig':>4} {'Domain':>7} {'Syn':>4} {'RFlag':>6} {'LLM':>4} "
        f"{'Score':>6} {'Class':>8}"
    )
    print(header)
    print("-" * 120)

    results = {}
    for sector_id in sorted(sectors.keys()):
        config = sectors[sector_id]
        analysis = analyze_sector(sector_id, config)
        has_synonyms = sector_id in synonym_coverage
        has_red_flag = sector_id in red_flag_exemptions

        classification, pct = classify_sector(analysis, has_synonyms, has_red_flag)

        results[sector_id] = {
            **analysis,
            "has_synonyms": has_synonyms,
            "synonym_canonicals": synonym_coverage.get(sector_id, 0),
            "has_red_flag_exemption": has_red_flag,
            "red_flag_types": red_flag_exemptions.get(sector_id, []),
            "classification": classification,
            "coverage_pct": pct,
        }

        row = (
            f"{sector_id:<25} "
            f"{analysis['keywords_count']:>4} "
            f"{analysis['exclusions_count']:>5} "
            f"{analysis['context_gates_count']:>4} "
            f"{analysis['co_occurrence_count']:>5} "
            f"{analysis['signature_terms_count']:>4} "
            f"{'Y' if analysis['has_domain_signals'] else '-':>7} "
            f"{'Y(' + str(synonym_coverage.get(sector_id, 0)) + ')' if has_synonyms else '-':>4} "
            f"{'Y' if has_red_flag else '-':>6} "
            f"{'Y':>4} "
            f"{pct:>5.0f}% "
            f"{classification:>8}"
        )
        print(row)

    print("-" * 120)

    # Summary
    maduro = [s for s, r in results.items() if r["classification"] == "Maduro"]
    parcial = [s for s, r in results.items() if r["classification"] == "Parcial"]
    raso = [s for s, r in results.items() if r["classification"] == "Raso"]

    print(f"\nMaduro ({len(maduro)}): {', '.join(maduro)}")
    print(f"Parcial ({len(parcial)}): {', '.join(parcial)}")
    print(f"Raso ({len(raso)}): {', '.join(raso) if raso else '(none)'}")

    # Missing layers detail
    print("\n" + "=" * 120)
    print("MISSING LAYERS DETAIL")
    print("=" * 120)

    for sector_id in sorted(results.keys()):
        r = results[sector_id]
        missing = []
        if r["co_occurrence_count"] == 0:
            missing.append("co_occurrence_rules")
        if not r["has_domain_signals"]:
            missing.append("domain_signals")
        if not r["has_synonyms"]:
            missing.append("synonym_dict")
        if not r["has_red_flag_exemption"]:
            missing.append("red_flag_exemption")

        if missing:
            print(f"  {sector_id}: MISSING {', '.join(missing)}")

    # Sectors needing expansion (AC3/AC5)
    print("\n" + "=" * 120)
    print("EXPANSION PRIORITIES")
    print("=" * 120)

    for sector_id in sorted(results.keys(), key=lambda s: results[s]["coverage_pct"]):
        r = results[sector_id]
        if r["classification"] in ("Raso", "Parcial"):
            gaps = []
            if r["co_occurrence_count"] == 0:
                gaps.append("+co_occurrence (min 2)")
            if not r["has_domain_signals"]:
                gaps.append("+domain_signals (NCM+unit)")
            if not r["has_synonyms"]:
                gaps.append("+synonyms")
            if r["exclusions_count"] < 15:
                gaps.append(f"+exclusions (have {r['exclusions_count']}, need 15+)")
            if gaps:
                print(f"  {sector_id} [{r['classification']}]: {', '.join(gaps)}")


if __name__ == "__main__":
    main()
