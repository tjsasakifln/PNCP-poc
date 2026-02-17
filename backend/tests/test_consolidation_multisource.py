"""
Integration tests for multi-source consolidation.

Tests AC30 (cross-source deduplication), AC31 (partial failure handling),
and AC33 (full integration with multiple sources).

These tests verify that ConsolidationService correctly:
- Deduplicates identical procurements from different sources
- Preserves higher-priority source data in dedup conflicts
- Handles partial failures gracefully (some sources succeed, others fail)
- Merges results from multiple sources with correct metadata
- Reports per-source statistics and timing
"""

import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from unittest.mock import AsyncMock

import pytest

from clients.base import (
    SourceAdapter,
    SourceMetadata,
    SourceStatus,
    UnifiedProcurement,
    SourceCapability,
)
from consolidation import ConsolidationService, AllSourcesFailedError


# ============ Mock Adapter Implementations ============


class MockSourceAdapter(SourceAdapter):
    """
    Mock source adapter for testing.

    Can be configured to:
    - Return predefined records
    - Raise exceptions
    - Simulate timeouts
    """

    def __init__(
        self,
        code: str,
        name: str,
        priority: int = 1,
        records: Optional[List[UnifiedProcurement]] = None,
        should_fail: bool = False,
        error_message: str = "Mock error",
        delay_seconds: float = 0.0,
    ):
        self._metadata = SourceMetadata(
            name=name,
            code=code,
            base_url=f"https://mock-{code.lower()}.api",
            priority=priority,
            capabilities={SourceCapability.DATE_RANGE},
        )
        self._records = records or []
        self._should_fail = should_fail
        self._error_message = error_message
        self._delay_seconds = delay_seconds
        self._fetch_call_count = 0
        self._health_check_call_count = 0

    @property
    def metadata(self) -> SourceMetadata:
        return self._metadata

    async def health_check(self) -> SourceStatus:
        self._health_check_call_count += 1
        if self._should_fail:
            return SourceStatus.UNAVAILABLE
        return SourceStatus.AVAILABLE

    async def fetch(
        self,
        data_inicial: str,
        data_final: str,
        ufs: Optional[Set[str]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[UnifiedProcurement, None]:
        self._fetch_call_count += 1

        if self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)

        if self._should_fail:
            raise Exception(self._error_message)

        for record in self._records:
            yield record

    def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
        # Not used in these tests - normalization happens in fetch()
        raise NotImplementedError("Mock adapter uses pre-normalized records")


# ============ Test Fixtures ============


def create_procurement(
    source_id: str,
    source_name: str,
    cnpj: str,
    numero_edital: str,
    ano: str,
    valor: float = 100000.0,
    objeto: str = "Test procurement",
) -> UnifiedProcurement:
    """Helper to create a UnifiedProcurement for testing."""
    return UnifiedProcurement(
        source_id=source_id,
        source_name=source_name,
        cnpj_orgao=cnpj,
        numero_edital=numero_edital,
        ano=ano,
        valor_estimado=valor,
        objeto=objeto,
        orgao="Test Agency",
        uf="SP",
        municipio="São Paulo",
        data_publicacao=datetime(2025, 1, 15),
    )


# ============ AC30: Cross-Source Deduplication Tests ============


@pytest.mark.asyncio
async def test_same_procurement_in_both_sources_keeps_higher_priority():
    """
    AC30: Same procurement in both PNCP and PCP → only 1 result.
    Higher-priority source (PNCP, priority=1) wins over lower-priority (PCP, priority=2).
    """
    # Same dedup key (cnpj:numero_edital:ano)
    pncp_record = create_procurement(
        source_id="PNCP-12345",
        source_name="PNCP",
        cnpj="12.345.678/0001-90",
        numero_edital="001/2025",
        ano="2025",
        valor=100000.0,
        objeto="Uniforms from PNCP",
    )
    pcp_record = create_procurement(
        source_id="PCP-67890",
        source_name="Portal",
        cnpj="12345678000190",  # Same CNPJ (normalized)
        numero_edital="001/2025",
        ano="2025",
        valor=100500.0,  # Slightly different value
        objeto="Uniforms from PCP",
    )

    pncp_adapter = MockSourceAdapter(
        code="PNCP", name="PNCP", priority=1, records=[pncp_record]
    )
    pcp_adapter = MockSourceAdapter(
        code="Portal", name="Portal", priority=2, records=[pcp_record]
    )

    service = ConsolidationService(
        adapters={"PNCP": pncp_adapter, "Portal": pcp_adapter}
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Only 1 record (deduplicated)
    assert result.total_before_dedup == 2
    assert result.total_after_dedup == 1
    assert result.duplicates_removed == 1
    assert len(result.records) == 1

    # Assert: Higher-priority source (PNCP) wins
    record = result.records[0]
    assert record["_source"] == "PNCP"
    assert record["numeroControlePNCP"] == "PNCP-12345"
    assert "PNCP" in record["objetoCompra"]


@pytest.mark.asyncio
async def test_different_procurements_from_different_sources_both_kept():
    """
    AC30: Different procurements from different sources → both kept.
    """
    pncp_record = create_procurement(
        source_id="PNCP-111",
        source_name="PNCP",
        cnpj="11.111.111/0001-11",
        numero_edital="001/2025",
        ano="2025",
    )
    pcp_record = create_procurement(
        source_id="PCP-222",
        source_name="Portal",
        cnpj="22.222.222/0001-22",
        numero_edital="002/2025",
        ano="2025",
    )

    pncp_adapter = MockSourceAdapter(code="PNCP", name="PNCP", records=[pncp_record])
    pcp_adapter = MockSourceAdapter(code="Portal", name="Portal", records=[pcp_record])

    service = ConsolidationService(
        adapters={"PNCP": pncp_adapter, "Portal": pcp_adapter}
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Both records kept (no deduplication)
    assert result.total_before_dedup == 2
    assert result.total_after_dedup == 2
    assert result.duplicates_removed == 0
    assert len(result.records) == 2

    # Assert: Both sources present
    sources = {r["_source"] for r in result.records}
    assert sources == {"PNCP", "Portal"}


@pytest.mark.asyncio
async def test_same_cnpj_different_edital_both_kept():
    """
    AC30: Same CNPJ but different edital → both kept.
    Dedup key includes numero_edital, so these are distinct procurements.
    """
    record1 = create_procurement(
        source_id="PNCP-100",
        source_name="PNCP",
        cnpj="12.345.678/0001-90",
        numero_edital="001/2025",
        ano="2025",
    )
    record2 = create_procurement(
        source_id="PNCP-200",
        source_name="PNCP",
        cnpj="12.345.678/0001-90",
        numero_edital="002/2025",  # Different edital
        ano="2025",
    )

    pncp_adapter = MockSourceAdapter(code="PNCP", name="PNCP", records=[record1, record2])

    service = ConsolidationService(adapters={"PNCP": pncp_adapter})

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Both records kept (different dedup keys)
    assert result.total_before_dedup == 2
    assert result.total_after_dedup == 2
    assert result.duplicates_removed == 0
    assert len(result.records) == 2


@pytest.mark.asyncio
async def test_dedup_with_three_sources_keeps_highest_priority():
    """
    AC30: Same procurement in 3 sources (PNCP, Portal, Licitar).
    Should keep only PNCP (priority=1), not Portal (priority=2) or Licitar (priority=3).
    """
    pncp_record = create_procurement(
        source_id="PNCP-X",
        source_name="PNCP",
        cnpj="99.999.999/0001-99",
        numero_edital="123/2025",
        ano="2025",
    )
    portal_record = create_procurement(
        source_id="PORTAL-X",
        source_name="Portal",
        cnpj="99999999000199",
        numero_edital="123/2025",
        ano="2025",
    )
    licitar_record = create_procurement(
        source_id="LICITAR-X",
        source_name="Licitar",
        cnpj="99.999.999/0001-99",
        numero_edital="123/2025",
        ano="2025",
    )

    pncp_adapter = MockSourceAdapter(
        code="PNCP", name="PNCP", priority=1, records=[pncp_record]
    )
    portal_adapter = MockSourceAdapter(
        code="Portal", name="Portal", priority=2, records=[portal_record]
    )
    licitar_adapter = MockSourceAdapter(
        code="Licitar", name="Licitar", priority=3, records=[licitar_record]
    )

    service = ConsolidationService(
        adapters={
            "PNCP": pncp_adapter,
            "Portal": portal_adapter,
            "Licitar": licitar_adapter,
        }
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Deduplication worked
    assert result.total_before_dedup == 3
    assert result.total_after_dedup == 1
    assert result.duplicates_removed == 2

    # Assert: PNCP wins (highest priority)
    assert result.records[0]["_source"] == "PNCP"
    assert result.records[0]["numeroControlePNCP"] == "PNCP-X"


# ============ AC31: Partial Failure Tests ============


@pytest.mark.asyncio
async def test_pcp_fails_pncp_succeeds_returns_pncp_results():
    """
    AC31: PCP adapter raises exception → PNCP results returned, is_partial=True.
    """
    pncp_record = create_procurement(
        source_id="PNCP-OK",
        source_name="PNCP",
        cnpj="11.111.111/0001-11",
        numero_edital="001/2025",
        ano="2025",
    )

    pncp_adapter = MockSourceAdapter(code="PNCP", name="PNCP", records=[pncp_record])
    pcp_adapter = MockSourceAdapter(
        code="Portal",
        name="Portal",
        should_fail=True,
        error_message="PCP API timeout",
    )

    service = ConsolidationService(
        adapters={"PNCP": pncp_adapter, "Portal": pcp_adapter}
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Partial success
    assert result.is_partial is True
    assert "Portal" in result.degradation_reason
    assert len(result.records) == 1
    assert result.records[0]["_source"] == "PNCP"

    # Assert: Source results reflect failure
    pncp_result = next(sr for sr in result.source_results if sr.source_code == "PNCP")
    pcp_result = next(sr for sr in result.source_results if sr.source_code == "Portal")

    assert pncp_result.status == "success"
    assert pncp_result.record_count == 1
    assert pcp_result.status == "error"
    assert pcp_result.record_count == 0
    assert "timeout" in pcp_result.error.lower()


@pytest.mark.asyncio
async def test_both_adapters_succeed_is_partial_false():
    """
    AC31: Both adapters succeed → all results merged, is_partial=False.
    """
    pncp_record = create_procurement(
        source_id="PNCP-1",
        source_name="PNCP",
        cnpj="11.111.111/0001-11",
        numero_edital="001/2025",
        ano="2025",
    )
    pcp_record = create_procurement(
        source_id="PCP-1",
        source_name="Portal",
        cnpj="22.222.222/0001-22",
        numero_edital="002/2025",
        ano="2025",
    )

    pncp_adapter = MockSourceAdapter(code="PNCP", name="PNCP", records=[pncp_record])
    pcp_adapter = MockSourceAdapter(code="Portal", name="Portal", records=[pcp_record])

    service = ConsolidationService(
        adapters={"PNCP": pncp_adapter, "Portal": pcp_adapter}
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Full success
    assert result.is_partial is False
    assert result.degradation_reason is None
    assert len(result.records) == 2

    # Assert: Both sources succeeded
    assert all(sr.status == "success" for sr in result.source_results)
    assert sum(sr.record_count for sr in result.source_results) == 2


@pytest.mark.asyncio
async def test_both_adapters_fail_raises_all_sources_failed_error():
    """
    AC31: Both adapters fail → raises AllSourcesFailedError.
    """
    pncp_adapter = MockSourceAdapter(
        code="PNCP",
        name="PNCP",
        should_fail=True,
        error_message="PNCP network error",
    )
    pcp_adapter = MockSourceAdapter(
        code="Portal",
        name="Portal",
        should_fail=True,
        error_message="PCP authentication failed",
    )

    service = ConsolidationService(
        adapters={"PNCP": pncp_adapter, "Portal": pcp_adapter},
        fail_on_all_errors=True,
    )

    with pytest.raises(AllSourcesFailedError) as exc_info:
        await service.fetch_all(data_inicial="2025-01-01", data_final="2025-01-31")

    # Assert: Exception contains both errors
    error = exc_info.value
    assert "PNCP" in error.source_errors
    assert "Portal" in error.source_errors
    assert "network error" in error.source_errors["PNCP"].lower()
    assert "authentication" in error.source_errors["Portal"].lower()


@pytest.mark.asyncio
async def test_both_fail_but_fallback_succeeds_returns_fallback_data():
    """
    AC31: Primary sources fail but fallback adapter succeeds → returns fallback data.
    """
    pncp_adapter = MockSourceAdapter(
        code="PNCP", name="PNCP", should_fail=True, error_message="PNCP down"
    )
    pcp_adapter = MockSourceAdapter(
        code="Portal", name="Portal", should_fail=True, error_message="PCP down"
    )

    fallback_record = create_procurement(
        source_id="FALLBACK-1",
        source_name="ComprasGov",
        cnpj="33.333.333/0001-33",
        numero_edital="999/2025",
        ano="2025",
    )
    fallback_adapter = MockSourceAdapter(
        code="ComprasGov", name="ComprasGov", records=[fallback_record]
    )

    service = ConsolidationService(
        adapters={"PNCP": pncp_adapter, "Portal": pcp_adapter},
        fallback_adapter=fallback_adapter,
        fail_on_all_errors=True,
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Fallback data returned
    assert len(result.records) == 1
    assert result.records[0]["_source"] == "ComprasGov"
    assert result.is_partial is True  # Still partial — primary sources failed even though fallback rescued

    # Assert: Fallback in source_results
    fallback_result = next(
        sr for sr in result.source_results if sr.source_code == "ComprasGov"
    )
    assert fallback_result.status == "success"
    assert fallback_result.record_count == 1


@pytest.mark.asyncio
async def test_partial_failure_one_of_three_sources_fails():
    """
    AC31: 1 out of 3 sources fails → partial results with is_partial=True.
    """
    pncp_record = create_procurement(
        source_id="PNCP-1", source_name="PNCP", cnpj="11.111.111/0001-11",
        numero_edital="001/2025", ano="2025"
    )
    portal_record = create_procurement(
        source_id="PORTAL-1", source_name="Portal", cnpj="22.222.222/0001-22",
        numero_edital="002/2025", ano="2025"
    )

    pncp_adapter = MockSourceAdapter(code="PNCP", name="PNCP", records=[pncp_record])
    portal_adapter = MockSourceAdapter(code="Portal", name="Portal", records=[portal_record])
    licitar_adapter = MockSourceAdapter(
        code="Licitar", name="Licitar", should_fail=True, error_message="Licitar timeout"
    )

    service = ConsolidationService(
        adapters={
            "PNCP": pncp_adapter,
            "Portal": portal_adapter,
            "Licitar": licitar_adapter,
        }
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Partial success
    assert result.is_partial is True
    assert "Licitar" in result.degradation_reason
    assert len(result.records) == 2  # PNCP + Portal

    # Assert: 2 succeeded, 1 failed
    success_count = sum(1 for sr in result.source_results if sr.status == "success")
    error_count = sum(1 for sr in result.source_results if sr.status == "error")
    assert success_count == 2
    assert error_count == 1


# ============ AC33: Integration Tests ============


@pytest.mark.asyncio
async def test_full_integration_merged_deduped_with_correct_metadata():
    """
    AC33: Full integration test with mock APIs.
    - Mock both PNCP and PCP
    - Verify merged + deduped results
    - Verify correct source metadata
    """
    # PNCP returns 3 records (2 unique, 1 duplicate with PCP)
    pncp_record1 = create_procurement(
        source_id="PNCP-100",
        source_name="PNCP",
        cnpj="10.000.000/0001-10",
        numero_edital="001/2025",
        ano="2025",
        valor=50000.0,
    )
    pncp_record2 = create_procurement(
        source_id="PNCP-200",
        source_name="PNCP",
        cnpj="20.000.000/0001-20",
        numero_edital="002/2025",
        ano="2025",
        valor=100000.0,
    )
    pncp_duplicate = create_procurement(
        source_id="PNCP-300",
        source_name="PNCP",
        cnpj="30.000.000/0001-30",
        numero_edital="003/2025",
        ano="2025",
        valor=150000.0,
    )

    # PCP returns 2 records (1 unique, 1 duplicate with PNCP)
    pcp_record1 = create_procurement(
        source_id="PCP-400",
        source_name="Portal",
        cnpj="40.000.000/0001-40",
        numero_edital="004/2025",
        ano="2025",
        valor=200000.0,
    )
    pcp_duplicate = create_procurement(
        source_id="PCP-300",  # Same as PNCP-300
        source_name="Portal",
        cnpj="30000000000130",  # Same CNPJ (normalized)
        numero_edital="003/2025",
        ano="2025",
        valor=151000.0,  # Slightly different value
    )

    pncp_adapter = MockSourceAdapter(
        code="PNCP",
        name="PNCP",
        priority=1,
        records=[pncp_record1, pncp_record2, pncp_duplicate],
    )
    pcp_adapter = MockSourceAdapter(
        code="Portal",
        name="Portal",
        priority=2,
        records=[pcp_record1, pcp_duplicate],
    )

    service = ConsolidationService(
        adapters={"PNCP": pncp_adapter, "Portal": pcp_adapter}
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Correct deduplication
    assert result.total_before_dedup == 5  # 3 from PNCP + 2 from PCP
    assert result.total_after_dedup == 4  # 1 duplicate removed
    assert result.duplicates_removed == 1
    assert len(result.records) == 4

    # Assert: Duplicate kept from PNCP (higher priority)
    duplicate_record = next(
        r for r in result.records if r["cnpjOrgao"] == "30.000.000/0001-30"
    )
    assert duplicate_record["_source"] == "PNCP"
    assert duplicate_record["numeroControlePNCP"] == "PNCP-300"

    # Assert: All expected records present
    source_ids = {r["numeroControlePNCP"] for r in result.records}
    assert source_ids == {"PNCP-100", "PNCP-200", "PNCP-300", "PCP-400"}

    # Assert: is_partial=False (both succeeded)
    assert result.is_partial is False

    # Assert: Source results contain per-source stats
    pncp_stats = next(sr for sr in result.source_results if sr.source_code == "PNCP")
    pcp_stats = next(sr for sr in result.source_results if sr.source_code == "Portal")

    assert pncp_stats.status == "success"
    assert pncp_stats.record_count == 3
    assert pncp_stats.duration_ms >= 0

    assert pcp_stats.status == "success"
    assert pcp_stats.record_count == 2
    assert pcp_stats.duration_ms >= 0


@pytest.mark.asyncio
async def test_sources_used_field_lists_only_successful_sources():
    """
    AC33: Verify sources_used field in response lists only sources that returned data.
    """
    pncp_record = create_procurement(
        source_id="PNCP-1",
        source_name="PNCP",
        cnpj="10.000.000/0001-10",
        numero_edital="001/2025",
        ano="2025",
    )

    pncp_adapter = MockSourceAdapter(code="PNCP", name="PNCP", records=[pncp_record])
    pcp_adapter = MockSourceAdapter(
        code="Portal", name="Portal", should_fail=True, error_message="PCP down"
    )

    service = ConsolidationService(
        adapters={"PNCP": pncp_adapter, "Portal": pcp_adapter}
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Derive sources_used from source_results (sources with record_count > 0)
    sources_used = [
        sr.source_code for sr in result.source_results if sr.record_count > 0
    ]

    # Assert: Only PNCP in sources_used (Portal failed)
    assert sources_used == ["PNCP"]
    assert len(result.records) == 1


@pytest.mark.asyncio
async def test_source_stats_contain_per_source_counts_and_timing():
    """
    AC33: Verify source_stats contain per-source record counts and timing.
    """
    pncp_record1 = create_procurement(
        source_id="PNCP-1", source_name="PNCP", cnpj="10.000.000/0001-10",
        numero_edital="001/2025", ano="2025"
    )
    pncp_record2 = create_procurement(
        source_id="PNCP-2", source_name="PNCP", cnpj="20.000.000/0001-20",
        numero_edital="002/2025", ano="2025"
    )
    pcp_record = create_procurement(
        source_id="PCP-1", source_name="Portal", cnpj="30.000.000/0001-30",
        numero_edital="003/2025", ano="2025"
    )

    pncp_adapter = MockSourceAdapter(
        code="PNCP", name="PNCP", records=[pncp_record1, pncp_record2]
    )
    pcp_adapter = MockSourceAdapter(code="Portal", name="Portal", records=[pcp_record])

    service = ConsolidationService(
        adapters={"PNCP": pncp_adapter, "Portal": pcp_adapter}
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: source_results present
    assert len(result.source_results) == 2

    # Assert: PNCP stats
    pncp_stats = next(sr for sr in result.source_results if sr.source_code == "PNCP")
    assert pncp_stats.status == "success"
    assert pncp_stats.record_count == 2
    assert pncp_stats.duration_ms >= 0
    assert pncp_stats.error is None

    # Assert: PCP stats
    pcp_stats = next(sr for sr in result.source_results if sr.source_code == "Portal")
    assert pcp_stats.status == "success"
    assert pcp_stats.record_count == 1
    assert pcp_stats.duration_ms >= 0
    assert pcp_stats.error is None

    # Assert: Overall timing
    assert result.elapsed_ms >= 0


@pytest.mark.asyncio
async def test_on_source_complete_callback_invoked_per_source():
    """
    AC33: Verify on_source_complete callback is invoked for each source with correct args.
    """
    pncp_record = create_procurement(
        source_id="PNCP-1", source_name="PNCP", cnpj="10.000.000/0001-10",
        numero_edital="001/2025", ano="2025"
    )

    pncp_adapter = MockSourceAdapter(code="PNCP", name="PNCP", records=[pncp_record])
    pcp_adapter = MockSourceAdapter(
        code="Portal", name="Portal", should_fail=True, error_message="PCP error"
    )

    service = ConsolidationService(
        adapters={"PNCP": pncp_adapter, "Portal": pcp_adapter}
    )

    # Track callback invocations
    callback_invocations = []

    def track_callback(source_code: str, count: int, error: Optional[str]):
        callback_invocations.append((source_code, count, error))

    await service.fetch_all(
        data_inicial="2025-01-01",
        data_final="2025-01-31",
        on_source_complete=track_callback,
    )

    # Assert: Callback invoked twice (once per source)
    assert len(callback_invocations) == 2

    # Assert: PNCP callback
    pncp_callback = next(cb for cb in callback_invocations if cb[0] == "PNCP")
    assert pncp_callback[1] == 1  # record count
    assert pncp_callback[2] is None  # no error

    # Assert: PCP callback
    pcp_callback = next(cb for cb in callback_invocations if cb[0] == "Portal")
    assert pcp_callback[1] == 0  # no records
    assert pcp_callback[2] is not None  # error message
    assert "PCP error" in pcp_callback[2]


@pytest.mark.asyncio
async def test_empty_adapters_returns_empty_result():
    """
    Edge case: ConsolidationService with no adapters returns empty result.
    """
    service = ConsolidationService(adapters={})

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    assert result.total_before_dedup == 0
    assert result.total_after_dedup == 0
    assert result.duplicates_removed == 0
    assert len(result.records) == 0
    assert len(result.source_results) == 0
    assert result.is_partial is False


@pytest.mark.asyncio
async def test_timeout_with_partial_records_salvaged():
    """
    AC31: Source times out but partial records are salvaged and returned.
    Requires async generator yielding records before timeout.
    """
    # Create a slow adapter that yields 2 records then times out
    async def slow_fetch_generator():
        # Yield 2 records quickly
        yield create_procurement(
            source_id="SLOW-1", source_name="SlowSource", cnpj="10.000.000/0001-10",
            numero_edital="001/2025", ano="2025"
        )
        yield create_procurement(
            source_id="SLOW-2", source_name="SlowSource", cnpj="20.000.000/0001-20",
            numero_edital="002/2025", ano="2025"
        )
        # Then hang indefinitely
        await asyncio.sleep(100)
        yield create_procurement(
            source_id="SLOW-3", source_name="SlowSource", cnpj="30.000.000/0001-30",
            numero_edital="003/2025", ano="2025"
        )

    class SlowAdapter(SourceAdapter):
        @property
        def metadata(self) -> SourceMetadata:
            return SourceMetadata(
                name="Slow Source",
                code="SlowSource",
                base_url="https://slow.api",
                priority=1,
            )

        async def health_check(self) -> SourceStatus:
            return SourceStatus.AVAILABLE

        async def fetch(
            self,
            data_inicial: str,
            data_final: str,
            ufs: Optional[Set[str]] = None,
            **kwargs: Any,
        ) -> AsyncGenerator[UnifiedProcurement, None]:
            async for record in slow_fetch_generator():
                yield record

        def normalize(self, raw_record: Dict[str, Any]) -> UnifiedProcurement:
            raise NotImplementedError()

    slow_adapter = SlowAdapter()

    service = ConsolidationService(
        adapters={"SlowSource": slow_adapter},
        timeout_per_source=1,  # 1 second timeout
    )

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Partial records salvaged
    # ConsolidationService._wrap_source() accumulates records in partial_collector
    # On timeout, it returns status="partial" with salvaged records
    assert result.is_partial is True
    assert len(result.records) >= 2  # At least 2 records yielded before timeout

    # Assert: Source status is "partial" (not "timeout" since we salvaged data)
    slow_stats = result.source_results[0]
    assert slow_stats.source_code == "SlowSource"
    assert slow_stats.status == "partial"
    assert slow_stats.record_count >= 2
    assert "Timeout" in slow_stats.error or "salvaged" in slow_stats.error


@pytest.mark.asyncio
async def test_dedup_key_fallback_uses_objeto_hash():
    """
    AC30: Dedup key generation fallback when numero_edital/ano missing.
    Uses cnpj:hash(objeto):valor instead.
    """
    # Create records without numero_edital/ano
    record1 = UnifiedProcurement(
        source_id="SRC1-1",
        source_name="Source1",
        cnpj_orgao="12.345.678/0001-90",
        numero_edital="",  # Empty
        ano="",  # Empty
        objeto="Aquisição de uniformes escolares",
        valor_estimado=100000.0,
        orgao="Test Org",
        uf="SP",
    )
    record2 = UnifiedProcurement(
        source_id="SRC2-1",
        source_name="Source2",
        cnpj_orgao="12345678000190",  # Same CNPJ (normalized)
        numero_edital="",
        ano="",
        objeto="Aquisição de uniformes escolares",  # Same objeto
        valor_estimado=100000.0,  # Same value
        orgao="Test Org 2",
        uf="SP",
    )

    adapter1 = MockSourceAdapter(code="Source1", name="Source1", priority=1, records=[record1])
    adapter2 = MockSourceAdapter(code="Source2", name="Source2", priority=2, records=[record2])

    service = ConsolidationService(adapters={"Source1": adapter1, "Source2": adapter2})

    result = await service.fetch_all(
        data_inicial="2025-01-01", data_final="2025-01-31"
    )

    # Assert: Records deduplicated using fallback key
    # Both have same cnpj, same objeto (→ same hash), same valor
    # So they should be treated as duplicates
    assert result.total_before_dedup == 2
    assert result.total_after_dedup == 1
    assert result.duplicates_removed == 1

    # Assert: Higher priority source wins
    assert result.records[0]["_source"] == "Source1"
