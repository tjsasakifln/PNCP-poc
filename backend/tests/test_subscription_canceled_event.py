"""
Wave frolicking-glacier — `subscription_canceled` Mixpanel funnel event emit
in subscription.deleted webhook.

Closes churn cohort: trial_started → trial_converted → subscription_canceled.
Without this event, churn analysis was invisible in Mixpanel.
"""

from unittest.mock import MagicMock, patch

import pytest


def _make_subscription_data(
    sub_id="sub_test_999",
    customer_id="cus_test_999",
    cancellation_reason="cancellation_requested",
    interval="month",
    interval_count=1,
):
    """Build a Stripe-like subscription deletion object."""
    data = {
        "id": sub_id,
        "customer": customer_id,
        "cancellation_details": {"reason": cancellation_reason},
        "plan": {"interval": interval, "interval_count": interval_count},
        "items": {"data": [{"plan": {"interval": interval, "interval_count": interval_count}}]},
    }

    class _SubObj:
        def __init__(self, d):
            self._d = d
            self.id = d["id"]

        def get(self, key, default=None):
            return self._d.get(key, default)

    return _SubObj(data)


def _make_event(sub_obj):
    event = MagicMock()
    event.type = "customer.subscription.deleted"
    event.data.object = sub_obj
    return event


def _make_supabase_with_user(user_id="user-uuid-x", plan_id="plan_pro_monthly", expires_at="2026-05-01T00:00:00Z"):
    """Build a mock Supabase client returning a user_subscriptions row."""
    sb = MagicMock()
    select_result = MagicMock()
    select_result.data = [{
        "id": "local-sub-1",
        "user_id": user_id,
        "plan_id": plan_id,
        "expires_at": expires_at,
    }]
    sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = select_result
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
    return sb


def _make_supabase_no_match():
    sb = MagicMock()
    result = MagicMock()
    result.data = []
    sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = result
    return sb


@patch("analytics_events.track_funnel_event")
def test_subscription_canceled_event_payload(mock_track):
    """Direct unit test of _emit_subscription_canceled_event helper."""
    from webhooks.handlers.subscription import _emit_subscription_canceled_event

    sub = _make_subscription_data(cancellation_reason="payment_failed")
    local_sub = {"plan_id": "plan_pro_monthly", "expires_at": "2026-05-01T00:00:00Z"}

    _emit_subscription_canceled_event("u-x", local_sub, sub)

    mock_track.assert_called_once()
    args, kwargs = mock_track.call_args
    assert args[0] == "subscription_canceled"
    assert args[1] == "u-x"
    payload = args[2]
    assert payload["plan_id"] == "plan_pro_monthly"
    assert payload["stripe_subscription_id"] == "sub_test_999"
    assert payload["billing_period"] == "monthly"
    assert payload["cancellation_reason"] == "payment_failed"
    assert payload["expires_at"] == "2026-05-01T00:00:00Z"


@patch("analytics_events.track_funnel_event")
def test_subscription_canceled_billing_period_annual(mock_track):
    from webhooks.handlers.subscription import _emit_subscription_canceled_event

    sub = _make_subscription_data(interval="year", interval_count=1)
    local_sub = {"plan_id": "plan_pro_annual", "expires_at": None}

    _emit_subscription_canceled_event("u-y", local_sub, sub)

    payload = mock_track.call_args.args[2]
    assert payload["billing_period"] == "annual"


@patch("analytics_events.track_funnel_event")
def test_subscription_canceled_billing_period_semiannual(mock_track):
    from webhooks.handlers.subscription import _emit_subscription_canceled_event

    sub = _make_subscription_data(interval="month", interval_count=6)
    local_sub = {"plan_id": "plan_pro_semiannual", "expires_at": None}

    _emit_subscription_canceled_event("u-z", local_sub, sub)

    payload = mock_track.call_args.args[2]
    assert payload["billing_period"] == "semiannual"


@patch("analytics_events.track_funnel_event")
def test_subscription_canceled_no_cancellation_details(mock_track):
    """Stripe events without cancellation_details should still emit (reason=None)."""
    from webhooks.handlers.subscription import _emit_subscription_canceled_event

    sub_no_details = _make_subscription_data()
    sub_no_details._d.pop("cancellation_details", None)

    _emit_subscription_canceled_event("u-q", {"plan_id": "p"}, sub_no_details)

    mock_track.assert_called_once()
    payload = mock_track.call_args.args[2]
    assert payload["cancellation_reason"] is None


@pytest.mark.asyncio
@patch("webhooks.handlers.subscription._send_cancellation_email")
@patch("webhooks.handlers.subscription._mark_partner_referral_churned")
@patch("webhooks.handlers.subscription.invalidate_user_caches")
@patch("analytics_events.track_funnel_event")
async def test_handle_subscription_deleted_emits_subscription_canceled(
    mock_track, mock_invalidate, mock_mark_churned, mock_send_email
):
    from webhooks.handlers.subscription import handle_subscription_deleted

    sub = _make_subscription_data()
    event = _make_event(sub)
    sb = _make_supabase_with_user(user_id="u-2", plan_id="plan_pro")

    await handle_subscription_deleted(sb, event)

    mock_track.assert_called_once()
    assert mock_track.call_args.args[0] == "subscription_canceled"
    assert mock_track.call_args.args[1] == "u-2"


@pytest.mark.asyncio
@patch("analytics_events.track_funnel_event")
async def test_handle_subscription_deleted_skips_when_no_local_sub(mock_track):
    """If user_subscriptions has no row for the deleted Stripe sub, no emit."""
    from webhooks.handlers.subscription import handle_subscription_deleted

    sub = _make_subscription_data()
    event = _make_event(sub)
    sb = _make_supabase_no_match()

    await handle_subscription_deleted(sb, event)

    mock_track.assert_not_called()


@pytest.mark.asyncio
@patch("webhooks.handlers.subscription._send_cancellation_email")
@patch("webhooks.handlers.subscription._mark_partner_referral_churned")
@patch("webhooks.handlers.subscription.invalidate_user_caches")
@patch("analytics_events.track_funnel_event", side_effect=RuntimeError("mixpanel down"))
async def test_handle_subscription_deleted_swallows_emit_errors(
    mock_track, mock_invalidate, mock_mark_churned, mock_send_email
):
    """Webhook never breaks if Mixpanel emit fails."""
    from webhooks.handlers.subscription import handle_subscription_deleted

    sub = _make_subscription_data()
    event = _make_event(sub)
    sb = _make_supabase_with_user()

    # Should not raise
    await handle_subscription_deleted(sb, event)
