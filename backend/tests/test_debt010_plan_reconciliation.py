"""DEBT-010 DB-015/DB-031: Plan reconciliation and table size monitoring tests."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from types import SimpleNamespace


def _make_response(data):
    """Create a Supabase-like response object."""
    return SimpleNamespace(data=data)


# ============================================================================
# Shared fixtures
# ============================================================================


@pytest.fixture
def mock_redis_acquired():
    """Mock Redis client where the lock IS acquired (set returns truthy)."""
    redis = AsyncMock()
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def mock_redis_held():
    """Mock Redis client where the lock is already held (set returns falsy)."""
    redis = AsyncMock()
    redis.set = AsyncMock(return_value=None)  # nx=True + key exists → None
    redis.delete = AsyncMock()
    return redis


@pytest.fixture
def mock_supabase():
    """Mock Supabase client (only used as a placeholder — sb_execute is patched separately)."""
    return MagicMock()


# ============================================================================
# TestPlanReconciliation — DEBT-010 DB-015
# ============================================================================


class TestPlanReconciliation:
    """DEBT-010 DB-015: Plan type drift detection between profiles and user_subscriptions."""

    @pytest.mark.asyncio
    async def test_no_drift(self, mock_supabase, mock_redis_acquired):
        """No drift when profiles match subscriptions — completed with drift_count=0."""
        profiles_data = [
            {"id": "user-aaaa-1111", "plan_type": "smartlic_pro"},
            {"id": "user-bbbb-2222", "plan_type": "free_trial"},
        ]
        subs_data = [
            {"user_id": "user-aaaa-1111", "plan_id": "smartlic_pro"},
        ]

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        mock_runs = MagicMock()
        mock_drift = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=mock_redis_acquired), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", mock_runs), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["status"] == "completed"
        assert result["drift_count"] == 0
        assert result["total_profiles"] == 2
        assert result["total_active_subs"] == 1
        mock_drift.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_detects_plan_type_mismatch(self, mock_supabase, mock_redis_acquired):
        """Detects when profile plan_type != subscription plan_id (profiles_stale)."""
        profiles_data = [
            {"id": "user-aaaa-1111", "plan_type": "free_trial"},  # Should be smartlic_pro
        ]
        subs_data = [
            {"user_id": "user-aaaa-1111", "plan_id": "smartlic_pro"},
        ]

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        mock_runs = MagicMock()
        mock_drift = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=mock_redis_acquired), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", mock_runs), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["status"] == "completed"
        assert result["drift_count"] == 1
        assert result["drift_details"][0]["direction"] == "profiles_stale"
        assert result["drift_details"][0]["profile_plan"] == "free_trial"
        assert result["drift_details"][0]["sub_plan"] == "smartlic_pro"
        mock_drift.labels.assert_called_once_with(direction="profiles_stale")
        mock_drift.labels.return_value.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_detects_orphan_profile(self, mock_supabase, mock_redis_acquired):
        """Detects paid profile with no active subscription (orphan_profile)."""
        profiles_data = [
            {"id": "user-aaaa-1111", "plan_type": "smartlic_pro"},
        ]
        subs_data = []  # No active subscriptions

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        mock_runs = MagicMock()
        mock_drift = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=mock_redis_acquired), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", mock_runs), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["status"] == "completed"
        assert result["drift_count"] == 1
        assert result["drift_details"][0]["direction"] == "orphan_profile"
        assert result["drift_details"][0]["sub_plan"] is None
        mock_drift.labels.assert_called_once_with(direction="orphan_profile")
        mock_drift.labels.return_value.inc.assert_called_once()

    @pytest.mark.asyncio
    async def test_free_trial_without_subscription_is_ok(self, mock_supabase, mock_redis_acquired):
        """free_trial and cancelled users without subscription are NOT flagged as orphans."""
        profiles_data = [
            {"id": "user-aaaa-1111", "plan_type": "free_trial"},
            {"id": "user-bbbb-2222", "plan_type": "cancelled"},
        ]
        subs_data = []

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        mock_runs = MagicMock()
        mock_drift = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=mock_redis_acquired), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", mock_runs), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["status"] == "completed"
        assert result["drift_count"] == 0
        mock_drift.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_none_plan_type_without_subscription_is_ok(self, mock_supabase, mock_redis_acquired):
        """Profiles with None/empty plan_type without subscription are NOT flagged."""
        profiles_data = [
            {"id": "user-aaaa-1111", "plan_type": None},
            {"id": "user-bbbb-2222", "plan_type": ""},
        ]
        subs_data = []

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        mock_runs = MagicMock()
        mock_drift = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=mock_redis_acquired), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", mock_runs), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["status"] == "completed"
        assert result["drift_count"] == 0

    @pytest.mark.asyncio
    async def test_multiple_drifts_detected(self, mock_supabase, mock_redis_acquired):
        """Multiple drifts are all captured and reported."""
        profiles_data = [
            {"id": "user-aaaa-1111", "plan_type": "free_trial"},   # stale (has sub)
            {"id": "user-bbbb-2222", "plan_type": "smartlic_pro"}, # orphan (no sub)
            {"id": "user-cccc-3333", "plan_type": "smartlic_pro"}, # OK (matches sub)
        ]
        subs_data = [
            {"user_id": "user-aaaa-1111", "plan_id": "smartlic_pro"},
            {"user_id": "user-cccc-3333", "plan_id": "smartlic_pro"},
        ]

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        mock_runs = MagicMock()
        mock_drift = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=mock_redis_acquired), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", mock_runs), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["status"] == "completed"
        assert result["drift_count"] == 2
        directions = {d["direction"] for d in result["drift_details"]}
        assert "profiles_stale" in directions
        assert "orphan_profile" in directions
        assert mock_drift.labels.call_count == 2

    @pytest.mark.asyncio
    async def test_lock_prevents_concurrent_run(self, mock_supabase, mock_redis_held):
        """When lock cannot be acquired, returns skipped status immediately."""
        mock_runs = MagicMock()
        mock_drift = MagicMock()

        with patch("redis_pool.get_redis_pool", return_value=mock_redis_held), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", mock_runs), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["status"] == "skipped"
        assert result["reason"] == "lock_held"
        # PLAN_RECONCILIATION_RUNS.inc() is called before the lock check
        mock_runs.inc.assert_called_once()
        # No Supabase calls should happen
        mock_drift.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_redis_none_proceeds_without_lock(self, mock_supabase):
        """When Redis returns None, proceeds without lock (graceful degradation)."""
        profiles_data = [{"id": "user-aaaa-1111", "plan_type": "free_trial"}]
        subs_data = []

        redis_none = AsyncMock()
        redis_none.set = AsyncMock(return_value=True)
        redis_none.delete = AsyncMock()

        # Simulate get_redis_pool returning None (no Redis available)
        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        mock_runs = MagicMock()
        mock_drift = MagicMock()

        # When Redis pool returns None, the redis.set check is skipped
        # (redis is None → if redis: is False → lock_acquired stays False → proceeds)
        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=None), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", mock_runs), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        # Should complete (lock_acquired=False but lock check passed since redis is None)
        assert result["status"] == "completed"
        assert result["drift_count"] == 0

    @pytest.mark.asyncio
    async def test_redis_lock_exception_proceeds(self, mock_supabase):
        """Redis exception during lock acquisition → proceeds (fail-open for lock)."""
        profiles_data = [{"id": "user-aaaa-1111", "plan_type": "free_trial"}]
        subs_data = []

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        async def raise_redis_error():
            raise ConnectionError("Redis connection refused")

        mock_runs = MagicMock()
        mock_drift = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", side_effect=raise_redis_error), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", mock_runs), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        # Should still complete — Redis failure sets lock_acquired=True and proceeds
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_supabase_error_returns_error_status(self, mock_supabase, mock_redis_acquired):
        """Supabase error returns error status and error message, doesn't crash."""
        async def mock_sb_execute(query):
            raise Exception("Connection refused")

        mock_runs = MagicMock()
        mock_drift = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=mock_redis_acquired), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", mock_runs), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["status"] == "error"
        assert "Connection refused" in result["error"]

    @pytest.mark.asyncio
    async def test_result_contains_checked_at_timestamp(self, mock_supabase, mock_redis_acquired):
        """Result includes checked_at ISO timestamp."""
        profiles_data = []
        subs_data = []

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=mock_redis_acquired), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", MagicMock()), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", MagicMock()):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["status"] == "completed"
        assert "checked_at" in result
        # Should be a valid ISO format string
        assert "T" in result["checked_at"]

    @pytest.mark.asyncio
    async def test_drift_details_capped_at_20(self, mock_supabase, mock_redis_acquired):
        """drift_details list is capped at 20 entries even if more drifts exist."""
        # Create 25 orphan profiles
        profiles_data = [
            {"id": f"user-{i:04d}-aaaa", "plan_type": "smartlic_pro"}
            for i in range(25)
        ]
        subs_data = []

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        mock_drift = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=mock_redis_acquired), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", MagicMock()), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", mock_drift):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["status"] == "completed"
        assert result["drift_count"] == 25
        # drift_details is capped at 20 in the response
        assert len(result["drift_details"]) == 20
        # But all 25 are counted by the metric
        assert mock_drift.labels.call_count == 25

    @pytest.mark.asyncio
    async def test_user_id_truncated_in_drift_details(self, mock_supabase, mock_redis_acquired):
        """User IDs in drift_details are truncated to 8 chars + '...' for privacy."""
        profiles_data = [
            {"id": "user-aaaa-1111-bbbb", "plan_type": "smartlic_pro"},
        ]
        subs_data = []

        call_count = 0

        async def mock_sb_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _make_response(profiles_data)
            return _make_response(subs_data)

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", side_effect=mock_sb_execute), \
             patch("redis_pool.get_redis_pool", return_value=mock_redis_acquired), \
             patch("metrics.PLAN_RECONCILIATION_RUNS", MagicMock()), \
             patch("metrics.PLAN_RECONCILIATION_DRIFT", MagicMock()):
            from cron_jobs import run_plan_reconciliation
            result = await run_plan_reconciliation()

        assert result["drift_count"] == 1
        user_id_logged = result["drift_details"][0]["user_id"]
        assert user_id_logged == "user-aaa..."
        assert len(user_id_logged) == 11  # 8 chars + "..."


# ============================================================================
# TestTableSizeMetrics — DEBT-010 DB-031
# ============================================================================


class TestTableSizeMetrics:
    """DEBT-010 DB-031: Table size Prometheus gauge update."""

    @pytest.mark.asyncio
    async def test_updates_metrics_for_all_tables(self, mock_supabase):
        """Updates gauge for every table in _MONITORED_TABLES."""
        async def mock_sb_execute_direct(query):
            return _make_response(12345678)

        mock_gauge = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute_direct", side_effect=mock_sb_execute_direct), \
             patch("metrics.DB_TABLE_SIZE_BYTES", mock_gauge):
            from cron_jobs import update_table_size_metrics, _MONITORED_TABLES
            result = await update_table_size_metrics()

        assert result["status"] == "ok"
        assert len(result["sizes"]) == len(_MONITORED_TABLES)
        # Every monitored table should have a gauge update
        assert mock_gauge.labels.call_count == len(_MONITORED_TABLES)
        # All sizes should be 12345678
        for table_name, size in result["sizes"].items():
            assert size == 12345678

    @pytest.mark.asyncio
    async def test_handles_rpc_failure_per_table_gracefully(self, mock_supabase):
        """RPC failure for individual tables sets size to -1 without crashing."""
        async def mock_sb_execute_direct(query):
            raise Exception("RPC not found")

        mock_gauge = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute_direct", side_effect=mock_sb_execute_direct), \
             patch("metrics.DB_TABLE_SIZE_BYTES", mock_gauge):
            from cron_jobs import update_table_size_metrics, _MONITORED_TABLES
            result = await update_table_size_metrics()

        assert result["status"] == "ok"
        assert len(result["sizes"]) == len(_MONITORED_TABLES)
        # All tables fail → size is -1, gauge.labels is NOT called for failures
        for table_name, size in result["sizes"].items():
            assert size == -1
        # Gauge should not be updated for failed tables
        mock_gauge.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_failure_mixed_results(self, mock_supabase):
        """Some tables succeed, others fail — both cases handled per-table.

        Uses call-order to simulate: first call succeeds, second call fails.
        """
        from cron_jobs import _MONITORED_TABLES

        first_table = _MONITORED_TABLES[0]
        second_table = _MONITORED_TABLES[1]

        call_count = 0

        async def mock_sb_execute_direct(query):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Table not found")
            return _make_response(99999)

        mock_gauge = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute_direct", side_effect=mock_sb_execute_direct), \
             patch("metrics.DB_TABLE_SIZE_BYTES", mock_gauge):
            from cron_jobs import update_table_size_metrics
            result = await update_table_size_metrics()

        assert result["status"] == "ok"
        # First table succeeds
        assert result["sizes"][first_table] == 99999
        # Second table fails → -1
        assert result["sizes"][second_table] == -1
        # Remaining tables succeed (calls 3+)
        for table in _MONITORED_TABLES[2:]:
            assert result["sizes"][table] == 99999

    @pytest.mark.asyncio
    async def test_list_response_handled(self, mock_supabase):
        """RPC returning a list → first element used as size."""
        async def mock_sb_execute_direct(query):
            return _make_response([8192])  # list format

        mock_gauge = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute_direct", side_effect=mock_sb_execute_direct), \
             patch("metrics.DB_TABLE_SIZE_BYTES", mock_gauge):
            from cron_jobs import update_table_size_metrics
            result = await update_table_size_metrics()

        assert result["status"] == "ok"
        for table_name, size in result["sizes"].items():
            assert size == 8192

    @pytest.mark.asyncio
    async def test_none_data_response_produces_zero(self, mock_supabase):
        """RPC returning data=None is handled gracefully (size=0)."""
        async def mock_sb_execute_direct(query):
            return _make_response(None)

        mock_gauge = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute_direct", side_effect=mock_sb_execute_direct), \
             patch("metrics.DB_TABLE_SIZE_BYTES", mock_gauge):
            from cron_jobs import update_table_size_metrics
            result = await update_table_size_metrics()

        # When result.data is None, the gauge is NOT set (condition: `if result and result.data is not None`)
        assert result["status"] == "ok"
        # Gauge not updated for None data rows
        mock_gauge.labels.assert_not_called()

    @pytest.mark.asyncio
    async def test_monitored_tables_constant_has_expected_tables(self):
        """_MONITORED_TABLES includes the JSONB-heavy tables from DEBT-010 spec."""
        from cron_jobs import _MONITORED_TABLES

        expected_tables = {
            "search_results_cache",
            "search_results_store",
            "search_sessions",
            "stripe_webhook_events",
            "profiles",
            "user_subscriptions",
        }
        for table in expected_tables:
            assert table in _MONITORED_TABLES, f"Expected table '{table}' in _MONITORED_TABLES"

    @pytest.mark.asyncio
    async def test_outer_supabase_error_returns_error_status(self, mock_supabase):
        """Top-level Supabase error (e.g., get_supabase() fails) returns error status."""
        def raise_on_get():
            raise Exception("Supabase unavailable")

        with patch("supabase_client.get_supabase", side_effect=raise_on_get), \
             patch("metrics.DB_TABLE_SIZE_BYTES", MagicMock()):
            from cron_jobs import update_table_size_metrics
            result = await update_table_size_metrics()

        assert result["status"] == "error"
        assert "Supabase unavailable" in result["error"]
