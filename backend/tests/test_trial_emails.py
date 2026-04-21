"""
STORY-321 AC17: Tests for trial email templates — 6 emails.

Tests each template renders correctly, contains expected content,
handles zero stats, and includes unsubscribe links.
"""


from templates.emails.trial import (
    render_trial_welcome_email,
    render_trial_engagement_email,
    render_trial_paywall_alert_email,
    render_trial_value_email,
    render_trial_last_day_email,
    render_trial_last_day_card_email,
    render_trial_expired_email,
    _format_brl,
    _stats_block,
    _unsubscribe_block,
    _preheader,
)


SAMPLE_STATS = {
    "searches_count": 12,
    "opportunities_found": 47,
    "total_value_estimated": 2_350_000,
    "pipeline_items_count": 8,
    "sectors_searched": ["software", "medicamentos", "construcao"],
}

ZERO_STATS = {
    "searches_count": 0,
    "opportunities_found": 0,
    "total_value_estimated": 0,
    "pipeline_items_count": 0,
    "sectors_searched": [],
}

UNSUB_URL = "https://api.smartlic.tech/v1/trial-emails/unsubscribe?user_id=test&token=abc"


# ============================================================================
# Helpers
# ============================================================================

class TestFormatBrl:
    """Test Brazilian Real formatting helper."""

    def test_millions(self):
        assert "M" in _format_brl(2_500_000)
        assert "2.5M" in _format_brl(2_500_000)

    def test_thousands(self):
        assert "k" in _format_brl(150_000)
        assert "150k" in _format_brl(150_000)

    def test_small_value(self):
        result = _format_brl(500)
        assert "500" in result
        assert "R$" in result

    def test_zero(self):
        result = _format_brl(0)
        assert "R$" in result


class TestStatsBlock:
    """Test stats block rendering."""

    def test_renders_with_stats(self):
        html = _stats_block(SAMPLE_STATS)
        assert "12" in html
        assert "47" in html
        assert "2.4M" in html or "2.3M" in html

    def test_shows_pipeline_when_enabled(self):
        html = _stats_block(SAMPLE_STATS, show_pipeline=True)
        assert "8" in html
        assert "pipeline" in html.lower()

    def test_empty_stats_safe(self):
        html = _stats_block({})
        assert "0" in html


class TestUnsubscribeBlock:
    """Test unsubscribe block rendering."""

    def test_renders_when_url_provided(self):
        html = _unsubscribe_block(UNSUB_URL)
        assert "unsubscribe" in html
        assert "trial" in html.lower()

    def test_empty_when_no_url(self):
        html = _unsubscribe_block("")
        assert html == ""


class TestPreheader:
    """Test preheader text rendering."""

    def test_renders_hidden_div(self):
        html = _preheader("Test preheader text")
        assert "display:none" in html
        assert "Test preheader text" in html

    def test_empty_string(self):
        html = _preheader("")
        assert "display:none" in html


# ============================================================================
# Email #1 — Day 0: Welcome
# ============================================================================

class TestWelcomeEmail:
    """AC17: Email #1 — Day 0: Welcome."""

    def test_renders_without_error(self):
        html = render_trial_welcome_email("Joao")
        assert "<!DOCTYPE html>" in html

    def test_contains_user_name(self):
        html = render_trial_welcome_email("Maria Silva")
        assert "Maria Silva" in html

    def test_contains_welcome_message(self):
        html = render_trial_welcome_email("Test")
        assert "Bem-vindo" in html

    def test_contains_14_day_trial_mention(self):
        html = render_trial_welcome_email("Test")
        assert "14 dias" in html

    def test_contains_3_steps(self):
        """AC7: Welcome email has 3 steps."""
        html = render_trial_welcome_email("Test")
        assert "1." in html
        assert "2." in html
        assert "3." in html

    def test_contains_buscar_cta(self):
        html = render_trial_welcome_email("Test")
        assert "/buscar" in html
        assert "primeira análise" in html.lower()

    def test_contains_preheader(self):
        html = render_trial_welcome_email("Test")
        assert "display:none" in html

    def test_contains_unsubscribe_link(self):
        html = render_trial_welcome_email("Test", unsubscribe_url=UNSUB_URL)
        assert "unsubscribe" in html

    def test_is_not_transactional(self):
        html = render_trial_welcome_email("Test", unsubscribe_url=UNSUB_URL)
        assert "Cancelar" in html or "unsubscribe" in html


# ============================================================================
# Email #2 — Day 3: Engagement
# ============================================================================

class TestEngagementEmail:
    """AC17: Email #2 — Day 3: Engagement with stats."""

    def test_renders_with_stats(self):
        html = render_trial_engagement_email("Joao", SAMPLE_STATS)
        assert "<!DOCTYPE html>" in html

    def test_shows_value_when_used(self):
        html = render_trial_engagement_email("Test", SAMPLE_STATS)
        assert "2.4M" in html or "2.3M" in html

    def test_adapts_for_zero_usage(self):
        html = render_trial_engagement_email("Test", ZERO_STATS)
        assert "11 dias" in html

    def test_cta_explore_sectors(self):
        """AC1: CTA is 'Explorar mais setores'."""
        html = render_trial_engagement_email("Test", SAMPLE_STATS)
        assert "Explorar mais setores" in html

    def test_contains_buscar_link(self):
        html = render_trial_engagement_email("Test", SAMPLE_STATS)
        assert "/buscar" in html

    def test_empty_stats_safe(self):
        html = render_trial_engagement_email("Test", {})
        assert "<!DOCTYPE html>" in html

    def test_unsubscribe_url_passed(self):
        html = render_trial_engagement_email("Test", SAMPLE_STATS, unsubscribe_url=UNSUB_URL)
        assert "unsubscribe" in html

    def test_contains_preheader(self):
        html = render_trial_engagement_email("Test", SAMPLE_STATS)
        assert "display:none" in html


# ============================================================================
# Email #3 — Day 7: Paywall Alert (NEW)
# ============================================================================

class TestPaywallAlertEmail:
    """AC17: Email #3 — Day 7: Paywall alert."""

    def test_renders_without_error(self):
        html = render_trial_paywall_alert_email("Joao", SAMPLE_STATS)
        assert "<!DOCTYPE html>" in html

    def test_mentions_preview_limited(self):
        html = render_trial_paywall_alert_email("Test", SAMPLE_STATS)
        assert "preview" in html.lower() or "limitado" in html.lower()

    def test_mentions_today(self):
        """P0 zero-churn: Email now says 'a partir de hoje' (was 'amanhã')."""
        html = render_trial_paywall_alert_email("Test", SAMPLE_STATS)
        assert "hoje" in html.lower()

    def test_lists_what_changes(self):
        """AC7: Lists what changes after paywall."""
        html = render_trial_paywall_alert_email("Test", SAMPLE_STATS)
        assert "10" in html  # limited to 10 results
        assert "5" in html or "pipeline" in html.lower()

    def test_cta_assine(self):
        """AC1: CTA is 'Assine antes do limite'."""
        html = render_trial_paywall_alert_email("Test", SAMPLE_STATS)
        assert "Assine" in html

    def test_links_to_planos(self):
        html = render_trial_paywall_alert_email("Test", SAMPLE_STATS)
        assert "/planos" in html

    def test_7_days_remaining(self):
        html = render_trial_paywall_alert_email("Test", SAMPLE_STATS)
        assert "7 dias" in html

    def test_shows_stats_when_used(self):
        html = render_trial_paywall_alert_email("Test", SAMPLE_STATS)
        assert "12" in html  # searches count

    def test_empty_stats_safe(self):
        html = render_trial_paywall_alert_email("Test", {})
        assert "<!DOCTYPE html>" in html

    def test_contains_preheader(self):
        html = render_trial_paywall_alert_email("Test", SAMPLE_STATS)
        assert "display:none" in html

    def test_unsubscribe(self):
        html = render_trial_paywall_alert_email("Test", SAMPLE_STATS, unsubscribe_url=UNSUB_URL)
        assert "unsubscribe" in html


# ============================================================================
# Email #4 — Day 10: Valor Acumulado (NEW)
# ============================================================================

class TestValueEmail:
    """AC17: Email #4 — Day 10: Accumulated value."""

    def test_renders_without_error(self):
        html = render_trial_value_email("Joao", SAMPLE_STATS)
        assert "<!DOCTYPE html>" in html

    def test_big_value_highlight(self):
        """AC7: Shows valor acumulado em destaque (R$ grande)."""
        html = render_trial_value_email("Test", SAMPLE_STATS)
        assert "2.4M" in html or "2.3M" in html
        assert "font-size: 36px" in html  # Big number

    def test_cta_nao_perca(self):
        """AC1: CTA is 'Não perca esse progresso'."""
        html = render_trial_value_email("Test", SAMPLE_STATS)
        assert "Não perca esse progresso" in html

    def test_links_to_planos(self):
        html = render_trial_value_email("Test", SAMPLE_STATS)
        assert "/planos" in html

    def test_mentions_annual_discount(self):
        html = render_trial_value_email("Test", SAMPLE_STATS)
        assert "20%" in html
        assert "anual" in html.lower()

    def test_adapts_for_opps_no_value(self):
        stats = {**SAMPLE_STATS, "total_value_estimated": 0}
        html = render_trial_value_email("Test", stats)
        assert "47" in html  # shows opp count

    def test_adapts_for_zero_usage(self):
        html = render_trial_value_email("Test", ZERO_STATS)
        assert "4 dias" in html

    def test_empty_stats_safe(self):
        html = render_trial_value_email("Test", {})
        assert "<!DOCTYPE html>" in html

    def test_pipeline_count_shown(self):
        html = render_trial_value_email("Test", SAMPLE_STATS)
        assert "8" in html  # pipeline items in sub-text

    def test_contains_preheader(self):
        html = render_trial_value_email("Test", SAMPLE_STATS)
        assert "display:none" in html

    def test_unsubscribe(self):
        html = render_trial_value_email("Test", SAMPLE_STATS, unsubscribe_url=UNSUB_URL)
        assert "unsubscribe" in html


# ============================================================================
# Email #5 — Day 13: Last Day
# ============================================================================

class TestLastDayEmail:
    """AC17: Email #5 — Day 13: Last day."""

    def test_renders_without_error(self):
        html = render_trial_last_day_email("Joao", SAMPLE_STATS)
        assert "<!DOCTYPE html>" in html

    def test_urgency_styling(self):
        html = render_trial_last_day_email("Test", SAMPLE_STATS)
        assert "#d32f2f" in html

    def test_contains_price(self):
        html = render_trial_last_day_email("Test", SAMPLE_STATS)
        assert "397" in html

    def test_mentions_tomorrow(self):
        html = render_trial_last_day_email("Test", {})
        assert "Amanhã" in html

    def test_cta_assinar_agora(self):
        """AC1: CTA is 'Assinar agora'."""
        html = render_trial_last_day_email("Test", {})
        assert "Assinar agora" in html

    def test_shows_stats(self):
        html = render_trial_last_day_email("Test", SAMPLE_STATS)
        assert "12" in html

    def test_empty_stats_safe(self):
        html = render_trial_last_day_email("Test", {})
        assert "<!DOCTYPE html>" in html

    def test_contains_preheader(self):
        html = render_trial_last_day_email("Test", SAMPLE_STATS)
        assert "display:none" in html


# ============================================================================
# Email #5b — Day 13 card-branch: First-charge-tomorrow compliance notice
# (STORY-CONV-003c AC1)
# ============================================================================

SAMPLE_CANCEL_URL = "https://smartlic.tech/conta/cancelar-trial?token=eyJ.sample.jwt"


class TestLastDayCardEmail:
    """STORY-CONV-003c AC1: Email #5b — Day 13 for card-rollout cohort."""

    def _render(self, user_name="Ana", stats=None, cancel_url=SAMPLE_CANCEL_URL):
        return render_trial_last_day_card_email(
            user_name=user_name,
            stats=stats if stats is not None else SAMPLE_STATS,
            charge_date_display="amanhã, 21/04",
            plan_name="SmartLic Pro",
            amount_display="R$ 397/mês",
            cancel_url=cancel_url,
        )

    def test_renders_without_error(self):
        assert "<!DOCTYPE html>" in self._render()

    def test_mentions_auto_charge(self):
        html = self._render()
        assert "cartão" in html or "cartao" in html.replace("ã", "a")
        assert "R$ 397" in html

    def test_cta_is_cancel(self):
        """AC1 compliance: CTA is CANCEL, not 'Assinar agora' (card branch auto-converts)."""
        html = self._render()
        assert "Cancelar minha trial" in html
        # MUST NOT contain the legacy scarcity CTA
        assert "Assinar agora" not in html

    def test_cancel_link_is_embedded(self):
        html = self._render()
        assert SAMPLE_CANCEL_URL in html

    def test_mentions_tomorrow(self):
        html = self._render()
        assert "Amanhã" in html or "amanhã" in html

    def test_does_not_say_access_expires(self):
        """Critical: card-branch users do NOT lose access — the trial auto-converts.
        Legacy copy 'seu acesso expira' must NOT appear for this cohort."""
        html = self._render(stats=ZERO_STATS)
        assert "acesso expira" not in html

    def test_headline_with_stats_shows_opportunities(self):
        html = self._render(stats=SAMPLE_STATS)
        # 47 opportunities from SAMPLE_STATS
        assert "47" in html

    def test_empty_stats_neutral_headline(self):
        html = self._render(stats=ZERO_STATS)
        # Neutral variant — still valid compliance notice
        assert "<!DOCTYPE html>" in html
        assert "Cancelar minha trial" in html
        assert "R$ 397" in html

    def test_preheader_present(self):
        assert "display:none" in self._render()

    def test_token_validity_note_present(self):
        """48h TTL of the JWT is disclosed to the user."""
        html = self._render()
        assert "48 horas" in html or "48h" in html

    def test_signature(self):
        """Brand sign-off present."""
        html = self._render()
        assert "Equipe SmartLic" in html


class TestLastDayCardBranchDispatch:
    """STORY-CONV-003c AC1: dispatch layer must branch on has_payment_method."""

    def test_render_email_uses_card_variant_when_flag_set(self, monkeypatch):
        from services import trial_email_sequence

        captured = {}

        def fake_card(**kwargs):
            captured["variant"] = "card"
            captured["cancel_url"] = kwargs.get("cancel_url")
            return "<html>CARD</html>"

        def fake_legacy(user_name, stats, unsubscribe_url=""):
            captured["variant"] = "legacy"
            return "<html>LEGACY</html>"

        # Patch imports inside _render_email via the trial module (local import)
        monkeypatch.setattr(
            "templates.emails.trial.render_trial_last_day_card_email", fake_card
        )
        monkeypatch.setattr(
            "templates.emails.trial.render_trial_last_day_email", fake_legacy
        )
        # Avoid reaching JWT secret config in this unit test
        monkeypatch.setattr(
            "services.trial_cancel_token.create_cancel_trial_token",
            lambda uid: "test.jwt.token",
        )

        subject, html = trial_email_sequence._render_email(
            email_type="last_day",
            user_name="Ana",
            stats=SAMPLE_STATS,
            user_id="user-abc-123",
            has_payment_method=True,
            user_created_at="2026-04-07T10:00:00Z",
        )

        assert captured["variant"] == "card"
        assert "test.jwt.token" in captured["cancel_url"]
        assert "SmartLic Pro" in subject

    def test_render_email_uses_legacy_variant_when_flag_unset(self, monkeypatch):
        from services import trial_email_sequence

        captured = {}

        def fake_card(**kwargs):
            captured["variant"] = "card"
            return "<html>CARD</html>"

        def fake_legacy(user_name, stats, unsubscribe_url=""):
            captured["variant"] = "legacy"
            return "<html>LEGACY</html>"

        monkeypatch.setattr(
            "templates.emails.trial.render_trial_last_day_card_email", fake_card
        )
        monkeypatch.setattr(
            "templates.emails.trial.render_trial_last_day_email", fake_legacy
        )

        subject, html = trial_email_sequence._render_email(
            email_type="last_day",
            user_name="Ana",
            stats=SAMPLE_STATS,
            has_payment_method=False,
        )

        assert captured["variant"] == "legacy"

    def test_token_mint_failure_falls_back_to_plain_url(self, monkeypatch):
        """Token minting MUST NOT break the send loop — fall back gracefully."""
        from services import trial_email_sequence

        captured_kwargs = {}

        def fake_card(**kwargs):
            captured_kwargs.update(kwargs)
            return "<html>CARD</html>"

        monkeypatch.setattr(
            "templates.emails.trial.render_trial_last_day_card_email", fake_card
        )

        def broken_mint(uid):
            raise RuntimeError("jwt_secret_missing")

        monkeypatch.setattr(
            "services.trial_cancel_token.create_cancel_trial_token", broken_mint
        )

        subject, html = trial_email_sequence._render_email(
            email_type="last_day",
            user_name="Ana",
            stats=SAMPLE_STATS,
            user_id="user-abc-123",
            has_payment_method=True,
        )

        # Fallback URL still produced — no token param
        assert "/conta/cancelar-trial" in captured_kwargs["cancel_url"]
        assert "token=" not in captured_kwargs["cancel_url"]


class TestFormatChargeDateDisplay:
    """STORY-CONV-003c AC1 helper: trial_end = created_at + 14d."""

    def test_parses_iso_8601_z_suffix(self):
        from services.trial_email_sequence import _format_charge_date_display

        # 2026-04-07 + 14d = 2026-04-21
        assert _format_charge_date_display("2026-04-07T10:00:00Z") == "amanhã, 21/04"

    def test_parses_iso_8601_offset(self):
        from services.trial_email_sequence import _format_charge_date_display

        assert _format_charge_date_display("2026-04-07T10:00:00+00:00") == "amanhã, 21/04"

    def test_falls_back_on_none(self):
        from services.trial_email_sequence import _format_charge_date_display

        assert _format_charge_date_display(None) == "amanhã"

    def test_falls_back_on_garbage(self):
        from services.trial_email_sequence import _format_charge_date_display

        assert _format_charge_date_display("not-an-iso-timestamp") == "amanhã"


# ============================================================================
# Email #6 — Day 16: Expired
# ============================================================================

class TestExpiredEmail:
    """AC17: Email #6 — Day 16: Expired with 20% off coupon."""

    def test_renders_without_error(self):
        html = render_trial_expired_email("Joao", SAMPLE_STATS)
        assert "<!DOCTYPE html>" in html

    def test_mentions_data_saved(self):
        html = render_trial_expired_email("Test", SAMPLE_STATS)
        assert "30 dias" in html

    def test_cta_20_off(self):
        """AC14: Expired email includes 20% off CTA."""
        html = render_trial_expired_email(
            "Test", SAMPLE_STATS,
            coupon_checkout_url="https://smartlic.tech/planos?coupon=TRIAL_COMEBACK_20",
        )
        assert "20% OFF" in html or "20% off" in html.lower()
        assert "Voltar com 20% off" in html

    def test_coupon_url_in_cta(self):
        """AC14: CTA links to checkout with coupon."""
        url = "https://smartlic.tech/planos?coupon=TRIAL_COMEBACK_20"
        html = render_trial_expired_email("Test", SAMPLE_STATS, coupon_checkout_url=url)
        assert "coupon=TRIAL_COMEBACK_20" in html

    def test_fallback_cta_without_coupon(self):
        html = render_trial_expired_email("Test", SAMPLE_STATS)
        assert "Reativar acesso" in html
        assert "/planos" in html

    def test_adapts_headline_pipeline(self):
        html = render_trial_expired_email("Test", {
            "opportunities_found": 30,
            "pipeline_items_count": 5,
        })
        assert "5 oportunidades" in html

    def test_adapts_headline_opps(self):
        html = render_trial_expired_email("Test", {
            "opportunities_found": 30,
            "pipeline_items_count": 0,
        })
        assert "30 oportunidades" in html

    def test_zero_usage_generic(self):
        html = render_trial_expired_email("Test", ZERO_STATS)
        assert "Sentimos sua falta" in html

    def test_empty_stats_safe(self):
        html = render_trial_expired_email("Test", {})
        assert "<!DOCTYPE html>" in html

    def test_contains_preheader(self):
        html = render_trial_expired_email("Test", SAMPLE_STATS)
        assert "display:none" in html

    def test_20_off_badge(self):
        """AC14: Shows 20% OFF badge."""
        html = render_trial_expired_email(
            "Test", SAMPLE_STATS,
            coupon_checkout_url="https://smartlic.tech/planos?coupon=X",
        )
        assert "20% OFF" in html
        assert "primeiro mês" in html.lower()


# ============================================================================
# CRIT-044 AC11: Verify legacy cron job is removed
# ============================================================================

class TestLegacyCronRemoved:
    """CRIT-044 AC11: Verify legacy STORY-266 trial reminder system is fully removed."""

    def test_check_trial_reminders_removed(self):
        import cron_jobs
        assert not hasattr(cron_jobs, "check_trial_reminders")

    def test_trial_email_milestones_removed(self):
        import cron_jobs
        assert not hasattr(cron_jobs, "TRIAL_EMAIL_MILESTONES")

    def test_start_trial_reminder_task_removed(self):
        import cron_jobs
        assert not hasattr(cron_jobs, "start_trial_reminder_task")

    def test_new_system_still_exists(self):
        import cron_jobs
        assert hasattr(cron_jobs, "start_trial_sequence_task")

    def test_new_system_respects_feature_flag(self):
        from services.trial_email_sequence import process_trial_emails
        import inspect
        source = inspect.getsource(process_trial_emails)
        assert "TRIAL_EMAILS_ENABLED" in source

    def test_new_system_checks_marketing_emails_enabled(self):
        from services.trial_email_sequence import process_trial_emails
        import inspect
        source = inspect.getsource(process_trial_emails)
        assert "marketing_emails_enabled" in source
