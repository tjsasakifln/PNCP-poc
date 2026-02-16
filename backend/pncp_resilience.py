"""
PNCP API Resilience Layer - Adaptive Timeouts, Circuit Breaker, and Caching

This module provides resilience patterns for the PNCP API client to handle:
- Timeouts: Adaptive per-UF timeouts based on historical performance
- Retries: Exponential backoff for failed requests
- Circuit Breaking: Prevent cascading failures
- Caching: Reduce API load for recent queries

Task #3: Prevent PNCP API timeouts and improve reliability
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)


# ============================================================================
# Adaptive Timeout Configuration
# ============================================================================

@dataclass
class UFPerformanceMetrics:
    """Performance metrics for a specific UF."""

    uf: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_count: int = 0
    avg_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    recent_durations: list = field(default_factory=list)  # Last 10 durations

    def record_success(self, duration_ms: float) -> None:
        """Record a successful request."""
        self.total_requests += 1
        self.successful_requests += 1
        self.last_success = datetime.now(timezone.utc)

        # Update recent durations (keep last 10)
        self.recent_durations.append(duration_ms)
        if len(self.recent_durations) > 10:
            self.recent_durations.pop(0)

        # Recalculate averages
        if self.recent_durations:
            self.avg_duration_ms = sum(self.recent_durations) / len(self.recent_durations)
            sorted_durations = sorted(self.recent_durations)
            p95_idx = int(len(sorted_durations) * 0.95)
            self.p95_duration_ms = sorted_durations[min(p95_idx, len(sorted_durations) - 1)]

    def record_failure(self, is_timeout: bool = False) -> None:
        """Record a failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_failure = datetime.now(timezone.utc)

        if is_timeout:
            self.timeout_count += 1

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 1.0  # No data = assume healthy
        return self.successful_requests / self.total_requests

    @property
    def is_healthy(self) -> bool:
        """Determine if this UF is healthy (>70% success rate)."""
        return self.success_rate >= 0.7


class AdaptiveTimeoutManager:
    """
    Manages adaptive timeouts per UF based on historical performance.

    Strategy:
    - Fast UFs (avg < 30s): timeout = avg * 2.5
    - Medium UFs (avg 30-60s): timeout = avg * 2.0
    - Slow UFs (avg > 60s): timeout = avg * 1.5
    - Unknown UFs: start with 90s (current default)
    - Minimum timeout: 30s
    - Maximum timeout: 180s (3 minutes)
    """

    # Baseline timeouts by UF size (estimated)
    # Large states that typically have more data
    LARGE_UFS = {"SP", "RJ", "MG", "BA", "RS", "PR", "PE", "CE"}
    MEDIUM_UFS = {"SC", "GO", "PA", "MA", "ES", "PB", "AL", "MT", "MS", "AM", "RN"}
    SMALL_UFS = {"DF", "PI", "RO", "TO", "SE", "AC", "AP", "RR"}

    def __init__(self):
        self.metrics: Dict[str, UFPerformanceMetrics] = {}
        self.default_timeout = 90.0  # seconds
        self.min_timeout = 30.0
        self.max_timeout = 180.0

    def get_timeout(self, uf: str) -> float:
        """
        Get adaptive timeout for a specific UF.

        Args:
            uf: State code (e.g., "SP", "RJ")

        Returns:
            Timeout in seconds
        """
        metrics = self.metrics.get(uf)

        if not metrics or metrics.total_requests < 3:
            # Not enough data - use baseline by UF size
            if uf in self.LARGE_UFS:
                return 120.0  # 2 minutes for large states
            elif uf in self.MEDIUM_UFS:
                return 90.0   # 1.5 minutes for medium states
            else:
                return 60.0   # 1 minute for small states

        # Use P95 duration with multiplier based on average
        avg_ms = metrics.avg_duration_ms
        p95_ms = metrics.p95_duration_ms

        if avg_ms < 30000:  # < 30s average
            timeout = (p95_ms / 1000) * 2.5
        elif avg_ms < 60000:  # 30-60s average
            timeout = (p95_ms / 1000) * 2.0
        else:  # > 60s average
            timeout = (p95_ms / 1000) * 1.5

        # Clamp to min/max
        timeout = max(self.min_timeout, min(timeout, self.max_timeout))

        logger.debug(
            f"Adaptive timeout for UF={uf}: {timeout:.1f}s "
            f"(avg={avg_ms/1000:.1f}s, p95={p95_ms/1000:.1f}s, "
            f"success_rate={metrics.success_rate:.2%})"
        )

        return timeout

    def record_request(self, uf: str, duration_ms: float, success: bool, is_timeout: bool = False) -> None:
        """
        Record a request result for adaptive learning.

        Args:
            uf: State code
            duration_ms: Request duration in milliseconds
            success: Whether request succeeded
            is_timeout: Whether request timed out
        """
        if uf not in self.metrics:
            self.metrics[uf] = UFPerformanceMetrics(uf=uf)

        metrics = self.metrics[uf]

        if success:
            metrics.record_success(duration_ms)
        else:
            metrics.record_failure(is_timeout=is_timeout)

    def get_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all UFs."""
        return {
            uf: {
                "total_requests": m.total_requests,
                "success_rate": m.success_rate,
                "avg_duration_ms": m.avg_duration_ms,
                "p95_duration_ms": m.p95_duration_ms,
                "timeout_count": m.timeout_count,
                "is_healthy": m.is_healthy,
            }
            for uf, m in self.metrics.items()
        }


# ============================================================================
# Circuit Breaker Pattern
# ============================================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5          # Open after N consecutive failures
    success_threshold: int = 2          # Close after N successes in half-open
    timeout_seconds: float = 60.0       # Time to wait before half-open
    failure_rate_threshold: float = 0.5 # Open if >50% fail in window
    window_size: int = 10               # Look at last N requests


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    States:
    - CLOSED: Normal operation, all requests allowed
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Testing recovery, allow limited requests

    This prevents hammering a failing API and gives it time to recover.
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0  # Changed from failure_count
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.recent_results: list[bool] = []  # True = success, False = failure

    def call(self, func, *args, **kwargs):
        """
        Execute function through circuit breaker.

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            Exception: If circuit is OPEN or function fails
        """
        if self.state == CircuitState.OPEN:
            # Check if enough time has passed to try half-open
            if (
                self.last_failure_time and
                time.time() - self.last_failure_time >= self.config.timeout_seconds
            ):
                logger.info(f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN (timeout elapsed)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                # Still open, reject immediately
                raise Exception(f"Circuit breaker '{self.name}' is OPEN, rejecting request")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    async def call_async(self, func, *args, **kwargs):
        """Async version of call()."""
        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time and
                time.time() - self.last_failure_time >= self.config.timeout_seconds
            ):
                logger.info(f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception(f"Circuit breaker '{self.name}' is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Record successful request."""
        self.recent_results.append(True)
        if len(self.recent_results) > self.config.window_size:
            self.recent_results.pop(0)

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                logger.info(
                    f"Circuit breaker '{self.name}': HALF_OPEN -> CLOSED "
                    f"({self.success_count} successes)"
                )
                self.state = CircuitState.CLOSED
                self.consecutive_failures = 0
                self.success_count = 0

        # Reset consecutive failure count on success in CLOSED state
        if self.state == CircuitState.CLOSED:
            self.consecutive_failures = 0

    def _on_failure(self) -> None:
        """Record failed request."""
        self.recent_results.append(False)
        if len(self.recent_results) > self.config.window_size:
            self.recent_results.pop(0)

        self.consecutive_failures += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open -> back to open
            logger.warning(
                f"Circuit breaker '{self.name}': HALF_OPEN -> OPEN "
                f"(failure during recovery)"
            )
            self.state = CircuitState.OPEN
            self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Check if we should open based on consecutive failures OR failure rate
            should_open_consecutive = self.consecutive_failures >= self.config.failure_threshold

            should_open_rate = False
            if len(self.recent_results) >= self.config.window_size:
                failure_rate = 1.0 - (sum(self.recent_results) / len(self.recent_results))
                should_open_rate = failure_rate >= self.config.failure_rate_threshold

            if should_open_consecutive or should_open_rate:
                logger.warning(
                    f"Circuit breaker '{self.name}': CLOSED -> OPEN "
                    f"(consecutive_failures={self.consecutive_failures}, "
                    f"rate={failure_rate if should_open_rate else 'N/A'})"
                )
                self.state = CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (healthy)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (unhealthy)."""
        return self.state == CircuitState.OPEN


# ============================================================================
# Simple Cache for PNCP Results
# ============================================================================

@dataclass
class CacheEntry:
    """Cache entry with TTL."""

    data: Any
    created_at: datetime
    ttl_seconds: int

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        age = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return age > self.ttl_seconds


class PNCPCache:
    """
    Simple in-memory cache for PNCP API results.

    Cache key: (uf, data_inicial, data_final, modalidade, status)
    TTL: 1 hour (PNCP data changes slowly)

    This reduces API load for repeated searches.
    """

    def __init__(self, ttl_seconds: int = 3600):  # 1 hour default
        self.cache: Dict[Tuple, CacheEntry] = {}
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0

    def _make_key(
        self,
        uf: str,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        status: Optional[str] = None
    ) -> Tuple:
        """Create cache key from search parameters."""
        return (uf, data_inicial, data_final, modalidade, status or "todos")

    def get(
        self,
        uf: str,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        status: Optional[str] = None
    ) -> Optional[list]:
        """
        Get cached results if available and not expired.

        Returns:
            Cached data or None if not found/expired
        """
        key = self._make_key(uf, data_inicial, data_final, modalidade, status)
        entry = self.cache.get(key)

        if entry is None:
            self.misses += 1
            return None

        if entry.is_expired:
            # Expired, remove from cache
            del self.cache[key]
            self.misses += 1
            return None

        self.hits += 1
        logger.debug(
            f"Cache HIT for UF={uf}, dates={data_inicial} to {data_final}, "
            f"modalidade={modalidade} (age={(datetime.now(timezone.utc) - entry.created_at).total_seconds():.0f}s)"
        )
        return entry.data

    def put(
        self,
        uf: str,
        data_inicial: str,
        data_final: str,
        modalidade: int,
        data: list,
        status: Optional[str] = None
    ) -> None:
        """Store results in cache."""
        key = self._make_key(uf, data_inicial, data_final, modalidade, status)
        self.cache[key] = CacheEntry(
            data=data,
            created_at=datetime.now(timezone.utc),
            ttl_seconds=self.ttl_seconds
        )
        logger.debug(
            f"Cache PUT for UF={uf}, dates={data_inicial} to {data_final}, "
            f"modalidade={modalidade} ({len(data)} items)"
        )

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")

    def clear_expired(self) -> int:
        """Remove expired entries. Returns number removed."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.info(f"Removed {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    @property
    def size(self) -> int:
        """Get number of cached entries."""
        return len(self.cache)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": self.size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
            "ttl_seconds": self.ttl_seconds,
        }


# ============================================================================
# Global Instances
# ============================================================================

# Singleton instances for application-wide use
_timeout_manager = AdaptiveTimeoutManager()
_circuit_breaker = CircuitBreaker("pncp_api")
_cache = PNCPCache(ttl_seconds=3600)  # 1 hour


def get_timeout_manager() -> AdaptiveTimeoutManager:
    """Get global timeout manager instance."""
    return _timeout_manager


def get_circuit_breaker() -> CircuitBreaker:
    """Get global circuit breaker instance."""
    return _circuit_breaker


def get_cache() -> PNCPCache:
    """Get global cache instance."""
    return _cache
