"""STAB-007 AC4: Cache warming non-interference with user searches.

Tests cover:
  1. Warming respects batch delay (WARMING_BATCH_DELAY_S between requests)
  2. Warming pauses when active_searches > 0
  3. Warming resumes after active searches complete
  4. Warming stops on circuit breaker OPEN
  5. Warming stops on 429 rate limit
  6. Warming respects 30min budget timeout
  7. Warming uses system UUID (WARMING_USER_ID)
  8. Max pause cycles exhausted → skip combination

Mock strategy: All imports inside cache_warming_job are deferred (inside function body),
so we patch at the SOURCE module:
  - config.CACHE_WARMING_ENABLED, config.WARMING_* constants
  - supabase_client.get_supabase
  - search_cache.trigger_background_revalidation
  - pncp_client.get_circuit_breaker
  - metrics.ACTIVE_SEARCHES, metrics.WARMING_COMBINATIONS_TOTAL, metrics.WARMING_PAUSES_TOTAL
"""

import asyncio
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

# Ensure arq is mockable (not installed locally)
if "arq" not in sys.modules:
    _arq_mock = MagicMock()
    _arq_mock.cron = MagicMock()
    sys.modules["arq"] = _arq_mock
    sys.modules["arq.connections"] = MagicMock()
    sys.modules["arq.cron"] = _arq_mock


def _make_supabase_mock(session_data=None):
    """Build a Supabase mock that returns search_sessions data."""
    mock_sb = MagicMock()
    mock_table = MagicMock()
    mock_sb.table.return_value = mock_table

    chain = MagicMock()
    for method in ("eq", "order", "limit", "select"):
        getattr(chain, method).return_value = chain
    mock_table.select.return_value = chain

    chain.execute.return_value = MagicMock(data=session_data or [])
    return mock_sb


def _make_session_rows(combos: list[dict]) -> list[dict]:
    """Build mock session data rows from a list of sector+UF combos."""
    rows = []
    for combo in combos:
        rows.append({
            "search_params": {
                "setor_id": combo.get("setor_id", "vestuario"),
                "ufs": combo.get("ufs", ["SP"]),
            }
        })
    return rows


def _make_active_searches_gauge(value: int = 0):
    """Build a mock ACTIVE_SEARCHES gauge with ._value.get() returning given value."""
    mock = MagicMock()
    mock._value = MagicMock()
    mock._value.get.return_value = value
    return mock


def _make_active_searches_sequence(values: list[int]):
    """Build a mock ACTIVE_SEARCHES gauge that returns sequential values."""
    mock = MagicMock()
    mock._value = MagicMock()
    mock._value.get.side_effect = values
    return mock


# ===========================================================================
# Test 1: Warming respects batch delay (3s between requests)
# ===========================================================================

@pytest.mark.asyncio
async def test_warming_respects_batch_delay():
    """Warming should sleep WARMING_BATCH_DELAY_S between each combination."""
    sessions = _make_session_rows([
        {"setor_id": "vestuario", "ufs": ["SP"]},
        {"setor_id": "vestuario", "ufs": ["SP"]},
        {"setor_id": "alimentos", "ufs": ["RJ"]},
        {"setor_id": "alimentos", "ufs": ["RJ"]},
    ])
    mock_sb = _make_supabase_mock(sessions)
    mock_trigger = AsyncMock(return_value=True)
    mock_cb = MagicMock()
    mock_cb.is_degraded = False
    mock_gauge = _make_active_searches_gauge(0)

    sleep_durations = []
    original_sleep = asyncio.sleep

    async def mock_sleep(duration):
        sleep_durations.append(duration)

    with (
        patch("config.CACHE_WARMING_ENABLED", True),
        patch("config.WARMING_BATCH_DELAY_S", 3.0),
        patch("config.WARMING_BUDGET_TIMEOUT_S", 1800.0),
        patch("config.WARMING_PAUSE_ON_ACTIVE_S", 10.0),
        patch("config.WARMING_MAX_PAUSE_CYCLES", 3),
        patch("config.WARMING_USER_ID", "00000000-0000-0000-0000-000000000000"),
        patch("config.WARMING_RATE_LIMIT_BACKOFF_S", 60.0),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.ACTIVE_SEARCHES", mock_gauge),
        patch("asyncio.sleep", side_effect=mock_sleep),
    ):
        from job_queue import cache_warming_job
        result = await cache_warming_job({})

    assert result["status"] == "completed"
    assert result["warmed"] == 2  # 2 unique combos
    # Between 2 combos there should be exactly 1 batch delay of 3.0s
    assert 3.0 in sleep_durations


# ===========================================================================
# Test 2: Warming pauses when active_searches > 0
# ===========================================================================

@pytest.mark.asyncio
async def test_warming_pauses_when_active_searches():
    """Warming should pause (sleep) when ACTIVE_SEARCHES gauge > 0."""
    sessions = _make_session_rows([
        {"setor_id": "vestuario", "ufs": ["SP"]},
    ])
    mock_sb = _make_supabase_mock(sessions)
    mock_trigger = AsyncMock(return_value=True)
    mock_cb = MagicMock()
    mock_cb.is_degraded = False

    # First call: active=2, second call: active=0 (cleared)
    mock_gauge = _make_active_searches_sequence([2, 0])

    sleep_calls = []

    async def mock_sleep(duration):
        sleep_calls.append(duration)

    with (
        patch("config.CACHE_WARMING_ENABLED", True),
        patch("config.WARMING_BATCH_DELAY_S", 3.0),
        patch("config.WARMING_BUDGET_TIMEOUT_S", 1800.0),
        patch("config.WARMING_PAUSE_ON_ACTIVE_S", 10.0),
        patch("config.WARMING_MAX_PAUSE_CYCLES", 3),
        patch("config.WARMING_USER_ID", "00000000-0000-0000-0000-000000000000"),
        patch("config.WARMING_RATE_LIMIT_BACKOFF_S", 60.0),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.ACTIVE_SEARCHES", mock_gauge),
        patch("asyncio.sleep", side_effect=mock_sleep),
    ):
        from job_queue import cache_warming_job
        result = await cache_warming_job({})

    assert result["status"] == "completed"
    assert result["warmed"] == 1
    # Should have paused once with 10s delay
    assert 10.0 in sleep_calls


# ===========================================================================
# Test 3: Warming resumes after active searches complete
# ===========================================================================

@pytest.mark.asyncio
async def test_warming_resumes_after_active_searches_complete():
    """After pause, warming should continue once active_searches drops to 0."""
    sessions = _make_session_rows([
        {"setor_id": "vestuario", "ufs": ["SP"]},
        {"setor_id": "vestuario", "ufs": ["SP"]},
        {"setor_id": "alimentos", "ufs": ["RJ"]},
        {"setor_id": "alimentos", "ufs": ["RJ"]},
    ])
    mock_sb = _make_supabase_mock(sessions)
    mock_trigger = AsyncMock(return_value=True)
    mock_cb = MagicMock()
    mock_cb.is_degraded = False

    # Combo 1 check: active=0 (proceed)
    # Combo 2 check: active=3 (pause), then active=0 (proceed)
    mock_gauge = _make_active_searches_sequence([0, 3, 0])

    async def mock_sleep(duration):
        pass

    with (
        patch("config.CACHE_WARMING_ENABLED", True),
        patch("config.WARMING_BATCH_DELAY_S", 3.0),
        patch("config.WARMING_BUDGET_TIMEOUT_S", 1800.0),
        patch("config.WARMING_PAUSE_ON_ACTIVE_S", 10.0),
        patch("config.WARMING_MAX_PAUSE_CYCLES", 3),
        patch("config.WARMING_USER_ID", "00000000-0000-0000-0000-000000000000"),
        patch("config.WARMING_RATE_LIMIT_BACKOFF_S", 60.0),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.ACTIVE_SEARCHES", mock_gauge),
        patch("asyncio.sleep", side_effect=mock_sleep),
    ):
        from job_queue import cache_warming_job
        result = await cache_warming_job({})

    assert result["status"] == "completed"
    assert result["warmed"] == 2  # Both combos warmed successfully
    assert mock_trigger.call_count == 2


# ===========================================================================
# Test 4: Warming stops on circuit breaker OPEN
# ===========================================================================

@pytest.mark.asyncio
async def test_warming_stops_on_circuit_breaker_open():
    """Warming should immediately stop when PNCP circuit breaker is degraded."""
    sessions = _make_session_rows([
        {"setor_id": "vestuario", "ufs": ["SP"]},
        {"setor_id": "vestuario", "ufs": ["SP"]},
        {"setor_id": "alimentos", "ufs": ["RJ"]},
        {"setor_id": "alimentos", "ufs": ["RJ"]},
        {"setor_id": "informatica", "ufs": ["MG"]},
        {"setor_id": "informatica", "ufs": ["MG"]},
    ])
    mock_sb = _make_supabase_mock(sessions)
    mock_trigger = AsyncMock(return_value=True)
    mock_cb = MagicMock()
    mock_cb.is_degraded = True  # CB is OPEN from the start
    mock_gauge = _make_active_searches_gauge(0)

    async def mock_sleep(duration):
        pass

    with (
        patch("config.CACHE_WARMING_ENABLED", True),
        patch("config.WARMING_BATCH_DELAY_S", 3.0),
        patch("config.WARMING_BUDGET_TIMEOUT_S", 1800.0),
        patch("config.WARMING_PAUSE_ON_ACTIVE_S", 10.0),
        patch("config.WARMING_MAX_PAUSE_CYCLES", 3),
        patch("config.WARMING_USER_ID", "00000000-0000-0000-0000-000000000000"),
        patch("config.WARMING_RATE_LIMIT_BACKOFF_S", 60.0),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.ACTIVE_SEARCHES", mock_gauge),
        patch("asyncio.sleep", side_effect=mock_sleep),
    ):
        from job_queue import cache_warming_job
        result = await cache_warming_job({})

    assert result["status"] == "completed"
    assert result["warmed"] == 0
    assert result["skipped_cb_open"] == 3  # All 3 unique combos skipped
    assert mock_trigger.call_count == 0  # No revalidation dispatched


# ===========================================================================
# Test 5: Warming stops on 429 rate limit
# ===========================================================================

@pytest.mark.asyncio
async def test_warming_stops_on_429_rate_limit():
    """Warming should stop on 429 response and not retry the failed request."""
    sessions = _make_session_rows([
        {"setor_id": "vestuario", "ufs": ["SP"]},
        {"setor_id": "vestuario", "ufs": ["SP"]},
        {"setor_id": "alimentos", "ufs": ["RJ"]},
        {"setor_id": "alimentos", "ufs": ["RJ"]},
        {"setor_id": "informatica", "ufs": ["MG"]},
        {"setor_id": "informatica", "ufs": ["MG"]},
    ])
    mock_sb = _make_supabase_mock(sessions)

    call_count = [0]

    async def mock_trigger_with_429(**kwargs):
        call_count[0] += 1
        if call_count[0] == 2:
            raise Exception("HTTP 429 Too Many Requests")
        return True

    mock_trigger = AsyncMock(side_effect=mock_trigger_with_429)
    mock_cb = MagicMock()
    mock_cb.is_degraded = False
    mock_gauge = _make_active_searches_gauge(0)

    async def mock_sleep(duration):
        pass

    with (
        patch("config.CACHE_WARMING_ENABLED", True),
        patch("config.WARMING_BATCH_DELAY_S", 3.0),
        patch("config.WARMING_BUDGET_TIMEOUT_S", 1800.0),
        patch("config.WARMING_PAUSE_ON_ACTIVE_S", 10.0),
        patch("config.WARMING_MAX_PAUSE_CYCLES", 3),
        patch("config.WARMING_USER_ID", "00000000-0000-0000-0000-000000000000"),
        patch("config.WARMING_RATE_LIMIT_BACKOFF_S", 60.0),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.ACTIVE_SEARCHES", mock_gauge),
        patch("asyncio.sleep", side_effect=mock_sleep),
    ):
        from job_queue import cache_warming_job
        result = await cache_warming_job({})

    assert result["status"] == "completed"
    assert result["warmed"] == 1  # First combo succeeded
    assert result["skipped_rate_limit"] >= 1  # At least the 429 combo + remaining
    assert mock_trigger.call_count == 2  # Only 2 calls: 1 success + 1 that got 429


# ===========================================================================
# Test 6: Warming respects 30min budget timeout
# ===========================================================================

@pytest.mark.asyncio
async def test_warming_respects_budget_timeout():
    """Warming should stop when WARMING_BUDGET_TIMEOUT_S is exceeded."""
    sessions = _make_session_rows([
        {"setor_id": "vestuario", "ufs": ["SP"]},
        {"setor_id": "vestuario", "ufs": ["SP"]},
        {"setor_id": "alimentos", "ufs": ["RJ"]},
        {"setor_id": "alimentos", "ufs": ["RJ"]},
    ])
    mock_sb = _make_supabase_mock(sessions)
    mock_trigger = AsyncMock(return_value=True)
    mock_cb = MagicMock()
    mock_cb.is_degraded = False
    mock_gauge = _make_active_searches_gauge(0)

    # Simulate time passage: start at 0, first check OK, second check exceeds budget
    start_time = time.monotonic()
    time_values = [
        start_time,         # start timestamp
        start_time + 1,     # first combo: elapsed=1 < budget (OK)
        start_time + 2000,  # second combo: elapsed=2000 > budget=10 (STOP)
    ]
    time_call_idx = [0]
    original_monotonic = time.monotonic

    def mock_monotonic():
        if time_call_idx[0] < len(time_values):
            val = time_values[time_call_idx[0]]
            time_call_idx[0] += 1
            return val
        return time_values[-1]

    async def mock_sleep(duration):
        pass

    with (
        patch("config.CACHE_WARMING_ENABLED", True),
        patch("config.WARMING_BATCH_DELAY_S", 3.0),
        patch("config.WARMING_BUDGET_TIMEOUT_S", 10.0),  # Very short for test
        patch("config.WARMING_PAUSE_ON_ACTIVE_S", 10.0),
        patch("config.WARMING_MAX_PAUSE_CYCLES", 3),
        patch("config.WARMING_USER_ID", "00000000-0000-0000-0000-000000000000"),
        patch("config.WARMING_RATE_LIMIT_BACKOFF_S", 60.0),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.ACTIVE_SEARCHES", mock_gauge),
        patch("job_queue.time.monotonic", side_effect=mock_monotonic),
        patch("asyncio.sleep", side_effect=mock_sleep),
    ):
        from job_queue import cache_warming_job
        result = await cache_warming_job({})

    assert result["status"] == "completed"
    assert result["warmed"] == 1  # Only first combo warmed
    assert result["skipped_budget"] == 1  # Second combo skipped due to budget


# ===========================================================================
# Test 7: Warming uses system UUID (not real user)
# ===========================================================================

@pytest.mark.asyncio
async def test_warming_uses_system_uuid():
    """Warming should use WARMING_USER_ID for all revalidation calls."""
    sessions = _make_session_rows([
        {"setor_id": "vestuario", "ufs": ["SP"]},
    ])
    mock_sb = _make_supabase_mock(sessions)
    mock_trigger = AsyncMock(return_value=True)
    mock_cb = MagicMock()
    mock_cb.is_degraded = False
    mock_gauge = _make_active_searches_gauge(0)

    async def mock_sleep(duration):
        pass

    system_uuid = "00000000-0000-0000-0000-000000000000"

    with (
        patch("config.CACHE_WARMING_ENABLED", True),
        patch("config.WARMING_BATCH_DELAY_S", 3.0),
        patch("config.WARMING_BUDGET_TIMEOUT_S", 1800.0),
        patch("config.WARMING_PAUSE_ON_ACTIVE_S", 10.0),
        patch("config.WARMING_MAX_PAUSE_CYCLES", 3),
        patch("config.WARMING_USER_ID", system_uuid),
        patch("config.WARMING_RATE_LIMIT_BACKOFF_S", 60.0),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.ACTIVE_SEARCHES", mock_gauge),
        patch("asyncio.sleep", side_effect=mock_sleep),
    ):
        from job_queue import cache_warming_job
        result = await cache_warming_job({})

    assert result["status"] == "completed"
    assert result["warmed"] == 1
    # Verify the user_id passed to trigger_background_revalidation
    call_kwargs = mock_trigger.call_args
    assert call_kwargs.kwargs["user_id"] == system_uuid


# ===========================================================================
# Test 8: Max pause cycles → skip combination
# ===========================================================================

@pytest.mark.asyncio
async def test_max_pause_cycles_skips_combination():
    """When max pause cycles exhausted, warming should skip the combination."""
    sessions = _make_session_rows([
        {"setor_id": "vestuario", "ufs": ["SP"]},
    ])
    mock_sb = _make_supabase_mock(sessions)
    mock_trigger = AsyncMock(return_value=True)
    mock_cb = MagicMock()
    mock_cb.is_degraded = False

    # Always active — all 3 pause cycles will see active > 0
    mock_gauge = _make_active_searches_sequence([5, 5, 5])

    sleep_calls = []

    async def mock_sleep(duration):
        sleep_calls.append(duration)

    with (
        patch("config.CACHE_WARMING_ENABLED", True),
        patch("config.WARMING_BATCH_DELAY_S", 3.0),
        patch("config.WARMING_BUDGET_TIMEOUT_S", 1800.0),
        patch("config.WARMING_PAUSE_ON_ACTIVE_S", 10.0),
        patch("config.WARMING_MAX_PAUSE_CYCLES", 3),
        patch("config.WARMING_USER_ID", "00000000-0000-0000-0000-000000000000"),
        patch("config.WARMING_RATE_LIMIT_BACKOFF_S", 60.0),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.ACTIVE_SEARCHES", mock_gauge),
        patch("asyncio.sleep", side_effect=mock_sleep),
    ):
        from job_queue import cache_warming_job
        result = await cache_warming_job({})

    assert result["status"] == "completed"
    assert result["warmed"] == 0
    assert result["skipped_active"] == 1
    # Should have had 3 pause sleeps of 10s each
    assert sleep_calls.count(10.0) == 3
    # trigger_background_revalidation should NOT have been called
    assert mock_trigger.call_count == 0
