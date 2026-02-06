"""
Unit tests for filtrar_por_valor() and valor-related filtering.

Tests cover:
- Value range filtering with min and max
- No minimum limit (valor_min=None)
- No maximum limit (valor_max=None)
- Both limits as None (returns all)
- String values in Brazilian format
- Alternative field names
- Edge cases
"""

import pytest
from filter import filtrar_por_valor
from schemas import BuscaRequest
from pydantic import ValidationError
from datetime import date, timedelta


def _recent_dates(days_back: int = 7) -> tuple[str, str]:
    """Return a valid recent date range for tests."""
    today = date.today()
    return (today - timedelta(days=days_back)).isoformat(), today.isoformat()


class TestValorRangeFiltering:
    """Tests for filtering by value range."""

    def test_valor_within_range(self):
        """Should return bids within the specified range."""
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 100000},
            {"valorTotalEstimado": 200000},
            {"valorTotalEstimado": 500000},
        ]
        result = filtrar_por_valor(bids, valor_min=80000, valor_max=300000)
        assert len(result) == 2
        assert result[0]["valorTotalEstimado"] == 100000
        assert result[1]["valorTotalEstimado"] == 200000

    def test_valor_at_exact_boundaries(self):
        """Should include bids at exact boundary values."""
        bids = [
            {"valorTotalEstimado": 100000},
            {"valorTotalEstimado": 200000},
            {"valorTotalEstimado": 300000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=300000)
        assert len(result) == 3

    def test_valor_range_excludes_outside(self):
        """Should exclude bids outside the range."""
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 150000},
            {"valorTotalEstimado": 500000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=200000)
        assert len(result) == 1
        assert result[0]["valorTotalEstimado"] == 150000

    def test_valor_range_no_matches(self):
        """Should return empty when no bids in range."""
        bids = [
            {"valorTotalEstimado": 10000},
            {"valorTotalEstimado": 50000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=200000)
        assert len(result) == 0


class TestValorNoMinimumLimit:
    """Tests for filtering without minimum limit."""

    def test_valor_no_min_filters_by_max(self):
        """Should filter only by max when min is None."""
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 150000},
            {"valorTotalEstimado": 300000},
        ]
        result = filtrar_por_valor(bids, valor_min=None, valor_max=200000)
        assert len(result) == 2
        assert all(b["valorTotalEstimado"] <= 200000 for b in result)

    def test_valor_no_min_includes_zero(self):
        """Should include zero value bids when no min."""
        bids = [
            {"valorTotalEstimado": 0},
            {"valorTotalEstimado": 100000},
        ]
        result = filtrar_por_valor(bids, valor_min=None, valor_max=150000)
        assert len(result) == 2

    def test_valor_no_min_includes_small_values(self):
        """Should include very small values when no min."""
        bids = [
            {"valorTotalEstimado": 1},
            {"valorTotalEstimado": 100},
            {"valorTotalEstimado": 1000000},
        ]
        result = filtrar_por_valor(bids, valor_min=None, valor_max=50000)
        assert len(result) == 2


class TestValorNoMaximumLimit:
    """Tests for filtering without maximum limit."""

    def test_valor_no_max_filters_by_min(self):
        """Should filter only by min when max is None."""
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 150000},
            {"valorTotalEstimado": 1000000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=None)
        assert len(result) == 2
        assert all(b["valorTotalEstimado"] >= 100000 for b in result)

    def test_valor_no_max_includes_large_values(self):
        """Should include very large values when no max."""
        bids = [
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 1000000000},  # 1 billion
        ]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=None)
        assert len(result) == 1
        assert result[0]["valorTotalEstimado"] == 1000000000


class TestValorBothLimitsNone:
    """Tests for filtering with both limits as None."""

    def test_valor_both_none_returns_all(self):
        """Should return all bids when both min and max are None."""
        bids = [
            {"valorTotalEstimado": 0},
            {"valorTotalEstimado": 50000},
            {"valorTotalEstimado": 1000000},
        ]
        result = filtrar_por_valor(bids, valor_min=None, valor_max=None)
        assert len(result) == 3
        assert result == bids

    def test_valor_defaults_return_all(self):
        """Default parameters should return all bids."""
        bids = [
            {"valorTotalEstimado": 100000},
            {"valorTotalEstimado": 200000},
        ]
        result = filtrar_por_valor(bids)
        assert len(result) == 2


class TestValorBrazilianStringFormat:
    """Tests for handling Brazilian number format strings."""

    def test_valor_brazilian_format_with_dots_and_comma(self):
        """Should parse '1.234.567,89' format."""
        bids = [
            {"valorTotalEstimado": "150.000,00"},
            {"valorTotalEstimado": "1.000.000,00"},
        ]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=500000)
        assert len(result) == 1

    def test_valor_brazilian_format_decimal_only(self):
        """Should parse '150000,50' format."""
        bids = [
            {"valorTotalEstimado": "150000,50"},
        ]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=200000)
        assert len(result) == 1

    def test_valor_mixed_formats(self):
        """Should handle mix of numeric and string values."""
        bids = [
            {"valorTotalEstimado": 150000.0},
            {"valorTotalEstimado": "200.000,00"},
            {"valorTotalEstimado": 50000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=250000)
        assert len(result) == 2

    def test_valor_invalid_string_treated_as_zero(self):
        """Invalid string values should be treated as 0."""
        bids = [
            {"valorTotalEstimado": "invalid"},
            {"valorTotalEstimado": 150000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000)
        assert len(result) == 1
        assert result[0]["valorTotalEstimado"] == 150000


class TestValorAlternativeFieldNames:
    """Tests for alternative field names."""

    def test_uses_valorTotalEstimado(self):
        """Should use valorTotalEstimado as primary field."""
        bids = [{"valorTotalEstimado": 150000}]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=200000)
        assert len(result) == 1

    def test_uses_valorEstimado_as_fallback(self):
        """Should use valorEstimado as fallback."""
        bids = [{"valorEstimado": 150000}]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=200000)
        assert len(result) == 1

    def test_uses_valor_as_fallback(self):
        """Should use valor as fallback."""
        bids = [{"valor": 150000}]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=200000)
        assert len(result) == 1

    def test_priority_valorTotalEstimado_over_others(self):
        """valorTotalEstimado should take priority over other fields."""
        bids = [{
            "valorTotalEstimado": 150000,
            "valorEstimado": 50000,
            "valor": 25000,
        }]
        result = filtrar_por_valor(bids, valor_min=100000, valor_max=200000)
        assert len(result) == 1


class TestValorEdgeCases:
    """Edge case tests for valor filtering."""

    def test_empty_list_returns_empty(self):
        """Empty bid list should return empty list."""
        result = filtrar_por_valor([], valor_min=100000, valor_max=200000)
        assert result == []

    def test_valor_none_in_bid(self):
        """Bid with None valor should be treated as 0."""
        bids = [
            {"valorTotalEstimado": None},
            {"valorTotalEstimado": 150000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000)
        assert len(result) == 1
        assert result[0]["valorTotalEstimado"] == 150000

    def test_valor_missing_field(self):
        """Bid with no valor field should be treated as 0."""
        bids = [
            {"objeto": "Something without value"},
            {"valorTotalEstimado": 150000},
        ]
        result = filtrar_por_valor(bids, valor_min=100000)
        assert len(result) == 1

    def test_valor_integer_conversion(self):
        """Should handle integer values."""
        bids = [{"valorTotalEstimado": 150000}]
        result = filtrar_por_valor(bids, valor_min=100000.0, valor_max=200000.0)
        assert len(result) == 1

    def test_valor_negative_values(self):
        """Should handle negative values (edge case)."""
        bids = [
            {"valorTotalEstimado": -1000},
            {"valorTotalEstimado": 50000},
        ]
        result = filtrar_por_valor(bids, valor_min=0)
        assert len(result) == 1
        assert result[0]["valorTotalEstimado"] == 50000

    def test_valor_very_large_numbers(self):
        """Should handle very large numbers."""
        bids = [
            {"valorTotalEstimado": 10_000_000_000},  # 10 billion
        ]
        result = filtrar_por_valor(bids, valor_min=1_000_000_000)
        assert len(result) == 1

    def test_valor_float_precision(self):
        """Should handle float precision correctly."""
        bids = [
            {"valorTotalEstimado": 150000.99},
        ]
        result = filtrar_por_valor(bids, valor_min=150000.99, valor_max=150001)
        assert len(result) == 1


class TestValorSchemaValidation:
    """Tests for valor validation in BuscaRequest schema."""

    def test_valor_range_accepted(self):
        """Valid valor range should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            valor_minimo=50000,
            valor_maximo=500000,
        )
        assert request.valor_minimo == 50000
        assert request.valor_maximo == 500000

    def test_valor_minimo_only_accepted(self):
        """valor_minimo alone should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            valor_minimo=100000,
            valor_maximo=None,
        )
        assert request.valor_minimo == 100000
        assert request.valor_maximo is None

    def test_valor_maximo_only_accepted(self):
        """valor_maximo alone should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            valor_minimo=None,
            valor_maximo=500000,
        )
        assert request.valor_minimo is None
        assert request.valor_maximo == 500000

    def test_valor_both_none_accepted(self):
        """Both None should be accepted (no valor filter)."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
        )
        assert request.valor_minimo is None
        assert request.valor_maximo is None

    def test_valor_minimo_greater_than_maximo_may_raise(self):
        """valor_minimo > valor_maximo behavior depends on schema validation."""
        d_ini, d_fin = _recent_dates(7)
        # This test documents expected behavior - adjust if schema validates this
        try:
            request = BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                valor_minimo=500000,
                valor_maximo=100000,
            )
            # If no validation error, filter will return empty (valid behavior)
            assert request.valor_minimo > request.valor_maximo
        except ValidationError:
            # Schema validates min <= max
            pass

