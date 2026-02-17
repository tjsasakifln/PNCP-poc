# GTM-FIX-002: Enable Production Observability

## Dimension Impact
- Moves D06 (Observability) from 5/10 to 7/10
- Moves D13 (Analytics) from 3/10 to 5/10

## Problem
Code is instrumented for Sentry error tracking and Mixpanel analytics, but environment variables (SENTRY_DSN, NEXT_PUBLIC_SENTRY_DSN, NEXT_PUBLIC_MIXPANEL_TOKEN) are not configured in Railway production. Currently receiving zero error reports and zero analytics data.

## Solution
1. Create Sentry project at sentry.io (or use existing SmartLic project)
2. Copy DSN from Sentry project settings
3. Set SENTRY_DSN + NEXT_PUBLIC_SENTRY_DSN in Railway (backend + frontend services)
4. Create Mixpanel project at mixpanel.com (or use existing)
5. Set NEXT_PUBLIC_MIXPANEL_TOKEN in Railway frontend service
6. Verify Sentry receives test error
7. Verify Mixpanel receives test event

## Acceptance Criteria
- [ ] AC1: Sentry project exists for SmartLic/BidIQ
- [ ] AC2: SENTRY_DSN set in Railway backend environment variables
- [ ] AC3: NEXT_PUBLIC_SENTRY_DSN set in Railway frontend environment variables
- [ ] AC4: NEXT_PUBLIC_MIXPANEL_TOKEN set in Railway frontend environment variables
- [ ] AC5: Trigger test error in production → appears in Sentry within 1 minute
- [ ] AC6: Trigger test analytics event → appears in Mixpanel within 1 minute
- [ ] AC7: Sentry captures unhandled exceptions (test with `throw new Error('test')`)
- [ ] AC8: Mixpanel tracks page views and search events

## Effort: XS (30min)
## Priority: P0 (Zero visibility into production)
## Dependencies: None

## Files to Modify
- Railway dashboard: Environment variables (no code changes needed)

## Testing Strategy
1. Set env vars in Railway → trigger redeployment
2. Open production site → open browser console → execute: `Sentry.captureMessage('Test from GTM-FIX-002')`
3. Check Sentry dashboard for message within 60s
4. Execute search → check Mixpanel dashboard for `search_completed` event
5. Verify error breadcrumbs include request context (user_id, url, timestamp)

## Post-Deployment Checklist
- [ ] Add Sentry DSN and Mixpanel token to `.env.example` with placeholder values
- [ ] Document observability setup in `docs/guides/observability.md`
- [ ] Set up Sentry alerts for critical errors (payment failures, auth errors)
- [ ] Create Mixpanel dashboard for key metrics (searches/day, conversions, retention)

## ⚠️ REVISÃO — Impacto PCP API (2026-02-16)

**Contexto:** Com a integração do Portal de Compras Públicas (GTM-FIX-011), a observabilidade precisa distinguir entre fontes.

**Adições (sem alterar ACs existentes):**

1. **Novo AC9:** Configurar Sentry tag `data_source` com valores `pncp` | `pcp` para erros de API, permitindo filtrar/alertar por fonte.

2. **Novo AC10:** Mixpanel events de busca devem incluir property `sources_used: ["pncp", "pcp"]` para analytics de cobertura por fonte.

3. **Post-deployment:** Criar alert Sentry específico: "PCP API errors > 10/hour" (monitorar estabilidade da nova API nas primeiras semanas).

4. **Impacto no effort:** +5min (apenas 1 alert adicional). Mantém XS.
