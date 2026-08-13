"""Intel Report one-time purchase routes (#630).

Endpoints:
- POST /intel-reports/checkout   — Create Stripe one-time checkout session
- GET  /intel-reports/           — List user's Intel Report purchases
- GET  /intel-reports/{id}       — Poll purchase status
- GET  /intel-reports/{id}/download — Stream PDF (auth + ownership check)

NOTE: Stripe Products must be created manually in the Stripe Dashboard before
using price_data in production. The create_intel_report_checkout service function
uses inline price_data (no pre-created Price object needed for development/testing).

The intel_report_purchases table is created in migration #628.
"""

import logging
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from saas_commerce import require_saas_commerce
from fastapi.responses import StreamingResponse

from auth import require_auth
from database import get_db
from supabase_client import sb_execute
from schemas.intel_report import (
    IntelReportCheckoutRequest,
    IntelReportCheckoutResponse,
    IntelReportStatusResponse,
    IntelReportPurchase,
)
from services.billing import create_intel_report_checkout as _create_checkout

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intel-reports", tags=["intel_reports"])


@router.post("/checkout", response_model=IntelReportCheckoutResponse)
async def create_intel_report_checkout(
    body: IntelReportCheckoutRequest,
    user: dict = Depends(require_auth),
    _frozen=Depends(require_saas_commerce),
):
    """Create a Stripe Checkout session for an Intel Report one-time purchase.

    product_type:
        - "cnpj"       → R$197.00 — Company analysis report (INTEL-REPORT-001)
        - "sector_uf"  → R$147.00 — Sector/UF market report (INTEL-REPORT-002)

    entity_key:
        - For cnpj:       the CNPJ string (e.g. "12345678000195")
        - For sector_uf:  "sector:uf" (e.g. "limpeza:SP")

    Returns checkout_url (redirect user) and session_id (for polling).
    """
    import stripe as stripe_lib

    try:
        result = _create_checkout(
            product_type=body.product_type,
            entity_key=body.entity_key,
            user_id=user["id"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except stripe_lib.error.InvalidRequestError as exc:
        stripe_request_id = getattr(exc, "request_id", None)
        logger.error(
            f"Stripe InvalidRequestError on Intel Report checkout: "
            f"user_id={user['id'][:8]} product_type={body.product_type} "
            f"stripe_request_id={stripe_request_id} error={exc}"
        )
        raise HTTPException(
            status_code=400,
            detail="Não foi possível iniciar o checkout. Verifique os dados e tente novamente.",
        )
    except stripe_lib.error.StripeError as exc:
        logger.error(f"Stripe error on Intel Report checkout: {exc}")
        raise HTTPException(
            status_code=503,
            detail="Serviço de pagamento temporariamente indisponível. Tente novamente em instantes.",
        )

    return IntelReportCheckoutResponse(
        checkout_url=result["checkout_url"],
        session_id=result["session_id"],
    )


@router.get("/", response_model=List[IntelReportPurchase])
async def list_intel_report_purchases(
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """List all Intel Report purchases for the authenticated user."""
    result = await sb_execute(
        db.table("intel_report_purchases")
        .select("id, user_id, product_type, entity_key, status, pdf_url, created_at, expires_at")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
    )

    return result.data or []


@router.get("/{purchase_id}", response_model=IntelReportStatusResponse)
async def get_intel_report_status(
    purchase_id: str,
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """Poll status of an Intel Report purchase.

    Frontend uses this endpoint after being redirected back from Stripe
    (/intel-reports/{CHECKOUT_SESSION_ID}?status=processing).
    Poll until status is "ready" or "failed".

    Returns:
    - 404 if purchase does not exist
    - 403 if purchase belongs to a different user
    """
    # First: look up by id only (without user_id filter) to distinguish 404 vs 403
    result = await sb_execute(
        db.table("intel_report_purchases")
        .select("id, user_id, status, pdf_url, expires_at")
        .eq("id", purchase_id)
        .single()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Compra não encontrada.",
        )

    if result.data["user_id"] != user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: esta compra não pertence ao usuário autenticado.",
        )

    purchase = result.data
    return IntelReportStatusResponse(
        status=purchase["status"],
        pdf_url=purchase.get("pdf_url"),
        expires_at=purchase.get("expires_at"),
    )


@router.get("/{purchase_id}/download", response_model=None)
async def download_intel_report(
    purchase_id: str,
    user: dict = Depends(require_auth),
    db=Depends(get_db),
):
    """Stream the Intel Report PDF.

    Requires:
    - Authentication
    - Ownership: purchase must belong to the authenticated user
    - Status: purchase must be "ready" (pdf_url present)

    Returns:
    - 401 if not authenticated
    - 404 if purchase does not exist
    - 403 if purchase belongs to a different user
    - 400 if purchase status is not "ready"
    - PDF stream if all checks pass
    """
    import httpx

    # First: look up by id only (without user_id filter) to distinguish 404 vs 403
    result = await sb_execute(
        db.table("intel_report_purchases")
        .select("id, user_id, status, pdf_url")
        .eq("id", purchase_id)
        .single()
    )

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Compra não encontrada.",
        )

    if result.data["user_id"] != user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: este relatório não pertence ao usuário autenticado.",
        )

    purchase = result.data

    if purchase["status"] != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Relatório ainda não disponível (status={purchase['status']}). "
                   "Aguarde o processamento ou tente novamente em instantes.",
        )

    pdf_url = purchase.get("pdf_url")
    if not pdf_url:
        raise HTTPException(
            status_code=404,
            detail="URL do PDF não encontrada. Entre em contato com o suporte.",
        )

    # Stream PDF from storage URL
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(pdf_url)
            response.raise_for_status()
            pdf_bytes = response.content
    except httpx.HTTPStatusError as exc:
        logger.error(f"Failed to fetch Intel Report PDF from storage: {exc}")
        raise HTTPException(status_code=502, detail="Erro ao baixar o relatório. Tente novamente.")
    except Exception as exc:
        logger.error(f"Unexpected error fetching Intel Report PDF: {exc}")
        raise HTTPException(status_code=500, detail="Erro interno ao baixar o relatório.")

    filename = f"intel-report-{purchase_id[:8]}.pdf"

    return StreamingResponse(
        content=iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
