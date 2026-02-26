"""Configuration models for PNCP client."""

from dataclasses import dataclass, field
from typing import Tuple, Type
import logging
import sys


@dataclass
class RetryConfig:
    """Configuration for HTTP retry logic."""

    max_retries: int = 5
    base_delay: float = 2.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: int = 2
    jitter: bool = True
    timeout: int = 30  # seconds

    # HTTP status codes that should trigger retry
    retryable_status_codes: Tuple[int, ...] = field(
        default_factory=lambda: (408, 429, 500, 502, 503, 504)
    )

    # Exception types that should trigger retry
    retryable_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=lambda: (
            ConnectionError,
            TimeoutError,
        )
    )


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application.

    Sets up a consistent logging format across all modules with proper
    level filtering and suppression of verbose third-party libraries.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to INFO.

    Example:
        >>> setup_logging("DEBUG")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
        2026-01-25 23:00:00 | INFO     | __main__ | Application started
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(handler)

    # Silence verbose logs from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


import os as _os

# ============================================================================
# Feature Flags
# ============================================================================

ENABLE_NEW_PRICING = _os.getenv("ENABLE_NEW_PRICING", "true").lower() in ("true", "1", "yes", "on")

# ============================================================================
# STORY-278: Daily Digest Configuration
# ============================================================================

DIGEST_ENABLED = _os.getenv("DIGEST_ENABLED", "false").lower() in ("true", "1", "yes", "on")
DIGEST_HOUR_UTC = int(_os.getenv("DIGEST_HOUR_UTC", "10"))  # 10:00 UTC = 7:00 BRT
DIGEST_MAX_PER_EMAIL = int(_os.getenv("DIGEST_MAX_PER_EMAIL", "10"))
DIGEST_BATCH_SIZE = 100  # Resend API limit per batch call
