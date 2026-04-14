#!/usr/bin/env python3
"""STORY-2.12 (TD-DB-015) AC1: quantify NULLs in pncp_raw_bids.data_*.

Writes a small markdown report to docs/audit/ so operators can see, for each
date column, how many rows are NULL and what percentage of the table that
represents. Non-destructive — this script only SELECTs.

Usage:
    python scripts/audit_pncp_data_nullability.py
    python scripts/audit_pncp_data_nullability.py --output-dir /tmp/audit
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("audit_pncp_data_nullability")


DATE_COLUMNS: tuple[str, ...] = (
    "data_publicacao",
    "data_abertura",
    "data_encerramento",
)


def _count(sb, column: str | None = None) -> int:
    q = sb.table("pncp_raw_bids").select("pncp_id", count="exact")
    if column is not None:
        q = q.is_(column, "null")
    res = q.execute()
    return int(getattr(res, "count", 0) or 0)


def run_audit(sb) -> dict:
    total = _count(sb)
    stats: dict[str, dict] = {}
    for col in DATE_COLUMNS:
        nulls = _count(sb, col)
        pct = round(nulls / total * 100, 2) if total else 0.0
        stats[col] = {"null": nulls, "total": total, "pct_null": pct}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_rows": total,
        "columns": stats,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# PNCP Raw Bids — Date Column Nullability Audit",
        "",
        "_STORY-2.12 (TD-DB-015) AC1 — read-only audit of `pncp_raw_bids.data_*` NULLs._",
        "",
        f"- Generated: `{report['generated_at']}`",
        f"- Total rows: **{report['total_rows']:,}**",
        "",
        "| Column | NULL rows | % of total |",
        "| --- | ---: | ---: |",
    ]
    for col, s in report["columns"].items():
        lines.append(f"| `{col}` | {s['null']:,} | {s['pct_null']}% |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `data_publicacao` = NULL blocks FTS queries filtered by period (see",
            "  `search_datalake` in migration `20260414132000_search_datalake_coalesce_dates.sql`).",
            "- `data_abertura` is treated as optional; backfill defaults to `data_publicacao`.",
            "- `data_encerramento` = NULL means 'open indefinitely' for `p_modo='abertas'`.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--output-dir", default="docs/audit")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from supabase_client import get_supabase

    sb = get_supabase()
    report = run_audit(sb)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"pncp_data_nullability_{ts}.md"
    md_path.write_text(render_markdown(report), encoding="utf-8")

    logger.info("audit: wrote %s", md_path)
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
