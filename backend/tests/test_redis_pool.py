"""Unit tests for redis_pool module (InMemoryCache + async pool singleton).

STORY-217 AC12-AC15: Comprehensive tests for the unified Redis connection pool.

Covers:
  - AC12: Concurrent requests share the same connection pool (singleton).
  - AC13: Redis unavailable -> fallback to InMemoryCache.
  - AC14: InMemoryCache LRU eviction at 10K entries.
  - AC15: No asyncio.run() in production code.
  - InMemoryCache unit tests (get, set, setex, delete, exists, ping, len).
  - Pool lifecycle tests (startup, shutdown, is_redis_available, fallback singleton).

Run from backend/:
    python -m pytest tests/test_redis_pool.py -v
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Pre-mock heavy third-party modules that may appear in the import chain
# but are NOT needed for unit-testing redis_pool.
for _mod_name in ("openai",):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = MagicMock()

import redis_pool
from redis_pool import (
    INMEMORY_MAX_ENTRIES,
    InMemoryCache,
    get_fallback_cache,
    get_redis_pool,
    is_redis_available,
    shutdown_redis,
    startup_redis,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_redis_pool_state():
    """Reset singleton state between tests so each test starts clean."""
    redis_pool._redis_pool = None
    redis_pool._pool_initialized = False
    redis_pool._fallback_cache = None
    yield
    redis_pool._redis_pool = None
    redis_pool._pool_initialized = False
    redis_pool._fallback_cache = None


@pytest.fixture
def cache():
    """Provide a fresh InMemoryCache with default max_entries."""
    return InMemoryCache()


@pytest.fixture
def small_cache():
    """Provide a fresh InMemoryCache with max_entries=5 for eviction tests."""
    return InMemoryCache(max_entries=5)


# ============================================================================
# InMemoryCache unit tests
# ============================================================================

class TestInMemoryCacheBasicOps:
    """Basic get/set/delete/exists/ping operations on InMemoryCache."""

    def test_get_missing_key(self, cache):
        """get() on a non-existent key returns None."""
        assert cache.get("nonexistent") is None

    def test_set_and_get(self, cache):
        """set() stores a value, get() retrieves it."""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_set_overwrites_existing(self, cache):
        """set() on an existing key overwrites the value."""
        cache.set("key1", "original")
        cache.set("key1", "updated")
        assert cache.get("key1") == "updated"

    def test_setex_with_ttl(self, cache):
        """setex() stores a value that expires after TTL."""
        cache.setex("key1", 3600, "value1")
        assert cache.get("key1") == "value1"

    def test_setex_expired_key_returns_none(self, cache):
        """setex() with expired TTL returns None on get()."""
        # Directly insert an already-expired entry
        expired_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        cache._store["expired_key"] = ("value", expired_time)

        assert cache.get("expired_key") is None

    def test_setex_expired_key_is_removed_from_store(self, cache):
        """Accessing an expired key removes it from internal store."""
        expired_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        cache._store["expired_key"] = ("value", expired_time)

        cache.get("expired_key")
        assert "expired_key" not in cache._store

    def test_delete_existing(self, cache):
        """delete() on existing key returns 1."""
        cache.set("key1", "value1")
        assert cache.delete("key1") == 1

    def test_delete_missing(self, cache):
        """delete() on non-existent key returns 0."""
        assert cache.delete("nonexistent") == 0

    def test_delete_removes_key(self, cache):
        """delete() actually removes the key from the store."""
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_exists_true(self, cache):
        """exists() returns True for a key that is present."""
        cache.set("key1", "value1")
        assert cache.exists("key1") is True

    def test_exists_false(self, cache):
        """exists() returns False for a key that is absent."""
        assert cache.exists("nonexistent") is False

    def test_exists_false_for_expired(self, cache):
        """exists() returns False for an expired key."""
        expired_time = datetime.now(timezone.utc) - timedelta(seconds=1)
        cache._store["expired_key"] = ("value", expired_time)
        assert cache.exists("expired_key") is False

    def test_ping_always_true(self, cache):
        """ping() always returns True (health check for in-memory)."""
        assert cache.ping() is True

    def test_len_empty(self, cache):
        """len() on empty cache returns 0."""
        assert len(cache) == 0

    def test_len_after_inserts(self, cache):
        """len() reflects the number of stored entries."""
        cache.set("a", "1")
        cache.set("b", "2")
        cache.set("c", "3")
        assert len(cache) == 3

    def test_set_without_ttl_does_not_expire(self, cache):
        """set() stores value with None expiry, so it never expires."""
        cache.set("key1", "value1")
        value, expiry = cache._store["key1"]
        assert expiry is None


# ============================================================================
# AC14: InMemoryCache LRU eviction
# ============================================================================

class TestInMemoryCacheLRUEviction:
    """LRU eviction behavior at max_entries boundary."""

    def test_lru_default_max_10k(self):
        """Default InMemoryCache max_entries is 10_000 (AC14)."""
        cache = InMemoryCache()
        assert cache._max_entries == 10_000
        assert cache._max_entries == INMEMORY_MAX_ENTRIES

    def test_lru_eviction_at_max(self, small_cache):
        """Inserting beyond max_entries evicts the oldest entry (LRU)."""
        # Fill cache to capacity (max_entries=5)
        for i in range(5):
            small_cache.set(f"key{i}", f"val{i}")

        assert len(small_cache) == 5

        # Insert one more; oldest (key0) should be evicted
        small_cache.set("key5", "val5")

        assert len(small_cache) == 5
        assert small_cache.get("key0") is None, "Oldest entry should be evicted"
        assert small_cache.get("key5") == "val5", "Newest entry should exist"

    def test_lru_access_refreshes_position(self, small_cache):
        """Accessing an item with get() moves it to end, so it survives eviction."""
        # Fill cache to capacity
        for i in range(5):
            small_cache.set(f"key{i}", f"val{i}")

        # Access key0 (oldest) to refresh it
        small_cache.get("key0")

        # Insert two more items; key1 and key2 should be evicted (they are oldest)
        small_cache.set("key5", "val5")
        small_cache.set("key6", "val6")

        assert small_cache.get("key0") == "val0", "Refreshed key0 should survive"
        assert small_cache.get("key1") is None, "key1 should be evicted"
        assert small_cache.get("key2") is None, "key2 should be evicted"

    def test_lru_setex_triggers_eviction(self, small_cache):
        """setex() also triggers LRU eviction when exceeding max_entries."""
        for i in range(5):
            small_cache.set(f"key{i}", f"val{i}")

        # setex should trigger eviction of key0
        small_cache.setex("key5", 3600, "val5")

        assert len(small_cache) == 5
        assert small_cache.get("key0") is None, "Oldest entry should be evicted by setex"
        assert small_cache.get("key5") == "val5"

    def test_lru_eviction_removes_multiple_if_needed(self):
        """If max_entries is reduced below current size, eviction removes multiple."""
        cache = InMemoryCache(max_entries=3)
        for i in range(3):
            cache.set(f"key{i}", f"val{i}")

        assert len(cache) == 3

        # Decrease is not supported, but inserting more triggers eviction
        cache.set("key3", "val3")
        assert len(cache) == 3
        assert cache.get("key0") is None

    def test_lru_set_existing_key_does_not_increase_size(self, small_cache):
        """Overwriting an existing key should not increase store size."""
        for i in range(5):
            small_cache.set(f"key{i}", f"val{i}")

        # Overwrite key0 -- should NOT trigger eviction of anything
        small_cache.set("key0", "updated")

        assert len(small_cache) == 5
        assert small_cache.get("key0") == "updated"
        # All keys should still exist
        for i in range(1, 5):
            assert small_cache.get(f"key{i}") == f"val{i}"


# ============================================================================
# AC13: Redis unavailable -> fallback to InMemoryCache
# ============================================================================

class TestRedisPoolFallback:
    """Redis unavailable scenarios and InMemoryCache fallback."""

    async def test_get_redis_pool_returns_none_without_url(self, monkeypatch):
        """No REDIS_URL env var -> get_redis_pool() returns None (AC13)."""
        monkeypatch.delenv("REDIS_URL", raising=False)

        result = await get_redis_pool()
        assert result is None

    async def test_get_redis_pool_returns_none_on_connection_failure(self, monkeypatch):
        """Bad REDIS_URL -> connection fails -> returns None (AC13)."""
        monkeypatch.setenv("REDIS_URL", "redis://nonexistent-host:9999/0")

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))

        with patch("redis.asyncio.from_url", return_value=mock_client):
            result = await get_redis_pool()

        assert result is None

    def test_fallback_cache_works(self):
        """get_fallback_cache() returns a functional InMemoryCache (AC13)."""
        cache = get_fallback_cache()
        assert isinstance(cache, InMemoryCache)

        # Verify it is actually functional
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

    def test_get_fallback_cache_singleton(self):
        """get_fallback_cache() always returns the same instance."""
        cache1 = get_fallback_cache()
        cache2 = get_fallback_cache()
        assert cache1 is cache2

    async def test_pool_initialized_flag_set_on_missing_url(self, monkeypatch):
        """After returning None for missing URL, _pool_initialized is True."""
        monkeypatch.delenv("REDIS_URL", raising=False)

        await get_redis_pool()
        assert redis_pool._pool_initialized is True

    async def test_pool_initialized_flag_set_on_connection_failure(self, monkeypatch):
        """After connection failure, _pool_initialized is True (no retry storm)."""
        monkeypatch.setenv("REDIS_URL", "redis://bad-host:6379/0")

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("timeout"))

        with patch("redis.asyncio.from_url", return_value=mock_client):
            await get_redis_pool()

        assert redis_pool._pool_initialized is True


# ============================================================================
# AC12: Concurrent requests share the same connection pool
# ============================================================================

class TestRedisPoolSingleton:
    """Connection pool singleton behavior under concurrent access."""

    async def test_concurrent_get_redis_pool_returns_same_instance(self, monkeypatch):
        """Multiple concurrent get_redis_pool() calls return the same object (AC12)."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        with patch("redis.asyncio.from_url", return_value=mock_client):
            results = await asyncio.gather(
                get_redis_pool(),
                get_redis_pool(),
                get_redis_pool(),
                get_redis_pool(),
                get_redis_pool(),
            )

        # All results should be the exact same object
        first = results[0]
        assert first is not None
        for r in results[1:]:
            assert r is first, "All concurrent calls must return the same pool instance"

    async def test_second_call_uses_cached_pool(self, monkeypatch):
        """Once initialized, subsequent calls skip re-initialization."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        with patch("redis.asyncio.from_url", return_value=mock_client) as mock_from_url:
            first = await get_redis_pool()
            second = await get_redis_pool()

        assert first is second
        # from_url should only be called once
        mock_from_url.assert_called_once()


# ============================================================================
# Pool lifecycle tests (startup, shutdown, is_redis_available)
# ============================================================================

class TestPoolLifecycle:
    """Lifecycle management: startup, shutdown, health checks."""

    async def test_startup_redis_without_url(self, monkeypatch, caplog):
        """startup_redis() without REDIS_URL logs a warning (AC11)."""
        monkeypatch.delenv("REDIS_URL", raising=False)

        import logging
        with caplog.at_level(logging.WARNING, logger="redis_pool"):
            await startup_redis()

        assert any("unavailable" in r.message.lower() or "not set" in r.message.lower()
                    for r in caplog.records), (
            f"Expected a warning log about Redis being unavailable. Got: {[r.message for r in caplog.records]}"
        )

    async def test_shutdown_redis_resets_state(self, monkeypatch):
        """shutdown_redis() clears the singleton so next call re-initializes."""
        # Set up a fake initialized pool
        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()
        redis_pool._redis_pool = mock_client
        redis_pool._pool_initialized = True

        await shutdown_redis()

        assert redis_pool._redis_pool is None
        assert redis_pool._pool_initialized is False
        mock_client.aclose.assert_awaited_once()

    async def test_shutdown_redis_no_pool_is_safe(self):
        """shutdown_redis() when no pool exists does not raise."""
        redis_pool._redis_pool = None
        redis_pool._pool_initialized = False

        # Should not raise
        await shutdown_redis()

        assert redis_pool._redis_pool is None
        assert redis_pool._pool_initialized is False

    async def test_is_redis_available_false_without_url(self, monkeypatch):
        """is_redis_available() returns False when REDIS_URL is not set."""
        monkeypatch.delenv("REDIS_URL", raising=False)

        result = await is_redis_available()
        assert result is False

    async def test_is_redis_available_true_with_healthy_pool(self, monkeypatch):
        """is_redis_available() returns True when pool ping succeeds."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        with patch("redis.asyncio.from_url", return_value=mock_client):
            result = await is_redis_available()

        assert result is True

    async def test_is_redis_available_false_on_ping_failure(self, monkeypatch):
        """is_redis_available() returns False when pool ping raises."""
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

        mock_client = AsyncMock()
        # First ping succeeds (during get_redis_pool init), second fails (during is_redis_available)
        mock_client.ping = AsyncMock(side_effect=[True, ConnectionError("lost connection")])

        with patch("redis.asyncio.from_url", return_value=mock_client):
            result = await is_redis_available()

        assert result is False


# ============================================================================
# AC15: No asyncio.run() in production code
# ============================================================================

class TestNoAsyncioRunInProduction:
    """Ensure production code never calls asyncio.run() (AC15)."""

    def test_no_asyncio_run_in_production(self):
        """Scan all .py files in backend/ (excluding tests/) for asyncio.run() calls."""
        backend_dir = Path(__file__).resolve().parent.parent

        violations = []
        for py_file in backend_dir.rglob("*.py"):
            # Skip test files and virtual environments
            relative = py_file.relative_to(backend_dir)
            parts = relative.parts
            if any(skip in parts for skip in ("tests", ".venv", "venv", "__pycache__", "node_modules")):
                continue

            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for line_num, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                # Skip comments
                if stripped.startswith("#"):
                    continue
                if "asyncio.run(" in line:
                    violations.append(f"{relative}:{line_num}: {stripped}")

        assert violations == [], (
            f"Found asyncio.run() in production code (AC15 violation):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


# ============================================================================
# Pool configuration tests
# ============================================================================

class TestPoolConfiguration:
    """Verify pool is created with correct configuration values."""

    async def test_pool_created_with_correct_params(self, monkeypatch):
        """from_url is called with POOL_MAX_CONNECTIONS, timeouts, decode_responses."""
        monkeypatch.setenv("REDIS_URL", "redis://myhost:6379/2")

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        with patch("redis.asyncio.from_url", return_value=mock_client) as mock_from_url:
            await get_redis_pool()

        mock_from_url.assert_called_once_with(
            "redis://myhost:6379/2",
            decode_responses=True,
            max_connections=20,
            socket_timeout=5,
            socket_connect_timeout=5,
        )

    def test_pool_constants(self):
        """Verify module-level pool configuration constants."""
        assert redis_pool.POOL_MAX_CONNECTIONS == 20
        assert redis_pool.POOL_SOCKET_TIMEOUT == 5
        assert redis_pool.POOL_SOCKET_CONNECT_TIMEOUT == 5
        assert redis_pool.INMEMORY_MAX_ENTRIES == 10_000
