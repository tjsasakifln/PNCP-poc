"""
Tests for GTM-RESILIENCE-D01 — Item Inspection for Gray Zone Bids.

AC9: 8 tests covering fetch, majority rule, domain signals, budget, timeout, cache.
"""

import time
from unittest.mock import patch, MagicMock

import pytest

from item_inspector import (
    classify_item,
    apply_majority_rule,
    inspect_bids_in_filter,
    _fetch_items_sync,
    _items_cache,
    _cache_key,
    _get_cached_items,
    _put_cached_items,
    clear_cache,
    get_cache_stats,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def _clear_item_cache():
    """Clear item cache before each test."""
    clear_cache()
    yield
    clear_cache()


VESTUARIO_KEYWORDS = {"uniforme", "fardamento", "jaleco", "camiseta", "calça", "bota"}
VESTUARIO_NCM = ["61", "62", "6505"]
VESTUARIO_UNITS = ["peça", "peca", "kit", "conjunto", "par"]
VESTUARIO_SIZES = [r"\bP\b", r"\bM\b", r"\bG\b", r"\bGG\b"]


def _make_item(descricao="", ncm="", unidade="", quantidade=1, valor=10.0):
    """Helper to create a mock item dict."""
    return {
        "descricao": descricao,
        "codigoNcm": ncm,
        "unidadeMedida": unidade,
        "quantidade": quantidade,
        "valorUnitario": valor,
    }


def _make_bid(
    cnpj="12345678000100",
    ano="2026",
    sequencial="1",
    objeto="Registro de preços para materiais diversos",
    density=0.03,
):
    """Helper to create a mock bid dict."""
    return {
        "orgaoEntidade": {"cnpj": cnpj},
        "anoCompra": ano,
        "sequencialCompra": sequencial,
        "objetoCompra": objeto,
        "_term_density": density,
    }


# ============================================================================
# AC9 Test 1: fetch_bid_items returns structured data (mock HTTP)
# ============================================================================

class TestFetchItems:
    """AC1: fetch_bid_items returns structured data with mock HTTP."""

    @patch("item_inspector.httpx.get")
    def test_fetch_returns_structured_items(self, mock_get):
        """Test that fetch parses PNCP response into structured item dicts."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "descricao": "Camiseta polo manga curta",
                "materialOuServico": {"codigoNcm": "61051000"},
                "unidadeMedida": "PEÇA",
                "quantidade": 500,
                "valorUnitarioEstimado": 45.00,
            },
            {
                "descricao": "Caneta esferográfica",
                "materialOuServico": {"codigoNcm": "96081000"},
                "unidadeMedida": "UNIDADE",
                "quantidade": 1000,
                "valorUnitarioEstimado": 2.50,
            },
        ]
        mock_get.return_value = mock_response

        items = _fetch_items_sync("12345678000100", "2026", "1")

        assert len(items) == 2
        assert items[0]["descricao"] == "Camiseta polo manga curta"
        assert items[0]["codigoNcm"] == "61051000"
        assert items[0]["unidadeMedida"] == "PEÇA"
        assert items[1]["descricao"] == "Caneta esferográfica"

    @patch("item_inspector.httpx.get")
    def test_fetch_returns_empty_on_404(self, mock_get):
        """Test that 404 returns empty list without error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        items = _fetch_items_sync("12345678000100", "2026", "999")
        assert items == []

    @patch("item_inspector.httpx.get")
    def test_fetch_returns_empty_on_timeout(self, mock_get):
        """Test that timeout returns empty list."""
        import httpx
        mock_get.side_effect = httpx.TimeoutException("timeout")

        items = _fetch_items_sync("12345678000100", "2026", "1")
        assert items == []


# ============================================================================
# AC9 Test 2: majority rule accepts bid with 8/10 items matching
# ============================================================================

class TestMajorityRuleAccept:
    """AC3: Majority rule accepts when >50% items match."""

    def test_accepts_80_percent_matching(self):
        """8/10 items matching → accepted (80% > 50%)."""
        items = [
            _make_item(descricao="camiseta polo azul tamanho M"),
            _make_item(descricao="calça social preta"),
            _make_item(descricao="jaleco branco manga longa"),
            _make_item(descricao="bota de segurança"),
            _make_item(descricao="uniforme completo feminino"),
            _make_item(descricao="camiseta manga curta"),
            _make_item(descricao="fardamento operacional"),
            _make_item(descricao="jaleco hospitalar"),
            # Non-matching:
            _make_item(descricao="papel A4 resma"),
            _make_item(descricao="caneta esferográfica azul"),
        ]

        accepted, ratio, matching, total = apply_majority_rule(
            items, VESTUARIO_KEYWORDS, VESTUARIO_NCM, VESTUARIO_UNITS, VESTUARIO_SIZES
        )

        assert accepted is True
        assert matching == 8
        assert total == 10
        assert ratio == pytest.approx(0.8)


# ============================================================================
# AC9 Test 3: majority rule rejects bid with 4/10 items matching
# ============================================================================

class TestMajorityRuleReject:
    """AC3: Majority rule rejects when <=50% items match."""

    def test_rejects_40_percent_matching(self):
        """4/10 items matching → rejected (40% ≤ 50%)."""
        items = [
            _make_item(descricao="camiseta polo azul"),
            _make_item(descricao="calça social preta"),
            _make_item(descricao="jaleco branco"),
            _make_item(descricao="bota de segurança"),
            # Non-matching (6):
            _make_item(descricao="papel A4 resma"),
            _make_item(descricao="caneta esferográfica"),
            _make_item(descricao="grampeador de mesa"),
            _make_item(descricao="toner para impressora"),
            _make_item(descricao="fita adesiva transparente"),
            _make_item(descricao="envelope ofício"),
        ]

        accepted, ratio, matching, total = apply_majority_rule(
            items, VESTUARIO_KEYWORDS, VESTUARIO_NCM, VESTUARIO_UNITS, VESTUARIO_SIZES
        )

        assert accepted is False
        assert matching == 4
        assert total == 10
        assert ratio == pytest.approx(0.4)


# ============================================================================
# AC9 Test 4: domain signals NCM prefix match
# ============================================================================

class TestDomainSignalsNCM:
    """AC4: NCM prefix match classifies item as matching."""

    def test_ncm_prefix_match(self):
        """Item with NCM 61051000 matches prefix '61' → score >= 1.0."""
        item = _make_item(
            descricao="produto têxtil genérico",  # No keyword match
            ncm="61051000",
        )

        score = classify_item(
            item, VESTUARIO_KEYWORDS, VESTUARIO_NCM, VESTUARIO_UNITS, VESTUARIO_SIZES
        )
        assert score >= 1.0

    def test_ncm_no_match(self):
        """Item with NCM 96081000 (pen) doesn't match vestuario prefixes."""
        item = _make_item(
            descricao="produto genérico",
            ncm="96081000",
        )

        score = classify_item(
            item, VESTUARIO_KEYWORDS, VESTUARIO_NCM, VESTUARIO_UNITS, VESTUARIO_SIZES
        )
        assert score < 1.0

    def test_unit_pattern_boost(self):
        """Unit pattern 'peça' adds 0.5 boost to keyword match."""
        item = _make_item(
            descricao="uniforme operacional",
            unidade="peça",
        )

        score = classify_item(
            item, VESTUARIO_KEYWORDS, VESTUARIO_NCM, VESTUARIO_UNITS, VESTUARIO_SIZES
        )
        # keyword match (1.0) + unit boost (0.5) = 1.5
        assert score == pytest.approx(1.5)

    def test_size_pattern_boost(self):
        """Size pattern in description adds 0.5 boost."""
        item = _make_item(
            descricao="uniforme tamanho M masculino",
        )

        score = classify_item(
            item, VESTUARIO_KEYWORDS, VESTUARIO_NCM, VESTUARIO_UNITS, VESTUARIO_SIZES
        )
        # keyword match (1.0) + size boost (0.5) = 1.5
        assert score == pytest.approx(1.5)

    def test_max_score_capped_at_2(self):
        """Score is capped at 2.0 even with multiple boosts."""
        item = _make_item(
            descricao="uniforme tamanho G",
            ncm="61051000",
            unidade="peça",
        )

        score = classify_item(
            item, VESTUARIO_KEYWORDS, VESTUARIO_NCM, VESTUARIO_UNITS, VESTUARIO_SIZES
        )
        # NCM match (1.0) + unit boost (0.5) + size boost (0.5) = 2.0 (capped)
        assert score == pytest.approx(2.0)


# ============================================================================
# AC9 Test 5: budget of 20 not exceeded (21st bid goes to LLM)
# ============================================================================

class TestBudget:
    """AC6: Budget of MAX_ITEM_INSPECTIONS is not exceeded."""

    @patch("item_inspector._fetch_items_sync")
    @patch("config.get_feature_flag", return_value=True)
    @patch("config.MAX_ITEM_INSPECTIONS", 5)
    def test_budget_not_exceeded(self, mock_ff, mock_fetch):
        """21 bids but budget=5: only 5 fetch, rest go to remaining."""
        mock_fetch.return_value = [
            _make_item(descricao="uniforme azul"),
            _make_item(descricao="uniforme verde"),
        ]

        bids = [_make_bid(sequencial=str(i)) for i in range(21)]

        accepted, remaining, metrics = inspect_bids_in_filter(
            gray_zone_bids=bids,
            sector_keywords=VESTUARIO_KEYWORDS,
            ncm_prefixes=VESTUARIO_NCM,
            unit_patterns=VESTUARIO_UNITS,
            size_patterns=VESTUARIO_SIZES,
        )

        # Only 5 fetches should have occurred (budget limit)
        assert mock_fetch.call_count <= 5
        # Remaining should have the overflow bids
        assert len(remaining) >= 16  # 21 - 5 = 16 minimum


# ============================================================================
# AC9 Test 6: timeout per fetch respected
# ============================================================================

class TestTimeout:
    """AC1: 5s timeout per fetch is respected."""

    @patch("item_inspector.httpx.get")
    def test_timeout_per_fetch(self, mock_get):
        """Timeout on fetch returns empty list (no crash)."""
        import httpx
        mock_get.side_effect = httpx.TimeoutException("connect timeout")

        result = _fetch_items_sync("12345678000100", "2026", "1", timeout=5.0)
        assert result == []
        # Should have tried 2x (initial + 1 retry)
        assert mock_get.call_count == 2


# ============================================================================
# AC9 Test 7: cache hit doesn't count against budget
# ============================================================================

class TestCacheHit:
    """AC7: Cache hit doesn't count against budget."""

    @patch("item_inspector._fetch_items_sync")
    @patch("config.get_feature_flag", return_value=True)
    @patch("config.MAX_ITEM_INSPECTIONS", 2)
    def test_cache_hit_preserves_budget(self, mock_ff, mock_fetch):
        """Pre-cached bid doesn't consume budget — all budget available for others."""
        # Pre-populate cache for bid 0
        _put_cached_items(
            _cache_key("12345678000100", "2026", "0"),
            [_make_item(descricao="uniforme azul"), _make_item(descricao="uniforme verde")],
        )

        # Fetch returns matching items for other bids
        mock_fetch.return_value = [
            _make_item(descricao="uniforme azul"),
            _make_item(descricao="uniforme verde"),
        ]

        # 3 bids: bid 0 (cached) + bid 1, bid 2 (need fetch)
        bids = [_make_bid(sequencial=str(i)) for i in range(3)]

        accepted, remaining, metrics = inspect_bids_in_filter(
            gray_zone_bids=bids,
            sector_keywords=VESTUARIO_KEYWORDS,
            ncm_prefixes=VESTUARIO_NCM,
            unit_patterns=VESTUARIO_UNITS,
            size_patterns=VESTUARIO_SIZES,
        )

        # Cache hit + 2 fetches = 3 total inspected, but only 2 budget used
        assert metrics["item_inspections_cache_hits"] == 1
        # All 3 should be accepted (all have matching items)
        assert len(accepted) == 3


# ============================================================================
# AC9 Test 8: Integration — 3 gray zone bids, mixed results
# ============================================================================

class TestIntegration:
    """Integration: 3 bids in gray zone, 2 accepted by item inspection, 1 to LLM."""

    @patch("item_inspector._fetch_items_sync")
    @patch("config.get_feature_flag", return_value=True)
    def test_mixed_results(self, mock_ff, mock_fetch):
        """3 bids: 2 have majority matching items, 1 doesn't."""

        def _fetch_side_effect(cnpj, ano, seq, timeout=5.0):
            if seq == "1":
                # 8/10 matching → accept
                return [
                    _make_item(descricao="uniforme polo azul"),
                    _make_item(descricao="calça social preta"),
                    _make_item(descricao="jaleco branco"),
                    _make_item(descricao="bota segurança"),
                    _make_item(descricao="camiseta manga curta"),
                    _make_item(descricao="fardamento operacional"),
                    _make_item(descricao="uniforme feminino"),
                    _make_item(descricao="camiseta polo verde"),
                    _make_item(descricao="papel A4"),
                    _make_item(descricao="caneta azul"),
                ]
            elif seq == "2":
                # 7/10 matching → accept
                return [
                    _make_item(descricao="uniforme escolar"),
                    _make_item(descricao="calça uniforme"),
                    _make_item(descricao="camiseta aluno"),
                    _make_item(descricao="jaleco laboratório"),
                    _make_item(descricao="bota borracha"),
                    _make_item(descricao="uniforme esportivo"),
                    _make_item(descricao="camiseta educação física"),
                    _make_item(descricao="mouse óptico"),
                    _make_item(descricao="teclado USB"),
                    _make_item(descricao="monitor LED"),
                ]
            elif seq == "3":
                # 2/10 matching → reject (go to LLM)
                return [
                    _make_item(descricao="uniforme polo"),
                    _make_item(descricao="calça social"),
                    _make_item(descricao="papel sulfite A4"),
                    _make_item(descricao="caneta esferográfica"),
                    _make_item(descricao="grampeador"),
                    _make_item(descricao="clips metal"),
                    _make_item(descricao="cola bastão"),
                    _make_item(descricao="borracha escolar"),
                    _make_item(descricao="lápis grafite"),
                    _make_item(descricao="tesoura escritório"),
                ]
            return []

        mock_fetch.side_effect = _fetch_side_effect

        bids = [_make_bid(sequencial=str(i)) for i in range(1, 4)]

        accepted, remaining, metrics = inspect_bids_in_filter(
            gray_zone_bids=bids,
            sector_keywords=VESTUARIO_KEYWORDS,
            ncm_prefixes=VESTUARIO_NCM,
            unit_patterns=VESTUARIO_UNITS,
            size_patterns=VESTUARIO_SIZES,
        )

        assert len(accepted) == 2
        assert len(remaining) == 1
        assert metrics["item_inspections_accepted"] == 2
        assert metrics["item_inspections_performed"] == 3

        # Accepted bids should have item_inspection source
        for bid in accepted:
            assert bid["_relevance_source"] == "item_inspection"
            assert "_item_inspection_detail" in bid


# ============================================================================
# Additional edge case tests
# ============================================================================

class TestEdgeCases:
    """Additional edge cases for robustness."""

    def test_empty_items_list(self):
        """Empty items → reject."""
        accepted, ratio, matching, total = apply_majority_rule(
            [], VESTUARIO_KEYWORDS, VESTUARIO_NCM, VESTUARIO_UNITS, VESTUARIO_SIZES
        )
        assert accepted is False
        assert total == 0

    def test_exactly_50_percent(self):
        """50% matching → reject (need >50%, not >=50%)."""
        items = [
            _make_item(descricao="uniforme azul"),
            _make_item(descricao="papel A4"),
        ]
        accepted, ratio, matching, total = apply_majority_rule(
            items, VESTUARIO_KEYWORDS, VESTUARIO_NCM, VESTUARIO_UNITS, VESTUARIO_SIZES
        )
        assert accepted is False
        assert ratio == pytest.approx(0.5)

    def test_cache_lru_eviction(self):
        """Cache evicts oldest when over capacity."""
        from item_inspector import _CACHE_MAX_SIZE

        # Fill cache to capacity + 1
        for i in range(_CACHE_MAX_SIZE + 1):
            _put_cached_items(f"key_{i}", [_make_item(descricao=f"item_{i}")])

        assert len(_items_cache) == _CACHE_MAX_SIZE
        # Oldest key should be evicted
        assert _get_cached_items("key_0") is None
        # Newest should exist
        assert _get_cached_items(f"key_{_CACHE_MAX_SIZE}") is not None

    def test_cache_stats(self):
        """Cache stats returns correct values."""
        _put_cached_items("test_key", [_make_item(descricao="test")])
        stats = get_cache_stats()
        assert stats["item_cache_size"] == 1
        assert stats["item_cache_max"] == 1000

    @patch("config.get_feature_flag", return_value=False)
    def test_feature_flag_disabled(self, mock_ff):
        """When ITEM_INSPECTION_ENABLED=false, all bids go to remaining."""
        bids = [_make_bid(sequencial="1")]

        accepted, remaining, metrics = inspect_bids_in_filter(
            gray_zone_bids=bids,
            sector_keywords=VESTUARIO_KEYWORDS,
            ncm_prefixes=VESTUARIO_NCM,
            unit_patterns=VESTUARIO_UNITS,
            size_patterns=VESTUARIO_SIZES,
        )

        assert len(accepted) == 0
        assert len(remaining) == 1
        assert metrics["item_inspections_performed"] == 0
