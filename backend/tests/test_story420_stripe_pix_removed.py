"""
STORY-420 (EPIC-INCIDENT-2026-04-10): Remove invalid Stripe PIX payment method.

Scope:
  AC2: `backend/routes/billing.py:create_checkout` must NOT include 'pix' in
       payment_method_types and must gracefully convert Stripe
       InvalidRequestError to HTTP 400 (not 500).
  AC5: New tests cover: no PIX, card ok, boleto ok, InvalidRequestError -> 400,
       generic StripeError -> 503.

These tests run standalone (do not depend on the rest of the app) by patching
`sb_execute`, `require_auth`, `get_db`, and `stripe_lib`.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


class _FakeStripeError(Exception):
    """Base for fake stripe errors used only inside patched stripe module."""

    def __init__(self, message: str = "", request_id: str | None = None):
        super().__init__(message)
        self.request_id = request_id


class _FakeInvalidRequestError(_FakeStripeError):
    pass


def _patched_stripe(create_side_effect):
    """Build a fake stripe module injected into sys.modules via sys.modules override."""
    fake = MagicMock()

    # Mirror the public surface used by routes.billing
    fake.error = SimpleNamespace(
        InvalidRequestError=_FakeInvalidRequestError,
        StripeError=_FakeStripeError,
    )
    fake.checkout = SimpleNamespace(
        Session=SimpleNamespace(create=MagicMock(side_effect=create_side_effect))
    )
    fake.PromotionCode = SimpleNamespace(
        list=MagicMock(return_value=SimpleNamespace(data=[]))
    )
    fake.billing_portal = SimpleNamespace(
        Session=SimpleNamespace(create=MagicMock())
    )
    fake.Subscription = SimpleNamespace(retrieve=MagicMock())
    return fake


@pytest.fixture
def fake_db():
    """Build an async-chained Supabase-like db mock."""
    db = MagicMock()

    # plan lookup returns a valid plan
    plan_result = SimpleNamespace(data={"id": "smartlic_pro", "name": "SmartLic Pro", "is_active": True})
    # billing period returns a valid stripe_price_id
    bp_result = SimpleNamespace(data={"stripe_price_id": "price_test_123"})

    call_counter = {"n": 0}

    class _QueryChain:
        def __init__(self, *args, **kwargs):
            self._args = args
            self._kwargs = kwargs

        def select(self, *a, **k):
            return self

        def eq(self, *a, **k):
            return self

        def single(self):
            return self

        def order(self, *a, **k):
            return self

        def limit(self, *a, **k):
            return self

    db.table = MagicMock(return_value=_QueryChain())

    async def sb_execute_side_effect(builder):  # noqa: ARG001 — builder unused in mock
        call_counter["n"] += 1
        # First call: plan lookup. Second call: plan_billing_periods lookup.
        return plan_result if call_counter["n"] == 1 else bp_result

    return db, sb_execute_side_effect


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")


def _reload_billing_with_stripe(fake_stripe):
    """Reload `routes.billing` so its local `import stripe as stripe_lib` picks up the fake."""
    import sys
    import importlib

    sys.modules["stripe"] = fake_stripe
    # also poison common submodules in case the route touches them directly
    sys.modules["stripe.error"] = fake_stripe.error
    import routes.billing as billing_module

    return importlib.reload(billing_module)


# ═══════════════════════════════════════════════════════════════════════
# AC2: Static source validation — 'pix' must be absent
# ═══════════════════════════════════════════════════════════════════════


def test_billing_source_has_no_pix_in_payment_method_types():
    """STORY-420 AC2: static guard — payment_method_types must not contain 'pix'."""
    import inspect
    import routes.billing as billing_module

    source = inspect.getsource(billing_module.create_checkout)
    # locate the literal assignment line (tolerant to spacing)
    assignment_lines = [
        line for line in source.splitlines()
        if '"payment_method_types"' in line or "'payment_method_types'" in line
    ]
    assert assignment_lines, "payment_method_types not found in create_checkout source"
    for line in assignment_lines:
        assert '"pix"' not in line and "'pix'" not in line, (
            f"STORY-420 AC2 regression: 'pix' reintroduced to payment_method_types: {line.strip()}"
        )


def test_billing_source_still_has_card_and_boleto():
    """STORY-420: card + boleto must remain as the two allowed methods."""
    import inspect
    import routes.billing as billing_module

    source = inspect.getsource(billing_module.create_checkout)
    assert '"card"' in source
    assert '"boleto"' in source


# ═══════════════════════════════════════════════════════════════════════
# AC5: Error handling — InvalidRequestError => HTTP 400
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_checkout_invalid_request_error_returns_http_400(fake_db, mock_env):
    """AC5: Stripe InvalidRequestError bubbles up as HTTP 400 (not 500)."""
    db, sb_side_effect = fake_db
    error_to_raise = _FakeInvalidRequestError(
        "The payment method type provided: pix is invalid.",
        request_id="req_test_123",
    )
    fake_stripe = _patched_stripe(create_side_effect=error_to_raise)
    billing_module = _reload_billing_with_stripe(fake_stripe)

    with patch("routes.billing.sb_execute", AsyncMock(side_effect=sb_side_effect)):
        with pytest.raises(HTTPException) as exc_info:
            await billing_module.create_checkout(
                plan_id="smartlic_pro",
                billing_period="monthly",
                coupon=None,
                user={"id": "user_test", "email": "test@example.com"},
                db=db,
            )

    assert exc_info.value.status_code == 400
    assert "checkout" in exc_info.value.detail.lower() or "pagamento" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_checkout_generic_stripe_error_returns_http_503(fake_db, mock_env):
    """AC5: Generic StripeError maps to HTTP 503 (temporarily unavailable)."""
    db, sb_side_effect = fake_db
    fake_stripe = _patched_stripe(create_side_effect=_FakeStripeError("API down"))
    billing_module = _reload_billing_with_stripe(fake_stripe)

    with patch("routes.billing.sb_execute", AsyncMock(side_effect=sb_side_effect)):
        with pytest.raises(HTTPException) as exc_info:
            await billing_module.create_checkout(
                plan_id="smartlic_pro",
                billing_period="monthly",
                coupon=None,
                user={"id": "user_test", "email": "test@example.com"},
                db=db,
            )

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_checkout_happy_path_returns_url(fake_db, mock_env):
    """AC5: Successful checkout returns a checkout_url dict."""
    db, sb_side_effect = fake_db
    fake_session = SimpleNamespace(url="https://checkout.stripe.com/fake-session")
    fake_stripe = _patched_stripe(create_side_effect=[fake_session])  # callable with return value
    # override create to return fake_session instead of raising
    fake_stripe.checkout.Session.create = MagicMock(return_value=fake_session)
    billing_module = _reload_billing_with_stripe(fake_stripe)

    with patch("routes.billing.sb_execute", AsyncMock(side_effect=sb_side_effect)):
        result = await billing_module.create_checkout(
            plan_id="smartlic_pro",
            billing_period="monthly",
            coupon=None,
            user={"id": "user_test", "email": "test@example.com"},
            db=db,
        )

    assert result == {"checkout_url": "https://checkout.stripe.com/fake-session"}
    # Confirm the call used ONLY card + boleto (no pix)
    call_kwargs = fake_stripe.checkout.Session.create.call_args.kwargs
    assert call_kwargs["payment_method_types"] == ["card", "boleto"]
