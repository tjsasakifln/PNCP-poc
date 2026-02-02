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
from schemas import BuscaRequest, BuscaResponse, FilterStats, ResumoLicitacoes
from pncp_client import PNCPClient
from exceptions import PNCPAPIError, PNCPRateLimitError
from filter import filter_batch, remove_stopwords
from excel import create_excel
from llm import gerar_resumo, gerar_resumo_fallback
from sectors import get_sector, list_sectors

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


@app.get("/setores")
async def listar_setores():
    """Return available procurement sectors for frontend dropdown."""
    return {"setores": list_sectors()}


@app.get("/debug/pncp-test")
async def debug_pncp_test():
    """Diagnostic: test if PNCP API is reachable from this server."""
    import time as t
    from datetime import date, timedelta

    start = t.time()
    try:
        client = PNCPClient()
        hoje = date.today()
        tres_dias = hoje - timedelta(days=3)
        response = client.fetch_page(
            data_inicial=tres_dias.strftime("%Y-%m-%d"),
            data_final=hoje.strftime("%Y-%m-%d"),
            modalidade=6,
            pagina=1,
            tamanho=10,
        )
        elapsed = int((t.time() - start) * 1000)
        return {
            "success": True,
            "total_registros": response.get("totalRegistros", 0),
            "items_returned": len(response.get("data", [])),
            "elapsed_ms": elapsed,
        }
    except Exception as e:
        elapsed = int((t.time() - start) * 1000)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "elapsed_ms": elapsed,
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
            "setor_id": request.setor_id,
        },
    )

    try:
        # Load sector configuration
        try:
            sector = get_sector(request.setor_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))

        logger.info(f"Using sector: {sector.name} ({len(sector.keywords)} keywords)")

        # Determine keywords: custom terms REPLACE sector keywords (mutually exclusive)
        custom_terms: list[str] = []
        if request.termos_busca and request.termos_busca.strip():
            raw_terms = [t.strip().lower() for t in request.termos_busca.strip().split() if t.strip()]
            custom_terms = remove_stopwords(raw_terms)
            if len(custom_terms) < len(raw_terms):
                removed = set(raw_terms) - set(custom_terms)
                logger.info(f"Removed {len(removed)} stopwords: {removed}")

        if custom_terms:
            active_keywords = set(custom_terms)
            logger.info(f"Using {len(custom_terms)} custom search terms: {custom_terms}")
        else:
            active_keywords = set(sector.keywords)
            logger.info(f"Using sector keywords ({len(active_keywords)} terms)")

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

        # Step 2: Apply filtering (fail-fast sequential: UF → value → keywords)
        # Value range expanded to capture more opportunities:
        # - R$ 10k min: Include smaller municipal contracts
        # - R$ 10M max: Include larger state/federal contracts
        # Reference: Investigation 2026-01-28 - docs/investigations/
        logger.info("Applying filters to raw bids")
        licitacoes_filtradas, stats = filter_batch(
            licitacoes_raw,
            ufs_selecionadas=set(request.ufs),
            valor_min=10_000.0,   # Expanded from R$ 50k to capture more opportunities
            valor_max=10_000_000.0,  # Expanded from R$ 5M to capture larger contracts
            keywords=active_keywords,
            exclusions=sector.exclusions if not custom_terms else set(),
        )

        # Detailed logging for debugging and monitoring
        logger.info(
            f"Filtering complete: {len(licitacoes_filtradas)}/{len(licitacoes_raw)} bids passed"
        )
        # Use .get() with defaults for robustness (e.g., in tests with mocked stats)
        if stats:
            logger.info(f"  - Total processadas: {stats.get('total', len(licitacoes_raw))}")
            logger.info(f"  - Aprovadas: {stats.get('aprovadas', len(licitacoes_filtradas))}")
            logger.info(f"  - Rejeitadas (UF): {stats.get('rejeitadas_uf', 0)}")
            logger.info(f"  - Rejeitadas (Valor): {stats.get('rejeitadas_valor', 0)}")
            logger.info(f"  - Rejeitadas (Keyword): {stats.get('rejeitadas_keyword', 0)}")
            logger.info(f"  - Rejeitadas (Prazo): {stats.get('rejeitadas_prazo', 0)}")
            logger.info(f"  - Rejeitadas (Outros): {stats.get('rejeitadas_outros', 0)}")

        # Diagnostic: sample of keyword-rejected items for debugging
        if stats.get('rejeitadas_keyword', 0) > 0:
            keyword_rejected_sample = []
            for lic in licitacoes_raw[:200]:
                obj = lic.get("objetoCompra", "")
                from filter import match_keywords, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO
                matched, _ = match_keywords(obj, KEYWORDS_UNIFORMES, KEYWORDS_EXCLUSAO)
                if not matched:
                    keyword_rejected_sample.append(obj[:120])
                    if len(keyword_rejected_sample) >= 3:
                        break
            if keyword_rejected_sample:
                logger.debug(f"  - Sample keyword-rejected objects: {keyword_rejected_sample}")

        # Build filter stats for frontend
        fs = FilterStats(
            rejeitadas_uf=stats.get("rejeitadas_uf", 0),
            rejeitadas_valor=stats.get("rejeitadas_valor", 0),
            rejeitadas_keyword=stats.get("rejeitadas_keyword", 0),
            rejeitadas_prazo=stats.get("rejeitadas_prazo", 0),
            rejeitadas_outros=stats.get("rejeitadas_outros", 0),
        )

        # Early return if no results passed filters — skip LLM and Excel
        if not licitacoes_filtradas:
            logger.info("No bids passed filters — skipping LLM and Excel generation")
            resumo = ResumoLicitacoes(
                resumo_executivo=(
                    f"Nenhuma licitação de {sector.name.lower()} encontrada "
                    f"nos estados selecionados para o período informado."
                ),
                total_oportunidades=0,
                valor_total=0.0,
                destaques=[],
                alerta_urgencia=None,
            )
            response = BuscaResponse(
                resumo=resumo,
                excel_base64="",
                total_raw=len(licitacoes_raw),
                total_filtrado=0,
                filter_stats=fs,
            )
            logger.info(
                "Search completed with 0 results",
                extra={"total_raw": len(licitacoes_raw), "total_filtrado": 0},
            )
            return response

        # Step 3: Generate executive summary via LLM (with automatic fallback)
        logger.info("Generating executive summary")
        try:
            resumo = gerar_resumo(licitacoes_filtradas, sector_name=sector.name)
            logger.info("LLM summary generated successfully")
        except Exception as e:
            logger.warning(
                f"LLM generation failed, using fallback mechanism: {e}",
                exc_info=True,
            )
            resumo = gerar_resumo_fallback(licitacoes_filtradas, sector_name=sector.name)
            logger.info("Fallback summary generated successfully")

        # CRITICAL: Override LLM-generated counts with actual computed values.
        # The LLM may hallucinate total_oportunidades (often returning 0),
        # which causes the frontend to show "no results found".
        actual_total = len(licitacoes_filtradas)
        actual_valor = sum(
            lic.get("valorTotalEstimado", 0) or 0 for lic in licitacoes_filtradas
        )
        if resumo.total_oportunidades != actual_total:
            logger.warning(
                f"LLM returned total_oportunidades={resumo.total_oportunidades}, "
                f"overriding with actual count={actual_total}"
            )
        resumo.total_oportunidades = actual_total
        resumo.valor_total = actual_valor

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
            filter_stats=fs,
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
            detail=(
                f"O PNCP está limitando requisições. "
                f"Aguarde {retry_after} segundos e tente novamente."
            ),
            headers={"Retry-After": str(retry_after)},
        )

    except PNCPAPIError as e:
        logger.error(f"PNCP API error: {e}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail=(
                "O Portal Nacional de Contratações (PNCP) está temporariamente "
                "indisponível ou retornou um erro. Tente novamente em alguns "
                "instantes ou reduza o número de estados selecionados."
            ),
        )

    except Exception:
        logger.exception("Internal server error during procurement search")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor. Tente novamente em alguns instantes.",
        )
