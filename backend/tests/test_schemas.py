"""Tests for Pydantic schemas (API request/response validation)."""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError
from schemas import (
    BuscaRequest,
    BuscaResponse,
    ResumoLicitacoes,
    StatusLicitacao,
    ModalidadeContratacao,
    EsferaGovernamental,
)


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
            excel_available=True,
            quota_used=10,
            quota_remaining=40,
        )

        assert response.total_raw == 523
        assert response.total_filtrado == 10
        assert isinstance(response.resumo, ResumoLicitacoes)
        assert response.excel_available is True
        assert response.quota_used == 10
        assert response.quota_remaining == 40

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
                excel_available=True,
                quota_used=0,
                quota_remaining=50,
            )

    def test_negative_totals_rejected(self):
        """Negative total_raw or total_filtrado should be rejected."""
        resumo = ResumoLicitacoes(
            resumo_executivo="Test", total_oportunidades=0, valor_total=0.0
        )

        # Negative total_raw
        with pytest.raises(ValidationError):
            BuscaResponse(
                resumo=resumo, excel_base64="test", total_raw=-100, total_filtrado=0,
                excel_available=True, quota_used=0, quota_remaining=50
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
            excel_available=False,
            quota_used=1,
            quota_remaining=49,
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
            resumo=resumo, excel_base64="ABC123", total_raw=100, total_filtrado=10,
            excel_available=True, quota_used=5, quota_remaining=45
        )

        json_data = response.model_dump()
        assert "resumo" in json_data
        assert json_data["resumo"]["total_oportunidades"] == 10
        assert json_data["excel_base64"] == "ABC123"
        assert json_data["excel_available"] is True
        assert json_data["quota_used"] == 5
        assert json_data["quota_remaining"] == 45


# ============================================================================
# NEW: Tests for P0/P1 Filters - Enums
# ============================================================================


class TestStatusLicitacaoEnum:
    """Tests for StatusLicitacao enum."""

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


class TestModalidadeContratacaoEnum:
    """Tests for ModalidadeContratacao enum (Lei 14.133/2021)."""

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
        """Codes 4, 5, 8 should NOT exist (Lei 8.666/93 deprecated)."""
        with pytest.raises(AttributeError):
            _ = ModalidadeContratacao.TOMADA_PRECOS
        with pytest.raises(AttributeError):
            _ = ModalidadeContratacao.CONVITE
        with pytest.raises(AttributeError):
            _ = ModalidadeContratacao.CREDENCIAMENTO

    def test_modalidade_enum_count(self):
        """Should have exactly 8 Lei 14.133/2021 modalidade options."""
        assert len(ModalidadeContratacao) == 8

    def test_modalidade_codes_match_lei_14133(self):
        """Modalidade codes should be 1,2,3,6,7,9,10,11 only."""
        codes = sorted([m.value for m in ModalidadeContratacao])
        assert codes == [1, 2, 3, 6, 7, 9, 10, 11]




class TestEsferaGovernamentalEnum:
    """Tests for EsferaGovernamental enum."""

    def test_all_esfera_values_exist(self):
        """All esfera codes should be defined."""
        assert EsferaGovernamental.FEDERAL.value == "F"
        assert EsferaGovernamental.ESTADUAL.value == "E"
        assert EsferaGovernamental.MUNICIPAL.value == "M"

    def test_esfera_enum_count(self):
        """Should have exactly 3 esfera options."""
        assert len(EsferaGovernamental) == 3


# ============================================================================
# NEW: Tests for BuscaRequest P0/P1 Filters Validation
# ============================================================================


class TestBuscaRequestValorValidation:
    """Tests for valor_minimo and valor_maximo validation."""

    def test_valor_maximo_greater_than_minimo_accepted(self):
        """valor_maximo >= valor_minimo should be accepted."""
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

    def test_valor_maximo_equal_to_minimo_accepted(self):
        """valor_maximo == valor_minimo should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            valor_minimo=100000,
            valor_maximo=100000,
        )
        assert request.valor_minimo == request.valor_maximo

    def test_valor_maximo_less_than_minimo_rejected(self):
        """valor_maximo < valor_minimo should be rejected."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                valor_minimo=500000,
                valor_maximo=50000,
            )
        assert "valor_maximo deve ser maior ou igual" in str(exc_info.value)

    def test_valor_minimo_only_accepted(self):
        """Only valor_minimo without valor_maximo should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            valor_minimo=50000,
        )
        assert request.valor_minimo == 50000
        assert request.valor_maximo is None

    def test_valor_maximo_only_accepted(self):
        """Only valor_maximo without valor_minimo should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            valor_maximo=500000,
        )
        assert request.valor_minimo is None
        assert request.valor_maximo == 500000

    def test_valor_minimo_negative_rejected(self):
        """Negative valor_minimo should be rejected."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError):
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                valor_minimo=-1000,
            )

    def test_valor_maximo_negative_rejected(self):
        """Negative valor_maximo should be rejected."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError):
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                valor_maximo=-1000,
            )

    def test_valor_zero_accepted(self):
        """Zero values should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            valor_minimo=0,
            valor_maximo=0,
        )
        assert request.valor_minimo == 0
        assert request.valor_maximo == 0


class TestBuscaRequestModalidadeValidation:
    """Tests for modalidades validation."""

    def test_valid_modalidade_codes_accepted(self):
        """Valid modalidade codes (1-10) should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            modalidades=[1, 2, 6],
        )
        assert request.modalidades == [1, 2, 6]

    def test_all_modalidade_codes_accepted(self):
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

    def test_invalid_modalidade_code_zero_rejected(self):
        """Modalidade code 0 should be rejected."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                modalidades=[0, 1],
            )
        assert "inválidos" in str(exc_info.value).lower()

    def test_invalid_modalidade_code_twelve_rejected(self):
        """Modalidade code 12 should be rejected (beyond Lei 14.133/2021 range)."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                modalidades=[12],
            )
        assert "inválidos" in str(exc_info.value).lower() or "12" in str(exc_info.value)

    def test_invalid_modalidade_negative_rejected(self):
        """Negative modalidade code should be rejected."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError):
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                modalidades=[-1],
            )

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


class TestBuscaRequestOrdenacaoValidation:
    """Tests for ordenacao validation."""

    def test_valid_ordenacao_data_desc(self):
        """'data_desc' should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            ordenacao="data_desc",
        )
        assert request.ordenacao == "data_desc"

    def test_valid_ordenacao_data_asc(self):
        """'data_asc' should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            ordenacao="data_asc",
        )
        assert request.ordenacao == "data_asc"

    def test_valid_ordenacao_valor_desc(self):
        """'valor_desc' should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            ordenacao="valor_desc",
        )
        assert request.ordenacao == "valor_desc"

    def test_valid_ordenacao_valor_asc(self):
        """'valor_asc' should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            ordenacao="valor_asc",
        )
        assert request.ordenacao == "valor_asc"

    def test_valid_ordenacao_prazo_asc(self):
        """'prazo_asc' should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            ordenacao="prazo_asc",
        )
        assert request.ordenacao == "prazo_asc"

    def test_valid_ordenacao_relevancia(self):
        """'relevancia' should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            ordenacao="relevancia",
        )
        assert request.ordenacao == "relevancia"

    def test_invalid_ordenacao_rejected(self):
        """Invalid ordenacao should be rejected."""
        d_ini, d_fin = _recent_dates(7)
        with pytest.raises(ValidationError) as exc_info:
            BuscaRequest(
                ufs=["SP"],
                data_inicial=d_ini,
                data_final=d_fin,
                ordenacao="invalid_option",
            )
        assert "inválida" in str(exc_info.value).lower()

    def test_default_ordenacao_is_data_desc(self):
        """Default ordenacao should be 'data_desc'."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
        )
        assert request.ordenacao == "data_desc"


class TestBuscaRequestStatusValidation:
    """Tests for status validation."""

    def test_default_status_is_recebendo_proposta(self):
        """Default status should be 'todos' (changed from recebendo_proposta)."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
        )
        assert request.status == StatusLicitacao.TODOS

    def test_status_todos_accepted(self):
        """Status 'todos' should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            status=StatusLicitacao.TODOS,
        )
        assert request.status == StatusLicitacao.TODOS

    def test_status_enum_value_accepted(self):
        """Status enum value should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            status="encerrada",
        )
        assert request.status == StatusLicitacao.ENCERRADA


class TestBuscaRequestEsferaValidation:
    """Tests for esferas validation."""

    def test_valid_esferas_accepted(self):
        """Valid esfera codes should be accepted."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP"],
            data_inicial=d_ini,
            data_final=d_fin,
            esferas=[EsferaGovernamental.MUNICIPAL, EsferaGovernamental.ESTADUAL],
        )
        assert len(request.esferas) == 2

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


class TestBuscaRequestFullRequest:
    """Tests for complete BuscaRequest with all P0/P1 fields."""

    def test_complete_request_with_all_filters(self):
        """Complete request with all filters should be valid."""
        d_ini, d_fin = _recent_dates(7)
        request = BuscaRequest(
            ufs=["SP", "RJ"],
            data_inicial=d_ini,
            data_final=d_fin,
            setor_id="vestuario",
            termos_busca="jaleco avental",
            status=StatusLicitacao.RECEBENDO_PROPOSTA,
            modalidades=[1, 2, 6],
            valor_minimo=50000,
            valor_maximo=500000,
            esferas=[EsferaGovernamental.MUNICIPAL],
            municipios=["3550308", "3304557"],
            ordenacao="valor_desc",
        )

        assert request.ufs == ["SP", "RJ"]
        assert request.setor_id == "vestuario"
        assert request.termos_busca == "jaleco avental"
        assert request.status == StatusLicitacao.RECEBENDO_PROPOSTA
        assert request.modalidades == [1, 2, 6]
        assert request.valor_minimo == 50000
        assert request.valor_maximo == 500000
        assert len(request.esferas) == 1
        assert request.municipios == ["3550308", "3304557"]
        assert request.ordenacao == "valor_desc"
