"""Multi-source procurement client adapters.

This package contains adapters for fetching procurement data from
various Brazilian government procurement portals. All adapters
implement the SourceAdapter interface for unified data handling.
"""

from clients.base import (
    SourceAdapter,
    SourceMetadata,
    SourceStatus,
    SourceCapability,
    SourceError,
    SourceTimeoutError,
    SourceAPIError,
    SourceRateLimitError,
    SourceAuthError,
    SourceParseError,
    UnifiedProcurement,
)

__all__ = [
    "SourceAdapter",
    "SourceMetadata",
    "SourceStatus",
    "SourceCapability",
    "SourceError",
    "SourceTimeoutError",
    "SourceAPIError",
    "SourceRateLimitError",
    "SourceAuthError",
    "SourceParseError",
    "UnifiedProcurement",
]
