"""routes/export.py — Per-edital PDF export endpoint.

STORY-447: Generates a 1-page executive PDF for a single bid/edital.
Uses pdf_generator_edital.generate_edital_pdf() synchronously (wrapped in
asyncio.to_thread) with a 10-second timeout.
"""

import asyncio
import logging
import re
import unicodedata
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from auth import require_auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["export"])

_ILLEGAL_FILENAME_RE = re.compile(r"[^\w\s\-]")


def _safe_filename(text: str, max_len: int = 60) -> str:
    """Normalise text into a safe ASCII filename fragment."""
    ascii_text = unicodedata.normalize("NFKD", text[:max_len]).encode("ascii", "ignore").decode("ascii")
    clean = _ILLEGAL_FILENAME_RE.sub("", ascii_text).strip()
    return clean.replace(" ", "_") or "edital"


# ---------------------------------------------------------------------------
# Request model
# ---------------------------------------------------------------------------

class PdfEditalRequest(BaseModel):
    # Core bid fields
    objeto: str
    orgao: str
    uf: str
    municipio: Optional[str] = None
    valor: Optional[float] = None
    data_encerramento: Optional[str] = None
    data_publicacao: Optional[str] = None
    modalidade: Optional[str] = None
    link: Optional[str] = None
    numero_compra: Optional[str] = None
    pncp_id: Optional[str] = None
    # Viability
    viability_level: Optional[str] = None
    viability_score: Optional[float] = None
    viability_factors: Optional[dict] = None
    # AI summary (optional — from BuscaResult.resumo)
    resumo_executivo: Optional[str] = None
    recomendacao: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/pdf")
async def export_edital_pdf(
    request: PdfEditalRequest,
    user: dict = Depends(require_auth),
) -> Response:
    """Generate and return a 1-page A4 PDF for a single bid.

    Trial users get a watermark footer.
    Synchronous generation wrapped in asyncio.to_thread with 10s timeout.
    """
    plan_type = user.get("plan_type", "free_trial")

    bid_data = request.model_dump()

    try:
        from pdf_generator_edital import generate_edital_pdf

        pdf_bytes = await asyncio.wait_for(
            asyncio.to_thread(generate_edital_pdf, bid_data, plan_type),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "STORY-447: PDF generation timeout for user %s / objeto=%s",
            str(user.get("id", "?"))[:8],
            request.objeto[:40],
        )
        raise HTTPException(
            status_code=503,
            detail="A geração do PDF excedeu o tempo limite. Tente novamente.",
        )
    except Exception as e:
        logger.error(
            "STORY-447: PDF generation error for user %s: %s",
            str(user.get("id", "?"))[:8],
            e,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao gerar PDF. Tente novamente.",
        )

    safe_title = _safe_filename(request.objeto)
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")
    filename = f"SmartLic_{safe_title}_{today}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
