"""STORY-362: Extend Result TTLs & Add Supabase L3 Persistence — tests.

Tests AC1-AC12:
- AC1: In-memory TTL increased to 3600s (1h)
- AC2: Redis TTL increased to 14400s (4h)
- AC3: .env.example documented (manual verification)
- AC4: Migration creates search_results_store (migration file exists)
- AC5: Results persisted to Supabase L3 (fire-and-forget)
- AC6: get_background_results_async falls back to Supabase L3
- AC7: Cron job cleans expired results
- AC8: PDF works 2h after search (L2 active)
- AC9: PDF works 6h after search (L3 Supabase active)
- AC10: Results persist after backend restart (L2/L3)
- AC11: No regression in existing tests
- AC12: RLS prevents cross-user access
"""

import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import sys
if "openai" not in sys.modules:
    sys.modules["openai"] = MagicMock()
if "stripe" not in sys.modules:
    sys.modules["stripe"] = MagicMock()


# ============================================================================
# Helpers
# ============================================================================


def _make_response(**overrides):
    """Create a mock BuscaResponse-like namespace."""
    defaults = {
        "resumo": "Test summary",
        "licitacoes": [],
        "total_raw": 10,
        "total_filtrado": 5,
        "setor": "software",
        "ufs": ["SP"],
    }
    defaults.update(overrides)
    ns = SimpleNamespace(**defaults)
    ns.model_dump = lambda mode="json": defaults
    return ns


def _make_sb_result(data=None):
    """Create a mock Supabase query result."""
    return SimpleNamespace(data=data or [])


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset in-memory caches."""
    from routes.search import _background_results, _active_background_tasks
    _background_results.clear()
    _active_background_tasks.clear()
    yield


@pytest.fixture
def mock_supabase():
    """Mock Supabase client with chainable table calls."""
    mock_db = MagicMock()
    mock_table = MagicMock()
    mock_db.table.return_value = mock_table
    mock_table.upsert.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.gt.return_value = mock_table
    mock_table.lt.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.delete.return_value = mock_table
    return mock_db


# ============================================================================
# AC1: In-memory TTL = 3600s (1h)
# ============================================================================


class TestAC1InMemoryTTL:
    def test_results_ttl_is_3600(self):
        """AC1: _RESULTS_TTL should be 3600 (1 hour)."""
        from routes.search import _RESULTS_TTL
        assert _RESULTS_TTL == 3600

    def test_results_accessible_within_ttl(self):
        """AC1: Results accessible before TTL expiry."""
        from routes.search import store_background_results, get_background_results
        resp = _make_response()
        store_background_results("test-ac1", resp)
        result = get_background_results("test-ac1")
        assert result is not None

    def test_results_expired_after_ttl(self):
        """AC1: Results not accessible after TTL expiry."""
        from routes.search import store_background_results, get_background_results, _background_results
        resp = _make_response()
        store_background_results("test-ac1-exp", resp)
        # Simulate TTL expiry
        _background_results["test-ac1-exp"]["stored_at"] = time.time() - 3601
        result = get_background_results("test-ac1-exp")
        assert result is None


# ============================================================================
# AC2: Redis TTL = 14400s (4h)
# ============================================================================


class TestAC2RedisTTL:
    def test_redis_ttl_config(self):
        """AC2: RESULTS_REDIS_TTL default should be 14400 (4 hours)."""
        from config import RESULTS_REDIS_TTL
        assert RESULTS_REDIS_TTL == 14400

    @pytest.mark.asyncio
    async def test_redis_setex_uses_14400(self):
        """AC2: _persist_results_to_redis uses 14400s TTL."""
        from routes.search import _persist_results_to_redis

        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            await _persist_results_to_redis("test-ac2", _make_response())

            call_args = mock_redis.setex.call_args
            assert call_args[0][1] == 14400


# ============================================================================
# AC5: Supabase L3 persist (fire-and-forget)
# ============================================================================


class TestAC5SupabasePersist:
    @pytest.mark.asyncio
    async def test_persist_to_supabase_success(self, mock_supabase):
        """AC5: Results persisted to Supabase with correct data."""
        from routes.search import _persist_results_to_supabase

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", new_callable=AsyncMock) as mock_exec:
            await _persist_results_to_supabase("search-l3", "user-123", _make_response())

            mock_exec.assert_called_once()
            mock_supabase.table.assert_called_with("search_results_store")

    @pytest.mark.asyncio
    async def test_persist_to_supabase_stores_metadata(self, mock_supabase):
        """AC5: Supabase record includes sector, ufs, total_filtered."""
        from routes.search import _persist_results_to_supabase

        captured_data = {}

        async def capture_upsert(query):
            # Extract the upsert data from the mock chain
            return _make_sb_result()

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", new_callable=AsyncMock, side_effect=capture_upsert):
            await _persist_results_to_supabase(
                "search-meta", "user-456",
                _make_response(setor="engenharia", ufs=["SP", "RJ"], total_filtrado=42)
            )

            # Verify upsert was called with correct table
            mock_supabase.table.assert_called_with("search_results_store")
            upsert_call = mock_supabase.table().upsert.call_args
            data = upsert_call[0][0]
            assert data["search_id"] == "search-meta"
            assert data["user_id"] == "user-456"
            assert data["sector"] == "engenharia"
            assert data["ufs"] == ["SP", "RJ"]
            assert data["total_filtered"] == 42
            assert "expires_at" in data

    @pytest.mark.asyncio
    async def test_persist_to_supabase_no_crash_on_error(self, mock_supabase):
        """AC5: Fire-and-forget — errors logged, never raised."""
        from routes.search import _persist_results_to_supabase

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", new_callable=AsyncMock, side_effect=Exception("DB error")):
            # Should not raise
            await _persist_results_to_supabase("search-err", "user-x", _make_response())

    @pytest.mark.asyncio
    async def test_persist_to_supabase_no_crash_when_unavailable(self):
        """AC5: No crash when Supabase is unavailable."""
        from routes.search import _persist_results_to_supabase

        with patch("supabase_client.get_supabase", return_value=None):
            await _persist_results_to_supabase("search-no-db", "user-x", _make_response())


# ============================================================================
# AC6: get_background_results_async falls back to Supabase L3
# ============================================================================


class TestAC6L3Fallback:
    @pytest.mark.asyncio
    async def test_fallback_l1_to_l3(self):
        """AC6: When L1, L2, and ARQ miss, L3 (Supabase) is checked."""
        from routes.search import get_background_results_async

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        l3_data = {"resumo": "From L3", "licitacoes": [], "total_filtrado": 3}

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search.get_background_results", return_value=None), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None), \
             patch("routes.search._get_results_from_supabase", new_callable=AsyncMock, return_value=l3_data):
            result = await get_background_results_async("search-l3-fallback")

            assert result is not None
            assert result["resumo"] == "From L3"
            assert result["total_filtrado"] == 3

    @pytest.mark.asyncio
    async def test_l2_takes_priority_over_l3(self):
        """AC6: L2 (Redis) data returned before reaching L3."""
        from routes.search import get_background_results_async

        mock_redis = AsyncMock()
        redis_data = json.dumps({"resumo": "From L2", "licitacoes": [], "total_filtrado": 7})
        mock_redis.get = AsyncMock(return_value=redis_data)

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search.get_background_results", return_value=None), \
             patch("routes.search._get_results_from_supabase", new_callable=AsyncMock) as mock_l3:
            result = await get_background_results_async("search-l2-priority")

            assert result is not None
            assert result["total_filtrado"] == 7
            mock_l3.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_when_all_miss(self):
        """AC6: Returns None when all layers miss."""
        from routes.search import get_background_results_async

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search.get_background_results", return_value=None), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None), \
             patch("routes.search._get_results_from_supabase", new_callable=AsyncMock, return_value=None):
            result = await get_background_results_async("search-all-miss")
            assert result is None


# ============================================================================
# AC6: _get_results_from_supabase
# ============================================================================


class TestGetResultsFromSupabase:
    @pytest.mark.asyncio
    async def test_returns_results_when_found(self, mock_supabase):
        """AC6: Returns results dict from Supabase."""
        from routes.search import _get_results_from_supabase

        expected = {"resumo": "Found", "licitacoes": [], "total_filtrado": 10}
        sb_result = _make_sb_result([{"results": expected}])

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", new_callable=AsyncMock, return_value=sb_result):
            result = await _get_results_from_supabase("search-found")
            assert result == expected

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, mock_supabase):
        """AC6: Returns None when no results in Supabase."""
        from routes.search import _get_results_from_supabase

        sb_result = _make_sb_result([])

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", new_callable=AsyncMock, return_value=sb_result):
            result = await _get_results_from_supabase("search-missing")
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_error(self, mock_supabase):
        """AC6: Returns None (no crash) on Supabase error."""
        from routes.search import _get_results_from_supabase

        with patch("supabase_client.get_supabase", return_value=mock_supabase), \
             patch("supabase_client.sb_execute", new_callable=AsyncMock, side_effect=Exception("DB down")):
            result = await _get_results_from_supabase("search-error")
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_supabase_unavailable(self):
        """AC6: Returns None when Supabase is unavailable."""
        from routes.search import _get_results_from_supabase

        with patch("supabase_client.get_supabase", return_value=None):
            result = await _get_results_from_supabase("search-no-db")
            assert result is None


# ============================================================================
# AC7: Cron job cleans expired results
# ============================================================================


class TestAC7CronCleanup:
    @pytest.mark.asyncio
    async def test_cleanup_expired_results(self):
        """AC7: cleanup_expired_results deletes expired rows."""
        from cron_jobs import cleanup_expired_results

        mock_db = MagicMock()
        mock_table = MagicMock()
        mock_db.table.return_value = mock_table
        mock_table.delete.return_value = mock_table
        mock_table.lt.return_value = mock_table

        deleted_data = [{"search_id": "expired-1"}, {"search_id": "expired-2"}]
        sb_result = _make_sb_result(deleted_data)

        with patch("supabase_client.get_supabase", return_value=mock_db), \
             patch("supabase_client.sb_execute", new_callable=AsyncMock, return_value=sb_result):
            result = await cleanup_expired_results()

            assert result["deleted"] == 2
            mock_db.table.assert_called_with("search_results_store")

    @pytest.mark.asyncio
    async def test_cleanup_no_crash_on_error(self):
        """AC7: Cleanup handles errors gracefully."""
        from cron_jobs import cleanup_expired_results

        with patch("supabase_client.get_supabase", side_effect=Exception("DB error")):
            result = await cleanup_expired_results()
            assert result["deleted"] == 0
            assert "error" in result

    def test_cleanup_interval_is_6h(self):
        """AC7: Cleanup interval is 6 hours."""
        from cron_jobs import RESULTS_CLEANUP_INTERVAL_SECONDS
        assert RESULTS_CLEANUP_INTERVAL_SECONDS == 6 * 60 * 60


# ============================================================================
# AC8/AC9/AC10: Integration-level TTL verification
# ============================================================================


class TestAC8AC9AC10Integration:
    @pytest.mark.asyncio
    async def test_ac8_pdf_after_2h_l2_active(self):
        """AC8: Results available 2h after search (L1 expired, L2 active)."""
        from routes.search import (
            store_background_results, _background_results,
            get_background_results_async,
        )

        resp = _make_response(total_filtrado=15)
        store_background_results("ac8-2h", resp)

        # Simulate L1 expired (2h > 1h TTL)
        _background_results["ac8-2h"]["stored_at"] = time.time() - 7200

        # L2 (Redis) still has it (2h < 4h TTL)
        redis_data = json.dumps({"resumo": "L2 active", "licitacoes": [], "total_filtrado": 15})
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=redis_data)

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            result = await get_background_results_async("ac8-2h")
            assert result is not None
            assert result["total_filtrado"] == 15

    @pytest.mark.asyncio
    async def test_ac9_pdf_after_6h_l3_active(self):
        """AC9: Results available 6h after search (L1/L2 expired, L3 active)."""
        from routes.search import get_background_results_async

        # L1 and L2 both expired
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        l3_data = {"resumo": "L3 active", "licitacoes": [], "total_filtrado": 15}

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search.get_background_results", return_value=None), \
             patch("job_queue.get_job_result", new_callable=AsyncMock, return_value=None), \
             patch("routes.search._get_results_from_supabase", new_callable=AsyncMock, return_value=l3_data):
            result = await get_background_results_async("ac9-6h")
            assert result is not None
            assert result["total_filtrado"] == 15

    @pytest.mark.asyncio
    async def test_ac10_results_after_restart(self):
        """AC10: Results accessible after backend restart (L1 empty, L2/L3 available)."""
        from routes.search import get_background_results_async

        # After restart, L1 is empty (in-memory wiped)
        mock_redis = AsyncMock()
        redis_data = json.dumps({"resumo": "Post-restart", "licitacoes": [], "total_filtrado": 8})
        mock_redis.get = AsyncMock(return_value=redis_data)

        with patch("routes.search.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis), \
             patch("routes.search.get_background_results", return_value=None):
            result = await get_background_results_async("ac10-restart")
            assert result is not None
            assert result["total_filtrado"] == 8


# ============================================================================
# AC4: Migration file exists
# ============================================================================


class TestAC4Migration:
    def test_migration_file_exists(self):
        """AC4: Migration file for search_results_store exists."""
        import os
        migration_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "supabase", "migrations"
        )
        migration_files = os.listdir(migration_dir) if os.path.exists(migration_dir) else []
        matching = [f for f in migration_files if "search_results_store" in f]
        assert len(matching) >= 1, "Migration file for search_results_store not found"


# ============================================================================
# AC3: .env.example documentation
# ============================================================================


class TestAC3Documentation:
    def test_env_example_documents_ttls(self):
        """AC3: .env.example contains RESULTS_REDIS_TTL and RESULTS_SUPABASE_TTL_HOURS."""
        import os
        env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env.example")
        with open(env_path, "r") as f:
            content = f.read()
        assert "RESULTS_REDIS_TTL" in content
        assert "RESULTS_SUPABASE_TTL_HOURS" in content
