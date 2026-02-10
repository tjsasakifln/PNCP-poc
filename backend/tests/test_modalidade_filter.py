"""
Unit tests for filtrar_por_modalidade() and modalidade-related filtering.

Tests cover:
- Filtering by single modalidade
- Filtering by multiple modalidades
- Empty list returns all
- Invalid/inexistent modalidade handling
- Alternative field names
- Lei 14.133/2021 compliance (valid codes: 1,2,3,6,7,9,10,11)
"""

import pytest
from filter import filtrar_por_modalidade
from schemas import ModalidadeContratacao, BuscaRequest
from pydantic import ValidationError
from datetime import date, timedelta


def _recent_dates(days_back: int = 7) -> tuple[str, str]:
    """Return a valid recent date range for tests."""
    today = date.today()
    return (today - timedelta(days=days_back)).isoformat(), today.isoformat()


class TestModalidadeEnumDefinition:
    """Tests for ModalidadeContratacao enum definition (Lei 14.133/2021)."""

    def test_all_lei_14133_modalidade_codes_exist(self):
        """All 8 Lei 14.133/2021 modalidade codes should be defined."""
        assert ModalidadeContratacao.PREGAO_ELETRONICO == 1
        assert ModalidadeContratacao.PREGAO_PRESENCIAL == 2
        assert ModalidadeContratacao.CONCORRENCIA == 3
        assert ModalidadeContratacao.DISPENSA == 6
        assert ModalidadeContratacao.INEXIGIBILIDADE == 7
        assert ModalidadeContratacao.LEILAO == 9
        assert ModalidadeContratacao.DIALOGO_COMPETITIVO == 10
        assert ModalidadeContratacao.CONCURSO == 11

    def test_deprecated_codes_removed(self):
        """Codes 4 (TOMADA_PRECOS) and 5 (CONVITE) should NOT exist."""
        with pytest.raises(AttributeError):
            _ = ModalidadeContratacao.TOMADA_PRECOS
        with pytest.raises(AttributeError):
            _ = ModalidadeContratacao.CONVITE
        # Also verify CREDENCIAMENTO (8) is removed
        with pytest.raises(AttributeError):
            _ = ModalidadeContratacao.CREDENCIAMENTO

    def test_modalidade_enum_count(self):
        """Should have exactly 8 Lei 14.133/2021 modalidade options."""
        assert len(ModalidadeContratacao) == 8

    def test_modalidade_codes_match_lei_14133(self):
        """Modalidade codes should be 1,2,3,6,7,9,10,11 only."""
        codes = sorted([m.value for m in ModalidadeContratacao])
        assert codes == [1, 2, 3, 6, 7, 9, 10, 11]


class TestSingleModalidadeFilter:
    """Tests for filtering by single modalidade."""

    def test_single_modalidade_pregao_eletronico(self):
        """Should filter by Pregao Eletronico (code 1)."""
        bids = [
            {"modalidadeId": 1, "objeto": "Pregao Eletronico"},
            {"modalidadeId": 2, "objeto": "Pregao Presencial"},
            {"modalidadeId": 6, "objeto": "Dispensa"},
        ]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1
        assert result[0]["modalidadeId"] == 1

    def test_single_modalidade_dispensa(self):
        """Should filter by Dispensa (code 6)."""
        bids = [
            {"modalidadeId": 1, "objeto": "Pregao"},
            {"modalidadeId": 6, "objeto": "Dispensa"},
        ]
        result = filtrar_por_modalidade(bids, [6])
        assert len(result) == 1
        assert result[0]["modalidadeId"] == 6

    def test_single_modalidade_concurso(self):
        """Should filter by Concurso (code 11) - NEW in Lei 14.133/2021."""
        bids = [
            {"modalidadeId": 1, "objeto": "Pregao"},
            {"modalidadeId": 11, "objeto": "Concurso"},
        ]
        result = filtrar_por_modalidade(bids, [11])
        assert len(result) == 1
        assert result[0]["modalidadeId"] == 11

    def test_single_modalidade_no_matches(self):
        """Should return empty when no bids match."""
        bids = [
            {"modalidadeId": 1, "objeto": "Pregao"},
            {"modalidadeId": 6, "objeto": "Dispensa"},
        ]
        result = filtrar_por_modalidade(bids, [3])  # Concorrencia
        assert len(result) == 0


class TestMultipleModalidadesFilter:
    """Tests for filtering by multiple modalidades."""

    def test_multiple_modalidades_pregoes_and_dispensa(self):
        """Should filter by multiple modalidades."""
        bids = [
            {"modalidadeId": 1, "objeto": "Pregao Eletronico"},
            {"modalidadeId": 2, "objeto": "Pregao Presencial"},
            {"modalidadeId": 6, "objeto": "Dispensa"},
            {"modalidadeId": 3, "objeto": "Concorrencia"},
        ]
        result = filtrar_por_modalidade(bids, [1, 2, 6])
        assert len(result) == 3
        assert all(b["modalidadeId"] in [1, 2, 6] for b in result)

    def test_all_lei_14133_modalidades_filter(self):
        """Should return all when filtering by all Lei 14.133/2021 codes."""
        bids = [
            {"modalidadeId": 1, "objeto": "Modalidade 1"},
            {"modalidadeId": 2, "objeto": "Modalidade 2"},
            {"modalidadeId": 3, "objeto": "Modalidade 3"},
            {"modalidadeId": 6, "objeto": "Modalidade 6"},
            {"modalidadeId": 7, "objeto": "Modalidade 7"},
            {"modalidadeId": 9, "objeto": "Modalidade 9"},
            {"modalidadeId": 10, "objeto": "Modalidade 10"},
            {"modalidadeId": 11, "objeto": "Modalidade 11"},
        ]
        result = filtrar_por_modalidade(bids, [1, 2, 3, 6, 7, 9, 10, 11])
        assert len(result) == 8


class TestEmptyListReturnsAll:
    """Tests for empty/None list returning all bids."""

    def test_modalidade_none_returns_all(self):
        """None modalidades should return all bids."""
        bids = [
            {"modalidadeId": 1},
            {"modalidadeId": 6},
        ]
        result = filtrar_por_modalidade(bids, None)
        assert len(result) == 2

    def test_modalidade_empty_list_returns_all(self):
        """Empty list should return all bids."""
        bids = [
            {"modalidadeId": 1},
            {"modalidadeId": 6},
        ]
        result = filtrar_por_modalidade(bids, [])
        assert len(result) == 2


class TestDeprecatedModalidadeCodesRejection:
    """Tests for rejecting deprecated Lei 8.666/93 modalidade codes."""

    def test_deprecated_code_4_rejected_in_schema(self):
        """Modalidade code 4 (Tomada de Preços) should be rejected in schema."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                modalidades=[4],
            )
        error_msg = str(exc_info.value).lower()
        assert "inválidos" in error_msg or "invalid" in error_msg
        assert "4" in str(exc_info.value)

    def test_deprecated_code_5_rejected_in_schema(self):
        """Modalidade code 5 (Convite) should be rejected in schema."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                modalidades=[5],
            )
        error_msg = str(exc_info.value).lower()
        assert "inválidos" in error_msg or "invalid" in error_msg
        assert "5" in str(exc_info.value)

    def test_deprecated_code_8_rejected_in_schema(self):
        """Modalidade code 8 (Credenciamento) should be rejected in schema."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                modalidades=[8],
            )
        error_msg = str(exc_info.value).lower()
        assert "inválidos" in error_msg or "invalid" in error_msg
        assert "8" in str(exc_info.value)

    def test_mixed_valid_and_deprecated_codes_rejected(self):
        """Mix of valid and deprecated codes should be rejected."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                modalidades=[1, 4, 6],  # 4 is deprecated
            )
        assert "4" in str(exc_info.value)


class TestInexistentModalidadeHandling:
    """Tests for handling inexistent/invalid modalidade codes."""

    def test_inexistent_modalidade_code_99(self):
        """Filtering by non-existent code 99 should return empty."""
        bids = [
            {"modalidadeId": 1},
            {"modalidadeId": 6},
        ]
        result = filtrar_por_modalidade(bids, [99])
        assert len(result) == 0

    def test_invalid_modalidade_code_zero_in_schema(self):
        """Modalidade code 0 should be rejected in schema."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                modalidades=[0, 1],
            )
        assert "0" in str(exc_info.value)

    def test_invalid_modalidade_code_twelve_in_schema(self):
        """Modalidade code 12 should be rejected in schema."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                modalidades=[12],
            )
        assert "12" in str(exc_info.value)

    def test_invalid_modalidade_negative_in_schema(self):
        """Negative modalidade code should be rejected in schema."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError):
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                modalidades=[-1],
            )


class TestAlternativeModalidadeFields:
    """Tests for alternative field names."""

    def test_uses_modalidadeId_field(self):
        """Should use modalidadeId as primary field."""
        bids = [{"modalidadeId": 1}]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1

    def test_uses_codigoModalidadeContratacao_as_fallback(self):
        """Should check codigoModalidadeContratacao as fallback."""
        bids = [{"codigoModalidadeContratacao": 1}]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1

    def test_uses_modalidade_id_as_fallback(self):
        """Should check modalidade_id as fallback."""
        bids = [{"modalidade_id": 6}]
        result = filtrar_por_modalidade(bids, [6])
        assert len(result) == 1


class TestModalidadeFilterEdgeCases:
    """Edge case tests for modalidade filtering."""

    def test_handles_string_modalidade_id(self):
        """Should handle modalidadeId as string."""
        bids = [
            {"modalidadeId": "1"},
            {"modalidadeId": "6"},
        ]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1

    def test_modalidade_none_value_in_bid(self):
        """Bid with None modalidadeId should be filtered out."""
        bids = [
            {"modalidadeId": None},
            {"modalidadeId": 1},
        ]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1
        assert result[0]["modalidadeId"] == 1

    def test_modalidade_invalid_string_value(self):
        """Bid with non-numeric string modalidadeId should be filtered out."""
        bids = [
            {"modalidadeId": "invalid"},
            {"modalidadeId": "1"},
        ]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1

    def test_modalidade_float_conversion(self):
        """Bid with float modalidadeId should be handled."""
        bids = [
            {"modalidadeId": 1.0},
            {"modalidadeId": 2.5},  # Should convert to 2
        ]
        result = filtrar_por_modalidade(bids, [1, 2])
        assert len(result) == 2

    def test_modalidade_empty_bid(self):
        """Bid with no modalidade fields should be filtered out."""
        bids = [
            {},
            {"modalidadeId": 1},
        ]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1

    def test_empty_list_input(self):
        """Empty bid list should return empty."""
        result = filtrar_por_modalidade([], [1, 2])
        assert result == []


class TestModalidadeSchemaValidation:
    """Tests for modalidade validation in BuscaRequest schema."""

    def test_valid_modalidade_codes_accepted(self):
        """Valid modalidade codes (1,2,3,6,7,9,10,11) should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            modalidades=[1, 2, 6],
        )
        assert request.modalidades == [1, 2, 6]

    def test_all_lei_14133_codes_accepted(self):
        """All 8 Lei 14.133/2021 modalidade codes should be accepted together."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            modalidades=[1, 2, 3, 6, 7, 9, 10, 11],
        )
        assert len(request.modalidades) == 8
        assert set(request.modalidades) == {1, 2, 3, 6, 7, 9, 10, 11}

    def test_modalidades_none_accepted(self):
        """None modalidades should be accepted (means all)."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            modalidades=None,
        )
        assert request.modalidades is None

    def test_modalidades_empty_list_accepted(self):
        """Empty modalidades list should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            modalidades=[],
        )
        assert request.modalidades == []

    def test_concurso_code_11_accepted(self):
        """Code 11 (Concurso) should be accepted - NEW in Lei 14.133/2021."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            modalidades=[11],
        )
        assert request.modalidades == [11]
