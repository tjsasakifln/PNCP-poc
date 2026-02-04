"""Custom exceptions for multi-source consolidation."""

from typing import Any, Optional


class SourceError(Exception):
    """Base exception for source adapter errors."""

    def __init__(self, source_code: str, message: str):
        self.source_code = source_code
        self.message = message
        super().__init__(f"[{source_code}] {message}")


class SourceTimeoutError(SourceError):
    """Source did not respond within timeout period."""

    def __init__(self, source_code: str, timeout_seconds: int):
        super().__init__(source_code, f"Timeout after {timeout_seconds}s")
        self.timeout_seconds = timeout_seconds


class SourceAPIError(SourceError):
    """Source API returned an error response."""

    def __init__(self, source_code: str, status_code: int, body: str = ""):
        super().__init__(source_code, f"HTTP {status_code}: {body[:200]}")
        self.status_code = status_code
        self.body = body


class SourceRateLimitError(SourceAPIError):
    """Source rate limit exceeded."""

    def __init__(self, source_code: str, retry_after: Optional[int] = None):
        super().__init__(source_code, 429, "Rate limit exceeded")
        self.retry_after = retry_after


class SourceParseError(SourceError):
    """Failed to parse source response."""

    def __init__(self, source_code: str, field: str, value: Any):
        super().__init__(source_code, f"Failed to parse {field}: {value!r}")
        self.field = field
        self.value = value


class DeduplicationError(Exception):
    """Error during deduplication process."""
    pass


class ConsolidationError(Exception):
    """Error during consolidation process."""

    def __init__(
        self,
        message: str,
        partial_result: Optional["ConsolidationResult"] = None,  # noqa: F821
    ):
        super().__init__(message)
        self.partial_result = partial_result
