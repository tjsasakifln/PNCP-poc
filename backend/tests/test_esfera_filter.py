"""
Unit tests for filtrar_por_esfera() and esfera-related filtering.

Tests cover:
- Filtering by single esfera (F, E, M)
- Filtering by multiple esferas
- Empty/None returns all
- Fallback detection by orgao name
- Alternative field names
- Edge cases
"""

import pytest
from filter import filtrar_por_esfera
from schemas import EsferaGovernamental, BuscaRequest
from pydantic import ValidationError
from datetime import date, timedelta


def _recent_dates(days_back: int = 7) -> tuple[str, str]:
    """Return a valid recent date range for tests."""
    today = date.today()
    return (today - timedelta(days=days_back)).isoformat(), today.isoformat()


class TestEsferaEnumDefinition:
    """Tests for EsferaGovernamental enum definition."""

    def test_all_esfera_values_exist(self):
        """All expected esfera values should be defined."""
        assert EsferaGovernamental.FEDERAL.value == "F"
        assert EsferaGovernamental.ESTADUAL.value == "E"
        assert EsferaGovernamental.MUNICIPAL.value == "M"

    def test_esfera_enum_count(self):
        """Should have exactly 3 esfera options."""
        assert len(EsferaGovernamental) == 3

    def test_esfera_from_string(self):
        """Should create enum from string value."""
        esfera = EsferaGovernamental("F")
        assert esfera == EsferaGovernamental.FEDERAL


class TestSingleEsferaFilter:
    """Tests for filtering by single esfera."""

    def test_single_esfera_federal(self):
        """Should filter by Federal (F)."""
        bids = [
            {"esferaId": "F", "orgao": "Ministério da Saúde"},
            {"esferaId": "E", "orgao": "Secretaria Estadual"},
            {"esferaId": "M", "orgao": "Prefeitura de São Paulo"},
        ]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 1
        assert result[0]["esferaId"] == "F"

    def test_single_esfera_estadual(self):
        """Should filter by Estadual (E)."""
        bids = [
            {"esferaId": "F", "orgao": "Ministério"},
            {"esferaId": "E", "orgao": "Estado de SP"},
            {"esferaId": "M", "orgao": "Prefeitura"},
        ]
        result = filtrar_por_esfera(bids, ["E"])
        assert len(result) == 1
        assert result[0]["esferaId"] == "E"

    def test_single_esfera_municipal(self):
        """Should filter by Municipal (M)."""
        bids = [
            {"esferaId": "F", "orgao": "Ministério"},
            {"esferaId": "E", "orgao": "Estado"},
            {"esferaId": "M", "orgao": "Prefeitura de Campinas"},
        ]
        result = filtrar_por_esfera(bids, ["M"])
        assert len(result) == 1
        assert result[0]["esferaId"] == "M"

    def test_single_esfera_no_matches(self):
        """Should return empty when no bids match."""
        bids = [
            {"esferaId": "M", "orgao": "Prefeitura"},
            {"esferaId": "M", "orgao": "Câmara Municipal"},
        ]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 0


class TestMultipleEsferasFilter:
    """Tests for filtering by multiple esferas."""

    def test_multiple_esferas_federal_estadual(self):
        """Should filter by multiple esferas (F and E)."""
        bids = [
            {"esferaId": "F", "orgao": "Ministério"},
            {"esferaId": "E", "orgao": "Secretaria Estadual"},
            {"esferaId": "M", "orgao": "Prefeitura"},
        ]
        result = filtrar_por_esfera(bids, ["F", "E"])
        assert len(result) == 2
        assert all(b["esferaId"] in ["F", "E"] for b in result)

    def test_multiple_esferas_all_three(self):
        """Should return all when filtering by all esferas."""
        bids = [
            {"esferaId": "F"},
            {"esferaId": "E"},
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, ["F", "E", "M"])
        assert len(result) == 3

    def test_multiple_esferas_estadual_municipal(self):
        """Should filter by E and M."""
        bids = [
            {"esferaId": "F", "orgao": "Ministério"},
            {"esferaId": "E", "orgao": "Estado"},
            {"esferaId": "M", "orgao": "Prefeitura"},
        ]
        result = filtrar_por_esfera(bids, ["E", "M"])
        assert len(result) == 2


class TestEmptyEsferaReturnsAll:
    """Tests for empty/None esfera returning all bids."""

    def test_esfera_none_returns_all(self):
        """None esferas should return all bids."""
        bids = [
            {"esferaId": "F"},
            {"esferaId": "E"},
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, None)
        assert len(result) == 3

    def test_esfera_empty_list_returns_all(self):
        """Empty list should return all bids."""
        bids = [
            {"esferaId": "F"},
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, [])
        assert len(result) == 2


class TestEsferaFallbackByOrgaoName:
    """Tests for fallback detection by orgao name when esferaId is missing."""

    def test_fallback_federal_ministerio(self):
        """Should detect Federal by 'Ministério' in orgao name."""
        bids = [
            {"nomeOrgao": "Ministério da Educação"},
        ]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 1

    def test_fallback_federal_universidade(self):
        """Should detect Federal by 'Universidade Federal' in orgao name."""
        bids = [
            {"nomeOrgao": "Universidade Federal do Rio de Janeiro"},
        ]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 1

    def test_fallback_estadual_secretaria_estado(self):
        """Should detect Estadual by 'Secretaria de Estado' in orgao name."""
        bids = [
            {"nomeOrgao": "Secretaria de Estado da Saúde"},
        ]
        result = filtrar_por_esfera(bids, ["E"])
        assert len(result) == 1

    def test_fallback_estadual_policia_militar(self):
        """Should detect Estadual by 'Polícia Militar' in orgao name."""
        bids = [
            {"nomeOrgao": "Polícia Militar do Estado de SP"},
        ]
        result = filtrar_por_esfera(bids, ["E"])
        assert len(result) == 1

    def test_fallback_municipal_prefeitura(self):
        """Should detect Municipal by 'Prefeitura' in orgao name."""
        bids = [
            {"nomeOrgao": "Prefeitura Municipal de Campinas"},
        ]
        result = filtrar_por_esfera(bids, ["M"])
        assert len(result) == 1

    def test_fallback_municipal_camara(self):
        """Should detect Municipal by 'Câmara Municipal' in orgao name."""
        bids = [
            {"nomeOrgao": "Câmara Municipal de São Paulo"},
        ]
        result = filtrar_por_esfera(bids, ["M"])
        assert len(result) == 1

    def test_fallback_not_detected_unknown_orgao(self):
        """Unknown orgao should not match any esfera filter."""
        bids = [
            {"nomeOrgao": "Organização Desconhecida"},
        ]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 0


class TestEsferaAlternativeFieldNames:
    """Tests for alternative field names."""

    def test_uses_esferaId_field(self):
        """Should use esferaId as primary field."""
        bids = [{"esferaId": "F"}]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 1

    def test_uses_esfera_as_fallback(self):
        """Should use esfera as fallback field."""
        bids = [{"esfera": "E"}]
        result = filtrar_por_esfera(bids, ["E"])
        assert len(result) == 1

    def test_uses_tipoEsfera_as_fallback(self):
        """Should use tipoEsfera as fallback field."""
        bids = [{"tipoEsfera": "M"}]
        result = filtrar_por_esfera(bids, ["M"])
        assert len(result) == 1


class TestEsferaCaseInsensitivity:
    """Tests for case insensitivity in esfera filtering."""

    def test_esfera_lowercase_input(self):
        """Should handle lowercase esfera filter."""
        bids = [
            {"esferaId": "F"},
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, ["f"])
        assert len(result) == 1
        assert result[0]["esferaId"] == "F"

    def test_esfera_mixed_case_input(self):
        """Should handle mixed case esfera filter."""
        bids = [
            {"esferaId": "E"},
        ]
        result = filtrar_por_esfera(bids, ["e"])
        assert len(result) == 1


class TestEsferaEdgeCases:
    """Edge case tests for esfera filtering."""

    def test_empty_list_returns_empty(self):
        """Empty bid list should return empty list."""
        result = filtrar_por_esfera([], ["F", "E", "M"])
        assert result == []

    def test_bid_with_no_esfera_field(self):
        """Bid with no esfera field should not match direct filter."""
        bids = [
            {"objeto": "Something without esfera"},
        ]
        # Without esferaId and without fallback keywords, should not match
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 0

    def test_bid_with_empty_esfera_value(self):
        """Bid with empty esferaId should rely on fallback."""
        bids = [
            {"esferaId": "", "nomeOrgao": "Ministério da Saúde"},
        ]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 1

    def test_bid_with_none_esfera_value(self):
        """Bid with None esferaId should rely on fallback."""
        bids = [
            {"esferaId": None, "nomeOrgao": "Prefeitura de Campinas"},
        ]
        result = filtrar_por_esfera(bids, ["M"])
        assert len(result) == 1


class TestEsferaSchemaValidation:
    """Tests for esfera validation in BuscaRequest schema."""

    def test_valid_esfera_codes_accepted(self):
        """Valid esfera codes (F, E, M) should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            esferas=["F", "E"],
        )
        assert "F" in request.esferas
        assert "E" in request.esferas

    def test_all_esfera_codes_accepted(self):
        """All 3 esfera codes should be accepted together."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            esferas=["F", "E", "M"],
        )
        assert len(request.esferas) == 3

    def test_esferas_none_accepted(self):
        """None esferas should be accepted (means all)."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            esferas=None,
        )
        assert request.esferas is None

    def test_esferas_empty_list_accepted(self):
        """Empty esferas list should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            esferas=[],
        )
        assert request.esferas == []

    def test_invalid_esfera_code_rejected(self):
        """Invalid esfera code should be rejected in schema."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError):
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                esferas=["X"],  # Invalid
            )

