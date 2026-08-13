"""Minimal CONFENGE handoff. Email + log. Not a CRM."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

CONFENGE_HANDOFF_TO = "tiago.sasaki@confenge.com.br"


def deliver_handoff(record: dict[str, Any]) -> None:
    record["attempts"] = int(record.get("attempts") or 0) + 1
    sent = False
    try:
        from email_service import EMAIL_ENABLED, send_plain_email
    except Exception:
        send_plain_email = None
        EMAIL_ENABLED = False

    if EMAIL_ENABLED and send_plain_email:
        body = (
            f"receipt={record['receipt_id']}\n"
            f"source={record.get('source')}\n"
            f"cta={record.get('cta_id')}\n"
            f"family={record.get('route_family')}\n"
            f"entity={record.get('entity_type')}:{record.get('entity_public_id')}\n"
            f"landing={record.get('landing_url')}\n"
            f"referrer_class={record.get('referrer_class')}\n"
            f"nome={record.get('nome')}\n"
            f"empresa={record.get('empresa')}\n"
            f"email={record.get('email')}\n"
            f"telefone={record.get('telefone')}\n"
        )
        try:
            send_plain_email(
                to=CONFENGE_HANDOFF_TO,
                subject=f"[SmartLic lead] {record.get('cta_id') or record.get('source')}",
                body=body,
            )
            sent = True
        except TypeError:
            # email_service may not expose send_plain_email — still durable.
            logger.info("lead_handoff_email_adapter_missing receipt=%s", record["receipt_id"])
        except Exception:
            logger.warning("lead_handoff_email_failed receipt=%s", record["receipt_id"], exc_info=True)

    record["handoff_state"] = "delivered" if sent else "queued"
    logger.info(
        "lead_handoff_state=%s receipt=%s cta=%s family=%s",
        record["handoff_state"],
        record["receipt_id"],
        record.get("cta_id"),
        record.get("route_family"),
    )
