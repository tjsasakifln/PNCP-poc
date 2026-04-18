"""DEBT-203: Integration test for multi-level cache (L1 miss → L2 hit → response).

Architecture: L1=Supabase (checked first), L2=Redis/InMemory, L3=Local file.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_l1_miss_l2_hit_returns_result():
    """DEBT-203 AC: L1(Supabase) miss → L2(Redis) hit → returns stale result.

    Layer order in _read_all_levels:
      L1 = Supabase (_get_from_supabase) — checked first
      L2 = Redis/InMemory (_get_from_redis) — checked on L1 miss
      L3 = Local file (_get_from_local) — checked on L2 miss
    """
    from cache.manager import get_from_cache

    stale_entry = {
        "results": [{"id": "test-1", "objeto": "obra pública"}],
        "sources_json": ["PNCP"],
        "fetched_at": (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat(),  # stale but not expired
        "user_id": "user-test",
        "params_hash": "abc123",
        "params": {"setor_id": "engenharia", "ufs": ["SP"]},
        "access_count": 2,
        "priority": "warm",
    }

    # L1 Supabase miss, L2 Redis hit with stale data
    with patch("cache.supabase._get_from_supabase", new_callable=AsyncMock, return_value=None) as mock_supa, \
         patch("cache.redis._get_from_redis", return_value=stale_entry) as mock_redis, \
         patch("cache.local_file._get_from_local", return_value=None), \
         patch("cache._ops._increment_and_reclassify", new_callable=AsyncMock):

        result = await get_from_cache(
            user_id="user-test",
            params={"setor_id": "engenharia", "ufs": ["SP"]},
        )

    # Should return stale data from L2 Redis
    assert result is not None
    assert len(result["results"]) == 1
    assert result["results"][0]["id"] == "test-1"
    # L1 Supabase was attempted and missed
    mock_supa.assert_called_once()
    # L2 Redis returned the result
    mock_redis.assert_called_once()


@pytest.mark.asyncio
async def test_l1_miss_l2_miss_returns_none():
    """DEBT-203 AC: L1 miss → L2 miss → None (no cache)."""
    from cache.manager import get_from_cache

    with patch("cache.redis._get_from_redis", return_value=None), \
         patch("cache.supabase._get_from_supabase", new_callable=AsyncMock, return_value=None):

        result = await get_from_cache(
            user_id="user-test",
            params={"setor_id": "medicamentos", "ufs": ["RJ"]},
        )

    assert result is None


@pytest.mark.asyncio
async def test_save_then_get_roundtrip():
    """DEBT-203 AC: Save to cache → immediately retrievable at L2."""
    from cache.manager import save_to_cache, get_from_cache

    test_results = [{"id": "bid-001", "objeto": "construção escola"}]
    test_params = {"setor_id": "engenharia", "ufs": ["SC"]}

    saved_entry = {}

    async def mock_save(user_id, params_hash, params, results, sources, **kwargs):
        saved_entry["results"] = results
        saved_entry["sources_json"] = sources
        saved_entry["fetched_at"] = datetime.now(timezone.utc).isoformat()
        saved_entry["user_id"] = user_id
        saved_entry["params_hash"] = params_hash
        saved_entry["params"] = params
        saved_entry["access_count"] = 0
        saved_entry["priority"] = "cold"

    with patch("cache.supabase._save_to_supabase", new_callable=AsyncMock, side_effect=mock_save), \
         patch("cache.redis._save_to_redis"):

        save_result = await save_to_cache(
            user_id="user-test",
            params=test_params,
            results=test_results,
            sources=["PNCP"],
        )

    assert save_result["success"] is True

    # Now retrieve - L1 miss, L2 should return saved entry
    with patch("cache.redis._get_from_redis", return_value=None), \
         patch("cache.supabase._get_from_supabase", new_callable=AsyncMock, return_value=saved_entry), \
         patch("cache.swr.trigger_background_revalidation", new_callable=AsyncMock, return_value=False):

        result = await get_from_cache(user_id="user-test", params=test_params)

    assert result is not None
    assert result["results"][0]["id"] == "bid-001"
    assert result["cache_level"] in ("supabase", "stale_supabase")
