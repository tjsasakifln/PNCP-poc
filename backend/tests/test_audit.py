"""Tests for audit.py — STORY-226 Track 5 (AC18-AC20).

Covers:
- hash_identifier privacy hashing
- AuditLogger event validation
- AuditLogger stdout logging
- AuditLogger Supabase persistence (mocked)
- Graceful degradation when Supabase is unavailable
"""

import hashlib
import logging
from unittest.mock import patch, MagicMock

import pytest

from audit import (
    AuditLogger,
    VALID_EVENT_TYPES,
    audit_logger,
    hash_identifier,
)


# ============================================================================
# hash_identifier
# ============================================================================

class TestHashIdentifier:
    """Tests for SHA-256 truncated hashing of PII."""

    def test_returns_16_char_hex(self):
        result = hash_identifier("test-user-id")
        assert result is not None
        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        """Same input always produces same output."""
        assert hash_identifier("user-123") == hash_identifier("user-123")

    def test_different_inputs_different_hashes(self):
        """Different inputs produce different hashes (with very high probability)."""
        h1 = hash_identifier("user-1")
        h2 = hash_identifier("user-2")
        assert h1 != h2

    def test_matches_sha256_prefix(self):
        """Verify hash matches first 16 chars of SHA-256 hex digest."""
        value = "550e8400-e29b-41d4-a716-446655440000"
        expected = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
        assert hash_identifier(value) == expected

    def test_none_returns_none(self):
        assert hash_identifier(None) is None

    def test_empty_string_returns_none(self):
        assert hash_identifier("") is None

    def test_ip_address_hashed(self):
        result = hash_identifier("192.168.1.100")
        assert result is not None
        assert len(result) == 16


# ============================================================================
# VALID_EVENT_TYPES
# ============================================================================

class TestValidEventTypes:
    """Verify the set of valid event types matches AC18 spec."""

    EXPECTED_TYPES = {
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

    def test_all_expected_types_present(self):
        for event_type in self.EXPECTED_TYPES:
            assert event_type in VALID_EVENT_TYPES, f"Missing event type: {event_type}"

    def test_no_extra_types(self):
        assert VALID_EVENT_TYPES == self.EXPECTED_TYPES


# ============================================================================
# AuditLogger.log (async)
# ============================================================================

class TestAuditLoggerAsync:
    """Tests for the async log() method."""

    @pytest.mark.asyncio
    async def test_valid_event_logs_to_stdout(self, caplog):
        """Valid event is logged to stdout with hashed identifiers."""
        with caplog.at_level(logging.INFO, logger="audit"):
            with patch("supabase_client.get_supabase") as mock_sb:
                mock_table = MagicMock()
                mock_sb.return_value.table.return_value = mock_table
                mock_table.insert.return_value.execute.return_value = None

                await audit_logger.log(
                    event_type="auth.login",
                    actor_id="user-123",
                    ip_address="10.0.0.1",
                    details={"method": "password"},
                )

        assert "AUDIT auth.login" in caplog.text
        # Actor hash should be present, not raw ID
        actor_hash = hash_identifier("user-123")
        assert actor_hash in caplog.text
        # Raw user ID must NOT appear
        assert "user-123" not in caplog.text

    @pytest.mark.asyncio
    async def test_valid_event_persists_to_supabase(self):
        """Valid event writes a row to the audit_events table."""
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_table = MagicMock()
            mock_sb.return_value.table.return_value = mock_table
            mock_table.insert.return_value.execute.return_value = None

            await audit_logger.log(
                event_type="admin.plan_assign",
                actor_id="admin-1",
                target_id="user-2",
                ip_address="192.168.1.1",
                details={"plan": "professional"},
            )

            # Verify insert was called
            mock_sb.return_value.table.assert_called_once_with("audit_events")
            insert_call = mock_table.insert.call_args[0][0]
            assert insert_call["event_type"] == "admin.plan_assign"
            assert insert_call["actor_id_hash"] == hash_identifier("admin-1")
            assert insert_call["target_id_hash"] == hash_identifier("user-2")
            assert insert_call["ip_hash"] == hash_identifier("192.168.1.1")
            assert insert_call["details"]["plan"] == "professional"

    @pytest.mark.asyncio
    async def test_invalid_event_type_raises_value_error(self):
        """Invalid event type raises ValueError immediately."""
        with pytest.raises(ValueError, match="Invalid audit event type"):
            await audit_logger.log(event_type="invalid.type")

    @pytest.mark.asyncio
    async def test_supabase_failure_does_not_suppress_stdout(self, caplog):
        """If Supabase write fails, the event still appears in stdout."""
        with caplog.at_level(logging.INFO, logger="audit"):
            with patch("supabase_client.get_supabase", side_effect=RuntimeError("DB down")):
                await audit_logger.log(
                    event_type="auth.login",
                    actor_id="user-x",
                )

        # Event was logged to stdout despite Supabase failure
        assert "AUDIT auth.login" in caplog.text
        # Warning about the Supabase failure was also logged
        assert "Failed to persist audit event" in caplog.text

    @pytest.mark.asyncio
    async def test_optional_fields_can_be_none(self, caplog):
        """All optional fields (actor_id, target_id, ip_address, details) can be None."""
        with caplog.at_level(logging.INFO, logger="audit"):
            with patch("supabase_client.get_supabase") as mock_sb:
                mock_table = MagicMock()
                mock_sb.return_value.table.return_value = mock_table
                mock_table.insert.return_value.execute.return_value = None

                await audit_logger.log(event_type="data.search")

        assert "AUDIT data.search" in caplog.text
        # Hashes should be None
        insert_call = mock_sb.return_value.table.return_value.insert.call_args[0][0]
        assert insert_call["actor_id_hash"] is None
        assert insert_call["target_id_hash"] is None
        assert insert_call["ip_hash"] is None


# ============================================================================
# AuditLogger.log_sync (synchronous)
# ============================================================================

class TestAuditLoggerSync:
    """Tests for the synchronous log_sync() method."""

    def test_sync_logs_to_stdout(self, caplog):
        """Sync version also logs to stdout."""
        with caplog.at_level(logging.INFO, logger="audit"):
            with patch("supabase_client.get_supabase") as mock_sb:
                mock_table = MagicMock()
                mock_sb.return_value.table.return_value = mock_table
                mock_table.insert.return_value.execute.return_value = None

                audit_logger.log_sync(
                    event_type="billing.checkout",
                    actor_id="buyer-1",
                    details={"plan": "starter", "amount": 29.90},
                )

        assert "AUDIT billing.checkout" in caplog.text

    def test_sync_invalid_event_raises(self):
        """Invalid event type raises ValueError in sync version too."""
        with pytest.raises(ValueError, match="Invalid audit event type"):
            audit_logger.log_sync(event_type="bogus.event")

    def test_sync_supabase_failure_graceful(self, caplog):
        """Supabase failure in sync mode is handled gracefully."""
        with caplog.at_level(logging.WARNING, logger="audit"):
            with patch("supabase_client.get_supabase", side_effect=Exception("timeout")):
                audit_logger.log_sync(event_type="data.download", actor_id="u1")

        assert "Failed to persist audit event" in caplog.text


# ============================================================================
# Module-level singleton
# ============================================================================

class TestModuleSingleton:
    """Verify the module-level audit_logger singleton."""

    def test_singleton_is_audit_logger_instance(self):
        assert isinstance(audit_logger, AuditLogger)

    def test_singleton_same_instance(self):
        from audit import audit_logger as a1
        from audit import audit_logger as a2
        assert a1 is a2
