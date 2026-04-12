"""Tests for STORY-371: Day 10 email template with top_opportunity block."""
import pytest


class TestDay10EmailTemplate:
    def test_renders_with_top_opportunity(self):
        from templates.emails.trial import render_trial_value_email
        stats = {
            "total_value_estimated": 87000.0,
            "opportunities_found": 3,
            "pipeline_items_count": 0,
            "top_opportunity": {
                "objeto": "Pregão Eletrônico de Limpeza Predial",
                "orgao_nome": "Prefeitura de Curitiba",
                "valor_formatado": "R$ 87.000",
                "valor": 87000.0,
                "numero_controle": "PNCP-2026-001",
                "dias_ate_encerramento": 8,
            }
        }
        html = render_trial_value_email("Maria", stats, unsubscribe_url="https://example.com/unsub")
        assert "Pregão Eletrônico de Limpeza Predial" in html
        assert "Prefeitura de Curitiba" in html
        assert "R$ 87.000" in html
        assert "Ver este edital agora" in html
        assert "PNCP-2026-001" in html

    def test_renders_without_top_opportunity(self):
        from templates.emails.trial import render_trial_value_email
        stats = {
            "total_value_estimated": 87000.0,
            "opportunities_found": 3,
            "pipeline_items_count": 0,
            "top_opportunity": None,
        }
        html = render_trial_value_email("Maria", stats)
        assert "R$ 87" in html
        assert "Ver este edital agora" not in html

    def test_renders_fallback_when_no_data(self):
        from templates.emails.trial import render_trial_value_email
        stats = {
            "total_value_estimated": 0.0,
            "opportunities_found": 0,
            "pipeline_items_count": 0,
            "top_opportunity": None,
        }
        html = render_trial_value_email("João", stats)
        assert "João" in html
        assert html  # Not empty

    def test_objeto_truncation_in_template(self):
        from templates.emails.trial import render_trial_value_email
        long_objeto = "A" * 200
        stats = {
            "total_value_estimated": 0.0,
            "opportunities_found": 0,
            "pipeline_items_count": 0,
            "top_opportunity": {
                "objeto": long_objeto[:120] + "...",  # Pre-truncated
                "orgao_nome": "Órgão X",
                "valor_formatado": "R$ 50.000",
                "valor": 50000.0,
                "numero_controle": "NUM-001",
                "dias_ate_encerramento": 5,
            }
        }
        html = render_trial_value_email("Test", stats)
        assert "R$ 50.000" in html
