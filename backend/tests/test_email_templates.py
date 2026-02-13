"""
Tests for email templates — STORY-225

Validates all email templates render correctly with proper content.
"""

import pytest

from templates.emails.welcome import render_welcome_email
from templates.emails.quota import render_quota_warning_email, render_quota_exhausted_email
from templates.emails.billing import (
    render_payment_confirmation_email,
    render_subscription_expiring_email,
    render_cancellation_email,
)
from templates.emails.base import email_base


# ============================================================================
# Base template
# ============================================================================

class TestBaseTemplate:
    """Test email base template wrapper."""

    def test_base_renders_html(self):
        html = email_base(title="Test", body_html="<p>Hello</p>")
        assert "<!DOCTYPE html>" in html
        assert "<p>Hello</p>" in html
        assert "SmartLic" in html

    def test_base_includes_footer(self):
        """AC18: Footer includes company info and privacy policy link."""
        html = email_base(title="Test", body_html="<p>Hi</p>")
        assert "Política de Privacidade" in html
        assert "Termos de Uso" in html
        assert "smartlic.tech" in html

    def test_base_transactional_no_unsubscribe(self):
        """AC17: Transactional emails exempt from unsubscribe."""
        html = email_base(
            title="Test",
            body_html="<p>Hi</p>",
            is_transactional=True,
            unsubscribe_url="https://example.com/unsub",
        )
        assert "Cancelar inscrição" not in html

    def test_base_marketing_has_unsubscribe(self):
        """AC15: Marketing emails include unsubscribe link."""
        html = email_base(
            title="Test",
            body_html="<p>Hi</p>",
            is_transactional=False,
            unsubscribe_url="https://example.com/unsub",
        )
        assert "Cancelar inscrição" in html
        assert "https://example.com/unsub" in html

    def test_base_responsive_meta_tag(self):
        """AC9: Responsive design meta viewport tag."""
        html = email_base(title="Test", body_html="<p>Hi</p>")
        assert 'name="viewport"' in html
        assert "width=device-width" in html


# ============================================================================
# Welcome email (AC6-AC9)
# ============================================================================

class TestWelcomeEmail:
    """Test welcome email template."""

    def test_welcome_contains_user_name(self):
        """AC8: Includes user name."""
        html = render_welcome_email(user_name="João Silva")
        assert "João Silva" in html

    def test_welcome_contains_plan_name(self):
        """AC8: Includes plan type."""
        html = render_welcome_email(user_name="Maria", plan_name="Consultor Ágil")
        assert "Consultor Ágil" in html

    def test_welcome_contains_search_link(self):
        """AC8: Includes link to /buscar."""
        html = render_welcome_email(user_name="Test")
        assert "/buscar" in html

    def test_welcome_value_proposition(self):
        """AC6: Value proposition recap."""
        html = render_welcome_email(user_name="Test")
        assert "PNCP" in html or "licitação" in html.lower() or "Contratações" in html

    def test_welcome_cta_button(self):
        """AC6: Contains call-to-action button."""
        html = render_welcome_email(user_name="Test")
        assert "Fazer minha primeira busca" in html

    def test_welcome_custom_login_url(self):
        html = render_welcome_email(user_name="Test", login_url="https://custom.com/login")
        assert "https://custom.com/login" in html


# ============================================================================
# Quota warning email (AC10)
# ============================================================================

class TestQuotaWarningEmail:
    """Test quota warning email template."""

    def test_quota_warning_shows_usage(self):
        """AC10: Shows usage numbers."""
        html = render_quota_warning_email(
            user_name="João", plan_name="Consultor Ágil",
            quota_used=8, quota_limit=10, reset_date="01/03/2026",
        )
        assert "8" in html
        assert "10" in html
        assert "80%" in html

    def test_quota_warning_shows_remaining(self):
        html = render_quota_warning_email(
            user_name="João", plan_name="Máquina",
            quota_used=240, quota_limit=300, reset_date="01/03/2026",
        )
        assert "60" in html  # remaining

    def test_quota_warning_shows_reset_date(self):
        html = render_quota_warning_email(
            user_name="João", plan_name="Test",
            quota_used=8, quota_limit=10, reset_date="15/04/2026",
        )
        assert "15/04/2026" in html

    def test_quota_warning_has_upgrade_cta(self):
        html = render_quota_warning_email(
            user_name="João", plan_name="Test",
            quota_used=8, quota_limit=10, reset_date="01/03/2026",
        )
        assert "upgrade" in html.lower()


# ============================================================================
# Quota exhausted email (AC11)
# ============================================================================

class TestQuotaExhaustedEmail:
    """Test quota exhaustion email template."""

    def test_quota_exhausted_shows_limit(self):
        """AC11: Shows the quota limit."""
        html = render_quota_exhausted_email(
            user_name="Maria", plan_name="Consultor Ágil",
            quota_limit=50, reset_date="01/03/2026",
        )
        assert "50" in html

    def test_quota_exhausted_shows_reset_date(self):
        """AC11: Shows reset date."""
        html = render_quota_exhausted_email(
            user_name="Maria", plan_name="Test",
            quota_limit=50, reset_date="01/04/2026",
        )
        assert "01/04/2026" in html

    def test_quota_exhausted_has_upgrade_cta(self):
        html = render_quota_exhausted_email(
            user_name="Maria", plan_name="Test",
            quota_limit=50, reset_date="01/03/2026",
        )
        assert "upgrade" in html.lower()


# ============================================================================
# Payment confirmation email (AC12)
# ============================================================================

class TestPaymentConfirmationEmail:
    """Test payment confirmation email template."""

    def test_payment_shows_plan_name(self):
        """AC12: Shows plan name."""
        html = render_payment_confirmation_email(
            user_name="João", plan_name="Máquina",
            amount="R$ 597,00", next_renewal_date="01/03/2026",
        )
        assert "Máquina" in html

    def test_payment_shows_amount(self):
        """AC12: Shows amount."""
        html = render_payment_confirmation_email(
            user_name="João", plan_name="Test",
            amount="R$ 297,00", next_renewal_date="01/03/2026",
        )
        assert "R$ 297,00" in html

    def test_payment_shows_next_renewal(self):
        """AC12: Shows next renewal date."""
        html = render_payment_confirmation_email(
            user_name="João", plan_name="Test",
            amount="R$ 297,00", next_renewal_date="15/04/2026",
        )
        assert "15/04/2026" in html

    def test_payment_shows_billing_period(self):
        html = render_payment_confirmation_email(
            user_name="João", plan_name="Test",
            amount="R$ 297,00", next_renewal_date="01/03/2026",
            billing_period="anual",
        )
        assert "Anual" in html

    def test_payment_is_transactional(self):
        """AC17: Payment emails are transactional (no unsubscribe)."""
        html = render_payment_confirmation_email(
            user_name="Test", plan_name="Test",
            amount="R$ 100", next_renewal_date="01/01/2027",
        )
        assert "Cancelar inscrição" not in html


# ============================================================================
# Subscription expiring email (AC13)
# ============================================================================

class TestSubscriptionExpiringEmail:
    """Test subscription expiration warning email template."""

    def test_expiring_7_days(self):
        """AC13: 7-day warning."""
        html = render_subscription_expiring_email(
            user_name="João", plan_name="Consultor Ágil",
            expiry_date="15/03/2026", days_remaining=7,
        )
        assert "7 dias" in html
        assert "15/03/2026" in html

    def test_expiring_1_day(self):
        """AC13: 1-day warning (more urgent)."""
        html = render_subscription_expiring_email(
            user_name="João", plan_name="Consultor Ágil",
            expiry_date="09/03/2026", days_remaining=1,
        )
        assert "1 dia" in html

    def test_expiring_has_renew_cta(self):
        html = render_subscription_expiring_email(
            user_name="João", plan_name="Test",
            expiry_date="01/03/2026", days_remaining=7,
        )
        assert "Renovar" in html


# ============================================================================
# Cancellation email (AC14)
# ============================================================================

class TestCancellationEmail:
    """Test cancellation confirmation email template."""

    def test_cancellation_shows_plan(self):
        """AC14: Shows plan name."""
        html = render_cancellation_email(
            user_name="João", plan_name="Máquina",
            end_date="01/04/2026",
        )
        assert "Máquina" in html

    def test_cancellation_shows_end_date(self):
        """AC14: Shows end date."""
        html = render_cancellation_email(
            user_name="João", plan_name="Test",
            end_date="15/03/2026",
        )
        assert "15/03/2026" in html

    def test_cancellation_has_reactivation_link(self):
        """AC14: Includes reactivation link."""
        html = render_cancellation_email(
            user_name="João", plan_name="Test",
            end_date="01/04/2026",
        )
        assert "Reativar" in html
        assert "/precos" in html
