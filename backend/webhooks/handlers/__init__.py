"""
Stripe webhook event handlers — decomposed from webhooks/stripe.py (DEBT-307).

Each module handles a group of related Stripe event types:
- checkout: checkout.session.completed, async_payment_succeeded, async_payment_failed
- subscription: customer.subscription.updated, customer.subscription.deleted
- invoice: invoice.payment_succeeded, invoice.payment_failed, invoice.payment_action_required
"""

from webhooks.handlers.checkout import (
    handle_checkout_session_completed,
    handle_async_payment_succeeded,
    handle_async_payment_failed,
)
from webhooks.handlers.subscription import (
    handle_subscription_updated,
    handle_subscription_deleted,
)
from webhooks.handlers.invoice import (
    handle_invoice_payment_succeeded,
    handle_invoice_payment_failed,
    handle_payment_action_required,
)

# Event type -> handler mapping for dispatcher
EVENT_HANDLERS: dict[str, object] = {
    "checkout.session.completed": handle_checkout_session_completed,
    "checkout.session.async_payment_succeeded": handle_async_payment_succeeded,
    "checkout.session.async_payment_failed": handle_async_payment_failed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
    "invoice.payment_succeeded": handle_invoice_payment_succeeded,
    "invoice.payment_failed": handle_invoice_payment_failed,
    "invoice.payment_action_required": handle_payment_action_required,
}

__all__ = [
    "EVENT_HANDLERS",
    "handle_checkout_session_completed",
    "handle_async_payment_succeeded",
    "handle_async_payment_failed",
    "handle_subscription_updated",
    "handle_subscription_deleted",
    "handle_invoice_payment_succeeded",
    "handle_invoice_payment_failed",
    "handle_payment_action_required",
]
