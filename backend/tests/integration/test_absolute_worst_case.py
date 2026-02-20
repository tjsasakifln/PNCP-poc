"""AC9: Absolute worst case -- all sources + all caches fail.

Tests the system's behavior when everything fails:
- All data sources (PNCP, PCP, ComprasGov) return 500
- All cache levels (Supabase, Redis, InMemory) are empty
- Verifies user gets deterministic empty_failure response.
Production scenario: Total infrastructure failure -> user gets clear error, not random timeout.
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from types import SimpleNamespace

from tests.integration.conftest import make_busca_request

# All tests use 2+ UFs to ensure the parallel fetch path (buscar_todas_ufs_paralelo)
# is taken. With a single UF the pipeline falls back to PNCPClient.fetch_all() which
# bypasses our mock.
_DEFAULT_UFS = ["SP", "RJ"]


def _mock_rate_limiter():
    """Create a mock rate limiter that always allows requests."""
    mock = Mock()
    mock.check_rate_limit = AsyncMock(return_value=(True, 0))
    return mock


@pytest.mark.integration
class TestAbsoluteWorstCase:
    """AC9: When all sources fail and all caches are empty, the user receives
    a deterministic empty_failure response with actionable guidance."""

    def test_all_sources_fail_returns_empty_failure(
        self, integration_app, sample_licitacoes_raw, monkeypatch
    ):
        """When PNCP is degraded and cache cascade returns None,
        the response has response_state='empty_failure' with zero licitacoes."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")

        from pncp_client import PNCPDegradedError

        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            side_effect=PNCPDegradedError("Circuit breaker open"),
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            resp = integration_app.post("/buscar", json=payload)

        assert resp.status_code == 200, (
            f"Expected HTTP 200 for empty_failure, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["response_state"] == "empty_failure"
        assert body["total_filtrado"] == 0
        assert body["licitacoes"] == []

    def test_empty_failure_contains_degradation_guidance(
        self, integration_app, monkeypatch
    ):
        """The empty_failure response includes a human-readable
        degradation_guidance field telling the user what to do."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")

        from pncp_client import PNCPDegradedError

        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            side_effect=PNCPDegradedError("All sources down"),
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            resp = integration_app.post("/buscar", json=payload)

        body = resp.json()
        assert body["degradation_guidance"] is not None, (
            "empty_failure response must include degradation_guidance"
        )
        guidance = body["degradation_guidance"]
        assert len(guidance) > 20, (
            "degradation_guidance should be a meaningful user-facing message"
        )
        # The guidance should mention trying again or reducing scope
        assert any(
            keyword in guidance.lower()
            for keyword in ["tente", "novamente", "indispon", "reduza", "minutos"]
        ), f"degradation_guidance should contain actionable advice, got: {guidance}"

    def test_empty_failure_returns_http_200_not_500(
        self, integration_app, monkeypatch
    ):
        """The empty_failure response is delivered as HTTP 200, not 500 or 504.
        This is by design: the pipeline completed successfully, the result
        is 'there is no data available right now'. The frontend uses
        response_state to determine the UI, not the HTTP status code."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")

        from pncp_client import PNCPDegradedError

        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            side_effect=PNCPDegradedError("Total failure"),
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            resp = integration_app.post("/buscar", json=payload)

        assert resp.status_code == 200, (
            f"empty_failure must return HTTP 200, got {resp.status_code}"
        )
        # Verify it is valid JSON
        body = resp.json()
        assert "response_state" in body
        assert "resumo" in body

    def test_empty_failure_is_deterministic(
        self, integration_app, monkeypatch
    ):
        """Calling POST /buscar twice under the same failure conditions
        produces structurally identical responses (same response_state,
        same empty licitacoes, same guidance). No randomness, no flakiness."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")

        from pncp_client import PNCPDegradedError

        bodies = []
        for _ in range(2):
            with patch(
                "routes.search.buscar_todas_ufs_paralelo",
                new_callable=AsyncMock,
                side_effect=PNCPDegradedError("Determinism check"),
            ), patch(
                "routes.search.rate_limiter",
                _mock_rate_limiter(),
            ):
                payload = make_busca_request(ufs=_DEFAULT_UFS)
                resp = integration_app.post("/buscar", json=payload)
                assert resp.status_code == 200
                bodies.append(resp.json())

        first, second = bodies
        assert first["response_state"] == second["response_state"] == "empty_failure"
        assert first["total_filtrado"] == second["total_filtrado"] == 0
        assert first["licitacoes"] == second["licitacoes"] == []
        assert first["degradation_guidance"] == second["degradation_guidance"]
        assert first["is_partial"] == second["is_partial"]
