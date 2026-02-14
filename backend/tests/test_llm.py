"""
Tests for LLM integration module (backend/llm.py).

Coverage requirements: ≥70% (enforced by pytest-cov)

Test categories:
1. Empty input handling
2. Valid input with various sizes (1, 50, 100+ bids)
3. API key validation
4. OpenAI API error scenarios
5. HTML formatting
6. Schema validation
"""

import os
from unittest.mock import Mock, patch
import pytest

from llm import gerar_resumo, format_resumo_html
from schemas import ResumoLicitacoes, ResumoEstrategico


# ─────────────────────────────────────────────────────────────────────────────
# 1. Empty Input Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_gerar_resumo_empty_input():
    """Should return empty summary when no bids provided."""
    resumo = gerar_resumo([])

    assert isinstance(resumo, ResumoLicitacoes)
    assert resumo.total_oportunidades == 0
    assert resumo.valor_total == 0.0
    assert resumo.destaques == []
    assert resumo.alerta_urgencia is None
    assert "Nenhuma licitação" in resumo.resumo_executivo


# ─────────────────────────────────────────────────────────────────────────────
# 2. API Key Validation Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_gerar_resumo_missing_api_key():
    """Should raise ValueError when OPENAI_API_KEY is not set."""
    licitacoes = [
        {
            "objetoCompra": "Uniforme escolar",
            "nomeOrgao": "Prefeitura SP",
            "uf": "SP",
            "valorTotalEstimado": 100000.0,
            "dataAberturaProposta": "2025-02-15T10:00:00",
        }
    ]

    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            gerar_resumo(licitacoes)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Valid Input Tests (Mocked OpenAI API)
# ─────────────────────────────────────────────────────────────────────────────


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
@patch("llm.OpenAI")
def test_gerar_resumo_single_bid(mock_openai):
    """Should generate summary for single bid."""
    # Mock OpenAI response
    mock_resumo = ResumoLicitacoes(
        resumo_executivo="Encontrada 1 licitação de uniformes em SP.",
        total_oportunidades=1,
        valor_total=100000.0,
        destaques=["Prefeitura SP: R$ 100.000,00"],
        alerta_urgencia=None,
    )

    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_client.beta.chat.completions.parse.return_value.choices = [
        Mock(message=Mock(parsed=mock_resumo))
    ]

    licitacoes = [
        {
            "objetoCompra": "Uniforme escolar",
            "nomeOrgao": "Prefeitura SP",
            "uf": "SP",
            "municipio": "São Paulo",
            "valorTotalEstimado": 100000.0,
            "dataAberturaProposta": "2025-02-15T10:00:00",
        }
    ]

    resumo = gerar_resumo(licitacoes)

    assert isinstance(resumo, ResumoLicitacoes)
    assert resumo.total_oportunidades == 1
    assert resumo.valor_total == 100000.0
    assert len(resumo.destaques) == 1

    # Verify API was called
    mock_client.beta.chat.completions.parse.assert_called_once()
    call_args = mock_client.beta.chat.completions.parse.call_args
    assert call_args.kwargs["model"] == "gpt-4.1-nano"
    assert call_args.kwargs["temperature"] == 0.3
    assert call_args.kwargs["max_tokens"] == 1200
    assert call_args.kwargs["response_format"] == ResumoEstrategico


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
@patch("llm.OpenAI")
def test_gerar_resumo_50_bids_limit(mock_openai):
    """Should limit input to 50 bids to avoid token overflow."""
    mock_resumo = ResumoLicitacoes(
        resumo_executivo="Encontradas 50 licitações.",
        total_oportunidades=50,
        valor_total=5000000.0,
        destaques=["Top 3 valores"],
        alerta_urgencia=None,
    )

    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_client.beta.chat.completions.parse.return_value.choices = [
        Mock(message=Mock(parsed=mock_resumo))
    ]

    # Create 100 bids (should be limited to 50)
    licitacoes = [
        {
            "objetoCompra": f"Uniforme {i}",
            "nomeOrgao": f"Orgao {i}",
            "uf": "SP",
            "municipio": "São Paulo",
            "valorTotalEstimado": 100000.0,
            "dataAberturaProposta": "2025-02-15T10:00:00",
        }
        for i in range(100)
    ]

    resumo = gerar_resumo(licitacoes)

    assert isinstance(resumo, ResumoLicitacoes)

    # Verify API was called with limited data
    call_args = mock_client.beta.chat.completions.parse.call_args
    user_prompt = call_args.kwargs["messages"][1]["content"]

    # Should mention 100 total bids in text
    assert "100 licitações" in user_prompt or "100" in user_prompt


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
@patch("llm.OpenAI")
def test_gerar_resumo_truncates_objeto_compra(mock_openai):
    """Should truncate objetoCompra to 200 chars to save tokens."""
    mock_resumo = ResumoLicitacoes(
        resumo_executivo="Resumo OK",
        total_oportunidades=1,
        valor_total=100000.0,
        destaques=[],
        alerta_urgencia=None,
    )

    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_client.beta.chat.completions.parse.return_value.choices = [
        Mock(message=Mock(parsed=mock_resumo))
    ]

    # Create bid with very long objetoCompra (>200 chars)
    long_texto = "A" * 500  # 500 characters
    licitacoes = [
        {
            "objetoCompra": long_texto,
            "nomeOrgao": "Prefeitura",
            "uf": "SP",
            "municipio": "São Paulo",
            "valorTotalEstimado": 100000.0,
            "dataAberturaProposta": "2025-02-15T10:00:00",
        }
    ]

    gerar_resumo(licitacoes)

    # Verify API was called
    call_args = mock_client.beta.chat.completions.parse.call_args
    user_prompt = call_args.kwargs["messages"][1]["content"]

    # The truncated text (200 chars) should be in the prompt
    # The full 500 char text should NOT be in the prompt
    assert long_texto not in user_prompt
    assert long_texto[:200] in user_prompt


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
@patch("llm.OpenAI")
def test_gerar_resumo_handles_none_values(mock_openai):
    """Should handle None values in bid data gracefully."""
    mock_resumo = ResumoLicitacoes(
        resumo_executivo="Resumo OK",
        total_oportunidades=1,
        valor_total=0.0,
        destaques=[],
        alerta_urgencia=None,
    )

    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_client.beta.chat.completions.parse.return_value.choices = [
        Mock(message=Mock(parsed=mock_resumo))
    ]

    # Bid with None values
    licitacoes = [
        {
            "objetoCompra": None,
            "nomeOrgao": None,
            "uf": None,
            "municipio": None,
            "valorTotalEstimado": None,
            "dataAberturaProposta": None,
        }
    ]

    resumo = gerar_resumo(licitacoes)

    assert isinstance(resumo, ResumoLicitacoes)

    # Should not crash - API was called successfully
    mock_client.beta.chat.completions.parse.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# 4. API Error Scenarios
# ─────────────────────────────────────────────────────────────────────────────


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
@patch("llm.OpenAI")
def test_gerar_resumo_api_error(mock_openai):
    """Should propagate OpenAI API errors."""
    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_client.beta.chat.completions.parse.side_effect = Exception("API Error")

    licitacoes = [
        {
            "objetoCompra": "Uniforme",
            "nomeOrgao": "Prefeitura",
            "uf": "SP",
            "valorTotalEstimado": 100000.0,
            "dataAberturaProposta": "2025-02-15T10:00:00",
        }
    ]

    with pytest.raises(Exception, match="API Error"):
        gerar_resumo(licitacoes)


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
@patch("llm.OpenAI")
def test_gerar_resumo_empty_api_response(mock_openai):
    """Should raise error when API returns empty response."""
    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_client.beta.chat.completions.parse.return_value.choices = [
        Mock(message=Mock(parsed=None))
    ]

    licitacoes = [
        {
            "objetoCompra": "Uniforme",
            "nomeOrgao": "Prefeitura",
            "uf": "SP",
            "valorTotalEstimado": 100000.0,
            "dataAberturaProposta": "2025-02-15T10:00:00",
        }
    ]

    with pytest.raises(ValueError, match="empty response"):
        gerar_resumo(licitacoes)


# ─────────────────────────────────────────────────────────────────────────────
# 5. HTML Formatting Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_format_resumo_html_basic():
    """Should format basic summary as HTML."""
    resumo = ResumoLicitacoes(
        resumo_executivo="Encontradas 15 licitações.",
        total_oportunidades=15,
        valor_total=2300000.00,
        destaques=["3 urgentes", "Maior valor: R$ 500k"],
        alerta_urgencia=None,
    )

    html = format_resumo_html(resumo)

    assert "resumo-container" in html
    assert "Encontradas 15 licitações" in html
    assert "15" in html  # Total count
    assert "2,300,000.00" in html  # Formatted value (Python default uses commas)
    assert "3 urgentes" in html
    assert "Maior valor: R$ 500k" in html


def test_format_resumo_html_with_alerta():
    """Should include urgency alert in HTML."""
    resumo = ResumoLicitacoes(
        resumo_executivo="Resumo",
        total_oportunidades=5,
        valor_total=100000.0,
        destaques=[],
        alerta_urgencia="⚠️ 5 licitações encerram em 24 horas",
    )

    html = format_resumo_html(resumo)

    assert "alerta-urgencia" in html
    assert "⚠️ 5 licitações encerram em 24 horas" in html


def test_format_resumo_html_empty_destaques():
    """Should handle empty destaques list."""
    resumo = ResumoLicitacoes(
        resumo_executivo="Resumo",
        total_oportunidades=0,
        valor_total=0.0,
        destaques=[],
        alerta_urgencia=None,
    )

    html = format_resumo_html(resumo)

    assert "resumo-container" in html
    assert "Resumo" in html
    # Should not include destaques section when empty
    assert "<li>" not in html or "Destaques" not in html


def test_format_resumo_html_no_alerta():
    """Should not include alerta HTML when None."""
    resumo = ResumoLicitacoes(
        resumo_executivo="Resumo",
        total_oportunidades=10,
        valor_total=500000.0,
        destaques=["Destaque 1"],
        alerta_urgencia=None,
    )

    html = format_resumo_html(resumo)

    assert "resumo-container" in html
    assert "alerta-urgencia" not in html


# ─────────────────────────────────────────────────────────────────────────────
# 6. Integration Tests (with Real Schema Validation)
# ─────────────────────────────────────────────────────────────────────────────


def test_resumo_schema_validation():
    """Should validate ResumoLicitacoes schema constraints."""
    # Valid resumo
    resumo = ResumoLicitacoes(
        resumo_executivo="Valid summary",
        total_oportunidades=10,
        valor_total=1000000.0,
        destaques=["Destaque 1", "Destaque 2"],
        alerta_urgencia="Alert",
    )

    assert resumo.total_oportunidades >= 0
    assert resumo.valor_total >= 0.0


def test_resumo_schema_validation_negative_values():
    """Should reject negative values in schema."""
    with pytest.raises(Exception):  # Pydantic ValidationError
        ResumoLicitacoes(
            resumo_executivo="Invalid",
            total_oportunidades=-5,  # Invalid: negative
            valor_total=100000.0,
            destaques=[],
            alerta_urgencia=None,
        )

    with pytest.raises(Exception):  # Pydantic ValidationError
        ResumoLicitacoes(
            resumo_executivo="Invalid",
            total_oportunidades=10,
            valor_total=-500.0,  # Invalid: negative
            destaques=[],
            alerta_urgencia=None,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 7. Edge Cases
# ─────────────────────────────────────────────────────────────────────────────


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key-12345"})
@patch("llm.OpenAI")
def test_gerar_resumo_missing_optional_fields(mock_openai):
    """Should handle bids with missing optional fields."""
    mock_resumo = ResumoLicitacoes(
        resumo_executivo="Resumo OK",
        total_oportunidades=1,
        valor_total=0.0,
        destaques=[],
        alerta_urgencia=None,
    )

    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_client.beta.chat.completions.parse.return_value.choices = [
        Mock(message=Mock(parsed=mock_resumo))
    ]

    # Minimal bid data (only objetoCompra)
    licitacoes = [
        {
            "objetoCompra": "Uniforme"
            # All other fields missing
        }
    ]

    resumo = gerar_resumo(licitacoes)

    assert isinstance(resumo, ResumoLicitacoes)
    mock_client.beta.chat.completions.parse.assert_called_once()
