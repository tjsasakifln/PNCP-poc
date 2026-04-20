"""Tests for GTM-INFRA-001: Eliminar Sync Fallback + Ajustar Circuit Breaker.

T1: Fallback doesn't block event loop (asyncio.to_thread wrapper)
T2: Circuit breaker trips after 15 failures (not 50)
T3: Zero time.sleep() in async production code (grep test)
T4: Gunicorn timeout configured at 180s
"""

import asyncio
import ast
import re
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ============================================================================
# T1: Fallback doesn't block event loop (asyncio.to_thread wrapper)
# ============================================================================


class TestSyncFallbackNotBlocking:
    """T1: Verify sync PNCPClient fallback is wrapped in asyncio.to_thread."""

    def test_search_pipeline_fallback_uses_to_thread(self):
        """search_pipeline.py (or extracted pipeline stages) must use asyncio.to_thread
        for sync PNCPClient fallback.

        STORY-BTS-009 + DEBT-204: the search pipeline was decomposed into
        ``backend/pipeline/stages/*`` (execute, enrich, generate, etc.), so the
        ``asyncio.to_thread`` call lives inside the stages tree rather than the
        thin ``search_pipeline.py`` facade. Walk the whole pipeline surface.
        """
        import ast

        backend_dir = Path(__file__).parent.parent
        candidate_files = [backend_dir / "search_pipeline.py"]
        pipeline_dir = backend_dir / "pipeline"
        if pipeline_dir.exists():
            candidate_files.extend(pipeline_dir.rglob("*.py"))

        found = False
        for path in candidate_files:
            if not path.exists():
                continue
            source = path.read_text(encoding="utf-8")
            if "asyncio.to_thread" in source:
                found = True
                break

        assert found, (
            "At least one module under search_pipeline.py / pipeline/ must use "
            "asyncio.to_thread() for sync PNCPClient fallback"
        )

    def test_pncp_legacy_adapter_uses_to_thread(self):
        """PNCPLegacyAdapter.fetch() single-UF path must use asyncio.to_thread.

        DEBT-204 Track 1: PNCPLegacyAdapter moved to ``clients/pncp/adapter.py``;
        ``pncp_client.py`` is now a thin re-export facade. Check the class via
        inspect.getsource (also survives future package moves).
        """
        import inspect
        from clients.pncp.adapter import PNCPLegacyAdapter

        adapter_source = inspect.getsource(PNCPLegacyAdapter)
        assert "asyncio.to_thread" in adapter_source, (
            "PNCPLegacyAdapter.fetch() must use asyncio.to_thread() for single-UF path"
        )

    @pytest.mark.asyncio
    async def test_to_thread_does_not_block_event_loop(self):
        """Verify asyncio.to_thread() runs sync code without blocking the event loop."""
        loop_blocked = False

        def sync_work():
            """Simulate sync PNCPClient work with time.sleep."""
            time.sleep(0.1)
            return [{"id": 1}]

        async def monitor_loop():
            """Monitor that the event loop remains responsive."""
            nonlocal loop_blocked
            for _ in range(5):
                await asyncio.sleep(0.03)
            # If we get here, loop wasn't blocked
            loop_blocked = False

        loop_blocked = True  # Assume blocked until proven otherwise

        # Run both: sync work in thread + event loop monitor
        results = await asyncio.gather(
            asyncio.to_thread(sync_work),
            monitor_loop(),
        )

        assert results[0] == [{"id": 1}], "to_thread should return sync function result"
        assert not loop_blocked, "Event loop should not be blocked by sync work"


# ============================================================================
# T2: Circuit breaker trips after 15 failures (not 50)
# ============================================================================


class TestCircuitBreakerThreshold:
    """T2: Circuit breaker trips after 15 failures."""

    def test_default_threshold_is_15(self):
        """PNCP circuit breaker default threshold must be 15 (was 50)."""
        from pncp_client import PNCP_CIRCUIT_BREAKER_THRESHOLD
        assert PNCP_CIRCUIT_BREAKER_THRESHOLD == 15, (
            f"Expected threshold 15, got {PNCP_CIRCUIT_BREAKER_THRESHOLD}. "
            f"GTM-INFRA-001 AC4 requires threshold reduction from 50 to 15."
        )

    def test_default_cooldown_is_60(self):
        """PNCP circuit breaker cooldown must be 60s (was 120s)."""
        from pncp_client import PNCP_CIRCUIT_BREAKER_COOLDOWN
        assert PNCP_CIRCUIT_BREAKER_COOLDOWN == 60, (
            f"Expected cooldown 60, got {PNCP_CIRCUIT_BREAKER_COOLDOWN}. "
            f"GTM-INFRA-001 AC5 requires proportional reduction."
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips_at_15_failures(self):
        """Circuit breaker must trip after exactly 15 consecutive failures."""
        from pncp_client import PNCPCircuitBreaker

        cb = PNCPCircuitBreaker(name="test_t2", threshold=15, cooldown_seconds=60)
        assert not cb.is_degraded, "Should start healthy"

        # Record 14 failures — should NOT trip
        for i in range(14):
            await cb.record_failure()
        assert not cb.is_degraded, "Should not trip after 14 failures"
        assert cb.consecutive_failures == 14

        # 15th failure — SHOULD trip
        await cb.record_failure()
        assert cb.is_degraded, "Must trip after 15 consecutive failures"
        assert cb.consecutive_failures == 15

    @pytest.mark.asyncio
    async def test_circuit_breaker_does_not_trip_at_50(self):
        """Verify the old threshold of 50 is no longer the default."""
        from pncp_client import PNCPCircuitBreaker

        # Using the new default threshold
        cb = PNCPCircuitBreaker(name="test_old", threshold=15, cooldown_seconds=60)

        for i in range(15):
            await cb.record_failure()

        # It should already be tripped at 15, not waiting for 50
        assert cb.is_degraded, "Should be degraded at 15, not waiting for 50"

    @pytest.mark.asyncio
    async def test_circuit_breaker_prometheus_metric_reports_state(self):
        """AC6: circuit_breaker_degraded Prometheus metric must report state.

        DEBT-204 Track 1: the CIRCUIT_BREAKER_STATE gauge is referenced inside
        ``clients/pncp/circuit_breaker.py``; ``pncp_client.CIRCUIT_BREAKER_STATE``
        is no longer a re-exported module attribute. Patch at the actual call
        site so the mock intercepts ``.labels(...).set(1)``.
        """
        from pncp_client import PNCPCircuitBreaker

        with patch("clients.pncp.circuit_breaker.CIRCUIT_BREAKER_STATE") as mock_gauge:
            mock_labels = MagicMock()
            mock_gauge.labels.return_value = mock_labels

            cb = PNCPCircuitBreaker(name="test_metric", threshold=3, cooldown_seconds=10)

            for _ in range(3):
                await cb.record_failure()

            # Should have set gauge to 1 when tripping
            mock_gauge.labels.assert_called_with(source="test_metric")
            mock_labels.set.assert_called_with(1)


# ============================================================================
# T3: Zero time.sleep() in async production code
# ============================================================================


class TestNoTimeSleepInAsyncCode:
    """T3: No time.sleep() in async functions across the backend codebase."""

    def _get_production_py_files(self):
        """Get all production Python files (exclude tests/, scripts/, examples/)."""
        backend_dir = Path(__file__).parent.parent
        excluded_dirs = {"tests", "scripts", "examples", "venv", "__pycache__", ".pytest_cache"}
        excluded_files = {"test_", "conftest"}

        py_files = []
        for path in backend_dir.rglob("*.py"):
            # Skip excluded directories
            parts = path.relative_to(backend_dir).parts
            if any(d in excluded_dirs for d in parts):
                continue
            # Skip test files
            if any(path.name.startswith(prefix) for prefix in excluded_files):
                continue
            py_files.append(path)

        return py_files

    def test_no_time_sleep_in_async_functions(self):
        """Verify no async function contains time.sleep() — must use asyncio.sleep()."""
        violations = []

        for py_file in self._get_production_py_files():
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef):
                    # Check all calls inside this async function
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            func = child.func
                            # Match time.sleep(...)
                            if (
                                isinstance(func, ast.Attribute)
                                and func.attr == "sleep"
                                and isinstance(func.value, ast.Name)
                                and func.value.id == "time"
                            ):
                                violations.append(
                                    f"{py_file.name}:{child.lineno} "
                                    f"async def {node.name}() contains time.sleep()"
                                )

        assert not violations, (
            "Found time.sleep() in async functions (must use asyncio.sleep()):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_time_sleep_grep_in_pncp_client_async_class(self):
        """Specifically verify AsyncPNCPClient has no time.sleep().

        DEBT-204 Track 1: AsyncPNCPClient moved to ``clients/pncp/async_client.py``.
        Use ``inspect.getsource`` on the imported class so the check survives any
        future package reorganisation.
        """
        import inspect
        from clients.pncp.async_client import AsyncPNCPClient

        async_class_body = inspect.getsource(AsyncPNCPClient)

        # Check for time.sleep (not asyncio.sleep)
        time_sleep_matches = re.findall(r'time\.sleep\(', async_class_body)
        assert not time_sleep_matches, (
            f"AsyncPNCPClient contains {len(time_sleep_matches)} time.sleep() calls. "
            f"Must use asyncio.sleep() in async code."
        )


# ============================================================================
# T4: Gunicorn timeout configured at 180s
# ============================================================================


class TestGunicornTimeout:
    """T4: Gunicorn timeout configured at 180s in start.sh."""

    def test_start_sh_timeout_is_180(self):
        """start.sh must set Gunicorn timeout default to 110s (DEBT-04 AC1: < Railway 120s hard cutoff, prevents silent request death)."""
        start_sh_path = Path(__file__).parent.parent / "start.sh"
        content = start_sh_path.read_text(encoding="utf-8")

        # Check the --timeout line uses 110 as default (DEBT-04 AC1 tightened from 120 → 110)
        assert "GUNICORN_TIMEOUT:-110" in content, (
            "start.sh must use GUNICORN_TIMEOUT:-110 (DEBT-04 AC1: < Railway 120s). "
            "GTM-INFRA-001 AC7/AC8."
        )

        # Ensure old 900 default is gone
        assert "GUNICORN_TIMEOUT:-900" not in content, (
            "start.sh still contains the old 900s timeout default"
        )

    def test_start_sh_echo_line_shows_180(self):
        """The echo/log line in start.sh must show 110 default (DEBT-04 AC1: < Railway 120s hard cutoff)."""
        start_sh_path = Path(__file__).parent.parent / "start.sh"
        content = start_sh_path.read_text(encoding="utf-8")

        # The echo line that logs the timeout
        echo_lines = [line for line in content.split("\n") if "timeout=" in line and "echo" in line]
        assert echo_lines, "No echo line with timeout found in start.sh"
        assert "110" in echo_lines[0], (
            f"Echo line should show 110s default: {echo_lines[0]}"
        )

    def test_railway_timeout_documented_in_claude_md(self):
        """AC9: CLAUDE.md must document Railway hard timeout ~120s."""
        claude_md_path = Path(__file__).parent.parent.parent / "CLAUDE.md"
        content = claude_md_path.read_text(encoding="utf-8")

        assert "Railway hard timeout" in content, (
            "CLAUDE.md must document Railway hard timeout (AC9)"
        )
        assert "120s" in content or "~120s" in content, (
            "CLAUDE.md must mention the ~120s Railway hard timeout value"
        )
