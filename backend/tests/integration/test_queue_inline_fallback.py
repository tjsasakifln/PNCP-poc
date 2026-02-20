"""AC7: Queue dispatch failure with inline fallback.

Tests that when is_queue_available() returns False, the pipeline
executes LLM and Excel generation inline (synchronously) instead
of dispatching to ARQ background jobs.
Production scenario: Redis/ARQ unavailable -> user still gets full results.
"""

import pytest
from unittest.mock import patch, AsyncMock
from pncp_client import ParallelFetchResult

from tests.integration.conftest import make_busca_request


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pncp_success(sample_data):
    """Build a ParallelFetchResult with successful data from all UFs."""
    return ParallelFetchResult(
        items=sample_data,
        succeeded_ufs=["SP", "RJ", "MG"],
        failed_ufs=[],
        truncated_ufs=[],
    )


@pytest.fixture(autouse=True)
def _disable_multi_source(monkeypatch):
    """Force PNCP-only path for all tests in this module."""
    monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")


@pytest.fixture(autouse=True)
def _bypass_inmemory_cache():
    """Prevent InMemoryCache from returning stale data between tests."""
    with patch("search_pipeline._read_cache", return_value=None):
        yield


# ===========================================================================
# Test: Queue unavailable -> inline LLM + Excel execution
# ===========================================================================

@pytest.mark.integration
def test_queue_unavailable_executes_inline_with_full_results(
    integration_app, sample_licitacoes_raw,
):
    """Production scenario: Redis is down or ARQ worker pool is unreachable,
    so is_queue_available() returns False. The pipeline must fall back to
    inline (synchronous) execution of both the LLM summary and Excel
    generation stages, returning a complete response in a single request.

    Prevents: Users getting a response with llm_status='processing' and
    excel_status='processing' that never resolves because there is no
    background worker to pick up the jobs. With inline fallback, the user
    gets everything in one request (at the cost of higher latency).
    """
    pncp_success = _make_pncp_success(sample_licitacoes_raw)

    with patch(
        "routes.search.buscar_todas_ufs_paralelo",
        new_callable=AsyncMock,
        return_value=pncp_success,
    ):
        payload = make_busca_request(ufs=["SP", "RJ", "MG"])
        response = integration_app.post("/buscar", json=payload)

    assert response.status_code == 200, (
        f"Expected 200 but got {response.status_code}: {response.text[:500]}"
    )
    body = response.json()

    # -----------------------------------------------------------------------
    # Core assertion: Resumo was generated inline (not deferred to queue)
    # -----------------------------------------------------------------------
    resumo = body.get("resumo")
    assert resumo is not None, (
        "Expected a resumo object -- inline LLM should have generated one"
    )
    assert resumo.get("resumo_executivo") is not None, (
        "Resumo should have a resumo_executivo when generated inline"
    )

    # -----------------------------------------------------------------------
    # LLM status must NOT be 'processing' (which indicates queue dispatch)
    # -----------------------------------------------------------------------
    llm_status = body.get("llm_status")
    assert llm_status != "processing", (
        f"llm_status should not be 'processing' in inline mode, got '{llm_status}'"
    )

    # -----------------------------------------------------------------------
    # Excel must have been generated inline (download_url present)
    # -----------------------------------------------------------------------
    excel_status = body.get("excel_status")
    assert excel_status != "processing", (
        f"excel_status should not be 'processing' in inline mode, got '{excel_status}'"
    )

    download_url = body.get("download_url")
    assert download_url is not None, (
        "Expected download_url to be present -- Excel should have been "
        "generated inline when queue is unavailable"
    )

    # -----------------------------------------------------------------------
    # Licitacoes should be present in the response
    # -----------------------------------------------------------------------
    licitacoes = body.get("licitacoes")
    assert licitacoes is not None, "Expected licitacoes in response"
    assert len(licitacoes) > 0, (
        "Expected at least 1 licitacao in response after filtering"
    )


@pytest.mark.integration
def test_queue_unavailable_does_not_enqueue_jobs(
    integration_app, sample_licitacoes_raw,
):
    """Production scenario: When the queue is unavailable, the pipeline
    should never attempt to enqueue background jobs -- doing so would either
    fail silently or raise an error. This test verifies that enqueue_job
    is NOT called when is_queue_available() returns False.

    Prevents: Wasted RPC calls to a dead queue, potential error noise in
    logs, and the risk of jobs being enqueued to a queue that will never
    process them.
    """
    pncp_success = _make_pncp_success(sample_licitacoes_raw)

    enqueue_mock = AsyncMock(return_value=None)

    with patch(
        "routes.search.buscar_todas_ufs_paralelo",
        new_callable=AsyncMock,
        return_value=pncp_success,
    ), patch(
        "job_queue.enqueue_job",
        enqueue_mock,
    ):
        payload = make_busca_request(ufs=["SP", "RJ", "MG"])
        response = integration_app.post("/buscar", json=payload)

    assert response.status_code == 200
    enqueue_mock.assert_not_called(), (
        "enqueue_job should NOT have been called when queue is unavailable"
    )


@pytest.mark.integration
def test_inline_response_contains_complete_data(
    integration_app, sample_licitacoes_raw,
):
    """Production scenario: Verify that inline execution produces a response
    that is structurally identical to what the queue path would eventually
    deliver. The response must contain all key fields: resumo, licitacoes,
    filter_stats, quota info, and coverage metadata.

    Prevents: Inline fallback returning a partial or differently-structured
    response that confuses the frontend rendering logic.
    """
    pncp_success = _make_pncp_success(sample_licitacoes_raw)

    with patch(
        "routes.search.buscar_todas_ufs_paralelo",
        new_callable=AsyncMock,
        return_value=pncp_success,
    ):
        payload = make_busca_request(ufs=["SP", "RJ", "MG"])
        response = integration_app.post("/buscar", json=payload)

    assert response.status_code == 200
    body = response.json()

    # Structural completeness checks
    assert "resumo" in body, "Missing 'resumo' field"
    assert "licitacoes" in body, "Missing 'licitacoes' field"
    assert "total_raw" in body, "Missing 'total_raw' field"
    assert "total_filtrado" in body, "Missing 'total_filtrado' field"
    assert "filter_stats" in body, "Missing 'filter_stats' field"
    assert "quota_used" in body, "Missing 'quota_used' field"
    assert "quota_remaining" in body, "Missing 'quota_remaining' field"

    # Verify numeric consistency
    assert body["total_raw"] >= body["total_filtrado"], (
        f"total_raw ({body['total_raw']}) should be >= total_filtrado ({body['total_filtrado']})"
    )

    # Resumo should reflect actual data
    resumo = body["resumo"]
    assert resumo["total_oportunidades"] == body["total_filtrado"], (
        f"Resumo total_oportunidades ({resumo['total_oportunidades']}) "
        f"should match total_filtrado ({body['total_filtrado']})"
    )
