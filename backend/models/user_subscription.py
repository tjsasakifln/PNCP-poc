"""
User Subscription Model

Represents user subscriptions and packs in the SmartLic system.

Schema:
- id: UUID primary key
- user_id: FK to profiles(id)
- plan_id: FK to plans(id)
- credits_remaining: NULL for unlimited plans (monthly/annual/master)
- starts_at: Subscription start timestamp
- expires_at: Subscription expiry (NULL for packs + master)
- stripe_subscription_id: Stripe Subscription ID (for recurring)
- stripe_customer_id: Stripe Customer ID
- billing_period: 'monthly' or 'annual' (added in STORY-171)
- annual_benefits: JSONB of enabled annual benefits (added in STORY-171)
- is_active: Boolean flag for active subscriptions
- created_at: Record creation timestamp
- updated_at: Last update timestamp (auto-updated via trigger)

Indexes:
- idx_user_subscriptions_user: Fast lookups by user_id
- idx_user_subscriptions_active: Fast lookups for active subscriptions
- idx_user_subscriptions_billing: Fast lookups by billing period (STORY-171)

Relationships:
- user: profiles (one-to-many)
- plan: plans (many-to-one)

Usage:
- Recurring subscriptions (monthly/annual): credits_remaining = NULL
- Packs (5, 10, 20 searches): credits_remaining = integer
- Master plan: credits_remaining = NULL, expires_at = NULL
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Index, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from database import Base


class UserSubscription(Base):
    """
    User subscription or purchased pack.

    Attributes:
        id: UUID primary key
        user_id: User who owns this subscription
        plan_id: Plan type (monthly, annual, pack_5, etc.)
        credits_remaining: Remaining searches (NULL for unlimited)
        starts_at: Subscription start date
        expires_at: Subscription expiry (NULL for packs/master)
        stripe_subscription_id: Stripe Subscription ID
        stripe_customer_id: Stripe Customer ID
        billing_period: 'monthly' or 'annual'
        annual_benefits: JSONB of enabled benefits (e.g., {"early_access": true})
        is_active: Whether subscription is currently active
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "user_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False)
    credits_remaining = Column(Integer, nullable=True)  # NULL = unlimited
    starts_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # NULL = never expires (packs + master)
    stripe_subscription_id = Column(String, nullable=True, unique=True)
    stripe_customer_id = Column(String, nullable=True)
    billing_period = Column(
        String(10),
        nullable=False,
        default="monthly",
        server_default="monthly",
    )
    annual_benefits = Column(JSONB, nullable=False, default={}, server_default="{}")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    # user = relationship("Profile", back_populates="subscriptions")
    # plan = relationship("Plan", back_populates="subscriptions")

    __table_args__ = (
        CheckConstraint(
            "billing_period IN ('monthly', 'annual')",
            name="check_billing_period_values",
        ),
        Index("idx_user_subscriptions_user", "user_id"),
        Index(
            "idx_user_subscriptions_active",
            "user_id",
            "is_active",
            postgresql_where="is_active = true",
        ),
        Index(
            "idx_user_subscriptions_billing",
            "user_id",
            "billing_period",
            "is_active",
            postgresql_where="is_active = true",
        ),
    )

    def __repr__(self):
        return (
            f"<UserSubscription(id={self.id}, user_id={self.user_id}, "
            f"plan_id={self.plan_id}, billing_period={self.billing_period}, "
            f"is_active={self.is_active})>"
        )
