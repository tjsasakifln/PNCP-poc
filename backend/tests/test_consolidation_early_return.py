"""Tests for GTM-STAB-003 AC3: Consolidation early return.

When >=80% of requested UFs have responded AND elapsed time >80s,
return partial results instead of waiting for remaining UFs.
"""

import asyncio
from unittest.mock import patch

import pytest

from consolidation import ConsolidationService, ConsolidationResult, AllSourcesFailedError
from clients.base import (
    SourceAdapter,
    SourceMetadata,
    SourceStatus,
    UnifiedProcurement,
)


def _make_record(
    source_name: str,
    source_id: str,
    uf: str = "SP",
    cnpj: str = "12345678000100",
    numero_edital: str = "001",
    ano: str = "2026",
    objeto: str = "Material de limpeza",
) -> UnifiedProcurement:
    """Helper to create a test UnifiedProcurement with a specific UF."""
    return UnifiedProcurement(
        source_id=source_id,
        source_name=source_name,
        objeto=objeto,
        valor_estimado=100000.0,
        orgao="Test Orgao",
        cnpj_orgao=cnpj,
        uf=uf,
        municipio="Test City",
        numero_edital=numero_edital,
        ano=ano,
    )


class FakeAdapter(SourceAdapter):
    """Fake adapter for testing with configurable delay and UF-specific records."""

    def __init__(
        self,
        code: str,
        priority: int,
        records: list,
        delay: float = 0,
        should_fail: bool = False,
        fail_error: Exception = None,
    ):
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


# Patch middleware search_id_var so consolidation.py doesn't fail on import
_MIDDLEWARE_PATCH = patch(
    "consolidation.search_id_var",
    create=True,
)


def _mock_search_id_var():
    """Return a mock for middleware.search_id_var that works with .get()."""
    from unittest.mock import MagicMock
    mock_var = MagicMock()
    mock_var.get.return_value = "test-search-id"
    return mock_var


@pytest.fixture(autouse=True)
def _patch_middleware():
    """Patch middleware.search_id_var for all tests."""
    with patch("middleware.search_id_var", _mock_search_id_var()):
        yield


@pytest.fixture(autouse=True)
def _patch_health_registry():
    """Patch source_health_registry to avoid side effects."""
    # CIG-BE-consolidation-helpers-private (TD-008): source_health_registry is now
    # imported by consolidation.source_merger from source_config.sources, not exposed
    # at the consolidation package root.
    with patch("consolidation.source_merger.source_health_registry") as mock_registry:
        mock_registry.get_status.return_value = "available"
        yield mock_registry


# ============================================================================
# Test 1: Normal return when UFs respond within time (no early return)
# ============================================================================
@pytest.mark.asyncio
async def test_no_early_return_when_within_time():
    """4 UFs requested, 3 respond within 80s -> normal return (not early)."""
    # Records from 3 UFs — elapsed is under EARLY_RETURN_TIME_S
    # Use distinct objects to avoid TITLE-PREFIX-DEDUP (ISSUE-027) fuzzy match
    records = [
        _make_record("SRC", "r1", uf="SP", cnpj="111", numero_edital="001",
                     objeto="Aquisição de uniformes escolares para rede municipal"),
        _make_record("SRC", "r2", uf="RJ", cnpj="222", numero_edital="002",
                     objeto="Contratação de serviços de pavimentação asfáltica urbana"),
        _make_record("SRC", "r3", uf="MG", cnpj="333", numero_edital="003",
                     objeto="Serviço de limpeza predial e manutenção hospitalar"),
    ]

    adapter = FakeAdapter("SRC", priority=1, records=records, delay=0)
    svc = ConsolidationService(
        adapters={"SRC": adapter},
        timeout_per_source=10,
        timeout_global=120,
    )

    # Early return time is 80s — with 0 delay, elapsed << 80s
    with patch("config.EARLY_RETURN_TIME_S", 80.0), \
         patch("config.EARLY_RETURN_THRESHOLD_PCT", 0.8):
        result = await svc.fetch_all(
            "2026-01-01", "2026-01-31",
            ufs={"SP", "RJ", "MG", "BA"},
        )

    # Source completed normally (all records from adapter returned)
    assert result.is_partial is False
    assert result.degradation_reason is None
    assert len(result.records) == 3
    assert set(result.ufs_completed) == {"SP", "RJ", "MG"}
    assert set(result.ufs_pending) == {"BA"}


# ============================================================================
# Test 2: Early return when elapsed > threshold and >= 80% UFs responded
# ============================================================================
@pytest.mark.asyncio
async def test_early_return_triggers_on_timeout_threshold():
    """4 UFs, source A has 3 UFs (fast), source B has 1 UF (slow).
    Elapsed > early_return_time AND >= 80% -> early return with is_partial=True.
    """
    # Source A: returns records for SP, RJ, MG quickly
    # Use distinct objects to avoid TITLE-PREFIX-DEDUP (ISSUE-027) fuzzy match
    records_a = [
        _make_record("SRC_A", "a1", uf="SP", cnpj="111", numero_edital="001",
                     objeto="Aquisição de uniformes escolares para rede municipal"),
        _make_record("SRC_A", "a2", uf="RJ", cnpj="222", numero_edital="002",
                     objeto="Contratação de serviços de pavimentação asfáltica urbana"),
        _make_record("SRC_A", "a3", uf="MG", cnpj="333", numero_edital="003",
                     objeto="Serviço de limpeza predial e manutenção hospitalar"),
    ]
    # Source B: very slow, would return BA but won't finish in time
    records_b = [_make_record("SRC_B", "b1", uf="BA", cnpj="444", numero_edital="004",
                              objeto="Fornecimento de medicamentos para unidade de saúde")]

    adapter_a = FakeAdapter("SRC_A", priority=1, records=records_a, delay=0)
    adapter_b = FakeAdapter("SRC_B", priority=2, records=records_b, delay=10)

    svc = ConsolidationService(
        adapters={"SRC_A": adapter_a, "SRC_B": adapter_b},
        timeout_per_source=15,
        timeout_global=120,
    )

    # Use very low early return time to trigger in test (0.05s instead of 80s)
    # 75% = 3/4 UFs. With threshold at 0.7, this triggers.
    on_early_return_called = []

    async def on_early_return(completed, pending):
        on_early_return_called.append({"completed": completed, "pending": pending})

    with patch("config.EARLY_RETURN_TIME_S", 0.05), \
         patch("config.EARLY_RETURN_THRESHOLD_PCT", 0.7):
        result = await svc.fetch_all(
            "2026-01-01", "2026-01-31",
            ufs={"SP", "RJ", "MG", "BA"},
            on_early_return=on_early_return,
        )

    assert result.is_partial is True
    assert result.degradation_reason == "early_return_timeout"
    # Should have records from source A (3 UFs)
    assert len(result.records) >= 3
    assert "SP" in result.ufs_completed
    assert "RJ" in result.ufs_completed
    assert "MG" in result.ufs_completed
    # on_early_return callback was called
    assert len(on_early_return_called) == 1


# ============================================================================
# Test 3: NO early return when < 80% UFs responded
# ============================================================================
@pytest.mark.asyncio
async def test_no_early_return_when_below_threshold():
    """4 UFs, only 1 responds (25% < 80%), elapsed > 80s -> NO early return."""
    # Only 1 UF has records — below 80% threshold
    records = [_make_record("SRC_A", "a1", uf="SP", cnpj="111", numero_edital="001")]

    adapter_a = FakeAdapter("SRC_A", priority=1, records=records, delay=0)
    # Source B is slow but doesn't return matching UFs
    records_b = []
    adapter_b = FakeAdapter("SRC_B", priority=2, records=records_b, delay=0.1)

    svc = ConsolidationService(
        adapters={"SRC_A": adapter_a, "SRC_B": adapter_b},
        timeout_per_source=5,
        timeout_global=10,
    )

    # Even with very low early return time, 25% < 80% threshold
    with patch("config.EARLY_RETURN_TIME_S", 0.01), \
         patch("config.EARLY_RETURN_THRESHOLD_PCT", 0.8):
        result = await svc.fetch_all(
            "2026-01-01", "2026-01-31",
            ufs={"SP", "RJ", "MG", "BA"},
        )

    # Early return should NOT have triggered (only 25% UFs)
    # Result should not have early_return_timeout as degradation reason
    assert result.degradation_reason != "early_return_timeout"
    assert "SP" in result.ufs_completed


# ============================================================================
# Test 4: 100% UFs respond -> normal return regardless of time
# ============================================================================
@pytest.mark.asyncio
async def test_no_early_return_when_all_ufs_complete():
    """2 UFs, both respond -> normal return regardless of time (100% != early return)."""
    records = [
        _make_record("SRC", "r1", uf="SP", cnpj="111", numero_edital="001"),
        _make_record("SRC", "r2", uf="RJ", cnpj="222", numero_edital="002"),
    ]

    adapter = FakeAdapter("SRC", priority=1, records=records, delay=0)
    svc = ConsolidationService(
        adapters={"SRC": adapter},
        timeout_per_source=10,
        timeout_global=120,
    )

    with patch("config.EARLY_RETURN_TIME_S", 0.01), \
         patch("config.EARLY_RETURN_THRESHOLD_PCT", 0.8):
        result = await svc.fetch_all(
            "2026-01-01", "2026-01-31",
            ufs={"SP", "RJ"},
        )

    # All sources completed normally — no early return needed
    assert result.is_partial is False
    assert result.degradation_reason is None
    assert set(result.ufs_completed) == {"SP", "RJ"}
    assert result.ufs_pending == []


# ============================================================================
# Test 5: All UFs timeout -> returns error/empty (not partial)
# ============================================================================
@pytest.mark.asyncio
async def test_all_ufs_timeout_returns_error():
    """All sources fail -> AllSourcesFailedError, not partial."""
    adapter = FakeAdapter(
        "SRC", priority=1, records=[], should_fail=True,
        fail_error=Exception("Network error"),
    )
    svc = ConsolidationService(
        adapters={"SRC": adapter},
        timeout_per_source=5,
        timeout_global=10,
        fail_on_all_errors=True,
    )

    with patch("config.EARLY_RETURN_TIME_S", 0.01), \
         patch("config.EARLY_RETURN_THRESHOLD_PCT", 0.8):
        with pytest.raises(AllSourcesFailedError):
            await svc.fetch_all(
                "2026-01-01", "2026-01-31",
                ufs={"SP", "RJ", "MG"},
            )


# ============================================================================
# Test 6: Verify ufs_completed and ufs_pending lists are correct
# ============================================================================
@pytest.mark.asyncio
async def test_ufs_completed_and_pending_lists():
    """Verify ufs_completed and ufs_pending are accurately populated."""
    records = [
        _make_record("SRC", "r1", uf="SP", cnpj="111", numero_edital="001"),
        _make_record("SRC", "r2", uf="RJ", cnpj="222", numero_edital="002"),
        _make_record("SRC", "r3", uf="MG", cnpj="333", numero_edital="003"),
        _make_record("SRC", "r4", uf="SP", cnpj="444", numero_edital="004"),  # Duplicate UF — still counts as one
    ]

    adapter = FakeAdapter("SRC", priority=1, records=records, delay=0)
    svc = ConsolidationService(
        adapters={"SRC": adapter},
        timeout_per_source=10,
        timeout_global=120,
    )

    result = await svc.fetch_all(
        "2026-01-01", "2026-01-31",
        ufs={"SP", "RJ", "MG", "BA", "PE"},
    )

    # SP, RJ, MG have records — BA, PE don't
    assert sorted(result.ufs_completed) == ["MG", "RJ", "SP"]
    assert sorted(result.ufs_pending) == ["BA", "PE"]


# ============================================================================
# Test 7: Filter/ranking runs only on collected results (not pending)
# ============================================================================
@pytest.mark.asyncio
async def test_filter_ranking_on_collected_results_only():
    """When early return triggers, dedup/legacy conversion runs on available data only."""
    # Source A: 3 UFs fast
    # Use distinct objects to avoid TITLE-PREFIX-DEDUP (ISSUE-027) fuzzy match
    records_a = [
        _make_record("SRC_A", "a1", uf="SP", cnpj="111", numero_edital="001",
                     objeto="Aquisição de uniformes escolares para rede municipal"),
        _make_record("SRC_A", "a2", uf="RJ", cnpj="222", numero_edital="002",
                     objeto="Contratação de serviços de pavimentação asfáltica urbana"),
        _make_record("SRC_A", "a3", uf="MG", cnpj="333", numero_edital="003",
                     objeto="Serviço de limpeza predial e manutenção hospitalar"),
    ]
    # Source B: 1 UF extremely slow
    records_b = [_make_record("SRC_B", "b1", uf="BA", cnpj="444", numero_edital="004",
                              objeto="Fornecimento de medicamentos para unidade de saúde")]

    adapter_a = FakeAdapter("SRC_A", priority=1, records=records_a, delay=0)
    adapter_b = FakeAdapter("SRC_B", priority=2, records=records_b, delay=10)

    svc = ConsolidationService(
        adapters={"SRC_A": adapter_a, "SRC_B": adapter_b},
        timeout_per_source=15,
        timeout_global=120,
    )

    # Trigger early return with very low thresholds
    with patch("config.EARLY_RETURN_TIME_S", 0.05), \
         patch("config.EARLY_RETURN_THRESHOLD_PCT", 0.7):
        result = await svc.fetch_all(
            "2026-01-01", "2026-01-31",
            ufs={"SP", "RJ", "MG", "BA"},
        )

    # Should have exactly the records from source A that completed
    # Records are in legacy format (dicts), check they have the expected UFs
    result_ufs = set()
    for rec in result.records:
        uf = rec.get("uf", "")
        if uf:
            result_ufs.add(uf)

    assert "SP" in result_ufs
    assert "RJ" in result_ufs
    assert "MG" in result_ufs
    # BA might or might not be present depending on timing, but the dedup ran
    assert result.total_before_dedup >= 3
    assert result.total_after_dedup >= 3
    assert result.total_after_dedup <= result.total_before_dedup


# ============================================================================
# Test: ConsolidationResult has new fields with correct defaults
# ============================================================================
@pytest.mark.asyncio
async def test_consolidation_result_has_uf_fields():
    """ConsolidationResult dataclass has ufs_completed and ufs_pending with defaults."""
    result = ConsolidationResult(
        records=[],
        total_before_dedup=0,
        total_after_dedup=0,
        duplicates_removed=0,
        source_results=[],
        elapsed_ms=0,
    )

    assert result.ufs_completed == []
    assert result.ufs_pending == []
    assert result.is_partial is False
    assert result.degradation_reason is None


# ============================================================================
# Test: Early return with no UFs parameter (backward compat)
# ============================================================================
@pytest.mark.asyncio
async def test_early_return_skipped_when_no_ufs():
    """When ufs is None (no UF filter), early return logic is skipped."""
    records = [_make_record("SRC", "r1", uf="SP", cnpj="111", numero_edital="001")]
    adapter = FakeAdapter("SRC", priority=1, records=records, delay=0)

    svc = ConsolidationService(
        adapters={"SRC": adapter},
        timeout_per_source=10,
        timeout_global=120,
    )

    with patch("config.EARLY_RETURN_TIME_S", 0.01), \
         patch("config.EARLY_RETURN_THRESHOLD_PCT", 0.8):
        result = await svc.fetch_all("2026-01-01", "2026-01-31", ufs=None)

    # Should complete normally — early return doesn't apply without UF filter
    assert result.degradation_reason is None
    assert len(result.records) == 1
