"""Durable lead outbox — #2117.

Idempotent, retryable, no PII in URLs or client analytics.
Analytics outage must not drop the lead.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

CONSENT_VERSION = "2026-08-confenge-v1"
OUTBOX_PATH = Path(os.getenv("LEAD_OUTBOX_PATH", "/tmp/smartlic-lead-outbox.jsonl"))

_MEMORY: dict[str, dict[str, Any]] = {}


def build_idempotency_key(
    email: str | None,
    phone: str | None,
    source: str,
    cta_id: str | None,
    entity_public_id: str | None,
    day: str | None = None,
) -> str:
    day = day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    material = "|".join(
        [
            (email or "").strip().lower(),
            (phone or "").strip(),
            source,
            cta_id or "",
            entity_public_id or "",
            day,
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def classify_referrer(referrer: str | None) -> str:
    if not referrer:
        return "direct"
    lowered = referrer.lower()
    if "google." in lowered:
        return "organic_search"
    if "bing." in lowered or "duckduckgo." in lowered:
        return "organic_search"
    if "smartlic.tech" in lowered:
        return "internal"
    if "linkedin." in lowered or "twitter." in lowered or "x.com" in lowered:
        return "social"
    return "referral"


def receipt_for(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "accepted": True,
        "receipt_id": record["receipt_id"],
        "idempotency_key": record["idempotency_key"],
        "handoff_state": record["handoff_state"],
        "consent_version": record["consent_version"],
    }


def _persist_jsonl(record: dict[str, Any]) -> None:
    OUTBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, default=str)
    # Atomic-ish append: write to temp then append to dest.
    fd, tmp = tempfile.mkstemp(prefix="lead-outbox-", suffix=".jsonl")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(line + "\n")
        with OUTBOX_PATH.open("a", encoding="utf-8") as dest:
            dest.write(line + "\n")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def accept_lead(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist first, then attempt handoff. Never depends on analytics."""
    key = build_idempotency_key(
        payload.get("email"),
        payload.get("telefone") or payload.get("phone"),
        str(payload.get("source") or "unknown"),
        payload.get("cta_id"),
        payload.get("entity_public_id"),
    )
    existing = _MEMORY.get(key)
    if existing:
        existing["deduplicated"] = True
        return existing

    record = {
        "receipt_id": str(uuid4()),
        "idempotency_key": key,
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "handoff_state": "accepted",
        "attempts": 0,
        "consent_version": payload.get("consent_version") or CONSENT_VERSION,
        "source": payload.get("source"),
        "cta_id": payload.get("cta_id"),
        "route_family": payload.get("route_family"),
        "entity_type": payload.get("entity_type"),
        "entity_public_id": payload.get("entity_public_id"),
        "landing_url": payload.get("landing_url") or payload.get("origin_url"),
        "referrer_class": classify_referrer(payload.get("referrer")),
        "utm_source": payload.get("utm_source"),
        "utm_medium": payload.get("utm_medium") or payload.get("medium"),
        "utm_campaign": payload.get("utm_campaign"),
        "correlation_id": payload.get("correlation_id") or str(uuid4()),
        "email": payload.get("email"),
        "nome": payload.get("nome"),
        "empresa": payload.get("empresa"),
        "telefone": payload.get("telefone") or payload.get("phone"),
        "mensagem": payload.get("mensagem"),
        "deduplicated": False,
    }
    _MEMORY[key] = record
    try:
        _persist_jsonl({k: v for k, v in record.items() if k != "mensagem"})
    except OSError:
        logger.warning("lead_outbox_fs_failed receipt=%s", record["receipt_id"])

    try:
        from leads.handoff import deliver_handoff

        deliver_handoff(record)
    except Exception:
        record["handoff_state"] = "failed"
        logger.warning("lead_handoff_failed receipt=%s", record["receipt_id"], exc_info=True)

    return record
