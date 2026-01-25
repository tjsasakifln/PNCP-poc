"""Tests for FastAPI application structure and base endpoints."""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


class TestApplicationSetup:
    """Test FastAPI application initialization and configuration."""

    def test_app_title(self):
        """Verify app has correct title."""
        assert app.title == "BidIQ Uniformes API"

    def test_app_version(self):
        """Verify app version matches expected."""
        assert app.version == "0.2.0"

    def test_app_has_docs_endpoint(self):
        """Verify OpenAPI documentation is configured."""
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"

    def test_cors_middleware_configured(self):
        """Verify CORS middleware is present."""
        # Check that CORSMiddleware is in the middleware stack
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes


class TestRootEndpoint:
    """Test root endpoint functionality."""

    def test_root_status_code(self, client):
        """Root endpoint should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_structure(self, client):
        """Root endpoint should return API information."""
        response = client.get("/")
        data = response.json()

        # Verify required fields
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "endpoints" in data
        assert "status" in data

    def test_root_version_matches(self, client):
        """Root endpoint version should match app version."""
        response = client.get("/")
        data = response.json()
        assert data["version"] == "0.2.0"

    def test_root_endpoints_links(self, client):
        """Root endpoint should include documentation links."""
        response = client.get("/")
        data = response.json()

        endpoints = data["endpoints"]
        assert endpoints["docs"] == "/docs"
        assert endpoints["redoc"] == "/redoc"
        assert endpoints["health"] == "/health"
        assert endpoints["openapi"] == "/openapi.json"

    def test_root_status_operational(self, client):
        """Root endpoint should indicate operational status."""
        response = client.get("/")
        data = response.json()
        assert data["status"] == "operational"


class TestHealthEndpoint:
    """Test health check endpoint functionality."""

    def test_health_status_code(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Health endpoint should return status, timestamp, and version."""
        response = client.get("/health")
        data = response.json()

        # Verify all required fields are present
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

    def test_health_status_healthy(self, client):
        """Health endpoint should report 'healthy' status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_timestamp_format(self, client):
        """Health endpoint timestamp should be valid ISO 8601 format."""
        from datetime import datetime
        response = client.get("/health")
        data = response.json()

        timestamp = data["timestamp"]
        # Verify ISO 8601 format by parsing it
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)

        # Timestamp should be recent (within last 5 seconds)
        import time
        now = datetime.utcnow()
        delta = (now - parsed).total_seconds()
        assert abs(delta) < 5, f"Timestamp {timestamp} is not recent (delta: {delta}s)"

    def test_health_timestamp_changes(self, client):
        """Health endpoint timestamp should update on each request."""
        import time
        response1 = client.get("/health")
        time.sleep(0.01)  # Small delay to ensure timestamp difference
        response2 = client.get("/health")

        timestamp1 = response1.json()["timestamp"]
        timestamp2 = response2.json()["timestamp"]

        # Timestamps should be different (not cached)
        assert timestamp1 != timestamp2

    def test_health_version_matches(self, client):
        """Health endpoint version should match app version."""
        response = client.get("/health")
        data = response.json()
        assert data["version"] == "0.2.0"

    def test_health_response_time(self, client):
        """Health endpoint should respond quickly (< 100ms)."""
        import time
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1  # 100ms threshold

    def test_health_no_authentication_required(self, client):
        """Health endpoint should be publicly accessible (no auth)."""
        # No authentication headers provided
        response = client.get("/health")
        # Should still succeed
        assert response.status_code == 200

    def test_health_json_content_type(self, client):
        """Health endpoint should return JSON content type."""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]


class TestCORSHeaders:
    """Test CORS configuration and headers."""

    def test_cors_preflight_options(self, client):
        """CORS preflight OPTIONS request should succeed."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.status_code == 200

    def test_cors_headers_present(self, client):
        """CORS headers should be present in responses."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )

        # Check for CORS headers (case-insensitive)
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert "access-control-allow-origin" in headers_lower

    def test_cors_allows_all_origins(self, client):
        """CORS should allow all origins (POC configuration)."""
        response = client.get(
            "/health",
            headers={"Origin": "http://example.com"}
        )

        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        # FastAPI CORS middleware returns the requesting origin or "*"
        assert "access-control-allow-origin" in headers_lower

    def test_cors_allows_post_method(self, client):
        """CORS should allow POST method."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert response.status_code == 200


class TestOpenAPIDocumentation:
    """Test OpenAPI documentation generation."""

    def test_openapi_json_accessible(self, client):
        """OpenAPI JSON schema should be accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_openapi_schema_structure(self, client):
        """OpenAPI schema should have required fields."""
        response = client.get("/openapi.json")
        schema = response.json()

        assert "openapi" in schema  # OpenAPI version
        assert "info" in schema     # API metadata
        assert "paths" in schema    # Endpoints

    def test_openapi_info_metadata(self, client):
        """OpenAPI info section should match app configuration."""
        response = client.get("/openapi.json")
        schema = response.json()

        info = schema["info"]
        assert info["title"] == "BidIQ Uniformes API"
        assert info["version"] == "0.2.0"

    def test_openapi_has_health_endpoint(self, client):
        """OpenAPI schema should document /health endpoint."""
        response = client.get("/openapi.json")
        schema = response.json()

        assert "/health" in schema["paths"]
        assert "get" in schema["paths"]["/health"]

    def test_openapi_has_root_endpoint(self, client):
        """OpenAPI schema should document / endpoint."""
        response = client.get("/openapi.json")
        schema = response.json()

        assert "/" in schema["paths"]
        assert "get" in schema["paths"]["/"]

    def test_docs_page_accessible(self, client):
        """Swagger UI docs page should be accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_page_accessible(self, client):
        """ReDoc documentation page should be accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestErrorHandling:
    """Test basic error handling for non-existent endpoints."""

    def test_404_for_invalid_endpoint(self, client):
        """Invalid endpoints should return 404 Not Found."""
        response = client.get("/invalid-endpoint-xyz")
        assert response.status_code == 404

    def test_404_response_structure(self, client):
        """404 response should have error detail."""
        response = client.get("/invalid-endpoint-xyz")
        data = response.json()
        assert "detail" in data
