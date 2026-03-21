"""Tests for cron_jobs.py — periodic cache, session cleanup, warmup, and canary tasks.

Wave 0 Safety Net: Covers get_pncp_cron_status, _update_pncp_cron_status,
_is_cb_or_connection_error, cleanup_stale_sessions, refresh_stale_cache_entries,
warmup_top_params, warmup_specific_combinations, _get_prioritized_ufs.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from types import SimpleNamespace
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cron_jobs import (
    get_pncp_cron_status,
    get_pncp_recovery_epoch,
    _update_pncp_cron_status,
    _is_cb_or_connection_error,
    cleanup_stale_sessions,
    refresh_stale_cache_entries,
    warmup_top_params,
    _get_prioritized_ufs,
    CLEANUP_INTERVAL_SECONDS,
    SESSION_STALE_HOURS,
    SESSION_OLD_DAYS,
)


@pytest.fixture(autouse=True)
def _reset_pncp_status():
    """Reset PNCP cron status between tests."""
    import cron_jobs
    with cron_jobs._pncp_cron_status_lock:
        cron_jobs._pncp_cron_status.update(
            {"status": "unknown", "latency_ms": None, "updated_at": None}
        )
        cron_jobs._pncp_recovery_epoch = 0
    yield


# ──────────────────────────────────────────────────────────────────────
# get_pncp_cron_status / _update_pncp_cron_status
# ──────────────────────────────────────────────────────────────────────

class TestPncpCronStatus:
    """Tests for PNCP cron canary status."""

    @pytest.mark.timeout(30)
    def test_initial_status(self):
        status = get_pncp_cron_status()
        assert status["status"] == "unknown"
        assert status["latency_ms"] is None

    @pytest.mark.timeout(30)
    def test_update_healthy(self):
        _update_pncp_cron_status("healthy", 150)
        status = get_pncp_cron_status()
        assert status["status"] == "healthy"
        assert status["latency_ms"] == 150
        assert status["updated_at"] is not None

    @pytest.mark.timeout(30)
    def test_update_degraded(self):
        _update_pncp_cron_status("degraded", 5000)
        status = get_pncp_cron_status()
        assert status["status"] == "degraded"

    @pytest.mark.timeout(30)
    def test_recovery_epoch_increments(self):
        """CRIT-056 AC4: Recovery from degraded->healthy increments epoch."""
        _update_pncp_cron_status("degraded", 5000)
        assert get_pncp_recovery_epoch() == 0
        _update_pncp_cron_status("healthy", 100)
        assert get_pncp_recovery_epoch() == 1

    @pytest.mark.timeout(30)
    def test_no_epoch_increment_on_healthy_to_healthy(self):
        _update_pncp_cron_status("healthy", 100)
        _update_pncp_cron_status("healthy", 120)
        assert get_pncp_recovery_epoch() == 0

    @pytest.mark.timeout(30)
    def test_down_to_healthy_increments(self):
        _update_pncp_cron_status("down", None)
        _update_pncp_cron_status("healthy", 200)
        assert get_pncp_recovery_epoch() == 1

    @pytest.mark.timeout(30)
    def test_returns_dict_copy(self):
        _update_pncp_cron_status("healthy", 100)
        status1 = get_pncp_cron_status()
        status1["status"] = "modified"
        status2 = get_pncp_cron_status()
        assert status2["status"] == "healthy"


# ──────────────────────────────────────────────────────────────────────
# _is_cb_or_connection_error
# ──────────────────────────────────────────────────────────────────────

class TestIsCbOrConnectionError:
    """Tests for circuit breaker / connection error detection."""

    @pytest.mark.timeout(30)
    def test_circuit_breaker_error(self):
        assert _is_cb_or_connection_error(
            type("CircuitBreakerOpenError", (Exception,), {})("CB is open")
        ) is True

    @pytest.mark.timeout(30)
    def test_connection_error(self):
        assert _is_cb_or_connection_error(ConnectionError("refused")) is True

    @pytest.mark.timeout(30)
    def test_connect_error_in_message(self):
        assert _is_cb_or_connection_error(Exception("ConnectError: timeout")) is True

    @pytest.mark.timeout(30)
    def test_pgrst205_in_message(self):
        assert _is_cb_or_connection_error(Exception("PGRST205: table not found")) is True

    @pytest.mark.timeout(30)
    def test_generic_error(self):
        assert _is_cb_or_connection_error(ValueError("bad input")) is False

    @pytest.mark.timeout(30)
    def test_empty_error(self):
        assert _is_cb_or_connection_error(Exception("")) is False


# ──────────────────────────────────────────────────────────────────────
# cleanup_stale_sessions
# ──────────────────────────────────────────────────────────────────────

class TestCleanupStaleSessions:
    """Tests for session cleanup task."""

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    @patch("supabase_client.sb_execute", new_callable=AsyncMock)
    async def test_happy_path(self, mock_execute, mock_get_sb):
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        mock_sb.table.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.delete.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.lt.return_value = mock_sb

        mock_execute.return_value = SimpleNamespace(data=[])

        result = await cleanup_stale_sessions()
        assert "marked_stale" in result
        assert "deleted_old" in result
        assert result["marked_stale"] == 0
        assert result["deleted_old"] == 0

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase", side_effect=Exception("DB down"))
    async def test_error_handling(self, mock_get_sb):
        result = await cleanup_stale_sessions()
        assert "error" in result

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    @patch("supabase_client.sb_execute", new_callable=AsyncMock)
    async def test_schema_fallback(self, mock_execute, mock_get_sb):
        """When status column missing, falls back to created_at cleanup."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb
        mock_sb.table.return_value = mock_sb
        mock_sb.update.return_value = mock_sb
        mock_sb.delete.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.lt.return_value = mock_sb

        call_count = [0]

        async def side_effect(query):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("42703: undefined column 'status'")
            return SimpleNamespace(data=[])

        mock_execute.side_effect = side_effect

        result = await cleanup_stale_sessions()
        assert "deleted_old" in result


# ──────────────────────────────────────────────────────────────────────
# refresh_stale_cache_entries
# ──────────────────────────────────────────────────────────────────────

class TestRefreshStaleCacheEntries:
    """Tests for stale cache refresh task."""

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock)
    @patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock)
    async def test_no_stale_entries(self, mock_trigger, mock_get_stale):
        mock_get_stale.return_value = []
        result = await refresh_stale_cache_entries()
        assert result["status"] == "no_stale_entries"

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock)
    @patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock)
    async def test_entries_refreshed(self, mock_trigger, mock_get_stale):
        mock_get_stale.return_value = [
            {"user_id": "u1", "search_params": {"ufs": ["SP"]}, "params_hash": "abc"},
        ]
        mock_trigger.return_value = True
        result = await refresh_stale_cache_entries()
        assert result["refreshed"] == 1

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_cache.get_stale_entries_for_refresh", new_callable=AsyncMock)
    async def test_error_handling(self, mock_get_stale):
        mock_get_stale.side_effect = Exception("cache error")
        result = await refresh_stale_cache_entries()
        assert result["status"] == "error"


# ──────────────────────────────────────────────────────────────────────
# warmup_top_params
# ──────────────────────────────────────────────────────────────────────

class TestWarmupTopParams:
    """Tests for top-params warmup task."""

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_cache.get_top_popular_params", new_callable=AsyncMock)
    @patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock)
    async def test_no_popular_params(self, mock_trigger, mock_popular):
        mock_popular.return_value = []
        result = await warmup_top_params()
        assert result["status"] == "no_params"

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_cache.get_top_popular_params", new_callable=AsyncMock)
    @patch("search_cache.trigger_background_revalidation", new_callable=AsyncMock)
    async def test_warmup_success(self, mock_trigger, mock_popular):
        mock_popular.return_value = [{"ufs": ["SP"], "modalidades": None}]
        mock_trigger.return_value = True
        result = await warmup_top_params()
        assert result["warmed"] == 1

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_cache.get_top_popular_params", new_callable=AsyncMock)
    async def test_error_handling(self, mock_popular):
        mock_popular.side_effect = Exception("db error")
        result = await warmup_top_params()
        assert result["status"] == "error"


# ──────────────────────────────────────────────────────────────────────
# _get_prioritized_ufs
# ──────────────────────────────────────────────────────────────────────

class TestGetPrioritizedUfs:
    """Tests for UF priority ordering."""

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_cache.get_popular_ufs_from_sessions", new_callable=AsyncMock)
    @patch("config.DEFAULT_UF_PRIORITY", ["SP", "RJ", "MG"])
    async def test_no_history_uses_default(self, mock_popular):
        mock_popular.return_value = []
        result = await _get_prioritized_ufs(["SP", "RJ", "MG", "BA"])
        assert result[0] == "SP"
        assert "BA" in result

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_cache.get_popular_ufs_from_sessions", new_callable=AsyncMock)
    async def test_popular_ufs_first(self, mock_popular):
        mock_popular.return_value = ["BA", "CE"]
        result = await _get_prioritized_ufs(["SP", "RJ", "BA", "CE"])
        assert result[0] == "BA"
        assert result[1] == "CE"


# ──────────────────────────────────────────────────────────────────────
# Constants sanity checks
# ──────────────────────────────────────────────────────────────────────

class TestConstants:
    """Sanity checks for cron job configuration."""

    @pytest.mark.timeout(30)
    def test_cleanup_interval(self):
        assert CLEANUP_INTERVAL_SECONDS == 6 * 60 * 60

    @pytest.mark.timeout(30)
    def test_session_thresholds(self):
        assert SESSION_STALE_HOURS == 1
        assert SESSION_OLD_DAYS == 7


# ──────────────────────────────────────────────────────────────────────
# _update_pncp_cron_status — extended
# ──────────────────────────────────────────────────────────────────────

class TestPncpRecoveryEpoch:
    """Tests for recovery epoch tracking (CRIT-056)."""

    @pytest.mark.timeout(30)
    def test_epoch_not_incremented_on_healthy_to_healthy(self):
        _update_pncp_cron_status("healthy", 50)
        epoch_before = get_pncp_recovery_epoch()
        _update_pncp_cron_status("healthy", 40)
        assert get_pncp_recovery_epoch() == epoch_before

    @pytest.mark.timeout(30)
    def test_epoch_not_incremented_on_healthy_to_degraded(self):
        _update_pncp_cron_status("healthy", 50)
        epoch_before = get_pncp_recovery_epoch()
        _update_pncp_cron_status("degraded", None)
        assert get_pncp_recovery_epoch() == epoch_before

    @pytest.mark.timeout(30)
    def test_epoch_incremented_on_down_to_healthy(self):
        _update_pncp_cron_status("down", None)
        epoch_before = get_pncp_recovery_epoch()
        _update_pncp_cron_status("healthy", 30)
        assert get_pncp_recovery_epoch() == epoch_before + 1

    @pytest.mark.timeout(30)
    def test_epoch_incremented_on_degraded_to_healthy(self):
        _update_pncp_cron_status("degraded", 500)
        epoch_before = get_pncp_recovery_epoch()
        _update_pncp_cron_status("healthy", 100)
        assert get_pncp_recovery_epoch() == epoch_before + 1

    @pytest.mark.timeout(30)
    def test_multiple_recovery_cycles(self):
        """Multiple degraded -> healthy cycles increment epoch each time."""
        for i in range(3):
            _update_pncp_cron_status("degraded", None)
            _update_pncp_cron_status("healthy", 50)
        assert get_pncp_recovery_epoch() == 3


# ──────────────────────────────────────────────────────────────────────
# _is_cb_or_connection_error — extended
# ──────────────────────────────────────────────────────────────────────

class TestIsCbOrConnectionErrorExtended:
    """Extended error classification tests."""

    @pytest.mark.timeout(30)
    def test_regular_value_error(self):
        assert not _is_cb_or_connection_error(ValueError("bad value"))

    @pytest.mark.timeout(30)
    def test_pgrst205_in_message(self):
        assert _is_cb_or_connection_error(Exception("PGRST205: schema cache"))

    @pytest.mark.timeout(30)
    def test_runtime_error(self):
        assert not _is_cb_or_connection_error(RuntimeError("something"))

    @pytest.mark.timeout(30)
    def test_connect_error_in_message(self):
        assert _is_cb_or_connection_error(Exception("ConnectError: timed out"))


# ──────────────────────────────────────────────────────────────────────
# cleanup_stale_sessions — extended
# ──────────────────────────────────────────────────────────────────────

class TestCleanupStaleSessionsExtended:
    """Extended session cleanup tests."""

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("supabase_client.get_supabase")
    @patch("supabase_client.sb_execute", new_callable=AsyncMock)
    async def test_column_error_fallback(self, mock_exec, mock_get_sb):
        """42703 error triggers created_at-only cleanup."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        call_count = [0]
        async def _exec_side(query):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("42703: column status does not exist")
            result = MagicMock()
            result.data = [{"id": "x"}]
            return result

        mock_exec.side_effect = _exec_side
        result = await cleanup_stale_sessions()
        assert result["marked_stale"] == 0
        assert result["deleted_old"] >= 0
