"""CRIT-057: Time Budget Guard for Zero-Match LLM Classification.

Tests that the filter's zero-match loop respects a configurable time budget,
marking unclassified items as pending_review instead of blocking the pipeline.
"""

import time
from unittest.mock import patch, MagicMock, AsyncMock


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
    """AC1/AC2: Budget guard inside batch zero-match loop.

    The batch zero-match classifier and its budget guard moved out of the
    synchronous filter into the async ``classify_zero_match_job`` ARQ job
    (see ``backend/jobs/queue/jobs.py``). These tests exercise the job
    directly so the AC still has coverage post-architectural-move.
    """

    def _run_job(self, candidates: list[dict]):
        """Run classify_zero_match_job to completion synchronously for test assertions."""
        import asyncio
        from jobs.queue.jobs import classify_zero_match_job

        async def _noop_store(*args, **kwargs):
            return None

        with patch("jobs.queue.result_store.store_zero_match_results", side_effect=_noop_store), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=None):
            return asyncio.run(
                classify_zero_match_job(
                    ctx={},
                    search_id="crit057-test",
                    candidates=candidates,
                    setor="engenharia",
                    sector_name="Engenharia",
                )
            )

    @patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 5)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 0.05)  # Very short budget to trigger
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    @patch("config.MAX_ZERO_MATCH_ITEMS", 100)
    def test_budget_exceeded_marks_pending_review(self):
        """Budget of 0.05s + slow LLM batches -> interrupts, marks rest as pending_review."""
        licitacoes = [_make_lic(f"Equipamento de construcao civil numero {i:03d} para obra publica") for i in range(20)]

        def slow_classify_batch(items, setor_name=None, setor_id=None, search_id=None):
            time.sleep(0.1)  # Each batch takes 100ms, budget is 50ms
            return [{"is_primary": True, "confidence": 60, "evidence": []}] * len(items)

        with patch("llm_arbiter._classify_zero_match_batch", slow_classify_batch):
            result = self._run_job(licitacoes)

        # Some items should be pending_review with the budget-exceeded reason.
        pending = [lic for lic in licitacoes if lic.get("_pending_review")]
        assert len(pending) > 0, f"Expected pending_review items, got result: {result}"
        budget_pending = [
            lic for lic in pending
            if lic.get("_pending_review_reason") == "zero_match_budget_exceeded"
        ]
        assert len(budget_pending) > 0, (
            "Expected at least one item with "
            "_pending_review_reason='zero_match_budget_exceeded'"
        )
        for lic in budget_pending:
            assert lic["_relevance_source"] == "pending_review"
        assert result["pending"] > 0

    @patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 5)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 999)  # Very high budget -- never triggers
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    @patch("config.MAX_ZERO_MATCH_ITEMS", 100)
    def test_high_budget_classifies_all(self):
        """Budget of 999s + 10 items -> classifies all normally."""
        licitacoes = [_make_lic(f"Servico de engenharia e construcao civil numero {i:03d} para obras") for i in range(10)]

        call_count = 0

        def fast_classify_batch(items, setor_name=None, setor_id=None, search_id=None):
            nonlocal call_count
            call_count += 1
            return [{"is_primary": True, "confidence": 65, "evidence": ["match"]}] * len(items)

        with patch("llm_arbiter._classify_zero_match_batch", fast_classify_batch):
            result = self._run_job(licitacoes)

        # All 10 items classified, no budget-exceeded pending reviews.
        assert result["status"] == "completed"
        assert result["total_classified"] == 10
        assert result["approved"] == 10
        assert result["pending"] == 0
        assert call_count == 2  # 10 items / batch_size 5 = 2 calls
        budget_pending = [
            lic for lic in licitacoes
            if lic.get("_pending_review_reason") == "zero_match_budget_exceeded"
        ]
        assert len(budget_pending) == 0


class TestCrit057Metrics:
    """AC3: Prometheus metric observed correctly.

    Post-architectural-move the job emits ``ZERO_MATCH_JOB_DURATION`` from
    ``classify_zero_match_job`` rather than the filter observing a
    ``FILTER_ZERO_MATCH_DURATION`` counter in-line.
    """

    @patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 10)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 999)
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    @patch("config.MAX_ZERO_MATCH_ITEMS", 100)
    def test_metric_observed_on_completion(self):
        """ZERO_MATCH_JOB_DURATION metric is observed after classification."""
        import asyncio
        from jobs.queue.jobs import classify_zero_match_job

        licitacoes = [_make_lic(f"Servico especializado de construcao civil item {i:03d} para obras") for i in range(5)]

        def fast_batch(items, setor_name=None, setor_id=None, search_id=None):
            return [{"is_primary": True, "confidence": 60, "evidence": []}] * len(items)

        mock_metric = MagicMock()
        mock_status = MagicMock()

        async def _noop_store(*args, **kwargs):
            return None

        with patch("llm_arbiter._classify_zero_match_batch", fast_batch), \
             patch("metrics.ZERO_MATCH_JOB_DURATION", mock_metric), \
             patch("metrics.ZERO_MATCH_JOB_STATUS", mock_status), \
             patch("jobs.queue.result_store.store_zero_match_results", side_effect=_noop_store), \
             patch("progress.get_tracker", new_callable=AsyncMock, return_value=None):
            asyncio.run(
                classify_zero_match_job(
                    ctx={},
                    search_id="crit057-metrics",
                    candidates=licitacoes,
                    setor="engenharia",
                    sector_name="Engenharia",
                )
            )

        # Job duration metric observed exactly once (on happy-path exit).
        mock_metric.observe.assert_called_once()
        # Status counter labelled as completed on success.
        mock_status.labels.assert_any_call(status="completed")


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
    """AC1: FILTER_ZERO_MATCH_BUDGET_S config variable.

    Pattern 3 (see docs/sessions/2026-04/2026-04-19-bts-wave1-handoff.md):
    FILTER_ZERO_MATCH_BUDGET_S is parsed in ``config/features.py`` and
    only re-exported by the ``config`` package root. Reloading ``config``
    alone does NOT re-trigger ``os.getenv`` — we must reload
    ``config.features`` (the source of truth).
    """

    def test_default_value(self):
        """Default budget is 30 seconds."""
        import importlib
        import os
        old = os.environ.pop("FILTER_ZERO_MATCH_BUDGET_S", None)
        try:
            from config import features
            importlib.reload(features)
            assert features.FILTER_ZERO_MATCH_BUDGET_S == 30.0
        finally:
            if old is not None:
                os.environ["FILTER_ZERO_MATCH_BUDGET_S"] = old
            from config import features as _features_final
            importlib.reload(_features_final)

    def test_env_override(self):
        """Budget can be overridden via env var."""
        import importlib
        with patch.dict("os.environ", {"FILTER_ZERO_MATCH_BUDGET_S": "15"}):
            from config import features
            importlib.reload(features)
            assert features.FILTER_ZERO_MATCH_BUDGET_S == 15.0
        # Restore the module to its ambient default after the patch context exits.
        from config import features as _features_final
        importlib.reload(_features_final)
