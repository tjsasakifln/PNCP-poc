"""STORY-4.4 (TD-SYS-003) — timeout invariant + budget wrapper tests.

Ensures the descending-budget invariant holds so Railway's 120s proxy never
cuts a request mid-serialization.
"""

from __future__ import annotations

import asyncio

import pytest


# ---------------------------------------------------------------------------
# Invariant: pipeline > consolidation > per_source > per_uf
# ---------------------------------------------------------------------------


def test_default_timeout_invariant_holds():
    """Fresh import of config reflects the tightened STORY-4.4 defaults."""

    from config import (
        CONSOLIDATION_TIMEOUT,
        PIPELINE_TIMEOUT,
        PNCP_TIMEOUT_PER_MODALITY,
        PNCP_TIMEOUT_PER_SOURCE,
        PNCP_TIMEOUT_PER_UF,
        PNCP_TIMEOUT_PER_UF_DEGRADED,
    )

    # Pipeline must leave Railway enough headroom (≤ 100s ≤ 120 - serialization).
    assert PIPELINE_TIMEOUT <= 110, f"PIPELINE_TIMEOUT {PIPELINE_TIMEOUT}s risks Railway 120s kill"
    assert PIPELINE_TIMEOUT > CONSOLIDATION_TIMEOUT, (
        "pipeline must exceed consolidation so outer wait_for swallows inner TimeoutError"
    )
    assert CONSOLIDATION_TIMEOUT > PNCP_TIMEOUT_PER_SOURCE
    assert PNCP_TIMEOUT_PER_SOURCE > PNCP_TIMEOUT_PER_UF
    assert PNCP_TIMEOUT_PER_UF > PNCP_TIMEOUT_PER_UF_DEGRADED
    assert PNCP_TIMEOUT_PER_UF > PNCP_TIMEOUT_PER_MODALITY


def test_consolidation_source_config_matches_pncp_config():
    """CONSOLIDATION_TIMEOUT_GLOBAL/PER_SOURCE defaults mirror config/pncp.py."""

    import os
    from source_config.sources import ConsolidationConfig
    from config import CONSOLIDATION_TIMEOUT, PNCP_TIMEOUT_PER_SOURCE

    # Clear env to read defaults (tests may import with parent env vars set).
    prior_global = os.environ.pop("CONSOLIDATION_TIMEOUT_GLOBAL", None)
    prior_per_source = os.environ.pop("CONSOLIDATION_TIMEOUT_PER_SOURCE", None)
    try:
        cfg = ConsolidationConfig.from_env()
    finally:
        if prior_global is not None:
            os.environ["CONSOLIDATION_TIMEOUT_GLOBAL"] = prior_global
        if prior_per_source is not None:
            os.environ["CONSOLIDATION_TIMEOUT_PER_SOURCE"] = prior_per_source

    assert cfg.timeout_global == CONSOLIDATION_TIMEOUT, (
        f"source_config.timeout_global ({cfg.timeout_global}) must mirror "
        f"CONSOLIDATION_TIMEOUT ({CONSOLIDATION_TIMEOUT})"
    )
    assert cfg.timeout_per_source == PNCP_TIMEOUT_PER_SOURCE, (
        f"source_config.timeout_per_source ({cfg.timeout_per_source}) must mirror "
        f"PNCP_TIMEOUT_PER_SOURCE ({PNCP_TIMEOUT_PER_SOURCE})"
    )


# ---------------------------------------------------------------------------
# Budget wrapper behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_with_budget_passes_through_value():
    """Fast coroutine returns its value without touching the timeout metric."""

    from pipeline.budget import _run_with_budget

    async def _fast():
        return 42

    assert await _run_with_budget(_fast(), budget=1.0, phase="pipeline") == 42


@pytest.mark.asyncio
async def test_run_with_budget_raises_when_no_fallback():
    """Timeout with ``fallback=None`` re-raises so recovery paths keep working."""

    from pipeline.budget import _run_with_budget

    async def _slow():
        await asyncio.sleep(1)
        return "never"

    with pytest.raises(asyncio.TimeoutError):
        await _run_with_budget(_slow(), budget=0.05, phase="consolidation", source="pncp")


@pytest.mark.asyncio
async def test_run_with_budget_returns_fallback():
    """When a fallback is provided, timeout swallows the error and returns it."""

    from pipeline.budget import _run_with_budget

    async def _slow():
        await asyncio.sleep(1)
        return "never"

    result = await _run_with_budget(
        _slow(), budget=0.05, phase="per_source", source="pncp", fallback=[]
    )
    assert result == []


@pytest.mark.asyncio
async def test_run_with_budget_increments_counter_on_timeout(monkeypatch):
    """The Prometheus counter is incremented on timeout."""

    from pipeline import budget as budget_mod

    calls = []

    class _FakeMetric:
        def labels(self, **kwargs):
            calls.append(kwargs)
            return self

        def inc(self):
            calls.append("inc")

    monkeypatch.setattr(
        "metrics.PIPELINE_BUDGET_EXCEEDED_TOTAL",
        _FakeMetric(),
        raising=False,
    )

    async def _slow():
        await asyncio.sleep(1)

    with pytest.raises(asyncio.TimeoutError):
        await budget_mod._run_with_budget(
            _slow(), budget=0.05, phase="per_uf", source="pncp"
        )

    assert {"phase": "per_uf", "source": "pncp"} in calls
    assert "inc" in calls
