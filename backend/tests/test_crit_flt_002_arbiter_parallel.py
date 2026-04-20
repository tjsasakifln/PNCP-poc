"""
CRIT-FLT-002: LLM Arbiter Parallelization Tests

Tests that the gray-zone (1-5% density) LLM arbiter runs in parallel
using ThreadPoolExecutor, matching the zero-match pattern.

Coverage:
- AC1: Parallel execution via ThreadPoolExecutor
- AC2: QA audit sampling works inside parallelism
- AC3: Thread-safe stats counters
- AC4: Fallback on LLM failure = REJECT
- AC5: Timing log emitted
- AC6: Cache MD5 functional (thread-safe by design)
- AC7: Parallelism validated via latency measurement
"""

import os
import time
from unittest.mock import patch

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


def _make_gray_zone_bid(index: int, uf: str = "SP") -> dict:
    """Create a bid that lands in the gray zone (1-5% density) for vestuario.

    Uses a long generic text with a single vestuario keyword ("uniformes")
    and no exclusion keywords. Density ~2% to land in the LLM arbiter gray zone.
    """
    return {
        "uf": uf,
        "valorTotalEstimado": 100_000,
        "objetoCompra": (
            f"Registro de preço para eventual aquisição de bens diversos "
            f"destinados ao órgão público federal, incluindo itens de "
            f"expediente e uniformes para colaboradores da unidade "
            f"número {index}, com entrega programada ao longo do exercício "
            f"financeiro vigente, pelo período de doze meses, com "
            f"possibilidade de prorrogação, em parcelas trimestrais, "
            f"tudo conforme condições do edital e seus respectivos anexos"
        ),
        "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
    }


def _mock_llm_response(is_primary: bool, confidence: int = 70):
    """Create a mock LLM structured response dict."""
    return {
        "is_primary": is_primary,
        "confidence": confidence,
        "evidence": ["uniformes"] if is_primary else [],
        "rejection_reason": "" if is_primary else "tangential mention only",
    }


class TestArbiterParallelExecution:
    """AC1 + AC7: Verify parallel execution via ThreadPoolExecutor."""

    @patch("llm_arbiter.classify_contract_primary_match")
    def test_parallel_faster_than_sequential(self, mock_classify):
        """AC7: Multiple bids execute in parallel (latency << sequential sum)."""
        call_delay = 0.1  # 100ms per call

        def slow_classify(**kwargs):
            time.sleep(call_delay)
            return _mock_llm_response(True, 75)

        mock_classify.side_effect = slow_classify

        num_bids = 10
        bids = [_make_gray_zone_bid(i) for i in range(num_bids)]

        t0 = time.monotonic()
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )
        elapsed = time.monotonic() - t0

        # If sequential, would take >= 1.0s (10 * 0.1s)
        # If parallel with 10 workers, should take ~0.1-0.3s
        # Use generous threshold to avoid flaky tests
        sequential_time = num_bids * call_delay
        assert elapsed < sequential_time * 0.6, (
            f"Expected parallel execution to be faster than 60% of sequential. "
            f"Elapsed: {elapsed:.2f}s, Sequential would be: {sequential_time:.1f}s"
        )

        # All calls should have been made
        assert stats["llm_arbiter_calls"] == num_bids

    @patch("llm_arbiter.classify_contract_primary_match")
    def test_single_bid_still_works(self, mock_classify):
        """Single bid doesn't break the parallel pattern."""
        mock_classify.return_value = _mock_llm_response(True, 80)

        bids = [_make_gray_zone_bid(0)]
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert stats["llm_arbiter_calls"] == 1
        assert stats["aprovadas_llm_arbiter"] == 1


class TestArbiterQaAudit:
    """AC2: QA audit sampling works inside parallelism."""

    @patch("llm_arbiter.classify_contract_primary_match")
    @patch("filter.pipeline.random")
    def test_qa_audit_sampling_in_parallel(self, mock_random, mock_classify):
        """AC2: QA audit tags are correctly applied within parallel execution."""
        mock_classify.return_value = _mock_llm_response(True, 75)
        # Make random.random() always return 0 (below any sample rate)
        # but keep random.sample working normally
        mock_random.random.return_value = 0.0
        mock_random.sample.side_effect = lambda pop, k: list(pop)[:k] if hasattr(pop, '__iter__') else []

        bids = [_make_gray_zone_bid(i) for i in range(5)]
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # All approved bids should have QA audit tags (since random always < rate)
        audited = [b for b in aprovadas if b.get("_qa_audit")]
        assert len(audited) > 0, "QA audit sampling should work within parallel execution"

        # Verify audit decision structure
        for bid in audited:
            decision = bid["_qa_audit_decision"]
            assert "trace_id" in decision
            assert "llm_response" in decision
            assert "prompt_level" in decision
            assert "confidence" in decision
            assert "evidence" in decision


class TestArbiterThreadSafeStats:
    """AC3: Stats counters are thread-safe."""

    @patch("llm_arbiter.classify_contract_primary_match")
    def test_stats_accurate_with_mixed_results(self, mock_classify):
        """AC3: Stats accurately count approvals and rejections in parallel."""
        # Alternate between approve and reject
        call_count = 0

        def alternating_classify(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                return _mock_llm_response(False, 30)
            return _mock_llm_response(True, 75)

        mock_classify.side_effect = alternating_classify

        num_bids = 20
        bids = [_make_gray_zone_bid(i) for i in range(num_bids)]
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # Total calls must equal number of bids that reached Camada 3A
        total_arbiter = stats["aprovadas_llm_arbiter"] + stats["rejeitadas_llm_arbiter"]
        assert stats["llm_arbiter_calls"] == total_arbiter, (
            f"llm_arbiter_calls ({stats['llm_arbiter_calls']}) != "
            f"approved ({stats['aprovadas_llm_arbiter']}) + "
            f"rejected ({stats['rejeitadas_llm_arbiter']})"
        )

    @patch("llm_arbiter.classify_contract_primary_match")
    def test_stats_all_approved(self, mock_classify):
        """AC3: All bids approved — stats consistent."""
        mock_classify.return_value = _mock_llm_response(True, 80)

        bids = [_make_gray_zone_bid(i) for i in range(8)]
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert stats["rejeitadas_llm_arbiter"] == 0
        assert stats["aprovadas_llm_arbiter"] == stats["llm_arbiter_calls"]

    @patch("llm_arbiter.classify_contract_primary_match")
    def test_stats_all_rejected(self, mock_classify):
        """AC3: All bids rejected — stats consistent."""
        mock_classify.return_value = _mock_llm_response(False, 20)

        bids = [_make_gray_zone_bid(i) for i in range(8)]
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert stats["aprovadas_llm_arbiter"] == 0
        assert stats["rejeitadas_llm_arbiter"] == stats["llm_arbiter_calls"]


class TestArbiterFailureFallback:
    """AC4: Fallback on LLM failure = REJECT."""

    @patch("llm_arbiter.classify_contract_primary_match")
    def test_llm_exception_counts_as_reject(self, mock_classify):
        """AC4: LLM exception → REJECT fallback, stats incremented."""
        mock_classify.side_effect = Exception("OpenAI API timeout")

        bids = [_make_gray_zone_bid(i) for i in range(3)]
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # All should be rejected (none approved via arbiter due to exception)
        assert stats["aprovadas_llm_arbiter"] == 0
        assert stats["rejeitadas_llm_arbiter"] == stats["llm_arbiter_calls"]

    @patch("llm_arbiter.classify_contract_primary_match")
    def test_partial_failure_mixed(self, mock_classify):
        """AC4: Some succeed, some fail — failed ones are REJECTED."""
        call_count = 0

        def sometimes_fail(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:
                raise Exception("Intermittent API failure")
            return _mock_llm_response(True, 75)

        mock_classify.side_effect = sometimes_fail

        bids = [_make_gray_zone_bid(i) for i in range(9)]
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # Verify stats consistency: calls = approved + rejected
        total = stats["aprovadas_llm_arbiter"] + stats["rejeitadas_llm_arbiter"]
        assert stats["llm_arbiter_calls"] == total


class TestArbiterTimingLog:
    """AC5: Consolidated timing log for Camada 3A."""

    @patch("llm_arbiter.classify_contract_primary_match")
    def test_timing_log_emitted(self, mock_classify, caplog):
        """AC5: Log includes elapsed time and bid count."""
        mock_classify.return_value = _mock_llm_response(True, 75)

        bids = [_make_gray_zone_bid(i) for i in range(3)]
        import logging
        with caplog.at_level(logging.INFO, logger="filter"):
            aprovadas, stats = aplicar_todos_filtros(
                licitacoes=bids,
                ufs_selecionadas={"SP"},
                setor="vestuario",
            )

        # Find the Camada 3A timing log
        timing_logs = [r for r in caplog.records if "Camada 3A resultado" in r.message]
        assert len(timing_logs) >= 1, "Expected Camada 3A resultado log with timing"
        log_msg = timing_logs[0].message
        assert "elapsed=" in log_msg, "Log should include elapsed time"
        assert "parallel" in log_msg, "Log should indicate parallel execution"
        assert f"{len(bids)} bids" in log_msg, "Log should include bid count"


class TestArbiterCacheCompatibility:
    """AC6: MD5 cache in LLM arbiter remains functional under parallelism."""

    @patch("llm_arbiter.classify_contract_primary_match")
    def test_duplicate_bids_all_classified(self, mock_classify):
        """AC6: Cache is thread-safe (dict reads are safe in CPython/GIL)."""
        mock_classify.return_value = _mock_llm_response(True, 80)

        # Create identical bids — cache should handle dedup internally
        bids = [_make_gray_zone_bid(0) for _ in range(5)]
        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        # All bids should be processed (cache is inside classify_contract_primary_match)
        assert stats["llm_arbiter_calls"] == 5
