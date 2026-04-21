# STORY-CONV-003c: Webhooks + Cron D-1 Email + Cancel One-Click + Observability + Rollback Docs

**Priority:** P0 — Fecha o ciclo trial→paid + compliance (cancelamento fácil)
**Effort:** L (2-3 dias)
**Squad:** @dev + @qa + @devops (deploy cron)
**Status:** InProgress (AC2 Done via PR #431 merged `0ef5902f`; AC3 + AC5 + AC7 em PR #433 — CI cascade; AC1 cron + AC4 observability dashboard deferidos)
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Parent:** [STORY-CONV-003](STORY-CONV-003-cartao-obrigatorio-trial-stripe.story.md) (superseded)
**Depends on:** [STORY-CONV-003a](STORY-CONV-003a-backend-stripe-signup.story.md) ✅ Done via PR #408 + #423

---

## Contexto

Terceira e última parte da decomposição de CONV-003. Entrega (a) emails D-1 antes do charge, (b) cancelamento one-click com token JWT assinado, (c) Mixpanel + Prometheus para instrumentação de funil, (d) webhooks restantes (`invoice.payment_succeeded`, `invoice.payment_failed`) completando ciclo trial→paid, e (e) runbook de rollback para operar a feature flag em produção.

Fecha compliance essencial: usuário precisa conseguir cancelar em 1 clique antes do primeiro charge para minimizar chargebacks.

---

## Acceptance Criteria

### AC1: Email D-1 automático antes do charge — ✅ Implemented via Abstract Coral session (branch-aware reuse)
- [x] **Cron infrastructure reused from STORY-321** (`services/trial_email_sequence.py` Day 13 "last_day"): already daily at 08:00 BRT with idempotency via `trial_email_log` table and `trial_conversion_emails_enabled` opt-out respected. No new cron needed.
- [x] **Query:** profiles at `created_at between now-13d-12h and now-12d+12h` (24h window) — already in `process_trial_emails` dispatcher.
- [x] **Branch-aware copy:** `render_trial_last_day_card_email` in `backend/templates/emails/trial.py` emits compliance-correct Day 13 for users with `profiles.stripe_default_pm_id` set (card rollout). Legacy `render_trial_last_day_email` continues for users without card. Dispatcher in `trial_email_sequence._render_email::last_day` branches on `has_payment_method`.
  - **Subject (card branch):** `"{N} oportunidades em 14 dias — amanhã vira SmartLic Pro"` (ROI-focused + urgência suave, approved 2026-04-21)
  - **Body (card branch):** ROI headline + explicit charge notice (date, plan, amount) + one-click `[CANCELAR MINHA TRIAL]` CTA (JWT link via `services.trial_cancel_token.create_cancel_trial_token`, 48h TTL) + brand sign-off
- [x] **Template safety:** HTML built via typed helpers (`_format_brl`, `_format_charge_date_display`) + static template; no raw user input interpolation beyond `user_name` which is already sanitized by Supabase auth constraints.
- [x] **Idempotência:** already-enforced via `trial_email_log` UPSERT ON CONFLICT DO NOTHING (`email_number=5`, STORY-321 AC6).
- [x] **Graceful degradation:** JWT mint failure falls back to unauthenticated `/conta/cancelar-trial` URL — email never blocked on secret config issue.
- [x] **Tests:** 18 new tests in `backend/tests/test_trial_emails.py` (`TestLastDayCardEmail`, `TestLastDayCardBranchDispatch`, `TestFormatChargeDateDisplay`) — render, cancel-CTA, link embedding, branch dispatch, fallback path, ISO date parsing all covered.

**Design note:** original AC1 proposed a brand-new `trial_charge_warning.py` cron. Investigation found STORY-321 already runs Day 13 "last_day" with full dispatch + idempotency + opt-out infrastructure. Reusing that avoids dual-cron conflict (see CRIT-044) and delivers the same user-visible behavior at ~1/3 the effort.

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
- [x] **email `welcome_to_pro` específico para primeiro charge pós-trial** — `backend/templates/emails/billing.py::render_welcome_to_pro_email` (dedicated template distinct from `render_payment_confirmation_email`), despachado via `invoice.py:336-345` quando `is_first_charge_after_trial=was_trialing`. Tests in `backend/tests/test_welcome_to_pro_email.py` (8 tests — render + dispatcher branch). Validated via Abstract Coral session 2026-04-21.
- [x] **Mixpanel event `trial_converted_auto`** — `backend/webhooks/handlers/invoice.py::handle_invoice_payment_succeeded` detecta `prior_status == "trialing"` e emite structured log `analytics.trial_converted_auto` com event + user_id + plan_id + amount_brl + stripe_subscription_id (pipeado para Mixpanel via log-sink)
- [x] **Handler para `invoice.payment_action_required` (3DS/SCA)** — já existe via STORY-309 AC10 em `handle_payment_action_required` + dispatcher routea em `webhooks/stripe.py` linha 208

### AC4: Observability end-to-end — ✅ Events + counters Done (Abstract Coral session). Dashboard P2 deferred.
- [x] Mixpanel events (emitidos via structured logger `analytics.*` → log-sink → Mixpanel):
  - [x] `trial_card_captured` em `backend/routes/auth_signup.py` (após full card path success: Customer + SetupIntent + Subscription). Props: `rollout_branch=card`, `stripe_customer_id`, `stripe_subscription_id`.
  - [x] `trial_cancelled_before_charge` em `backend/routes/conta.py` (POST /v1/conta/cancelar-trial success path). Props: `user_id`, `trial_end_ts`, `source=one_click_email`. **Implementado via PR #431 em sessão anterior.**
  - [x] `trial_converted_auto` em `backend/webhooks/handlers/invoice.py::handle_invoice_payment_succeeded` (prior_status=trialing branch). Props: `user_id`, `plan_id`, `amount_brl`, `stripe_subscription_id`. **Implementado via PR #431/#433.**
  - [x] `trial_charge_failed` em `backend/webhooks/handlers/invoice.py::handle_invoice_payment_failed` (was_trialing branch — distinto de payment_failed genérico). Props: `user_id`, `plan_id`, `amount_brl`, `decline_type`, `decline_code`, `attempt_count`, `stripe_subscription_id`.
- [x] Prometheus counters em `backend/metrics.py`:
  - [x] `smartlic_trial_signup_with_card_total{branch="card"|"legacy"}` — card vs legacy ratio durante canário
  - [x] `smartlic_trial_cancel_before_charge_total` — cancelamentos pré-charge
  - [x] `smartlic_trial_auto_converted_total` — conversion rate real-time (denominator: signup_with_card{branch=card})
  - [x] `smartlic_trial_charge_failed_total` — payment fail rate no dia 14 (alert trigger per runbook)
- [x] Todos counters + branches cobertos por `backend/tests/test_trial_funnel_metrics.py` (7 testes — 4 counter wiring + 2 charge_failed branch + 1 card counter labels).
- [ ] **Dashboard admin `/admin/billing/trial-funnel`** — **DEFERIDO P2** próxima sessão. Mixpanel nativo + Prometheus/Grafana via métricas acima são suficientes para operar o canário 10%. Dashboard dedicado é nice-to-have, não bloqueia flip.

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
  - Status atualizado Ready → InProgress.
- **2026-04-20 (flickering-llama)** — @dev: AC3 (welcome_to_pro email branching no `invoice.py`) + AC5 (runbook trial-card-rollback) + AC7 (frontend `/conta/cancelar-trial` page + proxy + tests) implementados em PR #433 (10 tests local PASS).
- **2026-04-20 (temporal-bonbon evening)** — @devops: PR #431 **MERGED** commit `0ef5902f` (post drift-sweep `1270f909` + CONV-003b `c9c29f3f`). PR #433 rebased com conflict em `invoice.py` resolvido (combina #431's analytics event + #433's email branching). CI rerun em progresso devido a 1 test flake (`test_invalid_signature_rejected DID NOT RAISE` — passa local + isoladamente, falha no full suite — suspeita de test pollution `auth.jwt.decode` patch global). AC1 (cron D-1 email) + AC4 (observability dashboard) deferidos para próxima sessão.
- **2026-04-21 (abstract-coral consultor session, Opus 4.7 — wave 1)** — @dev: **AC1 + AC3 último item COMPLETOS** via PR #442 merged (branch-aware reuse, no new cron).
  - Descoberta: STORY-321 já roda Day 13 "last_day" via `trial_email_sequence.py` com idempotency + opt-out + dispatch. Criar cron novo duplicava infraestrutura e reabriria risco CRIT-044.
  - Solução: `render_trial_last_day_card_email` em `backend/templates/emails/trial.py` (copy ROI-focused + urgência suave, compliance-correct — aviso explícito de charge + one-click cancel link via JWT), dispatcher branch-aware em `trial_email_sequence._render_email::last_day` detectando `profiles.stripe_default_pm_id`.
  - Helper `_format_charge_date_display(created_at)` para exibir data do charge user-friendly.
  - Graceful degradation: falha de mint JWT → fallback para URL plain (email nunca bloqueado).
  - `test_trial_emails.py` +18 tests (`TestLastDayCardEmail` × 11, `TestLastDayCardBranchDispatch` × 3, `TestFormatChargeDateDisplay` × 4). Full file 125/125 passing.
  - **AC3 último item** — auditoria confirmou que `welcome_to_pro` já está implementado em `billing.py:81` + `invoice.py:336-345` + `test_welcome_to_pro_email.py` (já shipado em sessions anteriores).
- **2026-04-21 (abstract-coral consultor session, Opus 4.7 — wave 2)** — @dev: **AC4 events + counters COMPLETO** via PR #443.
  - Novos eventos Mixpanel (via structured log sink): `trial_card_captured` em `routes/auth_signup.py` (card path success); `trial_charge_failed` em `webhooks/handlers/invoice.py::handle_invoice_payment_failed` (was_trialing branch, distinto de dunning genérico). Demais 2 (`trial_cancelled_before_charge`, `trial_converted_auto`) já emitidos em PR #431/#433.
  - 4 Prometheus counters novos em `metrics.py`: `TRIAL_SIGNUP_WITH_CARD{branch}`, `TRIAL_CANCEL_BEFORE_CHARGE`, `TRIAL_AUTO_CONVERTED`, `TRIAL_CHARGE_FAILED`. Instrumentados em auth_signup (card + legacy), conta cancel endpoint, invoice handlers (both branches).
  - Emissão robusta: metrics.inc() em try/except — métricas nunca quebram o fluxo de billing.
  - `tests/test_trial_funnel_metrics.py` 7 testes (counter wiring, charge_failed branch detection, card vs legacy labels). Regression: 48/48 em test_welcome_to_pro + test_cancel_trial_token + test_auth_signup_ratelimit + test_signup_with_card + test_trial_funnel_metrics.
  - Dashboard `/admin/billing/trial-funnel` deferido P2 (Mixpanel nativo + Grafana/Prometheus suficientes para operar canário 10% sem dashboard custom).
  - **Story status final pós-session:** AC1 ✅, AC2 ✅, AC3 ✅, AC4 ~90% (events/counters done, dashboard P2 deferred), AC5 ✅, AC6 parcial, AC7 ✅.
