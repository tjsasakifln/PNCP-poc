"""Test suite for search session history (STORY-223 Track 3).

Tests cover:
- AC12: save_search_session() succeeds with valid data
- AC13: save_search_session() when profile doesn't exist (triggers _ensure_profile_exists)
- AC14: save_search_session() DB failure → error logged, search result still returned
- AC15: History saved for zero-result searches
- AC16: Retry (max 1) for transient DB errors on history save
"""

import logging
from unittest.mock import Mock, patch, call
import pytest

from quota import save_search_session


class TestSaveSearchSessionSuccess:
    """AC12: Test successful session save."""

    def test_save_session_returns_id_with_valid_data(self):
        """save_search_session() succeeds with valid data and returns session ID."""
        mock_supabase = Mock()

        # Mock profile check - profile exists
        profile_result = Mock()
        profile_result.data = [{"id": "user-123"}]

        # Mock insert result for sessions
        insert_result = Mock()
        insert_result.data = [{"id": "session-uuid-abc123"}]

        # Configure table mock
        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "profiles":
                mock_table.select.return_value.eq.return_value.execute.return_value = profile_result
            elif table_name == "search_sessions":
                mock_table.insert.return_value.execute.return_value = insert_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = save_search_session(
                user_id="user-123",
                sectors=["uniformes", "alimentacao"],
                ufs=["SP", "RJ"],
                data_inicial="2025-01-01",
                data_final="2025-01-31",
                custom_keywords=["jaleco", "avental"],
                total_raw=100,
                total_filtered=25,
                valor_total=1500000.50,
                resumo_executivo="Encontradas 25 oportunidades relevantes.",
                destaques=["SP: R$ 500k", "RJ: R$ 1M"],
            )

        assert result == "session-uuid-abc123"

    def test_save_session_with_none_optional_fields(self):
        """save_search_session() succeeds with None for optional fields."""
        mock_supabase = Mock()

        # Mock profile check - profile exists
        profile_result = Mock()
        profile_result.data = [{"id": "user-456"}]

        # Mock insert result
        insert_result = Mock()
        insert_result.data = [{"id": "session-minimal"}]

        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "profiles":
                mock_table.select.return_value.eq.return_value.execute.return_value = profile_result
            elif table_name == "search_sessions":
                mock_table.insert.return_value.execute.return_value = insert_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = save_search_session(
                user_id="user-456",
                sectors=["uniformes"],
                ufs=["MG"],
                data_inicial="2025-02-01",
                data_final="2025-02-28",
                custom_keywords=None,
                total_raw=50,
                total_filtered=10,
                valor_total=200000.0,
                resumo_executivo=None,
                destaques=None,
            )

        assert result == "session-minimal"

    def test_save_session_stores_all_fields_correctly(self):
        """save_search_session() saves all session fields to database."""
        mock_supabase = Mock()

        # Mock profile check
        profile_result = Mock()
        profile_result.data = [{"id": "user-789"}]

        # Mock insert
        insert_result = Mock()
        insert_result.data = [{"id": "session-fields"}]

        insert_mock = Mock(return_value=Mock(execute=Mock(return_value=insert_result)))

        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "profiles":
                mock_table.select.return_value.eq.return_value.execute.return_value = profile_result
            elif table_name == "search_sessions":
                mock_table.insert = insert_mock
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            save_search_session(
                user_id="user-789",
                sectors=["vestuario"],
                ufs=["BA", "CE"],
                data_inicial="2025-03-01",
                data_final="2025-03-31",
                custom_keywords=["uniforme", "fardamento"],
                total_raw=200,
                total_filtered=50,
                valor_total=3000000.75,
                resumo_executivo="Resumo executivo de teste.",
                destaques=["BA: R$ 1M", "CE: R$ 2M"],
            )

        # Verify all fields were passed to insert
        call_args = insert_mock.call_args[0][0]
        assert call_args["user_id"] == "user-789"
        assert call_args["sectors"] == ["vestuario"]
        assert call_args["ufs"] == ["BA", "CE"]
        assert call_args["data_inicial"] == "2025-03-01"
        assert call_args["data_final"] == "2025-03-31"
        assert call_args["custom_keywords"] == ["uniforme", "fardamento"]
        assert call_args["total_raw"] == 200
        assert call_args["total_filtered"] == 50
        assert call_args["valor_total"] == 3000000.75
        assert call_args["resumo_executivo"] == "Resumo executivo de teste."
        assert call_args["destaques"] == ["BA: R$ 1M", "CE: R$ 2M"]


class TestSaveSearchSessionProfileCreation:
    """AC13: Test session save when profile doesn't exist."""

    @patch("quota._ensure_profile_exists")
    def test_save_session_creates_profile_when_missing(self, mock_ensure_profile):
        """save_search_session() triggers _ensure_profile_exists when profile missing."""
        mock_supabase = Mock()

        # _ensure_profile_exists succeeds
        mock_ensure_profile.return_value = True

        # Mock successful insert after profile creation
        insert_result = Mock()
        insert_result.data = [{"id": "session-after-profile"}]

        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = insert_result
        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = save_search_session(
                user_id="new-user-999",
                sectors=["alimentacao"],
                ufs=["RS"],
                data_inicial="2025-04-01",
                data_final="2025-04-30",
                custom_keywords=None,
                total_raw=75,
                total_filtered=15,
                valor_total=500000.0,
                resumo_executivo="Teste profile creation.",
                destaques=["RS: 15 resultados"],
            )

        # Verify _ensure_profile_exists was called
        mock_ensure_profile.assert_called_once_with("new-user-999", mock_supabase)
        assert result == "session-after-profile"

    @patch("quota._ensure_profile_exists")
    def test_save_session_fails_gracefully_when_profile_creation_fails(self, mock_ensure_profile):
        """save_search_session() returns None when _ensure_profile_exists fails."""
        mock_supabase = Mock()

        # _ensure_profile_exists fails
        mock_ensure_profile.return_value = False

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = save_search_session(
                user_id="missing-user",
                sectors=["uniformes"],
                ufs=["SP"],
                data_inicial="2025-05-01",
                data_final="2025-05-31",
                custom_keywords=None,
                total_raw=10,
                total_filtered=2,
                valor_total=50000.0,
                resumo_executivo=None,
                destaques=None,
            )

        # Session save should fail gracefully
        assert result is None
        mock_ensure_profile.assert_called_once()


class TestSaveSearchSessionDBFailure:
    """AC14: Test graceful failure on DB errors."""

    @patch("quota._ensure_profile_exists")
    def test_save_session_returns_none_on_db_failure(self, mock_ensure_profile, caplog):
        """DB failure is logged but doesn't raise exception — returns None."""
        mock_supabase = Mock()

        # Profile exists
        mock_ensure_profile.return_value = True

        # Mock DB failure on insert (both attempts fail)
        mock_table = Mock()
        mock_table.insert.return_value.execute.side_effect = Exception("Database connection lost")
        mock_supabase.table.return_value = mock_table

        with caplog.at_level(logging.WARNING):
            with patch("supabase_client.get_supabase", return_value=mock_supabase):
                result = save_search_session(
                    user_id="user-db-fail",
                    sectors=["uniformes"],
                    ufs=["MG"],
                    data_inicial="2025-06-01",
                    data_final="2025-06-30",
                    custom_keywords=None,
                    total_raw=100,
                    total_filtered=25,
                    valor_total=1000000.0,
                    resumo_executivo="Test DB failure.",
                    destaques=[],
                )

        # Should return None (silent fail)
        assert result is None

        # Should log warning on first attempt and error on second
        assert any("Transient error saving session" in record.message for record in caplog.records)
        assert any("Failed to save search session after retry" in record.message for record in caplog.records)

    @patch("quota._ensure_profile_exists")
    def test_save_session_empty_result_returns_none(self, mock_ensure_profile, caplog):
        """Insert returning empty result is handled gracefully — returns None."""
        mock_supabase = Mock()

        # Profile exists
        mock_ensure_profile.return_value = True

        # Mock empty insert result (both attempts)
        insert_result = Mock()
        insert_result.data = []

        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = insert_result
        mock_supabase.table.return_value = mock_table

        with caplog.at_level(logging.ERROR):
            with patch("supabase_client.get_supabase", return_value=mock_supabase):
                result = save_search_session(
                    user_id="user-empty-result",
                    sectors=["alimentacao"],
                    ufs=["PR"],
                    data_inicial="2025-07-01",
                    data_final="2025-07-31",
                    custom_keywords=None,
                    total_raw=50,
                    total_filtered=10,
                    valor_total=250000.0,
                    resumo_executivo=None,
                    destaques=None,
                )

        # Should return None
        assert result is None

        # Should log error about empty result
        assert any("Insert returned empty result" in record.message for record in caplog.records)


class TestSaveSearchSessionZeroResults:
    """AC15: Test history saved for searches with zero results."""

    def test_save_session_with_zero_results(self):
        """History saved even for searches with zero results."""
        mock_supabase = Mock()

        # Mock profile check
        profile_result = Mock()
        profile_result.data = [{"id": "user-zero"}]

        # Mock successful insert
        insert_result = Mock()
        insert_result.data = [{"id": "session-zero-results"}]

        def table_side_effect(table_name):
            mock_table = Mock()
            if table_name == "profiles":
                mock_table.select.return_value.eq.return_value.execute.return_value = profile_result
            elif table_name == "search_sessions":
                mock_table.insert.return_value.execute.return_value = insert_result
            return mock_table

        mock_supabase.table.side_effect = table_side_effect

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            result = save_search_session(
                user_id="user-zero",
                sectors=["vestuario"],
                ufs=["AC"],
                data_inicial="2025-08-01",
                data_final="2025-08-31",
                custom_keywords=None,
                total_raw=0,
                total_filtered=0,
                valor_total=0.0,
                resumo_executivo="Nenhuma licitação encontrada.",
                destaques=[],
            )

        assert result == "session-zero-results"


class TestSaveSearchSessionRetryLogic:
    """AC16: Test retry logic for transient DB errors."""

    @patch("quota._ensure_profile_exists")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_save_session_succeeds_on_retry(self, mock_sleep, mock_ensure_profile, caplog):
        """Transient error on first attempt, success on retry."""
        mock_supabase = Mock()

        # Profile exists
        mock_ensure_profile.return_value = True

        # First insert fails, second succeeds
        insert_result_success = Mock()
        insert_result_success.data = [{"id": "session-retry-success"}]

        mock_table = Mock()
        mock_table.insert.return_value.execute.side_effect = [
            Exception("Transient network error"),
            insert_result_success,
        ]
        mock_supabase.table.return_value = mock_table

        with caplog.at_level(logging.WARNING):
            with patch("supabase_client.get_supabase", return_value=mock_supabase):
                result = save_search_session(
                    user_id="user-retry",
                    sectors=["uniformes"],
                    ufs=["GO"],
                    data_inicial="2025-09-01",
                    data_final="2025-09-30",
                    custom_keywords=None,
                    total_raw=80,
                    total_filtered=20,
                    valor_total=800000.0,
                    resumo_executivo="Test retry success.",
                    destaques=["GO: 20 resultados"],
                )

        # Should succeed on retry
        assert result == "session-retry-success"

        # Should log warning about transient error
        assert any("Transient error saving session" in record.message for record in caplog.records)

        # Should have called sleep once (0.3s delay)
        mock_sleep.assert_called_once_with(0.3)

    @patch("quota._ensure_profile_exists")
    @patch("time.sleep")
    def test_save_session_fails_after_max_retries(self, mock_sleep, mock_ensure_profile, caplog):
        """Both attempts fail → returns None."""
        mock_supabase = Mock()

        # Profile exists
        mock_ensure_profile.return_value = True

        # Both insert attempts fail
        mock_table = Mock()
        mock_table.insert.return_value.execute.side_effect = Exception("Persistent DB error")
        mock_supabase.table.return_value = mock_table

        with caplog.at_level(logging.WARNING):
            with patch("supabase_client.get_supabase", return_value=mock_supabase):
                result = save_search_session(
                    user_id="user-max-retry",
                    sectors=["alimentacao"],
                    ufs=["SC"],
                    data_inicial="2025-10-01",
                    data_final="2025-10-31",
                    custom_keywords=None,
                    total_raw=150,
                    total_filtered=30,
                    valor_total=1500000.0,
                    resumo_executivo="Test max retry failure.",
                    destaques=["SC: 30 resultados"],
                )

        # Should return None after retries exhausted
        assert result is None

        # Should log both warning (retry) and error (final failure)
        assert any("Transient error saving session" in record.message for record in caplog.records)
        assert any("Failed to save search session after retry" in record.message for record in caplog.records)

        # Should have attempted retry once (0.3s delay)
        mock_sleep.assert_called_once_with(0.3)

    @patch("quota._ensure_profile_exists")
    @patch("time.sleep")
    def test_save_session_retry_delay_is_300ms(self, mock_sleep, mock_ensure_profile):
        """Retry delay is exactly 0.3 seconds (300ms)."""
        mock_supabase = Mock()

        # Profile exists
        mock_ensure_profile.return_value = True

        # Both attempts fail to trigger retry
        mock_table = Mock()
        mock_table.insert.return_value.execute.side_effect = Exception("Test error")
        mock_supabase.table.return_value = mock_table

        with patch("supabase_client.get_supabase", return_value=mock_supabase):
            save_search_session(
                user_id="user-delay",
                sectors=["uniformes"],
                ufs=["MT"],
                data_inicial="2025-11-01",
                data_final="2025-11-30",
                custom_keywords=None,
                total_raw=60,
                total_filtered=12,
                valor_total=600000.0,
                resumo_executivo=None,
                destaques=None,
            )

        # Verify exact delay
        mock_sleep.assert_called_once_with(0.3)
