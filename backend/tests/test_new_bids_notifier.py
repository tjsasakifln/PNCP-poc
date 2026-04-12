"""tests/test_new_bids_notifier.py — STORY-445: New bids notifier cron job tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_profiles():
    return [
        {
            "id": "user-a",
            "plan_type": "free_trial",
            "profile_context": {"setor_id": "saude", "ufs": ["SP", "RJ"]},
        },
        {
            "id": "user-b",
            "plan_type": "smartlic_pro",
            "profile_context": {"setor_id": "construcao", "ufs_selecionadas": ["MG"]},
        },
        {
            "id": "user-no-setor",
            "plan_type": "free_trial",
            "profile_context": {"ufs": ["SP"]},  # missing setor_id
        },
        {
            "id": "user-no-ufs",
            "plan_type": "free_trial",
            "profile_context": {"setor_id": "saude"},  # missing ufs
        },
    ]


# ---------------------------------------------------------------------------
# Tests — run_new_bids_notifier
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_new_bids_notifier_processes_valid_users(mock_profiles):
    """Users with setor_id AND ufs get a Redis key written."""
    mock_sb = MagicMock()
    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()

    # Profile query returns 4 profiles (2 valid, 2 missing fields)
    profiles_resp = MagicMock()
    profiles_resp.data = mock_profiles

    # Count query returns 5 new bids
    count_resp = MagicMock()
    count_resp.count = 5

    mock_table = MagicMock()
    mock_table.select.return_value = mock_table
    mock_table.in_.return_value = mock_table
    mock_table.not_ = mock_table
    mock_table.is_.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.gte.return_value = mock_table

    mock_sb.table.return_value = mock_table

    call_count = [0]

    async def mock_sb_execute(query):
        call_count[0] += 1
        if call_count[0] == 1:
            return profiles_resp
        return count_resp

    with (
        patch("redis_pool.get_redis_pool", return_value=mock_redis),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("supabase_client.sb_execute", side_effect=mock_sb_execute),
    ):
        from jobs.cron.new_bids_notifier import run_new_bids_notifier
        result = await run_new_bids_notifier()

    # 2 valid profiles processed, 2 skipped
    assert result["processed"] == 2
    assert result["skipped"] == 2
    assert result["errors"] == 0
    # Redis.setex called twice (once per valid user)
    assert mock_redis.setex.call_count == 2


@pytest.mark.asyncio
async def test_run_new_bids_notifier_stores_count_in_redis(mock_profiles):
    """Redis key format is new_bids_count:{user_id} with correct TTL."""
    mock_sb = MagicMock()
    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()

    profiles_resp = MagicMock()
    profiles_resp.data = [mock_profiles[0]]  # only user-a

    count_resp = MagicMock()
    count_resp.count = 7

    call_count = [0]

    async def mock_sb_execute(query):
        call_count[0] += 1
        if call_count[0] == 1:
            return profiles_resp
        return count_resp

    with (
        patch("redis_pool.get_redis_pool", return_value=mock_redis),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("supabase_client.sb_execute", side_effect=mock_sb_execute),
    ):
        from jobs.cron.new_bids_notifier import run_new_bids_notifier, NEW_BIDS_REDIS_TTL
        await run_new_bids_notifier()

    mock_redis.setex.assert_called_once_with(
        "new_bids_count:user-a",
        NEW_BIDS_REDIS_TTL,
        "7",
    )


@pytest.mark.asyncio
async def test_run_new_bids_notifier_no_profiles():
    """Returns early when no active profiles found."""
    mock_sb = MagicMock()
    mock_redis = AsyncMock()

    profiles_resp = MagicMock()
    profiles_resp.data = []

    async def mock_sb_execute(query):
        return profiles_resp

    with (
        patch("redis_pool.get_redis_pool", return_value=mock_redis),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("supabase_client.sb_execute", side_effect=mock_sb_execute),
    ):
        from jobs.cron.new_bids_notifier import run_new_bids_notifier
        result = await run_new_bids_notifier()

    assert result["processed"] == 0
    assert "reason" in result


@pytest.mark.asyncio
async def test_run_new_bids_notifier_redis_unavailable(mock_profiles):
    """Processes profiles gracefully when Redis is None (no exception raised)."""
    mock_sb = MagicMock()

    profiles_resp = MagicMock()
    profiles_resp.data = [mock_profiles[0]]

    count_resp = MagicMock()
    count_resp.count = 3

    call_count = [0]

    async def mock_sb_execute(query):
        call_count[0] += 1
        if call_count[0] == 1:
            return profiles_resp
        return count_resp

    with (
        patch("redis_pool.get_redis_pool", return_value=None),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("supabase_client.sb_execute", side_effect=mock_sb_execute),
    ):
        from jobs.cron.new_bids_notifier import run_new_bids_notifier
        result = await run_new_bids_notifier()

    # processed == 1 because count_resp was returned; no Redis write attempted
    assert result["processed"] == 1
    assert result["errors"] == 0


@pytest.mark.asyncio
async def test_run_new_bids_notifier_supabase_error():
    """Returns error dict when Supabase raises."""
    async def mock_sb_execute(query):
        raise Exception("connection refused")

    mock_sb = MagicMock()
    mock_redis = AsyncMock()

    with (
        patch("redis_pool.get_redis_pool", return_value=mock_redis),
        patch("supabase_client.get_supabase", return_value=mock_sb),
        patch("supabase_client.sb_execute", side_effect=mock_sb_execute),
    ):
        from jobs.cron.new_bids_notifier import run_new_bids_notifier
        result = await run_new_bids_notifier()

    assert result["processed"] == 0
    assert "error" in result
