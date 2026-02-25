"""Tests for GTM-STAB-005 AC6 — auto-relaxation and filter_stats in response.

Tests the auto-relaxation logic in SearchPipeline.stage_filter:
- Level 0: normal (no relaxation)
- Level 1: min_match_floor relaxed to None (existing behavior)
- Level 2: keyword filter removed entirely
- Level 3: top 10 by value (no filters beyond UF/status)

Also tests that filter_stats breakdown is included in the response when
total_from_sources > 0 but after_filter = 0.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from search_context import SearchContext
from search_pipeline import SearchPipeline


# ============================================================================
# Helper factories (mirrored from test_search_pipeline_filter_enrich.py)
# ============================================================================

def make_deps(**overrides):
    """Create deps namespace with sensible defaults."""
    defaults = {
        "ENABLE_NEW_PRICING": False,
        "PNCPClient": MagicMock,
        "buscar_todas_ufs_paralelo": MagicMock(return_value=[]),
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
        "search_id": "test-stab005-relaxation",
        "modo_busca": None,
        "check_sanctions": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_ctx(**overrides):
    """Create a SearchContext with sensible defaults for filter testing."""
    request_overrides = overrides.pop("request_overrides", {})
    user = overrides.pop("user", {"id": "user-stab005", "email": "test@example.com"})
    ctx = SearchContext(
        request=make_request(**request_overrides),
        user=user,
    )
    ctx.active_keywords = overrides.pop("active_keywords", {"uniforme", "jaleco"})
    ctx.active_exclusions = overrides.pop("active_exclusions", set())
    ctx.active_context_required = overrides.pop("active_context_required", None)
    ctx.custom_terms = overrides.pop("custom_terms", [])
    ctx.min_match_floor_value = overrides.pop("min_match_floor_value", None)
    ctx.licitacoes_raw = overrides.pop("licitacoes_raw", [])
    for k, v in overrides.items():
        setattr(ctx, k, v)
    return ctx


def _make_raw_licitacoes(n, uf="SC"):
    """Generate n fake raw licitacao dicts."""
    return [
        {
            "objetoCompra": f"Aquisicao de materiais diversos lote {i}",
            "valorTotalEstimado": 5000.0 * (i + 1),
            "uf": uf,
            "_matched_terms": [],
        }
        for i in range(n)
    ]


# ============================================================================
# Test: Auto-relaxation returns results when normal filtering returns 0
# ============================================================================

class TestAutoRelaxationReturnsResults:
    """STAB-005 AC6: When normal filtering returns 0, auto-relaxation kicks in."""

    @pytest.mark.asyncio
    async def test_level2_relaxation_when_normal_returns_zero(self):
        """Level 2: keyword filter removed → results recovered.

        Scenario: custom_terms set, normal filter returns 0, level-2 (no keywords)
        returns 5 results. Verifies relaxation_level=2 and results populated.
        """
        raw = _make_raw_licitacoes(20)
        l2_filtered = raw[:5]
        l2_stats = {"aprovadas": 5, "total": 20, "rejeitadas_keyword": 0}

        # First call (normal): zero results, all rejected by keyword
        normal_stats = {
            "aprovadas": 0, "total": 20,
            "rejeitadas_keyword": 15, "rejeitadas_uf": 0,
            "rejeitadas_valor": 5, "rejeitadas_min_match": 0,
            "rejeitadas_prazo": 0, "rejeitadas_outros": 0,
        }
        # Second call (level 2 relaxation): returns 5
        mock_filter = MagicMock(
            side_effect=[
                ([], normal_stats),       # normal: zero results
                (l2_filtered, l2_stats),  # level 2: keyword-free
            ]
        )

        deps = make_deps(aplicar_todos_filtros=mock_filter)
        ctx = make_ctx(
            licitacoes_raw=raw,
            custom_terms=["material escritorio", "papel A4"],
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        # Should have called filter twice: normal + level 2
        assert mock_filter.call_count == 2

        # Level 2 call should have keywords=None
        l2_call = mock_filter.call_args_list[1]
        assert l2_call.kwargs.get("keywords") is None
        assert l2_call.kwargs.get("exclusions") is None
        assert l2_call.kwargs.get("custom_terms") is None

        # Results recovered
        assert len(ctx.licitacoes_filtradas) == 5
        assert ctx.relaxation_level == 2

    @pytest.mark.asyncio
    async def test_level3_relaxation_top_by_value(self):
        """Level 3: when level 2 also returns 0, top 10 by value is returned.

        Scenario: custom_terms set, normal=0, level-2=0, level-3 returns
        top 10 sorted by valorTotalEstimado descending.
        """
        raw = _make_raw_licitacoes(15)
        # Make values varied for sorting verification
        for i, lic in enumerate(raw):
            lic["valorTotalEstimado"] = float((i + 1) * 10_000)

        normal_stats = {
            "aprovadas": 0, "total": 15,
            "rejeitadas_keyword": 10, "rejeitadas_valor": 5,
            "rejeitadas_uf": 0, "rejeitadas_min_match": 0,
            "rejeitadas_prazo": 0, "rejeitadas_outros": 0,
        }

        mock_filter = MagicMock(
            side_effect=[
                ([], normal_stats),  # normal: zero
                ([], {}),            # level 2: also zero
            ]
        )

        deps = make_deps(aplicar_todos_filtros=mock_filter)
        ctx = make_ctx(
            licitacoes_raw=raw,
            custom_terms=["material especifico"],
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        # Level 3: top 10 by value
        assert ctx.relaxation_level == 3
        assert len(ctx.licitacoes_filtradas) == 10

        # Should be sorted by value descending
        values = [l["valorTotalEstimado"] for l in ctx.licitacoes_filtradas]
        assert values == sorted(values, reverse=True)
        # Highest value is 15 * 10_000 = 150_000
        assert values[0] == 150_000.0


# ============================================================================
# Test: filter_stats included in response when filtrado=0
# ============================================================================

class TestFilterStatsInResponse:
    """STAB-005 AC6: filter_stats breakdown present when after_filter=0."""

    @pytest.mark.asyncio
    async def test_filter_stats_populated_on_zero_results(self):
        """When total_from_sources > 0 but after_filter = 0, ctx.filter_stats
        contains the full rejection breakdown."""
        raw = _make_raw_licitacoes(25)
        stats = {
            "total": 25,
            "aprovadas": 0,
            "rejeitadas_uf": 3,
            "rejeitadas_valor": 7,
            "rejeitadas_keyword": 10,
            "rejeitadas_min_match": 5,
            "rejeitadas_prazo": 0,
            "rejeitadas_outros": 0,
        }

        mock_filter = MagicMock(return_value=([], stats))
        deps = make_deps(aplicar_todos_filtros=mock_filter)
        ctx = make_ctx(licitacoes_raw=raw)
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        # filter_stats should have the full breakdown
        assert ctx.filter_stats["total"] == 25
        assert ctx.filter_stats["aprovadas"] == 0
        assert ctx.filter_stats["rejeitadas_uf"] == 3
        assert ctx.filter_stats["rejeitadas_valor"] == 7
        assert ctx.filter_stats["rejeitadas_keyword"] == 10
        assert ctx.filter_stats["rejeitadas_min_match"] == 5

    @pytest.mark.asyncio
    async def test_filter_summary_built_on_zero_results(self):
        """STAB-005 AC3: filter_summary is a human-readable string when results=0."""
        raw = _make_raw_licitacoes(20)
        stats = {
            "total": 20,
            "aprovadas": 0,
            "rejeitadas_uf": 5,
            "rejeitadas_valor": 8,
            "rejeitadas_keyword": 7,
            "rejeitadas_min_match": 0,
            "rejeitadas_prazo": 0,
            "rejeitadas_outros": 0,
        }

        mock_filter = MagicMock(return_value=([], stats))
        deps = make_deps(aplicar_todos_filtros=mock_filter)
        ctx = make_ctx(licitacoes_raw=raw)
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        # filter_summary should be present and descriptive
        assert ctx.filter_summary is not None
        assert "Nenhum resultado" in ctx.filter_summary
        assert "5 por UF" in ctx.filter_summary
        assert "8 por valor" in ctx.filter_summary
        assert "7 por keyword" in ctx.filter_summary


# ============================================================================
# Test: filter_relaxed=True and correct relaxation_level
# ============================================================================

class TestRelaxationLevelTracking:
    """Verify relaxation_level is set correctly at each level."""

    @pytest.mark.asyncio
    async def test_level0_no_relaxation(self):
        """When normal filtering returns results, relaxation_level stays 0."""
        raw = _make_raw_licitacoes(10)
        filtered = raw[:6]
        stats = {"aprovadas": 6, "total": 10, "rejeitadas_min_match": 0}

        mock_filter = MagicMock(return_value=(filtered, stats))
        deps = make_deps(aplicar_todos_filtros=mock_filter)
        ctx = make_ctx(
            licitacoes_raw=raw,
            custom_terms=["uniforme"],
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        assert ctx.relaxation_level == 0
        assert ctx.filter_relaxed is False
        assert len(ctx.licitacoes_filtradas) == 6

    @pytest.mark.asyncio
    async def test_level1_min_match_relaxation(self):
        """Level 1: min_match_floor relaxed, filter_relaxed=True, relaxation_level=1."""
        raw = _make_raw_licitacoes(10)
        relaxed_results = raw[:4]

        # First call: zero results, 8 hidden by min_match
        first_stats = {"rejeitadas_min_match": 8, "aprovadas": 0, "total": 10}
        # Second call (min_match=None): recovers 4 results, but still 0 after
        # level-2 check won't trigger because results > 0 after level 1
        second_stats = {"rejeitadas_min_match": 0, "aprovadas": 4, "total": 10}

        mock_filter = MagicMock(
            side_effect=[
                ([], first_stats),
                (relaxed_results, second_stats),
            ]
        )

        deps = make_deps(aplicar_todos_filtros=mock_filter)
        ctx = make_ctx(
            licitacoes_raw=raw,
            custom_terms=["uniforme escolar"],
            min_match_floor_value=3,
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        assert ctx.filter_relaxed is True
        assert ctx.relaxation_level == 1
        assert len(ctx.licitacoes_filtradas) == 4
        # Only 2 calls: normal + level-1 relaxation (level 2 not needed)
        assert mock_filter.call_count == 2


# ============================================================================
# Test: all relaxation levels fail → filter_stats still explains why
# ============================================================================

class TestAllRelaxationLevelsFail:
    """When all levels of relaxation still return 0, filter_stats shows why."""

    @pytest.mark.asyncio
    async def test_all_levels_zero_but_no_raw_items(self):
        """When licitacoes_raw is empty, no relaxation is attempted."""
        stats = {"aprovadas": 0, "total": 0}
        mock_filter = MagicMock(return_value=([], stats))
        deps = make_deps(aplicar_todos_filtros=mock_filter)
        ctx = make_ctx(
            licitacoes_raw=[],  # no raw data from sources
            custom_terms=["material"],
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        # No relaxation attempted because licitacoes_raw is empty
        assert mock_filter.call_count == 1
        assert ctx.relaxation_level == 0
        assert len(ctx.licitacoes_filtradas) == 0

    @pytest.mark.asyncio
    async def test_level2_and_3_fail_with_value_filter_rejects_all(self):
        """When normal=0, level-2=0, and even level-3 returns top by value,
        filter_stats from the normal run still shows the rejection breakdown."""
        raw = _make_raw_licitacoes(5)
        # Set all values to 0 so level 3 still picks them up (sorted by 0)
        for lic in raw:
            lic["valorTotalEstimado"] = 0.0

        normal_stats = {
            "total": 5, "aprovadas": 0,
            "rejeitadas_uf": 0, "rejeitadas_valor": 5,
            "rejeitadas_keyword": 0, "rejeitadas_min_match": 0,
            "rejeitadas_prazo": 0, "rejeitadas_outros": 0,
        }

        mock_filter = MagicMock(
            side_effect=[
                ([], normal_stats),  # normal: zero
                ([], {}),            # level 2: also zero
            ]
        )

        deps = make_deps(aplicar_todos_filtros=mock_filter)
        ctx = make_ctx(
            licitacoes_raw=raw,
            custom_terms=["material"],
        )
        pipeline = SearchPipeline(deps)

        await pipeline.stage_filter(ctx)

        # Level 3 kicks in — returns top by value even with 0 values
        assert ctx.relaxation_level == 3
        assert len(ctx.licitacoes_filtradas) == 5

        # filter_summary should have been built from the normal stats
        # (it was built when licitacoes_filtradas was still 0, before level 2/3)
        assert ctx.filter_summary is not None
        assert "5 por valor" in ctx.filter_summary
