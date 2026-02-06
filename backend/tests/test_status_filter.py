"""
Unit tests for filtrar_por_status() and status-related filtering.

Tests cover:
- Default status is recebendo_proposta
- All enum values work correctly
- Invalid status handled gracefully
- Query parameter inclusion for PNCP API
"""

import pytest
from filter import filtrar_por_status
from schemas import StatusLicitacao, BuscaRequest
from pydantic import ValidationError
from datetime import date, timedelta


def _recent_dates(days_back: int = 7) -> tuple[str, str]:
    """Return a valid recent date range for tests."""
    today = date.today()
    return (today - timedelta(days=days_back)).isoformat(), today.isoformat()


class TestStatusEnumDefinition:
    """Tests for StatusLicitacao enum definition."""

    def test_all_status_values_exist(self):
        """All expected status values should be defined."""
        assert StatusLicitacao.RECEBENDO_PROPOSTA.value == "recebendo_proposta"
        assert StatusLicitacao.EM_JULGAMENTO.value == "em_julgamento"
        assert StatusLicitacao.ENCERRADA.value == "encerrada"
        assert StatusLicitacao.TODOS.value == "todos"

    def test_status_enum_count(self):
        """Should have exactly 4 status options."""
        assert len(StatusLicitacao) == 4

    def test_status_from_string(self):
        """Should create enum from string value."""
        status = StatusLicitacao("recebendo_proposta")
        assert status == StatusLicitacao.RECEBENDO_PROPOSTA


class TestDefaultStatusIsRecebendoProposta:
    """Tests verifying default status is 'recebendo_proposta'."""

    def test_default_status_in_busca_request(self):
        """BuscaRequest should default to 'recebendo_proposta'."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
        )
        assert request.status == StatusLicitacao.RECEBENDO_PROPOSTA

    def test_explicit_status_recebendo_proposta(self):
        """Explicit 'recebendo_proposta' should work."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            status="recebendo_proposta",
        )
        assert request.status == StatusLicitacao.RECEBENDO_PROPOSTA


class TestAllStatusEnumValues:
    """Tests for all status enum values."""

    def test_status_recebendo_proposta_filtering(self):
        """Should filter bids receiving proposals."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Aberta"},
            {"situacaoCompra": "Encerrada"},
            {"situacaoCompra": "Em julgamento"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 2
        assert all(
            "recebendo" in b["situacaoCompra"].lower() or
            "aberta" in b["situacaoCompra"].lower()
            for b in result
        )

    def test_status_em_julgamento_filtering(self):
        """Should filter bids under evaluation."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Em julgamento"},
            {"situacaoCompra": "Propostas encerradas"},
            {"situacaoCompra": "Encerrada"},
        ]
        result = filtrar_por_status(bids, "em_julgamento")
        assert len(result) == 2

    def test_status_encerrada_filtering(self):
        """Should filter closed/finalized bids."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Encerrada"},
            {"situacaoCompra": "Homologada"},
            {"situacaoCompra": "Adjudicada"},
            {"situacaoCompra": "Anulada"},
        ]
        result = filtrar_por_status(bids, "encerrada")
        assert len(result) == 4

    def test_status_todos_returns_all(self):
        """Status 'todos' should return all bids."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Encerrada"},
        ]
        result = filtrar_por_status(bids, "todos")
        assert len(result) == 2

    def test_status_none_returns_all(self):
        """None status should return all bids."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Encerrada"},
        ]
        result = filtrar_por_status(bids, None)
        assert len(result) == 2

    def test_status_empty_string_returns_all(self):
        """Empty string status should return all bids (same as 'todos')."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Encerrada"},
        ]
        result = filtrar_por_status(bids, "")
        assert len(result) == 2


class TestInvalidStatusHandling:
    """Tests for invalid status handling."""

    def test_unknown_status_returns_all(self):
        """Unknown status should return all bids (graceful fallback)."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
            {"situacaoCompra": "Encerrada"},
        ]
        result = filtrar_por_status(bids, "status_invalido")
        assert len(result) == 2

    def test_invalid_status_in_schema_raises_error(self):
        """Invalid status in BuscaRequest should raise validation error."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError):
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                status="invalido",
            )


class TestStatusFilterFieldVariants:
    """Tests for different field names containing status."""

    def test_uses_situacaoCompra_field(self):
        """Should use situacaoCompra as primary field."""
        bids = [
            {"situacaoCompra": "Recebendo propostas"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 1

    def test_uses_situacao_as_fallback(self):
        """Should check 'situacao' field as fallback."""
        bids = [
            {"situacao": "Recebendo propostas"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 1

    def test_uses_statusCompra_as_fallback(self):
        """Should check 'statusCompra' field as fallback."""
        bids = [
            {"statusCompra": "Aberta"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 1

    def test_bid_with_no_status_fields_excluded(self):
        """Bid with no status fields should not match any filter."""
        bids = [
            {},  # No situacaoCompra, situacao, or statusCompra
            {"situacaoCompra": "Recebendo propostas"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 1


class TestStatusFilterCaseInsensitivity:
    """Tests for case insensitivity in status matching."""

    def test_status_case_insensitive(self):
        """Should handle case variations."""
        bids = [
            {"situacaoCompra": "RECEBENDO PROPOSTAS"},
            {"situacaoCompra": "recebendo propostas"},
            {"situacaoCompra": "Recebendo Propostas"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 3

    def test_status_with_extra_whitespace(self):
        """Status with extra whitespace should still match."""
        bids = [
            {"situacaoCompra": "  Recebendo propostas  "},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 1


class TestStatusFilterEdgeCases:
    """Edge case tests for status filtering."""

    def test_empty_list_returns_empty(self):
        """Empty bid list should return empty list."""
        result = filtrar_por_status([], "recebendo_proposta")
        assert result == []

    def test_bid_with_none_status_value(self):
        """Bid with None as status value should be handled."""
        bids = [
            {"situacaoCompra": None},
            {"situacaoCompra": "Recebendo propostas"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 1

    def test_status_accepts_all_valid_enum_string_values(self):
        """All valid enum string values should be accepted in BuscaRequest."""
        d_ini, d_fin = _recent_dates(7)
        valid_values = [
            "recebendo_proposta",
            "em_julgamento",
            "encerrada",
            "todos"
        ]
        for status_value in valid_values:
            request = BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                status=status_value,
            )
            assert request.status.value == status_value
