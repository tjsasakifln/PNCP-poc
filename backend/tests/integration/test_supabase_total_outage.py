"""AC8: Supabase total outage resilience test.

Tests that search works (degraded) when ALL Supabase operations fail.
Production scenario: Supabase down -> search must still return results from PNCP.
"""

import pytest
from unittest.mock import patch, AsyncMock
from pncp_client import ParallelFetchResult

from tests.integration.conftest import make_busca_request


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pncp_success(sample_data):
    """Build a ParallelFetchResult with successful data."""
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
# Test: Supabase total outage -- search still returns PNCP results
# ===========================================================================

@pytest.mark.integration
def test_supabase_outage_search_returns_pncp_results(
    integration_app, sample_licitacoes_raw, mock_supabase_client,
):
    """Production scenario: Supabase is completely down. Every DB operation
    (cache read, cache write, session registration, session status update)
    fails with an exception. Despite this, the search pipeline should still
    succeed because the core value (PNCP results) does not depend on Supabase.

    The pipeline is designed with graceful degradation at every Supabase
    touchpoint:
    - quota.register_search_session: failure sets session_id=None, continues
    - search_cache.save_to_cache: failure is logged and swallowed
    - search_cache.get_from_cache_cascade: failure is caught, no cache used
    - quota.update_search_session_status: failure is fire-and-forget

    Prevents: A Supabase outage causing a complete search outage when the
    actual data source (PNCP) is perfectly healthy. Users should still be
    able to find procurement opportunities.
    """
    # Make the mock Supabase client fail on all operations
    mock_supabase_client.fail_all(Exception("Supabase totally unavailable"))

    pncp_success = _make_pncp_success(sample_licitacoes_raw)

    with patch(
        "routes.search.buscar_todas_ufs_paralelo",
        new_callable=AsyncMock,
        return_value=pncp_success,
    ), patch(
        "search_cache.save_to_cache",
        new_callable=AsyncMock,
        side_effect=Exception("Supabase cache write failed"),
    ), patch(
        "search_cache.get_from_cache_cascade",
        new_callable=AsyncMock,
        side_effect=Exception("Supabase cache read failed"),
    ), patch(
        "quota.register_search_session",
        new_callable=AsyncMock,
        side_effect=Exception("Supabase session registration failed"),
    ), patch(
        "quota.update_search_session_status",
        new_callable=AsyncMock,
        side_effect=Exception("Supabase session update failed"),
    ):
        payload = make_busca_request(ufs=["SP", "RJ", "MG"])
        response = integration_app.post("/buscar", json=payload)

    assert response.status_code == 200, (
        f"Expected 200 (degraded but functional) but got {response.status_code}: "
        f"{response.text[:500]}"
    )

    body = response.json()

    # Core data must be present -- PNCP results should flow through
    licitacoes = body.get("licitacoes")
    assert licitacoes is not None, (
        "Expected licitacoes in response even during Supabase outage"
    )

    # Verify we got actual search results (not an empty degraded response)
    total_raw = body.get("total_raw", 0)
    assert total_raw > 0, (
        f"Expected total_raw > 0 (PNCP data should be present) but got {total_raw}"
    )


@pytest.mark.integration
def test_supabase_outage_session_id_is_none(
    integration_app, sample_licitacoes_raw, mock_supabase_client,
):
    """Production scenario: When Supabase is down, register_search_session
    fails, so session_id is set to None. The pipeline should continue
    without session tracking. This test verifies the session registration
    failure is handled gracefully.

    Prevents: The pipeline crashing when it tries to use a None session_id
    in subsequent update_search_session_status calls. All session-related
    operations must be guarded by 'if ctx.session_id'.
    """
    mock_supabase_client.fail_all(Exception("Supabase totally unavailable"))

    pncp_success = _make_pncp_success(sample_licitacoes_raw)

    session_register_mock = AsyncMock(
        side_effect=Exception("Supabase session registration failed"),
    )
    session_update_mock = AsyncMock(
        side_effect=Exception("Supabase session update failed"),
    )

    with patch(
        "routes.search.buscar_todas_ufs_paralelo",
        new_callable=AsyncMock,
        return_value=pncp_success,
    ), patch(
        "search_cache.save_to_cache",
        new_callable=AsyncMock,
        side_effect=Exception("Supabase unavailable"),
    ), patch(
        "search_cache.get_from_cache_cascade",
        new_callable=AsyncMock,
        side_effect=Exception("Supabase unavailable"),
    ), patch(
        "quota.register_search_session",
        session_register_mock,
    ), patch(
        "quota.update_search_session_status",
        session_update_mock,
    ):
        payload = make_busca_request(ufs=["SP", "RJ", "MG"])
        response = integration_app.post("/buscar", json=payload)

    # Search should still succeed
    assert response.status_code == 200, (
        f"Expected 200 but got {response.status_code}: {response.text[:500]}"
    )

    # register_search_session was called (and failed gracefully)
    session_register_mock.assert_called_once()

    body = response.json()
    # Despite session failure, results should be complete
    assert body.get("resumo") is not None, (
        "Expected resumo even without session tracking"
    )


@pytest.mark.integration
def test_supabase_outage_cache_write_failure_does_not_block(
    integration_app, sample_licitacoes_raw, mock_supabase_client,
):
    """Production scenario: PNCP returns results successfully, but writing
    those results to the Supabase cache fails. The user should still see
    the results. The cache write is a non-critical side effect.

    Prevents: A cache write failure (e.g., Supabase row-level security
    error, network timeout) causing the entire search to fail after we
    already have the data the user needs.
    """
    mock_supabase_client.fail_all(Exception("Supabase totally unavailable"))

    pncp_success = _make_pncp_success(sample_licitacoes_raw)

    cache_save_mock = AsyncMock(
        side_effect=Exception("Supabase cache write failed"),
    )

    with patch(
        "routes.search.buscar_todas_ufs_paralelo",
        new_callable=AsyncMock,
        return_value=pncp_success,
    ), patch(
        "search_cache.save_to_cache",
        cache_save_mock,
    ), patch(
        "search_cache.get_from_cache_cascade",
        new_callable=AsyncMock,
        side_effect=Exception("Supabase unavailable"),
    ), patch(
        "quota.register_search_session",
        new_callable=AsyncMock,
        side_effect=Exception("Supabase unavailable"),
    ), patch(
        "quota.update_search_session_status",
        new_callable=AsyncMock,
        side_effect=Exception("Supabase unavailable"),
    ):
        payload = make_busca_request(ufs=["SP", "RJ", "MG"])
        response = integration_app.post("/buscar", json=payload)

    assert response.status_code == 200, (
        f"Expected 200 but got {response.status_code}: {response.text[:500]}"
    )

    body = response.json()

    # Results are present despite cache write failure
    assert body.get("total_raw", 0) > 0, (
        "Expected raw results from PNCP despite cache write failure"
    )
    assert body.get("resumo") is not None, (
        "Expected resumo despite Supabase outage"
    )
    assert body.get("licitacoes") is not None, (
        "Expected licitacoes list despite Supabase outage"
    )
