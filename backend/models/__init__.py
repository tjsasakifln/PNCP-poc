"""
DEPRECATED: SQLAlchemy ORM Models — replaced by Supabase client in STORY-201.

All DB operations now use supabase_client.py (get_supabase()) with direct table queries.
These models are kept only for backward compatibility with existing tests.
DO NOT add new models or import from this package in new code.

Original models:
- stripe_webhook_event: Stripe webhook idempotency and audit trail
- user_subscription: User subscriptions and credits
"""

from .stripe_webhook_event import StripeWebhookEvent
from .user_subscription import UserSubscription

__all__ = ["StripeWebhookEvent", "UserSubscription"]
