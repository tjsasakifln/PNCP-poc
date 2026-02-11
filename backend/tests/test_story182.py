"""Tests for STORY-182: Search Quality & User Trust Restoration.

Tests for:
- AC1: Correct deadline field (dataEncerramentoProposta)
- AC2: Urgency classification
- AC3: Semantic sector context analysis
- AC5: Pluralization (backend helper)
"""

import pytest
from datetime import date, timedelta


# ──────────────────── AC1 + AC2: Deadline & Urgency ────────────────────


class TestCalcularDiasRestantes:
    """Test days remaining calculation from deadline date."""

    def test_future_deadline_positive_days(self):
        from routes.search import _calcular_dias_restantes
        # 30 days from today
        future = (date.today() + timedelta(days=30)).isoformat()
        result = _calcular_dias_restantes(future)
        assert result == 30

    def test_past_deadline_negative_days(self):
        from routes.search import _calcular_dias_restantes
        past = (date.today() - timedelta(days=5)).isoformat()
        result = _calcular_dias_restantes(past)
        assert result == -5

    def test_today_deadline_zero(self):
        from routes.search import _calcular_dias_restantes
        today = date.today().isoformat()
        result = _calcular_dias_restantes(today)
        assert result == 0

    def test_none_returns_none(self):
        from routes.search import _calcular_dias_restantes
        assert _calcular_dias_restantes(None) is None

    def test_empty_string_returns_none(self):
        from routes.search import _calcular_dias_restantes
        assert _calcular_dias_restantes("") is None

    def test_invalid_date_returns_none(self):
        from routes.search import _calcular_dias_restantes
        assert _calcular_dias_restantes("not-a-date") is None

    def test_datetime_string_truncated_to_date(self):
        from routes.search import _calcular_dias_restantes
        # Full ISO datetime with time component
        future = (date.today() + timedelta(days=10)).isoformat() + "T14:30:00Z"
        result = _calcular_dias_restantes(future)
        assert result == 10


class TestCalcularUrgencia:
    """Test urgency level classification."""

    def test_encerrada_negative_days(self):
        from routes.search import _calcular_urgencia
        assert _calcular_urgencia(-1) == "encerrada"
        assert _calcular_urgencia(-100) == "encerrada"

    def test_critica_under_7_days(self):
        from routes.search import _calcular_urgencia
        assert _calcular_urgencia(0) == "critica"
        assert _calcular_urgencia(3) == "critica"
        assert _calcular_urgencia(6) == "critica"

    def test_alta_7_to_13_days(self):
        from routes.search import _calcular_urgencia
        assert _calcular_urgencia(7) == "alta"
        assert _calcular_urgencia(10) == "alta"
        assert _calcular_urgencia(13) == "alta"

    def test_media_14_to_30_days(self):
        from routes.search import _calcular_urgencia
        assert _calcular_urgencia(14) == "media"
        assert _calcular_urgencia(20) == "media"
        assert _calcular_urgencia(30) == "media"

    def test_baixa_over_30_days(self):
        from routes.search import _calcular_urgencia
        assert _calcular_urgencia(31) == "baixa"
        assert _calcular_urgencia(100) == "baixa"
        assert _calcular_urgencia(365) == "baixa"

    def test_none_returns_none(self):
        from routes.search import _calcular_urgencia
        assert _calcular_urgencia(None) is None


class TestConvertToLicitacaoItems:
    """Test that _convert_to_licitacao_items populates dias_restantes and urgencia."""

    def test_items_have_dias_restantes(self):
        from routes.search import _convert_to_licitacao_items
        future = (date.today() + timedelta(days=15)).isoformat()
        raw = [{
            "codigoCompra": "TEST-001",
            "objetoCompra": "Test object",
            "nomeOrgao": "Test Org",
            "uf": "SP",
            "valorTotalEstimado": 100000,
            "dataEncerramentoProposta": future,
        }]
        items = _convert_to_licitacao_items(raw)
        assert len(items) == 1
        assert items[0].dias_restantes == 15
        assert items[0].urgencia == "media"

    def test_items_without_deadline(self):
        from routes.search import _convert_to_licitacao_items
        raw = [{
            "codigoCompra": "TEST-002",
            "objetoCompra": "Test object",
            "nomeOrgao": "Test Org",
            "uf": "RJ",
            "valorTotalEstimado": 50000,
        }]
        items = _convert_to_licitacao_items(raw)
        assert len(items) == 1
        assert items[0].dias_restantes is None
        assert items[0].urgencia is None

    def test_uses_data_encerramento_not_abertura(self):
        """AC1: System must use dataEncerramentoProposta, NOT dataAberturaProposta."""
        from routes.search import _convert_to_licitacao_items
        abertura = (date.today() - timedelta(days=30)).isoformat()  # past
        encerramento = (date.today() + timedelta(days=60)).isoformat()  # future
        raw = [{
            "codigoCompra": "TEST-003",
            "objetoCompra": "Test object",
            "nomeOrgao": "Test Org",
            "uf": "MG",
            "valorTotalEstimado": 200000,
            "dataAberturaProposta": abertura,
            "dataEncerramentoProposta": encerramento,
        }]
        items = _convert_to_licitacao_items(raw)
        assert items[0].dias_restantes == 60  # Uses encerramento, not abertura
        assert items[0].data_encerramento == encerramento[:10]


# ──────────────────── AC3: Semantic Sector Analysis ────────────────────


class TestAnalisarContextoSetor:
    """Test semantic sector context analysis."""

    def test_rodoviario_terms(self):
        from filter import analisar_contexto_setor
        scores = analisar_contexto_setor(["pavimentação", "drenagem", "terraplenagem"])
        assert "rodoviário" in scores
        assert scores["rodoviário"] > 0.5

    def test_hidroviario_terms(self):
        from filter import analisar_contexto_setor
        scores = analisar_contexto_setor(["dragagem", "porto", "atracação"])
        assert "hidroviário" in scores
        assert scores["hidroviário"] > 0.5

    def test_edificacoes_terms(self):
        from filter import analisar_contexto_setor
        scores = analisar_contexto_setor(["reforma", "pintura", "alvenaria"])
        assert "edificações" in scores
        assert scores["edificações"] > 0.5

    def test_empty_terms_returns_zeros(self):
        from filter import analisar_contexto_setor
        scores = analisar_contexto_setor([])
        for score in scores.values():
            assert score == 0.0

    def test_unrelated_terms_low_scores(self):
        from filter import analisar_contexto_setor
        scores = analisar_contexto_setor(["banana", "chocolate", "café"])
        for score in scores.values():
            assert score < 0.3


class TestObterSetorDominante:
    """Test dominant sector detection."""

    def test_clear_rodoviario(self):
        from filter import obter_setor_dominante
        result = obter_setor_dominante(["pavimentação", "asfalto", "rodovia"])
        assert result == "rodoviário"

    def test_clear_hidroviario(self):
        from filter import obter_setor_dominante
        result = obter_setor_dominante(["dragagem", "porto", "cais"])
        assert result == "hidroviário"

    def test_no_clear_sector_returns_none(self):
        from filter import obter_setor_dominante
        result = obter_setor_dominante(["banana", "chocolate"])
        assert result is None

    def test_empty_list_returns_none(self):
        from filter import obter_setor_dominante
        result = obter_setor_dominante([])
        assert result is None

    def test_rodoviario_not_hidroviario(self):
        """AC3: Search for road engineering should NOT return waterway results."""
        from filter import obter_setor_dominante
        result = obter_setor_dominante(["pavimentação", "drenagem", "terraplenagem"])
        assert result == "rodoviário"
        assert result != "hidroviário"
