"""Unit tests for SearchPipeline Stages 4-5 (FilterResults + EnrichResults)."""

import pytest
import asyncio
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, AsyncMock
from search_context import SearchContext
from search_pipeline import SearchPipeline


# ============================================================================
# Helper factories
# ============================================================================

def make_deps(**overrides):
    """Create deps namespace with sensible defaults."""
    defaults = {
        "ENABLE_NEW_PRICING": False,
        "PNCPClient": MagicMock,
        "buscar_todas_ufs_paralelo": AsyncMock(return_value=[]),
        "aplicar_todos_filtros": MagicMock(return_value=([], {})),
        "create_excel": MagicMock(),
        "rate_limiter": MagicMock(),
        "check_user_roles": MagicMock(return_value=(False, False)),
        "match_keywords": MagicMock(return_value=(True, [])),
        "KEYWORDS_UNIFORMES": set(),
        "KEYWORDS_EXCLUSAO": set(),
        "validate_terms": MagicMock(return_value={"valid": [], "ignored": [], "reasons": {}}),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_request(**overrides):
    """Create a minimal BuscaRequest-like object."""
    defaults = {
        "ufs": ["SC"],
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
        "search_id": "test-search-123",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_ctx(**overrides):
    """Create a SearchContext with sensible defaults for filter/enrich testing."""
    request_overrides = overrides.pop("request_overrides", {})
    user = overrides.pop("user", {"id": "user-123", "email": "test@example.com"})
    ctx = SearchContext(
        request=make_request(**request_overrides),
        user=user,
    )
    # Set defaults that stages 1-3 would have set
    ctx.active_keywords = overrides.pop("active_keywords", {"uniforme", "jaleco"})
    ctx.active_exclusions = overrides.pop("active_exclusions", set())
    ctx.active_context_required = overrides.pop("active_context_required", None)
    ctx.custom_terms = overrides.pop("custom_terms", [])
    ctx.min_match_floor_value = overrides.pop("min_match_floor_value", None)
    ctx.licitacoes_raw = overrides.pop("licitacoes_raw", [])
    for k, v in overrides.items():
        setattr(ctx, k, v)
    return ctx


def _make_raw_licitacoes(n):
    """Generate n fake raw licitacao dicts."""
    return [
        {
            "objetoCompra": f"Aquisicao de uniformes lote {i}",
            "valorTotalEstimado": 1000.0 * (i + 1),
            "uf": "SC",
            "_matched_terms": ["uniforme"],
        }
        for i in range(n)
    ]


# ============================================================================
# Stage 4: FilterResults
# ============================================================================

class TestStageFilter:
    """Tests for SearchPipeline.stage_filter (Stage 4)."""

    @pytest.mark.asyncio
    async def test_basic_filter_passthrough(self):
        """aplicar_todos_filtros returns 5 of 10 raw items; ctx.licitacoes_filtradas has 5."""
        raw = _make_raw_licitacoes(10)
        filtered = raw[:5]
        stats = {"aprovadas": 5, "total": 10}

        deps = make_deps(
            aplicar_todos_filtros=MagicMock(return_value=(filtered, stats)),
        )
        ctx = make_ctx(licitacoes_raw=raw)
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        assert len(ctx.licitacoes_filtradas) == 5
        assert ctx.licitacoes_filtradas is filtered

    @pytest.mark.asyncio
    async def test_empty_results(self):
        """aplicar_todos_filtros returns 0 items; ctx.licitacoes_filtradas is empty."""
        raw = _make_raw_licitacoes(10)
        stats = {"aprovadas": 0, "total": 10}

        deps = make_deps(
            aplicar_todos_filtros=MagicMock(return_value=([], stats)),
        )
        ctx = make_ctx(licitacoes_raw=raw)
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        assert ctx.licitacoes_filtradas == []
        assert len(ctx.licitacoes_filtradas) == 0

    @pytest.mark.asyncio
    async def test_filter_stats_populated(self):
        """filter_stats dict from aplicar_todos_filtros is stored in ctx.filter_stats."""
        raw = _make_raw_licitacoes(10)
        expected_stats = {
            "total": 10,
            "aprovadas": 6,
            "rejeitadas_uf": 1,
            "rejeitadas_status": 1,
            "rejeitadas_keyword": 2,
            "rejeitadas_min_match": 0,
        }

        deps = make_deps(
            aplicar_todos_filtros=MagicMock(return_value=(raw[:6], expected_stats)),
        )
        ctx = make_ctx(licitacoes_raw=raw)
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        assert ctx.filter_stats is expected_stats
        assert ctx.filter_stats["total"] == 10
        assert ctx.filter_stats["aprovadas"] == 6
        assert ctx.filter_stats["rejeitadas_keyword"] == 2

    @pytest.mark.asyncio
    async def test_min_match_relaxation(self):
        """When custom_terms set and min_match_floor > 1, first filter returns 0 with
        hidden_by_min_match > 0, triggers second call with min_match_floor=None.
        Verify aplicar_todos_filtros called twice and filter_relaxed=True."""
        raw = _make_raw_licitacoes(10)
        relaxed_filtered = raw[:3]

        # First call: zero results, but some hidden by min_match
        first_stats = {"rejeitadas_min_match": 5, "aprovadas": 0, "total": 10}
        # Second call: relaxed filter returns 3 results
        second_stats = {"rejeitadas_min_match": 0, "aprovadas": 3, "total": 10}

        mock_filter = MagicMock(
            side_effect=[
                ([], first_stats),
                (relaxed_filtered, second_stats),
            ]
        )

        deps = make_deps(aplicar_todos_filtros=mock_filter)
        ctx = make_ctx(
            licitacoes_raw=raw,
            custom_terms=["uniforme escolar", "jaleco"],
            min_match_floor_value=2,
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        # aplicar_todos_filtros must have been called exactly twice
        assert mock_filter.call_count == 2

        # First call should have min_match_floor=2
        first_call_kwargs = mock_filter.call_args_list[0]
        assert first_call_kwargs.kwargs.get("min_match_floor") == 2 or \
            first_call_kwargs[1].get("min_match_floor") == 2

        # Second call should have min_match_floor=None (relaxed)
        second_call_kwargs = mock_filter.call_args_list[1]
        assert second_call_kwargs.kwargs.get("min_match_floor") is None or \
            second_call_kwargs[1].get("min_match_floor") is None

        assert ctx.filter_relaxed is True
        assert ctx.hidden_by_min_match == 0
        assert len(ctx.licitacoes_filtradas) == 3

    @pytest.mark.asyncio
    async def test_no_relaxation_when_results_found(self):
        """When custom_terms set and min_match_floor > 1, but first filter returns > 0
        results, no second call is made."""
        raw = _make_raw_licitacoes(10)
        filtered = raw[:4]
        stats = {"rejeitadas_min_match": 3, "aprovadas": 4, "total": 10}

        mock_filter = MagicMock(return_value=(filtered, stats))

        deps = make_deps(aplicar_todos_filtros=mock_filter)
        ctx = make_ctx(
            licitacoes_raw=raw,
            custom_terms=["uniforme escolar", "jaleco"],
            min_match_floor_value=2,
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        # Only one call - no relaxation needed
        assert mock_filter.call_count == 1
        assert ctx.filter_relaxed is False
        assert len(ctx.licitacoes_filtradas) == 4
        assert ctx.hidden_by_min_match == 3


# ============================================================================
# Stage 5: EnrichResults
# ============================================================================

class TestStageEnrich:
    """Tests for SearchPipeline.stage_enrich (Stage 5)."""

    @pytest.mark.asyncio
    @patch("search_pipeline.ordenar_licitacoes")
    @patch("search_pipeline.count_phrase_matches", return_value=1)
    @patch("search_pipeline.score_relevance", return_value=0.85)
    async def test_relevance_scoring_with_custom_terms(
        self, mock_score_relevance, mock_count_phrases, mock_ordenar
    ):
        """When custom_terms is set and licitacoes_filtradas has items with
        _matched_terms, _relevance_score must be populated on each item."""
        items = [
            {"objetoCompra": "Uniforme escolar", "_matched_terms": ["uniforme", "escolar"]},
            {"objetoCompra": "Jaleco hospitalar", "_matched_terms": ["jaleco"]},
        ]
        mock_ordenar.return_value = items

        deps = make_deps()
        ctx = make_ctx(
            licitacoes_filtradas=items,
            custom_terms=["uniforme", "escolar", "jaleco"],
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_enrich(ctx)

        # score_relevance should have been called for each item
        assert mock_score_relevance.call_count == 2

        # First item: 2 matched_terms out of 3 custom_terms, 1 phrase match
        mock_score_relevance.assert_any_call(2, 3, 1)
        # Second item: 1 matched_term out of 3 custom_terms, 1 phrase match
        mock_score_relevance.assert_any_call(1, 3, 1)

        # Each item should have _relevance_score set to 0.85
        for item in items:
            assert item["_relevance_score"] == 0.85

    @pytest.mark.asyncio
    @patch("search_pipeline.ordenar_licitacoes")
    @patch("search_pipeline.score_relevance")
    async def test_no_scoring_without_custom_terms(self, mock_score_relevance, mock_ordenar):
        """When custom_terms is empty, score_relevance should NOT be called and
        items should NOT have _relevance_score modified."""
        items = [
            {"objetoCompra": "Uniforme escolar", "_matched_terms": ["uniforme"]},
        ]
        mock_ordenar.return_value = items

        deps = make_deps()
        ctx = make_ctx(
            licitacoes_filtradas=items,
            custom_terms=[],  # No custom terms
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_enrich(ctx)

        # score_relevance must NOT have been called
        mock_score_relevance.assert_not_called()

        # Items should not have _relevance_score
        assert "_relevance_score" not in items[0]

    @pytest.mark.asyncio
    @patch("search_pipeline.sync_time_module")
    @patch("search_pipeline.ordenar_licitacoes")
    async def test_sorting_applied(self, mock_ordenar, mock_time_module):
        """When licitacoes_filtradas is non-empty, ordenar_licitacoes is called
        with the correct params (ordenacao and termos_busca)."""
        items = [
            {"objetoCompra": "Uniforme A", "_matched_terms": ["uniforme"]},
            {"objetoCompra": "Uniforme B", "_matched_terms": ["uniforme"]},
        ]
        sorted_items = list(reversed(items))
        mock_ordenar.return_value = sorted_items
        mock_time_module.time.return_value = 100.0

        deps = make_deps()
        ctx = make_ctx(
            licitacoes_filtradas=items,
            custom_terms=[],
            active_keywords={"uniforme", "jaleco"},
            request_overrides={"ordenacao": "data_desc"},
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_enrich(ctx)

        mock_ordenar.assert_called_once()
        call_kwargs = mock_ordenar.call_args
        assert call_kwargs.kwargs.get("ordenacao") == "data_desc" or \
            call_kwargs[1].get("ordenacao") == "data_desc"

        # Since custom_terms is empty, termos_busca should be from active_keywords (up to 10)
        termos_arg = call_kwargs.kwargs.get("termos_busca") or call_kwargs[1].get("termos_busca")
        # active_keywords is a set, so the list can be in any order — just check content
        assert set(termos_arg) <= {"uniforme", "jaleco"}
        assert len(termos_arg) <= 10

        # ctx.licitacoes_filtradas should be the sorted result
        assert ctx.licitacoes_filtradas is sorted_items
