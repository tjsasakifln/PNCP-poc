"""
Tests for PNCP Resilience Layer

Task #3: Test timeout prevention, circuit breaker, and caching
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from pncp_resilience import (
    AdaptiveTimeoutManager,
    CircuitBreaker,
    CircuitState,
    CircuitBreakerConfig,
    PNCPCache,
    UFPerformanceMetrics,
)


# ============================================================================
# Adaptive Timeout Manager Tests
# ============================================================================

def test_adaptive_timeout_unknown_uf():
    """Test timeout for UF with no history - uses baseline by size."""
    manager = AdaptiveTimeoutManager()

    # Large UF (e.g., SP) -> 120s
    assert manager.get_timeout("SP") == 120.0

    # Medium UF (e.g., SC) -> 90s
    assert manager.get_timeout("SC") == 90.0

    # Small UF (e.g., AC) -> 60s
    assert manager.get_timeout("AC") == 60.0


def test_adaptive_timeout_with_history():
    """Test timeout adapts based on historical performance."""
    manager = AdaptiveTimeoutManager()

    # Record fast UF (avg 20s)
    for _ in range(5):
        manager.record_request("RJ", duration_ms=20000, success=True)

    timeout = manager.get_timeout("RJ")
    # Fast UF: P95 * 2.5, but at least 30s
    assert 30.0 <= timeout <= 60.0


def test_adaptive_timeout_slow_uf():
    """Test timeout for slow UF increases appropriately."""
    manager = AdaptiveTimeoutManager()

    # Record slow UF (avg 80s)
    for _ in range(5):
        manager.record_request("PR", duration_ms=80000, success=True)

    timeout = manager.get_timeout("PR")
    # Slow UF: P95 * 1.5, should be higher but capped at 180s
    assert 90.0 <= timeout <= 180.0


def test_adaptive_timeout_clamping():
    """Test timeout respects min/max bounds."""
    manager = AdaptiveTimeoutManager()

    # Record very fast UF (5s avg)
    for _ in range(5):
        manager.record_request("DF", duration_ms=5000, success=True)

    timeout = manager.get_timeout("DF")
    # Should be clamped to min (30s)
    assert timeout >= 30.0

    # Record very slow UF (200s avg)
    for _ in range(5):
        manager.record_request("SP", duration_ms=200000, success=True)

    timeout = manager.get_timeout("SP")
    # Should be clamped to max (180s)
    assert timeout <= 180.0


def test_record_success():
    """Test recording successful requests updates metrics."""
    manager = AdaptiveTimeoutManager()

    manager.record_request("MG", duration_ms=30000, success=True)
    manager.record_request("MG", duration_ms=35000, success=True)

    metrics = manager.metrics["MG"]
    assert metrics.total_requests == 2
    assert metrics.successful_requests == 2
    assert metrics.failed_requests == 0
    assert metrics.success_rate == 1.0
    assert metrics.is_healthy is True


def test_record_failure():
    """Test recording failed requests updates metrics."""
    manager = AdaptiveTimeoutManager()

    manager.record_request("BA", duration_ms=90000, success=False, is_timeout=True)
    manager.record_request("BA", duration_ms=0, success=False, is_timeout=False)

    metrics = manager.metrics["BA"]
    assert metrics.total_requests == 2
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 2
    assert metrics.timeout_count == 1
    assert metrics.success_rate == 0.0
    assert metrics.is_healthy is False


def test_mixed_success_failure():
    """Test mixed success/failure tracking."""
    manager = AdaptiveTimeoutManager()

    # 7 successes, 3 failures = 70% success rate (threshold for healthy)
    for _ in range(7):
        manager.record_request("RS", duration_ms=40000, success=True)
    for _ in range(3):
        manager.record_request("RS", duration_ms=0, success=False)

    metrics = manager.metrics["RS"]
    assert metrics.success_rate == 0.7
    assert metrics.is_healthy is True  # Exactly at threshold


def test_get_stats():
    """Test getting summary statistics."""
    manager = AdaptiveTimeoutManager()

    manager.record_request("SP", duration_ms=30000, success=True)
    manager.record_request("RJ", duration_ms=40000, success=True)
    manager.record_request("MG", duration_ms=0, success=False, is_timeout=True)

    stats = manager.get_stats()

    assert "SP" in stats
    assert "RJ" in stats
    assert "MG" in stats

    assert stats["SP"]["success_rate"] == 1.0
    assert stats["MG"]["timeout_count"] == 1


# ============================================================================
# Circuit Breaker Tests
# ============================================================================

def test_circuit_breaker_closed_state():
    """Test circuit breaker starts in CLOSED state and allows requests."""
    cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))

    def success_func():
        return "success"

    result = cb.call(success_func)
    assert result == "success"
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_opens_on_failures():
    """Test circuit breaker opens after threshold failures."""
    config = CircuitBreakerConfig(failure_threshold=3)
    cb = CircuitBreaker("test", config)

    def failing_func():
        raise Exception("API error")

    # First 2 failures - circuit stays CLOSED
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(failing_func)
        assert cb.state == CircuitState.CLOSED

    # 3rd failure - circuit OPENS
    with pytest.raises(Exception):
        cb.call(failing_func)
    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_rejects_when_open():
    """Test circuit breaker rejects requests when OPEN."""
    config = CircuitBreakerConfig(failure_threshold=2)
    cb = CircuitBreaker("test", config)

    def failing_func():
        raise Exception("API error")

    # Trigger 2 failures to OPEN circuit
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(failing_func)

    assert cb.state == CircuitState.OPEN

    # Next request should be rejected immediately
    with pytest.raises(Exception, match="Circuit breaker .* is OPEN"):
        cb.call(lambda: "should not execute")


def test_circuit_breaker_half_open_after_timeout():
    """Test circuit breaker enters HALF_OPEN state after timeout."""
    config = CircuitBreakerConfig(
        failure_threshold=2,
        timeout_seconds=0.1,  # 100ms for fast test
    )
    cb = CircuitBreaker("test", config)

    def failing_func():
        raise Exception("API error")

    # Open circuit
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(failing_func)

    assert cb.state == CircuitState.OPEN

    # Wait for timeout
    import time
    time.sleep(0.15)

    # Next call should transition to HALF_OPEN (before execution)
    # But since function fails, it goes back to OPEN
    with pytest.raises(Exception):
        cb.call(failing_func)

    # State should be OPEN again (failure in HALF_OPEN)
    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_closes_after_recovery():
    """Test circuit breaker closes after successful recoveries."""
    config = CircuitBreakerConfig(
        failure_threshold=2,
        success_threshold=2,
        timeout_seconds=0.1,
    )
    cb = CircuitBreaker("test", config)

    # Open circuit
    for _ in range(2):
        with pytest.raises(Exception):
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))

    assert cb.state == CircuitState.OPEN

    # Wait for timeout
    import time
    time.sleep(0.15)

    # Successful calls in HALF_OPEN should close circuit
    def success_func():
        return "ok"

    # First success - still HALF_OPEN
    result1 = cb.call(success_func)
    assert result1 == "ok"
    assert cb.state == CircuitState.HALF_OPEN

    # Second success - should CLOSE
    result2 = cb.call(success_func)
    assert result2 == "ok"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_async():
    """Test circuit breaker with async functions."""
    config = CircuitBreakerConfig(failure_threshold=2)
    cb = CircuitBreaker("test_async", config)

    async def success_func():
        await asyncio.sleep(0.01)
        return "success"

    result = await cb.call_async(success_func)
    assert result == "success"
    assert cb.state == CircuitState.CLOSED

    async def failing_func():
        raise Exception("async error")

    # Open circuit with async failures
    for _ in range(2):
        with pytest.raises(Exception):
            await cb.call_async(failing_func)

    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_failure_rate():
    """Test circuit breaker opens based on failure rate."""
    config = CircuitBreakerConfig(
        failure_threshold=100,  # High threshold
        failure_rate_threshold=0.5,  # 50% failure rate
        window_size=10,
    )
    cb = CircuitBreaker("test", config)

    # 5 successes, 5 failures = 50% failure rate
    for _ in range(5):
        cb.call(lambda: "ok")

    for _ in range(4):
        with pytest.raises(Exception):
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))

    assert cb.state == CircuitState.CLOSED  # Not yet at threshold

    # One more failure pushes it to 50%
    with pytest.raises(Exception):
        cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))

    assert cb.state == CircuitState.OPEN


# ============================================================================
# Cache Tests
# ============================================================================

def test_cache_miss():
    """Test cache miss returns None."""
    cache = PNCPCache(ttl_seconds=3600)

    result = cache.get(
        uf="SP",
        data_inicial="2026-02-01",
        data_final="2026-02-10",
        modalidade=6,
    )

    assert result is None
    assert cache.misses == 1
    assert cache.hits == 0


def test_cache_hit():
    """Test cache hit returns stored data."""
    cache = PNCPCache(ttl_seconds=3600)

    data = [{"id": "1"}, {"id": "2"}]
    cache.put(
        uf="SP",
        data_inicial="2026-02-01",
        data_final="2026-02-10",
        modalidade=6,
        data=data,
    )

    result = cache.get(
        uf="SP",
        data_inicial="2026-02-01",
        data_final="2026-02-10",
        modalidade=6,
    )

    assert result == data
    assert cache.hits == 1
    assert cache.misses == 0


def test_cache_expiration():
    """Test cache entries expire after TTL."""
    cache = PNCPCache(ttl_seconds=0.1)  # 100ms TTL

    data = [{"id": "1"}]
    cache.put(
        uf="RJ",
        data_inicial="2026-02-01",
        data_final="2026-02-10",
        modalidade=6,
        data=data,
    )

    # Immediate get - should hit
    result = cache.get(
        uf="RJ",
        data_inicial="2026-02-01",
        data_final="2026-02-10",
        modalidade=6,
    )
    assert result == data
    assert cache.hits == 1

    # Wait for expiration
    import time
    time.sleep(0.15)

    # Should miss now (expired)
    result = cache.get(
        uf="RJ",
        data_inicial="2026-02-01",
        data_final="2026-02-10",
        modalidade=6,
    )
    assert result is None
    assert cache.misses == 1


def test_cache_key_uniqueness():
    """Test different parameters create different cache keys."""
    cache = PNCPCache(ttl_seconds=3600)

    data1 = [{"id": "1"}]
    data2 = [{"id": "2"}]

    # Different UFs
    cache.put("SP", "2026-02-01", "2026-02-10", 6, data1)
    cache.put("RJ", "2026-02-01", "2026-02-10", 6, data2)

    assert cache.get("SP", "2026-02-01", "2026-02-10", 6) == data1
    assert cache.get("RJ", "2026-02-01", "2026-02-10", 6) == data2

    # Different dates
    data3 = [{"id": "3"}]
    cache.put("SP", "2026-02-11", "2026-02-20", 6, data3)
    assert cache.get("SP", "2026-02-11", "2026-02-20", 6) == data3
    assert cache.get("SP", "2026-02-01", "2026-02-10", 6) == data1  # Original still there

    # Different modalidades
    data4 = [{"id": "4"}]
    cache.put("SP", "2026-02-01", "2026-02-10", 7, data4)
    assert cache.get("SP", "2026-02-01", "2026-02-10", 7) == data4
    assert cache.get("SP", "2026-02-01", "2026-02-10", 6) == data1  # Original still there


def test_cache_with_status():
    """Test cache key includes status parameter."""
    cache = PNCPCache(ttl_seconds=3600)

    data1 = [{"id": "1"}]
    data2 = [{"id": "2"}]

    cache.put("MG", "2026-02-01", "2026-02-10", 6, data1, status="recebendo_proposta")
    cache.put("MG", "2026-02-01", "2026-02-10", 6, data2, status="em_julgamento")

    result1 = cache.get("MG", "2026-02-01", "2026-02-10", 6, status="recebendo_proposta")
    result2 = cache.get("MG", "2026-02-01", "2026-02-10", 6, status="em_julgamento")

    assert result1 == data1
    assert result2 == data2


def test_cache_clear():
    """Test clearing cache removes all entries."""
    cache = PNCPCache(ttl_seconds=3600)

    cache.put("SP", "2026-02-01", "2026-02-10", 6, [{"id": "1"}])
    cache.put("RJ", "2026-02-01", "2026-02-10", 6, [{"id": "2"}])

    assert cache.size == 2

    cache.clear()

    assert cache.size == 0
    assert cache.hits == 0
    assert cache.misses == 0


def test_cache_clear_expired():
    """Test clearing only expired entries."""
    cache = PNCPCache(ttl_seconds=0.1)

    cache.put("SP", "2026-02-01", "2026-02-10", 6, [{"id": "1"}])

    import time
    time.sleep(0.05)  # Half TTL

    cache.put("RJ", "2026-02-01", "2026-02-10", 6, [{"id": "2"}])

    time.sleep(0.07)  # SP should be expired (0.12s total), RJ not (0.07s)

    removed = cache.clear_expired()

    assert removed == 1  # Only SP expired
    assert cache.size == 1  # RJ still there


def test_cache_hit_rate():
    """Test cache hit rate calculation."""
    cache = PNCPCache(ttl_seconds=3600)

    # Initial hit rate = 0 (no requests)
    assert cache.hit_rate == 0.0

    # 1 miss
    cache.get("SP", "2026-02-01", "2026-02-10", 6)
    assert cache.hit_rate == 0.0  # 0/1 = 0%

    # 1 put + 1 hit
    cache.put("SP", "2026-02-01", "2026-02-10", 6, [{"id": "1"}])
    cache.get("SP", "2026-02-01", "2026-02-10", 6)
    assert cache.hit_rate == 0.5  # 1/2 = 50%

    # 2 more hits
    cache.get("SP", "2026-02-01", "2026-02-10", 6)
    cache.get("SP", "2026-02-01", "2026-02-10", 6)
    assert cache.hit_rate == 0.75  # 3/4 = 75%


def test_cache_stats():
    """Test getting cache statistics."""
    cache = PNCPCache(ttl_seconds=3600)

    cache.put("SP", "2026-02-01", "2026-02-10", 6, [{"id": "1"}])
    cache.get("SP", "2026-02-01", "2026-02-10", 6)  # Hit
    cache.get("RJ", "2026-02-01", "2026-02-10", 6)  # Miss

    stats = cache.get_stats()

    assert stats["size"] == 1
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.5
    assert stats["ttl_seconds"] == 3600
