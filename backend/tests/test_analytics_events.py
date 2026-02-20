"""Tests for analytics_events module (GTM-RESILIENCE-B05 AC1/AC2)."""

import logging
from unittest.mock import patch, MagicMock

import pytest


class TestTrackEvent:
    """AC1: track_event() behavior with and without Mixpanel."""

    def setup_method(self):
        """Reset module state before each test."""
        import analytics_events
        analytics_events.reset_for_testing()

    def test_track_event_without_mixpanel_logs_debug(self, caplog):
        """Without MIXPANEL_TOKEN, events are logged via logger.debug()."""
        import analytics_events
        with caplog.at_level(logging.DEBUG, logger="analytics_events"):
            analytics_events.track_event("test_event", {"key": "value"})
        assert "analytics_event: test_event" in caplog.text

    def test_track_event_with_mixpanel_token_calls_sdk(self):
        """With MIXPANEL_TOKEN, events are sent via Mixpanel SDK."""
        import analytics_events
        analytics_events.reset_for_testing()

        mock_mp_class = MagicMock()
        mock_mp_instance = MagicMock()
        mock_mp_class.return_value = mock_mp_instance

        with patch.dict("os.environ", {"MIXPANEL_TOKEN": "test-token-123"}):
            with patch.dict("sys.modules", {"mixpanel": MagicMock(Mixpanel=mock_mp_class)}):
                analytics_events.track_event("cache_operation", {"hit": True, "user_id": "u1"})

        mock_mp_instance.track.assert_called_once_with("u1", "cache_operation", {"hit": True})

    def test_track_event_never_raises(self):
        """track_event must never raise, even on internal errors."""
        import analytics_events
        analytics_events.reset_for_testing()

        # Force Mixpanel init to raise
        with patch.dict("os.environ", {"MIXPANEL_TOKEN": "bad-token"}):
            with patch.dict("sys.modules", {"mixpanel": MagicMock(Mixpanel=MagicMock(side_effect=RuntimeError("boom")))}):
                # Should not raise
                analytics_events.track_event("crash_event", {"x": 1})

    def test_track_event_without_properties(self, caplog):
        """track_event works with None/empty properties."""
        import analytics_events
        with caplog.at_level(logging.DEBUG, logger="analytics_events"):
            analytics_events.track_event("simple_event")
        assert "simple_event" in caplog.text

    def test_track_event_user_id_extraction(self):
        """user_id is extracted from properties and used as distinct_id."""
        import analytics_events
        analytics_events.reset_for_testing()

        mock_mp_class = MagicMock()
        mock_mp_instance = MagicMock()
        mock_mp_class.return_value = mock_mp_instance

        with patch.dict("os.environ", {"MIXPANEL_TOKEN": "test-token"}):
            with patch.dict("sys.modules", {"mixpanel": MagicMock(Mixpanel=mock_mp_class)}):
                analytics_events.track_event("ev", {"user_id": "uid-42", "data": "x"})

        # user_id should be popped from props and used as distinct_id
        mock_mp_instance.track.assert_called_once()
        call_args = mock_mp_instance.track.call_args
        assert call_args[0][0] == "uid-42"
        assert "user_id" not in call_args[0][2]

    def test_track_event_default_distinct_id(self):
        """Without user_id in props, distinct_id defaults to 'system'."""
        import analytics_events
        analytics_events.reset_for_testing()

        mock_mp_class = MagicMock()
        mock_mp_instance = MagicMock()
        mock_mp_class.return_value = mock_mp_instance

        with patch.dict("os.environ", {"MIXPANEL_TOKEN": "test-token"}):
            with patch.dict("sys.modules", {"mixpanel": MagicMock(Mixpanel=mock_mp_class)}):
                analytics_events.track_event("ev", {"data": "y"})

        call_args = mock_mp_instance.track.call_args
        assert call_args[0][0] == "system"

    def test_mixpanel_import_error_fallback(self, caplog):
        """If mixpanel package not installed, falls back to logging."""
        import analytics_events
        analytics_events.reset_for_testing()
        import sys

        # Remove mixpanel from modules if present
        original = sys.modules.pop("mixpanel", None)
        try:
            with patch.dict("os.environ", {"MIXPANEL_TOKEN": "token-123"}):
                with patch("builtins.__import__", side_effect=lambda name, *a, **kw: (_ for _ in ()).throw(ImportError("no mixpanel")) if name == "mixpanel" else __builtins__.__import__(name, *a, **kw)):
                    analytics_events.reset_for_testing()
                    with caplog.at_level(logging.DEBUG, logger="analytics_events"):
                        analytics_events.track_event("fallback_test", {"k": "v"})
                    assert "analytics_event: fallback_test" in caplog.text
        finally:
            if original is not None:
                sys.modules["mixpanel"] = original

    def test_reset_for_testing(self):
        """reset_for_testing clears singleton state."""
        import analytics_events
        analytics_events._mixpanel_initialized = True
        analytics_events._mixpanel_client = "fake"
        analytics_events.reset_for_testing()
        assert analytics_events._mixpanel_initialized is False
        assert analytics_events._mixpanel_client is None


class TestCacheOperationTracking:
    """AC2: Existing cache operations reach analytics_events.track_event()."""

    def test_track_cache_operation_calls_analytics(self):
        """_track_cache_operation calls analytics_events.track_event."""
        from search_cache import _track_cache_operation, CacheLevel

        with patch("analytics_events.track_event") as mock_track:
            _track_cache_operation("read", True, CacheLevel.SUPABASE, 10, 150.0, 3600.0)

        mock_track.assert_called_once()
        args = mock_track.call_args
        assert args[0][0] == "cache_operation"
        assert args[0][1]["operation"] == "read"
        assert args[0][1]["hit"] is True
        assert args[0][1]["level"] == "supabase"

    def test_track_cache_operation_increments_counters(self):
        """_track_cache_operation increments hit/miss counters in cache."""
        from search_cache import _track_cache_operation, CacheLevel

        mock_cache = MagicMock()

        with patch("analytics_events.track_event"):
            with patch("redis_pool.get_fallback_cache", return_value=mock_cache):
                _track_cache_operation("read", True, CacheLevel.SUPABASE, 5, 100.0, 1000.0)

        mock_cache.incr.assert_called()
        incr_calls = [c[0][0] for c in mock_cache.incr.call_args_list]
        assert any("hits" in k for k in incr_calls)

    def test_track_cache_operation_miss_counter(self):
        """Cache misses increment the misses counter."""
        from search_cache import _track_cache_operation, CacheLevel

        mock_cache = MagicMock()

        with patch("analytics_events.track_event"):
            with patch("redis_pool.get_fallback_cache", return_value=mock_cache):
                _track_cache_operation("read", False, CacheLevel.MISS, 0, 50.0)

        incr_calls = [c[0][0] for c in mock_cache.incr.call_args_list]
        assert any("misses" in k for k in incr_calls)
