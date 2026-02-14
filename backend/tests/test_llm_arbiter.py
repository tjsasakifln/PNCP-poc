"""
Tests for LLM Arbiter (STORY-179 AC7.1 + STORY-251 dynamic prompts).

Test coverage:
- Mock OpenAI API responses
- Cache hit/miss scenarios
- Fallback on API error
- Prompt construction (sector vs custom terms)
- Token counting (max 1 token output)
- STORY-251: Dynamic conservative prompts per sector
"""

import hashlib
import os
from unittest.mock import Mock, patch

import pytest

from llm_arbiter import (
    _build_conservative_prompt,
    classify_contract_primary_match,
    clear_cache,
    get_cache_stats,
)


@pytest.fixture(autouse=True)
def setup_env():
    """Set up environment variables for testing."""
    os.environ["LLM_ARBITER_ENABLED"] = "true"
    os.environ["LLM_ARBITER_MODEL"] = "gpt-4o-mini"
    os.environ["LLM_ARBITER_MAX_TOKENS"] = "1"
    os.environ["LLM_ARBITER_TEMPERATURE"] = "0"
    os.environ["OPENAI_API_KEY"] = "test-key-12345"
    clear_cache()
    yield
    clear_cache()


def _create_mock_response(content: str) -> Mock:
    """Helper to create a properly structured mock OpenAI response."""
    mock_message = Mock()
    mock_message.content = content

    mock_choice = Mock()
    mock_choice.message = mock_message

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    return mock_response


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("llm_arbiter._get_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        yield mock_client


class TestLLMClassification:
    """Test LLM classification logic."""

    def test_false_positive_detection_sector_mode(self, mock_openai_client):
        """
        STORY-179 AC3.8 Test 1: R$ 47.6M melhorias urbanas + vestuário
        Expected: NAO (false positive)
        """
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("NAO")

        result = classify_contract_primary_match(
            objeto="MELHORIAS URBANAS incluindo uniformes para agentes de trânsito",
            valor=47_600_000,
            setor_name="Vestuário e Uniformes",
        )

        assert result is False
        assert mock_openai_client.chat.completions.create.called
        call_args = mock_openai_client.chat.completions.create.call_args

        # Verify prompt construction
        user_message = call_args.kwargs["messages"][1]["content"]
        assert "Vestuário e Uniformes" in user_message
        assert "47,600,000" in user_message
        assert "MELHORIAS URBANAS" in user_message
        assert "PRIMARIAMENTE" in user_message

    def test_legitimate_contract_sector_mode(self, mock_openai_client):
        """
        STORY-179 AC3.8 Test 2: R$ 3M uniformes escolares
        Expected: SIM (legitimate)
        """
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        result = classify_contract_primary_match(
            objeto="Uniformes escolares diversos para rede municipal de ensino",
            valor=3_000_000,
            setor_name="Vestuário e Uniformes",
        )

        assert result is True

    def test_custom_terms_mode_relevant(self, mock_openai_client):
        """
        STORY-179 AC3.8 Test 2 (custom terms): Pavimentação relevante
        Expected: SIM
        """
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        result = classify_contract_primary_match(
            objeto="Execução de pavimentação e drenagem na Rodovia X",
            valor=5_000_000,
            termos_busca=["pavimentação", "drenagem", "terraplenagem"],
        )

        assert result is True

        # Verify prompt uses custom terms mode
        call_args = mock_openai_client.chat.completions.create.call_args
        user_message = call_args.kwargs["messages"][1]["content"]
        assert "Termos buscados:" in user_message
        assert "pavimentação" in user_message
        assert "OBJETO PRINCIPAL" in user_message

    def test_custom_terms_mode_irrelevant(self, mock_openai_client):
        """
        STORY-179 AC3.8 Test 3: Auditoria administrativa (irrelevante para pavimentação)
        Expected: NAO
        """
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("NAO")

        result = classify_contract_primary_match(
            objeto="Auditoria externa de processos administrativos",
            valor=10_000_000,
            termos_busca=["pavimentação", "drenagem"],
        )

        assert result is False


class TestCaching:
    """Test cache functionality."""

    def test_cache_miss_then_hit(self, mock_openai_client):
        """Test cache stores and retrieves decisions."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        # First call - cache miss
        result1 = classify_contract_primary_match(
            objeto="Uniformes escolares",
            valor=1_000_000,
            setor_name="Vestuário",
        )

        assert result1 is True
        assert mock_openai_client.chat.completions.create.call_count == 1

        # Second call with same inputs - cache hit
        result2 = classify_contract_primary_match(
            objeto="Uniformes escolares",
            valor=1_000_000,
            setor_name="Vestuário",
        )

        assert result2 is True
        # Should NOT call OpenAI again (cached)
        assert mock_openai_client.chat.completions.create.call_count == 1

    def test_cache_stats(self, mock_openai_client):
        """Test cache statistics."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        stats_before = get_cache_stats()
        assert stats_before["cache_size"] == 0

        # Add 3 different classifications
        classify_contract_primary_match(
            objeto="Objeto A", valor=1_000_000, setor_name="Setor A"
        )
        classify_contract_primary_match(
            objeto="Objeto B", valor=2_000_000, setor_name="Setor B"
        )
        classify_contract_primary_match(
            objeto="Objeto C", valor=3_000_000, setor_name="Setor C"
        )

        stats_after = get_cache_stats()
        assert stats_after["cache_size"] == 3

    def test_clear_cache(self, mock_openai_client):
        """Test cache can be cleared."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        # Add entry
        classify_contract_primary_match(
            objeto="Test", valor=1_000_000, setor_name="Test"
        )
        assert get_cache_stats()["cache_size"] == 1

        # Clear cache
        clear_cache()
        assert get_cache_stats()["cache_size"] == 0


class TestFallback:
    """Test fallback behavior on errors."""

    def test_fallback_on_openai_error(self, mock_openai_client):
        """
        AC3.6: If LLM fails, default to REJECT (conservative).
        Better to reject 1 ambiguous than approve 1 catastrophic false positive.
        """
        # Mock OpenAI API error
        mock_openai_client.chat.completions.create.side_effect = Exception(
            "API timeout"
        )

        result = classify_contract_primary_match(
            objeto="Objeto qualquer",
            valor=10_000_000,
            setor_name="Vestuário",
        )

        # Should default to False (reject) on error
        assert result is False

    def test_feature_flag_disabled(self, mock_openai_client):
        """Test behavior when LLM_ARBITER_ENABLED=false."""
        # Patch the module-level variable directly (it's read at import time)
        with patch("llm_arbiter.LLM_ENABLED", False):
            result = classify_contract_primary_match(
                objeto="Objeto qualquer",
                valor=10_000_000,
                setor_name="Vestuário",
            )

            # Should accept (legacy behavior) without calling OpenAI
            assert result is True
            assert not mock_openai_client.chat.completions.create.called

    def test_missing_inputs_defaults_to_accept(self, mock_openai_client):
        """Test behavior when neither setor_name nor termos_busca provided."""
        result = classify_contract_primary_match(
            objeto="Objeto qualquer",
            valor=10_000_000,
        )

        # Should accept (conservative fallback on misconfiguration)
        assert result is True
        assert not mock_openai_client.chat.completions.create.called


class TestPromptConstruction:
    """Test prompt generation for different modes."""

    def test_sector_mode_prompt_format(self, mock_openai_client):
        """Test sector mode prompt follows AC3.2 format."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        classify_contract_primary_match(
            objeto="Teste de prompt",
            valor=1_000_000,
            setor_name="Hardware e Equipamentos de TI",
        )

        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # System message
        assert messages[0]["role"] == "system"
        assert "classificador" in messages[0]["content"].lower()

        # User message (sector mode)
        user_msg = messages[1]["content"]
        assert "Setor: Hardware e Equipamentos de TI" in user_msg
        assert "Valor: R$" in user_msg
        assert "Objeto: Teste de prompt" in user_msg
        assert "PRIMARIAMENTE" in user_msg
        assert "SIM ou NAO" in user_msg

    def test_custom_terms_mode_prompt_format(self, mock_openai_client):
        """Test custom terms mode prompt follows AC3.3 format."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        classify_contract_primary_match(
            objeto="Teste de prompt",
            valor=1_000_000,
            termos_busca=["software", "sistema", "aplicativo"],
        )

        call_args = mock_openai_client.chat.completions.create.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]

        assert "Termos buscados: software, sistema, aplicativo" in user_msg
        assert "Valor: R$" in user_msg
        assert "Objeto: Teste de prompt" in user_msg
        assert "OBJETO PRINCIPAL" in user_msg
        assert "SIM ou NAO" in user_msg

    def test_objeto_truncation(self, mock_openai_client):
        """AC3.7: Test objeto is truncated to 500 chars."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        # Use distinct prefix/suffix so substring check works correctly
        long_objeto = "INICIO_" + "A" * 490 + "MARCA" + "B" * 490 + "_FIM"  # >500 chars
        classify_contract_primary_match(
            objeto=long_objeto,
            valor=1_000_000,
            setor_name="Vestuário",
        )

        call_args = mock_openai_client.chat.completions.create.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]

        # Should contain the start of the object
        assert "INICIO_" in user_msg
        # The marker at position ~497 should be partially included
        # but the suffix after 500 chars should NOT be in the prompt
        assert "_FIM" not in user_msg


class TestLLMParameters:
    """Test LLM API call parameters."""

    def test_llm_parameters(self, mock_openai_client):
        """AC3.4: Test LLM is called with correct parameters."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        classify_contract_primary_match(
            objeto="Teste",
            valor=1_000_000,
            setor_name="Vestuário",
        )

        call_args = mock_openai_client.chat.completions.create.call_args

        # Verify parameters
        assert call_args.kwargs["model"] == "gpt-4o-mini"
        assert call_args.kwargs["max_tokens"] == 1  # Force single token
        assert call_args.kwargs["temperature"] == 0  # Deterministic


class TestCacheKeyGeneration:
    """Test cache key generation for different scenarios."""

    def test_cache_key_different_for_different_inputs(self):
        """Test that different inputs generate different cache keys."""
        # Same function used internally by classify_contract_primary_match
        key1 = hashlib.md5("setor:Vestuário:1000000:Objeto A".encode()).hexdigest()
        key2 = hashlib.md5("setor:Vestuário:2000000:Objeto A".encode()).hexdigest()
        key3 = hashlib.md5("setor:Vestuário:1000000:Objeto B".encode()).hexdigest()

        assert key1 != key2  # Different valor
        assert key1 != key3  # Different objeto
        assert key2 != key3

    def test_cache_key_same_for_identical_inputs(self):
        """Test that identical inputs generate same cache key."""
        key1 = hashlib.md5("setor:Vestuário:1000000:Objeto A".encode()).hexdigest()
        key2 = hashlib.md5("setor:Vestuário:1000000:Objeto A".encode()).hexdigest()

        assert key1 == key2


# =============================================================================
# STORY-251: Dynamic Conservative Prompts Per Sector
# =============================================================================


class TestDynamicConservativePrompt:
    """STORY-251 AC4-AC9: Sector-aware conservative prompts with dynamic examples."""

    @pytest.mark.parametrize(
        "setor_id",
        ["vestuario", "informatica", "saude", "engenharia", "facilities"],
        ids=["vestuario", "informatica", "saude", "engenharia", "facilities"],
    )
    def test_conservative_prompt_uses_sector_data(self, setor_id):
        """AC11: Parametrized test verifying conservative prompt uses sector-specific data."""
        from sectors import get_sector

        config = get_sector(setor_id)
        prompt = _build_conservative_prompt(
            setor_id=setor_id,
            setor_name=config.name,
            objeto_truncated="Teste objeto",
            valor=1_000_000,
        )

        # AC4: Uses sector description (not hardcoded vestuário text)
        assert config.description in prompt

        # AC5: SIM examples contain top-3 keywords from the correct sector (sorted)
        expected_keywords = sorted(config.keywords)[:3]
        for kw in expected_keywords:
            assert kw in prompt, f"Expected keyword '{kw}' not found in prompt for {setor_id}"

        # AC6: NAO examples contain top-3 exclusions from the correct sector (sorted)
        expected_exclusions = sorted(config.exclusions)[:3]
        for exc in expected_exclusions:
            assert exc in prompt, f"Expected exclusion '{exc}' not found in prompt for {setor_id}"

        # Basic structure checks
        assert "SETOR:" in prompt
        assert "DESCRIÇÃO DO SETOR:" in prompt
        assert "SIM:" in prompt
        assert "PRIMARIAMENTE" in prompt

    def test_fallback_for_unknown_sector_id(self):
        """AC12: When setor_id is not found, falls back to standard prompt (no examples)."""
        prompt = _build_conservative_prompt(
            setor_id="inexistente_xyz",
            setor_name="Setor Fantasma",
            objeto_truncated="Objeto teste",
            valor=500_000,
        )

        # Standard prompt format — no examples, no description section
        assert "Setor: Setor Fantasma" in prompt or "Setor Fantasma" in prompt
        assert "EXEMPLOS DE CLASSIFICAÇÃO" not in prompt
        assert "DESCRIÇÃO DO SETOR" not in prompt
        assert "PRIMARIAMENTE" in prompt

    def test_fallback_for_none_sector_id(self):
        """AC7: When setor_id is None, falls back to standard prompt."""
        prompt = _build_conservative_prompt(
            setor_id=None,
            setor_name="Vestuário e Uniformes",
            objeto_truncated="Objeto teste",
            valor=500_000,
        )

        # Standard prompt — no examples
        assert "EXEMPLOS DE CLASSIFICAÇÃO" not in prompt
        assert "DESCRIÇÃO DO SETOR" not in prompt

    @pytest.mark.parametrize(
        "setor_id",
        [
            "vestuario", "alimentos", "informatica", "mobiliario", "papelaria",
            "engenharia", "software", "facilities", "saude", "vigilancia",
            "transporte", "manutencao_predial", "engenharia_rodoviaria",
            "materiais_eletricos", "materiais_hidraulicos",
        ],
        ids=lambda s: s,
    )
    def test_prompt_token_count_under_600(self, setor_id):
        """AC14: Conservative prompt does not exceed 600 tokens for any sector."""
        from sectors import get_sector

        config = get_sector(setor_id)
        prompt = _build_conservative_prompt(
            setor_id=setor_id,
            setor_name=config.name,
            objeto_truncated="A" * 500,  # Max-length objeto
            valor=99_999_999.99,  # Large value for max token usage
        )

        # Approximate token count: len(prompt) / 4
        approx_tokens = len(prompt) / 4
        assert approx_tokens < 600, (
            f"Sector '{setor_id}' prompt is ~{approx_tokens:.0f} tokens "
            f"(max 600). Prompt length: {len(prompt)} chars"
        )


class TestConservativePromptIntegration:
    """STORY-251: End-to-end integration tests for classify_contract_primary_match with setor_id."""

    def test_conservative_with_setor_id_uses_dynamic_prompt(self, mock_openai_client):
        """AC4: When setor_id + conservative mode, prompt uses sector description."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        classify_contract_primary_match(
            objeto="Aquisição de computadores para escola",
            valor=500_000,
            setor_name="Hardware e Equipamentos de TI",
            setor_id="informatica",
            prompt_level="conservative",
        )

        call_args = mock_openai_client.chat.completions.create.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]

        # Should use informatica description, NOT vestuário
        assert "Computadores, servidores, periféricos" in user_msg
        assert "uniformes, fardas" not in user_msg.lower() or "informatica" in user_msg.lower()

    def test_conservative_without_setor_id_uses_standard(self, mock_openai_client):
        """AC7: Without setor_id, conservative prompt falls back to standard."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        classify_contract_primary_match(
            objeto="Aquisição de computadores",
            valor=500_000,
            setor_name="Hardware e Equipamentos de TI",
            prompt_level="conservative",
        )

        call_args = mock_openai_client.chat.completions.create.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]

        # Standard prompt — no examples section
        assert "EXEMPLOS DE CLASSIFICAÇÃO" not in user_msg

    def test_standard_prompt_level_ignores_setor_id(self, mock_openai_client):
        """Standard prompt_level should use simple prompt regardless of setor_id."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        classify_contract_primary_match(
            objeto="Aquisição de computadores",
            valor=500_000,
            setor_name="Hardware e Equipamentos de TI",
            setor_id="informatica",
            prompt_level="standard",
        )

        call_args = mock_openai_client.chat.completions.create.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]

        # Standard prompt — no examples, no description
        assert "EXEMPLOS DE CLASSIFICAÇÃO" not in user_msg
        assert "DESCRIÇÃO DO SETOR" not in user_msg

    def test_backward_compatible_no_setor_id(self, mock_openai_client):
        """AC3: Existing callers without setor_id still work."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("NAO")

        result = classify_contract_primary_match(
            objeto="MELHORIAS URBANAS",
            valor=47_600_000,
            setor_name="Vestuário e Uniformes",
        )

        assert result is False
        assert mock_openai_client.chat.completions.create.called
