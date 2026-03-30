"""Tests for filter_basic.py — basic filter phases and keyword filter pipeline.

Wave 0 Safety Net: Covers apply_basic_filters, apply_keyword_filters,
apply_density_decision, apply_deadline_safety_net.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filter.basic import (
    apply_basic_filters,
    apply_deadline_safety_net,
)


def _make_stats():
    """Create a fresh stats dict matching the pipeline's expectation."""
    return {
        "rejeitadas_uf": 0,
        "rejeitadas_status": 0,
        "rejeitadas_esfera": 0,
        "esfera_indeterminada": 0,
        "rejeitadas_modalidade": 0,
        "rejeitadas_municipio": 0,
        "rejeitadas_orgao": 0,
        "rejeitadas_valor": 0,
        "rejeitadas_valor_alto": 0,
        "rejeitadas_prazo_aberto": 0,
        "rejeitadas_keyword": 0,
        "rejeitadas_prazo": 0,
        "aprovadas_alta_densidade": 0,
        "rejeitadas_baixa_densidade": 0,
        "duvidosas_llm_arbiter": 0,
    }


# ──────────────────────────────────────────────────────────────────────
# apply_basic_filters
# ──────────────────────────────────────────────────────────────────────

class TestApplyBasicFilters:
    """Tests for Phase 1 basic filtering."""

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_uf_filter(self, mock_tracker):
        mock_tracker.return_value = MagicMock()
        bids = [
            {"uf": "SP", "objetoCompra": "Test"},
            {"uf": "RJ", "objetoCompra": "Test"},
        ]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, None, None, None, None, None, None, None,
            None, None, None, stats,
        )
        assert len(result) == 1
        assert stats["rejeitadas_uf"] == 1

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_valor_min_filter(self, mock_tracker):
        mock_tracker.return_value = MagicMock()
        bids = [
            {"uf": "SP", "valorTotalEstimado": 50000},
            {"uf": "SP", "valorTotalEstimado": 200000},
        ]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, None, None, 100000, None, None, None, None,
            None, None, None, stats,
        )
        assert len(result) == 1
        assert stats["rejeitadas_valor"] == 1

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_all_pass(self, mock_tracker):
        mock_tracker.return_value = MagicMock()
        bids = [
            {"uf": "SP", "valorTotalEstimado": 100000},
            {"uf": "SP", "valorTotalEstimado": 200000},
        ]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, None, None, None, None, None, None, None,
            None, None, None, stats,
        )
        assert len(result) == 2

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_empty_input(self, mock_tracker):
        mock_tracker.return_value = MagicMock()
        stats = _make_stats()
        result = apply_basic_filters(
            [], {"SP"}, None, None, None, None, None, None, None,
            None, None, None, stats,
        )
        assert result == []

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_modalidade_filter(self, mock_tracker):
        mock_tracker.return_value = MagicMock()
        bids = [
            {"uf": "SP", "modalidadeId": 1},
            {"uf": "SP", "modalidadeId": 6},
        ]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, None, [1], None, None, None, None, None,
            None, None, None, stats,
        )
        assert len(result) == 1
        assert stats["rejeitadas_modalidade"] == 1

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_municipio_filter(self, mock_tracker):
        mock_tracker.return_value = MagicMock()
        bids = [
            {"uf": "SP", "codigoMunicipioIbge": "3550308"},
            {"uf": "SP", "codigoMunicipioIbge": "3304557"},
        ]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, None, None, None, None, None, ["3550308"], None,
            None, None, None, stats,
        )
        assert len(result) == 1
        assert stats["rejeitadas_municipio"] == 1


# ──────────────────────────────────────────────────────────────────────
# apply_deadline_safety_net
# ──────────────────────────────────────────────────────────────────────

class TestApplyDeadlineSafetyNet:
    """Tests for deadline safety net (Etapa 9)."""

    @pytest.mark.timeout(30)
    def test_non_recebendo_proposta_returns_all(self):
        bids = [{"objetoCompra": "test"}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "encerrada", stats)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_none_status_returns_all(self):
        bids = [{"objetoCompra": "test"}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, None, stats)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_future_deadline_passes(self):
        future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
        bids = [{"dataEncerramentoProposta": future}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_past_deadline_rejected(self):
        past = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        bids = [{"dataEncerramentoProposta": past}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        assert len(result) == 0
        assert stats["rejeitadas_prazo"] == 1

    @pytest.mark.timeout(30)
    def test_recent_abertura_passes(self):
        """Bids opened within 15 days should pass."""
        recent = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        bids = [{"dataAberturaProposta": recent}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_old_publication_rejected(self):
        """Bids published > 15 days ago without other dates are rejected."""
        old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        bids = [{"dataPublicacaoPncp": old}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        assert len(result) == 0
        assert stats["rejeitadas_prazo"] == 1

    @pytest.mark.timeout(30)
    def test_no_dates_rejected(self):
        """Bids with no date fields are rejected for recebendo_proposta."""
        bids = [{"objetoCompra": "test"}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        assert len(result) == 0
        assert stats["rejeitadas_prazo"] == 1

    @pytest.mark.timeout(30)
    def test_invalid_date_format_keeps_bid(self):
        """Invalid date strings should not cause rejection."""
        bids = [{"dataEncerramentoProposta": "not-a-date"}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        # Invalid date on encerramento still appends (see code: after except, append continues)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_mixed_bids(self):
        """Mix of future deadline and past deadline bids."""
        future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
        past = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        bids = [
            {"dataEncerramentoProposta": future, "id": 1},
            {"dataEncerramentoProposta": past, "id": 2},
        ]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        assert len(result) == 1
        assert stats["rejeitadas_prazo"] == 1

    @pytest.mark.timeout(30)
    def test_z_suffix_encerramento(self):
        """Dates with Z suffix are parsed correctly."""
        future = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        bids = [{"dataEncerramentoProposta": future}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_empty_list_returns_empty(self):
        """Empty input returns empty output."""
        stats = _make_stats()
        result = apply_deadline_safety_net([], "recebendo_proposta", stats)
        assert result == []
        assert stats["rejeitadas_prazo"] == 0

    @pytest.mark.timeout(30)
    def test_abertura_16_30_days_with_recebendo_status_passes(self):
        """Bids 16-30 days old with 'recebendo' in status should pass."""
        opened = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
        bids = [{"dataAberturaProposta": opened, "situacaoCompraNome": "Recebendo Propostas"}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_abertura_16_30_days_without_recebendo_status_rejected(self):
        """Bids 16-30 days old without 'recebendo' in status should be rejected."""
        opened = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
        bids = [{"dataAberturaProposta": opened, "situacaoCompraNome": "Encerrada"}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        assert len(result) == 0

    @pytest.mark.timeout(30)
    def test_abertura_over_30_days_rejected(self):
        """Bids opened > 30 days ago are rejected."""
        old = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        bids = [{"dataAberturaProposta": old}]
        stats = _make_stats()
        result = apply_deadline_safety_net(bids, "recebendo_proposta", stats)
        assert len(result) == 0


# ──────────────────────────────────────────────────────────────────────
# apply_basic_filters — additional edge cases
# ──────────────────────────────────────────────────────────────────────

class TestApplyBasicFiltersEdgeCases:
    """Additional edge case tests for basic filters."""

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_valor_max_filter(self, mock_tracker):
        mock_tracker.return_value = MagicMock()
        bids = [
            {"uf": "SP", "valorTotalEstimado": 50000},
            {"uf": "SP", "valorTotalEstimado": 200000},
        ]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, None, None, None, 100000, None, None, None,
            None, None, None, stats,
        )
        assert len(result) == 1
        assert result[0]["valorTotalEstimado"] == 50000

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_valor_string_format(self, mock_tracker):
        """Brazilian-format value strings (1.000.000,50) are parsed."""
        mock_tracker.return_value = MagicMock()
        bids = [{"uf": "SP", "valorTotalEstimado": "1.000.000,50"}]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, None, None, 500000, None, None, None, None,
            None, None, None, stats,
        )
        assert len(result) == 1

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_orgao_filter(self, mock_tracker):
        mock_tracker.return_value = MagicMock()
        bids = [
            {"uf": "SP", "nomeOrgao": "Prefeitura Municipal de Sao Paulo"},
            {"uf": "SP", "nomeOrgao": "Ministerio da Saude"},
        ]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, None, None, None, None, None, None,
            ["Prefeitura"], None, None, None, stats,
        )
        assert len(result) == 1

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_esfera_filter_all_selected(self, mock_tracker):
        """When all 3 esferas selected, filter is bypassed."""
        mock_tracker.return_value = MagicMock()
        bids = [
            {"uf": "SP", "esferaId": "F"},
            {"uf": "SP", "esferaId": "E"},
            {"uf": "SP", "esferaId": "M"},
        ]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, None, None, None, None, ["F", "E", "M"], None,
            None, None, None, None, stats,
        )
        assert len(result) == 3

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_status_filter_recebendo(self, mock_tracker):
        mock_tracker.return_value = MagicMock()
        bids = [
            {"uf": "SP", "_status_inferido": "recebendo_proposta"},
            {"uf": "SP", "_status_inferido": "encerrada"},
        ]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, "recebendo_proposta", None, None, None, None,
            None, None, None, None, None, stats,
        )
        assert len(result) == 1
        assert stats["rejeitadas_status"] == 1

    @pytest.mark.timeout(30)
    @patch("filter.basic._get_tracker")
    def test_status_todos_returns_all(self, mock_tracker):
        mock_tracker.return_value = MagicMock()
        bids = [
            {"uf": "SP", "_status_inferido": "encerrada"},
        ]
        stats = _make_stats()
        result = apply_basic_filters(
            bids, {"SP"}, "todos", None, None, None, None, None, None,
            None, None, None, stats,
        )
        assert len(result) == 1
