"""Optional SMARTLIC-003 evidence writer. Tests stay valid without it."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def write_evidence(name: str, payload: Any) -> Path | None:
    raw = os.environ.get("SMARTLIC_003_EVIDENCE_DIR", "").strip()
    if not raw:
        return None
    dest = Path(raw)
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / name
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
