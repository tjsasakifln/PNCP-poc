"""
STORY-280: Boleto + PIX via Stripe — Test Suite

Tests for:
  AC1: Boleto in checkout session params
  AC2: Async payment webhook handlers (succeeded/failed)
  AC2: Checkout.session.completed with payment_status="unpaid" (no activation)
  AC5: Boleto reminder email template

Mocking Strategy:
  - Same patterns as test_stripe_webhook.py (STORY-215)
  - @patch('webhooks.stripe.stripe.Webhook.construct_event') for signature validation
  - @patch('webhooks.stripe.get_supabase') for all DB operations
  - @patch('webhooks.stripe.redis_cache') for cache operations
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock



# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_request():
    """Mock FastAPI Request with async body() method."""
    request = AsyncMock()
    request.body = AsyncMock(return_value=b'{"id":"evt_boleto_123","type":"checkout.session.completed"}')
    request.headers = {"stripe-signature": "t=1234567890,v1=valid_signature"}
    return request


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client with chainable table operations."""
    sb = MagicMock()
    _table_mocks = {}

    def _make_chain():
        chain = MagicMock()
        chain.select.return_value = chain
        chain.insert.return_value = chain
        chain.update.return_value = chain
        chain.upsert.return_value = chain
        chain.delete.return_value = chain
        chain.eq.return_value = chain
        chain.limit.return_value = chain
        chain.single.return_value = chain
        chain.order.return_value = chain
        chain.execute.return_value = Mock(data=[])
        return chain

    def table_factory(name):
        if name not in _table_mocks:
            _table_mocks[name] = _make_chain()
        return _table_mocks[name]

    sb.table = MagicMock(side_effect=table_factory)
    sb._table_mocks = _table_mocks
    return sb


def configure_idempotency(sb, *, already_processed=False, event_id="evt_boleto_123"):
    """Helper: configure idempotency check response."""
    events_chain = sb.table("stripe_webhook_events")
    if already_processed:
        events_chain.execute.return_value = Mock(data=[{"id": event_id}])
    else:
        events_chain.execute.return_value = Mock(data=[])


def configure_plan_lookup(sb, *, duration_days=30, max_searches=1000):
    """Helper: configure plans table lookup."""
    plans_chain = sb.table("plans")
    plans_chain.execute.return_value = Mock(data={"duration_days": duration_days, "max_searches": max_searches})


def make_checkout_event(
    event_id="evt_boleto_123",
    event_type="checkout.session.completed",
    payment_status="paid",
    user_id="user_boleto_123",
    plan_id="smartlic_pro",
    billing_period="monthly",
    subscription_id="sub_boleto_456",
    customer_id="cus_boleto_789",
):
    """Factory for checkout session event mocks."""
    event = Mock()
    event.id = event_id
    event.type = event_type

    data_object = Mock()
    data_object.get = lambda key, default=None: {
        "client_reference_id": user_id,
        "metadata": {"plan_id": plan_id, "billing_period": billing_period},
        "subscription": subscription_id,
        "customer": customer_id,
        "payment_status": payment_status,
    }.get(key, default)

    event.data = Mock()
    event.data.object = data_object
    return event


# ═══════════════════════════════════════════════════════════════════════
# AC1: Boleto in Checkout Session
# ═══════════════════════════════════════════════════════════════════════

class TestAC1BoletoCheckout:
    """AC1: Boleto added to payment_method_types in checkout."""

    @pytest.mark.asyncio
    @patch("routes.billing.require_auth")
    @patch("routes.billing.get_db")
    async def test_checkout_includes_boleto_payment_method(self, mock_db, mock_auth):
        """AC1: payment_method_types includes 'boleto' alongside 'card'."""
        import importlib
        import routes.billing as billing_module
        importlib.reload(billing_module)

        # Read the source to verify payment_method_types
        import inspect
        source = inspect.getsource(billing_module.create_checkout)
        assert '"boleto"' in source or "'boleto'" in source, \
            "checkout must include 'boleto' in payment_method_types"
        assert '"pix"' not in source and "'pix'" not in source, \
            "checkout must NOT include 'pix' for subscription mode"

    @pytest.mark.asyncio
    @patch("routes.billing.require_auth")
    @patch("routes.billing.get_db")
    async def test_checkout_includes_boleto_expiry_option(self, mock_db, mock_auth):
        """AC1: payment_method_options.boleto.expires_after_days = 3."""
        import inspect
        import routes.billing as billing_module

        source = inspect.getsource(billing_module.create_checkout)
        assert "expires_after_days" in source, \
            "checkout must set boleto expires_after_days"
        assert "3" in source, \
            "boleto expires_after_days should be 3"

    def test_checkout_session_params_structure(self):
        """AC1: Verify the session_params dict structure in billing.py."""
        from routes.billing import create_checkout
        import inspect
        source = inspect.getsource(create_checkout)

        # Verify structure
        assert "payment_method_types" in source
        assert "card" in source
        assert "boleto" in source
        assert "payment_method_options" in source
        assert "expires_after_days" in source


# ═══════════════════════════════════════════════════════════════════════
# AC2: Checkout completed with payment_status="unpaid" (Boleto)
# ═══════════════════════════════════════════════════════════════════════

class TestAC2CheckoutUnpaid:
    """AC2: checkout.session.completed with payment_status='unpaid' does NOT activate."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_unpaid_checkout_creates_pending_subscription(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, mock_supabase_client
    ):
        """AC2: payment_status='unpaid' creates subscription with status 'pending_payment'."""
        event = make_checkout_event(payment_status="unpaid")
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        insert_calls = []
        original_table = mock_supabase_client.table

        def track_insert(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_insert = chain.insert

                def capturing_insert(data):
                    insert_calls.append(data)
                    return original_insert(data)

                chain.insert = capturing_insert
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_insert)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"

        # Verify subscription created as pending (NOT active)
        sub_inserts = [c for c in insert_calls if "subscription_status" in c]
        assert len(sub_inserts) >= 1, f"Expected pending subscription insert, got: {insert_calls}"
        pending_insert = sub_inserts[0]
        assert pending_insert["subscription_status"] == "pending_payment"
        assert pending_insert["is_active"] is False
        assert pending_insert["credits_remaining"] == 0

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_unpaid_checkout_does_not_sync_profiles(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, mock_supabase_client
    ):
        """AC2: payment_status='unpaid' does NOT update profiles.plan_type."""
        event = make_checkout_event(payment_status="unpaid")
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        profile_updates = []
        original_table = mock_supabase_client.table

        def track_profile(table_name):
            chain = original_table(table_name)
            if table_name == "profiles":
                original_update = chain.update

                def capturing_update(data):
                    profile_updates.append(data)
                    return original_update(data)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_profile)

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        # No profile sync should happen for unpaid checkout
        plan_syncs = [u for u in profile_updates if "plan_type" in u]
        assert len(plan_syncs) == 0, \
            f"Expected no profile sync for unpaid checkout, but got: {plan_syncs}"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_paid_checkout_still_activates_immediately(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, mock_supabase_client
    ):
        """AC2: payment_status='paid' (card) still activates immediately (no regression)."""
        event = make_checkout_event(payment_status="paid")
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_plan_lookup(mock_supabase_client)

        insert_calls = []
        profile_updates = []
        original_table = mock_supabase_client.table

        def track_all(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_insert = chain.insert

                def capturing_insert(data):
                    insert_calls.append(data)
                    return original_insert(data)

                chain.insert = capturing_insert
            if table_name == "profiles":
                original_update = chain.update

                def capturing_update(data):
                    profile_updates.append(data)
                    return original_update(data)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_all)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"

        # Verify subscription created as active
        sub_inserts = [c for c in insert_calls if "subscription_status" in c]
        assert len(sub_inserts) >= 1, f"Expected active subscription insert: {insert_calls}"
        assert sub_inserts[0]["subscription_status"] == "active"
        assert sub_inserts[0]["is_active"] is True

        # Verify profile synced
        plan_syncs = [u for u in profile_updates if "plan_type" in u]
        assert len(plan_syncs) >= 1, f"Expected profile sync for paid checkout: {profile_updates}"


# ═══════════════════════════════════════════════════════════════════════
# AC2: Async Payment Succeeded (Boleto/PIX confirmed)
# ═══════════════════════════════════════════════════════════════════════

class TestAC2AsyncPaymentSucceeded:
    """AC2: checkout.session.async_payment_succeeded activates subscription."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_async_succeeded_activates_pending_subscription(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, mock_supabase_client
    ):
        """AC2: async_payment_succeeded activates pending subscription."""
        event = make_checkout_event(
            event_id="evt_async_ok_123",
            event_type="checkout.session.async_payment_succeeded",
        )
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False, event_id="evt_async_ok_123")
        configure_plan_lookup(mock_supabase_client)

        # Configure pending subscription lookup
        subs_chain = mock_supabase_client.table("user_subscriptions")
        subs_chain.execute.return_value = Mock(data=[{"id": "sub-pending-uuid"}])

        update_calls = []
        original_table = mock_supabase_client.table

        def track_update(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_update = chain.update

                def capturing_update(data):
                    update_calls.append(data)
                    return original_update(data)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_update)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"

        # Verify subscription activated
        activation_updates = [u for u in update_calls if u.get("subscription_status") == "active"]
        assert len(activation_updates) >= 1, \
            f"Expected subscription activation update, got: {update_calls}"
        activated = activation_updates[0]
        assert activated["is_active"] is True
        assert activated["credits_remaining"] == 1000

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_async_succeeded_syncs_profiles(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, mock_supabase_client
    ):
        """AC2: async_payment_succeeded syncs profiles.plan_type and subscription_status."""
        event = make_checkout_event(
            event_id="evt_async_ok_456",
            event_type="checkout.session.async_payment_succeeded",
        )
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False, event_id="evt_async_ok_456")
        configure_plan_lookup(mock_supabase_client)

        # Configure pending subscription lookup
        subs_chain = mock_supabase_client.table("user_subscriptions")
        subs_chain.execute.return_value = Mock(data=[{"id": "sub-pending-uuid"}])

        profile_updates = []
        original_table = mock_supabase_client.table

        def track_profile(table_name):
            chain = original_table(table_name)
            if table_name == "profiles":
                original_update = chain.update

                def capturing_update(data):
                    profile_updates.append(data)
                    return original_update(data)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_profile)

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        # Verify profile synced with active status
        plan_syncs = [u for u in profile_updates if "plan_type" in u]
        assert len(plan_syncs) >= 1, f"Expected profile sync: {profile_updates}"
        assert plan_syncs[0]["plan_type"] == "smartlic_pro"
        assert plan_syncs[0]["subscription_status"] == "active"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_async_succeeded_creates_new_if_no_pending(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, mock_supabase_client
    ):
        """AC2: async_payment_succeeded creates new row if no pending subscription exists."""
        event = make_checkout_event(
            event_id="evt_async_ok_789",
            event_type="checkout.session.async_payment_succeeded",
        )
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False, event_id="evt_async_ok_789")
        configure_plan_lookup(mock_supabase_client)

        # No pending subscription found
        subs_chain = mock_supabase_client.table("user_subscriptions")
        subs_chain.execute.return_value = Mock(data=[])

        insert_calls = []
        original_table = mock_supabase_client.table

        def track_insert(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_insert = chain.insert

                def capturing_insert(data):
                    insert_calls.append(data)
                    return original_insert(data)

                chain.insert = capturing_insert
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_insert)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"

        # Verify new subscription created as active
        active_inserts = [c for c in insert_calls if c.get("subscription_status") == "active"]
        assert len(active_inserts) >= 1, f"Expected new active subscription: {insert_calls}"


# ═══════════════════════════════════════════════════════════════════════
# AC2: Async Payment Failed (Boleto expired)
# ═══════════════════════════════════════════════════════════════════════

class TestAC2AsyncPaymentFailed:
    """AC2: checkout.session.async_payment_failed sends email and cleans up."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_async_failed_marks_subscription_as_payment_failed(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, mock_supabase_client
    ):
        """AC2: async_payment_failed marks pending subscription as payment_failed."""
        event = make_checkout_event(
            event_id="evt_async_fail_123",
            event_type="checkout.session.async_payment_failed",
        )
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False, event_id="evt_async_fail_123")

        update_calls = []
        original_table = mock_supabase_client.table

        def track_update(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_update = chain.update

                def capturing_update(data):
                    update_calls.append(data)
                    return original_update(data)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_update)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"

        # Verify subscription status updated to payment_failed
        failed_updates = [u for u in update_calls if u.get("subscription_status") == "payment_failed"]
        assert len(failed_updates) >= 1, \
            f"Expected payment_failed status update, got: {update_calls}"

    @pytest.mark.asyncio
    @patch('webhooks.stripe._send_async_payment_failed_email')
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_async_failed_sends_email_notification(
        self, mock_construct, mock_get_sb, mock_redis, mock_send_email,
        mock_request, mock_supabase_client
    ):
        """AC2: async_payment_failed sends boleto expired email."""
        event = make_checkout_event(
            event_id="evt_async_fail_456",
            event_type="checkout.session.async_payment_failed",
        )
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False, event_id="evt_async_fail_456")

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        # Verify email was called
        mock_send_email.assert_called_once_with(
            mock_supabase_client,
            "user_boleto_123",
            "smartlic_pro",
        )

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_async_failed_without_user_id_logs_warning(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, mock_supabase_client
    ):
        """AC2: async_payment_failed without user_id just logs warning."""
        event = make_checkout_event(
            event_id="evt_async_fail_789",
            event_type="checkout.session.async_payment_failed",
            user_id=None,
        )
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False, event_id="evt_async_fail_789")

        from webhooks.stripe import stripe_webhook
        # Should not raise
        result = await stripe_webhook(mock_request)
        assert result["status"] == "success"


# ═══════════════════════════════════════════════════════════════════════
# AC2: Event routing
# ═══════════════════════════════════════════════════════════════════════

class TestAC2EventRouting:
    """AC2: Verify new event types are routed to correct handlers."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe._handle_async_payment_succeeded')
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_async_succeeded_event_routes_to_handler(
        self, mock_construct, mock_get_sb, mock_redis, mock_handler,
        mock_request, mock_supabase_client
    ):
        """AC2: checkout.session.async_payment_succeeded routes to correct handler."""
        event = make_checkout_event(
            event_id="evt_route_ok_123",
            event_type="checkout.session.async_payment_succeeded",
        )
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False, event_id="evt_route_ok_123")

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        mock_handler.assert_called_once()

    @pytest.mark.asyncio
    @patch('webhooks.stripe._handle_async_payment_failed')
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_async_failed_event_routes_to_handler(
        self, mock_construct, mock_get_sb, mock_redis, mock_handler,
        mock_request, mock_supabase_client
    ):
        """AC2: checkout.session.async_payment_failed routes to correct handler."""
        event = make_checkout_event(
            event_id="evt_route_fail_123",
            event_type="checkout.session.async_payment_failed",
        )
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False, event_id="evt_route_fail_123")

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        mock_handler.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════
# AC5: Boleto Reminder Email Template
# ═══════════════════════════════════════════════════════════════════════

class TestAC5BoletoEmailTemplate:
    """AC5: Boleto reminder and expired email templates."""

    def test_boleto_reminder_renders_html(self):
        """AC5: Boleto reminder template renders valid HTML."""
        from templates.emails.boleto_reminder import render_boleto_reminder_email

        html = render_boleto_reminder_email(
            user_name="Joao Silva",
            plan_name="SmartLic Pro",
            boleto_due_date="28/02/2026",
        )

        assert "<!DOCTYPE html>" in html
        assert "Joao Silva" in html
        assert "SmartLic Pro" in html
        assert "28/02/2026" in html
        assert "vence amanha" in html.lower()
        assert "smartlic.tech/planos" in html

    def test_boleto_expired_renders_html(self):
        """AC2: Boleto expired template renders valid HTML."""
        from templates.emails.boleto_reminder import render_boleto_expired_email

        html = render_boleto_expired_email(
            user_name="Maria Santos",
            plan_name="SmartLic Pro",
        )

        assert "<!DOCTYPE html>" in html
        assert "Maria Santos" in html
        assert "SmartLic Pro" in html
        assert "expirou" in html.lower()
        assert "smartlic.tech/planos" in html
        assert "Gerar novo boleto" in html

    def test_boleto_reminder_is_transactional(self):
        """AC5: Boleto reminder emails are transactional (no unsubscribe link)."""
        from templates.emails.boleto_reminder import render_boleto_reminder_email

        html = render_boleto_reminder_email(
            user_name="Test",
            plan_name="SmartLic Pro",
            boleto_due_date="01/03/2026",
        )

        assert "Cancelar inscrição" not in html

    def test_boleto_expired_is_transactional(self):
        """AC2: Boleto expired emails are transactional."""
        from templates.emails.boleto_reminder import render_boleto_expired_email

        html = render_boleto_expired_email(
            user_name="Test",
            plan_name="SmartLic Pro",
        )

        assert "Cancelar inscrição" not in html


# ═══════════════════════════════════════════════════════════════════════
# AC2: Checkout.session.completed missing fields (edge cases)
# ═══════════════════════════════════════════════════════════════════════

class TestCheckoutEdgeCases:
    """Edge cases for modified checkout.session.completed handler."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_checkout_missing_user_id_returns_early(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, mock_supabase_client
    ):
        """Missing client_reference_id → early return, no crash."""
        event = make_checkout_event(user_id=None, plan_id=None)
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)
        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_checkout_default_payment_status_is_paid(
        self, mock_construct, mock_get_sb, mock_redis, mock_request, mock_supabase_client
    ):
        """Default payment_status should be 'paid' for backward compatibility."""
        # Event without payment_status field
        event = Mock()
        event.id = "evt_no_status_123"
        event.type = "checkout.session.completed"
        data_object = Mock()
        data_object.get = lambda key, default=None: {
            "client_reference_id": "user_123",
            "metadata": {"plan_id": "smartlic_pro", "billing_period": "monthly"},
            "subscription": "sub_123",
            "customer": "cus_123",
            # NOTE: no payment_status key — should default to "paid"
        }.get(key, default)
        event.data = Mock()
        event.data.object = data_object

        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False, event_id="evt_no_status_123")
        configure_plan_lookup(mock_supabase_client)

        insert_calls = []
        original_table = mock_supabase_client.table

        def track_insert(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_insert = chain.insert

                def capturing_insert(data):
                    insert_calls.append(data)
                    return original_insert(data)

                chain.insert = capturing_insert
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_insert)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"

        # Should activate (default=paid)
        active_inserts = [c for c in insert_calls if c.get("subscription_status") == "active"]
        assert len(active_inserts) >= 1, \
            f"Default payment_status should be 'paid' (activate): {insert_calls}"
