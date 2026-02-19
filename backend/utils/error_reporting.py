"""Centralized error reporting — avoids double emission (GTM-RESILIENCE-E02).

Establishes a single rule for error emission:
  - Expected/transient errors: logger.warning (1 line, no traceback) + Sentry with tags
  - Unexpected errors: logger.error (with traceback) + Sentry with tags
  - Operational degradation: logger.warning (1 line) + Sentry capture_message

This eliminates the pattern of logger.error(..., exc_info=True) + sentry_sdk.capture_exception()
which duplicates stack traces in stdout AND Sentry.
"""

import logging
from typing import Optional

import sentry_sdk

logger = logging.getLogger(__name__)


def report_error(
    error: Exception,
    message: str,
    *,
    expected: bool = False,
    tags: Optional[dict] = None,
    log: Optional[logging.Logger] = None,
) -> None:
    """Report an error to stdout (logger) and Sentry without duplication.

    Args:
        error: The exception to report.
        message: Human-readable context message.
        expected: If True, treats as transient (warning, no traceback).
        tags: Optional Sentry tags for filtering/grouping.
        log: Optional logger instance (defaults to module logger).

    Examples:
        # Timeout (expected/transient)
        report_error(e, "PNCP fetch timeout", expected=True,
                     tags={"data_source": "pncp"})

        # Bug (unexpected)
        report_error(e, "Unexpected schema validation failure")

        # Source degradation (expected)
        report_error(e, "All sources failed", expected=True,
                     tags={"data_source": "all_sources"})
    """
    _log = log or logger

    if tags:
        for k, v in tags.items():
            sentry_sdk.set_tag(k, v)

    if expected:
        _log.warning(f"{message}: {type(error).__name__}: {error}")
    else:
        _log.error(f"{message}: {type(error).__name__}: {error}", exc_info=True)

    sentry_sdk.capture_exception(error)
