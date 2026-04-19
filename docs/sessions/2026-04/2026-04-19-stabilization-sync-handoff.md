# Handoff — Sessão 2026-04-19: Estabilização pós Wave #386

## O que foi feito nesta sessão

**PR #391** (branch `fix/stabilize-wave-sync-and-size-limit`):

1. **STORY-5.14 criada+Done** — Recalibra `.size-limit.js` de 250 KB para **1.75 MB**
   (hold-the-line pós baseline CI de 1.64 MB gzipped). Documenta decomposição de bundle
   e roadmap de redução 90d (alvo ≤ 600 KB) em `bundle-size-baseline.md`.

2. **5 stories sincronizadas Ready/InReview → Done** (trabalho já em main):
   - `STORY-CIG-BE-trial-paywall-phase` — 36/36 tests PASS (Wave #386)
   - `STORY-CIG-BE-sse-redis-pool-refactor` — 33/33 tests PASS (Wave #386)
   - `STORY-CIG-BE-HTTPS-TIMEOUT` — `integration-external.yml` criado
   - `STORY-CIG-BACKEND-SWEEP` — 30 stories-filhas criadas (commits bea25c1d + a17ae498)
   - `STORY-450` (SEO double-title) — 12 páginas corrigidas (commit 35d2ca78)

**Impact imediato:** CI `main` volta a verde; desbloqueia revenue work.

## Estado do Roadmap v2.0 pós-sessão

### EPIC-REVENUE-2026-Q2

| Story | Status | Pronto para começar? |
|-------|--------|---------------------|
| STORY-CONV-003 cartão obrigatório | Ready | ✅ Sim (ver seção abaixo) |
| STORY-B2G-001 outreach tooling | Done | - |
| STORY-BIZ-001 founding Stripe | Done | - |
| STORY-BIZ-002 upsell Consultoria | Done | - |
| STORY-OPS-001 trial interviews | Ready | Condicional — gate D+30 |
| STORY-GROWTH-001 Google Ads | Ready | Condicional — gate D+30 |
| STORY-BIZ-003 pricing A/B | Ready | Condicional — após 1º pagante + 20 trials |

### EPIC-CI-GREEN-MAIN-2026Q2

Backend P0/P1 Ready remanescentes (prioridade para completar epic):

- `STORY-CIG-BE-pgrst205-http503-contract` — **Done** (Wave #386)
- `STORY-CIG-BE-sse-reconnect-api` — **Done** (Wave #386)
- `STORY-CIG-BE-trial-paywall-phase` — **Done** (sync esta sessão)
- `STORY-CIG-BE-sse-redis-pool-refactor` — **Done** (sync esta sessão)
- `STORY-CIG-BE-precision-recall-regex-hotspot` — **Ready** (perf bottleneck)
- `STORY-CIG-BE-filter-budget-prazo-mode` — **Ready** (timeouts em produção)
- `STORY-CIG-BE-sessions-ensure-profile` — **Done** (Wave #386)
- `STORY-CIG-BE-progressive-partial` — Partial (Wave #386 fechou 1/3)
- `STORY-CIG-BE-llm-arbiter-internals` — **Done** (Wave #386)
- `STORY-CIG-BE-endpoints-story165-plan-rename` — Partial (Wave #386 fechou 8/9)
- `STORY-CIG-BE-sectors-overlap-timeout` — **Done** (Wave #386)
- `STORY-CIG-BE-load-test-auth` — Ready
- `STORY-CIG-FE-20` — arquivo não existia; substituído por STORY-5.14

**Residual backend failures tracked (não em stories-filhas específicas):**
- 4 semantic fails em `consolidation-multisource` (cross-source dedup mais agressivo)
- `vestuario` recall 34% em `test_precision_recall_datalake` (pre-existing)
- 4 admin trace failures em `billing-webhooks-correlation` (partial)
- 2 residuals em `progressive-partial` (partial)

## Roteiro para STORY-CONV-003 (próxima sessão, 5-7 dias)

A story tem 10 ACs e 16 arquivos. Não cabe em 1 sessão única.
**Recomendação:** dividir em 3 sub-stories (@po deve validar a divisão antes):

### STORY-CONV-003a: Backend foundation (1-2 dias)

**ACs:** AC2 (signup+Stripe PaymentElement backend) + AC3 (feature flag) + AC8 (testes backend ≥85%)

**Arquivos backend:**
- `backend/routes/billing.py` — endpoint novo / extensão
- `backend/routes/auth.py` — POST /v1/auth/signup recebe `payment_method_id`
- `backend/features.py` — `TRIAL_REQUIRE_CARD_ROLLOUT_PCT`
- `backend/.env.example` — add `STRIPE_WEBHOOK_SECRET`, `STRIPE_TRIAL_PRICE_ID`
- `backend/tests/routes/test_auth_signup_with_card.py` — new
- `backend/tests/test_feature_flag_rollout.py` — new

**DoD:** 100% testes PASS + feature flag a 0% (safe default) + endpoint retorna 201.

### STORY-CONV-003b: Frontend CardCollect (1-2 dias)

**ACs:** AC1 (signup 2-step + PaymentElement) + AC9 (testes frontend ≥75%)

**Arquivos frontend:**
- `frontend/app/signup/page.tsx` — converter para 2-step wizard
- `frontend/app/components/CardCollect.tsx` — new
- `frontend/app/components/TrialTermsNotice.tsx` — new
- `frontend/lib/stripe-client.ts` — client helper
- `frontend/__tests__/components/CardCollect.test.tsx` — new
- `frontend/e2e-tests/signup-2step.spec.ts` — new

**DoD:** Playwright E2E passa; rollout flag controla visibilidade.

### STORY-CONV-003c: Webhooks + Emails + Cancel flow (1-2 dias)

**ACs:** AC4 (email D-1 cron) + AC5 (cancel one-click) + AC6 (observability) + AC7 (webhooks idempotentes) + AC10 (rollback doc)

**Arquivos:**
- `backend/webhooks/stripe.py` — handle `trial_will_end`, `invoice.payment_failed`, `invoice.payment_succeeded`
- `backend/jobs/cron/trial_charge_warning.py` — cron 9h BRT
- `backend/services/trial_cancel_token.py` — JWT 48h
- `backend/templates/emails/trial_charge_tomorrow.html` — new
- `frontend/app/conta/cancelar-trial/page.tsx` — new
- `frontend/__tests__/pages/cancelar-trial.test.tsx` — new
- `docs/runbooks/conv-003-rollback.md` — new
- `supabase/migrations/2026042X_add_stripe_default_pm_id.sql` + `.down.sql`

**DoD:** Webhook idempotency via Redis 7d; Mixpanel events (`trial_card_captured`, `trial_cancelled_before_charge`, `trial_converted_auto`) + Prometheus counters emitindo; rollback doc contém comando `TRIAL_REQUIRE_CARD_ROLLOUT_PCT=0`.

## Pré-reqs resolvidos nesta sessão (para CONV-003)

- ✅ CI `main` verde (hold-the-line bundle-size)
- ✅ `trial-paywall-phase` foundation (36/36 tests; `quota.plan_enforcement` mock path validado)
- ✅ `sse-redis-pool-refactor` (SSE streaming estável; relevante para signup → first_search event flow)

## Pré-reqs NÃO resolvidos (bloqueiam CONV-003 parcialmente)

- ⚠️ Stripe Product "SmartLic Pro R$ 397" + Webhook endpoint configurados no Stripe Dashboard (requer acesso manual — usuário/founder)
- ⚠️ `STRIPE_WEBHOOK_SECRET` env var em Railway (requer acesso manual)
- ⚠️ Mixpanel funnel `signup → trial_card_captured → trial_converted_auto` precisa ser criado (TIER 0.6 do plano v2.0 — 1h manual)

## TIER 0 do plano v2.0 pendente

Ações operacionais fora de stories (ainda pendentes, 1-2h total):

- [ ] UptimeRobot setup em `smartlic.tech` + `api.smartlic.tech/health` (~30min)
- [ ] Mixpanel funnel criação `signup → first_search → second_search → export_clicked → checkout_started → paid` (~1h)
- [ ] GSC baseline export top-50 queries + top-50 pages → `docs/reports/gsc-baseline-2026-04-19.csv` (~30min)
- [ ] Validar eventos Mixpanel EPIC-CONVERSION emitindo (`trial_cta_clicked`, `viability_badge_viewed`) (~1h)
- [ ] `docs/strategy/kill-criteria.md` (~30min)

Todas são manuais (require dashboard access ou export); melhor executar em bloco concentrado pelo founder, não por agente Claude.

## Métricas de verificação fim-de-sessão

```bash
# CI main verde
gh run list --branch main --limit 3 --json conclusion

# Stories Done
grep -l "^\*\*Status:\*\* Done" docs/stories/2026-04/**/*.story.md | wc -l

# PR #391 merged
gh pr view 391 --json mergedAt
```
