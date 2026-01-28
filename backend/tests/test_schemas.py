"""Tests for Pydantic schemas (API request/response validation)."""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError
from schemas import BuscaRequest, BuscaResponse, ResumoLicitacoes


def _recent_dates(days_back: int = 7) -> tuple[str, str]:
    """Return a valid recent date range for tests."""
    today = date.today()
    return (today - timedelta(days=days_back)).isoformat(), today.isoformat()


class TestBuscaRequest:
    """Test BuscaRequest schema validation."""

    def test_valid_request(self):
        """Valid request should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP", "RJ"], data_inicial=d_ini, data_final=d_fin
        )
        assert request.ufs == ["SP", "RJ"]
        assert request.data_inicial == d_ini
        assert request.data_final == d_fin

    def test_single_uf(self):
        """Single UF should be valid."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"], data_inicial=d_ini, data_final=d_fin
        )
        assert len(request.ufs) == 1

    def test_multiple_ufs(self):
        """Multiple UFs should be valid."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP", "RJ", "MG", "RS"],
            data_inicial=d_ini,
            data_final=d_fin,
        )
        assert len(request.ufs) == 4

    def test_empty_ufs_rejected(self):
        """Empty UF list should be rejected."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(ufs=[], data_inicial=d_ini, data_final=d_fin)

        errors = exc_info.value.errors()
        assert any("min_length" in str(error) for error in errors)

    def test_missing_ufs_rejected(self):
        """Missing UFs field should be rejected."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(data_inicial=d_ini, data_final=d_fin)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("ufs",) for error in errors)

    def test_valid_date_format(self):
        """Valid date format YYYY-MM-DD should be accepted."""
        today = date.today().isoformat()
        request = BuscaRequest(
            ufs=["SP"], data_inicial=today, data_final=today
        )
        assert request.data_inicial == today

    def test_invalid_date_format_rejected(self):
        """Invalid date formats should be rejected."""
        d_fin = date.today().isoformat()
        invalid_formats = [
            "01/01/2025",  # DD/MM/YYYY
            "2025-1-1",  # Missing leading zeros
            "25-01-01",  # YY-MM-DD
            "2025/01/01",  # Wrong separator
            "01-01-2025",  # DD-MM-YYYY
        ]

        for invalid_date in invalid_formats:
            with pytest.raises(ValidationError):
                BuscaRequest(
                    ufs=["SP"], data_inicial=invalid_date, data_final=d_fin
                )

    def test_missing_date_inicial_rejected(self):
        """Missing data_inicial should be rejected."""
        d_fin = date.today().isoformat()
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(ufs=["SP"], data_final=d_fin)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("data_inicial",) for error in errors)

    def test_missing_date_final_rejected(self):
        """Missing data_final should be rejected."""
        d_ini = (date.today() - timedelta(days=7)).isoformat()
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(ufs=["SP"], data_inicial=d_ini)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("data_final",) for error in errors)

    # --- Date business logic validation tests ---

    def test_data_inicial_after_data_final_rejected(self):
        """data_inicial > data_final should be rejected (the actual PNCP 422 bug)."""
        today = date.today()
        d_ini = today.isoformat()
        d_fin = (today - timedelta(days=5)).isoformat()
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(ufs=["SP"], data_inicial=d_ini, data_final=d_fin)

        assert "anterior ou igual" in str(exc_info.value)

    def test_same_date_accepted(self):
        """Same date for inicial and final should be valid."""
        today = date.today().isoformat()
        request = BuscaRequest(ufs=["SP"], data_inicial=today, data_final=today)
        assert request.data_inicial == request.data_final

    def test_large_date_range_accepted(self):
        """Large date ranges should be accepted (no limit)."""
        today = date.today()
        d_ini = (today - timedelta(days=90)).isoformat()
        d_fin = today.isoformat()
        request = BuscaRequest(ufs=["SP"], data_inicial=d_ini, data_final=d_fin)
        assert request.data_inicial == d_ini

    def test_future_dates_accepted(self):
        """Future dates should be accepted (open range)."""
        today = date.today()
        d_ini = today.isoformat()
        d_fin = (today + timedelta(days=30)).isoformat()
        request = BuscaRequest(ufs=["SP"], data_inicial=d_ini, data_final=d_fin)
        assert request.data_final == d_fin

    def test_impossible_date_rejected(self):
        """Regex-valid but impossible dates like 2025-02-30 should be rejected."""
        with pytest.raises(ValidationError):
            BuscaRequest(ufs=["SP"], data_inicial="2025-02-30", data_final="2025-02-30")


class TestResumoLicitacoes:
    """Test ResumoLicitacoes schema validation."""

    def test_valid_resumo(self):
        """Valid summary should be accepted."""
        resumo = ResumoLicitacoes(
            resumo_executivo="Encontradas 15 licitações.",
            total_oportunidades=15,
            valor_total=2300000.00,
            destaques=["3 urgentes", "Maior valor: R$ 500k"],
            alerta_urgencia="⚠️ 5 encerram em 24h",
        )
        assert resumo.total_oportunidades == 15
        assert resumo.valor_total == 2300000.00
        assert len(resumo.destaques) == 2

    def test_minimal_resumo(self):
        """Minimal summary (no optional fields) should be valid."""
        resumo = ResumoLicitacoes(
            resumo_executivo="Nenhuma licitação encontrada.",
            total_oportunidades=0,
            valor_total=0.0,
        )
        assert resumo.destaques == []  # Default empty list
        assert resumo.alerta_urgencia is None  # Default None

    def test_empty_destaques_list(self):
        """Empty destaques list should be valid."""
        resumo = ResumoLicitacoes(
            resumo_executivo="Test",
            total_oportunidades=0,
            valor_total=0.0,
            destaques=[],
        )
        assert resumo.destaques == []

    def test_negative_total_oportunidades_rejected(self):
        """Negative total_oportunidades should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ResumoLicitacoes(
                resumo_executivo="Test", total_oportunidades=-5, valor_total=0.0
            )

        errors = exc_info.value.errors()
        assert any("greater_than_equal" in str(error) for error in errors)

    def test_negative_valor_total_rejected(self):
        """Negative valor_total should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ResumoLicitacoes(
                resumo_executivo="Test", total_oportunidades=0, valor_total=-1000.0
            )

        errors = exc_info.value.errors()
        assert any("greater_than_equal" in str(error) for error in errors)

    def test_missing_required_fields_rejected(self):
        """Missing required fields should be rejected."""
        with pytest.raises(ValidationError):
            ResumoLicitacoes()

    def test_alerta_urgencia_optional(self):
        """alerta_urgencia can be None."""
        resumo = ResumoLicitacoes(
            resumo_executivo="Test",
            total_oportunidades=5,
            valor_total=100000.0,
            alerta_urgencia=None,
        )
        assert resumo.alerta_urgencia is None


class TestBuscaResponse:
    """Test BuscaResponse schema validation."""

    def test_valid_response(self):
        """Valid response should be accepted."""
        resumo = ResumoLicitacoes(
            resumo_executivo="Test summary",
            total_oportunidades=10,
            valor_total=1500000.0,
            destaques=["Highlight 1"],
        )

        response = BuscaResponse(
            resumo=resumo,
            excel_base64="UEsDBBQABgAIAAAAIQA=",  # Sample base64
            total_raw=523,
            total_filtrado=10,
        )

        assert response.total_raw == 523
        assert response.total_filtrado == 10
        assert isinstance(response.resumo, ResumoLicitacoes)

    def test_nested_resumo_validation(self):
        """Nested ResumoLicitacoes should be validated."""
        # Invalid resumo (negative total)
        with pytest.raises(ValidationError):
            BuscaResponse(
                resumo=ResumoLicitacoes(
                    resumo_executivo="Test",
                    total_oportunidades=-1,  # Invalid
                    valor_total=0.0,
                ),
                excel_base64="test",
                total_raw=0,
                total_filtrado=0,
            )

    def test_negative_totals_rejected(self):
        """Negative total_raw or total_filtrado should be rejected."""
        resumo = ResumoLicitacoes(
            resumo_executivo="Test", total_oportunidades=0, valor_total=0.0
        )

        # Negative total_raw
        with pytest.raises(ValidationError):
            BuscaResponse(
                resumo=resumo, excel_base64="test", total_raw=-100, total_filtrado=0
            )

        # Negative total_filtrado
        with pytest.raises(ValidationError):
            BuscaResponse(
                resumo=resumo, excel_base64="test", total_raw=100, total_filtrado=-10
            )

    def test_empty_excel_base64_accepted(self):
        """Empty excel_base64 string should be accepted (edge case)."""
        resumo = ResumoLicitacoes(
            resumo_executivo="Test", total_oportunidades=0, valor_total=0.0
        )

        response = BuscaResponse(
            resumo=resumo,
            excel_base64="",  # Empty but valid string
            total_raw=0,
            total_filtrado=0,
        )
        assert response.excel_base64 == ""

    def test_missing_fields_rejected(self):
        """Missing required fields should be rejected."""
        with pytest.raises(ValidationError):
            BuscaResponse()


class TestSchemaJSONSerialization:
    """Test JSON serialization of schemas."""

    def test_busca_request_json(self):
        """BuscaRequest should serialize to JSON correctly."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP", "RJ"], data_inicial=d_ini, data_final=d_fin
        )

        json_data = request.model_dump()
        assert json_data["ufs"] == ["SP", "RJ"]
        assert json_data["data_inicial"] == d_ini

    def test_resumo_licitacoes_json(self):
        """ResumoLicitacoes should serialize to JSON correctly."""
        resumo = ResumoLicitacoes(
            resumo_executivo="Test",
            total_oportunidades=5,
            valor_total=100000.0,
            destaques=["A", "B"],
        )

        json_data = resumo.model_dump()
        assert json_data["total_oportunidades"] == 5
        assert len(json_data["destaques"]) == 2

    def test_busca_response_nested_json(self):
        """BuscaResponse with nested objects should serialize correctly."""
        resumo = ResumoLicitacoes(
            resumo_executivo="Test", total_oportunidades=10, valor_total=500000.0
        )

        response = BuscaResponse(
            resumo=resumo, excel_base64="ABC123", total_raw=100, total_filtrado=10
        )

        json_data = response.model_dump()
        assert "resumo" in json_data
        assert json_data["resumo"]["total_oportunidades"] == 10
        assert json_data["excel_base64"] == "ABC123"
