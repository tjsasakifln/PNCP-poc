"""STORY-CONV-003a AC5: POST /v1/auth/signup — tests with Stripe PM.

Mock targets:
    - `services.stripe_signup.stripe` for Stripe SDK calls.
    - `routes.auth_signup.get_supabase` is monkey-patched via the module's
      `_get_supabase` helper (patch `routes.auth_signup._get_supabase`).
    - `audit.log_audit_event` is injected by the autouse fixture below
      (mirrors tests/test_auth_signup_ratelimit.py pattern).

These tests NEVER hit real Stripe — all `stripe.Customer.create`,
`stripe.PaymentMethod.attach`, `stripe.Customer.modify`,
`stripe.Subscription.create` calls are patched.
"""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Eagerly import the module so `patch("routes.auth_signup.X")` resolves.
import routes.auth_signup as _auth_signup_module  # noqa: F401


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _mock_audit():
    """Inject audit.log_audit_event if missing (matches rate-limit tests)."""
    import audit

    if not hasattr(audit, "log_audit_event"):
        audit.log_audit_event = lambda **kwargs: None
    yield


@pytest.fixture(autouse=True)
def _stripe_env():
    """Provide Stripe env vars so service doesn't early-abort."""
    with patch.dict(
        os.environ,
        {
            "STRIPE_SECRET_KEY": "sk_test_signup_xxx",
            "STRIPE_SMARTLIC_PRO_PRICE_ID": "price_test_pro_monthly",
        },
    ):
        yield


@pytest.fixture(autouse=True)
def _passthrough_rate_limit():
    """Default: rate limiter allows all requests (tests don't exercise limits)."""
    async def _allow(key, max_req, window):
        return (True, 0)

    with patch("rate_limiter._flexible_limiter") as mock_limiter, \
         patch("config.get_feature_flag", return_value=False):
        mock_limiter.check_rate_limit = AsyncMock(side_effect=_allow)
        yield


class _FakeChain:
    """Minimal chainable Supabase mock that records updates."""

    def __init__(self, sink):
        self.sink = sink

    def update(self, payload):
        self.sink["update_payload"] = payload
        return self

    def eq(self, *a, **kw):
        self.sink.setdefault("eq_calls", []).append((a, kw))
        return self

    def execute(self):
        self.sink["executed"] = True
        return SimpleNamespace(data=[])


def _make_supabase(user_id: str = "usr-uuid-1", raise_on_create: Exception | None = None):
    """Build a Supabase client mock with auth.admin.create_user + table().update."""
    sb = MagicMock()
    profile_sink: dict = {}

    # auth.admin.create_user
    if raise_on_create is not None:
        sb.auth.admin.create_user.side_effect = raise_on_create
    else:
        created_user = SimpleNamespace(id=user_id, email="placeholder")
        sb.auth.admin.create_user.return_value = SimpleNamespace(user=created_user)

    # table().update().eq().execute()
    sb.table.return_value = _FakeChain(profile_sink)
    sb._profile_sink = profile_sink
    return sb


def _make_app():
    from routes.auth_signup import router

    app = FastAPI()
    app.include_router(router, prefix="/v1")
    return app


def _stripe_obj(**kwargs):
    """Dict-with-attr-access (matches real Stripe SDK objects)."""

    class _O(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)

    return _O(**kwargs)


# ---------------------------------------------------------------------------
# Happy path: PM + Stripe succeeds
# ---------------------------------------------------------------------------

class TestSignupWithValidPM:
    """AC1+AC2+AC3: PM provided → Stripe Customer + Subscription created."""

    def test_creates_customer_and_subscription(self):
        sb = _make_supabase(user_id="usr-001")

        with patch("routes.auth_signup._get_supabase", return_value=sb), \
             patch("services.stripe_signup.stripe") as mock_stripe:

            mock_stripe.Customer.create.return_value = _stripe_obj(id="cus_test_001")
            mock_stripe.PaymentMethod.attach.return_value = _stripe_obj(id="pm_test_001")
            mock_stripe.Customer.modify.return_value = _stripe_obj(id="cus_test_001")
            mock_stripe.Subscription.create.return_value = _stripe_obj(
                id="sub_test_001",
                trial_end=1_800_000_000,
            )
            # Real class for exception catching
            import stripe as stripe_real
            mock_stripe.error = stripe_real.error

            with TestClient(_make_app()) as client:
                resp = client.post(
                    "/v1/auth/signup",
                    json={
                        "email": "newuser@company.com",
                        "password": "Abcd1234!",
                        "stripe_payment_method_id": "pm_test_001",
                    },
                )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["user_id"] == "usr-001"
        assert body["email"] == "newuser@company.com"
        assert body["stripe_customer_id"] == "cus_test_001"
        assert body["stripe_subscription_id"] == "sub_test_001"
        assert body["trial_end_ts"] == 1_800_000_000
        assert body["subscription_status"] == "trialing"

        # Profile update should have persisted Stripe ids.
        payload = sb._profile_sink["update_payload"]
        assert payload["stripe_customer_id"] == "cus_test_001"
        assert payload["stripe_subscription_id"] == "sub_test_001"
        assert payload["stripe_default_pm_id"] == "pm_test_001"
        assert payload["subscription_status"] == "trialing"

    def test_idempotency_keys_are_set_per_step(self):
        """AC1: every Stripe call must carry a deterministic idempotency key."""
        sb = _make_supabase(user_id="usr-002")

        with patch("routes.auth_signup._get_supabase", return_value=sb), \
             patch("services.stripe_signup.stripe") as mock_stripe:

            mock_stripe.Customer.create.return_value = _stripe_obj(id="cus_002")
            mock_stripe.PaymentMethod.attach.return_value = _stripe_obj(id="pm_002")
            mock_stripe.Customer.modify.return_value = _stripe_obj(id="cus_002")
            mock_stripe.Subscription.create.return_value = _stripe_obj(
                id="sub_002",
                trial_end=1_810_000_000,
            )
            import stripe as stripe_real
            mock_stripe.error = stripe_real.error

            with TestClient(_make_app()) as client:
                client.post(
                    "/v1/auth/signup",
                    json={
                        "email": "idem@company.com",
                        "password": "Abcd1234!",
                        "stripe_payment_method_id": "pm_002",
                    },
                )

        # All four Stripe mutations must receive idempotency_key kwargs.
        for call_name, call_obj in [
            ("Customer.create", mock_stripe.Customer.create),
            ("PaymentMethod.attach", mock_stripe.PaymentMethod.attach),
            ("Customer.modify", mock_stripe.Customer.modify),
            ("Subscription.create", mock_stripe.Subscription.create),
        ]:
            assert call_obj.called, f"{call_name} must be called"
            _, kwargs = call_obj.call_args
            assert "idempotency_key" in kwargs, f"{call_name} missing idempotency_key"
            assert "signup-" in kwargs["idempotency_key"]
            assert "idem@company.com" in kwargs["idempotency_key"]


# ---------------------------------------------------------------------------
# Legacy path: no PM → user created, local trial
# ---------------------------------------------------------------------------

class TestSignupWithoutPM:
    """AC2 fallback: legacy trial path (no card required)."""

    def test_creates_user_only_and_returns_local_trial_end(self):
        sb = _make_supabase(user_id="usr-legacy-1")

        with patch("routes.auth_signup._get_supabase", return_value=sb), \
             patch("services.stripe_signup.stripe") as mock_stripe:
            # mock_stripe must still exist but must NOT be called.
            import stripe as stripe_real
            mock_stripe.error = stripe_real.error

            with TestClient(_make_app()) as client:
                resp = client.post(
                    "/v1/auth/signup",
                    json={
                        "email": "legacy@company.com",
                        "password": "Abcd1234!",
                        # stripe_payment_method_id omitted
                    },
                )

            assert mock_stripe.Customer.create.call_count == 0
            assert mock_stripe.Subscription.create.call_count == 0

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["user_id"] == "usr-legacy-1"
        assert body["stripe_customer_id"] is None
        assert body["stripe_subscription_id"] is None
        assert body["subscription_status"] == "free_trial"
        assert body["trial_end_ts"] is not None  # local +14d
        # ~14d window is 14*86400 = 1_209_600 seconds; loose upper bound.
        import time
        assert body["trial_end_ts"] > int(time.time())
        assert body["trial_end_ts"] < int(time.time()) + 15 * 86400


# ---------------------------------------------------------------------------
# Failure paths
# ---------------------------------------------------------------------------

class TestSignupFailureModes:
    """AC5 failure modes."""

    def test_invalid_pm_shape_returns_422(self):
        """Pydantic regex rejects non-`pm_` ids at the boundary (422)."""
        sb = _make_supabase()
        with patch("routes.auth_signup._get_supabase", return_value=sb):
            with TestClient(_make_app()) as client:
                resp = client.post(
                    "/v1/auth/signup",
                    json={
                        "email": "bad@company.com",
                        "password": "Abcd1234!",
                        "stripe_payment_method_id": "not_a_real_pm_id",
                    },
                )
        assert resp.status_code == 422

    def test_weak_password_returns_400(self):
        sb = _make_supabase()
        with patch("routes.auth_signup._get_supabase", return_value=sb):
            with TestClient(_make_app()) as client:
                resp = client.post(
                    "/v1/auth/signup",
                    json={"email": "weak@company.com", "password": "Abcdefgh"},
                )
        # weak password returns 400 from validate_password (service-level)
        assert resp.status_code == 400

    def test_duplicate_email_returns_409(self):
        """Supabase create_user raises "user already exists" → 409."""
        sb = _make_supabase(raise_on_create=Exception("User already registered"))
        with patch("routes.auth_signup._get_supabase", return_value=sb):
            with TestClient(_make_app()) as client:
                resp = client.post(
                    "/v1/auth/signup",
                    json={"email": "dup@company.com", "password": "Abcd1234!"},
                )
        assert resp.status_code == 409

    def test_stripe_timeout_fails_open_marks_payment_failed(self):
        """AC2 line 33: Stripe failure after user → 200 with payment_failed."""
        sb = _make_supabase(user_id="usr-timeout-1")

        with patch("routes.auth_signup._get_supabase", return_value=sb), \
             patch("services.stripe_signup.stripe") as mock_stripe:

            import stripe as stripe_real
            mock_stripe.error = stripe_real.error
            # Customer.create succeeds — so exc.customer_id should be set.
            mock_stripe.Customer.create.return_value = _stripe_obj(id="cus_to_001")
            # PaymentMethod.attach raises Stripe timeout.
            mock_stripe.PaymentMethod.attach.side_effect = stripe_real.error.APIConnectionError(
                "timeout contacting Stripe"
            )

            with TestClient(_make_app()) as client:
                resp = client.post(
                    "/v1/auth/signup",
                    json={
                        "email": "timeout@company.com",
                        "password": "Abcd1234!",
                        "stripe_payment_method_id": "pm_to_001",
                    },
                )

        # Signup still succeeds — user can log in during grace period.
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["user_id"] == "usr-timeout-1"
        assert body["stripe_subscription_id"] is None
        assert body["subscription_status"] == "payment_failed"
        # customer_id captured from the successful first step
        assert body["stripe_customer_id"] == "cus_to_001"

        # Profile was marked for recon.
        payload = sb._profile_sink["update_payload"]
        assert payload["subscription_status"] == "payment_failed"

    def test_stripe_card_declined_fails_open(self):
        """card_declined on Subscription.create → 200 payment_failed."""
        sb = _make_supabase(user_id="usr-cd-1")

        with patch("routes.auth_signup._get_supabase", return_value=sb), \
             patch("services.stripe_signup.stripe") as mock_stripe:

            import stripe as stripe_real
            mock_stripe.error = stripe_real.error
            mock_stripe.Customer.create.return_value = _stripe_obj(id="cus_cd_1")
            mock_stripe.PaymentMethod.attach.return_value = _stripe_obj(id="pm_cd_1")
            mock_stripe.Customer.modify.return_value = _stripe_obj(id="cus_cd_1")
            mock_stripe.Subscription.create.side_effect = stripe_real.error.CardError(
                "Your card was declined.", param="card", code="card_declined"
            )

            with TestClient(_make_app()) as client:
                resp = client.post(
                    "/v1/auth/signup",
                    json={
                        "email": "cd@company.com",
                        "password": "Abcd1234!",
                        "stripe_payment_method_id": "pm_cd_1",
                    },
                )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["subscription_status"] == "payment_failed"
        assert body["stripe_subscription_id"] is None

    def test_disposable_email_returns_400(self):
        """MED-SEC-001: disposable domain blocked even for signup endpoint."""
        sb = _make_supabase()
        with patch("routes.auth_signup._get_supabase", return_value=sb), \
             patch("routes.auth_signup.is_disposable_email", return_value=True):
            with TestClient(_make_app()) as client:
                resp = client.post(
                    "/v1/auth/signup",
                    json={
                        "email": "trash@mailinator.com",
                        "password": "Abcd1234!",
                    },
                )
        assert resp.status_code == 400
        assert "email" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Service-level tests (no FastAPI) for idempotency-key format
# ---------------------------------------------------------------------------

class TestStripeSignupService:
    """Direct coverage of `services/stripe_signup.py` helpers."""

    def test_missing_secret_key_raises(self):
        from services.stripe_signup import (
            StripeSignupError,
            create_customer_and_subscription,
        )
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": ""}, clear=False):
            # Explicitly remove so env helper sees absence.
            os.environ.pop("STRIPE_SECRET_KEY", None)
            with pytest.raises(StripeSignupError) as ei:
                create_customer_and_subscription(
                    email="nokey@company.com",
                    payment_method_id="pm_nokey_1",
                )
            assert ei.value.step == "config"

    def test_invalid_pm_prefix_raises_validate_step(self):
        from services.stripe_signup import (
            StripeSignupError,
            create_customer_and_subscription,
        )
        with pytest.raises(StripeSignupError) as ei:
            create_customer_and_subscription(
                email="noprefix@company.com",
                payment_method_id="garbage_id",
            )
        assert ei.value.step == "validate"

    def test_idempotency_key_is_stable_for_same_email_same_day(self):
        from services.stripe_signup import _build_idempotency_key

        k1 = _build_idempotency_key("User@Company.COM", "customer")
        k2 = _build_idempotency_key("user@company.com", "customer")
        # Case-insensitive email normalization.
        assert k1 == k2
        assert k1.startswith("signup-customer-")
        assert "user@company.com" in k1
