"""Authoritative family serve path.

off     — legacy only
shadow  — legacy serves; public_read is read in parallel; divergences classified
canary  — tenders may serve public when the gate is already decided by env
          PUBLIC_READ_CANARY_FAMILY + non-blocking compare; else legacy
on      — public_read, last-known-good, then blocked

The public response in shadow is the legacy payload. Never the extra-cli row.
"""

from __future__ import annotations

import os
from typing import Any

from public_read.adapters import read_family
from public_read.canary import CANARY_FAMILY, canary_family_allowed
from public_read.client import PublicReadUnavailable
from public_read.contract import CONTRACT_VERSION, FamilyRead, PublicEntity, SnapshotMeta
from public_read.dual_read import compare_reads, is_blocking
from public_read.flags import (
    PublicReadMode,
    get_public_read_mode,
    should_read_public,
    should_serve_public,
)


def _legacy_to_entity(family: str, legacy: dict[str, Any]) -> PublicEntity:
    canonical_id = str(
        legacy.get("canonical_id")
        or legacy.get("process_key")
        or legacy.get("entity_id")
        or legacy.get("municipality_id")
        or legacy.get("cnpj")
        or legacy.get("id")
        or ""
    )
    freshness_raw = legacy.get("freshness")
    completeness_raw = legacy.get("completeness")
    return PublicEntity(
        canonical_id=canonical_id,
        family=family,
        display_name=legacy.get("display_name") or legacy.get("title") or legacy.get("name"),
        as_of=legacy.get("as_of"),
        source_updated_at=legacy.get("source_updated_at"),
        completeness=completeness_raw if completeness_raw in {"COMPLETE", "INCOMPLETE", "UNKNOWN", "BLOCKED"} else "UNKNOWN",
        freshness=freshness_raw if freshness_raw in {"FRESH", "STALE", "FAILED", "BLOCKED", "UNKNOWN"} else "UNKNOWN",
        reason_codes=list(legacy.get("reason_codes") or []),
        provenance=legacy.get("provenance") if isinstance(legacy.get("provenance"), dict) else {},
        payload=legacy,
    )


def _legacy_read(family: str, public_id: str, legacy: dict[str, Any] | None, mode: str) -> FamilyRead:
    if not legacy:
        return FamilyRead(
            family=family,
            contract_version=CONTRACT_VERSION,
            mode=mode,
            served_from="legacy",
            snapshot=SnapshotMeta(contract_version=CONTRACT_VERSION),
            entity=None,
            items=[],
            row_count=0,
        )
    entity = _legacy_to_entity(family, legacy)
    count = legacy.get("row_count")
    if count is None:
        count = 1 if entity.canonical_id else 0
    return FamilyRead(
        family=family,
        contract_version=CONTRACT_VERSION,
        mode=mode,
        served_from="legacy",
        snapshot=SnapshotMeta(contract_version=CONTRACT_VERSION),
        entity=entity if entity.canonical_id else None,
        items=[entity] if entity.canonical_id else [],
        row_count=int(count),
    )


def _unavailable(family: str, mode: str, reason: str) -> FamilyRead:
    return FamilyRead(
        family=family,
        contract_version=CONTRACT_VERSION,
        mode=mode,
        served_from="blocked",
        divergence=[reason, "public_unavailable"],
    )


def _probe_public(family: str, public_id: str, mode: str) -> FamilyRead | None:
    """Consult extra-cli. Never swallow a producer failure as agreement."""
    if not should_read_public():
        return None
    try:
        return read_family(family, public_id)
    except PublicReadUnavailable as exc:
        return _unavailable(family, mode, exc.reason)
    except Exception:
        return _unavailable(family, mode, "public_unavailable")


def _canary_wants_public(family: str, codes: list[str]) -> bool:
    if not canary_family_allowed(family):
        return False
    allowed = os.getenv("PUBLIC_READ_CANARY_FAMILY", CANARY_FAMILY).strip() or CANARY_FAMILY
    if family != allowed:
        return False
    return not is_blocking(codes)


def serve_family(
    family: str,
    public_id: str,
    legacy: dict[str, Any] | None = None,
) -> FamilyRead:
    mode = get_public_read_mode()
    mode_value = mode.value
    public = _probe_public(family, public_id, mode_value)
    legacy_read = _legacy_read(family, public_id, legacy, mode_value)

    codes: list[str] = []
    if public is None:
        if mode is PublicReadMode.SHADOW:
            codes = ["public_not_consulted"]
    else:
        codes = compare_reads(legacy, public)
        if public.served_from == "blocked" and "public_unavailable" not in codes:
            codes.append("public_unavailable")
        for extra in public.divergence:
            if extra not in codes:
                codes.append(extra)

    if mode is PublicReadMode.SHADOW or not should_serve_public():
        legacy_read.divergence = codes
        return legacy_read

    if mode is PublicReadMode.CANARY:
        if public is not None and _canary_wants_public(family, codes):
            public.divergence = codes
            return public
        legacy_read.divergence = codes or ["canary_family_held"]
        return legacy_read

    # mode == on
    if public is not None:
        public.divergence = codes
        return public
    return FamilyRead(
        family=family,
        contract_version=CONTRACT_VERSION,
        mode=mode_value,
        served_from="blocked",
        divergence=["public_unavailable"],
    )
