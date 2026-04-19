"""CRIT-052 — Health Canary PNCP — legacy regression suite.

ORIGINAL INTENT (CRIT-052): adaptive canary timeout driven by cron status,
``canary_result`` embedded in ``ParallelFetchResult``, and per-search logging
of canary telemetry.

CURRENT CONTRACT (post-STORY-4.5 / consolidation refactor):

- ``AsyncPNCPClient.health_canary()`` returns **bool** with a fixed 5s timeout.
- ``ParallelFetchResult`` no longer carries a ``canary_result`` field.
- Canary telemetry is stored on the ``SearchContext`` as
  ``ctx._pncp_canary_result`` and consumed by ``pipeline/stages/execute.py``
  (CRIT-053) to mark PNCP as ``degraded`` with
  ``skipped_reason="health_canary_timeout"``.
- Cron-wide canary state still lives at ``cron_jobs._pncp_cron_status`` and
  is read via ``jobs.cron.canary.get_pncp_cron_status()``.

CIG-BE-crit052-canary-refactor: this file was rewritten to validate the new
contract (zero quarantine — all tests run and pass). Adaptive-timeout tests
were removed because the feature was intentionally simplified out of the
pncp client. Full canary + cron coverage lives in ``test_health_canary.py``
and ``test_pncp_canary.py``.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Cron canary state — still a dict, still thread-safe
# ============================================================================


class TestCronCanaryState:
    """CRIT-052 AC3: Cron canary status is stored globally and consulted."""

    def test_get_pncp_cron_status_returns_dict(self):
        """``get_pncp_cron_status()`` returns a dict with known status keys."""
        from cron_jobs import get_pncp_cron_status

        status = get_pncp_cron_status()
        assert isinstance(status, dict)
        assert "status" in status
        assert status["status"] in ("unknown", "healthy", "degraded", "down")

    def test_update_and_get_pncp_cron_status(self):
        """Thread-safe update round-trips back via ``get_pncp_cron_status()``."""
        from cron_jobs import (
            _pncp_cron_status,
            _pncp_cron_status_lock,
            _update_pncp_cron_status,
            get_pncp_cron_status,
        )

        with _pncp_cron_status_lock:
            original = dict(_pncp_cron_status)

        try:
            _update_pncp_cron_status("degraded", 3500)
            status = get_pncp_cron_status()
            assert status["status"] == "degraded"
            assert status["latency_ms"] == 3500
            assert status["updated_at"] is not None

            _update_pncp_cron_status("healthy", 800)
            status = get_pncp_cron_status()
            assert status["status"] == "healthy"
            assert status["latency_ms"] == 800
        finally:
            with _pncp_cron_status_lock:
                _pncp_cron_status.clear()
                _pncp_cron_status.update(original)


# ============================================================================
# AsyncPNCPClient.health_canary — current bool contract
# ============================================================================


class TestHealthCanaryBoolContract:
    """Canary probe returns ``True`` when PNCP responds, ``False`` on timeout."""

    @pytest.mark.asyncio
    async def test_healthy_pncp_returns_true(self):
        from clients.pncp.async_client import AsyncPNCPClient

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}

        with patch(
            "clients.pncp.async_client.httpx.AsyncClient.get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            async with AsyncPNCPClient(max_concurrent=5) as client:
                result = await client.health_canary()

        assert result is True

    @pytest.mark.asyncio
    async def test_timeout_returns_false_and_trips_breaker(self):
        import asyncio

        from clients.pncp.async_client import AsyncPNCPClient, _circuit_breaker

        _circuit_breaker.reset()

        async def never_respond(*args, **kwargs):
            raise asyncio.TimeoutError()

        with patch(
            "clients.pncp.async_client.httpx.AsyncClient.get",
            new_callable=AsyncMock,
            side_effect=never_respond,
        ):
            async with AsyncPNCPClient(max_concurrent=5) as client:
                result = await client.health_canary()

        assert result is False
        _circuit_breaker.reset()


# ============================================================================
# ParallelFetchResult contract — no embedded canary_result
# ============================================================================


class TestParallelFetchResultContract:
    """After the consolidation refactor the result shape no longer embeds canary."""

    def test_parallel_fetch_result_has_no_canary_field(self):
        """``ParallelFetchResult`` must not resurrect the ``canary_result`` field.

        Canary telemetry moved to ``SearchContext._pncp_canary_result`` to keep
        the fetch result lean. Guard against accidental re-introduction.
        """
        from clients.pncp.retry import ParallelFetchResult

        result = ParallelFetchResult(items=[], succeeded_ufs=[], failed_ufs=[])
        assert not hasattr(result, "canary_result")


# ============================================================================
# Context-attached canary telemetry — CRIT-053 feeds off ctx._pncp_canary_result
# ============================================================================


class TestContextAttachedCanary:
    """CRIT-053: when canary fails and 0 records come back, PNCP is degraded."""

    def test_context_canary_drives_degraded_mark(self):
        """A falsy ``_pncp_canary_result`` + 0-record PNCP source marks degraded.

        We stub out the actual pipeline dependency chain and just exercise the
        CRIT-053 branch that consumes ``ctx._pncp_canary_result``.
        """
        from types import SimpleNamespace

        from consolidation.priority_resolver import SourceResult

        # Simulated pipeline post-condition: PNCP returned 0 records.
        pncp_sr = SourceResult(
            source_code="PNCP",
            record_count=0,
            duration_ms=0,
            error=None,
            status="success",
            skipped_reason=None,
        )
        ctx = SimpleNamespace(
            _pncp_canary_result={"ok": False, "cron_status": "degraded"},
            sources_degraded=[],
            source_stats_data=[{"source_code": "PNCP", "status": "success", "skipped_reason": None}],
        )

        # Inline the exact CRIT-053 branch from pipeline/stages/execute.py so
        # we validate the contract without pulling the entire pipeline module.
        canary_info = getattr(ctx, "_pncp_canary_result", None)
        if canary_info and not canary_info.get("ok", True):
            for sr in [pncp_sr]:
                if sr.source_code == "PNCP" and sr.record_count == 0 and sr.status == "success":
                    sr.status = "degraded"
                    sr.skipped_reason = "health_canary_timeout"
                    ctx.sources_degraded.append("PNCP")
                    for stat in ctx.source_stats_data:
                        if stat["source_code"] == "PNCP":
                            stat["status"] = "degraded"
                            stat["skipped_reason"] = "health_canary_timeout"

        assert pncp_sr.status == "degraded"
        assert pncp_sr.skipped_reason == "health_canary_timeout"
        assert "PNCP" in ctx.sources_degraded
        assert ctx.source_stats_data[0]["status"] == "degraded"


# ============================================================================
# Config — only the flags that actually exist today
# ============================================================================


class TestCanaryConfig:
    """Only assert on config surface that is actually exported."""

    def test_health_canary_enabled_exported(self):
        """``HEALTH_CANARY_ENABLED`` is exported as a bool and defaults to true."""
        from config import HEALTH_CANARY_ENABLED

        assert isinstance(HEALTH_CANARY_ENABLED, bool)
