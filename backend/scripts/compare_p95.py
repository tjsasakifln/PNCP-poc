"""STORY-4.1 AC4 helper — compare Locust p95 latency across two CSV runs.

Usage::

    python backend/scripts/compare_p95.py baseline.csv new.csv [--target 0.40]

Exit code 0 when ``(baseline - new) / baseline >= target`` (default 40%
reduction). Designed to be used as a CI gate after running STORY-3.3's
Locust scenario against baseline and new branches.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Optional


def _extract_p95(path: Path, endpoint: Optional[str] = None) -> Optional[float]:
    """Return the 95%ile latency (ms) for the ``endpoint`` (or ``Aggregated``)."""

    with path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            name = row.get("Name") or row.get("name") or ""
            if endpoint is not None and endpoint.lower() not in name.lower():
                continue
            if endpoint is None and name.lower() != "aggregated":
                continue
            val = row.get("95%") or row.get("95%ile") or row.get("95th Percentile")
            if val:
                try:
                    return float(val)
                except ValueError:
                    pass
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--endpoint", default=None, help='Row name filter (default "Aggregated")')
    parser.add_argument("--target", type=float, default=0.40, help="Required fractional reduction")
    args = parser.parse_args()

    baseline_p95 = _extract_p95(args.baseline, args.endpoint)
    new_p95 = _extract_p95(args.new, args.endpoint)

    if baseline_p95 is None or new_p95 is None:
        print(f"ERROR: could not extract p95 from both files (baseline={baseline_p95}, new={new_p95})")
        return 2

    reduction = (baseline_p95 - new_p95) / baseline_p95 if baseline_p95 else 0.0
    print(f"baseline p95 = {baseline_p95:.0f} ms")
    print(f"new p95      = {new_p95:.0f} ms")
    print(f"reduction    = {reduction * 100:.1f}% (target: {args.target * 100:.0f}%)")

    if reduction >= args.target:
        print("PASS — meets STORY-4.1 AC4 threshold")
        return 0
    print("FAIL — does not meet STORY-4.1 AC4 threshold")
    return 1


if __name__ == "__main__":
    sys.exit(main())
