"""Tests for search_state_manager.py — state machine and transition logic.

Wave 0 Safety Net: Covers SearchStateMachine transitions, terminal states,
invalid transitions, helper methods, _estimate_progress, and registry.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.search_state import SearchState, validate_transition, TERMINAL_STATES
from search_state_manager import (
    SearchStateMachine,
    _estimate_progress,
    create_state_machine,
    get_state_machine,
    remove_state_machine,
    _active_machines,
)


# ──────────────────────────────────────────────────────────────────────
# validate_transition (model layer)
# ──────────────────────────────────────────────────────────────────────

class TestValidateTransition:
    """Tests for the state transition validator."""

    @pytest.mark.timeout(30)
    def test_none_to_created_valid(self):
        assert validate_transition(None, SearchState.CREATED) is True

    @pytest.mark.timeout(30)
    def test_none_to_fetching_invalid(self):
        assert validate_transition(None, SearchState.FETCHING) is False

    @pytest.mark.timeout(30)
    def test_created_to_validating(self):
        assert validate_transition(SearchState.CREATED, SearchState.VALIDATING) is True

    @pytest.mark.timeout(30)
    def test_created_to_failed(self):
        assert validate_transition(SearchState.CREATED, SearchState.FAILED) is True

    @pytest.mark.timeout(30)
    def test_created_to_completed_invalid(self):
        assert validate_transition(SearchState.CREATED, SearchState.COMPLETED) is False

    @pytest.mark.timeout(30)
    def test_validating_to_fetching(self):
        assert validate_transition(SearchState.VALIDATING, SearchState.FETCHING) is True

    @pytest.mark.timeout(30)
    def test_validating_to_rate_limited(self):
        assert validate_transition(SearchState.VALIDATING, SearchState.RATE_LIMITED) is True

    @pytest.mark.timeout(30)
    def test_fetching_to_timed_out(self):
        assert validate_transition(SearchState.FETCHING, SearchState.TIMED_OUT) is True

    @pytest.mark.timeout(30)
    def test_terminal_no_outgoing(self):
        for state in TERMINAL_STATES:
            assert validate_transition(state, SearchState.CREATED) is False

    @pytest.mark.timeout(30)
    def test_happy_path(self):
        """Full happy path: CREATED -> VALIDATING -> ... -> COMPLETED."""
        path = [
            SearchState.CREATED, SearchState.VALIDATING, SearchState.FETCHING,
            SearchState.FILTERING, SearchState.ENRICHING, SearchState.GENERATING,
            SearchState.PERSISTING, SearchState.COMPLETED,
        ]
        for i in range(len(path) - 1):
            assert validate_transition(path[i], path[i + 1]) is True


# ──────────────────────────────────────────────────────────────────────
# SearchStateMachine
# ──────────────────────────────────────────────────────────────────────

class TestSearchStateMachine:
    """Tests for the in-memory state machine."""

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    async def test_initial_transition(self, mock_update, mock_persist):
        sm = SearchStateMachine("search-1")
        assert sm.current_state is None
        result = await sm.transition_to(SearchState.CREATED)
        assert result is True
        assert sm.current_state == SearchState.CREATED

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    async def test_valid_transition_chain(self, mock_update, mock_persist):
        sm = SearchStateMachine("search-2")
        await sm.transition_to(SearchState.CREATED)
        result = await sm.transition_to(SearchState.VALIDATING)
        assert result is True
        assert sm.current_state == SearchState.VALIDATING

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    async def test_invalid_transition_rejected(self, mock_update, mock_persist):
        sm = SearchStateMachine("search-3")
        await sm.transition_to(SearchState.CREATED)
        result = await sm.transition_to(SearchState.COMPLETED)  # Invalid
        assert result is False
        assert sm.current_state == SearchState.CREATED  # Unchanged

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    async def test_is_terminal(self, mock_update, mock_persist):
        sm = SearchStateMachine("search-4")
        await sm.transition_to(SearchState.CREATED)
        assert sm.is_terminal is False
        await sm.transition_to(SearchState.FAILED)
        assert sm.is_terminal is True

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    async def test_fail_helper(self, mock_update, mock_persist):
        sm = SearchStateMachine("search-5")
        await sm.transition_to(SearchState.CREATED)
        result = await sm.fail("Something went wrong", "ERR_001")
        assert result is True
        assert sm.current_state == SearchState.FAILED

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    async def test_timeout_helper(self, mock_update, mock_persist):
        sm = SearchStateMachine("search-6")
        await sm.transition_to(SearchState.CREATED)
        await sm.transition_to(SearchState.VALIDATING)
        await sm.transition_to(SearchState.FETCHING)
        result = await sm.timeout(stage="fetch")
        assert result is True
        assert sm.current_state == SearchState.TIMED_OUT

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    async def test_rate_limited_helper(self, mock_update, mock_persist):
        sm = SearchStateMachine("search-7")
        await sm.transition_to(SearchState.CREATED)
        await sm.transition_to(SearchState.VALIDATING)
        result = await sm.rate_limited(retry_after=120)
        assert result is True
        assert sm.current_state == SearchState.RATE_LIMITED

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    async def test_transitions_recorded(self, mock_update, mock_persist):
        sm = SearchStateMachine("search-8")
        await sm.transition_to(SearchState.CREATED)
        await sm.transition_to(SearchState.VALIDATING)
        assert len(sm._transitions) == 2

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    async def test_user_id_stored(self, mock_update, mock_persist):
        sm = SearchStateMachine("search-9", user_id="user-abc")
        assert sm.user_id == "user-abc"


# ──────────────────────────────────────────────────────────────────────
# _estimate_progress
# ──────────────────────────────────────────────────────────────────────

class TestEstimateProgress:
    """Tests for progress estimation."""

    @pytest.mark.timeout(30)
    def test_created(self):
        assert _estimate_progress("created") == 0

    @pytest.mark.timeout(30)
    def test_completed(self):
        assert _estimate_progress("completed") == 100

    @pytest.mark.timeout(30)
    def test_failed(self):
        assert _estimate_progress("failed") == -1

    @pytest.mark.timeout(30)
    def test_fetching(self):
        assert _estimate_progress("fetching") == 30

    @pytest.mark.timeout(30)
    def test_unknown_state(self):
        assert _estimate_progress("unknown") == 0

    @pytest.mark.timeout(30)
    def test_none(self):
        assert _estimate_progress(None) == 0


# ──────────────────────────────────────────────────────────────────────
# Registry Functions
# ──────────────────────────────────────────────────────────────────────

class TestRegistry:
    """Tests for state machine registry."""

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    async def test_create_and_get(self, mock_update, mock_persist):
        sm = await create_state_machine("reg-test-1")
        assert sm.current_state == SearchState.CREATED
        retrieved = get_state_machine("reg-test-1")
        assert retrieved is sm
        # Cleanup
        remove_state_machine("reg-test-1")

    @pytest.mark.timeout(30)
    def test_get_nonexistent(self):
        result = get_state_machine("nonexistent-id")
        assert result is None

    @pytest.mark.timeout(30)
    def test_remove(self):
        _active_machines["remove-test"] = MagicMock()
        remove_state_machine("remove-test")
        assert "remove-test" not in _active_machines

    @pytest.mark.timeout(30)
    def test_remove_nonexistent_safe(self):
        """Removing nonexistent key should not raise."""
        remove_state_machine("does-not-exist")


# ──────────────────────────────────────────────────────────────────────
# Additional validate_transition edge cases
# ──────────────────────────────────────────────────────────────────────

class TestValidateTransitionExtended:
    """Extended transition validation tests."""

    @pytest.mark.timeout(30)
    def test_all_states_can_reach_failed(self):
        """Every non-terminal state can transition to FAILED."""
        non_terminal = [s for s in SearchState if s not in TERMINAL_STATES]
        for state in non_terminal:
            assert validate_transition(state, SearchState.FAILED), \
                f"{state.value} should be able to transition to FAILED"

    @pytest.mark.timeout(30)
    def test_terminal_states_have_no_outgoing(self):
        """Terminal states cannot transition anywhere."""
        for state in TERMINAL_STATES:
            for target in SearchState:
                assert not validate_transition(state, target), \
                    f"Terminal state {state.value} should not transition to {target.value}"

    @pytest.mark.timeout(30)
    def test_fetching_to_timed_out(self):
        assert validate_transition(SearchState.FETCHING, SearchState.TIMED_OUT)

    @pytest.mark.timeout(30)
    def test_filtering_cannot_timeout(self):
        """Only FETCHING can transition to TIMED_OUT."""
        assert not validate_transition(SearchState.FILTERING, SearchState.TIMED_OUT)

    @pytest.mark.timeout(30)
    def test_enriching_to_generating(self):
        assert validate_transition(SearchState.ENRICHING, SearchState.GENERATING)

    @pytest.mark.timeout(30)
    def test_generating_to_persisting(self):
        assert validate_transition(SearchState.GENERATING, SearchState.PERSISTING)

    @pytest.mark.timeout(30)
    def test_persisting_to_completed(self):
        assert validate_transition(SearchState.PERSISTING, SearchState.COMPLETED)


# ──────────────────────────────────────────────────────────────────────
# SearchStateMachine edge cases
# ──────────────────────────────────────────────────────────────────────

class TestSearchStateMachineExtended:
    """Extended state machine tests."""

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    async def test_double_fail_rejected(self, mock_persist, mock_update):
        """Cannot fail twice from terminal state."""
        sm = SearchStateMachine("double-fail")
        await sm.transition_to(SearchState.CREATED)
        await sm.fail("first error")
        assert sm.current_state == SearchState.FAILED
        result = await sm.fail("second error")
        assert result is False

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    async def test_full_happy_path(self, mock_persist, mock_update):
        """Full pipeline: CREATED -> VALIDATING -> ... -> COMPLETED."""
        sm = SearchStateMachine("full-path")
        states = [
            SearchState.CREATED,
            SearchState.VALIDATING,
            SearchState.FETCHING,
            SearchState.FILTERING,
            SearchState.ENRICHING,
            SearchState.GENERATING,
            SearchState.PERSISTING,
            SearchState.COMPLETED,
        ]
        for s in states:
            result = await sm.transition_to(s)
            assert result is True, f"Failed to transition to {s.value}"
        assert sm.is_terminal
        assert sm.current_state == SearchState.COMPLETED

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    async def test_skip_state_rejected(self, mock_persist, mock_update):
        """Cannot skip states (e.g., CREATED -> FILTERING)."""
        sm = SearchStateMachine("skip")
        await sm.transition_to(SearchState.CREATED)
        result = await sm.transition_to(SearchState.FILTERING)
        assert result is False
        assert sm.current_state == SearchState.CREATED

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    async def test_transition_details_stored(self, mock_persist, mock_update):
        """Transition details are stored in the transition list."""
        sm = SearchStateMachine("details-test")
        await sm.transition_to(SearchState.CREATED, stage="init", details={"key": "value"})
        assert len(sm._transitions) == 1
        assert sm._transitions[0].details == {"key": "value"}
        assert sm._transitions[0].stage == "init"

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    async def test_timeout_from_fetching(self, mock_persist, mock_update):
        sm = SearchStateMachine("timeout-test")
        await sm.transition_to(SearchState.CREATED)
        await sm.transition_to(SearchState.VALIDATING)
        await sm.transition_to(SearchState.FETCHING)
        result = await sm.timeout(stage="fetch")
        assert result is True
        assert sm.current_state == SearchState.TIMED_OUT
        assert sm.is_terminal

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    @patch("search_state_manager._update_session_state", new_callable=AsyncMock)
    @patch("search_state_manager._persist_transition", new_callable=AsyncMock)
    async def test_rate_limited_from_validating(self, mock_persist, mock_update):
        sm = SearchStateMachine("rl-test")
        await sm.transition_to(SearchState.CREATED)
        await sm.transition_to(SearchState.VALIDATING)
        result = await sm.rate_limited(retry_after=120)
        assert result is True
        assert sm.current_state == SearchState.RATE_LIMITED


# ──────────────────────────────────────────────────────────────────────
# _estimate_progress extended
# ──────────────────────────────────────────────────────────────────────

class TestEstimateProgressExtended:
    """Additional progress estimation tests."""

    @pytest.mark.timeout(30)
    def test_enriching_70(self):
        assert _estimate_progress("enriching") == 70

    @pytest.mark.timeout(30)
    def test_generating_85(self):
        assert _estimate_progress("generating") == 85

    @pytest.mark.timeout(30)
    def test_persisting_95(self):
        assert _estimate_progress("persisting") == 95

    @pytest.mark.timeout(30)
    def test_rate_limited_negative(self):
        assert _estimate_progress("rate_limited") == -1

    @pytest.mark.timeout(30)
    def test_timed_out_negative(self):
        assert _estimate_progress("timed_out") == -1

    @pytest.mark.timeout(30)
    def test_validating_5(self):
        assert _estimate_progress("validating") == 5
