"""
Tests for deadline terminology clarity in LLM-generated summaries.

NOTE: The deadline terminology validation (ValueError on forbidden terms,
system prompt checks) was removed from llm.py. The current implementation
does not validate or reject LLM output based on terminology.

Tests that relied on ValueError being raised are now skipped.
Tests that verify the fallback function still validate terminology
behavior of the fallback (pure Python, no LLM).
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from llm import gerar_resumo, gerar_resumo_fallback
from schemas import ResumoLicitacoes


# Mock licitacoes for testing
@pytest.fixture
def mock_licitacoes():
    """Sample licitacoes with clear deadline dates."""
    return [
        {
            "objetoCompra": "Confecção de fardamentos escolares",
            "nomeOrgao": "Prefeitura de Porto Alegre",
            "uf": "RS",
            "municipio": "Porto Alegre",
            "valorTotalEstimado": 75000.0,
            "dataAberturaProposta": (datetime.now() + timedelta(days=5)).isoformat(),
        },
        {
            "objetoCompra": "Uniformes para servidores públicos",
            "nomeOrgao": "Prefeitura de Florianópolis",
            "uf": "SC",
            "municipio": "Florianópolis",
            "valorTotalEstimado": 36000.0,
            "dataAberturaProposta": (datetime.now() + timedelta(days=18)).isoformat(),
        },
    ]


class TestLLMDeadlineTerminology:
    """Test suite for deadline terminology validation in LLM summaries."""

    @pytest.mark.skip(reason="Deadline terminology validation (ValueError) removed from gerar_resumo()")
    def test_forbidden_terms_trigger_assertion(self, mock_licitacoes, monkeypatch):
        """
        SKIPPED: LLM output validation (ValueError on forbidden terms) was removed.
        gerar_resumo() no longer raises ValueError for ambiguous terminology.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = ResumoLicitacoes(
            resumo_executivo="Há 2 oportunidades com prazo de abertura em 5 de fevereiro.",
            total_oportunidades=2,
            valor_total=111000.0,
            destaques=["Test"],
            alerta_urgencia=None,
        )

        with patch("llm.OpenAI") as mock_openai:
            mock_openai.return_value.beta.chat.completions.parse.return_value = mock_response

            with pytest.raises(ValueError) as exc_info:
                gerar_resumo(mock_licitacoes)

            assert "ambiguous deadline terminology" in str(exc_info.value).lower()
            assert "prazo de abertura" in str(exc_info.value)

    @pytest.mark.skip(reason="Deadline terminology validation (ValueError) removed from gerar_resumo()")
    def test_forbidden_abertura_em_triggers_assertion(self, mock_licitacoes, monkeypatch):
        """
        SKIPPED: LLM output validation (ValueError on forbidden terms) was removed.
        """
        pass

    def test_clear_terminology_passes_validation(self, mock_licitacoes, monkeypatch):
        """
        LLM output should be returned as-is (no terminology validation).
        """
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = ResumoLicitacoes(
            resumo_executivo=(
                "Há 2 oportunidades em uniformes no Sul totalizando R$ 111.000. "
                "Maior licitação: R$ 75.000 da Prefeitura de Porto Alegre."
            ),
            total_oportunidades=2,
            valor_total=111000.0,
            destaques=["Porto Alegre: R$ 75.000", "Florianópolis: R$ 36.000"],
            alerta_urgencia=None,
        )

        with patch("llm.OpenAI") as mock_openai:
            mock_openai.return_value.beta.chat.completions.parse.return_value = mock_response

            # Should NOT raise exception
            resumo = gerar_resumo(mock_licitacoes)

            assert resumo.total_oportunidades == 2

    def test_fallback_uses_clear_terminology(self, mock_licitacoes):
        """
        Fallback function must use clear, non-ambiguous output.
        gerar_resumo_fallback() accepts optional sector_name and termos_busca kwargs.
        """
        resumo = gerar_resumo_fallback(mock_licitacoes)

        # Validate no forbidden terms in fallback output
        assert "prazo de abertura" not in resumo.resumo_executivo.lower()
        assert "abertura em" not in resumo.resumo_executivo.lower()

        # Should contain clear information
        assert resumo.total_oportunidades == 2
        assert resumo.valor_total == 111000.0

    def test_urgent_alert_uses_clear_terminology(self):
        """
        Urgency alerts in fallback must use clear language.
        """
        urgent_licitacoes = [
            {
                "objetoCompra": "Fardamentos urgentes",
                "nomeOrgao": "Prefeitura Teste",
                "uf": "SP",
                "municipio": "São Paulo",
                "valorTotalEstimado": 50000.0,
                "dataAberturaProposta": (datetime.now() + timedelta(days=3)).isoformat(),
            }
        ]

        resumo = gerar_resumo_fallback(urgent_licitacoes)

        if resumo.alerta_urgencia:
            # Validate alert doesn't use ambiguous terminology
            assert "prazo de abertura" not in resumo.alerta_urgencia.lower()

    @pytest.mark.skip(reason="System prompt no longer includes forbidden terms list / NUNCA use instructions")
    def test_system_prompt_includes_forbidden_terms_list(self):
        """
        SKIPPED: System prompt no longer includes forbidden terms list.
        The deadline terminology validation was removed from llm.py.
        """
        import llm
        import inspect

        source = inspect.getsource(llm.gerar_resumo)

        assert "prazo de abertura" in source
        assert "abertura em" in source
        assert "NUNCA use" in source or "NEVER use" in source.lower()

    @pytest.mark.skip(reason="System prompt no longer contains these specific example phrases")
    def test_system_prompt_includes_correct_examples(self):
        """
        SKIPPED: System prompt examples changed.
        """
        import llm
        import inspect

        source = inspect.getsource(llm.gerar_resumo)

        assert "recebe propostas" in source.lower()
        assert "prazo final" in source.lower()
        assert "você tem" in source.lower()


class TestAssertionLogging:
    """Test that assertion failures are logged for monitoring."""

    @pytest.mark.skip(reason="ValueError / assertion logging removed from gerar_resumo()")
    def test_assertion_failure_is_logged(self, mock_licitacoes, monkeypatch):
        """
        SKIPPED: ValueError is no longer raised, so assertion logging doesn't happen.
        """
        pass


class TestEdgeCases:
    """Test edge cases for deadline terminology."""

    def test_empty_licitacoes_has_clear_message(self):
        """
        Empty result set should have clear, non-ambiguous message.
        """
        resumo = gerar_resumo_fallback([])

        assert resumo.total_oportunidades == 0
        assert "nenhuma" in resumo.resumo_executivo.lower()
        # Should not contain any date-related ambiguous terms
        assert "prazo" not in resumo.resumo_executivo.lower()

    def test_single_licitacao_clarity(self):
        """
        Single bid should also follow clear terminology rules.
        """
        single = [
            {
                "objetoCompra": "Uniformes escolares",
                "nomeOrgao": "Escola Estadual",
                "uf": "MG",
                "municipio": "Belo Horizonte",
                "valorTotalEstimado": 30000.0,
                "dataAberturaProposta": (datetime.now() + timedelta(days=10)).isoformat(),
            }
        ]

        resumo = gerar_resumo_fallback(single)

        # Should not contain ambiguous terms even for single bid
        assert "prazo de abertura" not in resumo.resumo_executivo.lower()
