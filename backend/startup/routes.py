"""startup/routes.py — Router registration (DEBT-107).

Extracted from main.py to keep the app factory lean.
"""
from fastapi import FastAPI
# Routers
from admin import router as admin_router
from routes.subscriptions import router as subscriptions_router
from routes.upgrade_to_lifetime import router as upgrade_to_lifetime_router
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
from routes.auth_signup import router as auth_signup_router
from routes.health import router as cache_health_router
from routes.health_core import router as health_core_router
from routes.feedback import router as feedback_router
from routes.admin_trace import router as admin_trace_router
from routes.admin_cron import router as admin_cron_router
from routes.admin_cnae_mapping import router as admin_cnae_mapping_router
from routes.admin_llm_cost import router as admin_llm_cost_router
from routes.admin_calibration import router as admin_calibration_router
from routes.survey import router as survey_router
from routes.admin_billing_sync import router as admin_billing_sync_router
from routes.admin_founding import router as admin_founding_router
from routes.admin_metrics import router as admin_metrics_router
from routes.admin_sessions import router as admin_sessions_router
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
from routes.weekly_digest import router as weekly_digest_router
from routes.stats_public import router as stats_public_router
from routes.dados_publicos import router as dados_publicos_router
from routes.alertas_publicos import router as alertas_publicos_router
from routes.lead_capture import router as lead_capture_router
from routes.lead_magnet import router as lead_magnet_router
from routes.public_read import router as public_read_router
from routes.comparador import router as comparador_router
from routes.seo_admin import router as seo_admin_router
from routes.sitemap_cnpjs import router as sitemap_cnpjs_router
from routes.sitemap_orgaos import router as sitemap_orgaos_router
from routes.orgao_publico import router as orgao_publico_router
from routes.contratos_publicos import router as contratos_publicos_router
from routes.daily_digest import router as daily_digest_router
from routes.municipios_publicos import router as municipios_publicos_router
from routes.compliance_publicos import router as compliance_publicos_router
from routes.itens_publicos import router as itens_publicos_router
from routes.observatorio import router as observatorio_router
from routes.sitemap_licitacoes import router as sitemap_licitacoes_router
from routes.sitemap_licitacoes_do_dia import router as sitemap_licitacoes_do_dia_router
from routes.indice_municipal import router as indice_municipal_router
from routes.notifications import router as notifications_router
from routes.export import router as edital_export_router
from routes.founding import router as founding_router
from routes.founders import router as founders_router
from routes.founders_hall import router as founders_hall_router
from routes.conta import router as conta_router
from routes.intel_reports import router as intel_reports_router
from routes.pseo_data import router as pseo_data_router
from routes.seo_coverage_manifest import router as seo_coverage_manifest_router
from routes.products import router as products_router
from routes.datalake_api import router as datalake_api_router
from routes.api_keys import router as api_keys_router
from routes.checkout import router as checkout_router
from routes.seasonal_calendar import router as seasonal_calendar_router
from routes.network_events import router as network_events_router
from routes.segment import router as segment_router
from routes.api_search import router as api_search_router
from routes.email_tracking import router as email_tracking_router
from routes.admin_digest_metrics import router as admin_digest_metrics_router
from routes.admin_command import router as admin_command_router
from routes.admin_dlq import router as admin_dlq_router
from routes.admin_log_level import router as admin_log_level_router
from routes.admin_synthetic import router as admin_synthetic_router
from routes.intel_tasting import router as intel_tasting_router
from routes.predint import router as predint_router
from routes.monthly_report import router as monthly_report_router
from routes.intel_vitrine import router as intel_vitrine_router
from routes.pseo_intel_feed import router as pseo_intel_feed_router
from routes.widget_compint import router as widget_compint_router
from routes.competitive_intel import router as competitive_intel_router
from routes.consultoria import router as consultoria_router
from routes.subcontract import router as subcontract_router, health_router as subcontract_health_router
from routes.score import router as score_router
from routes.subcontract_intel import router as subcontract_intel_router
from routes.data_deletion import router as data_deletion_router
from routes.admin_alerts import router as admin_alerts_router
from routes.admin_circuit_breakers import router as admin_circuit_breakers_router
from routes.admin_data_retention import router as admin_data_retention_router
from routes.integrations import router as integrations_router
from routes.admin_db_pool import router as admin_db_pool_router
from routes.csp_report import router as csp_report_router
from routes.alerts_b2gops import router as alerts_b2gops_router
from routes.workspace_watchlist import router as workspace_watchlist_router
from routes.workspace_alertas import router as workspace_alertas_router
from routes.workspace_integracoes import router as workspace_integracoes_router
from routes.admin_outgoing_webhooks import router as admin_outgoing_webhooks_router
from routes.admin_audit_log import router as admin_audit_log_router
from routes.admin_rate_limits import router as admin_rate_limits_router
from routes.workspace import router as workspace_router
from routes.workspace_timeline import router as workspace_timeline_router
from routes.workspace_centro_guerra import router as workspace_centro_guerra_router
from routes.workspace_documentos import router as workspace_documentos_router
_v1_routers = [
    admin_router, admin_rate_limits_router, subscriptions_router, upgrade_to_lifetime_router,
    features_router, messages_router,
    analytics_router, oauth_router, export_sheets_router,
    search_router, user_router, billing_router, sessions_router, plans_router,
    emails_router, pipeline_router, onboarding_router, auth_email_router,
    auth_signup_router,
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
    weekly_digest_router,
    stats_public_router,
    dados_publicos_router,
    alertas_publicos_router,
    lead_capture_router,
    lead_magnet_router,
    public_read_router,
    comparador_router,
    seo_admin_router,
    sitemap_cnpjs_router,
    sitemap_orgaos_router,
    orgao_publico_router,
    contratos_publicos_router,
    daily_digest_router,
    municipios_publicos_router,
    compliance_publicos_router,
    itens_publicos_router,
    observatorio_router,
    sitemap_licitacoes_router,
    sitemap_licitacoes_do_dia_router,
    indice_municipal_router,
    notifications_router,
    edital_export_router,
    founding_router,
    conta_router,
    survey_router,
    intel_reports_router,
    pseo_data_router,
    seo_coverage_manifest_router,
    products_router,
    datalake_api_router,
    api_keys_router,
    seasonal_calendar_router,
    network_events_router,
    segment_router,
    api_search_router,
    intel_tasting_router,
    predint_router,
    monthly_report_router,
    intel_vitrine_router,
    pseo_intel_feed_router,
    competitive_intel_router,
    widget_compint_router,
    consultoria_router,
    subcontract_router,
    subcontract_health_router,
    score_router,
    subcontract_intel_router,
    data_deletion_router,
    integrations_router,
    csp_report_router,
    alerts_b2gops_router,
    workspace_router,
    workspace_timeline_router,
    workspace_watchlist_router,
    workspace_alertas_router,
    workspace_centro_guerra_router,
    workspace_integracoes_router,
    workspace_documentos_router,
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
    app.include_router(admin_cron_router)
    app.include_router(admin_cnae_mapping_router)
    app.include_router(admin_llm_cost_router)
    app.include_router(admin_calibration_router)
    app.include_router(admin_billing_sync_router)
    app.include_router(admin_founding_router)
    app.include_router(admin_metrics_router)
    app.include_router(admin_dlq_router)
    app.include_router(admin_sessions_router)
    app.include_router(slo_router)
    # Issue #1002: founders availability — self-prefixed at /api/founders/*
    # (NOT under /v1/ — public landing-page consumers + SEO programmatic).
    app.include_router(founders_router)
    # Issue #1008: Hall of Founders public listing + LGPD opt-in toggle.
    # Self-prefixed at /api/founders/hall/* — public listing + authenticated
    # consent toggle. Mirrors PR #1014's /api/founders/availability prefix.
    app.include_router(founders_hall_router)
    # CONV-005b-2: Checkout endpoint — self-prefixed at /api/checkout/*
    # (NOT under /v1/ — generic path for frontend convenience).
    app.include_router(checkout_router)
    # DIGEST-005 (#1421): Email tracking (open/click/unsubscribe) endpoints
    # Self-prefixed at /api/email/* — no auth, must be accessible from email clients
    app.include_router(email_tracking_router)
    # DIGEST-005 (#1421): Admin digest metrics dashboard widget
    app.include_router(admin_digest_metrics_router)
    # GAP-002 (#1579): Command plan provisioning — self-prefixed at /v1/admin/subscriptions/*
    app.include_router(admin_command_router)
    # #1814: Runtime log level toggle — self-prefixed at /v1/admin/log-level
    app.include_router(admin_log_level_router)
    # Issue #1869: Synthetic monitoring last-run — self-prefixed at /v1/admin/synthetic/last-run
    app.include_router(admin_synthetic_router)
    # #1865: Alert routing — self-prefixed at /v1/admin/test-alert
    app.include_router(admin_alerts_router)
    # #1877 AC2: Data retention status — self-prefixed at /v1/admin/data-retention/status
    app.include_router(admin_data_retention_router)
    # Issue #1919: Circuit breaker states — self-prefixed at /v1/admin/circuit-breakers
    app.include_router(admin_circuit_breakers_router)
    # Issue #1916: DB pool monitoring — self-prefixed at /v1/admin/db-pool
    app.include_router(admin_db_pool_router)
    # Issue #1959: Outgoing webhook deliveries — self-prefixed at /v1/admin/webhook-deliveries
    app.include_router(admin_outgoing_webhooks_router)
    # #1974: Admin audit log — query endpoint at /v1/admin/audit-log
    app.include_router(admin_audit_log_router)
    # Stripe webhook at root — DEBT-324: single registration only.
    # Removed from _v1_routers above to prevent duplicate at /v1/webhooks/stripe.
    # Stripe Dashboard must be configured with: POST /webhooks/stripe
    app.include_router(stripe_webhook_router)
