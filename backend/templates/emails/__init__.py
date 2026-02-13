"""Email templates for SmartLic transactional emails — STORY-225."""

from templates.emails.base import email_base, SMARTLIC_GREEN, SMARTLIC_DARK
from templates.emails.welcome import render_welcome_email
from templates.emails.quota import render_quota_warning_email, render_quota_exhausted_email
from templates.emails.billing import (
    render_payment_confirmation_email,
    render_subscription_expiring_email,
    render_cancellation_email,
)

__all__ = [
    "email_base",
    "SMARTLIC_GREEN",
    "SMARTLIC_DARK",
    "render_welcome_email",
    "render_quota_warning_email",
    "render_quota_exhausted_email",
    "render_payment_confirmation_email",
    "render_subscription_expiring_email",
    "render_cancellation_email",
]
