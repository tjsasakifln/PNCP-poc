"""CRIT-004: Tests for schema contract validation.

Tests AC13-AC16b covering:
- _check_cache_schema() with RPC available
- _check_cache_schema() fallback when RPC fails
- Schema contract validation with missing columns
- Schema contract validation with all columns present
- Schema contract raises SystemExit on critical missing columns
"""
import pytest
from unittest.mock import patch, MagicMock


class TestCacheSchemaCheck:
    """AC13-AC14: Tests for _check_cache_schema() function."""

    @pytest.mark.asyncio
    async def test_check_cache_schema_with_rpc(self):
        """AC13: _check_cache_schema() works when RPC exists and returns columns."""
        from main import _check_cache_schema

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            {"column_name": "id"},
            {"column_name": "params_hash"},
            {"column_name": "results_json"},
            {"column_name": "created_at"},
            {"column_name": "priority"},
            {"column_name": "access_count"},
        ]
        mock_db.rpc.return_value.execute.return_value = mock_result

        with patch("supabase_client.get_supabase", return_value=mock_db):
            # Should not raise
            await _check_cache_schema()

        # Verify RPC was called
        mock_db.rpc.assert_called_once_with(
            "get_table_columns_simple",
            {"p_table_name": "search_results_cache"}
        )

    @pytest.mark.asyncio
    async def test_check_cache_schema_rpc_fallback(self):
        """AC14: _check_cache_schema() does fallback when RPC raises Exception."""
        from main import _check_cache_schema

        mock_db = MagicMock()
        # RPC fails
        mock_db.rpc.return_value.execute.side_effect = Exception("RPC not found")
        # Direct table query succeeds
        mock_db.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock()

        with patch("supabase_client.get_supabase", return_value=mock_db):
            # Should not raise
            await _check_cache_schema()

        # Verify both attempts
        mock_db.rpc.assert_called_once()
        mock_db.table.assert_called_once_with("search_results_cache")

    @pytest.mark.asyncio
    async def test_check_cache_schema_both_fail(self):
        """AC14b: _check_cache_schema() handles both RPC and fallback failures gracefully."""
        from main import _check_cache_schema

        mock_db = MagicMock()
        # Both RPC and direct query fail
        mock_db.rpc.return_value.execute.side_effect = Exception("RPC not found")
        mock_db.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("Table not found")

        with patch("supabase_client.get_supabase", return_value=mock_db):
            # Should not raise (graceful degradation)
            await _check_cache_schema()


class TestSchemaContract:
    """AC15-AC16b: Tests for schema contract validation."""

    def test_schema_contract_detects_missing_columns(self):
        """AC15: Schema contract validation detects missing columns."""
        from schema_contract import validate_schema_contract

        mock_db = MagicMock()

        # Mock RPC responses for each table with missing columns
        def rpc_side_effect(func_name, params):
            table_name = params["p_table_name"]
            mock_result = MagicMock()

            if table_name == "search_sessions":
                # Missing 'status' and 'search_id'
                mock_result.data = [
                    {"column_name": "id"},
                    {"column_name": "user_id"},
                    {"column_name": "started_at"},
                    {"column_name": "completed_at"},
                    {"column_name": "created_at"},
                ]
            elif table_name == "search_results_cache":
                # Missing 'results_json'
                mock_result.data = [
                    {"column_name": "id"},
                    {"column_name": "params_hash"},
                    {"column_name": "created_at"},
                ]
            elif table_name == "profiles":
                # All columns present
                mock_result.data = [
                    {"column_name": "id"},
                    {"column_name": "user_id"},
                    {"column_name": "plan_type"},
                    {"column_name": "email"},
                ]

            mock_execute = MagicMock()
            mock_execute.execute.return_value = mock_result
            return mock_execute

        mock_db.rpc.side_effect = rpc_side_effect

        passed, missing = validate_schema_contract(mock_db)

        assert not passed, "Should detect missing columns"
        assert "search_sessions.status" in missing
        assert "search_sessions.search_id" in missing
        assert "search_results_cache.results_json" in missing
        assert len(missing) == 3

    def test_schema_contract_all_columns_present(self):
        """AC16: Schema contract with all columns present passes."""
        from schema_contract import validate_schema_contract

        mock_db = MagicMock()

        # Mock RPC responses for each table with ALL required columns
        def rpc_side_effect(func_name, params):
            table_name = params["p_table_name"]
            mock_result = MagicMock()

            if table_name == "search_sessions":
                mock_result.data = [
                    {"column_name": "id"},
                    {"column_name": "user_id"},
                    {"column_name": "search_id"},
                    {"column_name": "status"},
                    {"column_name": "started_at"},
                    {"column_name": "completed_at"},
                    {"column_name": "created_at"},
                ]
            elif table_name == "search_results_cache":
                mock_result.data = [
                    {"column_name": "id"},
                    {"column_name": "params_hash"},
                    {"column_name": "results_json"},
                    {"column_name": "created_at"},
                ]
            elif table_name == "profiles":
                mock_result.data = [
                    {"column_name": "id"},
                    {"column_name": "user_id"},
                    {"column_name": "plan_type"},
                    {"column_name": "email"},
                ]

            mock_execute = MagicMock()
            mock_execute.execute.return_value = mock_result
            return mock_execute

        mock_db.rpc.side_effect = rpc_side_effect

        passed, missing = validate_schema_contract(mock_db)

        assert passed, "Should pass with all required columns present"
        assert len(missing) == 0

    def test_schema_contract_rpc_unavailable_fallback(self):
        """AC16a: Schema contract handles RPC unavailable with graceful fallback."""
        from schema_contract import validate_schema_contract

        mock_db = MagicMock()

        # RPC fails, but table query succeeds
        mock_db.rpc.side_effect = Exception("RPC not available")
        mock_db.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock()

        # Should not crash, but also can't validate columns
        passed, missing = validate_schema_contract(mock_db)

        # When RPC unavailable, we skip validation (continue)
        # So we expect passed=True, missing=[]
        assert passed, "Should pass when RPC unavailable (graceful degradation)"
        assert len(missing) == 0

    def test_schema_contract_table_not_exists(self):
        """AC16b: Schema contract detects when entire table is missing."""
        from schema_contract import validate_schema_contract

        mock_db = MagicMock()

        # All queries fail (tables don't exist)
        mock_db.rpc.side_effect = Exception("Table not found")
        mock_db.table.side_effect = Exception("Table not found")

        passed, missing = validate_schema_contract(mock_db)

        assert not passed, "Should fail when tables don't exist"
        # All columns from all 3 tables should be missing
        assert len(missing) > 0
        assert any("search_sessions." in m for m in missing)
        assert any("search_results_cache." in m for m in missing)
        assert any("profiles." in m for m in missing)


class TestStartupSchemaValidation:
    """AC16b: Test that startup validation raises SystemExit on schema violation."""

    @pytest.mark.asyncio
    async def test_startup_blocks_on_missing_critical_columns(self):
        """AC16b: Schema contract with missing critical column raises SystemExit."""
        from main import lifespan
        from fastapi import FastAPI

        app = FastAPI()

        # Mock the schema validation to return failure
        with patch("schema_contract.validate_schema_contract") as mock_validate:
            mock_validate.return_value = (False, ["search_sessions.status"])

            with patch("supabase_client.get_supabase"):
                # Mock all other startup functions to avoid side effects
                with patch("main.validate_env_vars"), \
                     patch("main.startup_redis"), \
                     patch("job_queue.get_arq_pool"), \
                     patch("cron_jobs.start_cache_cleanup_task"), \
                     patch("cron_jobs.start_session_cleanup_task"), \
                     patch("main._check_cache_schema"), \
                     patch("search_state_manager.recover_stale_searches"), \
                     patch("main._log_registered_routes"), \
                     patch("telemetry.init_tracing"), \
                     patch("telemetry.shutdown_tracing"):

                    # lifespan should raise SystemExit(1)
                    with pytest.raises(SystemExit) as exc_info:
                        async with lifespan(app):
                            pass

                    assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_startup_succeeds_with_valid_schema(self):
        """AC16c: Schema contract validation allows startup when all columns present."""
        from main import lifespan
        from fastapi import FastAPI
        import asyncio

        app = FastAPI()

        # Mock the schema validation to return success
        with patch("schema_contract.validate_schema_contract") as mock_validate:
            mock_validate.return_value = (True, [])

            with patch("supabase_client.get_supabase"):
                # Mock all other startup functions
                with patch("main.validate_env_vars"), \
                     patch("main.startup_redis", new_callable=lambda: lambda: asyncio.sleep(0)), \
                     patch("job_queue.get_arq_pool", new_callable=lambda: lambda: asyncio.sleep(0)), \
                     patch("cron_jobs.start_cache_cleanup_task", return_value=asyncio.create_task(asyncio.sleep(0))), \
                     patch("cron_jobs.start_session_cleanup_task", return_value=asyncio.create_task(asyncio.sleep(0))), \
                     patch("main._check_cache_schema", new_callable=lambda: lambda: asyncio.sleep(0)), \
                     patch("search_state_manager.recover_stale_searches", new_callable=lambda: lambda max_age_minutes: asyncio.sleep(0)), \
                     patch("main._log_registered_routes"), \
                     patch("telemetry.init_tracing"), \
                     patch("telemetry.shutdown_tracing"), \
                     patch("main._mark_inflight_sessions_timed_out", new_callable=lambda: lambda: asyncio.sleep(0)):

                    # Should not raise
                    async with lifespan(app):
                        pass  # Startup succeeded
