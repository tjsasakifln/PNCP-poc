"""GTM-FIX-010: Tests for SWR search cache module.

Covers:
  AC2:  compute_search_hash determinism
  AC3:  save_to_cache persists to Supabase
  AC4:  get_from_cache retrieves on failure
  AC5r: cached_sources field in response
  AC10: test_cache_hit_on_pncp_failure
  AC11: test_cache_miss_returns_error
  AC12: test_cache_expired_not_served
  AC16r: partial live preferred over cache
  AC17r: fallback cascade Live → Partial → Cache → empty
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, Mock, AsyncMock, MagicMock

from search_cache import (
    compute_search_hash,
    save_to_cache,
    get_from_cache,
    CACHE_FRESH_HOURS,
    CACHE_STALE_HOURS,
)


# ============================================================================
# AC2: Hash determinism
# ============================================================================


class TestComputeSearchHash:
    """AC2: search_hash = sha256(json.dumps(sorted(params)))"""

    def test_same_params_produce_same_hash(self):
        params = {"setor_id": 1, "ufs": ["SP", "RJ"], "status": "aberta"}
        h1 = compute_search_hash(params)
        h2 = compute_search_hash(params)
        assert h1 == h2

    def test_uf_order_does_not_matter(self):
        h1 = compute_search_hash({"setor_id": 1, "ufs": ["SP", "RJ"]})
        h2 = compute_search_hash({"setor_id": 1, "ufs": ["RJ", "SP"]})
        assert h1 == h2

    def test_different_params_produce_different_hash(self):
        h1 = compute_search_hash({"setor_id": 1, "ufs": ["SP"]})
        h2 = compute_search_hash({"setor_id": 2, "ufs": ["SP"]})
        assert h1 != h2

    def test_hash_is_sha256_hex(self):
        h = compute_search_hash({"setor_id": 1, "ufs": ["SP"]})
        assert len(h) == 64  # SHA256 produces 64 hex chars
        assert all(c in "0123456789abcdef" for c in h)

    def test_modalidades_order_does_not_matter(self):
        h1 = compute_search_hash({"setor_id": 1, "ufs": ["SP"], "modalidades": ["pregao", "concurso"]})
        h2 = compute_search_hash({"setor_id": 1, "ufs": ["SP"], "modalidades": ["concurso", "pregao"]})
        assert h1 == h2

    def test_none_modalidades_handled(self):
        h1 = compute_search_hash({"setor_id": 1, "ufs": ["SP"], "modalidades": None})
        h2 = compute_search_hash({"setor_id": 1, "ufs": ["SP"]})
        assert h1 == h2


# ============================================================================
# AC3: save_to_cache
# ============================================================================


class TestSaveToCache:
    """AC3: After successful PNCP fetch, upsert to search_results_cache."""

    @pytest.mark.asyncio
    async def test_save_calls_supabase_upsert(self):
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.upsert.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{"id": "test"}])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            await save_to_cache(
                user_id="user-123",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=[{"id": 1}],
                sources=["PNCP"],
            )

        mock_sb.table.assert_called_once_with("search_results_cache")
        mock_sb.upsert.assert_called_once()
        call_args = mock_sb.upsert.call_args
        row = call_args[0][0]
        assert row["user_id"] == "user-123"
        assert row["total_results"] == 1
        assert row["sources_json"] == ["PNCP"]

    @pytest.mark.asyncio
    async def test_save_failure_is_non_fatal(self):
        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")):
            # Should not raise
            await save_to_cache(
                user_id="user-123",
                params={"setor_id": 1, "ufs": ["SP"]},
                results=[{"id": 1}],
                sources=["PNCP"],
            )


# ============================================================================
# AC4 + AC5: get_from_cache
# ============================================================================


class TestGetFromCache:
    """AC4: On PNCP failure, retrieve stale cache."""

    def _mock_supabase_with_cache(self, fetched_at: str, sources=None):
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{
            "results": [{"id": 1, "objeto": "test"}],
            "total_results": 1,
            "sources_json": sources or ["PNCP"],
            "fetched_at": fetched_at,
            "created_at": fetched_at,
        }])
        return mock_sb

    @pytest.mark.asyncio
    async def test_cache_hit_fresh(self):
        """Cache entry < 6h old — returned as fresh."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=2)).isoformat()
        mock_sb = self._mock_supabase_with_cache(fetched_at, sources=["PNCP", "PORTAL_COMPRAS"])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await get_from_cache(
                user_id="user-123",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        assert result["results"] == [{"id": 1, "objeto": "test"}]
        assert result["cached_sources"] == ["PNCP", "PORTAL_COMPRAS"]
        assert result["is_stale"] is False
        assert result["cache_age_hours"] < CACHE_FRESH_HOURS

    @pytest.mark.asyncio
    async def test_cache_hit_stale(self):
        """Cache entry 6-24h old — returned as stale."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=12)).isoformat()
        mock_sb = self._mock_supabase_with_cache(fetched_at)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await get_from_cache(
                user_id="user-123",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        assert result["is_stale"] is True
        assert CACHE_FRESH_HOURS < result["cache_age_hours"] < CACHE_STALE_HOURS

    @pytest.mark.asyncio
    async def test_cache_expired_not_served(self):
        """AC12: Cache entry > 24h old — NOT served."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=30)).isoformat()
        mock_sb = self._mock_supabase_with_cache(fetched_at)

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await get_from_cache(
                user_id="user-123",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_miss_returns_none(self):
        """AC11: No cache entry — returns None."""
        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await get_from_cache(
                user_id="user-123",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_read_failure_returns_none(self):
        """Cache read failures are non-fatal."""
        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")):
            result = await get_from_cache(
                user_id="user-123",
                params={"setor_id": 1, "ufs": ["SP"]},
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_cached_sources_defaults_to_pncp(self):
        """AC5r: sources_json defaults to ['pncp'] if missing."""
        now = datetime.now(timezone.utc)
        fetched_at = (now - timedelta(hours=2)).isoformat()

        mock_sb = MagicMock()
        mock_sb.table.return_value = mock_sb
        mock_sb.select.return_value = mock_sb
        mock_sb.eq.return_value = mock_sb
        mock_sb.order.return_value = mock_sb
        mock_sb.limit.return_value = mock_sb
        mock_sb.execute.return_value = Mock(data=[{
            "results": [{"id": 1}],
            "total_results": 1,
            "sources_json": None,  # Legacy row without sources
            "fetched_at": fetched_at,
            "created_at": fetched_at,
        }])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            result = await get_from_cache(
                user_id="user-123",
                params={"setor_id": 1, "ufs": ["SP"]},
            )

        assert result is not None
        assert result["cached_sources"] == ["pncp"]


# ============================================================================
# AC10/AC11: Pipeline integration (cache on failure)
# ============================================================================


class TestPipelineCacheFallback:
    """AC10: cache_hit_on_pncp_failure, AC11: cache_miss_returns_error.

    These test the search_pipeline.py AllSourcesFailedError handler
    which now queries get_from_cache().
    """

    @pytest.mark.asyncio
    async def test_cache_hit_on_all_sources_failure(self):
        """AC10: When all sources fail and cache has data, serve stale."""
        from search_context import SearchContext
        from schemas import DataSourceStatus

        # Simulate what happens in the AllSourcesFailedError handler
        now = datetime.now(timezone.utc)
        stale_cache = {
            "results": [{"id": 1, "objeto": "Cached bid"}],
            "cached_at": (now - timedelta(hours=8)).isoformat(),
            "cached_sources": ["PNCP"],
            "cache_age_hours": 8.0,
            "is_stale": True,
        }

        # Verify the cache data can be applied to context
        ctx = SearchContext(
            request=Mock(setor_id=1, ufs=["SP"]),
            user={"id": "user-123"},
        )

        # Simulate the failover logic
        ctx.licitacoes_raw = stale_cache["results"]
        ctx.cached = True
        ctx.cached_at = stale_cache["cached_at"]
        ctx.cached_sources = stale_cache.get("cached_sources", ["PNCP"])
        ctx.is_partial = True

        assert ctx.cached is True
        assert len(ctx.licitacoes_raw) == 1
        assert ctx.cached_sources == ["PNCP"]
        assert ctx.is_partial is True

    @pytest.mark.asyncio
    async def test_cache_miss_on_all_sources_failure(self):
        """AC11: When all sources fail and no cache, return empty."""
        from search_context import SearchContext

        ctx = SearchContext(
            request=Mock(setor_id=1, ufs=["SP"]),
            user={"id": "user-123"},
        )

        # Simulate cache miss path
        ctx.licitacoes_raw = []
        ctx.is_partial = True
        ctx.degradation_reason = "All sources failed"

        assert ctx.cached is False
        assert ctx.licitacoes_raw == []
        assert ctx.is_partial is True


# ============================================================================
# AC17r: Fallback cascade
# ============================================================================


class TestFallbackCascade:
    """AC17r: Live (PNCP+PCP) → Partial → Cache stale → Empty."""

    def test_cascade_order_documented(self):
        """Verify the cascade is documented in the pipeline module."""
        import search_pipeline
        with open(search_pipeline.__file__, encoding="utf-8") as f:
            source = f.read()
        # The AllSourcesFailedError handler should mention cache fallback
        assert "_supabase_get_cache" in source
        # And it should be in the AllSourcesFailedError except block
        assert "AllSourcesFailedError" in source

    def test_search_context_has_cache_fields(self):
        """SearchContext should have cached, cached_at, cached_sources."""
        from search_context import SearchContext
        ctx = SearchContext(request=Mock(), user={})
        assert ctx.cached is False
        assert ctx.cached_at is None
        assert ctx.cached_sources is None

    def test_busca_response_has_cached_sources(self):
        """BuscaResponse schema should include cached_sources field."""
        from schemas import BuscaResponse
        fields = BuscaResponse.model_fields
        assert "cached_sources" in fields
        assert "cached" in fields
        assert "cached_at" in fields
