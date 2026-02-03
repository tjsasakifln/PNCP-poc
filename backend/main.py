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
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from config import setup_logging
from schemas import BuscaRequest, BuscaResponse, FilterStats, ResumoLicitacoes
from pncp_client import PNCPClient
from exceptions import PNCPAPIError, PNCPRateLimitError
from filter import filter_batch, remove_stopwords
from excel import create_excel
from llm import gerar_resumo, gerar_resumo_fallback
from sectors import get_sector, list_sectors
from auth import get_current_user, require_auth
from admin import router as admin_router

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
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],  # Allow all headers for development
)

app.include_router(admin_router)

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
            client = get_supabase()
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
    except Exception as e:
        logger.error(f"Password change failed for user {user['id']}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao alterar senha")

    logger.info(f"Password changed for user {user['id']}")
    return {"success": True}


def _get_admin_ids() -> set[str]:
    """Get admin user IDs from environment variable."""
    raw = os.getenv("ADMIN_USER_IDS", "")
    return {uid.strip() for uid in raw.split(",") if uid.strip()}


@app.get("/me")
async def get_profile(user: dict = Depends(require_auth)):
    """Get current user profile with active subscription info."""
    from supabase_client import get_supabase
    sb = get_supabase()

    profile = (
        sb.table("profiles")
        .select("*")
        .eq("id", user["id"])
        .single()
        .execute()
    )

    # Get active subscription
    sub = (
        sb.table("user_subscriptions")
        .select("*, plans(*)")
        .eq("user_id", user["id"])
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    # Count total searches (for free tier tracking)
    sessions = (
        sb.table("search_sessions")
        .select("id", count="exact")
        .eq("user_id", user["id"])
        .execute()
    )

    # Check if user is admin
    admin_ids = _get_admin_ids()
    is_admin = user["id"] in admin_ids

    return {
        "profile": profile.data,
        "subscription": sub.data[0] if sub.data else None,
        "total_searches": sessions.count or 0,
        "is_admin": is_admin,
    }


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

    logger.info(f"Activated plan {plan_id} for user {user_id}")


def _deactivate_stripe_subscription(stripe_sub_id: str):
    """Deactivate subscription when cancelled in Stripe."""
    from supabase_client import get_supabase
    sb = get_supabase()
    sb.table("user_subscriptions").update({"is_active": False}).eq("stripe_subscription_id", stripe_sub_id).execute()
    logger.info(f"Deactivated Stripe subscription {stripe_sub_id}")


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
    logger.info(
        "Starting procurement search",
        extra={
            "ufs": request.ufs,
            "data_inicial": request.data_inicial,
            "data_final": request.data_final,
            "setor_id": request.setor_id,
        },
    )

    # Quota check (user is always authenticated due to require_auth)
    quota_info = None
    try:
        from quota import check_quota, QuotaExceededError
        quota_info = check_quota(user["id"])
    except QuotaExceededError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except RuntimeError as e:
        # Configuration error (missing env vars) - fail fast
        logger.error(f"Supabase configuration error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Serviço temporariamente indisponível. Tente novamente em alguns minutos."
        )
    except Exception as e:
        # Unexpected error - log but continue (user already authenticated)
        logger.warning(f"Quota check failed (continuing without quota tracking): {e}")

    try:
        # Load sector configuration
        try:
            sector = get_sector(request.setor_id)
        except KeyError as e:
            raise HTTPException(status_code=400, detail=str(e))

        logger.info(f"Using sector: {sector.name} ({len(sector.keywords)} keywords)")

        # Determine keywords: custom terms REPLACE sector keywords (mutually exclusive)
        custom_terms: list[str] = []
        stopwords_removed: list[str] = []
        if request.termos_busca and request.termos_busca.strip():
            raw_terms = [t.strip().lower() for t in request.termos_busca.strip().split() if t.strip()]
            custom_terms = remove_stopwords(raw_terms)
            stopwords_removed = [t for t in raw_terms if t not in custom_terms]
            if stopwords_removed:
                logger.info(f"Removed {len(stopwords_removed)} stopwords: {stopwords_removed}")

        if custom_terms:
            active_keywords = set(custom_terms)
            logger.info(f"Using {len(custom_terms)} custom search terms: {custom_terms}")
        else:
            active_keywords = set(sector.keywords)
            if stopwords_removed:
                logger.warning(
                    f"All user terms were stopwords ({stopwords_removed}), "
                    f"falling back to sector '{sector.id}' keywords"
                )
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
                termos_utilizados=custom_terms if custom_terms else None,
                stopwords_removidas=stopwords_removed if stopwords_removed else None,
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
            termos_utilizados=custom_terms if custom_terms else None,
            stopwords_removidas=stopwords_removed if stopwords_removed else None,
        )

        logger.info(
            "Search completed successfully",
            extra={
                "total_raw": response.total_raw,
                "total_filtrado": response.total_filtrado,
                "valor_total": resumo.valor_total,
            },
        )

        # Save session + decrement credits (only for authenticated users)
        if user:
            try:
                from quota import save_search_session, decrement_credits
                save_search_session(
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
                if quota_info and quota_info.get("subscription_id"):
                    decrement_credits(quota_info["subscription_id"], user["id"])
            except Exception as e:
                logger.error(f"Failed to save session/decrement credits: {e}")

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
