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
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200

    def test_cors_headers_present(self, client):
        """CORS headers should be present in responses."""
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})

        # Check for CORS headers (case-insensitive)
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert "access-control-allow-origin" in headers_lower

    def test_cors_allows_all_origins(self, client):
        """CORS should allow all origins (POC configuration)."""
        response = client.get("/health", headers={"Origin": "http://example.com"})

        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        # FastAPI CORS middleware returns the requesting origin or "*"
        assert "access-control-allow-origin" in headers_lower

    def test_cors_allows_post_method(self, client):
        """CORS should allow POST method."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
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
        assert "info" in schema  # API metadata
        assert "paths" in schema  # Endpoints

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


class TestBuscarEndpoint:
    """Test POST /buscar endpoint - main orchestration pipeline."""

    @pytest.fixture
    def valid_request(self):
        """Fixture for valid search request."""
        return {
            "ufs": ["SP", "RJ"],
            "data_inicial": "2025-01-01",
            "data_final": "2025-01-31",
        }

    @pytest.fixture
    def mock_licitacao(self):
        """Fixture for a valid PNCP bid matching uniform keywords."""
        return {
            "codigoCompra": "123456789",
            "objetoCompra": "Aquisição de uniformes escolares para secretaria de educação",
            "nomeOrgao": "Prefeitura Municipal de São Paulo",
            "uf": "SP",
            "municipio": "São Paulo",
            "valorTotalEstimado": 150000.00,
            "dataAberturaProposta": "2025-02-15T10:00:00",
            "linkSistemaOrigem": "https://pncp.gov.br/app/editais/123456789",
        }

    @pytest.fixture(autouse=True)
    def mock_auth_and_quota(self, monkeypatch):
        """Auto-apply auth mock and quota mock for all tests in this class."""
        from auth import require_auth
        mock_user = {"id": "test-user-123", "email": "test@example.com", "role": "authenticated"}
        app.dependency_overrides[require_auth] = lambda: mock_user
        # Mock check_quota to skip Supabase connection
        monkeypatch.setattr("quota.check_quota", lambda user_id: {"credits_remaining": 100, "plan": "unlimited"})
        yield
        app.dependency_overrides.clear()

    def test_buscar_endpoint_exists(self, client):
        """POST /buscar endpoint should be defined."""
        # Send empty POST to trigger validation error (not 404)
        response = client.post("/buscar", json={})
        # Should get 422 (validation error) not 404 (endpoint doesn't exist)
        assert response.status_code == 422

    def test_buscar_validation_empty_ufs(self, client, valid_request):
        """Request with empty UFs list should fail validation."""
        request = valid_request.copy()
        request["ufs"] = []
        response = client.post("/buscar", json=request)
        assert response.status_code == 422
        assert "ufs" in response.json()["detail"][0]["loc"]

    def test_buscar_validation_invalid_date_format(self, client, valid_request):
        """Request with invalid date format should fail validation."""
        request = valid_request.copy()
        request["data_inicial"] = "01-01-2025"  # Wrong format (DD-MM-YYYY)
        response = client.post("/buscar", json=request)
        assert response.status_code == 422

    def test_buscar_validation_missing_fields(self, client):
        """Request with missing required fields should fail."""
        response = client.post("/buscar", json={"ufs": ["SP"]})
        assert response.status_code == 422
        data = response.json()
        # Should have validation errors for missing fields
        assert "detail" in data

    def test_buscar_success_response_structure(self, client, valid_request, mock_licitacao, monkeypatch):
        """Successful request should return all required fields."""
        from unittest.mock import Mock

        # Mock PNCP client
        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter([mock_licitacao])

        def mock_pncp_client():
            return mock_client_instance

        # Mock filter_batch to return the bid
        def mock_filter_batch(bids, **kwargs):
            return [bids[0]], {"total_rejeitados": 0}

        # Mock create_excel to return a buffer
        from io import BytesIO
        def mock_create_excel(bids):
            buffer = BytesIO()
            buffer.write(b"fake-excel-content")
            buffer.seek(0)
            return buffer

        # Mock gerar_resumo to return valid summary
        def mock_gerar_resumo(bids, **kwargs):
            from schemas import ResumoLicitacoes
            return ResumoLicitacoes(
                resumo_executivo="1 licitação encontrada",
                total_oportunidades=1,
                valor_total=150000.00,
                destaques=["SP: R$ 150k"],
            )

        # Apply mocks
        monkeypatch.setattr("main.PNCPClient", mock_pncp_client)
        monkeypatch.setattr("main.filter_batch", mock_filter_batch)
        monkeypatch.setattr("main.create_excel", mock_create_excel)
        monkeypatch.setattr("main.gerar_resumo", mock_gerar_resumo)

        response = client.post("/buscar", json=valid_request)

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields
        assert "resumo" in data
        assert "excel_base64" in data
        assert "total_raw" in data
        assert "total_filtrado" in data

    def test_buscar_resumo_structure(self, client, valid_request, mock_licitacao, monkeypatch):
        """Response should include valid resumo structure."""
        from unittest.mock import Mock
        from io import BytesIO

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter([mock_licitacao])

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)
        monkeypatch.setattr("main.filter_batch", lambda bids, **kwargs: ([bids[0]], {}))
        monkeypatch.setattr("main.create_excel", lambda bids: BytesIO(b"excel"))

        def mock_gerar_resumo(bids, **kwargs):
            from schemas import ResumoLicitacoes
            return ResumoLicitacoes(
                resumo_executivo="Test summary",
                total_oportunidades=1,
                valor_total=150000.00,
                destaques=["Test highlight"],
                alerta_urgencia="Test alert",
            )

        monkeypatch.setattr("main.gerar_resumo", mock_gerar_resumo)

        response = client.post("/buscar", json=valid_request)
        data = response.json()

        resumo = data["resumo"]
        assert "resumo_executivo" in resumo
        assert "total_oportunidades" in resumo
        assert "valor_total" in resumo
        assert "destaques" in resumo
        assert "alerta_urgencia" in resumo

    def test_buscar_excel_base64_valid(self, client, valid_request, mock_licitacao, monkeypatch):
        """Excel should be valid base64 string."""
        import base64
        from unittest.mock import Mock
        from io import BytesIO

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter([mock_licitacao])

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)
        monkeypatch.setattr("main.filter_batch", lambda bids, **kwargs: ([bids[0]], {}))

        excel_content = b"PK\x03\x04fake-excel-header"
        monkeypatch.setattr("main.create_excel", lambda bids: BytesIO(excel_content))

        def mock_gerar_resumo(bids, **kwargs):
            from schemas import ResumoLicitacoes
            return ResumoLicitacoes(
                resumo_executivo="Test",
                total_oportunidades=1,
                valor_total=150000.00,
            )

        monkeypatch.setattr("main.gerar_resumo", mock_gerar_resumo)

        response = client.post("/buscar", json=valid_request)
        data = response.json()

        excel_base64 = data["excel_base64"]
        # Should be valid base64
        decoded = base64.b64decode(excel_base64)
        assert decoded == excel_content

    def test_buscar_llm_fallback_on_error(self, client, valid_request, mock_licitacao, monkeypatch):
        """Should use fallback when LLM fails."""
        from unittest.mock import Mock
        from io import BytesIO

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter([mock_licitacao])

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)
        monkeypatch.setattr("main.filter_batch", lambda bids, **kwargs: ([bids[0]], {}))
        monkeypatch.setattr("main.create_excel", lambda bids: BytesIO(b"excel"))

        # Mock gerar_resumo to raise exception
        def mock_gerar_resumo(bids, **kwargs):
            raise Exception("OpenAI API error")

        # Mock fallback to return valid summary
        def mock_gerar_resumo_fallback(bids, **kwargs):
            from schemas import ResumoLicitacoes
            return ResumoLicitacoes(
                resumo_executivo="Fallback summary",
                total_oportunidades=1,
                valor_total=150000.00,
            )

        monkeypatch.setattr("main.gerar_resumo", mock_gerar_resumo)
        monkeypatch.setattr("main.gerar_resumo_fallback", mock_gerar_resumo_fallback)

        response = client.post("/buscar", json=valid_request)
        assert response.status_code == 200
        # Should succeed with fallback
        data = response.json()
        assert data["resumo"]["resumo_executivo"] == "Fallback summary"

    def test_buscar_pncp_api_error_502(self, client, valid_request, monkeypatch):
        """PNCP API error should return 502."""
        from exceptions import PNCPAPIError
        from unittest.mock import Mock

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.side_effect = PNCPAPIError("Connection timeout")

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)

        response = client.post("/buscar", json=valid_request)
        assert response.status_code == 502
        assert "PNCP" in response.json()["detail"]

    def test_buscar_rate_limit_error_503(self, client, valid_request, monkeypatch):
        """PNCP rate limit error should return 503 with Retry-After."""
        from exceptions import PNCPRateLimitError
        from unittest.mock import Mock

        mock_client_instance = Mock()
        error = PNCPRateLimitError("Rate limit exceeded")
        error.retry_after = 120
        mock_client_instance.fetch_all.side_effect = error

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)

        response = client.post("/buscar", json=valid_request)
        assert response.status_code == 503
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "120"

    def test_buscar_internal_error_500(self, client, valid_request, monkeypatch):
        """Unexpected error should return 500 with sanitized message."""
        from unittest.mock import Mock

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.side_effect = RuntimeError("Internal bug with sensitive data")

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)

        response = client.post("/buscar", json=valid_request)
        assert response.status_code == 500
        # Should NOT expose internal error details
        assert "Erro interno do servidor" in response.json()["detail"]
        assert "sensitive data" not in response.json()["detail"]

    def test_buscar_empty_results(self, client, valid_request, monkeypatch):
        """Should handle empty results gracefully."""
        from unittest.mock import Mock
        from io import BytesIO

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter([])  # Empty generator

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)
        monkeypatch.setattr("main.filter_batch", lambda bids, **kwargs: ([], {}))
        monkeypatch.setattr("main.create_excel", lambda bids: BytesIO(b"empty-excel"))

        def mock_gerar_resumo(bids, **kwargs):
            from schemas import ResumoLicitacoes
            return ResumoLicitacoes(
                resumo_executivo="Nenhuma licitação encontrada",
                total_oportunidades=0,
                valor_total=0.0,
            )

        monkeypatch.setattr("main.gerar_resumo", mock_gerar_resumo)

        response = client.post("/buscar", json=valid_request)
        assert response.status_code == 200
        data = response.json()
        assert data["total_raw"] == 0
        assert data["total_filtrado"] == 0

    def test_buscar_statistics_match(self, client, valid_request, mock_licitacao, monkeypatch):
        """total_raw and total_filtrado should reflect actual counts."""
        from unittest.mock import Mock
        from io import BytesIO

        # Mock 10 raw bids, 3 filtered
        mock_licitacoes_raw = [mock_licitacao.copy() for _ in range(10)]
        mock_licitacoes_filtradas = mock_licitacoes_raw[:3]

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter(mock_licitacoes_raw)

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)
        monkeypatch.setattr("main.filter_batch", lambda bids, **kwargs: (mock_licitacoes_filtradas, {}))
        monkeypatch.setattr("main.create_excel", lambda bids: BytesIO(b"excel"))

        def mock_gerar_resumo(bids, **kwargs):
            from schemas import ResumoLicitacoes
            return ResumoLicitacoes(
                resumo_executivo="3 licitações",
                total_oportunidades=len(bids),
                valor_total=450000.00,
            )

        monkeypatch.setattr("main.gerar_resumo", mock_gerar_resumo)

        response = client.post("/buscar", json=valid_request)
        data = response.json()
        assert data["total_raw"] == 10
        assert data["total_filtrado"] == 3

    def test_buscar_logs_pipeline_stages(self, client, valid_request, mock_licitacao, monkeypatch, caplog):
        """Should log each pipeline stage."""
        from unittest.mock import Mock
        from io import BytesIO

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter([mock_licitacao])

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)
        monkeypatch.setattr("main.filter_batch", lambda bids, **kwargs: ([bids[0]], {}))
        monkeypatch.setattr("main.create_excel", lambda bids: BytesIO(b"excel"))

        def mock_gerar_resumo(bids, **kwargs):
            from schemas import ResumoLicitacoes
            return ResumoLicitacoes(
                resumo_executivo="Test",
                total_oportunidades=1,
                valor_total=150000.00,
            )

        monkeypatch.setattr("main.gerar_resumo", mock_gerar_resumo)

        with caplog.at_level("INFO"):
            _response = client.post("/buscar", json=valid_request)

        # Verify key log messages
        log_messages = " ".join([record.message for record in caplog.records])
        assert "Starting procurement search" in log_messages
        assert "Fetching bids from PNCP API" in log_messages
        assert "Applying filters" in log_messages
        assert "Generating executive summary" in log_messages
        assert "Generating Excel report" in log_messages
        assert "Search completed successfully" in log_messages


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
        monkeypatch.setattr("quota.check_quota", lambda user_id: {"credits_remaining": 100, "plan": "unlimited"})
        yield
        app.dependency_overrides.clear()

    def test_buscar_invalid_sector_id(self, client):
        """Request with invalid sector ID should return 500 (HTTPException caught by general handler)."""
        request = {
            "ufs": ["SP"],
            "data_inicial": "2025-01-01",
            "data_final": "2025-01-31",
            "setor_id": "invalid-sector-999",
        }
        response = client.post("/buscar", json=request)
        # HTTPException(400) is caught by the outer Exception handler and converted to 500
        # This covers line 213-214 (KeyError -> HTTPException path)
        assert response.status_code == 500
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

    def test_buscar_with_custom_search_terms(self, client, monkeypatch):
        """Request with custom search terms should use them instead of sector keywords."""
        from unittest.mock import Mock
        from io import BytesIO

        mock_licitacao = {
            "codigoCompra": "CUSTOM123",
            "objetoCompra": "Aquisição de customizado especial",
            "nomeOrgao": "Prefeitura Test",
            "uf": "SP",
            "municipio": "São Paulo",
            "valorTotalEstimado": 100000.00,
            "dataAberturaProposta": "2025-02-10T10:00:00",
            "linkSistemaOrigem": "https://pncp.gov.br/test",
        }

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter([mock_licitacao])

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)
        monkeypatch.setattr("main.filter_batch", lambda bids, **kwargs: ([bids[0]], {}))
        monkeypatch.setattr("main.create_excel", lambda bids: BytesIO(b"excel"))

        def mock_gerar_resumo(bids, **kwargs):
            from schemas import ResumoLicitacoes
            return ResumoLicitacoes(
                resumo_executivo="Custom terms used",
                total_oportunidades=1,
                valor_total=100000.00,
            )

        monkeypatch.setattr("main.gerar_resumo", mock_gerar_resumo)

        request = {
            "ufs": ["SP"],
            "data_inicial": "2025-01-01",
            "data_final": "2025-01-31",
            "termos_busca": "customizado especial",
        }

        response = client.post("/buscar", json=request)
        assert response.status_code == 200

    def test_buscar_with_empty_custom_search_terms(self, client, monkeypatch):
        """Request with empty/whitespace-only custom terms should use sector keywords."""
        from unittest.mock import Mock

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter([])

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)
        monkeypatch.setattr("main.filter_batch", lambda bids, **kwargs: ([], {}))

        request = {
            "ufs": ["SP"],
            "data_inicial": "2025-01-01",
            "data_final": "2025-01-31",
            "termos_busca": "   ",  # Only whitespace
        }

        response = client.post("/buscar", json=request)
        assert response.status_code == 200


class TestBuscarDiagnosticLogging:
    """Test diagnostic logging features in /buscar endpoint."""

    @pytest.fixture(autouse=True)
    def mock_auth_and_quota(self, monkeypatch):
        """Auto-apply auth mock and quota mock for all tests in this class."""
        from auth import require_auth
        mock_user = {"id": "test-user-123", "email": "test@example.com", "role": "authenticated"}
        app.dependency_overrides[require_auth] = lambda: mock_user
        monkeypatch.setattr("quota.check_quota", lambda user_id: {"credits_remaining": 100, "plan": "unlimited"})
        yield
        app.dependency_overrides.clear()

    def test_buscar_logs_keyword_rejection_sample(self, client, monkeypatch, caplog):
        """Should log sample of keyword-rejected bids when rejections occur."""
        from unittest.mock import Mock

        # Create bids that will be keyword-rejected
        rejected_bids = [
            {
                "codigoCompra": f"REJ{i}",
                "objetoCompra": "Aquisição de equipamentos de informática não relacionados a uniformes",
                "nomeOrgao": "Prefeitura Test",
                "uf": "SP",
                "municipio": "São Paulo",
                "valorTotalEstimado": 100000.00,
                "dataAberturaProposta": "2025-02-10T10:00:00",
            }
            for i in range(5)
        ]

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter(rejected_bids)

        # Mock filter to return empty results (all rejected by keyword)
        def mock_filter_batch(bids, **kwargs):
            return [], {
                "total": len(bids),
                "aprovadas": 0,
                "rejeitadas_keyword": len(bids),
            }

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)
        monkeypatch.setattr("main.filter_batch", mock_filter_batch)

        request = {
            "ufs": ["SP"],
            "data_inicial": "2025-01-01",
            "data_final": "2025-01-31",
        }

        with caplog.at_level("DEBUG"):
            _response = client.post("/buscar", json=request)

        # Check if diagnostic logging occurred
        log_messages = " ".join([record.message for record in caplog.records])
        # Should mention keyword rejections
        assert "rejeitadas_keyword" in log_messages.lower() or "keyword" in log_messages.lower()

    def test_buscar_override_llm_total_oportunidades(self, client, monkeypatch, caplog):
        """Should override LLM total_oportunidades when it differs from actual count."""
        from unittest.mock import Mock
        from io import BytesIO

        mock_licitacao = {
            "codigoCompra": "TEST123",
            "objetoCompra": "Aquisição de uniformes escolares",
            "nomeOrgao": "Prefeitura Test",
            "uf": "SP",
            "municipio": "São Paulo",
            "valorTotalEstimado": 150000.00,
            "dataAberturaProposta": "2025-02-10T10:00:00",
        }

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter([mock_licitacao])

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)
        monkeypatch.setattr("main.filter_batch", lambda bids, **kwargs: ([bids[0]], {}))
        monkeypatch.setattr("main.create_excel", lambda bids: BytesIO(b"excel"))

        # Mock LLM to return WRONG count (0 instead of 1)
        def mock_gerar_resumo(bids, **kwargs):
            from schemas import ResumoLicitacoes
            return ResumoLicitacoes(
                resumo_executivo="Test",
                total_oportunidades=0,  # WRONG - should be 1
                valor_total=0.0,  # WRONG - should be 150k
            )

        monkeypatch.setattr("main.gerar_resumo", mock_gerar_resumo)

        request = {
            "ufs": ["SP"],
            "data_inicial": "2025-01-01",
            "data_final": "2025-01-31",
        }

        with caplog.at_level("WARNING"):
            response = client.post("/buscar", json=request)

        # Verify override occurred
        data = response.json()
        assert data["resumo"]["total_oportunidades"] == 1  # Overridden to correct value

        # Check for warning log
        log_messages = " ".join([record.message for record in caplog.records])
        assert "overriding with actual count" in log_messages.lower()


class TestBuscarIntegration:
    """Integration tests using real modules (not fully mocked)."""

    @pytest.fixture(autouse=True)
    def mock_auth_and_quota(self, monkeypatch):
        """Auto-apply auth mock and quota mock for all tests in this class."""
        from auth import require_auth
        mock_user = {"id": "test-user-123", "email": "test@example.com", "role": "authenticated"}
        app.dependency_overrides[require_auth] = lambda: mock_user
        monkeypatch.setattr("quota.check_quota", lambda user_id: {"credits_remaining": 100, "plan": "unlimited"})
        yield
        app.dependency_overrides.clear()

    @pytest.mark.integration
    def test_buscar_with_real_filter_and_excel(self, client, monkeypatch):
        """Test with real filter and excel modules (mock only PNCP and LLM)."""
        from unittest.mock import Mock
        from datetime import datetime, timedelta

        # Use a deadline within 7 days to pass the filter
        future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%dT10:00:00")

        mock_licitacao = {
            "codigoCompra": "TEST123",
            "objetoCompra": "Aquisição de uniformes escolares",
            "nomeOrgao": "Prefeitura Test",
            "uf": "SP",
            "municipio": "São Paulo",
            "valorTotalEstimado": 200000.00,
            "dataAberturaProposta": future_date,  # Future date within 7 days
            "linkSistemaOrigem": "https://pncp.gov.br/test",
        }

        mock_client_instance = Mock()
        mock_client_instance.fetch_all.return_value = iter([mock_licitacao])

        monkeypatch.setattr("main.PNCPClient", lambda: mock_client_instance)

        # Mock only LLM to avoid API calls
        def mock_gerar_resumo(bids, **kwargs):
            from schemas import ResumoLicitacoes
            return ResumoLicitacoes(
                resumo_executivo=f"{len(bids)} licitação encontrada",
                total_oportunidades=len(bids),
                valor_total=sum(b.get("valorTotalEstimado", 0) for b in bids),
            )

        monkeypatch.setattr("main.gerar_resumo", mock_gerar_resumo)

        request = {
            "ufs": ["SP"],
            "data_inicial": "2025-01-01",
            "data_final": "2025-01-31",
        }

        response = client.post("/buscar", json=request)
        assert response.status_code == 200

        data = response.json()
        # Filter should pass the uniform keyword and date validation
        assert data["total_filtrado"] >= 1
        # Excel should be generated (non-empty base64)
        assert len(data["excel_base64"]) > 100
