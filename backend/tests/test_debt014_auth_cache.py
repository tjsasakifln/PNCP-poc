"""DEBT-014 SYS-010 + SYS-018: Tests for bounded auth cache + Redis L2."""

import time
import json
import hashlib
from collections import OrderedDict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestBoundedAuthCache:
    """SYS-010: Auth cache has TTL and max entry limit."""

    def test_cache_is_ordered_dict(self):
        from auth import _token_cache
        assert isinstance(_token_cache, OrderedDict)

    def test_max_cache_entries_defined(self):
        from auth import MAX_CACHE_ENTRIES
        assert MAX_CACHE_ENTRIES == 1000

    def test_cache_ttl_defined(self):
        from auth import CACHE_TTL
        assert CACHE_TTL == 60

    def test_redis_cache_ttl_defined(self):
        from auth import REDIS_CACHE_TTL
        assert REDIS_CACHE_TTL == 300

    def test_cache_store_memory_basic(self):
        """_cache_store_memory stores and respects LRU order."""
        from auth import _cache_store_memory, _token_cache

        _token_cache.clear()

        _cache_store_memory("hash_a", {"id": "user_a", "email": "a@test.com"})
        _cache_store_memory("hash_b", {"id": "user_b", "email": "b@test.com"})

        assert "hash_a" in _token_cache
        assert "hash_b" in _token_cache
        assert len(_token_cache) == 2

        # hash_b should be last (most recent)
        assert list(_token_cache.keys())[-1] == "hash_b"

        _token_cache.clear()

    def test_cache_store_memory_lru_eviction(self):
        """When MAX_CACHE_ENTRIES exceeded, oldest entries evicted."""
        from auth import _cache_store_memory, _token_cache, MAX_CACHE_ENTRIES

        _token_cache.clear()

        # Fill cache to max
        for i in range(MAX_CACHE_ENTRIES):
            _cache_store_memory(f"hash_{i}", {"id": f"user_{i}", "email": f"{i}@test.com"})

        assert len(_token_cache) == MAX_CACHE_ENTRIES

        # Add one more — should evict oldest (hash_0)
        _cache_store_memory("hash_new", {"id": "user_new", "email": "new@test.com"})

        assert len(_token_cache) == MAX_CACHE_ENTRIES
        assert "hash_0" not in _token_cache
        assert "hash_new" in _token_cache

        _token_cache.clear()


class TestRedisAuthCache:
    """SYS-018: Auth token cache shared via Redis between workers."""

    @pytest.mark.asyncio
    async def test_redis_cache_get_hit(self):
        """_redis_cache_get returns data from Redis."""
        from auth import _redis_cache_get

        user_data = {"id": "user123", "email": "test@test.com", "role": "authenticated"}
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(user_data))

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            result = await _redis_cache_get("test_hash")
            assert result == user_data
            mock_redis.get.assert_called_once_with("smartlic:auth:test_hash")

    @pytest.mark.asyncio
    async def test_redis_cache_get_miss(self):
        """_redis_cache_get returns None on miss."""
        from auth import _redis_cache_get

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            result = await _redis_cache_get("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_redis_cache_get_error_returns_none(self):
        """_redis_cache_get returns None on Redis error (resilience)."""
        from auth import _redis_cache_get

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, side_effect=Exception("Redis down")):
            result = await _redis_cache_get("test_hash")
            assert result is None

    @pytest.mark.asyncio
    async def test_redis_cache_set_stores_with_ttl(self):
        """_redis_cache_set stores data in Redis with correct TTL."""
        from auth import _redis_cache_set, REDIS_CACHE_TTL

        user_data = {"id": "user123", "email": "test@test.com"}
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=mock_redis):
            await _redis_cache_set("test_hash", user_data)
            mock_redis.setex.assert_called_once_with(
                "smartlic:auth:test_hash",
                REDIS_CACHE_TTL,
                json.dumps(user_data),
            )

    @pytest.mark.asyncio
    async def test_redis_cache_set_error_silenced(self):
        """_redis_cache_set silently handles Redis errors."""
        from auth import _redis_cache_set

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, side_effect=Exception("Redis down")):
            # Should not raise
            await _redis_cache_set("test_hash", {"id": "u1"})

    @pytest.mark.asyncio
    async def test_redis_cache_get_none_pool(self):
        """_redis_cache_get returns None when pool is None (no Redis)."""
        from auth import _redis_cache_get

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None):
            result = await _redis_cache_get("test_hash")
            assert result is None

    @pytest.mark.asyncio
    async def test_redis_cache_set_none_pool(self):
        """_redis_cache_set does nothing when pool is None."""
        from auth import _redis_cache_set

        with patch("redis_pool.get_redis_pool", new_callable=AsyncMock, return_value=None):
            # Should not raise
            await _redis_cache_set("test_hash", {"id": "u1"})


class TestGetCurrentUserCacheIntegration:
    """Integration tests for the full L1+L2 cache flow."""

    @pytest.mark.asyncio
    async def test_l1_cache_hit(self):
        """L1 in-memory cache hit skips Redis and JWT validation."""
        from auth import _token_cache, get_current_user

        _token_cache.clear()

        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.sig"
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        user_data = {"id": "user-l1", "email": "l1@test.com", "role": "authenticated", "aal": "aal1"}
        _token_cache[token_hash] = (user_data, time.time())

        mock_creds = MagicMock()
        mock_creds.credentials = token

        result = await get_current_user(mock_creds)
        assert result["id"] == "user-l1"

        _token_cache.clear()

    @pytest.mark.asyncio
    async def test_l1_expired_does_not_return_stale(self):
        """Expired L1 entry does NOT return stale data — falls through."""
        from auth import _token_cache, get_current_user, CACHE_TTL

        _token_cache.clear()

        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired_test.sig"
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        stale_data = {"id": "user-stale", "email": "stale@test.com", "role": "authenticated", "aal": "aal1"}
        # Set timestamp in the past (expired)
        _token_cache[token_hash] = (stale_data, time.time() - CACHE_TTL - 10)

        mock_creds = MagicMock()
        mock_creds.credentials = token

        # L2 returns fresh data — should NOT return stale L1 data
        fresh_data = {"id": "user-fresh", "email": "fresh@test.com", "role": "authenticated", "aal": "aal1"}
        with patch("auth._redis_cache_get", new_callable=AsyncMock, return_value=fresh_data):
            result = await get_current_user(mock_creds)
            assert result["id"] == "user-fresh"  # Got fresh, not stale

        _token_cache.clear()

    @pytest.mark.asyncio
    async def test_l2_redis_hit_promotes_to_l1(self):
        """Redis L2 hit promotes to L1 and returns data."""
        from auth import _token_cache, get_current_user

        _token_cache.clear()

        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.redis.sig"
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        user_data = {"id": "user-redis", "email": "redis@test.com", "role": "authenticated", "aal": "aal1"}

        mock_creds = MagicMock()
        mock_creds.credentials = token

        with patch("auth._redis_cache_get", new_callable=AsyncMock, return_value=user_data):
            result = await get_current_user(mock_creds)
            assert result["id"] == "user-redis"

        # Should now be in L1
        assert token_hash in _token_cache

        _token_cache.clear()


class TestClearTokenCache:
    def test_clear_cache_returns_count(self):
        from auth import _token_cache, clear_token_cache

        _token_cache.clear()
        _token_cache["a"] = ({"id": "1"}, time.time())
        _token_cache["b"] = ({"id": "2"}, time.time())

        count = clear_token_cache()
        assert count == 2
        assert len(_token_cache) == 0
