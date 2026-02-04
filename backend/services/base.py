"""Base class for source adapters."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional, Set

from services.models import SourceMetadata, SourceStatus, UnifiedProcurement


class SourceAdapter(ABC):
    """
    Abstract base class for procurement source adapters.

    All source adapters MUST implement this interface to be used
    with the ConsolidationService.
    """

    @property
    @abstractmethod
    def metadata(self) -> SourceMetadata:
        """Return source metadata."""
        pass

    @property
    def name(self) -> str:
        """Human-readable source name."""
        return self.metadata.name

    @property
    def code(self) -> str:
        """Short code for logs/metrics."""
        return self.metadata.code

    @property
    def priority(self) -> int:
        """Source priority for deduplication (lower = higher priority)."""
        return self.metadata.priority

    @abstractmethod
    async def health_check(self) -> SourceStatus:
        """
        Check if source API is available.

        Returns:
            SourceStatus indicating current health

        Implementation notes:
            - MUST complete within 5 seconds
            - SHOULD use lightweight endpoint (e.g., HEAD request, health endpoint)
            - MUST NOT throw exceptions (return UNAVAILABLE instead)
        """
        pass

    @abstractmethod
    async def fetch(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[UnifiedProcurement, None]:
        """
        Fetch procurement records from this source.

        Args:
            data_inicial: Start date in YYYY-MM-DD format
            data_final: End date in YYYY-MM-DD format
            ufs: Optional set of Brazilian state codes (e.g., {"SP", "RJ"})
            **kwargs: Source-specific parameters

        Yields:
            UnifiedProcurement records one at a time (for memory efficiency)

        Raises:
            SourceTimeoutError: If source doesn't respond in time
            SourceAPIError: If source returns an error response
            SourceRateLimitError: If rate limit exceeded

        Implementation notes:
            - MUST handle pagination internally
            - MUST apply rate limiting internally
            - MUST normalize records to UnifiedProcurement before yielding
            - SHOULD log progress for long-running fetches
            - MAY filter by UF client-side if source doesn't support it
        """
        # This is required for the abstract method to be an async generator
        yield  # type: ignore
        pass

    @abstractmethod
    def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        """
        Convert source-specific record format to unified model.

        Args:
            raw_record: Raw record from source API

        Returns:
            UnifiedProcurement with all fields populated

        Implementation notes:
            - MUST set source_id and source_name
            - MUST generate dedup_key
            - MUST handle missing/null fields gracefully
            - SHOULD normalize text (remove extra whitespace, fix encoding)
        """
        pass

    async def close(self) -> None:
        """
        Clean up resources (HTTP sessions, connections, etc.).

        Called when adapter is no longer needed.
        """
        pass
