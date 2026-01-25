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
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
    openapi_url="/openapi.json"
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

logger.info("FastAPI application initialized with CORS middleware")


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
            "openapi": "/openapi.json"
        },
        "status": "operational"
    }


@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        dict: Service health status

    Example:
        >>> response = await health()
        >>> response
        {'status': 'ok', 'version': '0.2.0'}
    """
    return {
        "status": "ok",
        "version": "0.2.0"
    }


# Additional endpoints will be implemented in subsequent issues:
# - POST /buscar (Issue #18) - Main search endpoint
# - Structured logging (Issue #19) - Enhanced logging middleware
# - Extended health checks (Issue #29) - Database/API connectivity checks
