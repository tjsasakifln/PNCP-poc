"""STORY-CONV-003c AC2: Trial cancel one-click via JWT token — endpoint + service tests.

Covers:
- `services/trial_cancel_token.py` — sign + verify happy path + error cases
- `routes/conta.py` — GET /v1/conta/cancelar-trial + POST /v1/conta/cancelar-trial

Mocks:
- `routes.conta.get_supabase` for DB reads/writes
- `routes.conta.stripe.Subscription` for Stripe interactions
- `os.environ["TRIAL_CANCEL_JWT_SECRET"]` via fixture for signing
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.trial_cancel_token import (
    ACTION_CANCEL_TRIAL,
    TrialCancelTokenError,
    create_cancel_trial_token,
    verify_cancel_trial_token,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _jwt_secret():
    with patch.dict(os.environ, {"TRIAL_CANCEL_JWT_SECRET": "test-secret-abcdefghijklmnopqrstuvwxyz0123456789"}):
        yield


USER_ID = "11111111-1111-1111-1111-111111111111"


def _make_app():
    from routes.conta import router

    app = FastAPI()
    app.include_router(router, prefix="/v1")
    return app


def _fake_profile(**overrides) -> dict:
    base = {
        "id": USER_ID,
        "email": "user@example.com",
        "plan_type": "free_trial",
        "subscription_status": "trialing",
        "stripe_subscription_id": "sub_test_123",
    }
    base.update(overrides)
    return base


def _fake_subscription(**overrides) -> dict:
    base = {
        "id": "uuid-sub-1",
        "plan_id": "pro",
        "stripe_subscription_id": "sub_test_123",
        "is_active": True,
        "subscription_status": "trialing",
    }
    base.update(overrides)
    return base


def _supabase_with(profile: dict | None, subscription: dict | None):
    """Build a supabase mock that returns the given profile + subscription rows."""
    sb = MagicMock()
    profile_update_sink: dict = {}
    sub_update_sink: dict = {}

    class _SelectChain:
        def __init__(self, table):
            self.table = table
            self._conditions: list = []

        def select(self, *_a, **_kw):
            return self

        def eq(self, *a, **kw):
            self._conditions.append((a, kw))
            return self

        def limit(self, _n):
            return self

        def execute(self):
            if self.table == "profiles":
                return SimpleNamespace(data=[profile] if profile else [])
            if self.table == "user_subscriptions":
                return SimpleNamespace(data=[subscription] if subscription else [])
            return SimpleNamespace(data=[])

    class _UpdateChain:
        def __init__(self, table, sink):
            self.table = table
            self.sink = sink

        def update(self, payload):
            self.sink["payload"] = payload
            return self

        def eq(self, *a, **kw):
            self.sink.setdefault("eq_calls", []).append((a, kw))
            return self

        def execute(self):
            self.sink["executed"] = True
            return SimpleNamespace(data=[])

    def table_dispatcher(name: str):
        chain = MagicMock()
        chain.select = _SelectChain(name).select
        chain.update = _UpdateChain(
            name, profile_update_sink if name == "profiles" else sub_update_sink
        ).update
        return chain

    sb.table.side_effect = table_dispatcher
    sb._profile_update_sink = profile_update_sink
    sb._sub_update_sink = sub_update_sink
    return sb


# ---------------------------------------------------------------------------
# Service: create + verify
# ---------------------------------------------------------------------------

class TestCreateAndVerifyToken:
    def test_roundtrip(self):
        token = create_cancel_trial_token(USER_ID)
        assert isinstance(token, str)
        assert len(token) > 40

        resolved = verify_cancel_trial_token(token)
        assert resolved == USER_ID

    def test_rejects_empty_user_id(self):
        with pytest.raises(TrialCancelTokenError) as exc:
            create_cancel_trial_token("")
        assert exc.value.reason == "user_id_required"

    def test_expired_token_rejected(self):
        past = datetime.now(timezone.utc) - timedelta(hours=72)
        token = create_cancel_trial_token(USER_ID, expiry_hours=1, now=past)

        with pytest.raises(TrialCancelTokenError) as exc:
            verify_cancel_trial_token(token)
        assert exc.value.reason == "expired"

    def test_invalid_signature_rejected(self):
        # Flipping a single last char is flaky: HMAC-SHA256 base64url uses
        # 43 chars × 6 bits = 258 bits for a 256-bit signature — the last
        # char has 2 padding bits. Chars in the base64url alphabet that share
        # the same top-4 bits (e.g. "A"/"B", "C"/"D") decode to IDENTICAL
        # bytes after padding strip, so a naive flip may yield the same
        # signature bytes ~6.25% of the time → test passes/fails by chance.
        #
        # Deterministic fix: replace the entire signature with "A"*len — this
        # produces all-zero decoded bytes which cannot possibly be a valid
        # HMAC-SHA256 output for the given (header, payload, secret) tuple.
        token = create_cancel_trial_token(USER_ID)
        header, payload, signature = token.split(".")
        tampered = f"{header}.{payload}.{'A' * len(signature)}"

        with pytest.raises(TrialCancelTokenError) as exc:
            verify_cancel_trial_token(tampered)
        assert exc.value.reason == "invalid_signature"

    def test_wrong_action_rejected(self):
        # Build a JWT with a different action to ensure verifier enforces it.
        import jwt as pyjwt

        payload = {
            "user_id": USER_ID,
            "action": "some_other_action",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
        }
        token = pyjwt.encode(payload, "test-secret-abcdefghijklmnopqrstuvwxyz0123456789", algorithm="HS256")

        with pytest.raises(TrialCancelTokenError) as exc:
            verify_cancel_trial_token(token)
        assert exc.value.reason == "wrong_action"

    def test_empty_token_rejected(self):
        with pytest.raises(TrialCancelTokenError) as exc:
            verify_cancel_trial_token("")
        assert exc.value.reason == "token_required"

    def test_action_claim_is_cancel_trial(self):
        import jwt as pyjwt

        token = create_cancel_trial_token(USER_ID)
        decoded = pyjwt.decode(
            token, "test-secret-abcdefghijklmnopqrstuvwxyz0123456789", algorithms=["HS256"]
        )
        assert decoded["action"] == ACTION_CANCEL_TRIAL
        assert decoded["user_id"] == USER_ID


# ---------------------------------------------------------------------------
# GET /v1/conta/cancelar-trial — info endpoint
# ---------------------------------------------------------------------------

class TestCancelTrialInfoEndpoint:
    def test_valid_token_returns_trial_info(self):
        token = create_cancel_trial_token(USER_ID)
        sb = _supabase_with(_fake_profile(), _fake_subscription())

        app = _make_app()
        with patch("routes.conta.get_supabase", return_value=sb), \
             patch("routes.conta.stripe.Subscription.retrieve") as mock_retrieve:
            mock_retrieve.return_value = {"trial_end": 1900000000}
            client = TestClient(app)
            resp = client.get(f"/v1/conta/cancelar-trial?token={token}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == USER_ID
        assert body["email"] == "user@example.com"
        assert body["trial_end_ts"] == 1900000000
        assert body["already_cancelled"] is False

    def test_expired_token_returns_410(self):
        past = datetime.now(timezone.utc) - timedelta(hours=72)
        token = create_cancel_trial_token(USER_ID, expiry_hours=1, now=past)

        app = _make_app()
        client = TestClient(app)
        resp = client.get(f"/v1/conta/cancelar-trial?token={token}")
        assert resp.status_code == 410
        assert resp.json()["detail"]["error"] == "token_expired"

    def test_invalid_signature_returns_400(self):
        # Sign the token with a DIFFERENT secret so the endpoint (running
        # under the autouse fixture secret) always reports invalid_signature.
        # A single-char flip of the last base64url char leaves ~1/16 of
        # possibilities where the decoded signature bytes still validate —
        # that flakiness caused DNS lookup errors in CI whenever the tamper
        # accidentally kept the signature valid and the handler tried to
        # call the real Supabase API.
        with patch.dict(os.environ, {"TRIAL_CANCEL_JWT_SECRET": "wrong-secret-for-tamper-test-deterministic"}):
            tampered = create_cancel_trial_token(USER_ID)

        app = _make_app()
        client = TestClient(app)
        resp = client.get(f"/v1/conta/cancelar-trial?token={tampered}")
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"] == "token_invalid"

    def test_missing_profile_returns_404(self):
        token = create_cancel_trial_token(USER_ID)
        sb = _supabase_with(None, None)

        app = _make_app()
        with patch("routes.conta.get_supabase", return_value=sb):
            client = TestClient(app)
            resp = client.get(f"/v1/conta/cancelar-trial?token={token}")
        assert resp.status_code == 404

    def test_already_cancelled_flag(self):
        token = create_cancel_trial_token(USER_ID)
        sb = _supabase_with(
            _fake_profile(subscription_status="canceled_trial"),
            _fake_subscription(subscription_status="canceled_trial", is_active=False),
        )

        app = _make_app()
        with patch("routes.conta.get_supabase", return_value=sb), \
             patch("routes.conta.stripe.Subscription.retrieve") as mock_retrieve:
            # Subscription retrieval may still succeed
            mock_retrieve.return_value = {"trial_end": 1900000000}
            client = TestClient(app)
            resp = client.get(f"/v1/conta/cancelar-trial?token={token}")

        # user_subscriptions row with is_active=False won't be returned by the
        # query filter, so the profile's subscription_status drives the answer.
        sb2 = _supabase_with(
            _fake_profile(subscription_status="canceled_trial"), None
        )
        with patch("routes.conta.get_supabase", return_value=sb2), \
             patch("routes.conta.stripe.Subscription.retrieve") as mock_retrieve:
            mock_retrieve.return_value = {"trial_end": 1900000000}
            client = TestClient(app)
            resp = client.get(f"/v1/conta/cancelar-trial?token={token}")

        assert resp.status_code == 200
        assert resp.json()["already_cancelled"] is True


# ---------------------------------------------------------------------------
# POST /v1/conta/cancelar-trial — execute endpoint
# ---------------------------------------------------------------------------

class TestCancelTrialExecuteEndpoint:
    def test_cancels_active_trial(self):
        token = create_cancel_trial_token(USER_ID)
        sb = _supabase_with(_fake_profile(), _fake_subscription())

        app = _make_app()
        with patch("routes.conta.get_supabase", return_value=sb), \
             patch("routes.conta.stripe.Subscription.cancel") as mock_cancel:
            mock_cancel.return_value = {"trial_end": 1900000000}
            client = TestClient(app)
            resp = client.post("/v1/conta/cancelar-trial", json={"token": token})

        assert resp.status_code == 200
        body = resp.json()
        assert body["cancelled"] is True
        assert body["access_until"] == 1900000000
        assert body["already_cancelled"] is False

        # Verify Stripe was called with the right sub id
        mock_cancel.assert_called_once_with("sub_test_123")
        # Verify profile update payload
        assert sb._profile_update_sink["payload"]["subscription_status"] == "canceled_trial"
        assert sb._profile_update_sink["payload"]["plan_type"] == "free_trial"

    def test_idempotent_already_cancelled(self):
        token = create_cancel_trial_token(USER_ID)
        sb = _supabase_with(
            _fake_profile(subscription_status="canceled_trial"),
            None,  # no active user_subscriptions row
        )

        app = _make_app()
        with patch("routes.conta.get_supabase", return_value=sb), \
             patch("routes.conta.stripe.Subscription.retrieve") as mock_retrieve, \
             patch("routes.conta.stripe.Subscription.cancel") as mock_cancel:
            mock_retrieve.return_value = {"trial_end": 1900000000}
            client = TestClient(app)
            resp = client.post("/v1/conta/cancelar-trial", json={"token": token})

        assert resp.status_code == 200
        body = resp.json()
        assert body["cancelled"] is True
        assert body["already_cancelled"] is True
        # Stripe.Subscription.cancel MUST NOT be called when already cancelled
        mock_cancel.assert_not_called()

    def test_stripe_failure_does_not_block_local_update(self):
        """Fail-safe: Stripe cancel errors shouldn't block local state update."""
        import stripe

        token = create_cancel_trial_token(USER_ID)
        sb = _supabase_with(_fake_profile(), _fake_subscription())

        app = _make_app()
        with patch("routes.conta.get_supabase", return_value=sb), \
             patch("routes.conta.stripe.Subscription.cancel") as mock_cancel:
            mock_cancel.side_effect = stripe.error.InvalidRequestError(
                "subscription already canceled", param="id"
            )
            client = TestClient(app)
            resp = client.post("/v1/conta/cancelar-trial", json={"token": token})

        # Endpoint returns 200 with local state updated even though Stripe errored
        assert resp.status_code == 200
        body = resp.json()
        assert body["cancelled"] is True
        # Profile still updated for billing recon to reconcile
        assert sb._profile_update_sink["payload"]["subscription_status"] == "canceled_trial"

    def test_expired_token_returns_410(self):
        past = datetime.now(timezone.utc) - timedelta(hours=72)
        token = create_cancel_trial_token(USER_ID, expiry_hours=1, now=past)

        app = _make_app()
        client = TestClient(app)
        resp = client.post("/v1/conta/cancelar-trial", json={"token": token})
        assert resp.status_code == 410
        assert resp.json()["detail"]["error"] == "token_expired"

    def test_invalid_token_returns_400(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/v1/conta/cancelar-trial", json={"token": "a" * 50}  # random noise
        )
        assert resp.status_code == 400
        assert resp.json()["detail"]["error"] == "token_invalid"

    def test_missing_user_returns_404(self):
        token = create_cancel_trial_token(USER_ID)
        sb = _supabase_with(None, None)

        app = _make_app()
        with patch("routes.conta.get_supabase", return_value=sb):
            client = TestClient(app)
            resp = client.post("/v1/conta/cancelar-trial", json={"token": token})

        assert resp.status_code == 404

    def test_token_validates_minimum_length_on_post(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.post("/v1/conta/cancelar-trial", json={"token": "short"})
        # Pydantic min_length=20 rejects before touching verifier
        assert resp.status_code == 422
