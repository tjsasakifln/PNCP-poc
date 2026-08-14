"""COPY-COP-006: Lead capture endpoint for non-converted visitors.

Extends the pre-existing lead-capture flow (A2/REPO-004) with:
- New sources: lead_magnet_1/2/3, newsletter, exit_intent, seo_banner
- Email regex validation
- Redis token bucket rate limiting (3 attempts/min per IP)
- Storage in ``lead_captures`` table (via service_role)
- 201 response on success

Backward-compatible: old sources (calculadora, cnpj, alertas, consultoria,
radar, report, intel, diagnostico) continue to be stored in the original
``leads`` table.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from rate_limiter import require_rate_limit
from pipeline.budget import _run_with_budget

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/lead-capture", tags=["lead-capture"])

# ---------------------------------------------------------------------------
# Source enums
# ---------------------------------------------------------------------------

# Old sources (backward compat — stored in ``leads``)
OldLeadCaptureSource = Literal[
    "calculadora",
    "cnpj",
    "alertas",
    "consultoria",
    "radar",
    "report",
    "intel",
    "diagnostico",
    "newsletter_footer",
    "lead_magnet_guia",
    "lead_magnet_checklist",
    "seo_banner",
    "licitacoes_setor",
]

# New sources (COPY-COP-006 — stored in ``lead_captures``)
LeadCaptureSource = Literal[
    "lead_magnet_1",
    "lead_magnet_2",
    "lead_magnet_3",
    "newsletter",
    "exit_intent",
    "seo_banner",
    "partial_preview",
]

ALL_SOURCES = frozenset({
    "calculadora", "cnpj", "alertas",
    "consultoria", "radar", "report", "intel", "diagnostico",
    "lead_magnet_1", "lead_magnet_2", "lead_magnet_3",
    "newsletter", "exit_intent", "seo_banner",
    "partial_preview",
    "family_tender", "family_contract", "family_company",
    "family_organ", "family_municipality", "family_observatory",
    "family_tool", "home",
})

NEW_SOURCES = frozenset({
    "lead_magnet_1", "lead_magnet_2", "lead_magnet_3",
    "newsletter", "exit_intent", "seo_banner",
    "partial_preview",
})

ModalidadeInteresse = Literal["radar", "report", "intel", "nao_sei"]

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class LeadCaptureRequest(BaseModel):
    """Body for POST /v1/lead-capture.

    Supports both old (backward compat) and new (COPY-COP-006) sources.
    """

    email: str
    source: str  # validated at runtime against ALL_SOURCES
    sector: Optional[str] = None
    origin_url: Optional[str] = None
    # Legacy fields (REPO-004)
    uf: Optional[str] = None
    captured_at: Optional[str] = None
    nome: Optional[str] = None
    empresa: Optional[str] = None
    cnpj: Optional[str] = None
    telefone: Optional[str] = None
    modalidade_interesse: Optional[ModalidadeInteresse] = None
    mensagem: Optional[str] = Field(None, max_length=500)
    utm_source: Optional[str] = None
    utm_campaign: Optional[str] = None
    referer_path: Optional[str] = None
    utm_medium: Optional[str] = None
    cta_id: Optional[str] = None
    route_family: Optional[str] = None
    entity_type: Optional[str] = None
    entity_public_id: Optional[str] = None
    landing_url: Optional[str] = None
    referrer: Optional[str] = None
    correlation_id: Optional[str] = None
    consent_version: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        if not EMAIL_RE.match(value):
            raise ValueError("Email inválido")
        return value.lower().strip()

    @field_validator("source")
    @classmethod
    def _validate_source(cls, value: str) -> str:
        if value not in ALL_SOURCES:
            raise ValueError(
                f"source must be one of {sorted(ALL_SOURCES)}, got '{value}'"
            )
        return value


class LeadCaptureResponse(BaseModel):
    """Body for POST /v1/lead-capture (201)."""

    success: bool
    id: Optional[str] = None
    receipt_id: Optional[str] = None
    handoff_state: Optional[str] = None


# ---------------------------------------------------------------------------
# Helper: upsert to legacy ``leads`` table
# ---------------------------------------------------------------------------


async def _store_in_legacy_leads(req: LeadCaptureRequest) -> None:
    """Upsert a row into the original ``leads`` table (old sources only)."""
    from supabase_client import get_supabase, sb_execute

    sb = get_supabase()
    lead_row = {
        "email": req.email.lower().strip(),
        "source": req.source,
        "setor": req.sector,
        "uf": req.uf.upper() if req.uf else None,
        "captured_at": req.captured_at or datetime.now(timezone.utc).isoformat(),
        "nome": req.nome,
        "empresa": req.empresa,
        "cnpj": req.cnpj,
        "telefone": req.telefone,
        "modalidade_interesse": req.modalidade_interesse,
        "mensagem": req.mensagem,
        "utm_source": req.utm_source,
        "utm_campaign": req.utm_campaign,
        "referer_path": req.referer_path,
    }

    try:
        await _run_with_budget(
            sb_execute(
                sb.table("leads").upsert(lead_row, on_conflict="email,source"),
                category="write",
            ),
            budget=5.0,
            phase="route",
            source="lead_capture.legacy_upsert",
        )
    except Exception as exc:
        logger.warning("Failed to store legacy lead: %s", exc)


# ---------------------------------------------------------------------------
# Helper: insert into new ``lead_captures`` table
# ---------------------------------------------------------------------------


async def _store_in_lead_captures(
    req: LeadCaptureRequest,
) -> str | None:
    """Insert a row into the new ``lead_captures`` table via service_role.

    Returns the new row id on success, ``None`` on failure (fail-open).
    """
    from supabase_client import get_supabase, sb_execute

    sb = get_supabase()
    row = {
        "email": req.email.lower().strip(),
        "source": req.source,
        "sector": req.sector,
        "origin_url": req.origin_url,
        "metadata": {
            "uf": req.uf,
            "nome": req.nome,
            "empresa": req.empresa,
            "cnpj": req.cnpj,
            "telefone": req.telefone,
            "modalidade_interesse": req.modalidade_interesse,
            "mensagem": req.mensagem,
            "utm_source": req.utm_source,
            "utm_campaign": req.utm_campaign,
            "referer_path": req.referer_path,
        },
    }

    try:
        result = await _run_with_budget(
            sb_execute(
                sb.table("lead_captures").insert(row),
                category="write",
            ),
            budget=5.0,
            phase="route",
            source="lead_capture.insert",
        )
        rows = getattr(result, "data", None) or []
        if rows:
            return str(rows[0].get("id", ""))
    except Exception as exc:
        logger.warning("Failed to store lead_capture: %s", exc)

    return None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=LeadCaptureResponse,
    status_code=201,
)
async def capture_lead(
    req: LeadCaptureRequest,
    request: Request,
    _rl=Depends(require_rate_limit(3, 60)),  # 3 attempts/min per IP
) -> LeadCaptureResponse:
    """Store a lead capture from a non-authenticated visitor.

    - New sources (COPY-COP-006): stored in ``lead_captures`` table
    - Old sources (backward compat): stored in ``leads`` table
    - Rate limited to 3 requests/min per IP
    - Fail-open: returns success even if DB storage fails
    - Lead magnet PDF delivery enqueued for legacy sources (LEAD-MAGNET-001)

    Returns 201 on success.
    """
    inserted_id: str | None = None

    if req.source in NEW_SOURCES:
        inserted_id = await _store_in_lead_captures(req)
    else:
        # Legacy source — store in original leads table
        await _store_in_legacy_leads(req)

    # Enqueue lead magnet PDF delivery (best-effort, never blocks response)
    try:
        from email_service import EMAIL_ENABLED
        if EMAIL_ENABLED:
            from job_queue import get_arq_pool
            pool = get_arq_pool()
            if pool:
                await pool.enqueue_job(
                    "send_lead_magnet_job",
                    email=req.email.lower().strip(),
                    setor=req.sector,
                    uf=req.uf.upper() if req.uf else None,
                )
    except Exception:
        logger.warning("lead_magnet: failed to enqueue delivery job", exc_info=True)

    from leads.outbox import LeadOutboxError, accept_lead, receipt_for

    try:
        record = accept_lead(
            {
                "email": req.email,
                "nome": req.nome,
                "empresa": req.empresa,
                "telefone": req.telefone,
                "mensagem": req.mensagem,
                "source": req.source,
                "cta_id": req.cta_id,
                "route_family": req.route_family,
                "entity_type": req.entity_type,
                "entity_public_id": req.entity_public_id,
                "landing_url": req.landing_url or req.origin_url,
                "referrer": req.referrer or req.referer_path,
                "utm_source": req.utm_source,
                "utm_medium": req.utm_medium,
                "utm_campaign": req.utm_campaign,
                "correlation_id": req.correlation_id,
                "consent_version": req.consent_version,
            }
        )
    except LeadOutboxError as exc:
        logger.warning("lead_outbox_persist_failed")
        raise HTTPException(status_code=503, detail="lead_outbox_unavailable") from exc

    receipt = receipt_for(record)
    receipt_id = receipt["receipt_id"]
    handoff_state = receipt["handoff_state"]
    try:
        from metrics import INBOUND_LEAD_ACCEPTED

        INBOUND_LEAD_ACCEPTED.labels(
            family=req.route_family or "unknown",
            cta_id=req.cta_id or "none",
            state=handoff_state or "accepted",
        ).inc()
    except Exception:
        logger.info("lead_analytics_failed receipt=%s", receipt_id)

    return LeadCaptureResponse(
        success=True,
        id=inserted_id,
        receipt_id=receipt_id,
        handoff_state=handoff_state,
    )
