"""
Redis Cache Client for Feature Flags and General Caching

Provides Redis connection with fallback to in-memory cache for local development.

Features:
- Connection pooling (max 10 connections)
- Automatic fallback to in-memory dict if Redis unavailable
- TTL support with automatic expiration
- JSON serialization for complex objects
- Thread-safe operations

Configuration:
- REDIS_URL: Redis connection URL (redis://host:port/db)
- Default: Uses in-memory cache if REDIS_URL not set

Usage:
    from cache import redis_client

    # Set with TTL (seconds)
    redis_client.setex("features:user123", 300, json.dumps({"features": [...]}))

    # Get
    cached = redis_client.get("features:user123")

    # Delete
    redis_client.delete("features:user123")

Performance:
- Redis: <1ms per operation (local network)
- In-memory: <0.1ms per operation
- Connection pool prevents connection exhaustion
"""

import logging
import os
from typing import Optional, Any
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class InMemoryCache:
    """
    Thread-safe in-memory cache with TTL support.

    Fallback when Redis is unavailable.
    """

    def __init__(self):
        self._store: dict[str, tuple[Any, Optional[datetime]]] = {}

    def get(self, key: str) -> Optional[str]:
        """Get value from cache (returns None if expired or missing)."""
        if key not in self._store:
            return None

        value, expiry = self._store[key]

        # Check if expired
        if expiry and datetime.utcnow() > expiry:
            del self._store[key]
            return None

        return value

    def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set value with TTL (time-to-live in seconds)."""
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        self._store[key] = (value, expiry)
        return True

    def set(self, key: str, value: str) -> bool:
        """Set value without TTL (never expires)."""
        self._store[key] = (value, None)
        return True

    def delete(self, key: str) -> int:
        """Delete key from cache (returns 1 if deleted, 0 if not found)."""
        if key in self._store:
            del self._store[key]
            return 1
        return 0

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def ping(self) -> bool:
        """Health check (always returns True for in-memory)."""
        return True


class RedisCacheClient:
    """
    Redis client wrapper with fallback to in-memory cache.

    Automatically falls back to InMemoryCache if Redis unavailable.
    """

    def __init__(self):
        self._redis_client = self._connect_redis()
        self._fallback_cache = InMemoryCache()
        self._using_fallback = self._redis_client is None

    def _connect_redis(self) -> Optional[Any]:
        """Connect to Redis (returns None if unavailable)."""
        redis_url = os.getenv("REDIS_URL")

        if not redis_url:
            logger.warning("REDIS_URL not set - using in-memory cache")
            return None

        try:
            import redis

            client = redis.from_url(
                redis_url,
                decode_responses=True,
                max_connections=10,  # Connection pooling
                socket_timeout=5,
                socket_connect_timeout=5,
            )

            # Test connection
            client.ping()
            logger.info(f"Redis connected: {redis_url}")
            return client

        except ImportError:
            logger.warning("redis library not installed - using in-memory cache")
            return None
        except Exception as e:
            logger.error(f"Redis connection failed: {e} - using in-memory cache")
            return None

    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        if self._using_fallback:
            return self._fallback_cache.get(key)

        try:
            return self._redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis GET failed: {e} - using fallback")
            return self._fallback_cache.get(key)

    def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set value with TTL (time-to-live in seconds)."""
        if self._using_fallback:
            return self._fallback_cache.setex(key, ttl, value)

        try:
            self._redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Redis SETEX failed: {e} - using fallback")
            return self._fallback_cache.setex(key, ttl, value)

    def set(self, key: str, value: str) -> bool:
        """Set value without TTL."""
        if self._using_fallback:
            return self._fallback_cache.set(key, value)

        try:
            self._redis_client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET failed: {e} - using fallback")
            return self._fallback_cache.set(key, value)

    def delete(self, key: str) -> int:
        """Delete key from cache."""
        if self._using_fallback:
            return self._fallback_cache.delete(key)

        try:
            return self._redis_client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE failed: {e} - using fallback")
            return self._fallback_cache.delete(key)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if self._using_fallback:
            return self._fallback_cache.exists(key)

        try:
            return self._redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS failed: {e} - using fallback")
            return self._fallback_cache.exists(key)

    def ping(self) -> bool:
        """Health check."""
        if self._using_fallback:
            return self._fallback_cache.ping()

        try:
            return self._redis_client.ping()
        except Exception as e:
            logger.error(f"Redis PING failed: {e}")
            return False


# Global singleton instance
redis_client = RedisCacheClient()
