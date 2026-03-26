"""Partner service — Revenue share tracking for consultancy partners.

STORY-323: Handles partner lookup, signup attribution, revenue calculation,
and monthly reporting.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from supabase_client import get_supabase, sb_execute

logger = logging.getLogger(__name__)


# ============================================================================
# AC4: Partner lookup by slug (signup flow)
# ============================================================================

async def get_partner_by_slug(slug: str) -> Optional[dict]:
    """Look up an active partner by slug.

    Args:
        slug: Partner slug (e.g. "triunfo-legis")

    Returns:
        Partner dict or None if not found/inactive
    """
    sb = get_supabase()
    result = await sb_execute(
        sb.table("partners")
        .select("id, name, slug, stripe_coupon_id, revenue_share_pct, status")
        .eq("slug", slug)
        .eq("status", "active")
        .limit(1)
    )
    return result.data[0] if result.data else None


async def get_partner_by_coupon(stripe_coupon_id: str) -> Optional[dict]:
    """Look up a partner by their Stripe coupon ID.

    AC5: Used when checkout uses a coupon — auto-link to partner.

    Args:
        stripe_coupon_id: Stripe coupon ID

    Returns:
        Partner dict or None
    """
    if not stripe_coupon_id:
        return None
    sb = get_supabase()
    result = await sb_execute(
        sb.table("partners")
        .select("id, name, slug, revenue_share_pct, status")
        .eq("stripe_coupon_id", stripe_coupon_id)
        .eq("status", "active")
        .limit(1)
    )
    return result.data[0] if result.data else None


# ============================================================================
# AC4: Signup attribution
# ============================================================================

async def attribute_signup_to_partner(user_id: str, partner_slug: str) -> bool:
    """Persist partner attribution on user profile during signup.

    Args:
        user_id: UUID of the new user
        partner_slug: Partner slug from ?partner= query param

    Returns:
        True if attribution was saved, False otherwise
    """
    partner = await get_partner_by_slug(partner_slug)
    if not partner:
        logger.warning("Partner slug '%s' not found or inactive", partner_slug)
        return False

    sb = get_supabase()
    await sb_execute(
        sb.table("profiles")
        .update({"referred_by_partner_id": partner["id"]})
        .eq("id", user_id)
    )
    logger.info(
        "Partner attribution: user=%s partner=%s (%s)",
        user_id[:8], partner["slug"], partner["name"],
    )
    return True


# ============================================================================
# AC6: Create partner referral on conversion (checkout.session.completed)
# ============================================================================

async def create_partner_referral(
    user_id: str,
    monthly_revenue: float,
    stripe_coupon_id: Optional[str] = None,
) -> Optional[str]:
    """Create a partner_referral record when a referred user converts.

    Called from Stripe webhook on checkout.session.completed.
    Looks up partner via:
    1. profiles.referred_by_partner_id (signup flow)
    2. Stripe coupon ID (AC5: coupon-based attribution)

    Args:
        user_id: UUID of the converting user
        monthly_revenue: Monthly subscription amount in BRL
        stripe_coupon_id: Optional Stripe coupon applied at checkout

    Returns:
        Referral ID if created, None otherwise
    """
    sb = get_supabase()

    # 1. Check profile for partner attribution
    profile = await sb_execute(
        sb.table("profiles")
        .select("referred_by_partner_id")
        .eq("id", user_id)
        .single()
    )
    partner_id = (profile.data or {}).get("referred_by_partner_id")

    # 2. Fallback: check coupon-based attribution (AC5)
    if not partner_id and stripe_coupon_id:
        partner = await get_partner_by_coupon(stripe_coupon_id)
        if partner:
            partner_id = partner["id"]
            # Also save attribution to profile for future reference
            await sb_execute(
                sb.table("profiles")
                .update({"referred_by_partner_id": partner_id})
                .eq("id", user_id)
            )

    if not partner_id:
        return None  # User not referred by any partner

    # Get partner's revenue share percentage
    partner_result = await sb_execute(
        sb.table("partners")
        .select("revenue_share_pct")
        .eq("id", partner_id)
        .single()
    )
    share_pct = float((partner_result.data or {}).get("revenue_share_pct", 25.00))
    share_amount = round(monthly_revenue * share_pct / 100, 2)

    # Upsert referral (idempotent — handles duplicate webhooks)
    result = await sb_execute(
        sb.table("partner_referrals")
        .upsert(
            {
                "partner_id": partner_id,
                "referred_user_id": user_id,
                "converted_at": datetime.now(timezone.utc).isoformat(),
                "monthly_revenue": monthly_revenue,
                "revenue_share_amount": share_amount,
            },
            on_conflict="partner_id,referred_user_id",
        )
    )

    referral_id = result.data[0]["id"] if result.data else None
    logger.info(
        "Partner referral created: user=%s partner=%s revenue=R$%.2f share=R$%.2f",
        user_id[:8], str(partner_id)[:8], monthly_revenue, share_amount,
    )
    return referral_id


# ============================================================================
# AC7: Mark churn on subscription deletion
# ============================================================================

async def mark_referral_churned(user_id: str) -> bool:
    """Update partner_referral with churn timestamp.

    Called from Stripe webhook on customer.subscription.deleted.

    Args:
        user_id: UUID of the churning user

    Returns:
        True if a referral was updated, False if user wasn't referred
    """
    sb = get_supabase()
    result = await sb_execute(
        sb.table("partner_referrals")
        .update({"churned_at": datetime.now(timezone.utc).isoformat()})
        .eq("referred_user_id", user_id)
        .is_("churned_at", "null")
    )
    updated = bool(result.data)
    if updated:
        logger.info("Partner referral churned: user=%s", user_id[:8])
    return updated


# ============================================================================
# AC8: Revenue share calculation
# ============================================================================

async def calculate_partner_revenue(
    partner_id: str,
    year: int,
    month: int,
) -> dict:
    """Calculate revenue share for a partner in a given month.

    AC8: Sums monthly_revenue of all active referrals, applies revenue_share_pct.

    Args:
        partner_id: UUID of the partner
        year: Year (e.g. 2026)
        month: Month (1-12)

    Returns:
        dict with total_revenue, share_amount, active_clients
    """
    sb = get_supabase()

    # Get partner's share percentage
    partner = await sb_execute(
        sb.table("partners")
        .select("revenue_share_pct, name")
        .eq("id", partner_id)
        .single()
    )
    if not partner.data:
        return {"error": "partner_not_found"}

    share_pct = float(partner.data["revenue_share_pct"])

    # Get active referrals (converted, not churned) as of the target month
    # "Active" = converted_at <= end of month AND (churned_at IS NULL OR churned_at > start of month)
    month_start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        month_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        month_end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    referrals = await sb_execute(
        sb.table("partner_referrals")
        .select("monthly_revenue, converted_at, churned_at")
        .eq("partner_id", partner_id)
        .not_.is_("converted_at", "null")
        .lte("converted_at", month_end.isoformat())
    )

    # Filter: active during this month (not churned before month start)
    active_referrals = []
    for ref in (referrals.data or []):
        churned = ref.get("churned_at")
        if churned:
            churned_dt = datetime.fromisoformat(churned.replace("Z", "+00:00"))
            if churned_dt <= month_start:
                continue  # Churned before this month
        active_referrals.append(ref)

    total_revenue = sum(float(r.get("monthly_revenue") or 0) for r in active_referrals)
    share_amount = round(total_revenue * share_pct / 100, 2)

    return {
        "partner_id": partner_id,
        "partner_name": partner.data["name"],
        "year": year,
        "month": month,
        "total_revenue": total_revenue,
        "share_pct": share_pct,
        "share_amount": share_amount,
        "active_clients": len(active_referrals),
    }


# ============================================================================
# AC9: Monthly revenue share report (all partners)
# ============================================================================

async def generate_monthly_revenue_report(year: int, month: int) -> dict:
    """Generate revenue share report for all active partners.

    AC9: Called by cron job on day 1 of each month at 09:00 BRT.

    Args:
        year: Year
        month: Month (1-12)

    Returns:
        dict with partner_reports list and totals
    """
    sb = get_supabase()

    # Get all active partners
    partners = await sb_execute(
        sb.table("partners")
        .select("id, name, slug, contact_email")
        .eq("status", "active")
    )

    reports = []
    total_revenue = 0.0
    total_share = 0.0

    for partner in (partners.data or []):
        report = await calculate_partner_revenue(partner["id"], year, month)
        if "error" not in report:
            reports.append({
                **report,
                "contact_email": partner["contact_email"],
                "slug": partner["slug"],
            })
            total_revenue += report["total_revenue"]
            total_share += report["share_amount"]

    logger.info(
        "Monthly revenue report: %d/%d — %d partners, "
        "total_revenue=R$%.2f, total_share=R$%.2f",
        month, year, len(reports), total_revenue, total_share,
    )

    return {
        "year": year,
        "month": month,
        "partner_reports": reports,
        "total_revenue": total_revenue,
        "total_share": total_share,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# Admin helpers
# ============================================================================

async def list_partners(status_filter: Optional[str] = None) -> list[dict]:
    """List all partners, optionally filtered by status.

    AC10: Used by GET /v1/admin/partners.
    """
    sb = get_supabase()
    query = sb.table("partners").select("*").order("created_at", desc=True)
    if status_filter:
        query = query.eq("status", status_filter)
    result = await sb_execute(query)
    return result.data or []


async def create_partner(
    name: str,
    slug: str,
    contact_email: str,
    contact_name: Optional[str] = None,
    stripe_coupon_id: Optional[str] = None,
    revenue_share_pct: float = 25.00,
) -> dict:
    """Create a new partner.

    AC11: Used by POST /v1/admin/partners.
    """
    sb = get_supabase()
    result = await sb_execute(
        sb.table("partners").insert({
            "name": name,
            "slug": slug,
            "contact_email": contact_email,
            "contact_name": contact_name,
            "stripe_coupon_id": stripe_coupon_id,
            "revenue_share_pct": revenue_share_pct,
            "status": "active",
        })
    )
    partner = result.data[0] if result.data else {}
    logger.info("Partner created: slug=%s name=%s", slug, name)
    return partner


async def get_partner_referrals(partner_id: str) -> list[dict]:
    """Get all referrals for a partner.

    AC12: Used by GET /v1/admin/partners/{id}/referrals.
    Joins with profiles to get user name/email.
    """
    sb = get_supabase()
    result = await sb_execute(
        sb.table("partner_referrals")
        .select("*, profiles!referred_user_id(email, full_name)")
        .eq("partner_id", partner_id)
        .order("signup_at", desc=True)
    )
    return result.data or []


async def get_partner_dashboard(user_email: str) -> Optional[dict]:
    """Get dashboard data for a partner (self-service).

    AC14: Partner identified by their email matching partners.contact_email.
    """
    sb = get_supabase()

    # Find partner by email
    partner_result = await sb_execute(
        sb.table("partners")
        .select("id, name, slug, revenue_share_pct, status, created_at")
        .eq("contact_email", user_email)
        .eq("status", "active")
        .limit(1)
    )
    if not partner_result.data:
        return None

    partner = partner_result.data[0]
    partner_id = partner["id"]

    # Get referral summary
    referrals = await sb_execute(
        sb.table("partner_referrals")
        .select("id, signup_at, converted_at, churned_at, monthly_revenue, revenue_share_amount")
        .eq("partner_id", partner_id)
        .order("signup_at", desc=True)
    )

    all_refs = referrals.data or []
    active = [r for r in all_refs if r.get("converted_at") and not r.get("churned_at")]
    total_share = sum(float(r.get("revenue_share_amount") or 0) for r in active)

    return {
        "partner": partner,
        "referrals_total": len(all_refs),
        "referrals_active": len(active),
        "monthly_share": total_share,
        "referrals": all_refs,
    }
