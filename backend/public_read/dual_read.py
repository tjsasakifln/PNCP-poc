"""Shadow compare legacy vs public_read_v1. Divergences are classified."""

from __future__ import annotations

from typing import Any

from public_read.contract import FamilyRead

BLOCKING = frozenset({"identity_mismatch", "missing_canonical_id"})
EXPLAINABLE = frozenset(
    {
        "count_delta",
        "freshness_delta",
        "field_delta",
        "legacy_only",
        "public_only",
    }
)


def compare_reads(legacy: dict[str, Any] | None, public: FamilyRead) -> list[str]:
    codes: list[str] = []
    if not legacy:
        codes.append("public_only" if public.entity else "both_empty")
        return codes
    legacy_id = str(
        legacy.get("canonical_id")
        or legacy.get("id")
        or legacy.get("cnpj")
        or legacy.get("process_key")
        or ""
    )
    if public.entity is None:
        codes.append("legacy_only")
        return codes
    if not public.entity.canonical_id:
        codes.append("missing_canonical_id")
    elif legacy_id and public.entity.canonical_id != legacy_id:
        codes.append("identity_mismatch")
    legacy_count = legacy.get("row_count")
    if legacy_count is not None and public.row_count is not None and legacy_count != public.row_count:
        codes.append("count_delta")
    return codes


def is_blocking(codes: list[str]) -> bool:
    return any(code in BLOCKING for code in codes)
