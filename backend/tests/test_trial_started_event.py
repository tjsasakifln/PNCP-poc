"""
Wave B (generic-sparrow plan) — `trial_started` event emit in subscription.created webhook.

Closes funnel: signup_completed → trial_started → paywall_hit → checkout_completed.
"""

from unittest.mock import MagicMock, patch


def _make_subscription_data(status="trialing", sub_id="sub_test_123",
                             customer_id="cus_test_456",
                             plan_metadata="plan_pro_monthly",
                             trial_end=1735689600,
                             interval="month", interval_count=1):
    """Build a Stripe-like subscription object as a dict (uses .get())."""
    data = {
        "id": sub_id,
        "status": status,
        "customer": customer_id,
        "trial_end": trial_end,
        "metadata": {"plan_id": plan_metadata},
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


def _make_event(sub_obj, event_type="customer.subscription.created"):
    event = MagicMock()
    event.type = event_type
    event.data.object = sub_obj
    return event


def _make_supabase_with_user(user_id="user-uuid-1", plan_id="plan_pro_monthly"):
    """Build a mock Supabase client that returns a matching user_subscriptions row."""
    sb = MagicMock()
    result = MagicMock()
    result.data = [{"user_id": user_id, "plan_id": plan_id}]
    sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = result
    return sb


def _make_supabase_no_match():
    sb = MagicMock()
    result = MagicMock()
    result.data = []
    sb.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = result
    return sb


@patch("analytics_events.track_funnel_event")
def test_trial_started_emitted_when_status_trialing(mock_track):
    from webhooks.handlers.subscription import _emit_trial_started_event

    sub = _make_subscription_data(status="trialing")
    sb = _make_supabase_with_user(user_id="u-1", plan_id="plan_pro")

    _emit_trial_started_event(sb, sub)

    mock_track.assert_called_once()
    args, kwargs = mock_track.call_args
    assert args[0] == "trial_started"
    assert args[1] == "u-1"
    payload = args[2]
    assert payload["plan_id"] == "plan_pro"
    assert payload["stripe_subscription_id"] == "sub_test_123"
    assert payload["billing_period"] == "monthly"
    assert payload["trial_end_unix"] == 1735689600


@patch("analytics_events.track_funnel_event")
def test_trial_started_billing_period_annual(mock_track):
    from webhooks.handlers.subscription import _emit_trial_started_event

    sub = _make_subscription_data(interval="year", interval_count=1)
    sb = _make_supabase_with_user()

    _emit_trial_started_event(sb, sub)

    payload = mock_track.call_args.args[2]
    assert payload["billing_period"] == "annual"


@patch("analytics_events.track_funnel_event")
def test_trial_started_billing_period_semiannual(mock_track):
    from webhooks.handlers.subscription import _emit_trial_started_event

    sub = _make_subscription_data(interval="month", interval_count=6)
    sb = _make_supabase_with_user()

    _emit_trial_started_event(sb, sub)

    payload = mock_track.call_args.args[2]
    assert payload["billing_period"] == "semiannual"


@patch("analytics_events.track_funnel_event")
def test_trial_started_no_emit_when_user_unresolved(mock_track):
    from webhooks.handlers.subscription import _emit_trial_started_event

    sub = _make_subscription_data()
    sb = _make_supabase_no_match()

    _emit_trial_started_event(sb, sub)

    mock_track.assert_not_called()


@patch("analytics_events.track_funnel_event")
async def test_handle_subscription_created_emits_trial_started(mock_track):
    from webhooks.handlers.subscription import handle_subscription_created

    sub = _make_subscription_data(status="trialing")
    event = _make_event(sub)
    sb = _make_supabase_with_user(user_id="u-2", plan_id="plan_pro")

    await handle_subscription_created(sb, event)

    mock_track.assert_called_once()
    assert mock_track.call_args.args[0] == "trial_started"
    assert mock_track.call_args.args[1] == "u-2"


@patch("analytics_events.track_funnel_event")
async def test_handle_subscription_created_skips_when_status_not_trialing(mock_track):
    from webhooks.handlers.subscription import handle_subscription_created

    sub = _make_subscription_data(status="active")
    event = _make_event(sub)
    sb = _make_supabase_with_user()

    await handle_subscription_created(sb, event)

    mock_track.assert_not_called()


@patch("analytics_events.track_funnel_event", side_effect=RuntimeError("mixpanel down"))
async def test_handle_subscription_created_swallows_emit_errors(mock_track):
    """Webhook never breaks if Mixpanel emit fails."""
    from webhooks.handlers.subscription import handle_subscription_created

    sub = _make_subscription_data(status="trialing")
    event = _make_event(sub)
    sb = _make_supabase_with_user()

    await handle_subscription_created(sb, event)
