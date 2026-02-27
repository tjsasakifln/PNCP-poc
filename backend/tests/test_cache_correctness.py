"""STORY-306: Cache Correctness & Data Integrity tests.

Covers:
  AC14: Same query with different dates → different cache keys
  AC15: Fallback serves cache with cache_fallback=True flag
  AC16: Dual-read returns cache of old key when new key misses
  AC17: SWR triggers background revalidation when serving stale
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from search_cache import (
    compute_search_hash,
    compute_search_hash_without_dates,
    _normalize_date,
    get_from_cache,
    get_from_cache_cascade,
    CACHE_FRESH_HOURS,
    CACHE_STALE_HOURS,
    _format_cache_date_range,
)


# ============================================================================
# AC14: Same query with different dates → different cache keys
# ============================================================================


class TestCacheKeyWithDates:
    """AC14: Different dates must produce different cache keys."""

    def test_same_query_different_dates_produce_different_keys(self):
        """AC3/AC14: setor=X, UF=SP, periodo=7d vs periodo=30d → different cache keys."""
        params_7d = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }
        params_30d = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-01-28",
            "date_to": "2026-02-27",
        }
        assert compute_search_hash(params_7d) != compute_search_hash(params_30d)

    def test_same_query_same_dates_produce_same_key(self):
        params1 = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }
        params2 = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }
        assert compute_search_hash(params1) == compute_search_hash(params2)

    def test_none_dates_produce_consistent_key(self):
        """Missing dates should still produce a valid, consistent key."""
        params1 = {"setor_id": "vestuario", "ufs": ["SP"]}
        params2 = {"setor_id": "vestuario", "ufs": ["SP"], "date_from": None, "date_to": None}
        assert compute_search_hash(params1) == compute_search_hash(params2)

    def test_key_with_dates_differs_from_key_without_dates(self):
        """New key (with dates) must differ from legacy key (without dates) when dates are present."""
        params = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }
        assert compute_search_hash(params) != compute_search_hash_without_dates(params)

    def test_key_without_dates_matches_legacy_behavior(self):
        """compute_search_hash_without_dates should produce same hash as old compute_search_hash."""
        params = {
            "setor_id": "vestuario",
            "ufs": ["RJ", "SP"],
            "status": "aberta",
            "modalidades": ["pregao", "concurso"],
            "modo_busca": "setor",
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }
        # Legacy hash is the same regardless of dates
        legacy = compute_search_hash_without_dates(params)
        params_no_dates = {
            "setor_id": "vestuario",
            "ufs": ["RJ", "SP"],
            "status": "aberta",
            "modalidades": ["pregao", "concurso"],
            "modo_busca": "setor",
        }
        assert legacy == compute_search_hash_without_dates(params_no_dates)

    def test_all_params_included_in_key(self):
        """AC4: Verify all params that affect results are in the hash."""
        base = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "status": "aberta",
            "modalidades": [6],
            "modo_busca": "setor",
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }
        # Changing any param should produce a different hash
        for key, alt_value in [
            ("setor_id", "informatica"),
            ("ufs", ["RJ"]),
            ("status", "encerrada"),
            ("modalidades", [4, 5]),
            ("modo_busca", "termo"),
            ("date_from", "2026-02-01"),
            ("date_to", "2026-02-28"),
        ]:
            modified = {**base, key: alt_value}
            assert compute_search_hash(base) != compute_search_hash(modified), (
                f"Changing {key} should produce a different hash"
            )

    def test_uf_order_does_not_affect_key(self):
        h1 = compute_search_hash({"setor_id": 1, "ufs": ["SP", "RJ"], "date_from": "2026-02-20"})
        h2 = compute_search_hash({"setor_id": 1, "ufs": ["RJ", "SP"], "date_from": "2026-02-20"})
        assert h1 == h2


# ============================================================================
# AC2: Date normalization
# ============================================================================


class TestDateNormalization:
    """AC2: Dates normalized to ISO 8601 (YYYY-MM-DD) before hashing."""

    def test_iso_date_passthrough(self):
        assert _normalize_date("2026-02-27") == "2026-02-27"

    def test_iso_datetime_truncated(self):
        assert _normalize_date("2026-02-27T14:30:00") == "2026-02-27"

    def test_iso_datetime_with_tz_truncated(self):
        assert _normalize_date("2026-02-27T14:30:00+00:00") == "2026-02-27"

    def test_none_returns_none(self):
        assert _normalize_date(None) is None

    def test_empty_string_returns_none(self):
        assert _normalize_date("") is None

    def test_different_formats_produce_same_key(self):
        """ISO datetime vs ISO date → same hash."""
        p1 = {"setor_id": "x", "ufs": ["SP"], "date_from": "2026-02-20", "date_to": "2026-02-27"}
        p2 = {"setor_id": "x", "ufs": ["SP"], "date_from": "2026-02-20T00:00:00", "date_to": "2026-02-27T23:59:59"}
        assert compute_search_hash(p1) == compute_search_hash(p2)

    def test_alternative_date_field_names(self):
        """Support data_inicio/data_fim and data_inicial/data_final."""
        p1 = {"setor_id": "x", "ufs": ["SP"], "date_from": "2026-02-20"}
        p2 = {"setor_id": "x", "ufs": ["SP"], "data_inicio": "2026-02-20"}
        p3 = {"setor_id": "x", "ufs": ["SP"], "data_inicial": "2026-02-20"}
        h1, h2, h3 = compute_search_hash(p1), compute_search_hash(p2), compute_search_hash(p3)
        assert h1 == h2 == h3


# ============================================================================
# AC15: Fallback serves cache with cache_fallback=True
# ============================================================================


class TestCacheFallbackFlag:
    """AC15: When serving from legacy key, cache_fallback=True must be set."""

    @pytest.mark.asyncio
    @patch("config.CACHE_LEGACY_KEY_FALLBACK", True)
    @patch("search_cache._get_global_fallback_from_supabase", new_callable=AsyncMock, return_value=None)
    async def test_fallback_serves_with_flag(self, mock_global):
        """When exact key misses but legacy key hits, result has cache_fallback=True."""
        now = datetime.now(timezone.utc)
        fresh_data = {
            "results": [{"id": "bid-1"}],
            "fetched_at": now.isoformat(),
            "sources_json": ["PNCP"],
            "priority": "warm",
            "access_count": 2,
            "last_accessed_at": now.isoformat(),
        }

        params = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }

        # Exact key (with dates) → miss; Legacy key (without dates) → hit
        exact_hash = compute_search_hash(params)
        legacy_hash = compute_search_hash_without_dates(params)

        async def mock_supabase(user_id, params_hash):
            if params_hash == legacy_hash:
                return fresh_data
            return None  # Exact key misses

        with patch("search_cache._get_from_supabase", side_effect=mock_supabase), \
             patch("search_cache._get_from_redis", return_value=None), \
             patch("search_cache._get_from_local", return_value=None), \
             patch("search_cache._increment_and_reclassify", new_callable=AsyncMock):
            result = await get_from_cache("user-1", params)

        assert result is not None
        assert result["cache_fallback"] is True
        assert result["cache_date_range"] is not None
        assert len(result["results"]) == 1

    @pytest.mark.asyncio
    @patch("search_cache._get_global_fallback_from_supabase", new_callable=AsyncMock, return_value=None)
    async def test_exact_hit_no_fallback_flag(self, mock_global):
        """When exact key hits, cache_fallback should not be set."""
        now = datetime.now(timezone.utc)
        fresh_data = {
            "results": [{"id": "bid-1"}],
            "fetched_at": now.isoformat(),
            "sources_json": ["PNCP"],
            "priority": "warm",
            "access_count": 2,
            "last_accessed_at": now.isoformat(),
        }

        params = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }

        with patch("search_cache._get_from_supabase", new_callable=AsyncMock, return_value=fresh_data), \
             patch("search_cache._increment_and_reclassify", new_callable=AsyncMock):
            result = await get_from_cache("user-1", params)

        assert result is not None
        assert result.get("cache_fallback", False) is False


# ============================================================================
# AC16: Dual-read returns cache of old key when new key misses
# ============================================================================


class TestDualReadLegacyKey:
    """AC16: Dual-read returns legacy cache when new key misses."""

    @pytest.mark.asyncio
    @patch("config.CACHE_LEGACY_KEY_FALLBACK", True)
    @patch("search_cache._get_global_fallback_from_supabase", new_callable=AsyncMock, return_value=None)
    async def test_cascade_dual_read_legacy_key(self, mock_global):
        """get_from_cache_cascade tries legacy key when exact key misses."""
        now = datetime.now(timezone.utc)
        stale_data = {
            "results": [{"id": "bid-old"}],
            "fetched_at": (now - timedelta(hours=2)).isoformat(),
            "sources_json": ["PNCP"],
            "priority": "cold",
            "access_count": 1,
            "last_accessed_at": now.isoformat(),
        }

        params = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }

        legacy_hash = compute_search_hash_without_dates(params)

        def mock_redis(cache_key):
            # _get_from_redis receives raw hash, adds search_cache: prefix internally
            # We mock at _get_from_redis level — cache_key IS the raw hash
            if cache_key == legacy_hash:
                return stale_data  # _get_from_redis returns parsed dict
            return None

        with patch("search_cache._get_from_redis", side_effect=mock_redis), \
             patch("search_cache._get_from_supabase", new_callable=AsyncMock, return_value=None), \
             patch("search_cache._get_from_local", return_value=None):
            result = await get_from_cache_cascade("user-1", params)

        assert result is not None
        assert result["cache_fallback"] is True
        assert result["results"] == [{"id": "bid-old"}]

    @pytest.mark.asyncio
    @patch("config.CACHE_LEGACY_KEY_FALLBACK", False)
    @patch("search_cache._get_global_fallback_from_supabase", new_callable=AsyncMock, return_value=None)
    async def test_dual_read_disabled_skips_legacy(self, mock_global):
        """When CACHE_LEGACY_KEY_FALLBACK=False, legacy key is not tried."""
        params = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }

        with patch("search_cache._get_from_redis", return_value=None), \
             patch("search_cache._get_from_supabase", new_callable=AsyncMock, return_value=None), \
             patch("search_cache._get_from_local", return_value=None):
            result = await get_from_cache_cascade("user-1", params)

        assert result is None  # No fallback attempted


# ============================================================================
# AC17: SWR triggers background revalidation when serving stale
# ============================================================================


class TestSWRBackgroundRevalidation:
    """AC17: SWR dispatches background revalidation when serving stale data."""

    @pytest.mark.asyncio
    @patch("search_cache._get_global_fallback_from_supabase", new_callable=AsyncMock, return_value=None)
    async def test_stale_cache_triggers_revalidation_tracking(self, mock_global):
        """When cache_age_hours > CACHE_FRESH_HOURS, result is marked as stale."""
        now = datetime.now(timezone.utc)
        stale_time = now - timedelta(hours=CACHE_FRESH_HOURS + 1)  # 5h old (stale)
        stale_data = {
            "results": [{"id": "bid-stale"}],
            "fetched_at": stale_time.isoformat(),
            "sources_json": ["PNCP"],
            "priority": "warm",
            "access_count": 5,
            "last_accessed_at": now.isoformat(),
        }

        params = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }

        with patch("search_cache._get_from_supabase", new_callable=AsyncMock, return_value=stale_data), \
             patch("search_cache._increment_and_reclassify", new_callable=AsyncMock):
            result = await get_from_cache("user-1", params)

        assert result is not None
        assert result["is_stale"] is True
        assert result["cache_age_hours"] > CACHE_FRESH_HOURS

    @pytest.mark.asyncio
    @patch("search_cache._get_global_fallback_from_supabase", new_callable=AsyncMock, return_value=None)
    async def test_fresh_cache_not_stale(self, mock_global):
        """When cache_age_hours < CACHE_FRESH_HOURS, result is not marked as stale."""
        now = datetime.now(timezone.utc)
        fresh_time = now - timedelta(hours=1)  # 1h old (fresh)
        fresh_data = {
            "results": [{"id": "bid-fresh"}],
            "fetched_at": fresh_time.isoformat(),
            "sources_json": ["PNCP"],
            "priority": "hot",
            "access_count": 10,
            "last_accessed_at": now.isoformat(),
        }

        params = {
            "setor_id": "vestuario",
            "ufs": ["SP"],
            "date_from": "2026-02-20",
            "date_to": "2026-02-27",
        }

        with patch("search_cache._get_from_supabase", new_callable=AsyncMock, return_value=fresh_data), \
             patch("search_cache._increment_and_reclassify", new_callable=AsyncMock):
            result = await get_from_cache("user-1", params)

        assert result is not None
        assert result["is_stale"] is False


# ============================================================================
# TTL policy validation (AC8-AC11)
# ============================================================================


class TestTTLPolicy:
    """AC8-AC11: TTL policy consistency."""

    def test_fresh_hours_aligned_with_redis_ttl(self):
        """AC9: L1 and L2 should have same TTL (4h)."""
        from search_cache import CACHE_FRESH_HOURS, REDIS_CACHE_TTL_SECONDS
        # CACHE_FRESH_HOURS in hours, REDIS_CACHE_TTL_SECONDS in seconds
        assert CACHE_FRESH_HOURS * 3600 == REDIS_CACHE_TTL_SECONDS

    def test_stale_hours_greater_than_fresh(self):
        """AC10: SWR window is between FRESH and STALE."""
        assert CACHE_STALE_HOURS > CACHE_FRESH_HOURS

    def test_stale_hours_is_24(self):
        """AC11: Expired after 24h."""
        assert CACHE_STALE_HOURS == 24


# ============================================================================
# _format_cache_date_range helper
# ============================================================================


class TestFormatCacheDateRange:

    def test_iso_timestamp(self):
        result = _format_cache_date_range("2026-02-20T14:30:00+00:00")
        assert result == "2026-02-20"

    def test_none(self):
        assert _format_cache_date_range(None) is None

    def test_plain_date_string(self):
        result = _format_cache_date_range("2026-02-20")
        assert result == "2026-02-20"
