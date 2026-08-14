"""One adapter per public family. Never query extra-cli internal tables."""

from __future__ import annotations

from typing import Any

from public_read.client import (
    PublicReadUnavailable,
    fetchall,
    last_known_good,
    store_last_known_good,
)
from public_read.contract import (
    CONTRACT_VERSION,
    FamilyRead,
    PublicEntity,
    SnapshotMeta,
)
from public_read.flags import get_public_read_mode

# Predicates and LIMITs match extra-cli public_read_v1.query_budgets.
_FAMILY_SQL = {
    "tenders": """
        SELECT * FROM public_read_v1.tenders
        WHERE process_key = %s
        LIMIT 100
    """,
    "contracts": """
        SELECT * FROM public_read_v1.contracts
        WHERE process_key = %s
        LIMIT 100
    """,
    "entities": """
        SELECT * FROM public_read_v1.entities
        WHERE entity_id = %s
        LIMIT 10
    """,
    "suppliers": """
        SELECT * FROM public_read_v1.suppliers
        WHERE entity_id = %s
        LIMIT 10
    """,
    "organs": """
        SELECT * FROM public_read_v1.organs
        WHERE entity_id = %s
        LIMIT 10
    """,
    "municipalities": """
        SELECT * FROM public_read_v1.municipalities
        WHERE municipality_id = %s
        LIMIT 10
    """,
}

_CANONICAL_KEY = {
    "tenders": "process_key",
    "contracts": "process_key",
    "entities": "entity_id",
    "suppliers": "entity_id",
    "organs": "entity_id",
    "municipalities": "municipality_id",
}

_VALID_FRESHNESS = {"FRESH", "STALE", "FAILED", "BLOCKED", "UNKNOWN"}
_VALID_COMPLETENESS = {"COMPLETE", "INCOMPLETE", "UNKNOWN", "BLOCKED"}


def _as_reason_codes(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [str(item) for item in raw]
    return [str(raw)]


def _completeness(row: dict[str, Any]) -> str:
    value = row.get("completeness")
    if value in _VALID_COMPLETENESS:
        return value
    return "UNKNOWN"


def _freshness(row: dict[str, Any]) -> str:
    """Pass through producer freshness. Derive only when the column is absent."""
    value = row.get("freshness")
    if value in _VALID_FRESHNESS:
        return value
    codes = {item.lower() for item in _as_reason_codes(row.get("reason_codes"))}
    if "kill_switch_blocked" in codes or any("blocked" in item for item in codes):
        return "BLOCKED"
    completeness = _completeness(row)
    if completeness == "COMPLETE":
        return "FRESH"
    if completeness == "INCOMPLETE":
        return "STALE"
    if completeness == "BLOCKED":
        return "BLOCKED"
    return "UNKNOWN"


def _row_to_entity(family: str, row: dict[str, Any]) -> PublicEntity:
    key = _CANONICAL_KEY.get(family, "entity_id")
    canonical_id = str(row.get(key) or row.get("canonical_id") or "")
    provenance = row.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    return PublicEntity(
        canonical_id=canonical_id,
        family=family,
        display_name=row.get("title") or row.get("name") or row.get("display_name"),
        as_of=row.get("as_of"),
        source_updated_at=row.get("source_updated_at"),
        completeness=_completeness(row),
        freshness=_freshness(row),
        reason_codes=_as_reason_codes(row.get("reason_codes")),
        provenance=provenance,
        payload=row,
    )


def _blocked(family: str, mode: str, reason: str) -> FamilyRead:
    return FamilyRead(
        family=family,
        contract_version=CONTRACT_VERSION,
        mode=mode,
        served_from="blocked",
        divergence=[reason],
    )


def read_surface_health() -> list[dict[str, Any]]:
    return fetchall("SELECT * FROM public_read_v1.surface_health LIMIT 20")


def read_family(family: str, public_id: str) -> FamilyRead:
    mode = get_public_read_mode().value
    sql = _FAMILY_SQL.get(family)
    if not sql:
        return _blocked(family, mode, "unknown_family")

    try:
        rows = fetchall(sql, (public_id,))
    except PublicReadUnavailable as exc:
        cached = last_known_good(f"{family}:{public_id}")
        if cached:
            cached.served_from = "last_known_good"
            cached.divergence = [exc.reason]
            return cached
        return _blocked(family, mode, exc.reason)

    items = [_row_to_entity(family, row) for row in rows]
    reasons = [code for item in items for code in item.reason_codes]
    if not items:
        try:
            health_rows = read_surface_health()
        except PublicReadUnavailable:
            health_rows = []
        if any(
            str(row.get("completeness") or "") == "KILL_SWITCH_BLOCKED"
            or str(row.get("last_refresh_status") or "") == "FAILED"
            for row in health_rows
        ):
            return _blocked(family, mode, "surface_blocked")

    result = FamilyRead(
        family=family,
        contract_version=CONTRACT_VERSION,
        mode=mode,
        served_from="public_read_v1",
        snapshot=SnapshotMeta(contract_version=CONTRACT_VERSION),
        entity=items[0] if items else None,
        items=items,
        row_count=len(items),
        divergence=reasons if not items else [],
    )
    if items:
        store_last_known_good(f"{family}:{public_id}", result)
    return result
