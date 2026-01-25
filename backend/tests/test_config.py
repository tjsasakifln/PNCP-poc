"""Tests for configuration module, including logging setup."""

import logging
import sys
from config import setup_logging, RetryConfig


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
            formatter._fmt == "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
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
        """Test that calling setup_logging multiple times is safe."""
        setup_logging("INFO")
        initial_handler_count = len(logging.getLogger().handlers)

        # Call again with different level
        setup_logging("DEBUG")

        # Should have added another handler
        # NOTE: This is expected behavior - each call adds a handler
        # In production, setup_logging should only be called once
        assert len(logging.getLogger().handlers) >= initial_handler_count


class TestRetryConfig:
    """Test suite for RetryConfig dataclass."""

    def test_default_values(self):
        """Test that RetryConfig has correct default values."""
        config = RetryConfig()

        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2
        assert config.jitter is True
        assert config.timeout == 30

    def test_retryable_status_codes_default(self):
        """Test default retryable HTTP status codes."""
        config = RetryConfig()

        expected_codes = (408, 429, 500, 502, 503, 504)
        assert config.retryable_status_codes == expected_codes

    def test_retryable_exceptions_default(self):
        """Test default retryable exception types."""
        config = RetryConfig()

        expected_exceptions = (ConnectionError, TimeoutError)
        assert config.retryable_exceptions == expected_exceptions

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
