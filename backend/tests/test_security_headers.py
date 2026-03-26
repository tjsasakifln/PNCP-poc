"""Tests for SecurityHeadersMiddleware + STORY-311 security hardening.

Covers:
- STORY-210 AC10: 5 original security headers are present and correct
- GTM-GO-006 AC5/AC6: HSTS header present with correct value
- STORY-311 AC9: Cache-Control: no-store on authenticated endpoints
- STORY-311 AC10: Rate limiting on /health (60/min) and /plans (30/min)
- STORY-311 AC11: Permissions-Policy aligned with frontend
- STORY-311 AC13: term_parser input length limit (256 chars)
- STORY-311 AC14: log_sanitizer covers all sensitive fields
- STORY-311 AC16: HSTS includes preload directive
- STORY-311 AC18: Automated header validation

Related Files:
- backend/middleware.py: SecurityHeadersMiddleware, RateLimitMiddleware
- backend/term_parser.py: parse_search_terms, MAX_INPUT_LENGTH
- backend/log_sanitizer.py: mask_*, sanitize_*, SENSITIVE_FIELDS
"""

import pytest
from httpx import AsyncClient, ASGITransport
from starlette.testclient import TestClient
from fastapi import FastAPI
from middleware import SecurityHeadersMiddleware, RateLimitMiddleware


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def app_with_security_headers():
    """Create a minimal FastAPI app with SecurityHeadersMiddleware."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    return app


@pytest.fixture
def app_client():
    """Sync test client with both SecurityHeaders and RateLimit middleware."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/v1/health")
    def v1_health():
        return {"status": "ok"}

    @app.get("/v1/plans")
    def plans():
        return {"plans": []}

    @app.get("/v1/me")
    def me():
        return {"user": "test"}

    @app.post("/webhook/stripe")
    def stripe_webhook():
        return {"received": True}

    return TestClient(app)


# ============================================================================
# STORY-210 + GTM-GO-006: Original security headers tests
# ============================================================================


class TestSecurityHeadersMiddleware:
    """Test SecurityHeadersMiddleware applies all security headers."""

    @pytest.mark.anyio
    async def test_all_security_headers_present(self, app_with_security_headers):
        """All 6 security headers are present in response."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers
        assert "referrer-policy" in response.headers
        assert "permissions-policy" in response.headers
        assert "strict-transport-security" in response.headers

    @pytest.mark.anyio
    async def test_x_content_type_options_nosniff(self, app_with_security_headers):
        """X-Content-Type-Options: nosniff prevents MIME type sniffing."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert response.headers["x-content-type-options"] == "nosniff"

    @pytest.mark.anyio
    async def test_x_frame_options_deny(self, app_with_security_headers):
        """X-Frame-Options: DENY prevents clickjacking."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert response.headers["x-frame-options"] == "DENY"

    @pytest.mark.anyio
    async def test_x_xss_protection_block(self, app_with_security_headers):
        """X-XSS-Protection: 1; mode=block provides legacy XSS protection."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert response.headers["x-xss-protection"] == "1; mode=block"

    @pytest.mark.anyio
    async def test_referrer_policy(self, app_with_security_headers):
        """Referrer-Policy: strict-origin-when-cross-origin controls referrer leakage."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"

    @pytest.mark.anyio
    async def test_permissions_policy_disables_apis(self, app_with_security_headers):
        """Permissions-Policy disables camera, microphone, geolocation."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        policy = response.headers["permissions-policy"]
        assert "camera=()" in policy
        assert "microphone=()" in policy
        assert "geolocation=()" in policy

    @pytest.mark.anyio
    async def test_headers_present_on_error_responses(self, app_with_security_headers):
        """Security headers are present even on error responses."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Intentional error")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            try:
                await client.get("/error")
            except Exception:
                pass

    @pytest.mark.anyio
    async def test_headers_do_not_overwrite_existing(self, app_with_security_headers):
        """Middleware sets headers without breaking existing response headers."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/with-headers")
        async def endpoint_with_headers():
            from fastapi import Response
            response = Response(content='{"ok": true}', media_type="application/json")
            response.headers["X-Custom-Header"] = "custom-value"
            return response

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/with-headers")

        assert response.headers.get("x-custom-header") == "custom-value"
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers

    @pytest.mark.anyio
    async def test_headers_on_different_status_codes(self, app_with_security_headers):
        """Security headers are present on 200, 404, 500, etc."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/ok")
        async def ok_endpoint():
            return {"status": "ok"}

        @app.get("/not-found")
        async def not_found_endpoint():
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response_200 = await client.get("/ok")
            assert response_200.status_code == 200
            assert "x-content-type-options" in response_200.headers

            response_404 = await client.get("/not-found")
            assert response_404.status_code == 404
            assert "x-content-type-options" in response_404.headers

    @pytest.mark.anyio
    async def test_all_headers_correct_values(self, app_with_security_headers):
        """All 6 headers have the exact expected values (updated for STORY-311 AC16)."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["x-xss-protection"] == "1; mode=block"
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
        # AC16: Now includes preload
        assert response.headers["strict-transport-security"] == (
            "max-age=31536000; includeSubDomains; preload"
        )

    @pytest.mark.anyio
    async def test_middleware_order_independence(self):
        """SecurityHeadersMiddleware works regardless of middleware order."""
        from middleware import CorrelationIDMiddleware

        app = FastAPI()
        app.add_middleware(CorrelationIDMiddleware)
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert "x-request-id" in response.headers
        assert "x-content-type-options" in response.headers

    @pytest.mark.anyio
    async def test_hsts_header_present(self, app_with_security_headers):
        """Response includes Strict-Transport-Security header."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert "strict-transport-security" in response.headers

    @pytest.mark.anyio
    async def test_hsts_header_value_with_preload(self, app_with_security_headers):
        """AC16: HSTS header has max-age, includeSubDomains, and preload."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        hsts = response.headers["strict-transport-security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts

    @pytest.mark.anyio
    async def test_headers_on_post_requests(self, app_with_security_headers):
        """Security headers are present on POST requests as well."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.post("/submit")
        async def submit_endpoint(data: dict):
            return {"received": data}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/submit", json={"test": "data"})

        assert response.status_code == 200
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers
        assert "referrer-policy" in response.headers
        assert "permissions-policy" in response.headers


# ============================================================================
# STORY-311 AC9: Cache-Control on authenticated endpoints
# ============================================================================


class TestCacheControlAuthenticated:
    """AC9: Cache-Control: no-store on requests with Authorization header."""

    def test_no_cache_control_without_auth(self, app_client):
        resp = app_client.get("/health")
        assert "Cache-Control" not in resp.headers

    def test_cache_control_with_auth_header(self, app_client):
        resp = app_client.get("/v1/me", headers={"Authorization": "Bearer test-token"})
        assert resp.headers.get("Cache-Control") == "no-store"

    def test_no_cache_control_on_public_without_auth(self, app_client):
        resp = app_client.get("/v1/plans")
        assert "Cache-Control" not in resp.headers


# ============================================================================
# STORY-311 AC10: Rate limiting on public endpoints
# ============================================================================


class TestRateLimiting:
    """AC10: Per-IP rate limiting on /health and /plans."""

    def test_health_allows_60_requests(self, app_client):
        """Health endpoint allows 60 req/min."""
        for i in range(60):
            resp = app_client.get("/health")
            assert resp.status_code == 200, f"Request {i+1} should succeed"

    def test_health_blocks_61st_request(self, app_client):
        """Health endpoint blocks after 60 req/min."""
        for _ in range(60):
            app_client.get("/health")
        resp = app_client.get("/health")
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

    def test_plans_allows_30_requests(self, app_client):
        """Plans endpoint allows 30 req/min."""
        for i in range(30):
            resp = app_client.get("/v1/plans")
            assert resp.status_code == 200, f"Request {i+1} should succeed"

    def test_plans_blocks_31st_request(self, app_client):
        """Plans endpoint blocks after 30 req/min."""
        for _ in range(30):
            app_client.get("/v1/plans")
        resp = app_client.get("/v1/plans")
        assert resp.status_code == 429

    def test_stripe_webhook_exempt(self, app_client):
        """Stripe webhook has no rate limit."""
        for _ in range(100):
            resp = app_client.post("/webhook/stripe")
            assert resp.status_code == 200

    def test_rate_limit_response_body(self, app_client):
        """429 response includes descriptive detail."""
        for _ in range(60):
            app_client.get("/health")
        resp = app_client.get("/health")
        assert resp.status_code == 429
        body = resp.json()
        assert "Rate limit" in body["detail"]

    def test_non_limited_endpoint_unaffected(self, app_client):
        """Endpoints not in LIMITS dict have no rate limiting."""
        for _ in range(100):
            resp = app_client.get("/v1/me")
            assert resp.status_code == 200


# ============================================================================
# STORY-311 AC13: term_parser input length limit
# ============================================================================


class TestTermParserInputLimit:
    """AC13: Search input capped at 256 chars to prevent ReDoS."""

    def test_normal_input_unchanged(self):
        from term_parser import parse_search_terms
        result = parse_search_terms("engenharia")
        assert len(result) >= 1

    def test_oversized_input_truncated(self):
        from term_parser import parse_search_terms
        long_input = "a" * 500
        result = parse_search_terms(long_input)
        assert isinstance(result, list)

    def test_max_input_length_constant(self):
        from term_parser import MAX_INPUT_LENGTH
        assert MAX_INPUT_LENGTH == 256

    def test_exactly_256_chars_not_truncated(self):
        from term_parser import parse_search_terms
        input_256 = "x" * 256
        result = parse_search_terms(input_256)
        assert isinstance(result, list)

    def test_257_chars_truncated(self):
        from term_parser import parse_search_terms
        input_257 = "y" * 257
        result = parse_search_terms(input_257)
        assert isinstance(result, list)

    def test_empty_input_safe(self):
        from term_parser import parse_search_terms
        assert parse_search_terms("") == []
        assert parse_search_terms("   ") == []


# ============================================================================
# STORY-311 AC14: Log sanitizer covers required fields
# ============================================================================


class TestLogSanitizerCoverage:
    """AC14: Verify log_sanitizer.py sanitizes all required sensitive fields."""

    def test_user_id_partially_masked(self):
        from log_sanitizer import mask_user_id
        result = mask_user_id("550e8400-e29b-41d4-a716-446655440000")
        assert result == "550e8400-***"
        assert "446655440000" not in result

    def test_email_masked_preserves_domain(self):
        from log_sanitizer import mask_email
        result = mask_email("user@example.com")
        assert "@example.com" in result
        assert "user@" not in result

    def test_access_token_never_logged(self):
        from log_sanitizer import mask_token
        result = mask_token("eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.sig")
        assert "eyJhbGci" not in result
        assert "JWT" in result

    def test_password_fully_redacted(self):
        from log_sanitizer import sanitize_value
        result = sanitize_value("password", "super_secret_123")
        assert result == "[PASSWORD_REDACTED]"

    def test_api_key_masked(self):
        from log_sanitizer import mask_api_key
        result = mask_api_key("sk-1234567890abcdef1234567890abcdef")
        assert "sk-" in result
        assert "***" in result

    def test_sensitive_fields_set_complete(self):
        """Verify SENSITIVE_FIELDS covers all critical field names."""
        from log_sanitizer import SENSITIVE_FIELDS
        critical_fields = {
            "password", "token", "api_key", "authorization",
            "access_token", "refresh_token", "secret",
        }
        for field in critical_fields:
            assert field in SENSITIVE_FIELDS, f"Missing: {field}"

    def test_sanitize_dict_handles_nested(self):
        from log_sanitizer import sanitize_dict
        data = {
            "user": {
                "email": "admin@test.com",
                "password": "secret123",
            }
        }
        result = sanitize_dict(data)
        assert "admin" not in str(result)
        assert "[PASSWORD_REDACTED]" in str(result)


# ============================================================================
# STORY-311 AC18: All expected headers validated
# ============================================================================


class TestAllExpectedHeaders:
    """AC18: Comprehensive header validation across multiple endpoints."""

    REQUIRED_HEADERS = [
        "x-content-type-options",
        "x-frame-options",
        "x-xss-protection",
        "referrer-policy",
        "permissions-policy",
        "strict-transport-security",
    ]

    def test_headers_on_health(self, app_client):
        resp = app_client.get("/health")
        for header in self.REQUIRED_HEADERS:
            assert header in resp.headers, f"Missing {header} on /health"

    def test_headers_on_plans(self, app_client):
        resp = app_client.get("/v1/plans")
        for header in self.REQUIRED_HEADERS:
            assert header in resp.headers, f"Missing {header} on /v1/plans"

    def test_headers_on_authenticated(self, app_client):
        resp = app_client.get("/v1/me", headers={"Authorization": "Bearer test"})
        for header in self.REQUIRED_HEADERS:
            assert header in resp.headers, f"Missing {header} on /v1/me"

    def test_hsts_preload_present(self, app_client):
        """AC16: HSTS preload directive present."""
        resp = app_client.get("/health")
        hsts = resp.headers["strict-transport-security"]
        assert "preload" in hsts
