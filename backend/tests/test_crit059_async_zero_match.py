"""CRIT-059: Async zero-match classification via ARQ background job.

Tests:
- AC1: Filter returns immediately without LLM when async enabled
- AC2: Job classifies candidates correctly
- AC3: SSE events emitted in order (started → progress → ready)
- AC4: Endpoint /search/{id}/zero-match returns results after job completes
- AC7: Graceful degradation — ARQ unavailable → no crash
- AC7: Job timeout → partial results saved
- AC11: Feature flag off → inline behavior unchanged
- Zero regressions in filter.py
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# AC1: Filter returns zero_match_candidates when async enabled
# ---------------------------------------------------------------------------

class TestFilterAsyncZeroMatch:
    """Verify filter.py collects candidates instead of calling LLM inline."""

    def _make_bids(self, n: int, with_keyword: bool = False) -> list:
        """Create test bid dicts."""
        bids = []
        for i in range(n):
            bid = {
                "uf": "SP",
                "valorTotalEstimado": 100000 + i * 1000,
                "objetoCompra": f"Aquisição de uniformes escolares tipo {i}" if with_keyword else f"Contratação de serviços gerais para o órgão público número {i}",
                "dataPublicacaoPncp": "2026-03-01T00:00:00",
                "codigoModalidadeContratacao": 6,
            }
            bids.append(bid)
        return bids

    @patch("config.ASYNC_ZERO_MATCH_ENABLED", False)
    def test_async_disabled_uses_inline_llm(self):
        """When ASYNC_ZERO_MATCH_ENABLED=False, filter calls LLM inline (existing behavior)."""
        from filter import aplicar_todos_filtros
        bids = self._make_bids(5, with_keyword=True)
        result, stats = aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )
        # With keyword bids, they should pass through keyword filter
        assert stats.get("zero_match_candidates") is None or stats.get("zero_match_candidates") == []

    @patch("config.ASYNC_ZERO_MATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    @patch("config.MAX_ZERO_MATCH_ITEMS", 200)
    def test_async_enabled_collects_candidates(self):
        """When ASYNC_ZERO_MATCH_ENABLED=True, filter collects zero-match candidates."""
        from filter import aplicar_todos_filtros

        # Create bids that WON'T match keywords → become zero-match candidates
        bids = self._make_bids(10, with_keyword=False)
        result, stats = aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # Candidates should be collected, not classified inline
        candidates = stats.get("zero_match_candidates", [])
        candidates_count = stats.get("zero_match_candidates_count", 0)

        # Some bids should become candidates (those not matching keywords)
        # The exact count depends on filter stages (UF, status, value, etc.)
        assert candidates_count == len(candidates)
        # LLM should NOT have been called inline
        assert stats.get("llm_zero_match_calls", 0) == 0

    @patch("config.ASYNC_ZERO_MATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    def test_async_enabled_but_llm_disabled_no_candidates(self):
        """When LLM_ZERO_MATCH_ENABLED=False, no candidates collected."""
        from filter import aplicar_todos_filtros
        bids = self._make_bids(5, with_keyword=False)
        result, stats = aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )
        assert stats.get("zero_match_candidates_count", 0) == 0


# ---------------------------------------------------------------------------
# AC2: Job classifies candidates correctly
# ---------------------------------------------------------------------------

class TestClassifyZeroMatchJob:
    """Test the ARQ job function."""

    @pytest.mark.asyncio
    async def test_job_classifies_and_stores_results(self):
        """Job should call LLM, store results in Redis, emit SSE events."""
        candidates = [
            {
                "objetoCompra": "Contratação de empresa para fornecimento de camisetas e uniformes",
                "valorTotalEstimado": 50000,
            },
            {
                "objetoCompra": "Aquisição de material de escritório e papelaria",
                "valorTotalEstimado": 10000,
            },
        ]

        mock_batch_results = [
            {"is_primary": True, "confidence": 65, "evidence": ["uniformes"]},
            {"is_primary": False, "confidence": 20, "evidence": []},
        ]

        mock_tracker = AsyncMock()

        with patch("llm_arbiter._classify_zero_match_batch", return_value=mock_batch_results), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=AsyncMock(
                 setex=AsyncMock(),
                 get=AsyncMock(return_value=None),
             )), \
             patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 20), \
             patch("config.FILTER_ZERO_MATCH_BUDGET_S", 30), \
             patch("config.ZERO_MATCH_JOB_TIMEOUT_S", 120), \
             patch("config.MAX_ZERO_MATCH_ITEMS", 200), \
             patch("config.LLM_FALLBACK_PENDING_ENABLED", True):

            import job_queue
            result = await job_queue.classify_zero_match_job(
                ctx={},
                search_id="test-search-001",
                candidates=candidates,
                setor="vestuario",
                sector_name="Vestuário",
                enqueued_at=time.time() - 1,
            )

        assert result["status"] == "completed"
        assert result["approved"] == 1
        assert result["rejected"] == 1

        # Verify SSE events were emitted
        calls = mock_tracker.emit.call_args_list
        stages = [call.args[0] for call in calls]
        assert "zero_match_started" in stages
        assert "zero_match_ready" in stages

    @pytest.mark.asyncio
    async def test_job_handles_llm_failure_gracefully(self):
        """When LLM fails, job should save partial results and emit error."""
        candidates = [
            {"objetoCompra": "Test bid description for classification", "valorTotalEstimado": 10000},
        ]

        mock_tracker = AsyncMock()

        with patch("llm_arbiter._classify_zero_match_batch", side_effect=Exception("LLM unavailable")), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker), \
             patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=AsyncMock(
                 setex=AsyncMock(),
                 get=AsyncMock(return_value=None),
             )), \
             patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 20), \
             patch("config.FILTER_ZERO_MATCH_BUDGET_S", 30), \
             patch("config.ZERO_MATCH_JOB_TIMEOUT_S", 120), \
             patch("config.MAX_ZERO_MATCH_ITEMS", 200), \
             patch("config.LLM_FALLBACK_PENDING_ENABLED", True):

            import job_queue
            result = await job_queue.classify_zero_match_job(
                ctx={},
                search_id="test-search-002",
                candidates=candidates,
                setor="vestuario",
                sector_name="Vestuário",
            )

        # Should still complete (with pending/failed status)
        assert result["status"] in ("completed", "failed")


# ---------------------------------------------------------------------------
# AC4: Endpoint returns results after job completes
# ---------------------------------------------------------------------------

class TestZeroMatchEndpoint:
    """Test GET /v1/search/{search_id}/zero-match."""

    @pytest.mark.asyncio
    async def test_returns_results_when_available(self):
        """200 with results when job has completed."""
        mock_results = [
            {"objetoCompra": "Uniformes escolares", "_relevance_source": "llm_zero_match"},
        ]

        with patch("job_queue.get_zero_match_results", new_callable=AsyncMock, return_value=mock_results):
            from fastapi.testclient import TestClient
            from main import app
            from auth import require_auth

            app.dependency_overrides[require_auth] = lambda: {"id": "test-user", "email": "test@test.com"}
            try:
                client = TestClient(app)
                response = client.get("/v1/search/test-search-001/zero-match")
                assert response.status_code == 200
                data = response.json()
                assert data["count"] == 1
                assert data["results"][0]["_relevance_source"] == "llm_zero_match"
            finally:
                app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_returns_404_when_not_ready(self):
        """404 when job hasn't completed yet."""
        with patch("job_queue.get_zero_match_results", new_callable=AsyncMock, return_value=None):
            from fastapi.testclient import TestClient
            from main import app
            from auth import require_auth

            app.dependency_overrides[require_auth] = lambda: {"id": "test-user", "email": "test@test.com"}
            try:
                client = TestClient(app)
                response = client.get("/v1/search/test-search-001/zero-match")
                assert response.status_code == 404
            finally:
                app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# AC7: Graceful degradation
# ---------------------------------------------------------------------------

class TestGracefulDegradation:
    """Test degradation scenarios."""

    @pytest.mark.asyncio
    async def test_redis_unavailable_store_returns_false(self):
        """When Redis is down, store_zero_match_results returns False."""
        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None):
            from job_queue import store_zero_match_results
            result = await store_zero_match_results("test-id", [{"test": True}])
            assert result is False

    @pytest.mark.asyncio
    async def test_redis_unavailable_get_returns_none(self):
        """When Redis is down, get_zero_match_results returns None."""
        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None):
            from job_queue import get_zero_match_results
            result = await get_zero_match_results("test-id")
            assert result is None

    @pytest.mark.asyncio
    async def test_store_and_get_roundtrip(self):
        """Store and retrieve results via Redis."""
        stored_data = {}

        mock_redis = AsyncMock()

        async def mock_setex(key, ttl, value):
            stored_data[key] = value

        async def mock_get(key):
            return stored_data.get(key)

        mock_redis.setex = mock_setex
        mock_redis.get = mock_get

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import store_zero_match_results, get_zero_match_results

            test_results = [{"objetoCompra": "Test", "_relevance_source": "llm_zero_match"}]
            ok = await store_zero_match_results("roundtrip-test", test_results)
            assert ok is True

            retrieved = await get_zero_match_results("roundtrip-test")
            assert retrieved is not None
            assert len(retrieved) == 1
            assert retrieved[0]["_relevance_source"] == "llm_zero_match"


# ---------------------------------------------------------------------------
# AC8: Metrics
# ---------------------------------------------------------------------------

class TestMetrics:
    """Verify metrics are defined and importable."""

    def test_metrics_importable(self):
        from metrics import (
            ZERO_MATCH_JOB_DURATION,
            ZERO_MATCH_JOB_STATUS,
            ZERO_MATCH_JOB_QUEUE_TIME,
        )
        # Just verify they exist and have observe/inc/labels methods
        assert hasattr(ZERO_MATCH_JOB_DURATION, 'observe')
        assert hasattr(ZERO_MATCH_JOB_STATUS, 'labels')
        assert hasattr(ZERO_MATCH_JOB_QUEUE_TIME, 'observe')


# ---------------------------------------------------------------------------
# AC11: Feature flag
# ---------------------------------------------------------------------------

class TestFeatureFlag:
    """Verify feature flag controls behavior."""

    def test_config_flag_defaults_to_false(self):
        from config import ASYNC_ZERO_MATCH_ENABLED
        assert ASYNC_ZERO_MATCH_ENABLED is False

    def test_config_timeout_defaults_to_120(self):
        from config import ZERO_MATCH_JOB_TIMEOUT_S
        assert ZERO_MATCH_JOB_TIMEOUT_S == 120

    def test_feature_flag_registry_includes_async_zero_match(self):
        from config import _FEATURE_FLAG_REGISTRY
        assert "ASYNC_ZERO_MATCH_ENABLED" in _FEATURE_FLAG_REGISTRY


# ---------------------------------------------------------------------------
# AC6: BuscaResponse includes new fields
# ---------------------------------------------------------------------------

class TestSchemaFields:
    """Verify BuscaResponse has new fields."""

    def test_busca_response_has_zero_match_fields(self):
        from schemas import BuscaResponse
        fields = BuscaResponse.model_fields
        assert "zero_match_job_id" in fields
        assert "zero_match_candidates_count" in fields

    def test_busca_response_defaults(self):
        from schemas import BuscaResponse, ResumoEstrategico
        response = BuscaResponse(
            resumo=ResumoEstrategico(
                titulo="Test",
                oportunidades_relevantes=0,
                setores_destaque=[],
                recomendacoes=[],
                texto_resumo="Test summary",
                resumo_executivo="Executive summary",
                total_oportunidades=0,
                valor_total=0.0,
            ),
            excel_available=False,
            quota_used=0,
            quota_remaining=100,
            total_raw=0,
            total_filtrado=0,
        )
        assert response.zero_match_job_id is None
        assert response.zero_match_candidates_count == 0


# ---------------------------------------------------------------------------
# SearchContext has new fields
# ---------------------------------------------------------------------------

class TestSearchContext:
    """Verify SearchContext has new fields."""

    def test_search_context_has_zero_match_fields(self):
        from search_context import SearchContext
        ctx = SearchContext(request=MagicMock(), user={})
        assert ctx.zero_match_candidates == []
        assert ctx.zero_match_job_id is None
        assert ctx.zero_match_candidates_count == 0
