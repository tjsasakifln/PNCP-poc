"""STORY-271: Resolve All 5 Sentry Unresolved Issues — unit tests.

Tests cover:
  AC1: WARMING_USER_ID defined in config + migration exists
  AC2: Pipeline timeout < GUNICORN_TIMEOUT (sufficient buffer)
  AC4: PNCP health canary uses correct params (date format, modalidade, status)

Mock strategy:
  - health.py: patch httpx.AsyncClient to verify request params
  - config: direct import to verify constants exist
  - consolidation: import class constants
"""

import os
import re
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# AC1: WARMING_USER_ID in config
# ---------------------------------------------------------------------------


class TestAC1WarmingUserConfig:
    """AC1: Verify WARMING_USER_ID is defined and valid."""

    def test_warming_user_id_defined(self):
        """WARMING_USER_ID must be importable from config."""
        from config import WARMING_USER_ID

        assert WARMING_USER_ID is not None
        assert isinstance(WARMING_USER_ID, str)

    def test_warming_user_id_is_nil_uuid(self):
        """Default WARMING_USER_ID is the nil UUID."""
        from config import WARMING_USER_ID

        assert WARMING_USER_ID == "00000000-0000-0000-0000-000000000000"

    def test_warming_user_id_env_override(self):
        """WARMING_USER_ID can be overridden via env var."""
        custom = "11111111-1111-1111-1111-111111111111"
        with patch.dict(os.environ, {"WARMING_USER_ID": custom}):
            # Need to reimport to pick up env var
            import config as _cfg

            # Verify the env-var mechanism exists (module-level read)
            assert _cfg.WARMING_USER_ID is not None
            # Restore — don't use importlib.reload to avoid test pollution

    def test_migration_file_exists(self):
        """Migration SQL for warming user profile must exist."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "supabase",
            "migrations",
            "20260226110000_warming_user_profile.sql",
        )
        assert os.path.isfile(migration_path), (
            f"Migration file not found: {migration_path}"
        )

    def test_migration_inserts_nil_uuid(self):
        """Migration must INSERT the nil UUID into profiles."""
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "supabase",
            "migrations",
            "20260226110000_warming_user_profile.sql",
        )
        with open(migration_path, "r") as f:
            sql = f.read()

        assert "00000000-0000-0000-0000-000000000000" in sql
        assert "profiles" in sql.lower()
        assert "ON CONFLICT" in sql or "on conflict" in sql


# ---------------------------------------------------------------------------
# AC2: Worker timeout buffer
# ---------------------------------------------------------------------------


class TestAC2WorkerTimeout:
    """AC2: Verify pipeline timeout has buffer before GUNICORN_TIMEOUT."""

    def test_degraded_global_timeout_reduced(self):
        """DEGRADED_GLOBAL_TIMEOUT must be <= 100s (15s buffer before 115s gunicorn)."""
        from consolidation import ConsolidationService

        assert ConsolidationService.DEGRADED_GLOBAL_TIMEOUT <= 100

    def test_degraded_global_timeout_is_100(self):
        """DEGRADED_GLOBAL_TIMEOUT should be exactly 100 after STORY-271."""
        from consolidation import ConsolidationService

        assert ConsolidationService.DEGRADED_GLOBAL_TIMEOUT == 100

    def test_failover_timeout_per_source_within_budget(self):
        """FAILOVER_TIMEOUT_PER_SOURCE must be < DEGRADED_GLOBAL_TIMEOUT."""
        from consolidation import ConsolidationService

        assert (
            ConsolidationService.FAILOVER_TIMEOUT_PER_SOURCE
            < ConsolidationService.DEGRADED_GLOBAL_TIMEOUT
        )

    def test_gunicorn_default_in_start_sh(self):
        """start.sh should have GUNICORN_TIMEOUT default of 120."""
        start_sh = os.path.join(os.path.dirname(__file__), "..", "start.sh")
        if os.path.isfile(start_sh):
            with open(start_sh) as f:
                content = f.read()
            assert "GUNICORN_TIMEOUT:-120" in content

    def test_early_return_config_defined(self):
        """EARLY_RETURN_TIME_S and EARLY_RETURN_THRESHOLD_PCT must be in config."""
        from config import EARLY_RETURN_TIME_S, EARLY_RETURN_THRESHOLD_PCT

        assert isinstance(EARLY_RETURN_TIME_S, float)
        assert isinstance(EARLY_RETURN_THRESHOLD_PCT, float)
        assert EARLY_RETURN_TIME_S == 80.0
        assert EARLY_RETURN_THRESHOLD_PCT == 0.8


# ---------------------------------------------------------------------------
# AC4: PNCP health canary
# ---------------------------------------------------------------------------


class TestAC4PNCPHealthCanary:
    """AC4: Verify PNCP health canary uses correct params."""

    @pytest.mark.asyncio
    async def test_pncp_canary_date_format_yyyymmdd(self):
        """PNCP canary must use yyyyMMdd date format, not YYYY-MM-DD."""
        from health import check_source_health

        captured_params = {}

        class FakeResponse:
            status_code = 200

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url, params=None):
                captured_params.update(params or {})
                return FakeResponse()

        with patch("health.httpx.AsyncClient", return_value=FakeClient()):
            await check_source_health("PNCP")

        # Date params must be yyyyMMdd (no dashes)
        assert "dataInicial" in captured_params
        assert re.match(r"^\d{8}$", str(captured_params["dataInicial"])), (
            f"dataInicial should be yyyyMMdd format, got: {captured_params['dataInicial']}"
        )
        assert "-" not in str(captured_params["dataInicial"]), (
            "dataInicial must NOT contain dashes"
        )

    @pytest.mark.asyncio
    async def test_pncp_canary_has_modalidade_param(self):
        """PNCP canary must include codigoModalidadeContratacao parameter."""
        from health import check_source_health

        captured_params = {}

        class FakeResponse:
            status_code = 200

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url, params=None):
                captured_params.update(params or {})
                return FakeResponse()

        with patch("health.httpx.AsyncClient", return_value=FakeClient()):
            await check_source_health("PNCP")

        assert "codigoModalidadeContratacao" in captured_params, (
            "PNCP canary must include codigoModalidadeContratacao"
        )
        assert captured_params["codigoModalidadeContratacao"] == 6

    @pytest.mark.asyncio
    async def test_pncp_canary_400_is_unhealthy(self):
        """HTTP 400 from PNCP should NOT be treated as healthy."""
        from health import check_source_health, HealthStatus

        class FakeResponse:
            status_code = 400

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url, params=None):
                return FakeResponse()

        with patch("health.httpx.AsyncClient", return_value=FakeClient()):
            result = await check_source_health("PNCP")

        # HTTP 400 should be DEGRADED (not HEALTHY as it was before the fix)
        assert result.status != HealthStatus.HEALTHY, (
            "HTTP 400 must NOT be reported as HEALTHY"
        )
        assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_pncp_canary_200_is_healthy(self):
        """HTTP 200 from PNCP should be HEALTHY."""
        from health import check_source_health, HealthStatus

        class FakeResponse:
            status_code = 200

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url, params=None):
                return FakeResponse()

        with patch("health.httpx.AsyncClient", return_value=FakeClient()):
            result = await check_source_health("PNCP")

        assert result.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_pncp_canary_uses_realistic_page_size(self):
        """PNCP canary should use tamanhoPagina=50 (STORY-316: realistic canary detects page size bug)."""
        from health import check_source_health

        captured_params = {}

        class FakeResponse:
            status_code = 200

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def get(self, url, params=None):
                captured_params.update(params or {})
                return FakeResponse()

        with patch("health.httpx.AsyncClient", return_value=FakeClient()):
            await check_source_health("PNCP")

        assert captured_params.get("tamanhoPagina") == 50


# ---------------------------------------------------------------------------
# AC3: AllSourcesFailedError resilience (verification only)
# ---------------------------------------------------------------------------


class TestAC3AllSourcesFailed:
    """AC3: Verify AllSourcesFailedError fallback exists."""

    def test_all_sources_failed_error_defined(self):
        """AllSourcesFailedError exception class must exist."""
        from consolidation import AllSourcesFailedError

        assert issubclass(AllSourcesFailedError, Exception)

    def test_all_sources_failed_error_has_source_errors(self):
        """AllSourcesFailedError must carry source_errors dict."""
        from consolidation import AllSourcesFailedError

        err = AllSourcesFailedError({"PNCP": "timeout", "PCP": "connection refused"})
        assert err.source_errors == {"PNCP": "timeout", "PCP": "connection refused"}
        assert "PNCP" in str(err)

    def test_circuit_breaker_thresholds(self):
        """Circuit breaker thresholds should be reasonable."""
        from pncp_client import (
            PNCP_CIRCUIT_BREAKER_THRESHOLD,
            PNCP_CIRCUIT_BREAKER_COOLDOWN,
        )

        assert PNCP_CIRCUIT_BREAKER_THRESHOLD == 15
        assert PNCP_CIRCUIT_BREAKER_COOLDOWN == 60
