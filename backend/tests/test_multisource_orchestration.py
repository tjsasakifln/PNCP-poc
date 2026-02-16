"""Tests for Multi-Source Orchestration & Failover (STORY-252 Track 3, AC12-AC17)."""

import asyncio
import time

import pytest
from unittest.mock import patch

from consolidation import (
    AllSourcesFailedError,
    ConsolidationResult,
    ConsolidationService,
)
from clients.base import (
    SourceAdapter,
    SourceMetadata,
    SourceStatus,
    UnifiedProcurement,
)
from source_config.sources import (
    SourceHealthRegistry,
    source_health_registry,
)


# ============ Helpers ============


def _make_record(
    source_name: str,
    source_id: str,
    cnpj: str = "12345678000100",
    numero_edital: str = "001",
    ano: str = "2026",
    objeto: str = "Material de limpeza",
) -> UnifiedProcurement:
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


@pytest.fixture(autouse=True)
def reset_health_registry():
    """Reset the global health registry before each test."""
    source_health_registry.reset()
    yield
    source_health_registry.reset()


# ============ AC12: Source Health Registry Tests ============


class TestSourceHealthRegistry:
    """Tests for SourceHealthRegistry (AC12)."""

    def test_new_source_is_healthy(self):
        """Unknown source defaults to healthy."""
        registry = SourceHealthRegistry()
        assert registry.get_status("UNKNOWN") == "healthy"

    def test_record_success_sets_healthy(self):
        """Recording success sets status to healthy."""
        registry = SourceHealthRegistry()
        registry.record_failure("PNCP")
        registry.record_failure("PNCP")
        registry.record_failure("PNCP")  # Now degraded
        assert registry.get_status("PNCP") == "degraded"

        registry.record_success("PNCP")
        assert registry.get_status("PNCP") == "healthy"

    def test_record_success_resets_consecutive_failures(self):
        """Success resets the consecutive failure counter."""
        registry = SourceHealthRegistry()
        registry.record_failure("PNCP")
        registry.record_failure("PNCP")
        registry.record_success("PNCP")
        # After success, 2 more failures should NOT trigger degraded
        registry.record_failure("PNCP")
        registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "healthy"

    def test_three_failures_sets_degraded(self):
        """3 consecutive failures transition to degraded."""
        registry = SourceHealthRegistry()
        registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "healthy"
        registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "healthy"
        registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "degraded"

    def test_five_failures_sets_down(self):
        """5 consecutive failures transition to down."""
        registry = SourceHealthRegistry()
        for _ in range(5):
            registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "down"

    def test_is_available_healthy(self):
        """Healthy source is available."""
        registry = SourceHealthRegistry()
        assert registry.is_available("PNCP") is True

    def test_is_available_degraded(self):
        """Degraded source is still available."""
        registry = SourceHealthRegistry()
        for _ in range(3):
            registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "degraded"
        assert registry.is_available("PNCP") is True

    def test_is_available_down(self):
        """Down source is NOT available."""
        registry = SourceHealthRegistry()
        for _ in range(5):
            registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "down"
        assert registry.is_available("PNCP") is False

    def test_status_persists_between_calls(self):
        """Status persists between get_status calls (in-memory persistence)."""
        registry = SourceHealthRegistry()
        registry.record_failure("PNCP")
        registry.record_failure("PNCP")
        registry.record_failure("PNCP")

        # Multiple calls should return same status
        assert registry.get_status("PNCP") == "degraded"
        assert registry.get_status("PNCP") == "degraded"
        assert registry.get_status("PNCP") == "degraded"

    def test_ttl_expiration_resets_to_healthy(self):
        """Status resets to healthy after TTL expires."""
        registry = SourceHealthRegistry()
        for _ in range(5):
            registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "down"

        # Simulate TTL expiration by manipulating updated_at
        entry = registry._statuses["PNCP"]
        entry.updated_at = time.time() - 301  # 301 seconds ago (TTL is 300)

        assert registry.get_status("PNCP") == "healthy"

    def test_ttl_not_expired_keeps_status(self):
        """Status remains unchanged before TTL expiration."""
        registry = SourceHealthRegistry()
        for _ in range(5):
            registry.record_failure("PNCP")
        assert registry.get_status("PNCP") == "down"

        # Simulate 4 minutes elapsed (under 5-minute TTL)
        entry = registry._statuses["PNCP"]
        entry.updated_at = time.time() - 240

        assert registry.get_status("PNCP") == "down"

    def test_reset_clears_all_statuses(self):
        """Reset clears the entire registry."""
        registry = SourceHealthRegistry()
        registry.record_failure("PNCP")
        registry.record_failure("PNCP")
        registry.record_failure("PNCP")
        registry.record_failure("Portal")

        registry.reset()
        assert registry.get_status("PNCP") == "healthy"
        assert registry.get_status("Portal") == "healthy"

    def test_multiple_sources_independent(self):
        """Each source tracks its own status independently."""
        registry = SourceHealthRegistry()
        for _ in range(3):
            registry.record_failure("PNCP")
        registry.record_success("Portal")

        assert registry.get_status("PNCP") == "degraded"
        assert registry.get_status("Portal") == "healthy"

    def test_module_level_singleton_exists(self):
        """The module-level singleton is a SourceHealthRegistry instance."""
        assert isinstance(source_health_registry, SourceHealthRegistry)


# ============ AC13: Automatic Failover Tests ============


class TestAutomaticFailover:
    """Tests for automatic failover when PNCP is degraded (AC13)."""

    @pytest.mark.asyncio
    async def test_failover_increases_alt_source_timeout_when_pncp_degraded(self):
        """When PNCP is degraded, alternative sources get 40s timeout instead of 25s."""
        # Mark PNCP as degraded
        for _ in range(3):
            source_health_registry.record_failure("PNCP")
        assert source_health_registry.get_status("PNCP") == "degraded"

        records_portal = [
            _make_record("Portal", "p1", cnpj="222", numero_edital="002")
        ]
        adapters = {
            "PNCP": FakeAdapter("PNCP", 1, []),  # Empty but succeeds
            "Portal": FakeAdapter("Portal", 2, records_portal),
        }

        svc = ConsolidationService(adapters=adapters, timeout_per_source=25)

        # Patch _wrap_source to capture the timeout values used
        original_wrap = svc._wrap_source
        captured_timeouts = {}

        async def capturing_wrap(code, coro, timeout=None):
            captured_timeouts[code] = timeout
            return await original_wrap(code, coro, timeout=timeout)

        svc._wrap_source = capturing_wrap
        await svc.fetch_all("2026-01-01", "2026-01-31")

        # PNCP should keep its original timeout (25)
        assert captured_timeouts["PNCP"] == 25
        # Portal should get increased timeout (40)
        assert captured_timeouts["Portal"] == 40

    @pytest.mark.asyncio
    async def test_no_failover_when_pncp_healthy(self):
        """When PNCP is healthy, all sources use default timeout."""
        source_health_registry.record_success("PNCP")

        records_pncp = [_make_record("PNCP", "p1")]
        records_portal = [
            _make_record("Portal", "p2", cnpj="222", numero_edital="002")
        ]
        adapters = {
            "PNCP": FakeAdapter("PNCP", 1, records_pncp),
            "Portal": FakeAdapter("Portal", 2, records_portal),
        }

        svc = ConsolidationService(adapters=adapters, timeout_per_source=25)

        original_wrap = svc._wrap_source
        captured_timeouts = {}

        async def capturing_wrap(code, coro, timeout=None):
            captured_timeouts[code] = timeout
            return await original_wrap(code, coro, timeout=timeout)

        svc._wrap_source = capturing_wrap
        await svc.fetch_all("2026-01-01", "2026-01-31")

        # Both sources should use default timeout
        assert captured_timeouts["PNCP"] == 25
        assert captured_timeouts["Portal"] == 25


# ============ AC14: Degraded Mode Tests ============


class TestDegradedMode:
    """Tests for degraded mode with partial results (AC14)."""

    @pytest.mark.asyncio
    async def test_partial_results_when_one_source_fails(self):
        """is_partial=True when some sources fail but others return data."""
        records_ok = [_make_record("OK_SOURCE", "ok1")]

        adapters = {
            "FAIL_SOURCE": FakeAdapter("FAIL_SOURCE", 1, [], should_fail=True),
            "OK_SOURCE": FakeAdapter("OK_SOURCE", 2, records_ok),
        }

        svc = ConsolidationService(adapters=adapters)
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        assert result.is_partial is True
        assert result.degradation_reason is not None
        assert "FAIL_SOURCE" in result.degradation_reason
        assert result.total_after_dedup == 1

    @pytest.mark.asyncio
    async def test_not_partial_when_all_sources_succeed(self):
        """is_partial=False when all sources return data successfully."""
        records_a = [_make_record("SOURCE_A", "a1", cnpj="111")]
        records_b = [
            _make_record("SOURCE_B", "b1", cnpj="222", numero_edital="002")
        ]

        adapters = {
            "SOURCE_A": FakeAdapter("SOURCE_A", 1, records_a),
            "SOURCE_B": FakeAdapter("SOURCE_B", 2, records_b),
        }

        svc = ConsolidationService(adapters=adapters)
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        assert result.is_partial is False
        assert result.degradation_reason is None
        assert result.total_after_dedup == 2

    @pytest.mark.asyncio
    async def test_all_fail_raises_error_not_empty_results(self):
        """When 0 sources return data, raises AllSourcesFailedError (AC14)."""
        adapters = {
            "FAIL_A": FakeAdapter("FAIL_A", 1, [], should_fail=True),
            "FAIL_B": FakeAdapter("FAIL_B", 2, [], should_fail=True),
        }

        svc = ConsolidationService(adapters=adapters, fail_on_all_errors=True)
        with pytest.raises(AllSourcesFailedError) as exc_info:
            await svc.fetch_all("2026-01-01", "2026-01-31")

        assert "FAIL_A" in str(exc_info.value)
        assert "FAIL_B" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_partial_with_timeout_source(self):
        """is_partial=True when one source times out but others succeed."""
        records_ok = [_make_record("FAST", "f1")]

        adapters = {
            "SLOW": FakeAdapter("SLOW", 1, [], delay=10),  # Will timeout
            "FAST": FakeAdapter("FAST", 2, records_ok),
        }

        svc = ConsolidationService(adapters=adapters, timeout_per_source=0.1)
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        assert result.is_partial is True
        assert "SLOW" in result.degradation_reason


# ============ AC15: ComprasGov Fallback Tests ============


class TestComprasGovFallback:
    """Tests for ComprasGov as last-resort fallback (AC15)."""

    @pytest.mark.asyncio
    async def test_fallback_tried_when_all_primary_sources_fail(self):
        """ComprasGov fallback is tried when ALL primary sources fail."""
        fallback_records = [
            _make_record("ComprasGov", "cg1", cnpj="333", numero_edital="003")
        ]

        adapters = {
            "PNCP": FakeAdapter("PNCP", 1, [], should_fail=True),
            "Portal": FakeAdapter("Portal", 2, [], should_fail=True),
        }
        fallback = FakeAdapter("ComprasGov", 4, fallback_records)

        svc = ConsolidationService(
            adapters=adapters,
            fail_on_all_errors=True,
            fallback_adapter=fallback,
        )
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        # Should NOT raise because fallback returned data
        assert result.total_after_dedup == 1
        assert result.records[0]["_source"] == "ComprasGov"

        # Fallback should appear in source_results
        cg_sr = next(
            sr for sr in result.source_results if sr.source_code == "ComprasGov"
        )
        assert cg_sr.status == "success"
        assert cg_sr.record_count == 1

    @pytest.mark.asyncio
    async def test_fallback_not_tried_when_some_sources_succeed(self):
        """Fallback is NOT tried when at least one primary source returns data."""
        records_ok = [_make_record("PNCP", "p1")]
        fallback_records = [_make_record("ComprasGov", "cg1", cnpj="333")]

        adapters = {
            "PNCP": FakeAdapter("PNCP", 1, records_ok),
            "Portal": FakeAdapter("Portal", 2, [], should_fail=True),
        }
        fallback = FakeAdapter("ComprasGov", 4, fallback_records)

        svc = ConsolidationService(
            adapters=adapters,
            fallback_adapter=fallback,
        )
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        # Fallback should NOT be in source_results
        cg_results = [
            sr for sr in result.source_results if sr.source_code == "ComprasGov"
        ]
        assert len(cg_results) == 0
        assert result.total_after_dedup == 1

    @pytest.mark.asyncio
    async def test_fallback_not_tried_when_already_primary(self):
        """Fallback is NOT tried if ComprasGov was already a primary source."""
        adapters = {
            "PNCP": FakeAdapter("PNCP", 1, [], should_fail=True),
            "ComprasGov": FakeAdapter("ComprasGov", 4, [], should_fail=True),
        }
        fallback = FakeAdapter("ComprasGov", 4, [_make_record("ComprasGov", "x1")])

        svc = ConsolidationService(
            adapters=adapters,
            fail_on_all_errors=True,
            fallback_adapter=fallback,
        )

        with pytest.raises(AllSourcesFailedError):
            await svc.fetch_all("2026-01-01", "2026-01-31")

    @pytest.mark.asyncio
    async def test_fallback_also_fails_raises_error(self):
        """If fallback also fails, AllSourcesFailedError is raised."""
        adapters = {
            "PNCP": FakeAdapter("PNCP", 1, [], should_fail=True),
        }
        fallback = FakeAdapter("ComprasGov", 4, [], should_fail=True)

        svc = ConsolidationService(
            adapters=adapters,
            fail_on_all_errors=True,
            fallback_adapter=fallback,
        )

        with pytest.raises(AllSourcesFailedError) as exc_info:
            await svc.fetch_all("2026-01-01", "2026-01-31")

        # Both PNCP and ComprasGov should be in the error
        assert "PNCP" in str(exc_info.value)
        assert "ComprasGov" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fallback_uses_40s_timeout(self):
        """Fallback uses the FALLBACK_TIMEOUT (40s), not the default."""
        adapters = {
            "PNCP": FakeAdapter("PNCP", 1, [], should_fail=True),
        }
        fallback_records = [_make_record("ComprasGov", "cg1", cnpj="444")]
        fallback = FakeAdapter("ComprasGov", 4, fallback_records)

        svc = ConsolidationService(
            adapters=adapters,
            timeout_per_source=25,
            fallback_adapter=fallback,
        )

        original_wrap = svc._wrap_source
        fallback_timeout_used = None

        async def capturing_wrap(code, coro, timeout=None):
            nonlocal fallback_timeout_used
            if code == "ComprasGov":
                fallback_timeout_used = timeout
            return await original_wrap(code, coro, timeout=timeout)

        svc._wrap_source = capturing_wrap
        await svc.fetch_all("2026-01-01", "2026-01-31")

        assert fallback_timeout_used == 40

    @pytest.mark.asyncio
    async def test_no_fallback_adapter_all_fail_raises(self):
        """Without fallback_adapter, all failures raise AllSourcesFailedError."""
        adapters = {
            "PNCP": FakeAdapter("PNCP", 1, [], should_fail=True),
        }

        svc = ConsolidationService(
            adapters=adapters,
            fail_on_all_errors=True,
            fallback_adapter=None,
        )

        with pytest.raises(AllSourcesFailedError):
            await svc.fetch_all("2026-01-01", "2026-01-31")


# ============ AC16: Source Status in Response Tests ============


class TestSourceStatusInResponse:
    """Tests for detailed source_results in ConsolidationResult (AC16)."""

    @pytest.mark.asyncio
    async def test_source_results_present_for_all_sources(self):
        """ConsolidationResult includes a SourceResult for each source."""
        records_a = [_make_record("SOURCE_A", "a1", cnpj="111")]
        records_b = [
            _make_record("SOURCE_B", "b1", cnpj="222", numero_edital="002")
        ]

        adapters = {
            "SOURCE_A": FakeAdapter("SOURCE_A", 1, records_a),
            "SOURCE_B": FakeAdapter("SOURCE_B", 2, records_b),
        }

        svc = ConsolidationService(adapters=adapters)
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        assert len(result.source_results) == 2
        codes = {sr.source_code for sr in result.source_results}
        assert codes == {"SOURCE_A", "SOURCE_B"}

    @pytest.mark.asyncio
    async def test_source_result_success_fields(self):
        """Successful source has correct SourceResult fields."""
        records = [_make_record("PNCP", "p1")]
        adapters = {"PNCP": FakeAdapter("PNCP", 1, records)}

        svc = ConsolidationService(adapters=adapters)
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        sr = result.source_results[0]
        assert sr.source_code == "PNCP"
        assert sr.status == "success"
        assert sr.record_count == 1
        assert sr.duration_ms >= 0
        assert sr.error is None

    @pytest.mark.asyncio
    async def test_source_result_error_fields(self):
        """Failed source has correct SourceResult fields."""
        adapters = {"FAIL": FakeAdapter("FAIL", 1, [], should_fail=True)}

        svc = ConsolidationService(adapters=adapters, fail_on_all_errors=False)
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        sr = result.source_results[0]
        assert sr.source_code == "FAIL"
        assert sr.status == "error"
        assert sr.record_count == 0
        assert sr.error is not None

    @pytest.mark.asyncio
    async def test_source_result_timeout_fields(self):
        """Timed-out source has correct SourceResult fields."""
        adapters = {"SLOW": FakeAdapter("SLOW", 1, [], delay=10)}

        svc = ConsolidationService(
            adapters=adapters,
            timeout_per_source=0.05,
            fail_on_all_errors=False,
        )
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        sr = result.source_results[0]
        assert sr.source_code == "SLOW"
        assert sr.status == "timeout"
        assert sr.record_count == 0
        assert sr.error is not None
        assert "Timeout" in sr.error

    @pytest.mark.asyncio
    async def test_mixed_source_results(self):
        """Mix of success, error, and timeout sources all reported correctly."""
        records_ok = [_make_record("OK", "ok1")]

        adapters = {
            "OK": FakeAdapter("OK", 1, records_ok),
            "FAIL": FakeAdapter("FAIL", 2, [], should_fail=True),
            "SLOW": FakeAdapter("SLOW", 3, [], delay=10),
        }

        svc = ConsolidationService(adapters=adapters, timeout_per_source=0.05)
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        status_map = {sr.source_code: sr.status for sr in result.source_results}
        assert status_map["OK"] == "success"
        assert status_map["FAIL"] == "error"
        assert status_map["SLOW"] == "timeout"


# ============ AC17: Global Timeout Adjustment Tests ============


class TestGlobalTimeoutAdjustment:
    """Tests for global timeout increase when PNCP is degraded (AC17)."""

    @pytest.mark.asyncio
    async def test_global_timeout_increases_when_pncp_degraded(self):
        """Global timeout goes from 60s to 90s when PNCP is degraded."""
        # Mark PNCP as degraded
        for _ in range(3):
            source_health_registry.record_failure("PNCP")

        records = [_make_record("PNCP", "p1")]
        adapters = {"PNCP": FakeAdapter("PNCP", 1, records)}

        svc = ConsolidationService(
            adapters=adapters, timeout_global=60
        )

        # Patch asyncio.wait_for to capture the global timeout used
        original_wait_for = asyncio.wait_for
        captured_global_timeout = None

        async def patched_wait_for(coro, *, timeout=None):
            nonlocal captured_global_timeout
            # The first wait_for call in fetch_all is for the gather (global timeout)
            if captured_global_timeout is None:
                captured_global_timeout = timeout
            return await original_wait_for(coro, timeout=timeout)

        with patch("consolidation.asyncio.wait_for", side_effect=patched_wait_for):
            await svc.fetch_all("2026-01-01", "2026-01-31")

        assert captured_global_timeout == 90

    @pytest.mark.asyncio
    async def test_global_timeout_normal_when_pncp_healthy(self):
        """Global timeout remains at default (60s) when PNCP is healthy."""
        source_health_registry.record_success("PNCP")

        records = [_make_record("PNCP", "p1")]
        adapters = {"PNCP": FakeAdapter("PNCP", 1, records)}

        svc = ConsolidationService(
            adapters=adapters, timeout_global=60
        )

        original_wait_for = asyncio.wait_for
        captured_global_timeout = None

        async def patched_wait_for(coro, *, timeout=None):
            nonlocal captured_global_timeout
            if captured_global_timeout is None:
                captured_global_timeout = timeout
            return await original_wait_for(coro, timeout=timeout)

        with patch("consolidation.asyncio.wait_for", side_effect=patched_wait_for):
            await svc.fetch_all("2026-01-01", "2026-01-31")

        assert captured_global_timeout == 60

    @pytest.mark.asyncio
    async def test_global_timeout_increases_when_pncp_down(self):
        """Global timeout also increases when PNCP is down (not just degraded)."""
        for _ in range(5):
            source_health_registry.record_failure("PNCP")
        assert source_health_registry.get_status("PNCP") == "down"

        records = [_make_record("Portal", "p1")]
        adapters = {"Portal": FakeAdapter("Portal", 2, records)}

        svc = ConsolidationService(
            adapters=adapters, timeout_global=60
        )

        original_wait_for = asyncio.wait_for
        captured_global_timeout = None

        async def patched_wait_for(coro, *, timeout=None):
            nonlocal captured_global_timeout
            if captured_global_timeout is None:
                captured_global_timeout = timeout
            return await original_wait_for(coro, timeout=timeout)

        with patch("consolidation.asyncio.wait_for", side_effect=patched_wait_for):
            await svc.fetch_all("2026-01-01", "2026-01-31")

        assert captured_global_timeout == 90


# ============ Integration-style Tests ============


class TestHealthRegistryIntegration:
    """Integration tests verifying health registry updates during fetch_all."""

    @pytest.mark.asyncio
    async def test_fetch_all_records_success_in_registry(self):
        """Successful source fetch records success in health registry."""
        records = [_make_record("PNCP", "p1")]
        adapters = {"PNCP": FakeAdapter("PNCP", 1, records)}

        svc = ConsolidationService(adapters=adapters)
        await svc.fetch_all("2026-01-01", "2026-01-31")

        assert source_health_registry.get_status("PNCP") == "healthy"

    @pytest.mark.asyncio
    async def test_fetch_all_records_failure_in_registry(self):
        """Failed source fetch records failure in health registry."""
        adapters = {"PNCP": FakeAdapter("PNCP", 1, [], should_fail=True)}

        svc = ConsolidationService(adapters=adapters, fail_on_all_errors=False)
        await svc.fetch_all("2026-01-01", "2026-01-31")

        # After 1 failure, still healthy (need 3 for degraded)
        assert source_health_registry.get_status("PNCP") == "healthy"

        # Fetch again twice more to trigger degraded
        await svc.fetch_all("2026-01-01", "2026-01-31")
        await svc.fetch_all("2026-01-01", "2026-01-31")

        assert source_health_registry.get_status("PNCP") == "degraded"

    @pytest.mark.asyncio
    async def test_consecutive_failures_accumulate_across_fetch_all_calls(self):
        """Health status accumulates across multiple fetch_all invocations."""
        adapters = {"PNCP": FakeAdapter("PNCP", 1, [], should_fail=True)}

        svc = ConsolidationService(adapters=adapters, fail_on_all_errors=False)

        # 5 consecutive failures across 5 fetch_all calls
        for _ in range(5):
            await svc.fetch_all("2026-01-01", "2026-01-31")

        assert source_health_registry.get_status("PNCP") == "down"

    @pytest.mark.asyncio
    async def test_success_after_failures_resets_registry(self):
        """A successful fetch resets the failure counter in the registry."""
        fail_adapter = FakeAdapter("PNCP", 1, [], should_fail=True)
        ok_adapter = FakeAdapter("PNCP", 1, [_make_record("PNCP", "p1")])

        # 3 failures -> degraded
        svc_fail = ConsolidationService(
            adapters={"PNCP": fail_adapter}, fail_on_all_errors=False
        )
        for _ in range(3):
            await svc_fail.fetch_all("2026-01-01", "2026-01-31")
        assert source_health_registry.get_status("PNCP") == "degraded"

        # 1 success -> back to healthy
        svc_ok = ConsolidationService(adapters={"PNCP": ok_adapter})
        await svc_ok.fetch_all("2026-01-01", "2026-01-31")
        assert source_health_registry.get_status("PNCP") == "healthy"


# ============ Backward Compatibility Tests ============


class TestBackwardCompatibility:
    """Ensure existing interfaces still work with new fields."""

    @pytest.mark.asyncio
    async def test_consolidation_result_defaults(self):
        """New fields have safe defaults for backward compatibility."""
        result = ConsolidationResult(
            records=[],
            total_before_dedup=0,
            total_after_dedup=0,
            duplicates_removed=0,
            source_results=[],
            elapsed_ms=0,
        )
        assert result.is_partial is False
        assert result.degradation_reason is None

    @pytest.mark.asyncio
    async def test_service_works_without_fallback_adapter(self):
        """Service works correctly when no fallback_adapter is provided."""
        records = [_make_record("PNCP", "p1")]
        adapters = {"PNCP": FakeAdapter("PNCP", 1, records)}

        svc = ConsolidationService(adapters=adapters)
        result = await svc.fetch_all("2026-01-01", "2026-01-31")

        assert result.total_after_dedup == 1
        assert result.is_partial is False
