"""Persistent audit logger for security-relevant events.

STORY-226 Track 5 (AC18-AC20): Writes audit events both to structured stdout
logging AND to the Supabase `audit_events` table for long-term persistence.

All user IDs and IP addresses are hashed with SHA-256 (truncated to 16 hex
chars) before storage to comply with LGPD/GDPR privacy requirements.

Usage:
    from audit import audit_logger

    # Log an authentication event
    await audit_logger.log(
        event_type="auth.login",
        actor_id="550e8400-e29b-41d4-a716-446655440000",
        ip_address="192.168.1.100",
        details={"method": "password"},
    )

    # Log an admin action
    await audit_logger.log(
        event_type="admin.plan_assign",
        actor_id=admin_user_id,
        target_id=target_user_id,
        ip_address=client_ip,
        details={"plan": "professional", "previous_plan": "starter"},
    )
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Optional, Set

from middleware import request_id_var

logger = logging.getLogger(__name__)


# ============================================================================
# Valid event types — any event not in this set is rejected
# ============================================================================

VALID_EVENT_TYPES: Set[str] = {
    "auth.login",
    "auth.logout",
    "auth.signup",
    "admin.user_create",
    "admin.user_delete",
    "admin.plan_assign",
    "billing.checkout",
    "billing.subscription_change",
    "data.search",
    "data.download",
}


# ============================================================================
# Privacy-safe hashing
# ============================================================================

def hash_identifier(value: Optional[str]) -> Optional[str]:
    """Hash a PII value (user ID, IP) with SHA-256, truncated to 16 hex chars.

    This provides a consistent, privacy-safe identifier that:
    - Cannot be reversed to the original value
    - Is deterministic (same input always produces same output)
    - Is short enough for readable logs and efficient storage

    Args:
        value: The raw identifier to hash. Returns None if value is None/empty.

    Returns:
        First 16 characters of the SHA-256 hex digest, or None.
    """
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


# ============================================================================
# AuditLogger
# ============================================================================

class AuditLogger:
    """Dual-destination audit logger: stdout (structured) + Supabase table.

    The logger writes every event to:
    1. **stdout** via Python logging (immediate, always available)
    2. **Supabase audit_events table** (persistent, queryable, 12-month retention)

    If the Supabase write fails (e.g., network error, misconfiguration), the
    event is still logged to stdout and the error is logged as a warning.
    This ensures audit visibility is never lost due to transient DB issues.

    Thread/async safety:
    - Uses the request_id_var context variable for correlation IDs
    - Supabase writes are async-safe (called with await)
    """

    async def log(
        self,
        event_type: str,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log an audit event to stdout and Supabase.

        Args:
            event_type: One of VALID_EVENT_TYPES (e.g., 'auth.login').
            actor_id: Raw user ID of the actor (will be hashed before storage).
            target_id: Raw user ID of the target (will be hashed before storage).
            ip_address: Raw client IP address (will be hashed before storage).
            details: Optional structured metadata (must not contain PII).

        Raises:
            ValueError: If event_type is not in VALID_EVENT_TYPES.
        """
        if event_type not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid audit event type: '{event_type}'. "
                f"Valid types: {sorted(VALID_EVENT_TYPES)}"
            )

        # Hash PII before any logging or storage
        actor_hash = hash_identifier(actor_id)
        target_hash = hash_identifier(target_id)
        ip_hash = hash_identifier(ip_address)

        # Get correlation ID from middleware context
        request_id = request_id_var.get("-")

        # --- 1. Structured stdout logging (always succeeds) ---
        log_data = {
            "event_type": event_type,
            "actor_id_hash": actor_hash,
            "target_id_hash": target_hash,
            "ip_hash": ip_hash,
            "request_id": request_id,
        }
        if details:
            log_data["details"] = details

        logger.info(
            f"AUDIT {event_type} actor={actor_hash or '-'} "
            f"target={target_hash or '-'} ip={ip_hash or '-'} "
            f"[req_id={request_id}]",
            extra=log_data,
        )

        # --- 2. Persist to Supabase audit_events table ---
        row = {
            "event_type": event_type,
            "actor_id_hash": actor_hash,
            "target_id_hash": target_hash,
            "ip_hash": ip_hash,
            "details": {
                **(details or {}),
                "request_id": request_id,
            },
        }

        try:
            from supabase_client import get_supabase

            supabase = get_supabase()
            supabase.table("audit_events").insert(row).execute()
        except Exception as e:
            # Never let a DB write failure suppress the audit event.
            # The stdout log above already captured it.
            logger.warning(
                f"Failed to persist audit event to Supabase: {e} "
                f"(event_type={event_type}, req_id={request_id})"
            )

    def log_sync(
        self,
        event_type: str,
        actor_id: Optional[str] = None,
        target_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Synchronous version of log() for non-async contexts.

        Same behavior as log() but does not require await.
        Useful in synchronous route handlers or middleware.
        """
        if event_type not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid audit event type: '{event_type}'. "
                f"Valid types: {sorted(VALID_EVENT_TYPES)}"
            )

        actor_hash = hash_identifier(actor_id)
        target_hash = hash_identifier(target_id)
        ip_hash = hash_identifier(ip_address)

        request_id = request_id_var.get("-")

        log_data = {
            "event_type": event_type,
            "actor_id_hash": actor_hash,
            "target_id_hash": target_hash,
            "ip_hash": ip_hash,
            "request_id": request_id,
        }
        if details:
            log_data["details"] = details

        logger.info(
            f"AUDIT {event_type} actor={actor_hash or '-'} "
            f"target={target_hash or '-'} ip={ip_hash or '-'} "
            f"[req_id={request_id}]",
            extra=log_data,
        )

        row = {
            "event_type": event_type,
            "actor_id_hash": actor_hash,
            "target_id_hash": target_hash,
            "ip_hash": ip_hash,
            "details": {
                **(details or {}),
                "request_id": request_id,
            },
        }

        try:
            from supabase_client import get_supabase

            supabase = get_supabase()
            supabase.table("audit_events").insert(row).execute()
        except Exception as e:
            logger.warning(
                f"Failed to persist audit event to Supabase: {e} "
                f"(event_type={event_type}, req_id={request_id})"
            )


# Module-level singleton — import and use directly:
#   from audit import audit_logger
#   await audit_logger.log("auth.login", actor_id=user_id, ...)
audit_logger = AuditLogger()
