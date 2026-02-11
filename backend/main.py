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

import asyncio
import base64
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from config import setup_logging, ENABLE_NEW_PRICING, get_cors_origins
from schemas import BuscaRequest, BuscaResponse, FilterStats, ResumoLicitacoes, UserProfileResponse, LicitacaoItem
from pncp_client import PNCPClient, buscar_todas_ufs_paralelo
from exceptions import PNCPAPIError, PNCPRateLimitError
from filter import (
    remove_stopwords,
    aplicar_todos_filtros,
)
from status_inference import enriquecer_com_status_inferido
from utils.ordenacao import ordenar_licitacoes
from excel import create_excel
from llm import gerar_resumo, gerar_resumo_fallback
from sectors import get_sector, list_sectors
from auth import require_auth
from admin import router as admin_router
from log_sanitizer import mask_user_id, log_user_action
from rate_limiter import rate_limiter
from routes.subscriptions import router as subscriptions_router
from routes.features import router as features_router
from routes.messages import router as messages_router
from routes.analytics import router as analytics_router
from routes.auth_oauth import router as oauth_router  # STORY-180: Google OAuth
from routes.export_sheets import router as export_sheets_router  # STORY-180: Google Sheets Export
from webhooks.stripe import router as stripe_webhook_router

# Configure structured logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Error codes for structured error responses (UX clarity)
class ErrorCode:
    """Structured error codes for better frontend error handling"""
    DATE_RANGE_EXCEEDED = "DATE_RANGE_EXCEEDED"
    RATE_LIMIT = "RATE_LIMIT"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    INVALID_SECTOR = "INVALID_SECTOR"
    INVALID_UF = "INVALID_UF"
    INVALID_DATE_RANGE = "INVALID_DATE_RANGE"

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
# Secure CORS: Only allow specific origins defined in CORS_ORIGINS env var
# Default origins for development: localhost:3000
# Production origins should be set via environment variable
cors_origins = get_cors_origins()
logger.info(f"CORS configured for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

app.include_router(admin_router)
app.include_router(subscriptions_router)
app.include_router(features_router)
app.include_router(messages_router)
app.include_router(analytics_router)
app.include_router(oauth_router)  # STORY-180: Google OAuth routes
app.include_router(export_sheets_router)  # STORY-180: Google Sheets Export routes
app.include_router(stripe_webhook_router)

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
# Log all registered routes at startup to help diagnose export 404
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
        logger.info(f"✅ Export routes found: {len(export_routes)}")
        for r in export_routes:
            methods = ','.join(r.methods) if hasattr(r, 'methods') and r.methods else 'N/A'
            logger.info(f"   {methods:8s} {r.path}")
    else:
        logger.error("❌ NO EXPORT ROUTES FOUND - /api/export/google-sheets will return 404!")
    logger.info("=" * 60)

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

    Provides lightweight service health verification including dependency
    checks for Supabase connectivity. Designed for use by orchestrators
    (Docker, Kubernetes), load balancers, and uptime monitoring tools.

    Returns:
        dict: Service health status with timestamp, version and dependency status

    Response Schema:
        - status (str): "healthy" or "degraded"
        - timestamp (str): Current server time in ISO 8601 format
        - version (str): API version from app configuration
        - dependencies (dict): Status of external dependencies

    HTTP Status Codes:
        - 200: Service is healthy and operational
        - 503: Service is degraded (dependency checks fail)
    """
    from datetime import datetime
    import os

    dependencies = {
        "supabase": "unconfigured",
        "openai": "unconfigured",
    }

    # Check Supabase configuration
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if supabase_url and supabase_key:
        try:
            from supabase_client import get_supabase
            get_supabase()
            # Quick connectivity test - just verify client is initialized
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

    # Determine overall status
    # Supabase is optional - missing_env_vars is acceptable (anonymous searches work)
    # Only "error:*" status indicates actual degradation
    supabase_ok = not dependencies["supabase"].startswith("error")
    status = "healthy" if supabase_ok else "degraded"

    response_data = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version,
        "dependencies": dependencies,
    }

    if not supabase_ok:
        from fastapi.responses import JSONResponse
        return JSONResponse(content=response_data, status_code=503)

    return response_data


@app.get("/sources/health")
async def sources_health():
    """
    Health check for all configured procurement data sources.

    Returns status, response time, and priority for each source.
    Results are cached for 60 seconds to avoid spamming external APIs.
    """
    import time as t
    from datetime import datetime, timezone

    enable_multi_source = os.getenv("ENABLE_MULTI_SOURCE", "false").lower() == "true"
    from source_config.sources import get_source_config
    source_config = get_source_config()

    sources_info = []

    # Always report PNCP
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

    # Run health checks in parallel
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


@app.post("/change-password")
async def change_password(
    request: Request,
    user: dict = Depends(require_auth),
):
    """Change current user's password."""
    body = await request.json()
    new_password = body.get("new_password", "")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter no minimo 6 caracteres")

    from supabase_client import get_supabase
    sb = get_supabase()
    try:
        sb.auth.admin.update_user_by_id(user["id"], {"password": new_password})
    except Exception:
        # SECURITY: Sanitize error message (Issue #168) - never log password-related details
        log_user_action(logger, "password-change-failed", user["id"], level=logging.ERROR)
        raise HTTPException(status_code=500, detail="Erro ao alterar senha")

    # SECURITY: Sanitize user ID in logs (Issue #168)
    log_user_action(logger, "password-changed", user["id"])
    return {"success": True}


def _get_admin_ids() -> set[str]:
    """Get admin user IDs from environment variable (fallback/override)."""
    raw = os.getenv("ADMIN_USER_IDS", "")
    return {uid.strip().lower() for uid in raw.split(",") if uid.strip()}


def _check_user_roles(user_id: str) -> tuple[bool, bool]:
    """
    Check user's admin and master status from Supabase.

    Returns:
        tuple: (is_admin, is_master)
        - is_admin: Can manage users via /admin/* endpoints
        - is_master: Has full feature access (Excel, unlimited quota)

    Hierarchy: admin > master > regular users
    Admins automatically get master privileges.
    """
    import time
    for attempt in range(2):
        try:
            from supabase_client import get_supabase
            sb = get_supabase()

            # Get profile - try with is_admin first, fallback to just plan_type
            try:
                profile = (
                    sb.table("profiles")
                    .select("is_admin, plan_type")
                    .eq("id", user_id)
                    .single()
                    .execute()
                )
            except Exception:
                # is_admin column might not exist yet - fallback
                profile = (
                    sb.table("profiles")
                    .select("plan_type")
                    .eq("id", user_id)
                    .single()
                    .execute()
                )

            if not profile.data:
                return (False, False)

            is_admin = profile.data.get("is_admin", False)
            plan_type = profile.data.get("plan_type", "")

            # Admin implies master access
            is_master = is_admin or plan_type == "master"

            if is_admin:
                logger.debug(f"User {mask_user_id(user_id)} is ADMIN (profiles.is_admin)")
            elif is_master:
                logger.debug(f"User {mask_user_id(user_id)} is MASTER (profiles.plan_type)")

            return (is_admin, is_master)

        except Exception as e:
            if attempt == 0:
                logger.debug(f"Retry user roles check for {mask_user_id(user_id)} after error: {type(e).__name__}")
                time.sleep(0.3)
                continue
            logger.warning(
                f"ROLE CHECK FAILED for user {mask_user_id(user_id)} after 2 attempts: {type(e).__name__}. "
                f"User will be treated as regular (non-admin/non-master)."
            )
            return (False, False)
    return (False, False)


def _is_admin(user_id: str) -> bool:
    """
    Check if user can access /admin/* endpoints.

    Sources (in order):
    1. ADMIN_USER_IDS env var (fallback/override)
    2. Supabase profiles.is_admin = true
    """
    # Fast path: check env var first (no DB call)
    admin_ids = _get_admin_ids()
    if user_id.lower() in admin_ids:
        return True

    # Check Supabase
    is_admin, _ = _check_user_roles(user_id)
    return is_admin


def _has_master_access(user_id: str) -> bool:
    """
    Check if user has full feature access (master or admin).

    Sources:
    1. ADMIN_USER_IDS env var (admins get master access)
    2. Supabase profiles.is_admin = true (admins get master access)
    3. Supabase profiles.plan_type = 'master'
    """
    # Fast path: check env var first (no DB call)
    admin_ids = _get_admin_ids()
    if user_id.lower() in admin_ids:
        return True

    # Check Supabase
    is_admin, is_master = _check_user_roles(user_id)
    return is_admin or is_master


def _get_master_quota_info(is_admin: bool = False):
    """
    Get quota info for admin/master users - returns sala_guerra (highest tier).

    Admins/masters bypass all quota restrictions and have full access to all features.
    """
    from quota import QuotaInfo, PLAN_CAPABILITIES
    from datetime import datetime, timezone

    plan_name = "Sala de Guerra (Admin)" if is_admin else "Sala de Guerra (Master)"

    return QuotaInfo(
        allowed=True,
        plan_id="sala_guerra",
        plan_name=plan_name,
        capabilities=PLAN_CAPABILITIES["sala_guerra"],
        quota_used=0,
        quota_remaining=999999,  # Unlimited for admins/masters
        quota_reset_date=datetime.now(timezone.utc),
        trial_expires_at=None,
        error_message=None,
    )


@app.get("/me", response_model=UserProfileResponse)
async def get_profile(user: dict = Depends(require_auth)):
    """
    Get current user profile with plan capabilities and quota status.

    Returns complete user information including:
    - Plan capabilities (max_history_days, allow_excel, etc.)
    - Monthly quota usage and remaining
    - Trial expiration (if applicable)
    - Subscription status

    This endpoint provides all necessary information for the frontend
    to render plan-based UI elements (badges, quota counters, locked features).

    Note: Admin users automatically receive "Sala de Guerra" tier with unlimited access.
    """
    from quota import check_quota, QuotaInfo, PLAN_CAPABILITIES, get_plan_from_profile, PLAN_NAMES
    from supabase_client import get_supabase
    from datetime import datetime, timezone

    # ADMIN/MASTER BYPASS: Get highest tier automatically
    is_admin, is_master = _check_user_roles(user["id"])
    # Also check env var for admin override
    if user["id"].lower() in _get_admin_ids():
        is_admin = True
        is_master = True

    if is_admin or is_master:
        role = "ADMIN" if is_admin else "MASTER"
        logger.info(f"{role} user detected: {mask_user_id(user['id'])} - granting sala_guerra access")
        quota_info = _get_master_quota_info(is_admin=is_admin)
    elif ENABLE_NEW_PRICING:
        # FEATURE FLAG: New Pricing Model (STORY-165)
        # Get quota info with capabilities
        try:
            quota_info = check_quota(user["id"])
        except Exception as e:
            logger.error(f"Failed to check quota for user {user['id']}: {e}")
            # RESILIENCE: Use profile's plan_type instead of hardcoded free_trial
            fallback_plan = get_plan_from_profile(user["id"]) or "free_trial"
            fallback_caps = PLAN_CAPABILITIES.get(fallback_plan, PLAN_CAPABILITIES["free_trial"])
            fallback_name = PLAN_NAMES.get(fallback_plan, "FREE Trial") if fallback_plan != "free_trial" else "FREE Trial"
            if fallback_plan != "free_trial":
                logger.warning(
                    f"PLAN FALLBACK for user {mask_user_id(user['id'])}: "
                    f"subscription check failed, using profiles.plan_type='{fallback_plan}'"
                )
            quota_info = QuotaInfo(
                allowed=True,
                plan_id=fallback_plan,
                plan_name=fallback_name,
                capabilities=fallback_caps,
                quota_used=0,
                quota_remaining=999999,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=None,
                error_message=None,
            )
    else:
        # OLD BEHAVIOR: No quota/plan capabilities
        logger.debug("New pricing disabled, using legacy behavior")
        quota_info = QuotaInfo(
            allowed=True,
            plan_id="legacy",
            plan_name="Legacy",
            capabilities=PLAN_CAPABILITIES["free_trial"],  # Use free_trial as fallback
            quota_used=0,
            quota_remaining=999999,
            quota_reset_date=datetime.now(timezone.utc),
            trial_expires_at=None,
            error_message=None,
        )

    # Get user email
    try:
        sb = get_supabase()
        user_data = sb.auth.admin.get_user_by_id(user["id"])
        email = user_data.user.email if user_data and user_data.user else user.get("email", "unknown@example.com")
    except Exception as e:
        logger.warning(f"Failed to fetch user email: {e}")
        email = user.get("email", "unknown@example.com")

    # Determine subscription status
    if quota_info.trial_expires_at:
        if datetime.now(timezone.utc) > quota_info.trial_expires_at:
            subscription_status = "expired"
        else:
            subscription_status = "trial"
    else:
        subscription_status = "active"

    return UserProfileResponse(
        user_id=user["id"],
        email=email,
        plan_id=quota_info.plan_id,
        plan_name=quota_info.plan_name,
        capabilities=quota_info.capabilities,
        quota_used=quota_info.quota_used,
        quota_remaining=quota_info.quota_remaining,
        quota_reset_date=quota_info.quota_reset_date.isoformat(),
        trial_expires_at=quota_info.trial_expires_at.isoformat() if quota_info.trial_expires_at else None,
        subscription_status=subscription_status,
        is_admin=is_admin,
    )


@app.get("/sessions")
async def get_sessions(
    user: dict = Depends(require_auth),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Get user's search session history."""
    from supabase_client import get_supabase
    sb = get_supabase()

    result = (
        sb.table("search_sessions")
        .select("*", count="exact")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "sessions": result.data,
        "total": result.count or 0,
        "limit": limit,
        "offset": offset,
    }


@app.get("/plans")
async def get_plans():
    """Get available subscription plans."""
    from supabase_client import get_supabase
    sb = get_supabase()

    result = (
        sb.table("plans")
        .select("id, name, description, max_searches, price_brl, duration_days")
        .eq("is_active", True)
        .order("price_brl")
        .execute()
    )
    return {"plans": result.data}


@app.post("/checkout")
async def create_checkout(
    plan_id: str = Query(...),
    user: dict = Depends(require_auth),
):
    """Create Stripe Checkout session for a plan purchase."""
    import stripe as stripe_lib

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    stripe_lib.api_key = stripe_key

    from supabase_client import get_supabase
    sb = get_supabase()

    # Get plan
    plan_result = sb.table("plans").select("*").eq("id", plan_id).eq("is_active", True).single().execute()
    if not plan_result.data:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")

    plan = plan_result.data
    if not plan.get("stripe_price_id"):
        raise HTTPException(status_code=400, detail="Plano sem preco Stripe configurado")

    # Determine if subscription or one-time
    is_recurring = plan_id in ("monthly", "annual")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    session_params = {
        "payment_method_types": ["card"],
        "line_items": [{"price": plan["stripe_price_id"], "quantity": 1}],
        "mode": "subscription" if is_recurring else "payment",
        "success_url": f"{frontend_url}/planos?success=true&plan={plan_id}",
        "cancel_url": f"{frontend_url}/planos?cancelled=true",
        "client_reference_id": user["id"],
        "metadata": {"plan_id": plan_id, "user_id": user["id"]},
    }

    # Attach customer email for receipt
    session_params["customer_email"] = user["email"]

    checkout_session = stripe_lib.checkout.Session.create(**session_params)
    return {"checkout_url": checkout_session.url}


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (checkout completed, subscription updated)."""
    import stripe as stripe_lib

    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not stripe_key or not webhook_secret:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    stripe_lib.api_key = stripe_key

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe_lib.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("client_reference_id") or session["metadata"].get("user_id")
        plan_id = session["metadata"].get("plan_id")

        if user_id and plan_id:
            _activate_plan(user_id, plan_id, session)

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        _deactivate_stripe_subscription(sub["id"])

    elif event["type"] == "customer.subscription.updated":
        # Handles plan changes and billing period updates
        sub = event["data"]["object"]
        _handle_subscription_updated(sub)

    elif event["type"] == "invoice.payment_succeeded":
        # Handles successful payment (renewal) — reactivates subscription
        invoice = event["data"]["object"]
        _handle_invoice_paid(invoice)

    return {"status": "ok"}


def _activate_plan(user_id: str, plan_id: str, stripe_session: dict):
    """Activate a plan for a user after successful payment."""
    from supabase_client import get_supabase
    from datetime import datetime, timezone, timedelta
    sb = get_supabase()

    # Get plan details
    plan = sb.table("plans").select("*").eq("id", plan_id).single().execute()
    if not plan.data:
        logger.error(f"Plan {plan_id} not found during activation")
        return

    p = plan.data
    expires_at = None
    if p["duration_days"]:
        expires_at = (datetime.now(timezone.utc) + timedelta(days=p["duration_days"])).isoformat()

    # Deactivate previous subscriptions
    sb.table("user_subscriptions").update({"is_active": False}).eq("user_id", user_id).eq("is_active", True).execute()

    # Create new subscription
    sb.table("user_subscriptions").insert({
        "user_id": user_id,
        "plan_id": plan_id,
        "credits_remaining": p["max_searches"],
        "expires_at": expires_at,
        "stripe_subscription_id": stripe_session.get("subscription"),
        "stripe_customer_id": stripe_session.get("customer"),
        "is_active": True,
    }).execute()

    # Update profile plan_type
    sb.table("profiles").update({"plan_type": plan_id}).eq("id", user_id).execute()

    # SECURITY: Sanitize user ID in logs (Issue #168)
    log_user_action(logger, "plan-activated", user_id, details={"plan_id": plan_id})


def _deactivate_stripe_subscription(stripe_sub_id: str):
    """Deactivate subscription when cancelled in Stripe.

    Also updates profiles.plan_type to free_trial so the profile-based
    fallback correctly reflects the cancellation.
    """
    from supabase_client import get_supabase
    sb = get_supabase()

    # Find subscription to get user_id before deactivating
    try:
        sub_result = (
            sb.table("user_subscriptions")
            .select("user_id")
            .eq("stripe_subscription_id", stripe_sub_id)
            .limit(1)
            .execute()
        )
        user_id = sub_result.data[0]["user_id"] if sub_result.data else None
    except Exception as e:
        logger.warning(f"Could not find user for stripe subscription {stripe_sub_id[:8]}***: {e}")
        user_id = None

    # Deactivate subscription
    sb.table("user_subscriptions").update({"is_active": False}).eq("stripe_subscription_id", stripe_sub_id).execute()

    # Sync profiles.plan_type so fallback reflects cancellation
    if user_id:
        sb.table("profiles").update({"plan_type": "free_trial"}).eq("id", user_id).execute()
        logger.info(f"Deactivated subscription and updated profile for user {mask_user_id(user_id)}")
    else:
        logger.info(f"Deactivated Stripe subscription {stripe_sub_id[:8]}***")


def _handle_subscription_updated(sub_data: dict):
    """Handle Stripe subscription updated (plan change, billing period update).

    Syncs user_subscriptions and profiles.plan_type so the profile-based
    fallback always reflects the user's current plan.

    Ready to plug: requires Stripe metadata to contain plan_id.
    """
    from supabase_client import get_supabase
    sb = get_supabase()
    stripe_sub_id = sub_data.get("id", "")

    try:
        # Find the local subscription
        sub_result = (
            sb.table("user_subscriptions")
            .select("id, user_id, plan_id")
            .eq("stripe_subscription_id", stripe_sub_id)
            .limit(1)
            .execute()
        )

        if not sub_result.data:
            logger.warning(f"No local subscription for Stripe sub {stripe_sub_id[:8]}***")
            return

        local_sub = sub_result.data[0]
        user_id = local_sub["user_id"]

        # Check if plan changed (Stripe metadata should contain plan_id)
        new_plan_id = (sub_data.get("metadata") or {}).get("plan_id")

        if new_plan_id and new_plan_id != local_sub["plan_id"]:
            # Plan upgrade/downgrade — update both subscription and profile
            sb.table("user_subscriptions").update({
                "plan_id": new_plan_id,
                "is_active": True,
            }).eq("id", local_sub["id"]).execute()

            sb.table("profiles").update({
                "plan_type": new_plan_id,
            }).eq("id", user_id).execute()

            logger.info(
                f"Plan changed for user {mask_user_id(user_id)}: "
                f"{local_sub['plan_id']} → {new_plan_id}"
            )
        else:
            # Ensure subscription is active (covers reactivation after past_due)
            sb.table("user_subscriptions").update({
                "is_active": True,
            }).eq("id", local_sub["id"]).execute()
            logger.info(f"Subscription updated for user {mask_user_id(user_id)}")

    except Exception as e:
        logger.error(f"Error handling subscription.updated for {stripe_sub_id[:8]}***: {e}")


def _handle_invoice_paid(invoice_data: dict):
    """Handle successful invoice payment (subscription renewal).

    Reactivates the subscription and extends expiry. Critical for preventing
    billing-gap downgrades: when a payment succeeds, the subscription must
    be marked active immediately.

    Also syncs profiles.plan_type to ensure the profile-based fallback
    reflects the renewed plan.
    """
    from supabase_client import get_supabase
    from datetime import datetime, timezone, timedelta
    sb = get_supabase()

    stripe_sub_id = invoice_data.get("subscription")
    if not stripe_sub_id:
        logger.debug("Invoice has no subscription_id, skipping")
        return

    try:
        sub_result = (
            sb.table("user_subscriptions")
            .select("id, user_id, plan_id")
            .eq("stripe_subscription_id", stripe_sub_id)
            .limit(1)
            .execute()
        )

        if not sub_result.data:
            logger.warning(f"No local subscription for invoice stripe_sub {stripe_sub_id[:8]}***")
            return

        local_sub = sub_result.data[0]
        user_id = local_sub["user_id"]
        plan_id = local_sub["plan_id"]

        # Get plan duration for new expiry
        plan_result = sb.table("plans").select("duration_days").eq("id", plan_id).single().execute()
        duration_days = plan_result.data["duration_days"] if plan_result.data else 30

        new_expires = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()

        # Reactivate and extend
        sb.table("user_subscriptions").update({
            "is_active": True,
            "expires_at": new_expires,
        }).eq("id", local_sub["id"]).execute()

        # Ensure profile reflects active plan
        sb.table("profiles").update({
            "plan_type": plan_id,
        }).eq("id", user_id).execute()

        logger.info(
            f"Invoice payment processed for user {mask_user_id(user_id)}: "
            f"plan={plan_id}, new_expires={new_expires[:10]}"
        )

    except Exception as e:
        logger.error(f"Error handling invoice.paid for sub {stripe_sub_id[:8]}***: {e}")


def _build_pncp_link(lic: dict) -> str:
    """
    Build PNCP link from bid data.

    Priority: linkSistemaOrigem > linkProcessoEletronico > constructed URL from numeroControlePNCP
    """
    link = lic.get("linkSistemaOrigem") or lic.get("linkProcessoEletronico")

    if not link:
        numero_controle = lic.get("numeroControlePNCP", "")
        if numero_controle:
            try:
                # Parse: "67366310000103-1-000189/2025" -> cnpj=67366310000103, ano=2025, seq=189
                partes = numero_controle.split("/")
                if len(partes) == 2:
                    ano = partes[1]
                    cnpj_tipo_seq = partes[0].split("-")
                    if len(cnpj_tipo_seq) >= 3:
                        cnpj = cnpj_tipo_seq[0]
                        sequencial = cnpj_tipo_seq[2].lstrip("0")
                        if cnpj and ano and sequencial:
                            link = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{sequencial}"
            except Exception:
                pass

    return link or ""


def _calcular_urgencia(dias_restantes: int | None) -> str | None:
    """Classify urgency based on days remaining until deadline."""
    if dias_restantes is None:
        return None
    if dias_restantes < 0:
        return "encerrada"
    if dias_restantes < 7:
        return "critica"
    if dias_restantes < 14:
        return "alta"
    if dias_restantes <= 30:
        return "media"
    return "baixa"


def _calcular_dias_restantes(data_encerramento_str: str | None) -> int | None:
    """Calculate days remaining from today to the deadline date."""
    if not data_encerramento_str:
        return None
    try:
        from datetime import date
        enc = date.fromisoformat(data_encerramento_str[:10])
        return (enc - date.today()).days
    except (ValueError, TypeError):
        return None


def _convert_to_licitacao_items(licitacoes: list[dict]) -> list[LicitacaoItem]:
    """
    Convert raw bid dictionaries to LicitacaoItem objects for frontend display.
    """
    items = []
    for lic in licitacoes:
        try:
            data_enc = lic.get("dataEncerramentoProposta", "")[:10] if lic.get("dataEncerramentoProposta") else None
            dias_rest = _calcular_dias_restantes(data_enc)
            item = LicitacaoItem(
                pncp_id=lic.get("codigoCompra", lic.get("numeroControlePNCP", "")),
                objeto=lic.get("objetoCompra", "")[:500],  # Truncate long descriptions
                orgao=lic.get("nomeOrgao", ""),
                uf=lic.get("uf", ""),
                municipio=lic.get("municipio"),
                valor=lic.get("valorTotalEstimado") or 0.0,
                modalidade=lic.get("modalidadeNome"),
                data_publicacao=lic.get("dataPublicacaoPncp", "")[:10] if lic.get("dataPublicacaoPncp") else None,
                data_abertura=lic.get("dataAberturaProposta", "")[:10] if lic.get("dataAberturaProposta") else None,
                data_encerramento=data_enc,
                dias_restantes=dias_rest,
                urgencia=_calcular_urgencia(dias_rest),
                link=_build_pncp_link(lic),
                source=lic.get("_source"),
                relevance_score=lic.get("_relevance_score"),
                matched_terms=lic.get("_matched_terms"),
            )
            items.append(item)
        except Exception as e:
            logger.warning(f"Failed to convert bid to LicitacaoItem: {e}")
            continue
    return items


@app.get("/buscar-progress/{search_id}")
async def buscar_progress_stream(
    search_id: str,
    request: Request,
    user: dict = Depends(require_auth),
):
    """
    SSE endpoint for real-time search progress updates.

    The client opens this connection simultaneously with POST /buscar,
    using the same search_id to correlate progress events.

    Events:
        - connecting (5%): Initial setup
        - fetching (10-55%): Per-UF progress with uf_index/uf_total
        - filtering (60-70%): Filter application
        - llm (75-90%): LLM summary generation
        - excel (92-98%): Excel report generation
        - complete (100%): Search finished
        - error: Search failed
    """
    import asyncio as _asyncio
    import json as _json
    from progress import get_tracker
    from starlette.responses import StreamingResponse

    async def event_generator():
        # Wait up to 30s for the tracker to be created by POST /buscar
        tracker = None
        for _ in range(60):  # 60 * 0.5s = 30s
            tracker = get_tracker(search_id)
            if tracker:
                break
            await _asyncio.sleep(0.5)

        if not tracker:
            yield f"data: {_json.dumps({'stage': 'error', 'progress': -1, 'message': 'Search not found'})}\n\n"
            return

        # Stream events from the tracker's queue
        while True:
            try:
                event = await _asyncio.wait_for(tracker.queue.get(), timeout=30.0)
                yield f"data: {_json.dumps(event.to_dict())}\n\n"

                if event.stage in ("complete", "error"):
                    break

            except _asyncio.TimeoutError:
                # Heartbeat to keep connection alive
                yield ": heartbeat\n\n"

            except _asyncio.CancelledError:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/buscar", response_model=BuscaResponse)
async def buscar_licitacoes(
    request: BuscaRequest,
    user: dict = Depends(require_auth),
):
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
    import time as sync_time
    from progress import create_tracker, remove_tracker

    start_time = sync_time.time()

    # SSE Progress Tracking: Create tracker if search_id provided
    tracker = None
    if request.search_id:
        tracker = create_tracker(request.search_id, len(request.ufs))
        await tracker.emit("connecting", 3, "Iniciando busca...")

    logger.info(
        "Starting procurement search",
        extra={
            "ufs": request.ufs,
            "data_inicial": request.data_inicial,
            "data_final": request.data_final,
            "setor_id": request.setor_id,
            "status": request.status.value if request.status else None,
            "modalidades": request.modalidades,
            "valor_minimo": request.valor_minimo,
            "valor_maximo": request.valor_maximo,
            "esferas": [e.value for e in request.esferas] if request.esferas else None,
            "municipios": request.municipios,
            "ordenacao": request.ordenacao,
        },
    )

    # FEATURE FLAG: New Pricing Model (STORY-165)
    from quota import check_quota, QuotaInfo, PLAN_CAPABILITIES, get_plan_from_profile, PLAN_NAMES
    from datetime import datetime, timezone

    # ADMIN/MASTER BYPASS: Get highest tier automatically (no quota/rate limits)
    is_admin, is_master = _check_user_roles(user["id"])
    # Also check env var for admin override
    if user["id"].lower() in _get_admin_ids():
        is_admin = True
        is_master = True

    # -----------------------------------------------------------------
    # RATE LIMITING CHECK (per-minute, plan-based)
    # Must happen BEFORE quota check to prevent abuse
    # Admins/masters bypass rate limiting
    # -----------------------------------------------------------------
    if not (is_admin or is_master):
        # Get user's plan to determine rate limit
        # Quick check to get max_requests_per_min without full quota check
        try:
            quick_quota = check_quota(user["id"])
            max_rpm = quick_quota.capabilities.get("max_requests_per_min", 10)
        except Exception as e:
            logger.warning(f"Failed to get rate limit for user {mask_user_id(user['id'])}: {e}")
            # Fallback to conservative limit (consultor_agil level)
            max_rpm = 10

        rate_allowed, retry_after = rate_limiter.check_rate_limit(user["id"], max_rpm)

        if not rate_allowed:
            logger.warning(
                f"Rate limit exceeded for user {mask_user_id(user['id'])}: "
                f"{max_rpm} req/min limit, retry after {retry_after}s"
            )
            raise HTTPException(
                status_code=429,
                detail=f"Limite de requisições excedido ({max_rpm}/min). Aguarde {retry_after} segundos.",
                headers={"Retry-After": str(retry_after)},
            )

        logger.debug(f"Rate limit check passed for user {mask_user_id(user['id'])}: {max_rpm} req/min")

    if is_admin or is_master:
        role = "ADMIN" if is_admin else "MASTER"
        logger.info(f"{role} user detected: {mask_user_id(user['id'])} - bypassing quota check")
        quota_info = _get_master_quota_info(is_admin=is_admin)
    elif ENABLE_NEW_PRICING:
        logger.debug("New pricing enabled, checking quota and plan capabilities")
        try:
            # HOTFIX 2026-02-10: Use atomic check-and-increment to prevent race conditions
            # Issue #189: TOCTOU vulnerability fix
            from quota import check_quota, check_and_increment_quota_atomic

            quota_info = check_quota(user["id"])

            # Pre-check trial expiration and quota availability
            if not quota_info.allowed:
                # Quota exhausted or trial expired
                raise HTTPException(status_code=403, detail=quota_info.error_message)

            # ATOMIC: Check and increment quota BEFORE search execution
            # This prevents race condition where multiple concurrent requests
            # could exceed the quota limit
            allowed, new_quota_used, quota_remaining_after = check_and_increment_quota_atomic(
                user["id"],
                quota_info.capabilities["max_requests_per_month"]
            )

            if not allowed:
                # Quota was exhausted atomically (another request consumed last credit)
                raise HTTPException(
                    status_code=429,
                    detail=f"Limite de {quota_info.capabilities['max_requests_per_month']} buscas mensais atingido. Renova em {quota_info.quota_reset_date.strftime('%d/%m/%Y')}."
                )

            # Update quota_info with atomic values for response
            quota_info.quota_used = new_quota_used
            quota_info.quota_remaining = quota_remaining_after
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except RuntimeError as e:
            # Configuration error (missing env vars) - fail fast
            logger.error(f"Supabase configuration error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Serviço temporariamente indisponível. Tente novamente em alguns minutos."
            )
        except Exception as e:
            # Unexpected error - log but continue with safe fallback (user already authenticated)
            logger.warning(f"Quota check failed (continuing with fallback): {e}")
            # RESILIENCE: Use profile's plan_type instead of hardcoded free_trial
            fallback_plan = get_plan_from_profile(user["id"]) or "free_trial"
            fallback_caps = PLAN_CAPABILITIES.get(fallback_plan, PLAN_CAPABILITIES["free_trial"])
            fallback_name = PLAN_NAMES.get(fallback_plan, "FREE Trial") if fallback_plan != "free_trial" else "FREE Trial"
            if fallback_plan != "free_trial":
                logger.warning(
                    f"PLAN FALLBACK for user {mask_user_id(user['id'])}: "
                    f"subscription check failed, using profiles.plan_type='{fallback_plan}'"
                )
            quota_info = QuotaInfo(
                allowed=True,
                plan_id=fallback_plan,
                plan_name=fallback_name,
                capabilities=fallback_caps,
                quota_used=0,
                quota_remaining=999999,
                quota_reset_date=datetime.now(timezone.utc),
                trial_expires_at=None,
                error_message=None,
            )
    else:
        # OLD BEHAVIOR: No quota/plan enforcement
        logger.debug("New pricing disabled, using legacy behavior (no quota limits)")
        quota_info = QuotaInfo(
            allowed=True,
            plan_id="legacy",
            plan_name="Legacy",
            capabilities=PLAN_CAPABILITIES["free_trial"],  # Use free_trial capabilities as base
            quota_used=0,
            quota_remaining=999999,
            quota_reset_date=datetime.now(timezone.utc),
            trial_expires_at=None,
            error_message=None,
        )

    # ==========================================================================
    # DATE RANGE: No restrictions - users can search any period
    # ==========================================================================
    # HOTFIX 2026-02-10: Removed date_range validation that was blocking paying users.
    # Essential validations (data_inicial <= data_final) are handled by Pydantic
    # in schemas.py BuscaRequest.validate_dates_and_values()
    #
    # Previously blocked users with 400 errors for searches > max_history_days.
    # Now unlimited date ranges allowed per user requirement.

    try:
        # Load sector configuration
        try:
            sector = get_sector(request.setor_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))

        logger.info(f"Using sector: {sector.name} ({len(sector.keywords)} keywords)")

        # Determine keywords: custom terms REPLACE sector keywords (mutually exclusive)
        # STORY-178 AC1: Use intelligent term parser with comma/phrase support
        from term_parser import parse_search_terms
        from relevance import calculate_min_matches
        from filter import validate_terms  # NEW: Robust term validation

        custom_terms: list[str] = []
        stopwords_removed: list[str] = []  # kept for backward compat in response
        min_match_floor_value: int | None = None

        if request.termos_busca and request.termos_busca.strip():
            # STEP 1: Parse terms (comma-delimited phrases + stopword removal)
            parsed_terms = parse_search_terms(request.termos_busca)

            # STEP 2: CRITICAL - Validate terms with robust logic
            # This eliminates the bug where terms appear in BOTH "used" and "ignored"
            validated = validate_terms(parsed_terms)

            if not validated['valid']:
                # ALL terms rejected - return helpful error
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Nenhum termo válido para busca",
                        "termos_ignorados": validated['ignored'],
                        "motivos_ignorados": validated['reasons'],
                        "sugestao": "Use termos mais específicos (mínimo 4 caracteres, evite palavras comuns como 'de', 'da', etc.)"
                    }
                )

            # Use only VALIDATED terms for search
            custom_terms = validated['valid']
            stopwords_removed = validated['ignored']  # For response transparency

            logger.info(
                f"Term validation: {len(custom_terms)} valid, {len(stopwords_removed)} ignored. "
                f"Valid={custom_terms}, Ignored={list(validated['reasons'].keys())}"
            )

            # Calculate min_match_floor for custom terms (AC2.2)
            if custom_terms and not request.show_all_matches:
                min_match_floor_value = calculate_min_matches(len(custom_terms))
                logger.info(
                    f"Min match floor: {min_match_floor_value} "
                    f"(total_terms={len(custom_terms)})"
                )

        if custom_terms:
            active_keywords = set(custom_terms)
            logger.info(f"Using {len(custom_terms)} custom search terms: {custom_terms}")
        else:
            active_keywords = set(sector.keywords)
            logger.info(f"Using sector keywords ({len(active_keywords)} terms)")

        # SSE: Sector ready, starting fetch
        if tracker:
            await tracker.emit("connecting", 8, f"Setor '{sector.name}' configurado, conectando ao PNCP...")

        # Step 1: Fetch from procurement sources
        # FEATURE FLAG: Multi-source consolidation (STORY-177)
        enable_multi_source = os.getenv("ENABLE_MULTI_SOURCE", "false").lower() == "true"
        source_stats_data = None  # Will be populated if multi-source is active

        # Use parallel fetching for multiple UFs to improve performance
        use_parallel = len(request.ufs) > 1

        # Get status value for PNCP API query
        status_value = request.status.value if request.status else None

        # Get modalidades to fetch (defaults to [6] if not specified)
        modalidades_to_fetch = request.modalidades if request.modalidades else None

        # SSE: Starting fetch
        if tracker:
            msg = f"Iniciando busca em {len(request.ufs)} estados..."
            if enable_multi_source:
                msg += " (multi-fonte ativo)"
            await tracker.emit("fetching", 10, msg)

        # Build per-UF progress callback for SSE
        uf_progress_callback = None
        if tracker:
            async def uf_progress_callback(uf: str, items_count: int):
                await tracker.emit_uf_complete(uf, items_count)

        # Global fetch timeout: 4 minutes max for the entire fetch phase
        FETCH_TIMEOUT = 4 * 60  # seconds

        if enable_multi_source:
            # === MULTI-SOURCE PATH (STORY-177) ===
            logger.info("Multi-source fetch enabled, using ConsolidationService")
            from consolidation import ConsolidationService
            from clients.compras_gov_client import ComprasGovAdapter
            from clients.portal_compras_client import PortalComprasAdapter
            from source_config.sources import get_source_config

            source_config = get_source_config()
            adapters = {}

            # Always include PNCP via legacy wrapper
            from clients.base import SourceAdapter, SourceMetadata, SourceStatus, SourceCapability, UnifiedProcurement
            class _PNCPLegacyAdapter(SourceAdapter):
                """Wraps existing PNCPClient as a SourceAdapter for consolidation."""
                _meta = SourceMetadata(
                    name="PNCP", code="PNCP",
                    base_url="https://pncp.gov.br/api/consulta/v1",
                    capabilities={SourceCapability.PAGINATION, SourceCapability.DATE_RANGE, SourceCapability.FILTER_BY_UF},
                    rate_limit_rps=10.0, priority=1,
                )
                @property
                def metadata(self): return self._meta
                async def health_check(self): return SourceStatus.AVAILABLE
                async def fetch(self, data_inicial, data_final, ufs=None, **kwargs):
                    _ufs = list(ufs) if ufs else request.ufs
                    if len(_ufs) > 1:
                        results = await buscar_todas_ufs_paralelo(
                            ufs=_ufs, data_inicial=data_inicial, data_final=data_final,
                            modalidades=modalidades_to_fetch, status=status_value,
                            max_concurrent=10, on_uf_complete=uf_progress_callback,
                        )
                    else:
                        client = PNCPClient()
                        results = list(client.fetch_all(
                            data_inicial=data_inicial, data_final=data_final,
                            ufs=_ufs, modalidades=modalidades_to_fetch,
                        ))
                    for item in results:
                        yield UnifiedProcurement(
                            source_id=item.get("codigoCompra", ""),
                            source_name="PNCP",
                            objeto=item.get("objetoCompra", ""),
                            valor_estimado=item.get("valorTotalEstimado", 0) or 0,
                            orgao=item.get("nomeOrgao", ""),
                            cnpj_orgao=item.get("cnpjOrgao", ""),
                            uf=item.get("uf", ""),
                            municipio=item.get("municipio", ""),
                            numero_edital=item.get("numeroEdital", ""),
                            modalidade=item.get("modalidadeNome", ""),
                            situacao=item.get("situacaoCompraNome", ""),
                            link_edital=item.get("linkSistemaOrigem", ""),
                            link_portal=item.get("linkProcessoEletronico", ""),
                            raw_data=item,
                        )
                def normalize(self, raw_record): pass

            if source_config.pncp.enabled:
                adapters["PNCP"] = _PNCPLegacyAdapter()

            if source_config.compras_gov.enabled:
                adapters["COMPRAS_GOV"] = ComprasGovAdapter(
                    timeout=source_config.compras_gov.timeout
                )

            if source_config.portal.enabled and source_config.portal.credentials.has_api_key():
                adapters["PORTAL_COMPRAS"] = PortalComprasAdapter(
                    api_key=source_config.portal.credentials.api_key,
                    timeout=source_config.portal.timeout,
                )

            consolidation_svc = ConsolidationService(
                adapters=adapters,
                timeout_per_source=source_config.consolidation.timeout_per_source,
                timeout_global=source_config.consolidation.timeout_global,
                fail_on_all_errors=source_config.consolidation.fail_on_all_errors,
            )

            # SSE callback for source completion
            source_complete_cb = None
            if tracker:
                def source_complete_cb(src_code, count, error):
                    logger.info(f"[MULTI-SOURCE] {src_code}: {count} records, error={error}")

            try:
                consolidation_result = await asyncio.wait_for(
                    consolidation_svc.fetch_all(
                        data_inicial=request.data_inicial,
                        data_final=request.data_final,
                        ufs=set(request.ufs),
                        on_source_complete=source_complete_cb,
                    ),
                    timeout=FETCH_TIMEOUT,
                )
                licitacoes_raw = consolidation_result.records
                source_stats_data = [
                    {
                        "source_code": sr.source_code,
                        "record_count": sr.record_count,
                        "duration_ms": sr.duration_ms,
                        "error": sr.error,
                        "status": sr.status,
                    }
                    for sr in consolidation_result.source_results
                ]
                logger.info(
                    f"Multi-source fetch: {consolidation_result.total_before_dedup} raw → "
                    f"{consolidation_result.total_after_dedup} deduped "
                    f"({consolidation_result.duplicates_removed} dupes removed)"
                )
            except asyncio.TimeoutError:
                logger.error(f"Multi-source fetch timed out after {FETCH_TIMEOUT}s")
                if tracker:
                    await tracker.emit_error("Busca expirou por tempo")
                    remove_tracker(request.search_id)
                raise HTTPException(
                    status_code=504,
                    detail=(
                        f"A busca excedeu o tempo limite de {FETCH_TIMEOUT // 60} minutos. "
                        f"Tente com menos estados ou um período menor."
                    ),
                )
            finally:
                await consolidation_svc.close()
        else:
            # === PNCP-ONLY PATH (default, original behavior) ===
            logger.info(f"Fetching bids from PNCP API for {len(request.ufs)} UFs")

            async def _do_fetch() -> list:
                if use_parallel:
                    logger.info(f"Using parallel fetch for {len(request.ufs)} UFs (max_concurrent=10)")
                    try:
                        return await buscar_todas_ufs_paralelo(
                            ufs=request.ufs,
                            data_inicial=request.data_inicial,
                            data_final=request.data_final,
                            modalidades=modalidades_to_fetch,
                            status=status_value,
                            max_concurrent=10,
                            on_uf_complete=uf_progress_callback,
                        )
                    except Exception as e:
                        logger.warning(f"Parallel fetch failed, falling back to sequential: {e}")
                        client = PNCPClient()
                        return list(
                            client.fetch_all(
                                data_inicial=request.data_inicial,
                                data_final=request.data_final,
                                ufs=request.ufs,
                                modalidades=modalidades_to_fetch,
                            )
                        )
                else:
                    client = PNCPClient()
                    return list(
                        client.fetch_all(
                            data_inicial=request.data_inicial,
                            data_final=request.data_final,
                            ufs=request.ufs,
                            modalidades=modalidades_to_fetch,
                        )
                    )

            try:
                licitacoes_raw = await asyncio.wait_for(_do_fetch(), timeout=FETCH_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(f"PNCP fetch timed out after {FETCH_TIMEOUT}s for {len(request.ufs)} UFs")
                if tracker:
                    await tracker.emit_error("Busca expirou por tempo")
                    remove_tracker(request.search_id)
                raise HTTPException(
                    status_code=504,
                    detail=(
                        f"A busca excedeu o tempo limite de {FETCH_TIMEOUT // 60} minutos. "
                        f"Tente com menos estados ou um período menor."
                    ),
                )

        fetch_elapsed = sync_time.time() - start_time
        logger.info(f"Fetched {len(licitacoes_raw)} raw bids in {fetch_elapsed:.2f}s")

        # SSE: Fetch complete
        if tracker:
            await tracker.emit("fetching", 55, f"Busca concluida: {len(licitacoes_raw)} licitacoes encontradas", total_raw=len(licitacoes_raw))

        # Step 2: Enrich with inferred status (before filtering)
        # IMPORTANTE: A API PNCP não retorna status padronizado, então inferimos
        # baseado em datas (abertura, encerramento) e valores (homologado)
        logger.info("Enriching bids with inferred status...")
        enriquecer_com_status_inferido(licitacoes_raw)
        logger.info(f"Status inference complete for {len(licitacoes_raw)} bids")

        # SSE: Starting filtering
        if tracker:
            await tracker.emit("filtering", 60, f"Aplicando filtros em {len(licitacoes_raw)} licitacoes...")

        # Step 3: Apply ALL filters (fail-fast sequential)
        # Filter order (optimized for performance):
        # 1. UF (O(1) - already filtered at API level for parallel, but verify)
        # 2. Status (if specified)
        # 3. Esfera (if specified)
        # 4. Modalidade (if specified - may be filtered at API level)
        # 5. Município (if specified)
        # 6. Valor (if specified)
        # 7. Keywords (regex - most expensive)

        # Extract filter parameters from request
        esferas_values = [e.value for e in request.esferas] if request.esferas else None
        status_filter = request.status.value if request.status else "todos"

        logger.info(
            f"Applying filters: status={status_filter}, modalidades={request.modalidades}, "
            f"valor=[{request.valor_minimo}, {request.valor_maximo}], esferas={esferas_values}, "
            f"municipios={len(request.municipios) if request.municipios else 0}"
        )

        # Use the comprehensive filter function that applies all filters in order
        # AC3.1: Re-enable sector exclusions when custom terms + sector selected
        # AC3.2: No exclusions when custom terms without sector (generic/default)
        # AC3.3: User-provided exclusion_terms override sector exclusions
        if request.exclusion_terms:
            active_exclusions = set(request.exclusion_terms)
            active_context_required = None
        elif custom_terms and request.setor_id and request.setor_id != "vestuario":
            # AC3.1: Sector selected with custom terms — re-enable sector safety nets
            active_exclusions = sector.exclusions
            active_context_required = sector.context_required_keywords
        elif not custom_terms:
            # Sector-only mode: full exclusions (existing behavior)
            active_exclusions = sector.exclusions
            active_context_required = sector.context_required_keywords
        else:
            # AC3.2: Custom terms without specific sector — no exclusions
            active_exclusions = set()
            active_context_required = None

        licitacoes_filtradas, stats = aplicar_todos_filtros(
            licitacoes_raw,
            ufs_selecionadas=set(request.ufs),
            status=status_filter,
            modalidades=request.modalidades,
            valor_min=request.valor_minimo,
            valor_max=request.valor_maximo,
            esferas=esferas_values,
            municipios=request.municipios,
            keywords=active_keywords,
            exclusions=active_exclusions,
            context_required=active_context_required,
            min_match_floor=min_match_floor_value,
        )

        # AC2.3: Degradation — if min_match_floor produced 0 results, relax to 1
        hidden_by_min_match = stats.get("rejeitadas_min_match", 0)
        filter_relaxed = False

        if (
            custom_terms
            and min_match_floor_value is not None
            and min_match_floor_value > 1
            and len(licitacoes_filtradas) == 0
            and hidden_by_min_match > 0
        ):
            logger.warning(
                f"Min match floor relaxed from {min_match_floor_value} to 1 — "
                f"zero results with strict filter"
            )
            filter_relaxed = True
            # Re-run filter without min_match_floor
            licitacoes_filtradas, stats = aplicar_todos_filtros(
                licitacoes_raw,
                ufs_selecionadas=set(request.ufs),
                status=status_filter,
                modalidades=request.modalidades,
                valor_min=request.valor_minimo,
                valor_max=request.valor_maximo,
                esferas=esferas_values,
                municipios=request.municipios,
                keywords=active_keywords,
                exclusions=active_exclusions,
                context_required=active_context_required,
                min_match_floor=None,  # Relaxed — no minimum
            )
            hidden_by_min_match = 0  # All results now shown

        # STORY-178: Compute relevance scores for each bid when custom terms active
        if custom_terms and licitacoes_filtradas:
            from relevance import score_relevance, count_phrase_matches
            for lic in licitacoes_filtradas:
                matched_terms = lic.get("_matched_terms", [])
                phrase_count = count_phrase_matches(matched_terms)
                lic["_relevance_score"] = score_relevance(
                    len(matched_terms), len(custom_terms), phrase_count
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
            logger.info(f"  - Rejeitadas (Status): {stats.get('rejeitadas_status', 0)}")
            logger.info(f"  - Rejeitadas (Esfera): {stats.get('rejeitadas_esfera', 0)}")
            logger.info(f"  - Rejeitadas (Modalidade): {stats.get('rejeitadas_modalidade', 0)}")
            logger.info(f"  - Rejeitadas (Município): {stats.get('rejeitadas_municipio', 0)}")
            logger.info(f"  - Rejeitadas (Valor): {stats.get('rejeitadas_valor', 0)}")
            logger.info(f"  - Rejeitadas (Keyword): {stats.get('rejeitadas_keyword', 0)}")
            logger.info(f"  - Rejeitadas (Min Match): {stats.get('rejeitadas_min_match', 0)}")
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

        # SSE: Filtering complete
        if tracker:
            await tracker.emit("filtering", 70, f"Filtragem concluida: {len(licitacoes_filtradas)} resultados", total_filtered=len(licitacoes_filtradas))

        # Build filter stats for frontend
        fs = FilterStats(
            rejeitadas_uf=stats.get("rejeitadas_uf", 0),
            rejeitadas_valor=stats.get("rejeitadas_valor", 0),
            rejeitadas_keyword=stats.get("rejeitadas_keyword", 0),
            rejeitadas_min_match=stats.get("rejeitadas_min_match", 0),
            rejeitadas_prazo=stats.get("rejeitadas_prazo", 0),
            rejeitadas_outros=stats.get("rejeitadas_outros", 0),
        )

        # Early return if no results passed filters — skip LLM and Excel
        if not licitacoes_filtradas:
            logger.info("No bids passed filters — skipping LLM and Excel generation")
            if tracker:
                await tracker.emit_complete()
                remove_tracker(request.search_id)
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

            # Quota already incremented atomically at request start (check_and_increment_quota_atomic)
            # Use values from quota_info which were updated after atomic increment
            new_quota_used = quota_info.quota_used if quota_info else 0
            quota_remaining = quota_info.quota_remaining if quota_info else 0

            response = BuscaResponse(
                resumo=resumo,
                licitacoes=[],  # Empty list for zero results
                excel_base64=None if not quota_info or not quota_info.capabilities["allow_excel"] else "",
                excel_available=quota_info.capabilities["allow_excel"] if quota_info else False,
                quota_used=new_quota_used,
                quota_remaining=quota_remaining,
                total_raw=len(licitacoes_raw),
                total_filtrado=0,
                filter_stats=fs,
                termos_utilizados=custom_terms if custom_terms else None,
                stopwords_removidas=stopwords_removed if stopwords_removed else None,
                upgrade_message="Exportar Excel disponível no plano Máquina (R$ 597/mês)." if quota_info and not quota_info.capabilities["allow_excel"] else None,
                source_stats=source_stats_data,
                hidden_by_min_match=hidden_by_min_match if custom_terms else None,
                filter_relaxed=filter_relaxed if custom_terms else None,
            )
            logger.info(
                "Search completed with 0 results",
                extra={"total_raw": len(licitacoes_raw), "total_filtrado": 0},
            )

            # Save session even for zero results (for history tracking)
            if user:
                try:
                    from quota import save_search_session
                    session_id = save_search_session(
                        user_id=user["id"],
                        sectors=[request.setor_id],
                        ufs=request.ufs,
                        data_inicial=request.data_inicial,
                        data_final=request.data_final,
                        custom_keywords=custom_terms if custom_terms else None,
                        total_raw=len(licitacoes_raw),
                        total_filtered=0,
                        valor_total=0.0,
                        resumo_executivo=resumo.resumo_executivo,
                        destaques=[],
                    )
                    logger.info(f"Search session saved (0 results): {session_id[:8]}*** for user {mask_user_id(user['id'])}")
                except Exception as e:
                    logger.error(
                        f"Failed to save search session for user {mask_user_id(user['id'])}: {type(e).__name__}: {e}",
                        exc_info=True,
                    )

            return response

        # Step 2.5: Apply sorting/ordering
        # Sort results before LLM summary and Excel generation so order is consistent
        logger.info(f"Applying sorting: ordenacao='{request.ordenacao}'")
        licitacoes_filtradas = ordenar_licitacoes(
            licitacoes_filtradas,
            ordenacao=request.ordenacao,
            termos_busca=custom_terms if custom_terms else list(active_keywords)[:10],  # Use first 10 keywords for relevance
        )

        filter_elapsed = sync_time.time() - start_time
        logger.info(
            f"Filtering and sorting complete in {filter_elapsed:.2f}s: "
            f"{len(licitacoes_filtradas)} results ordered by '{request.ordenacao}'"
        )

        # SSE: Starting LLM
        if tracker:
            await tracker.emit("llm", 75, "Gerando resumo executivo com IA...")

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

        # SSE: LLM done, starting Excel
        if tracker:
            await tracker.emit("excel", 92, "Gerando planilha Excel...")

        # Step 4: Generate Excel report (conditional based on plan)
        excel_base64 = None
        excel_available = quota_info.capabilities["allow_excel"] if quota_info else False
        upgrade_message = None

        if excel_available:
            logger.info("Generating Excel report")
            excel_buffer = create_excel(licitacoes_filtradas)
            excel_base64 = base64.b64encode(excel_buffer.read()).decode("utf-8")
            logger.info(f"Excel report generated ({len(excel_base64)} base64 chars)")
        else:
            logger.info("Excel generation skipped (not allowed for user's plan)")
            upgrade_message = "Exportar Excel disponível no plano Máquina (R$ 597/mês)."

        # Quota already incremented atomically at request start (check_and_increment_quota_atomic)
        # Use values from quota_info which were updated after atomic increment
        new_quota_used = quota_info.quota_used if quota_info else 0
        quota_remaining = quota_info.quota_remaining if quota_info else 0

        # Step 5: Return response with individual bid items for preview
        licitacao_items = _convert_to_licitacao_items(licitacoes_filtradas)

        response = BuscaResponse(
            resumo=resumo,
            licitacoes=licitacao_items,  # Individual bids for frontend display
            excel_base64=excel_base64,
            excel_available=excel_available,
            quota_used=new_quota_used,
            quota_remaining=quota_remaining,
            total_raw=len(licitacoes_raw),
            total_filtrado=len(licitacoes_filtradas),
            filter_stats=fs,
            termos_utilizados=custom_terms if custom_terms else None,
            stopwords_removidas=stopwords_removed if stopwords_removed else None,
            upgrade_message=upgrade_message,
            source_stats=source_stats_data,
            hidden_by_min_match=hidden_by_min_match if custom_terms else None,
            filter_relaxed=filter_relaxed if custom_terms else None,
            ultima_atualizacao=datetime.now().isoformat() + "Z",
        )

        logger.info(
            "Search completed successfully",
            extra={
                "total_raw": response.total_raw,
                "total_filtrado": response.total_filtrado,
                "valor_total": resumo.valor_total,
            },
        )

        # Save session to history (for /historico page)
        # This must happen BEFORE returning the response
        if user:
            try:
                from quota import save_search_session
                session_id = save_search_session(
                    user_id=user["id"],
                    sectors=[request.setor_id],
                    ufs=request.ufs,
                    data_inicial=request.data_inicial,
                    data_final=request.data_final,
                    custom_keywords=custom_terms if custom_terms else None,
                    total_raw=len(licitacoes_raw),
                    total_filtered=len(licitacoes_filtradas),
                    valor_total=resumo.valor_total,
                    resumo_executivo=resumo.resumo_executivo,
                    destaques=resumo.destaques,
                )
                logger.info(f"Search session saved: {session_id[:8]}*** for user {mask_user_id(user['id'])}")
            except Exception as e:
                # Log detailed error but don't fail the search request
                logger.error(
                    f"Failed to save search session for user {mask_user_id(user['id'])}: {type(e).__name__}: {e}",
                    exc_info=True,
                )

        # SSE: Search complete
        if tracker:
            await tracker.emit_complete()
            remove_tracker(request.search_id)

        return response

    except PNCPRateLimitError as e:
        if tracker:
            await tracker.emit_error(f"PNCP rate limit: {e}")
            remove_tracker(request.search_id)
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
        if tracker:
            await tracker.emit_error(f"PNCP API error: {e}")
            remove_tracker(request.search_id)
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
        if tracker:
            await tracker.emit_error("Erro interno do servidor")
            remove_tracker(request.search_id)
        logger.exception("Internal server error during procurement search")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor. Tente novamente em alguns instantes.",
        )
