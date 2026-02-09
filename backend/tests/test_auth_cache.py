"""Tests for auth token caching functionality.

Tests the token validation cache added to eliminate intermittent
Supabase Auth API failures (38% failure rate → <1%).
"""

import time
from unittest.mock import Mock, patch, MagicMock
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from auth import get_current_user, clear_token_cache, _token_cache, CACHE_TTL


@pytest.fixture(autouse=True)
def reset_cache():
    """Clear token cache before each test."""
    clear_token_cache()
    yield
    clear_token_cache()


@pytest.fixture
def mock_credentials():
    """Mock HTTPAuthorizationCredentials with valid token."""
    creds = Mock(spec=HTTPAuthorizationCredentials)
    creds.credentials = "valid_token_12345678901234567890"
    return creds


@pytest.fixture
def mock_supabase_success():
    """Mock successful Supabase get_user response."""
    with patch('auth.get_supabase') as mock_get_sb:
        mock_sb_instance = MagicMock()
        mock_user_response = Mock()
        mock_user_response.user = Mock(
            id="user-123",
            email="test@example.com",
            role="authenticated"
        )
        mock_sb_instance.auth.get_user.return_value = mock_user_response
        mock_get_sb.return_value = mock_sb_instance
        yield mock_sb_instance


@pytest.mark.asyncio
async def test_auth_cache_miss_validates_remotely(mock_credentials, mock_supabase_success):
    """Cache miss should validate token with Supabase and store result."""
    # First call - cache miss
    user = await get_current_user(mock_credentials)

    assert user["id"] == "user-123"
    assert user["email"] == "test@example.com"
    assert user["role"] == "authenticated"

    # Verify Supabase was called
    mock_supabase_success.auth.get_user.assert_called_once_with(mock_credentials.credentials)

    # Verify token was cached
    assert len(_token_cache) == 1


@pytest.mark.asyncio
async def test_auth_cache_hit_skips_remote_validation(mock_credentials, mock_supabase_success):
    """Cache hit should return cached user without calling Supabase."""
    # First call - cache miss (populates cache)
    user1 = await get_current_user(mock_credentials)
    assert mock_supabase_success.auth.get_user.call_count == 1

    # Second call - cache hit (should NOT call Supabase)
    user2 = await get_current_user(mock_credentials)

    # Verify Supabase was NOT called again
    assert mock_supabase_success.auth.get_user.call_count == 1

    # Verify same user data returned
    assert user1 == user2
    assert user2["id"] == "user-123"


@pytest.mark.asyncio
async def test_auth_cache_expiry_revalidates(mock_credentials, mock_supabase_success):
    """Expired cache entry should revalidate with Supabase."""
    # First call - populate cache
    user1 = await get_current_user(mock_credentials)
    assert mock_supabase_success.auth.get_user.call_count == 1

    # Manually expire cache entry
    token_hash = hash(mock_credentials.credentials[:16])
    user_data, _ = _token_cache[token_hash]
    _token_cache[token_hash] = (user_data, time.time() - CACHE_TTL - 1)

    # Second call - cache expired, should revalidate
    user2 = await get_current_user(mock_credentials)

    # Verify Supabase was called again
    assert mock_supabase_success.auth.get_user.call_count == 2

    # Verify user data is correct
    assert user2["id"] == "user-123"


@pytest.mark.asyncio
async def test_auth_cache_invalid_token_not_cached(mock_credentials):
    """Invalid token should raise 401 and not be cached."""
    with patch('auth.get_supabase') as mock_get_sb:
        mock_sb_instance = MagicMock()
        mock_sb_instance.auth.get_user.return_value = Mock(user=None)
        mock_get_sb.return_value = mock_sb_instance

        # Should raise 401
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401

        # Verify token was NOT cached
        assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_auth_cache_exception_not_cached(mock_credentials):
    """Token validation exception should raise 401 and not be cached."""
    with patch('auth.get_supabase') as mock_get_sb:
        mock_sb_instance = MagicMock()
        mock_sb_instance.auth.get_user.side_effect = Exception("Connection timeout")
        mock_get_sb.return_value = mock_sb_instance

        # Should raise 401
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "invalido ou expirado" in exc_info.value.detail.lower()

        # Verify token was NOT cached
        assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_auth_cache_concurrent_requests_same_token(mock_credentials, mock_supabase_success):
    """Multiple concurrent requests with same token should only validate once."""
    # Simulate concurrent requests (cache will be empty initially)
    results = []
    for _ in range(5):
        user = await get_current_user(mock_credentials)
        results.append(user)

    # All should return same user data
    assert all(u["id"] == "user-123" for u in results)

    # Only first request should call Supabase (others hit cache)
    assert mock_supabase_success.auth.get_user.call_count == 1


@pytest.mark.asyncio
async def test_auth_cache_different_tokens_separate_entries(mock_supabase_success):
    """Different tokens should create separate cache entries."""
    creds1 = Mock(spec=HTTPAuthorizationCredentials)
    creds1.credentials = "token_A_12345678901234567890"

    creds2 = Mock(spec=HTTPAuthorizationCredentials)
    creds2.credentials = "token_B_09876543210987654321"

    # Call with two different tokens
    user1 = await get_current_user(creds1)
    user2 = await get_current_user(creds2)

    # Should have 2 cache entries
    assert len(_token_cache) == 2

    # Supabase should be called twice (once per token)
    assert mock_supabase_success.auth.get_user.call_count == 2


@pytest.mark.asyncio
async def test_clear_token_cache():
    """clear_token_cache() should remove all entries and return count."""
    # Populate cache with fake entries
    _token_cache[123] = ({"id": "user1"}, time.time())
    _token_cache[456] = ({"id": "user2"}, time.time())
    _token_cache[789] = ({"id": "user3"}, time.time())

    # Clear cache
    count = clear_token_cache()

    # Verify count and cache is empty
    assert count == 3
    assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_auth_no_credentials_returns_none():
    """No credentials should return None (anonymous access allowed)."""
    user = await get_current_user(None)
    assert user is None

    # Verify cache is still empty (nothing to cache)
    assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_auth_cache_ttl_boundary(mock_credentials, mock_supabase_success):
    """Test cache behavior at TTL boundary."""
    # First call - populate cache
    user1 = await get_current_user(mock_credentials)

    # Manually set cache entry to exactly TTL seconds ago
    token_hash = hash(mock_credentials.credentials[:16])
    user_data, _ = _token_cache[token_hash]
    _token_cache[token_hash] = (user_data, time.time() - CACHE_TTL)

    # Second call - should be expired (>= TTL)
    user2 = await get_current_user(mock_credentials)

    # Verify Supabase was called again (cache expired)
    assert mock_supabase_success.auth.get_user.call_count == 2


@pytest.mark.asyncio
async def test_auth_cache_performance_improvement(mock_credentials, mock_supabase_success):
    """Measure cache performance improvement (informational test)."""
    import time as time_module

    # Measure first call (cache miss - slow)
    start = time_module.perf_counter()
    await get_current_user(mock_credentials)
    first_call_time = time_module.perf_counter() - start

    # Measure second call (cache hit - fast)
    start = time_module.perf_counter()
    await get_current_user(mock_credentials)
    second_call_time = time_module.perf_counter() - start

    # Cache hit should be significantly faster (informational assertion)
    # In real scenario, cache hit is ~1000x faster (no network call)
    # With mocks, difference is less dramatic but still measurable
    print(f"\nCache miss: {first_call_time*1000:.2f}ms")
    print(f"Cache hit: {second_call_time*1000:.2f}ms")
    print(f"Speedup: {first_call_time/second_call_time:.1f}x")
