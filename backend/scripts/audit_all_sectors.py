#!/usr/bin/env python3
"""
Audit ALL sectors against real PNCP data for false positives/negatives.

Usage:
    cd backend
    python scripts/audit_all_sectors.py
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import RetryConfig, setup_logging
from pncp_client import PNCPClient
from filter import match_keywords, filter_licitacao
from sectors import SECTORS, SectorConfig

setup_logging("INFO")

# --- Config ---
UFS_SAMPLE = ["SP", "MG", "RJ"]
DATE_END = date.today()
DATE_START = DATE_END - timedelta(days=10)
MODALIDADES = [6]  # Pregão Eletrônico
MAX_ITEMS = 400


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

    print(f"\n=== Fetched {len(items)} raw items ===\n")
    return items


def audit_sector(items: list[dict], sector: SectorConfig) -> dict:
    """Audit a single sector against the items."""
    ufs_set = set(UFS_SAMPLE)
    approved = []
    rejected_kw = []
    blocked_by_exc = []

    for item in items:
        objeto = item.get("objetoCompra", "")
        valor = item.get("valorTotalEstimado")
        uf = item.get("uf", "")

        # Keyword analysis
        kw_match, kw_found = match_keywords(objeto, sector.keywords, sector.exclusions)
        kw_match_no_exc, kw_found_no_exc = match_keywords(objeto, sector.keywords, None)

        # Full filter (using sector keywords)
        fake_lic = {"uf": uf, "valorTotalEstimado": valor, "objetoCompra": objeto}
        ok, reason = filter_licitacao(
            fake_lic, ufs_set,
            keywords=sector.keywords,
            exclusions=sector.exclusions,
        )

        entry = {
            "objeto": objeto[:250],
            "valor": valor,
            "uf": uf,
            "approved": ok,
            "reason": reason,
            "keywords_found": kw_found,
            "blocked_by_exclusion": (not kw_match and kw_match_no_exc),
            "kw_without_exc": kw_found_no_exc if (not kw_match and kw_match_no_exc) else [],
        }

        if ok:
            approved.append(entry)
        elif reason and "keyword" in reason.lower():
            if not kw_match and kw_match_no_exc:
                blocked_by_exc.append(entry)
            else:
                rejected_kw.append(entry)

    return {
        "sector_id": sector.id,
        "sector_name": sector.name,
        "total_items": len(items),
        "approved_count": len(approved),
        "rejected_keyword_count": len(rejected_kw),
        "blocked_by_exclusion_count": len(blocked_by_exc),
        "approved_sample": approved[:15],
        "blocked_by_exclusion": blocked_by_exc[:10],
    }


def analyze_cross_sector_conflicts(items: list[dict]) -> list[dict]:
    """Find items that match multiple sectors (potential ambiguity)."""
    ufs_set = set(UFS_SAMPLE)
    conflicts = []

    for item in items:
        objeto = item.get("objetoCompra", "")
        valor = item.get("valorTotalEstimado")
        uf = item.get("uf", "")
        fake_lic = {"uf": uf, "valorTotalEstimado": valor, "objetoCompra": objeto}

        matching_sectors = []
        for sector in SECTORS.values():
            ok, _ = filter_licitacao(
                fake_lic, ufs_set,
                keywords=sector.keywords,
                exclusions=sector.exclusions,
            )
            if ok:
                matching_sectors.append(sector.id)

        if len(matching_sectors) > 1:
            conflicts.append({
                "objeto": objeto[:200],
                "sectors": matching_sectors,
            })

    return conflicts


def generate_report(results: list[dict], conflicts: list[dict]) -> str:
    """Generate markdown report."""
    lines = [
        "# Auditoria Multi-Setor — Falsos Positivos/Negativos",
        "",
        f"**Data:** {date.today().isoformat()}",
        f"**Período:** {DATE_START} a {DATE_END}",
        f"**UFs:** {', '.join(UFS_SAMPLE)}",
        f"**Total itens:** {results[0]['total_items'] if results else 0}",
        "",
        "## Resumo por Setor",
        "",
        "| Setor | Aprovados | Bloqueados por Exclusão | Rejeitados (keyword) |",
        "|-------|-----------|------------------------|---------------------|",
    ]

    for r in results:
        lines.append(
            f"| {r['sector_name']} | {r['approved_count']} | "
            f"{r['blocked_by_exclusion_count']} | {r['rejected_keyword_count']} |"
        )

    lines.append("")

    # Per-sector details
    for r in results:
        lines.append(f"## {r['sector_name']} ({r['sector_id']})")
        lines.append("")

        if r["approved_sample"]:
            lines.append(f"### Aprovados (amostra — {r['approved_count']} total)")
            lines.append("")
            for i, item in enumerate(r["approved_sample"]):
                val_str = f"R$ {item['valor']:,.2f}" if item['valor'] else "N/A"
                lines.append(f"**{i+1}.** [{item['uf']}] {val_str}")
                lines.append(f"  {item['objeto'][:180]}")
                lines.append(f"  Keywords: {', '.join(item['keywords_found'][:5])}")
                lines.append("")
        else:
            lines.append("Nenhum item aprovado.")
            lines.append("")

        if r["blocked_by_exclusion"]:
            lines.append(f"### Bloqueados por Exclusão ({r['blocked_by_exclusion_count']})")
            lines.append("")
            for i, item in enumerate(r["blocked_by_exclusion"]):
                lines.append(f"**EXC-{i+1}.** {item['objeto'][:180]}")
                lines.append(f"  Keywords que teriam matchado: {', '.join(item['kw_without_exc'][:5])}")
                lines.append("")

    # Cross-sector conflicts
    if conflicts:
        lines.append("## Conflitos Cross-Setor")
        lines.append("")
        lines.append("Itens que matcham em mais de um setor:")
        lines.append("")
        for i, c in enumerate(conflicts[:20]):
            lines.append(f"**{i+1}.** Setores: {', '.join(c['sectors'])}")
            lines.append(f"  {c['objeto']}")
            lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("  AUDITORIA MULTI-SETOR")
    print("=" * 60)

    items = fetch_raw_data()
    if not items:
        print("ERRO: Nenhum item retornado.")
        sys.exit(1)

    results = []
    for sector in SECTORS.values():
        print(f"\nAuditando setor: {sector.name}...")
        r = audit_sector(items, sector)
        results.append(r)
        print(f"  Aprovados: {r['approved_count']}, "
              f"Bloqueados excl: {r['blocked_by_exclusion_count']}, "
              f"Rejeitados kw: {r['rejected_keyword_count']}")

    print("\nAnalisando conflitos cross-setor...")
    conflicts = analyze_cross_sector_conflicts(items)
    print(f"  {len(conflicts)} itens em múltiplos setores")

    output_dir = Path(__file__).parent

    with open(output_dir / "audit_all_sectors.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    report = generate_report(results, conflicts)
    with open(output_dir / "audit_all_sectors_report.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("\nResultados salvos em scripts/audit_all_sectors_report.md")

    # Summary table
    print(f"\n{'='*60}")
    print(f"{'Setor':<30} {'Aprov':>6} {'Excl':>6} {'Rej':>6}")
    print(f"{'='*60}")
    for r in results:
        print(f"{r['sector_name']:<30} {r['approved_count']:>6} "
              f"{r['blocked_by_exclusion_count']:>6} {r['rejected_keyword_count']:>6}")
    print(f"{'='*60}")
    print(f"Conflitos cross-setor: {len(conflicts)}")


if __name__ == "__main__":
    main()
