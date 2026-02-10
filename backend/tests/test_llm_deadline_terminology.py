"""
Tests for deadline terminology clarity in LLM-generated summaries.

CRITICAL: These tests ensure the LLM NEVER generates ambiguous deadline
terminology that confuses users about submission deadlines.
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

    def test_forbidden_terms_trigger_assertion(self, mock_licitacoes, monkeypatch):
        """
        CRITICAL: LLM output with ambiguous terms must be rejected.
        """
        # Mock environment variable
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")

        # Mock OpenAI response with FORBIDDEN terminology
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

            # Should raise ValueError due to forbidden term "prazo de abertura"
            with pytest.raises(ValueError) as exc_info:
                gerar_resumo(mock_licitacoes)

            assert "ambiguous deadline terminology" in str(exc_info.value).lower()
            assert "prazo de abertura" in str(exc_info.value)

    def test_forbidden_abertura_em_triggers_assertion(self, mock_licitacoes, monkeypatch):
        """
        CRITICAL: "abertura em [data]" is forbidden and must be rejected.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = ResumoLicitacoes(
            resumo_executivo="Licitação importante com abertura em 5 de fevereiro.",
            total_oportunidades=1,
            valor_total=50000.0,
            destaques=["Test"],
            alerta_urgencia=None,
        )

        with patch("llm.OpenAI") as mock_openai:
            mock_openai.return_value.beta.chat.completions.parse.return_value = mock_response

            with pytest.raises(ValueError) as exc_info:
                gerar_resumo(mock_licitacoes)

            assert "abertura em" in str(exc_info.value)

    def test_clear_terminology_passes_validation(self, mock_licitacoes, monkeypatch):
        """
        LLM output with CLEAR terminology should pass validation.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = ResumoLicitacoes(
            resumo_executivo=(
                "Há 2 oportunidades em uniformes no Sul totalizando R$ 111.000. "
                "Maior licitação: R$ 75.000 da Prefeitura de Porto Alegre, "
                "recebe propostas até 15/02/2026 (você tem 8 dias para enviar)."
            ),
            total_oportunidades=2,
            valor_total=111000.0,
            destaques=["Porto Alegre: R$ 75.000", "Florianópolis: R$ 36.000"],
            alerta_urgencia=None,
        )

        with patch("llm.OpenAI") as mock_openai:
            mock_openai.return_value.beta.chat.completions.parse.return_value = mock_response

            # Should NOT raise exception - clear terminology is acceptable
            resumo = gerar_resumo(mock_licitacoes)

            assert resumo.total_oportunidades == 2
            assert "prazo de abertura" not in resumo.resumo_executivo.lower()
            assert "abertura em" not in resumo.resumo_executivo.lower()

    def test_fallback_uses_clear_terminology(self, mock_licitacoes):
        """
        Fallback function must also use clear deadline terminology.
        """
        resumo = gerar_resumo_fallback(mock_licitacoes, sector_name="uniformes")

        # Validate no forbidden terms
        assert "prazo de abertura" not in resumo.resumo_executivo.lower()
        assert "abertura em" not in resumo.resumo_executivo.lower()

        # Should contain clear information
        assert resumo.total_oportunidades == 2
        assert resumo.valor_total == 111000.0

    def test_urgent_alert_uses_clear_terminology(self):
        """
        Urgency alerts must use "encerra em X dias" not "prazo em X dias".
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
            # Should say "encerra em X dia(s)" not "prazo em X dias"
            assert "encerra em" in resumo.alerta_urgencia.lower()
            assert "prazo em menos de" not in resumo.alerta_urgencia.lower()

    def test_system_prompt_includes_forbidden_terms_list(self):
        """
        System prompt must explicitly forbid ambiguous terminology.
        """
        # Read the actual system prompt from llm.py
        import llm
        import inspect

        source = inspect.getsource(llm.gerar_resumo)

        # Validate that forbidden terms are explicitly listed in prompt
        assert "prazo de abertura" in source
        assert "abertura em" in source
        assert "NUNCA use" in source or "NEVER use" in source.lower()

    def test_system_prompt_includes_correct_examples(self):
        """
        System prompt must include examples of CORRECT terminology.
        """
        import llm
        import inspect

        source = inspect.getsource(llm.gerar_resumo)

        # Validate correct terminology examples are present
        assert "recebe propostas" in source.lower()
        assert "prazo final" in source.lower()
        assert "você tem" in source.lower()


class TestAssertionLogging:
    """Test that assertion failures are logged for monitoring."""

    def test_assertion_failure_is_logged(self, mock_licitacoes, monkeypatch):
        """
        When assertion fails, error should be logged for monitoring.
        """
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = ResumoLicitacoes(
            resumo_executivo="Prazo de abertura em 5 de fevereiro",
            total_oportunidades=1,
            valor_total=50000.0,
            destaques=["Test"],
            alerta_urgencia=None,
        )

        with patch("llm.OpenAI") as mock_openai, \
             patch("logging.warning") as mock_warning:
            mock_openai.return_value.beta.chat.completions.parse.return_value = mock_response

            with pytest.raises(ValueError):
                gerar_resumo(mock_licitacoes)

            # Should have logged the issue
            mock_warning.assert_called_once()
            assert "ambiguous term" in str(mock_warning.call_args).lower()


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
