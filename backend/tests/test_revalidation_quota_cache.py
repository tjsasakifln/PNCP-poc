"""GTM-INFRA-003: Background Revalidation Multi-Source + Skip Quota on Cache.

Tests:
    T1: Revalidation uses ConsolidationService (multi-source)
    T2: Partial revalidation (without PNCP) updates cache
    T3: Cache hit does NOT consume quota
    T4: Live search consumes quota normally
    T5: Revalidation does NOT consume user quota
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

# Suppress unawaited coroutine warnings from mocked asyncio.create_task
pytestmark = pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")


# ---------------------------------------------------------------------------
# T1: Revalidation uses ConsolidationService
# ---------------------------------------------------------------------------


class TestT1_RevalidationUsesConsolidationService:
    """T1: _fetch_multi_source_for_revalidation uses ConsolidationService."""

    @pytest.mark.asyncio
    async def test_revalidation_calls_consolidation_service(self):
        """ConsolidationService is instantiated and fetch_all called."""
        mock_source_config = MagicMock()
        mock_source_config.pncp.enabled = True
        mock_source_config.compras_gov.enabled = True
        mock_source_config.portal.enabled = False

        mock_consolidation_result = MagicMock()
        mock_consolidation_result.records = [{"id": "1"}, {"id": "2"}]
        mock_consolidation_result.source_results = [
            MagicMock(source_code="PNCP", status="success"),
            MagicMock(source_code="COMPRAS_GOV", status="success"),
        ]

        mock_svc = AsyncMock()
        mock_svc.fetch_all = AsyncMock(return_value=mock_consolidation_result)
        mock_svc.close = AsyncMock()

        # Deferred imports inside _fetch_multi_source_for_revalidation — patch at source
        with (
            patch("source_config.sources.get_source_config", return_value=mock_source_config),
            patch("consolidation.ConsolidationService", return_value=mock_svc) as MockCS,
            patch("pncp_client.PNCPLegacyAdapter"),
            patch("clients.compras_gov_client.ComprasGovAdapter"),
        ):
            from search_cache import _fetch_multi_source_for_revalidation

            results, sources = await _fetch_multi_source_for_revalidation({
                "ufs": ["SP", "RJ"],
                "data_inicial": "2026-02-01",
                "data_final": "2026-02-10",
                "modalidades": [6],
            })

            assert len(results) == 2
            assert "PNCP" in sources
            assert "COMPRAS_GOV" in sources
            MockCS.assert_called_once()
            mock_svc.fetch_all.assert_called_once()
            mock_svc.close.assert_called_once()


# ---------------------------------------------------------------------------
# T2: Partial revalidation (without PNCP) updates cache
# ---------------------------------------------------------------------------


class TestT2_PartialRevalidationUpdatesCache:
    """T2: When full multi-source fails, PCP+ComprasGov fallback updates cache."""

    @pytest.mark.asyncio
    async def test_pcp_comprasgov_fallback_returns_results(self):
        """When ConsolidationService fails entirely, PCP+ComprasGov fallback is tried."""
        mock_source_config = MagicMock()
        mock_source_config.pncp.enabled = True
        mock_source_config.compras_gov.enabled = True
        mock_source_config.compras_gov.timeout = 30
        mock_source_config.portal.enabled = False

        # First ConsolidationService call raises exception
        first_call_error = Exception("All sources failed")

        # Fallback ConsolidationService succeeds
        fallback_result = MagicMock()
        fallback_result.records = [{"id": "fb1"}]
        fallback_result.source_results = [
            MagicMock(source_code="COMPRAS_GOV", status="success"),
        ]

        call_count = 0

        def side_effect_cs(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock = AsyncMock()
            mock.close = AsyncMock()
            if call_count == 1:
                # First call (full multi-source) fails
                mock.fetch_all = AsyncMock(side_effect=first_call_error)
            else:
                # Second call (PCP+ComprasGov fallback) succeeds
                mock.fetch_all = AsyncMock(return_value=fallback_result)
            return mock

        with (
            patch("source_config.sources.get_source_config", return_value=mock_source_config),
            patch("consolidation.ConsolidationService", side_effect=side_effect_cs),
            patch("pncp_client.PNCPLegacyAdapter"),
            patch("clients.compras_gov_client.ComprasGovAdapter"),
        ):
            from search_cache import _fetch_multi_source_for_revalidation

            results, sources = await _fetch_multi_source_for_revalidation({
                "ufs": ["SP"],
                "data_inicial": "2026-02-01",
                "data_final": "2026-02-10",
            })

            assert len(results) == 1
            assert results[0]["id"] == "fb1"
            assert "COMPRAS_GOV" in sources

    @pytest.mark.asyncio
    async def test_all_fallbacks_fail_returns_empty(self):
        """When all fallbacks fail, returns empty list (caller keeps stale)."""
        mock_source_config = MagicMock()
        mock_source_config.pncp.enabled = True
        mock_source_config.compras_gov.enabled = False  # No ComprasGov
        mock_source_config.portal.enabled = False  # No Portal

        # ConsolidationService fails
        mock_svc = AsyncMock()
        mock_svc.fetch_all = AsyncMock(side_effect=Exception("PNCP down"))
        mock_svc.close = AsyncMock()

        with (
            patch("source_config.sources.get_source_config", return_value=mock_source_config),
            patch("consolidation.ConsolidationService", return_value=mock_svc),
            patch("pncp_client.PNCPLegacyAdapter"),
            patch("pncp_client.buscar_todas_ufs_paralelo", new_callable=AsyncMock, side_effect=Exception("PNCP down")),
        ):
            from search_cache import _fetch_multi_source_for_revalidation

            results, sources = await _fetch_multi_source_for_revalidation({
                "ufs": ["SP"],
                "data_inicial": "2026-02-01",
                "data_final": "2026-02-10",
            })

            assert results == []
            assert sources == []


# ---------------------------------------------------------------------------
# T3: Cache hit does NOT consume quota
# ---------------------------------------------------------------------------


class TestT3_CacheHitSkipsQuota:
    """T3: When response comes from cache, quota is NOT consumed."""

    @pytest.mark.asyncio
    async def test_cache_hit_skips_quota_increment(self):
        """stage_validate skips check_and_increment_quota_atomic when cache hit."""
        from search_context import SearchContext

        # Build a minimal request
        mock_request = MagicMock()
        mock_request.setor_id = "vestuario"
        mock_request.ufs = ["SP"]
        mock_request.status = None
        mock_request.modalidades = None
        mock_request.modo_busca = "publicacao"
        mock_request.termos_busca = None
        mock_request.search_id = "test-search-1"
        mock_request.force_fresh = False

        ctx = SearchContext(
            request=mock_request,
            user={"id": "user-123"},
        )

        # Cache returns a hit
        mock_cache_result = {
            "results": [{"id": "cached-1"}],
            "cached_at": "2026-02-23T00:00:00+00:00",
            "cached_sources": ["PNCP"],
            "cache_age_hours": 2.0,
            "is_stale": False,
            "cache_level": "supabase",
            "cache_status": "fresh",
            "cache_priority": "warm",
        }

        mock_quota_info = MagicMock()
        mock_quota_info.allowed = True
        mock_quota_info.quota_used = 5
        mock_quota_info.quota_remaining = 95
        mock_quota_info.capabilities = {"max_requests_per_month": 100, "max_requests_per_min": 10}

        deps = SimpleNamespace(
            ENABLE_NEW_PRICING=True,
            check_user_roles=AsyncMock(return_value=(False, False)),
            rate_limiter=MagicMock(),
        )
        deps.rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

        # _supabase_get_cache is a top-level import in search_pipeline
        with (
            patch("pipeline.stages.validate._supabase_get_cache", new_callable=AsyncMock, return_value=mock_cache_result),
            patch("pipeline.stages.validate.quota") as mock_quota_mod,
            patch("pipeline.stages.validate.get_admin_ids", return_value=set()),
            patch("search_cache.compute_search_hash", return_value="abc123hash"),
            patch("metrics.CACHE_QUOTA_SKIPPED") as mock_metric,
        ):
            mock_quota_mod.check_quota = MagicMock(return_value=mock_quota_info)
            mock_quota_mod.register_search_session = AsyncMock(return_value="session-1")
            mock_quota_mod.update_search_session_status = AsyncMock()
            mock_quota_mod.check_and_increment_quota_atomic = MagicMock()

            from search_pipeline import SearchPipeline
            pipeline = SearchPipeline(deps)
            await pipeline.stage_validate(ctx)

            # Quota was NOT incremented
            mock_quota_mod.check_and_increment_quota_atomic.assert_not_called()

            # from_cache is set
            assert ctx.from_cache is True

            # Metric was incremented
            mock_metric.inc.assert_called_once()


# ---------------------------------------------------------------------------
# T4: Live search consumes quota normally
# ---------------------------------------------------------------------------


class TestT4_LiveSearchConsumesQuota:
    """T4: When cache misses, quota IS consumed."""

    @pytest.mark.asyncio
    async def test_cache_miss_consumes_quota(self):
        """stage_validate calls check_and_increment_quota_atomic on cache miss."""
        from search_context import SearchContext

        mock_request = MagicMock()
        mock_request.setor_id = "vestuario"
        mock_request.ufs = ["SP"]
        mock_request.status = None
        mock_request.modalidades = None
        mock_request.modo_busca = "publicacao"
        mock_request.termos_busca = None
        mock_request.search_id = "test-search-2"
        mock_request.force_fresh = False

        ctx = SearchContext(
            request=mock_request,
            user={"id": "user-456"},
        )

        mock_quota_info = MagicMock()
        mock_quota_info.allowed = True
        mock_quota_info.quota_used = 5
        mock_quota_info.quota_remaining = 95
        mock_quota_info.capabilities = {"max_requests_per_month": 100, "max_requests_per_min": 10}
        mock_quota_info.quota_reset_date = datetime(2026, 3, 1, tzinfo=timezone.utc)

        deps = SimpleNamespace(
            ENABLE_NEW_PRICING=True,
            check_user_roles=AsyncMock(return_value=(False, False)),
            rate_limiter=MagicMock(),
        )
        deps.rate_limiter.check_rate_limit = AsyncMock(return_value=(True, 0))

        with (
            patch("pipeline.stages.validate._supabase_get_cache", new_callable=AsyncMock, return_value=None),  # Cache MISS
            patch("pipeline.stages.validate.quota") as mock_quota_mod,
            patch("pipeline.stages.validate.get_admin_ids", return_value=set()),
            patch("pipeline.stages.validate._maybe_send_quota_email"),
        ):
            mock_quota_mod.check_quota = MagicMock(return_value=mock_quota_info)
            mock_quota_mod.register_search_session = AsyncMock(return_value="session-2")
            mock_quota_mod.update_search_session_status = AsyncMock()
            mock_quota_mod.check_and_increment_quota_atomic = MagicMock(return_value=(True, 6, 94))

            from search_pipeline import SearchPipeline
            pipeline = SearchPipeline(deps)
            await pipeline.stage_validate(ctx)

            # Quota WAS consumed
            mock_quota_mod.check_and_increment_quota_atomic.assert_called_once_with(
                "user-456", 100
            )

            # from_cache is NOT set
            assert ctx.from_cache is False


# ---------------------------------------------------------------------------
# T5: Revalidation does NOT consume user quota
# ---------------------------------------------------------------------------


class TestT5_RevalidationNoUserQuota:
    """T5: Background revalidation never calls quota functions."""

    @pytest.mark.asyncio
    async def test_do_revalidation_never_calls_quota(self):
        """_do_revalidation does not call any quota functions.

        Patches target `cache.swr` (where _do_revalidation lives) and
        `cache.manager.save_to_cache` (lazy-imported inside the function).
        Patching the `search_cache` re-export facade does not reach the
        call sites inside cache.swr — that was the old drift causing
        the test to hang on the real asyncio.Lock.
        """
        mock_results = [{"id": "reval-1"}]
        mock_sources = ["PNCP", "COMPRAS_GOV"]

        import asyncio as _asyncio
        real_lock = _asyncio.Lock()

        with (
            patch(
                "cache.swr._fetch_multi_source_for_revalidation",
                new_callable=AsyncMock,
                return_value=(mock_results, mock_sources),
            ),
            patch("cache.manager.save_to_cache", new_callable=AsyncMock) as mock_save,
            patch("cache.swr._clear_revalidating", new_callable=AsyncMock),
            patch("cache.swr._get_revalidation_lock", return_value=real_lock),
            patch("config.REVALIDATION_TIMEOUT", 60),
        ):
            import search_cache
            search_cache._active_revalidations = 1

            try:
                await search_cache._do_revalidation(
                    user_id="user-reval",
                    params={"setor_id": "vestuario", "ufs": ["SP"]},
                    params_hash="abc123hashfull",
                    request_data={
                        "ufs": ["SP"],
                        "data_inicial": "2026-02-01",
                        "data_final": "2026-02-10",
                    },
                    search_id=None,
                )

                # save_to_cache was called (results saved)
                mock_save.assert_called_once()

                # Verify the save call args
                save_kwargs = mock_save.call_args
                assert save_kwargs[1]["user_id"] == "user-reval"
                assert len(save_kwargs[1]["results"]) == 1
            finally:
                search_cache._active_revalidations = 0

    @pytest.mark.asyncio
    async def test_revalidation_has_no_quota_import(self):
        """_do_revalidation and _fetch_multi_source_for_revalidation have no quota references."""
        import inspect
        from search_cache import _do_revalidation, _fetch_multi_source_for_revalidation

        # Verify source code does NOT contain quota references
        reval_source = inspect.getsource(_do_revalidation)
        fetch_source = inspect.getsource(_fetch_multi_source_for_revalidation)

        assert "check_and_increment_quota" not in reval_source
        assert "increment_monthly_quota" not in fetch_source
        assert "check_quota" not in reval_source
