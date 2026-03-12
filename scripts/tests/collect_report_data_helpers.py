"""
Testable helpers extracted from collect-report-data.py.

We can't directly import the script because its top-level Windows encoding
wrapper (sys.stdout replacement) breaks pytest's capture mechanism.
Instead, we duplicate the pure functions here for testing.
"""
import re
from datetime import datetime, timezone
from typing import Any


def _clean_cnpj(cnpj: str) -> str:
    """Remove formatting from CNPJ, return 14 digits."""
    return re.sub(r"[^0-9]", "", cnpj).zfill(14)


def _format_cnpj(cnpj14: str) -> str:
    """Format 14-digit CNPJ as XX.XXX.XXX/XXXX-XX."""
    c = cnpj14
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"


def _safe_float(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        if isinstance(v, str):
            v = v.replace(",", ".")
        return float(v)
    except (ValueError, TypeError):
        return default


def _source_tag(status: str, detail: str = "") -> dict:
    """Create a _source metadata tag."""
    tag = {"status": status, "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    if detail:
        tag["detail"] = detail
    return tag
