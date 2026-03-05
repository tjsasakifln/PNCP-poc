"""CRIT-055: Tests for adaptive warmup with 27-UF coverage, history-based priority, and PNCP pause.

AC6 tests:
  T1: warmup iterates 27 UFs x 5 sectors
  T2: UFs prioritized by search history
  T3: PNCP degraded → warmup pauses
  T4: Periodic warmup loop triggers warmup_top_params
  T5: Coverage metric updated after warmup
  T6: get_popular_ufs_from_sessions returns sorted UFs
  T7: get_popular_ufs_from_sessions handles empty/error
  T8: Default UF priority used when no history
  T9: Rate limiting respected between dispatches
"""

import asyncio
import sys
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure arq is mockable (not installed locally)
if "arq" not in sys.modules:
    _arq_mock = MagicMock()
    _arq_mock.cron = MagicMock()
    sys.modules["arq"] = _arq_mock
    sys.modules["arq.connections"] = MagicMock()
    sys.modules["arq.cron"] = _arq_mock


# ===========================================================================
# T1: Warmup iterates 27 UFs x 5 sectors
# ===========================================================================

@pytest.mark.asyncio
async def test_warmup_covers_all_27_ufs():
    """AC1: warmup_specific_combinations dispatches for all 27 UFs."""
    from config import ALL_BRAZILIAN_UFS

    sectors = ["software", "informatica", "engenharia", "saude", "facilities"]
    ufs = ALL_BRAZILIAN_UFS.copy()

    assert len(ufs) == 27, "Brazil has 27 UFs"

    mock_trigger = AsyncMock(return_value=True)
    mock_popular = AsyncMock(return_value=[])  # No history → use default order

    with (
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("search_cache.get_popular_ufs_from_sessions", mock_popular),
        patch("cron_jobs.get_pncp_cron_status", return_value={"status": "healthy"}),
    ):
        from cron_jobs import warmup_specific_combinations
        result = await warmup_specific_combinations(ufs, sectors)

    expected_total = 5 * 27  # 135
    assert result["total"] == expected_total
    assert result["dispatched"] == expected_total
    assert result["ufs_covered"] == 27
    assert result["ufs_total"] == 27
    assert mock_trigger.call_count == expected_total

    # Verify all 27 UFs were dispatched
    dispatched_ufs = set()
    for call in mock_trigger.call_args_list:
        uf_list = call.kwargs["params"]["ufs"]
        dispatched_ufs.update(uf_list)
    assert dispatched_ufs == set(ALL_BRAZILIAN_UFS)


# ===========================================================================
# T2: UFs prioritized by search history
# ===========================================================================

@pytest.mark.asyncio
async def test_ufs_prioritized_by_history():
    """AC2: Popular UFs from search history are warmed first."""
    from cron_jobs import _get_prioritized_ufs

    all_ufs = ["SP", "RJ", "MG", "BA", "PR", "RS", "SC"]

    # Mock: RS and SC are most popular in last 7 days
    with patch(
        "search_cache.get_popular_ufs_from_sessions",
        new_callable=AsyncMock,
        return_value=["RS", "SC", "SP"],
    ):
        result = await _get_prioritized_ufs(all_ufs)

    # RS and SC should be first (from history), then SP, then remaining
    assert result[0] == "RS"
    assert result[1] == "SC"
    assert result[2] == "SP"
    # All UFs present
    assert set(result) == set(all_ufs)
    assert len(result) == len(all_ufs)


@pytest.mark.asyncio
async def test_ufs_default_priority_when_no_history():
    """AC2: When no search history, use DEFAULT_UF_PRIORITY order."""
    from cron_jobs import _get_prioritized_ufs
    from config import DEFAULT_UF_PRIORITY

    all_ufs = ["MG", "SP", "RJ"]

    with patch(
        "search_cache.get_popular_ufs_from_sessions",
        new_callable=AsyncMock,
        return_value=[],
    ):
        result = await _get_prioritized_ufs(all_ufs)

    # Should follow DEFAULT_UF_PRIORITY order
    expected_order = [uf for uf in DEFAULT_UF_PRIORITY if uf in set(all_ufs)]
    assert result == expected_order


# ===========================================================================
# T3: PNCP degraded → warmup pauses
# ===========================================================================

@pytest.mark.asyncio
async def test_warmup_pauses_on_pncp_degraded():
    """AC4: When PNCP canary reports degraded, warmup pauses."""
    sectors = ["software"]
    ufs = ["SP", "RJ"]

    mock_trigger = AsyncMock(return_value=True)
    call_count = [0]

    def mock_pncp_status():
        call_count[0] += 1
        # First call: degraded, second: healthy, third: healthy
        if call_count[0] == 1:
            return {"status": "degraded", "latency_ms": 5000}
        return {"status": "healthy", "latency_ms": 500}

    with (
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("search_cache.get_popular_ufs_from_sessions", new_callable=AsyncMock, return_value=[]),
        patch("cron_jobs.get_pncp_cron_status", side_effect=mock_pncp_status),
        patch("config.WARMUP_PNCP_DEGRADED_PAUSE_S", 0.01),  # Fast for tests
    ):
        from cron_jobs import warmup_specific_combinations
        result = await warmup_specific_combinations(ufs, sectors)

    assert result["paused"] >= 1
    assert result["dispatched"] == 2  # Both UFs still dispatched after pause


# ===========================================================================
# T4: Periodic warmup loop triggers warmup_top_params
# ===========================================================================

@pytest.mark.asyncio
async def test_periodic_warmup_loop():
    """AC3: _warmup_startup_and_periodic runs startup then periodic warmup."""
    from cron_jobs import _warmup_startup_and_periodic

    mock_warmup = AsyncMock(return_value={
        "dispatched": 10, "skipped": 0, "failed": 0,
        "paused": 0, "total": 10, "ufs_covered": 5, "ufs_total": 5,
    })
    mock_top = AsyncMock(return_value={"status": "completed", "warmed": 3})

    iteration = [0]
    original_sleep = asyncio.sleep

    async def mock_sleep(seconds):
        iteration[0] += 1
        if iteration[0] >= 3:
            # Cancel after periodic warmup triggers once
            raise asyncio.CancelledError()
        await original_sleep(0)

    with (
        patch("cron_jobs.warmup_specific_combinations", mock_warmup),
        patch("cron_jobs.warmup_top_params", mock_top),
        patch("asyncio.sleep", side_effect=mock_sleep),
        patch("config.WARMUP_PERIODIC_INTERVAL_HOURS", 1),
    ):
        # Should complete without error (CancelledError is caught)
        await _warmup_startup_and_periodic(["SP"], ["software"], 0)

    mock_warmup.assert_called_once()  # Startup warmup
    mock_top.assert_called_once()  # Periodic warmup


# ===========================================================================
# T5: Coverage metric updated after warmup
# ===========================================================================

@pytest.mark.asyncio
async def test_warmup_updates_coverage_metric():
    """AC5: WARMUP_COVERAGE_RATIO gauge is set after warmup."""
    sectors = ["software"]
    ufs = ["SP", "RJ", "MG"]

    mock_trigger = AsyncMock(return_value=True)
    mock_gauge = MagicMock()

    with (
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("search_cache.get_popular_ufs_from_sessions", new_callable=AsyncMock, return_value=[]),
        patch("cron_jobs.get_pncp_cron_status", return_value={"status": "healthy"}),
        patch("metrics.WARMUP_COVERAGE_RATIO", mock_gauge),
    ):
        from cron_jobs import warmup_specific_combinations
        result = await warmup_specific_combinations(ufs, sectors)

    assert result["ufs_covered"] == 3
    # Metric should be set to 1.0 (3/3 = full coverage)
    mock_gauge.set.assert_called_once_with(1.0)


# ===========================================================================
# T6: get_popular_ufs_from_sessions returns sorted UFs
# ===========================================================================

@pytest.mark.asyncio
async def test_get_popular_ufs_from_sessions():
    """AC2: get_popular_ufs_from_sessions returns UFs sorted by frequency."""
    mock_sb = MagicMock()
    mock_table = MagicMock()
    mock_sb.table.return_value = mock_table

    chain = MagicMock()
    for method in ("select", "gte", "in_", "limit"):
        getattr(chain, method).return_value = chain
    mock_table.select.return_value = chain

    # Simulate sessions: SP appears 3x, RS 2x, SC 1x
    chain.execute.return_value = MagicMock(data=[
        {"ufs": ["SP", "RS"]},
        {"ufs": ["SP", "RS"]},
        {"ufs": ["SP", "SC"]},
    ])

    with patch("supabase_client.get_supabase", return_value=mock_sb):
        from search_cache import get_popular_ufs_from_sessions
        result = await get_popular_ufs_from_sessions(days=7)

    assert result == ["SP", "RS", "SC"]


# ===========================================================================
# T7: get_popular_ufs_from_sessions handles empty/error
# ===========================================================================

@pytest.mark.asyncio
async def test_get_popular_ufs_handles_empty():
    """AC2: Returns empty list when no sessions found."""
    mock_sb = MagicMock()
    mock_table = MagicMock()
    mock_sb.table.return_value = mock_table

    chain = MagicMock()
    for method in ("select", "gte", "in_", "limit"):
        getattr(chain, method).return_value = chain
    mock_table.select.return_value = chain
    chain.execute.return_value = MagicMock(data=[])

    with patch("supabase_client.get_supabase", return_value=mock_sb):
        from search_cache import get_popular_ufs_from_sessions
        result = await get_popular_ufs_from_sessions(days=7)

    assert result == []


@pytest.mark.asyncio
async def test_get_popular_ufs_handles_error():
    """AC2: Returns empty list on database error."""
    with patch("supabase_client.get_supabase", side_effect=Exception("DB down")):
        from search_cache import get_popular_ufs_from_sessions
        result = await get_popular_ufs_from_sessions(days=7)

    assert result == []


# ===========================================================================
# T8: Default UF priority used when history call fails
# ===========================================================================

@pytest.mark.asyncio
async def test_prioritized_ufs_fallback_on_error():
    """AC2: When get_popular_ufs_from_sessions raises, use DEFAULT_UF_PRIORITY."""
    from cron_jobs import _get_prioritized_ufs
    from config import DEFAULT_UF_PRIORITY

    all_ufs = ["SP", "RJ", "MG"]

    with patch(
        "search_cache.get_popular_ufs_from_sessions",
        new_callable=AsyncMock,
        side_effect=Exception("DB error"),
    ):
        result = await _get_prioritized_ufs(all_ufs)

    # Should fall back to DEFAULT_UF_PRIORITY order
    expected = [uf for uf in DEFAULT_UF_PRIORITY if uf in {"SP", "RJ", "MG"}]
    assert result == expected


# ===========================================================================
# T9: Rate limiting respected
# ===========================================================================

@pytest.mark.asyncio
async def test_warmup_respects_rate_limit():
    """AC4: Warmup sleeps between requests at configured rate."""
    sectors = ["software"]
    ufs = ["SP", "RJ"]

    mock_trigger = AsyncMock(return_value=True)
    sleep_calls: list[float] = []
    original_sleep = asyncio.sleep

    async def track_sleep(seconds):
        sleep_calls.append(seconds)
        await original_sleep(0)

    with (
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("search_cache.get_popular_ufs_from_sessions", new_callable=AsyncMock, return_value=[]),
        patch("cron_jobs.get_pncp_cron_status", return_value={"status": "healthy"}),
        patch("asyncio.sleep", side_effect=track_sleep),
    ):
        from cron_jobs import warmup_specific_combinations
        await warmup_specific_combinations(ufs, sectors)

    # Should have rate-limit sleeps (0.5s = 1/2 rps)
    rate_sleeps = [s for s in sleep_calls if s == 0.5]
    assert len(rate_sleeps) >= 2  # One per UF dispatch


# ===========================================================================
# T10: start_warmup_task disabled returns noop
# ===========================================================================

@pytest.mark.asyncio
async def test_start_warmup_disabled():
    """start_warmup_task returns noop task when WARMUP_ENABLED=false."""
    with patch("config.WARMUP_ENABLED", False):
        from cron_jobs import start_warmup_task
        task = await start_warmup_task()

    assert task is not None
    await task  # Should complete immediately


# ===========================================================================
# T11: Warmup summary log format (AC5)
# ===========================================================================

@pytest.mark.asyncio
async def test_warmup_summary_log_format():
    """AC5: Warmup result dict contains all expected keys."""
    sectors = ["software"]
    ufs = ["SP"]

    mock_trigger = AsyncMock(return_value=True)

    with (
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("search_cache.get_popular_ufs_from_sessions", new_callable=AsyncMock, return_value=[]),
        patch("cron_jobs.get_pncp_cron_status", return_value={"status": "healthy"}),
    ):
        from cron_jobs import warmup_specific_combinations
        result = await warmup_specific_combinations(ufs, sectors)

    # Verify all expected keys exist
    assert "dispatched" in result
    assert "skipped" in result
    assert "failed" in result
    assert "paused" in result
    assert "total" in result
    assert "ufs_covered" in result
    assert "ufs_total" in result
