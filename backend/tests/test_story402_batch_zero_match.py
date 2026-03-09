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
    os.environ["LLM_ZERO_MATCH_BATCH_ENABLED"] = "true"
    os.environ["OPENAI_API_KEY"] = "test-key"
    clear_cache()
    yield
    clear_cache()
    os.environ.pop("LLM_ZERO_MATCH_BATCH_ENABLED", None)


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
        assert results[0]["confidence"] == 70  # capped

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


# ==============================================================================
# AC2: Batch failure → fallback to individual calls
# ==============================================================================


class TestAC2BatchFallbackToIndividual:
    """AC2: When batch call fails, fallback to individual calls."""

    @patch("llm_arbiter._get_client")
    @patch("llm_arbiter._classify_zero_match_batch", side_effect=Exception("Batch crash"))
    def test_batch_failure_triggers_individual_fallback(self, mock_batch, mock_get_client):
        """If batch function raises exception, filter.py falls back to individual."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Individual calls succeed
        resp = MagicMock()
        resp.choices[0].message.content = "SIM"
        resp.usage = None
        mock_client.chat.completions.create.return_value = resp

        bids = [
            make_zero_match_bid(
                codigo=f"FB-{i}",
                objeto=f"Consultoria em planejamento e gestão pública para município {i}",
            )
            for i in range(5)
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # Batch was attempted
        assert mock_batch.called
        # All 5 should have been processed (via individual fallback)
        assert stats["llm_zero_match_calls"] == 5
        # Individual calls made (5 bids = 5 calls)
        assert mock_client.chat.completions.create.call_count == 5


# ==============================================================================
# AC6: Feature flag False → use individual loop
# ==============================================================================


class TestAC6FeatureFlag:
    """AC6: LLM_ZERO_MATCH_BATCH_ENABLED=False uses individual calls."""

    @patch("config.LLM_ZERO_MATCH_BATCH_ENABLED", False)
    @patch("llm_arbiter._get_client")
    def test_flag_disabled_uses_individual(self, mock_get_client):
        """With batch flag off, each bid gets its own LLM call."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        resp = MagicMock()
        resp.choices[0].message.content = "SIM"
        resp.usage = None
        mock_client.chat.completions.create.return_value = resp

        bids = [
            make_zero_match_bid(
                codigo=f"IND-{i}",
                objeto=f"Consultoria em planejamento estratégico e gestão empresarial {i}",
            )
            for i in range(5)
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # All 5 classified individually
        assert stats["llm_zero_match_calls"] == 5
        assert stats["llm_zero_match_aprovadas"] == 5
        # Individual calls: 1 per bid
        assert mock_client.chat.completions.create.call_count == 5


# ==============================================================================
# Integration: 50 zero-match items via batch (LLM mocked)
# ==============================================================================


class TestIntegration50Items:
    """Integration: 50 zero-match items complete via batch classification."""

    @patch("llm_arbiter._get_client")
    def test_50_items_batch_processing(self, mock_get_client):
        """50 zero-match bids processed in batch mode (3 chunks: 20+20+10)."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Mock returns correct number of answers per call
        def batch_response(**kwargs):
            messages = kwargs.get("messages", [])
            user_msg = messages[-1]["content"] if messages else ""
            # Count numbered items in prompt
            import re
            items = re.findall(r'^\d+\.', user_msg, re.MULTILINE)
            count = len(items)
            if count == 0:
                count = 1

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

        bids = [
            make_zero_match_bid(
                codigo=f"INT-{i}",
                objeto=f"Consultoria em planejamento estratégico e assessoria técnica especializada número {i}",
            )
            for i in range(50)
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # All 50 processed
        assert stats["llm_zero_match_calls"] == 50
        total_decisions = stats["llm_zero_match_aprovadas"] + stats["llm_zero_match_rejeitadas"]
        assert total_decisions == 50
        # Batch mode: 3 calls (20+20+10) instead of 50 individual
        assert mock_client.chat.completions.create.call_count == 3


# ==============================================================================
# Regression: Batch vs individual produce equivalent decisions
# ==============================================================================


class TestRegressionBatchVsIndividual:
    """Regression: batch and individual modes produce consistent results."""

    @patch("llm_arbiter._get_client")
    def test_batch_and_individual_same_stats(self, mock_get_client):
        """Both modes should produce same accept/reject counts for same inputs."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Individual mode: always returns SIM
        resp_individual = MagicMock()
        resp_individual.choices[0].message.content = "SIM"
        resp_individual.usage = None

        bids = [
            make_zero_match_bid(
                codigo=f"REG-{i}",
                objeto=f"Consultoria em planejamento estratégico e gestão organizacional completa {i}",
            )
            for i in range(10)
        ]

        # Run individual mode
        clear_cache()
        mock_client.chat.completions.create.return_value = resp_individual

        with patch("config.LLM_ZERO_MATCH_BATCH_ENABLED", False):
            _, stats_ind = aplicar_todos_filtros(
                licitacoes=[dict(b) for b in bids],
                ufs_selecionadas={"SP"},
                setor="vestuario",
            )

        # Run batch mode
        clear_cache()
        batch_lines = "\n".join(f"{i+1}. YES" for i in range(10))
        resp_batch = MagicMock()
        resp_batch.choices[0].message.content = batch_lines
        resp_batch.usage = MagicMock()
        resp_batch.usage.prompt_tokens = 1000
        resp_batch.usage.completion_tokens = 30
        mock_client.chat.completions.create.return_value = resp_batch

        with patch("config.LLM_ZERO_MATCH_BATCH_ENABLED", True):
            _, stats_batch = aplicar_todos_filtros(
                licitacoes=[dict(b) for b in bids],
                ufs_selecionadas={"SP"},
                setor="vestuario",
            )

        # Same number of calls and approvals
        assert stats_ind["llm_zero_match_calls"] == stats_batch["llm_zero_match_calls"]
        assert stats_ind["llm_zero_match_aprovadas"] == stats_batch["llm_zero_match_aprovadas"]
        assert stats_ind["llm_zero_match_rejeitadas"] == stats_batch["llm_zero_match_rejeitadas"]


# ==============================================================================
# AC4: Existing counters remain compatible
# ==============================================================================


class TestAC4CounterCompatibility:
    """AC4: llm_zero_match_calls/aprovadas/rejeitadas counters work with batch."""

    @patch("llm_arbiter._get_client")
    def test_counters_compatible_with_batch(self, mock_get_client):
        """Batch mode still populates the same stats keys."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Batch: 3 YES, 2 NO
        resp = MagicMock()
        resp.choices[0].message.content = "1. YES\n2. YES\n3. YES\n4. NO\n5. NO"
        resp.usage = MagicMock()
        resp.usage.prompt_tokens = 500
        resp.usage.completion_tokens = 15
        mock_client.chat.completions.create.return_value = resp

        bids = [
            make_zero_match_bid(
                codigo=f"COMPAT-{i}",
                objeto=f"Consultoria em assessoria técnica e planejamento estratégico {i}",
            )
            for i in range(5)
        ]

        _, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert stats["llm_zero_match_calls"] == 5
        assert stats["llm_zero_match_aprovadas"] == 3
        assert stats["llm_zero_match_rejeitadas"] == 2
        assert "llm_zero_match_skipped_short" in stats


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

        assert '1. "Serviço A"' in prompt
        assert '2. "Serviço B"' in prompt
        assert '3. "Serviço C"' in prompt
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
        """When batch call exceeds timeout, all items get rejected/pending."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Simulate timeout
        mock_client.chat.completions.create.side_effect = TimeoutError("5s exceeded")

        items = [
            {"objeto": f"Serviço de consultoria {i}", "valor": 50000.0}
            for i in range(10)
        ]

        results = _classify_zero_match_batch(
            items=items, setor_id="vestuario", setor_name="Vestuário",
        )

        assert len(results) == 10
        assert all(not r["is_primary"] for r in results)
        # With PENDING fallback enabled, should have pending_review
        assert all(r.get("pending_review", False) for r in results)
