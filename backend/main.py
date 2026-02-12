"""
BidIQ Uniformes POC - Backend API

FastAPI application for searching and analyzing uniform procurement bids
from Brazil's PNCP (Portal Nacional de Contratações Públicas).

This API provides endpoints for:
- Searching procurement opportunities by state and date range
- Filtering results by keywords and value thresholds
- Generating Excel reports with formatted data
- Creating AI-powered executive summaries (GPT-4.1-nano)

STORY-202: Monolith decomposition — routes extracted to:
  - routes/search.py (buscar + progress SSE)
  - routes/user.py (profile, change-password)
  - routes/billing.py (plans, checkout)
  - routes/sessions.py (search history)
  - authorization.py (admin/master role helpers)
"""

import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import setup_logging, ENABLE_NEW_PRICING, get_cors_origins
from pncp_client import PNCPClient
from sectors import list_sectors
from middleware import CorrelationIDMiddleware  # STORY-202 SYS-M01

# Existing routers
from admin import router as admin_router
from routes.subscriptions import router as subscriptions_router
from routes.features import router as features_router
from routes.messages import router as messages_router
from routes.analytics import router as analytics_router
from routes.auth_oauth import router as oauth_router  # STORY-180: Google OAuth
from routes.export_sheets import router as export_sheets_router  # STORY-180: Google Sheets Export
from webhooks.stripe import router as stripe_webhook_router

# STORY-202: Decomposed routers
from routes.search import router as search_router
from routes.user import router as user_router
from routes.billing import router as billing_router
from routes.sessions import router as sessions_router
from routes.plans import router as plans_router  # STORY-203 CROSS-M01

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
cors_origins = get_cors_origins()
logger.info(f"CORS configured for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With", "X-Request-ID"],
)

# STORY-202 SYS-M01: Add correlation ID middleware for distributed tracing
app.add_middleware(CorrelationIDMiddleware)

# ============================================================================
# SYS-M08: API Versioning with /v1/ prefix
# ============================================================================

# Mount all routers under /v1/ prefix for versioning
app.include_router(admin_router, prefix="/v1")
app.include_router(subscriptions_router, prefix="/v1")
app.include_router(features_router, prefix="/v1")
app.include_router(messages_router, prefix="/v1")
app.include_router(analytics_router, prefix="/v1")
app.include_router(oauth_router, prefix="/v1")  # STORY-180: Google OAuth routes
app.include_router(export_sheets_router, prefix="/v1")  # STORY-180: Google Sheets Export routes
app.include_router(stripe_webhook_router, prefix="/v1")
# STORY-202: Decomposed routers
app.include_router(search_router, prefix="/v1")
app.include_router(user_router, prefix="/v1")
app.include_router(billing_router, prefix="/v1")
app.include_router(sessions_router, prefix="/v1")
app.include_router(plans_router, prefix="/v1")  # STORY-203 CROSS-M01

# ============================================================================
# SYS-M08: Backward Compatibility - Mount routers without /v1/ prefix
# ============================================================================
# For gradual migration, also mount at original paths (will be deprecated)
app.include_router(admin_router)
app.include_router(subscriptions_router)
app.include_router(features_router)
app.include_router(messages_router)
app.include_router(analytics_router)
app.include_router(oauth_router)
app.include_router(export_sheets_router)
app.include_router(stripe_webhook_router)
app.include_router(search_router)
app.include_router(user_router)
app.include_router(billing_router)
app.include_router(sessions_router)
app.include_router(plans_router)

logger.info(
    "FastAPI application initialized — PORT=%s",
    os.getenv("PORT", "8000"),
)

# Log feature flag states
logger.info(
    "Feature Flags — ENABLE_NEW_PRICING=%s",
    ENABLE_NEW_PRICING,
)


# HOTFIX STORY-183: Diagnostic logging for route registration
@app.on_event("startup")
async def log_registered_routes():
    """Log all registered routes for debugging route 404 issues."""
    logger.info("=" * 60)
    logger.info("REGISTERED ROUTES:")
    logger.info("=" * 60)
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ','.join(route.methods) if route.methods else 'N/A'
            logger.info(f"  {methods:8s} {route.path}")
    logger.info("=" * 60)

    # Specifically check for export route
    export_routes = [r for r in app.routes if hasattr(r, 'path') and '/export' in r.path]
    if export_routes:
        logger.info(f"Export routes found: {len(export_routes)}")
        for r in export_routes:
            methods = ','.join(r.methods) if hasattr(r, 'methods') and r.methods else 'N/A'
            logger.info(f"   {methods:8s} {r.path}")
    else:
        logger.error("NO EXPORT ROUTES FOUND - /api/export/google-sheets will return 404!")
    logger.info("=" * 60)


# ============================================================================
# Core utility endpoints (stay in main.py)
# ============================================================================

@app.get("/")
async def root():
    """
    API root endpoint - provides navigation to documentation.

    SYS-M08: Informs clients about API versioning.
    """
    return {
        "name": "BidIQ Uniformes API",
        "version": "0.2.0",
        "api_version": "v1",  # SYS-M08: Current API version
        "description": "API para busca de licitações de uniformes no PNCP",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "openapi": "/openapi.json",
            "v1_api": "/v1",  # SYS-M08: Versioned API endpoint
        },
        "versioning": {  # SYS-M08: API versioning information
            "current": "v1",
            "supported": ["v1"],
            "deprecated": [],
            "note": "All endpoints available at /v1/<endpoint> and /<endpoint> (legacy)",
        },
        "status": "operational",
    }


@app.get("/health")
async def health():
    """
    Health check endpoint for monitoring and load balancers.

    Provides lightweight service health verification including dependency
    checks for Supabase, OpenAI, and Redis connectivity.
    """
    from datetime import datetime, timezone

    dependencies = {
        "supabase": "unconfigured",
        "openai": "unconfigured",
        "redis": "unconfigured",
    }

    # Check Supabase configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_url and supabase_key:
        try:
            from supabase_client import get_supabase
            get_supabase()
            dependencies["supabase"] = "healthy"
        except Exception as e:
            dependencies["supabase"] = f"error: {str(e)[:50]}"
    else:
        dependencies["supabase"] = "missing_env_vars"

    # Check OpenAI configuration
    if os.getenv("OPENAI_API_KEY"):
        dependencies["openai"] = "configured"
    else:
        dependencies["openai"] = "missing_api_key"

    # Check Redis connectivity (optional dependency)
    # SYS-L06: Add Redis health check to health endpoint
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            from redis_client import is_redis_available
            redis_available = await is_redis_available()
            dependencies["redis"] = "healthy" if redis_available else "unavailable"
        except Exception as e:
            dependencies["redis"] = f"error: {str(e)[:50]}"
    else:
        # Redis is optional - not configured is not an error
        dependencies["redis"] = "not_configured"

    # Determine overall health status
    # Supabase is critical, Redis is optional
    supabase_ok = not dependencies["supabase"].startswith("error")
    redis_degraded = dependencies["redis"].startswith("error") or dependencies["redis"] == "unavailable"

    if not supabase_ok:
        status = "unhealthy"
    elif redis_degraded and redis_url:  # Only degrade if Redis is configured but failing
        status = "degraded"
    else:
        status = "healthy"

    response_data = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": app.version,
        "dependencies": dependencies,
    }

    # Return 503 if unhealthy (critical dependencies down)
    if not supabase_ok:
        from fastapi.responses import JSONResponse
        return JSONResponse(content=response_data, status_code=503)

    return response_data


@app.get("/sources/health")
async def sources_health():
    """
    Health check for all configured procurement data sources.

    Returns status, response time, and priority for each source.
    """
    from datetime import datetime, timezone

    enable_multi_source = os.getenv("ENABLE_MULTI_SOURCE", "false").lower() == "true"
    from source_config.sources import get_source_config
    source_config = get_source_config()

    sources_info = []

    if source_config.pncp.enabled:
        sources_info.append({
            "code": "PNCP",
            "name": source_config.pncp.name,
            "enabled": True,
            "priority": source_config.pncp.priority,
        })

    if source_config.compras_gov.enabled:
        sources_info.append({
            "code": "COMPRAS_GOV",
            "name": source_config.compras_gov.name,
            "enabled": True,
            "priority": source_config.compras_gov.priority,
        })

    if source_config.portal.enabled:
        sources_info.append({
            "code": "PORTAL_COMPRAS",
            "name": source_config.portal.name,
            "enabled": True,
            "priority": source_config.portal.priority,
        })

    if enable_multi_source:
        from consolidation import ConsolidationService
        from clients.compras_gov_client import ComprasGovAdapter
        from clients.portal_compras_client import PortalComprasAdapter

        adapters = {}
        if source_config.compras_gov.enabled:
            adapters["COMPRAS_GOV"] = ComprasGovAdapter(timeout=source_config.compras_gov.timeout)
        if source_config.portal.enabled and source_config.portal.credentials.has_api_key():
            adapters["PORTAL_COMPRAS"] = PortalComprasAdapter(
                api_key=source_config.portal.credentials.api_key,
                timeout=source_config.portal.timeout,
            )

        if adapters:
            svc = ConsolidationService(adapters=adapters)
            health_results = await svc.health_check_all()
            await svc.close()

            for info in sources_info:
                code = info["code"]
                if code in health_results:
                    info["status"] = health_results[code]["status"]
                    info["response_ms"] = health_results[code]["response_ms"]
                elif code == "PNCP":
                    info["status"] = "available"
                    info["response_ms"] = 0
                else:
                    info["status"] = "unknown"
                    info["response_ms"] = 0
        else:
            for info in sources_info:
                info["status"] = "available" if info["code"] == "PNCP" else "unknown"
                info["response_ms"] = 0
    else:
        for info in sources_info:
            info["status"] = "available" if info["code"] == "PNCP" else "disabled"
            info["response_ms"] = 0

    total_enabled = len([s for s in sources_info if s["enabled"]])
    total_available = len([s for s in sources_info if s.get("status") == "available"])

    return {
        "sources": sources_info,
        "multi_source_enabled": enable_multi_source,
        "total_enabled": total_enabled,
        "total_available": total_available,
        "checked_at": datetime.now(timezone.utc).isoformat(),
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
