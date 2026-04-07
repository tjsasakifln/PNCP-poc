"""startup/routes.py — Router registration (DEBT-107).

Extracted from main.py to keep the app factory lean.
"""

from fastapi import FastAPI

# Routers
from admin import router as admin_router
from routes.subscriptions import router as subscriptions_router
from routes.features import router as features_router
from routes.messages import router as messages_router
from routes.analytics import router as analytics_router
from routes.auth_oauth import router as oauth_router
from routes.export_sheets import router as export_sheets_router
from webhooks.stripe import router as stripe_webhook_router
from routes.search import router as search_router
from routes.user import router as user_router
from routes.billing import router as billing_router
from routes.sessions import router as sessions_router
from routes.plans import router as plans_router
from routes.emails import router as emails_router
from routes.pipeline import router as pipeline_router
from routes.onboarding import router as onboarding_router
from routes.auth_email import router as auth_email_router
from routes.health import router as cache_health_router
from routes.health_core import router as health_core_router
from routes.feedback import router as feedback_router
from routes.admin_trace import router as admin_trace_router
from routes.auth_check import router as auth_check_router
from routes.bid_analysis import router as bid_analysis_router
from routes.slo import router as slo_router
from routes.alerts import router as alerts_router
from routes.trial_emails import router as trial_emails_router
from routes.mfa import router as mfa_router
from routes.organizations import router as org_router
from routes.partners import router as partners_router
from routes.sectors_public import router as sectors_public_router
from routes.reports import router as reports_router
from routes.blog_stats import router as blog_stats_router
from routes.metrics_api import router as metrics_api_router
from routes.feature_flags import router as feature_flags_router
from routes.feature_flags import public_router as feature_flags_public_router
from routes.calculadora import router as calculadora_router
from routes.empresa_publica import router as empresa_publica_router
from routes.share import router as share_router
from routes.referral import router as referral_router
from routes.relatorio import router as relatorio_router
from routes.trial_extension import router as trial_extension_router

_v1_routers = [
    admin_router, subscriptions_router, features_router, messages_router,
    analytics_router, oauth_router, export_sheets_router,
    search_router, user_router, billing_router, sessions_router, plans_router,
    emails_router, pipeline_router, onboarding_router, auth_email_router,
    cache_health_router, feedback_router, auth_check_router, bid_analysis_router,
    alerts_router, trial_emails_router, mfa_router, org_router, partners_router,
    sectors_public_router, reports_router, blog_stats_router, metrics_api_router,
    feature_flags_router,
    feature_flags_public_router,
    calculadora_router,
    empresa_publica_router,
    share_router,
    referral_router,
    relatorio_router,
    trial_extension_router,
]


def register_routes(app: FastAPI) -> None:
    """Register all application routers onto *app*."""
    # Health core at root (not /v1/) for container probes
    app.include_router(health_core_router)

    # All API routers at /v1/
    for r in _v1_routers:
        app.include_router(r, prefix="/v1")

    # Self-prefixed routers
    app.include_router(admin_trace_router)
    app.include_router(slo_router)

    # Stripe webhook at root — DEBT-324: single registration only.
    # Removed from _v1_routers above to prevent duplicate at /v1/webhooks/stripe.
    # Stripe Dashboard must be configured with: POST /webhooks/stripe
    app.include_router(stripe_webhook_router)
