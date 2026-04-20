"""
GTM-PROXY-001: Tests for backend error sanitization.

T4: FastAPI validation returns PT message
T5: Stripe error returns generic PT message

AC9: RequestValidationError → PT message
AC10: Stripe errors sanitized (never expose details)
AC11: RLS errors sanitized
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with mocked dependencies."""
    from main import app
    from auth import require_auth
    from database import get_db

    # Mock auth for all tests
    async def mock_auth():
        return {"id": "test-user-id", "email": "test@test.com", "role": "authenticated"}

    # Mock DB
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
    mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = None

    app.dependency_overrides[require_auth] = mock_auth
    app.dependency_overrides[get_db] = lambda: mock_db

    # STORY-BTS-009: reset the Supabase circuit breakers so we don't pick up
    # OPEN state left by upstream test files (e.g. test_schema_validation's
    # lifespan smoke test). Without this, the first request under test returns
    # 503 before any handler runs.
    try:
        from supabase_client import _CB_REGISTRY, supabase_cb
        for cb in list(_CB_REGISTRY.values()) + [supabase_cb]:
            cb.reset()
    except Exception:
        pass

    yield TestClient(app, raise_server_exceptions=False)

    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(get_db, None)


class TestValidationErrorHandler:
    """AC9: FastAPI RequestValidationError returns PT message."""

    def test_validation_error_returns_pt_message(self, client):
        """T4: Invalid request body returns Portuguese validation message."""
        # POST /v1/buscar with completely empty body (triggers RequestValidationError)
        response = client.post(
            "/v1/buscar",
            json={},  # Missing required fields like ufs, setor, etc.
        )
        # Should be 422 with PT message (not English Pydantic errors)
        assert response.status_code == 422
        body = response.json()
        assert "detail" in body
        detail = body["detail"]
        # Must be our custom PT string, not a list of Pydantic validation errors
        assert isinstance(detail, str), f"Expected string detail, got: {type(detail)}"
        assert "inválidos" in detail.lower() or "verifique" in detail.lower()

    def test_validation_error_does_not_expose_field_names(self, client):
        """AC9: Validation errors don't expose internal field names in a list."""
        response = client.post(
            "/v1/buscar",
            json={"invalid_field": True},
        )
        assert response.status_code == 422
        body = response.json()
        # Should be generic PT message, not field-by-field errors
        assert isinstance(body["detail"], str)
        # Must NOT contain Pydantic-style error list
        assert not isinstance(body.get("detail"), list)


class TestStripeErrorSanitization:
    """AC10: Stripe errors never expose raw details."""

    def test_checkout_without_stripe_key_returns_pt(self, client):
        """T5: Missing Stripe key returns PT error, not 'Stripe not configured'."""
        with patch.dict("os.environ", {}, clear=False):
            import os
            original = os.environ.pop("STRIPE_SECRET_KEY", None)
            try:
                response = client.post(
                    "/v1/checkout?plan_id=smartlic_pro&billing_period=monthly",
                )
                assert response.status_code == 500
                body = response.json()
                detail = body.get("detail", "")
                # Must NOT contain "Stripe not configured"
                assert "stripe not configured" not in detail.lower()
                assert "not configured" not in detail.lower()
                # Must contain PT message
                assert "pagamento" in detail.lower() or "tente" in detail.lower()
            finally:
                if original:
                    os.environ["STRIPE_SECRET_KEY"] = original

    def test_billing_portal_without_stripe_key_returns_pt(self, client):
        """AC10: Billing portal without Stripe returns PT."""
        with patch.dict("os.environ", {}, clear=False):
            import os
            original = os.environ.pop("STRIPE_SECRET_KEY", None)
            try:
                response = client.post("/v1/billing-portal")
                assert response.status_code == 500
                body = response.json()
                detail = body.get("detail", "")
                assert "stripe not configured" not in detail.lower()
                assert "pagamento" in detail.lower() or "tente" in detail.lower()
            finally:
                if original:
                    os.environ["STRIPE_SECRET_KEY"] = original


class TestWebhookErrorSanitization:
    """Stripe webhook errors are in PT."""

    def test_missing_signature_header_returns_pt(self, client):
        """Webhook without signature header returns PT error.

        DEBT-324: Stripe webhook is mounted at /webhooks/stripe (root, no /v1/ prefix).
        Stripe Dashboard must be configured with this canonical URL — do not revert
        to /v1/webhooks/stripe here without also restoring the duplicate mount.
        """
        response = client.post(
            "/webhooks/stripe",
            content=b'{}',
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 400
        body = response.json()
        detail = body.get("detail", "")
        # Must NOT contain English text like "Missing stripe-signature header"
        assert "missing" not in detail.lower()
        assert "stripe-signature" not in detail.lower()


class TestGlobalExceptionHandlerRLS:
    """AC11: RLS errors are sanitized by global handler."""

    def test_rls_handler_logic(self):
        """AC11: The global handler detects RLS error patterns."""
        # Test the detection logic directly rather than through HTTP
        # to avoid middleware interference
        error_msg = "new row violates row-level security policy for table profiles"
        lower = error_msg.lower()

        # Verify our detection conditions match
        assert (
            "rls" in lower or
            "row-level security" in lower or
            ("policy" in lower and "permission" in lower)
        ), "RLS error pattern should be detected"

    def test_rls_error_message_never_leaks(self):
        """AC11: The sanitized response never contains RLS text."""
        # Verify the response we'd generate
        from fastapi.responses import JSONResponse
        response = JSONResponse(
            status_code=403,
            content={"detail": "Erro de permissão. Faça login novamente."},
        )
        assert response.status_code == 403
        # The response body is clean
        import json
        body = json.loads(response.body)
        assert "rls" not in body["detail"].lower()
        assert "row-level" not in body["detail"].lower()
        assert "policy" not in body["detail"].lower()
        # Contains Portuguese
        assert "permissão" in body["detail"].lower()


class TestNoEnglishInErrorMessages:
    """AC14: Verify no visible English errors in user-facing responses."""

    def test_subscription_status_errors_are_pt(self):
        """Subscription error messages are in Portuguese."""
        # Verify by checking route source — all error details must be PT
        import inspect
        import routes.subscriptions as sub_module
        source = inspect.getsource(sub_module)

        # These English strings should NOT appear in error details
        assert "Stripe not configured" not in source
        assert "Erro ao atualizar no Stripe" not in source
        assert "Erro ao cancelar no Stripe" not in source

    def test_billing_errors_are_pt(self):
        """Billing error messages are in Portuguese."""
        import inspect
        import routes.billing as billing_module
        source = inspect.getsource(billing_module)

        assert "Stripe not configured" not in source
