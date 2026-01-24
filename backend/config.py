"""Configuration models for PNCP client."""
from dataclasses import dataclass, field
from typing import Tuple, Type


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
