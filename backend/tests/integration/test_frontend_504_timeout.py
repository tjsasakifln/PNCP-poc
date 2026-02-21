"""AC11: Frontend proxy 504 timeout handling.

Tests the backend's behavior with slow responses that would trigger
a frontend proxy timeout (504).
Production scenario: Backend takes too long -> frontend proxy fires AbortController.

Since we cannot simulate the Next.js proxy in a Python integration test,
we test the backend's own timeout handling:
- When the pipeline's fetch stage times out, the response is structured correctly
- When there is no cache fallback, the backend returns HTTP 504
- The error response body is JSON-parseable with a user-friendly message
"""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock, Mock
from types import SimpleNamespace

from tests.integration.conftest import make_busca_request

# Use 2+ UFs so the parallel fetch path (buscar_todas_ufs_paralelo) is taken.
_DEFAULT_UFS = ["SP", "RJ"]


def _mock_rate_limiter():
    """Create a mock rate limiter that always allows requests."""
    mock = Mock()
    mock.check_rate_limit = AsyncMock(return_value=(True, 0))
    return mock


@pytest.mark.integration
class TestFrontend504Timeout:
    """AC11: When the pipeline exceeds its internal timeout and no cache
    is available, the backend returns a well-structured 504 response."""

    def test_pipeline_timeout_returns_504_when_no_cache(
        self, integration_app, monkeypatch
    ):
        """When buscar_todas_ufs_paralelo takes longer than the fetch timeout
        and no cached data is available, the backend responds with HTTP 504."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")
        # Set a very short timeout to trigger timeout quickly
        monkeypatch.setenv("SEARCH_FETCH_TIMEOUT", "1")

        async def slow_fetch(**kwargs):
            await asyncio.sleep(5)
            return []

        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            side_effect=slow_fetch,
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            resp = integration_app.post("/buscar", json=payload)

        assert resp.status_code == 504, (
            f"Expected HTTP 504 for timeout, got {resp.status_code}: {resp.text}"
        )

    def test_504_response_is_json_parseable(
        self, integration_app, monkeypatch
    ):
        """The 504 error response body must be valid JSON, not a raw
        traceback or plain-text error."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")
        monkeypatch.setenv("SEARCH_FETCH_TIMEOUT", "1")

        async def slow_fetch(**kwargs):
            await asyncio.sleep(5)
            return []

        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            side_effect=slow_fetch,
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            resp = integration_app.post("/buscar", json=payload)

        body = resp.json()
        assert "detail" in body, (
            "504 response must include a 'detail' field with the error message"
        )

    def test_504_response_contains_user_friendly_message(
        self, integration_app, monkeypatch
    ):
        """The error detail must be a human-readable message in Portuguese,
        not a raw exception string or traceback."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")
        monkeypatch.setenv("SEARCH_FETCH_TIMEOUT", "1")

        async def slow_fetch(**kwargs):
            await asyncio.sleep(5)
            return []

        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            side_effect=slow_fetch,
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            resp = integration_app.post("/buscar", json=payload)

        body = resp.json()
        raw_detail = body["detail"]
        # CRIT-009: detail may be a structured dict with inner "detail" key
        detail = raw_detail["detail"] if isinstance(raw_detail, dict) else raw_detail
        assert len(detail) > 20, (
            "Error detail must be a meaningful message, not a short code"
        )
        # Should mention time limit or suggest reducing scope
        assert any(
            keyword in detail.lower()
            for keyword in ["tempo", "limite", "tente", "estados", "cache", "exced"]
        ), f"Error message should guide the user, got: {detail}"
        # Must not contain raw Python exception traces
        assert "Traceback" not in detail, (
            "Error detail must not expose Python tracebacks"
        )

    def test_direct_timeout_error_returns_structured_response(
        self, integration_app, monkeypatch
    ):
        """When the pipeline's internal asyncio.TimeoutError fires (from wait_for),
        the response is always a JSON object regardless of status code.
        This ensures the frontend can always parse the body."""
        monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")
        monkeypatch.setenv("SEARCH_FETCH_TIMEOUT", "1")

        async def slow_fetch(**kwargs):
            await asyncio.sleep(5)
            return []

        with patch(
            "routes.search.buscar_todas_ufs_paralelo",
            new_callable=AsyncMock,
            side_effect=slow_fetch,
        ), patch(
            "routes.search.rate_limiter",
            _mock_rate_limiter(),
        ):
            payload = make_busca_request(ufs=_DEFAULT_UFS)
            resp = integration_app.post("/buscar", json=payload)

        # Must be parseable JSON regardless of status code
        body = resp.json()
        assert isinstance(body, dict), "Response body must be a JSON object"
        # Must have either 'detail' (error) or 'response_state' (success/degraded)
        assert "detail" in body or "response_state" in body, (
            "Response must include 'detail' or 'response_state' for frontend parsing"
        )
