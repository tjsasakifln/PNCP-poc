"""
Multi-source consolidation services.

This package provides the infrastructure for fetching procurement data
from multiple sources (PNCP, BLL, Portal, BNC, Licitar) and consolidating
them into a unified format with deduplication.
"""

from services.models import (
    SourceStatus,
    SourceCapability,
    SourceMetadata,
    UnifiedProcurement,
    SourceStats,
    ConsolidationResult,
)
from services.base import SourceAdapter
from services.exceptions import (
    SourceError,
    SourceTimeoutError,
    SourceAPIError,
    SourceRateLimitError,
    SourceParseError,
    DeduplicationError,
    ConsolidationError,
)
from services.consolidation import ConsolidationService
from services.deduplication import DeduplicationService
from services.source_registry import SourceRegistry

__all__ = [
    # Models
    "SourceStatus",
    "SourceCapability",
    "SourceMetadata",
    "UnifiedProcurement",
    "SourceStats",
    "ConsolidationResult",
    # Base class
    "SourceAdapter",
    # Exceptions
    "SourceError",
    "SourceTimeoutError",
    "SourceAPIError",
    "SourceRateLimitError",
    "SourceParseError",
    "DeduplicationError",
    "ConsolidationError",
    # Services
    "ConsolidationService",
    "DeduplicationService",
    "SourceRegistry",
]
