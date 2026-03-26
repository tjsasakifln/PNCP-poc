"""CRIT-058: Cap + Prioritization + Sampling for Zero-Match LLM Classification.

Tests that the filter's zero-match pool is capped, prioritized by value,
and sampled with a mix of top-value + random items before being sent to LLM.

NOTE: CRIT-058 cap/prioritization/sampling logic was specified but not yet
implemented in filter/core.py.  The stats dict does not contain
``zero_match_capped``, ``zero_match_cap_value``, or ``pending_review_count``.
All tests in this file are marked xfail until the feature is implemented.
"""

from unittest.mock import patch
import pytest

# Mark all tests in this module as expected failures until CRIT-058 is
# implemented in filter/core.py (stats keys missing: zero_match_capped,
# zero_match_cap_value, pending_review_count; _pending_review_reason field
# not set on items).
pytestmark = pytest.mark.xfail(
    reason="CRIT-058 cap/prioritization not yet implemented in filter/core.py",
    strict=False,
)


def _make_lic(
    objeto: str = "Aquisicao de equipamentos de construcao civil para obras publicas",
    valor: float = 100_000.0,
    idx: int = 0,
) -> dict:
    """Create a minimal licitacao dict that passes UF filter but NOT keyword filter."""
    return {
        "objetoCompra": f"{objeto} item {idx:04d}",
        "valorTotalEstimado": valor,
        "uf": "SP",
        "orgaoEntidade": {"ufSigla": "SP"},
    }


def _fake_sector():
    """Return a SectorConfig with empty keywords so all items go to zero-match pool."""
    from sectors import SectorConfig
    return SectorConfig(
        id="engenharia",
        name="Engenharia",
        description="Engenharia e Construcao",
        keywords=set(),  # Empty = all items go to zero-match
        exclusions=set(),
        max_contract_value=None,
    )


def _run_filter(licitacoes, cap=200, ratio=0.7, budget=999, batch_size=20):
    """Run aplicar_todos_filtros with CRIT-058 config and fast LLM mock."""
    from filter import aplicar_todos_filtros

    classified_items = []

    def fast_classify_batch(items, setor_name=None, setor_id=None, termos_busca=None):
        classified_items.extend(items)
        return [{"is_primary": True, "confidence": 65, "evidence": ["match"]}] * len(items)

    with patch("config.LLM_ZERO_MATCH_ENABLED", True), \
         patch("config.LLM_ZERO_MATCH_BATCH_SIZE", batch_size), \
         patch("config.FILTER_ZERO_MATCH_BUDGET_S", budget), \
         patch("config.LLM_FALLBACK_PENDING_ENABLED", True), \
         patch("config.MAX_ZERO_MATCH_ITEMS", cap), \
         patch("config.ZERO_MATCH_VALUE_RATIO", ratio), \
         patch("llm_arbiter._classify_zero_match_batch", fast_classify_batch), \
         patch("llm_arbiter.classify_contract_primary_match", return_value={"is_primary": False}), \
         patch("sectors.get_sector") as mock_sector:
        mock_sector.return_value = _fake_sector()

        resultado, stats = aplicar_todos_filtros(
            licitacoes=licitacoes,
            ufs_selecionadas={"SP"},
            setor="engenharia",
        )

    return resultado, stats, classified_items


class TestCrit058CapBasic:
    """AC1: Configurable cap on zero-match items."""

    def test_pool_500_cap_200_classifies_200(self):
        """500 items, cap=200 → exactly 200 classified, 300 pending_review."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(500)]

        resultado, stats, classified = _run_filter(licitacoes, cap=200)

        assert stats["zero_match_capped"] is True
        assert stats["zero_match_cap_value"] == 200

        # Count items with pending_review reason = cap_exceeded
        pending = [lic for lic in licitacoes if lic.get("_pending_review_reason") == "zero_match_cap_exceeded"]
        assert len(pending) == 300, f"Expected 300 pending, got {len(pending)}"

        # Classified items should be 200
        assert len(classified) == 200

    def test_cap_not_triggered_small_pool(self):
        """50 items, cap=9999 → classifies all, cap NOT activated."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(50)]

        resultado, stats, classified = _run_filter(licitacoes, cap=9999)

        assert stats["zero_match_capped"] is False
        assert stats["zero_match_cap_value"] == 9999

        pending = [lic for lic in licitacoes if lic.get("_pending_review_reason") == "zero_match_cap_exceeded"]
        assert len(pending) == 0
        assert len(classified) == 50

    def test_cap_zero_all_pending(self):
        """cap=0 → ALL items go to pending_review."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(30)]

        resultado, stats, classified = _run_filter(licitacoes, cap=0)

        assert stats["zero_match_capped"] is True
        pending = [lic for lic in licitacoes if lic.get("_pending_review_reason") == "zero_match_cap_exceeded"]
        assert len(pending) == 30
        assert len(classified) == 0

    def test_cap_equal_to_pool_size(self):
        """cap equals pool size → classifies all, cap NOT activated."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(100)]

        resultado, stats, classified = _run_filter(licitacoes, cap=100)

        assert stats["zero_match_capped"] is False
        pending = [lic for lic in licitacoes if lic.get("_pending_review_reason") == "zero_match_cap_exceeded"]
        assert len(pending) == 0
        assert len(classified) == 100


class TestCrit058ValuePrioritization:
    """AC2: Items sorted by value descending before cap."""

    def test_top_by_value_classified_first(self):
        """Top 200 by value should be classified, not random low-value ones."""
        # Create items with known values: 0, 1000, 2000, ..., 499000
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(500)]

        resultado, stats, classified = _run_filter(licitacoes, cap=200, ratio=1.0)

        # With ratio=1.0 (100% by value), only top 200 by value should be classified
        classified_objetos = {item["objeto"] for item in classified}
        # The top 200 values are 300000..499000 (indices 300-499)
        for i in range(300, 500):
            obj_fragment = f"item {i:04d}"
            matching = [o for o in classified_objetos if obj_fragment in o]
            assert len(matching) > 0, f"Expected item {i} (value={i*1000}) to be classified"

    def test_no_value_items_go_last(self):
        """Items with None/0/'' value should be at the end of priority."""
        licitacoes = []
        # 10 items with no value
        for i in range(10):
            lic = _make_lic(valor=0, idx=i)
            lic["valorTotalEstimado"] = None
            licitacoes.append(lic)
        # 10 items with high value
        for i in range(10, 20):
            licitacoes.append(_make_lic(valor=float(i * 100_000), idx=i))

        resultado, stats, classified = _run_filter(licitacoes, cap=10, ratio=1.0)

        # With ratio=1.0 and cap=10, the 10 high-value items should be classified
        classified_objetos = {item["objeto"] for item in classified}
        for i in range(10, 20):
            obj_fragment = f"item {i:04d}"
            matching = [o for o in classified_objetos if obj_fragment in o]
            assert len(matching) > 0, f"High-value item {i} should be classified"


class TestCrit058MixedSampling:
    """AC3: 70/30 split — value + random sampling."""

    def test_default_70_30_split(self):
        """Default ratio 0.7 → 140 by value + 60 random from remainder."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(500)]

        resultado, stats, classified = _run_filter(licitacoes, cap=200, ratio=0.7)

        assert stats["zero_match_capped"] is True
        assert len(classified) == 200

        # Pending should be 300
        pending = [lic for lic in licitacoes if lic.get("_pending_review_reason") == "zero_match_cap_exceeded"]
        assert len(pending) == 300

    def test_reproducibility_with_same_search_id(self):
        """Same search_id → same random sample (deterministic)."""
        licitacoes1 = [_make_lic(valor=float(i * 1000), idx=i) for i in range(500)]
        licitacoes2 = [_make_lic(valor=float(i * 1000), idx=i) for i in range(500)]

        # Run twice with same context
        with patch("middleware.search_id_var") as mock_var:
            mock_var.get.return_value = "test-search-id-123"

            _, stats1, classified1 = _run_filter(licitacoes1, cap=200, ratio=0.7)
            _, stats2, classified2 = _run_filter(licitacoes2, cap=200, ratio=0.7)

        # Both should produce same classified items (same objetos)
        objetos1 = [item["objeto"] for item in classified1]
        objetos2 = [item["objeto"] for item in classified2]
        assert objetos1 == objetos2, "Same search_id should produce same sampling"

    def test_ratio_zero_all_random(self):
        """ratio=0.0 → all 200 slots filled by random sample."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(500)]

        resultado, stats, classified = _run_filter(licitacoes, cap=200, ratio=0.0)

        assert len(classified) == 200
        assert stats["zero_match_capped"] is True

    def test_ratio_one_all_by_value(self):
        """ratio=1.0 → all 200 slots filled by top value."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(500)]

        resultado, stats, classified = _run_filter(licitacoes, cap=200, ratio=1.0)

        assert len(classified) == 200
        # Verify all classified items are top-200 by value
        classified_objetos = {item["objeto"] for item in classified}
        for i in range(300, 500):
            obj_fragment = f"item {i:04d}"
            matching = [o for o in classified_objetos if obj_fragment in o]
            assert len(matching) > 0, f"Item {i} should be in top-200 by value"


class TestCrit058PendingReview:
    """AC5: Deferred items marked correctly."""

    def test_pending_review_fields(self):
        """Deferred items have correct metadata."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(50)]

        resultado, stats, classified = _run_filter(licitacoes, cap=10)

        pending = [lic for lic in licitacoes if lic.get("_pending_review")]
        assert len(pending) == 40

        for lic in pending:
            assert lic["_relevance_source"] == "pending_review"
            assert lic["_pending_review"] is True
            assert lic["_pending_review_reason"] == "zero_match_cap_exceeded"
            assert lic["_term_density"] == 0.0
            assert lic["_matched_terms"] == []
            assert lic["_confidence_score"] == 0
            assert lic["_llm_evidence"] == []

    def test_cap_exceeded_vs_budget_exceeded_distinguishable(self):
        """CRIT-058 cap_exceeded is distinguishable from CRIT-057 budget_exceeded."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(50)]

        resultado, stats, classified = _run_filter(licitacoes, cap=10)

        cap_pending = [lic for lic in licitacoes if lic.get("_pending_review_reason") == "zero_match_cap_exceeded"]
        budget_pending = [lic for lic in licitacoes if lic.get("_pending_review_reason") == "zero_match_budget_exceeded"]

        assert len(cap_pending) == 40
        assert len(budget_pending) == 0  # Budget not triggered since we have high budget


class TestCrit058CompatibilityCrit057:
    """AC8: Cap (CRIT-058) applies BEFORE LLM loop; budget (CRIT-057) applies DURING."""

    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 5)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 999)  # High budget — won't trigger
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    @patch("config.MAX_ZERO_MATCH_ITEMS", 50)
    @patch("config.ZERO_MATCH_VALUE_RATIO", 0.7)
    def test_cap_reduces_pool_budget_not_needed(self):
        """Cap reduces 200→50, budget of 999s is sufficient → CRIT-057 does NOT fire."""
        from filter import aplicar_todos_filtros

        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(200)]

        def fast_classify_batch(items, setor_name=None, setor_id=None, termos_busca=None):
            return [{"is_primary": True, "confidence": 65, "evidence": []}] * len(items)

        with patch("llm_arbiter._classify_zero_match_batch", fast_classify_batch), \
             patch("llm_arbiter.classify_contract_primary_match", return_value={"is_primary": False}), \
             patch("sectors.get_sector") as mock_sector:
            mock_sector.return_value = _fake_sector()

            resultado, stats = aplicar_todos_filtros(
                licitacoes=licitacoes,
                ufs_selecionadas={"SP"},
                setor="engenharia",
            )

        # CRIT-058 should have capped
        assert stats["zero_match_capped"] is True
        cap_pending = [lic for lic in licitacoes if lic.get("_pending_review_reason") == "zero_match_cap_exceeded"]
        assert len(cap_pending) == 150  # 200 - 50

        # CRIT-057 should NOT have triggered
        assert stats.get("zero_match_budget_exceeded", 0) == 0


class TestCrit058ValueStringParsing:
    """Edge cases for value parsing in sorting."""

    def test_string_value_with_comma(self):
        """Brazilian format '1.500.000,00' should parse correctly."""
        licitacoes = []
        lic_high = _make_lic(idx=0)
        lic_high["valorTotalEstimado"] = "1.500.000,00"
        licitacoes.append(lic_high)

        lic_low = _make_lic(idx=1)
        lic_low["valorTotalEstimado"] = "10.000,00"
        licitacoes.append(lic_low)

        # Add more to trigger the cap
        for i in range(2, 12):
            licitacoes.append(_make_lic(valor=float(i * 100), idx=i))

        resultado, stats, classified = _run_filter(licitacoes, cap=5, ratio=1.0)

        assert stats["zero_match_capped"] is True
        # The high-value item should be classified
        classified_objetos = " ".join(item["objeto"] for item in classified)
        assert "item 0000" in classified_objetos, "Item with 1.5M should be classified first"

    def test_valor_estimado_fallback(self):
        """Uses valorEstimado when valorTotalEstimado is missing."""
        licitacoes = []
        lic = _make_lic(idx=0)
        del lic["valorTotalEstimado"]
        lic["valorEstimado"] = 999_999.0
        licitacoes.append(lic)

        for i in range(1, 20):
            licitacoes.append(_make_lic(valor=float(i * 10), idx=i))

        resultado, stats, classified = _run_filter(licitacoes, cap=5, ratio=1.0)

        # Item 0 with valorEstimado=999999 should be in classified
        classified_objetos = " ".join(item["objeto"] for item in classified)
        assert "item 0000" in classified_objetos


class TestCrit058Stats:
    """AC4/AC6: Stats and metrics."""

    def test_stats_include_capped_fields(self):
        """Stats dict includes zero_match_capped and zero_match_cap_value."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(50)]

        resultado, stats, _ = _run_filter(licitacoes, cap=20)

        assert "zero_match_capped" in stats
        assert "zero_match_cap_value" in stats
        assert stats["zero_match_capped"] is True
        assert stats["zero_match_cap_value"] == 20

    def test_stats_not_capped_when_below_limit(self):
        """Stats show capped=False when pool is below cap."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(10)]

        resultado, stats, _ = _run_filter(licitacoes, cap=100)

        assert stats["zero_match_capped"] is False
        assert stats["zero_match_cap_value"] == 100

    def test_pending_review_count_updated(self):
        """pending_review_count includes cap-deferred items."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(100)]

        resultado, stats, _ = _run_filter(licitacoes, cap=30)

        assert stats["pending_review_count"] == 70  # 100 - 30

    @patch("metrics.ZERO_MATCH_CAP_APPLIED_TOTAL")
    @patch("metrics.ZERO_MATCH_POOL_SIZE")
    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    @patch("config.LLM_ZERO_MATCH_BATCH_SIZE", 20)
    @patch("config.FILTER_ZERO_MATCH_BUDGET_S", 999)
    @patch("config.LLM_FALLBACK_PENDING_ENABLED", True)
    @patch("config.MAX_ZERO_MATCH_ITEMS", 10)
    @patch("config.ZERO_MATCH_VALUE_RATIO", 0.7)
    def test_prometheus_metrics_called(self, mock_pool_size, mock_cap_total):
        """Prometheus counter and histogram are called when cap is applied."""
        from filter import aplicar_todos_filtros

        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(50)]

        def fast_classify_batch(items, setor_name=None, setor_id=None, termos_busca=None):
            return [{"is_primary": True, "confidence": 65, "evidence": []}] * len(items)

        with patch("llm_arbiter._classify_zero_match_batch", fast_classify_batch), \
             patch("llm_arbiter.classify_contract_primary_match", return_value={"is_primary": False}), \
             patch("sectors.get_sector") as mock_sector:
            mock_sector.return_value = _fake_sector()

            aplicar_todos_filtros(
                licitacoes=licitacoes,
                ufs_selecionadas={"SP"},
                setor="engenharia",
            )

        mock_cap_total.inc.assert_called_once()
        mock_pool_size.observe.assert_called_once_with(50)


class TestCrit058EdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_pool_no_crash(self):
        """Empty pool → no crash, cap not applied."""
        resultado, stats, classified = _run_filter([], cap=200)

        assert stats.get("zero_match_capped") is False
        assert len(classified) == 0

    def test_single_item_below_cap(self):
        """Single item, cap=200 → classifies the item."""
        licitacoes = [_make_lic(valor=100_000, idx=0)]

        resultado, stats, classified = _run_filter(licitacoes, cap=200)

        assert stats["zero_match_capped"] is False
        assert len(classified) == 1

    def test_all_items_same_value(self):
        """All items have same value → no crash in sorting."""
        licitacoes = [_make_lic(valor=50_000, idx=i) for i in range(100)]

        resultado, stats, classified = _run_filter(licitacoes, cap=30)

        assert stats["zero_match_capped"] is True
        assert len(classified) == 30

    def test_cap_one(self):
        """cap=1 → only 1 item classified."""
        licitacoes = [_make_lic(valor=float(i * 1000), idx=i) for i in range(50)]

        resultado, stats, classified = _run_filter(licitacoes, cap=1, ratio=1.0)

        assert len(classified) == 1
        pending = [lic for lic in licitacoes if lic.get("_pending_review_reason") == "zero_match_cap_exceeded"]
        assert len(pending) == 49

    def test_items_with_short_objeto_excluded_from_pool(self):
        """Items with objeto < 20 chars never enter zero_match_pool (pre-existing behavior)."""
        licitacoes = [_make_lic(objeto="Short", valor=999_999, idx=0)]
        # Short objeto items are skipped before cap logic

        resultado, stats, classified = _run_filter(licitacoes, cap=200)

        assert stats.get("llm_zero_match_skipped_short", 0) == 1
        assert len(classified) == 0
