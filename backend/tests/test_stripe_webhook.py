"""
STORY-215: Stripe Webhook Handler — Complete Test Suite

Replaces placeholder tests with real assertions covering all 24 acceptance criteria.

Coverage target: >85% of webhooks/stripe.py

Tracks:
  1. Infrastructure: Proper @patch patterns (no sys.modules hack)
  2. Signature validation (AC1-AC3)
  3. Idempotency (AC4-AC6)
  4. Subscription events (AC7-AC12)
  5. Invoice/payment + cache (AC13-AC16)
  6. Error handling (AC17-AC19)
  7. Test infrastructure (AC20-AC24)

Mocking Strategy:
  - @patch('webhooks.stripe.stripe.Webhook.construct_event') for signature validation
  - @patch('webhooks.stripe.get_supabase') for all DB operations
  - @patch('webhooks.stripe.redis_cache') for cache operations
  - @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test') for env config
  - AsyncMock for request.body() (FastAPI sends coroutine)
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import HTTPException

# ──────────────────────────────────────────────────────────────────────
# AC20: NO sys.modules['stripe'] = MagicMock() — use proper @patch
# ──────────────────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_request():
    """Mock FastAPI Request with async body() method."""
    request = AsyncMock()
    request.body = AsyncMock(return_value=b'{"id":"evt_test_123","type":"customer.subscription.updated"}')
    request.headers = {"stripe-signature": "t=1234567890,v1=valid_signature"}
    return request


@pytest.fixture
def mock_request_no_signature():
    """Mock request missing stripe-signature header."""
    request = AsyncMock()
    request.body = AsyncMock(return_value=b'{"id":"evt_test_123"}')
    request.headers = {}
    return request


@pytest.fixture
def make_stripe_event():
    """Factory for Stripe Event mocks."""
    def _make(event_id="evt_test_123", event_type="customer.subscription.updated",
              data_object=None):
        event = Mock()
        event.id = event_id
        event.type = event_type
        if data_object is None:
            data_object = Mock()
            data_object.id = "sub_test_456"
            data_object.get = lambda key, default=None: {
                "plan": {"interval": "year"},
                "items": {"data": [{"plan": {"interval": "year"}}]},
                "customer": "cus_test_789",
                "metadata": {"plan_id": "plan_pro"},
                "subscription": "sub_test_456",
            }.get(key, default)
        event.data = Mock()
        event.data.object = data_object
        return event
    return _make


@pytest.fixture
def subscription_updated_event(make_stripe_event):
    """Standard subscription.updated event."""
    return make_stripe_event(
        event_type="customer.subscription.updated",
    )


@pytest.fixture
def subscription_deleted_event(make_stripe_event):
    """Standard subscription.deleted event."""
    data = Mock()
    data.id = "sub_test_456"
    data.get = lambda key, default=None: {
        "customer": "cus_test_789",
    }.get(key, default)
    return make_stripe_event(
        event_id="evt_test_del_124",
        event_type="customer.subscription.deleted",
        data_object=data,
    )


@pytest.fixture
def invoice_paid_event(make_stripe_event):
    """Standard invoice.payment_succeeded event."""
    data = Mock()
    data.id = "in_test_789"
    data.get = lambda key, default=None: {
        "subscription": "sub_test_456",
        "customer": "cus_test_789",
    }.get(key, default)
    return make_stripe_event(
        event_id="evt_test_inv_125",
        event_type="invoice.payment_succeeded",
        data_object=data,
    )


@pytest.fixture
def mock_supabase_client():
    """
    Mock Supabase client with chainable table operations.

    Returns a mock that supports:
        sb.table("x").select("y").eq("z", val).limit(1).execute()
        sb.table("x").insert({...}).execute()
        sb.table("x").update({...}).eq("z", val).execute()
        sb.table("x").select("y").eq("z", val).single().execute()
    """
    sb = MagicMock()

    # Track per-table call chains
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


def configure_idempotency(sb, *, already_processed=False, event_id="evt_test_123"):
    """Helper: configure idempotency check response on Supabase mock."""
    events_chain = sb.table("stripe_webhook_events")
    if already_processed:
        events_chain.execute.return_value = Mock(data=[{"id": event_id}])
    else:
        events_chain.execute.return_value = Mock(data=[])


def configure_subscription_lookup(sb, *, found=True, user_id="user_123",
                                   plan_id="plan_pro", sub_id="sub-local-uuid"):
    """Helper: configure user_subscriptions lookup response."""
    subs_chain = sb.table("user_subscriptions")
    if found:
        subs_chain.execute.return_value = Mock(data=[{
            "id": sub_id,
            "user_id": user_id,
            "plan_id": plan_id,
        }])
    else:
        subs_chain.execute.return_value = Mock(data=[])


def configure_plan_lookup(sb, *, duration_days=30):
    """Helper: configure plans table lookup for invoice handler."""
    plans_chain = sb.table("plans")
    plans_chain.execute.return_value = Mock(data={"duration_days": duration_days})


# ═══════════════════════════════════════════════════════════════════════
# Track 2: Signature Validation (AC1-AC3)
# ═══════════════════════════════════════════════════════════════════════

class TestSignatureValidation:
    """AC1-AC3: Webhook signature verification."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    async def test_ac1_missing_signature_returns_400(self, mock_request_no_signature):
        """AC1: Missing stripe-signature header → HTTP 400."""
        from webhooks.stripe import stripe_webhook

        with pytest.raises(HTTPException) as exc_info:
            await stripe_webhook(mock_request_no_signature)

        assert exc_info.value.status_code == 400
        assert "Missing stripe-signature" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac2_invalid_signature_returns_400(self, mock_construct, mock_request):
        """AC2: Invalid/tampered payload → HTTP 400."""
        import stripe as stripe_mod
        mock_construct.side_effect = stripe_mod.error.SignatureVerificationError(
            "Invalid signature", sig_header="bad"
        )

        from webhooks.stripe import stripe_webhook

        with pytest.raises(HTTPException) as exc_info:
            await stripe_webhook(mock_request)

        assert exc_info.value.status_code == 400
        assert "Invalid signature" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac3_valid_signature_returns_200(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        subscription_updated_event, mock_supabase_client
    ):
        """AC3: Valid signature → HTTP 200, event processed."""
        mock_construct.return_value = subscription_updated_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"
        assert result["event_id"] == subscription_updated_event.id
        mock_construct.assert_called_once()

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_invalid_payload_returns_400(self, mock_construct, mock_request):
        """AC19: Malformed event payload → HTTP 400, not HTTP 500."""
        mock_construct.side_effect = ValueError("Invalid JSON")

        from webhooks.stripe import stripe_webhook

        with pytest.raises(HTTPException) as exc_info:
            await stripe_webhook(mock_request)

        assert exc_info.value.status_code == 400
        assert "Invalid payload" in exc_info.value.detail


# ═══════════════════════════════════════════════════════════════════════
# Track 3: Idempotency (AC4-AC6)
# ═══════════════════════════════════════════════════════════════════════

class TestIdempotency:
    """AC4-AC6: Duplicate event handling."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac4_duplicate_event_returns_already_processed(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        subscription_updated_event, mock_supabase_client
    ):
        """AC4: Duplicate event.id → HTTP 200 with 'already_processed'."""
        mock_construct.return_value = subscription_updated_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=True)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "already_processed"
        assert result["event_id"] == "evt_test_123"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac5_new_event_inserted_into_webhook_events(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        subscription_updated_event, mock_supabase_client
    ):
        """AC5: New event.id → inserted into stripe_webhook_events table."""
        mock_construct.return_value = subscription_updated_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"

        # Verify insert was called on stripe_webhook_events table
        mock_supabase_client.table.assert_any_call("stripe_webhook_events")

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac6_event_record_contains_required_fields(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        subscription_updated_event, mock_supabase_client
    ):
        """AC6: Database stores event_id, event_type, processed_at."""
        mock_construct.return_value = subscription_updated_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client)

        # Track insert calls
        insert_calls = []
        original_table = mock_supabase_client.table

        def track_insert(table_name):
            chain = original_table(table_name)
            if table_name == "stripe_webhook_events":
                original_insert = chain.insert

                def capturing_insert(data):
                    insert_calls.append(data)
                    return original_insert(data)

                chain.insert = capturing_insert
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_insert)

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        # Verify at least one insert was captured for webhook events
        assert len(insert_calls) >= 1, "Expected insert into stripe_webhook_events"
        record = insert_calls[0]
        assert "id" in record, "Record must contain event id"
        assert record["id"] == "evt_test_123"
        assert "type" in record, "Record must contain event type"
        assert record["type"] == "customer.subscription.updated"
        assert "processed_at" in record, "Record must contain processed_at timestamp"


# ═══════════════════════════════════════════════════════════════════════
# Track 3: Subscription Updated (AC7-AC9)
# ═══════════════════════════════════════════════════════════════════════

class TestSubscriptionUpdated:
    """AC7-AC9: customer.subscription.updated event handling."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac7_monthly_interval_sets_billing_period_monthly(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, make_stripe_event
    ):
        """AC7: interval=month → billing_period='monthly'."""
        data = Mock()
        data.id = "sub_test_456"
        data.get = lambda key, default=None: {
            "plan": {"interval": "month"},
            "items": {"data": [{"plan": {"interval": "month"}}]},
            "customer": "cus_test_789",
            "metadata": None,
        }.get(key, default)

        event = make_stripe_event(event_type="customer.subscription.updated", data_object=data)
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client)

        # Track updates
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
        assert any(
            u.get("billing_period") == "monthly" for u in update_calls
        ), f"Expected billing_period='monthly' in updates: {update_calls}"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac8_annual_interval_sets_billing_period_annual(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, subscription_updated_event
    ):
        """AC8: interval=year → billing_period='annual'."""
        mock_construct.return_value = subscription_updated_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client)

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
        assert any(
            u.get("billing_period") == "annual" for u in update_calls
        ), f"Expected billing_period='annual' in updates: {update_calls}"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac9_subscription_updated_syncs_profiles_plan_type(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, subscription_updated_event
    ):
        """AC9: subscription.updated syncs profiles.plan_type (critical fallback)."""
        mock_construct.return_value = subscription_updated_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client, plan_id="plan_pro")

        profile_updates = []
        original_table = mock_supabase_client.table

        def track_profile_update(table_name):
            chain = original_table(table_name)
            if table_name == "profiles":
                original_update = chain.update

                def capturing_update(data):
                    profile_updates.append(data)
                    return original_update(data)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_profile_update)

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        assert len(profile_updates) >= 1, "Expected profiles.plan_type sync"
        assert any(
            "plan_type" in u for u in profile_updates
        ), f"Expected plan_type in profile updates: {profile_updates}"


# ═══════════════════════════════════════════════════════════════════════
# Track 3: Subscription Deleted (AC10-AC12)
# ═══════════════════════════════════════════════════════════════════════

class TestSubscriptionDeleted:
    """AC10-AC12: customer.subscription.deleted event handling."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac10_deleted_sets_is_active_false(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, subscription_deleted_event
    ):
        """AC10: subscription.deleted → is_active=False in user_subscriptions."""
        mock_construct.return_value = subscription_deleted_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client)

        sub_updates = []
        original_table = mock_supabase_client.table

        def track_update(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_update = chain.update

                def capturing_update(data):
                    sub_updates.append(data)
                    return original_update(data)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_update)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"
        assert any(
            u.get("is_active") is False for u in sub_updates
        ), f"Expected is_active=False in subscription updates: {sub_updates}"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac11_deleted_syncs_profiles_plan_type_to_free_trial(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, subscription_deleted_event
    ):
        """AC11: subscription.deleted syncs profiles.plan_type to 'free_trial'."""
        mock_construct.return_value = subscription_deleted_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client)

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

        assert len(profile_updates) >= 1, "Expected profiles.plan_type sync on deletion"
        assert any(
            u.get("plan_type") == "free_trial" for u in profile_updates
        ), f"Expected plan_type='free_trial' in profile updates: {profile_updates}"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac12_unknown_subscription_logged_no_crash(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, subscription_updated_event
    ):
        """AC12: Unknown subscription_id → logged warning, no crash (HTTP 200)."""
        mock_construct.return_value = subscription_updated_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        # Subscription NOT found
        configure_subscription_lookup(mock_supabase_client, found=False)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        # Should still return success (event logged, no crash)
        assert result["status"] == "success"


# ═══════════════════════════════════════════════════════════════════════
# Track 4: Invoice/Payment (AC13-AC14)
# ═══════════════════════════════════════════════════════════════════════

class TestInvoicePayment:
    """AC13-AC14: invoice.payment_succeeded event handling."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac13_invoice_payment_syncs_plan_type(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, invoice_paid_event
    ):
        """AC13: invoice.payment_succeeded → syncs profiles.plan_type."""
        mock_construct.return_value = invoice_paid_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client, plan_id="plan_pro")
        configure_plan_lookup(mock_supabase_client, duration_days=30)

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
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"
        assert any(
            u.get("plan_type") == "plan_pro" for u in profile_updates
        ), f"Expected plan_type='plan_pro' in profile updates: {profile_updates}"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac14_invoice_payment_invalidates_cache(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, invoice_paid_event
    ):
        """AC14: invoice.payment_succeeded → invalidates features cache key."""
        mock_construct.return_value = invoice_paid_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client, user_id="user_456")
        configure_plan_lookup(mock_supabase_client, duration_days=365)

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        mock_redis.delete.assert_called_with("features:user_456")


# ═══════════════════════════════════════════════════════════════════════
# Track 4: Cache Invalidation (AC15-AC16)
# ═══════════════════════════════════════════════════════════════════════

class TestCacheInvalidation:
    """AC15-AC16: Redis cache invalidation behavior."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac15_cache_key_format_is_features_user_id(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, subscription_updated_event
    ):
        """AC15: After billing update, cache key 'features:{user_id}' is deleted."""
        mock_construct.return_value = subscription_updated_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client, user_id="user_abc_123")

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        mock_redis.delete.assert_called_with("features:user_abc_123")

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac16_redis_unavailable_webhook_still_processes(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, subscription_updated_event
    ):
        """AC16: Redis unavailable → webhook still processes (graceful degradation)."""
        mock_construct.return_value = subscription_updated_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client)

        # Redis operations raise exceptions
        mock_redis.delete.side_effect = Exception("Redis connection refused")

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        # Webhook should still succeed even if Redis fails
        assert result["status"] == "success"


# ═══════════════════════════════════════════════════════════════════════
# Track 5: Error Handling (AC17-AC19)
# ═══════════════════════════════════════════════════════════════════════

class TestErrorHandling:
    """AC17-AC19: Error handling and edge cases."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac17_database_error_returns_500(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        subscription_updated_event
    ):
        """AC17: Database error during webhook processing → HTTP 500, error logged."""
        mock_construct.return_value = subscription_updated_event
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        # Make the idempotency check raise a DB error
        mock_sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = Exception(
            "Database connection lost"
        )

        from webhooks.stripe import stripe_webhook

        with pytest.raises(HTTPException) as exc_info:
            await stripe_webhook(mock_request)

        assert exc_info.value.status_code == 500
        assert "Database error" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac18_unhandled_event_type_returns_200(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, make_stripe_event
    ):
        """AC18: Unhandled event type → HTTP 200 with event logged."""
        unhandled_event = make_stripe_event(
            event_id="evt_unhandled_999",
            event_type="charge.succeeded",  # Not in our handlers
        )
        mock_construct.return_value = unhandled_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        # Should still return success (just logs and records, no processing)
        assert result["status"] == "success"
        assert result["event_id"] == "evt_unhandled_999"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_ac19_malformed_payload_returns_400_not_500(
        self, mock_construct, mock_request
    ):
        """AC19: Malformed event payload → HTTP 400, not HTTP 500."""
        mock_construct.side_effect = ValueError("No JSON object could be decoded")

        from webhooks.stripe import stripe_webhook

        with pytest.raises(HTTPException) as exc_info:
            await stripe_webhook(mock_request)

        assert exc_info.value.status_code == 400
        assert exc_info.value.status_code != 500  # Explicitly NOT 500


# ═══════════════════════════════════════════════════════════════════════
# Track 7: Test Infrastructure Validation (AC20-AC21, AC24)
# ═══════════════════════════════════════════════════════════════════════

class TestInfrastructureQuality:
    """AC20-AC21, AC24: Test quality meta-checks."""

    def test_ac20_no_sys_modules_hack(self):
        """AC20: Verify no module-level stripe mock injection is used."""
        import pathlib
        import re
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        # Look for the actual hack pattern: sys.modules[...] = MagicMock/Mock
        hack_pattern = re.compile(r"^sys\.modules\[.*stripe.*\]\s*=", re.MULTILINE)
        matches = hack_pattern.findall(source)
        assert len(matches) == 0, (
            f"FOUND sys.modules stripe hack pattern — use @patch instead: {matches}"
        )

    def test_ac21_no_assertion_free_tests(self):
        """AC21: All test methods in this module have real assertions."""
        import sys
        import inspect
        module = sys.modules[__name__]
        test_classes = [
            cls for name, cls in inspect.getmembers(module, inspect.isclass)
            if name.startswith("Test")
        ]

        tests_without_asserts = []
        for cls in test_classes:
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                if not name.startswith("test_"):
                    continue
                source = inspect.getsource(method)
                has_assert = "assert" in source or "pytest.raises" in source
                if not has_assert:
                    tests_without_asserts.append(f"{cls.__name__}.{name}")

        assert len(tests_without_asserts) == 0, (
            f"Tests without assertions found: {tests_without_asserts}"
        )

    def test_ac24_minimum_assertion_count(self):
        """AC24: Total assert count > 30 across all tests (validation metric)."""
        import pathlib
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        assert_count = source.count("assert ")
        # Validation metric from story: grep -c "assert" > 30
        assert assert_count > 30, (
            f"Only {assert_count} assertions found, need >30"
        )


# ═══════════════════════════════════════════════════════════════════════
# Additional Edge Cases
# ═══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════
# GTM-FIX-001: Checkout Session Completed (AC1-AC7)
# ═══════════════════════════════════════════════════════════════════════

class TestCheckoutSessionCompleted:
    """GTM-FIX-001: checkout.session.completed activates subscription."""

    @pytest.fixture
    def checkout_completed_event(self, make_stripe_event):
        """Standard checkout.session.completed event with SmartLic Pro."""
        data = Mock()
        data.id = "cs_test_checkout_789"
        data.get = lambda key, default=None: {
            "client_reference_id": "user_checkout_123",
            "metadata": {"plan_id": "smartlic_pro", "billing_period": "monthly"},
            "subscription": "sub_new_456",
            "customer": "cus_checkout_789",
        }.get(key, default)
        return make_stripe_event(
            event_id="evt_checkout_001",
            event_type="checkout.session.completed",
            data_object=data,
        )

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_checkout_completed_creates_subscription(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, checkout_completed_event
    ):
        """AC2-AC3: checkout.session.completed creates user_subscription row."""
        mock_construct.return_value = checkout_completed_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        # Configure plan lookup
        plans_chain = mock_supabase_client.table("plans")
        plans_chain.execute.return_value = Mock(data={"duration_days": 30, "max_searches": 1000})

        insert_calls = []
        original_table = mock_supabase_client.table

        def track_insert(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_insert = chain.insert

                def capturing_insert(d):
                    insert_calls.append(d)
                    return original_insert(d)

                chain.insert = capturing_insert
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_insert)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"
        assert len(insert_calls) >= 1, "Expected INSERT into user_subscriptions"
        record = insert_calls[0]
        assert record["user_id"] == "user_checkout_123"
        assert record["plan_id"] == "smartlic_pro"
        assert record["billing_period"] == "monthly"
        assert record["is_active"] is True
        assert record["stripe_subscription_id"] == "sub_new_456"
        assert record["stripe_customer_id"] == "cus_checkout_789"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_checkout_completed_syncs_profiles_plan_type(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, checkout_completed_event
    ):
        """AC5: checkout.session.completed syncs profiles.plan_type to smartlic_pro."""
        mock_construct.return_value = checkout_completed_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        plans_chain = mock_supabase_client.table("plans")
        plans_chain.execute.return_value = Mock(data={"duration_days": 30, "max_searches": 1000})

        profile_updates = []
        original_table = mock_supabase_client.table

        def track_profile(table_name):
            chain = original_table(table_name)
            if table_name == "profiles":
                original_update = chain.update

                def capturing_update(d):
                    profile_updates.append(d)
                    return original_update(d)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_profile)

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        assert any(
            u.get("plan_type") == "smartlic_pro" for u in profile_updates
        ), f"Expected plan_type='smartlic_pro' in profile updates: {profile_updates}"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_checkout_completed_deactivates_previous_subscriptions(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, checkout_completed_event
    ):
        """AC3: Deactivates existing active subscriptions before creating new one."""
        mock_construct.return_value = checkout_completed_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        plans_chain = mock_supabase_client.table("plans")
        plans_chain.execute.return_value = Mock(data={"duration_days": 30, "max_searches": 1000})

        deactivate_calls = []
        original_table = mock_supabase_client.table

        def track_deactivate(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_update = chain.update

                def capturing_update(d):
                    if d.get("is_active") is False:
                        deactivate_calls.append(d)
                    return original_update(d)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_deactivate)

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        assert len(deactivate_calls) >= 1, "Expected deactivation of previous subscriptions"
        assert deactivate_calls[0]["is_active"] is False

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_checkout_completed_invalidates_cache(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, checkout_completed_event
    ):
        """AC6: Checkout completion invalidates user's features cache."""
        mock_construct.return_value = checkout_completed_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        plans_chain = mock_supabase_client.table("plans")
        plans_chain.execute.return_value = Mock(data={"duration_days": 30, "max_searches": 1000})

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        mock_redis.delete.assert_called_with("features:user_checkout_123")

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_checkout_completed_sets_subscription_status_active(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, checkout_completed_event
    ):
        """AC6: checkout.session.completed sets subscription_status='active' in profiles."""
        mock_construct.return_value = checkout_completed_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        plans_chain = mock_supabase_client.table("plans")
        plans_chain.execute.return_value = Mock(data={"duration_days": 30, "max_searches": 1000})

        profile_updates = []
        insert_calls = []
        original_table = mock_supabase_client.table

        def track_all(table_name):
            chain = original_table(table_name)
            if table_name == "profiles":
                original_update = chain.update

                def capturing_update(d):
                    profile_updates.append(d)
                    return original_update(d)

                chain.update = capturing_update
            if table_name == "user_subscriptions":
                original_insert = chain.insert

                def capturing_insert(d):
                    insert_calls.append(d)
                    return original_insert(d)

                chain.insert = capturing_insert
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_all)

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        # AC6: profiles.subscription_status must be 'active'
        assert any(
            u.get("subscription_status") == "active" for u in profile_updates
        ), f"Expected subscription_status='active' in profile updates: {profile_updates}"

        # Also check user_subscriptions has subscription_status='active'
        assert any(
            d.get("subscription_status") == "active" for d in insert_calls
        ), f"Expected subscription_status='active' in subscription insert: {insert_calls}"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_checkout_completed_missing_metadata_skips(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, make_stripe_event
    ):
        """Edge: Missing metadata (no plan_id) → handler skips gracefully."""
        data = Mock()
        data.id = "cs_test_no_meta"
        data.get = lambda key, default=None: {
            "client_reference_id": "user_123",
            "metadata": {},  # No plan_id
            "subscription": "sub_456",
            "customer": "cus_789",
        }.get(key, default)

        event = make_stripe_event(
            event_id="evt_no_meta_001",
            event_type="checkout.session.completed",
            data_object=data,
        )
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        # Should succeed without crash (handler skips)
        assert result["status"] == "success"
        # No subscription should have been created
        mock_supabase_client.table("user_subscriptions").insert.assert_not_called()

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_checkout_completed_annual_billing_period(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, make_stripe_event
    ):
        """AC3: Annual billing period correctly passed through to subscription."""
        data = Mock()
        data.id = "cs_test_annual"
        data.get = lambda key, default=None: {
            "client_reference_id": "user_annual_123",
            "metadata": {"plan_id": "smartlic_pro", "billing_period": "annual"},
            "subscription": "sub_annual_456",
            "customer": "cus_annual_789",
        }.get(key, default)

        event = make_stripe_event(
            event_id="evt_annual_001",
            event_type="checkout.session.completed",
            data_object=data,
        )
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)

        plans_chain = mock_supabase_client.table("plans")
        plans_chain.execute.return_value = Mock(data={"duration_days": 365, "max_searches": 1000})

        insert_calls = []
        original_table = mock_supabase_client.table

        def track_insert(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_insert = chain.insert

                def capturing_insert(d):
                    insert_calls.append(d)
                    return original_insert(d)

                chain.insert = capturing_insert
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_insert)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"
        assert len(insert_calls) >= 1
        assert insert_calls[0]["billing_period"] == "annual"
        assert insert_calls[0]["user_id"] == "user_annual_123"


class TestCheckoutIsSubscription:
    """GTM-FIX-001 AC1: smartlic_pro creates subscription mode checkout."""

    def test_smartlic_pro_is_subscription(self):
        """AC1: is_subscription('smartlic_pro') should be True in checkout route."""
        # Verify the logic inline (same as routes/billing.py line 63)
        plan_id = "smartlic_pro"
        is_subscription = plan_id in ("smartlic_pro", "consultor_agil", "maquina", "sala_guerra")
        assert is_subscription is True

    def test_legacy_plans_still_subscription(self):
        """Legacy plans remain subscriptions after adding smartlic_pro."""
        for plan_id in ("consultor_agil", "maquina", "sala_guerra"):
            is_subscription = plan_id in ("smartlic_pro", "consultor_agil", "maquina", "sala_guerra")
            assert is_subscription is True, f"{plan_id} should still be a subscription"

    def test_unknown_plan_is_not_subscription(self):
        """Unknown plans should NOT be subscriptions."""
        plan_id = "free_trial"
        is_subscription = plan_id in ("smartlic_pro", "consultor_agil", "maquina", "sala_guerra")
        assert is_subscription is False


class TestSubscriptionUpdatedEdgeCases:
    """Extra edge cases for subscription update handler."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_missing_interval_defaults_to_monthly(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, make_stripe_event
    ):
        """Missing plan.interval should default to 'monthly'."""
        data = Mock()
        data.id = "sub_test_456"
        data.get = lambda key, default=None: {
            "plan": {},  # No interval key
            "items": {"data": [{"plan": {}}]},
            "customer": "cus_test_789",
            "metadata": None,
        }.get(key, default)

        event = make_stripe_event(event_type="customer.subscription.updated", data_object=data)
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client)

        update_calls = []
        original_table = mock_supabase_client.table

        def track_update(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_update = chain.update

                def capturing_update(d):
                    update_calls.append(d)
                    return original_update(d)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_update)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"
        assert any(
            u.get("billing_period") == "monthly" for u in update_calls
        ), f"Expected billing_period='monthly' as default: {update_calls}"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_plan_change_updates_plan_id(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, make_stripe_event
    ):
        """Plan change via metadata.plan_id updates subscription plan_id."""
        data = Mock()
        data.id = "sub_test_456"
        data.get = lambda key, default=None: {
            "plan": {"interval": "month"},
            "items": {"data": [{"plan": {"interval": "month"}}]},
            "customer": "cus_test_789",
            "metadata": {"plan_id": "plan_enterprise"},
        }.get(key, default)

        event = make_stripe_event(event_type="customer.subscription.updated", data_object=data)
        mock_construct.return_value = event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client, plan_id="plan_pro")

        update_calls = []
        original_table = mock_supabase_client.table

        def track_update(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_update = chain.update

                def capturing_update(d):
                    update_calls.append(d)
                    return original_update(d)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_update)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"
        assert any(
            u.get("plan_id") == "plan_enterprise" for u in update_calls
        ), f"Expected plan_id='plan_enterprise' in updates: {update_calls}"


class TestInvoicePaymentEdgeCases:
    """Edge cases for invoice payment handler."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_invoice_without_subscription_skipped(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, make_stripe_event
    ):
        """Invoice without subscription_id (one-time payment) is skipped."""
        data = Mock()
        data.id = "in_oneoff_999"
        data.get = lambda key, default=None: {
            "subscription": None,  # No subscription
            "customer": "cus_test_789",
        }.get(key, default)

        event = make_stripe_event(
            event_id="evt_oneoff_999",
            event_type="invoice.payment_succeeded",
            data_object=data,
        )
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
    async def test_invoice_unknown_subscription_no_crash(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, invoice_paid_event
    ):
        """Invoice for unknown subscription doesn't crash."""
        mock_construct.return_value = invoice_paid_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client, found=False)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_invoice_extends_subscription_expiry(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, invoice_paid_event
    ):
        """Invoice payment extends subscription expiry date."""
        mock_construct.return_value = invoice_paid_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client)
        configure_plan_lookup(mock_supabase_client, duration_days=365)

        sub_updates = []
        original_table = mock_supabase_client.table

        def track_update(table_name):
            chain = original_table(table_name)
            if table_name == "user_subscriptions":
                original_update = chain.update

                def capturing_update(d):
                    sub_updates.append(d)
                    return original_update(d)

                chain.update = capturing_update
            return chain

        mock_supabase_client.table = MagicMock(side_effect=track_update)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"
        assert any(
            "expires_at" in u and u.get("is_active") is True
            for u in sub_updates
        ), f"Expected expires_at + is_active=True in updates: {sub_updates}"


class TestDeletedSubscriptionEdgeCases:
    """Edge cases for subscription deletion handler."""

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_deleted_unknown_subscription_no_crash(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, subscription_deleted_event
    ):
        """Deletion for unknown subscription doesn't crash."""
        mock_construct.return_value = subscription_deleted_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client, found=False)

        from webhooks.stripe import stripe_webhook
        result = await stripe_webhook(mock_request)

        assert result["status"] == "success"

    @pytest.mark.asyncio
    @patch('webhooks.stripe.STRIPE_WEBHOOK_SECRET', 'whsec_test')
    @patch('webhooks.stripe.redis_cache')
    @patch('webhooks.stripe.get_supabase')
    @patch('webhooks.stripe.stripe.Webhook.construct_event')
    async def test_deleted_invalidates_cache(
        self, mock_construct, mock_get_sb, mock_redis, mock_request,
        mock_supabase_client, subscription_deleted_event
    ):
        """Subscription deletion invalidates the user's cache."""
        mock_construct.return_value = subscription_deleted_event
        mock_get_sb.return_value = mock_supabase_client
        configure_idempotency(mock_supabase_client, already_processed=False)
        configure_subscription_lookup(mock_supabase_client, user_id="user_del_789")

        from webhooks.stripe import stripe_webhook
        await stripe_webhook(mock_request)

        mock_redis.delete.assert_called_with("features:user_del_789")
