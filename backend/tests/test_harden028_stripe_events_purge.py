"""HARDEN-028 AC4: Tests for Stripe webhook events purge (> 90 days)."""

from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for purge tests."""
    sb = MagicMock()
    table = MagicMock()
    sb.table.return_value = table
    table.delete.return_value = table
    table.lt.return_value = table
    return sb, table


@pytest.mark.asyncio
async def test_purge_deletes_old_events(mock_supabase):
    """AC1: Purge deletes events older than 90 days."""
    sb, table = mock_supabase

    # Simulate 5 deleted rows
    result_data = [{"id": f"evt_{i}"} for i in range(5)]

    async def fake_execute(query):
        return SimpleNamespace(data=result_data, count=None)

    with patch("cron_jobs.get_supabase" if False else "supabase_client.get_supabase", return_value=sb), \
         patch("cron_jobs.sb_execute" if False else "supabase_client.sb_execute", side_effect=fake_execute) as mock_exec:  # noqa: F841
        from cron_jobs import purge_old_stripe_events
        result = await purge_old_stripe_events()

    assert result["deleted"] == 5
    assert "cutoff" in result
    assert "error" not in result

    # Verify it targeted stripe_webhook_events
    sb.table.assert_called_with("stripe_webhook_events")
    table.delete.assert_called_once()
    table.lt.assert_called_once()
    # Verify cutoff is ~90 days ago
    call_args = table.lt.call_args
    assert call_args[0][0] == "processed_at"


@pytest.mark.asyncio
async def test_purge_no_old_events(mock_supabase):
    """AC1: Purge returns 0 when no old events exist."""
    sb, table = mock_supabase

    async def fake_execute(query):
        return SimpleNamespace(data=[], count=None)

    with patch("supabase_client.get_supabase", return_value=sb), \
         patch("supabase_client.sb_execute", side_effect=fake_execute):
        from cron_jobs import purge_old_stripe_events
        result = await purge_old_stripe_events()

    assert result["deleted"] == 0


@pytest.mark.asyncio
async def test_purge_cutoff_is_90_days():
    """AC1: Cutoff date is exactly 90 days ago."""
    sb = MagicMock()
    table = MagicMock()
    sb.table.return_value = table
    table.delete.return_value = table
    table.lt.return_value = table

    captured_cutoff = None

    async def fake_execute(query):
        return SimpleNamespace(data=[], count=None)

    original_lt = table.lt

    def capture_lt(col, val):
        nonlocal captured_cutoff
        captured_cutoff = val
        return original_lt.return_value

    table.lt.side_effect = capture_lt

    with patch("supabase_client.get_supabase", return_value=sb), \
         patch("supabase_client.sb_execute", side_effect=fake_execute):
        from cron_jobs import purge_old_stripe_events
        result = await purge_old_stripe_events()  # noqa: F841

    assert captured_cutoff is not None
    cutoff_dt = datetime.fromisoformat(captured_cutoff)
    expected = datetime.now(timezone.utc) - timedelta(days=90)
    # Allow 5 seconds of drift
    assert abs((cutoff_dt - expected).total_seconds()) < 5


@pytest.mark.asyncio
async def test_purge_handles_supabase_error():
    """AC1: Purge handles errors gracefully."""
    with patch("supabase_client.get_supabase", side_effect=Exception("DB down")):
        from cron_jobs import purge_old_stripe_events
        result = await purge_old_stripe_events()

    assert result["deleted"] == 0
    assert "error" in result


@pytest.mark.asyncio
async def test_purge_logs_deleted_count(mock_supabase, caplog):
    """AC3: Purge logs count of deleted events."""
    import logging
    sb, table = mock_supabase

    async def fake_execute(query):
        return SimpleNamespace(data=[{"id": "evt_1"}, {"id": "evt_2"}, {"id": "evt_3"}], count=None)

    with caplog.at_level(logging.INFO, logger="jobs.cron.billing"), \
         patch("supabase_client.get_supabase", return_value=sb), \
         patch("supabase_client.sb_execute", side_effect=fake_execute):
        from cron_jobs import purge_old_stripe_events
        result = await purge_old_stripe_events()

    assert result["deleted"] == 3
    assert any("Purged 3 Stripe webhook events" in msg for msg in caplog.messages)


@pytest.mark.asyncio
async def test_purge_constants():
    """AC1+AC2: Verify retention and interval constants."""
    from cron_jobs import STRIPE_EVENTS_RETENTION_DAYS, STRIPE_PURGE_INTERVAL_SECONDS

    assert STRIPE_EVENTS_RETENTION_DAYS == 90
    assert STRIPE_PURGE_INTERVAL_SECONDS == 86400  # 24h
