"""Tests for STORY-226 Track 4: Infrastructure & Security (AC14-AC17).

Covers:
- AC14: DeprecationMiddleware for legacy routes
- AC15: Excel storage-only (no base64 fallback)
- AC16: Runtime-reloadable feature flags
- AC17: Password policy validation
"""

import os
import time
import pytest
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# AC14: DeprecationMiddleware
# ---------------------------------------------------------------------------


class TestDeprecationMiddleware:
    """AC14: Legacy routes get deprecation headers."""

    def test_middleware_class_exists(self):
        from middleware import DeprecationMiddleware
        assert DeprecationMiddleware is not None

    @pytest.mark.asyncio
    async def test_legacy_route_gets_deprecation_header(self):
        """Non-prefixed routes should receive Deprecation: true header."""
        from middleware import DeprecationMiddleware

        middleware = DeprecationMiddleware(app=MagicMock())

        # Simulate request to legacy route
        mock_request = MagicMock()
        mock_request.url.path = "/admin/users"
        mock_request.method = "GET"

        mock_response = MagicMock()
        mock_response.headers = {}

        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)
        assert result.headers.get("Deprecation") == "true"
        assert result.headers.get("Sunset") == "2026-06-01"
        assert "/v1/admin/users" in result.headers.get("Link", "")

    @pytest.mark.asyncio
    async def test_v1_route_no_deprecation_header(self):
        """Routes starting with /v1/ should NOT get deprecation headers."""
        from middleware import DeprecationMiddleware

        middleware = DeprecationMiddleware(app=MagicMock())

        mock_request = MagicMock()
        mock_request.url.path = "/v1/admin/users"
        mock_request.method = "GET"

        mock_response = MagicMock()
        mock_response.headers = {}

        async def mock_call_next(request):
            return mock_response

        result = await middleware.dispatch(mock_request, mock_call_next)
        assert "Deprecation" not in result.headers

    @pytest.mark.asyncio
    async def test_exempt_routes_no_deprecation(self):
        """Root utility routes (/, /health, /docs) should NOT get deprecation headers."""
        from middleware import DeprecationMiddleware

        for exempt_path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            middleware = DeprecationMiddleware(app=MagicMock())

            mock_request = MagicMock()
            mock_request.url.path = exempt_path
            mock_request.method = "GET"

            mock_response = MagicMock()
            mock_response.headers = {}

            async def mock_call_next(request):
                return mock_response

            result = await middleware.dispatch(mock_request, mock_call_next)
            assert "Deprecation" not in result.headers, f"Path {exempt_path} should be exempt"

    @pytest.mark.asyncio
    async def test_warning_logged_once_per_path(self):
        """Deprecation warning should be logged only once per unique path."""
        from middleware import DeprecationMiddleware

        # Reset warned paths for clean test
        DeprecationMiddleware._warned_paths = set()

        middleware = DeprecationMiddleware(app=MagicMock())

        mock_request = MagicMock()
        mock_request.url.path = "/buscar"
        mock_request.method = "POST"

        mock_response = MagicMock()
        mock_response.headers = {}

        async def mock_call_next(request):
            return mock_response

        with patch("middleware.logger") as mock_logger:
            # First request — should log warning
            await middleware.dispatch(mock_request, mock_call_next)
            assert mock_logger.warning.call_count == 1

            # Second request — same path — should NOT log again
            mock_response.headers = {}
            await middleware.dispatch(mock_request, mock_call_next)
            assert mock_logger.warning.call_count == 1

        # Cleanup
        DeprecationMiddleware._warned_paths = set()


# ---------------------------------------------------------------------------
# AC15: Excel storage-only (no base64 fallback)
# ---------------------------------------------------------------------------


class TestExcelStorageOnly:
    """AC15: When storage upload fails, Excel should be marked unavailable (not base64)."""

    def test_no_base64_import_in_search_pipeline(self):
        """search_pipeline.py should not import base64 anymore."""
        import search_pipeline
        import inspect
        source = inspect.getsource(search_pipeline)
        # Check there's no "import base64" statement
        assert "import base64" not in source

    @pytest.mark.asyncio
    async def test_storage_failure_marks_excel_unavailable(self):
        """When upload_excel returns None, excel_available should be False."""
        from search_pipeline import SearchPipeline
        from search_context import SearchContext
        from types import SimpleNamespace
        from io import BytesIO

        # Create minimal context
        mock_request = SimpleNamespace(
            ufs=["SC"],
            data_inicial="2026-01-01",
            data_final="2026-01-07",
            setor_id="vestuario",
            search_id="test-123",
            termos_busca=None,
            exclusion_terms=None,
            status=None,
            modalidades=None,
            valor_minimo=0,
            valor_maximo=999999999,
            esferas=None,
            municipios=None,
            ordenacao="relevancia",
            show_all_matches=False,
            check_sanctions=False,
        )

        ctx = SearchContext(
            request=mock_request,
            user={"id": "test-user-id"},
            tracker=None,
            start_time=time.time(),
        )

        # Simulate state after stage 5
        ctx.licitacoes_raw = [{"codigoCompra": "123", "objetoCompra": "Uniformes", "valorTotalEstimado": 100000}]
        ctx.licitacoes_filtradas = ctx.licitacoes_raw.copy()
        ctx.filter_stats = {"rejeitadas_uf": 0, "rejeitadas_valor": 0, "rejeitadas_keyword": 0,
                            "rejeitadas_min_match": 0, "rejeitadas_prazo": 0, "rejeitadas_outros": 0}
        ctx.custom_terms = []
        ctx.stopwords_removed = []
        ctx.hidden_by_min_match = 0
        ctx.filter_relaxed = False
        ctx.source_stats_data = None
        ctx.sector = SimpleNamespace(name="Vestuario", keywords=set())
        ctx.active_keywords = set()
        ctx.quota_info = SimpleNamespace(
            quota_used=1, quota_remaining=9,
            capabilities={"allow_excel": True, "max_requests_per_month": 10},
            plan_name="Test"
        )

        # Create deps
        excel_buffer = BytesIO(b"fake excel content")
        deps = SimpleNamespace(
            ENABLE_NEW_PRICING=False,
            create_excel=MagicMock(return_value=excel_buffer),
        )

        pipeline = SearchPipeline(deps)

        # Mock upload_excel to return None (failure)
        from schemas import ResumoEstrategico
        with patch("search_pipeline.upload_excel", return_value=None), \
             patch("search_pipeline.gerar_resumo") as mock_resumo:
            mock_resumo.return_value = ResumoEstrategico(
                resumo_executivo="test",
                total_oportunidades=1,
                valor_total=100000,
                destaques=[],
                alerta_urgencia=None,
            )

            await pipeline.stage_generate(ctx)

            # Verify: no base64 fallback, excel marked unavailable
            assert ctx.excel_base64 is None
            assert ctx.download_url is None
            assert ctx.excel_available is False
            assert "temporário" in (ctx.upgrade_message or "").lower() or "Erro" in (ctx.upgrade_message or "")


# ---------------------------------------------------------------------------
# AC16: Runtime-reloadable feature flags
# ---------------------------------------------------------------------------


class TestRuntimeFeatureFlags:
    """AC16: Feature flags should be readable at runtime with caching."""

    def test_get_feature_flag_reads_from_env(self):
        """get_feature_flag should read the current env value."""
        from config import get_feature_flag, _feature_flag_cache

        _feature_flag_cache.clear()

        with patch.dict(os.environ, {"ENABLE_NEW_PRICING": "false"}):
            result = get_feature_flag("ENABLE_NEW_PRICING")
            assert result is False

        _feature_flag_cache.clear()

        with patch.dict(os.environ, {"ENABLE_NEW_PRICING": "true"}):
            result = get_feature_flag("ENABLE_NEW_PRICING")
            assert result is True

    def test_get_feature_flag_caches_result(self):
        """Repeated calls within TTL should return cached value."""
        from config import get_feature_flag, _feature_flag_cache

        _feature_flag_cache.clear()

        with patch.dict(os.environ, {"ENABLE_NEW_PRICING": "true"}):
            result1 = get_feature_flag("ENABLE_NEW_PRICING")
            assert result1 is True

        # Change env but cache should still return True
        with patch.dict(os.environ, {"ENABLE_NEW_PRICING": "false"}):
            result2 = get_feature_flag("ENABLE_NEW_PRICING")
            assert result2 is True  # Still cached

        _feature_flag_cache.clear()

    def test_get_feature_flag_unknown_flag_with_default(self):
        """Unknown flags should use the provided default."""
        from config import get_feature_flag, _feature_flag_cache

        _feature_flag_cache.clear()

        result = get_feature_flag("NONEXISTENT_FLAG", default=False)
        assert result is False

        _feature_flag_cache.clear()

        result = get_feature_flag("NONEXISTENT_FLAG", default=True)
        assert result is True

        _feature_flag_cache.clear()

    def test_reload_feature_flags_clears_cache(self):
        """reload_feature_flags should clear the cache and return current values."""
        from config import reload_feature_flags, _feature_flag_cache, get_feature_flag

        _feature_flag_cache.clear()

        # Populate cache
        with patch.dict(os.environ, {"ENABLE_NEW_PRICING": "true"}):
            get_feature_flag("ENABLE_NEW_PRICING")
            assert len(_feature_flag_cache) > 0

        # Reload
        with patch.dict(os.environ, {"ENABLE_NEW_PRICING": "false"}):
            result = reload_feature_flags()
            assert result["ENABLE_NEW_PRICING"] is False

        _feature_flag_cache.clear()

    def test_cache_expires_after_ttl(self):
        """Cache entries should expire after TTL."""
        from config import get_feature_flag, _feature_flag_cache, _FEATURE_FLAG_TTL

        _feature_flag_cache.clear()

        with patch.dict(os.environ, {"ENABLE_NEW_PRICING": "true"}):
            get_feature_flag("ENABLE_NEW_PRICING")

        # Manually expire the cache entry
        name = "ENABLE_NEW_PRICING"
        if name in _feature_flag_cache:
            val, _ = _feature_flag_cache[name]
            _feature_flag_cache[name] = (val, time.time() - _FEATURE_FLAG_TTL - 1)

        # Now it should re-read from env
        with patch.dict(os.environ, {"ENABLE_NEW_PRICING": "false"}):
            result = get_feature_flag("ENABLE_NEW_PRICING")
            assert result is False

        _feature_flag_cache.clear()


# ---------------------------------------------------------------------------
# AC17: Password policy validation
# ---------------------------------------------------------------------------


class TestPasswordValidation:
    """AC17: Password must be >= 8 chars, >= 1 uppercase, >= 1 digit."""

    def test_valid_password(self):
        from schemas import validate_password
        is_valid, msg = validate_password("Abc12345")
        assert is_valid is True
        assert msg == ""

    def test_valid_complex_password(self):
        from schemas import validate_password
        is_valid, msg = validate_password("MyP@ssw0rd!")
        assert is_valid is True
        assert msg == ""

    def test_too_short(self):
        from schemas import validate_password
        is_valid, msg = validate_password("Ab1")
        assert is_valid is False
        assert "8 caracteres" in msg

    def test_exactly_7_chars(self):
        from schemas import validate_password
        is_valid, msg = validate_password("Abcde1!")
        assert is_valid is False
        assert "8 caracteres" in msg

    def test_exactly_8_chars_valid(self):
        from schemas import validate_password
        is_valid, msg = validate_password("Abcdef1!")
        assert is_valid is True

    def test_no_uppercase(self):
        from schemas import validate_password
        is_valid, msg = validate_password("abcdefg1")
        assert is_valid is False
        assert "maiúscula" in msg

    def test_no_digit(self):
        from schemas import validate_password
        is_valid, msg = validate_password("Abcdefgh")
        assert is_valid is False
        assert "dígito" in msg.lower() or "gito" in msg.lower()

    def test_empty_password(self):
        from schemas import validate_password
        is_valid, msg = validate_password("")
        assert is_valid is False
        assert "8 caracteres" in msg

    def test_only_digits(self):
        from schemas import validate_password
        is_valid, msg = validate_password("12345678")
        assert is_valid is False
        assert "maiúscula" in msg

    def test_only_uppercase(self):
        from schemas import validate_password
        is_valid, msg = validate_password("ABCDEFGH")
        assert is_valid is False
        assert "gito" in msg.lower()

    def test_unicode_characters_allowed(self):
        """Password with unicode should still require uppercase and digit."""
        from schemas import validate_password
        is_valid, msg = validate_password("Açúcar12")
        assert is_valid is True

    def test_password_with_spaces(self):
        from schemas import validate_password
        is_valid, msg = validate_password("My Pass1")
        assert is_valid is True

    def test_error_messages_in_portuguese(self):
        """All error messages should be in Portuguese."""
        from schemas import validate_password

        _, msg_short = validate_password("Ab1")
        assert "senha" in msg_short.lower()

        _, msg_upper = validate_password("abcdefg1")
        assert "maiúscula" in msg_upper.lower() or "maiuscula" in msg_upper.lower()

        _, msg_digit = validate_password("Abcdefgh")
        assert "dígito" in msg_digit.lower() or "digito" in msg_digit.lower()
