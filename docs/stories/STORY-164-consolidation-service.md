# Story MSP-001-09: Consolidation Service Implementation

**Story ID:** MSP-001-09
**GitHub Issue:** #164 (to be created)
**Epic:** MSP-001 (Multi-Source Procurement Consolidation)
**Sprint:** TBD
**Owner:** @dev
**Created:** February 3, 2026

---

## Story

**As a** backend developer,
**I want** to implement a consolidation service that aggregates data from all procurement sources,
**So that** users receive unified search results from multiple platforms in a single response.

---

## Objective

Create a consolidation service that:

1. Orchestrates parallel fetching from all enabled sources
2. Aggregates results from multiple clients
3. Deduplicates cross-platform listings
4. Handles partial failures gracefully
5. Provides transparent source attribution

---

## Acceptance Criteria

### AC1: Orchestration
- [ ] Parallel fetching from all enabled sources
- [ ] Configurable timeout per source
- [ ] Global request timeout
- [ ] Source-specific error isolation

### AC2: Aggregation
- [ ] Results merged from all sources
- [ ] Consistent sorting (by date, value, etc.)
- [ ] Pagination support for large result sets
- [ ] Source attribution preserved

### AC3: Deduplication
- [ ] Cross-source duplicate detection
- [ ] Fingerprint-based matching
- [ ] Priority rules for duplicate resolution
- [ ] Deduplication metrics captured

### AC4: Graceful Degradation
- [ ] Partial results returned when sources fail
- [ ] Failed sources reported in response
- [ ] No single source blocks others
- [ ] Retry failed sources on subsequent requests

### AC5: API Integration
- [ ] Updated `/api/buscar` endpoint
- [ ] Source filter parameter (optional)
- [ ] Response includes source metadata
- [ ] Backward compatible with existing API

### AC6: Monitoring
- [ ] Per-source metrics (count, latency, errors)
- [ ] Deduplication statistics
- [ ] Health check endpoint
- [ ] Logging for debugging

### AC7: Testing
- [ ] Unit tests for orchestration
- [ ] Unit tests for deduplication
- [ ] Integration tests with mocked clients
- [ ] 90%+ code coverage

---

## Technical Tasks

### Task 1: Source Manager (2 SP)
- [ ] Create `backend/services/source_manager.py`
- [ ] Implement source registration
- [ ] Implement health checks
- [ ] Implement enable/disable logic
- [ ] Add circuit breaker integration

### Task 2: Deduplication Service (3 SP)
- [ ] Create `backend/services/deduplication.py`
- [ ] Implement fingerprint generation
- [ ] Implement matching algorithm
- [ ] Implement priority resolution
- [ ] Add metrics collection

### Task 3: Consolidation Service (5 SP)
- [ ] Create `backend/services/consolidation.py`
- [ ] Implement parallel orchestration
- [ ] Implement result aggregation
- [ ] Implement error handling
- [ ] Integrate deduplication

### Task 4: API Updates (2 SP)
- [ ] Update `/api/buscar` endpoint
- [ ] Add source filter parameter
- [ ] Update response schema
- [ ] Ensure backward compatibility

### Task 5: Testing (1 SP)
- [ ] Create test suite for services
- [ ] Add integration tests
- [ ] Test failure scenarios

---

## Implementation Design

### Service Architecture

```
backend/services/
├── __init__.py
├── source_manager.py    # Source registration & health
├── deduplication.py     # Cross-source duplicate detection
└── consolidation.py     # Main orchestration service
```

### Source Manager

```python
# backend/services/source_manager.py

from dataclasses import dataclass
from typing import Dict, List
from clients.base_client import BaseClient, CircuitState
import logging

logger = logging.getLogger(__name__)

@dataclass
class SourceStatus:
    name: str
    enabled: bool
    healthy: bool
    circuit_state: CircuitState
    last_success: float | None
    last_error: str | None
    request_count: int
    error_count: int

class SourceManager:
    """Manages procurement data sources and their health status."""

    def __init__(self):
        self._sources: Dict[str, BaseClient] = {}
        self._enabled: Dict[str, bool] = {}

    def register(self, name: str, client: BaseClient, enabled: bool = True):
        """Register a new source client."""
        self._sources[name] = client
        self._enabled[name] = enabled
        logger.info(f"Registered source: {name} (enabled={enabled})")

    def get_enabled_sources(self) -> List[BaseClient]:
        """Get list of enabled and healthy sources."""
        return [
            client for name, client in self._sources.items()
            if self._enabled.get(name, False)
            and client.circuit_breaker.can_execute()
        ]

    def get_source(self, name: str) -> BaseClient | None:
        """Get a specific source by name."""
        return self._sources.get(name)

    def enable(self, name: str):
        """Enable a source."""
        if name in self._sources:
            self._enabled[name] = True
            logger.info(f"Enabled source: {name}")

    def disable(self, name: str):
        """Disable a source."""
        if name in self._sources:
            self._enabled[name] = False
            logger.info(f"Disabled source: {name}")

    def get_status(self) -> List[SourceStatus]:
        """Get status of all registered sources."""
        return [
            SourceStatus(
                name=name,
                enabled=self._enabled.get(name, False),
                healthy=client.circuit_breaker.state != CircuitState.OPEN,
                circuit_state=client.circuit_breaker.state,
                last_success=None,  # Track in client
                last_error=None,
                request_count=client._request_count,
                error_count=client.circuit_breaker.failure_count,
            )
            for name, client in self._sources.items()
        ]

# Global instance
source_manager = SourceManager()
```

### Deduplication Service

```python
# backend/services/deduplication.py

from typing import List, Dict
from schemas.unified_schema import UnifiedProcurement, SourceType
import hashlib
import logging

logger = logging.getLogger(__name__)

# Source priority for duplicate resolution (lower = higher priority)
SOURCE_PRIORITY = {
    SourceType.PNCP: 1,      # Official government source
    SourceType.BLL: 2,
    SourceType.PCP: 3,
    SourceType.BNC: 4,
    SourceType.LICITAR: 5,
}

class DeduplicationService:
    """Detects and resolves duplicate procurement records across sources."""

    def __init__(self):
        self._stats = {
            "total_input": 0,
            "total_output": 0,
            "duplicates_found": 0,
        }

    def deduplicate(
        self,
        items: List[UnifiedProcurement]
    ) -> List[UnifiedProcurement]:
        """
        Remove duplicate procurement records.

        Uses fingerprint matching to detect duplicates.
        When duplicates found, keeps the record from highest-priority source.
        """
        self._stats["total_input"] = len(items)

        # Group by fingerprint
        seen: Dict[str, UnifiedProcurement] = {}

        for item in items:
            fp = item.fingerprint or self._generate_fingerprint(item)

            if fp not in seen:
                seen[fp] = item
            else:
                # Resolve duplicate - keep higher priority or more complete
                existing = seen[fp]
                winner = self._resolve_duplicate(existing, item)
                seen[fp] = winner
                self._stats["duplicates_found"] += 1

        unique = list(seen.values())
        self._stats["total_output"] = len(unique)

        logger.info(
            f"Deduplication: {self._stats['total_input']} input, "
            f"{self._stats['total_output']} output, "
            f"{self._stats['duplicates_found']} duplicates removed"
        )

        return unique

    def _generate_fingerprint(self, item: UnifiedProcurement) -> str:
        """Generate fingerprint for duplicate detection."""
        # Combine key identifying fields
        # Normalize text for better matching
        objeto_normalized = (
            item.objeto[:100].lower()
            .replace(" ", "")
            .replace("-", "")
        )
        key = f"{item.orgao_cnpj or ''}|{objeto_normalized}|{item.valor_estimado or 0}"
        return hashlib.md5(key.encode()).hexdigest()

    def _resolve_duplicate(
        self,
        existing: UnifiedProcurement,
        new: UnifiedProcurement
    ) -> UnifiedProcurement:
        """
        Resolve which duplicate to keep.

        Priority:
        1. Higher priority source (PNCP first)
        2. More complete data (fewer None fields)
        """
        existing_priority = SOURCE_PRIORITY.get(existing.source, 99)
        new_priority = SOURCE_PRIORITY.get(new.source, 99)

        # Prefer higher priority source
        if new_priority < existing_priority:
            return new
        if existing_priority < new_priority:
            return existing

        # Same priority - prefer more complete record
        existing_score = self._completeness_score(existing)
        new_score = self._completeness_score(new)

        return new if new_score > existing_score else existing

    def _completeness_score(self, item: UnifiedProcurement) -> int:
        """Calculate completeness score (number of non-None fields)."""
        score = 0
        for field in [
            item.valor_estimado,
            item.municipio,
            item.orgao_cnpj,
            item.data_abertura,
            item.data_encerramento,
            item.source_url,
        ]:
            if field is not None:
                score += 1
        return score

    def get_stats(self) -> Dict[str, int]:
        """Get deduplication statistics."""
        return self._stats.copy()

# Global instance
deduplication_service = DeduplicationService()
```

### Consolidation Service

```python
# backend/services/consolidation.py

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
import logging

from clients.base_client import BaseClient
from schemas.unified_schema import UnifiedProcurement
from services.source_manager import source_manager
from services.deduplication import deduplication_service

logger = logging.getLogger(__name__)

@dataclass
class SourceError:
    source: str
    error: str
    timestamp: datetime

@dataclass
class ConsolidatedResult:
    items: List[UnifiedProcurement]
    total: int
    sources_queried: int
    sources_succeeded: int
    sources_failed: int
    errors: List[SourceError]
    dedup_stats: Dict[str, int]
    fetch_duration_ms: float

class ConsolidationService:
    """Orchestrates multi-source procurement data fetching."""

    def __init__(
        self,
        source_timeout: float = 30.0,
        global_timeout: float = 60.0,
    ):
        self.source_timeout = source_timeout
        self.global_timeout = global_timeout

    async def fetch_all_sources(
        self,
        data_inicial: str,
        data_final: str,
        ufs: List[str] | None = None,
        sources: List[str] | None = None,
    ) -> ConsolidatedResult:
        """
        Fetch procurement data from all enabled sources in parallel.

        Args:
            data_inicial: Start date (YYYY-MM-DD)
            data_final: End date (YYYY-MM-DD)
            ufs: Optional list of state codes
            sources: Optional list of source names to query

        Returns:
            ConsolidatedResult with aggregated, deduplicated items
        """
        start_time = datetime.utcnow()

        # Get sources to query
        if sources:
            clients = [
                source_manager.get_source(s)
                for s in sources
                if source_manager.get_source(s)
            ]
        else:
            clients = source_manager.get_enabled_sources()

        if not clients:
            return ConsolidatedResult(
                items=[],
                total=0,
                sources_queried=0,
                sources_succeeded=0,
                sources_failed=0,
                errors=[],
                dedup_stats={},
                fetch_duration_ms=0,
            )

        # Launch parallel fetches
        tasks = [
            self._fetch_with_timeout(client, data_inicial, data_final, ufs)
            for client in clients
        ]

        # Wait for all with global timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.global_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Global timeout ({self.global_timeout}s) exceeded")
            results = [asyncio.TimeoutError()] * len(tasks)

        # Process results
        all_items: List[UnifiedProcurement] = []
        errors: List[SourceError] = []
        succeeded = 0

        for client, result in zip(clients, results):
            source_name = client.config.name

            if isinstance(result, Exception):
                errors.append(SourceError(
                    source=source_name,
                    error=str(result),
                    timestamp=datetime.utcnow()
                ))
                logger.warning(f"Source {source_name} failed: {result}")
            else:
                all_items.extend(result)
                succeeded += 1
                logger.info(f"Source {source_name}: {len(result)} items")

        # Deduplicate
        unique_items = deduplication_service.deduplicate(all_items)

        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ConsolidatedResult(
            items=unique_items,
            total=len(unique_items),
            sources_queried=len(clients),
            sources_succeeded=succeeded,
            sources_failed=len(errors),
            errors=errors,
            dedup_stats=deduplication_service.get_stats(),
            fetch_duration_ms=duration,
        )

    async def _fetch_with_timeout(
        self,
        client: BaseClient,
        data_inicial: str,
        data_final: str,
        ufs: List[str] | None,
    ) -> List[UnifiedProcurement]:
        """Fetch from a single source with timeout."""
        try:
            # Run sync generator in executor
            loop = asyncio.get_event_loop()
            items = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: list(client.fetch_all(data_inicial, data_final, ufs))
                ),
                timeout=self.source_timeout
            )
            return items
        except asyncio.TimeoutError:
            raise TimeoutError(f"Source timeout ({self.source_timeout}s)")

# Global instance
consolidation_service = ConsolidationService()
```

### API Updates

```python
# In main.py - updated endpoint

from services.consolidation import consolidation_service, ConsolidatedResult
from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    ufs: List[str] | None = None
    data_inicial: str
    data_final: str
    sources: List[str] | None = None  # NEW: optional source filter

class SearchResponse(BaseModel):
    items: List[dict]
    total: int
    sources_queried: int
    sources_succeeded: int
    sources_failed: int
    errors: List[dict]
    dedup_stats: dict
    duration_ms: float

@app.post("/api/buscar", response_model=SearchResponse)
async def buscar(request: SearchRequest):
    """Search for procurement opportunities across all sources."""
    result = await consolidation_service.fetch_all_sources(
        data_inicial=request.data_inicial,
        data_final=request.data_final,
        ufs=request.ufs,
        sources=request.sources,
    )

    return SearchResponse(
        items=[item.dict() for item in result.items],
        total=result.total,
        sources_queried=result.sources_queried,
        sources_succeeded=result.sources_succeeded,
        sources_failed=result.sources_failed,
        errors=[e.__dict__ for e in result.errors],
        dedup_stats=result.dedup_stats,
        duration_ms=result.fetch_duration_ms,
    )
```

---

## Definition of Done

- [ ] Source manager implemented
- [ ] Deduplication service implemented
- [ ] Consolidation service implemented
- [ ] API endpoint updated
- [ ] Parallel fetching working
- [ ] Graceful degradation verified
- [ ] Unit tests passing (90%+ coverage)
- [ ] Integration tests passing
- [ ] Code reviewed by peer

---

## Story Points: 13 SP

**Complexity:** High (async orchestration, deduplication logic)
**Uncertainty:** Medium (clear requirements)

---

## Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| MSP-001-04 | Code dependency | Base client provides interface |
| MSP-001-05 | Code dependency | BLL client needed |
| MSP-001-06 | Code dependency | PCP client needed |
| MSP-001-07 | Code dependency | BNC client needed |
| MSP-001-08 | Code dependency | Licitar client needed |

---

## Blocks

- MSP-001-10 (Multi-Source Test Suite)
- MSP-001-11 (Deployment & Monitoring)

---

## Test Scenarios

1. **All sources succeed** - Verify aggregation and deduplication
2. **One source fails** - Verify graceful degradation
3. **All sources fail** - Verify empty result with errors
4. **Source timeout** - Verify timeout handling
5. **Duplicate detection** - Verify same bid from multiple sources
6. **Large result sets** - Verify performance with 10k+ items

---

## References

- Epic: `docs/stories/epic-multi-source-procurement.md`
- Architecture: `docs/stories/STORY-158-architecture-design.md`
- Client Stories: STORY-159 through STORY-163

---

**Story Status:** READY (pending client implementations)
**Estimated Duration:** 4-5 days
**Priority:** P1 - Critical Path
