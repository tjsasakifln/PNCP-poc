"""Durable lead outbox — #2117.

Persist first, then handoff. Analytics is never on this path.
Idempotency survives process restart via JSONL reload.
Retry/reprocess never mints a second receipt.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

logger = logging.getLogger(__name__)

CONSENT_VERSION = "2026-08-confenge-v1"
PRODUCTION_OUTBOX_PATH = "/var/lib/smartlic/lead-outbox.jsonl"
DEV_OUTBOX_PATH = "/tmp/smartlic-lead-outbox.jsonl"
PII_FIELDS = frozenset({"email", "nome", "empresa", "telefone", "mensagem"})
UNFINISHED = frozenset({"accepted", "queued", "failed"})

_LOCK = threading.Lock()
_MEMORY: dict[str, dict[str, Any]] = {}
_INDEX = {"loaded": False}


class LeadOutboxError(RuntimeError):
    """Durable persist failed. Caller must not claim success."""


def outbox_path() -> Path:
    configured = os.getenv("LEAD_OUTBOX_PATH")
    if configured:
        return Path(configured)
    if Path("/var/lib/smartlic").is_dir():
        return Path(PRODUCTION_OUTBOX_PATH)
    return Path(DEV_OUTBOX_PATH)


def reset_outbox_state() -> None:
    """Test helper. Does not delete the file."""
    with _LOCK:
        _MEMORY.clear()
        _INDEX["loaded"] = False


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


def _referrer_host(referrer: str) -> str:
    parsed = urlparse(referrer)
    host = (parsed.hostname or "").lower().rstrip(".")
    if host:
        return host
    # Bare host or path-only input — never substring-match "x.com" in a path.
    candidate = referrer.split("/", 1)[0].split(":", 1)[0].lower()
    return candidate


def _host_matches(host: str, *roots: str) -> bool:
    return any(host == root or host.endswith(f".{root}") for root in roots)


def classify_referrer(referrer: str | None) -> str:
    if not referrer:
        return "direct"
    host = _referrer_host(referrer)
    if _host_matches(host, "google.com", "google.com.br", "bing.com", "duckduckgo.com"):
        return "organic_search"
    if _host_matches(host, "smartlic.tech"):
        return "internal"
    if _host_matches(host, "linkedin.com", "twitter.com", "x.com"):
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


def _durable_line(record: dict[str, Any]) -> dict[str, Any]:
    # Persist contact fields server-side. Never persist free-text mensagem.
    return {key: value for key, value in record.items() if key != "mensagem"}


def _persist_jsonl(record: dict[str, Any]) -> None:
    path = outbox_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(_durable_line(record), ensure_ascii=False, default=str) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def _load_index_locked() -> None:
    if _INDEX["loaded"]:
        return
    path = outbox_path()
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    record = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("lead_outbox_corrupt_line")
                    continue
                key = record.get("idempotency_key")
                if key:
                    _MEMORY[str(key)] = record
    _INDEX["loaded"] = True


def _handoff(record: dict[str, Any]) -> None:
    try:
        from leads.handoff import deliver_handoff

        deliver_handoff(record)
    except Exception:
        record["handoff_state"] = "failed"
        logger.warning("lead_handoff_failed receipt=%s", record["receipt_id"], exc_info=True)
    try:
        _persist_jsonl(record)
    except OSError:
        logger.warning("lead_outbox_state_persist_failed receipt=%s", record["receipt_id"])


def accept_lead(payload: dict[str, Any]) -> dict[str, Any]:
    """Persist first, then attempt handoff. Never depends on analytics."""
    key = build_idempotency_key(
        payload.get("email"),
        payload.get("telefone") or payload.get("phone"),
        str(payload.get("source") or "unknown"),
        payload.get("cta_id"),
        payload.get("entity_public_id"),
    )
    with _LOCK:
        _load_index_locked()
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
        try:
            _persist_jsonl(record)
        except OSError as exc:
            raise LeadOutboxError("persist_failed") from exc
        _MEMORY[key] = record

    _handoff(record)
    return record


def reprocess_unfinished(limit: int = 50) -> list[dict[str, Any]]:
    """Retry queued/failed/accepted leads without minting a new receipt."""
    with _LOCK:
        _load_index_locked()
        pending = [
            record
            for record in _MEMORY.values()
            if record.get("handoff_state") in UNFINISHED
        ][:limit]
    processed: list[dict[str, Any]] = []
    for record in pending:
        _handoff(record)
        processed.append(record)
    return processed


def redact_for_log(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key not in PII_FIELDS}
