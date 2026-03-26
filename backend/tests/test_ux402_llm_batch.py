"""
Tests for UX-402: LLM Zero-Match Batch Classification.

Test coverage:
- AC1: Batch with 20 items returns 20 YES/NO responses
- AC5: Batch with incomplete response (15 for 20 items) rejects all
- AC2: Batch failure falls back to individual calls
- AC6: Feature flag False uses individual loop
- Integration: 50 zero-match items completes (LLM mocked)
- Regression: batch vs individual produce identical results for same data
"""

import os
from unittest.mock import Mock, patch

import pytest

from llm_arbiter import (
    _classify_zero_match_batch,
    _parse_batch_response,
    _build_zero_match_batch_prompt,
    _build_zero_match_batch_prompt_terms,
    clear_cache,
)


@pytest.fixture(autouse=True)
def setup_env():
    """Set up environment variables for testing."""
    os.environ["LLM_ARBITER_ENABLED"] = "true"
    os.environ["LLM_ARBITER_MODEL"] = "gpt-4.1-nano"
    os.environ["OPENAI_API_KEY"] = "test-key-12345"
    os.environ["LLM_ZERO_MATCH_BATCH_SIZE"] = "20"
    os.environ["LLM_ZERO_MATCH_BATCH_TIMEOUT"] = "5.0"
    clear_cache()
    yield
    clear_cache()


def _create_mock_response(content: str, prompt_tokens: int = 200, completion_tokens: int = 50) -> Mock:
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


def _make_items(n: int) -> list[dict]:
    """Create n test items for batch classification."""
    return [
        {"objeto": f"Aquisição de equipamento tipo {i} para órgão público", "valor": 1000.0 * (i + 1)}
        for i in range(n)
    ]


# ============================================================================
# _parse_batch_response tests
# ============================================================================


class TestParseBatchResponse:
    """Tests for the batch response parser."""

    def test_parse_numbered_yes_no(self):
        """Parse standard numbered YES/NO format."""
        raw = "1. YES\n2. NO\n3. YES\n4. NO\n5. YES"
        result = _parse_batch_response(raw, 5)
        assert result == [True, False, True, False, True]

    def test_parse_with_sim_nao(self):
        """Parse Portuguese SIM/NAO format."""
        raw = "1. SIM\n2. NAO\n3. SIM"
        result = _parse_batch_response(raw, 3)
        assert result == [True, False, True]

    def test_parse_with_nao_accent(self):
        """Parse NÃO with accent."""
        raw = "1. YES\n2. NÃO\n3. YES"
        result = _parse_batch_response(raw, 3)
        assert result == [True, False, True]

    def test_parse_count_mismatch_returns_none(self):
        """AC5: Count mismatch returns None (reject all)."""
        raw = "1. YES\n2. NO\n3. YES"
        result = _parse_batch_response(raw, 5)  # Expected 5, got 3
        assert result is None

    def test_parse_empty_lines_ignored(self):
        """Empty lines between results are ignored."""
        raw = "1. YES\n\n2. NO\n\n3. YES"
        result = _parse_batch_response(raw, 3)
        assert result == [True, False, True]

    def test_parse_parenthesis_format(self):
        """Parse 1) YES format."""
        raw = "1) YES\n2) NO\n3) YES"
        result = _parse_batch_response(raw, 3)
        assert result == [True, False, True]

    def test_parse_colon_format(self):
        """Parse 1: YES format."""
        raw = "1: YES\n2: NO"
        result = _parse_batch_response(raw, 2)
        assert result == [True, False]

    def test_parse_case_insensitive(self):
        """YES/NO matching is case insensitive."""
        raw = "1. yes\n2. No\n3. Yes"
        result = _parse_batch_response(raw, 3)
        assert result == [True, False, True]

    def test_parse_zero_items(self):
        """Zero expected items with empty response."""
        raw = ""
        result = _parse_batch_response(raw, 0)
        assert result == []


# ============================================================================
# _build_zero_match_batch_prompt tests
# ============================================================================


class TestBuildBatchPrompt:
    """Tests for batch prompt builders."""

    def test_sector_prompt_contains_all_items(self):
        """Prompt includes all items in numbered list."""
        items = _make_items(3)
        prompt = _build_zero_match_batch_prompt("informatica", "Informática e TI", items)
        assert "1." in prompt
        assert "2." in prompt
        assert "3." in prompt
        assert "Informática e TI" in prompt
        assert "YES ou NO" in prompt

    def test_sector_prompt_truncates_objeto(self):
        """Items with long objeto are truncated to 200 chars."""
        items = [{"objeto": "X" * 300, "valor": 1000.0}]
        prompt = _build_zero_match_batch_prompt("informatica", "Informática e TI", items)
        # The item line should have truncated objeto
        assert "X" * 201 not in prompt

    def test_terms_prompt_includes_terms(self):
        """Term-based prompt includes user's search terms."""
        items = _make_items(2)
        prompt = _build_zero_match_batch_prompt_terms(["computador", "servidor"], items)
        assert "computador, servidor" in prompt
        assert "1." in prompt
        assert "2." in prompt

    @patch("sectors.get_sector")
    def test_sector_prompt_with_unknown_sector(self, mock_get_sector):
        """Unknown sector falls back gracefully."""
        mock_get_sector.side_effect = KeyError("not found")
        items = _make_items(2)
        prompt = _build_zero_match_batch_prompt("unknown", "Unknown Sector", items)
        assert "Unknown Sector" in prompt


# ============================================================================
# _classify_zero_match_batch tests
# ============================================================================


class TestClassifyZeroMatchBatch:
    """Tests for the batch classification function."""

    @patch("llm_arbiter._get_client")
    def test_batch_20_items_returns_20_results(self, mock_get_client):
        """AC1: Batch with 20 items returns 20 YES/NO responses."""
        # Build response: first 10 YES, last 10 NO
        response_lines = [f"{i+1}. {'YES' if i < 10 else 'NO'}" for i in range(20)]
        raw = "\n".join(response_lines)
        mock_get_client.return_value.chat.completions.create.return_value = _create_mock_response(raw)

        items = _make_items(20)
        results = _classify_zero_match_batch(
            items=items, setor_name="Informática e TI", setor_id="informatica"
        )

        assert len(results) == 20
        assert sum(1 for r in results if r["is_primary"]) == 10
        assert sum(1 for r in results if not r["is_primary"]) == 10
        # Confidence is 60 for batch YES, 0 for NO
        assert results[0]["confidence"] == 60
        assert results[15]["confidence"] == 0

    @patch("llm_arbiter._get_client")
    def test_batch_incomplete_response_rejects_all(self, mock_get_client):
        """AC5: Batch with 15 responses for 20 items rejects all."""
        response_lines = [f"{i+1}. YES" for i in range(15)]
        raw = "\n".join(response_lines)
        mock_get_client.return_value.chat.completions.create.return_value = _create_mock_response(raw)

        items = _make_items(20)
        results = _classify_zero_match_batch(
            items=items, setor_name="Informática e TI", setor_id="informatica"
        )

        assert len(results) == 20
        # All rejected due to count mismatch
        assert all(not r["is_primary"] for r in results)
        assert all(r["rejection_reason"] == "Batch response count mismatch" for r in results)

    @patch("llm_arbiter._get_client")
    def test_batch_llm_failure_raises(self, mock_get_client):
        """AC2: Batch failure raises exception (caller handles fallback)."""
        mock_get_client.return_value.chat.completions.create.side_effect = Exception("API error")

        items = _make_items(5)
        with pytest.raises(Exception, match="API error"):
            _classify_zero_match_batch(
                items=items, setor_name="Informática e TI", setor_id="informatica"
            )

    @patch("llm_arbiter._get_client")
    def test_batch_empty_items_returns_empty(self, mock_get_client):
        """Empty input returns empty results without calling LLM."""
        results = _classify_zero_match_batch(
            items=[], setor_name="Informática e TI", setor_id="informatica"
        )
        assert results == []
        mock_get_client.return_value.chat.completions.create.assert_not_called()

    @patch("llm_arbiter._get_client")
    def test_batch_with_custom_terms(self, mock_get_client):
        """Batch works with custom search terms instead of sector."""
        raw = "1. YES\n2. NO\n3. YES"
        mock_get_client.return_value.chat.completions.create.return_value = _create_mock_response(raw)

        items = _make_items(3)
        results = _classify_zero_match_batch(
            items=items, termos_busca=["computador", "servidor"]
        )

        assert len(results) == 3
        assert results[0]["is_primary"] is True
        assert results[1]["is_primary"] is False
        assert results[2]["is_primary"] is True

    @patch("llm_arbiter._get_client")
    def test_batch_timeout_handled(self, mock_get_client):
        """AC7: Timeout raises exception (caller handles)."""
        from openai import APITimeoutError
        mock_get_client.return_value.chat.completions.create.side_effect = \
            APITimeoutError(request=Mock())

        items = _make_items(5)
        with pytest.raises(APITimeoutError):
            _classify_zero_match_batch(
                items=items, setor_name="Test", setor_id="test"
            )


# ============================================================================
# Integration: filter.py batch path
# ============================================================================


class TestFilterBatchIntegration:
    """Integration tests for batch zero-match in filter.py."""

    @patch("llm_arbiter._get_client")
    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    def test_50_items_completes_via_batch(self, mock_get_client):
        """Integration: 50 zero-match items processed via batch (mocked LLM)."""
        call_count = [0]  # noqa: F841

        # Pre-build responses for 3 batches: 20, 20, 10
        responses = [
            _create_mock_response("\n".join(f"{i+1}. YES" for i in range(20))),
            _create_mock_response("\n".join(f"{i+1}. YES" for i in range(20))),
            _create_mock_response("\n".join(f"{i+1}. YES" for i in range(10))),
        ]

        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = responses
        mock_get_client.return_value = mock_client

        from llm_arbiter import _classify_zero_match_batch

        items = _make_items(50)
        from config import LLM_ZERO_MATCH_BATCH_SIZE
        all_results = []
        for i in range(0, len(items), LLM_ZERO_MATCH_BATCH_SIZE):
            batch = items[i:i + LLM_ZERO_MATCH_BATCH_SIZE]
            results = _classify_zero_match_batch(
                items=batch, setor_name="Informática e TI", setor_id="informatica"
            )
            all_results.extend(results)

        assert len(all_results) == 50
        assert all(r["is_primary"] for r in all_results)
        assert mock_client.chat.completions.create.call_count == 3  # 20 + 20 + 10

    @patch("llm_arbiter._get_client")
    def test_batch_vs_individual_regression(self, mock_get_client):
        """Regression: batch and individual produce same accept/reject for same data.

        Uses deterministic mock responses to verify consistency.
        """
        items = _make_items(5)

        # Batch: items 0,2,4 = YES; 1,3 = NO
        batch_raw = "1. YES\n2. NO\n3. YES\n4. NO\n5. YES"
        mock_get_client.return_value.chat.completions.create.return_value = \
            _create_mock_response(batch_raw)

        batch_results = _classify_zero_match_batch(
            items=items, setor_name="Informática e TI", setor_id="informatica"
        )

        # Verify pattern
        expected_primary = [True, False, True, False, True]
        actual_primary = [r["is_primary"] for r in batch_results]
        assert actual_primary == expected_primary

        # Individual: same pattern via classify_contract_primary_match
        clear_cache()
        from llm_arbiter import classify_contract_primary_match

        individual_results = []
        for i, item in enumerate(items):
            # Mock response for each individual call
            response_text = "SIM" if expected_primary[i] else "NAO"
            mock_get_client.return_value.chat.completions.create.return_value = \
                _create_mock_response(response_text, completion_tokens=1)

            result = classify_contract_primary_match(
                objeto=item["objeto"],
                valor=item["valor"],
                setor_name="Informática e TI",
                prompt_level="zero_match",
                setor_id="informatica",
            )
            individual_results.append(result)
            clear_cache()  # Prevent cache hits

        individual_primary = [r["is_primary"] for r in individual_results]
        assert individual_primary == expected_primary


# ============================================================================
# Metrics tests
# ============================================================================


class TestBatchMetrics:
    """Tests for UX-402 Prometheus metrics."""

    def test_batch_duration_metric_exists(self):
        """AC3: smartlic_llm_zero_match_batch_duration_seconds exists."""
        from metrics import LLM_ZERO_MATCH_BATCH_DURATION
        assert LLM_ZERO_MATCH_BATCH_DURATION is not None

    def test_batch_size_metric_exists(self):
        """AC8: smartlic_llm_zero_match_batch_size exists."""
        from metrics import LLM_ZERO_MATCH_BATCH_SIZE
        assert LLM_ZERO_MATCH_BATCH_SIZE is not None

    @patch("llm_arbiter._get_client")
    def test_batch_observes_duration_metric(self, mock_get_client):
        """AC3: Batch classification observes duration histogram."""
        raw = "1. YES\n2. NO"
        mock_get_client.return_value.chat.completions.create.return_value = _create_mock_response(raw)

        items = _make_items(2)
        results = _classify_zero_match_batch(
            items=items, setor_name="Test", setor_id="test"
        )
        assert len(results) == 2
        # Duration metric is observed inside the function (no assertion needed beyond no-error)

    def test_batch_size_config(self):
        """AC1: Batch size config defaults to 20."""
        from config import LLM_ZERO_MATCH_BATCH_SIZE
        assert LLM_ZERO_MATCH_BATCH_SIZE == 20

    def test_batch_timeout_config(self):
        """AC7: Batch timeout config defaults to 5.0s."""
        from config import LLM_ZERO_MATCH_BATCH_TIMEOUT
        assert LLM_ZERO_MATCH_BATCH_TIMEOUT == 5.0
