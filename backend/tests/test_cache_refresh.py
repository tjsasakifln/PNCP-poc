"""CRIT-032: Tests for periodic cache refresh via ARQ cron job.

Covers AC22-AC31:
- get_stale_entries_for_refresh() query logic
- cache_refresh_job feature flag, dispatch, CB check, graceful degradation
- Stagger timing
- Prometheus metrics emission

Mock strategy: All imports inside cache_refresh_job are deferred (inside function body),
so we patch at the SOURCE module, not at job_queue:
  - redis_pool.get_redis_pool (not job_queue.get_redis_pool)
  - search_cache.get_stale_entries_for_refresh (not job_queue.*)
  - search_cache.trigger_background_revalidation (not job_queue.*)
  - pncp_client.get_circuit_breaker (not job_queue.*)
  - metrics.CACHE_REFRESH_TOTAL / CACHE_REFRESH_DURATION
  - supabase_client.get_supabase (for search_cache tests)
"""

from datetime import datetime, timezone, timedelta, date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_supabase_mock(empty_data=None, hot_data=None, warm_data=None):
    """Helper: build a Supabase mock that returns different data per select() call.

    get_stale_entries_for_refresh() calls .table().select() 3 times:
      1. Empty entries (eq total_results=0)
      2. HOT stale entries (eq priority=hot, lt fetched_at, gt total_results)
      3. WARM stale entries (eq priority=warm, lt fetched_at, gt total_results)
    """
    mock_sb = MagicMock()
    mock_table = MagicMock()
    mock_sb.table.return_value = mock_table

    call_count = [0]

    def mock_select(*args, **kwargs):
        chain = MagicMock()
        call_count[0] += 1
        idx = call_count[0]

        # Make all chaining methods return the chain itself
        for method in ("eq", "lt", "gt", "gte", "lte", "order", "limit"):
            getattr(chain, method).return_value = chain

        if idx == 1:
            chain.execute.return_value = MagicMock(data=empty_data or [])
        elif idx == 2:
            chain.execute.return_value = MagicMock(data=hot_data or [])
        else:
            chain.execute.return_value = MagicMock(data=warm_data or [])
        return chain

    mock_table.select = mock_select
    return mock_sb


# ===========================================================================
# AC22: get_stale_entries_for_refresh returns HOT+WARM stale entries
# ===========================================================================

@pytest.mark.asyncio
async def test_get_stale_entries_returns_hot_warm_stale():
    """AC22: Query returns HOT and WARM stale entries ordered by priority."""
    hot_entry = {
        "user_id": "u1", "params_hash": "hash_hot",
        "search_params": {"setor_id": "vestuario", "ufs": ["SP"]},
        "total_results": 10, "priority": "hot", "access_count": 5, "degraded_until": None,
    }
    warm_entry = {
        "user_id": "u2", "params_hash": "hash_warm",
        "search_params": {"setor_id": "alimentos", "ufs": ["RJ"]},
        "total_results": 3, "priority": "warm", "access_count": 2, "degraded_until": None,
    }

    mock_sb = _make_supabase_mock(empty_data=[], hot_data=[hot_entry], warm_data=[warm_entry])

    with patch("supabase_client.get_supabase", return_value=mock_sb):
        from search_cache import get_stale_entries_for_refresh
        result = await get_stale_entries_for_refresh(batch_size=10)

    assert len(result) == 2
    assert result[0]["params_hash"] == "hash_hot"
    assert result[1]["params_hash"] == "hash_warm"


# ===========================================================================
# AC23: Empty entries appear before stale entries
# ===========================================================================

@pytest.mark.asyncio
async def test_empty_entries_before_stale():
    """AC23: Entries with total_results=0 appear first regardless of priority."""
    empty_entry = {
        "user_id": "u1", "params_hash": "hash_empty",
        "search_params": {"setor_id": "vestuario", "ufs": ["SP"]},
        "total_results": 0, "priority": "cold", "access_count": 0, "degraded_until": None,
    }
    hot_entry = {
        "user_id": "u2", "params_hash": "hash_hot",
        "search_params": {"setor_id": "alimentos", "ufs": ["MG"]},
        "total_results": 15, "priority": "hot", "access_count": 10, "degraded_until": None,
    }

    mock_sb = _make_supabase_mock(empty_data=[empty_entry], hot_data=[hot_entry], warm_data=[])

    with patch("supabase_client.get_supabase", return_value=mock_sb):
        from search_cache import get_stale_entries_for_refresh
        result = await get_stale_entries_for_refresh(batch_size=10)

    assert len(result) == 2
    assert result[0]["params_hash"] == "hash_empty"
    assert result[0]["total_results"] == 0
    assert result[1]["params_hash"] == "hash_hot"


# ===========================================================================
# AC24: Degraded entries are excluded
# ===========================================================================

@pytest.mark.asyncio
async def test_degraded_entries_excluded():
    """AC24: Entries with degraded_until in the future are excluded."""
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    degraded_entry = {
        "user_id": "u1", "params_hash": "hash_deg",
        "search_params": {"setor_id": "vestuario", "ufs": ["SP"]},
        "total_results": 5, "priority": "hot", "access_count": 3,
        "degraded_until": future,
    }

    mock_sb = _make_supabase_mock(empty_data=[], hot_data=[degraded_entry], warm_data=[])

    with patch("supabase_client.get_supabase", return_value=mock_sb):
        from search_cache import get_stale_entries_for_refresh
        result = await get_stale_entries_for_refresh(batch_size=10)

    assert len(result) == 0


# ===========================================================================
# AC25: cache_refresh_job with feature flag false
# ===========================================================================

@pytest.mark.asyncio
async def test_cache_refresh_job_flag_disabled():
    """AC25: Job returns immediately when CACHE_REFRESH_ENABLED=false."""
    with patch("config.CACHE_REFRESH_ENABLED", False):
        from job_queue import cache_refresh_job
        result = await cache_refresh_job({})

    assert result["status"] == "disabled"


# ===========================================================================
# AC26: cache_refresh_job dispatches trigger_background_revalidation
# ===========================================================================

@pytest.mark.asyncio
async def test_cache_refresh_job_dispatches_revalidation():
    """AC26: Job calls trigger_background_revalidation for each entry with correct dates."""
    entries = [
        {
            "user_id": "u1", "params_hash": "hash1",
            "search_params": {"setor_id": "vestuario", "ufs": ["SP", "RJ"], "modalidades": [6, 7]},
            "total_results": 5, "priority": "hot", "access_count": 3,
        },
        {
            "user_id": "u2", "params_hash": "hash2",
            "search_params": {"setor_id": "alimentos", "ufs": ["MG"]},
            "total_results": 0, "priority": "cold", "access_count": 0,
        },
    ]

    mock_trigger = AsyncMock(return_value=True)
    mock_redis = AsyncMock()
    mock_cb = MagicMock()
    mock_cb.is_degraded = False

    with (
        patch("config.CACHE_REFRESH_ENABLED", True),
        patch("config.CACHE_REFRESH_BATCH_SIZE", 25),
        patch("config.CACHE_REFRESH_STAGGER_SECONDS", 0),
        patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
        patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, return_value=entries),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.CACHE_REFRESH_TOTAL", MagicMock()),
        patch("metrics.CACHE_REFRESH_DURATION", MagicMock()),
    ):
        from job_queue import cache_refresh_job
        result = await cache_refresh_job({})

    assert result["status"] == "completed"
    assert result["refreshed"] == 2
    assert mock_trigger.call_count == 2

    # Verify dates are today-10d to today
    expected_final = date.today().isoformat()
    expected_inicial = (date.today() - timedelta(days=10)).isoformat()

    for c in mock_trigger.call_args_list:
        kw = c.kwargs
        assert kw["request_data"]["data_inicial"] == expected_inicial
        assert kw["request_data"]["data_final"] == expected_final


# ===========================================================================
# AC27: Job stops on circuit breaker degraded
# ===========================================================================

@pytest.mark.asyncio
async def test_cache_refresh_job_stops_on_cb_degraded():
    """AC27: Job stops cycle immediately when PNCP CB is degraded."""
    entries = [
        {
            "user_id": "u1", "params_hash": "hash1",
            "search_params": {"setor_id": "vestuario", "ufs": ["SP"]},
            "total_results": 5, "priority": "hot", "access_count": 3,
        },
        {
            "user_id": "u2", "params_hash": "hash2",
            "search_params": {"setor_id": "alimentos", "ufs": ["RJ"]},
            "total_results": 3, "priority": "warm", "access_count": 1,
        },
    ]

    mock_cb = MagicMock()
    mock_cb.is_degraded = True
    mock_redis = AsyncMock()

    with (
        patch("config.CACHE_REFRESH_ENABLED", True),
        patch("config.CACHE_REFRESH_BATCH_SIZE", 25),
        patch("config.CACHE_REFRESH_STAGGER_SECONDS", 0),
        patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
        patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, return_value=entries),
        patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock) as mock_trigger,
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.CACHE_REFRESH_TOTAL", MagicMock()),
        patch("metrics.CACHE_REFRESH_DURATION", MagicMock()),
    ):
        from job_queue import cache_refresh_job
        result = await cache_refresh_job({})

    assert result["skipped_cb_open"] == 2
    assert result["refreshed"] == 0
    mock_trigger.assert_not_called()


# ===========================================================================
# AC28: Graceful on Redis unavailable
# ===========================================================================

@pytest.mark.asyncio
async def test_cache_refresh_job_graceful_redis_unavailable():
    """AC28: Job returns without error when Redis is unavailable."""
    with (
        patch("config.CACHE_REFRESH_ENABLED", True),
        patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None),
    ):
        from job_queue import cache_refresh_job
        result = await cache_refresh_job({})

    assert result["status"] == "redis_unavailable"


# ===========================================================================
# AC28b: Graceful on Supabase unavailable
# ===========================================================================

@pytest.mark.asyncio
async def test_cache_refresh_job_graceful_supabase_unavailable():
    """AC28: Job returns without error when Supabase query fails."""
    mock_redis = AsyncMock()

    with (
        patch("config.CACHE_REFRESH_ENABLED", True),
        patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
        patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, side_effect=Exception("DB down")),
    ):
        from job_queue import cache_refresh_job
        result = await cache_refresh_job({})

    assert result["status"] == "supabase_unavailable"


# ===========================================================================
# AC29: Stagger between dispatches
# ===========================================================================

@pytest.mark.asyncio
async def test_cache_refresh_job_stagger():
    """AC29: Job waits CACHE_REFRESH_STAGGER_SECONDS between dispatches."""
    entries = [
        {
            "user_id": f"u{i}", "params_hash": f"hash{i}",
            "search_params": {"setor_id": "vestuario", "ufs": ["SP"]},
            "total_results": 5, "priority": "hot", "access_count": 3,
        }
        for i in range(3)
    ]

    mock_cb = MagicMock()
    mock_cb.is_degraded = False
    mock_redis = AsyncMock()
    sleep_calls = []

    async def mock_sleep(seconds):
        sleep_calls.append(seconds)

    with (
        patch("config.CACHE_REFRESH_ENABLED", True),
        patch("config.CACHE_REFRESH_BATCH_SIZE", 25),
        patch("config.CACHE_REFRESH_STAGGER_SECONDS", 5),
        patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
        patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, return_value=entries),
        patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock, return_value=True),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("asyncio.sleep", side_effect=mock_sleep),
        patch("metrics.CACHE_REFRESH_TOTAL", MagicMock()),
        patch("metrics.CACHE_REFRESH_DURATION", MagicMock()),
    ):
        from job_queue import cache_refresh_job
        result = await cache_refresh_job({})

    # 3 entries = 2 sleeps (no sleep after last)
    assert len(sleep_calls) == 2
    assert all(s == 5 for s in sleep_calls)
    assert result["refreshed"] == 3


# ===========================================================================
# AC30: Prometheus metrics emitted correctly
# ===========================================================================

@pytest.mark.asyncio
async def test_cache_refresh_job_metrics():
    """AC30: Job emits Prometheus metrics for success, skipped, failed, empty_retry."""
    entries = [
        {
            "user_id": "u1", "params_hash": "hash1",
            "search_params": {"setor_id": "vestuario", "ufs": ["SP"]},
            "total_results": 5, "priority": "hot", "access_count": 3,
        },
        {
            "user_id": "u2", "params_hash": "hash2",
            "search_params": {"setor_id": "alimentos", "ufs": ["RJ"]},
            "total_results": 0, "priority": "cold", "access_count": 0,
        },
        {
            "user_id": "u3", "params_hash": "hash3",
            "search_params": {"setor_id": "software", "ufs": ["MG"]},
            "total_results": 8, "priority": "warm", "access_count": 1,
        },
    ]

    # First dispatch succeeds (hot), second succeeds (empty), third fails
    mock_trigger = AsyncMock(side_effect=[True, True, Exception("network error")])
    mock_cb = MagicMock()
    mock_cb.is_degraded = False
    mock_redis = AsyncMock()

    mock_counter = MagicMock()
    mock_counter.labels.return_value = MagicMock()
    mock_histogram = MagicMock()

    with (
        patch("config.CACHE_REFRESH_ENABLED", True),
        patch("config.CACHE_REFRESH_BATCH_SIZE", 25),
        patch("config.CACHE_REFRESH_STAGGER_SECONDS", 0),
        patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
        patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock, return_value=entries),
        patch("search_cache.trigger_background_revalidation", mock_trigger),
        patch("pncp_client.get_circuit_breaker", return_value=mock_cb),
        patch("metrics.CACHE_REFRESH_TOTAL", mock_counter),
        patch("metrics.CACHE_REFRESH_DURATION", mock_histogram),
    ):
        from job_queue import cache_refresh_job
        result = await cache_refresh_job({})

    assert result["refreshed"] == 2
    assert result["failed"] == 1
    assert result["empty_retried"] == 1

    # Verify counter labels called with expected result types
    label_calls = [str(c) for c in mock_counter.labels.call_args_list]
    assert any("success" in c for c in label_calls)
    assert any("empty_retry" in c for c in label_calls)
    assert any("failed" in c for c in label_calls)

    # Verify histogram observed once at end
    mock_histogram.observe.assert_called_once()
