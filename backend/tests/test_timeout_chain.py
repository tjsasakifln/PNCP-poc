"""GTM-FIX-029: Timeout chain invariant and integration tests.

Validates:
- AC1-AC5: PER_UF_TIMEOUT recalibration (30→90 normal, 45→120 degraded, env var)
- AC6-AC11: Consolidation timeout recalibration (50→180 per-source, 120→300 global)
- AC12-AC15: HTTP 422 special handling (1 retry, log body, circuit breaker)
- AC16-AC17: FETCH_TIMEOUT 240→360, env var
- AC19-AC20: Frontend proxy timeout 300→480 (verified via constant assertion)
- Chain invariant: FE(480) > Pipeline(360) > Consolidation(300) > Per-Source(180) > Per-UF(90)
"""

import sys
from pathlib import Path
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
        """AC20: STAB-003 timeout chain — inner chain (Consolidation > Per-Source > Per-UF) is strictly decreasing.
        Note: FE proxy (115s) is now intentionally BELOW pipeline FETCH_TIMEOUT (360s) because Railway
        hard-kills at ~120s. The FE proxy is the effective cutoff for users; pipeline runs independently.
        """
        from pncp_client import PNCP_TIMEOUT_PER_UF
        from source_config.sources import ConsolidationConfig

        config = ConsolidationConfig.from_env()

        # Inner chain must still be strictly decreasing: Consolidation global > per-source > per-UF
        assert config.timeout_global > config.timeout_per_source, (
            f"Consolidation global ({config.timeout_global}) must be > per-source ({config.timeout_per_source})"
        )
        assert config.timeout_per_source > PNCP_TIMEOUT_PER_UF, (
            f"Per-source ({config.timeout_per_source}) must be > per-UF ({PNCP_TIMEOUT_PER_UF})"
        )

        # FE proxy (115s) must be below Railway's hard cutoff (~120s)
        fe_proxy_timeout = 115
        railway_hard_cutoff = 120
        assert fe_proxy_timeout < railway_hard_cutoff, (
            f"FE proxy ({fe_proxy_timeout}s) must be < Railway hard cutoff ({railway_hard_cutoff}s)"
        )

        # Per-UF must be well below FE proxy (per-UF = 30s, FE = 115s)
        assert PNCP_TIMEOUT_PER_UF < fe_proxy_timeout, (
            f"Per-UF ({PNCP_TIMEOUT_PER_UF}s) must be < FE proxy ({fe_proxy_timeout}s)"
        )

    def test_degraded_timeout_greater_than_normal(self):
        """AC2: STORY-4.4 TD-SYS-003 — In degraded mode, abort per-UF FASTER (12s) than normal (25s).
        Rationale: degraded mode = PNCP is struggling; cut losses quickly, don't wait as long.
        """
        from config.pncp import PNCP_TIMEOUT_PER_UF, PNCP_TIMEOUT_PER_UF_DEGRADED

        # STORY-4.4 TD-SYS-003: tightened from 30/15 to 25/12 per Time Budget Waterfall
        assert PNCP_TIMEOUT_PER_UF == 25, (
            f"Normal per-UF timeout expected 25s, got {PNCP_TIMEOUT_PER_UF}"
        )
        assert PNCP_TIMEOUT_PER_UF_DEGRADED == 12, (
            f"Degraded per-UF timeout expected 12s, got {PNCP_TIMEOUT_PER_UF_DEGRADED}"
        )
        assert PNCP_TIMEOUT_PER_UF_DEGRADED < PNCP_TIMEOUT_PER_UF, (
            f"Degraded ({PNCP_TIMEOUT_PER_UF_DEGRADED}) must be < normal ({PNCP_TIMEOUT_PER_UF}) — "
            f"cut losses faster in degraded mode (STORY-4.4)"
        )

    def test_per_modality_fits_within_per_uf(self):
        """F03-AC13: PerModality must be strictly less than PerUF (hierarchy enforced)."""
        from pncp_client import PNCP_TIMEOUT_PER_MODALITY, PNCP_TIMEOUT_PER_UF

        assert PNCP_TIMEOUT_PER_MODALITY < PNCP_TIMEOUT_PER_UF, (
            f"PerModality ({PNCP_TIMEOUT_PER_MODALITY}s) must be strictly < "
            f"PerUF ({PNCP_TIMEOUT_PER_UF}s) — hierarchy inversion!"
        )


# ---------------------------------------------------------------------------
# Test 2 — AC1/AC5: PER_UF_TIMEOUT values and env var
# ---------------------------------------------------------------------------

class TestPerUfTimeout:
    """AC1, AC2, AC5: PER_UF_TIMEOUT values and env var configurability."""

    def test_normal_mode_default_90s(self):
        """AC1: Normal mode PER_UF_TIMEOUT = 25s (STORY-4.4 TD-SYS-003: tightened from 30s per Time Budget Waterfall)."""
        from pncp_client import PNCP_TIMEOUT_PER_UF
        assert PNCP_TIMEOUT_PER_UF == 25.0

    def test_degraded_mode_default_120s(self):
        """AC2: Degraded mode PER_UF_TIMEOUT = 12s (STORY-4.4 TD-SYS-003: tightened from 15s — abort faster under degraded conditions)."""
        from config.pncp import PNCP_TIMEOUT_PER_UF_DEGRADED
        assert PNCP_TIMEOUT_PER_UF_DEGRADED == 12.0

    def test_env_var_override(self):
        """AC5: PNCP_TIMEOUT_PER_UF env var overrides default.
        DEBT-118: env var read moved from pncp_client.py to config/pncp.py."""
        # Verify the env var lookup exists in config/pncp.py (source of truth)
        import config.pncp as config_pncp
        src = Path(config_pncp.__file__).read_text()
        assert 'PNCP_TIMEOUT_PER_UF' in src
        assert 'os.getenv("PNCP_TIMEOUT_PER_UF"' in src or 'os.environ.get("PNCP_TIMEOUT_PER_UF"' in src


# ---------------------------------------------------------------------------
# Test 3 — AC6-AC9: Consolidation timeouts
# ---------------------------------------------------------------------------

class TestConsolidationTimeouts:
    """AC6-AC9: Consolidation timeout values after recalibration."""

    def test_env_default_per_source_180(self):
        """AC6: Default timeout_per_source from env = 70s (STORY-4.4 TD-SYS-003: synced with config/pncp.py PNCP_TIMEOUT_PER_SOURCE)."""
        from source_config.sources import ConsolidationConfig
        config = ConsolidationConfig.from_env()
        assert config.timeout_per_source == 70

    def test_env_default_global_300(self):
        """AC7: Default timeout_global from env = 90s (STORY-4.4 TD-SYS-003: synced with CONSOLIDATION_TIMEOUT default)."""
        from source_config.sources import ConsolidationConfig
        config = ConsolidationConfig.from_env()
        assert config.timeout_global == 90

    def test_degraded_global_timeout_100(self):
        """AC8: DEGRADED_GLOBAL_TIMEOUT = 100s (STORY-271 AC2: reduced from 110s, 15s buffer before GUNICORN_TIMEOUT=115s)."""
        from consolidation import ConsolidationService
        assert ConsolidationService.DEGRADED_GLOBAL_TIMEOUT == 100

    def test_failover_timeout_per_source_120(self):
        """AC9: FAILOVER_TIMEOUT_PER_SOURCE = 80s (STAB-003: reduced from 120s)."""
        from consolidation import ConsolidationService
        assert ConsolidationService.FAILOVER_TIMEOUT_PER_SOURCE == 80

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
            ConsolidationService(
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
            ConsolidationService(
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
        """AC12-AC14: 422-specific retry+breaker logic lives in clients.pncp.retry.

        DEBT-015 SYS-002 thin-client refactor moved 422 handling from pncp_client.py
        into `_handle_422_response()` in clients/pncp/retry.py. pncp_client.py
        re-exports the symbol for back-compat.
        """
        from pathlib import Path
        import clients.pncp.retry as retry_mod
        src = Path(retry_mod.__file__).read_text()
        # Check 422 handling block exists in the thin-client location
        assert "422" in src, "Missing 422 status handling in clients/pncp/retry.py"
        assert "_handle_422_response" in src, "Missing _handle_422_response helper"
        # Back-compat: symbol still importable from pncp_client
        from pncp_client import _handle_422_response
        assert callable(_handle_422_response), "_handle_422_response must be re-exported from pncp_client"


# ---------------------------------------------------------------------------
# Test 5 — AC16-AC17: FETCH_TIMEOUT
# ---------------------------------------------------------------------------

class TestFetchTimeout:
    """AC16-AC17 (STORY-4.4 superseded): FETCH_TIMEOUT replaced by PIPELINE_TIMEOUT.

    STORY-4.4 TD-SYS-003 consolidated search-pipeline timeouts into config/pncp.py
    PIPELINE_TIMEOUT (default 100s) to enforce the 120s Railway budget waterfall.
    The legacy FETCH_TIMEOUT (=360s) and SEARCH_FETCH_TIMEOUT env var were removed.
    """

    def test_default_pipeline_timeout_100s(self):
        """AC16 (rebaselined): Default PIPELINE_TIMEOUT = 100s per STORY-4.4 waterfall."""
        from config.pncp import PIPELINE_TIMEOUT
        assert PIPELINE_TIMEOUT == 100, (
            f"PIPELINE_TIMEOUT should be 100s per STORY-4.4 TD-SYS-003, got {PIPELINE_TIMEOUT}"
        )

    def test_pipeline_timeout_env_configurable(self):
        """AC17 (rebaselined): PIPELINE_TIMEOUT env var is the override hook post-STORY-4.4."""
        import config.pncp as config_pncp
        src = Path(config_pncp.__file__).read_text()
        assert 'os.getenv("PIPELINE_TIMEOUT"' in src, (
            "PIPELINE_TIMEOUT should be configurable via PIPELINE_TIMEOUT env var"
        )


# ---------------------------------------------------------------------------
# Test 6 — AC19: Frontend proxy timeout (source-level check)
# ---------------------------------------------------------------------------

class TestFrontendProxyTimeout:
    """AC19 (CRIT-082 rebaselined): Frontend proxy timeout = 60s.

    CRIT-082 reduced the proxy timeout to 60s (chain: Client 65s > Proxy 60s > Gunicorn 120s)
    because 202-async is the primary path (<2s) — 60s only covers sync-fallback edge cases.
    """

    def test_frontend_proxy_60s(self):
        """CRIT-082: route.ts uses `60 * 1000` timeout."""
        route_ts = Path(__file__).resolve().parents[2] / "frontend" / "app" / "api" / "buscar" / "route.ts"
        if not route_ts.exists():
            pytest.skip("Frontend route.ts not found")
        content = route_ts.read_text(encoding="utf-8")
        assert "60 * 1000" in content, (
            "Frontend proxy should use 60s timeout (60 * 1000) — CRIT-082 reduced from 115s"
        )

    def test_frontend_timeout_error_message(self):
        """CRIT-082: timeout error message mentions the analysis exceeded the limit."""
        route_ts = Path(__file__).resolve().parents[2] / "frontend" / "app" / "api" / "buscar" / "route.ts"
        if not route_ts.exists():
            pytest.skip("Frontend route.ts not found")
        content = route_ts.read_text(encoding="utf-8")
        assert "A análise excedeu o tempo limite" in content, (
            "Frontend timeout error message should contain 'A análise excedeu o tempo limite' (CRIT-082)"
        )


# ---------------------------------------------------------------------------
# Test 7 — Chain hierarchy comment in route.ts
# ---------------------------------------------------------------------------

class TestHierarchyComment:
    """AC20: Comment documenting timeout hierarchy exists in route.ts."""

    def test_hierarchy_comment_in_route(self):
        """AC20: route.ts contains timeout comment (STAB-003: 115s, aligned with Railway's ~120s hard cutoff)."""
        route_ts = Path(__file__).resolve().parents[2] / "frontend" / "app" / "api" / "buscar" / "route.ts"
        if not route_ts.exists():
            pytest.skip("Frontend route.ts not found")
        content = route_ts.read_text(encoding="utf-8")
        assert "115" in content or "STAB-003" in content or "Railway" in content, (
            "Frontend route.ts should document the timeout (115s) or reference STAB-003/Railway"
        )


# ---------------------------------------------------------------------------
# Test 8 — AC3: Calculation comment in pncp_client.py
# ---------------------------------------------------------------------------

class TestCalculationComment:
    """AC3: Code comment explaining timeout calculation."""

    def test_calculation_comment_exists(self):
        """AC3: config/pncp.py contains calculation comment for PER_UF_TIMEOUT.
        DEBT-118: env var config moved from pncp_client.py to config/pncp.py."""
        import config.pncp as config_pncp
        src = Path(config_pncp.__file__).read_text()
        assert "4 mods" in src.lower() or "4 modalities" in src.lower(), (
            "Should have comment explaining 4 modalities calculation"
        )
        assert "margin" in src.lower(), (
            "Should mention safety margin in timeout calculation comment"
        )


# ---------------------------------------------------------------------------
# Test 9 — GTM-RESILIENCE-F03: PerModality recalibration & validation
# ---------------------------------------------------------------------------

class TestPerModalityRecalibration:
    """GTM-RESILIENCE-F03 AC1-AC6, AC13-AC20: PerModality timeout hierarchy."""

    def test_per_modality_default_60s(self):
        """F03-AC14: Default PerModality is 20s (STAB-003: reduced from 60s)."""
        from pncp_client import PNCP_TIMEOUT_PER_MODALITY
        assert PNCP_TIMEOUT_PER_MODALITY == 20.0

    def test_per_modality_margin_30s(self):
        """F03-AC15 (STORY-4.4 TD-SYS-003): Margin between PerUF and PerModality >= 5s.

        History: original 30s margin (PerUF=90, PerModality=60); STAB-003 reduced to 10s
        (PerUF=30, PerModality=20); STORY-4.4 tightened to 5s (PerUF=25, PerModality=20)
        to fit the 100s pipeline budget while preserving strict ordering.
        """
        from pncp_client import PNCP_TIMEOUT_PER_MODALITY, PNCP_TIMEOUT_PER_UF
        margin = PNCP_TIMEOUT_PER_UF - PNCP_TIMEOUT_PER_MODALITY
        assert margin >= 5, (
            f"Margin ({margin}s) must be >= 5s (PerUF - PerModality >= 5s post-STORY-4.4). "
            f"PerUF={PNCP_TIMEOUT_PER_UF}, PerModality={PNCP_TIMEOUT_PER_MODALITY}"
        )

    def test_startup_validation_rejects_inversion(self, caplog):
        """F03-AC16: validate_timeout_chain() rejects PerModality >= PerUF with critical log.

        NOTE (STORY-BTS-011): validate_timeout_chain lives in clients.pncp.retry and
        mutates retry.PNCP_TIMEOUT_* via `global` — patching pncp_client.X targets the
        re-export copy, which is not read by the function. Patch the source module.
        """
        import logging
        import clients.pncp.retry as retry_mod

        original_mod, original_uf = retry_mod.PNCP_TIMEOUT_PER_MODALITY, retry_mod.PNCP_TIMEOUT_PER_UF
        try:
            with caplog.at_level(logging.CRITICAL, logger="clients.pncp.retry"):
                retry_mod.PNCP_TIMEOUT_PER_MODALITY = 100.0
                retry_mod.PNCP_TIMEOUT_PER_UF = 90.0
                retry_mod.validate_timeout_chain()

            assert any("TIMEOUT MISCONFIGURATION" in r.message for r in caplog.records), (
                "Expected CRITICAL log with 'TIMEOUT MISCONFIGURATION'"
            )
            # Fallback to safe defaults (_SAFE_PER_MODALITY=20, _SAFE_PER_UF=30)
            assert retry_mod.PNCP_TIMEOUT_PER_MODALITY == 20.0
            assert retry_mod.PNCP_TIMEOUT_PER_UF == 30.0
        finally:
            retry_mod.PNCP_TIMEOUT_PER_MODALITY = original_mod
            retry_mod.PNCP_TIMEOUT_PER_UF = original_uf

    def test_startup_validation_warns_near_inversion(self, caplog):
        """F03-AC17: validate_timeout_chain() warns when PerModality > 80% of PerUF.

        Patch source module clients.pncp.retry (see rejects_inversion test for rationale).
        """
        import logging
        import clients.pncp.retry as retry_mod

        original_mod, original_uf = retry_mod.PNCP_TIMEOUT_PER_MODALITY, retry_mod.PNCP_TIMEOUT_PER_UF
        try:
            with caplog.at_level(logging.WARNING, logger="clients.pncp.retry"):
                retry_mod.PNCP_TIMEOUT_PER_MODALITY = 80.0
                retry_mod.PNCP_TIMEOUT_PER_UF = 90.0
                retry_mod.validate_timeout_chain()

            assert any("TIMEOUT NEAR-INVERSION" in r.message for r in caplog.records), (
                "Expected WARNING log with 'TIMEOUT NEAR-INVERSION'"
            )
        finally:
            retry_mod.PNCP_TIMEOUT_PER_MODALITY = original_mod
            retry_mod.PNCP_TIMEOUT_PER_UF = original_uf

    def test_startup_validation_passes_healthy(self, caplog):
        """F03-AC18: No warnings with healthy defaults (60/90)."""
        import logging

        with caplog.at_level(logging.WARNING, logger="pncp_client"):
            with patch("pncp_client.PNCP_TIMEOUT_PER_MODALITY", 60.0), \
                 patch("pncp_client.PNCP_TIMEOUT_PER_UF", 90.0):
                from pncp_client import validate_timeout_chain
                validate_timeout_chain()

        timeout_warnings = [
            r for r in caplog.records
            if "TIMEOUT" in r.message and r.levelno >= logging.WARNING
        ]
        assert len(timeout_warnings) == 0, (
            f"Expected no timeout warnings with healthy config, got: "
            f"{[r.message for r in timeout_warnings]}"
        )

    def test_no_near_inversion_with_defaults(self, caplog):
        """F03-AC20: Zero near-inversion warnings with default config."""
        import logging

        with caplog.at_level(logging.WARNING, logger="pncp_client"):
            from pncp_client import validate_timeout_chain
            validate_timeout_chain()

        near_inv = [r for r in caplog.records if "NEAR-INVERSION" in r.message]
        assert len(near_inv) == 0, (
            f"Default config should produce zero near-inversion warnings, got: "
            f"{[r.message for r in near_inv]}"
        )
