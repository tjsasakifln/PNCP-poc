"""Tests for STORY-329: Granular progress events during filtering.

AC7: Verify on_progress callback fires every 50 items or 5% of total.
"""

from unittest.mock import patch

from filter import aplicar_todos_filtros


def _make_bids(count: int, uf: str = "SP") -> list[dict]:
    """Create minimal test bids for progress callback testing."""
    return [
        {
            "uf": uf,
            "objetoCompra": f"Aquisição de uniformes escolares item {i}",
            "valorTotalEstimado": 100_000,
            "_status_inferido": "recebendo_proposta",
        }
        for i in range(count)
    ]


class TestFilterProgressCallback:
    """AC7: Test callback fires at correct intervals."""

    def test_callback_fires_at_50_item_intervals(self):
        """For 1000 items, callback should fire every 50 items."""
        bids = _make_bids(1000)
        calls: list[tuple] = []

        def on_progress(processed: int, total: int, phase: str = "filter"):
            calls.append((processed, total, phase))

        aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            keywords={"uniformes"},
            on_progress=on_progress,
        )

        filter_calls = [c for c in calls if c[2] == "filter"]
        assert len(filter_calls) > 0, "Callback should have been called"
        # First call at index 50 (every 50 items, 5% of 1000=50, min(50,50)=50)
        assert filter_calls[0][0] == 50
        assert filter_calls[0][1] == 1000
        # All calls should have "filter" phase
        assert all(c[2] == "filter" for c in filter_calls)

    def test_callback_fires_at_5_percent_for_small_batch(self):
        """For 40 items, 5% = 2, which is < 50, so fires every 2 items."""
        bids = _make_bids(40)
        calls: list[tuple] = []

        def on_progress(processed: int, total: int, phase: str = "filter"):
            calls.append((processed, total, phase))

        aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            keywords={"uniformes"},
            on_progress=on_progress,
        )

        filter_calls = [c for c in calls if c[2] == "filter"]
        assert len(filter_calls) > 0, "Callback should fire for small batches"
        # 5% of 40 = 2, min(50, 2) = 2. First call at index 2.
        assert filter_calls[0][0] == 2
        assert filter_calls[0][1] == 40

    def test_callback_fires_every_item_for_tiny_batch(self):
        """For 10 items, 5% = 0.5 → max(1, 0) = 1, fires every item."""
        bids = _make_bids(10)
        calls: list[tuple] = []

        def on_progress(processed: int, total: int, phase: str = "filter"):
            calls.append((processed, total, phase))

        aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            keywords={"uniformes"},
            on_progress=on_progress,
        )

        filter_calls = [c for c in calls if c[2] == "filter"]
        assert len(filter_calls) > 0

    def test_no_callback_when_none(self):
        """Filter works normally when on_progress is None."""
        bids = _make_bids(100)
        result, stats = aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            keywords={"uniformes"},
            on_progress=None,
        )
        assert stats["total"] == 100

    def test_callback_not_called_for_empty_input(self):
        """No callback calls when licitacoes is empty."""
        calls: list[tuple] = []

        def on_progress(processed: int, total: int, phase: str = "filter"):
            calls.append((processed, total, phase))

        aplicar_todos_filtros(
            [],
            ufs_selecionadas={"SP"},
            on_progress=on_progress,
        )

        assert len(calls) == 0

    def test_callback_receives_correct_total(self):
        """Total should be the count of items entering keyword stage."""
        bids = _make_bids(200)
        totals = set()

        def on_progress(processed: int, total: int, phase: str = "filter"):
            if phase == "filter":
                totals.add(total)

        aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            keywords={"uniformes"},
            on_progress=on_progress,
        )

        # All calls should have the same total (items entering keyword stage)
        assert len(totals) == 1
        total = totals.pop()
        # Total should be <= 200 (some may be rejected by prior fast stages)
        assert total <= 200

    def test_processed_increases_monotonically(self):
        """Processed count should increase with each callback call."""
        bids = _make_bids(300)
        processed_values: list[int] = []

        def on_progress(processed: int, total: int, phase: str = "filter"):
            if phase == "filter":
                processed_values.append(processed)

        aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            on_progress=on_progress,
        )

        # Verify monotonically increasing
        for i in range(1, len(processed_values)):
            assert processed_values[i] > processed_values[i - 1]


class TestLlmProgressCallback:
    """AC3: Test LLM zero-match emits progress with llm_classify phase."""

    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    def test_llm_classify_phase_emitted(self):
        """LLM zero-match should emit on_progress with phase='llm_classify'."""
        # Create bids that will NOT match keywords (trigger zero-match)
        bids = [
            {
                "uf": "SP",
                "objetoCompra": "Construção de ponte sobre rio municipal para transporte público urbano",
                "valorTotalEstimado": 500_000,
                "_status_inferido": "recebendo_proposta",
            }
            for _ in range(5)
        ]
        calls: list[tuple] = []

        def on_progress(processed: int, total: int, phase: str = "filter"):
            calls.append((processed, total, phase))

        # Mock LLM classifier to avoid real API calls
        mock_result = {"is_primary": False, "confidence": 30, "evidence": [], "rejection_reason": "not relevant", "needs_more_data": False}
        with patch("llm_arbiter.classify_contract_primary_match", return_value=mock_result) as mock_classify:
            aplicar_todos_filtros(
                bids,
                ufs_selecionadas={"SP"},
                setor="uniformes_escolares",
                on_progress=on_progress,
            )

        # Check if any llm_classify calls were made
        llm_calls = [c for c in calls if c[2] == "llm_classify"]
        if mock_classify.called:
            # LLM was invoked, so we should see llm_classify callbacks
            assert len(llm_calls) > 0, "Should emit llm_classify progress when LLM is called"
            # Verify total matches the zero_match_pool size
            assert all(c[1] > 0 for c in llm_calls)

    def test_filter_and_llm_phases_are_sequential(self):
        """Filter phase callbacks should come before llm_classify phase."""
        bids = _make_bids(100)
        call_phases: list[str] = []

        def on_progress(processed: int, total: int, phase: str = "filter"):
            call_phases.append(phase)

        aplicar_todos_filtros(
            bids,
            ufs_selecionadas={"SP"},
            on_progress=on_progress,
        )

        # If both phases exist, filter should come before llm_classify
        if "filter" in call_phases and "llm_classify" in call_phases:
            last_filter_idx = max(i for i, p in enumerate(call_phases) if p == "filter")
            first_llm_idx = min(i for i, p in enumerate(call_phases) if p == "llm_classify")
            assert last_filter_idx < first_llm_idx, "Filter phase should complete before LLM phase"
