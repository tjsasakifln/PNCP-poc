"""
Stripe Webhook Event Model

Stores Stripe webhook events for idempotency and audit trail.

Purpose:
- Prevent duplicate processing of webhooks (Stripe may retry)
- Audit trail for debugging billing issues
- Compliance and forensics

Schema:
- id: Stripe event ID (evt_xxx) - PRIMARY KEY
- type: Event type (customer.subscription.updated, etc.)
- processed_at: When the event was processed (TIMESTAMPTZ)
- payload: Full Stripe event object (JSONB)

Performance:
- Index on (type, processed_at) for analytics queries
- Composite index allows fast lookups by event type

Retention:
- Keep events for 90 days (compliance)
- Archive to S3 after 90 days (future enhancement)
"""

from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from database import Base


class StripeWebhookEvent(Base):
    """
    Stripe webhook event record for idempotency and audit.

    Attributes:
        id: Stripe event ID (evt_xxx)
        type: Event type (customer.subscription.updated, etc.)
        processed_at: Timestamp when event was processed
        payload: Full Stripe event data object (JSONB)
    """

    __tablename__ = "stripe_webhook_events"

    id = Column(String(255), primary_key=True)  # Stripe event ID (evt_xxx)
    type = Column(String(100), nullable=False)
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    payload = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_webhook_events_type", "type", "processed_at"),
    )

    def __repr__(self):
        return f"<StripeWebhookEvent(id={self.id}, type={self.type}, processed_at={self.processed_at})>"
