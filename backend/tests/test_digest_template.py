"""Tests for STORY-278 AC3: Digest Email Template.

Tests render_daily_digest_email() output for various scenarios.
"""



class TestRenderDailyDigestEmail:
    """Test daily digest email rendering."""

    def test_renders_with_opportunities(self):
        from templates.emails.digest import render_daily_digest_email

        opportunities = [
            {
                "titulo": "Uniformes escolares para rede municipal",
                "orgao": "Prefeitura de Sao Paulo",
                "valor_estimado": 500000.0,
                "uf": "SP",
                "viability_score": 0.85,
                "data_publicacao": "2026-02-25",
            },
            {
                "titulo": "Camisetas para evento esportivo",
                "orgao": "Secretaria de Esportes RJ",
                "valor_estimado": 150000.0,
                "uf": "RJ",
                "viability_score": 0.5,
                "data_publicacao": "2026-02-25",
            },
        ]

        stats = {
            "total_novas": 2,
            "setor_nome": "Vestuario e Uniformes",
            "total_valor": 650000.0,
        }

        html = render_daily_digest_email("Tiago", opportunities, stats)

        assert "Bom dia, Tiago!" in html
        assert "2 novas oportunidades" in html
        assert "Vestuario e Uniformes" in html
        assert "R$ 650k" in html
        assert "Uniformes escolares" in html
        assert "Prefeitura de Sao Paulo" in html
        assert "SP" in html
        assert "Alta viabilidade" in html  # score 0.85
        assert "Viabilidade média" in html  # score 0.5
        assert "Ver todas as oportunidades" in html
        assert "/buscar?auto=true" in html

    def test_renders_empty_state(self):
        from templates.emails.digest import render_daily_digest_email

        html = render_daily_digest_email("Maria", [], {
            "total_novas": 0,
            "setor_nome": "TI",
            "total_valor": 0,
        })

        assert "Bom dia, Maria!" in html
        assert "Nenhuma nova oportunidade" in html
        assert "Fazer análise manual" in html

    def test_renders_with_low_viability(self):
        from templates.emails.digest import render_daily_digest_email

        opportunities = [
            {
                "titulo": "Contrato de TI",
                "orgao": "INSS",
                "valor_estimado": 100000.0,
                "uf": "DF",
                "viability_score": 0.2,
            },
        ]

        html = render_daily_digest_email("User", opportunities, {
            "total_novas": 1,
            "setor_nome": "Software",
            "total_valor": 100000.0,
        })

        assert "Baixa viabilidade" in html

    def test_renders_without_viability_score(self):
        from templates.emails.digest import render_daily_digest_email

        opportunities = [
            {
                "titulo": "Material de escritorio",
                "orgao": "Camara Municipal",
                "valor_estimado": 50000.0,
                "uf": "MG",
                "viability_score": None,
            },
        ]

        html = render_daily_digest_email("User", opportunities, {
            "total_novas": 1,
            "setor_nome": "Papelaria",
            "total_valor": 50000.0,
        })

        # Should not crash, just no badge
        assert "Material de escritorio" in html
        assert "Alta viabilidade" not in html
        assert "Viabilidade média" not in html
        assert "Baixa viabilidade" not in html

    def test_truncates_long_titulo(self):
        from templates.emails.digest import render_daily_digest_email

        long_title = "A" * 200
        opportunities = [
            {
                "titulo": long_title,
                "orgao": "Orgao",
                "valor_estimado": 10000.0,
                "uf": "SP",
                "viability_score": 0.7,
            },
        ]

        html = render_daily_digest_email("User", opportunities, {
            "total_novas": 1, "setor_nome": "test", "total_valor": 10000.0,
        })

        # Should not contain the full 200-char title
        assert long_title not in html
        assert long_title[:117] in html

    def test_includes_unsubscribe_link(self):
        from templates.emails.digest import render_daily_digest_email

        html = render_daily_digest_email("User", [
            {"titulo": "T", "orgao": "O", "valor_estimado": 100, "uf": "SP", "viability_score": 0.5},
        ], {"total_novas": 1, "setor_nome": "test", "total_valor": 100})

        assert "/conta" in html
        assert "smartlic.tech" in html

    def test_mobile_responsive(self):
        from templates.emails.digest import render_daily_digest_email

        html = render_daily_digest_email("User", [], {"total_novas": 0, "setor_nome": "t", "total_valor": 0})

        assert "max-width: 600px" in html or "max-width:600px" in html
        # Should have responsive styles from base template
        assert "@media" in html

    def test_handles_zero_value(self):
        from templates.emails.digest import render_daily_digest_email

        opportunities = [
            {"titulo": "T", "orgao": "O", "valor_estimado": 0, "uf": "SP", "viability_score": 0.8},
        ]

        html = render_daily_digest_email("User", opportunities, {
            "total_novas": 1, "setor_nome": "test", "total_valor": 0,
        })

        assert "Valor não informado" in html


class TestViabilityBadge:
    """Test the _viability_badge helper."""

    def test_alta_viability(self):
        from templates.emails.digest import _viability_badge
        badge = _viability_badge(0.8)
        assert "Alta viabilidade" in badge
        assert "#2e7d32" in badge  # green text

    def test_media_viability(self):
        from templates.emails.digest import _viability_badge
        badge = _viability_badge(0.5)
        assert "Viabilidade média" in badge
        assert "#f57f17" in badge  # amber text

    def test_baixa_viability(self):
        from templates.emails.digest import _viability_badge
        badge = _viability_badge(0.2)
        assert "Baixa viabilidade" in badge
        assert "#c62828" in badge  # red text

    def test_none_viability(self):
        from templates.emails.digest import _viability_badge
        badge = _viability_badge(None)
        assert badge == ""

    def test_boundary_0_7(self):
        from templates.emails.digest import _viability_badge
        badge = _viability_badge(0.7)
        assert "Alta viabilidade" in badge

    def test_boundary_0_4(self):
        from templates.emails.digest import _viability_badge
        badge = _viability_badge(0.4)
        assert "Viabilidade média" in badge


class TestFormatBrl:
    """Test the _format_brl helper."""

    def test_millions(self):
        from templates.emails.digest import _format_brl
        assert _format_brl(2_500_000) == "R$ 2.5M"

    def test_thousands(self):
        from templates.emails.digest import _format_brl
        assert _format_brl(150_000) == "R$ 150k"

    def test_small_value(self):
        from templates.emails.digest import _format_brl
        result = _format_brl(500)
        assert "R$" in result
        assert "500" in result

    def test_exact_million(self):
        from templates.emails.digest import _format_brl
        assert _format_brl(1_000_000) == "R$ 1.0M"
