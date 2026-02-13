"""Tests for auth token caching functionality (STORY-214 Frente 2).

Validates the JWT-based local auth cache introduced in STORY-210/203:
- Cache key uses hashlib.sha256(full_token) for deterministic, collision-resistant hashing
- Local JWT decode via PyJWT (no Supabase API calls)
- Failed auth is never cached
- TTL-based expiry (60s)
"""

import hashlib
import os
import time
from unittest.mock import Mock, patch, AsyncMock

import jwt as pyjwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from auth import get_current_user, clear_token_cache, _token_cache, CACHE_TTL


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_cache():
    """Clear token cache before and after each test."""
    clear_token_cache()
    yield
    clear_token_cache()


@pytest.fixture
def mock_credentials():
    """Mock HTTPAuthorizationCredentials with a realistic JWT-shaped token."""
    creds = Mock(spec=HTTPAuthorizationCredentials)
    creds.credentials = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSJ9.abc123"
    return creds


_ENV_VARS = {
    "SUPABASE_JWT_SECRET": "test-secret-key-at-least-32-characters-long!",
    "SUPABASE_URL": "https://test.supabase.co",
}

_VALID_PAYLOAD = {
    "sub": "user-123",
    "email": "test@example.com",
    "role": "authenticated",
    "aud": "authenticated",
}


@pytest.fixture
def mock_jwt_decode():
    """Mock jwt.decode in the auth module to return a valid user payload.

    Also patches environment variables needed by the auth module.
    """
    with patch("auth.jwt.decode") as mock_decode, \
         patch.dict(os.environ, _ENV_VARS):
        mock_decode.return_value = dict(_VALID_PAYLOAD)
        yield mock_decode


# ---------------------------------------------------------------------------
# AC11: Cache key uses hashlib.sha256(full_token).hexdigest()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ac11_cache_key_is_sha256_of_full_token(mock_credentials, mock_jwt_decode):
    """AC11: Verify cache dict key is the SHA-256 hex digest of the full token."""
    token = mock_credentials.credentials
    expected_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    await get_current_user(mock_credentials)

    # Exactly one entry in cache, keyed by SHA-256 of full token
    assert len(_token_cache) == 1
    assert expected_hash in _token_cache

    # The cached value should be a (user_data, timestamp) tuple
    user_data, cached_at = _token_cache[expected_hash]
    assert user_data["id"] == "user-123"
    assert user_data["email"] == "test@example.com"
    assert user_data["role"] == "authenticated"
    assert isinstance(cached_at, float)
    assert cached_at <= time.time()


@pytest.mark.asyncio
async def test_ac11_cache_key_is_64_char_hex(mock_credentials, mock_jwt_decode):
    """AC11 supplementary: SHA-256 hex digest is exactly 64 hex characters."""
    await get_current_user(mock_credentials)

    keys = list(_token_cache.keys())
    assert len(keys) == 1
    key = keys[0]
    assert len(key) == 64
    assert all(c in "0123456789abcdef" for c in key)


# ---------------------------------------------------------------------------
# AC12: Same token returns cached result within TTL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ac12_cache_hit_returns_cached_result(mock_credentials, mock_jwt_decode):
    """AC12: Second call with same token returns cached result; jwt.decode called once."""
    user1 = await get_current_user(mock_credentials)
    assert mock_jwt_decode.call_count == 1

    user2 = await get_current_user(mock_credentials)
    # jwt.decode must NOT be called again
    assert mock_jwt_decode.call_count == 1

    # Same data returned
    assert user1 == user2
    assert user2["id"] == "user-123"
    assert user2["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_ac12_multiple_cache_hits(mock_credentials, mock_jwt_decode):
    """AC12 extended: Many calls within TTL all use cache; jwt.decode called once."""
    for _ in range(10):
        user = await get_current_user(mock_credentials)
        assert user["id"] == "user-123"

    assert mock_jwt_decode.call_count == 1
    assert len(_token_cache) == 1


# ---------------------------------------------------------------------------
# AC13: Different tokens produce different cache entries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ac13_different_tokens_different_cache_entries(mock_jwt_decode):
    """AC13: Two different tokens create two separate cache entries, no collision."""
    creds_a = Mock(spec=HTTPAuthorizationCredentials)
    creds_a.credentials = "token_AAAAAAAAAAAAAAAAAAAAA"

    creds_b = Mock(spec=HTTPAuthorizationCredentials)
    creds_b.credentials = "token_BBBBBBBBBBBBBBBBBBBBB"

    # Return different users for different tokens
    def decode_side_effect(token, *args, **kwargs):
        if "AAAA" in token:
            return {"sub": "user-aaa", "email": "a@test.com", "role": "authenticated", "aud": "authenticated"}
        return {"sub": "user-bbb", "email": "b@test.com", "role": "authenticated", "aud": "authenticated"}

    mock_jwt_decode.side_effect = decode_side_effect

    user_a = await get_current_user(creds_a)
    user_b = await get_current_user(creds_b)

    assert user_a["id"] == "user-aaa"
    assert user_b["id"] == "user-bbb"

    # Two separate entries
    assert len(_token_cache) == 2
    assert mock_jwt_decode.call_count == 2

    hash_a = hashlib.sha256(creds_a.credentials.encode("utf-8")).hexdigest()
    hash_b = hashlib.sha256(creds_b.credentials.encode("utf-8")).hexdigest()
    assert hash_a != hash_b
    assert hash_a in _token_cache
    assert hash_b in _token_cache
    assert _token_cache[hash_a][0]["id"] == "user-aaa"
    assert _token_cache[hash_b][0]["id"] == "user-bbb"


@pytest.mark.asyncio
async def test_ac13_tokens_sharing_prefix_no_collision(mock_jwt_decode):
    """AC13 extended: Tokens sharing the same 16-char prefix must NOT collide."""
    shared_prefix = "eyJhbGciOiJIUzI1"  # 16 chars shared

    creds_x = Mock(spec=HTTPAuthorizationCredentials)
    creds_x.credentials = shared_prefix + "_suffix_X_unique"

    creds_y = Mock(spec=HTTPAuthorizationCredentials)
    creds_y.credentials = shared_prefix + "_suffix_Y_unique"

    def decode_side_effect(token, *args, **kwargs):
        if "X_unique" in token:
            return {"sub": "user-x", "email": "x@test.com", "role": "authenticated", "aud": "authenticated"}
        return {"sub": "user-y", "email": "y@test.com", "role": "authenticated", "aud": "authenticated"}

    mock_jwt_decode.side_effect = decode_side_effect

    user_x = await get_current_user(creds_x)
    user_y = await get_current_user(creds_y)

    # Must be separate users despite shared prefix
    assert user_x["id"] == "user-x"
    assert user_y["id"] == "user-y"
    assert len(_token_cache) == 2
    assert mock_jwt_decode.call_count == 2


# ---------------------------------------------------------------------------
# AC14: Cache expires after TTL (60s)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ac14_cache_expires_after_ttl(mock_credentials, mock_jwt_decode):
    """AC14: After TTL elapses, jwt.decode is called again on next request."""
    # Populate cache
    await get_current_user(mock_credentials)
    assert mock_jwt_decode.call_count == 1

    # Manually expire the cache entry
    token_hash = hashlib.sha256(mock_credentials.credentials.encode("utf-8")).hexdigest()
    user_data, _ = _token_cache[token_hash]
    _token_cache[token_hash] = (user_data, time.time() - CACHE_TTL - 1)

    # Next call should re-validate
    user2 = await get_current_user(mock_credentials)
    assert mock_jwt_decode.call_count == 2
    assert user2["id"] == "user-123"


@pytest.mark.asyncio
async def test_ac14_ttl_boundary_exactly_at_ttl(mock_credentials, mock_jwt_decode):
    """AC14 boundary: Entry aged exactly CACHE_TTL seconds should be expired."""
    await get_current_user(mock_credentials)
    assert mock_jwt_decode.call_count == 1

    # Set cache timestamp to exactly CACHE_TTL ago
    token_hash = hashlib.sha256(mock_credentials.credentials.encode("utf-8")).hexdigest()
    user_data, _ = _token_cache[token_hash]
    _token_cache[token_hash] = (user_data, time.time() - CACHE_TTL)

    # The auth code uses `age < CACHE_TTL`, so exactly CACHE_TTL is expired
    await get_current_user(mock_credentials)
    assert mock_jwt_decode.call_count == 2


@pytest.mark.asyncio
async def test_ac14_ttl_boundary_just_before_ttl(mock_credentials, mock_jwt_decode):
    """AC14 boundary: Entry aged slightly less than CACHE_TTL should still be valid."""
    await get_current_user(mock_credentials)
    assert mock_jwt_decode.call_count == 1

    # Set cache timestamp to just under CACHE_TTL ago
    token_hash = hashlib.sha256(mock_credentials.credentials.encode("utf-8")).hexdigest()
    user_data, _ = _token_cache[token_hash]
    _token_cache[token_hash] = (user_data, time.time() - CACHE_TTL + 1)

    # Should still be a cache hit
    await get_current_user(mock_credentials)
    assert mock_jwt_decode.call_count == 1


@pytest.mark.asyncio
async def test_ac14_expired_entry_removed_from_cache(mock_credentials, mock_jwt_decode):
    """AC14: Expired entry is deleted from cache, then re-populated on re-validation."""
    await get_current_user(mock_credentials)
    token_hash = hashlib.sha256(mock_credentials.credentials.encode("utf-8")).hexdigest()

    # Force expiry
    user_data, _ = _token_cache[token_hash]
    _token_cache[token_hash] = (user_data, time.time() - CACHE_TTL - 10)

    # Re-validate populates a fresh entry
    await get_current_user(mock_credentials)

    # Cache should have exactly 1 entry with a recent timestamp
    assert len(_token_cache) == 1
    assert token_hash in _token_cache
    _, new_ts = _token_cache[token_hash]
    assert time.time() - new_ts < 2  # freshly cached


# ---------------------------------------------------------------------------
# AC15: Failed auth is NOT cached
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ac15_expired_signature_not_cached(mock_credentials):
    """AC15: jwt.ExpiredSignatureError raises 401 and is NOT cached."""
    with patch("auth.jwt.decode") as mock_decode, \
         patch.dict(os.environ, _ENV_VARS):
        mock_decode.side_effect = pyjwt.ExpiredSignatureError("Token expired")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "expirado" in exc_info.value.detail.lower()
        assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_ac15_invalid_token_error_not_cached(mock_credentials):
    """AC15: jwt.InvalidTokenError raises 401 and is NOT cached."""
    with patch("auth.jwt.decode") as mock_decode, \
         patch.dict(os.environ, _ENV_VARS):
        mock_decode.side_effect = pyjwt.InvalidTokenError("Bad token")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "invalido" in exc_info.value.detail.lower()
        assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_ac15_missing_sub_claim_not_cached(mock_credentials):
    """AC15: Token with no 'sub' claim raises 401 and is NOT cached."""
    with patch("auth.jwt.decode") as mock_decode, \
         patch.dict(os.environ, _ENV_VARS):
        mock_decode.return_value = {
            "email": "test@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            # "sub" is intentionally missing
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "user id" in exc_info.value.detail.lower()
        assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_ac15_decode_exception_not_cached(mock_credentials):
    """AC15: Generic decode exception raises 401 and is NOT cached."""
    with patch("auth.jwt.decode") as mock_decode, \
         patch.dict(os.environ, _ENV_VARS), \
         patch("auth.log_auth_event"):
        mock_decode.side_effect = Exception("Unexpected decode failure")

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "invalido ou expirado" in exc_info.value.detail.lower()
        assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_ac15_missing_jwt_secret_not_cached(mock_credentials):
    """AC15: Missing SUPABASE_JWT_SECRET raises 500 and is NOT cached."""
    env_no_secret = {"SUPABASE_URL": "https://test.supabase.co"}
    with patch.dict(os.environ, env_no_secret, clear=True):
        # Ensure SUPABASE_JWT_SECRET is definitely not set
        os.environ.pop("SUPABASE_JWT_SECRET", None)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)

        assert exc_info.value.status_code == 500
        assert "not configured" in exc_info.value.detail.lower()
        assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_ac15_failed_then_success_only_caches_success(mock_credentials):
    """AC15 extended: A failed attempt followed by a success only caches the success."""
    with patch("auth.jwt.decode") as mock_decode, \
         patch.dict(os.environ, _ENV_VARS), \
         patch("auth.log_auth_event"):
        # First call: fail
        mock_decode.side_effect = pyjwt.InvalidTokenError("Bad")
        with pytest.raises(HTTPException):
            await get_current_user(mock_credentials)
        assert len(_token_cache) == 0

        # Second call: succeed
        mock_decode.side_effect = None
        mock_decode.return_value = dict(_VALID_PAYLOAD)
        user = await get_current_user(mock_credentials)

        assert user["id"] == "user-123"
        assert len(_token_cache) == 1


# ---------------------------------------------------------------------------
# AC16: Concurrent requests for same token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ac16_sequential_requests_same_token_one_decode(mock_credentials, mock_jwt_decode):
    """AC16: Multiple sequential requests with same token only call jwt.decode once."""
    results = []
    for _ in range(5):
        user = await get_current_user(mock_credentials)
        results.append(user)

    # All results should match
    assert all(u["id"] == "user-123" for u in results)
    assert all(u["email"] == "test@example.com" for u in results)

    # jwt.decode called only for the first request
    assert mock_jwt_decode.call_count == 1
    assert len(_token_cache) == 1


@pytest.mark.asyncio
async def test_ac16_concurrent_async_requests_same_token(mock_credentials, mock_jwt_decode):
    """AC16: Concurrent async requests with same token hit cache efficiently."""
    import asyncio

    tasks = [get_current_user(mock_credentials) for _ in range(10)]
    results = await asyncio.gather(*tasks)

    assert all(u["id"] == "user-123" for u in results)
    # The first call populates the cache; subsequent concurrent calls may
    # also call jwt.decode if they start before the cache is populated,
    # but at minimum it should be far fewer than 10.
    # In practice, since Python asyncio is single-threaded and get_current_user
    # is not truly concurrent (no await before cache check), all 10 should
    # see the cache after the first one completes.
    assert mock_jwt_decode.call_count <= 1


# ---------------------------------------------------------------------------
# clear_token_cache() tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clear_cache_returns_count():
    """clear_token_cache() removes all entries and returns the count removed."""
    # Populate cache with fake entries using SHA-256 hex keys
    key1 = hashlib.sha256(b"token1").hexdigest()
    key2 = hashlib.sha256(b"token2").hexdigest()
    key3 = hashlib.sha256(b"token3").hexdigest()

    _token_cache[key1] = ({"id": "user1"}, time.time())
    _token_cache[key2] = ({"id": "user2"}, time.time())
    _token_cache[key3] = ({"id": "user3"}, time.time())

    count = clear_token_cache()

    assert count == 3
    assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_clear_cache_empty_returns_zero():
    """clear_token_cache() on empty cache returns 0."""
    count = clear_token_cache()
    assert count == 0
    assert len(_token_cache) == 0


@pytest.mark.asyncio
async def test_clear_cache_then_revalidate(mock_credentials, mock_jwt_decode):
    """After clearing cache, next request must call jwt.decode again."""
    # Populate cache
    await get_current_user(mock_credentials)
    assert mock_jwt_decode.call_count == 1
    assert len(_token_cache) == 1

    # Clear
    count = clear_token_cache()
    assert count == 1
    assert len(_token_cache) == 0

    # Next call must re-validate
    await get_current_user(mock_credentials)
    assert mock_jwt_decode.call_count == 2
    assert len(_token_cache) == 1


# ---------------------------------------------------------------------------
# No credentials (anonymous access)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_credentials_returns_none():
    """No credentials provided returns None with no cache interaction."""
    user = await get_current_user(None)
    assert user is None
    assert len(_token_cache) == 0


# ---------------------------------------------------------------------------
# Performance: cache hit vs miss
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_hit_faster_than_miss(mock_credentials, mock_jwt_decode):
    """Informational: cache hit should be faster than cache miss."""
    import time as time_module

    # Cache miss (first call)
    start = time_module.perf_counter()
    await get_current_user(mock_credentials)
    miss_time = time_module.perf_counter() - start

    # Cache hit (second call)
    start = time_module.perf_counter()
    await get_current_user(mock_credentials)
    hit_time = time_module.perf_counter() - start

    # With mocks the difference is small, but hit should not be slower
    # The key assertion is that jwt.decode was only called once
    assert mock_jwt_decode.call_count == 1

    # Informational output
    print(f"\nCache miss: {miss_time * 1000:.3f}ms")
    print(f"Cache hit:  {hit_time * 1000:.3f}ms")
    if miss_time > 0:
        print(f"Speedup:    {miss_time / max(hit_time, 1e-9):.1f}x")
