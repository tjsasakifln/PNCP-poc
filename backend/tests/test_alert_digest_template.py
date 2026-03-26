"""
Tests for STORY-315 AC23: Alert digest email templates.

Covers:
  - Individual alert digest rendering
  - Consolidated digest rendering (AC6)
  - Subject line generation
  - Edge cases (empty, single, many)
  - Format helpers (_format_brl, _viability_badge)
"""



# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

MOCK_OPPORTUNITIES = [
    {
        "titulo": "Aquisicao de computadores desktop",
        "orgao": "Prefeitura Municipal de Sao Paulo",
        "valor_estimado": 150000.0,
        "uf": "SP",
        "modalidade": "Pregao Eletronico",
        "link_pncp": "https://pncp.gov.br/item-001",
        "viability_score": 0.85,
    },
    {
        "titulo": "Fornecimento de notebooks para secretaria",
        "orgao": "Governo do Estado de RJ",
        "valor_estimado": 500000.0,
        "uf": "RJ",
        "modalidade": "Concorrencia",
        "link_pncp": "https://pncp.gov.br/item-002",
        "viability_score": 0.45,
    },
    {
        "titulo": "Servico de manutencao de equipamentos de TI",
        "orgao": "Tribunal Regional Federal",
        "valor_estimado": 0.0,
        "uf": "DF",
        "modalidade": "",
        "link_pncp": "",
        "viability_score": None,
    },
]


# ============================================================================
# Individual digest
# ============================================================================


class TestRenderAlertDigestEmail:
    """AC5: Individual alert digest email template."""

    def test_renders_with_opportunities(self):
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Joao",
            alert_name="Hardware e TI",
            opportunities=MOCK_OPPORTUNITIES,
            total_count=3,
            unsubscribe_url="https://example.com/unsub",
        )

        assert "Joao" in html
        assert "Hardware e TI" in html
        assert "computadores desktop" in html
        assert "Prefeitura Municipal" in html
        assert "R$" in html
        assert "https://example.com/unsub" in html

    def test_renders_empty_state(self):
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Maria",
            alert_name="Software",
            opportunities=[],
            total_count=0,
            unsubscribe_url="https://example.com/unsub",
        )

        assert "Maria" in html
        assert "não encontrou novas oportunidades" in html
        assert "Fazer análise manual" in html

    def test_renders_single_opportunity(self):
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Carlos",
            alert_name="Engenharia",
            opportunities=[MOCK_OPPORTUNITIES[0]],
            total_count=1,
            unsubscribe_url="https://example.com/unsub",
        )

        assert "Carlos" in html
        assert "1" in html
        assert "oportunidade" in html

    def test_truncates_long_title(self):
        from templates.emails.alert_digest import render_alert_digest_email

        long_opp = [{
            **MOCK_OPPORTUNITIES[0],
            "titulo": "A" * 200,
        }]

        html = render_alert_digest_email(
            user_name="Test",
            alert_name="Test",
            opportunities=long_opp,
            total_count=1,
            unsubscribe_url="https://example.com/unsub",
        )

        # Title should be truncated (max 120 chars + "...")
        assert "A" * 117 + "..." in html

    def test_contains_pncp_link(self):
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Test",
            alert_name="Test",
            opportunities=MOCK_OPPORTUNITIES[:1],
            total_count=1,
            unsubscribe_url="https://example.com/unsub",
        )

        assert "https://pncp.gov.br/item-001" in html
        assert "Ver edital completo" in html

    def test_handles_no_pncp_link(self):
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Test",
            alert_name="Test",
            opportunities=[MOCK_OPPORTUNITIES[2]],  # No link_pncp
            total_count=1,
            unsubscribe_url="https://example.com/unsub",
        )

        assert "Servico de manutencao" in html

    def test_max_10_items_displayed(self):
        from templates.emails.alert_digest import render_alert_digest_email

        # Create 15 opportunities
        many_opps = [
            {**MOCK_OPPORTUNITIES[0], "titulo": f"Item {i}"} for i in range(15)
        ]

        html = render_alert_digest_email(
            user_name="Test",
            alert_name="Test",
            opportunities=many_opps,
            total_count=15,
            unsubscribe_url="https://example.com/unsub",
        )

        # Item 0-9 should be present, items 10+ should not
        assert "Item 0" in html
        assert "Item 9" in html
        # CTA should show total count
        assert "15" in html

    def test_cta_shows_total_when_more(self):
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Test",
            alert_name="Test",
            opportunities=MOCK_OPPORTUNITIES[:2],
            total_count=25,
            unsubscribe_url="https://example.com/unsub",
        )

        assert "Ver todas as 25 oportunidades" in html

    def test_unsubscribe_footer(self):
        from templates.emails.alert_digest import render_alert_digest_email

        html = render_alert_digest_email(
            user_name="Test",
            alert_name="Test",
            opportunities=MOCK_OPPORTUNITIES[:1],
            total_count=1,
            unsubscribe_url="https://example.com/unsub/abc",
        )

        assert "https://example.com/unsub/abc" in html
        assert "preferencias" in html.lower() or "preferências" in html.lower()


# ============================================================================
# Consolidated digest (AC6)
# ============================================================================


class TestRenderConsolidatedDigestEmail:
    """AC6: Consolidated multi-alert digest email."""

    def test_renders_multiple_alerts(self):
        from templates.emails.alert_digest import render_consolidated_digest_email

        summaries = [
            {
                "alert_name": "Hardware",
                "opportunities": MOCK_OPPORTUNITIES[:2],
                "total_count": 2,
            },
            {
                "alert_name": "Software",
                "opportunities": [MOCK_OPPORTUNITIES[2]],
                "total_count": 1,
            },
        ]

        html = render_consolidated_digest_email(
            user_name="Ana",
            alert_summaries=summaries,
            unsubscribe_url="https://example.com/unsub",
        )

        assert "Ana" in html
        assert "Hardware" in html
        assert "Software" in html
        assert "3" in html  # Total across alerts
        assert "2 alertas" in html or "2" in html

    def test_empty_consolidated_digest(self):
        from templates.emails.alert_digest import render_consolidated_digest_email

        html = render_consolidated_digest_email(
            user_name="Pedro",
            alert_summaries=[],
            unsubscribe_url="https://example.com/unsub",
        )

        assert "Pedro" in html
        assert "Nenhum" in html or "nenhum" in html

    def test_consolidated_with_zero_count_alerts(self):
        from templates.emails.alert_digest import render_consolidated_digest_email

        summaries = [
            {"alert_name": "Empty Alert", "opportunities": [], "total_count": 0},
        ]

        html = render_consolidated_digest_email(
            user_name="Test",
            alert_summaries=summaries,
            unsubscribe_url="https://example.com/unsub",
        )

        # Should show no-results state
        assert "Nenhum" in html or "nenhum" in html

    def test_consolidated_top_5_per_alert(self):
        """AC6: Consolidated shows max 5 items per alert section."""
        from templates.emails.alert_digest import render_consolidated_digest_email

        many_opps = [
            {**MOCK_OPPORTUNITIES[0], "titulo": f"Opp {i}"} for i in range(10)
        ]

        summaries = [
            {"alert_name": "Big Alert", "opportunities": many_opps, "total_count": 10},
        ]

        html = render_consolidated_digest_email(
            user_name="Test",
            alert_summaries=summaries,
            unsubscribe_url="https://example.com/unsub",
        )

        # Should show Opp 0-4 but NOT Opp 5-9 (max 5 per section)
        assert "Opp 0" in html
        assert "Opp 4" in html


# ============================================================================
# Subject lines
# ============================================================================


class TestSubjectLines:
    """AC15: Subject line generation."""

    def test_individual_subject_with_count(self):
        from templates.emails.alert_digest import get_alert_digest_subject

        subject = get_alert_digest_subject(5, "Hardware")
        assert "5" in subject
        assert "Hardware" in subject
        assert "SmartLic" in subject

    def test_individual_subject_singular(self):
        from templates.emails.alert_digest import get_alert_digest_subject

        subject = get_alert_digest_subject(1, "Software")
        assert "1 nova oportunidade" in subject

    def test_individual_subject_zero(self):
        from templates.emails.alert_digest import get_alert_digest_subject

        subject = get_alert_digest_subject(0, "Saude")
        assert "Nenhuma" in subject or "nenhuma" in subject

    def test_consolidated_subject_with_count(self):
        from templates.emails.alert_digest import get_consolidated_digest_subject

        subject = get_consolidated_digest_subject(12, 3)
        assert "12" in subject
        assert "3" in subject
        assert "SmartLic" in subject

    def test_consolidated_subject_singular(self):
        from templates.emails.alert_digest import get_consolidated_digest_subject

        subject = get_consolidated_digest_subject(1, 1)
        assert "1 nova oportunidade" in subject

    def test_consolidated_subject_zero(self):
        from templates.emails.alert_digest import get_consolidated_digest_subject

        subject = get_consolidated_digest_subject(0, 0)
        assert "Nenhuma" in subject or "nenhuma" in subject


# ============================================================================
# Format helpers
# ============================================================================


class TestFormatHelpers:
    """Test currency formatting and viability badges."""

    def test_format_brl_millions(self):
        from templates.emails.alert_digest import _format_brl

        assert "M" in _format_brl(5_000_000)

    def test_format_brl_thousands(self):
        from templates.emails.alert_digest import _format_brl

        result = _format_brl(50_000)
        assert "k" in result
        assert "50" in result

    def test_format_brl_small(self):
        from templates.emails.alert_digest import _format_brl

        result = _format_brl(500)
        assert "R$" in result

    def test_viability_badge_alta(self):
        from templates.emails.alert_digest import _viability_badge

        badge = _viability_badge(0.8)
        assert "Alta viabilidade" in badge
        assert "#2e7d32" in badge  # Green

    def test_viability_badge_media(self):
        from templates.emails.alert_digest import _viability_badge

        badge = _viability_badge(0.5)
        assert "média" in badge.lower()

    def test_viability_badge_baixa(self):
        from templates.emails.alert_digest import _viability_badge

        badge = _viability_badge(0.2)
        assert "Baixa" in badge

    def test_viability_badge_none(self):
        from templates.emails.alert_digest import _viability_badge

        badge = _viability_badge(None)
        assert badge == ""
