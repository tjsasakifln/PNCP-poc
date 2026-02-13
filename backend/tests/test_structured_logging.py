"""Tests for STORY-220: JSON Structured Logging.

Validates:
- AC3: JSON output includes all required fields
- AC4: Production defaults to JSON, development to text
- AC5: Existing log statements work without modification
- AC10: JSON format produces valid JSON for each log line
- AC11: request_id is present in JSON output during requests
- AC12: request_id defaults to "-" outside request context
- AC13: Development mode produces human-readable format
"""
import io
import json
import logging
import os
import sys
from unittest.mock import patch

import pytest

from config import setup_logging
from middleware import request_id_var


class TestJSONStructuredLogging:
    """Test JSON structured logging (STORY-220)."""

    def _clean_root_logger(self):
        """Remove all handlers and filters from root logger."""
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            handler.close()
        for f in root.filters[:]:
            root.removeFilter(f)
        root.setLevel(logging.WARNING)

    def setup_method(self):
        self._clean_root_logger()

    def teardown_method(self):
        self._clean_root_logger()
        for name in ("test_structured", "urllib3", "httpx"):
            lg = logging.getLogger(name)
            lg.setLevel(logging.NOTSET)
            lg.propagate = True

    def _setup_and_capture(self, env_overrides: dict) -> tuple:
        """Setup logging with env vars and return (buffer, logger).

        Replaces sys.stdout during setup_logging so the StreamHandler
        writes directly to our buffer. Then removes any extra handlers
        (e.g. pytest's) so only our handler remains.
        """
        self._clean_root_logger()
        buffer = io.StringIO()

        saved_stdout = sys.stdout
        try:
            sys.stdout = buffer
            with patch.dict(os.environ, env_overrides, clear=False):
                setup_logging("INFO")
        finally:
            sys.stdout = saved_stdout

        # Remove any handlers not writing to our buffer (pytest adds its own)
        root = logging.getLogger()
        for h in root.handlers[:]:
            is_ours = (
                isinstance(h, logging.StreamHandler)
                and getattr(h, "stream", None) is buffer
            )
            if not is_ours:
                root.removeHandler(h)

        return buffer, logging.getLogger("test_structured")

    # ── AC10: JSON format produces valid JSON ────────────────────────

    def test_json_format_produces_valid_json(self):
        """AC10: JSON format produces valid JSON for each log line."""
        buffer, logger = self._setup_and_capture({"LOG_FORMAT": "json"})

        logger.info("Test JSON validity")

        output = buffer.getvalue().strip()
        parsed = json.loads(output)  # Must not raise
        assert parsed["message"] == "Test JSON validity"

    # ── AC3: JSON includes all required fields ───────────────────────

    def test_json_includes_all_required_fields(self):
        """AC3: timestamp, level, request_id, logger_name, message, module, funcName, lineno."""
        buffer, logger = self._setup_and_capture({"LOG_FORMAT": "json"})

        logger.info("Field check")

        output = buffer.getvalue().strip()
        parsed = json.loads(output)

        required = [
            "timestamp", "level", "request_id", "logger_name",
            "message", "module", "funcName", "lineno",
        ]
        for field in required:
            assert field in parsed, f"Missing required field: {field}"

        assert parsed["logger_name"] == "test_structured"
        assert parsed["level"] == "INFO"
        assert isinstance(parsed["lineno"], int)

    # ── AC11: request_id present during requests ─────────────────────

    def test_request_id_present_in_json(self):
        """AC11: request_id is present in JSON output during requests."""
        buffer, logger = self._setup_and_capture({"LOG_FORMAT": "json"})

        token = request_id_var.set("req-abc-123")
        try:
            logger.info("Request scoped log")
            output = buffer.getvalue().strip()
            parsed = json.loads(output)
            assert parsed["request_id"] == "req-abc-123"
        finally:
            request_id_var.reset(token)

    # ── AC12: request_id defaults to "-" ─────────────────────────────

    def test_request_id_defaults_to_dash(self):
        """AC12: request_id defaults to '-' outside request context."""
        buffer, logger = self._setup_and_capture({"LOG_FORMAT": "json"})

        logger.info("No request context")

        output = buffer.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["request_id"] == "-"

    # ── AC13: Development mode human-readable format ─────────────────

    def test_text_format_pipe_delimited(self):
        """AC13: Text format uses human-readable pipe-delimited output."""
        buffer, logger = self._setup_and_capture(
            {"LOG_FORMAT": "text", "ENVIRONMENT": "development"}
        )

        logger.info("Dev mode message")

        output = buffer.getvalue().strip()

        # Must NOT be valid JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(output)

        # Must contain pipe delimiters and content
        assert "|" in output
        assert "Dev mode message" in output
        assert "INFO" in output

    # ── AC4: Default format based on environment ─────────────────────

    def test_production_defaults_to_json(self):
        """AC4: Production defaults to JSON when LOG_FORMAT is not set."""
        buffer, logger = self._setup_and_capture(
            {"ENVIRONMENT": "production", "LOG_FORMAT": ""}
        )

        logger.info("Production default")

        output = buffer.getvalue().strip()
        parsed = json.loads(output)
        assert parsed["message"] == "Production default"

    def test_development_defaults_to_text(self):
        """AC4: Development defaults to text when LOG_FORMAT is not set."""
        buffer, logger = self._setup_and_capture(
            {"ENVIRONMENT": "development", "LOG_FORMAT": ""}
        )

        logger.info("Dev default")

        output = buffer.getvalue().strip()

        with pytest.raises(json.JSONDecodeError):
            json.loads(output)
        assert "|" in output

    # ── AC5: Existing log patterns work unchanged ────────────────────

    def test_existing_log_patterns_work_in_json(self):
        """AC5: Various log patterns produce valid JSON without modification."""
        buffer, logger = self._setup_and_capture({"LOG_FORMAT": "json"})

        logger.info("Simple message")
        logger.warning("Warning with %s", "interpolation")
        logger.error("Error: %s", Exception("test error"))

        output = buffer.getvalue().strip()
        lines = [line for line in output.split("\n") if line.strip()]

        assert len(lines) == 3
        for line in lines:
            parsed = json.loads(line)  # Each line must be valid JSON
            assert "message" in parsed

    def test_existing_log_patterns_work_in_text(self):
        """AC5: Various log patterns work in text format."""
        buffer, logger = self._setup_and_capture(
            {"LOG_FORMAT": "text", "ENVIRONMENT": "development"}
        )

        logger.info("Simple message")
        logger.warning("Warning with %s", "interpolation")
        logger.error("Error: %s", Exception("test error"))

        output = buffer.getvalue()
        assert "Simple message" in output
        assert "Warning with interpolation" in output
        assert "Error: test error" in output


class TestImportTimeLogging:
    """Test that no logs are emitted before setup_logging (AC6/AC7)."""

    def test_log_feature_flags_is_callable(self):
        """AC6: log_feature_flags exists as a callable function."""
        from config import log_feature_flags
        assert callable(log_feature_flags)

    def test_log_feature_flags_emits_logs(self, caplog):
        """AC6: log_feature_flags emits expected log messages."""
        from config import log_feature_flags

        with caplog.at_level(logging.INFO, logger="config"):
            log_feature_flags()

        messages = " ".join(r.message for r in caplog.records)
        assert "ENABLE_NEW_PRICING" in messages
        assert "LLM_ARBITER_ENABLED" in messages
        assert "SYNONYM_MATCHING_ENABLED" in messages
        assert "ZERO_RESULTS_RELAXATION_ENABLED" in messages

    def test_config_import_does_not_emit_feature_flag_logs(self, caplog):
        """AC7: Importing config does not emit feature flag logs at import time."""
        import importlib

        with caplog.at_level(logging.INFO):
            # Force reimport
            import config
            importlib.reload(config)

        # Feature flag logs should NOT appear during import
        feature_flag_messages = [
            r for r in caplog.records
            if "Feature Flag" in r.message and r.name == "config"
        ]
        assert len(feature_flag_messages) == 0, (
            f"Feature flag logs emitted at import time: "
            f"{[r.message for r in feature_flag_messages]}"
        )


class TestSanitizedLoggerAdoption:
    """Test that critical modules use SanitizedLogAdapter (AC8/AC9)."""

    def test_auth_uses_sanitized_logger(self):
        """AC8: auth.py uses get_sanitized_logger."""
        import auth
        from log_sanitizer import SanitizedLogAdapter
        assert isinstance(auth.logger, SanitizedLogAdapter)

    def test_stripe_webhook_uses_sanitized_logger(self):
        """AC8: webhooks/stripe.py uses get_sanitized_logger."""
        from webhooks import stripe as stripe_mod
        from log_sanitizer import SanitizedLogAdapter
        assert isinstance(stripe_mod.logger, SanitizedLogAdapter)

    def test_search_route_uses_sanitized_logger(self):
        """AC8: routes/search.py uses get_sanitized_logger."""
        from routes import search as search_mod
        from log_sanitizer import SanitizedLogAdapter
        assert isinstance(search_mod.logger, SanitizedLogAdapter)

    def test_sanitized_logger_masks_email_in_message(self, caplog):
        """AC9: PII in log messages is automatically sanitized."""
        from log_sanitizer import get_sanitized_logger

        safe_logger = get_sanitized_logger("test_sanitized")

        with caplog.at_level(logging.INFO, logger="test_sanitized"):
            safe_logger.info("User login: user@example.com succeeded")

        assert "user@example.com" not in caplog.text
        assert "u***@example.com" in caplog.text
