"""
Unit tests for filtrar_por_municipio() and municipio-related filtering.

Tests cover:
- Filtering by single IBGE code
- Filtering by multiple IBGE codes
- Empty/None returns all
- Alternative field names
- Edge cases (invalid codes, formatting)
"""

import pytest
from filter import filtrar_por_municipio
from schemas import BuscaRequest
from pydantic import ValidationError
from datetime import date, timedelta


def _recent_dates(days_back: int = 7) -> tuple[str, str]:
    """Return a valid recent date range for tests."""
    today = date.today()
    return (today - timedelta(days=days_back)).isoformat(), today.isoformat()


class TestSingleMunicipioFilter:
    """Tests for filtering by single IBGE code."""

    def test_single_municipio_sao_paulo(self):
        """Should filter by single IBGE code (São Paulo = 3550308)."""
        bids = [
            {"codigoMunicipioIbge": "3550308", "municipio": "São Paulo"},
            {"codigoMunicipioIbge": "3304557", "municipio": "Rio de Janeiro"},
            {"codigoMunicipioIbge": "3106200", "municipio": "Belo Horizonte"},
        ]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1
        assert result[0]["municipio"] == "São Paulo"

    def test_single_municipio_rio_de_janeiro(self):
        """Should filter by Rio de Janeiro IBGE code."""
        bids = [
            {"codigoMunicipioIbge": "3550308", "municipio": "São Paulo"},
            {"codigoMunicipioIbge": "3304557", "municipio": "Rio de Janeiro"},
        ]
        result = filtrar_por_municipio(bids, ["3304557"])
        assert len(result) == 1
        assert result[0]["municipio"] == "Rio de Janeiro"

    def test_single_municipio_no_matches(self):
        """Should return empty when no bids match."""
        bids = [
            {"codigoMunicipioIbge": "3550308", "municipio": "São Paulo"},
            {"codigoMunicipioIbge": "3304557", "municipio": "Rio de Janeiro"},
        ]
        result = filtrar_por_municipio(bids, ["1100205"])  # Porto Velho
        assert len(result) == 0


class TestMultipleMunicipiosFilter:
    """Tests for filtering by multiple IBGE codes."""

    def test_multiple_municipios(self):
        """Should filter by multiple IBGE codes."""
        bids = [
            {"codigoMunicipioIbge": "3550308", "municipio": "São Paulo"},
            {"codigoMunicipioIbge": "3304557", "municipio": "Rio de Janeiro"},
            {"codigoMunicipioIbge": "3106200", "municipio": "Belo Horizonte"},
            {"codigoMunicipioIbge": "4106902", "municipio": "Curitiba"},
        ]
        result = filtrar_por_municipio(bids, ["3550308", "3304557"])
        assert len(result) == 2
        municipios = [b["municipio"] for b in result]
        assert "São Paulo" in municipios
        assert "Rio de Janeiro" in municipios

    def test_multiple_municipios_capital_cities(self):
        """Should filter by multiple capital city IBGE codes."""
        bids = [
            {"codigoMunicipioIbge": "3550308", "municipio": "São Paulo"},
            {"codigoMunicipioIbge": "4106902", "municipio": "Curitiba"},
            {"codigoMunicipioIbge": "4314902", "municipio": "Porto Alegre"},
            {"codigoMunicipioIbge": "5300108", "municipio": "Brasília"},
        ]
        # SP, Curitiba, Porto Alegre
        result = filtrar_por_municipio(bids, ["3550308", "4106902", "4314902"])
        assert len(result) == 3

    def test_multiple_municipios_all_match(self):
        """Should return all bids when all codes match."""
        bids = [
            {"codigoMunicipioIbge": "3550308"},
            {"codigoMunicipioIbge": "3304557"},
        ]
        result = filtrar_por_municipio(bids, ["3550308", "3304557"])
        assert len(result) == 2


class TestEmptyMunicipioReturnsAll:
    """Tests for empty/None municipio returning all bids."""

    def test_municipio_none_returns_all(self):
        """None municipios should return all bids."""
        bids = [
            {"codigoMunicipioIbge": "3550308"},
            {"codigoMunicipioIbge": "3304557"},
            {"codigoMunicipioIbge": "3106200"},
        ]
        result = filtrar_por_municipio(bids, None)
        assert len(result) == 3

    def test_municipio_empty_list_returns_all(self):
        """Empty list should return all bids."""
        bids = [
            {"codigoMunicipioIbge": "3550308"},
            {"codigoMunicipioIbge": "3304557"},
        ]
        result = filtrar_por_municipio(bids, [])
        assert len(result) == 2


class TestMunicipioAlternativeFieldNames:
    """Tests for alternative field names."""

    def test_uses_codigoMunicipioIbge(self):
        """Should use codigoMunicipioIbge as primary field."""
        bids = [{"codigoMunicipioIbge": "3550308"}]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    def test_uses_municipioId_as_fallback(self):
        """Should use municipioId as fallback field."""
        bids = [{"municipioId": "3550308"}]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    def test_uses_codigoMunicipio_as_fallback(self):
        """Should use codigoMunicipio as fallback field."""
        bids = [{"codigoMunicipio": "3550308"}]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    def test_uses_ibge_as_fallback(self):
        """Should use ibge as fallback field."""
        bids = [{"ibge": "3550308"}]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1


class TestMunicipioCodeFormatting:
    """Tests for IBGE code formatting handling."""

    def test_ibge_code_as_integer(self):
        """Should handle IBGE code as integer."""
        bids = [{"codigoMunicipioIbge": 3550308}]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    def test_ibge_code_with_whitespace(self):
        """Should handle IBGE code with whitespace."""
        bids = [{"codigoMunicipioIbge": "  3550308  "}]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    def test_filter_with_integer_codes(self):
        """Should handle filter codes as integers."""
        bids = [{"codigoMunicipioIbge": "3550308"}]
        result = filtrar_por_municipio(bids, [3550308])  # Integer in filter
        assert len(result) == 1

    def test_filter_with_whitespace_codes(self):
        """Should handle filter codes with whitespace."""
        bids = [{"codigoMunicipioIbge": "3550308"}]
        result = filtrar_por_municipio(bids, ["  3550308  "])
        assert len(result) == 1


class TestMunicipioEdgeCases:
    """Edge case tests for municipio filtering."""

    def test_empty_list_returns_empty(self):
        """Empty bid list should return empty list."""
        result = filtrar_por_municipio([], ["3550308"])
        assert result == []

    def test_bid_with_no_municipio_field(self):
        """Bid with no municipio field should not match."""
        bids = [
            {"objeto": "Something without municipio"},
            {"codigoMunicipioIbge": "3550308"},
        ]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    def test_bid_with_empty_municipio_value(self):
        """Bid with empty codigoMunicipioIbge should not match."""
        bids = [
            {"codigoMunicipioIbge": ""},
            {"codigoMunicipioIbge": "3550308"},
        ]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    def test_bid_with_none_municipio_value(self):
        """Bid with None codigoMunicipioIbge should not match."""
        bids = [
            {"codigoMunicipioIbge": None},
            {"codigoMunicipioIbge": "3550308"},
        ]
        result = filtrar_por_municipio(bids, ["3550308"])
        assert len(result) == 1

    def test_partial_ibge_code_no_match(self):
        """Partial IBGE code should not match."""
        bids = [{"codigoMunicipioIbge": "3550308"}]
        result = filtrar_por_municipio(bids, ["355030"])  # Missing digit
        assert len(result) == 0

    def test_ibge_code_with_prefix_no_match(self):
        """IBGE code with prefix should not match."""
        bids = [{"codigoMunicipioIbge": "3550308"}]
        result = filtrar_por_municipio(bids, ["03550308"])  # Extra digit
        assert len(result) == 0


class TestMunicipioBrazilianCapitals:
    """Tests with real Brazilian capital city IBGE codes."""

    def test_filter_brazilian_capitals(self):
        """Should correctly filter by Brazilian capital city codes."""
        # Real IBGE codes for Brazilian capitals
        bids = [
            {"codigoMunicipioIbge": "3550308", "municipio": "São Paulo"},
            {"codigoMunicipioIbge": "3304557", "municipio": "Rio de Janeiro"},
            {"codigoMunicipioIbge": "5300108", "municipio": "Brasília"},
            {"codigoMunicipioIbge": "2927408", "municipio": "Salvador"},
            {"codigoMunicipioIbge": "2304400", "municipio": "Fortaleza"},
            {"codigoMunicipioIbge": "3106200", "municipio": "Belo Horizonte"},
            {"codigoMunicipioIbge": "1302603", "municipio": "Manaus"},
            {"codigoMunicipioIbge": "4106902", "municipio": "Curitiba"},
            {"codigoMunicipioIbge": "2611606", "municipio": "Recife"},
            {"codigoMunicipioIbge": "4314902", "municipio": "Porto Alegre"},
        ]

        # Filter for São Paulo, Rio, and Brasília
        result = filtrar_por_municipio(bids, ["3550308", "3304557", "5300108"])
        assert len(result) == 3

        municipios = [b["municipio"] for b in result]
        assert "São Paulo" in municipios
        assert "Rio de Janeiro" in municipios
        assert "Brasília" in municipios


class TestMunicipioSchemaValidation:
    """Tests for municipio validation in BuscaRequest schema."""

    def test_valid_municipio_codes_accepted(self):
        """Valid IBGE codes should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            municipios=["3550308", "3509502"],  # São Paulo, Campinas
        )
        assert "3550308" in request.municipios
        assert "3509502" in request.municipios

    def test_municipios_none_accepted(self):
        """None municipios should be accepted (means all)."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            municipios=None,
        )
        assert request.municipios is None

    def test_municipios_empty_list_accepted(self):
        """Empty municipios list should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            municipios=[],
        )
        assert request.municipios == []

    def test_single_municipio_code_accepted(self):
        """Single IBGE code should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            municipios=["3550308"],
        )
        assert len(request.municipios) == 1

    def test_multiple_municipio_codes_accepted(self):
        """Multiple IBGE codes should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP", "RJ"],
            data_inicial=d_ini,
            data_final=d_fin,
            municipios=["3550308", "3304557", "3106200"],
        )
        assert len(request.municipios) == 3

