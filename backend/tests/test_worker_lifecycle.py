"""Tests for worker_lifecycle.py — timeout tracking and diagnostics.

Wave 0 Safety Net: Covers set_active_request, clear_active_request,
get_active_request, build_timeout_info, install_timeout_handler.
"""

import pytest
import time
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from worker_lifecycle import (
    set_active_request,
    clear_active_request,
    get_active_request,
    build_timeout_info,
    install_timeout_handler,
    _active_request,
)


@pytest.fixture(autouse=True)
def _cleanup_active_request():
    """Ensure active request is cleared between tests."""
    clear_active_request()
    yield
    clear_active_request()


# ──────────────────────────────────────────────────────────────────────
# set_active_request / get_active_request / clear_active_request
# ──────────────────────────────────────────────────────────────────────

class TestActiveRequestTracking:
    """Tests for request tracking functions."""

    @pytest.mark.timeout(30)
    def test_set_and_get(self):
        set_active_request("/v1/buscar", "search-abc")
        info = get_active_request()
        assert info["endpoint"] == "/v1/buscar"
        assert info["search_id"] == "search-abc"
        assert "start_time" in info
        assert "pid" in info

    @pytest.mark.timeout(30)
    def test_clear(self):
        set_active_request("/test", "123")
        clear_active_request()
        info = get_active_request()
        assert info == {}

    @pytest.mark.timeout(30)
    def test_no_search_id_defaults_to_dash(self):
        set_active_request("/health")
        info = get_active_request()
        assert info["search_id"] == "-"

    @pytest.mark.timeout(30)
    def test_get_returns_copy(self):
        set_active_request("/test", "abc")
        info = get_active_request()
        info["endpoint"] = "modified"
        # Original should not be modified
        assert _active_request.get("endpoint") == "/test"


# ──────────────────────────────────────────────────────────────────────
# build_timeout_info
# ──────────────────────────────────────────────────────────────────────

class TestBuildTimeoutInfo:
    """Tests for timeout diagnostic data builder."""

    @pytest.mark.timeout(30)
    def test_with_active_request(self):
        set_active_request("/v1/buscar", "search-xyz")
        time.sleep(0.05)
        info = build_timeout_info(12345)
        assert info["worker_pid"] == 12345
        assert info["endpoint"] == "/v1/buscar"
        assert info["search_id"] == "search-xyz"
        assert info["request_duration_s"] >= 0

    @pytest.mark.timeout(30)
    def test_idle_worker(self):
        clear_active_request()
        info = build_timeout_info(99)
        assert info["worker_pid"] == 99
        assert info["endpoint"] == "idle"
        assert info["search_id"] == "-"
        assert info["request_duration_s"] == -1


# ──────────────────────────────────────────────────────────────────────
# install_timeout_handler
# ──────────────────────────────────────────────────────────────────────

class TestInstallTimeoutHandler:
    """Tests for SIGABRT handler installation."""

    @pytest.mark.timeout(30)
    def test_windows_skips_handler(self):
        """On Windows, handler installation is skipped gracefully."""
        if sys.platform == "win32":
            install_timeout_handler(1234)
            # Should not raise, just skip
        else:
            # On Unix, it would install the handler
            install_timeout_handler(1234)

    @pytest.mark.timeout(30)
    @patch("worker_lifecycle.sys")
    def test_windows_platform_check(self, mock_sys):
        mock_sys.platform = "win32"
        # Should return early without error
        install_timeout_handler(5678)


# ──────────────────────────────────────────────────────────────────────
# Additional edge-case coverage
# ──────────────────────────────────────────────────────────────────────

class TestActiveRequestOverwrite:
    """Tests for overwriting active request data."""

    @pytest.mark.timeout(30)
    def test_overwrite_endpoint(self):
        """Setting a new active request overwrites the previous one."""
        set_active_request("/first", "s1")
        set_active_request("/second", "s2")
        info = get_active_request()
        assert info["endpoint"] == "/second"
        assert info["search_id"] == "s2"

    @pytest.mark.timeout(30)
    def test_pid_is_current_process(self):
        set_active_request("/test")
        info = get_active_request()
        assert info["pid"] == os.getpid()

    @pytest.mark.timeout(30)
    def test_start_time_is_recent(self):
        before = time.time()
        set_active_request("/test")
        after = time.time()
        info = get_active_request()
        assert before <= info["start_time"] <= after

    @pytest.mark.timeout(30)
    def test_clear_is_idempotent(self):
        clear_active_request()
        clear_active_request()
        assert get_active_request() == {}

    @pytest.mark.timeout(30)
    def test_empty_endpoint(self):
        set_active_request("")
        info = get_active_request()
        assert info["endpoint"] == ""

    @pytest.mark.timeout(30)
    def test_none_search_id_becomes_dash(self):
        set_active_request("/x", None)
        assert get_active_request()["search_id"] == "-"


class TestBuildTimeoutInfoEdgeCases:
    """Additional edge cases for build_timeout_info."""

    @pytest.mark.timeout(30)
    def test_duration_increases_over_time(self):
        set_active_request("/slow", "slow-search")
        time.sleep(0.1)
        info1 = build_timeout_info(1)
        time.sleep(0.1)
        info2 = build_timeout_info(1)
        assert info2["request_duration_s"] > info1["request_duration_s"]

    @pytest.mark.timeout(30)
    def test_different_worker_pids(self):
        set_active_request("/test")
        info_a = build_timeout_info(100)
        info_b = build_timeout_info(200)
        assert info_a["worker_pid"] == 100
        assert info_b["worker_pid"] == 200

    @pytest.mark.timeout(30)
    def test_zero_pid(self):
        info = build_timeout_info(0)
        assert info["worker_pid"] == 0
