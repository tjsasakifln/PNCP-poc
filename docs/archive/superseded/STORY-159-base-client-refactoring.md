# Story MSP-001-04: Base Client Refactoring

**Story ID:** MSP-001-04
**GitHub Issue:** #159 (to be created)
**Epic:** MSP-001 (Multi-Source Procurement Consolidation)
**Sprint:** TBD
**Owner:** @dev
**Created:** February 3, 2026

---

## Story

**As a** backend developer,
**I want** to refactor the existing PNCP client into a reusable base client abstraction,
**So that** all new source clients can inherit common functionality (retry, rate limiting, circuit breaker).

---

## Objective

Extract common HTTP client functionality from `pncp_client.py` into an abstract base class that:

1. Provides exponential backoff retry logic
2. Implements rate limiting
3. Supports circuit breaker pattern
4. Handles common error scenarios
5. Provides logging and metrics hooks

---

## Acceptance Criteria

### AC1: Base Client Abstraction
- [ ] `BaseClient` abstract class created
- [ ] Retry logic extracted and parameterized
- [ ] Rate limiting extracted and configurable
- [ ] Circuit breaker pattern implemented
- [ ] Context manager support (`__enter__`/`__exit__`)

### AC2: PNCP Client Refactoring
- [ ] `PNCPClient` extends `BaseClient`
- [ ] All existing functionality preserved
- [ ] Existing tests pass without modification
- [ ] No regression in PNCP functionality

### AC3: Configuration
- [ ] `SourceConfig` dataclass created
- [ ] Per-source configuration support
- [ ] Environment variable overrides
- [ ] Sensible defaults for all sources

### AC4: Circuit Breaker
- [ ] Circuit breaker states: CLOSED, OPEN, HALF_OPEN
- [ ] Configurable failure threshold
- [ ] Configurable recovery timeout
- [ ] Proper state transitions

### AC5: Testing
- [ ] Unit tests for `BaseClient`
- [ ] Unit tests for circuit breaker
- [ ] Integration tests for `PNCPClient` (refactored)
- [ ] 90%+ coverage on new code

### AC6: Documentation
- [ ] Docstrings for all public methods
- [ ] Usage examples in docstrings
- [ ] Architecture notes updated

---

## Technical Tasks

### Task 1: Create Base Client (2 SP)
- [ ] Create `backend/clients/base_client.py`
- [ ] Extract `calculate_delay()` function
- [ ] Implement `BaseClient` abstract class
- [ ] Add retry logic as reusable method
- [ ] Add rate limiting as reusable method
- [ ] Implement circuit breaker

### Task 2: Create Configuration (0.5 SP)
- [ ] Create `backend/config/sources.py`
- [ ] Define `SourceConfig` dataclass
- [ ] Define `RetryConfig` (refactor from existing)
- [ ] Add environment variable support

### Task 3: Refactor PNCP Client (1.5 SP)
- [ ] Move `pncp_client.py` to `backend/clients/`
- [ ] Update imports throughout codebase
- [ ] Make `PNCPClient` extend `BaseClient`
- [ ] Remove duplicated code
- [ ] Verify all existing functionality

### Task 4: Testing (1 SP)
- [ ] Create `backend/tests/test_base_client.py`
- [ ] Add circuit breaker tests
- [ ] Update `test_pncp_client.py` for new location
- [ ] Verify no test regressions

---

## Implementation Design

### Base Client Structure

```python
# backend/clients/base_client.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class SourceConfig:
    """Configuration for a procurement data source."""
    name: str
    base_url: str
    enabled: bool = True
    timeout: float = 30.0

    # Retry configuration
    max_retries: int = 5
    base_delay: float = 2.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

    # Rate limiting
    requests_per_second: float = 10.0

    # Circuit breaker
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_requests: int = 3

class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""

    def __init__(self, config: SourceConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float = 0
        self.half_open_successes = 0

    def record_success(self) -> None:
        """Record a successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.config.half_open_requests:
                self._transition_to_closed()
        else:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self._transition_to_open()

    def can_execute(self) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self._transition_to_half_open()
                return True
            return False
        else:  # HALF_OPEN
            return True

    def _transition_to_open(self) -> None:
        logger.warning(f"Circuit breaker OPEN for {self.config.name}")
        self.state = CircuitState.OPEN

    def _transition_to_half_open(self) -> None:
        logger.info(f"Circuit breaker HALF_OPEN for {self.config.name}")
        self.state = CircuitState.HALF_OPEN
        self.half_open_successes = 0

    def _transition_to_closed(self) -> None:
        logger.info(f"Circuit breaker CLOSED for {self.config.name}")
        self.state = CircuitState.CLOSED
        self.failure_count = 0

class BaseClient(ABC):
    """Abstract base client for procurement data sources."""

    def __init__(self, config: SourceConfig):
        self.config = config
        self.session = self._create_session()
        self.circuit_breaker = CircuitBreaker(config)
        self._last_request_time = 0.0
        self._request_count = 0

    @abstractmethod
    def _create_session(self):
        """Create HTTP session with source-specific configuration."""
        pass

    @abstractmethod
    def fetch_page(self, **kwargs) -> dict:
        """Fetch a single page of data from the source."""
        pass

    @abstractmethod
    def fetch_all(self, **kwargs):
        """Fetch all data with pagination."""
        pass

    def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        min_interval = 1.0 / self.config.requests_per_second
        elapsed = time.time() - self._last_request_time

        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)

        self._last_request_time = time.time()
        self._request_count += 1

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        if self.config.jitter:
            import random
            delay *= random.uniform(0.5, 1.5)
        return delay

    def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute operation with retry logic and circuit breaker."""
        if not self.circuit_breaker.can_execute():
            raise CircuitOpenError(f"Circuit open for {self.config.name}")

        for attempt in range(self.config.max_retries + 1):
            try:
                self._rate_limit()
                result = operation(*args, **kwargs)
                self.circuit_breaker.record_success()
                return result
            except RetryableError as e:
                self.circuit_breaker.record_failure()
                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                else:
                    raise

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
        logger.debug(f"Session closed. Total requests: {self._request_count}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass

class RetryableError(Exception):
    """Base class for errors that should trigger retry."""
    pass
```

### PNCP Client Refactoring

```python
# backend/clients/pncp_client.py

from .base_client import BaseClient, SourceConfig, RetryableError
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class PNCPClient(BaseClient):
    """Resilient HTTP client for PNCP API."""

    DEFAULT_CONFIG = SourceConfig(
        name="pncp",
        base_url="https://pncp.gov.br/api/consulta/v1",
        timeout=30.0,
        max_retries=5,
        base_delay=2.0,
        requests_per_second=10.0,
    )

    def __init__(self, config: SourceConfig | None = None):
        super().__init__(config or self.DEFAULT_CONFIG)

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        # ... existing session setup ...
        return session

    def fetch_page(self, ...) -> dict:
        # Use _execute_with_retry for automatic retry handling
        return self._execute_with_retry(self._fetch_page_impl, ...)

    def _fetch_page_impl(self, ...) -> dict:
        # Actual implementation (existing code)
        ...
```

---

## File Changes

### New Files
- `backend/clients/__init__.py`
- `backend/clients/base_client.py`
- `backend/config/__init__.py`
- `backend/config/sources.py`
- `backend/tests/test_base_client.py`

### Modified Files
- `backend/pncp_client.py` -> `backend/clients/pncp_client.py`
- `backend/main.py` - Update imports
- `backend/filter.py` - Update imports if needed
- `backend/tests/test_pncp_client.py` - Update imports

### Import Updates Required
```python
# Before
from pncp_client import PNCPClient

# After
from clients.pncp_client import PNCPClient
```

---

## Definition of Done

- [ ] `BaseClient` abstract class implemented
- [ ] Circuit breaker implemented and tested
- [ ] `PNCPClient` refactored to extend `BaseClient`
- [ ] All 82 existing PNCP tests pass
- [ ] New tests added for base client (target: 20+ tests)
- [ ] 90%+ code coverage on new code
- [ ] No breaking changes to existing API
- [ ] Documentation updated

---

## Story Points: 5 SP

**Complexity:** Medium (refactoring with clear patterns)
**Uncertainty:** Low (existing code provides template)

---

## Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| MSP-001-02 | Soft dependency | Schema design informs transformer integration |
| MSP-001-03 | Blocks this story | Architecture design provides patterns |

---

## Blocks

- MSP-001-05 (BLL Client)
- MSP-001-06 (PCP Client)
- MSP-001-07 (BNC Client)
- MSP-001-08 (Licitar Client)
- MSP-001-09 (Consolidation Service)

---

## Test Plan

### Unit Tests

```python
# test_base_client.py

class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        ...

    def test_transitions_to_open_after_threshold(self):
        ...

    def test_transitions_to_half_open_after_timeout(self):
        ...

    def test_transitions_to_closed_after_successes(self):
        ...

    def test_rejects_requests_when_open(self):
        ...

class TestBaseClient:
    def test_rate_limiting(self):
        ...

    def test_exponential_backoff(self):
        ...

    def test_retry_on_retryable_error(self):
        ...

    def test_no_retry_on_non_retryable_error(self):
        ...
```

---

## References

- Epic: `docs/stories/epic-multi-source-procurement.md`
- Architecture: `docs/stories/STORY-158-architecture-design.md`
- Existing PNCP client: `backend/pncp_client.py`

---

**Story Status:** READY (pending dependency completion)
**Estimated Duration:** 2-3 days
**Priority:** P1 - Critical Path
