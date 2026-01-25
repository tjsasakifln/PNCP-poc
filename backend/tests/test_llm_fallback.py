"""
Tests for gerar_resumo_fallback() - LLM fallback function.

This test module validates the fallback executive summary generator that works
without OpenAI API access. It ensures the system remains functional during
network issues, rate limits, or missing API keys.
"""

import pytest
from datetime import datetime, timedelta
from schemas import ResumoLicitacoes
from llm import gerar_resumo_fallback


class TestGerarResumoFallback:
    """Tests for gerar_resumo_fallback() - LLM fallback function."""

    def test_empty_input_returns_appropriate_message(self):
        """Should return empty state message for empty input."""
        resumo = gerar_resumo_fallback([])

        assert resumo.resumo_executivo == "Nenhuma licitação encontrada."
        assert resumo.total_oportunidades == 0
        assert resumo.valor_total == 0.0
        assert resumo.destaques == []
        assert resumo.alerta_urgencia is None

    def test_single_bid_statistics(self):
        """Should correctly calculate statistics for single bid."""
        licitacoes = [
            {
                "nomeOrgao": "Prefeitura de São Paulo",
                "uf": "SP",
                "valorTotalEstimado": 150_000.0,
                "dataAberturaProposta": "2026-03-01T10:00:00"
            }
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert resumo.total_oportunidades == 1
        assert resumo.valor_total == 150_000.0
        assert "1 licitações" in resumo.resumo_executivo
        assert "150" in resumo.resumo_executivo  # Value in summary
        assert len(resumo.destaques) == 1
        assert "Prefeitura de São Paulo" in resumo.destaques[0]

    def test_multiple_bids_total_value_calculation(self):
        """Should correctly sum values from multiple bids."""
        licitacoes = [
            {"nomeOrgao": "Órgão A", "uf": "SP", "valorTotalEstimado": 100_000.0},
            {"nomeOrgao": "Órgão B", "uf": "RJ", "valorTotalEstimado": 200_000.0},
            {"nomeOrgao": "Órgão C", "uf": "MG", "valorTotalEstimado": 150_000.0}
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert resumo.total_oportunidades == 3
        assert resumo.valor_total == 450_000.0

    def test_top_3_bids_by_value(self):
        """Should highlight top 3 bids by value in descending order."""
        licitacoes = [
            {"nomeOrgao": "Menor", "uf": "SP", "valorTotalEstimado": 50_000.0},
            {"nomeOrgao": "Maior", "uf": "RJ", "valorTotalEstimado": 500_000.0},
            {"nomeOrgao": "Médio", "uf": "MG", "valorTotalEstimado": 150_000.0},
            {"nomeOrgao": "Segundo", "uf": "RS", "valorTotalEstimado": 300_000.0}
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert len(resumo.destaques) == 3
        # First should be highest value
        assert "Maior" in resumo.destaques[0]
        assert "500" in resumo.destaques[0]  # Value in first highlight
        # Second should be second highest
        assert "Segundo" in resumo.destaques[1]
        # Third should be third highest
        assert "Médio" in resumo.destaques[2]

    def test_only_2_bids_returns_2_destaques(self):
        """Should return only 2 highlights when there are only 2 bids."""
        licitacoes = [
            {"nomeOrgao": "A", "uf": "SP", "valorTotalEstimado": 100_000.0},
            {"nomeOrgao": "B", "uf": "RJ", "valorTotalEstimado": 200_000.0}
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert len(resumo.destaques) == 2

    def test_urgency_alert_for_deadline_within_7_days(self):
        """Should trigger urgency alert when deadline is < 7 days."""
        # Bid closing in 5 days (urgent)
        data_urgente = (datetime.now() + timedelta(days=5)).isoformat()

        licitacoes = [
            {
                "nomeOrgao": "Prefeitura Urgente",
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "dataAberturaProposta": data_urgente
            }
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert resumo.alerta_urgencia is not None
        assert "menos de 7 dias" in resumo.alerta_urgencia
        assert "Prefeitura Urgente" in resumo.alerta_urgencia

    def test_no_urgency_alert_for_deadline_over_7_days(self):
        """Should not trigger urgency alert when deadline is > 7 days."""
        # Bid closing in 30 days (not urgent)
        data_futura = (datetime.now() + timedelta(days=30)).isoformat()

        licitacoes = [
            {
                "nomeOrgao": "Prefeitura Normal",
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "dataAberturaProposta": data_futura
            }
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert resumo.alerta_urgencia is None

    def test_urgency_detection_on_day_6(self):
        """Should trigger urgency alert when deadline is exactly 6 days away."""
        data_urgente = (datetime.now() + timedelta(days=6)).isoformat()

        licitacoes = [
            {
                "nomeOrgao": "Prefeitura Limite",
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "dataAberturaProposta": data_urgente
            }
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert resumo.alerta_urgencia is not None

    def test_handles_missing_optional_fields(self):
        """Should gracefully handle bids with missing fields."""
        licitacoes = [
            {
                # Missing nomeOrgao, dataAberturaProposta
                "uf": "SP",
                "valorTotalEstimado": 100_000.0
            },
            {
                "nomeOrgao": "Órgão Completo",
                "uf": "RJ",
                # Missing valorTotalEstimado - should default to 0
                "dataAberturaProposta": "2026-05-01T10:00:00"
            }
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert resumo.total_oportunidades == 2
        assert resumo.valor_total == 100_000.0  # Only first bid has value
        assert "N/A" in resumo.destaques[0]  # Missing nomeOrgao

    def test_handles_none_values_in_valor_field(self):
        """Should treat None valor as 0 for calculations."""
        licitacoes = [
            {"nomeOrgao": "A", "uf": "SP", "valorTotalEstimado": None},
            {"nomeOrgao": "B", "uf": "RJ", "valorTotalEstimado": 150_000.0}
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert resumo.valor_total == 150_000.0
        assert resumo.total_oportunidades == 2

    def test_handles_missing_uf_field(self):
        """Should use 'N/A' for missing UF field."""
        licitacoes = [
            {
                "nomeOrgao": "Órgão Sem UF",
                # Missing uf field
                "valorTotalEstimado": 100_000.0
            }
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        # Should not crash, just use N/A for UF distribution
        assert resumo.total_oportunidades == 1

    def test_matches_gerar_resumo_schema(self):
        """Should return same ResumoLicitacoes schema as gerar_resumo()."""
        licitacoes = [
            {
                "nomeOrgao": "Prefeitura Teste",
                "uf": "SP",
                "valorTotalEstimado": 100_000.0
            }
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        # Should be valid ResumoLicitacoes instance
        assert isinstance(resumo, ResumoLicitacoes)
        assert hasattr(resumo, "resumo_executivo")
        assert hasattr(resumo, "total_oportunidades")
        assert hasattr(resumo, "valor_total")
        assert hasattr(resumo, "destaques")
        assert hasattr(resumo, "alerta_urgencia")

    def test_urgency_detection_uses_first_urgent_bid(self):
        """Should stop at first urgent bid found (fail-fast)."""
        data_urgente_1 = (datetime.now() + timedelta(days=3)).isoformat()
        data_urgente_2 = (datetime.now() + timedelta(days=5)).isoformat()

        licitacoes = [
            {
                "nomeOrgao": "Primeira Urgente",
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "dataAberturaProposta": data_urgente_1
            },
            {
                "nomeOrgao": "Segunda Urgente",
                "uf": "RJ",
                "valorTotalEstimado": 150_000.0,
                "dataAberturaProposta": data_urgente_2
            }
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert resumo.alerta_urgencia is not None
        # Should mention the first urgent bid
        assert "Primeira Urgente" in resumo.alerta_urgencia

    def test_handles_malformed_date_gracefully(self):
        """Should skip urgency check for malformed dates (no crash)."""
        licitacoes = [
            {
                "nomeOrgao": "Órgão com Data Inválida",
                "uf": "SP",
                "valorTotalEstimado": 100_000.0,
                "dataAberturaProposta": "invalid-date-format"
            }
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        # Should not crash
        assert resumo.total_oportunidades == 1
        # Should not trigger urgency (can't parse date)
        assert resumo.alerta_urgencia is None

    def test_resumo_executivo_format(self):
        """Should generate resumo_executivo in correct format."""
        licitacoes = [
            {"nomeOrgao": "A", "uf": "SP", "valorTotalEstimado": 100_000.0},
            {"nomeOrgao": "B", "uf": "RJ", "valorTotalEstimado": 200_000.0}
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        # Should contain count
        assert "2 licitações" in resumo.resumo_executivo
        # Should contain total value
        assert "300" in resumo.resumo_executivo
        # Should mention uniforms
        assert "uniformes" in resumo.resumo_executivo.lower()

    def test_large_batch_performance(self):
        """Should handle large batch (100+ bids) efficiently."""
        licitacoes = [
            {
                "nomeOrgao": f"Órgão {i}",
                "uf": ["SP", "RJ", "MG", "RS"][i % 4],
                "valorTotalEstimado": 50_000.0 + (i * 10_000.0),
                "dataAberturaProposta": (datetime.now() + timedelta(days=30)).isoformat()
            }
            for i in range(150)
        ]

        resumo = gerar_resumo_fallback(licitacoes)

        assert resumo.total_oportunidades == 150
        assert len(resumo.destaques) == 3  # Still only top 3
        # Top 1 should be highest value (last in list)
        assert "Órgão 149" in resumo.destaques[0]

    def test_works_offline_no_external_dependencies(self):
        """Should function without network access or external APIs."""
        import sys
        from unittest.mock import patch

        licitacoes = [
            {
                "nomeOrgao": "Teste Offline",
                "uf": "SP",
                "valorTotalEstimado": 100_000.0
            }
        ]

        # Mock OpenAI module to ensure no external dependencies
        with patch.dict(sys.modules, {"openai": None}):
            resumo = gerar_resumo_fallback(licitacoes)

            # Should work even with OpenAI module "unavailable"
            assert resumo.total_oportunidades == 1
            assert resumo.valor_total == 100_000.0
