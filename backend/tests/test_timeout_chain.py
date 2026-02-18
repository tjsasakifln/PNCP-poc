"""GTM-FIX-029: Timeout chain invariant and integration tests.

Validates:
- AC1-AC5: PER_UF_TIMEOUT recalibration (30→90 normal, 45→120 degraded, env var)
- AC6-AC11: Consolidation timeout recalibration (50→180 per-source, 120→300 global)
- AC12-AC15: HTTP 422 special handling (1 retry, log body, circuit breaker)
- AC16-AC17: FETCH_TIMEOUT 240→360, env var
- AC19-AC20: Frontend proxy timeout 300→480 (verified via constant assertion)
- Chain invariant: FE(480) > Pipeline(360) > Consolidation(300) > Per-Source(180) > Per-UF(90)
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Pre-mock heavy third-party modules before importing pipeline
for _mod_name in ("openai",):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = MagicMock()


# ---------------------------------------------------------------------------
# Test 1 — Timeout Chain Invariant (AC20)
# ---------------------------------------------------------------------------

class TestTimeoutChainInvariant:
    """Verify the strict ordering: FE > Pipeline > Consolidation > Per-Source > Per-UF."""

    def test_chain_ordering_defaults(self):
        """AC20: Default timeout chain must be strictly decreasing."""
        from pncp_client import PNCP_TIMEOUT_PER_UF, PNCP_TIMEOUT_PER_UF_DEGRADED
        from source_config.sources import ConsolidationConfig

        config = ConsolidationConfig.from_env()

        # Pipeline FETCH_TIMEOUT (default 360)
        fetch_timeout = int(os.environ.get("SEARCH_FETCH_TIMEOUT", "360"))

        # Frontend proxy timeout (hardcoded 480 in route.ts — assert as constant here)
        fe_proxy_timeout = 480

        assert fe_proxy_timeout > fetch_timeout, (
            f"FE proxy ({fe_proxy_timeout}) must be > Pipeline FETCH_TIMEOUT ({fetch_timeout})"
        )
        assert fetch_timeout > config.timeout_global, (
            f"Pipeline ({fetch_timeout}) must be > Consolidation global ({config.timeout_global})"
        )
        assert config.timeout_global > config.timeout_per_source, (
            f"Consolidation global ({config.timeout_global}) must be > per-source ({config.timeout_per_source})"
        )
        assert config.timeout_per_source > PNCP_TIMEOUT_PER_UF, (
            f"Per-source ({config.timeout_per_source}) must be > per-UF ({PNCP_TIMEOUT_PER_UF})"
        )

    def test_degraded_timeout_greater_than_normal(self):
        """AC2: Degraded per-UF timeout must be >= normal per-UF timeout."""
        from pncp_client import PNCP_TIMEOUT_PER_UF, PNCP_TIMEOUT_PER_UF_DEGRADED

        assert PNCP_TIMEOUT_PER_UF_DEGRADED >= PNCP_TIMEOUT_PER_UF, (
            f"Degraded ({PNCP_TIMEOUT_PER_UF_DEGRADED}) must be >= normal ({PNCP_TIMEOUT_PER_UF})"
        )

    def test_per_modality_fits_within_per_uf(self):
        """AC4: Per-modality timeout (120s) should not exceed per-UF (90s) by too much.

        Note: Per-modality > Per-UF is intentional (4 mods run in parallel within 1 UF).
        But the UF timeout should give at least 1 modality a fair chance to complete.
        """
        from pncp_client import PNCP_TIMEOUT_PER_MODALITY, PNCP_TIMEOUT_PER_UF

        # Per-UF should be at least 50% of per-modality to allow completion
        assert PNCP_TIMEOUT_PER_UF >= PNCP_TIMEOUT_PER_MODALITY * 0.5, (
            f"Per-UF ({PNCP_TIMEOUT_PER_UF}) should be >= 50% of per-modality "
            f"({PNCP_TIMEOUT_PER_MODALITY}) to allow at least 1 modality to complete"
        )


# ---------------------------------------------------------------------------
# Test 2 — AC1/AC5: PER_UF_TIMEOUT values and env var
# ---------------------------------------------------------------------------

class TestPerUfTimeout:
    """AC1, AC2, AC5: PER_UF_TIMEOUT values and env var configurability."""

    def test_normal_mode_default_90s(self):
        """AC1: Normal mode PER_UF_TIMEOUT = 90s."""
        from pncp_client import PNCP_TIMEOUT_PER_UF
        assert PNCP_TIMEOUT_PER_UF == 90.0

    def test_degraded_mode_default_120s(self):
        """AC2: Degraded mode PER_UF_TIMEOUT = 120s."""
        from pncp_client import PNCP_TIMEOUT_PER_UF_DEGRADED
        assert PNCP_TIMEOUT_PER_UF_DEGRADED == 120.0

    def test_env_var_override(self):
        """AC5: PNCP_TIMEOUT_PER_UF env var overrides default."""
        # This test verifies the env var lookup pattern exists in source
        import pncp_client
        src = Path(pncp_client.__file__).read_text()
        assert 'PNCP_TIMEOUT_PER_UF' in src
        assert 'os.environ.get("PNCP_TIMEOUT_PER_UF"' in src


# ---------------------------------------------------------------------------
# Test 3 — AC6-AC9: Consolidation timeouts
# ---------------------------------------------------------------------------

class TestConsolidationTimeouts:
    """AC6-AC9: Consolidation timeout values after recalibration."""

    def test_env_default_per_source_180(self):
        """AC6: Default timeout_per_source from env = 180s."""
        from source_config.sources import ConsolidationConfig
        config = ConsolidationConfig.from_env()
        assert config.timeout_per_source == 180

    def test_env_default_global_300(self):
        """AC7: Default timeout_global from env = 300s."""
        from source_config.sources import ConsolidationConfig
        config = ConsolidationConfig.from_env()
        assert config.timeout_global == 300

    def test_degraded_global_timeout_360(self):
        """AC8: DEGRADED_GLOBAL_TIMEOUT = 360s."""
        from consolidation import ConsolidationService
        assert ConsolidationService.DEGRADED_GLOBAL_TIMEOUT == 360

    def test_failover_timeout_per_source_120(self):
        """AC9: FAILOVER_TIMEOUT_PER_SOURCE = 120s."""
        from consolidation import ConsolidationService
        assert ConsolidationService.FAILOVER_TIMEOUT_PER_SOURCE == 120

    def test_near_inversion_warning(self, caplog):
        """AC10: Log warning when timeout_per_source > 80% of timeout_global."""
        from consolidation import ConsolidationService

        # Create a mock adapter that passes contract validation
        mock_adapter = MagicMock()
        mock_adapter.code = "test"
        mock_adapter.metadata = {}
        mock_adapter.fetch = AsyncMock()
        mock_adapter.health_check = AsyncMock()
        mock_adapter.close = AsyncMock()

        import logging
        with caplog.at_level(logging.WARNING, logger="consolidation"):
            # per_source=90 is > 80% of global=100
            svc = ConsolidationService(
                adapters={"test": mock_adapter},
                timeout_per_source=90,
                timeout_global=100,
            )

        assert any("near-inversion" in r.message.lower() for r in caplog.records), (
            "Expected near-inversion warning when per_source > 80% of global"
        )

    def test_no_warning_when_healthy_ratio(self, caplog):
        """AC10 negative: No warning when ratio is healthy."""
        from consolidation import ConsolidationService

        mock_adapter = MagicMock()
        mock_adapter.code = "test"
        mock_adapter.metadata = {}
        mock_adapter.fetch = AsyncMock()
        mock_adapter.health_check = AsyncMock()
        mock_adapter.close = AsyncMock()

        import logging
        with caplog.at_level(logging.WARNING, logger="consolidation"):
            svc = ConsolidationService(
                adapters={"test": mock_adapter},
                timeout_per_source=50,
                timeout_global=300,
            )

        assert not any("near-inversion" in r.message.lower() for r in caplog.records), (
            "Should NOT warn when per_source is well below 80% of global"
        )


# ---------------------------------------------------------------------------
# Test 4 — AC12-AC15: HTTP 422 handling
# ---------------------------------------------------------------------------

class TestHttp422Handling:
    """AC12-AC15: 422 in retryable_status_codes and special handling."""

    def test_422_in_retryable_codes(self):
        """AC12: 422 is in retryable_status_codes."""
        from config import RetryConfig
        config = RetryConfig()
        assert 422 in config.retryable_status_codes

    def test_422_retry_logic_in_source(self):
        """AC12-AC14: pncp_client.py contains 422-specific retry+breaker logic."""
        import pncp_client
        src = Path(pncp_client.__file__).read_text()
        # Check 422 handling block exists
        assert "response.status_code == 422" in src, "Missing 422 status check"
        assert "record_failure" in src, "Missing circuit breaker failure recording for 422"
        assert "pncp_422_count" in src, "Missing 422 metric logging"


# ---------------------------------------------------------------------------
# Test 5 — AC16-AC17: FETCH_TIMEOUT
# ---------------------------------------------------------------------------

class TestFetchTimeout:
    """AC16-AC17: FETCH_TIMEOUT raised and configurable."""

    def test_default_fetch_timeout_360(self):
        """AC16: Default FETCH_TIMEOUT = 360s (6 minutes)."""
        import search_pipeline
        src = Path(search_pipeline.__file__).read_text()
        # The default in the env fallback should be 360 (6 * 60)
        assert "6 * 60" in src or '"360"' in src, (
            "FETCH_TIMEOUT default should be 6 minutes (360s)"
        )

    def test_env_var_configurable(self):
        """AC17: SEARCH_FETCH_TIMEOUT env var exists in source."""
        import search_pipeline
        src = Path(search_pipeline.__file__).read_text()
        assert "SEARCH_FETCH_TIMEOUT" in src, (
            "FETCH_TIMEOUT should be configurable via SEARCH_FETCH_TIMEOUT env var"
        )


# ---------------------------------------------------------------------------
# Test 6 — AC19: Frontend proxy timeout (source-level check)
# ---------------------------------------------------------------------------

class TestFrontendProxyTimeout:
    """AC19: Frontend proxy timeout = 480s (8 minutes)."""

    def test_frontend_proxy_8min(self):
        """AC19: route.ts uses 8 * 60 * 1000 timeout."""
        route_ts = Path(__file__).resolve().parents[2] / "frontend" / "app" / "api" / "buscar" / "route.ts"
        if not route_ts.exists():
            pytest.skip("Frontend route.ts not found")
        content = route_ts.read_text(encoding="utf-8")
        assert "8 * 60 * 1000" in content, (
            "Frontend proxy should use 8-minute timeout (8 * 60 * 1000)"
        )

    def test_frontend_error_message_8min(self):
        """AC19: Error message references 8 min."""
        route_ts = Path(__file__).resolve().parents[2] / "frontend" / "app" / "api" / "buscar" / "route.ts"
        if not route_ts.exists():
            pytest.skip("Frontend route.ts not found")
        content = route_ts.read_text(encoding="utf-8")
        assert "8 min" in content, (
            "Frontend timeout error message should reference 8 minutes"
        )


# ---------------------------------------------------------------------------
# Test 7 — Chain hierarchy comment in route.ts
# ---------------------------------------------------------------------------

class TestHierarchyComment:
    """AC20: Comment documenting timeout hierarchy exists in route.ts."""

    def test_hierarchy_comment_in_route(self):
        """AC20: route.ts contains timeout hierarchy comment."""
        route_ts = Path(__file__).resolve().parents[2] / "frontend" / "app" / "api" / "buscar" / "route.ts"
        if not route_ts.exists():
            pytest.skip("Frontend route.ts not found")
        content = route_ts.read_text(encoding="utf-8")
        assert "480" in content or "FE proxy" in content, (
            "Frontend route.ts should document the timeout hierarchy"
        )


# ---------------------------------------------------------------------------
# Test 8 — AC3: Calculation comment in pncp_client.py
# ---------------------------------------------------------------------------

class TestCalculationComment:
    """AC3: Code comment explaining timeout calculation."""

    def test_calculation_comment_exists(self):
        """AC3: pncp_client.py contains calculation comment for PER_UF_TIMEOUT."""
        import pncp_client
        src = Path(pncp_client.__file__).read_text()
        assert "4 mods" in src.lower() or "4 modalities" in src.lower(), (
            "Should have comment explaining 4 modalities calculation"
        )
        assert "margin" in src.lower(), (
            "Should mention safety margin in timeout calculation comment"
        )
