"""Tests for welcome_to_pro email (STORY-CONV-003c AC3).

Asserts that:
  - `render_welcome_to_pro_email` renders lifecycle-aware copy distinct
    from the renewal template.
  - `_send_payment_confirmation_email` branches on
    `is_first_charge_after_trial` and dispatches the correct category
    tag + subject.
"""

from unittest.mock import MagicMock, patch


class TestRenderWelcomeToPro:
    def test_contains_trial_end_and_plan(self):
        from templates.emails.billing import render_welcome_to_pro_email

        html = render_welcome_to_pro_email(
            user_name="Founder B2G",
            plan_name="SmartLic Pro",
            amount="R$ 397,00",
            next_renewal_date="20/05/2026",
            billing_period="mensal",
        )

        # Lifecycle-aware content:
        assert "Bem-vindo ao SmartLic Pro" in html
        assert "trial de 14 dias terminou" in html
        assert "Founder B2G" in html
        assert "R$ 397,00" in html
        assert "20/05/2026" in html
        assert "SmartLic Pro" in html
        # Must link to account + support (reduces support tickets)
        assert "/conta" in html
        assert "/ajuda" in html

    def test_distinguishable_from_renewal_template(self):
        """Post-trial welcome must NOT just duplicate the generic renewal
        confirmation copy — if they rendered the same, detecting
        trial→paid conversion has no user-visible value."""
        from templates.emails.billing import (
            render_payment_confirmation_email,
            render_welcome_to_pro_email,
        )

        renewal = render_payment_confirmation_email(
            user_name="X",
            plan_name="SmartLic Pro",
            amount="R$ 397,00",
            next_renewal_date="20/05/2026",
        )
        welcome = render_welcome_to_pro_email(
            user_name="X",
            plan_name="SmartLic Pro",
            amount="R$ 397,00",
            next_renewal_date="20/05/2026",
        )
        assert renewal != welcome
        assert "Bem-vindo" in welcome
        assert "Bem-vindo" not in renewal


class TestInvoiceHandlerBranching:
    """Verify _send_payment_confirmation_email chooses the right template
    based on is_first_charge_after_trial."""

    def test_trial_branch_uses_welcome_subject_and_tag(self):
        from webhooks.handlers import invoice as invoice_module

        sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {"email": "a@b.com", "full_name": "A B"}
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        invoice_data = {
            "amount_paid": 39700,
            "lines": {"data": [{"plan": {"interval": "month", "interval_count": 1}}]},
        }

        with patch("email_service.send_email_async") as mock_send:
            invoice_module._send_payment_confirmation_email(
                sb,
                user_id="u-1",
                plan_id="smartlic_pro",
                invoice_data=invoice_data,
                new_expires="2026-05-04T00:00:00+00:00",
                is_first_charge_after_trial=True,
            )
            mock_send.assert_called_once()
            kwargs = mock_send.call_args.kwargs
            assert "Bem-vindo ao SmartLic Pro" in kwargs["subject"]
            assert kwargs["tags"] == [{"name": "category", "value": "welcome_to_pro"}]
            assert "Bem-vindo" in kwargs["html"]

    def test_renewal_branch_uses_generic_confirmation(self):
        from webhooks.handlers import invoice as invoice_module

        sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {"email": "c@d.com", "full_name": "C D"}
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        invoice_data = {
            "amount_paid": 39700,
            "lines": {"data": [{"plan": {"interval": "month", "interval_count": 1}}]},
        }

        with patch("email_service.send_email_async") as mock_send:
            invoice_module._send_payment_confirmation_email(
                sb,
                user_id="u-2",
                plan_id="smartlic_pro",
                invoice_data=invoice_data,
                new_expires="2026-05-04T00:00:00+00:00",
                is_first_charge_after_trial=False,
            )
            mock_send.assert_called_once()
            kwargs = mock_send.call_args.kwargs
            assert "Pagamento confirmado" in kwargs["subject"]
            assert kwargs["tags"] == [{"name": "category", "value": "payment_confirmation"}]
            # Must NOT include trial→paid copy on renewals
            assert "trial de 14 dias terminou" not in kwargs["html"]

    def test_default_is_renewal_branch(self):
        """Backward compatibility: callers not passing the new flag fall
        back to the renewal template."""
        from webhooks.handlers import invoice as invoice_module

        sb = MagicMock()
        profile_result = MagicMock()
        profile_result.data = {"email": "e@f.com", "full_name": "E F"}
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = profile_result

        with patch("email_service.send_email_async") as mock_send:
            invoice_module._send_payment_confirmation_email(
                sb,
                user_id="u-3",
                plan_id="smartlic_pro",
                invoice_data={"amount_paid": 0},
                new_expires="2026-05-04T00:00:00+00:00",
            )
            kwargs = mock_send.call_args.kwargs
            assert kwargs["tags"] == [
                {"name": "category", "value": "payment_confirmation"}
            ]
