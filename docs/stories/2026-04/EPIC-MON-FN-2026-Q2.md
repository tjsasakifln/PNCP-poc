# EPIC-MON-FN-2026-Q2 — Funil Monetização Fortune-500

**Status:** Draft
**Owner:** @pm (Morgan) + @dev (Dex) + @data-engineer (Dara)
**Quality Gate:** @qa (Quinn)
**Sprint Window:** 2026-04-29 → 2026-07-07 (10 semanas, 6 sprints)
**Origem:** Auditoria sistêmica + gap MIXPANEL_TOKEN backend (memory 2026-04-24) — plano `/home/tjsasakifln/.claude/plans/sistema-est-amea-ado-por-serene-hanrahan.md`

---

## Context

SmartLic operou com **2 signups em 30 dias** sob estratégia inbound, com pivô 2026-04-26 para 100% via SEO programático. Funil monetização atual tem 8 gaps críticos identificados:

1. **HMAC verify Resend webhook ausente** — bounces/complaints silenciosos; deliverability cega.
2. **Stripe webhook sem DLQ** — handler crash perde evento; tabela `stripe_webhook_events` é idempotente mas sem retry exponencial nem alert Sentry após falhas consecutivas.
3. **Plan status cache (5min TTL) sem invalidação atômica** — janela de até 5s onde usuário pago vê paywall pós-checkout.
4. **Race condition `/planos/obrigado`** — frontend redireciona antes do webhook Stripe confirmar `plan_type=paid`; UX falso positivo.
5. **MIXPANEL_TOKEN backend gap (memory 2026-04-24)** — eventos `paywall_hit`, `trial_started` silenciados em prod por período não definido.
6. **8 eventos críticos do funil ausentes** — `first_search`, `trial_expiring_d3/d1`, `trial_expired`, `checkout_started` (backend), `payment_failed` (parcial); funil cego em Mixpanel.
7. **Dunning workflow não implementado** — env var `SUBSCRIPTION_GRACE_DAYS=3` declarada mas sem ARQ job correspondente; payment fail = bloqueio imediato sem recovery.
8. **Sem free tier downsell** — trial expira → paywall instantâneo → 0 retention; LGPD data export/deletion ausentes (compliance Brasil).

`backend/email_service.py:195+` envia mas não valida assinatura Resend; `backend/webhooks/stripe.py` processa mas não enfileira retry; `backend/quota/quota_core.py:28` cacheia plan status com TTL puro; `backend/services/billing.py` atualiza `profiles.plan_type` sem pub/sub. Onboarding tracking depende de `localStorage smartlic_onboarding_completed` (frontend `GuidedTour.tsx`), com `first_search` server-side ausente em `backend/routes/search/`.

Backlog `trial → paid` (precificação, plano gating) permanece bloqueado até `n≥30` por princípio anti-noise-floor (decisões prematuras destroem valor). Este epic foca em **infra de funil**, não em decisão de produto.

---

## Goal

Instrumentar funil completo (first_search → trial → checkout → paid), implementar dunning, paywall com downsell e compliance LGPD em até 6 sprints (10 semanas).

---

## Business Value

- **Converte tráfego inbound em receita confiável** — pré-requisito para destravar backlog trial→paid quando n≥30.
- **Remove friction operacional** — email forçado pré-trial, race condition checkout, deliverability cega.
- **Compliance LGPD obrigatório (Brasil)** — sem isto risco multa ANPD.
- **Habilita decisões editoriais SEO via Mixpanel funnel** — quais rotas convertem? Sem eventos completos, decisões são especulativas.
- **Reduz churn voluntário** — dunning + free tier downsell + abandoned cart recovery; benchmark Fortune-500: dunning recupera 15-30% de payment fails.
- **ARPU/MRR/cohort visibility** — destrava decisões de pricing pós-n≥30 sem reconstrução de instrumentação.

---

## Success Metrics (binários ou numéricos pós-Sprint 6)

| # | Métrica | Baseline | Target | Fonte |
|---|---|---|---|---|
| 1 | Eventos críticos do funil emitidos backend | 4/12 (33%) | 12/12 (100%) | Mixpanel `events.list` |
| 2 | HMAC verify Resend webhook ativo | Não | Sim | code review + counter `smartlic_resend_webhook_invalid_total` |
| 3 | Stripe webhook DLQ size sustained | n/a | < 5 | Prometheus `smartlic_stripe_webhook_dlq_size` |
| 4 | Plan status cache invalidação atômica lag | até 5s (TTL) | < 500ms | Sentry breadcrumb timestamp delta |
| 5 | LGPD data export SLA | n/a | < 72h por request teste | E2E test |
| 6 | LGPD data deletion soft+hard delete | n/a | 100% audit log | DB query + audit table |
| 7 | Funnel Mixpanel dropout por estágio (signup→paid) | desconhecido | mensurável (todos estágios visíveis) | Mixpanel funnel |
| 8 | n cumulativo signups (destrava backlog trial→paid) | 2 | ≥ 30 | `profiles.created_at >= 2026-04-27` |
| 9 | Webhook handler success rate | desconhecido | ≥ 99.5% | Prometheus rate |
| 10 | Dunning recovery rate (Sprint 6+) | n/a | mensurável | Mixpanel `dunning_recovered` / `dunning_started` |

---

## Constraints

- **Pre-revenue** — n=2 baseline impede A/B test estatístico; decisões via instrumentação técnica (Sentry, Prometheus) e benchmarks Fortune-500.
- **Stripe Brasil compliance** — plan_billing_periods table sincronizada com Stripe; proration handled by Stripe; sem custom prorata.
- **LGPD obrigatório** — endpoints data-export e data-deletion são compliance, não feature.
- **Mixpanel quota free tier** — gerenciar volume de eventos; priorizar críticos.
- **Backlog trial→paid bloqueado até n≥30** — este epic não decide pricing/plan structure; entrega instrumentação para decisões futuras.
- **Resend domain verified** — domínio `smartlic.tech` já validado (memory: from `tiago@smartlic.tech` + reply-to gmail para outreach pessoal).
- **Stripe webhook idempotência atual** — tabela `stripe_webhook_events` ON CONFLICT já existe (STORY-307); este epic adiciona DLQ, não reescreve.

---

## Stories deste Epic

| ID | Título | Prio | Esforço | Sprint | Dep |
|---|---|---|---|---|---|
| [MON-FN-001](MON-FN-001-resend-webhook-hmac.md) | Resend webhook HMAC verify (svix-signature) | P0 | S | 1 | — |
| [MON-FN-002](MON-FN-002-stripe-webhook-dlq-retry.md) | Stripe webhook DLQ + retry exponencial (5 tentativas) | P0 | M | 1-2 | — |
| [MON-FN-003](MON-FN-003-plan-status-cache-atomic-invalidation.md) | Plan status cache invalidação atômica (Redis Pub/Sub) | P0 | M | 2 | MON-FN-002 |
| [MON-FN-004](MON-FN-004-checkout-obrigado-polling.md) | Race condition `/planos/obrigado` polling client-side | P0 | M | 2 | MON-FN-003 |
| [MON-FN-005](MON-FN-005-mixpanel-token-startup-assertion.md) | MIXPANEL_TOKEN startup assertion (boot fail se ausente) | P0 | S | 1 | — |
| [MON-FN-006](MON-FN-006-funnel-events-backend-complete.md) | 8 eventos funil backend completos (first_search → paid) | P0 | L | 2-3 | MON-FN-005 |
| [MON-FN-007](MON-FN-007-dunning-workflow.md) | Dunning workflow (D+1, D+2, D+3, suspend D+4) | P1 | L | 4-5 | MON-FN-006 |
| [MON-FN-008](MON-FN-008-free-tier-downsell.md) | Free tier (5 buscas/mês) como downsell paywall | P1 | L | 4-5 | MON-FN-006 |
| [MON-FN-009](MON-FN-009-abandoned-cart-recovery.md) | Abandoned cart recovery (checkout.session.expired + email) | P1 | M | 4 | MON-FN-006 |
| [MON-FN-010](MON-FN-010-lgpd-data-export.md) | LGPD data export endpoint (`POST /api/me/data-export`) | P1 | M | 3-4 | — |
| [MON-FN-011](MON-FN-011-lgpd-data-deletion.md) | LGPD data deletion (right to erasure, soft + hard D+30) | P1 | M | 4 | MON-FN-010 |
| [MON-FN-012](MON-FN-012-cohort-retention-dashboard.md) | Cohort retention dashboard (W1/W4/W12) | P2 | M | 6 | MON-FN-006 |
| [MON-FN-013](MON-FN-013-arpu-mrr-churn-analytics.md) | ARPU/MRR/churn analytics dashboard | P2 | M | 6 | MON-FN-007 |
| [MON-FN-014](MON-FN-014-onboarding-server-side-tracking.md) | Onboarding tracking server-side (deprecate localStorage) | P1 | S | 3 | MON-FN-006 |
| [MON-FN-015](MON-FN-015-email-confirm-soft-bypass.md) | Email confirmation soft-bypass (browse + 1ª busca pré-verify) | P1 | M | 5 | — |

---

## Sequenciamento Crítico

```
Sprint 1 (29/abr–05/mai):  MON-FN-001, MON-FN-002, MON-FN-005 (P0 paralelos)
Sprint 2 (06–12/mai):      MON-FN-003 → MON-FN-004
                           MON-FN-006 (eventos funil; depende de MON-FN-005)
Sprint 3 (13–19/mai):      MON-FN-006 (continuação)
                           MON-FN-010 (LGPD export)
                           MON-FN-014 (onboarding tracking)
Sprint 4 (20–26/mai):      MON-FN-009 (abandoned cart)
                           MON-FN-011 (LGPD deletion)
                           MON-FN-007 (dunning) [início]
Sprint 5 (27/mai–02/jun):  MON-FN-007 (dunning) [conclusão]
                           MON-FN-008 (free tier)
                           MON-FN-015 (email soft-bypass)
Sprint 6 (03–09/jun):      MON-FN-012 (cohort), MON-FN-013 (ARPU)
```

---

## Validation Framework

### Mixpanel funnel (PRIMARY)

```
signup_started
  → signup_completed
  → onboarding_completed
  → first_search
  → paywall_hit
  → checkout_started
  → checkout_completed
  → trial_started
  → trial_expiring_d3
  → trial_expiring_d1
  → trial_expired | trial_converted
  → payment_failed | dunning_started → dunning_recovered | dunning_lost
```

### Prometheus

- `smartlic_stripe_webhook_dlq_size` — < 5 sustained
- `smartlic_resend_webhook_invalid_total` — alerta se rate > 0
- `smartlic_dunning_started_total`, `_recovered_total`, `_lost_total`
- `smartlic_plan_cache_invalidation_lag_seconds` — p99 < 0.5s
- `smartlic_lgpd_export_duration_seconds` — < 72h target

### Sentry

- Webhook handler errors = 0 (alarme se > 0/min sustained)
- Fingerprint `["stripe_webhook_dlq", event_type]` para retries esgotados
- Fingerprint `["lgpd_export_failed", user_id]` para SLA violado

### E2E Playwright tests

- Trial signup → first_search → paywall_hit (eventos visíveis Mixpanel)
- Checkout → /planos/obrigado polling até `plan_type=paid` (max 30s)
- LGPD data export request → email com link em ≤72h
- Dunning sequence (mock past_due via Stripe test) — D+1/D+2/D+3 emails enviados

---

## Rollback Strategy

| Trigger | Ação |
|---|---|
| Webhook handler error rate > 1% | Pausar dunning ARQ jobs; reverter cache invalidation para TTL puro |
| DLQ size growing > 50 | Alertar finance; manualmente reprocessar via admin panel |
| LGPD endpoint SLA violado | Disable feature flag `LGPD_EXPORT_ENABLED=false`; processar manualmente |
| Free tier mass-abuse (>1000 signups/dia) | Tightening quota free → 2 buscas/mês; rate limit por IP |
| Mixpanel quota exceeded | Sample eventos não-críticos; manter funil completo |

---

## Out-of-Scope (deste Epic)

- **Decisão de pricing/plan gating** — bloqueado por n≥30; reabrir backlog trial→paid pós-Sprint 6.
- **Custom prorata logic** — Stripe nativo cobre.
- **Multi-currency** — Brasil-only (BRL).
- **Chargeback automation** — escopo legal/finance separado.
- **Affiliate/referral program** — STORY-364 separado.
- **Annual upgrade flow** — Stripe portal cobre default.
- **Tax calculation por estado** — Stripe Tax cobre se ativado (decisão financeira separada).
- **Anti-fraud (Stripe Radar custom rules)** — Stripe default suficiente pre-revenue.

---

## Dependencies (entrada)

- Plano aprovado: `/home/tjsasakifln/.claude/plans/sistema-est-amea-ado-por-serene-hanrahan.md`
- Stories existentes: STORY-307 (Stripe webhook idempotência), STORY-OBS-001 (retention 400d).
- Memory: `reference_mixpanel_backend_token_gap_2026_04_24`, `reference_trial_email_log_delivery_status_null`, `reference_admin_bypass_paywall`.

## Dependencies (saída)

- **Backlog trial→paid** desbloqueia quando MON-FN-006 + n≥30 atingidos.
- **Decisões editoriais SEO** consomem MON-FN-006 funnel events para priorizar conteúdo.

---

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Epic criado a partir do plano de auditoria pós-P0 + gap MIXPANEL | @sm (River) |
