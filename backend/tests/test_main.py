"""Tests for FastAPI application structure and base endpoints."""

import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from main import app


@pytest.fixture(autouse=True)
def mock_supabase_for_health():
    """Mock get_supabase to prevent 503 in health endpoint tests."""
    with patch("supabase_client.get_supabase", return_value=Mock()):
        yield


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
        assert app.version  # GTM-GO-003: env-driven (defaults to "dev" locally)

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
        assert data["version"] == app.version

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
        from datetime import datetime, timezone

        response = client.get("/health")
        data = response.json()

        timestamp = data["timestamp"]
        # Verify ISO 8601 format by parsing it
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)

        # Timestamp should be recent (within last 5 seconds)
        now = datetime.now(timezone.utc)
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
        assert data["version"] == app.version

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

    def test_health_includes_dependencies(self, client):
        """Health endpoint should report status of all dependencies."""
        response = client.get("/health")
        data = response.json()

        assert "dependencies" in data
        dependencies = data["dependencies"]

        # Should include all tracked dependencies
        assert "supabase" in dependencies
        assert "openai" in dependencies
        assert "redis" in dependencies

    def test_health_redis_not_configured(self, client):
        """When Redis is not configured, health should show 'not_configured'."""
        import os
        from unittest.mock import patch

        # Simulate Redis not configured
        with patch.dict(os.environ, {"REDIS_URL": ""}, clear=False):
            response = client.get("/health")
            data = response.json()

            # Should still be healthy (Redis is optional)
            assert data["status"] == "healthy"
            assert data["dependencies"]["redis"] == "not_configured"

    def test_health_redis_configured_but_unavailable(self, client):
        """When Redis is configured but unavailable, health should degrade."""
        import os
        from unittest.mock import patch, AsyncMock

        # Simulate Redis configured but unavailable
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}, clear=False):
            with patch("redis_client.is_redis_available", new_callable=AsyncMock) as mock_redis:
                mock_redis.return_value = False

                response = client.get("/health")
                data = response.json()

                # Should be degraded when Redis is configured but down
                assert data["status"] == "degraded"
                assert data["dependencies"]["redis"] == "unavailable"

    def test_health_redis_healthy(self, client):
        """When Redis is available, health should report it as healthy."""
        import os
        from unittest.mock import patch, AsyncMock

        # Mock Redis pool with ping support
        mock_pool = AsyncMock()
        mock_pool.ping.return_value = True
        mock_pool.info.return_value = {"used_memory": 1024 * 1024}  # 1 MB

        # Simulate Redis configured and available
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}, clear=False):
            with patch("redis_pool.is_redis_available", new_callable=AsyncMock, return_value=True):
                with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_pool):
                    response = client.get("/health")
                    data = response.json()

                    # Should be healthy
                    assert data["status"] == "healthy"
                    assert data["dependencies"]["redis"] == "healthy"


class TestCORSHeaders:
    """Test CORS configuration and headers."""

    def test_cors_preflight_options(self, client):
        """CORS preflight OPTIONS request should succeed for allowed origins."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200

    def test_cors_headers_present_for_allowed_origin(self, client):
        """CORS headers should be present for allowed origins (localhost:3000)."""
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})

        # Check for CORS headers (case-insensitive)
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert "access-control-allow-origin" in headers_lower
        assert headers_lower["access-control-allow-origin"] == "http://localhost:3000"

    def test_cors_blocks_unauthorized_origins(self, client):
        """CORS should not include allow-origin header for unauthorized origins."""
        # example.com is not in the allowed origins list
        response = client.get("/health", headers={"Origin": "http://example.com"})

        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        # For unauthorized origins, CORS middleware should not include the header
        # or should not echo back the unauthorized origin
        if "access-control-allow-origin" in headers_lower:
            # If header is present, it should NOT be the unauthorized origin
            assert headers_lower["access-control-allow-origin"] != "http://example.com"

    def test_cors_allows_post_method(self, client):
        """CORS should allow POST method for allowed origins."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200

    def test_cors_allows_127_localhost(self, client):
        """CORS should allow requests from 127.0.0.1:3000."""
        response = client.get("/health", headers={"Origin": "http://127.0.0.1:3000"})

        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert "access-control-allow-origin" in headers_lower
        assert headers_lower["access-control-allow-origin"] == "http://127.0.0.1:3000"


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
        assert "info" in schema  # API metadata
        assert "paths" in schema  # Endpoints

    def test_openapi_info_metadata(self, client):
        """OpenAPI info section should match app configuration."""
        response = client.get("/openapi.json")
        schema = response.json()

        info = schema["info"]
        assert info["title"] == "BidIQ Uniformes API"
        assert info["version"] == app.version

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




class TestSetoresEndpoint:
    """Test /setores endpoint for sector listing."""

    def test_listar_setores_status_code(self, client):
        """Setores endpoint should return 200 OK."""
        response = client.get("/setores")
        assert response.status_code == 200

    def test_listar_setores_response_structure(self, client):
        """Setores endpoint should return list of sectors."""
        response = client.get("/setores")
        data = response.json()
        assert "setores" in data
        assert isinstance(data["setores"], list)

    def test_listar_setores_contains_uniformes(self, client):
        """Setores endpoint should include uniformes sector."""
        response = client.get("/setores")
        data = response.json()
        setores = data["setores"]

        # Should have at least one sector
        assert len(setores) > 0

        # Each sector should have required fields
        for sector in setores:
            assert "id" in sector
            assert "name" in sector
            assert "description" in sector


class TestDebugPNCPEndpoint:
    """Test /debug/pncp-test diagnostic endpoint."""

    @pytest.fixture(autouse=True)
    def mock_admin_auth(self):
        """Override admin auth dependency so tests can access the debug endpoint."""
        from admin import require_admin
        mock_admin_user = {"id": "admin-user-123", "email": "admin@example.com", "role": "authenticated"}
        app.dependency_overrides[require_admin] = lambda: mock_admin_user
        yield
        app.dependency_overrides.pop(require_admin, None)

    def test_debug_pncp_test_success(self, client, monkeypatch):
        """Debug endpoint should return success when PNCP is reachable."""
        from unittest.mock import Mock

        mock_client_instance = Mock()
        mock_client_instance.fetch_page.return_value = {
            "totalRegistros": 100,
            "data": [{"codigoCompra": "123"}],
        }

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)

        response = client.get("/debug/pncp-test")
        assert response.status_code == 200

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "total_registros" in data
        assert "items_returned" in data
        assert "elapsed_ms" in data

    def test_debug_pncp_test_failure(self, client, monkeypatch):
        """Debug endpoint should return error details when PNCP fails."""
        from unittest.mock import Mock

        mock_client_instance = Mock()
        mock_client_instance.fetch_page.side_effect = Exception("Connection timeout")

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)

        response = client.get("/debug/pncp-test")
        assert response.status_code == 200  # Always 200 (diagnostic endpoint)

        data = response.json()
        assert data["success"] is False
        assert "error" in data
        assert "Connection timeout" in data["error"]
        assert "error_type" in data
        assert data["error_type"] == "Exception"

    def test_debug_pncp_test_measures_elapsed_time(self, client, monkeypatch):
        """Debug endpoint should measure response time."""
        from unittest.mock import Mock

        mock_client_instance = Mock()
        mock_client_instance.fetch_page.return_value = {
            "totalRegistros": 10,
            "data": [],
        }

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)

        response = client.get("/debug/pncp-test")
        data = response.json()

        # Should have elapsed time in milliseconds
        assert "elapsed_ms" in data
        assert isinstance(data["elapsed_ms"], int)
        assert data["elapsed_ms"] >= 0


class TestBuscarValidationExtended:
    """Extended validation tests for /buscar endpoint edge cases."""

    @pytest.fixture(autouse=True)
    def mock_auth_and_quota(self, monkeypatch):
        """Auto-apply auth mock and quota mock for all tests in this class."""
        from auth import require_auth
        mock_user = {"id": "test-user-123", "email": "test@example.com", "role": "authenticated"}
        app.dependency_overrides[require_auth] = lambda: mock_user
        from quota import QuotaInfo, PLAN_CAPABILITIES
        from datetime import datetime, timezone
        mock_quota = QuotaInfo(
            allowed=True,
            plan_id="maquina",
            plan_name="Máquina",
            capabilities=PLAN_CAPABILITIES["maquina"],
            quota_used=10,
            quota_remaining=290,
            quota_reset_date=datetime.now(timezone.utc)
        )
        monkeypatch.setattr("quota.check_quota", lambda user_id: mock_quota)
        # Mock atomic quota check to prevent Supabase connection
        monkeypatch.setattr(
            "quota.check_and_increment_quota_atomic",
            lambda user_id, max_q: (True, 11, max_q - 11),
        )
        yield
        app.dependency_overrides.clear()

    def test_buscar_invalid_sector_id(self, client):
        """Request with invalid sector ID should return 400 (HTTPException from stage_prepare)."""
        request = {
            "ufs": ["SP"],
            "data_inicial": "2025-01-01",
            "data_final": "2025-01-31",
            "setor_id": "invalid-sector-999",
        }
        response = client.post("/buscar", json=request)
        # SearchPipeline.stage_prepare raises HTTPException(400) for unknown sector_id
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_buscar_date_range_end_before_start(self, client):
        """Request with end date before start date should fail validation."""
        request = {
            "ufs": ["SP"],
            "data_inicial": "2025-01-31",
            "data_final": "2025-01-01",  # Before start
        }
        response = client.post("/buscar", json=request)
        assert response.status_code == 422



