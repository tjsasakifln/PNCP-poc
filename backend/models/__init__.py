"""
Database Models Package

SQLAlchemy ORM models for SmartLic database entities.

Models:
- stripe_webhook_event: Stripe webhook idempotency and audit trail
- user_subscription: User subscriptions and credits

Note: These models complement the Supabase schema defined in migrations.
Use migrations for schema changes, ORM models for application logic.
"""

from .stripe_webhook_event import StripeWebhookEvent
from .user_subscription import UserSubscription

__all__ = ["StripeWebhookEvent", "UserSubscription"]
