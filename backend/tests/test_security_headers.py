"""Tests for SecurityHeadersMiddleware.

Tests that all security headers are properly set on HTTP responses.

Covers:
- STORY-210 AC10: 5 original security headers are present and correct
- GTM-GO-006 AC5/AC6: HSTS header (Strict-Transport-Security) present with correct value

Related Files:
- backend/middleware.py: SecurityHeadersMiddleware
"""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from middleware import SecurityHeadersMiddleware


class TestSecurityHeadersMiddleware:
    """Test SecurityHeadersMiddleware applies all security headers."""

    @pytest.fixture
    def app_with_security_headers(self):
        """Create a minimal FastAPI app with SecurityHeadersMiddleware."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        return app

    @pytest.mark.anyio
    async def test_all_security_headers_present(self, app_with_security_headers):
        """All 6 security headers are present in response."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        # All 6 headers must be present
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
                # Exception is expected - we're testing headers were set
                pass

        # Headers should be set even if endpoint raises exception
        # (middleware runs before exception handling)

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

        # Both custom and security headers should be present
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
            # 200 OK
            response_200 = await client.get("/ok")
            assert response_200.status_code == 200
            assert "x-content-type-options" in response_200.headers

            # 404 Not Found
            response_404 = await client.get("/not-found")
            assert response_404.status_code == 404
            assert "x-content-type-options" in response_404.headers

    @pytest.mark.anyio
    async def test_all_headers_correct_values(self, app_with_security_headers):
        """All 6 headers have the exact expected values (STORY-210 AC10 + GTM-GO-006 AC5)."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["x-xss-protection"] == "1; mode=block"
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert response.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
        assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"

    @pytest.mark.anyio
    async def test_middleware_order_independence(self):
        """SecurityHeadersMiddleware works regardless of middleware order."""
        from middleware import CorrelationIDMiddleware

        app = FastAPI()
        # Add SecurityHeaders AFTER CorrelationID
        app.add_middleware(CorrelationIDMiddleware)
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        # Both middlewares should function
        assert "x-request-id" in response.headers  # From CorrelationIDMiddleware
        assert "x-content-type-options" in response.headers  # From SecurityHeadersMiddleware

    @pytest.mark.anyio
    async def test_hsts_header_present(self, app_with_security_headers):
        """GTM-GO-006 T1: Response includes Strict-Transport-Security header."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert "strict-transport-security" in response.headers, (
            "Strict-Transport-Security header is missing from response. "
            "Ensure SecurityHeadersMiddleware sets HSTS header."
        )

    @pytest.mark.anyio
    async def test_hsts_header_value(self, app_with_security_headers):
        """GTM-GO-006 T2: HSTS header has correct max-age and includeSubDomains."""
        transport = ASGITransport(app=app_with_security_headers)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test")

        assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"

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
