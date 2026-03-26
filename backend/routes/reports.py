"""PDF report generation routes.

Endpoints:
- POST /reports/diagnostico - Generate a PDF diagnostico report for a completed search
"""

import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import require_auth
from routes.search import get_background_results_async
import pdf_report
from viability import assess_batch

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])

# UUID-like pattern: 8-4-4-4-12 hex characters
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


# ============================================================================
# Request Models
# ============================================================================


class DiagnosticoRequest(BaseModel):
    """Request body for PDF diagnostico report generation."""

    search_id: str  # Reference to a completed search
    client_name: str | None = None  # Optional company name
    max_items: int = Field(default=20, ge=1, le=50)


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/reports/diagnostico")
async def generate_diagnostico(
    request: DiagnosticoRequest,
    user: dict = Depends(require_auth),
) -> StreamingResponse:
    """Generate a PDF diagnostico report for a completed search.

    Fetches the results from a previous search (by search_id), applies
    viability scoring if not already present, selects the top N opportunities,
    and streams a styled PDF back to the caller as a file download.

    Request Body:
        {
            "search_id": "uuid-of-completed-search",
            "client_name": "Empresa ABC Ltda",  // optional
            "max_items": 20                       // 1-50
        }

    Returns:
        PDF file as a streaming attachment:
        Content-Disposition: attachment; filename="diagnostico-<setor>-<date>.pdf"

    Errors:
        400 Bad Request: search_id is not a valid UUID
        404 Not Found: search not found or expired
        500 Internal Server Error: PDF generation failed
    """
    # 1. Validate search_id format
    if not _UUID_RE.match(request.search_id):
        raise HTTPException(
            status_code=400,
            detail="search_id inválido. Deve ser um UUID no formato xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.",
        )

    # 2. Fetch results from in-memory / Redis / ARQ cache
    results = await get_background_results_async(request.search_id)
    if results is None:
        raise HTTPException(
            status_code=404,
            detail="Análise não encontrada ou expirada. Refaça a análise.",
        )

    # 3. Extract licitacoes, resumo, and metadata
    # Results may be a dict (from Redis/ARQ) or a BuscaResponse-like object
    if isinstance(results, dict):
        licitacoes: list[dict] = results.get("licitacoes", [])
        resumo: dict = results.get("resumo", {})
        setor: str = results.get("setor", "")
        ufs_busca: list[str] = results.get("ufs", [])
        termos: list[str] = results.get("termos", [])
    else:
        # BuscaResponse Pydantic model
        licitacoes = [
            item.model_dump() if hasattr(item, "model_dump") else dict(item)
            for item in getattr(results, "licitacoes", [])
        ]
        resumo = (
            results.resumo.model_dump()
            if hasattr(getattr(results, "resumo", None), "model_dump")
            else dict(getattr(results, "resumo", {}))
        )
        setor = getattr(results, "setor", "")
        ufs_busca = list(getattr(results, "ufs", []))
        termos = list(getattr(results, "termos", []))  # noqa: F841

    # 4. Apply viability scores if not already present
    has_viability = any("_viability_score" in bid for bid in licitacoes)
    if licitacoes and not has_viability:
        logger.debug(
            f"Calculating viability for {len(licitacoes)} bids "
            f"(search_id={request.search_id[:8]})"
        )
        assess_batch(
            bids=licitacoes,
            ufs_busca=set(ufs_busca) if ufs_busca else set(),
        )

    # 5. Sort by viability score descending; take top max_items
    sorted_licitacoes = sorted(
        licitacoes,
        key=lambda b: b.get("_viability_score", 0.0),
        reverse=True,
    )[: request.max_items]

    logger.info(
        f"Generating diagnostico PDF: user={user['id'][:8]}, "
        f"search_id={request.search_id[:8]}, "
        f"items={len(sorted_licitacoes)}/{len(licitacoes)}, "
        f"setor={setor!r}"
    )

    # 6. Build search_metadata and generate PDF
    search_metadata = {
        "setor_name": setor,
        "ufs": ufs_busca,
        "date_from": results.get("date_from", "") if isinstance(results, dict) else getattr(results, "date_from", ""),
        "date_to": results.get("date_to", "") if isinstance(results, dict) else getattr(results, "date_to", ""),
        "total_raw": results.get("total_raw", 0) if isinstance(results, dict) else getattr(results, "total_raw", 0),
    }

    try:
        pdf_buffer = pdf_report.generate_diagnostico_pdf(
            licitacoes=sorted_licitacoes,
            resumo=resumo,
            search_metadata=search_metadata,
            client_name=request.client_name,
            max_items=request.max_items,
        )
        pdf_bytes = pdf_buffer.getvalue()
    except Exception as exc:
        logger.error(
            f"PDF generation failed for search_id={request.search_id[:8]}: "
            f"{type(exc).__name__}: {exc}"
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao gerar o relatório PDF. Tente novamente.",
        )

    # 7. Build filename and stream response
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    safe_setor = re.sub(r"[^\w-]", "-", setor.lower()) if setor else "licitacoes"
    filename = f"diagnostico-{safe_setor}-{date_str}.pdf"

    return StreamingResponse(
        content=iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
