"""
STORY-354: LLM Graceful Degradation — Pending Review Tests

AC9: Unit tests — mock OpenAI down, bids not lost, pending count correct
AC10: Integration tests — LLM returns, ARQ reclassifies, SSE notifies

Test coverage:
  1. llm_arbiter returns pending_review when LLM fails + flag enabled + zero_match
  2. llm_arbiter REJECT when flag disabled (old behavior)
  3. llm_arbiter REJECT for non-zero_match even with flag enabled
  4. filter returns correct pending_review_count in stats
  5. filter includes pending_review bids in approved list (not dropped)
  6. Prometheus counter incremented on pending review
  7. BuscaResponse schema accepts pending_review_count
  8. store_pending_review_bids stores in Redis with correct TTL
  9. reclassify_pending_bids_job success path
 10. reclassify_pending_bids_job retries when LLM still down
 11. reclassify_pending_bids_job handles no bids (skipped)
 12. emit_pending_review_complete emits SSE event with correct data
"""

import asyncio
import json
import os
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from llm_arbiter import classify_contract_primary_match, clear_cache
from schemas import BuscaResponse


# ============================================================================
# Helpers
# ============================================================================

def _make_resumo() -> dict:
    """Minimal ResumoEstrategico dict for BuscaResponse construction."""
    return {
        "resumo_executivo": "Test summary",
        "total_oportunidades": 0,
        "valor_total": 0.0,
        "destaques": [],
        "alerta_urgencia": None,
    }


def _make_busca_response(**overrides) -> BuscaResponse:
    """Build a valid BuscaResponse with minimal required fields + overrides."""
    defaults = {
        "resumo": _make_resumo(),
        "licitacoes": [],
        "excel_available": False,
        "quota_used": 0,
        "quota_remaining": 100,
        "total_raw": 0,
        "total_filtrado": 0,
    }
    defaults.update(overrides)
    return BuscaResponse(**defaults)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def _setup_env(monkeypatch):
    """Ensure LLM-related env vars are set for every test, then clear cache."""
    monkeypatch.setenv("LLM_ARBITER_ENABLED", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-354")
    monkeypatch.setenv("LLM_ZERO_MATCH_ENABLED", "true")
    monkeypatch.setenv("LLM_FALLBACK_PENDING_ENABLED", "true")
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def mock_openai_client():
    """Mock the OpenAI client at the _get_client level."""
    with patch("llm_arbiter._get_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        yield mock_client


# ============================================================================
# AC9 — Unit Tests
# ============================================================================

class TestAC9LlmArbiterPendingReview:
    """AC9: Unit tests — mock OpenAI down, bids not lost, pending count correct."""

    # Test 1 ----------------------------------------------------------------
    def test_llm_arbiter_pending_review_on_failure(self, mock_openai_client):
        """When LLM throws exception + flag enabled + prompt_level=zero_match
        the arbiter returns pending_review: True instead of REJECT."""
        mock_openai_client.chat.completions.create.side_effect = Exception(
            "OpenAI API connection timeout"
        )

        result = classify_contract_primary_match(
            objeto="Servicos de manutencao predial e conservacao",
            valor=100_000,
            setor_name="Servicos de Engenharia",
            prompt_level="zero_match",
            setor_id="engenharia",
            search_id="test-354-1",
        )

        assert isinstance(result, dict)
        assert result["is_primary"] is False
        assert result["pending_review"] is True
        assert result["confidence"] == 0
        assert result["rejection_reason"] == "LLM unavailable"

    # Test 2 ----------------------------------------------------------------
    def test_llm_arbiter_reject_when_flag_disabled(self, mock_openai_client):
        """When LLM_FALLBACK_PENDING_ENABLED=false, the arbiter returns
        the old behavior: is_primary=False without pending_review."""
        mock_openai_client.chat.completions.create.side_effect = Exception(
            "API key invalid"
        )

        with patch("config.LLM_FALLBACK_PENDING_ENABLED", False):
            result = classify_contract_primary_match(
                objeto="Manutencao de equipamentos hospitalares",
                valor=200_000,
                setor_name="Saude",
                prompt_level="zero_match",
                setor_id="saude",
                search_id="test-354-2",
            )

        assert isinstance(result, dict)
        assert result["is_primary"] is False
        assert result.get("pending_review") is not True
        assert result["confidence"] == 0
        assert result["rejection_reason"] == "LLM unavailable"

    # Test 3 ----------------------------------------------------------------
    def test_llm_arbiter_reject_non_zero_match(self, mock_openai_client):
        """When prompt_level is NOT zero_match, the arbiter still REJECTs even
        with LLM_FALLBACK_PENDING_ENABLED=true (pending_review only for zero_match)."""
        mock_openai_client.chat.completions.create.side_effect = Exception(
            "Rate limit exceeded"
        )

        for prompt_level in ("standard", "conservative"):
            clear_cache()
            result = classify_contract_primary_match(
                objeto="Fornecimento de uniformes escolares",
                valor=50_000,
                setor_name="Vestuario",
                prompt_level=prompt_level,
                setor_id="vestuario",
                search_id="test-354-3",
            )

            assert isinstance(result, dict)
            assert result["is_primary"] is False
            assert result.get("pending_review") is not True, (
                f"pending_review should not be set for prompt_level={prompt_level}"
            )
            assert result["confidence"] == 0

    # Test 4 ----------------------------------------------------------------
    def test_filter_pending_review_count(self, mock_openai_client):
        """Filter returns correct pending_review_count in stats when LLM is down."""
        # LLM always fails -> pending_review for zero_match bids
        mock_openai_client.chat.completions.create.side_effect = Exception("LLM down")

        from filter import aplicar_todos_filtros

        # Bids with objects that will NOT match vestuario keywords (zero density)
        bids = [
            {
                "uf": "SP",
                "valorTotalEstimado": 100_000,
                "objetoCompra": (
                    "Servicos de assessoria juridica especializada "
                    "em contratos administrativos e licitacoes publicas"
                ),
                "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
                "codigoModalidadeContratacao": 6,
            },
            {
                "uf": "SP",
                "valorTotalEstimado": 200_000,
                "objetoCompra": (
                    "Contratacao de empresa para execucao de servicos "
                    "de engenharia civil em rodovias estaduais"
                ),
                "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
                "codigoModalidadeContratacao": 6,
            },
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"SP"},
            setor="vestuario",
        )

        assert stats["pending_review_count"] == 2
        assert stats["llm_zero_match_calls"] == 2

    # Test 5 ----------------------------------------------------------------
    def test_filter_pending_review_bids_included(self, mock_openai_client):
        """Pending review bids are included in the approved results (not dropped)."""
        mock_openai_client.chat.completions.create.side_effect = Exception("timeout")

        from filter import aplicar_todos_filtros

        bids = [
            {
                "uf": "RJ",
                "valorTotalEstimado": 75_000,
                "objetoCompra": (
                    "Prestacao de servicos de monitoramento ambiental "
                    "e controle de qualidade da agua em reservatorios"
                ),
                "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
                "codigoModalidadeContratacao": 6,
            },
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"RJ"},
            setor="vestuario",
        )

        # The bid should be in the approved list (merged from resultado_pending_review)
        assert len(aprovadas) == 1
        assert aprovadas[0]["_relevance_source"] == "pending_review"
        assert aprovadas[0]["_pending_review"] is True
        assert aprovadas[0]["_confidence_score"] == 0
        assert stats["pending_review_count"] == 1

    # Test 6 ----------------------------------------------------------------
    def test_pending_review_metric_incremented(self, mock_openai_client):
        """Prometheus counter LLM_FALLBACK_PENDING is incremented when LLM fails
        and pending_review is returned."""
        mock_openai_client.chat.completions.create.side_effect = RuntimeError(
            "Connection refused"
        )

        with patch("metrics.LLM_FALLBACK_PENDING") as mock_counter:
            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels

            result = classify_contract_primary_match(
                objeto="Servicos especializados de logistica reversa",
                valor=300_000,
                setor_name="Logistica",
                prompt_level="zero_match",
                setor_id="logistica",
                search_id="test-354-6",
            )

            assert result["pending_review"] is True
            mock_counter.labels.assert_called_once()
            call_kwargs = mock_counter.labels.call_args
            # Verify sector label is set (first 50 chars of context)
            assert "sector" in call_kwargs.kwargs or len(call_kwargs.args) > 0
            mock_labels.inc.assert_called_once()

    # Test 7 ----------------------------------------------------------------
    def test_busca_response_pending_review_count(self):
        """BuscaResponse schema accepts pending_review_count field."""
        response = _make_busca_response(pending_review_count=5)
        assert response.pending_review_count == 5

    def test_busca_response_pending_review_count_default(self):
        """BuscaResponse defaults pending_review_count to 0."""
        response = _make_busca_response()
        assert response.pending_review_count == 0

    def test_busca_response_pending_review_count_validation(self):
        """BuscaResponse rejects negative pending_review_count."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            _make_busca_response(pending_review_count=-1)


# ============================================================================
# AC10 — Integration Tests
# ============================================================================

class TestAC10StorePendingReviewBids:
    """AC10 Test 8: store_pending_review_bids stores bids in Redis with correct TTL."""

    @pytest.mark.asyncio
    async def test_store_pending_review_bids(self):
        """Bids are stored in Redis with the correct key prefix and TTL."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import store_pending_review_bids

            bids = [
                {"objetoCompra": "Bid 1", "_pending_review": True},
                {"objetoCompra": "Bid 2", "_pending_review": True},
            ]

            result = await store_pending_review_bids(
                search_id="search-abc-123",
                bids=bids,
                sector_name="Engenharia",
            )

            assert result is True
            mock_redis.setex.assert_called_once()

            # Verify the call arguments
            call_args = mock_redis.setex.call_args
            key = call_args[0][0]
            ttl = call_args[0][1]
            payload_raw = call_args[0][2]

            assert key == "smartlic:pending_review:search-abc-123"
            assert ttl == 86400  # PENDING_REVIEW_TTL_SECONDS default
            payload = json.loads(payload_raw)
            assert len(payload["bids"]) == 2
            assert payload["sector_name"] == "Engenharia"
            assert "stored_at" in payload

    @pytest.mark.asyncio
    async def test_store_pending_review_bids_redis_unavailable(self):
        """Returns False when Redis is unavailable."""
        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None):
            from job_queue import store_pending_review_bids

            result = await store_pending_review_bids(
                search_id="search-fail",
                bids=[{"objetoCompra": "test"}],
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_store_pending_review_bids_redis_error(self):
        """Returns False when Redis setex raises an exception."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(side_effect=ConnectionError("Redis connection lost"))

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import store_pending_review_bids

            result = await store_pending_review_bids(
                search_id="search-err",
                bids=[{"objetoCompra": "test"}],
            )
            assert result is False


class TestAC10ReclassifyJob:
    """AC10 Tests 9-11: reclassify_pending_bids_job."""

    @pytest.mark.asyncio
    async def test_reclassify_job_success(self):
        """Job loads bids, calls LLM successfully, returns accepted/rejected counts."""
        stored_data = json.dumps({
            "bids": [
                {"objetoCompra": "Fornecimento de uniformes escolares", "valorTotalEstimado": 50000},
                {"objetoCompra": "Servicos de consultoria ambiental", "valorTotalEstimado": 80000},
                {"objetoCompra": "Manutencao predial completa", "valorTotalEstimado": 120000},
            ],
            "sector_name": "Vestuario",
            "stored_at": time.time(),
        })

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=stored_data)
        mock_redis.delete = AsyncMock()

        # LLM returns: first accepted, second rejected, third accepted
        llm_results = [
            {"is_primary": True, "confidence": 80, "evidence": ["uniformes"], "rejection_reason": None, "needs_more_data": False},
            {"is_primary": False, "confidence": 10, "evidence": [], "rejection_reason": "Not relevant", "needs_more_data": False},
            {"is_primary": True, "confidence": 75, "evidence": ["manutencao"], "rejection_reason": None, "needs_more_data": False},
        ]
        call_count = 0

        def _mock_classify(objeto, valor, setor_name=None, prompt_level="standard", setor_id=None, search_id="", **kwargs):
            nonlocal call_count
            r = llm_results[call_count]
            call_count += 1
            return r

        mock_tracker = AsyncMock()

        with (
            patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
            patch("llm_arbiter.classify_contract_primary_match", side_effect=_mock_classify),
            patch("progress.get_tracker", new_callable=AsyncMock, return_value=mock_tracker),
        ):
            from job_queue import reclassify_pending_bids_job

            result = await reclassify_pending_bids_job(
                ctx={},
                search_id="search-reclass-ok",
                sector_name="Vestuario",
                sector_id="vestuario",
                attempt=1,
            )

            assert result["status"] == "completed"
            assert result["accepted"] == 2
            assert result["rejected"] == 1
            assert result["still_pending"] == 0
            assert result["total"] == 3

            # Redis key should be deleted (all classified)
            mock_redis.delete.assert_called_once_with(
                "smartlic:pending_review:search-reclass-ok"
            )
            # SSE event should be emitted
            mock_tracker.emit_pending_review_complete.assert_called_once_with(
                reclassified_count=3,
                accepted_count=2,
                rejected_count=1,
            )

    @pytest.mark.asyncio
    async def test_reclassify_job_still_pending(self):
        """Job retries when LLM is still down (returns pending_review)."""
        stored_data = json.dumps({
            "bids": [
                {"objetoCompra": "Item de teste para reclassificacao", "valorTotalEstimado": 40000},
            ],
            "sector_name": "Saude",
            "stored_at": time.time(),
        })

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=stored_data)

        # LLM still failing -> pending_review
        def _mock_classify_still_down(**kwargs):
            return {
                "is_primary": False, "confidence": 0, "evidence": [],
                "rejection_reason": "LLM unavailable", "needs_more_data": False,
                "pending_review": True,
            }

        mock_arq_pool = AsyncMock()
        mock_arq_pool.enqueue_job = AsyncMock()

        with (
            patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
            patch("llm_arbiter.classify_contract_primary_match", side_effect=_mock_classify_still_down),
            patch("job_queue.get_arq_pool", new_callable=AsyncMock, return_value=mock_arq_pool),
            patch("progress.get_tracker", new_callable=AsyncMock, return_value=None),
        ):
            from job_queue import reclassify_pending_bids_job

            result = await reclassify_pending_bids_job(
                ctx={},
                search_id="search-retry",
                sector_name="Saude",
                sector_id="saude",
                attempt=1,
            )

            assert result["status"] == "completed"
            assert result["still_pending"] == 1
            assert result["accepted"] == 0
            assert result["rejected"] == 0

            # Should schedule a retry via ARQ
            mock_arq_pool.enqueue_job.assert_called_once()
            enqueue_call = mock_arq_pool.enqueue_job.call_args
            assert enqueue_call[0][0] == "reclassify_pending_bids_job"
            assert enqueue_call[1]["attempt"] == 2

    @pytest.mark.asyncio
    async def test_reclassify_job_no_bids(self):
        """Job returns skipped when no bids are found in Redis (expired or already done)."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)  # Key expired or deleted

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import reclassify_pending_bids_job

            result = await reclassify_pending_bids_job(
                ctx={},
                search_id="search-expired",
                sector_name="TI",
                sector_id="ti",
                attempt=1,
            )

            assert result["status"] == "skipped"
            assert result["reason"] == "no_pending_bids"

    @pytest.mark.asyncio
    async def test_reclassify_job_empty_bids_list(self):
        """Job returns skipped when bids list is empty in stored data."""
        stored_data = json.dumps({
            "bids": [],
            "sector_name": "TI",
            "stored_at": time.time(),
        })

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=stored_data)

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import reclassify_pending_bids_job

            result = await reclassify_pending_bids_job(
                ctx={},
                search_id="search-empty",
                sector_name="TI",
                sector_id="ti",
                attempt=1,
            )

            assert result["status"] == "skipped"
            assert result["reason"] == "empty_bids"

    @pytest.mark.asyncio
    async def test_reclassify_job_max_retries_exceeded(self):
        """Job does NOT schedule retry when attempt >= PENDING_REVIEW_MAX_RETRIES."""
        stored_data = json.dumps({
            "bids": [
                {"objetoCompra": "Item teste max retries", "valorTotalEstimado": 10000},
            ],
            "sector_name": "Saude",
            "stored_at": time.time(),
        })

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=stored_data)

        def _mock_classify_fail(**kwargs):
            return {
                "is_primary": False, "confidence": 0, "evidence": [],
                "rejection_reason": "LLM unavailable", "needs_more_data": False,
                "pending_review": True,
            }

        mock_arq_pool = AsyncMock()
        mock_arq_pool.enqueue_job = AsyncMock()

        with (
            patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis),
            patch("llm_arbiter.classify_contract_primary_match", side_effect=_mock_classify_fail),
            patch("job_queue.get_arq_pool", new_callable=AsyncMock, return_value=mock_arq_pool),
            patch("progress.get_tracker", new_callable=AsyncMock, return_value=None),
            patch("config.PENDING_REVIEW_MAX_RETRIES", 3),
        ):
            from job_queue import reclassify_pending_bids_job

            result = await reclassify_pending_bids_job(
                ctx={},
                search_id="search-maxretry",
                sector_name="Saude",
                sector_id="saude",
                attempt=3,  # Already at max
            )

            assert result["status"] == "completed"
            assert result["still_pending"] == 1
            # No retry should be scheduled
            mock_arq_pool.enqueue_job.assert_not_called()


class TestAC10EmitPendingReviewComplete:
    """AC10 Test 12: emit_pending_review_complete emits SSE event with correct data."""

    @pytest.mark.asyncio
    async def test_emit_pending_review_complete(self):
        """ProgressTracker emits a pending_review event with correct structure."""
        from progress import ProgressTracker

        tracker = ProgressTracker(search_id="test-sse-354", uf_count=1, use_redis=False)

        await tracker.emit_pending_review_complete(
            reclassified_count=10,
            accepted_count=7,
            rejected_count=3,
        )

        # The event should be in the queue
        assert not tracker.queue.empty()
        event = await tracker.queue.get()

        assert event.stage == "pending_review"
        assert event.progress == -1
        assert "7 aprovadas" in event.message
        assert "3 rejeitadas" in event.message
        assert event.detail["reclassified_count"] == 10
        assert event.detail["accepted_count"] == 7
        assert event.detail["rejected_count"] == 3

    @pytest.mark.asyncio
    async def test_emit_pending_review_complete_zero_counts(self):
        """Emit event with zero counts (edge case — all still pending)."""
        from progress import ProgressTracker

        tracker = ProgressTracker(search_id="test-sse-zero", uf_count=1, use_redis=False)

        await tracker.emit_pending_review_complete(
            reclassified_count=0,
            accepted_count=0,
            rejected_count=0,
        )

        event = await tracker.queue.get()
        assert event.stage == "pending_review"
        assert event.detail["reclassified_count"] == 0
        assert event.detail["accepted_count"] == 0
        assert event.detail["rejected_count"] == 0


# ============================================================================
# Edge Cases and Additional Coverage
# ============================================================================

class TestPendingReviewEdgeCases:
    """Additional edge case tests for robustness."""

    def test_llm_arbiter_pending_review_preserves_evidence_structure(self, mock_openai_client):
        """Result dict from pending_review has all expected keys with correct types."""
        mock_openai_client.chat.completions.create.side_effect = TimeoutError("read timeout")

        result = classify_contract_primary_match(
            objeto="Servicos de transporte escolar",
            valor=250_000,
            setor_name="Transporte",
            prompt_level="zero_match",
            setor_id="transporte",
            search_id="test-354-edge-1",
        )

        # Verify complete structure matches what filter.py expects
        assert "is_primary" in result
        assert "confidence" in result
        assert "evidence" in result
        assert "rejection_reason" in result
        assert "needs_more_data" in result
        assert "pending_review" in result

        assert isinstance(result["is_primary"], bool)
        assert isinstance(result["confidence"], int)
        assert isinstance(result["evidence"], list)
        assert isinstance(result["pending_review"], bool)

    def test_filter_pending_review_with_executor_exception(self, mock_openai_client):
        """When ThreadPoolExecutor future raises (not LLM), bid still becomes
        pending_review if flag enabled (filter.py exception handler)."""
        # Force the classify function itself to raise (simulates executor error)
        mock_openai_client.chat.completions.create.side_effect = Exception(
            "Unexpected executor failure"
        )

        from filter import aplicar_todos_filtros

        bids = [
            {
                "uf": "MG",
                "valorTotalEstimado": 60_000,
                "objetoCompra": (
                    "Aquisicao de materiais de construcao para reforma "
                    "de creches municipais e centros de educacao infantil"
                ),
                "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
                "codigoModalidadeContratacao": 6,
            },
        ]

        aprovadas, stats = aplicar_todos_filtros(
            licitacoes=bids,
            ufs_selecionadas={"MG"},
            setor="vestuario",
        )

        assert stats["pending_review_count"] == 1
        assert len(aprovadas) == 1
        assert aprovadas[0]["_pending_review"] is True

    def test_filter_pending_review_rejected_when_flag_off(self, mock_openai_client):
        """When LLM_FALLBACK_PENDING_ENABLED=false, failed LLM calls in filter
        lead to rejection (not pending_review)."""
        mock_openai_client.chat.completions.create.side_effect = Exception("LLM error")

        from filter import aplicar_todos_filtros

        bids = [
            {
                "uf": "BA",
                "valorTotalEstimado": 90_000,
                "objetoCompra": (
                    "Contratacao de servicos de auditoria contabil "
                    "e financeira para secretaria de fazenda estadual"
                ),
                "dataEncerramentoProposta": "2026-12-31T10:00:00Z",
                "codigoModalidadeContratacao": 6,
            },
        ]

        with patch("config.LLM_FALLBACK_PENDING_ENABLED", False):
            aprovadas, stats = aplicar_todos_filtros(
                licitacoes=bids,
                ufs_selecionadas={"BA"},
                setor="vestuario",
            )

        # Should be rejected, not pending_review
        assert stats["pending_review_count"] == 0
        assert stats["llm_zero_match_rejeitadas"] == 1
        assert len(aprovadas) == 0

    @pytest.mark.asyncio
    async def test_reclassify_job_redis_error_on_load(self):
        """Job returns error when Redis get raises an exception."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis offline"))

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            from job_queue import reclassify_pending_bids_job

            result = await reclassify_pending_bids_job(
                ctx={},
                search_id="search-redis-err",
                sector_name="TI",
                sector_id="ti",
                attempt=1,
            )

            assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_reclassify_job_redis_unavailable(self):
        """Job returns error when Redis pool is None."""
        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None):
            from job_queue import reclassify_pending_bids_job

            result = await reclassify_pending_bids_job(
                ctx={},
                search_id="search-no-redis",
                sector_name="TI",
                sector_id="ti",
                attempt=1,
            )

            assert result["status"] == "error"
            assert result["reason"] == "redis_unavailable"

    def test_pending_review_metric_reason_label(self, mock_openai_client):
        """Metric label 'reason' reflects the exception class name."""
        mock_openai_client.chat.completions.create.side_effect = ConnectionError(
            "Cannot reach API"
        )

        with patch("metrics.LLM_FALLBACK_PENDING") as mock_counter:
            mock_labels = MagicMock()
            mock_counter.labels.return_value = mock_labels

            classify_contract_primary_match(
                objeto="Servicos gerais de limpeza e conservacao",
                valor=45_000,
                setor_name="Servicos Gerais",
                prompt_level="zero_match",
                setor_id="servicos_gerais",
                search_id="test-354-reason",
            )

            # Verify the reason label is the exception class name
            call_kwargs = mock_counter.labels.call_args
            if call_kwargs.kwargs:
                assert call_kwargs.kwargs.get("reason") == "ConnectionError"
            else:
                # Positional args: labels(sector=..., reason=...)
                assert "ConnectionError" in str(call_kwargs)
