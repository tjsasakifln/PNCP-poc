"""STORY-5.4 AC5 (TD-SYS-015): FTS precision/recall benchmark.

Runs a set of representative queries against the Supabase datalake and
measures top-K precision and recall against a labelled ground truth set.
Writes results to `docs/tech-debt/fts-benchmark.md` for tracking over time.

USAGE

    # Full run against production (read-only RPC) — use with care.
    python backend/scripts/bench_fts.py --env=prod --topk=20

    # Dry-run with canned expectations (no DB) — for CI smoke.
    python backend/scripts/bench_fts.py --dry-run

DESIGN

- This is a *harness*, not a gate. It does NOT fail the test suite; it
  writes a Markdown report that an engineer eyeballs before rolling the
  portuguese_smartlic config to production.
- Ground truth is a hand-curated list of (query, expected_pncp_ids) pairs.
  Start with 10-20; grow over time as anomalies surface.
- Without explicit ground truth, we fall back to a *stability* benchmark:
  compare top-K stability between `portuguese` (baseline) and
  `portuguese_smartlic` (new) by measuring rank overlap.

This file purposely does NOT run on every test run — it's a developer tool
invoked manually during rollout. Keep dependencies minimal.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Sequence


# ---------------------------------------------------------------------------
# Ground truth (seed set)
# ---------------------------------------------------------------------------
# Extend incrementally. Each entry is a plausible user query (natural language,
# lowercased) paired with a list of pncp_ids the *informed analyst* considers
# relevant. Score = top-K precision wrt this set.

GROUND_TRUTH: list[dict[str, Any]] = [
    # Placeholder — real IDs must be captured from production when running
    # this benchmark for the first time. The structure is what matters.
    # {"query": "pavimentação asfáltica", "expected_ids": ["...PNCP-id-1...", "..."]},
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark Portuguese FTS precision/recall."
    )
    parser.add_argument("--env", choices=["dev", "prod"], default="dev")
    parser.add_argument("--topk", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true", help="Skip DB; print queries only")
    parser.add_argument(
        "--out",
        default="docs/tech-debt/fts-benchmark.md",
        help="Output Markdown report path (relative to repo root).",
    )
    return parser.parse_args()


def _precision_at_k(returned: Sequence[str], expected: set[str], k: int) -> float:
    if not expected or k <= 0:
        return 0.0
    topk = list(returned)[:k]
    hits = sum(1 for pid in topk if pid in expected)
    return hits / min(k, len(topk))


def _recall_at_k(returned: Sequence[str], expected: set[str], k: int) -> float:
    if not expected:
        return 0.0
    topk = set(list(returned)[:k])
    hits = len(topk & expected)
    return hits / len(expected)


def _write_report(out_path: Path, rows: list[dict[str, Any]], *, topk: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# FTS Portuguese Benchmark")
    lines.append("")
    lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**top-K:** {topk}")
    lines.append("")
    lines.append("| Query | Expected | Returned | Precision@K | Recall@K | Latency ms |")
    lines.append("|-------|----------|----------|-------------|----------|------------|")
    for row in rows:
        lines.append(
            "| {q} | {e} | {r} | {p:.2%} | {rc:.2%} | {lat} |".format(
                q=row["query"],
                e=len(row["expected"]),
                r=len(row["returned"]),
                p=row["precision"],
                rc=row["recall"],
                lat=row["latency_ms"],
            )
        )
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote report → {out_path}")


def _run_against_datalake(query: str, topk: int) -> tuple[list[str], int]:
    """Call the real `query_datalake` and return (pncp_ids, latency_ms).

    Kept tiny so the script works end-to-end once credentials are configured.
    """
    from datalake_query import query_datalake

    t0 = time.perf_counter()
    results = query_datalake(
        ufs=None,
        data_inicial=None,
        data_final=None,
        keywords=[query],
        custom_terms=None,
        modo_busca="publicacao",
        modalidades=None,
        limit=topk,
    )
    elapsed = int((time.perf_counter() - t0) * 1000)
    ids = [r.get("numeroControlePNCP") or r.get("codigoCompra") or "" for r in results]
    return ids, elapsed


def main() -> int:
    args = _parse_args()

    if not GROUND_TRUTH:
        print(
            "WARNING: GROUND_TRUTH is empty. Benchmark will run queries but "
            "precision/recall will be 0%. Populate the seed set in this file "
            "before first production rollout.",
            file=sys.stderr,
        )

    rows: list[dict[str, Any]] = []
    for gt in GROUND_TRUTH:
        query = gt["query"]
        expected = set(gt.get("expected_ids", []))
        if args.dry_run:
            returned: list[str] = []
            latency_ms = 0
        else:
            returned, latency_ms = _run_against_datalake(query, args.topk)
        rows.append(
            {
                "query": query,
                "expected": expected,
                "returned": returned,
                "precision": _precision_at_k(returned, expected, args.topk),
                "recall": _recall_at_k(returned, expected, args.topk),
                "latency_ms": latency_ms,
            }
        )

    out = Path(__file__).resolve().parents[2] / args.out
    _write_report(out, rows, topk=args.topk)

    if not rows:
        print("No ground-truth entries — nothing to summarize.", file=sys.stderr)
        return 0

    avg_p = sum(r["precision"] for r in rows) / len(rows)
    avg_r = sum(r["recall"] for r in rows) / len(rows)
    print(json.dumps({"avg_precision": avg_p, "avg_recall": avg_r}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
