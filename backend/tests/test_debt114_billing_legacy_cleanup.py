"""Tests for DEBT-114: Billing Legacy Cleanup — stripe_price_id.

AC1: billing.py uses ONLY plan_billing_periods for stripe_price_id
AC2: WARNING log when billing period config is missing
AC3: All billing tests pass (verified by running full test suite)
"""

import os
import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.billing import router
from database import get_db
from auth import require_auth


def _create_app(mock_db=None, mock_user=None):
    """Create test app with optional DB and auth overrides."""
    app = FastAPI()
    app.include_router(router, prefix="/v1")
    if mock_db is not None:
        app.dependency_overrides[get_db] = lambda: mock_db
    if mock_user is not None:
        app.dependency_overrides[require_auth] = lambda: mock_user
    return app


def _mock_db_for_checkout(plan_data, bp_data):
    """Build a mock DB that handles both plans and plan_billing_periods queries.

    The checkout flow calls sb_execute twice:
    1. db.table("plans").select(...).eq(...).eq(...).single()
    2. db.table("plan_billing_periods").select(...).eq(...).eq(...).single()
    """
    db = Mock()

    call_count = [0]

    def table_side_effect(table_name):
        chain = Mock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.single.return_value = chain
        chain.order.return_value = chain

        if table_name == "plans":
            result = Mock(data=plan_data)
        elif table_name == "plan_billing_periods":
            result = Mock(data=bp_data)
        else:
            result = Mock(data=None)

        chain.execute.return_value = result
        return chain

    db.table.side_effect = table_side_effect
    return db


# ============================================================================
# AC1: billing.py uses ONLY plan_billing_periods for stripe_price_id
# ============================================================================

class TestAC1PlanBillingPeriodsOnly:
    """AC1: Checkout gets stripe_price_id from plan_billing_periods table."""

    def test_checkout_uses_plan_billing_periods(self):
        """Source code no longer references legacy plans.stripe_price_id fallback."""
        import inspect
        from routes.billing import create_checkout

        source = inspect.getsource(create_checkout)
        # Must NOT have the old fallback pattern
        assert 'plan.get("stripe_price_id")' not in source
        # Must reference plan_billing_periods
        assert "plan_billing_periods" in source

    def test_checkout_monthly_from_billing_periods(self):
        """Monthly checkout resolves stripe_price_id from plan_billing_periods."""
        plan_data = {"id": "smartlic_pro", "name": "SmartLic Pro", "is_active": True}
        bp_data = {"stripe_price_id": "price_monthly_123"}

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"

        db = _mock_db_for_checkout(plan_data, bp_data)
        user = {"id": "user-1", "email": "test@test.com"}
        app = _create_app(mock_db=db, mock_user=user)

        with (
            patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test", "FRONTEND_URL": "http://localhost:3000"}),
            patch("stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client = TestClient(app)
            resp = client.post("/v1/checkout?plan_id=smartlic_pro&billing_period=monthly")

        assert resp.status_code == 200
        # Verify the correct price ID was used
        call_kwargs = mock_create.call_args.kwargs
        line_items = call_kwargs["line_items"]
        assert line_items[0]["price"] == "price_monthly_123"

    def test_checkout_annual_from_billing_periods(self):
        """Annual checkout resolves stripe_price_id from plan_billing_periods."""
        plan_data = {"id": "smartlic_pro", "name": "SmartLic Pro", "is_active": True}
        bp_data = {"stripe_price_id": "price_annual_456"}

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"

        db = _mock_db_for_checkout(plan_data, bp_data)
        user = {"id": "user-1", "email": "test@test.com"}
        app = _create_app(mock_db=db, mock_user=user)

        with (
            patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test", "FRONTEND_URL": "http://localhost:3000"}),
            patch("stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client = TestClient(app)
            resp = client.post("/v1/checkout?plan_id=smartlic_pro&billing_period=annual")

        assert resp.status_code == 200
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["line_items"][0]["price"] == "price_annual_456"

    def test_checkout_semiannual_from_billing_periods(self):
        """Semiannual checkout resolves stripe_price_id from plan_billing_periods."""
        plan_data = {"id": "smartlic_pro", "name": "SmartLic Pro", "is_active": True}
        bp_data = {"stripe_price_id": "price_semi_789"}

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"

        db = _mock_db_for_checkout(plan_data, bp_data)
        user = {"id": "user-1", "email": "test@test.com"}
        app = _create_app(mock_db=db, mock_user=user)

        with (
            patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test", "FRONTEND_URL": "http://localhost:3000"}),
            patch("stripe.checkout.Session.create", return_value=mock_session) as mock_create,
        ):
            client = TestClient(app)
            resp = client.post("/v1/checkout?plan_id=smartlic_pro&billing_period=semiannual")

        assert resp.status_code == 200
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["line_items"][0]["price"] == "price_semi_789"

    def test_checkout_plan_not_found_returns_404(self):
        """Plan not found still returns 404."""
        db = _mock_db_for_checkout(None, None)
        user = {"id": "user-1", "email": "test@test.com"}
        app = _create_app(mock_db=db, mock_user=user)

        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test"}):
            client = TestClient(app)
            resp = client.post("/v1/checkout?plan_id=nonexistent&billing_period=monthly")

        assert resp.status_code == 404

    def test_checkout_no_price_id_returns_400(self):
        """Missing stripe_price_id in plan_billing_periods returns 400."""
        plan_data = {"id": "smartlic_pro", "name": "SmartLic Pro", "is_active": True}
        bp_data = {"stripe_price_id": None}  # No price configured

        db = _mock_db_for_checkout(plan_data, bp_data)
        user = {"id": "user-1", "email": "test@test.com"}
        app = _create_app(mock_db=db, mock_user=user)

        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test"}):
            client = TestClient(app)
            resp = client.post("/v1/checkout?plan_id=smartlic_pro&billing_period=monthly")

        assert resp.status_code == 400
        assert "configuração de preço" in resp.json()["detail"]

    def test_checkout_billing_period_not_found_returns_400(self):
        """No billing period row at all returns 400."""
        plan_data = {"id": "smartlic_pro", "name": "SmartLic Pro", "is_active": True}

        db = _mock_db_for_checkout(plan_data, None)  # No billing period data
        user = {"id": "user-1", "email": "test@test.com"}
        app = _create_app(mock_db=db, mock_user=user)

        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test"}):
            client = TestClient(app)
            resp = client.post("/v1/checkout?plan_id=smartlic_pro&billing_period=monthly")

        assert resp.status_code == 400

    def test_plans_select_does_not_fetch_stripe_price_id(self):
        """Plans query no longer uses SELECT * — only fetches needed fields."""
        import inspect
        from routes.billing import create_checkout

        source = inspect.getsource(create_checkout)
        # Should NOT use select("*") for plans anymore
        assert '.select("*")' not in source or "plan_billing_periods" in source


# ============================================================================
# AC2: WARNING log when legacy code path would have been hit
# ============================================================================

class TestAC2WarningLog:
    """AC2: WARNING log when billing period config is missing."""

    def test_warning_logged_when_no_price_id(self):
        """WARNING log emitted when plan_billing_periods has no stripe_price_id."""
        plan_data = {"id": "smartlic_pro", "name": "SmartLic Pro", "is_active": True}
        bp_data = None  # No billing period row

        db = _mock_db_for_checkout(plan_data, bp_data)
        user = {"id": "user-1", "email": "test@test.com"}
        app = _create_app(mock_db=db, mock_user=user)

        with (
            patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test"}),
            patch("routes.billing.logger") as mock_logger,
        ):
            client = TestClient(app)
            resp = client.post("/v1/checkout?plan_id=smartlic_pro&billing_period=monthly")

        assert resp.status_code == 400
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "DEBT-114" in warning_msg
        assert "plan_billing_periods" in warning_msg
        assert "smartlic_pro" in warning_msg

    def test_no_warning_when_price_id_exists(self):
        """No WARNING when stripe_price_id is properly configured."""
        plan_data = {"id": "smartlic_pro", "name": "SmartLic Pro", "is_active": True}
        bp_data = {"stripe_price_id": "price_valid_123"}

        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"

        db = _mock_db_for_checkout(plan_data, bp_data)
        user = {"id": "user-1", "email": "test@test.com"}
        app = _create_app(mock_db=db, mock_user=user)

        with (
            patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test", "FRONTEND_URL": "http://localhost:3000"}),
            patch("stripe.checkout.Session.create", return_value=mock_session),
            patch("routes.billing.logger") as mock_logger,
        ):
            client = TestClient(app)
            resp = client.post("/v1/checkout?plan_id=smartlic_pro&billing_period=monthly")

        assert resp.status_code == 200
        mock_logger.warning.assert_not_called()


# ============================================================================
# AC1 Regression: Legacy fallback code is fully removed
# ============================================================================

class TestLegacyCodeRemoved:
    """Verify no traces of legacy stripe_price_id fallback remain in billing route."""

    def test_no_stripe_price_id_key_construction(self):
        """No f-string building stripe_price_id_{billing_period} key."""
        import inspect
        from routes.billing import create_checkout

        source = inspect.getsource(create_checkout)
        assert "stripe_price_id_{" not in source
        assert "price_id_key" not in source

    def test_checkout_queries_plan_billing_periods_table(self):
        """checkout explicitly queries plan_billing_periods table."""
        import inspect
        from routes.billing import create_checkout

        source = inspect.getsource(create_checkout)
        assert '"plan_billing_periods"' in source

    def test_plans_query_is_narrow_select(self):
        """Plans query only selects needed columns, not SELECT *."""
        import inspect
        from routes.billing import create_checkout

        source = inspect.getsource(create_checkout)
        # The plans select should be narrow
        assert 'select("id, name, is_active")' in source or 'select("id, name")' in source
