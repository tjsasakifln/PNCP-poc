"""
STORY-444: Trial Nurturing Sequence — tests for Day 1 and Day 5 emails.

Inventário de templates existentes ao momento desta story:
- Day 0:  render_trial_welcome_email       (STORY-321)
- Day 3:  render_trial_engagement_email    (STORY-321)
- Day 7:  render_trial_paywall_alert_email (STORY-321)
- Day 10: render_trial_value_email         (STORY-321)
- Day 13: render_trial_last_day_email      (STORY-321)
- Day 16: render_trial_expired_email       (STORY-321)
- Day 1:  activation_nudge (day3_activation.py) — optional flag DAY3_ACTIVATION_EMAIL_ENABLED
- Day 2:  feature_pipeline (trial.py #10)  — optional flag FEATURE_DISCOVERY_EMAILS_ENABLED
- Day 5:  feature_excel    (trial.py #11)  — optional flag FEATURE_DISCOVERY_EMAILS_ENABLED
- Day 8:  feature_ai       (trial.py #12)  — optional flag FEATURE_DISCOVERY_EMAILS_ENABLED
- Day 8:  referral_invitation              — optional flag REFERRAL_EMAIL_ENABLED

STORY-444 foca em garantir a qualidade dos emails Day 1 (activation_nudge) e
Day 5 (feature_excel), além do comportamento correto de supressão para usuários
que já fizeram upgrade do trial.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ============================================================================
# 1. Template Day 1 — activation_nudge (render_day3_activation_email)
# ============================================================================


class TestRenderTrialDay1Email:
    """Day 1: activation_nudge — usuário ainda não fez busca."""

    def test_returns_html_string(self):
        """Template deve retornar uma string HTML não vazia."""
        from templates.emails.day3_activation import render_day3_activation_email
        html = render_day3_activation_email(user_name="Ana", unsubscribe_url="https://unsub")
        assert isinstance(html, str)
        assert len(html) > 100

    def test_contains_user_name(self):
        """Nome do usuário deve aparecer no corpo do email."""
        from templates.emails.day3_activation import render_day3_activation_email
        html = render_day3_activation_email(user_name="Carlos", unsubscribe_url="https://u")
        assert "Carlos" in html

    def test_contains_cta_to_buscar(self):
        """Email deve ter CTA apontando para /buscar (aha moment)."""
        from templates.emails.day3_activation import render_day3_activation_email
        html = render_day3_activation_email(user_name="Joao")
        assert "/buscar" in html

    def test_contains_urgency_hook(self):
        """Email deve conter copy de urgência ('30 segundos')."""
        from templates.emails.day3_activation import render_day3_activation_email
        html = render_day3_activation_email(user_name="Maria")
        assert "30 segundos" in html

    def test_renders_without_unsubscribe_url(self):
        """Template deve renderizar mesmo sem URL de descadastro."""
        from templates.emails.day3_activation import render_day3_activation_email
        html = render_day3_activation_email(user_name="Pedro")
        assert "Pedro" in html

    def test_contains_unsubscribe_link_when_provided(self):
        """Quando URL de descadastro é fornecida, deve aparecer no HTML."""
        from templates.emails.day3_activation import render_day3_activation_email
        html = render_day3_activation_email(
            user_name="Roberta", unsubscribe_url="https://unsub.example.com"
        )
        assert "https://unsub.example.com" in html

    def test_render_email_dispatch_day1(self):
        """_render_email('activation_nudge') deve produzir subject + html corretos."""
        from services.trial_email_sequence import _render_email
        subject, html = _render_email(
            email_type="activation_nudge",
            user_name="Beatriz",
            stats={"searches_count": 0},
            unsubscribe_url="https://u",
        )
        assert isinstance(subject, str) and len(subject) > 0
        assert "/buscar" in html
        assert "30 segundos" in subject


# ============================================================================
# 2. Template Day 5 — feature_excel (render_trial_feature_excel_email)
# ============================================================================


class TestRenderTrialDay5Email:
    """Day 5: feature_excel — introduz a exportação Excel para o usuário."""

    def test_returns_html_string(self):
        """Template deve retornar uma string HTML não vazia."""
        from templates.emails.trial import render_trial_feature_excel_email
        html = render_trial_feature_excel_email(
            user_name="Fernanda",
            stats={},
            unsubscribe_url="https://unsub",
        )
        assert isinstance(html, str)
        assert len(html) > 100

    def test_contains_user_name(self):
        """Nome do usuário deve aparecer no corpo do email."""
        from templates.emails.trial import render_trial_feature_excel_email
        html = render_trial_feature_excel_email(user_name="Gustavo", stats={})
        assert "Gustavo" in html

    def test_contains_excel_topic(self):
        """Email deve mencionar Excel (feature principal)."""
        from templates.emails.trial import render_trial_feature_excel_email
        html = render_trial_feature_excel_email(user_name="Helena", stats={})
        assert "Excel" in html

    def test_contains_cta_to_buscar(self):
        """CTA deve apontar para /buscar onde o export fica disponível."""
        from templates.emails.trial import render_trial_feature_excel_email
        html = render_trial_feature_excel_email(user_name="Igor", stats={})
        assert "/buscar" in html

    def test_contains_unsubscribe_link_when_provided(self):
        """URL de descadastro deve aparecer quando fornecida."""
        from templates.emails.trial import render_trial_feature_excel_email
        html = render_trial_feature_excel_email(
            user_name="Julia",
            stats={},
            unsubscribe_url="https://smartlic.tech/unsub?t=abc",
        )
        assert "https://smartlic.tech/unsub?t=abc" in html

    def test_includes_stats_block_when_user_has_searches(self):
        """Com buscas realizadas, email deve mostrar bloco de stats."""
        from templates.emails.trial import render_trial_feature_excel_email
        stats = {"searches_count": 5, "opportunities_found": 20, "total_value_estimated": 500_000.0}
        html = render_trial_feature_excel_email(user_name="Lucas", stats=stats)
        # Stats block aparece — pelo menos o valor formatado deve estar no HTML
        assert "500" in html or "R$" in html

    def test_render_email_dispatch_day5(self):
        """_render_email('feature_excel') deve produzir subject + html corretos."""
        from services.trial_email_sequence import _render_email
        subject, html = _render_email(
            email_type="feature_excel",
            user_name="Marina",
            stats={"searches_count": 3},
            unsubscribe_url="https://u",
        )
        assert isinstance(subject, str) and len(subject) > 0
        assert "Excel" in subject
        assert "/buscar" in html


# ============================================================================
# 3. Supressão para usuários que já fizeram upgrade
# ============================================================================


class TestTrialEmailNotSentIfUpgraded:
    """AC8: Se plan_type != free_trial, email não deve ser enviado."""

    @pytest.mark.asyncio
    async def test_email_not_sent_for_pro_user(self):
        """Usuário com plan_type='smartlic_pro' não recebe email de nurturing."""
        from services import trial_email_sequence as svc

        # Simulamos um usuário já convertido retornado pelo Supabase
        pro_user = {
            "id": "u-pro-1",
            "email": "pro@test.com",
            "full_name": "Pro User",
            "plan_type": "smartlic_pro",  # já convertido
            "marketing_emails_enabled": True,
            "trial_conversion_emails_enabled": True,
        }

        sb_exec_mock = AsyncMock()
        sb_exec_mock.return_value = MagicMock(data=[pro_user])

        with patch("config.TRIAL_EMAILS_ENABLED", True), \
             patch("config.DAY3_ACTIVATION_EMAIL_ENABLED", True), \
             patch("config.REFERRAL_EMAIL_ENABLED", False), \
             patch("config.SHARE_ACTIVATION_EMAIL_ENABLED", False), \
             patch("config.features.FEATURE_DISCOVERY_EMAILS_ENABLED", False), \
             patch("services.trial_email_sequence._is_in_send_window", return_value=True), \
             patch("supabase_client.get_supabase", return_value=MagicMock()), \
             patch("supabase_client.sb_execute", sb_exec_mock), \
             patch("email_service.send_email_async") as send_mock:
            result = await svc.process_trial_emails(batch_size=50)

        # Nenhum email deve ter sido enviado para usuário pro
        send_mock.assert_not_called()
        # O usuário deve ter sido contado em converted_skipped
        assert result.get("converted_skipped", 0) >= 1 or result.get("sent", 0) == 0

    @pytest.mark.asyncio
    async def test_email_not_sent_when_trial_emails_disabled(self):
        """Quando TRIAL_EMAILS_ENABLED=false, nenhum email é enviado."""
        from services import trial_email_sequence as svc

        with patch("config.TRIAL_EMAILS_ENABLED", False), \
             patch("email_service.send_email_async") as send_mock:
            result = await svc.process_trial_emails(batch_size=50)

        send_mock.assert_not_called()
        assert result.get("disabled") is True


# ============================================================================
# 4. Todos os templates de nurturing têm link de descadastro
# ============================================================================


class TestTrialEmailTemplatesHaveUnsubscribe:
    """Todos os templates de nurturing devem incluir link de descadastro."""

    UNSUB_URL = "https://api.smartlic.tech/v1/trial-emails/unsubscribe?user_id=u1&token=abc"

    def test_day0_welcome_has_unsubscribe(self):
        from templates.emails.trial import render_trial_welcome_email
        html = render_trial_welcome_email(
            user_name="Test", unsubscribe_url=self.UNSUB_URL
        )
        assert self.UNSUB_URL in html

    def test_day1_activation_has_unsubscribe(self):
        from templates.emails.day3_activation import render_day3_activation_email
        html = render_day3_activation_email(
            user_name="Test", unsubscribe_url=self.UNSUB_URL
        )
        assert self.UNSUB_URL in html

    def test_day3_engagement_has_unsubscribe(self):
        from templates.emails.trial import render_trial_engagement_email
        html = render_trial_engagement_email(
            user_name="Test", stats={}, unsubscribe_url=self.UNSUB_URL
        )
        assert self.UNSUB_URL in html

    def test_day5_excel_has_unsubscribe(self):
        from templates.emails.trial import render_trial_feature_excel_email
        html = render_trial_feature_excel_email(
            user_name="Test", stats={}, unsubscribe_url=self.UNSUB_URL
        )
        assert self.UNSUB_URL in html

    def test_day7_paywall_has_unsubscribe(self):
        from templates.emails.trial import render_trial_paywall_alert_email
        html = render_trial_paywall_alert_email(
            user_name="Test", stats={}, unsubscribe_url=self.UNSUB_URL
        )
        assert self.UNSUB_URL in html

    def test_day10_value_has_unsubscribe(self):
        from templates.emails.trial import render_trial_value_email
        html = render_trial_value_email(
            user_name="Test", stats={}, unsubscribe_url=self.UNSUB_URL
        )
        assert self.UNSUB_URL in html

    def test_day13_last_day_has_unsubscribe(self):
        from templates.emails.trial import render_trial_last_day_email
        html = render_trial_last_day_email(
            user_name="Test", stats={}, unsubscribe_url=self.UNSUB_URL
        )
        assert self.UNSUB_URL in html

    def test_day16_expired_has_unsubscribe(self):
        from templates.emails.trial import render_trial_expired_email
        html = render_trial_expired_email(
            user_name="Test", stats={}, unsubscribe_url=self.UNSUB_URL
        )
        assert self.UNSUB_URL in html


# ============================================================================
# 5. Sequência completa — cobertura dos days no _active_sequence
# ============================================================================


class TestNurturingSequenceDays:
    """Garante que Day 1 e Day 5 estão corretamente registrados na sequência."""

    def test_activation_nudge_day1_in_optional_sequence(self):
        """activation_nudge deve estar no Day 1 da TRIAL_EMAIL_SEQUENCE_OPTIONAL."""
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE_OPTIONAL
        nudge = next((e for e in TRIAL_EMAIL_SEQUENCE_OPTIONAL if e["type"] == "activation_nudge"), None)
        assert nudge is not None
        assert nudge["day"] == 1

    def test_feature_excel_day5_in_optional_sequence(self):
        """feature_excel deve estar no Day 5 da TRIAL_EMAIL_SEQUENCE_OPTIONAL."""
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE_OPTIONAL
        excel = next((e for e in TRIAL_EMAIL_SEQUENCE_OPTIONAL if e["type"] == "feature_excel"), None)
        assert excel is not None
        assert excel["day"] == 5

    def test_active_sequence_includes_day1_when_flag_on(self):
        """Com DAY3_ACTIVATION_EMAIL_ENABLED=True, Day 1 aparece na sequência ativa."""
        with patch("config.DAY3_ACTIVATION_EMAIL_ENABLED", True), \
             patch("config.REFERRAL_EMAIL_ENABLED", False), \
             patch("config.SHARE_ACTIVATION_EMAIL_ENABLED", False), \
             patch("config.features.FEATURE_DISCOVERY_EMAILS_ENABLED", False):
            from services.trial_email_sequence import _active_sequence
            seq = _active_sequence()
            days = [e["day"] for e in seq]
            assert 1 in days

    def test_active_sequence_includes_day5_when_flag_on(self):
        """Com FEATURE_DISCOVERY_EMAILS_ENABLED=True, Day 5 aparece na sequência ativa."""
        with patch("config.DAY3_ACTIVATION_EMAIL_ENABLED", False), \
             patch("config.REFERRAL_EMAIL_ENABLED", False), \
             patch("config.SHARE_ACTIVATION_EMAIL_ENABLED", False), \
             patch("config.features.FEATURE_DISCOVERY_EMAILS_ENABLED", True):
            from services.trial_email_sequence import _active_sequence
            seq = _active_sequence()
            days = [e["day"] for e in seq]
            assert 5 in days

    def test_base_sequence_does_not_include_day1_or_day5(self):
        """Sequência base (6 emails) NÃO deve incluir Day 1 nem Day 5."""
        from services.trial_email_sequence import TRIAL_EMAIL_SEQUENCE
        days = [e["day"] for e in TRIAL_EMAIL_SEQUENCE]
        assert 1 not in days
        assert 5 not in days
