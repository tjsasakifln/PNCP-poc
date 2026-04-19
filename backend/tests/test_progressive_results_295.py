"""Tests for STORY-295: Progressive Results Delivery.

AC15: Test: 1 fast source + 1 slow → partial results in <10s
AC16: Test: 1 source fails → other sources deliver results
AC17: Test: all sources timeout → empty result with error details
AC18: Existing tests still pass (covered by CI)
"""

import asyncio
import time
import pytest

from consolidation import ConsolidationService, AllSourcesFailedError
from clients.base import (
    SourceAdapter,
    SourceMetadata,
    SourceStatus,
    UnifiedProcurement,
)
from progress import ProgressTracker


# ============================================================================
# Test helpers
# ============================================================================

def _make_record(source_name: str, source_id: str, cnpj: str = "12345678000100",
                 numero_edital: str = "001", ano: str = "2026",
                 objeto: str = "Material de limpeza", uf: str = "SP") -> UnifiedProcurement:
    """Helper to create a test UnifiedProcurement."""
    return UnifiedProcurement(
        source_id=source_id,
        source_name=source_name,
        objeto=objeto,
        valor_estimado=100000.0,
        orgao="Test Orgao",
        cnpj_orgao=cnpj,
        uf=uf,
        municipio="Sao Paulo",
        numero_edital=numero_edital,
        ano=ano,
    )


class FakeAdapter(SourceAdapter):
    """Fake adapter for testing progressive results."""

    def __init__(self, code: str, priority: int, records: list, delay: float = 0,
                 should_fail: bool = False, fail_error: Exception = None):
        self._code = code
        self._priority = priority
        self._records = records
        self._delay = delay
        self._should_fail = should_fail
        self._fail_error = fail_error or Exception(f"{code} failed")

    @property
    def metadata(self) -> SourceMetadata:
        return SourceMetadata(
            name=f"Test {self._code}",
            code=self._code,
            base_url="http://test.example.com",
            priority=self._priority,
        )

    async def health_check(self) -> SourceStatus:
        return SourceStatus.AVAILABLE

    async def fetch(self, data_inicial, data_final, ufs=None, **kwargs):
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._should_fail:
            raise self._fail_error
        for record in self._records:
            yield record

    def normalize(self, raw_record):
        pass


# ============================================================================
# AC15: 1 fast source + 1 slow → partial results emitted quickly
# ============================================================================

@pytest.mark.asyncio
async def test_fast_source_emits_partial_before_slow_completes():
    """AC15: When one source is fast and another is slow, on_source_done
    is called for the fast source BEFORE the slow source finishes."""
    fast_records = [
        _make_record("FAST", f"fast-{i}", cnpj=f"111{i:04d}", numero_edital=f"{i:03d}")
        for i in range(5)
    ]
    slow_records = [
        _make_record("SLOW", f"slow-{i}", cnpj=f"222{i:04d}", numero_edital=f"{i:03d}")
        for i in range(3)
    ]

    adapters = {
        "FAST": FakeAdapter("FAST", 1, fast_records, delay=0),
        "SLOW": FakeAdapter("SLOW", 2, slow_records, delay=2.0),
    }

    svc = ConsolidationService(
        adapters=adapters,
        timeout_per_source=10,
        timeout_global=15,
    )

    # Track on_source_done calls
    calls = []
    timestamps = []

    async def on_source_done(code, status, legacy_records, duration_ms, error):
        calls.append({
            "code": code,
            "status": status,
            "count": len(legacy_records),
            "error": error,
        })
        timestamps.append(time.time())

    start = time.time()
    result = await svc.fetch_all(
        data_inicial="2026-01-01",
        data_final="2026-01-10",
        on_source_done=on_source_done,
    )

    # FAST should have been called first
    assert len(calls) == 2
    assert calls[0]["code"] == "FAST"
    assert calls[0]["status"] == "success"
    assert calls[0]["count"] == 5
    assert calls[0]["error"] is None

    # FAST callback should have been called in < 1s (well before SLOW)
    assert timestamps[0] - start < 1.0

    # SLOW completes after ~2s
    assert calls[1]["code"] == "SLOW"
    assert calls[1]["status"] == "success"
    assert calls[1]["count"] == 3

    # Total result has all records
    assert result.total_after_dedup == 8


@pytest.mark.asyncio
async def test_partial_results_timing_under_10s():
    """AC15: First partial result should appear in <10s even if another source is slow."""
    fast_records = [_make_record("FAST", "fast-1", cnpj="11100001")]
    # Slow source takes 5s but we should get fast results in <1s
    slow_records = [_make_record("SLOW", "slow-1", cnpj="22200001")]

    adapters = {
        "FAST": FakeAdapter("FAST", 1, fast_records, delay=0),
        "SLOW": FakeAdapter("SLOW", 2, slow_records, delay=5.0),
    }

    svc = ConsolidationService(
        adapters=adapters,
        timeout_per_source=10,
        timeout_global=15,
    )

    first_partial_time = [None]
    start = time.time()

    async def on_source_done(code, status, legacy_records, duration_ms, error):
        if first_partial_time[0] is None and len(legacy_records) > 0:
            first_partial_time[0] = time.time() - start

    await svc.fetch_all(
        data_inicial="2026-01-01",
        data_final="2026-01-10",
        on_source_done=on_source_done,
    )

    assert first_partial_time[0] is not None
    assert first_partial_time[0] < 10.0, f"First partial at {first_partial_time[0]:.1f}s, should be <10s"


# ============================================================================
# AC16: 1 source fails → other sources deliver results
# ============================================================================

@pytest.mark.asyncio
async def test_one_source_fails_others_deliver():
    """AC16: If one source fails, results from other sources are still delivered."""
    ok_records = [
        _make_record("OK_SOURCE", f"ok-{i}", cnpj=f"111{i:04d}", numero_edital=f"{i:03d}")
        for i in range(3)
    ]

    adapters = {
        "OK_SOURCE": FakeAdapter("OK_SOURCE", 1, ok_records, delay=0),
        "FAIL_SOURCE": FakeAdapter("FAIL_SOURCE", 2, [], should_fail=True,
                                    fail_error=Exception("Connection refused")),
    }

    svc = ConsolidationService(
        adapters=adapters,
        timeout_per_source=5,
        timeout_global=10,
        fail_on_all_errors=True,
    )

    calls = []

    async def on_source_done(code, status, legacy_records, duration_ms, error):
        calls.append({"code": code, "status": status, "count": len(legacy_records), "error": error})

    result = await svc.fetch_all(
        data_inicial="2026-01-01",
        data_final="2026-01-10",
        on_source_done=on_source_done,
    )

    # Should have 2 callbacks
    assert len(calls) == 2

    # OK source delivered records
    ok_call = next(c for c in calls if c["code"] == "OK_SOURCE")
    assert ok_call["status"] == "success"
    assert ok_call["count"] == 3

    # Failed source reported error
    fail_call = next(c for c in calls if c["code"] == "FAIL_SOURCE")
    assert fail_call["status"] == "error"
    assert fail_call["count"] == 0
    assert fail_call["error"] is not None

    # Final result still has OK source records
    assert result.total_after_dedup == 3
    assert result.is_partial is True


@pytest.mark.asyncio
async def test_source_timeout_delivers_others():
    """AC16+AC6: Source timeout returns partial, other sources succeed."""
    fast_records = [_make_record("FAST", "fast-1", cnpj="11100001")]

    adapters = {
        "FAST": FakeAdapter("FAST", 1, fast_records, delay=0),
        # Slow source will timeout (delay > timeout_per_source)
        "SLOW": FakeAdapter("SLOW", 2, [_make_record("SLOW", "slow-1", cnpj="22200001")], delay=10),
    }

    svc = ConsolidationService(
        adapters=adapters,
        timeout_per_source=1,  # Very short timeout for test
        timeout_global=5,
    )

    calls = []

    async def on_source_done(code, status, legacy_records, duration_ms, error):
        calls.append({"code": code, "status": status, "count": len(legacy_records)})

    result = await svc.fetch_all(
        data_inicial="2026-01-01",
        data_final="2026-01-10",
        on_source_done=on_source_done,
    )

    assert len(calls) == 2
    fast_call = next(c for c in calls if c["code"] == "FAST")
    assert fast_call["status"] == "success"
    assert fast_call["count"] == 1

    # Result contains fast source records
    assert result.total_after_dedup >= 1
    assert result.is_partial is True


# ============================================================================
# AC17: All sources timeout → empty result with error details
# ============================================================================

@pytest.mark.asyncio
async def test_all_sources_timeout_empty_result():
    """AC17: When all sources timeout, raise AllSourcesFailedError."""
    adapters = {
        "SOURCE_A": FakeAdapter("SOURCE_A", 1, [_make_record("A", "a1")], delay=10),
        "SOURCE_B": FakeAdapter("SOURCE_B", 2, [_make_record("B", "b1")], delay=10),
    }

    svc = ConsolidationService(
        adapters=adapters,
        timeout_per_source=0.1,  # Tiny timeout forces all to timeout
        timeout_global=0.5,
        fail_on_all_errors=True,
    )

    calls = []

    async def on_source_done(code, status, legacy_records, duration_ms, error):
        calls.append({"code": code, "status": status, "error": error})

    with pytest.raises(AllSourcesFailedError) as exc_info:
        await svc.fetch_all(
            data_inicial="2026-01-01",
            data_final="2026-01-10",
            on_source_done=on_source_done,
        )

    # AllSourcesFailedError should contain details about each source
    assert "SOURCE_A" in str(exc_info.value) or "SOURCE_B" in str(exc_info.value)


@pytest.mark.asyncio
async def test_all_sources_fail_empty_result():
    """AC17: When all sources fail (not timeout), same behavior."""
    adapters = {
        "SOURCE_A": FakeAdapter("SOURCE_A", 1, [], should_fail=True,
                                 fail_error=Exception("API down")),
        "SOURCE_B": FakeAdapter("SOURCE_B", 2, [], should_fail=True,
                                 fail_error=Exception("Connection refused")),
    }

    svc = ConsolidationService(
        adapters=adapters,
        timeout_per_source=5,
        timeout_global=10,
        fail_on_all_errors=True,
    )

    calls = []

    async def on_source_done(code, status, legacy_records, duration_ms, error):
        calls.append({"code": code, "status": status, "error": error})

    with pytest.raises(AllSourcesFailedError):
        await svc.fetch_all(
            data_inicial="2026-01-01",
            data_final="2026-01-10",
            on_source_done=on_source_done,
        )

    # Both callbacks should have been called with error status
    assert len(calls) == 2
    for call in calls:
        assert call["status"] == "error"
        assert call["error"] is not None


# ============================================================================
# ProgressTracker: New event types
# ============================================================================

@pytest.mark.asyncio
async def test_tracker_emit_source_complete():
    """Test ProgressTracker.emit_source_complete produces correct event."""
    tracker = ProgressTracker("test-123", uf_count=5, use_redis=False)

    await tracker.emit_source_complete(
        source="PNCP",
        status="success",
        record_count=42,
        duration_ms=1500,
    )

    event = tracker.queue.get_nowait()
    assert event.stage == "source_complete"
    assert event.progress == -1  # Non-progress event
    assert "PNCP" in event.message
    assert event.detail["source"] == "PNCP"
    assert event.detail["source_status"] == "success"
    assert event.detail["record_count"] == 42
    assert event.detail["duration_ms"] == 1500


@pytest.mark.asyncio
async def test_tracker_emit_source_error():
    """Test ProgressTracker.emit_source_error produces correct event."""
    tracker = ProgressTracker("test-123", uf_count=5, use_redis=False)

    await tracker.emit_source_error(
        source="PORTAL_COMPRAS",
        error="Connection refused",
        duration_ms=500,
    )

    event = tracker.queue.get_nowait()
    assert event.stage == "source_error"
    assert event.progress == -1
    assert "PORTAL_COMPRAS" in event.message
    assert event.detail["source"] == "PORTAL_COMPRAS"
    # CIG-BE-progressive-partial: UX-428 AC3 added _sanitize_source_error which
    # maps raw error strings to user-friendly messages prefixed with the source
    # code. "Connection refused" doesn't match any keyword (auth/rate limit/
    # timeout/...) so it falls through to the default "<source>: erro temporário".
    assert event.detail["error"] == "PORTAL_COMPRAS: erro temporário"


@pytest.mark.asyncio
async def test_tracker_emit_progressive_results():
    """Test ProgressTracker.emit_progressive_results produces correct event."""
    tracker = ProgressTracker("test-123", uf_count=5, use_redis=False)

    await tracker.emit_progressive_results(
        source="PNCP",
        items_count=25,
        total_so_far=25,
        sources_completed=["PNCP"],
        sources_pending=["PORTAL_COMPRAS", "COMPRAS_GOV"],
    )

    event = tracker.queue.get_nowait()
    assert event.stage == "partial_results"
    assert 10 <= event.progress <= 55
    assert event.detail["source"] == "PNCP"
    assert event.detail["new_results_count"] == 25
    assert event.detail["total_so_far"] == 25
    assert event.detail["sources_completed"] == ["PNCP"]
    assert event.detail["sources_pending"] == ["PORTAL_COMPRAS", "COMPRAS_GOV"]


@pytest.mark.asyncio
async def test_source_complete_event_with_error():
    """Test source_complete event includes error details for failed sources."""
    tracker = ProgressTracker("test-456", uf_count=3, use_redis=False)

    await tracker.emit_source_complete(
        source="COMPRAS_GOV",
        status="timeout",
        record_count=0,
        duration_ms=90000,
        error="Timeout after 90s",
    )

    event = tracker.queue.get_nowait()
    assert event.stage == "source_complete"
    assert event.detail["source_status"] == "timeout"
    assert event.detail["error"] == "Timeout after 90s"
    assert event.detail["record_count"] == 0


# ============================================================================
# on_source_done callback integration with ConsolidationService
# ============================================================================

@pytest.mark.asyncio
async def test_on_source_done_receives_legacy_format():
    """Verify on_source_done callback receives records in legacy format (dicts)."""
    records = [_make_record("TEST", "test-1", cnpj="11100001")]

    adapters = {
        "TEST": FakeAdapter("TEST", 1, records, delay=0),
    }

    svc = ConsolidationService(adapters=adapters, timeout_per_source=5, timeout_global=10)

    received_records = []

    async def on_source_done(code, status, legacy_records, duration_ms, error):
        received_records.extend(legacy_records)

    await svc.fetch_all(
        data_inicial="2026-01-01",
        data_final="2026-01-10",
        on_source_done=on_source_done,
    )

    # Should receive legacy format (dicts, not UnifiedProcurement)
    assert len(received_records) == 1
    assert isinstance(received_records[0], dict)
    assert "objetoCompra" in received_records[0] or "objeto" in received_records[0]


@pytest.mark.asyncio
async def test_on_source_done_not_called_when_none():
    """Verify no error when on_source_done is None (backward compatible)."""
    records = [_make_record("TEST", "test-1", cnpj="11100001")]

    adapters = {
        "TEST": FakeAdapter("TEST", 1, records, delay=0),
    }

    svc = ConsolidationService(adapters=adapters, timeout_per_source=5, timeout_global=10)

    # Should not raise even without callback
    result = await svc.fetch_all(
        data_inicial="2026-01-01",
        data_final="2026-01-10",
    )

    assert result.total_after_dedup == 1


@pytest.mark.asyncio
async def test_progressive_results_progress_pct():
    """Verify progressive results progress percentage is in valid range."""
    tracker = ProgressTracker("test-pct", uf_count=5, use_redis=False)

    # 1 of 3 sources complete → ~25% of 10-55 range
    await tracker.emit_progressive_results(
        source="PNCP",
        items_count=10,
        total_so_far=10,
        sources_completed=["PNCP"],
        sources_pending=["PCP", "COMPRAS_GOV"],
    )
    event = tracker.queue.get_nowait()
    assert 10 <= event.progress <= 55

    # 2 of 3 sources complete
    await tracker.emit_progressive_results(
        source="PCP",
        items_count=5,
        total_so_far=15,
        sources_completed=["PNCP", "PCP"],
        sources_pending=["COMPRAS_GOV"],
    )
    event = tracker.queue.get_nowait()
    assert 10 <= event.progress <= 55

    # 3 of 3 sources complete
    await tracker.emit_progressive_results(
        source="COMPRAS_GOV",
        items_count=3,
        total_so_far=18,
        sources_completed=["PNCP", "PCP", "COMPRAS_GOV"],
        sources_pending=[],
    )
    event = tracker.queue.get_nowait()
    assert event.progress == 55  # max of fetch phase
