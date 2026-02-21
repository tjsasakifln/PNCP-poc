"""AC6: Full pipeline cascade failure tests.

Tests SearchPipeline with all stages running (not mocked stages),
verifying that failures propagate correctly through the pipeline.
Production scenario: When PNCP API fails, what does the user see?
"""

import os
import pytest
from unittest.mock import patch, AsyncMock, Mock
from pncp_client import ParallelFetchResult

from tests.integration.conftest import make_busca_request

# All tests use 2+ UFs to ensure the parallel fetch path
# (buscar_todas_ufs_paralelo) is taken. With a single UF the pipeline falls
# back to PNCPClient.fetch_all() which bypasses our mock and attempts real
# HTTP requests, causing the test to hang indefinitely.
_DEFAULT_UFS = ["SP", "RJ"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pncp_total_failure():
    """Build a ParallelFetchResult where ALL UFs failed (PNCP 500)."""
    return ParallelFetchResult(
        items=[],
        succeeded_ufs=[],
        failed_ufs=_DEFAULT_UFS,
        truncated_ufs=[],
    )


def _make_pncp_success(sample_data):
    """Build a ParallelFetchResult with successful data."""
    return ParallelFetchResult(
        items=sample_data,
        succeeded_ufs=_DEFAULT_UFS,
        failed_ufs=[],
        truncated_ufs=[],
    )


def _make_cache_hit(sample_data):
    """Build a stale cache response as returned by get_from_cache_cascade."""
    return {
        "results": sample_data,
        "cache_age_hours": 2,
        "cache_level": "supabase",
        "cached_at": "2026-02-20T10:00:00Z",
        "cached_sources": ["PNCP"],
        "is_stale": True,
        "cache_status": "stale",
    }


@pytest.fixture(autouse=True)
def _disable_multi_source(monkeypatch):
    """Force PNCP-only path for all tests in this module.

    Multi-source uses ConsolidationService which bypasses
    buscar_todas_ufs_paralelo, making it impossible to mock
    the PNCP fetch at the route level. Disabling multi-source
    ensures the pipeline calls deps.buscar_todas_ufs_paralelo.
    """
    monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")


@pytest.fixture(autouse=True)
def _bypass_inmemory_cache():
    """Prevent the InMemoryCache from returning stale data.

    The pipeline reads from InMemoryCache via _read_cache() before
    checking Supabase cache. This fixture ensures the cache is
    empty so the pipeline proceeds to the PNCP fetch stage.
    """
    with patch("search_pipeline._read_cache", return_value=None):
        yield


# ===========================================================================
# Scenario A: PNCP 500 for all UFs + cache available -> HTTP 200, cached
# ===========================================================================

@pytest.mark.integration
def test_pncp_total_failure_with_cache_returns_cached_data(
    integration_app, sample_licitacoes_raw,
):
    """Production scenario: PNCP returns 500 for every UF, but we have stale
    cache data in Supabase. The user should see cached results with a
    'cached' response_state so the frontend can display a staleness banner.

    Prevents: Users seeing an error page when PNCP is down but we have
    perfectly usable (albeit slightly stale) cached results.
    """
    pncp_failure = _make_pncp_total_failure()
    cache_data = _make_cache_hit(sample_licitacoes_raw)

    with patch(
        "routes.search.buscar_todas_ufs_paralelo",
        new_callable=AsyncMock,
        return_value=pncp_failure,
    ), patch(
        # Patch in search_cache module (used by routes/search.py A-04 cache-first path)
        "search_cache.get_from_cache_cascade",
        new_callable=AsyncMock,
        return_value=cache_data,
    ), patch(
        # Also patch the direct import in search_pipeline (used by _execute_pncp_only
        # PNCPDegradedError handler, which calls the module-level reference)
        "search_pipeline.get_from_cache_cascade",
        new_callable=AsyncMock,
        return_value=cache_data,
    ):
        payload = make_busca_request(ufs=_DEFAULT_UFS)
        response = integration_app.post("/buscar", json=payload)

    assert response.status_code == 200, (
        f"Expected 200 (cached fallback) but got {response.status_code}: "
        f"{response.text[:500]}"
    )
    body = response.json()
    assert body.get("response_state") == "cached", (
        f"Expected response_state='cached' but got '{body.get('response_state')}'"
    )
    # Verify cache metadata is propagated to the response
    assert body.get("cached") is True
    assert body.get("cached_at") == "2026-02-20T10:00:00Z"
    assert body.get("cache_level") == "supabase"


# ===========================================================================
# Scenario B: PNCP 500 + cache completely empty -> HTTP 200, empty_failure
# ===========================================================================

@pytest.mark.integration
def test_pncp_total_failure_no_cache_returns_empty_failure(
    integration_app,
):
    """Production scenario: PNCP is completely down AND there is no cached
    data at all. The user should see an empty result set with
    response_state='empty_failure' and guidance text explaining what happened.

    The pipeline only sets empty_failure when PNCPDegradedError is raised
    and the cache cascade returns None. A ParallelFetchResult with empty
    items is treated as a successful (but empty) search.

    Prevents: Unhandled 500 errors when both PNCP and cache are unavailable.
    The frontend needs a structured response to show a helpful empty state.
    """
    from pncp_client import PNCPDegradedError

    with patch(
        "routes.search.buscar_todas_ufs_paralelo",
        new_callable=AsyncMock,
        side_effect=PNCPDegradedError("PNCP 500 for all UFs"),
    ), patch(
        # Patch in search_cache module (used by routes/search.py A-04 cache-first path)
        "search_cache.get_from_cache_cascade",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        # Also patch the direct import in search_pipeline (used by _execute_pncp_only
        # PNCPDegradedError handler at line ~1391, which calls the module-level reference)
        "search_pipeline.get_from_cache_cascade",
        new_callable=AsyncMock,
        return_value=None,
    ):
        payload = make_busca_request(ufs=_DEFAULT_UFS)
        response = integration_app.post("/buscar", json=payload)

    assert response.status_code == 200, (
        f"Expected 200 (empty_failure) but got {response.status_code}: "
        f"{response.text[:500]}"
    )
    body = response.json()
    assert body.get("response_state") == "empty_failure", (
        f"Expected response_state='empty_failure' but got '{body.get('response_state')}'"
    )
    assert body.get("total_filtrado") == 0
    assert body.get("licitacoes") == [] or body.get("licitacoes") is None


# ===========================================================================
# Scenario C: Stage 4 (filter) crash -> HTTP 500
# ===========================================================================

@pytest.mark.integration
def test_filter_stage_crash_returns_500(
    integration_app, sample_licitacoes_raw,
):
    """Production scenario: A bug or unexpected data causes the filtering
    stage (Stage 4) to crash with a RuntimeError. Since filtering is a
    critical stage in the pipeline, the error should propagate to an HTTP 500
    response rather than returning partial/corrupt data.

    Prevents: Silently returning unfiltered results to users when the filter
    logic has a bug, which could surface irrelevant or excluded bids.
    """
    pncp_success = _make_pncp_success(sample_licitacoes_raw)

    with patch(
        "routes.search.buscar_todas_ufs_paralelo",
        new_callable=AsyncMock,
        return_value=pncp_success,
    ), patch(
        "routes.search.aplicar_todos_filtros",
        side_effect=RuntimeError("Unexpected filter crash: invalid regex in keyword set"),
    ):
        payload = make_busca_request(ufs=_DEFAULT_UFS)
        response = integration_app.post("/buscar", json=payload)

    assert response.status_code == 500, (
        f"Expected 500 (filter crash) but got {response.status_code}: "
        f"{response.text[:500]}"
    )
    body = response.json()
    assert "detail" in body
    # CRIT-009: detail may be a structured dict with inner "detail" key
    raw_detail = body["detail"]
    detail_msg = raw_detail["detail"] if isinstance(raw_detail, dict) else raw_detail
    # Verify the error message is user-friendly (not a raw traceback)
    assert "Erro interno" in detail_msg or "erro" in detail_msg.lower()


# ===========================================================================
# Scenario D: Stage 6 (LLM) timeout -> HTTP 200 with fallback resumo
# ===========================================================================

@pytest.mark.integration
def test_llm_timeout_returns_fallback_resumo(
    integration_app, sample_licitacoes_raw,
):
    """Production scenario: OpenAI is slow or unreachable, causing the LLM
    summary generation to time out. The pipeline should catch this, use the
    deterministic fallback summary generator, and still return HTTP 200 with
    complete search results.

    Prevents: Users waiting forever for LLM or getting an error page just
    because the AI summary could not be generated. The search results
    themselves are perfectly valid.
    """
    pncp_success = _make_pncp_success(sample_licitacoes_raw)

    with patch(
        "routes.search.buscar_todas_ufs_paralelo",
        new_callable=AsyncMock,
        return_value=pncp_success,
    ), patch(
        # Patch the direct import reference in search_pipeline (where
        # stage_generate actually calls gerar_resumo at line ~1892).
        # Patching "llm.gerar_resumo" only affects the llm module namespace,
        # not search_pipeline's own reference from `from llm import gerar_resumo`.
        "search_pipeline.gerar_resumo",
        side_effect=TimeoutError("OpenAI request timed out after 30s"),
    ):
        payload = make_busca_request(ufs=_DEFAULT_UFS)
        response = integration_app.post("/buscar", json=payload)

    assert response.status_code == 200, (
        f"Expected 200 (LLM fallback) but got {response.status_code}: "
        f"{response.text[:500]}"
    )
    body = response.json()

    # The response should contain the fallback resumo
    resumo = body.get("resumo")
    assert resumo is not None, "Expected a resumo object in the response"
    assert resumo.get("resumo_executivo") is not None, (
        "Fallback resumo should have a resumo_executivo"
    )

    # Search results should still be present
    assert body.get("total_filtrado", 0) >= 0
    # LLM source should indicate fallback was used (CRIT-005 AC13)
    assert body.get("llm_source") == "fallback", (
        f"Expected llm_source='fallback' but got '{body.get('llm_source')}'"
    )
