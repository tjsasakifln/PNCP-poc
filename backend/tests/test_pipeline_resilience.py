"""GTM-FIX-025 T5: Pipeline resilience tests.

Validates that the search pipeline gracefully handles:
- ComprasGov 503 errors without killing PNCP+PCP results (AC19)
- Unexpected exceptions triggering cache fallback (AC20)
- All sources failing triggering stale cache (AC21)
- PNCP using tamanhoPagina=500 (AC22)
- ComprasGov disabled by default (AC1)
- Fallback adapter is None (AC2)
- Generic exception handler (AC5-AC9)
"""

import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Pre-mock heavy third-party modules before importing pipeline
for _mod_name in ("openai",):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = MagicMock()

from search_context import SearchContext
from search_pipeline import SearchPipeline


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

def _make_rate_limiter():
    rl = MagicMock()
    rl.check_rate_limit = AsyncMock(return_value=(True, 0))
    return rl


def _make_deps(**overrides):
    defaults = {
        "ENABLE_NEW_PRICING": False,
        "PNCPClient": MagicMock,
        "buscar_todas_ufs_paralelo": AsyncMock(return_value=[]),
        "aplicar_todos_filtros": MagicMock(return_value=([], {})),
        "create_excel": MagicMock(),
        "rate_limiter": _make_rate_limiter(),
        "check_user_roles": AsyncMock(return_value=(False, False)),
        "match_keywords": MagicMock(return_value=(True, [])),
        "KEYWORDS_UNIFORMES": set(),
        "KEYWORDS_EXCLUSAO": set(),
        "validate_terms": MagicMock(return_value={"valid": [], "ignored": [], "reasons": {}}),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_request(**overrides):
    defaults = {
        "ufs": ["SP"],
        "data_inicial": "2026-01-01",
        "data_final": "2026-01-07",
        "setor_id": "vestuario",
        "termos_busca": None,
        "show_all_matches": False,
        "exclusion_terms": None,
        "status": MagicMock(value="todos"),
        "modalidades": None,
        "valor_minimo": None,
        "valor_maximo": None,
        "esferas": None,
        "municipios": None,
        "ordenacao": "relevancia",
        "search_id": "test-resilience-001",
        "modo_busca": None,
        "check_sanctions": False,
        "force_fresh": True,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_ctx(**overrides):
    request_overrides = overrides.pop("request_overrides", {})
    user = overrides.pop("user", {"id": "user-resilience", "email": "test@test.com"})
    ctx = SearchContext(request=_make_request(**request_overrides), user=user)
    ctx.active_keywords = overrides.pop("active_keywords", {"uniforme"})
    ctx.active_exclusions = overrides.pop("active_exclusions", set())
    ctx.custom_terms = overrides.pop("custom_terms", [])
    ctx.min_match_floor_value = overrides.pop("min_match_floor_value", None)
    ctx.sector = overrides.pop("sector", SimpleNamespace(name="Vestuário", keywords=["uniforme"]))
    for k, v in overrides.items():
        setattr(ctx, k, v)
    return ctx


# ---------------------------------------------------------------------------
# AC1: ENABLE_SOURCE_COMPRAS_GOV default is "false"
# ---------------------------------------------------------------------------

class TestComprasGovDisabled:
    """T1: ComprasGov disabled by default in SourceConfig."""

    def test_ac1_compras_gov_default_disabled(self):
        """AC1: ENABLE_SOURCE_COMPRAS_GOV defaults to false."""
        from source_config.sources import SourceConfig
        # Don't set the env var — use the code default
        with patch.dict("os.environ", {}, clear=False):
            # Remove the env var if set
            import os
            original = os.environ.pop("ENABLE_SOURCE_COMPRAS_GOV", None)
            try:
                config = SourceConfig.from_env()
                assert config.compras_gov.enabled is False, (
                    "ComprasGov should be disabled by default (GTM-FIX-025 T1)"
                )
            finally:
                if original is not None:
                    os.environ["ENABLE_SOURCE_COMPRAS_GOV"] = original

    def test_ac3_compras_gov_not_in_enabled_sources(self):
        """AC3: ComprasGov doesn't appear in get_enabled_sources() when disabled."""
        from source_config.sources import SourceConfig
        import os
        original = os.environ.pop("ENABLE_SOURCE_COMPRAS_GOV", None)
        try:
            config = SourceConfig.from_env()
            enabled = config.get_enabled_sources()
            assert "ComprasGov" not in enabled, (
                f"ComprasGov should not be in enabled sources, got: {enabled}"
            )
        finally:
            if original is not None:
                os.environ["ENABLE_SOURCE_COMPRAS_GOV"] = original

    def test_compras_gov_can_be_enabled_via_env(self):
        """ComprasGov can still be enabled via env var override."""
        from source_config.sources import SourceConfig
        import os
        original = os.environ.get("ENABLE_SOURCE_COMPRAS_GOV")
        os.environ["ENABLE_SOURCE_COMPRAS_GOV"] = "true"
        try:
            config = SourceConfig.from_env()
            assert config.compras_gov.enabled is True
            assert "ComprasGov" in config.get_enabled_sources()
        finally:
            if original is not None:
                os.environ["ENABLE_SOURCE_COMPRAS_GOV"] = original
            else:
                os.environ.pop("ENABLE_SOURCE_COMPRAS_GOV", None)


# ---------------------------------------------------------------------------
# AC2: Fallback adapter is None in search_pipeline
# ---------------------------------------------------------------------------

class TestFallbackAdapterNone:
    """T1: Fallback adapter removed from multi-source pipeline."""

    @pytest.mark.asyncio
    @patch("source_config.sources.get_source_config")
    @patch("utils.error_reporting.sentry_sdk")
    @patch("search_pipeline.get_from_cache_cascade", new_callable=AsyncMock, return_value=None)
    @patch("search_pipeline._supabase_save_cache", new_callable=AsyncMock)
    @patch("search_pipeline.enriquecer_com_status_inferido")
    @patch("search_pipeline.os.getenv", return_value="true")  # ENABLE_MULTI_SOURCE
    async def test_ac2_fallback_adapter_is_none(
        self, mock_getenv, mock_enrich, mock_save, mock_get_cache,
        mock_sentry, mock_config,
    ):
        """AC2: ConsolidationService receives fallback_adapter=None."""
        from source_config.sources import SourceConfig, SingleSourceConfig, SourceCode, ConsolidationConfig

        # Setup minimal source config with only PNCP enabled
        sc = MagicMock(spec=SourceConfig)
        sc.pncp = MagicMock(enabled=True)
        sc.compras_gov = MagicMock(enabled=False, timeout=30)
        sc.portal = MagicMock(enabled=False, timeout=30)
        sc.consolidation = MagicMock(
            timeout_per_source=50, timeout_global=120,
            fail_on_all_errors=True,
        )
        sc.get_enabled_source_configs.return_value = [sc.pncp]
        sc.get_pending_credentials.return_value = []
        mock_config.return_value = sc

        captured_kwargs = {}

        original_init = None

        # Patch ConsolidationService to capture its init args
        with patch("consolidation.ConsolidationService") as MockCS:
            mock_svc = AsyncMock()
            mock_svc.fetch_all = AsyncMock(return_value=MagicMock(
                records=[], source_results=[], is_partial=False,
                degradation_reason=None, total_before_dedup=0,
                total_after_dedup=0, duplicates_removed=0,
            ))
            mock_svc.close = AsyncMock()

            def capture_init(**kwargs):
                captured_kwargs.update(kwargs)
                return mock_svc

            MockCS.side_effect = capture_init

            deps = _make_deps()
            pipeline = SearchPipeline(deps)
            ctx = _make_ctx()

            await pipeline._execute_multi_source(
                ctx, ctx.request, deps, None, None, None, 240,
            )

        assert captured_kwargs.get("fallback_adapter") is None, (
            "fallback_adapter should be None (GTM-FIX-025 T1)"
        )


# ---------------------------------------------------------------------------
# AC19: ComprasGov 503 preserves PNCP+PCP results
# ---------------------------------------------------------------------------

class TestComprasGov503Resilience:
    """T5 AC19: When ComprasGov fails with 503, PNCP+PCP results are preserved."""

    @pytest.mark.asyncio
    async def test_ac19_compras_gov_failure_preserves_other_sources(self):
        """AC19: ComprasGov 503 doesn't kill pipeline — PNCP+PCP results survive."""
        from consolidation import ConsolidationService
        from clients.base import UnifiedProcurement, SourceAdapter, SourceMetadata, SourceStatus

        # Create a mock PNCP adapter that returns good data
        class GoodAdapter:
            was_truncated = False

            @property
            def metadata(self):
                return SourceMetadata(name="PNCP", code="PNCP",
                                      base_url="http://test", priority=1)

            @property
            def name(self):
                return "PNCP"

            @property
            def code(self):
                return "PNCP"

            async def health_check(self):
                return SourceStatus.AVAILABLE

            async def fetch(self, data_inicial, data_final, ufs=None, **kwargs):
                yield UnifiedProcurement(
                    source_id="pncp-001", source_name="PNCP",
                    objeto="Uniforme escolar", valor_estimado=50000.0,
                    orgao="Prefeitura SP", cnpj_orgao="12345678000100",
                    uf="SP", municipio="São Paulo",
                )

            def normalize(self, raw_record):
                pass

            async def close(self):
                pass

        # Create a failing ComprasGov adapter (simulates 503)
        class FailingAdapter:
            was_truncated = False

            @property
            def metadata(self):
                return SourceMetadata(name="ComprasGov", code="COMPRAS_GOV",
                                      base_url="http://test", priority=4)

            @property
            def name(self):
                return "ComprasGov"

            @property
            def code(self):
                return "COMPRAS_GOV"

            async def health_check(self):
                return SourceStatus.AVAILABLE

            async def fetch(self, data_inicial, data_final, ufs=None, **kwargs):
                raise Exception("HTTP 503: Service Unavailable")
                # yield is needed to make this an async generator if it reaches
                yield  # pragma: no cover

            def normalize(self, raw_record):
                pass

            async def close(self):
                pass

        adapters = {
            "PNCP": GoodAdapter(),
            "COMPRAS_GOV": FailingAdapter(),
        }

        svc = ConsolidationService(
            adapters=adapters,
            timeout_per_source=10,
            timeout_global=30,
            fail_on_all_errors=True,
        )

        result = await svc.fetch_all(
            data_inicial="2026-01-01",
            data_final="2026-01-07",
            ufs={"SP"},
        )

        # PNCP data should be preserved despite ComprasGov failure
        assert result.total_after_dedup >= 1, (
            f"Expected at least 1 result from PNCP, got {result.total_after_dedup}"
        )
        assert result.is_partial is True, "Should be marked as partial"

        # Verify ComprasGov failed but PNCP succeeded
        source_statuses = {sr.source_code: sr.status for sr in result.source_results}
        assert source_statuses.get("PNCP") == "success"
        assert source_statuses.get("COMPRAS_GOV") in ("error", "partial")


# ---------------------------------------------------------------------------
# AC20: Unexpected exception triggers cache fallback
# ---------------------------------------------------------------------------

class TestGenericExceptionHandler:
    """T2 AC5-AC9 + T5 AC20: Generic exception handler in multi-source fetch."""

    @pytest.mark.asyncio
    @patch("search_pipeline.get_from_cache_cascade", new_callable=AsyncMock)
    @patch("search_pipeline._supabase_save_cache", new_callable=AsyncMock)
    @patch("utils.error_reporting.sentry_sdk")
    @patch("search_pipeline.enriquecer_com_status_inferido")
    @patch("source_config.sources.get_source_config")
    async def test_ac20_unexpected_exception_triggers_cache(
        self, mock_config, mock_enrich, mock_sentry,
        mock_save_cache, mock_get_cache,
    ):
        """AC20: Unexpected exception triggers stale cache fallback."""
        from source_config.sources import SourceConfig

        # Setup: ConsolidationService raises unexpected RuntimeError
        sc = MagicMock(spec=SourceConfig)
        sc.pncp = MagicMock(enabled=True)
        sc.compras_gov = MagicMock(enabled=False, timeout=30)
        sc.portal = MagicMock(enabled=False, timeout=30)
        sc.consolidation = MagicMock(
            timeout_per_source=50, timeout_global=120,
            fail_on_all_errors=True,
        )
        sc.get_enabled_source_configs.return_value = [sc.pncp]
        sc.get_pending_credentials.return_value = []
        mock_config.return_value = sc

        # Stale cache is available
        mock_get_cache.return_value = {
            "results": [{"objetoCompra": "Cached result", "codigoCompra": "cache-001"}],
            "cached_at": "2026-02-17T10:00:00Z",
            "cache_age_hours": 12.0,
            "cached_sources": ["PNCP"],
        }

        with patch("consolidation.ConsolidationService") as MockCS:
            mock_svc = AsyncMock()
            mock_svc.fetch_all = AsyncMock(
                side_effect=RuntimeError("Totally unexpected kaboom!")
            )
            mock_svc.close = AsyncMock()
            MockCS.return_value = mock_svc

            deps = _make_deps()
            pipeline = SearchPipeline(deps)
            ctx = _make_ctx()

            await pipeline._execute_multi_source(
                ctx, ctx.request, deps, None, None, None, 240,
            )

        # AC6: Stale cache served
        assert ctx.licitacoes_raw == [{"objetoCompra": "Cached result", "codigoCompra": "cache-001"}]
        assert ctx.cached is True
        assert ctx.cached_at == "2026-02-17T10:00:00Z"
        assert ctx.cached_sources == ["PNCP"]

        # AC8: Context marked as partial with degradation reason
        assert ctx.is_partial is True
        assert "RuntimeError" in ctx.degradation_reason
        assert "kaboom" in ctx.degradation_reason

        # AC7: Sentry capture called
        mock_sentry.set_tag.assert_called_with("data_source", "consolidation_unexpected")
        mock_sentry.capture_exception.assert_called_once()

    @pytest.mark.asyncio
    @patch("search_pipeline.get_from_cache_cascade", new_callable=AsyncMock, return_value=None)
    @patch("search_pipeline._supabase_save_cache", new_callable=AsyncMock)
    @patch("utils.error_reporting.sentry_sdk")
    @patch("search_pipeline.enriquecer_com_status_inferido")
    @patch("source_config.sources.get_source_config")
    async def test_ac9_no_http_500_on_unexpected_exception(
        self, mock_config, mock_enrich, mock_sentry,
        mock_save_cache, mock_get_cache,
    ):
        """AC9: No HTTP 500 — empty results returned instead."""
        from source_config.sources import SourceConfig
        from fastapi import HTTPException

        sc = MagicMock(spec=SourceConfig)
        sc.pncp = MagicMock(enabled=True)
        sc.compras_gov = MagicMock(enabled=False, timeout=30)
        sc.portal = MagicMock(enabled=False, timeout=30)
        sc.consolidation = MagicMock(
            timeout_per_source=50, timeout_global=120,
            fail_on_all_errors=True,
        )
        sc.get_enabled_source_configs.return_value = [sc.pncp]
        sc.get_pending_credentials.return_value = []
        mock_config.return_value = sc

        with patch("consolidation.ConsolidationService") as MockCS:
            mock_svc = AsyncMock()
            mock_svc.fetch_all = AsyncMock(
                side_effect=ValueError("Invalid state in consolidation")
            )
            mock_svc.close = AsyncMock()
            MockCS.return_value = mock_svc

            deps = _make_deps()
            pipeline = SearchPipeline(deps)
            ctx = _make_ctx()

            # Should NOT raise HTTPException
            await pipeline._execute_multi_source(
                ctx, ctx.request, deps, None, None, None, 240,
            )

        # Should have empty results, NOT a 500 error
        assert ctx.licitacoes_raw == []
        assert ctx.is_partial is True
        assert "ValueError" in ctx.degradation_reason


# ---------------------------------------------------------------------------
# AC21: All sources fail triggers stale cache
# ---------------------------------------------------------------------------

class TestAllSourcesFailCache:
    """T5 AC21: When all sources fail, stale cache is served."""

    @pytest.mark.asyncio
    @patch("search_pipeline.get_from_cache_cascade", new_callable=AsyncMock)
    @patch("search_pipeline._supabase_save_cache", new_callable=AsyncMock)
    @patch("utils.error_reporting.sentry_sdk")
    @patch("search_pipeline.enriquecer_com_status_inferido")
    @patch("source_config.sources.get_source_config")
    async def test_ac21_all_sources_fail_triggers_stale_cache(
        self, mock_config, mock_enrich, mock_sentry,
        mock_save_cache, mock_get_cache,
    ):
        """AC21: All sources failing triggers stale cache lookup."""
        from consolidation import AllSourcesFailedError
        from source_config.sources import SourceConfig

        sc = MagicMock(spec=SourceConfig)
        sc.pncp = MagicMock(enabled=True)
        sc.compras_gov = MagicMock(enabled=False, timeout=30)
        sc.portal = MagicMock(enabled=True, timeout=30)
        sc.consolidation = MagicMock(
            timeout_per_source=50, timeout_global=120,
            fail_on_all_errors=True,
        )
        sc.get_enabled_source_configs.return_value = [sc.pncp, sc.portal]
        sc.get_pending_credentials.return_value = []
        mock_config.return_value = sc

        # Stale cache is available
        mock_get_cache.return_value = {
            "results": [
                {"objetoCompra": "Stale uniform bid", "codigoCompra": "stale-001"},
                {"objetoCompra": "Stale glove bid", "codigoCompra": "stale-002"},
            ],
            "cached_at": "2026-02-16T18:00:00Z",
            "cache_age_hours": 20.5,
            "cached_sources": ["PNCP", "PORTAL_COMPRAS"],
        }

        # All sources fail
        all_failed = AllSourcesFailedError(
            source_errors={
                "PNCP": "Connection timeout after 30s",
                "PORTAL_COMPRAS": "503 Service Unavailable",
            }
        )

        with patch("consolidation.ConsolidationService") as MockCS:
            mock_svc = AsyncMock()
            mock_svc.fetch_all = AsyncMock(side_effect=all_failed)
            mock_svc.close = AsyncMock()
            MockCS.return_value = mock_svc

            deps = _make_deps()
            pipeline = SearchPipeline(deps)
            ctx = _make_ctx()

            await pipeline._execute_multi_source(
                ctx, ctx.request, deps, None, None, None, 240,
            )

        # Stale cache served
        assert len(ctx.licitacoes_raw) == 2
        assert ctx.cached is True
        assert ctx.cached_at == "2026-02-16T18:00:00Z"
        assert ctx.cached_sources == ["PNCP", "PORTAL_COMPRAS"]
        assert ctx.is_partial is True


# ---------------------------------------------------------------------------
# AC22: PNCP uses tamanhoPagina=50 (reduced from 500 by PNCP ~Feb 2026)
# ---------------------------------------------------------------------------

class TestPNCPPageSize:
    """T3 AC10/AC22: PNCP client sends tamanhoPagina=50."""

    @pytest.mark.asyncio
    async def test_ac22_pncp_uses_page_size_50(self):
        """AC22: _fetch_single_modality passes tamanho=50 to _fetch_page_async."""
        from pncp_client import AsyncPNCPClient

        captured_kwargs_list = []

        async with AsyncPNCPClient(max_concurrent=2) as client:
            # Mock _fetch_page_async to capture its arguments
            original_fetch = client._fetch_page_async

            async def mock_fetch(*args, **kwargs):
                captured_kwargs_list.append(kwargs)
                return {
                    "data": [],
                    "totalRegistros": 0,
                    "totalPaginas": 0,
                    "paginaAtual": 1,
                    "paginasRestantes": 0,
                }

            client._fetch_page_async = mock_fetch

            await client._fetch_single_modality(
                uf="SP",
                data_inicial="2026-01-01",
                data_final="2026-01-07",
                modalidade=6,
            )

        assert len(captured_kwargs_list) >= 1, "Expected at least 1 page fetch"
        assert captured_kwargs_list[0].get("tamanho") == 50, (
            f"Expected tamanho=50, got {captured_kwargs_list[0].get('tamanho')}"
        )

    @pytest.mark.asyncio
    async def test_ac10_fetch_page_sends_tamanho_in_params(self):
        """AC10+AC11: _fetch_page_async includes tamanhoPagina in API params."""
        from pncp_client import AsyncPNCPClient

        captured_params = {}

        async with AsyncPNCPClient(max_concurrent=1) as client:
            original_get = client._client.get

            async def mock_get(url, params=None, **kwargs):
                captured_params.update(params or {})
                # Return a mock response
                response = MagicMock()
                response.status_code = 200
                response.headers = {"content-type": "application/json"}
                response.json.return_value = {
                    "data": [],
                    "totalRegistros": 0,
                    "totalPaginas": 0,
                    "paginaAtual": 1,
                    "paginasRestantes": 0,
                }
                response.text = "{}"
                return response

            client._client.get = mock_get

            await client._fetch_page_async(
                data_inicial="2026-01-01",
                data_final="2026-01-07",
                modalidade=6,
                uf="SP",
                tamanho=50,
            )

        assert captured_params.get("tamanhoPagina") == 50, (
            f"Expected tamanhoPagina=50 in API params, got: {captured_params}"
        )


# ---------------------------------------------------------------------------
# AC4: Busca completa com PNCP+PCP (2 fontes) sem ComprasGov
# ---------------------------------------------------------------------------

class TestSearchWithoutComprasGov:
    """T1 AC4: Search completes successfully with only PNCP+PCP."""

    @pytest.mark.asyncio
    @patch("search_pipeline.get_from_cache_cascade", new_callable=AsyncMock, return_value=None)
    @patch("search_pipeline._supabase_save_cache", new_callable=AsyncMock)
    @patch("utils.error_reporting.sentry_sdk")
    @patch("search_pipeline.enriquecer_com_status_inferido")
    @patch("source_config.sources.get_source_config")
    async def test_ac4_search_completes_with_pncp_pcp_only(
        self, mock_config, mock_enrich, mock_sentry,
        mock_save_cache, mock_get_cache,
    ):
        """AC4: Busca completa com sucesso usando apenas PNCP+PCP."""
        from source_config.sources import SourceConfig

        sc = MagicMock(spec=SourceConfig)
        sc.pncp = MagicMock(enabled=True)
        sc.compras_gov = MagicMock(enabled=False, timeout=30)
        sc.portal = MagicMock(enabled=True, timeout=30)
        sc.consolidation = MagicMock(
            timeout_per_source=50, timeout_global=120,
            fail_on_all_errors=True,
        )
        sc.get_enabled_source_configs.return_value = [sc.pncp, sc.portal]
        sc.get_pending_credentials.return_value = []
        mock_config.return_value = sc

        mock_result = MagicMock(
            records=[{"objetoCompra": "Uniforme", "codigoCompra": "001"}],
            source_results=[
                MagicMock(source_code="PNCP", record_count=1, duration_ms=500,
                         error=None, status="success"),
                MagicMock(source_code="PORTAL_COMPRAS", record_count=0, duration_ms=300,
                         error=None, status="success"),
            ],
            is_partial=False,
            degradation_reason=None,
            total_before_dedup=1,
            total_after_dedup=1,
            duplicates_removed=0,
        )

        with patch("consolidation.ConsolidationService") as MockCS:
            mock_svc = AsyncMock()
            mock_svc.fetch_all = AsyncMock(return_value=mock_result)
            mock_svc.close = AsyncMock()
            MockCS.return_value = mock_svc

            deps = _make_deps()
            pipeline = SearchPipeline(deps)
            ctx = _make_ctx()

            await pipeline._execute_multi_source(
                ctx, ctx.request, deps, None, None, None, 240,
            )

        assert len(ctx.licitacoes_raw) == 1
        assert ctx.is_partial is False

        # Verify ConsolidationService was NOT created with ComprasGov adapter
        cs_call_kwargs = MockCS.call_args
        adapters = cs_call_kwargs.kwargs.get("adapters", {}) if cs_call_kwargs.kwargs else {}
        assert "COMPRAS_GOV" not in adapters, (
            "ComprasGov should not be in adapters when disabled"
        )


# ---------------------------------------------------------------------------
# AC23: Zero regressions — verify existing imports/structures work
# ---------------------------------------------------------------------------

class TestZeroRegressions:
    """AC23: Basic sanity checks that nothing is broken."""

    def test_source_config_loads(self):
        """SourceConfig.from_env() doesn't crash."""
        from source_config.sources import SourceConfig
        config = SourceConfig.from_env()
        assert config is not None
        # PNCP should always be enabled by default
        assert config.pncp.enabled is True

    def test_search_pipeline_imports(self):
        """SearchPipeline can be imported and instantiated."""
        deps = _make_deps()
        pipeline = SearchPipeline(deps)
        assert pipeline is not None

    def test_search_context_creates(self):
        """SearchContext can be created with defaults."""
        ctx = _make_ctx()
        assert ctx.is_partial is False
        assert ctx.cached is False
        assert ctx.degradation_reason is None
