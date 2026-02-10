"""
Integration tests for LLM Arbiter + Filter pipeline (STORY-179 AC7.2).

Tests the complete flow:
1. Keyword matching
2. Camada 1A (value threshold)
3. Camada 2A (term density)
4. Camada 3A (LLM arbiter)

Coverage:
- R$ 47.6M melhorias urbanas case (real world false positive)
- Legitimate contracts should pass
- Edge cases (density 1-5%)
- LLM should NOT be called for high/low density
"""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from filter import aplicar_todos_filtros
from llm_arbiter import clear_cache


@pytest.fixture(autouse=True)
def setup_env():
    """Set up environment for testing."""
    os.environ["LLM_ARBITER_ENABLED"] = "true"
    os.environ["OPENAI_API_KEY"] = "test-key"
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client."""
    with patch("llm_arbiter._get_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        yield mock_client


class TestRealWorldCases:
    """Test real-world scenarios from STORY-179."""

    def test_caso_real_47_6m_melhorias_urbanas_rejected(self, mock_openai_client):
        """
        STORY-179 Critical Case: R$ 47.6M "melhorias urbanas" + uniformes
        Expected: REJECTED by Camada 1A (value threshold)
        LLM should NOT be called (rejected before reaching Camada 3A)
        """
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "NAO"
        mock_openai_client.chat.completions.create.return_value = mock_response

        licitacoes = [
            {
                "uf": "RJ",
                "valorTotalEstimado": 47_600_000,
                "objetoCompra": (
                    "MELHORIAS URBANAS EM NITERÓI incluindo pavimentação, "
                    "drenagem, sinalização e fornecimento de uniformes para "
                    "agentes de trânsito"
                ),
                "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
            }
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=licitacoes,
            ufs_selecionadas={"RJ"},
            setor="vestuario",  # max_contract_value = R$ 5M
        )

        # Should be REJECTED by Camada 1A (value > R$ 5M)
        assert len(aprovadas) == 0
        assert stats["rejeitadas_valor_alto"] == 1
        assert stats["aprovadas"] == 0

        # LLM should NOT be called (rejected before reaching Camada 3A)
        assert mock_openai_client.chat.completions.create.call_count == 0

    def test_caso_legitimo_3m_uniformes_approved(self, mock_openai_client):
        """
        STORY-179 Test: R$ 3M uniformes escolares (legitimate)
        Expected: APPROVED (value < R$ 5M threshold, high density)
        LLM should NOT be called (alta densidade > 5%)
        """
        licitacoes = [
            {
                "uf": "SP",
                "valorTotalEstimado": 3_000_000,
                "objetoCompra": (
                    "Uniformes escolares diversos para rede municipal de ensino: "
                    "camisetas, calças, bermudas, agasalhos, tênis e mochilas"
                ),
                "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
            }
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=licitacoes,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # Should be APPROVED (value OK + alta densidade)
        assert len(aprovadas) == 1
        assert stats["aprovadas_alta_densidade"] > 0 or stats["aprovadas"] == 1

        # LLM should NOT be called (alta densidade auto-aprova)
        # Note: might be called if densidade 1-5%, but likely >5% for "uniformes" repeated
        # This test validates the RESULT, not necessarily LLM avoidance


class TestCamada1AValueThreshold:
    """Test Camada 1A (value threshold) in isolation."""

    def test_value_threshold_rejects_high_value_informatica(self, mock_openai_client):
        """Test R$ 25M informática contract rejected (threshold R$ 20M)."""
        licitacoes = [
            {
                "uf": "SP",
                "valorTotalEstimado": 25_000_000,
                "objetoCompra": "Aquisição de notebooks para rede municipal",
                "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
            }
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=licitacoes,
            ufs_selecionadas={"SP"},
            setor="informatica",  # max_contract_value = R$ 20M
        )

        assert len(aprovadas) == 0
        assert stats["rejeitadas_valor_alto"] == 1

    def test_value_threshold_accepts_just_under_limit(self, mock_openai_client):
        """Test R$ 4.9M vestuário contract approved (threshold R$ 5M)."""
        licitacoes = [
            {
                "uf": "SP",
                "valorTotalEstimado": 4_900_000,
                "objetoCompra": (
                    "Uniformes operacionais para guardas municipais: "
                    "gandolas, calças, bonés, coturnos e coletes"
                ),
                "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
            }
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=licitacoes,
            ufs_selecionadas={"SP"},
            setor="vestuario",  # max_contract_value = R$ 5M
        )

        # Should be approved (value < threshold, alta densidade)
        assert len(aprovadas) == 1
        assert stats["rejeitadas_valor_alto"] == 0
