"""Tests for filter_status.py — status, modalidade, esfera, and deadline filtering.

Wave 0 Safety Net: Covers filtrar_por_status, filtrar_por_modalidade,
filtrar_por_esfera, filtrar_por_prazo_aberto.
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filter_status import (
    filtrar_por_status,
    filtrar_por_modalidade,
    filtrar_por_esfera,
    filtrar_por_prazo_aberto,
)


# ──────────────────────────────────────────────────────────────────────
# filtrar_por_status
# ──────────────────────────────────────────────────────────────────────

class TestFiltrarPorStatus:
    """Tests for status filtering with inferred status."""

    @pytest.mark.timeout(30)
    def test_todos_returns_all(self):
        bids = [{"_status_inferido": "recebendo_proposta"}, {"_status_inferido": "encerrada"}]
        result = filtrar_por_status(bids, "todos")
        assert len(result) == 2

    @pytest.mark.timeout(30)
    def test_none_status_returns_all(self):
        bids = [{"_status_inferido": "recebendo_proposta"}]
        result = filtrar_por_status(bids, None)
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_filter_recebendo_proposta(self):
        bids = [
            {"_status_inferido": "recebendo_proposta"},
            {"_status_inferido": "encerrada"},
        ]
        result = filtrar_por_status(bids, "recebendo_proposta")
        assert len(result) == 1
        assert result[0]["_status_inferido"] == "recebendo_proposta"

    @pytest.mark.timeout(30)
    @patch("status_inference.inferir_status_licitacao", return_value="encerrada")
    def test_infers_status_on_the_fly(self, mock_infer):
        bids = [{"objetoCompra": "Test bid"}]  # No _status_inferido
        result = filtrar_por_status(bids, "encerrada")
        assert len(result) == 1
        assert bids[0]["_status_inferido"] == "encerrada"

    @pytest.mark.timeout(30)
    def test_empty_list(self):
        result = filtrar_por_status([], "recebendo_proposta")
        assert result == []


# ──────────────────────────────────────────────────────────────────────
# filtrar_por_modalidade
# ──────────────────────────────────────────────────────────────────────

class TestFiltrarPorModalidade:
    """Tests for modalidade filtering."""

    @pytest.mark.timeout(30)
    def test_none_returns_all(self):
        bids = [{"modalidadeId": 1}, {"modalidadeId": 6}]
        result = filtrar_por_modalidade(bids, None)
        assert len(result) == 2

    @pytest.mark.timeout(30)
    def test_filter_specific_modalidades(self):
        bids = [
            {"modalidadeId": 1},
            {"modalidadeId": 6},
            {"modalidadeId": 3},
        ]
        result = filtrar_por_modalidade(bids, [1, 3])
        assert len(result) == 2

    @pytest.mark.timeout(30)
    def test_string_modalidade_converted(self):
        bids = [{"modalidadeId": "1"}]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_alternative_field_name(self):
        bids = [{"codigoModalidadeContratacao": 5}]
        result = filtrar_por_modalidade(bids, [5])
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_no_match(self):
        bids = [{"modalidadeId": 1}]
        result = filtrar_por_modalidade(bids, [6])
        assert len(result) == 0

    @pytest.mark.timeout(30)
    def test_none_modalidade_id_excluded(self):
        bids = [{"objetoCompra": "No modalidade field"}]
        result = filtrar_por_modalidade(bids, [1])
        assert len(result) == 0


# ──────────────────────────────────────────────────────────────────────
# filtrar_por_esfera
# ──────────────────────────────────────────────────────────────────────

class TestFiltrarPorEsfera:
    """Tests for esfera (government sphere) filtering."""

    @pytest.mark.timeout(30)
    def test_none_returns_all(self):
        bids = [{"esferaId": "F"}, {"esferaId": "M"}]
        result = filtrar_por_esfera(bids, None)
        assert len(result) == 2

    @pytest.mark.timeout(30)
    def test_filter_federal(self):
        bids = [{"esferaId": "F"}, {"esferaId": "M"}]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 1
        assert result[0]["esferaId"] == "F"

    @pytest.mark.timeout(30)
    def test_case_insensitive(self):
        bids = [{"esferaId": "f"}]
        result = filtrar_por_esfera(bids, ["F"])
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_fallback_by_orgao_name(self):
        """When esferaId missing, infer from org name."""
        bids = [{"nomeOrgao": "Prefeitura Municipal de Teste"}]
        result = filtrar_por_esfera(bids, ["M"])
        assert len(result) == 1

    @pytest.mark.timeout(30)
    def test_multiple_esferas(self):
        bids = [
            {"esferaId": "F"},
            {"esferaId": "E"},
            {"esferaId": "M"},
        ]
        result = filtrar_por_esfera(bids, ["F", "M"])
        assert len(result) == 2

    @pytest.mark.timeout(30)
    def test_empty_bids(self):
        result = filtrar_por_esfera([], ["F"])
        assert result == []


# ──────────────────────────────────────────────────────────────────────
# filtrar_por_prazo_aberto
# ──────────────────────────────────────────────────────────────────────

class TestFiltrarPorPrazoAberto:
    """Tests for open-deadline filtering."""

    @pytest.mark.timeout(30)
    def test_future_deadline_passes(self):
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        bids = [{"dataEncerramentoProposta": future}]
        approved, rejected = filtrar_por_prazo_aberto(bids)
        assert len(approved) == 1
        assert rejected == 0

    @pytest.mark.timeout(30)
    def test_past_deadline_rejected(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        bids = [{"dataEncerramentoProposta": past}]
        approved, rejected = filtrar_por_prazo_aberto(bids)
        assert len(approved) == 0
        assert rejected == 1

    @pytest.mark.timeout(30)
    def test_no_deadline_passes(self):
        """Conservative: bids without deadline are kept."""
        bids = [{"objetoCompra": "Test"}]
        approved, rejected = filtrar_por_prazo_aberto(bids)
        assert len(approved) == 1
        assert rejected == 0

    @pytest.mark.timeout(30)
    def test_invalid_date_passes(self):
        """Conservative: unparseable dates are kept."""
        bids = [{"dataEncerramentoProposta": "not-a-date"}]
        approved, rejected = filtrar_por_prazo_aberto(bids)
        assert len(approved) == 1

    @pytest.mark.timeout(30)
    def test_empty_list(self):
        approved, rejected = filtrar_por_prazo_aberto([])
        assert approved == []
        assert rejected == 0

    @pytest.mark.timeout(30)
    def test_z_suffix_handled(self):
        future = "2030-12-31T23:59:59Z"
        bids = [{"dataEncerramentoProposta": future}]
        approved, rejected = filtrar_por_prazo_aberto(bids)
        assert len(approved) == 1
