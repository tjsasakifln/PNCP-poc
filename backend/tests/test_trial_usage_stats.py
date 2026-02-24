"""
STORY-266 AC17: Tests for get_trial_usage_stats() function.

Validates:
- Stats collection from multiple tables (monthly_quota, search_sessions, user_pipeline)
- Correct aggregation of opportunities, value, sectors
- Graceful handling of missing data and errors
- AC20: Zero-usage user returns all-zero stats
"""

import pytest
from unittest.mock import patch, MagicMock

from services.trial_stats import get_trial_usage_stats, TrialUsageStats


class TestTrialUsageStatsModel:
    """AC6: TrialUsageStats Pydantic model tests."""

    def test_default_values(self):
        stats = TrialUsageStats()
        assert stats.searches_count == 0
        assert stats.opportunities_found == 0
        assert stats.total_value_estimated == 0.0
        assert stats.pipeline_items_count == 0
        assert stats.sectors_searched == []

    def test_with_values(self):
        stats = TrialUsageStats(
            searches_count=10,
            opportunities_found=42,
            total_value_estimated=1_500_000.0,
            pipeline_items_count=5,
            sectors_searched=["vestuario", "alimentos"],
        )
        assert stats.searches_count == 10
        assert stats.total_value_estimated == 1_500_000.0

    def test_model_dump(self):
        stats = TrialUsageStats(
            searches_count=3,
            opportunities_found=15,
            total_value_estimated=750_000.0,
        )
        d = stats.model_dump()
        assert d["searches_count"] == 3
        assert d["opportunities_found"] == 15
        assert isinstance(d["sectors_searched"], list)


class TestGetTrialUsageStats:
    """AC17: Tests for get_trial_usage_stats() function."""

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used", return_value=7)
    def test_full_stats_collection(self, mock_quota, mock_get_sb):
        """Collects data from all three tables correctly."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        # Mock search_sessions query
        sessions_chain = MagicMock()
        sessions_chain.select.return_value = sessions_chain
        sessions_chain.eq.return_value = sessions_chain
        sessions_chain.execute.return_value = MagicMock(data=[
            {"total_filtered": 20, "valor_total": 500_000, "sectors": ["vestuario"]},
            {"total_filtered": 15, "valor_total": 300_000, "sectors": ["alimentos", "vestuario"]},
        ])

        # Mock user_pipeline count
        pipeline_chain = MagicMock()
        pipeline_chain.select.return_value = pipeline_chain
        pipeline_chain.eq.return_value = pipeline_chain
        pipeline_chain.execute.return_value = MagicMock(count=3, data=[])

        def table_side_effect(name):
            if name == "search_sessions":
                return sessions_chain
            elif name == "user_pipeline":
                return pipeline_chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        stats = get_trial_usage_stats("user-abc-123")

        assert stats.searches_count == 7
        assert stats.opportunities_found == 35  # 20 + 15
        assert stats.total_value_estimated == 800_000.0  # 500k + 300k
        assert stats.pipeline_items_count == 3
        assert set(stats.sectors_searched) == {"alimentos", "vestuario"}

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used", return_value=0)
    def test_zero_usage_returns_zeros(self, mock_quota, mock_get_sb):
        """AC20: User who hasn't done any searches gets all-zero stats."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        # Empty results from all tables
        empty_chain = MagicMock()
        empty_chain.select.return_value = empty_chain
        empty_chain.eq.return_value = empty_chain
        empty_chain.execute.return_value = MagicMock(data=[], count=0)

        mock_sb.table.return_value = empty_chain

        stats = get_trial_usage_stats("new-user-no-searches")

        assert stats.searches_count == 0
        assert stats.opportunities_found == 0
        assert stats.total_value_estimated == 0.0
        assert stats.pipeline_items_count == 0
        assert stats.sectors_searched == []

    @patch("supabase_client.get_supabase")
    def test_supabase_error_returns_defaults(self, mock_get_sb):
        """Gracefully handles Supabase errors without crashing."""
        mock_get_sb.side_effect = Exception("Connection refused")

        stats = get_trial_usage_stats("user-error")

        assert isinstance(stats, TrialUsageStats)
        assert stats.searches_count == 0
        assert stats.opportunities_found == 0

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used", side_effect=Exception("quota error"))
    def test_partial_failure_still_returns(self, mock_quota, mock_get_sb):
        """If one table fails, other stats still collected."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        # Sessions succeed
        sessions_chain = MagicMock()
        sessions_chain.select.return_value = sessions_chain
        sessions_chain.eq.return_value = sessions_chain
        sessions_chain.execute.return_value = MagicMock(data=[
            {"total_filtered": 10, "valor_total": 200_000, "sectors": ["software"]},
        ])

        # Pipeline fails
        pipeline_chain = MagicMock()
        pipeline_chain.select.return_value = pipeline_chain
        pipeline_chain.eq.return_value = pipeline_chain
        pipeline_chain.execute.side_effect = Exception("pipeline table error")

        def table_side_effect(name):
            if name == "search_sessions":
                return sessions_chain
            elif name == "user_pipeline":
                return pipeline_chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        stats = get_trial_usage_stats("user-partial")

        # Quota failed = 0, sessions succeeded, pipeline failed = 0
        assert stats.searches_count == 0
        assert stats.opportunities_found == 10
        assert stats.total_value_estimated == 200_000.0
        assert stats.pipeline_items_count == 0

    @patch("supabase_client.get_supabase")
    @patch("quota.get_monthly_quota_used", return_value=5)
    def test_null_values_in_sessions(self, mock_quota, mock_get_sb):
        """Handles None values in session records gracefully."""
        mock_sb = MagicMock()
        mock_get_sb.return_value = mock_sb

        sessions_chain = MagicMock()
        sessions_chain.select.return_value = sessions_chain
        sessions_chain.eq.return_value = sessions_chain
        sessions_chain.execute.return_value = MagicMock(data=[
            {"total_filtered": None, "valor_total": None, "sectors": None},
            {"total_filtered": 5, "valor_total": 100_000, "sectors": ["saude"]},
        ])

        pipeline_chain = MagicMock()
        pipeline_chain.select.return_value = pipeline_chain
        pipeline_chain.eq.return_value = pipeline_chain
        pipeline_chain.execute.return_value = MagicMock(count=0, data=[])

        def table_side_effect(name):
            if name == "search_sessions":
                return sessions_chain
            elif name == "user_pipeline":
                return pipeline_chain
            return MagicMock()

        mock_sb.table.side_effect = table_side_effect

        stats = get_trial_usage_stats("user-nulls")

        assert stats.opportunities_found == 5  # 0 + 5
        assert stats.total_value_estimated == 100_000.0
        assert stats.sectors_searched == ["saude"]
