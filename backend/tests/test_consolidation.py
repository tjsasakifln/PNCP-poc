"""Tests for ConsolidationService (STORY-177 AC1)."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from consolidation import ConsolidationService, ConsolidationResult, SourceResult, AllSourcesFailedError
from clients.base import (
    SourceAdapter,
    SourceMetadata,
    SourceStatus,
    SourceCapability,
    UnifiedProcurement,
)


def _make_record(source_name: str, source_id: str, cnpj: str = "12345678000100",
                 numero_edital: str = "001", ano: str = "2026",
                 objeto: str = "Material de limpeza") -> UnifiedProcurement:
    """Helper to create a test UnifiedProcurement."""
    return UnifiedProcurement(
        source_id=source_id,
        source_name=source_name,
        objeto=objeto,
        valor_estimado=100000.0,
        orgao="Test Orgao",
        cnpj_orgao=cnpj,
        uf="SP",
        municipio="Sao Paulo",
        numero_edital=numero_edital,
        ano=ano,
    )


class FakeAdapter(SourceAdapter):
    """Fake adapter for testing."""

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


@pytest.mark.asyncio
async def test_two_sources_no_overlap():
    """Test with 2 sources returning different records → all appear."""
    records_a = [_make_record("SOURCE_A", "a1", cnpj="111", numero_edital="001")]
    records_b = [_make_record("SOURCE_B", "b1", cnpj="222", numero_edital="002")]

    adapters = {
        "SOURCE_A": FakeAdapter("SOURCE_A", 1, records_a),
        "SOURCE_B": FakeAdapter("SOURCE_B", 2, records_b),
    }

    svc = ConsolidationService(adapters=adapters)
    result = await svc.fetch_all("2026-01-01", "2026-01-31")

    assert result.total_after_dedup == 2
    assert result.duplicates_removed == 0
    assert len(result.records) == 2
    assert len(result.source_results) == 2
    assert all(sr.status == "success" for sr in result.source_results)


@pytest.mark.asyncio
async def test_dedup_keeps_higher_priority():
    """Test with 2 sources returning same dedup_key → keeps higher priority source."""
    # Same CNPJ + numero_edital + ano = same dedup_key
    record_a = _make_record("SOURCE_A", "a1", cnpj="111", numero_edital="001", ano="2026")
    record_b = _make_record("SOURCE_B", "b1", cnpj="111", numero_edital="001", ano="2026")

    adapters = {
        "SOURCE_A": FakeAdapter("SOURCE_A", 1, [record_a]),  # priority 1 = higher
        "SOURCE_B": FakeAdapter("SOURCE_B", 2, [record_b]),  # priority 2 = lower
    }

    svc = ConsolidationService(adapters=adapters)
    result = await svc.fetch_all("2026-01-01", "2026-01-31")

    assert result.total_before_dedup == 2
    assert result.total_after_dedup == 1
    assert result.duplicates_removed == 1
    # Should keep SOURCE_A (priority 1)
    assert result.records[0]["_source"] == "SOURCE_A"


@pytest.mark.asyncio
async def test_one_source_timeout_partial_results():
    """Test with 1 source timeout + 1 OK → returns partial results."""
    records_ok = [_make_record("OK_SOURCE", "ok1")]

    adapters = {
        "SLOW_SOURCE": FakeAdapter("SLOW_SOURCE", 1, [], delay=10),  # Will timeout
        "OK_SOURCE": FakeAdapter("OK_SOURCE", 2, records_ok),
    }

    svc = ConsolidationService(adapters=adapters, timeout_per_source=0.1)
    result = await svc.fetch_all("2026-01-01", "2026-01-31")

    assert result.total_after_dedup == 1
    # Check source results
    slow_sr = next(sr for sr in result.source_results if sr.source_code == "SLOW_SOURCE")
    ok_sr = next(sr for sr in result.source_results if sr.source_code == "OK_SOURCE")
    assert slow_sr.status == "timeout"
    assert ok_sr.status == "success"


@pytest.mark.asyncio
async def test_all_sources_fail_raises():
    """Test with all sources in error + fail_on_all_errors=True → raises exception."""
    adapters = {
        "FAIL_A": FakeAdapter("FAIL_A", 1, [], should_fail=True),
        "FAIL_B": FakeAdapter("FAIL_B", 2, [], should_fail=True),
    }

    svc = ConsolidationService(adapters=adapters, fail_on_all_errors=True)
    with pytest.raises(AllSourcesFailedError):
        await svc.fetch_all("2026-01-01", "2026-01-31")


@pytest.mark.asyncio
async def test_all_sources_fail_no_raise():
    """Test with all sources in error + fail_on_all_errors=False → returns empty list."""
    adapters = {
        "FAIL_A": FakeAdapter("FAIL_A", 1, [], should_fail=True),
        "FAIL_B": FakeAdapter("FAIL_B", 2, [], should_fail=True),
    }

    svc = ConsolidationService(adapters=adapters, fail_on_all_errors=False)
    result = await svc.fetch_all("2026-01-01", "2026-01-31")

    assert result.total_after_dedup == 0
    assert len(result.records) == 0


@pytest.mark.asyncio
async def test_on_source_complete_callback():
    """Test that on_source_complete callback is called for each source."""
    records_a = [_make_record("SOURCE_A", "a1")]
    records_b = [_make_record("SOURCE_B", "b1", cnpj="222")]

    adapters = {
        "SOURCE_A": FakeAdapter("SOURCE_A", 1, records_a),
        "SOURCE_B": FakeAdapter("SOURCE_B", 2, records_b),
    }

    callback_calls = []

    def on_complete(source_code, count, error):
        callback_calls.append((source_code, count, error))

    svc = ConsolidationService(adapters=adapters)
    await svc.fetch_all("2026-01-01", "2026-01-31", on_source_complete=on_complete)

    assert len(callback_calls) == 2
    codes = {c[0] for c in callback_calls}
    assert "SOURCE_A" in codes
    assert "SOURCE_B" in codes


@pytest.mark.asyncio
async def test_empty_adapters():
    """Test with no adapters → returns empty result."""
    svc = ConsolidationService(adapters={})
    result = await svc.fetch_all("2026-01-01", "2026-01-31")

    assert result.total_after_dedup == 0
    assert len(result.records) == 0
    assert len(result.source_results) == 0


@pytest.mark.asyncio
async def test_legacy_format_output():
    """Test that records are converted to legacy format."""
    record = _make_record("PNCP", "test1", objeto="Uniformes escolares")

    adapters = {
        "PNCP": FakeAdapter("PNCP", 1, [record]),
    }

    svc = ConsolidationService(adapters=adapters)
    result = await svc.fetch_all("2026-01-01", "2026-01-31")

    assert len(result.records) == 1
    legacy = result.records[0]
    assert "objetoCompra" in legacy
    assert legacy["objetoCompra"] == "Uniformes escolares"
    assert "_source" in legacy
    assert legacy["_source"] == "PNCP"
    assert "_dedup_key" in legacy


@pytest.mark.asyncio
async def test_health_check_all():
    """Test health_check_all runs checks in parallel."""
    adapters = {
        "SOURCE_A": FakeAdapter("SOURCE_A", 1, []),
        "SOURCE_B": FakeAdapter("SOURCE_B", 2, []),
    }

    svc = ConsolidationService(adapters=adapters)
    results = await svc.health_check_all()

    assert "SOURCE_A" in results
    assert "SOURCE_B" in results
    assert results["SOURCE_A"]["status"] == "available"
