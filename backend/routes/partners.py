"""Partner routes — Admin management + partner self-service dashboard.

STORY-323: Revenue Share Tracking.
AC10-AC14: Partner admin endpoints + partner dashboard.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import require_auth
from authorization import check_user_roles
from config import PARTNERS_ENABLED
from log_sanitizer import mask_user_id
from services.partner_service import (
    calculate_partner_revenue,
    create_partner,
    get_partner_dashboard,
    get_partner_referrals,
    list_partners,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["partners"])


# ── Request body schemas ──────────────────────────────────────────────────────

class CreatePartnerRequest(BaseModel):
    name: str
    slug: str
    contact_email: str
    contact_name: Optional[str] = None
    stripe_coupon_id: Optional[str] = None
    revenue_share_pct: float = 25.00


# ── Admin guard helper ────────────────────────────────────────────────────────

async def _require_admin(user: dict) -> None:
    """Raise 403 if user is not admin."""
    is_admin, _ = await check_user_roles(user["id"])
    if not is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")


# ── AC14: Partner self-service dashboard (MUST be before /{partner_id}) ───────

@router.get("/partner/dashboard")
async def partner_dashboard(user: dict = Depends(require_auth)):
    """AC14: Dashboard for the logged-in partner.

    Partner is identified by matching their auth email to partners.contact_email.
    """
    if not PARTNERS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email não disponível")

    dashboard = await get_partner_dashboard(email)
    if not dashboard:
        raise HTTPException(
            status_code=404,
            detail="Você não está vinculado a nenhuma consultoria parceira",
        )
    return dashboard


# ── AC10: List partners (admin only) ─────────────────────────────────────────

@router.get("/admin/partners")
async def list_partners_endpoint(
    status: Optional[str] = Query(None, description="Filter by status: active, inactive, pending"),
    user: dict = Depends(require_auth),
):
    """AC10: List all partners. Admin only."""
    if not PARTNERS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    await _require_admin(user)
    partners = await list_partners(status_filter=status)

    # Enrich with referral counts
    from supabase_client import get_supabase, sb_execute
    sb = get_supabase()
    for p in partners:
        refs = await sb_execute(
            sb.table("partner_referrals")
            .select("id, converted_at, churned_at, monthly_revenue, revenue_share_amount")
            .eq("partner_id", p["id"])
        )
        all_refs = refs.data or []
        active = [r for r in all_refs if r.get("converted_at") and not r.get("churned_at")]
        p["referrals_total"] = len(all_refs)
        p["referrals_active"] = len(active)
        p["monthly_share"] = sum(float(r.get("revenue_share_amount") or 0) for r in active)

    return {"partners": partners}


# ── AC11: Create partner (admin only) ────────────────────────────────────────

@router.post("/admin/partners", status_code=201)
async def create_partner_endpoint(
    body: CreatePartnerRequest,
    user: dict = Depends(require_auth),
):
    """AC11: Create a new partner. Admin only."""
    if not PARTNERS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    await _require_admin(user)
    logger.info(
        "Creating partner: slug=%s by admin=%s",
        body.slug, mask_user_id(user["id"]),
    )
    try:
        partner = await create_partner(
            name=body.name,
            slug=body.slug,
            contact_email=body.contact_email,
            contact_name=body.contact_name,
            stripe_coupon_id=body.stripe_coupon_id,
            revenue_share_pct=body.revenue_share_pct,
        )
        return partner
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail=f"Slug '{body.slug}' já existe")
        logger.error("Failed to create partner: %s", e)
        raise HTTPException(status_code=500, detail="Erro ao criar parceiro")


# ── AC12: Partner referrals (admin only) ─────────────────────────────────────

@router.get("/admin/partners/{partner_id}/referrals")
async def get_partner_referrals_endpoint(
    partner_id: str,
    user: dict = Depends(require_auth),
):
    """AC12: Get referrals for a specific partner. Admin only."""
    if not PARTNERS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    await _require_admin(user)
    referrals = await get_partner_referrals(partner_id)
    return {"referrals": referrals}


# ── AC13: Partner revenue (admin only) ───────────────────────────────────────

@router.get("/admin/partners/{partner_id}/revenue")
async def get_partner_revenue_endpoint(
    partner_id: str,
    year: int = Query(default=None, description="Year (default: current)"),
    month: int = Query(default=None, description="Month 1-12 (default: current)"),
    user: dict = Depends(require_auth),
):
    """AC13: Get revenue share for a partner in a given month. Admin only."""
    if not PARTNERS_ENABLED:
        raise HTTPException(status_code=404, detail="Feature not available")
    await _require_admin(user)

    now = datetime.now(timezone.utc)
    target_year = year or now.year
    target_month = month or now.month

    if target_month < 1 or target_month > 12:
        raise HTTPException(status_code=400, detail="month deve ser entre 1 e 12")

    report = await calculate_partner_revenue(partner_id, target_year, target_month)
    if "error" in report:
        raise HTTPException(status_code=404, detail="Parceiro não encontrado")
    return report
