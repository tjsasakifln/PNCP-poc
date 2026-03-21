"""Tests for filter_utils.py — value parsing and sector config lookup utilities.

Wave 0 Safety Net: Covers parse_valor, get_valor_from_lic, get_setor_config.
"""

import pytest
from unittest.mock import patch, MagicMock

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filter_utils import parse_valor, get_valor_from_lic, get_setor_config


# ──────────────────────────────────────────────────────────────────────
# parse_valor
# ──────────────────────────────────────────────────────────────────────

class TestParseValor:
    """Tests for parse_valor — Brazilian currency string parsing."""

    @pytest.mark.timeout(30)
    def test_none_returns_zero(self):
        assert parse_valor(None) == 0.0

    @pytest.mark.timeout(30)
    def test_int_value(self):
        assert parse_valor(100000) == 100000.0

    @pytest.mark.timeout(30)
    def test_float_value(self):
        assert parse_valor(150000.50) == 150000.50

    @pytest.mark.timeout(30)
    def test_zero_int(self):
        assert parse_valor(0) == 0.0

    @pytest.mark.timeout(30)
    def test_zero_float(self):
        assert parse_valor(0.0) == 0.0

    @pytest.mark.timeout(30)
    def test_brazilian_format_string(self):
        """Brazilian format: dots for thousands, comma for decimals."""
        # "1.000.000,50" -> remove dots -> "1000000,50" -> comma->dot -> "1000000.50"
        assert parse_valor("1.000.000,50") == 1000000.5

    @pytest.mark.timeout(30)
    def test_simple_string_number(self):
        assert parse_valor("50000") == 50000.0

    @pytest.mark.timeout(30)
    def test_unparseable_string(self):
        assert parse_valor("abc") == 0.0

    @pytest.mark.timeout(30)
    def test_empty_string(self):
        assert parse_valor("") == 0.0

    @pytest.mark.timeout(30)
    def test_unsupported_type(self):
        assert parse_valor([1, 2, 3]) == 0.0

    @pytest.mark.timeout(30)
    def test_negative_value(self):
        assert parse_valor(-500.0) == -500.0


# ──────────────────────────────────────────────────────────────────────
# get_valor_from_lic
# ──────────────────────────────────────────────────────────────────────

class TestGetValorFromLic:
    """Tests for get_valor_from_lic — extract value from bid dict."""

    @pytest.mark.timeout(30)
    def test_valorTotalEstimado(self):
        lic = {"valorTotalEstimado": 250000.0}
        assert get_valor_from_lic(lic) == 250000.0

    @pytest.mark.timeout(30)
    def test_valorEstimado_fallback(self):
        lic = {"valorEstimado": 100000}
        assert get_valor_from_lic(lic) == 100000.0

    @pytest.mark.timeout(30)
    def test_no_value_returns_zero(self):
        lic = {"objetoCompra": "Test bid"}
        assert get_valor_from_lic(lic) == 0.0

    @pytest.mark.timeout(30)
    def test_empty_dict(self):
        assert get_valor_from_lic({}) == 0.0

    @pytest.mark.timeout(30)
    def test_string_value(self):
        lic = {"valorTotalEstimado": "500000"}
        assert get_valor_from_lic(lic) == 500000.0


# ──────────────────────────────────────────────────────────────────────
# get_setor_config
# ──────────────────────────────────────────────────────────────────────

class TestGetSetorConfig:
    """Tests for get_setor_config — sector config lookup."""

    @pytest.mark.timeout(30)
    @patch("sectors.get_sector")
    def test_valid_sector(self, mock_get_sector):
        mock_config = MagicMock()
        mock_config.name = "Vestuario"
        mock_get_sector.return_value = mock_config
        result = get_setor_config("vestuario")
        assert result is not None
        assert result.name == "Vestuario"

    @pytest.mark.timeout(30)
    @patch("sectors.get_sector", side_effect=KeyError("not found"))
    def test_unknown_sector_returns_none(self, mock_get_sector):
        result = get_setor_config("nonexistent")
        assert result is None

    @pytest.mark.timeout(30)
    @patch("sectors.get_sector", side_effect=Exception("db error"))
    def test_exception_returns_none(self, mock_get_sector):
        result = get_setor_config("broken")
        assert result is None
