"""Tests for filter_recovery.py — synonym recovery and zero-results relaxation.

Wave 0 Safety Net: Covers run_synonym_recovery, _log_fluxo2_stats.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filter_recovery import run_synonym_recovery


def _make_stats():
    """Create a fresh stats dict for FLUXO 2."""
    return {
        "rejeitadas_keyword": 0,
    }


class TestRunSynonymRecovery:
    """Tests for FLUXO 2 synonym recovery pipeline."""

    @pytest.mark.timeout(30)
    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    def test_skips_when_llm_zero_match_active(self):
        """GTM-FIX-028 AC10: Skip FLUXO 2 when LLM zero-match active."""
        stats = _make_stats()
        aprovadas = [{"id": 1}]
        result = run_synonym_recovery(
            aprovadas, [{"id": 1}, {"id": 2}],
            setor="vestuario", custom_terms=None,
            stats=stats, llm_zero_match_active=True,
        )
        assert len(result) == 1  # No recovery added
        assert "recuperadas_exclusion_recovery" in stats

    @pytest.mark.timeout(30)
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    def test_no_setor_no_custom_terms_skips(self):
        """Without sector or custom terms, FLUXO 2 is skipped."""
        stats = _make_stats()
        aprovadas = []
        result = run_synonym_recovery(
            aprovadas, [{"objetoCompra": "test"}],
            setor=None, custom_terms=None,
            stats=stats, llm_zero_match_active=False,
        )
        assert len(result) == 0
        assert "aprovadas_synonym_match" in stats

    @pytest.mark.timeout(30)
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    @patch("synonyms.find_synonym_matches", return_value=[])
    @patch("synonyms.should_auto_approve_by_synonyms", return_value=(False, []))
    @patch("sectors.get_sector")
    def test_no_synonyms_found(self, mock_get_sector, mock_auto, mock_find):
        """When no synonyms are found, no recovery happens."""
        mock_sector = MagicMock()
        mock_sector.keywords = {"uniforme", "farda"}
        mock_sector.name = "Vestuario"
        mock_get_sector.return_value = mock_sector

        stats = _make_stats()
        aprovadas = [{"id": 1, "objetoCompra": "uniformes"}]
        resultado_valor = [
            {"id": 1, "objetoCompra": "uniformes"},
            {"id": 2, "objetoCompra": "computadores"},
        ]
        result = run_synonym_recovery(
            aprovadas, resultado_valor,
            setor="vestuario", custom_terms=None,
            stats=stats, llm_zero_match_active=False,
        )
        assert len(result) == 1  # Only original, no recovery

    @pytest.mark.timeout(30)
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    @patch("synonyms.find_synonym_matches", return_value=[("farda", "fardamento")])
    @patch("synonyms.should_auto_approve_by_synonyms")
    @patch("sectors.get_sector")
    def test_single_synonym_goes_to_llm(self, mock_get_sector, mock_auto, mock_find):
        """Single synonym match goes to LLM recovery candidate pool."""
        mock_sector = MagicMock()
        mock_sector.keywords = {"uniforme"}
        mock_sector.name = "Vestuario"
        mock_get_sector.return_value = mock_sector
        mock_auto.return_value = (False, [("farda", "fardamento")])

        stats = _make_stats()
        aprovadas = []
        resultado_valor = [{"id": 2, "objetoCompra": "fardamento militar"}]

        with patch("filter_recovery._run_llm_recovery") as mock_llm:
            result = run_synonym_recovery(
                aprovadas, resultado_valor,
                setor="vestuario", custom_terms=None,
                stats=stats, llm_zero_match_active=False,
            )
            mock_llm.assert_called_once()

    @pytest.mark.timeout(30)
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    @patch("sectors.get_sector", side_effect=KeyError("no"))
    @patch("synonyms.find_synonym_matches")
    @patch("synonyms.should_auto_approve_by_synonyms")
    def test_setor_not_found_handled(self, mock_auto, mock_find, mock_get_sector):
        """KeyError for unknown sector is handled gracefully."""
        stats = _make_stats()
        aprovadas = []
        resultado_valor = [{"objetoCompra": "test"}]

        result = run_synonym_recovery(
            aprovadas, resultado_valor,
            setor="nonexistent", custom_terms=None,
            stats=stats, llm_zero_match_active=False,
        )
        assert len(result) == 0

    @pytest.mark.timeout(30)
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    def test_stats_initialized(self):
        """Stats keys are always initialized even if FLUXO 2 is skipped."""
        stats = {}
        result = run_synonym_recovery(
            [], [], setor=None, custom_terms=None,
            stats=stats, llm_zero_match_active=False,
        )
        assert "recuperadas_exclusion_recovery" in stats
        assert "aprovadas_synonym_match" in stats
        assert "recuperadas_zero_results" in stats

    @pytest.mark.timeout(30)
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    @patch("synonyms.find_synonym_matches")
    @patch("synonyms.should_auto_approve_by_synonyms")
    @patch("sectors.get_sector")
    def test_auto_approve_two_plus_synonyms(self, mock_get_sector, mock_auto, mock_find):
        """2+ synonyms triggers auto-approve without LLM."""
        mock_sector = MagicMock()
        mock_sector.keywords = {"uniforme", "farda"}
        mock_sector.name = "Vestuario"
        mock_get_sector.return_value = mock_sector
        mock_find.return_value = [("farda", "fardamento"), ("uniforme", "vestimenta")]
        mock_auto.return_value = (True, [("farda", "fardamento"), ("uniforme", "vestimenta")])

        stats = _make_stats()
        aprovadas = []
        resultado_valor = [{"id": 2, "objetoCompra": "fardamento e vestimenta"}]

        result = run_synonym_recovery(
            aprovadas, resultado_valor,
            setor="vestuario", custom_terms=None,
            stats=stats, llm_zero_match_active=False,
        )
        assert stats["synonyms_auto_approved"] >= 1
        assert len(result) == 1

    @pytest.mark.timeout(30)
    @patch("config.LLM_ZERO_MATCH_ENABLED", True)
    def test_llm_zero_match_disabled_but_flag_off(self):
        """When LLM_ZERO_MATCH_ENABLED=True but llm_zero_match_active=False, FLUXO 2 runs."""
        stats = _make_stats()
        # With no sector and no custom terms, still skips
        result = run_synonym_recovery(
            [], [{"objetoCompra": "test"}],
            setor=None, custom_terms=None,
            stats=stats, llm_zero_match_active=False,
        )
        assert "aprovadas_synonym_match" in stats

    @pytest.mark.timeout(30)
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    @patch("synonyms.find_synonym_matches", return_value=[])
    @patch("synonyms.should_auto_approve_by_synonyms", return_value=(False, []))
    @patch("sectors.get_sector")
    def test_empty_objeto_skipped(self, mock_get_sector, mock_auto, mock_find):
        """Bids with empty objetoCompra are skipped in recovery."""
        mock_sector = MagicMock()
        mock_sector.keywords = set()
        mock_sector.name = "Test"
        mock_get_sector.return_value = mock_sector

        stats = _make_stats()
        aprovadas = []
        resultado_valor = [
            {"id": 1, "objetoCompra": ""},
            {"id": 2},  # Missing key
        ]
        result = run_synonym_recovery(
            aprovadas, resultado_valor,
            setor="test", custom_terms=None,
            stats=stats, llm_zero_match_active=False,
        )
        assert len(result) == 0

    @pytest.mark.timeout(30)
    @patch("config.LLM_ZERO_MATCH_ENABLED", False)
    @patch("synonyms.find_synonym_matches", side_effect=Exception("boom"))
    @patch("synonyms.should_auto_approve_by_synonyms")
    @patch("sectors.get_sector")
    def test_exception_in_recovery_handled(self, mock_get_sector, mock_auto, mock_find):
        """Exceptions during synonym matching are handled gracefully."""
        mock_sector = MagicMock()
        mock_sector.keywords = {"x"}
        mock_sector.name = "Test"
        mock_get_sector.return_value = mock_sector

        stats = _make_stats()
        aprovadas = []
        resultado_valor = [{"id": 1, "objetoCompra": "something"}]
        result = run_synonym_recovery(
            aprovadas, resultado_valor,
            setor="test", custom_terms=None,
            stats=stats, llm_zero_match_active=False,
        )
        # Should not raise, returns empty
        assert isinstance(result, list)
