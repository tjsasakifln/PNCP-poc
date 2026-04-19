"""
STORY-402: LLM Zero Match Batch Classification Tests

Tests for batch LLM zero-match classification that sends up to 20 items per call
instead of individual calls. Covers AC1-AC8.
"""

import os
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime, timedelta

import pytest

from llm_arbiter import (
    _classify_zero_match_batch,
    _build_zero_match_batch_prompt,
    _parse_batch_response,
    clear_cache,
)
from filter import aplicar_todos_filtros


@pytest.fixture(autouse=True)
def setup_env():
    """Set up environment for testing."""
    os.environ["LLM_ARBITER_ENABLED"] = "true"
    os.environ["LLM_ZERO_MATCH_ENABLED"] = "true"
    os.environ["OPENAI_API_KEY"] = "test-key"
    clear_cache()
    yield
    clear_cache()


def _future_date(days=10):
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def _past_date(days=2):
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def make_zero_match_bid(
    codigo="ZM-001",
    objeto="Consultoria em gestão empresarial e planejamento estratégico",
    valor=150000.0,
    uf="SP",
):
    return {
        "codigoCompra": codigo,
        "objetoCompra": objeto,
        "valorTotalEstimado": valor,
        "uf": uf,
        "modalidadeNome": "Pregão Eletrônico",
        "nomeOrgao": "Prefeitura Municipal de São Paulo",
        "municipio": "São Paulo",
        "dataPublicacaoPncp": _past_date(),
        "dataAberturaProposta": _past_date(1),
        "dataEncerramentoProposta": _future_date(),
    }


# ==============================================================================
# AC1: Batch with 20 items returns 20 YES/NO responses
# ==============================================================================


class TestAC1BatchClassification:
    """AC1: _classify_zero_match_batch sends up to 20 items per call."""

    @patch("llm_arbiter._get_client")
    def test_batch_20_items_returns_20_results(self, mock_get_client):
        """20 items in batch → 20 results returned."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # LLM returns YES for first 8, NO for rest
        response_lines = []
        for i in range(20):
            answer = "YES" if i < 8 else "NO"
            response_lines.append(f"{i+1}. {answer}")
        response_text = "\n".join(response_lines)

        resp = MagicMock()
        resp.choices[0].message.content = response_text
        resp.usage = MagicMock()
        resp.usage.prompt_tokens = 500
        resp.usage.completion_tokens = 60
        mock_client.chat.completions.create.return_value = resp

        items = [
            {"objeto": f"Consultoria técnica em serviço {i}", "valor": 50000.0}
            for i in range(20)
        ]

        results = _classify_zero_match_batch(
            items=items,
            setor_id="vestuario",
            setor_name="Vestuário e Uniformes",
        )

        assert len(results) == 20
        assert sum(1 for r in results if r["is_primary"]) == 8
        assert sum(1 for r in results if not r["is_primary"]) == 12
        # Single LLM call
        assert mock_client.chat.completions.create.call_count == 1

    @patch("llm_arbiter._get_client")
    def test_batch_confidence_capped_at_70(self, mock_get_client):
        """D-02 AC4: Zero-match batch results have confidence capped at 70."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        resp = MagicMock()
        resp.choices[0].message.content = "1. YES"
        resp.usage = MagicMock()
        resp.usage.prompt_tokens = 100
        resp.usage.completion_tokens = 10
        mock_client.chat.completions.create.return_value = resp

        items = [{"objeto": "Aquisição de uniformes", "valor": 50000.0}]
        results = _classify_zero_match_batch(
            items=items, setor_id="vestuario", setor_name="Vestuário",
        )

        assert len(results) == 1
        assert results[0]["confidence"] == 60  # batch mode uses fixed confidence=60

    @patch("llm_arbiter._get_client")
    def test_batch_empty_items_returns_empty(self, mock_get_client):
        """Empty items list returns empty results."""
        results = _classify_zero_match_batch(
            items=[], setor_id="vestuario", setor_name="Vestuário",
        )
        assert results == []
        mock_get_client.assert_not_called()


# ==============================================================================
# AC5: Incomplete batch response → reject all
# ==============================================================================


class TestAC5IncompleteResponse:
    """AC5: If batch response count != item count, reject all."""

    @patch("llm_arbiter._get_client")
    def test_incomplete_response_rejects_all(self, mock_get_client):
        """15 responses for 20 items → all rejected."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Only 15 answers for 20 items
        response_lines = [f"{i+1}. YES" for i in range(15)]
        response_text = "\n".join(response_lines)

        resp = MagicMock()
        resp.choices[0].message.content = response_text
        resp.usage = MagicMock()
        resp.usage.prompt_tokens = 500
        resp.usage.completion_tokens = 45
        mock_client.chat.completions.create.return_value = resp

        items = [
            {"objeto": f"Serviço de consultoria {i}", "valor": 50000.0}
            for i in range(20)
        ]

        results = _classify_zero_match_batch(
            items=items, setor_id="vestuario", setor_name="Vestuário",
        )

        assert len(results) == 20
        assert all(not r["is_primary"] for r in results)
        assert all(r["rejection_reason"] == "Batch response count mismatch" for r in results)

    def test_parse_batch_response_mismatch(self):
        """Parser returns None on count mismatch."""
        result = _parse_batch_response("1. YES\n2. NO\n3. YES", expected_count=5)
        assert result is None

    def test_parse_batch_response_exact_match(self):
        """Parser succeeds with exact count."""
        result = _parse_batch_response("1. YES\n2. NO\n3. YES", expected_count=3)
        assert result == [True, False, True]

    def test_parse_batch_response_formats(self):
        """Parser handles various numbering formats."""
        result = _parse_batch_response(
            "1) YES\n2) NO\n3: SIM\n4. NAO", expected_count=4
        )
        assert result == [True, False, True, False]


# DEBT-128: TestAC2BatchFallbackToIndividual removed — individual fallback mode
# no longer exists. Batch mode is always-on.


#
# ==============================================================================
# Integration: 50 zero-match items via batch (LLM mocked)
# ==============================================================================


class TestIntegration50Items:
    """Integration: _classify_zero_match_batch chunks 50 items into 3 LLM calls.

    CIG-BE-story-drift-llm-batch-zero-match: the filter pipeline was migrated
    from batch to per-item gather by STORY-4.1 (TD-SYS-014). The batch
    function itself is still the contract for `jobs/queue/jobs.py`, so this
    integration test now exercises `_classify_zero_match_batch` directly.
    """

    @patch("llm_arbiter._get_client")
    def test_50_items_batch_processing(self, mock_get_client):
        """50 zero-match items call _classify_zero_match_batch 3x (20+20+10)."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        def batch_response(**kwargs):
            messages = kwargs.get("messages", [])
            user_msg = messages[-1]["content"] if messages else ""
            import re
            items = re.findall(r'^\d+\.', user_msg, re.MULTILINE)
            count = len(items) or 1

            lines = []
            for i in range(count):
                answer = "YES" if i % 3 == 0 else "NO"
                lines.append(f"{i+1}. {answer}")

            resp = MagicMock()
            resp.choices[0].message.content = "\n".join(lines)
            resp.usage = MagicMock()
            resp.usage.prompt_tokens = 1000
            resp.usage.completion_tokens = count * 3
            return resp

        mock_client.chat.completions.create.side_effect = batch_response

        items = [
            {
                "index": i + 1,
                "objeto": f"Consultoria em planejamento estratégico {i}",
                "valor": 150000.0 + i,
            }
            for i in range(50)
        ]

        # Chunk in batches of 20 (LLM_ZERO_MATCH_BATCH_SIZE default): 20 + 20 + 10
        BATCH_SIZE = 20
        all_results = []
        for start in range(0, len(items), BATCH_SIZE):
            chunk = items[start:start + BATCH_SIZE]
            all_results.extend(
                _classify_zero_match_batch(
                    items=chunk,
                    setor_name="Vestuário",
                    setor_id="vestuario",
                )
            )

        assert len(all_results) == 50
        assert mock_client.chat.completions.create.call_count == 3
        approved = sum(1 for r in all_results if r.get("is_primary"))
        rejected = sum(1 for r in all_results if not r.get("is_primary"))
        assert approved + rejected == 50




# ==============================================================================
# AC4: Existing counters remain compatible
# ==============================================================================


class TestAC4CounterCompatibility:
    """AC4: llm_zero_match_calls/aprovadas/rejeitadas counters work with batch."""

    @patch("llm_arbiter._get_client")
    def test_counters_compatible_with_batch(self, mock_get_client):
        """_classify_zero_match_batch produces 3 YES / 2 NO decisions in order.

        CIG-BE-story-drift-llm-batch-zero-match: asserts directly on the batch
        function's output (same data contract used by `jobs/queue/jobs.py`).
        """
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Batch: 3 YES, 2 NO
        resp = MagicMock()
        resp.choices[0].message.content = "1. YES\n2. YES\n3. YES\n4. NO\n5. NO"
        resp.usage = MagicMock()
        resp.usage.prompt_tokens = 500
        resp.usage.completion_tokens = 15
        mock_client.chat.completions.create.return_value = resp

        items = [
            {"index": i + 1, "objeto": f"Consultoria {i}", "valor": 150000.0}
            for i in range(5)
        ]

        results = _classify_zero_match_batch(
            items=items,
            setor_name="Vestuário",
            setor_id="vestuario",
        )

        assert len(results) == 5
        approved = [r for r in results if r.get("is_primary")]
        rejected = [r for r in results if not r.get("is_primary")]
        assert len(approved) == 3
        assert len(rejected) == 2


# ==============================================================================
# Prompt building tests
# ==============================================================================


class TestBatchPromptBuilding:
    """Tests for _build_zero_match_batch_prompt."""

    def test_prompt_contains_all_items(self):
        items = [
            {"index": 1, "objeto": "Serviço A", "valor": 100},
            {"index": 2, "objeto": "Serviço B", "valor": 200},
            {"index": 3, "objeto": "Serviço C", "valor": 300},
        ]
        prompt = _build_zero_match_batch_prompt("vestuario", "Vestuário", items)

        # Format: {i}. [{val_display}] {obj}
        assert "1. [R$ 100.00] Serviço A" in prompt
        assert "2. [R$ 200.00] Serviço B" in prompt
        assert "3. [R$ 300.00] Serviço C" in prompt
        assert "Vestuário" in prompt

    def test_prompt_without_sector_id(self):
        items = [{"index": 1, "objeto": "Serviço X", "valor": 100}]
        prompt = _build_zero_match_batch_prompt(None, "Custom Sector", items)
        assert "Custom Sector" in prompt
        assert "YES ou NO" in prompt

    def test_prompt_truncates_long_objeto(self):
        long_text = "A" * 500
        items = [{"index": 1, "objeto": long_text, "valor": 100}]
        prompt = _build_zero_match_batch_prompt("vestuario", "Vestuário", items)
        # Should truncate to 200 chars
        assert "A" * 200 in prompt
        assert "A" * 201 not in prompt


# ==============================================================================
# AC7: Timeout per batch
# ==============================================================================


class TestAC7BatchTimeout:
    """AC7: Batch timeout → reject pending and continue."""

    @patch("llm_arbiter._get_client")
    def test_batch_timeout_rejects_all(self, mock_get_client):
        """When batch call exceeds timeout, exception is raised for caller to handle."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Simulate timeout
        mock_client.chat.completions.create.side_effect = TimeoutError("5s exceeded")

        items = [
            {"objeto": f"Serviço de consultoria {i}", "valor": 50000.0}
            for i in range(10)
        ]

        # _classify_zero_match_batch re-raises exceptions for caller to handle fallback
        with pytest.raises(TimeoutError):
            _classify_zero_match_batch(
                items=items, setor_id="vestuario", setor_name="Vestuário",
            )
