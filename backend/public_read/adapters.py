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

_FAMILY_SQL = {
    "tenders": """
        SELECT * FROM public_read_v1.tenders
        WHERE process_key = %s
        LIMIT 20
    """,
    "contracts": """
        SELECT * FROM public_read_v1.contracts
        WHERE process_key = %s
        LIMIT 20
    """,
    "entities": """
        SELECT * FROM public_read_v1.entities
        WHERE entity_id = %s
        LIMIT 5
    """,
    "suppliers": """
        SELECT * FROM public_read_v1.suppliers
        WHERE entity_id = %s
        LIMIT 5
    """,
    "organs": """
        SELECT * FROM public_read_v1.organs
        WHERE entity_id = %s
        LIMIT 5
    """,
    "municipalities": """
        SELECT * FROM public_read_v1.municipalities
        WHERE municipality_id = %s
        LIMIT 5
    """,
}


def _row_to_entity(family: str, row: dict[str, Any], canonical_key: str) -> PublicEntity:
    canonical_id = str(
        row.get(canonical_key)
        or row.get("canonical_id")
        or row.get("entity_id")
        or row.get("process_key")
        or row.get("municipality_id")
        or ""
    )
    return PublicEntity(
        canonical_id=canonical_id,
        family=family,
        display_name=row.get("title") or row.get("name") or row.get("display_name"),
        as_of=row.get("as_of"),
        source_updated_at=row.get("source_updated_at"),
        completeness=row.get("completeness") or "UNKNOWN",
        freshness=row.get("freshness") or "UNKNOWN",
        reason_codes=list(row.get("reason_codes") or []),
        provenance=row.get("provenance") if isinstance(row.get("provenance"), dict) else {},
        payload=row,
    )


def read_family(family: str, public_id: str) -> FamilyRead:
    mode = get_public_read_mode().value
    sql = _FAMILY_SQL.get(family)
    if not sql:
        return FamilyRead(
            family=family,
            mode=mode,
            served_from="blocked",
            divergence=["unknown_family"],
        )

    try:
        rows = fetchall(sql, (public_id,))
    except PublicReadUnavailable as exc:
        cached = last_known_good(f"{family}:{public_id}")
        if cached:
            cached.served_from = "last_known_good"
            cached.divergence = [exc.reason]
            return cached
        return FamilyRead(
            family=family,
            mode=mode,
            served_from="blocked",
            divergence=[exc.reason],
        )

    items = [
        _row_to_entity(
            family,
            row,
            "process_key" if family in {"tenders", "contracts"} else "entity_id",
        )
        for row in rows
    ]
    result = FamilyRead(
        family=family,
        contract_version=CONTRACT_VERSION,
        mode=mode,
        served_from="public_read_v1",
        snapshot=SnapshotMeta(contract_version=CONTRACT_VERSION),
        entity=items[0] if items else None,
        items=items,
        row_count=len(items),
    )
    store_last_known_good(f"{family}:{public_id}", result)
    return result
