# STORY-CONV-003c: Webhooks + Cron D-1 Email + Cancel One-Click + Observability + Rollback Docs

**Priority:** P0 — Fecha o ciclo trial→paid + compliance (cancelamento fácil)
**Effort:** L (2-3 dias)
**Squad:** @dev + @qa + @devops (deploy cron)
**Status:** InProgress (AC2 Done via PR #431; AC3 ~90% pré-existente via STORY-309; AC1/AC4/AC5/AC7 pendentes)
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Parent:** [STORY-CONV-003](STORY-CONV-003-cartao-obrigatorio-trial-stripe.story.md) (superseded)
**Depends on:** [STORY-CONV-003a](STORY-CONV-003a-backend-stripe-signup.story.md) ✅ Done via PR #408 + #423

---

## Contexto

Terceira e última parte da decomposição de CONV-003. Entrega (a) emails D-1 antes do charge, (b) cancelamento one-click com token JWT assinado, (c) Mixpanel + Prometheus para instrumentação de funil, (d) webhooks restantes (`invoice.payment_succeeded`, `invoice.payment_failed`) completando ciclo trial→paid, e (e) runbook de rollback para operar a feature flag em produção.

Fecha compliance essencial: usuário precisa conseguir cancelar em 1 clique antes do primeiro charge para minimizar chargebacks.

---

## Acceptance Criteria

### AC1: Email D-1 automático antes do charge
- [ ] ARQ cron job diário às 9h BRT: `backend/jobs/cron/trial_charge_warning.py`
- [ ] Query: profiles com `trial_end_ts` entre `now+22h` e `now+26h` (janela de 4h para garantir cobertura com drift)
- [ ] Envia email via Resend template `templates/emails/trial_charge_tomorrow.html`:
  - Subject: "Amanhã sua trial SmartLic expira — R$ 397 serão cobrados"
  - Body: CTA "Cancelar minha trial" (link assinado) + "Manter assinatura" (no-op)
- [ ] Template sanitizado (Pydantic para vars + HTML escape)
- [ ] Idempotência: marca `profiles.trial_charge_warning_sent_at` para não reenviar

### AC2: Endpoint cancel one-click via token JWT ✅ (via PR #431)
- [x] Token JWT `payload: {user_id, action: "cancel_trial", iat, exp: now+48h}`, chave `TRIAL_CANCEL_JWT_SECRET` (fallback para `SUPABASE_JWT_SECRET` em dev) — `backend/services/trial_cancel_token.py`
- [x] `GET /v1/conta/cancelar-trial?token=<jwt>` — retorna JSON metadata para UI (user_id, email, plan_name, trial_end_ts, already_cancelled). NÃO muta state.
- [x] `POST /v1/conta/cancelar-trial` body `{token}` executa:
  - Valida JWT (signature + exp + action=cancel_trial + user_id)
  - Chama `stripe.Subscription.cancel(sub_id)` — trials não geram proration
  - Atualiza `profiles.subscription_status='canceled_trial'`, `profiles.plan_type='free_trial'`, `user_subscriptions.is_active=false`
  - Retorna JSON `{ cancelled: true, access_until: <trial_end_ts>, already_cancelled: false|true }`
  - Idempotent: já cancelada → retorna 200 com `already_cancelled=true`
  - Fail-safe: erros Stripe logados mas cleanup local prossegue (billing recon STORY-314 reconcilia)
- [x] 19 testes passing local (`tests/test_cancel_trial_token.py`) — 7 service + 5 GET + 7 POST
- [ ] Frontend `/conta/cancelar-trial` page.tsx (consome GET + POST) — **deferido para CONV-003c frontend companion**

### AC3: Webhooks Stripe completos (trial→paid lifecycle) — ~90% pré-existente via STORY-309
- [x] `invoice.payment_failed` handler — `backend/webhooks/handlers/invoice.py::handle_invoice_payment_failed`:
  - Email dunning via `services/dunning.send_dunning_email` (STORY-309 AC3)
  - Mantém `plan_type='pro'` + marca `subscription_status='past_due'` (SUBSCRIPTION_GRACE_DAYS ativa)
  - Sentry capture_message + structured log `payment_failed_event`
  - Attempt count + decline_type (soft/hard) + decline_code extraídos
- [x] `invoice.payment_succeeded` handler — `backend/webhooks/handlers/invoice.py::handle_invoice_payment_succeeded`:
  - Atualiza `profiles.plan_type=<plan>`, `profiles.subscription_status='active'`
  - `user_subscriptions.expires_at` estendido por duration_days do plan
  - Email `render_payment_confirmation_email` (STORY-225 AC12)
  - `send_recovery_email` se was_past_due (STORY-309 AC11)
- [x] Idempotência via `stripe_webhook_events` table (dispatcher em `webhooks/stripe.py` — upsert on_conflict + claim com timeout 5min). Redis dedup alternativa equivalente.
- [ ] **PENDENTE: email `welcome_to_pro.html` específico para primeiro charge pós-trial** (current `render_payment_confirmation_email` é genérico de renewal; próxima sessão)
- [x] **Mixpanel event `trial_converted_auto`** — `backend/webhooks/handlers/invoice.py::handle_invoice_payment_succeeded` detecta `prior_status == "trialing"` e emite structured log `analytics.trial_converted_auto` com event + user_id + plan_id + amount_brl + stripe_subscription_id (pipeado para Mixpanel via log-sink)
- [x] **Handler para `invoice.payment_action_required` (3DS/SCA)** — já existe via STORY-309 AC10 em `handle_payment_action_required` + dispatcher routea em `webhooks/stripe.py` linha 208

### AC4: Observability end-to-end
- [ ] Mixpanel events:
  - `trial_card_captured` no signup (props: `rollout_branch`, `cnae`)
  - `trial_cancelled_before_charge` no cancel (props: `days_before_charge`)
  - `trial_converted_auto` no invoice.payment_succeeded primeiro ciclo
  - `trial_charge_failed` no invoice.payment_failed
- [ ] Prometheus counters:
  - `smartlic_trial_signup_with_card_total{branch="card"|"legacy"}`
  - `smartlic_trial_cancel_before_charge_total`
  - `smartlic_trial_auto_converted_total`
  - `smartlic_trial_charge_failed_total`
- [ ] Dashboard admin `/admin/billing/trial-funnel` (simples, tabela + 4 big numbers)

### AC5: Rollback plan documentado
- [ ] `docs/runbooks/trial-card-rollback.md`:
  - Trigger: conversion drop >50% em 7 dias OU chargeback rate >1%
  - Action: `railway variables set NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=0` (sem deploy, client lê via env next build; em produção com client-side hash, vira 0 imediato)
  - Backend cleanup: signups existentes com subscription trialing continuam processando normal; não mexer em Stripe data
  - Validação pós-rollback: monitoring Mixpanel `trial_card_captured` deve cair a 0 em <30min
- [ ] Runbook linkado em `docs/runbooks/README.md` (se existir) ou `docs/README.md`

### AC6: Testes backend ≥ 85% cobertura
- [ ] `backend/tests/test_trial_charge_warning_cron.py` — detecta trials expirando amanhã; idempotência
- [ ] `backend/tests/test_cancel_trial_token.py` — JWT válido, expirado, revogado, user inexistente
- [ ] `backend/tests/test_webhook_invoice_handlers.py` — `payment_succeeded`, `payment_failed`, idempotência
- [ ] `backend/tests/test_trial_funnel_metrics.py` — Mixpanel + Prometheus emission

### AC7: Testes frontend ≥ 75% cobertura
- [ ] `frontend/__tests__/conta/cancel-trial.test.tsx` — render página, cancelamento success, token inválido

---

## Arquivos (Criar/Modificar)

**Backend:**
- `backend/jobs/cron/trial_charge_warning.py` (novo)
- `backend/jobs/queue/definitions.py` (modificar — registrar cron)
- `backend/routes/conta.py` (novo ou modificar — handlers cancel-trial)
- `backend/services/trial_cancel_token.py` (novo — JWT sign/verify)
- `backend/webhooks/stripe.py` (modificar — invoice.payment_succeeded/failed handlers)
- `backend/templates/emails/trial_charge_tomorrow.html` (novo)
- `backend/templates/emails/welcome_to_pro.html` (novo)
- `backend/routes/admin_billing.py` (novo ou modificar — dashboard trial-funnel endpoint)

**Frontend:**
- `frontend/app/conta/cancelar-trial/page.tsx` (novo)
- `frontend/app/conta/cancelar-trial/confirmado/page.tsx` (novo)
- `frontend/app/admin/billing/trial-funnel/page.tsx` (novo — se permitido sem auditoria extra de segurança)

**Runbook:**
- `docs/runbooks/trial-card-rollback.md` (novo)

**Tests:** 4 backend + 1 frontend conforme AC6/AC7.

---

## Definition of Done

- [ ] AC1-AC7 todos `[x]`
- [ ] Cron testado em staging (trigger manual via ARQ admin ou similar)
- [ ] ≥1 charge automático bem-sucedido após 14 dias em staging (validação E2E)
- [ ] Dashboard `/admin/billing/trial-funnel` mostra conversion rate separada por branch (N≥5 signups por branch)
- [ ] Chargeback rate ≤ 0.5% nos primeiros 30 dias de rollout
- [ ] Runbook `docs/runbooks/trial-card-rollback.md` commitado

---

## Change Log

- **2026-04-19** — @sm (River): Sub-story criada a partir da decomposição de STORY-CONV-003. Status Ready. Bloqueia até CONV-003a em main; pode rodar em paralelo com CONV-003b.
- **2026-04-20** — @dev (bubbly-anchor consultor session, Opus 4.7): **AC2 COMPLETO via PR #431.**
  - `backend/services/trial_cancel_token.py` (137 linhas) — JWT HMAC-SHA256 sign/verify com action claim + TTL 48h + 5 error codes machine-readable
  - `backend/routes/conta.py` (239 linhas) — GET + POST `/v1/conta/cancelar-trial`, idempotent, fail-safe, structured log para Mixpanel
  - `backend/tests/test_cancel_trial_token.py` (294 linhas, 19 testes) — 7 service + 5 GET + 7 POST, incluindo happy path, expiry, invalid sig, wrong action, missing user, already cancelled, Stripe fail-safe
  - Router registrado em `startup/routes.py` (agora 60 routers total)
  - **AC3 ~90% pré-existente** — descoberto durante auditoria que `invoice.py::handle_invoice_payment_succeeded/failed` já implementa core lifecycle (STORY-309 AC11+AC3). Faltam apenas: `welcome_to_pro.html` email específico first-charge + Mixpanel `trial_converted_auto` event detection logic.
  - **AC4 parcial** — Mixpanel hook `analytics.trial_cancelled_before_charge` emitido via structured log; Prometheus counters + admin dashboard pendentes.
  - **Não incluído nesta sessão:** AC1 (cron email D-1), AC5 (runbook), AC7 (frontend page), AC6 pending (Mixpanel+Prometheus full suite + admin dashboard).
  - Status atualizado Ready → InProgress. Próxima sessão: AC1 cron + AC3 welcome_to_pro email + frontend page.
