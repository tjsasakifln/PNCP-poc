"""Map a FamilyRead onto the public page model. No invented facts."""

from __future__ import annotations

from typing import Any

from public_read.contract import FamilyRead, PublicEntity


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def entity_to_page(entity: PublicEntity | None) -> dict[str, Any] | None:
    if entity is None:
        return None
    return {
        "canonical_id": entity.canonical_id,
        "family": entity.family,
        "display_name": entity.display_name,
        "as_of": _iso(entity.as_of),
        "source_updated_at": _iso(entity.source_updated_at),
        "completeness": entity.completeness,
        "freshness": entity.freshness,
        "reason_codes": list(entity.reason_codes or []),
        "provenance": entity.provenance or {},
    }


def family_read_to_page_model(read: FamilyRead) -> dict[str, Any]:
    entity = entity_to_page(read.entity)
    freshness = (entity or {}).get("freshness")
    return {
        "family": read.family,
        "contract_version": read.contract_version,
        "mode": read.mode,
        "served_from": read.served_from,
        "canonical_id": (entity or {}).get("canonical_id"),
        "display_name": (entity or {}).get("display_name"),
        "as_of": (entity or {}).get("as_of") or _iso(read.snapshot.as_of if read.snapshot else None),
        "source_updated_at": (entity or {}).get("source_updated_at"),
        "completeness": (entity or {}).get("completeness")
        or (read.snapshot.completeness if read.snapshot else None),
        "freshness": freshness,
        "reason_codes": (entity or {}).get("reason_codes") or [],
        "provenance": (entity or {}).get("provenance") or {},
        "row_count": read.row_count,
        "divergence": list(read.divergence or []),
        "blocked": read.served_from == "blocked" or freshness == "BLOCKED",
        "stale": freshness == "STALE",
        "empty": entity is None or read.row_count == 0,
        "last_known_good": read.served_from == "last_known_good",
        "entity": entity,
        "items": [entity_to_page(item) for item in read.items],
    }
