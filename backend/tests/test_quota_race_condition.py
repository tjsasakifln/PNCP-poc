"""Tests for quota race condition fix (Issue #189).

These tests verify that the quota check/increment operations are atomic
and prevent race conditions under concurrent access.

Test Categories:
1. Unit tests for atomic increment function
2. Concurrent access stress tests
3. Edge cases (limit boundary, concurrent first access)

For full race condition testing, run with:
    pytest tests/test_quota_race_condition.py -v -s

For stress testing with more concurrency:
    pytest tests/test_quota_race_condition.py::TestQuotaConcurrency -v -s
"""

import asyncio
import pytest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone


class TestAtomicIncrementUnit:
    """Unit tests for increment_monthly_quota atomic operation."""

    def test_increment_calls_rpc_first(self):
        """Should attempt to use RPC function for atomic increment."""
        from quota import increment_monthly_quota

        mock_supabase = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"new_count": 5, "was_at_limit": False}]
        mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = increment_monthly_quota("user-123")

        # Verify RPC was called
        mock_supabase.rpc.assert_called_once()
        call_args = mock_supabase.rpc.call_args
        assert call_args[0][0] == "increment_quota_atomic"
        assert call_args[0][1]["p_user_id"] == "user-123"

        # Verify result
        assert result == 5

    def test_increment_falls_back_on_rpc_error(self):
        """Should fall back to upsert if RPC function doesn't exist."""
        from quota import increment_monthly_quota

        mock_supabase = Mock()

        # RPC fails (function doesn't exist)
        mock_supabase.rpc.return_value.execute.side_effect = Exception("function does not exist")

        # Fallback: get current count
        mock_select_result = Mock()
        mock_select_result.data = [{"searches_count": 10}]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_select_result
        mock_table.upsert.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = increment_monthly_quota("user-123")

        # Should have attempted upsert
        mock_table.upsert.assert_called_once()
        # Result should be refetched count
        assert result == 10  # Re-fetched after upsert

    def test_increment_with_max_quota_passes_to_rpc(self):
        """Should pass max_quota to RPC for limit enforcement."""
        from quota import increment_monthly_quota

        mock_supabase = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"new_count": 50, "was_at_limit": True}]
        mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = increment_monthly_quota("user-123", max_quota=50)

        # Verify max_quota was passed
        call_args = mock_supabase.rpc.call_args
        assert call_args[0][1]["p_max_quota"] == 50


class TestCheckAndIncrementAtomic:
    """Unit tests for check_and_increment_quota_atomic function."""

    def test_allowed_when_under_limit(self):
        """Should return allowed=True when under quota limit."""
        from quota import check_and_increment_quota_atomic

        mock_supabase = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{
            "allowed": True,
            "new_count": 25,
            "previous_count": 24,
            "quota_remaining": 25
        }]
        mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            allowed, new_count, remaining = check_and_increment_quota_atomic("user-123", max_quota=50)

        assert allowed is True
        assert new_count == 25
        assert remaining == 25

    def test_blocked_when_at_limit(self):
        """Should return allowed=False when at quota limit."""
        from quota import check_and_increment_quota_atomic

        mock_supabase = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{
            "allowed": False,
            "new_count": 50,
            "previous_count": 50,
            "quota_remaining": 0
        }]
        mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            allowed, new_count, remaining = check_and_increment_quota_atomic("user-123", max_quota=50)

        assert allowed is False
        assert new_count == 50
        assert remaining == 0

    def test_fallback_on_rpc_error(self):
        """Should fall back to non-atomic check on RPC error."""
        from quota import check_and_increment_quota_atomic

        mock_supabase = Mock()

        # RPC fails
        mock_supabase.rpc.return_value.execute.side_effect = Exception("RPC error")

        # Fallback: get current count (under limit)
        mock_select_result = Mock()
        mock_select_result.data = [{"searches_count": 10}]

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_select_result
        mock_table.upsert.return_value.execute.return_value = Mock()

        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            allowed, new_count, remaining = check_and_increment_quota_atomic("user-123", max_quota=50)

        # Should allow (was under limit) and increment
        assert allowed is True


class TestQuotaConcurrency:
    """Stress tests for concurrent quota access.

    These tests simulate race conditions by making multiple concurrent
    requests to increment quota. Without atomic operations, some increments
    would be lost.
    """

    @pytest.fixture
    def mock_db_state(self):
        """Simulate a mutable database state for testing."""
        return {"count": 0, "calls": 0}

    def test_concurrent_increments_no_lost_updates(self, mock_db_state):
        """Multiple concurrent increments should not lose any updates.

        This test simulates the race condition by:
        1. Having multiple threads read the "current" count
        2. Each thread increments and writes
        3. Without atomic ops, some increments are lost

        With atomic ops (via mock), all increments should be preserved.
        """
        from quota import increment_monthly_quota
        import threading

        num_threads = 10
        increments_per_thread = 5
        expected_total = num_threads * increments_per_thread

        # Lock for simulating atomic behavior in mock
        db_lock = threading.Lock()

        def mock_rpc(func_name, params):
            """Simulate atomic RPC behavior."""
            mock_result = Mock()
            if func_name == "increment_quota_atomic":
                with db_lock:
                    mock_db_state["count"] += 1
                    mock_db_state["calls"] += 1
                    mock_result.data = [{
                        "new_count": mock_db_state["count"],
                        "was_at_limit": False,
                        "previous_count": mock_db_state["count"] - 1
                    }]
            mock_execute = Mock()
            mock_execute.execute.return_value = mock_result
            return mock_execute

        mock_supabase = Mock()
        mock_supabase.rpc = mock_rpc

        def worker():
            """Worker that increments quota multiple times."""
            for _ in range(increments_per_thread):
                with patch("supabase_client.get_supabase", return_value=mock_supabase):
                    increment_monthly_quota("user-concurrent")

        # Run concurrent threads
        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All increments should be counted
        assert mock_db_state["count"] == expected_total
        assert mock_db_state["calls"] == expected_total

    def test_concurrent_check_and_increment_respects_limit(self, mock_db_state):
        """Concurrent requests should not exceed quota limit.

        This test verifies that even under heavy concurrent load,
        the quota limit is respected and no more than max_quota
        requests are allowed through.
        """
        from quota import check_and_increment_quota_atomic
        import threading

        max_quota = 10
        num_threads = 20  # More than quota limit
        mock_db_state["allowed_count"] = 0

        # Lock for simulating atomic behavior
        db_lock = threading.Lock()

        def mock_rpc(func_name, params):
            """Simulate atomic check-and-increment."""
            mock_result = Mock()
            if func_name == "check_and_increment_quota":
                max_q = params.get("p_max_quota", 999999)
                with db_lock:
                    if mock_db_state["count"] < max_q:
                        mock_db_state["count"] += 1
                        mock_db_state["allowed_count"] += 1
                        allowed = True
                    else:
                        allowed = False
                    mock_result.data = [{
                        "allowed": allowed,
                        "new_count": mock_db_state["count"],
                        "previous_count": mock_db_state["count"] - (1 if allowed else 0),
                        "quota_remaining": max(0, max_q - mock_db_state["count"])
                    }]
            mock_execute = Mock()
            mock_execute.execute.return_value = mock_result
            return mock_execute

        mock_supabase = Mock()
        mock_supabase.rpc = mock_rpc

        results = []
        results_lock = threading.Lock()

        def worker():
            """Worker that tries to increment quota."""
            with patch("supabase_client.get_supabase", return_value=mock_supabase):
                allowed, count, remaining = check_and_increment_quota_atomic(
                    "user-limit-test",
                    max_quota=max_quota
                )
                with results_lock:
                    results.append(allowed)

        # Run concurrent threads
        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly max_quota requests should be allowed
        allowed_count = sum(1 for r in results if r)
        assert allowed_count == max_quota
        assert mock_db_state["count"] == max_quota
        assert mock_db_state["allowed_count"] == max_quota

    def test_race_condition_window_eliminated(self):
        """Verify no race window between check and increment.

        The old code had a TOCTOU vulnerability:
        1. Thread A checks quota (count=49, limit=50) -> allowed
        2. Thread B checks quota (count=49, limit=50) -> allowed
        3. Thread A increments (count=50)
        4. Thread B increments (count=51) <- EXCEEDED LIMIT!

        With atomic check_and_increment, this cannot happen.
        """
        from quota import check_and_increment_quota_atomic
        import threading
        import time

        max_quota = 50
        starting_count = 49  # One away from limit
        state = {"count": starting_count, "increments": 0}
        db_lock = threading.Lock()
        barrier = threading.Barrier(2)  # Synchronize two threads

        def mock_rpc(func_name, params):
            mock_result = Mock()
            if func_name == "check_and_increment_quota":
                max_q = params.get("p_max_quota", 999999)
                # Atomic operation - lock is held for entire check+increment
                with db_lock:
                    if state["count"] < max_q:
                        state["count"] += 1
                        state["increments"] += 1
                        allowed = True
                    else:
                        allowed = False
                    mock_result.data = [{
                        "allowed": allowed,
                        "new_count": state["count"],
                        "quota_remaining": max(0, max_q - state["count"])
                    }]
            mock_execute = Mock()
            mock_execute.execute.return_value = mock_result
            return mock_execute

        mock_supabase = Mock()
        mock_supabase.rpc = mock_rpc

        results = []

        def worker(worker_id):
            # Wait for both threads to be ready
            barrier.wait()
            with patch("supabase_client.get_supabase", return_value=mock_supabase):
                allowed, count, _ = check_and_increment_quota_atomic(
                    "user-race",
                    max_quota=max_quota
                )
                results.append((worker_id, allowed, count))

        # Start two threads simultaneously
        t1 = threading.Thread(target=worker, args=(1,))
        t2 = threading.Thread(target=worker, args=(2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Only ONE thread should have been allowed (49 -> 50)
        allowed_results = [r for r in results if r[1]]
        assert len(allowed_results) == 1, f"Expected 1 allowed, got {len(allowed_results)}: {results}"

        # Final count should be exactly at limit
        assert state["count"] == max_quota


class TestQuotaEdgeCases:
    """Edge case tests for quota operations."""

    def test_first_access_concurrent(self):
        """Multiple concurrent first-time accesses should all be handled.

        When multiple requests hit for a user with no quota record,
        only one INSERT should succeed and others should update.
        """
        from quota import increment_monthly_quota
        import threading

        num_threads = 5
        state = {"count": 0, "inserts": 0, "updates": 0}
        db_lock = threading.Lock()

        def mock_rpc(func_name, params):
            mock_result = Mock()
            if func_name == "increment_quota_atomic":
                with db_lock:
                    # Simulate INSERT ON CONFLICT behavior
                    if state["count"] == 0:
                        state["inserts"] += 1
                    else:
                        state["updates"] += 1
                    state["count"] += 1
                    mock_result.data = [{
                        "new_count": state["count"],
                        "was_at_limit": False
                    }]
            mock_execute = Mock()
            mock_execute.execute.return_value = mock_result
            return mock_execute

        mock_supabase = Mock()
        mock_supabase.rpc = mock_rpc

        barrier = threading.Barrier(num_threads)
        results = []

        def worker():
            barrier.wait()  # Synchronize all threads
            with patch("supabase_client.get_supabase", return_value=mock_supabase):
                result = increment_monthly_quota("new-user")
                results.append(result)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All increments should be counted
        assert state["count"] == num_threads
        # Results should be sequential (1, 2, 3, 4, 5) though order may vary
        assert sorted(results) == list(range(1, num_threads + 1))

    def test_quota_at_boundary(self):
        """Test behavior when quota is exactly at limit."""
        from quota import check_and_increment_quota_atomic

        mock_supabase = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{
            "allowed": False,
            "new_count": 50,
            "previous_count": 50,
            "quota_remaining": 0
        }]
        mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            allowed, count, remaining = check_and_increment_quota_atomic("user-at-limit", max_quota=50)

        assert allowed is False
        assert count == 50
        assert remaining == 0

    def test_handles_db_error_gracefully(self):
        """Should not crash on database errors."""
        from quota import increment_monthly_quota

        mock_supabase = Mock()
        mock_supabase.rpc.return_value.execute.side_effect = Exception("DB connection lost")

        mock_table = Mock()
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.side_effect = Exception("DB error")
        mock_table.upsert.return_value.execute.side_effect = Exception("DB error")
        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            # Should not raise, should return 0 as fallback
            result = increment_monthly_quota("user-db-error")

        assert result == 0  # Safe fallback


class TestBackwardCompatibility:
    """Ensure backward compatibility with existing code."""

    def test_increment_returns_int(self):
        """increment_monthly_quota should still return int."""
        from quota import increment_monthly_quota

        mock_supabase = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"new_count": 42, "was_at_limit": False}]
        mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = increment_monthly_quota("user-compat")

        assert isinstance(result, int)
        assert result == 42

    def test_increment_without_max_quota_still_works(self):
        """Calling without max_quota parameter should work (backward compat)."""
        from quota import increment_monthly_quota

        mock_supabase = Mock()
        mock_rpc_result = Mock()
        mock_rpc_result.data = [{"new_count": 1, "was_at_limit": False}]
        mock_supabase.rpc.return_value.execute.return_value = mock_rpc_result

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            # Call without max_quota (old signature)
            result = increment_monthly_quota("user-old-api")

        assert result == 1

        # Verify p_max_quota was passed as None
        call_args = mock_supabase.rpc.call_args
        assert call_args[0][1]["p_max_quota"] is None
