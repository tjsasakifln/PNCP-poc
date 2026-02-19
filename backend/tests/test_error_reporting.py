"""Tests for centralized error reporting helper (GTM-RESILIENCE-E02).

Validates:
  - Expected errors emit logger.warning (no traceback) + Sentry capture
  - Unexpected errors emit logger.error (with traceback) + Sentry capture
  - Tags are set on Sentry scope before capture
  - Custom logger instances are respected
"""

import logging
import pytest
from unittest.mock import patch, MagicMock

from utils.error_reporting import report_error


class TestReportErrorExpected:
    """AC1: Expected/transient errors — warning level, no traceback."""

    @patch("utils.error_reporting.sentry_sdk")
    def test_expected_error_logs_warning(self, mock_sentry, caplog):
        error = TimeoutError("connection timed out")
        with caplog.at_level(logging.WARNING):
            report_error(error, "PNCP fetch timeout", expected=True)

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) == 1
        assert "PNCP fetch timeout" in warning_records[0].message
        assert "TimeoutError" in warning_records[0].message
        assert "connection timed out" in warning_records[0].message

    @patch("utils.error_reporting.sentry_sdk")
    def test_expected_error_no_traceback(self, mock_sentry, caplog):
        error = ConnectionError("refused")
        with caplog.at_level(logging.WARNING):
            report_error(error, "Cache save failed", expected=True)

        warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(warning_records) == 1
        assert warning_records[0].exc_info is None or not warning_records[0].exc_info[0]

    @patch("utils.error_reporting.sentry_sdk")
    def test_expected_error_captures_sentry(self, mock_sentry):
        error = TimeoutError("timed out")
        report_error(error, "Fetch timeout", expected=True)

        mock_sentry.capture_exception.assert_called_once_with(error)

    @patch("utils.error_reporting.sentry_sdk")
    def test_expected_error_sets_tags(self, mock_sentry):
        error = TimeoutError("timed out")
        report_error(
            error, "PNCP timeout",
            expected=True, tags={"data_source": "pncp", "phase": "fetch"},
        )

        mock_sentry.set_tag.assert_any_call("data_source", "pncp")
        mock_sentry.set_tag.assert_any_call("phase", "fetch")


class TestReportErrorUnexpected:
    """AC1: Unexpected errors — error level, with traceback."""

    @patch("utils.error_reporting.sentry_sdk")
    def test_unexpected_error_logs_error(self, mock_sentry, caplog):
        error = ValueError("null pointer equivalent")
        with caplog.at_level(logging.ERROR):
            report_error(error, "Unexpected schema failure", expected=False)

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) == 1
        assert "Unexpected schema failure" in error_records[0].message
        assert "ValueError" in error_records[0].message

    @patch("utils.error_reporting.sentry_sdk")
    def test_unexpected_error_has_traceback(self, mock_sentry, caplog):
        error = RuntimeError("bug")
        with caplog.at_level(logging.ERROR):
            report_error(error, "Unexpected error", expected=False)

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) == 1
        assert error_records[0].exc_info is not None

    @patch("utils.error_reporting.sentry_sdk")
    def test_unexpected_error_captures_sentry(self, mock_sentry):
        error = RuntimeError("bug")
        report_error(error, "Bug found", expected=False)

        mock_sentry.capture_exception.assert_called_once_with(error)

    @patch("utils.error_reporting.sentry_sdk")
    def test_unexpected_error_no_tags(self, mock_sentry):
        error = RuntimeError("bug")
        report_error(error, "Bug found")

        mock_sentry.set_tag.assert_not_called()


class TestReportErrorCustomLogger:
    """Custom logger instance support."""

    @patch("utils.error_reporting.sentry_sdk")
    def test_uses_custom_logger(self, mock_sentry, caplog):
        custom_logger = logging.getLogger("custom.test.logger")
        error = TimeoutError("timeout")
        with caplog.at_level(logging.WARNING, logger="custom.test.logger"):
            report_error(error, "Custom log", expected=True, log=custom_logger)

        assert any("Custom log" in r.message and r.name == "custom.test.logger" for r in caplog.records)

    @patch("utils.error_reporting.sentry_sdk")
    def test_default_expected_is_false(self, mock_sentry, caplog):
        error = RuntimeError("test")
        with caplog.at_level(logging.ERROR):
            report_error(error, "Default behavior")

        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_records) == 1
