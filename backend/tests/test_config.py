"""Tests for configuration module, including logging setup."""

import logging
import os
import sys
from unittest.mock import patch

import pytest

from config import setup_logging, RetryConfig, validate_env_vars


class TestSetupLogging:
    """Test suite for setup_logging() function."""

    def teardown_method(self):
        """Clean up logging configuration after each test."""
        # Remove all handlers from root logger
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()

        # Reset all loggers to default state
        for logger_name in ["urllib3", "httpx", "test_logger"]:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.NOTSET)
            logger.propagate = True

    def test_default_level_is_info(self):
        """Test that default logging level is INFO."""
        setup_logging()
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_custom_level_debug(self):
        """Test setting custom DEBUG level."""
        setup_logging("DEBUG")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_custom_level_warning(self):
        """Test setting custom WARNING level."""
        setup_logging("WARNING")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    def test_custom_level_error(self):
        """Test setting custom ERROR level."""
        setup_logging("ERROR")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.ERROR

    def test_level_case_insensitive(self):
        """Test that level parameter is case-insensitive."""
        setup_logging("debug")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

        # Clean up and test uppercase
        self.teardown_method()
        setup_logging("DEBUG")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_formatter_format(self):
        """Test that formatter uses correct format string."""
        setup_logging()
        root_logger = logging.getLogger()

        # Find our StreamHandler (pytest may add its own handler)
        stream_handlers = [
            h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(stream_handlers) > 0

        # Get our handler (the one that outputs to stdout)
        handler = None
        for h in stream_handlers:
            if hasattr(h, "stream") and h.stream == sys.stdout:
                handler = h
                break

        assert handler is not None, "StreamHandler with stdout not found"
        formatter = handler.formatter

        assert (
            formatter._fmt == "%(asctime)s | %(levelname)-8s | req=%(request_id)s | search=%(search_id)s | %(name)s | %(message)s"
        )

    def test_formatter_datefmt(self):
        """Test that formatter uses correct date format."""
        setup_logging()
        root_logger = logging.getLogger()

        # Find our StreamHandler
        stream_handlers = [
            h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        handler = None
        for h in stream_handlers:
            if hasattr(h, "stream") and h.stream == sys.stdout:
                handler = h
                break

        assert handler is not None
        formatter = handler.formatter

        assert formatter.datefmt == "%Y-%m-%d %H:%M:%S"

    def test_handler_is_stream_handler(self):
        """Test that a StreamHandler is added to root logger."""
        setup_logging()
        root_logger = logging.getLogger()

        # Check that at least one StreamHandler exists
        stream_handlers = [
            h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(stream_handlers) > 0

    def test_handler_outputs_to_stdout(self):
        """Test that handler outputs to sys.stdout."""
        setup_logging()
        root_logger = logging.getLogger()

        # Find handler that outputs to stdout
        stdout_handlers = [
            h
            for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and hasattr(h, "stream")
            and h.stream == sys.stdout
        ]

        assert len(stdout_handlers) > 0, "No StreamHandler outputting to stdout found"

    def test_urllib3_logger_set_to_warning(self):
        """Test that urllib3 logger is set to WARNING level."""
        setup_logging("DEBUG")  # Root at DEBUG
        urllib3_logger = logging.getLogger("urllib3")

        assert urllib3_logger.level == logging.WARNING

    def test_httpx_logger_set_to_warning(self):
        """Test that httpx logger is set to WARNING level."""
        setup_logging("DEBUG")  # Root at DEBUG
        httpx_logger = logging.getLogger("httpx")

        assert httpx_logger.level == logging.WARNING

    def test_logging_output_format(self, caplog):
        """Test that logging output matches expected format."""
        setup_logging("INFO")

        # Capture logs directly via caplog
        logger = logging.getLogger("test_logger")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        # Check that the log was captured
        assert len(caplog.records) == 1
        record = caplog.records[0]

        assert record.levelname == "INFO"
        assert record.name == "test_logger"
        assert record.message == "Test message"

    def test_debug_messages_filtered_at_info_level(self, caplog):
        """Test that DEBUG messages are filtered when level is INFO."""
        setup_logging("INFO")
        logger = logging.getLogger("test_logger")

        with caplog.at_level(logging.INFO):
            logger.debug("This should not appear")
            logger.info("This should appear")

        # Only INFO message should be captured
        messages = [rec.message for rec in caplog.records]
        assert "This should not appear" not in messages
        assert "This should appear" in messages

    def test_info_messages_visible_at_debug_level(self, caplog):
        """Test that INFO messages are visible when level is DEBUG."""
        setup_logging("DEBUG")
        logger = logging.getLogger("test_logger")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")

        messages = [rec.message for rec in caplog.records]
        assert "Debug message" in messages
        assert "Info message" in messages

    def test_urllib3_verbose_logs_suppressed(self, caplog):
        """Test that urllib3 DEBUG/INFO logs are suppressed."""
        setup_logging("DEBUG")  # Root at DEBUG
        urllib3_logger = logging.getLogger("urllib3")

        with caplog.at_level(logging.DEBUG):
            urllib3_logger.debug("This should be suppressed")
            urllib3_logger.info("This should also be suppressed")
            urllib3_logger.warning("This should appear")

        messages = [rec.message for rec in caplog.records]
        assert "This should be suppressed" not in messages
        assert "This should also be suppressed" not in messages
        assert "This should appear" in messages

    def test_httpx_verbose_logs_suppressed(self, caplog):
        """Test that httpx DEBUG/INFO logs are suppressed."""
        setup_logging("DEBUG")  # Root at DEBUG
        httpx_logger = logging.getLogger("httpx")

        with caplog.at_level(logging.DEBUG):
            httpx_logger.debug("This should be suppressed")
            httpx_logger.info("This should also be suppressed")
            httpx_logger.warning("This should appear")

        messages = [rec.message for rec in caplog.records]
        assert "This should be suppressed" not in messages
        assert "This should also be suppressed" not in messages
        assert "This should appear" in messages

    def test_multiple_calls_idempotent(self):
        """STORY-330 AC3: Calling setup_logging() 2x yields exactly 1 StreamHandler.

        Root cause of STORY-330: Gunicorn logconfig_dict adds a handler, then
        each worker's setup_logging() added another → 2 handlers → every log 2x.
        After fix, setup_logging() clears existing handlers before adding its own.
        """
        setup_logging("INFO")
        setup_logging("DEBUG")

        root_logger = logging.getLogger()
        stdout_handlers = [
            h for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and hasattr(h, "stream") and h.stream == sys.stdout
        ]
        assert len(stdout_handlers) == 1, (
            f"Expected exactly 1 stdout StreamHandler, got {len(stdout_handlers)}"
        )
        # Level should reflect the LAST call
        assert root_logger.level == logging.DEBUG

    def test_setup_after_preexisting_handler_replaces_it(self):
        """STORY-330 AC1: setup_logging clears pre-existing handlers (Gunicorn scenario).

        Simulates Gunicorn's logconfig_dict adding a handler to root logger
        BEFORE setup_logging() runs in the worker.
        """
        root_logger = logging.getLogger()
        # Simulate Gunicorn's pre-existing handler
        gunicorn_handler = logging.StreamHandler(sys.stderr)
        root_logger.addHandler(gunicorn_handler)
        pre_count = len(root_logger.handlers)
        assert pre_count >= 1

        setup_logging("INFO")

        # After setup_logging, only our stdout handler should remain
        stdout_handlers = [
            h for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and hasattr(h, "stream") and h.stream == sys.stdout
        ]
        assert len(stdout_handlers) == 1
        # The old stderr handler should be gone
        assert gunicorn_handler not in root_logger.handlers


class TestRetryConfig:
    """Test suite for RetryConfig dataclass."""

    def test_default_values(self):
        """Test that RetryConfig has correct default values."""
        config = RetryConfig()

        assert config.max_retries == 1  # PNCP_MAX_RETRIES default
        assert config.base_delay == 1.5
        assert config.max_delay == 15.0
        assert config.exponential_base == 2
        assert config.jitter is True
        assert config.timeout == 15  # PNCP_READ_TIMEOUT default

    def test_retryable_status_codes_default(self):
        """Test default retryable HTTP status codes."""
        config = RetryConfig()

        expected_codes = (408, 422, 429, 500, 502, 503, 504)
        assert config.retryable_status_codes == expected_codes

    def test_retryable_exceptions_default(self):
        """Test default retryable exception types include builtins + httpx."""
        import httpx
        config = RetryConfig()

        # DEBT-107: Migrated from requests.exceptions to httpx exceptions
        assert ConnectionError in config.retryable_exceptions
        assert TimeoutError in config.retryable_exceptions
        assert httpx.TimeoutException in config.retryable_exceptions
        assert httpx.ConnectError in config.retryable_exceptions
        assert httpx.ReadError in config.retryable_exceptions

    def test_custom_values(self):
        """Test creating RetryConfig with custom values."""
        config = RetryConfig(
            max_retries=10,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=3,
            jitter=False,
            timeout=60,
        )

        assert config.max_retries == 10
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 3
        assert config.jitter is False
        assert config.timeout == 60

    def test_custom_retryable_status_codes(self):
        """Test custom retryable status codes."""
        custom_codes = (400, 401, 403)
        config = RetryConfig(retryable_status_codes=custom_codes)

        assert config.retryable_status_codes == custom_codes

    def test_custom_retryable_exceptions(self):
        """Test custom retryable exceptions."""
        custom_exceptions = (ValueError, RuntimeError)
        config = RetryConfig(retryable_exceptions=custom_exceptions)

        assert config.retryable_exceptions == custom_exceptions


class TestValidateEnvVarsMixpanelToken:
    """MON-FN-005: MIXPANEL_TOKEN must be required in production.

    Memory `reference_mixpanel_backend_token_gap_2026_04_24` — token was
    silently absent in prod, suppressing paywall_hit/trial_started events
    for an unknown period. Boot fail closes the gap.
    """

    @patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "SUPABASE_URL": "https://x.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "k",
        "SUPABASE_JWT_SECRET": "s",
        "STRIPE_WEBHOOK_SECRET": "w",
        "MIXPANEL_TOKEN": "",
    }, clear=False)
    def test_mixpanel_missing_in_production_raises(self):
        with pytest.raises(RuntimeError, match="MIXPANEL_TOKEN"):
            validate_env_vars()

    @patch.dict(os.environ, {
        "ENVIRONMENT": "development",
        "SUPABASE_URL": "https://x.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "k",
        "SUPABASE_JWT_SECRET": "s",
        "STRIPE_WEBHOOK_SECRET": "w",
        "MIXPANEL_TOKEN": "",
    }, clear=False)
    def test_mixpanel_missing_in_dev_only_warns(self, caplog):
        with caplog.at_level(logging.WARNING):
            validate_env_vars()
        assert any("MIXPANEL_TOKEN" in r.message for r in caplog.records)

    @patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "SUPABASE_URL": "https://x.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "k",
        "SUPABASE_JWT_SECRET": "s",
        "STRIPE_WEBHOOK_SECRET": "w",
        "MIXPANEL_TOKEN": "bc4162c2267b4c415357a02e2ef39cdc",
    }, clear=False)
    def test_mixpanel_present_in_production_passes(self):
        validate_env_vars()
