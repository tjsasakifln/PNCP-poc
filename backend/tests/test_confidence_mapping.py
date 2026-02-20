"""
C-02 AC3: Tests for confidence field mapping.

Tests that relevance_source is correctly mapped to confidence level:
- keyword -> high
- llm_standard -> medium
- llm_conservative -> low
- llm_zero_match -> low
- None -> None (backward compat)
"""

import pytest
from search_pipeline import _map_confidence


class TestMapConfidence:
    """C-02 AC3: Unit tests for _map_confidence()."""

    def test_keyword_maps_to_high(self):
        """AC3.1: keyword -> high."""
        assert _map_confidence("keyword") == "high"

    def test_llm_standard_maps_to_medium(self):
        """AC3.2: llm_standard -> medium."""
        assert _map_confidence("llm_standard") == "medium"

    def test_llm_conservative_maps_to_low(self):
        """AC3.3: llm_conservative -> low."""
        assert _map_confidence("llm_conservative") == "low"

    def test_llm_zero_match_maps_to_low(self):
        """AC3.4: llm_zero_match -> low."""
        assert _map_confidence("llm_zero_match") == "low"

    def test_none_maps_to_none(self):
        """AC3.5: None -> None (backward compat)."""
        assert _map_confidence(None) is None

    def test_empty_string_maps_to_none(self):
        """Empty string should map to None."""
        assert _map_confidence("") is None

    def test_unknown_source_maps_to_none(self):
        """Unknown relevance source should map to None."""
        assert _map_confidence("unknown_source") is None


class TestConfidenceInLicitacaoItem:
    """C-02 AC1: Test that confidence field exists in schema."""

    def test_confidence_field_exists(self):
        """AC1.1: LicitacaoItem includes confidence field."""
        from schemas import LicitacaoItem
        fields = LicitacaoItem.model_fields
        assert "confidence" in fields

    def test_confidence_is_optional(self):
        """AC1.2: confidence is Optional for backward compatibility."""
        from schemas import LicitacaoItem
        item = LicitacaoItem(
            pncp_id="test-123",
            objeto="Test object",
            orgao="Test org",
            uf="SP",
            valor=100000.0,
            link="https://pncp.gov.br/test",
        )
        assert item.confidence is None

    def test_confidence_accepts_valid_values(self):
        """AC1.3: confidence accepts high, medium, low."""
        from schemas import LicitacaoItem
        for level in ["high", "medium", "low"]:
            item = LicitacaoItem(
                pncp_id="test-123",
                objeto="Test object",
                orgao="Test org",
                uf="SP",
                valor=100000.0,
                link="https://pncp.gov.br/test",
                confidence=level,
            )
            assert item.confidence == level


class TestConfidenceOrdenacao:
    """C-02 AC8: Test confidence sorting in ordenacao."""

    def test_confianca_sort_orders_high_first(self):
        """AC8.1: Sorting by confianca puts keyword (high) first."""
        from utils.ordenacao import ordenar_licitacoes

        licitacoes = [
            {"objetoCompra": "C", "_relevance_source": "llm_zero_match", "_confidence_score": 60, "valorTotalEstimado": 100000},
            {"objetoCompra": "A", "_relevance_source": "keyword", "_confidence_score": 95, "valorTotalEstimado": 50000},
            {"objetoCompra": "B", "_relevance_source": "llm_standard", "_confidence_score": 75, "valorTotalEstimado": 200000},
        ]
        result = ordenar_licitacoes(licitacoes, "confianca")
        assert result[0]["objetoCompra"] == "A"  # keyword = high
        assert result[1]["objetoCompra"] == "B"  # llm_standard = medium
        assert result[2]["objetoCompra"] == "C"  # llm_zero_match = low

    def test_confianca_sort_null_last(self):
        """AC8.2: Results without confidence go last."""
        from utils.ordenacao import ordenar_licitacoes

        licitacoes = [
            {"objetoCompra": "Legacy", "valorTotalEstimado": 100000},
            {"objetoCompra": "High", "_relevance_source": "keyword", "_confidence_score": 95, "valorTotalEstimado": 50000},
        ]
        result = ordenar_licitacoes(licitacoes, "confianca")
        assert result[0]["objetoCompra"] == "High"
        assert result[1]["objetoCompra"] == "Legacy"

    def test_confianca_sort_within_same_level_by_value(self):
        """AC8.3: Within same confidence level, sort by value descending."""
        from utils.ordenacao import ordenar_licitacoes

        licitacoes = [
            {"objetoCompra": "Small", "_relevance_source": "keyword", "_confidence_score": 95, "valorTotalEstimado": 50000},
            {"objetoCompra": "Big", "_relevance_source": "keyword", "_confidence_score": 95, "valorTotalEstimado": 500000},
        ]
        result = ordenar_licitacoes(licitacoes, "confianca")
        assert result[0]["objetoCompra"] == "Big"
        assert result[1]["objetoCompra"] == "Small"

    def test_confianca_is_valid_ordenacao_option(self):
        """AC8.4: 'confianca' is accepted by BuscaRequest schema."""
        from schemas import BuscaRequest
        req = BuscaRequest(
            ufs=["SP"],
            data_inicial="2026-01-01",
            data_final="2026-01-10",
            ordenacao="confianca",
        )
        assert req.ordenacao == "confianca"
