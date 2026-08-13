"""GAP-002 (#1579) — Tests for admin Command provisioning route.

Covers:
- POST /v1/admin/subscriptions/command creates Stripe Checkout session.
- Non-admin gets 403.
- Missing COMMAND_PRICE_ID env var returns 500.
- Missing STRIPE_SECRET_KEY returns 500.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake")
os.environ.setdefault("COMMAND_PRICE_ID", "price_command_test")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

from main import app  # noqa: E402
from auth import require_auth  # noqa: E402
from rbac_granular import require_admin_ops  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_client():
    fake_admin = {"id": "00000000-0000-0000-0000-00000000a001", "email": "admin@test"}
    app.dependency_overrides[require_auth] = lambda: fake_admin
    app.dependency_overrides[require_admin_ops] = lambda: fake_admin
    yield TestClient(app)
    app.dependency_overrides.pop(require_auth, None)
    app.dependency_overrides.pop(require_admin_ops, None)


@pytest.fixture
def regular_client():
    """Logged-in non-admin user — should get 403 from require_admin."""
    fake_user = {"id": "regular-user", "email": "user@test"}
    app.dependency_overrides[require_auth] = lambda: fake_user
    yield TestClient(app)
    app.dependency_overrides.pop(require_auth, None)


# ---------------------------------------------------------------------------
# POST /v1/admin/subscriptions/command
# ---------------------------------------------------------------------------


@patch("stripe.checkout.Session.create")
def test_provision_command_checkout_creates_session(mock_stripe_create, admin_client):
    """Admin creates a Command checkout session successfully."""
    mock_session = MagicMock()
    mock_session.id = "cs_test_command_123"
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_command_123"
    mock_stripe_create.return_value = mock_session

    r = admin_client.post(
        "/v1/admin/subscriptions/command",
        json={"email": "enterprise@example.com", "org_id": "org-42"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["checkout_url"] == "https://checkout.stripe.com/pay/cs_test_command_123"
    assert body["session_id"] == "cs_test_command_123"
    assert body["plan_id"] == "smartlic_command"

    # Verify Stripe was called with correct params
    call_kwargs = mock_stripe_create.call_args.kwargs
    assert call_kwargs["mode"] == "subscription"
    assert call_kwargs["customer_email"] == "enterprise@example.com"
    assert call_kwargs["metadata"]["plan_id"] == "smartlic_command"
    assert call_kwargs["metadata"]["source"] == "admin_command"
    assert call_kwargs["metadata"]["provisioned_by"] == "admin@test"
    assert call_kwargs["metadata"]["org_id"] == "org-42"
    assert len(call_kwargs["line_items"]) == 1
    assert call_kwargs["line_items"][0]["price"] == "price_command_test"


@patch("stripe.checkout.Session.create")
def test_provision_command_without_org_id(mock_stripe_create, admin_client):
    """Admin creates Command checkout without optional org_id."""
    mock_session = MagicMock()
    mock_session.id = "cs_test_no_org"
    mock_session.url = "https://checkout.stripe.com/pay/cs_test_no_org"
    mock_stripe_create.return_value = mock_session

    r = admin_client.post(
        "/v1/admin/subscriptions/command",
        json={"email": "noorganisation@example.com"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == "cs_test_no_org"
    call_kwargs = mock_stripe_create.call_args.kwargs
    assert call_kwargs["metadata"]["org_id"] == ""


def test_provision_command_rejects_non_admin(regular_client):
    """Non-admin user gets 403."""
    r = regular_client.post(
        "/v1/admin/subscriptions/command",
        json={"email": "hacker@example.com"},
    )
    assert r.status_code == 403


def test_provision_command_missing_price_id(admin_client, monkeypatch):
    """Missing COMMAND_PRICE_ID returns 500.

    Do not mock ``os.getenv`` wholesale — that also blanks
    ``SAAS_COMMERCE_ENABLED`` and 410s before the price check.
    """
    monkeypatch.setenv("COMMAND_PRICE_ID", "")
    r = admin_client.post(
        "/v1/admin/subscriptions/command",
        json={"email": "noprice@example.com"},
    )
    assert r.status_code == 500
    body = r.json()
    assert "Preco" in body.get("detail", "")


@patch.dict(os.environ, {"STRIPE_SECRET_KEY": ""})
def test_provision_command_missing_stripe_key(admin_client):
    """Missing STRIPE_SECRET_KEY returns 500."""
    r = admin_client.post(
        "/v1/admin/subscriptions/command",
        json={"email": "nostripe@example.com"},
    )
    assert r.status_code == 500
    body = r.json()
    assert "Servico" in body.get("detail", "")


@patch("stripe.checkout.Session.create")
def test_provision_command_stripe_invalid_request(mock_stripe_create, admin_client):
    """Stripe InvalidRequestError returns 400."""
    import stripe as stripe_lib
    mock_stripe_create.side_effect = stripe_lib.error.InvalidRequestError(
        message="Invalid price",
        param="price",
    )

    r = admin_client.post(
        "/v1/admin/subscriptions/command",
        json={"email": "invalid@example.com"},
    )
    assert r.status_code == 400


@patch("stripe.checkout.Session.create")
def test_provision_command_stripe_api_error(mock_stripe_create, admin_client):
    """Stripe generic error returns 503."""
    import stripe as stripe_lib
    mock_stripe_create.side_effect = stripe_lib.error.StripeError("API down")

    r = admin_client.post(
        "/v1/admin/subscriptions/command",
        json={"email": "api-down@example.com"},
    )
    assert r.status_code == 503
