"""Unit tests for SearchPipeline Stages 6-7 + helper functions."""

import pytest
import asyncio
from io import BytesIO
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, AsyncMock

from search_context import SearchContext
from search_pipeline import (
    SearchPipeline,
    _build_pncp_link,
    _calcular_urgencia,
    _calcular_dias_restantes,
    _convert_to_licitacao_items,
)
from schemas import LicitacaoItem, ResumoLicitacoes, ResumoEstrategico, BuscaResponse


# ============================================================================
# Factories
# ============================================================================


def make_deps(**overrides):
    """Create deps namespace with sensible defaults."""
    defaults = {
        "ENABLE_NEW_PRICING": False,
        "PNCPClient": MagicMock,
        "buscar_todas_ufs_paralelo": AsyncMock(return_value=[]),
        "aplicar_todos_filtros": MagicMock(return_value=([], {})),
        "create_excel": MagicMock(),
        "rate_limiter": MagicMock(),
        "check_user_roles": MagicMock(return_value=(False, False)),
        "match_keywords": MagicMock(return_value=(True, [])),
        "KEYWORDS_UNIFORMES": set(),
        "KEYWORDS_EXCLUSAO": set(),
        "validate_terms": MagicMock(return_value={"valid": [], "ignored": [], "reasons": {}}),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_request(**overrides):
    """Create a minimal BuscaRequest-like object."""
    defaults = {
        "ufs": ["SC"],
        "data_inicial": "2026-01-01",
        "data_final": "2026-01-07",
        "setor_id": "vestuario",
        "termos_busca": None,
        "show_all_matches": False,
        "exclusion_terms": None,
        "status": MagicMock(value="todos"),
        "modalidades": None,
        "valor_minimo": None,
        "valor_maximo": None,
        "esferas": None,
        "municipios": None,
        "ordenacao": "relevancia",
        "search_id": "test-search-123",
        "modo_busca": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_licitacao(**overrides):
    """Create a minimal raw licitacao dictionary."""
    defaults = {
        "codigoCompra": "CODE-001",
        "objetoCompra": "Aquisicao de uniformes escolares para alunos",
        "nomeOrgao": "Prefeitura Municipal de Florianopolis",
        "uf": "SC",
        "municipio": "Florianopolis",
        "valorTotalEstimado": 50000.0,
        "modalidadeNome": "Pregao Eletronico",
        "dataPublicacaoPncp": "2026-01-02T10:00:00",
        "dataAberturaProposta": "2026-01-10T08:00:00",
        "dataEncerramentoProposta": "2026-03-15T18:00:00",
        "linkSistemaOrigem": "https://pncp.gov.br/app/editais/123",
        "numeroControlePNCP": "12345678000100-1-00001/2026",
    }
    defaults.update(overrides)
    return defaults


def make_resumo(**overrides):
    """Create a ResumoEstrategico instance."""
    defaults = {
        "resumo_executivo": "Encontradas 2 licitacoes de vestuario em SC.",
        "total_oportunidades": 2,
        "valor_total": 100000.0,
        "destaques": ["2 oportunidades em SC"],
        "alerta_urgencia": None,
    }
    defaults.update(overrides)
    return ResumoEstrategico(**defaults)


def make_ctx(**overrides):
    """Create a SearchContext with sensible defaults for stage 6/7 tests."""
    defaults = {
        "request": make_request(),
        "user": {"id": "user-abc-123", "email": "test@test.com"},
        "sector": SimpleNamespace(name="Vestuario"),
        "quota_info": SimpleNamespace(
            capabilities={"allow_excel": False},
            quota_used=1,
            quota_remaining=49,
        ),
        "licitacoes_raw": [make_licitacao()],
        "licitacoes_filtradas": [],
        "filter_stats": {
            "rejeitadas_uf": 0,
            "rejeitadas_valor": 0,
            "rejeitadas_keyword": 0,
            "rejeitadas_min_match": 0,
            "rejeitadas_prazo": 0,
            "rejeitadas_outros": 0,
        },
        "custom_terms": [],
        "stopwords_removed": [],
        "source_stats_data": None,
        "hidden_by_min_match": 0,
        "filter_relaxed": False,
        "tracker": None,
    }
    defaults.update(overrides)

    ctx = SearchContext(
        request=defaults.pop("request"),
        user=defaults.pop("user"),
    )
    for k, v in defaults.items():
        setattr(ctx, k, v)
    return ctx


# ============================================================================
# TestBuildPncpLink
# ============================================================================


class TestBuildPncpLink:
    """Tests for _build_pncp_link helper function."""

    def test_returns_link_sistema_origem_when_present(self):
        """linkSistemaOrigem has highest priority."""
        lic = {
            "linkSistemaOrigem": "https://compras.gov.br/123",
            "linkProcessoEletronico": "https://outro.gov.br/456",
            "numeroControlePNCP": "12345678000100-1-00001/2026",
        }
        assert _build_pncp_link(lic) == "https://compras.gov.br/123"

    def test_falls_back_to_link_processo_eletronico(self):
        """When linkSistemaOrigem is absent, uses linkProcessoEletronico."""
        lic = {
            "linkProcessoEletronico": "https://processo.gov.br/456",
            "numeroControlePNCP": "12345678000100-1-00001/2026",
        }
        assert _build_pncp_link(lic) == "https://processo.gov.br/456"

    def test_constructs_url_from_numero_controle(self):
        """When no direct links, constructs URL from numeroControlePNCP."""
        lic = {"numeroControlePNCP": "12345678000100-1-00001/2026"}
        result = _build_pncp_link(lic)
        assert result == "https://pncp.gov.br/app/editais/12345678000100/2026/1"

    def test_returns_empty_when_no_data(self):
        """Returns empty string when no link fields exist."""
        lic = {}
        assert _build_pncp_link(lic) == ""

    def test_returns_empty_for_malformed_numero_controle(self):
        """Malformed numeroControlePNCP handled gracefully, returns empty."""
        lic = {"numeroControlePNCP": "invalid-format"}
        assert _build_pncp_link(lic) == ""


# ============================================================================
# TestCalcularUrgencia
# ============================================================================


class TestCalcularUrgencia:
    """Tests for _calcular_urgencia helper function."""

    def test_none_input_returns_none(self):
        """None days_restantes returns None."""
        assert _calcular_urgencia(None) is None

    def test_negative_days_returns_encerrada(self):
        """Negative days means the deadline has passed."""
        assert _calcular_urgencia(-1) == "encerrada"
        assert _calcular_urgencia(-100) == "encerrada"

    def test_zero_to_six_days_returns_critica(self):
        """0-6 days is critical urgency."""
        assert _calcular_urgencia(0) == "critica"
        assert _calcular_urgencia(3) == "critica"
        assert _calcular_urgencia(6) == "critica"

    def test_seven_to_thirteen_days_returns_alta(self):
        """7-13 days is high urgency."""
        assert _calcular_urgencia(7) == "alta"
        assert _calcular_urgencia(10) == "alta"
        assert _calcular_urgencia(13) == "alta"

    def test_fourteen_to_thirty_days_returns_media(self):
        """14-30 days is medium urgency."""
        assert _calcular_urgencia(14) == "media"
        assert _calcular_urgencia(20) == "media"
        assert _calcular_urgencia(30) == "media"

    def test_thirty_one_plus_days_returns_baixa(self):
        """31+ days is low urgency."""
        assert _calcular_urgencia(31) == "baixa"
        assert _calcular_urgencia(100) == "baixa"
        assert _calcular_urgencia(365) == "baixa"


# ============================================================================
# TestCalcularDiasRestantes
# ============================================================================


class TestCalcularDiasRestantes:
    """Tests for _calcular_dias_restantes helper function."""

    def test_none_input_returns_none(self):
        """None date string returns None."""
        assert _calcular_dias_restantes(None) is None

    def test_valid_future_date_returns_positive_int(self):
        """A future date returns positive number of days."""
        future = date.today() + timedelta(days=10)
        result = _calcular_dias_restantes(future.isoformat())
        assert result == 10
        assert isinstance(result, int)

    def test_invalid_date_string_returns_none(self):
        """An invalid date string returns None."""
        assert _calcular_dias_restantes("not-a-date") is None
        assert _calcular_dias_restantes("2026-99-99") is None


# ============================================================================
# TestConvertToLicitacaoItems
# ============================================================================


class TestConvertToLicitacaoItems:
    """Tests for _convert_to_licitacao_items helper function."""

    def test_basic_conversion(self):
        """Converts a dict with all fields to a LicitacaoItem."""
        lic = make_licitacao()
        result = _convert_to_licitacao_items([lic])
        assert len(result) == 1
        item = result[0]
        assert isinstance(item, LicitacaoItem)
        assert item.pncp_id == "CODE-001"
        assert item.objeto.startswith("Aquisicao de uniformes")
        assert item.orgao == "Prefeitura Municipal de Florianopolis"
        assert item.uf == "SC"
        assert item.valor == 50000.0
        assert item.link == "https://pncp.gov.br/app/editais/123"

    def test_missing_optional_fields(self):
        """Handles missing optional fields with graceful defaults."""
        lic = {
            "objetoCompra": "Servicos gerais",
            "nomeOrgao": "Orgao Teste",
            "uf": "RJ",
        }
        result = _convert_to_licitacao_items([lic])
        assert len(result) == 1
        item = result[0]
        assert item.valor == 0.0
        assert item.municipio is None
        assert item.modalidade is None
        assert item.data_publicacao is None

    def test_malformed_item_skipped(self):
        """A bad item does not crash the conversion; good items proceed."""
        good_lic = make_licitacao()
        # A truly malformed dict that causes an exception inside the try block.
        # Setting objetoCompra to an int so [:500] will raise TypeError.
        bad_lic = {"objetoCompra": 12345}
        result = _convert_to_licitacao_items([bad_lic, good_lic])
        assert len(result) == 1
        assert result[0].pncp_id == "CODE-001"


# ============================================================================
# TestStageGenerate (Stage 6)
# ============================================================================


class TestStageGenerate:
    """Tests for SearchPipeline.stage_generate (Stage 6)."""

    @pytest.mark.asyncio
    async def test_empty_results_path(self):
        """No licitacoes_filtradas: response has empty licitacoes, no LLM called."""
        deps = make_deps()
        pipeline = SearchPipeline(deps)
        ctx = make_ctx(licitacoes_filtradas=[], licitacoes_raw=[make_licitacao()])

        with patch("search_pipeline.gerar_resumo") as mock_resumo:
            await pipeline.stage_generate(ctx)

        mock_resumo.assert_not_called()
        assert ctx.response is not None
        assert ctx.response.licitacoes == []
        assert ctx.response.total_filtrado == 0
        assert ctx.response.total_raw == 1
        assert ctx.response.resumo.total_oportunidades == 0

    @pytest.mark.asyncio
    async def test_llm_summary_generated(self):
        """With filtered results, gerar_resumo is called and response includes resumo."""
        deps = make_deps()
        buf = BytesIO(b"fake-excel")
        deps.create_excel = MagicMock(return_value=buf)

        lics = [make_licitacao(), make_licitacao(codigoCompra="CODE-002", valorTotalEstimado=60000.0)]
        resumo = make_resumo(total_oportunidades=2, valor_total=110000.0)

        pipeline = SearchPipeline(deps)
        ctx = make_ctx(
            licitacoes_filtradas=lics,
            licitacoes_raw=lics,
            quota_info=SimpleNamespace(
                capabilities={"allow_excel": False},
                quota_used=1,
                quota_remaining=49,
            ),
        )

        with patch("search_pipeline.gerar_resumo", return_value=resumo) as mock_resumo, \
             patch("search_pipeline.upload_excel"):
            await pipeline.stage_generate(ctx)

        mock_resumo.assert_called_once_with(lics, sector_name="Vestuario")
        assert ctx.response is not None
        assert ctx.response.resumo.resumo_executivo == resumo.resumo_executivo
        # Actual totals override LLM values
        assert ctx.response.resumo.total_oportunidades == 2
        assert ctx.response.resumo.valor_total == 110000.0
        assert ctx.response.total_filtrado == 2

    @pytest.mark.asyncio
    async def test_llm_fallback_on_error(self):
        """When gerar_resumo raises, gerar_resumo_fallback is used instead."""
        deps = make_deps()
        buf = BytesIO(b"fake-excel")
        deps.create_excel = MagicMock(return_value=buf)

        lics = [make_licitacao()]
        fallback_resumo = make_resumo(resumo_executivo="Fallback summary")

        pipeline = SearchPipeline(deps)
        ctx = make_ctx(
            licitacoes_filtradas=lics,
            licitacoes_raw=lics,
            quota_info=SimpleNamespace(
                capabilities={"allow_excel": False},
                quota_used=1,
                quota_remaining=49,
            ),
        )

        with patch("search_pipeline.gerar_resumo", side_effect=Exception("LLM timeout")), \
             patch("search_pipeline.gerar_resumo_fallback", return_value=fallback_resumo) as mock_fb, \
             patch("search_pipeline.upload_excel"):
            await pipeline.stage_generate(ctx)

        mock_fb.assert_called_once_with(lics, sector_name="Vestuario")
        assert ctx.response.resumo.resumo_executivo == "Fallback summary"

    @pytest.mark.asyncio
    async def test_excel_generated_when_allowed(self):
        """When quota allows Excel, create_excel is called and upload attempted."""
        buf = BytesIO(b"fake-excel-bytes")
        deps = make_deps()
        deps.create_excel = MagicMock(return_value=buf)

        lics = [make_licitacao()]
        resumo = make_resumo()

        pipeline = SearchPipeline(deps)
        ctx = make_ctx(
            licitacoes_filtradas=lics,
            licitacoes_raw=lics,
            quota_info=SimpleNamespace(
                capabilities={"allow_excel": True},
                quota_used=1,
                quota_remaining=49,
            ),
        )

        signed_url = "https://storage.example.com/excel/signed"
        storage_result = {"signed_url": signed_url, "file_path": "excels/test.xlsx", "expires_in": 3600}

        with patch("search_pipeline.gerar_resumo", return_value=resumo), \
             patch("search_pipeline.upload_excel", return_value=storage_result) as mock_upload:
            await pipeline.stage_generate(ctx)

        deps.create_excel.assert_called_once_with(lics)
        mock_upload.assert_called_once()
        assert ctx.response.excel_available is True
        assert ctx.response.download_url == signed_url


# ============================================================================
# TestStagePersist (Stage 7)
# ============================================================================


class TestStagePersist:
    """Tests for SearchPipeline.stage_persist (Stage 7)."""

    @pytest.mark.asyncio
    async def test_session_saved_for_results(self):
        """quota.save_search_session called with correct params for non-empty results."""
        deps = make_deps()
        pipeline = SearchPipeline(deps)

        lics = [make_licitacao()]
        resumo = make_resumo()
        response = MagicMock(spec=BuscaResponse)

        ctx = make_ctx(
            licitacoes_filtradas=lics,
            licitacoes_raw=lics,
            resumo=resumo,
            response=response,
        )

        with patch("search_pipeline.quota") as mock_quota:
            mock_quota.save_search_session.return_value = "session-uuid-1234"
            result = await pipeline.stage_persist(ctx)

        mock_quota.save_search_session.assert_called_once_with(
            user_id="user-abc-123",
            sectors=["vestuario"],
            ufs=["SC"],
            data_inicial="2026-01-01",
            data_final="2026-01-07",
            custom_keywords=None,
            total_raw=1,
            total_filtered=1,
            valor_total=resumo.valor_total,
            resumo_executivo=resumo.resumo_executivo,
            destaques=resumo.destaques,
        )
        assert ctx.session_id == "session-uuid-1234"
        assert result is response

    @pytest.mark.asyncio
    async def test_session_save_failure_does_not_crash(self):
        """If save_search_session raises, response is still returned."""
        deps = make_deps()
        pipeline = SearchPipeline(deps)

        lics = [make_licitacao()]
        resumo = make_resumo()
        response = MagicMock(spec=BuscaResponse)

        ctx = make_ctx(
            licitacoes_filtradas=lics,
            licitacoes_raw=lics,
            resumo=resumo,
            response=response,
        )

        with patch("search_pipeline.quota") as mock_quota:
            mock_quota.save_search_session.side_effect = Exception("DB connection failed")
            result = await pipeline.stage_persist(ctx)

        # Response is still returned despite save failure
        assert result is response

    @pytest.mark.asyncio
    async def test_empty_results_early_return(self):
        """When ctx.response is set and no filtered results, returns existing response."""
        deps = make_deps()
        pipeline = SearchPipeline(deps)

        existing_response = MagicMock(spec=BuscaResponse)
        resumo = make_resumo(total_oportunidades=0, valor_total=0.0)

        ctx = make_ctx(
            licitacoes_filtradas=[],
            licitacoes_raw=[make_licitacao()],
            resumo=resumo,
            response=existing_response,
        )

        with patch("search_pipeline.quota") as mock_quota:
            mock_quota.save_search_session.return_value = "session-empty-uuid"
            result = await pipeline.stage_persist(ctx)

        # Session is still saved even for 0 results
        mock_quota.save_search_session.assert_called_once()
        call_kwargs = mock_quota.save_search_session.call_args[1]
        assert call_kwargs["total_filtered"] == 0
        assert call_kwargs["valor_total"] == 0.0
        assert call_kwargs["destaques"] == []
        assert result is existing_response
