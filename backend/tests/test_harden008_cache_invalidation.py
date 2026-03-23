"""
HARDEN-008: Cache Invalidation Imediata no Stripe Webhook

Tests that Stripe webhook handlers invalidate in-memory plan caches
(_plan_status_cache + plan_capabilities_cache) after plan_type updates.

AC3: Validate invalidation on downgrade (subscription deleted → free_trial)
AC4: Validate invalidation on upgrade (checkout completed → plan_pro)
AC5: Zero regressions (covered by full test suite run)
"""

import time
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from quota import (
    _plan_status_cache,
    _plan_status_cache_lock,
    invalidate_plan_status_cache,
    _cache_plan_status,
    _get_cached_plan_status,
    clear_plan_capabilities_cache,
)


# ═══════════════════════════════════════════════════════════════════════
# Unit tests for invalidate_plan_status_cache (AC1)
# ═══════════════════════════════════════════════════════════════════════


class TestInvalidatePlanStatusCache:
    """AC1: Webhook handler limpa _plan_status_cache[user_id] após update."""

    def setup_method(self):
        with _plan_status_cache_lock:
            _plan_status_cache.clear()

    def teardown_method(self):
        with _plan_status_cache_lock:
            _plan_status_cache.clear()

    def test_invalidate_existing_entry(self):
        """Invalidating a cached user removes their entry."""
        _cache_plan_status("user_abc", "smartlic_pro")
        assert _get_cached_plan_status("user_abc") == "smartlic_pro"

        invalidate_plan_status_cache("user_abc")

        assert _get_cached_plan_status("user_abc") is None

    def test_invalidate_nonexistent_entry_no_error(self):
        """Invalidating a user not in cache does not raise."""
        invalidate_plan_status_cache("user_nonexistent")
        assert _get_cached_plan_status("user_nonexistent") is None

    def test_invalidate_does_not_affect_other_users(self):
        """Invalidating one user leaves other users' cache intact."""
        _cache_plan_status("user_a", "smartlic_pro")
        _cache_plan_status("user_b", "smartlic_consultoria")

        invalidate_plan_status_cache("user_a")

        assert _get_cached_plan_status("user_a") is None
        assert _get_cached_plan_status("user_b") == "smartlic_consultoria"

    def test_invalidate_then_recache(self):
        """After invalidation, cache can be repopulated."""
        _cache_plan_status("user_x", "smartlic_pro")
        invalidate_plan_status_cache("user_x")
        assert _get_cached_plan_status("user_x") is None

        _cache_plan_status("user_x", "free_trial")
        assert _get_cached_plan_status("user_x") == "free_trial"


# ═══════════════════════════════════════════════════════════════════════
# Fixtures for webhook integration tests
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _clear_plan_caches():
    """Clear plan caches before/after each test."""
    with _plan_status_cache_lock:
        _plan_status_cache.clear()
    yield
    with _plan_status_cache_lock:
        _plan_status_cache.clear()


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


def configure_idempotency(sb, *, already_processed=False, event_id="evt_test_123"):
    events_chain = sb.table("stripe_webhook_events")
    if already_processed:
        events_chain.execute.return_value = Mock(data=[])
    else:
        events_chain.execute.return_value = Mock(data=[{"id": event_id}])


def configure_subscription_lookup(sb, *, found=True, user_id="user_123",
                                   plan_id="plan_pro", sub_id="sub-local-uuid"):
    subs_chain = sb.table("user_subscriptions")
    if found:
        subs_chain.execute.return_value = Mock(data=[{
            "id": sub_id,
            "user_id": user_id,
            "plan_id": plan_id,
            "stripe_subscription_id": "sub_test_456",
            "stripe_customer_id": "cus_test_789",
            "billing_period": "monthly",
            "is_active": True,
            "subscription_status": "active",
            "expires_at": "2027-01-01T00:00:00Z",
            "first_failed_at": None,
        }])
    else:
        subs_chain.execute.return_value = Mock(data=[])


# ═══════════════════════════════════════════════════════════════════════
# AC3: Downgrade invalidation (subscription.deleted → free_trial)
# ═══════════════════════════════════════════════════════════════════════


class TestDowngradeInvalidation:
    """AC3: Teste unitário valida invalidação no downgrade."""

    @pytest.mark.asyncio
    @patch("webhooks.handlers._shared.redis_cache", new_callable=AsyncMock)
    @patch("webhooks.stripe.get_supabase")
    async def test_subscription_deleted_invalidates_plan_cache(
        self, mock_get_sb, mock_redis, mock_supabase_client
    ):
        """When subscription is deleted, _plan_status_cache[user_id] must be cleared."""
        from webhooks.stripe import _handle_subscription_deleted

        sb = mock_supabase_client
        mock_get_sb.return_value = sb

        user_id = "user_downgrade_123"
        configure_idempotency(sb, already_processed=False)
        configure_subscription_lookup(sb, found=True, user_id=user_id, plan_id="smartlic_pro")

        # Pre-populate cache (simulating active plan cached)
        _cache_plan_status(user_id, "smartlic_pro")
        assert _get_cached_plan_status(user_id) == "smartlic_pro"

        # Build event
        event = Mock()
        event.id = "evt_del_001"
        event.type = "customer.subscription.deleted"
        data_obj = Mock()
        data_obj.id = "sub_test_456"
        data_obj.get = lambda key, default=None: {
            "customer": "cus_test_789",
        }.get(key, default)
        event.data = Mock()
        event.data.object = data_obj

        with patch("webhooks.handlers.subscription._mark_partner_referral_churned"):
            await _handle_subscription_deleted(sb, event)

        # Cache must be invalidated
        assert _get_cached_plan_status(user_id) is None

    @pytest.mark.asyncio
    @patch("webhooks.handlers._shared.redis_cache", new_callable=AsyncMock)
    @patch("webhooks.stripe.get_supabase")
    @patch("webhooks.handlers._shared.clear_plan_capabilities_cache")
    async def test_subscription_deleted_clears_capabilities_cache(
        self, mock_clear_caps, mock_get_sb, mock_redis, mock_supabase_client
    ):
        """AC2: clear_plan_capabilities_cache() called on downgrade."""
        from webhooks.stripe import _handle_subscription_deleted

        sb = mock_supabase_client
        mock_get_sb.return_value = sb

        configure_idempotency(sb, already_processed=False)
        configure_subscription_lookup(sb, found=True, user_id="user_d2", plan_id="smartlic_pro")

        event = Mock()
        event.id = "evt_del_002"
        event.type = "customer.subscription.deleted"
        data_obj = Mock()
        data_obj.id = "sub_test_456"
        data_obj.get = lambda key, default=None: {"customer": "cus_test_789"}.get(key, default)
        event.data = Mock()
        event.data.object = data_obj

        with patch("webhooks.handlers.subscription._mark_partner_referral_churned"):
            await _handle_subscription_deleted(sb, event)

        mock_clear_caps.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════
# AC4: Upgrade invalidation (checkout.session.completed → plan_pro)
# ═══════════════════════════════════════════════════════════════════════


class TestUpgradeInvalidation:
    """AC4: Teste unitário valida invalidação no upgrade."""

    @pytest.mark.asyncio
    @patch("webhooks.handlers.checkout._create_partner_referral_async")
    @patch("webhooks.handlers._shared.redis_cache", new_callable=AsyncMock)
    @patch("webhooks.stripe.get_supabase")
    async def test_checkout_completed_invalidates_plan_cache(
        self, mock_get_sb, mock_redis, mock_referral, mock_supabase_client
    ):
        """When checkout completes, _plan_status_cache[user_id] must be cleared."""
        from webhooks.stripe import _handle_checkout_session_completed

        sb = mock_supabase_client
        mock_get_sb.return_value = sb

        user_id = "user_upgrade_456"

        # Configure: idempotency passes, plan lookup succeeds
        configure_idempotency(sb, already_processed=False)

        # plans table: .single().execute() returns a dict (not list)
        plans_chain = sb.table("plans")
        plans_chain.execute.return_value = Mock(data={
            "duration_days": 30,
            "max_searches": 1000,
        })

        # Pre-populate cache with old plan (free_trial)
        _cache_plan_status(user_id, "free_trial")
        assert _get_cached_plan_status(user_id) == "free_trial"

        # Build checkout event
        event = Mock()
        event.id = "evt_checkout_001"
        event.type = "checkout.session.completed"
        session = Mock()
        session.id = "cs_test_789"
        session.mode = "subscription"
        session.payment_status = "paid"
        session.subscription = "sub_test_456"
        session.customer = "cus_test_789"
        session.get = lambda key, default=None: {
            "subscription": "sub_test_456",
            "customer": "cus_test_789",
            "mode": "subscription",
            "payment_status": "paid",
            "metadata": {"plan_id": "smartlic_pro", "billing_period": "monthly", "user_id": user_id},
            "client_reference_id": user_id,
        }.get(key, default)
        session.metadata = {"plan_id": "smartlic_pro", "billing_period": "monthly", "user_id": user_id}
        session.client_reference_id = user_id
        event.data = Mock()
        event.data.object = session

        # Mock stripe.Subscription.retrieve
        mock_stripe_sub = Mock()
        mock_stripe_sub.id = "sub_test_456"
        mock_stripe_sub.current_period_end = 1735689600  # 2025-01-01
        mock_stripe_sub.items = Mock()
        mock_stripe_sub.items.data = [Mock(price=Mock(id="price_monthly"))]

        with patch("webhooks.stripe.stripe.Subscription.retrieve", return_value=mock_stripe_sub):
            await _handle_checkout_session_completed(sb, event)

        # Cache must be invalidated after upgrade
        assert _get_cached_plan_status(user_id) is None

    @pytest.mark.asyncio
    @patch("webhooks.handlers.checkout._create_partner_referral_async")
    @patch("webhooks.handlers._shared.redis_cache", new_callable=AsyncMock)
    @patch("webhooks.stripe.get_supabase")
    @patch("webhooks.handlers._shared.clear_plan_capabilities_cache")
    async def test_checkout_completed_clears_capabilities_cache(
        self, mock_clear_caps, mock_get_sb, mock_redis, mock_referral, mock_supabase_client
    ):
        """AC2: clear_plan_capabilities_cache() called on upgrade."""
        from webhooks.stripe import _handle_checkout_session_completed

        sb = mock_supabase_client
        mock_get_sb.return_value = sb

        user_id = "user_upgrade_789"

        configure_idempotency(sb, already_processed=False)
        plans_chain = sb.table("plans")
        plans_chain.execute.return_value = Mock(data={
            "duration_days": 30,
            "max_searches": 1000,
        })

        event = Mock()
        event.id = "evt_checkout_002"
        event.type = "checkout.session.completed"
        session = Mock()
        session.id = "cs_test_002"
        session.mode = "subscription"
        session.payment_status = "paid"
        session.subscription = "sub_test_456"
        session.customer = "cus_test_789"
        session.get = lambda key, default=None: {
            "subscription": "sub_test_456",
            "customer": "cus_test_789",
            "mode": "subscription",
            "payment_status": "paid",
            "metadata": {"plan_id": "smartlic_pro", "billing_period": "monthly", "user_id": user_id},
            "client_reference_id": user_id,
        }.get(key, default)
        session.metadata = {"plan_id": "smartlic_pro", "billing_period": "monthly", "user_id": user_id}
        session.client_reference_id = user_id
        event.data = Mock()
        event.data.object = session

        mock_stripe_sub = Mock()
        mock_stripe_sub.id = "sub_test_456"
        mock_stripe_sub.current_period_end = 1735689600
        mock_stripe_sub.items = Mock()
        mock_stripe_sub.items.data = [Mock(price=Mock(id="price_monthly"))]

        with patch("webhooks.stripe.stripe.Subscription.retrieve", return_value=mock_stripe_sub):
            await _handle_checkout_session_completed(sb, event)

        mock_clear_caps.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════
# AC4 extra: subscription_updated invalidation
# ═══════════════════════════════════════════════════════════════════════


class TestSubscriptionUpdatedInvalidation:
    """subscription.updated handler also invalidates caches."""

    @pytest.mark.asyncio
    @patch("webhooks.handlers._shared.redis_cache", new_callable=AsyncMock)
    @patch("webhooks.stripe.get_supabase")
    async def test_subscription_updated_invalidates_plan_cache(
        self, mock_get_sb, mock_redis, mock_supabase_client
    ):
        from webhooks.stripe import _handle_subscription_updated

        sb = mock_supabase_client
        mock_get_sb.return_value = sb

        user_id = "user_update_001"
        configure_idempotency(sb, already_processed=False)
        configure_subscription_lookup(sb, found=True, user_id=user_id, plan_id="smartlic_pro")

        # Pre-populate cache
        _cache_plan_status(user_id, "smartlic_pro")

        event = Mock()
        event.id = "evt_upd_001"
        event.type = "customer.subscription.updated"
        sub_obj = Mock()
        sub_obj.id = "sub_test_456"
        sub_obj.get = lambda key, default=None: {
            "plan": {"interval": "year"},
            "items": {"data": [{"plan": {"interval": "year"}}]},
            "customer": "cus_test_789",
            "metadata": {"plan_id": "smartlic_pro"},
        }.get(key, default)
        event.data = Mock()
        event.data.object = sub_obj

        # Configure plan_billing_periods lookup
        pbp_chain = sb.table("plan_billing_periods")
        pbp_chain.execute.return_value = Mock(data=[])

        await _handle_subscription_updated(sb, event)

        assert _get_cached_plan_status(user_id) is None
