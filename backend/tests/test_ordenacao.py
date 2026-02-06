"""
Tests for the ordenacao module.

Tests cover:
- Date parsing with various formats
- Value parsing with Brazilian and US formats
- Relevance calculation
- Sorting by all criteria
- Edge cases (None, invalid data, empty lists)
"""

import pytest
from datetime import datetime

from utils.ordenacao import (
    parse_date,
    parse_valor,
    calcular_relevancia,
    ordenar_licitacoes,
)


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_iso_format_with_z(self):
        """Parse ISO format with Z timezone."""
        result = parse_date("2026-02-06T10:00:00Z")
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 6
        assert result.hour == 10

    def test_parse_iso_format_with_milliseconds(self):
        """Parse ISO format with milliseconds."""
        result = parse_date("2026-02-06T10:00:00.123Z")
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 6

    def test_parse_iso_format_with_offset(self):
        """Parse ISO format with timezone offset."""
        result = parse_date("2026-02-06T10:00:00+00:00")
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 6

    def test_parse_date_only(self):
        """Parse date-only format."""
        result = parse_date("2026-02-06")
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 6

    def test_parse_brazilian_format(self):
        """Parse Brazilian date format DD/MM/YYYY."""
        result = parse_date("06/02/2026")
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 6

    def test_parse_brazilian_format_with_time(self):
        """Parse Brazilian format with time."""
        result = parse_date("06/02/2026 10:30:00")
        assert result.year == 2026
        assert result.month == 2
        assert result.day == 6
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_none_returns_min(self):
        """None should return datetime.min."""
        result = parse_date(None)
        assert result == datetime.min

    def test_parse_empty_string_returns_min(self):
        """Empty string should return datetime.min."""
        result = parse_date("")
        assert result == datetime.min

    def test_parse_invalid_string_returns_min(self):
        """Invalid string should return datetime.min."""
        result = parse_date("not a date")
        assert result == datetime.min

    def test_parse_non_string_returns_min(self):
        """Non-string input should return datetime.min."""
        result = parse_date(12345)  # type: ignore
        assert result == datetime.min

    def test_parse_whitespace_is_stripped(self):
        """Whitespace should be stripped."""
        result = parse_date("  2026-02-06  ")
        assert result.year == 2026


class TestParseValor:
    """Tests for parse_valor function."""

    def test_parse_float(self):
        """Parse float value."""
        result = parse_valor(150000.50)
        assert result == 150000.50

    def test_parse_int(self):
        """Parse integer value."""
        result = parse_valor(150000)
        assert result == 150000.0

    def test_parse_brazilian_format(self):
        """Parse Brazilian format 1.234.567,89."""
        result = parse_valor("1.234.567,89")
        assert result == 1234567.89

    def test_parse_brazilian_decimal_only(self):
        """Parse Brazilian format with comma decimal only."""
        result = parse_valor("150000,50")
        assert result == 150000.50

    def test_parse_us_format(self):
        """Parse US format with dot decimal."""
        result = parse_valor("150000.50")
        assert result == 150000.50

    def test_parse_integer_string(self):
        """Parse integer string."""
        result = parse_valor("150000")
        assert result == 150000.0

    def test_parse_none_returns_zero(self):
        """None should return 0.0."""
        result = parse_valor(None)
        assert result == 0.0

    def test_parse_empty_string_returns_zero(self):
        """Empty string should return 0.0."""
        result = parse_valor("")
        assert result == 0.0

    def test_parse_invalid_string_returns_zero(self):
        """Invalid string should return 0.0."""
        result = parse_valor("not a number")
        assert result == 0.0

    def test_parse_non_string_non_numeric_returns_zero(self):
        """Non-string, non-numeric input should return 0.0."""
        result = parse_valor([1, 2, 3])  # type: ignore
        assert result == 0.0

    def test_parse_whitespace_is_stripped(self):
        """Whitespace should be stripped."""
        result = parse_valor("  150000  ")
        assert result == 150000.0

    def test_parse_large_brazilian_value(self):
        """Parse large Brazilian formatted value."""
        result = parse_valor("10.500.000,00")
        assert result == 10500000.00


class TestCalcularRelevancia:
    """Tests for calcular_relevancia function."""

    def test_all_terms_match(self):
        """All search terms match - should return 1.0."""
        licitacao = {"objetoCompra": "Aquisição de uniformes escolares"}
        result = calcular_relevancia(licitacao, ["uniforme", "escolar"])
        assert result == 1.0

    def test_partial_match(self):
        """Some terms match - should return partial score."""
        licitacao = {"objetoCompra": "Aquisição de uniformes escolares"}
        result = calcular_relevancia(licitacao, ["uniforme", "hospital"])
        assert result == 0.5

    def test_no_match(self):
        """No terms match - should return 0.0."""
        licitacao = {"objetoCompra": "Serviços de limpeza"}
        result = calcular_relevancia(licitacao, ["uniforme", "escola"])
        assert result == 0.0

    def test_empty_terms_returns_zero(self):
        """Empty terms list should return 0.0."""
        licitacao = {"objetoCompra": "Qualquer coisa"}
        result = calcular_relevancia(licitacao, [])
        assert result == 0.0

    def test_matches_in_descricao(self):
        """Terms in descricao should match."""
        licitacao = {
            "objetoCompra": "Licitação para aquisição",
            "descricao": "Uniformes escolares para alunos"
        }
        result = calcular_relevancia(licitacao, ["uniforme"])
        assert result == 1.0

    def test_matches_in_nome_orgao(self):
        """Terms in nomeOrgao should match."""
        licitacao = {
            "objetoCompra": "Aquisição de materiais",
            "nomeOrgao": "Escola Municipal de Uniformes"
        }
        result = calcular_relevancia(licitacao, ["uniforme"])
        assert result == 1.0

    def test_case_insensitive_matching(self):
        """Matching should be case insensitive."""
        licitacao = {"objetoCompra": "UNIFORMES ESCOLARES"}
        result = calcular_relevancia(licitacao, ["uniforme"])
        assert result == 1.0

    def test_accent_insensitive_matching(self):
        """Matching should ignore accents."""
        licitacao = {"objetoCompra": "Aquisição de jalecos médicos"}
        result = calcular_relevancia(licitacao, ["medico"])
        assert result == 1.0

    def test_empty_licitacao(self):
        """Empty licitacao should return 0.0."""
        licitacao = {}
        result = calcular_relevancia(licitacao, ["uniforme"])
        assert result == 0.0

    def test_none_values_in_licitacao(self):
        """None values in licitacao should be handled."""
        licitacao = {
            "objetoCompra": None,
            "descricao": None,
            "nomeOrgao": "Prefeitura Municipal"
        }
        result = calcular_relevancia(licitacao, ["prefeitura"])
        assert result == 1.0


class TestOrdenarLicitacoes:
    """Tests for ordenar_licitacoes function."""

    @pytest.fixture
    def sample_licitacoes(self):
        """Sample licitacoes for testing."""
        return [
            {
                "objetoCompra": "Uniformes escolares",
                "dataPublicacao": "2026-01-15",
                "valorTotalEstimado": 150000.0,
                "dataAberturaProposta": "2026-02-01",
            },
            {
                "objetoCompra": "Jalecos para hospital",
                "dataPublicacao": "2026-02-01",
                "valorTotalEstimado": 300000.0,
                "dataAberturaProposta": "2026-02-15",
            },
            {
                "objetoCompra": "Fardamento militar",
                "dataPublicacao": "2026-01-01",
                "valorTotalEstimado": 50000.0,
                "dataAberturaProposta": "2026-01-20",
            },
        ]

    def test_data_desc_default(self, sample_licitacoes):
        """Default ordering should be data_desc (most recent first)."""
        result = ordenar_licitacoes(sample_licitacoes)
        assert result[0]["objetoCompra"] == "Jalecos para hospital"
        assert result[1]["objetoCompra"] == "Uniformes escolares"
        assert result[2]["objetoCompra"] == "Fardamento militar"

    def test_data_desc_explicit(self, sample_licitacoes):
        """Explicit data_desc ordering."""
        result = ordenar_licitacoes(sample_licitacoes, "data_desc")
        assert result[0]["dataPublicacao"] == "2026-02-01"

    def test_data_asc(self, sample_licitacoes):
        """data_asc ordering (oldest first)."""
        result = ordenar_licitacoes(sample_licitacoes, "data_asc")
        assert result[0]["objetoCompra"] == "Fardamento militar"
        assert result[2]["objetoCompra"] == "Jalecos para hospital"

    def test_valor_desc(self, sample_licitacoes):
        """valor_desc ordering (highest value first)."""
        result = ordenar_licitacoes(sample_licitacoes, "valor_desc")
        assert result[0]["valorTotalEstimado"] == 300000.0
        assert result[1]["valorTotalEstimado"] == 150000.0
        assert result[2]["valorTotalEstimado"] == 50000.0

    def test_valor_asc(self, sample_licitacoes):
        """valor_asc ordering (lowest value first)."""
        result = ordenar_licitacoes(sample_licitacoes, "valor_asc")
        assert result[0]["valorTotalEstimado"] == 50000.0
        assert result[2]["valorTotalEstimado"] == 300000.0

    def test_prazo_asc(self, sample_licitacoes):
        """prazo_asc ordering (nearest deadline first)."""
        result = ordenar_licitacoes(sample_licitacoes, "prazo_asc")
        assert result[0]["dataAberturaProposta"] == "2026-01-20"
        assert result[1]["dataAberturaProposta"] == "2026-02-01"
        assert result[2]["dataAberturaProposta"] == "2026-02-15"

    def test_relevancia_ordering(self, sample_licitacoes):
        """relevancia ordering (most relevant first)."""
        termos = ["uniforme", "escolar"]
        result = ordenar_licitacoes(sample_licitacoes, "relevancia", termos)
        # "Uniformes escolares" matches both terms
        assert result[0]["objetoCompra"] == "Uniformes escolares"

    def test_empty_list(self):
        """Empty list should return empty list."""
        result = ordenar_licitacoes([])
        assert result == []

    def test_single_item(self):
        """Single item list should return the same item."""
        licitacoes = [{"objetoCompra": "Test", "dataPublicacao": "2026-01-01"}]
        result = ordenar_licitacoes(licitacoes)
        assert len(result) == 1
        assert result[0]["objetoCompra"] == "Test"

    def test_invalid_ordenacao_uses_default(self, sample_licitacoes):
        """Invalid ordering option should fall back to data_desc."""
        result = ordenar_licitacoes(sample_licitacoes, "invalid_option")
        # Should use data_desc (default)
        assert result[0]["objetoCompra"] == "Jalecos para hospital"

    def test_does_not_mutate_original(self, sample_licitacoes):
        """Sorting should not mutate the original list."""
        original_first = sample_licitacoes[0]["objetoCompra"]
        ordenar_licitacoes(sample_licitacoes, "valor_desc")
        assert sample_licitacoes[0]["objetoCompra"] == original_first

    def test_handles_missing_date_field(self):
        """Missing date fields should be handled gracefully."""
        licitacoes = [
            {"objetoCompra": "A", "dataPublicacao": "2026-02-01"},
            {"objetoCompra": "B"},  # Missing dataPublicacao
            {"objetoCompra": "C", "dataPublicacao": "2026-01-01"},
        ]
        result = ordenar_licitacoes(licitacoes, "data_desc")
        # Items with valid dates should come first (in order)
        assert result[0]["objetoCompra"] == "A"
        assert result[1]["objetoCompra"] == "C"
        # Item with missing date (datetime.min) should be last
        assert result[2]["objetoCompra"] == "B"

    def test_handles_none_value_field(self):
        """None value fields should be handled gracefully."""
        licitacoes = [
            {"objetoCompra": "A", "valorTotalEstimado": 100000},
            {"objetoCompra": "B", "valorTotalEstimado": None},
            {"objetoCompra": "C", "valorTotalEstimado": 200000},
        ]
        result = ordenar_licitacoes(licitacoes, "valor_desc")
        assert result[0]["objetoCompra"] == "C"
        assert result[1]["objetoCompra"] == "A"
        # Item with None value (0.0) should be last
        assert result[2]["objetoCompra"] == "B"

    def test_alternative_field_names(self):
        """Should handle alternative field names from PNCP API."""
        licitacoes = [
            {
                "objetoCompra": "A",
                "dataPublicacaoPncp": "2026-02-01",  # Alternative name
                "valorEstimado": 100000,  # Alternative name
            },
            {
                "objetoCompra": "B",
                "dataPublicacaoPncp": "2026-01-01",
                "valorEstimado": 200000,
            },
        ]
        result = ordenar_licitacoes(licitacoes, "data_desc")
        assert result[0]["objetoCompra"] == "A"

        result = ordenar_licitacoes(licitacoes, "valor_desc")
        assert result[0]["objetoCompra"] == "B"

    def test_relevancia_with_no_terms(self, sample_licitacoes):
        """Relevancia with no terms should still work (all get 0.0)."""
        result = ordenar_licitacoes(sample_licitacoes, "relevancia", None)
        # All have 0.0 relevance, order is stable sort based on input
        assert len(result) == 3

    def test_relevancia_with_empty_terms(self, sample_licitacoes):
        """Relevancia with empty terms list should still work."""
        result = ordenar_licitacoes(sample_licitacoes, "relevancia", [])
        assert len(result) == 3


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_workflow(self):
        """Test complete workflow: parse dates, parse values, sort."""
        licitacoes = [
            {
                "objetoCompra": "Aquisição de uniformes escolares",
                "dataPublicacao": "2026-01-15T10:00:00Z",
                "valorTotalEstimado": "1.500.000,00",
                "dataAberturaProposta": "2026-02-01",
                "nomeOrgao": "Escola Municipal ABC",
            },
            {
                "objetoCompra": "Jalecos para hospital",
                "dataPublicacao": "2026-02-01T08:30:00Z",
                "valorTotalEstimado": "500.000,00",
                "dataAberturaProposta": "2026-02-15",
                "nomeOrgao": "Hospital Regional",
            },
        ]

        # Sort by relevance with school-related terms
        result = ordenar_licitacoes(licitacoes, "relevancia", ["uniforme", "escola"])
        assert result[0]["objetoCompra"] == "Aquisição de uniformes escolares"

        # Sort by value descending
        result = ordenar_licitacoes(licitacoes, "valor_desc")
        assert parse_valor(result[0]["valorTotalEstimado"]) == 1500000.0

        # Sort by date
        result = ordenar_licitacoes(licitacoes, "data_desc")
        assert "2026-02-01" in result[0]["dataPublicacao"]
