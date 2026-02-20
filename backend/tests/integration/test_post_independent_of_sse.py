"""AC10: POST /buscar works independently of SSE connection.

Verifies that the POST /buscar endpoint returns complete results
even when the client never opens an SSE connection.
Production scenario: Mobile client or bot that only uses REST, no EventSource.
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from types import SimpleNamespace

from tests.integration.conftest import make_busca_request

# Use 2+ UFs so the parallel fetch path (buscar_todas_ufs_paralelo) is taken.
_DEFAULT_UFS = ["SP", "RJ", "MG"]


def _make_pncp_result(sample_data):
    """Build a successful PNCP ParallelFetchResult-like mock.

    Returns a SimpleNamespace that quacks like ParallelFetchResult.
    The pipeline checks isinstance(result, ParallelFetchResult) -- since this
    is a SimpleNamespace, the code falls through to treating it as a plain list.
    We therefore set .items to the data AND make this directly iterable/indexable
    as a list via the items field.

    Actually, the simplest approach: return the raw list directly. The pipeline
    handles both ParallelFetchResult and plain list returns.
    """
    from pncp_client import ParallelFetchResult
    return ParallelFetchResult(
        items=sample_data,
        succeeded_ufs=["SP", "RJ", "MG"],
        failed_ufs=[],
        truncated_ufs=[],
    )


def _mock_rate_limiter():
    """Create a mock rate limiter that always allows requests."""
    mock = Mock()
    mock.check_rate_limit = AsyncMock(return_value=(True, 0))
    return mock


@pytest.mark.integration
class TestPostIndependentOfSSE:
    """AC10: The POST /buscar endpoint must return a complete, self-contained
    response without requiring the client to open an SSE connection."""

    def test_post_buscar_returns_complete_response_without_sse(
        self, integration_app, sample_licitacoes_raw, monkeypatch
    ):
        """Send POST /buscar with a search_id but never open SSE.
        The response must contain all required fields and the full result set."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")

        pncp_result = _make_pncp_result(sample_licitacoes_raw)
        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            return_value=pncp_result,
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            resp = integration_app.post("/buscar", json=payload)

        assert resp.status_code == 200, (
            f"Expected HTTP 200, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()

        # Verify all critical response fields are present
        assert "licitacoes" in body, "Response must contain licitacoes field"
        assert "resumo" in body, "Response must contain resumo field"
        assert "total_filtrado" in body, "Response must contain total_filtrado field"
        assert "excel_available" in body, "Response must contain excel_available field"
        assert "quota_used" in body, "Response must contain quota_used field"
        assert "quota_remaining" in body, "Response must contain quota_remaining field"

    def test_response_contains_licitacoes_data(
        self, integration_app, sample_licitacoes_raw, monkeypatch
    ):
        """The response must include actual bid data, not an empty shell."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")

        pncp_result = _make_pncp_result(sample_licitacoes_raw)
        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            return_value=pncp_result,
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            resp = integration_app.post("/buscar", json=payload)

        body = resp.json()
        assert body["total_filtrado"] >= 0, "total_filtrado must be non-negative"
        assert body["total_raw"] > 0, (
            "total_raw must reflect fetched records from PNCP mock"
        )

    def test_response_contains_resumo_with_content(
        self, integration_app, sample_licitacoes_raw, monkeypatch
    ):
        """The AI-generated resumo must be present and populated."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")

        pncp_result = _make_pncp_result(sample_licitacoes_raw)
        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            return_value=pncp_result,
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            resp = integration_app.post("/buscar", json=payload)

        body = resp.json()
        resumo = body["resumo"]
        assert resumo is not None, "resumo must not be None"
        assert "resumo_executivo" in resumo, "resumo must have resumo_executivo"
        assert len(resumo["resumo_executivo"]) > 0, (
            "resumo_executivo must be non-empty"
        )

    def test_no_hanging_or_timeout_without_sse_consumer(
        self, integration_app, sample_licitacoes_raw, monkeypatch
    ):
        """The POST /buscar endpoint must not hang waiting for an SSE consumer.
        Even though a search_id is provided, the endpoint completes synchronously
        without requiring a GET /buscar-progress/{search_id} consumer."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")

        import time

        pncp_result = _make_pncp_result(sample_licitacoes_raw)
        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            return_value=pncp_result,
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            start = time.monotonic()
            resp = integration_app.post("/buscar", json=payload)
            elapsed = time.monotonic() - start

        assert resp.status_code == 200
        # The request should complete in well under 10 seconds since
        # everything is mocked. Anything beyond that indicates a hang.
        assert elapsed < 10.0, (
            f"POST /buscar took {elapsed:.1f}s without SSE consumer -- "
            f"possible hang/timeout waiting for SSE"
        )
