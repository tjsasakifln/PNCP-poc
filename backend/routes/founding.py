"""STORY-BIZ-001 + BIZ-FOUND-002 + #783: Founding customer checkout + canonical policy.

Endpoints:
- ``POST /v1/founding/checkout`` — qualifying form -> Stripe Checkout Session.
- ``GET  /v1/founding/availability`` — public seat counter / countdown feed.

BIZ-FOUND-002 changes:
- Pre-checkout, the route invokes ``public.check_founding_availability()`` RPC.
  The RPC takes ``SELECT FOR UPDATE`` on the founding_policy row + counts
  completed leads in one atomic step (race guard #1).
- When the RPC returns ``available=false`` we respond with 410 Gone and a
  structured ``error_code`` so the frontend can render the right message
  without parsing free-form text.
- The new ``GET /v1/founding/availability`` endpoint is anonymous (no auth)
  and used by the landing-page seat counter + countdown timer.

#783 (v2 lifetime pivot):
- ``mode='payment'`` one-time R$997 BRL via ``FOUNDING_ONE_TIME_PRICE_ID``.
- Adds ``payment_method_types=['card', 'boleto']``.
- Removes coupon / discounts block entirely.
- Expands session metadata: ``offer_version``, ``offer_mode``,
  ``price_brl_cents``, ``checkout_source``.
- ``FoundingCheckoutResponse`` gains ``payment_mode='lifetime'``.
- ``FOUNDING_ONE_TIME_PRICE_ID`` must be set in env; route returns 500 if
  missing so misconfiguration is caught immediately (fail-closed).
"""

from __future__ import annotations

import logging
import os

from pipeline.budget import _run_with_budget
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field, field_validator

from metrics import FOUNDING_CHECKOUTS_TOTAL
from rate_limiter import require_rate_limit
from saas_commerce import require_saas_commerce
from supabase_client import get_supabase, sb_execute


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/founding", tags=["founding"])


# ---------------------------------------------------------------------------
# v2 one-time price — env var set by operator after running
# scripts/create_founding_lifetime_price.py
# NOTE: read at request-time (not module-load-time) to avoid import-order
# freeze in tests and environments where the var is set after module import.
# ---------------------------------------------------------------------------


class FoundingCheckoutRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=320)
    nome: str = Field(..., min_length=2, max_length=200)
    cnpj: str = Field(..., min_length=11, max_length=18)
    razao_social: str | None = Field(default=None, max_length=300)
    motivo: str = Field(..., min_length=140, max_length=1000)

    @field_validator("cnpj")
    @classmethod
    def _validate_cnpj(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos")
        if not _is_valid_cnpj_check_digits(digits):
            raise ValueError("CNPJ inválido (dígito verificador)")
        return digits

    @field_validator("email")
    @classmethod
    def _validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@", 1)[1]:
            raise ValueError("Email inválido")
        return v


class FoundingCheckoutResponse(BaseModel):
    checkout_url: str
    lead_id: str
    payment_mode: str = Field(
        default="lifetime",
        description="'lifetime' for one-time payment (v2) or 'subscription' for legacy",
    )


class FoundingCheckoutStatusResponse(BaseModel):
    """Response model for GET /v1/founding/checkout/status."""

    status: str
    payment_status: str


class FoundingAvailabilityResponse(BaseModel):
    """Public availability snapshot for landing-page seat counter + countdown."""

    available: bool
    seats_total: int
    seats_remaining: int
    seats_taken: int
    deadline_at: str | None
    paused: bool
    reason: str
    coupon_code: str
    discount_pct: int
    offer_mode: str = Field(default="lifetime", description="'lifetime' or 'subscription'")
    price_brl_cents: int = Field(default=99700, description="Price in BRL cents")


class FoundingSessionStatusResponse(BaseModel):
    """Enriched session status for the /fundadores/obrigado page (#865).

    Returns masked email, has_account, and invite_sent so the frontend can
    render the correct post-purchase CTA without exposing full PII.
    """

    status: str = Field(description="'completed' | 'pending' | 'not_found'")
    email: str = Field(description="Masked email (2 chars before @ + **** + domain).")
    has_account: bool = Field(description="True if a profiles row exists for this email.")
    invite_sent: bool = Field(description="True if magic_link_sent_at IS NOT NULL.")


def _is_valid_cnpj_check_digits(cnpj: str) -> bool:
    """Validate Brazilian CNPJ check digits. `cnpj` must be 14 digits already."""
    if len(cnpj) != 14 or not cnpj.isdigit():
        return False
    if cnpj == cnpj[0] * 14:
        return False

    def _compute(digits: str, weights: list[int]) -> int:
        total = sum(int(d) * w for d, w in zip(digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6] + w1
    d1 = _compute(cnpj[:12], w1)
    if d1 != int(cnpj[12]):
        return False
    d2 = _compute(cnpj[:13], w2)
    return d2 == int(cnpj[13])


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _mask_email(email: str) -> str:
    """Return a masked email exposing only the first 2 chars of the local part.

    Example: ``mariaalvabaron@gmail.com`` -> ``ma****@gmail.com``
    Returns the input unchanged if it does not contain ``@`` (malformed).
    """
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    return f"{local[:2]}****@{domain}"


async def _already_registered(sb, email: str) -> bool:
    """Return True if the email already owns a profile. Best-effort, non-blocking."""
    try:
        res = await sb_execute(
            sb.table("profiles").select("id").eq("email", email).limit(1)
        )
        return bool(res.data)
    except Exception as e:
        logger.warning(f"founding: profile lookup failed (non-blocking): {e}")
        return False


async def _get_session_lead(sb, session_id: str) -> dict | None:
    """Return founding_leads row for the given Stripe checkout session ID.

    Returns ``None`` when not found. Raises on unexpected DB errors.
    """
    res = await sb_execute(
        sb.table("founding_leads")
        .select("email, checkout_status, magic_link_sent_at, created_at")
        .eq("checkout_session_id", session_id)
        .limit(1)
    )
    rows = res.data or []
    return rows[0] if rows else None


async def _check_availability(sb) -> dict[str, Any]:
    """Call ``check_founding_availability()`` RPC; return normalized dict.

    On any DB error returns ``available=False`` with reason ``'unavailable'``
    so the route fails closed (never accidentally over-sell the cohort).
    """
    try:
        res = await sb_execute(sb.rpc("check_founding_availability"), category="rpc")
        rows = getattr(res, "data", None) or []
        if not rows:
            logger.warning("founding: check_founding_availability returned empty")
            return {
                "available": False,
                "seats_total": 0,
                "seats_remaining": 0,
                "deadline_at": None,
                "paused": False,
                "reason": "unavailable",
                "offer_mode": "lifetime",
                "price_brl_cents": 99700,
            }
        row = rows[0] if isinstance(rows, list) else rows
        return {
            "available": bool(row.get("available")),
            "seats_total": int(row.get("seats_total") or 0),
            "seats_remaining": int(row.get("seats_remaining") or 0),
            "deadline_at": row.get("deadline_at"),
            "paused": bool(row.get("paused")),
            "reason": str(row.get("reason") or "unavailable"),
            "offer_mode": str(row.get("offer_mode") or "lifetime"),
            "price_brl_cents": int(row.get("price_brl_cents") or 99700),
        }
    except Exception as e:
        logger.error(f"founding: check_founding_availability RPC failed: {e}")
        return {
            "available": False,
            "seats_total": 0,
            "seats_remaining": 0,
            "deadline_at": None,
            "paused": False,
            "reason": "unavailable",
            "offer_mode": "lifetime",
            "price_brl_cents": 99700,
        }


def _user_message_for_reason(reason: str) -> str:
    """Map RPC reason enum -> user-facing Portuguese message."""
    mapping = {
        "founding_cap_reached": (
            "As 50 vagas founding já foram preenchidas. Obrigado pelo interesse — "
            "entre em contato para entrar na lista de espera."
        ),
        "founding_deadline_passed": (
            "O período de inscrição founding (até 30/05/2026) terminou. O plano "
            "regular SmartLic Pro continua disponível em /pricing."
        ),
        "founding_paused": (
            "As inscrições founding estão temporariamente pausadas. Tente novamente em algumas horas."
        ),
        "founding_disabled": (
            "O programa founding não está aceitando novas inscrições no momento."
        ),
        "founding_policy_missing": (
            "Configuração founding indisponível. Tente novamente em instantes."
        ),
        "unavailable": (
            "Não foi possível validar disponibilidade founding agora. Tente novamente em instantes."
        ),
    }
    return mapping.get(reason, mapping["unavailable"])


@router.get("/availability", response_model=FoundingAvailabilityResponse)
async def founding_availability(response: Response) -> Any:
    """Public seat counter + countdown feed.

    No auth — the landing page calls this anonymously to render the
    countdown and the X/50 seat counter. Falls open with ``available=False``
    on transient DB error so the CTA is disabled rather than over-selling.
    """
    from config.features import get_feature_flag

    if not get_feature_flag("FOUNDERS_OFFER_ENABLED"):
        return FoundingAvailabilityResponse(
            available=False,
            seats_total=0,
            seats_remaining=0,
            seats_taken=0,
            deadline_at=None,
            paused=False,
            reason="founders_offer_disabled",
            coupon_code="",
            discount_pct=0,
            offer_mode="lifetime",
            price_brl_cents=99700,
        )

    sb = get_supabase()
    snapshot = await _run_with_budget(
        _check_availability(sb),
        budget=5.0,  # 2026-05-31: raised from 3s → 5s (Sentry #8-#10: 115 timeout events in 14d).
                      # check_founding_availability() uses SELECT FOR UPDATE — under concurrent
                      # landing-page traffic the lock queue can push latency past 3s.
        phase="route",
        source="founding.availability",
        fallback={
            "available": False,
            "seats_total": 0,
            "seats_remaining": 0,
            "deadline_at": None,
            "paused": False,
            "reason": "unavailable",
            "offer_mode": "lifetime",
            "price_brl_cents": 99700,
        },
    )
    # Cache-Control for Googlebot fanout — short-lived public cache so the
    # seat counter stays accurate but bursty crawls don't hammer the RPC.
    response.headers["Cache-Control"] = "public, s-maxage=30"

    seats_total = snapshot["seats_total"]
    seats_remaining = snapshot["seats_remaining"]
    seats_taken = max(0, seats_total - seats_remaining)
    deadline_iso: str | None = None
    if snapshot["deadline_at"]:
        deadline_iso = (
            snapshot["deadline_at"].isoformat()
            if hasattr(snapshot["deadline_at"], "isoformat")
            else str(snapshot["deadline_at"])
        )

    return FoundingAvailabilityResponse(
        available=snapshot["available"],
        seats_total=seats_total,
        seats_remaining=seats_remaining,
        seats_taken=seats_taken,
        deadline_at=deadline_iso,
        paused=snapshot["paused"],
        reason=snapshot["reason"],
        coupon_code="",
        discount_pct=0,
        offer_mode=snapshot.get("offer_mode", "lifetime"),
        price_brl_cents=snapshot.get("price_brl_cents", 99700),
    )


@router.get("/checkout/status", response_model=FoundingCheckoutStatusResponse)
async def founding_checkout_status(
    session_id: str = Query(..., min_length=8),
    _rl=Depends(require_rate_limit(30, 60)),
) -> Any:
    """Return Stripe checkout session status for the founding purchase confirmation page.

    No auth required — Stripe ``cs_*`` session IDs are long random tokens that
    are unguessable. Only ``status`` and ``payment_status`` are returned so no
    PII is exposed. Used by ``/fundadores/obrigado`` to poll until payment is
    confirmed (max 20 × 3 s = 60 s).
    """
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        logger.warning("founding: checkout/status called but STRIPE_SECRET_KEY not set")
        return FoundingCheckoutStatusResponse(status="unknown", payment_status="unpaid")

    try:
        import stripe as stripe_lib  # local import to keep module testable without Stripe

        session = stripe_lib.checkout.Session.retrieve(
            session_id,
            api_key=stripe_key,
        )
        return FoundingCheckoutStatusResponse(
            status=session.status,
            payment_status=session.payment_status,
        )
    except Exception as exc:
        logger.warning(f"founding: checkout/status retrieval failed — session_id_prefix={session_id[:8]} err={exc}")
        return FoundingCheckoutStatusResponse(status="unknown", payment_status="unpaid")


@router.get("/session-status", response_model=FoundingSessionStatusResponse)
async def founding_session_status(
    session_id: str = Query(..., min_length=8),
    _rl=Depends(require_rate_limit(10, 60)),
) -> Any:
    """Enriched session status for the /fundadores/obrigado confirmation page (#865).

    No auth required — Stripe ``cs_*`` session IDs are long random opaque tokens.
    Returns masked email, ``has_account``, and ``invite_sent`` so the frontend
    can render the right post-purchase CTA without polling Stripe directly.

    Expiry guard: sessions with checkout_status != 'completed' that are older
    than 24 h return ``status='pending'`` to prevent infinite polling.
    """
    from datetime import datetime, timezone

    sb = get_supabase()

    try:
        lead = await _run_with_budget(
            _get_session_lead(sb, session_id),
            budget=5.0,
            phase="route",
            source="founding.session_status",
        )
    except Exception as exc:
        logger.warning(
            f"founding: session-status DB error — session_id_prefix={session_id[:8]} err={exc}"
        )
        raise HTTPException(
            status_code=503,
            detail="Erro temporário ao consultar status. Tente novamente.",
        )

    if lead is None:
        return FoundingSessionStatusResponse(
            status="not_found",
            email="",
            has_account=False,
            invite_sent=False,
        )

    email: str = lead.get("email", "") or ""
    checkout_status: str = lead.get("checkout_status", "") or ""
    magic_link_sent_at = lead.get("magic_link_sent_at")
    created_at_raw = lead.get("created_at")

    # Status resolution — completed is always returned as-is.
    # Non-completed leads older than 24 h are capped at "pending" to stop polling.
    status: str
    if checkout_status == "completed":
        status = "completed"
    else:
        age_expired = False
        if created_at_raw:
            try:
                created_dt = (
                    datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
                    if isinstance(created_at_raw, str)
                    else created_at_raw
                )
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                if (datetime.now(tz=timezone.utc) - created_dt).total_seconds() > 86400:
                    age_expired = True
            except Exception:
                pass  # unparseable date — leave age_expired=False (safe)
        status = "pending" if age_expired else (checkout_status or "pending")

    # has_account — non-blocking profile lookup
    has_account = False
    if email:
        try:
            has_account = await _already_registered(sb, email)
        except Exception as exc:
            logger.warning(
                f"founding: session-status profile check failed (non-blocking): {exc}"
            )

    invite_sent = bool(magic_link_sent_at)
    masked = _mask_email(email) if email else ""

    logger.info(
        f"founding: session-status — session_id_prefix={session_id[:8]} "
        f"status={status} has_account={has_account} invite_sent={invite_sent}"
    )

    return FoundingSessionStatusResponse(
        status=status,
        email=masked,
        has_account=has_account,
        invite_sent=invite_sent,
    )


@router.post("/checkout", response_model=FoundingCheckoutResponse)
async def founding_checkout(
    payload: FoundingCheckoutRequest,
    request: Request,
    _rl=Depends(require_rate_limit(3, 3600)),
    _frozen=Depends(require_saas_commerce),
) -> Any:
    """Create a founding-customer Stripe Checkout Session (v2 one-time payment).

    BIZ-FOUND-002 gate:
    - Calls ``check_founding_availability()`` BEFORE creating the lead row.
    - On ``available=false`` returns 410 Gone with structured ``error_code`` +
      ``error_reason`` so the frontend can render the right copy.

    #783 changes:
    - Uses ``mode='payment'`` (one-time) with ``FOUNDING_ONE_TIME_PRICE_ID``.
    - Accepts ``card`` and ``boleto`` payment methods.
    - No coupon / discounts applied.
    - Expanded metadata: ``offer_version``, ``offer_mode``, ``price_brl_cents``,
      ``checkout_source`` (resolved from ``src`` or ``utm_source`` query param).

    Side effects (when available):
    - Inserts a ``founding_leads`` row with ``checkout_status='pending'``.
    - Subsequent webhook events (``checkout.session.completed`` / ``expired``)
      update it. The webhook also re-checks availability for race guard
      (handled in webhooks.handlers.founding).
    """
    from config.features import get_feature_flag

    if not get_feature_flag("FOUNDERS_OFFER_ENABLED"):
        raise HTTPException(
            status_code=410,
            detail={
                "message": "Oferta Fundadores encerrada.",
                "error_code": "founders_offer_disabled",
            },
        )

    sb = get_supabase()

    # BIZ-FOUND-002 gate — atomic cap + deadline + paused check.
    # Evaluated BEFORE Stripe config checks so that 410 responses are always
    # returned correctly even in environments without Stripe configured (e.g. tests).
    # 2026-05-31: raised from 3s → 5s to match availability endpoint budget.
    # No fallback — checkout MUST have an authoritative answer; failing open
    # (available=True) would over-sell the cohort.
    snapshot = await _run_with_budget(
        _check_availability(sb),
        budget=5.0,
        phase="route",
        source="founding.checkout_gate",
    )
    if not snapshot["available"]:
        reason = snapshot["reason"]
        logger.info(
            f"founding: checkout rejected — reason={reason} "
            f"seats_taken={snapshot['seats_total'] - snapshot['seats_remaining']}/"
            f"{snapshot['seats_total']}"
        )
        raise HTTPException(
            status_code=410,
            detail={
                "message": _user_message_for_reason(reason),
                "error_code": reason,
                "seats_total": snapshot["seats_total"],
                "seats_remaining": snapshot["seats_remaining"],
            },
        )

    if await _already_registered(sb, payload.email):
        raise HTTPException(
            status_code=409,
            detail="Este email já possui conta SmartLic. Faça login para gerenciar sua assinatura.",
        )

    import stripe as stripe_lib

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        logger.error("founding: STRIPE_SECRET_KEY not configured")
        raise HTTPException(status_code=500, detail="Erro ao processar pagamento. Tente novamente.")

    founding_price_id = os.getenv("FOUNDING_ONE_TIME_PRICE_ID", "")
    if not founding_price_id:
        logger.error("founding: FOUNDING_ONE_TIME_PRICE_ID not configured")
        raise HTTPException(
            status_code=500,
            detail="Configuração de preço founding indisponível. Contate o suporte.",
        )

    # Resolve checkout_source from query params (src takes priority over utm_source)
    checkout_source = (
        request.query_params.get("src")
        or request.query_params.get("utm_source")
        or "direct"
    )

    lead_row = {
        "email": payload.email,
        "nome": payload.nome,
        "cnpj": payload.cnpj,
        "razao_social": payload.razao_social,
        "motivo": payload.motivo,
        "ip_address": _client_ip(request),
        "user_agent": request.headers.get("user-agent", "")[:500],
    }

    lead_insert = await _run_with_budget(
        sb_execute(sb.table("founding_leads").insert(lead_row), category="write"),
        budget=5.0,
        phase="route",
        source="founding.checkout.insert_lead",
    )
    lead_record = (lead_insert.data or [{}])[0]
    lead_id = lead_record.get("id")
    if not lead_id:
        logger.error("founding: Supabase insert returned no id")
        raise HTTPException(status_code=500, detail="Erro ao registrar sua solicitação.")

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    offer_mode = snapshot.get("offer_mode", "lifetime")
    price_brl_cents = snapshot.get("price_brl_cents", 99700)

    session_params = {
        "payment_method_types": ["card", "boleto"],
        "line_items": [{"price": founding_price_id, "quantity": 1}],
        "mode": "payment",
        "success_url": f"{frontend_url}/fundadores/obrigado?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{frontend_url}/fundadores?cancelled=true",
        "customer_email": payload.email,
        "metadata": {
            "source": "founding",
            "offer_version": "v2_lifetime",
            "offer_mode": offer_mode,
            "price_brl_cents": str(price_brl_cents),
            "checkout_source": checkout_source,
            "founding_lead_id": lead_id,
            "cnpj": payload.cnpj,
        },
    }

    try:
        session = stripe_lib.checkout.Session.create(**session_params, api_key=stripe_key)
    except stripe_lib.error.InvalidRequestError as e:
        logger.error(
            f"founding: Stripe InvalidRequestError — cnpj={payload.cnpj} "
            f"lead_id={lead_id} err={e}"
        )
        raise HTTPException(
            status_code=400,
            detail="Não foi possível iniciar o checkout. Verifique os dados e tente novamente.",
        )
    except stripe_lib.error.StripeError as e:
        logger.error(f"founding: Stripe error — lead_id={lead_id} err={e}")
        raise HTTPException(
            status_code=503,
            detail="Serviço de pagamento temporariamente indisponível. Tente novamente em instantes.",
        )

    try:
        _session_id = session.id

        await _run_with_budget(
            sb_execute(
                sb.table("founding_leads")
                .update({"checkout_session_id": _session_id})
                .eq("id", lead_id),
                category="write",
            ),
            budget=5.0,
            phase="route",
            source="founding.checkout.update_session_id",
        )
    except Exception as e:
        logger.warning(f"founding: failed to persist session_id — lead_id={lead_id} err={e}")

    logger.info(
        f"founding: checkout session created — lead_id={lead_id} "
        f"session_id={session.id} email={payload.email} cnpj={payload.cnpj[:4]}*** "
        f"offer_mode={offer_mode} checkout_source={checkout_source}"
    )

    FOUNDING_CHECKOUTS_TOTAL.labels(status="started").inc()

    return FoundingCheckoutResponse(
        checkout_url=session.url,
        lead_id=lead_id,
        payment_mode="lifetime",
    )
