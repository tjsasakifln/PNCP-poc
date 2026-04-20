"""Tests for POST /v1/billing/setup-intent (STORY-CONV-003b AC2).

Anonymous endpoint used by the frontend CardCollect component BEFORE the
Supabase user exists. Must:
  - return {client_secret, publishable_key} on happy path
  - 503 when Stripe keys missing
  - 503 when Stripe API raises
  - be rate-limited via the same bucket as /auth/signup
"""

from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

import pytest


def _client_with_patched_rate_limit():
    """Return a TestClient with rate-limit dependency patched to always-allow.

    The real limiter uses Redis which we can't depend on in unit tests.
    """
    from main import app
    from rate_limiter import require_rate_limit, SIGNUP_RATE_LIMIT_PER_10MIN

    # require_rate_limit returns a Depends callable. Build the real dep
    # signature then override to no-op for tests.
    async def _noop():
        return None

    real_dep = require_rate_limit(SIGNUP_RATE_LIMIT_PER_10MIN, 600)
    app.dependency_overrides[real_dep] = _noop

    client = TestClient(app)
    return client, app, real_dep


class TestSetupIntentHappyPath:
    def test_returns_client_secret_and_publishable_key(self):
        client, app, dep = _client_with_patched_rate_limit()
        try:
            with patch.dict(
                "os.environ",
                {
                    "STRIPE_SECRET_KEY": "sk_test_fake",
                    "STRIPE_PUBLISHABLE_KEY": "pk_test_fake",
                },
                clear=False,
            ):
                with patch("stripe.SetupIntent.create") as mock_create:
                    fake_intent = Mock()
                    fake_intent.client_secret = "seti_1_secret_abc"
                    mock_create.return_value = fake_intent

                    res = client.post("/v1/billing/setup-intent")

                    assert res.status_code == 200
                    body = res.json()
                    assert body["client_secret"] == "seti_1_secret_abc"
                    assert body["publishable_key"] == "pk_test_fake"

                    # Must request off_session + card-only + flag metadata
                    mock_create.assert_called_once()
                    kwargs = mock_create.call_args.kwargs
                    assert kwargs["usage"] == "off_session"
                    assert kwargs["payment_method_types"] == ["card"]
                    assert kwargs["metadata"] == {"flow": "pre_signup_trial"}
                    assert kwargs["api_key"] == "sk_test_fake"
        finally:
            app.dependency_overrides.pop(dep, None)


class TestSetupIntentMissingConfig:
    def test_503_when_stripe_secret_missing(self):
        client, app, dep = _client_with_patched_rate_limit()
        try:
            with patch.dict("os.environ", {"STRIPE_SECRET_KEY": ""}, clear=False):
                # Ensure publishable is also unset to force 503
                with patch.dict(
                    "os.environ", {"STRIPE_PUBLISHABLE_KEY": ""}, clear=False
                ):
                    res = client.post("/v1/billing/setup-intent")
                    assert res.status_code == 503
                    assert "pagamento" in res.json()["detail"].lower()
        finally:
            app.dependency_overrides.pop(dep, None)

    def test_503_when_publishable_key_missing(self):
        client, app, dep = _client_with_patched_rate_limit()
        try:
            with patch.dict(
                "os.environ",
                {"STRIPE_SECRET_KEY": "sk_x", "STRIPE_PUBLISHABLE_KEY": ""},
                clear=False,
            ):
                res = client.post("/v1/billing/setup-intent")
                assert res.status_code == 503
        finally:
            app.dependency_overrides.pop(dep, None)


class TestSetupIntentStripeError:
    def test_returns_503_on_stripe_api_failure(self):
        import stripe as stripe_lib

        client, app, dep = _client_with_patched_rate_limit()
        try:
            with patch.dict(
                "os.environ",
                {"STRIPE_SECRET_KEY": "sk_x", "STRIPE_PUBLISHABLE_KEY": "pk_x"},
                clear=False,
            ):
                with patch(
                    "stripe.SetupIntent.create",
                    side_effect=stripe_lib.error.APIConnectionError("network fail"),
                ):
                    res = client.post("/v1/billing/setup-intent")
                    assert res.status_code == 503
                    body = res.json()
                    assert "cartão" in body["detail"].lower() or "cartao" in body["detail"].lower()
        finally:
            app.dependency_overrides.pop(dep, None)
