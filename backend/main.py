"""
BidIQ Uniformes POC - Backend API

FastAPI application for searching and analyzing uniform procurement bids
from Brazil's PNCP (Portal Nacional de Contratações Públicas).

This API provides endpoints for:
- Searching procurement opportunities by state and date range
- Filtering results by keywords and value thresholds
- Generating Excel reports with formatted data
- Creating AI-powered executive summaries (GPT-4.1-nano)
"""

import base64
import logging
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from config import setup_logging
from schemas import BuscaRequest, BuscaResponse
from pncp_client import PNCPClient
from exceptions import PNCPAPIError, PNCPRateLimitError
from filter import filter_batch
from excel import create_excel
from llm import gerar_resumo, gerar_resumo_fallback

# Configure structured logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="BidIQ Uniformes API",
    description=(
        "API para busca e análise de licitações de uniformes no PNCP. "
        "Permite filtrar oportunidades por estado, valor e keywords, "
        "gerando relatórios Excel e resumos executivos via IA."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Configuration
# NOTE: In production, restrict allow_origins to specific domains
# Example: allow_origins=["https://bidiq-uniformes.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for POC (TODO: restrict in production)
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only methods we use
    allow_headers=["*"],  # Allow all headers for development
)

logger.info(
    "FastAPI application initialized — PORT=%s",
    os.getenv("PORT", "8000"),
)


@app.get("/")
async def root():
    """
    API root endpoint - provides navigation to documentation.

    Returns:
        dict: API information and links to documentation endpoints
    """
    return {
        "name": "BidIQ Uniformes API",
        "version": "0.2.0",
        "description": "API para busca de licitações de uniformes no PNCP",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "openapi": "/openapi.json",
        },
        "status": "operational",
    }


@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring and load balancers.

    Provides lightweight service health verification without triggering
    heavy operations (PNCP API calls, LLM processing, etc.). Designed
    for use by orchestrators (Docker, Kubernetes), load balancers, and
    uptime monitoring tools.

    Returns:
        dict: Service health status with timestamp and version

    Response Schema:
        - status (str): "healthy" when service is operational
        - timestamp (str): Current server time in ISO 8601 format
        - version (str): API version from app configuration

    Example:
        >>> response = await health()
        >>> response
        {
            'status': 'healthy',
            'timestamp': '2026-01-25T23:15:42.123456',
            'version': '0.2.0'
        }

    HTTP Status Codes:
        - 200: Service is healthy and operational
        - 503: Service is degraded (future: dependency checks fail)
    """
    from datetime import datetime

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version,
    }


@app.post("/buscar", response_model=BuscaResponse)
async def buscar_licitacoes(request: BuscaRequest):
    """
    Main search endpoint - orchestrates the complete pipeline.

    Workflow:
        1. Fetch bids from PNCP API (with automatic pagination)
        2. Apply sequential filters (UF, value, keywords, status)
        3. Generate executive summary via GPT-4.1-nano (with fallback)
        4. Create formatted Excel report
        5. Return summary + base64-encoded Excel

    Args:
        request: BuscaRequest with ufs, data_inicial, data_final

    Returns:
        BuscaResponse with resumo, excel_base64, total_raw, total_filtrado

    Raises:
        HTTPException 502: PNCP API error (network, timeout, invalid response)
        HTTPException 503: PNCP rate limit exceeded (retry after N seconds)
        HTTPException 500: Internal server error (unexpected failure)

    Example:
        >>> request = BuscaRequest(
        ...     ufs=["SP", "RJ"],
        ...     data_inicial="2025-01-01",
        ...     data_final="2025-01-31"
        ... )
        >>> response = await buscar_licitacoes(request)
        >>> response.total_filtrado
        15
    """
    logger.info(
        "Starting procurement search",
        extra={
            "ufs": request.ufs,
            "data_inicial": request.data_inicial,
            "data_final": request.data_final,
        },
    )

    try:
        # Step 1: Fetch from PNCP (generator → list for reusability in filter + LLM)
        logger.info("Fetching bids from PNCP API")
        client = PNCPClient()
        licitacoes_raw = list(
            client.fetch_all(
                data_inicial=request.data_inicial,
                data_final=request.data_final,
                ufs=request.ufs,
            )
        )
        logger.info(f"Fetched {len(licitacoes_raw)} raw bids from PNCP")

        # Step 2: Apply filtering (fail-fast sequential: UF → value → keywords → status)
        logger.info("Applying filters to raw bids")
        licitacoes_filtradas, stats = filter_batch(
            licitacoes_raw,
            ufs_selecionadas=set(request.ufs),
            valor_min=50_000.0,  # PRD Section 1.2: R$ 50k minimum
            valor_max=5_000_000.0,  # PRD Section 1.2: R$ 5M maximum
        )
        logger.info(
            f"Filtering complete: {len(licitacoes_filtradas)}/{len(licitacoes_raw)} bids passed",
            extra={"rejection_stats": stats},
        )

        # Step 3: Generate executive summary via LLM (with automatic fallback)
        logger.info("Generating executive summary")
        try:
            resumo = gerar_resumo(licitacoes_filtradas)
            logger.info("LLM summary generated successfully")
        except Exception as e:
            logger.warning(
                f"LLM generation failed, using fallback mechanism: {e}",
                exc_info=True,
            )
            resumo = gerar_resumo_fallback(licitacoes_filtradas)
            logger.info("Fallback summary generated successfully")

        # Step 4: Generate Excel report
        logger.info("Generating Excel report")
        excel_buffer = create_excel(licitacoes_filtradas)
        excel_base64 = base64.b64encode(excel_buffer.read()).decode("utf-8")
        logger.info(f"Excel report generated ({len(excel_base64)} base64 chars)")

        # Step 5: Return response
        response = BuscaResponse(
            resumo=resumo,
            excel_base64=excel_base64,
            total_raw=len(licitacoes_raw),
            total_filtrado=len(licitacoes_filtradas),
        )

        logger.info(
            "Search completed successfully",
            extra={
                "total_raw": response.total_raw,
                "total_filtrado": response.total_filtrado,
                "valor_total": resumo.valor_total,
            },
        )

        return response

    except PNCPRateLimitError as e:
        logger.error(f"PNCP rate limit exceeded: {e}", exc_info=True)
        # Extract Retry-After header if available
        retry_after = getattr(e, "retry_after", 60)  # Default 60s if not provided
        raise HTTPException(
            status_code=503,
            detail=f"PNCP API rate limit exceeded. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    except PNCPAPIError as e:
        logger.error(f"PNCP API error: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=f"Error communicating with PNCP API: {str(e)}",
        )

    except Exception:
        logger.exception("Internal server error during procurement search")
        # Sanitize error message (don't expose internal details)
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again later.",
        )
