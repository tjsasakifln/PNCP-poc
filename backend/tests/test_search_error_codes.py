"""
CRIT-009 T1-T5: Tests for structured error responses from /buscar endpoint.

Validates that all exception types produce structured error bodies with:
- detail (str)
- error_code (SearchErrorCode value)
- search_id (uuid or None)
- correlation_id (uuid or None)
- timestamp (ISO 8601)
"""

import asyncio
import uuid
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app
from auth import require_auth
from schemas import SearchErrorCode


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_auth():
    """Override auth for all tests."""
    async def fake_auth():
        return {"id": str(uuid.uuid4()), "email": "test@example.com"}
    app.dependency_overrides[require_auth] = fake_auth
    yield
    app.dependency_overrides.pop(require_auth, None)


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


VALID_SEARCH_BODY = {
    "ufs": ["SP"],
    "data_inicial": "2026-02-10",
    "data_final": "2026-02-20",
    "setor_id": "vestuario",
    "search_id": str(uuid.uuid4()),
}


def _assert_structured_error(response_json: dict, expected_code: str):
    """Assert response body is a structured error per CRIT-009 AC1."""
    detail = response_json.get("detail", response_json)
    assert "detail" in detail, f"Missing 'detail' field: {detail}"
    assert "error_code" in detail, f"Missing 'error_code' field: {detail}"
    assert "timestamp" in detail, f"Missing 'timestamp' field: {detail}"
    assert detail["error_code"] == expected_code, (
        f"Expected error_code={expected_code}, got {detail['error_code']}"
    )
    # Timestamp should be ISO 8601
    assert "T" in detail["timestamp"], f"Timestamp not ISO 8601: {detail['timestamp']}"
    # search_id should be present (may be None for some errors)
    assert "search_id" in detail


# ---------------------------------------------------------------------------
# T1: AllSourcesFailedError → ALL_SOURCES_FAILED or SOURCE_UNAVAILABLE
# ---------------------------------------------------------------------------

class TestAllSourcesFailedError:
    """T1: AllSourcesFailedError produces structured error with correct code."""

    def test_pncp_api_error_returns_source_unavailable(self, client):
        """PNCPAPIError maps to SOURCE_UNAVAILABLE with structured body."""
        from exceptions import PNCPAPIError

        with patch("routes.search.SearchPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.run = AsyncMock(side_effect=PNCPAPIError("PNCP down"))
            # Also need to mock stage methods called before run for cache-first path
            mock_pipeline.stage_validate = AsyncMock()
            mock_pipeline.stage_prepare = AsyncMock()

            with patch("routes.search.check_user_roles", return_value=None), \
                 patch("routes.search.rate_limiter"):
                response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 502
        _assert_structured_error(response.json(), SearchErrorCode.SOURCE_UNAVAILABLE.value)


# ---------------------------------------------------------------------------
# T2: asyncio.TimeoutError → TIMEOUT
# ---------------------------------------------------------------------------

class TestTimeoutError:
    """T2: asyncio.TimeoutError returns error_code TIMEOUT."""

    def test_timeout_error_returns_timeout_code(self, client):
        """Timeout produces TIMEOUT error code and 504 status."""
        with patch("routes.search.SearchPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.run = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_pipeline.stage_validate = AsyncMock()
            mock_pipeline.stage_prepare = AsyncMock()

            with patch("routes.search.check_user_roles", return_value=None), \
                 patch("routes.search.rate_limiter"):
                response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 504
        _assert_structured_error(response.json(), SearchErrorCode.TIMEOUT.value)


# ---------------------------------------------------------------------------
# T3: QuotaExceededError → QUOTA_EXCEEDED
# ---------------------------------------------------------------------------

class TestQuotaExceededError:
    """T3: QuotaExceeded (403 HTTPException from pipeline) returns QUOTA_EXCEEDED."""

    def test_quota_exceeded_returns_quota_code(self, client):
        """Quota exceeded maps to QUOTA_EXCEEDED code with 403 status."""
        from fastapi import HTTPException

        with patch("routes.search.SearchPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.run = AsyncMock(
                side_effect=HTTPException(status_code=403, detail="Suas buscas acabaram.")
            )
            mock_pipeline.stage_validate = AsyncMock()
            mock_pipeline.stage_prepare = AsyncMock()

            with patch("routes.search.check_user_roles", return_value=None), \
                 patch("routes.search.rate_limiter"):
                response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 403
        _assert_structured_error(response.json(), SearchErrorCode.QUOTA_EXCEEDED.value)


# ---------------------------------------------------------------------------
# T4: Generic exception → INTERNAL_ERROR (no stack trace)
# ---------------------------------------------------------------------------

class TestInternalError:
    """T4: Unexpected exception returns INTERNAL_ERROR without stack traces."""

    def test_generic_error_returns_internal_error_code(self, client):
        """Generic exception maps to INTERNAL_ERROR, does NOT expose stack trace."""
        with patch("routes.search.SearchPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.run = AsyncMock(
                side_effect=RuntimeError("secret internal details: DB password=xyz")
            )
            mock_pipeline.stage_validate = AsyncMock()
            mock_pipeline.stage_prepare = AsyncMock()

            with patch("routes.search.check_user_roles", return_value=None), \
                 patch("routes.search.rate_limiter"):
                response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 500
        body = response.json()
        _assert_structured_error(body, SearchErrorCode.INTERNAL_ERROR.value)

        # CRITICAL: Stack trace and internal details must NOT be exposed
        detail = body.get("detail", body)
        assert "DB password" not in detail.get("detail", ""), "Stack trace leaked!"
        assert "secret" not in detail.get("detail", ""), "Internal details leaked!"


# ---------------------------------------------------------------------------
# T5: Validate required fields always present
# ---------------------------------------------------------------------------

class TestRequiredFields:
    """T5: All structured error responses contain required fields."""

    def test_rate_limit_error_has_required_fields(self, client):
        """PNCPRateLimitError structured response has all required fields."""
        from exceptions import PNCPRateLimitError

        error = PNCPRateLimitError("Too many requests")
        error.retry_after = 60

        with patch("routes.search.SearchPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.run = AsyncMock(side_effect=error)
            mock_pipeline.stage_validate = AsyncMock()
            mock_pipeline.stage_prepare = AsyncMock()

            with patch("routes.search.check_user_roles", return_value=None), \
                 patch("routes.search.rate_limiter"):
                response = client.post("/v1/buscar", json=VALID_SEARCH_BODY)

        assert response.status_code == 503
        body = response.json()
        detail = body.get("detail", body)

        # Required fields per AC1
        assert "detail" in detail, "Missing 'detail' (message)"
        assert "error_code" in detail, "Missing 'error_code'"
        assert "timestamp" in detail, "Missing 'timestamp'"
        assert detail["error_code"] == SearchErrorCode.RATE_LIMIT.value
        # search_id should be present
        assert "search_id" in detail
        assert detail["search_id"] == VALID_SEARCH_BODY["search_id"]
