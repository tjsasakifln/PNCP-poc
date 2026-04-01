"""STORY-296: Bulkhead pattern — per-source concurrency isolation.

Each data source (PNCP, PCP, ComprasGov) gets its own semaphore and
connection pool budget. If one source exhausts its allocation, the
others continue unaffected.

Reference: https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead
"""

import asyncio
import logging
import time
from typing import Any, Awaitable, Dict, Optional, TypeVar

from metrics import (
    BULKHEAD_ACQUIRE_TIMEOUT,
    SOURCE_ACTIVE_REQUESTS,
    SOURCE_POOL_EXHAUSTED,
    SOURCE_SEMAPHORE_WAIT_SECONDS,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BulkheadAcquireTimeoutError(Exception):
    """Raised when a coroutine cannot acquire the bulkhead semaphore in time.

    This signals that the UF should be marked as ``skipped`` (not ``error``),
    since the work was never attempted — it simply couldn't get a slot.
    """

    def __init__(self, source: str, timeout: float):
        self.source = source
        self.timeout = timeout
        super().__init__(
            f"Bulkhead acquire timeout for {source}: "
            f"could not acquire semaphore within {timeout:.1f}s"
        )


class SourceBulkhead:
    """Isolates a data source with its own concurrency limit.

    Wraps coroutine execution with an asyncio.Semaphore so that at most
    ``max_concurrent`` operations run simultaneously for this source.

    Attributes:
        name: Source identifier (e.g. "PNCP", "PORTAL_COMPRAS").
        max_concurrent: Maximum concurrent operations.
        timeout: Per-source timeout in seconds.
    """

    def __init__(self, name: str, max_concurrent: int, timeout: float):
        self.name = name
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active = 0
        self._exhausted_count = 0

    @property
    def active(self) -> int:
        """Number of currently active operations."""
        return self._active

    @property
    def available(self) -> int:
        """Number of available slots."""
        return self.max_concurrent - self._active

    @property
    def is_exhausted(self) -> bool:
        """True if all slots are in use."""
        return self._active >= self.max_concurrent

    async def execute(self, coro: Awaitable[T], timeout: Optional[float] = None) -> T:
        """Execute a coroutine within the bulkhead's concurrency limit.

        Timeout is split 50/50: half for acquiring the semaphore, half for
        executing the coroutine.  If the semaphore cannot be acquired within
        the acquire budget, :class:`BulkheadAcquireTimeoutError` is raised so
        the caller can mark the unit of work as *skipped* rather than *error*.

        Args:
            coro: Awaitable to run inside the bulkhead.
            timeout: Override total timeout (defaults to ``self.timeout``).

        Returns:
            The result of the awaitable.

        Raises:
            BulkheadAcquireTimeoutError: semaphore not acquired in time.
        """
        effective_timeout = timeout if timeout is not None else self.timeout
        acquire_budget = effective_timeout / 2.0

        # Check if we'll have to wait (semaphore is exhausted)
        if self._active >= self.max_concurrent:
            self._exhausted_count += 1
            SOURCE_POOL_EXHAUSTED.labels(source=self.name).inc()
            logger.warning(
                f"[BULKHEAD] {self.name}: pool exhausted "
                f"(active={self._active}/{self.max_concurrent}), queuing"
            )

        wait_start = time.monotonic()
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=acquire_budget)
        except asyncio.TimeoutError:
            BULKHEAD_ACQUIRE_TIMEOUT.labels(source=self.name).inc()
            logger.warning(
                f"[BULKHEAD] {self.name}: acquire timeout after {acquire_budget:.1f}s "
                f"(active={self._active}/{self.max_concurrent})"
            )
            raise BulkheadAcquireTimeoutError(self.name, acquire_budget)

        wait_duration = time.monotonic() - wait_start
        if wait_duration > 0.01:  # Only record meaningful waits
            SOURCE_SEMAPHORE_WAIT_SECONDS.labels(source=self.name).observe(wait_duration)

        self._active += 1
        SOURCE_ACTIVE_REQUESTS.labels(source=self.name).set(self._active)
        try:
            return await coro
        finally:
            self._active -= 1
            SOURCE_ACTIVE_REQUESTS.labels(source=self.name).set(self._active)
            self._semaphore.release()

    def status(self) -> str:
        """Return health status string based on utilization.

        Returns:
            "healthy" if <80% utilized, "degraded" if >=80%, "exhausted" if full.
        """
        if self._active >= self.max_concurrent:
            return "exhausted"
        if self._active >= self.max_concurrent * 0.8:
            return "degraded"
        return "healthy"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize bulkhead state for health/debug endpoints."""
        return {
            "max_concurrent": self.max_concurrent,
            "active": self._active,
            "available": self.available,
            "timeout": self.timeout,
            "status": self.status(),
            "exhausted_count": self._exhausted_count,
        }

    def __repr__(self) -> str:
        return (
            f"SourceBulkhead(name={self.name!r}, "
            f"active={self._active}/{self.max_concurrent})"
        )


# ---------------------------------------------------------------------------
# Module-level registry — one bulkhead per source
# ---------------------------------------------------------------------------

_bulkhead_registry: Dict[str, SourceBulkhead] = {}


def get_bulkhead(source_name: str) -> Optional[SourceBulkhead]:
    """Return the bulkhead for *source_name*, or None if not registered."""
    return _bulkhead_registry.get(source_name)


def register_bulkhead(bulkhead: SourceBulkhead) -> None:
    """Register a bulkhead in the global registry."""
    _bulkhead_registry[bulkhead.name] = bulkhead
    logger.info(
        f"[BULKHEAD] Registered: {bulkhead.name} "
        f"(max_concurrent={bulkhead.max_concurrent}, timeout={bulkhead.timeout}s)"
    )


def get_all_bulkheads() -> Dict[str, SourceBulkhead]:
    """Return snapshot of all registered bulkheads."""
    return dict(_bulkhead_registry)


def reset_registry() -> None:
    """Clear all bulkheads (for testing)."""
    _bulkhead_registry.clear()


def initialize_bulkheads() -> Dict[str, SourceBulkhead]:
    """Create and register bulkheads for all sources using config values.

    Called at application startup. Safe to call multiple times (idempotent).

    Returns:
        Dict mapping source name to its SourceBulkhead.
    """
    from config import (
        PNCP_BULKHEAD_CONCURRENCY,
        PCP_BULKHEAD_CONCURRENCY,
        COMPRASGOV_BULKHEAD_CONCURRENCY,
        PNCP_SOURCE_TIMEOUT,
        PCP_SOURCE_TIMEOUT,
        COMPRASGOV_SOURCE_TIMEOUT,
    )

    bulkheads = {
        "PNCP": SourceBulkhead("PNCP", PNCP_BULKHEAD_CONCURRENCY, PNCP_SOURCE_TIMEOUT),
        "PORTAL_COMPRAS": SourceBulkhead("PORTAL_COMPRAS", PCP_BULKHEAD_CONCURRENCY, PCP_SOURCE_TIMEOUT),
        "COMPRAS_GOV": SourceBulkhead("COMPRAS_GOV", COMPRASGOV_BULKHEAD_CONCURRENCY, COMPRASGOV_SOURCE_TIMEOUT),
    }

    for bh in bulkheads.values():
        register_bulkhead(bh)

    logger.info(
        f"[BULKHEAD] Initialized {len(bulkheads)} bulkheads: "
        + ", ".join(f"{k}({v.max_concurrent})" for k, v in bulkheads.items())
    )

    return bulkheads
