"""CRIT-057: Time Budget Guard for Zero-Match LLM Classification.

Tests that the filter's zero-match loop respects a configurable time budget,
marking unclassified items as pending_review instead of blocking the pipeline.
"""

import time
from unittest.mock import patch, MagicMock


def _make_lic(objeto: str = "Aquisicao de equipamentos de construcao civil para obras publicas", valor: float = 100_000.0) -> dict:
    """Create a minimal licitacao dict that passes UF + value filters but NOT keyword filter."""
    return {
        "objetoCompra": objeto,
        "valorTotalEstimado": valor,
        "uf": "SP",
        "orgaoEntidade": {"ufSigla": "SP"},
    }


def _fake_sector():
    """Return a real SectorConfig with safe defaults for testing."""
    from sectors import SectorConfig
    return SectorConfig(
        id="engenharia",
        name="Engenharia",
        description="Engenharia e Construcao",
        keywords=set(),  # Empty keywords = all items go to zero-match pool
        exclusions=set(),
        max_contract_value=None,
    )


class TestCrit057BatchBudgetGuard:
    """AC1/AC2: Budget guard inside batch zero-match loop."""

    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 5)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 0.05)  # Very short budget to trigger
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    def test_budget_exceeded_marks_pending_review(self):
        """Budget of 0.05s + slow LLM batches -> interrupts, marks rest as pending_review."""
        from filter import aplicar_todos_filtros

        # Create 20 items (4 batches of 5)
        licitacoes = [_make_lic(f"Equipamento de construcao civil numero {i:03d} para obra publica") for i in range(20)]

        call_count = 0

        def slow_classify_batch(items, setor_name=None, setor_id=None, termos_busca=None):
            nonlocal call_count
            call_count += 1
            time.sleep(0.1)  # Each batch takes 100ms, budget is 50ms
            return [{"is_primary": True, "confidence": 60, "evidence": []}] * len(items)

        with patch("llm_arbiter._classify_zero_match_batch", slow_classify_batch), \
             patch("llm_arbiter.classify_contract_primary_match", return_value={"is_primary": False}), \
             patch("sectors.get_sector") as mock_sector:
            mock_sector.return_value = _fake_sector()

            resultado, stats = aplicar_todos_filtros(
                licitacoes=licitacoes,
                ufs_selecionadas={"SP"},
                setor="engenharia",
            )

        # Budget should have been exceeded
        assert stats.get("zero_match_budget_exceeded", 0) > 0, \
            f"Expected budget exceeded items, got stats: {stats}"
        # Some items should be pending_review
        pending = [lic for lic in licitacoes if lic.get("_pending_review")]
        assert len(pending) > 0, "Expected some items marked as pending_review"
        # Pending items should have correct reason
        for lic in pending:
            assert lic["_pending_review_reason"] == "zero_match_budget_exceeded"
            assert lic["_relevance_source"] == "pending_review"

    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 5)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 999)  # Very high budget -- never triggers
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    def test_high_budget_classifies_all(self):
        """Budget of 999s + 10 items -> classifies all normally."""
        from filter import aplicar_todos_filtros

        licitacoes = [_make_lic(f"Servico de engenharia e construcao civil numero {i:03d} para obras") for i in range(10)]

        def fast_classify_batch(items, setor_name=None, setor_id=None, termos_busca=None):
            return [{"is_primary": True, "confidence": 65, "evidence": ["match"]}] * len(items)

        with patch("llm_arbiter._classify_zero_match_batch", fast_classify_batch), \
             patch("llm_arbiter.classify_contract_primary_match", return_value={"is_primary": False}), \
             patch("sectors.get_sector") as mock_sector:
            mock_sector.return_value = _fake_sector()

            resultado, stats = aplicar_todos_filtros(
                licitacoes=licitacoes,
                ufs_selecionadas={"SP"},
                setor="engenharia",
            )

        # No budget exceeded
        assert stats.get("zero_match_budget_exceeded", 0) == 0
        # All should be classified
        assert stats.get("llm_zero_match_calls", 0) == 10
        pending = [lic for lic in licitacoes if lic.get("_pending_review")]
        assert len(pending) == 0, "No items should be pending_review with high budget"


class TestCrit057Metrics:
    """AC3: Prometheus metric observed correctly."""

    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 10)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 999)
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    def test_metric_observed_on_completion(self):
        """FILTER_ZERO_MATCH_DURATION metric is observed after classification."""
        from filter import aplicar_todos_filtros

        licitacoes = [_make_lic(f"Servico especializado de construcao civil item {i:03d} para obras") for i in range(5)]

        def fast_batch(items, setor_name=None, setor_id=None, termos_busca=None):
            return [{"is_primary": True, "confidence": 60, "evidence": []}] * len(items)

        mock_metric = MagicMock()
        with patch("llm_arbiter._classify_zero_match_batch", fast_batch), \
             patch("llm_arbiter.classify_contract_primary_match", return_value={"is_primary": False}), \
             patch("metrics.FILTER_ZERO_MATCH_DURATION", mock_metric), \
             patch("sectors.get_sector") as mock_sector:
            mock_sector.return_value = _fake_sector()

            aplicar_todos_filtros(
                licitacoes=licitacoes,
                ufs_selecionadas={"SP"},
                setor="engenharia",
            )

        # Metric should have been observed
        mock_metric.labels.assert_called()
        call_kwargs = mock_metric.labels.call_args[1]
        assert call_kwargs["mode"] == "batch"
        assert call_kwargs["budget_exceeded"] == "false"


class TestCrit057SearchContext:
    """AC4: SearchContext fields populated correctly."""

    def test_search_context_has_zero_match_fields(self):
        """SearchContext has the CRIT-057 fields with correct defaults."""
        from search_context import SearchContext

        ctx = SearchContext(request=None, user={})
        assert ctx.zero_match_budget_exceeded is False
        assert ctx.zero_match_classified == 0
        assert ctx.zero_match_deferred == 0

    def test_search_context_fields_settable(self):
        """SearchContext fields can be set."""
        from search_context import SearchContext

        ctx = SearchContext(request=None, user={})
        ctx.zero_match_budget_exceeded = True
        ctx.zero_match_classified = 50
        ctx.zero_match_deferred = 150
        assert ctx.zero_match_budget_exceeded is True
        assert ctx.zero_match_classified == 50
        assert ctx.zero_match_deferred == 150


class TestCrit057FilterStatsSchema:
    """AC2: FilterStats schema includes zero_match_budget_exceeded."""

    def test_filter_stats_has_budget_field(self):
        """FilterStats includes zero_match_budget_exceeded with default 0."""
        from schemas import FilterStats

        fs = FilterStats()
        assert fs.zero_match_budget_exceeded == 0

    def test_filter_stats_budget_field_serializes(self):
        """FilterStats.zero_match_budget_exceeded appears in JSON."""
        from schemas import FilterStats

        fs = FilterStats(zero_match_budget_exceeded=42)
        data = fs.model_dump()
        assert data["zero_match_budget_exceeded"] == 42


class TestCrit057ConfigVar:
    """AC1: FILTER_ZERO_MATCH_BUDGET_S config variable."""

    def test_default_value(self):
        """Default budget is 30 seconds."""
        import importlib
        import os
        old = os.environ.pop("FILTER_ZERO_MATCH_BUDGET_S", None)
        try:
            import config
            importlib.reload(config)
            assert config.FILTER_ZERO_MATCH_BUDGET_S == 30.0
        finally:
            if old is not None:
                os.environ["FILTER_ZERO_MATCH_BUDGET_S"] = old
            importlib.reload(config)

    def test_env_override(self):
        """Budget can be overridden via env var."""
        import importlib
        with patch.dict("os.environ", {"FILTER_ZERO_MATCH_BUDGET_S": "15"}):
            import config
            importlib.reload(config)
            assert config.FILTER_ZERO_MATCH_BUDGET_S == 15.0
            importlib.reload(config)
