#!/usr/bin/env python3
"""GitHub Actions billing health check (CRIT-080).

Reads a JSON array of recent workflow runs on stdin and prints two lines:
  1) queued_count: number of runs stuck in queued/waiting with no conclusion
  2) last_conclusion: conclusion of the most recent completed run

Used by `.github/workflows/billing-check.yml` — extracted to its own file
because embedding the Python source inside a YAML block scalar via
`python3 -c "..."` broke YAML indentation (lines at column 1 terminate the
outer `run: |` block scalar, making the whole workflow file invalid).
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    runs = json.load(sys.stdin)
    stalled = [
        r for r in runs
        if r.get("status") in ("queued", "waiting") and r.get("conclusion") is None
    ]
    completed = [r for r in runs if r.get("conclusion") is not None]

    queued_count = len(stalled)
    last_conclusion = completed[0]["conclusion"] if completed else "unknown"

    print(f"queued_count={queued_count}")
    print(f"last_conclusion={last_conclusion}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
