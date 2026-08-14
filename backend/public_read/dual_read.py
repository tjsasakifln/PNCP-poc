"""Shadow compare legacy vs public_read_v1. Divergences are classified."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from public_read.contract import FamilyRead

BLOCKING = frozenset({"identity_mismatch", "missing_canonical_id"})
DIMENSIONS = {
    "identity_mismatch": "identity",
    "missing_canonical_id": "identity",
    "count_delta": "count",
    "value_delta": "value",
    "freshness_delta": "freshness",
    "provenance_delta": "provenance",
    "reason_code_delta": "reason",
    "legacy_only": "empty",
    "public_only": "empty",
    "both_empty": "empty",
    "blocked_public": "blocked",
    "blocked_legacy": "blocked",
    "stale_public": "freshness",
    "stale_legacy": "freshness",
}


@dataclass(frozen=True)
class ClassifiedDivergence:
    code: str
    dimension: str
    blocking: bool


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _legacy_id(legacy: dict[str, Any]) -> str:
    return _as_text(
        legacy.get("canonical_id")
        or legacy.get("process_key")
        or legacy.get("entity_id")
        or legacy.get("municipality_id")
        or legacy.get("cnpj")
        or legacy.get("id")
    )


def _legacy_value(legacy: dict[str, Any]) -> str:
    return _as_text(
        legacy.get("value")
        or legacy.get("contract_value")
        or legacy.get("valor")
        or legacy.get("estimated_value")
    )


def _public_value(public: FamilyRead) -> str:
    if public.entity is None:
        return ""
    payload = public.entity.payload or {}
    return _as_text(
        payload.get("contract_value")
        or payload.get("value")
        or payload.get("valor")
    )


def _legacy_freshness(legacy: dict[str, Any]) -> str:
    return _as_text(legacy.get("freshness") or legacy.get("freshness_state")).upper()


def _legacy_provenance(legacy: dict[str, Any]) -> str:
    block = legacy.get("provenance")
    if isinstance(block, dict):
        return _as_text(block.get("snapshot_id") or block.get("source") or block)
    return _as_text(block or legacy.get("source"))


def _public_provenance(public: FamilyRead) -> str:
    if public.entity is None:
        return ""
    block = public.entity.provenance or {}
    if isinstance(block, dict):
        return _as_text(block.get("snapshot_id") or block.get("source") or block)
    return _as_text(block)


def _legacy_reasons(legacy: dict[str, Any]) -> set[str]:
    raw = legacy.get("reason_codes") or []
    return {str(item) for item in raw}


def _is_blocked(payload: dict[str, Any] | None, public: FamilyRead | None) -> bool:
    if payload and (
        payload.get("blocked")
        or str(payload.get("freshness") or "").upper() == "BLOCKED"
        or str(payload.get("completeness") or "").upper() == "BLOCKED"
    ):
        return True
    if public is not None and (
        public.served_from == "blocked"
        or (public.entity is not None and public.entity.freshness == "BLOCKED")
        or (public.entity is not None and public.entity.completeness == "BLOCKED")
    ):
        return True
    return False


def classify_divergences(codes: list[str]) -> list[ClassifiedDivergence]:
    classified: list[ClassifiedDivergence] = []
    for code in codes:
        classified.append(
            ClassifiedDivergence(
                code=code,
                dimension=DIMENSIONS.get(code, "other"),
                blocking=code in BLOCKING,
            )
        )
    return classified


def compare_reads(legacy: dict[str, Any] | None, public: FamilyRead) -> list[str]:
    """Return classified reason codes. Never a single aggregate percentage."""
    codes: list[str] = []
    public_blocked = _is_blocked(None, public)
    legacy_blocked = _is_blocked(legacy, None)
    if public_blocked:
        codes.append("blocked_public")
    if legacy_blocked:
        codes.append("blocked_legacy")

    if not legacy:
        codes.append("public_only" if public.entity else "both_empty")
        return codes

    legacy_id = _legacy_id(legacy)
    if public.entity is None:
        if public.served_from == "blocked" or public_blocked:
            codes.append("legacy_only")
        else:
            codes.append("legacy_only")
        return codes

    if not public.entity.canonical_id:
        codes.append("missing_canonical_id")
    elif legacy_id and public.entity.canonical_id != legacy_id:
        codes.append("identity_mismatch")

    legacy_count = legacy.get("row_count")
    if legacy_count is not None and public.row_count is not None and int(legacy_count) != int(public.row_count):
        codes.append("count_delta")

    legacy_value = _legacy_value(legacy)
    public_value = _public_value(public)
    if legacy_value and public_value and legacy_value != public_value:
        codes.append("value_delta")

    legacy_fresh = _legacy_freshness(legacy)
    public_fresh = (public.entity.freshness or "").upper()
    if legacy_fresh and public_fresh and legacy_fresh != public_fresh:
        codes.append("freshness_delta")
    if public_fresh == "STALE":
        codes.append("stale_public")
    if legacy_fresh == "STALE":
        codes.append("stale_legacy")

    legacy_prov = _legacy_provenance(legacy)
    public_prov = _public_provenance(public)
    if legacy_prov and public_prov and legacy_prov != public_prov:
        codes.append("provenance_delta")

    public_reasons = {str(item) for item in (public.entity.reason_codes or [])}
    legacy_reasons = _legacy_reasons(legacy)
    if legacy_reasons and public_reasons and legacy_reasons != public_reasons:
        codes.append("reason_code_delta")

    # Deduplicate while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return ordered


def is_blocking(codes: list[str]) -> bool:
    return any(code in BLOCKING for code in codes)
