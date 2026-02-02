"""
Sector diagnostic script — tests keyword/exclusion lists against real PNCP API data.

For each sector: fetches recent procurements and applies sector filters,
reporting approved/rejected items with reasons for manual review.

Usage:
    cd backend
    python scripts/sector_diagnostic.py
    python scripts/sector_diagnostic.py --sectors facilities manutencao_predial
    python scripts/sector_diagnostic.py --pages 2
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx

from filter import match_keywords, normalize_text
from sectors import SECTORS


PNCP_BASE = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
ITEMS_PER_PAGE = 50
MAX_PAGES = 20
# Modalidades: 6=Pregão Eletrônico, 8=Dispensa, 4=Concorrência, 5=Pregão Presencial
MODALIDADES = [6, 8, 4, 5]


def fetch_pncp_page(
    data_inicial: str,
    data_final: str,
    modalidade: int = 6,
    pagina: int = 1,
    tam_pagina: int = ITEMS_PER_PAGE,
) -> dict[str, Any]:
    """Fetch one page from PNCP API."""
    params = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "codigoModalidadeContratacao": modalidade,
        "pagina": pagina,
        "tamanhoPagina": tam_pagina,
    }
    with httpx.Client(timeout=30) as client:
        resp = client.get(PNCP_BASE, params=params)
        resp.raise_for_status()
        return resp.json()


def diagnose_sector(
    sector_id: str,
    items: list[dict],
) -> dict[str, Any]:
    """Apply sector filters to items and categorize results."""
    sector = SECTORS[sector_id]
    approved = []
    rejected_keyword = []
    rejected_exclusion = []

    for item in items:
        objeto = item.get("objetoCompra", "") or ""
        objeto_norm = normalize_text(objeto)

        # Check exclusions first
        excluded_by = None
        if sector.exclusions:
            for exc in sector.exclusions:
                import re
                exc_norm = normalize_text(exc)
                pattern = rf"\b{re.escape(exc_norm)}\b"
                if re.search(pattern, objeto_norm):
                    excluded_by = exc
                    break

        if excluded_by:
            rejected_exclusion.append({
                "objeto": objeto[:200],
                "excluded_by": excluded_by,
            })
            continue

        # Check keywords
        matched, kw_list = match_keywords(objeto, sector.keywords, set())  # no exclusions, already checked
        if matched:
            approved.append({
                "objeto": objeto[:200],
                "matched_keywords": kw_list[:5],
            })
        else:
            rejected_keyword.append({
                "objeto": objeto[:200],
            })

    return {
        "sector_id": sector_id,
        "sector_name": sector.name,
        "total_items": len(items),
        "approved_count": len(approved),
        "rejected_keyword_count": len(rejected_keyword),
        "rejected_exclusion_count": len(rejected_exclusion),
        "approved_samples": approved[:20],
        "rejected_keyword_samples": rejected_keyword[:30],
        "rejected_exclusion_samples": rejected_exclusion[:20],
    }


def main():
    parser = argparse.ArgumentParser(description="Sector keyword diagnostic")
    parser.add_argument("--sectors", nargs="*", help="Specific sectors to test")
    parser.add_argument("--pages", type=int, default=MAX_PAGES, help="Pages to fetch")
    parser.add_argument("--days", type=int, default=7, help="Days back to search")
    args = parser.parse_args()

    sector_ids = args.sectors or list(SECTORS.keys())
    for sid in sector_ids:
        if sid not in SECTORS:
            print(f"ERROR: Unknown sector '{sid}'. Available: {list(SECTORS.keys())}")
            sys.exit(1)

    data_final = datetime.now().strftime("%Y%m%d")
    data_inicial = (datetime.now() - timedelta(days=args.days)).strftime("%Y%m%d")
    print(f"Fetching PNCP data: {data_inicial} to {data_final}, {args.pages} pages")

    # Fetch all items across modalidades
    all_items: list[dict] = []
    seen_ids: set[str] = set()
    for mod in MODALIDADES:
        for page in range(1, args.pages + 1):
            print(f"  Fetching modalidade {mod}, page {page}/{args.pages}...")
            try:
                import time
                time.sleep(0.15)  # Rate limit
                data = fetch_pncp_page(data_inicial, data_final, modalidade=mod, pagina=page)
                items = data.get("data", [])
                if not items:
                    break
                for item in items:
                    item_id = item.get("codigoCompra", "") or str(len(all_items))
                    if item_id not in seen_ids:
                        seen_ids.add(item_id)
                        all_items.append(item)
                if not data.get("temProximaPagina", False):
                    break
            except Exception as e:
                print(f"  Error fetching modalidade {mod} page {page}: {e}")
                break

    print(f"Total items fetched: {len(all_items)}")

    # Diagnose each sector
    results = {}
    for sid in sector_ids:
        print(f"\nDiagnosing sector: {sid}")
        result = diagnose_sector(sid, all_items)
        results[sid] = result
        print(f"  Approved: {result['approved_count']}")
        print(f"  Rejected (no keyword): {result['rejected_keyword_count']}")
        print(f"  Rejected (exclusion): {result['rejected_exclusion_count']}")

    # Save output
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"diagnostic_{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
