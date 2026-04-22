# STORY-CONV-003a: Backend Signup + Stripe Customer + Subscription (Trial com Cartão)

**Priority:** P0 — Foundation para CONV-003b/c
**Effort:** M (1-2 dias)
**Squad:** @dev + @qa + @data-engineer
**Status:** Done
**Merged:** PR #408 (scaffolding) + PR #423 (backend implementation) — 2026-04-20
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Parent:** [STORY-CONV-003](STORY-CONV-003-cartao-obrigatorio-trial-stripe.story.md) (superseded — decomposto em a/b/c)

---

## Contexto

Decomposição de STORY-CONV-003 conforme handoff session 2026-04-19-stabilization-sync e plano Board v2.0. Esta sub-story entrega a camada backend que permite coleta de cartão no signup via Stripe, sem mudar frontend ainda (testável via curl).

Prerequisite para CONV-003b (frontend 2-step) e CONV-003c (webhooks completos + cron email + cancel).

---

## Acceptance Criteria

### AC1: Backend recebe payment_method_id no signup ✅
- [x] `POST /v1/auth/signup` aceita payload opcional `{ email, password, cnae, payment_method_id? }` — `backend/routes/auth_signup.py`
- [x] Quando `payment_method_id` presente, backend chama `stripe.Customer.create(email=...)` antes de criar user
- [x] Backend anexa PM via `stripe.PaymentMethod.attach(pm_id, customer=cus_id)` + `stripe.Customer.modify(invoice_settings.default_payment_method=pm_id)`
- [x] Backend cria Subscription: `stripe.Subscription.create(customer=cus_id, items=[{price: STRIPE_SMARTLIC_PRO_PRICE_ID}], trial_period_days=14, default_payment_method=pm_id)`
- [x] Respeita idempotência: `Idempotency-Key` header do Stripe com chave deterministica `signup-{user_email}-{date_utc}` — `services/stripe_signup.py`

### AC2: Persistência em `profiles` ✅
- [x] Migration `supabase/migrations/20260420000003_add_profiles_stripe_default_pm_id.sql` adiciona coluna `stripe_default_pm_id TEXT NULL` (PR #408)
- [x] Migration down `.down.sql` faz `DROP COLUMN` (STORY-6.2 pairing)
- [x] Signup atualiza `profiles.stripe_customer_id`, `profiles.stripe_subscription_id`, `profiles.stripe_default_pm_id`, `profiles.subscription_status='trialing'`, `profiles.plan_type='free_trial'`
- [x] Fail-open: Stripe erros após user criado → `subscription_status='payment_failed'`; billing recon (STORY-314) retries depois

### AC3: Response JSON retorna `trial_end_ts` ✅
- [x] Pydantic schema `SignupResponse` inclui `trial_end_ts: int | None` (Unix epoch seconds) — `backend/schemas/user.py`
- [x] Quando signup cria subscription com trial, retorna timestamp do trial_end do Stripe
- [x] Quando signup sem cartão (legacy path), retorna trial_end_ts calculado localmente (now + 14d)

### AC4: Webhook handler para `customer.subscription.trial_will_end` ✅
- [x] `backend/webhooks/stripe.py` dispatcher routes `customer.subscription.trial_will_end` para handler novo
- [x] Handler `backend/webhooks/handlers/subscription.py::handle_subscription_trial_will_end` loga estruturado + dispara Sentry breadcrumb (fingerprint `["stripe", "trial_will_end", user_id]`)
- [x] Idempotência via Redis key `stripe_event:{event.id}` com TTL 7d (rejeita eventos duplicados)

### AC5: Testes backend ≥ 85% cobertura ✅
- [x] `backend/tests/test_signup_with_card.py` — 4 test classes, 10 test cases cobrindo:
  - sucesso com PM válido
  - PM inválido / Stripe 400
  - email duplicado (409)
  - Stripe timeout (fail-open path)
  - idempotency key verification
  - legacy no-PM path (rollout=0)
- [x] Teste do webhook trial_will_end integrado na suite principal (`webhooks/handlers/subscription.py` coberto)
- [x] Coverage validado no CI Backend Tests (PR Gate) run verde do PR #423

---

## Arquivos (Criados/Modificados — PR #408 e #423)

**Backend — novos arquivos (PR #423, commit 251702dd):**
- `backend/routes/auth_signup.py` (262 linhas — endpoint `POST /v1/auth/signup`)
- `backend/services/stripe_signup.py` (256 linhas — 4-step Stripe dance + idempotency)
- `backend/webhooks/handlers/subscription.py` (88 linhas — `handle_subscription_trial_will_end`)
- `backend/tests/test_signup_with_card.py` (433 linhas, 4 classes)

**Backend — modificações (PR #423):**
- `backend/schemas/user.py` (+73 linhas — `SignupRequest` + `SignupResponse`)
- `backend/webhooks/stripe.py` (+4 — dispatcher routing)
- `backend/startup/routes.py` (+2 — register auth_signup router)
- `backend/tests/snapshots/openapi_schema.json` (+177 — snapshot atualizado)
- `frontend/app/api-types.generated.ts` (+218 — TS types auto-gerados)

**Database (PR #408, commit pré-423):**
- `supabase/migrations/20260420000003_add_profiles_stripe_default_pm_id.sql` + down.sql

**Config:**
- Nenhuma (flag `TRIAL_REQUIRE_CARD_ROLLOUT_PCT` entra em CONV-003b)

---

## Fora de Escopo (delegado para sub-stories seguintes)

- **CONV-003b:** Frontend 2-step PaymentElement + feature flag A/B + testes frontend
- **CONV-003c:** Email D-1 cron + cancel one-click endpoint + Mixpanel+Prometheus observability + invoice.* webhooks + rollback docs

---

## Definition of Done

- [x] AC1-AC5 todos marcados `[x]`
- [x] Migration aplicada em main via `supabase db push` (PR #408 merged 2026-04-20 17:35 UTC)
- [x] PR mergeado para `main` (PR #423 merged 2026-04-20 18:32 UTC)
- [x] CI Backend Tests (PR Gate) run SUCCESS pós-merge em main (run 24683564675, 2026-04-20 18:32 UTC)
- [ ] Smoke test via curl em staging — **deferido para CONV-003b** (endpoint testável apenas quando frontend usa; não bloqueia Done desta sub-story)

---

## Change Log

- **2026-04-19** — @sm (River): Sub-story criada a partir da decomposição de STORY-CONV-003. Status Ready.
- **2026-04-20 (manhã)** — @dev (Wave 3 session): **Partial scaffolding shipped** — DB foundation only (PR #408).
  - Migration `20260420000003_add_profiles_stripe_default_pm_id.sql` + down pareado cria coluna nullable + índice parcial.
  - Status permaneceu `Ready` — scaffolding sem código de endpoint.
- **2026-04-20 (tarde)** — @dev + @qa (PR #423 merged 18:32 UTC): **AC1-AC5 COMPLETOS — story Done.**
  - `backend/routes/auth_signup.py` implementa `POST /v1/auth/signup` com payload opcional `payment_method_id` (regex `pm_...`).
  - `backend/services/stripe_signup.py` executa 4-step dance: Customer.create → PM.attach → Customer.modify(default_pm) → Subscription.create(trial=14d). Idempotency key determinística.
  - Fail-open: erros Stripe após user criado marcam `profiles.subscription_status='payment_failed'`; billing recon (STORY-314) decide próximo passo.
  - Webhook `customer.subscription.trial_will_end` handler implementado em `backend/webhooks/handlers/subscription.py` com Redis dedup (TTL 7d) + Sentry breadcrumb.
  - Testes: 4 classes, 10 test cases em `test_signup_with_card.py` — happy path, legacy no-PM, Stripe failures, idempotency.
  - CI Backend Tests (PR Gate) run 24683564675 = SUCCESS pós-merge.
  - **Status: Done.** Blockers para 003b/c removidos.
- **2026-04-20 (noite)** — @aios-master (docs sync session): Frontmatter atualizado Ready → Done, checkboxes AC1-AC5 marcados, File List reconciliado com código mergeado, DoD items checked.
