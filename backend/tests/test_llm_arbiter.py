"""
Tests for LLM Arbiter (STORY-179 AC7.1 + STORY-251 dynamic prompts + D-02 structured output).

Test coverage:
- Mock OpenAI API responses
- Cache hit/miss scenarios
- Fallback on API error
- Prompt construction (sector vs custom terms)
- D-02: LLMClassification schema validation
- D-02: Structured JSON parsing with fallback
- D-02: Confidence scoring (keyword=95, LLM=varies, zero_match<=70)
- D-02: Evidence substring validation
- D-02: Feature flag toggle (structured vs binary)
- D-02: Cost monitoring
"""

import hashlib
import json
import os
from unittest.mock import Mock, patch, PropertyMock

import pytest

from llm_arbiter import (
    LLMClassification,
    _build_conservative_prompt,
    _parse_structured_response,
    classify_contract_primary_match,
    clear_cache,
    get_cache_stats,
    get_parse_stats,
    get_search_cost_stats,
)


@pytest.fixture(autouse=True)
def setup_env():
    """Set up environment variables for testing."""
    os.environ["LLM_ARBITER_ENABLED"] = "true"
    os.environ["LLM_ARBITER_MODEL"] = "gpt-4.1-nano"
    os.environ["LLM_ARBITER_MAX_TOKENS"] = "1"
    os.environ["LLM_ARBITER_TEMPERATURE"] = "0"
    os.environ["OPENAI_API_KEY"] = "test-key-12345"
    clear_cache()
    yield
    clear_cache()


def _create_mock_response(content: str, prompt_tokens: int = 100, completion_tokens: int = 1) -> Mock:
    """Helper to create a properly structured mock OpenAI response."""
    mock_message = Mock()
    mock_message.content = content

    mock_choice = Mock()
    mock_choice.message = mock_message

    mock_usage = Mock()
    mock_usage.prompt_tokens = prompt_tokens
    mock_usage.completion_tokens = completion_tokens

    mock_response = Mock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    return mock_response


def _structured_json(classe="SIM", confianca=85, evidencias=None, motivo_exclusao=None, precisa_mais_dados=False):
    """Helper to build a structured JSON response string."""
    return json.dumps({
        "classe": classe,
        "confianca": confianca,
        "evidencias": evidencias or [],
        "motivo_exclusao": motivo_exclusao,
        "precisa_mais_dados": precisa_mais_dados,
    })


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("llm_arbiter._get_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        yield mock_client


# =============================================================================
# D-02 AC1: LLMClassification Schema Validation
# =============================================================================

class TestLLMClassificationSchema:
    """D-02 AC10: Unit tests for LLMClassification Pydantic model."""

    def test_valid_json_all_fields(self):
        """AC10.1: LLMClassification validates correct JSON with all fields."""
        c = LLMClassification(
            classe="SIM",
            confianca=85,
            evidencias=["uniformes escolares", "rede municipal"],
            motivo_exclusao=None,
            precisa_mais_dados=False,
        )
        assert c.classe == "SIM"
        assert c.confianca == 85
        assert len(c.evidencias) == 2
        assert c.motivo_exclusao is None

    def test_valid_nao_with_rejection(self):
        """NAO classification with motivo_exclusao."""
        c = LLMClassification(
            classe="NAO",
            confianca=15,
            evidencias=[],
            motivo_exclusao="Contrato é sobre obras, não vestuário",
        )
        assert c.classe == "NAO"
        assert c.motivo_exclusao is not None

    def test_rejects_confidence_below_zero(self):
        """AC10.2: Confidence < 0 rejected."""
        with pytest.raises(Exception):
            LLMClassification(classe="SIM", confianca=-1)

    def test_rejects_confidence_above_100(self):
        """AC10.2: Confidence > 100 rejected."""
        with pytest.raises(Exception):
            LLMClassification(classe="SIM", confianca=101)

    def test_boundary_confidence_0(self):
        """Confidence 0 is valid."""
        c = LLMClassification(classe="NAO", confianca=0)
        assert c.confianca == 0

    def test_boundary_confidence_100(self):
        """Confidence 100 is valid."""
        c = LLMClassification(classe="SIM", confianca=100)
        assert c.confianca == 100

    def test_rejects_invalid_classe(self):
        """Only SIM/NAO allowed."""
        with pytest.raises(Exception):
            LLMClassification(classe="MAYBE", confianca=50)

    def test_model_validate_json(self):
        """Validate from raw JSON string."""
        raw = '{"classe": "SIM", "confianca": 90, "evidencias": ["test"], "motivo_exclusao": null, "precisa_mais_dados": false}'
        c = LLMClassification.model_validate_json(raw)
        assert c.classe == "SIM"
        assert c.confianca == 90


# =============================================================================
# D-02 AC3: Parser with Robust Fallback
# =============================================================================

class TestStructuredParser:
    """D-02 AC10.3: Test parser fallback when LLM returns non-JSON."""

    def test_valid_json_parsed(self):
        """Valid JSON response parsed correctly."""
        raw = _structured_json("SIM", 85, ["uniformes escolares"])
        result = _parse_structured_response(raw, "Aquisição de uniformes escolares para rede municipal")
        assert result.classe == "SIM"
        assert result.confianca == 85
        assert "uniformes escolares" in result.evidencias

    def test_fallback_on_plain_text_sim(self):
        """AC10.3: Plain text 'SIM' falls back to SIM with confidence=60."""
        result = _parse_structured_response("SIM", "objeto teste")
        assert result.classe == "SIM"
        assert result.confianca == 60

    def test_fallback_on_plain_text_nao(self):
        """AC10.3: Plain text 'NAO' falls back to NAO with confidence=40."""
        result = _parse_structured_response("NAO", "objeto teste")
        assert result.classe == "NAO"
        assert result.confianca == 40

    def test_fallback_on_garbage(self):
        """Unrecognizable text falls back to NAO."""
        result = _parse_structured_response("???random garbage", "objeto teste")
        assert result.classe == "NAO"

    def test_fallback_on_malformed_json(self):
        """Malformed JSON falls back to text detection."""
        result = _parse_structured_response('{"classe": "SIM", broken...', "objeto teste")
        assert result.classe == "SIM"  # Found "SIM" in raw text

    def test_evidence_substring_validation(self):
        """AC10.4: Evidence not a substring of objeto is discarded."""
        raw = _structured_json("SIM", 80, ["uniformes escolares", "HALLUCINATED EVIDENCE"])
        result = _parse_structured_response(raw, "Aquisição de uniformes escolares para rede")
        assert "uniformes escolares" in result.evidencias
        assert "HALLUCINATED EVIDENCE" not in result.evidencias

    def test_evidence_case_insensitive_validation(self):
        """Evidence matching is case-insensitive."""
        raw = _structured_json("SIM", 80, ["Uniformes Escolares"])
        result = _parse_structured_response(raw, "aquisição de uniformes escolares para rede")
        assert len(result.evidencias) == 1

    def test_parse_stats_tracking(self):
        """Parse success rate tracked per search."""
        search_id = "test-parse-123"
        raw_json = _structured_json("SIM", 90)
        _parse_structured_response(raw_json, "objeto", search_id)
        _parse_structured_response("NAO", "objeto", search_id)  # fallback

        stats = get_parse_stats(search_id)
        assert stats["attempts"] == 2
        assert stats["json_success"] == 1
        assert stats["fallback"] == 1


# =============================================================================
# D-02 AC4/AC8: Structured vs Binary Mode
# =============================================================================

class TestStructuredOutput:
    """D-02: Test structured output mode with feature flag."""

    def test_structured_mode_returns_dict_with_confidence(self, mock_openai_client):
        """When structured enabled, returns dict with confidence."""
        json_resp = _structured_json("SIM", 85, ["uniformes para agentes"])
        mock_openai_client.chat.completions.create.return_value = _create_mock_response(
            json_resp, prompt_tokens=200, completion_tokens=30
        )

        with patch("config.get_feature_flag", return_value=True):
            result = classify_contract_primary_match(
                objeto="Aquisição de uniformes para agentes de trânsito",
                valor=500_000,
                setor_name="Vestuário e Uniformes",
            )

        assert isinstance(result, dict)
        assert result["is_primary"] is True
        assert result["confidence"] == 85
        assert isinstance(result["evidence"], list)

    def test_structured_mode_nao_with_rejection_reason(self, mock_openai_client):
        """NAO response includes rejection_reason."""
        json_resp = _structured_json("NAO", 20, [], "Contrato é sobre obras de infraestrutura")
        mock_openai_client.chat.completions.create.return_value = _create_mock_response(json_resp)

        with patch("config.get_feature_flag", return_value=True):
            result = classify_contract_primary_match(
                objeto="Melhorias urbanas diversas",
                valor=47_600_000,
                setor_name="Vestuário e Uniformes",
            )

        assert result["is_primary"] is False
        assert result["confidence"] == 20
        assert "obras" in result["rejection_reason"].lower()

    def test_feature_flag_false_uses_binary_mode(self, mock_openai_client):
        """AC10.7: Feature flag false uses old behavior (max_tokens=1)."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        with patch("config.get_feature_flag", return_value=False):
            result = classify_contract_primary_match(
                objeto="Uniformes escolares",
                valor=1_000_000,
                setor_name="Vestuário",
            )

        assert result["is_primary"] is True
        assert result["confidence"] == 100  # Binary: SIM=100
        assert result["evidence"] == []

        # Verify max_tokens=1 was used (binary)
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs["max_tokens"] == 1
        assert "response_format" not in call_args.kwargs

    def test_structured_mode_uses_json_format(self, mock_openai_client):
        """AC2: Structured mode uses response_format=json_object."""
        json_resp = _structured_json("SIM", 90)
        mock_openai_client.chat.completions.create.return_value = _create_mock_response(json_resp)

        with patch("config.get_feature_flag", return_value=True):
            classify_contract_primary_match(
                objeto="Teste", valor=1_000_000, setor_name="Vestuário",
            )

        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs["max_tokens"] == 150  # Structured max
        assert call_args.kwargs["response_format"] == {"type": "json_object"}

    def test_error_returns_reject_dict(self, mock_openai_client):
        """API error returns reject dict with confidence=0."""
        mock_openai_client.chat.completions.create.side_effect = Exception("timeout")

        with patch("config.get_feature_flag", return_value=True):
            result = classify_contract_primary_match(
                objeto="Teste", valor=1_000_000, setor_name="Vestuário",
            )

        assert result["is_primary"] is False
        assert result["confidence"] == 0
        assert result["rejection_reason"] == "LLM unavailable"


# =============================================================================
# D-02 AC9: Cost Monitoring
# =============================================================================

class TestCostMonitoring:
    """D-02 AC9: Test token/cost tracking."""

    def test_cost_stats_tracked_per_search(self, mock_openai_client):
        """Token usage accumulated per search_id."""
        json_resp = _structured_json("SIM", 90)
        mock_openai_client.chat.completions.create.return_value = _create_mock_response(
            json_resp, prompt_tokens=150, completion_tokens=25
        )

        search_id = "cost-test-123"
        with patch("config.get_feature_flag", return_value=True):
            # Two different inputs = two cache misses = two LLM calls
            classify_contract_primary_match(
                objeto="Objeto A para uniformes", valor=100_000, setor_name="Vestuário",
                search_id=search_id,
            )
            classify_contract_primary_match(
                objeto="Objeto B para calças", valor=200_000, setor_name="Vestuário",
                search_id=search_id,
            )

        stats = get_search_cost_stats(search_id)
        assert stats["llm_tokens_input"] == 300  # 150 * 2
        assert stats["llm_tokens_output"] == 50  # 25 * 2
        assert stats["llm_calls"] == 2
        assert stats["llm_cost_estimated_brl"] > 0


# =============================================================================
# Existing tests updated for dict return
# =============================================================================

class TestLLMClassificationLegacy:
    """Test LLM classification logic (updated for dict return)."""

    def test_false_positive_detection_sector_mode(self, mock_openai_client):
        """STORY-179 AC3.8 Test 1: R$ 47.6M melhorias urbanas + vestuário = NAO."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("NAO")

        with patch("config.get_feature_flag", return_value=False):
            result = classify_contract_primary_match(
                objeto="MELHORIAS URBANAS incluindo uniformes para agentes de trânsito",
                valor=47_600_000,
                setor_name="Vestuário e Uniformes",
            )

        assert result["is_primary"] is False
        assert mock_openai_client.chat.completions.create.called

    def test_legitimate_contract_sector_mode(self, mock_openai_client):
        """STORY-179 AC3.8 Test 2: R$ 3M uniformes escolares = SIM."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        with patch("config.get_feature_flag", return_value=False):
            result = classify_contract_primary_match(
                objeto="Uniformes escolares diversos para rede municipal de ensino",
                valor=3_000_000,
                setor_name="Vestuário e Uniformes",
            )

        assert result["is_primary"] is True

    def test_custom_terms_mode_relevant(self, mock_openai_client):
        """Custom terms: pavimentação = SIM."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        with patch("config.get_feature_flag", return_value=False):
            result = classify_contract_primary_match(
                objeto="Execução de pavimentação e drenagem na Rodovia X",
                valor=5_000_000,
                termos_busca=["pavimentação", "drenagem", "terraplenagem"],
            )

        assert result["is_primary"] is True

    def test_custom_terms_mode_irrelevant(self, mock_openai_client):
        """Custom terms: auditoria = NAO."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("NAO")

        with patch("config.get_feature_flag", return_value=False):
            result = classify_contract_primary_match(
                objeto="Auditoria externa de processos administrativos",
                valor=10_000_000,
                termos_busca=["pavimentação", "drenagem"],
            )

        assert result["is_primary"] is False


class TestCaching:
    """Test cache functionality."""

    def test_cache_miss_then_hit(self, mock_openai_client):
        """Test cache stores and retrieves decisions."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        with patch("config.get_feature_flag", return_value=False):
            result1 = classify_contract_primary_match(
                objeto="Uniformes escolares", valor=1_000_000, setor_name="Vestuário",
            )

        assert result1["is_primary"] is True
        assert mock_openai_client.chat.completions.create.call_count == 1

        with patch("config.get_feature_flag", return_value=False):
            result2 = classify_contract_primary_match(
                objeto="Uniformes escolares", valor=1_000_000, setor_name="Vestuário",
            )

        assert result2["is_primary"] is True
        assert mock_openai_client.chat.completions.create.call_count == 1

    def test_cache_stats(self, mock_openai_client):
        """Test cache statistics."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        stats_before = get_cache_stats()
        assert stats_before["cache_size"] == 0

        with patch("config.get_feature_flag", return_value=False):
            classify_contract_primary_match(objeto="A", valor=1_000_000, setor_name="A")
            classify_contract_primary_match(objeto="B", valor=2_000_000, setor_name="B")
            classify_contract_primary_match(objeto="C", valor=3_000_000, setor_name="C")

        stats_after = get_cache_stats()
        assert stats_after["cache_size"] == 3

    def test_clear_cache(self, mock_openai_client):
        """Test cache can be cleared."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        with patch("config.get_feature_flag", return_value=False):
            classify_contract_primary_match(objeto="Test", valor=1_000_000, setor_name="Test")
        assert get_cache_stats()["cache_size"] == 1

        clear_cache()
        assert get_cache_stats()["cache_size"] == 0


class TestFallback:
    """Test fallback behavior on errors."""

    def test_fallback_on_openai_error(self, mock_openai_client):
        """AC3.6: If LLM fails, default to REJECT (conservative)."""
        mock_openai_client.chat.completions.create.side_effect = Exception("API timeout")

        with patch("config.get_feature_flag", return_value=False):
            result = classify_contract_primary_match(
                objeto="Objeto qualquer", valor=10_000_000, setor_name="Vestuário",
            )

        assert result["is_primary"] is False

    def test_feature_flag_disabled(self, mock_openai_client):
        """Test behavior when LLM_ARBITER_ENABLED=false."""
        with patch("llm_arbiter.LLM_ENABLED", False):
            result = classify_contract_primary_match(
                objeto="Objeto qualquer", valor=10_000_000, setor_name="Vestuário",
            )

            assert result["is_primary"] is True
            assert not mock_openai_client.chat.completions.create.called

    def test_missing_inputs_defaults_to_accept(self, mock_openai_client):
        """Test behavior when neither setor_name nor termos_busca provided."""
        result = classify_contract_primary_match(objeto="Objeto qualquer", valor=10_000_000)

        assert result["is_primary"] is True
        assert not mock_openai_client.chat.completions.create.called


class TestPromptConstruction:
    """Test prompt generation for different modes."""

    def test_sector_mode_prompt_format(self, mock_openai_client):
        """Test sector mode prompt follows AC3.2 format."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        with patch("config.get_feature_flag", return_value=False):
            classify_contract_primary_match(
                objeto="Teste de prompt", valor=1_000_000,
                setor_name="Hardware e Equipamentos de TI",
            )

        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert "classificador" in messages[0]["content"].lower()

        user_msg = messages[1]["content"]
        assert "Setor: Hardware e Equipamentos de TI" in user_msg
        assert "Valor: R$" in user_msg
        assert "PRIMARIAMENTE" in user_msg
        assert "SIM ou NAO" in user_msg

    def test_custom_terms_mode_prompt_format(self, mock_openai_client):
        """Test custom terms mode prompt follows AC3.3 format."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        with patch("config.get_feature_flag", return_value=False):
            classify_contract_primary_match(
                objeto="Teste de prompt", valor=1_000_000,
                termos_busca=["software", "sistema", "aplicativo"],
            )

        call_args = mock_openai_client.chat.completions.create.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]
        assert "Termos buscados: software, sistema, aplicativo" in user_msg
        assert "OBJETO PRINCIPAL" in user_msg
        assert "SIM ou NAO" in user_msg

    def test_objeto_truncation(self, mock_openai_client):
        """AC3.7: Test objeto is truncated to 500 chars."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        long_objeto = "INICIO_" + "A" * 490 + "MARCA" + "B" * 490 + "_FIM"
        with patch("config.get_feature_flag", return_value=False):
            classify_contract_primary_match(
                objeto=long_objeto, valor=1_000_000, setor_name="Vestuário",
            )

        call_args = mock_openai_client.chat.completions.create.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]
        assert "INICIO_" in user_msg
        assert "_FIM" not in user_msg


class TestLLMParameters:
    """Test LLM API call parameters."""

    def test_llm_parameters_binary(self, mock_openai_client):
        """AC3.4: Test LLM is called with correct parameters in binary mode."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        with patch("config.get_feature_flag", return_value=False):
            classify_contract_primary_match(
                objeto="Teste", valor=1_000_000, setor_name="Vestuário",
            )

        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4.1-nano"
        assert call_args.kwargs["max_tokens"] == 1
        assert call_args.kwargs["temperature"] == 0


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
            setor_id=setor_id, setor_name=config.name,
            objeto_truncated="Teste objeto", valor=1_000_000,
        )

        assert config.description in prompt
        expected_keywords = sorted(config.keywords)[:3]
        for kw in expected_keywords:
            assert kw in prompt, f"Expected keyword '{kw}' not found in prompt for {setor_id}"

        expected_exclusions = sorted(config.exclusions)[:3]
        for exc in expected_exclusions:
            assert exc in prompt, f"Expected exclusion '{exc}' not found in prompt for {setor_id}"

        assert "SETOR:" in prompt
        assert "DESCRIÇÃO DO SETOR:" in prompt
        assert "SIM:" in prompt
        assert "PRIMARIAMENTE" in prompt

    def test_fallback_for_unknown_sector_id(self):
        """AC12: When setor_id is not found, falls back to standard prompt."""
        prompt = _build_conservative_prompt(
            setor_id="inexistente_xyz", setor_name="Setor Fantasma",
            objeto_truncated="Objeto teste", valor=500_000,
        )
        assert "Setor Fantasma" in prompt
        assert "EXEMPLOS DE CLASSIFICAÇÃO" not in prompt
        assert "DESCRIÇÃO DO SETOR" not in prompt
        assert "PRIMARIAMENTE" in prompt

    def test_fallback_for_none_sector_id(self):
        """AC7: When setor_id is None, falls back to standard prompt."""
        prompt = _build_conservative_prompt(
            setor_id=None, setor_name="Vestuário e Uniformes",
            objeto_truncated="Objeto teste", valor=500_000,
        )
        assert "EXEMPLOS DE CLASSIFICAÇÃO" not in prompt
        assert "DESCRIÇÃO DO SETOR" not in prompt


class TestConservativePromptIntegration:
    """STORY-251: End-to-end integration tests."""

    def test_conservative_with_setor_id_uses_dynamic_prompt(self, mock_openai_client):
        """AC4: When setor_id + conservative mode, prompt uses sector description."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("SIM")

        with patch("config.get_feature_flag", return_value=False):
            classify_contract_primary_match(
                objeto="Aquisição de computadores para escola", valor=500_000,
                setor_name="Hardware e Equipamentos de TI", setor_id="informatica",
                prompt_level="conservative",
            )

        call_args = mock_openai_client.chat.completions.create.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]
        assert "Computadores, servidores, periféricos" in user_msg

    def test_backward_compatible_no_setor_id(self, mock_openai_client):
        """AC3: Existing callers without setor_id still work."""
        mock_openai_client.chat.completions.create.return_value = _create_mock_response("NAO")

        with patch("config.get_feature_flag", return_value=False):
            result = classify_contract_primary_match(
                objeto="MELHORIAS URBANAS", valor=47_600_000,
                setor_name="Vestuário e Uniformes",
            )

        assert result["is_primary"] is False
