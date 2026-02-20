"""CRIT-003: Tests for SearchState enum, transition validator, and state manager.

Tests cover:
- State machine valid/invalid transitions (AC1, AC3)
- Terminal state detection
- Stage-to-state mapping
- State metadata (AC4)
- State duration metrics (AC22)
- Tracker TTL >= FETCH_TIMEOUT (AC14)
- Progress estimation
- Startup recovery logic (AC16-AC18)
"""

import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from models.search_state import (
    SearchState,
    VALID_TRANSITIONS,
    TERMINAL_STATES,
    STAGE_TO_STATE,
    StateTransition,
    validate_transition,
    is_terminal,
)
from search_state_manager import (
    SearchStateMachine,
    _estimate_progress,
    _persist_transition,
    _update_session_state,
    recover_stale_searches,
    create_state_machine,
    get_state_machine,
    remove_state_machine,
    _active_machines,
)


# ============================================================================
# SearchState Enum Tests
# ============================================================================

class TestSearchStateEnum:
    """AC1: SearchState enum has correct values."""

    def test_all_states_defined(self):
        expected = {
            "created", "validating", "fetching", "filtering",
            "enriching", "generating", "persisting", "completed",
            "failed", "rate_limited", "timed_out",
        }
        actual = {s.value for s in SearchState}
        assert actual == expected

    def test_states_are_strings(self):
        for state in SearchState:
            assert isinstance(state.value, str)


# ============================================================================
# Transition Validation Tests (AC1, AC3)
# ============================================================================

class TestTransitionValidation:
    """AC1: Only valid transitions are allowed. AC3: Invalid ones log CRITICAL."""

    def test_valid_happy_path(self):
        """Full pipeline: CREATED -> ... -> COMPLETED."""
        path = [
            (None, SearchState.CREATED),
            (SearchState.CREATED, SearchState.VALIDATING),
            (SearchState.VALIDATING, SearchState.FETCHING),
            (SearchState.FETCHING, SearchState.FILTERING),
            (SearchState.FILTERING, SearchState.ENRICHING),
            (SearchState.ENRICHING, SearchState.GENERATING),
            (SearchState.GENERATING, SearchState.PERSISTING),
            (SearchState.PERSISTING, SearchState.COMPLETED),
        ]
        for from_state, to_state in path:
            assert validate_transition(from_state, to_state) is True

    def test_valid_failure_from_any_processing_state(self):
        """Every processing state can transition to FAILED."""
        processing_states = [
            SearchState.CREATED, SearchState.VALIDATING, SearchState.FETCHING,
            SearchState.FILTERING, SearchState.ENRICHING,
            SearchState.GENERATING, SearchState.PERSISTING,
        ]
        for state in processing_states:
            assert validate_transition(state, SearchState.FAILED) is True

    def test_valid_rate_limited_from_validating(self):
        assert validate_transition(SearchState.VALIDATING, SearchState.RATE_LIMITED) is True

    def test_valid_timed_out_from_fetching(self):
        assert validate_transition(SearchState.FETCHING, SearchState.TIMED_OUT) is True

    def test_invalid_backward_transition(self):
        """AC3: COMPLETED -> FETCHING is invalid."""
        assert validate_transition(SearchState.COMPLETED, SearchState.FETCHING) is False

    def test_invalid_skip_state(self):
        """Can't skip from CREATED directly to FILTERING."""
        assert validate_transition(SearchState.CREATED, SearchState.FILTERING) is False

    def test_invalid_initial_state(self):
        """Must start with CREATED."""
        assert validate_transition(None, SearchState.FETCHING) is False

    def test_terminal_states_have_no_outgoing(self):
        """Terminal states cannot transition anywhere."""
        for state in TERMINAL_STATES:
            for target in SearchState:
                assert validate_transition(state, target) is False

    def test_invalid_transition_logs_critical(self):
        with patch("models.search_state.logger") as mock_logger:
            validate_transition(SearchState.COMPLETED, SearchState.FETCHING)
            mock_logger.critical.assert_called_once()
            assert "Invalid state transition" in mock_logger.critical.call_args[0][0]


# ============================================================================
# Terminal State Tests
# ============================================================================

class TestTerminalStates:
    def test_terminal_set(self):
        assert TERMINAL_STATES == {
            SearchState.COMPLETED, SearchState.FAILED,
            SearchState.RATE_LIMITED, SearchState.TIMED_OUT,
        }

    def test_is_terminal(self):
        assert is_terminal(SearchState.COMPLETED) is True
        assert is_terminal(SearchState.FAILED) is True
        assert is_terminal(SearchState.FETCHING) is False
        assert is_terminal(SearchState.CREATED) is False


# ============================================================================
# Stage-to-State Mapping Tests
# ============================================================================

class TestStageToState:
    def test_validate_maps_to_validating(self):
        assert STAGE_TO_STATE["validate"] == SearchState.VALIDATING

    def test_execute_maps_to_fetching(self):
        assert STAGE_TO_STATE["execute"] == SearchState.FETCHING

    def test_filter_maps_to_filtering(self):
        assert STAGE_TO_STATE["filter"] == SearchState.FILTERING

    def test_all_pipeline_stages_mapped(self):
        required_stages = {"validate", "prepare", "execute", "fetch", "filter", "enrich", "generate", "persist"}
        assert required_stages == set(STAGE_TO_STATE.keys())


# ============================================================================
# StateTransition Dataclass Tests (AC4)
# ============================================================================

class TestStateTransition:
    def test_carries_metadata(self):
        t = StateTransition(
            search_id="test-123",
            from_state=SearchState.FETCHING,
            to_state=SearchState.FILTERING,
            stage="filter",
            details={"items_count": 500},
            duration_since_previous=1234.5,
        )
        assert t.search_id == "test-123"
        assert t.from_state == SearchState.FETCHING
        assert t.to_state == SearchState.FILTERING
        assert t.details["items_count"] == 500
        assert t.duration_since_previous == 1234.5
        assert t.timestamp > 0


# ============================================================================
# SearchStateMachine Tests
# ============================================================================

class TestSearchStateMachine:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        _active_machines.clear()
        yield
        _active_machines.clear()

    @pytest.mark.asyncio
    async def test_valid_transition_succeeds(self):
        sm = SearchStateMachine("test-sm-1")
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                result = await sm.transition_to(SearchState.CREATED, stage="init")
                assert result is True
                assert sm.current_state == SearchState.CREATED

    @pytest.mark.asyncio
    async def test_invalid_transition_fails(self):
        sm = SearchStateMachine("test-sm-2")
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                await sm.transition_to(SearchState.CREATED, stage="init")
                # Skip directly to FILTERING (invalid)
                result = await sm.transition_to(SearchState.FILTERING, stage="filter")
                assert result is False
                assert sm.current_state == SearchState.CREATED

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        sm = SearchStateMachine("test-sm-3")
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                await sm.transition_to(SearchState.CREATED, stage="init")
                await sm.transition_to(SearchState.VALIDATING, stage="validate")
                await sm.transition_to(SearchState.FETCHING, stage="execute")
                await sm.transition_to(SearchState.FILTERING, stage="filter")
                await sm.transition_to(SearchState.ENRICHING, stage="enrich")
                await sm.transition_to(SearchState.GENERATING, stage="generate")
                await sm.transition_to(SearchState.PERSISTING, stage="persist")
                await sm.transition_to(SearchState.COMPLETED, stage="persist")

                assert sm.current_state == SearchState.COMPLETED
                assert sm.is_terminal is True
                assert len(sm._transitions) == 8

    @pytest.mark.asyncio
    async def test_fail_helper(self):
        sm = SearchStateMachine("test-sm-4")
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                await sm.transition_to(SearchState.CREATED, stage="init")
                await sm.transition_to(SearchState.VALIDATING, stage="validate")
                result = await sm.fail("API error", error_code="sources_unavailable", stage="validate")
                assert result is True
                assert sm.current_state == SearchState.FAILED

    @pytest.mark.asyncio
    async def test_timeout_helper(self):
        sm = SearchStateMachine("test-sm-5")
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                await sm.transition_to(SearchState.CREATED, stage="init")
                await sm.transition_to(SearchState.VALIDATING, stage="validate")
                await sm.transition_to(SearchState.FETCHING, stage="execute")
                result = await sm.timeout(stage="execute")
                assert result is True
                assert sm.current_state == SearchState.TIMED_OUT

    @pytest.mark.asyncio
    async def test_rate_limited_helper(self):
        sm = SearchStateMachine("test-sm-6")
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                await sm.transition_to(SearchState.CREATED, stage="init")
                await sm.transition_to(SearchState.VALIDATING, stage="validate")
                result = await sm.rate_limited(retry_after=120)
                assert result is True
                assert sm.current_state == SearchState.RATE_LIMITED


# ============================================================================
# Registry Tests
# ============================================================================

class TestStateMachineRegistry:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        _active_machines.clear()
        yield
        _active_machines.clear()

    @pytest.mark.asyncio
    async def test_create_and_get(self):
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                sm = await create_state_machine("reg-1")
                assert sm.current_state == SearchState.CREATED
                assert get_state_machine("reg-1") is sm

    def test_get_nonexistent(self):
        assert get_state_machine("nonexistent") is None

    @pytest.mark.asyncio
    async def test_remove(self):
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                await create_state_machine("reg-2")
                remove_state_machine("reg-2")
                assert get_state_machine("reg-2") is None


# ============================================================================
# Progress Estimation Tests
# ============================================================================

class TestProgressEstimation:
    def test_created(self):
        assert _estimate_progress("created") == 0

    def test_fetching(self):
        assert _estimate_progress("fetching") == 30

    def test_completed(self):
        assert _estimate_progress("completed") == 100

    def test_failed(self):
        assert _estimate_progress("failed") == -1

    def test_unknown(self):
        assert _estimate_progress("unknown") == 0

    def test_none(self):
        assert _estimate_progress(None) == 0


# ============================================================================
# Tracker TTL Tests (AC14)
# ============================================================================

class TestTrackerTTL:
    def test_tracker_ttl_gte_fetch_timeout(self):
        """AC14: _TRACKER_TTL must be >= FETCH_TIMEOUT (360s) + margin."""
        from progress import _TRACKER_TTL
        FETCH_TIMEOUT = 360  # from config
        assert _TRACKER_TTL >= FETCH_TIMEOUT, (
            f"Tracker TTL ({_TRACKER_TTL}s) must be >= FETCH_TIMEOUT ({FETCH_TIMEOUT}s)"
        )
        assert _TRACKER_TTL >= 420, f"Expected TTL >= 420, got {_TRACKER_TTL}"


# ============================================================================
# State Duration Metrics Tests (AC22)
# ============================================================================

class TestStateDurationMetrics:
    @pytest.mark.asyncio
    async def test_transition_records_duration(self):
        """AC22: State duration is recorded in Prometheus histogram."""
        sm = SearchStateMachine("metric-test")
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                with patch("metrics.STATE_DURATION") as mock_histogram:
                    mock_labeled = MagicMock()
                    mock_histogram.labels.return_value = mock_labeled

                    await sm.transition_to(SearchState.CREATED, stage="init")
                    await sm.transition_to(SearchState.VALIDATING, stage="validate")

                    # Should have recorded duration of CREATED state
                    mock_histogram.labels.assert_called_with(state="created")
                    mock_labeled.observe.assert_called_once()


# ============================================================================
# Startup Recovery Tests (AC16-AC18)
# ============================================================================

class TestStartupRecovery:
    @pytest.mark.asyncio
    async def test_old_searches_marked_timed_out(self):
        """AC17: Searches > 10 min old marked as timed_out."""
        from datetime import datetime, timezone, timedelta

        old_time = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        mock_sessions = [
            {"id": "sess-1", "search_id": "search-old", "status": "processing", "started_at": old_time}
        ]

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=mock_sessions)
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
                count = await recover_stale_searches(max_age_minutes=10)
                assert count == 1

                # Verify timed_out status was set
                update_call = mock_sb.table.return_value.update.call_args
                assert update_call[0][0]["status"] == "timed_out"
                assert "Server restart" in update_call[0][0]["error_message"]

    @pytest.mark.asyncio
    async def test_recent_searches_marked_failed(self):
        """AC18: Searches < 10 min old marked as failed with retry."""
        from datetime import datetime, timezone, timedelta

        recent_time = (datetime.now(timezone.utc) - timedelta(minutes=3)).isoformat()
        mock_sessions = [
            {"id": "sess-2", "search_id": "search-recent", "status": "processing", "started_at": recent_time}
        ]

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=mock_sessions)
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
                count = await recover_stale_searches(max_age_minutes=10)
                assert count == 1

                update_call = mock_sb.table.return_value.update.call_args
                assert update_call[0][0]["status"] == "failed"
                assert "retry" in update_call[0][0]["error_message"].lower()

    @pytest.mark.asyncio
    async def test_no_stale_searches(self):
        """No-op when no in-flight sessions."""
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[])

        with patch("supabase_client.get_supabase", return_value=mock_sb):
            count = await recover_stale_searches()
            assert count == 0

    @pytest.mark.asyncio
    async def test_recovery_handles_db_error(self):
        """Recovery never crashes — returns 0 on error."""
        with patch("supabase_client.get_supabase", side_effect=Exception("DB down")):
            count = await recover_stale_searches()
            assert count == 0


# ============================================================================
# Concurrent Searches Independence Test
# ============================================================================

class TestConcurrentSearches:
    @pytest.fixture(autouse=True)
    def cleanup(self):
        _active_machines.clear()
        yield
        _active_machines.clear()

    @pytest.mark.asyncio
    async def test_independent_state(self):
        """Two searches maintain independent state."""
        with patch("search_state_manager._persist_transition", new_callable=AsyncMock):
            with patch("search_state_manager._update_session_state", new_callable=AsyncMock):
                sm1 = await create_state_machine("concurrent-1")
                sm2 = await create_state_machine("concurrent-2")

                await sm1.transition_to(SearchState.VALIDATING, stage="validate")
                await sm1.transition_to(SearchState.FETCHING, stage="execute")

                await sm2.transition_to(SearchState.VALIDATING, stage="validate")

                assert sm1.current_state == SearchState.FETCHING
                assert sm2.current_state == SearchState.VALIDATING

                await sm1.fail("error1")
                assert sm1.is_terminal is True
                assert sm2.is_terminal is False
