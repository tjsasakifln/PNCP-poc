"""STORY-316 AC19-AC21: Tests for health canary, uptime calculation, and incident detection."""

from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

import pytest

from health import (
    HealthStatus,
    SourceHealthResult,
    check_source_health,
    calculate_overall_status,
    get_public_status,
    calculate_uptime_percentages,
    save_health_check,
    detect_incident,
    get_recent_incidents,
    get_uptime_history,
    cleanup_old_health_checks,
)


# ============================================================================
# AC19: Canary realistic tests
# ============================================================================


class TestRealisticCanary:
    """STORY-316 AC19: Tests for realistic canary parameters."""

    @pytest.mark.asyncio
    async def test_pncp_canary_uses_page_size_50(self):
        """AC1: PNCP canary uses tamanhoPagina=50 (same as production)."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("health.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await check_source_health("PNCP", timeout=10.0)

            # DEBT-008: Now makes 2 calls (canary at 50 + validation at 51)
            # Check the first call uses tamanhoPagina=50
            first_call = mock_client.get.call_args_list[0]
            params = first_call.kwargs.get("params", first_call.args[1] if len(first_call.args) > 1 else {})
            assert params["tamanhoPagina"] == 50
            assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_pcp_canary_uses_v2_endpoint(self):
        """AC1: PCP v2 canary uses real pagination endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("health.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await check_source_health("Portal", timeout=10.0)

            call_args = mock_client.get.call_args
            url = call_args.args[0]
            assert "v2/licitacao/processos" in url
            assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_comprasgov_canary_returns_unknown_source(self):
        """W1-PR2: ComprasGov removed from SOURCE_HEALTH_ENDPOINTS (offline since 2026-03-03).
        check_source_health now returns UNHEALTHY with 'Unknown source' error."""
        result = await check_source_health("ComprasGov", timeout=10.0)

        assert result.status == HealthStatus.UNHEALTHY
        assert "Unknown source" in result.error

    @pytest.mark.asyncio
    async def test_canary_timeout_returns_degraded(self):
        """AC1: Canary returns DEGRADED on timeout."""
        import httpx

        with patch("health.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client_cls.return_value = mock_client

            result = await check_source_health("PNCP", timeout=10.0)
            assert result.status == HealthStatus.DEGRADED
            assert result.error == "Timeout"

    @pytest.mark.asyncio
    async def test_canary_http_400_returns_degraded(self):
        """AC1: PNCP returns HTTP 400 when page size >50 — canary detects."""
        mock_response = MagicMock()
        mock_response.status_code = 400

        with patch("health.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await check_source_health("PNCP", timeout=10.0)
            assert result.status == HealthStatus.DEGRADED
            assert "400" in result.error


class TestPublicStatus:
    """STORY-316 AC2-AC3: Tests for public status endpoint."""

    @pytest.mark.asyncio
    async def test_public_status_returns_per_source(self):
        """AC2: Public status returns per-source status."""
        healthy_result = SourceHealthResult(
            source_code="PNCP",
            status=HealthStatus.HEALTHY,
            response_time_ms=450,
        )
        with patch("health.check_all_sources_health", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {"PNCP": healthy_result, "Portal": healthy_result}
            with patch("redis_pool.get_redis_pool", new_callable=AsyncMock) as mock_redis:
                mock_pool = AsyncMock()
                mock_pool.ping = AsyncMock()
                mock_redis.return_value = mock_pool
                with patch("supabase_client.get_supabase") as mock_sb:
                    mock_sb.return_value = MagicMock()
                    with patch("supabase_client.sb_execute", new_callable=AsyncMock) as mock_exec:
                        mock_exec.return_value = SimpleNamespace(data=[{"id": "1"}])
                        with patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True):
                            with patch("health.calculate_uptime_percentages", new_callable=AsyncMock) as mock_up:
                                mock_up.return_value = {"24h": 99.5, "7d": 98.0, "30d": 97.5}
                                with patch("health.get_last_incident", new_callable=AsyncMock, return_value=None):
                                    result = await get_public_status()

        assert result["status"] == "healthy"
        assert "pncp" in result["sources"]
        assert "portal" in result["sources"]
        assert result["sources"]["pncp"]["status"] == "healthy"
        assert result["sources"]["pncp"]["latency_ms"] == 450
        assert result["components"]["redis"] == "healthy"
        assert result["uptime_pct_24h"] == 99.5

    @pytest.mark.asyncio
    async def test_public_status_degraded_when_source_unhealthy(self):
        """AC2: Status is degraded when a source is unhealthy."""
        pncp = SourceHealthResult(source_code="PNCP", status=HealthStatus.HEALTHY, response_time_ms=100)
        pcp = SourceHealthResult(source_code="Portal", status=HealthStatus.UNHEALTHY, error="timeout")

        with patch("health.check_all_sources_health", new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {"PNCP": pncp, "Portal": pcp}
            with patch("redis_pool.get_redis_pool", new_callable=AsyncMock) as mock_redis:
                mock_redis.return_value = AsyncMock(ping=AsyncMock())
                with patch("supabase_client.get_supabase") as mock_sb:
                    mock_sb.return_value = MagicMock()
                    with patch("supabase_client.sb_execute", new_callable=AsyncMock) as mock_exec:
                        mock_exec.return_value = SimpleNamespace(data=[{"id": "1"}])
                        with patch("job_queue.is_queue_available", new_callable=AsyncMock, return_value=True):
                            with patch("health.calculate_uptime_percentages", new_callable=AsyncMock, return_value={"24h": 50.0, "7d": 50.0, "30d": 50.0}):
                                with patch("health.get_last_incident", new_callable=AsyncMock, return_value=None):
                                    result = await get_public_status()

        assert result["status"] == "degraded"


# ============================================================================
# AC20: Uptime calculation tests
# ============================================================================


class TestUptimeCalculation:
    """STORY-316 AC20: Tests for uptime percentage calculation."""

    @pytest.mark.asyncio
    async def test_all_healthy_gives_100_percent(self):
        """AC7: All healthy checks = 100% uptime."""
        mock_resp = SimpleNamespace(data=[
            {"overall_status": "healthy"},
            {"overall_status": "healthy"},
            {"overall_status": "healthy"},
        ])
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock, return_value=mock_resp):
                result = await calculate_uptime_percentages()

        assert result["24h"] == 100.0
        assert result["7d"] == 100.0
        assert result["30d"] == 100.0

    @pytest.mark.asyncio
    async def test_mixed_statuses_gives_correct_percentage(self):
        """AC7: healthy=100, degraded=50, unhealthy=0."""
        mock_resp = SimpleNamespace(data=[
            {"overall_status": "healthy"},
            {"overall_status": "degraded"},
            {"overall_status": "unhealthy"},
            {"overall_status": "healthy"},
        ])
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock, return_value=mock_resp):
                result = await calculate_uptime_percentages()

        # (100 + 50 + 0 + 100) / 4 = 62.5
        assert result["24h"] == 62.5

    @pytest.mark.asyncio
    async def test_no_checks_gives_100_percent(self):
        """AC7: No checks yet = 100% (optimistic default)."""
        mock_resp = SimpleNamespace(data=[])
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock, return_value=mock_resp):
                result = await calculate_uptime_percentages()

        assert result["24h"] == 100.0


# ============================================================================
# AC21: Incident detection and auto-resolution tests
# ============================================================================


class TestIncidentDetection:
    """STORY-316 AC21: Tests for incident detection and auto-resolution."""

    @pytest.mark.asyncio
    async def test_creates_incident_on_degraded(self):
        """AC8: Creates incident when status changes to degraded."""
        ongoing_resp = SimpleNamespace(data=[])
        insert_resp = SimpleNamespace(data=[{"id": "inc-1"}])

        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock) as mock_exec:
                mock_exec.side_effect = [ongoing_resp, insert_resp]
                with patch("email_service.send_email") as mock_email:
                    mock_email.return_value = "email-id"
                    with patch("sentry_sdk.capture_message"):
                        await detect_incident("degraded", {
                            "pncp": {"status": "healthy"},
                            "portal": {"status": "degraded", "error": "timeout"},
                        })

                assert mock_exec.call_count == 2
                assert mock_email.called

    @pytest.mark.asyncio
    async def test_no_duplicate_incident_when_ongoing(self):
        """AC8: Does not create duplicate if incident already ongoing."""
        ongoing_resp = SimpleNamespace(data=[{"id": "inc-1", "status": "ongoing"}])

        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = ongoing_resp
                await detect_incident("degraded", {"pncp": {"status": "degraded"}})

                # Only 1 call (the ongoing check), no insert
                assert mock_exec.call_count == 1

    @pytest.mark.asyncio
    async def test_auto_resolve_after_3_healthy(self):
        """AC10: Auto-resolves incident after 3 consecutive healthy checks."""
        ongoing = {"id": "inc-1", "status": "ongoing", "description": "test incident"}
        ongoing_resp = SimpleNamespace(data=[ongoing])
        recent_resp = SimpleNamespace(data=[
            {"overall_status": "healthy"},
            {"overall_status": "healthy"},
            {"overall_status": "healthy"},
        ])
        update_resp = SimpleNamespace(data=[{"id": "inc-1"}])

        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock) as mock_exec:
                mock_exec.side_effect = [ongoing_resp, recent_resp, update_resp]
                with patch("email_service.send_email") as mock_email:
                    mock_email.return_value = "email-id"
                    await detect_incident("healthy", {})

                    assert mock_email.called
                    call_kwargs = mock_email.call_args
                    assert "resolvido" in call_kwargs.kwargs.get("subject", "").lower()

    @pytest.mark.asyncio
    async def test_no_resolve_with_less_than_3_healthy(self):
        """AC10: Does not resolve if less than 3 consecutive healthy."""
        ongoing = {"id": "inc-1", "status": "ongoing"}
        ongoing_resp = SimpleNamespace(data=[ongoing])
        recent_resp = SimpleNamespace(data=[
            {"overall_status": "healthy"},
            {"overall_status": "healthy"},
        ])

        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock) as mock_exec:
                mock_exec.side_effect = [ongoing_resp, recent_resp]
                await detect_incident("healthy", {})

                assert mock_exec.call_count == 2


# ============================================================================
# Supporting function tests
# ============================================================================


class TestSaveHealthCheck:
    """Tests for save_health_check."""

    @pytest.mark.asyncio
    async def test_saves_to_db(self):
        """AC6: Saves health check result to DB."""
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = SimpleNamespace(data=[])
                await save_health_check(
                    "healthy",
                    {"pncp": {"status": "healthy"}},
                    {"redis": "healthy"},
                    450,
                )
                assert mock_exec.called

    @pytest.mark.asyncio
    async def test_handles_save_error_gracefully(self):
        """AC6: Does not raise on DB error."""
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock, side_effect=Exception("DB error")):
                await save_health_check("healthy", {}, {}, None)


class TestRecentIncidents:
    """Tests for get_recent_incidents."""

    @pytest.mark.asyncio
    async def test_returns_incidents_list(self):
        """AC13: Returns list of recent incidents."""
        mock_data = [
            {"id": "1", "started_at": "2026-02-28T10:00:00Z", "status": "resolved"},
        ]
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = SimpleNamespace(data=mock_data)
                result = await get_recent_incidents(30)
                assert len(result) == 1
                assert result[0]["id"] == "1"


class TestUptimeHistory:
    """Tests for get_uptime_history."""

    @pytest.mark.asyncio
    async def test_groups_by_date(self):
        """AC12: Groups health checks by date for chart."""
        mock_data = [
            {"checked_at": "2026-02-27T10:00:00Z", "overall_status": "healthy"},
            {"checked_at": "2026-02-27T15:00:00Z", "overall_status": "healthy"},
            {"checked_at": "2026-02-28T10:00:00Z", "overall_status": "degraded"},
        ]
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = SimpleNamespace(data=mock_data)
                result = await get_uptime_history(90)

                assert len(result) == 2
                assert result[0]["date"] == "2026-02-27"
                assert result[0]["uptime_pct"] == 100.0
                assert result[1]["date"] == "2026-02-28"
                assert result[1]["uptime_pct"] == 50.0


class TestOverallStatus:
    """Tests for calculate_overall_status."""

    def test_all_healthy(self):
        """All sources healthy = HEALTHY."""
        sources = {
            "PNCP": SourceHealthResult("PNCP", HealthStatus.HEALTHY),
            "Portal": SourceHealthResult("Portal", HealthStatus.HEALTHY),
        }
        assert calculate_overall_status(sources) == HealthStatus.HEALTHY

    def test_pncp_unhealthy_is_unhealthy(self):
        """PNCP unhealthy = system UNHEALTHY."""
        sources = {
            "PNCP": SourceHealthResult("PNCP", HealthStatus.UNHEALTHY),
            "Portal": SourceHealthResult("Portal", HealthStatus.HEALTHY),
        }
        assert calculate_overall_status(sources) == HealthStatus.UNHEALTHY

    def test_mixed_is_degraded(self):
        """Mixed statuses = DEGRADED."""
        sources = {
            "PNCP": SourceHealthResult("PNCP", HealthStatus.HEALTHY),
            "Portal": SourceHealthResult("Portal", HealthStatus.UNHEALTHY),
        }
        assert calculate_overall_status(sources) == HealthStatus.DEGRADED

    def test_empty_is_unhealthy(self):
        """No sources = UNHEALTHY."""
        assert calculate_overall_status({}) == HealthStatus.UNHEALTHY


class TestCleanup:
    """Tests for cleanup_old_health_checks."""

    @pytest.mark.asyncio
    async def test_cleanup_returns_count(self):
        """Cleanup returns number of deleted records."""
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock) as mock_exec:
                mock_exec.return_value = SimpleNamespace(data=[{"id": "1"}, {"id": "2"}])
                count = await cleanup_old_health_checks()
                assert count == 2


# ============================================================================
# STORY-352 AC4: Uptime gauge tests
# ============================================================================


class TestUptimeGauge:
    """STORY-352 AC4: Tests for smartlic_uptime_pct_30d gauge."""

    @pytest.mark.asyncio
    async def test_gauge_updated_on_uptime_calculation(self):
        """AC4: UPTIME_PCT_30D gauge is updated after calculate_uptime_percentages."""
        mock_resp = SimpleNamespace(data=[
            {"overall_status": "healthy"},
            {"overall_status": "healthy"},
            {"overall_status": "degraded"},
        ])
        mock_gauge = MagicMock()
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock, return_value=mock_resp):
                with patch("metrics.UPTIME_PCT_30D", mock_gauge):
                    result = await calculate_uptime_percentages()

        # (100 + 100 + 50) / 3 = 83.3
        assert result["30d"] == 83.3
        mock_gauge.set.assert_called_with(83.3)

    @pytest.mark.asyncio
    async def test_gauge_set_to_100_when_all_healthy(self):
        """AC4: Gauge set to 100 when all checks are healthy."""
        mock_resp = SimpleNamespace(data=[
            {"overall_status": "healthy"},
            {"overall_status": "healthy"},
        ])
        mock_gauge = MagicMock()
        with patch("supabase_client.get_supabase") as mock_sb:
            mock_sb.return_value = MagicMock()
            with patch("supabase_client.sb_execute_direct", new_callable=AsyncMock, return_value=mock_resp):
                with patch("metrics.UPTIME_PCT_30D", mock_gauge):
                    result = await calculate_uptime_percentages()

        assert result["30d"] == 100.0
        mock_gauge.set.assert_called_with(100.0)
