# STORY-CONV-003a: Backend Signup + Stripe Customer + Subscription (Trial com Cartão)

**Priority:** P0 — Foundation para CONV-003b/c
**Effort:** M (1-2 dias)
**Squad:** @dev + @qa + @data-engineer
**Status:** Ready
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Parent:** [STORY-CONV-003](STORY-CONV-003-cartao-obrigatorio-trial-stripe.story.md) (superseded — decomposto em a/b/c)

---

## Contexto

Decomposição de STORY-CONV-003 conforme handoff session 2026-04-19-stabilization-sync e plano Board v2.0. Esta sub-story entrega a camada backend que permite coleta de cartão no signup via Stripe, sem mudar frontend ainda (testável via curl).

Prerequisite para CONV-003b (frontend 2-step) e CONV-003c (webhooks completos + cron email + cancel).

---

## Acceptance Criteria

### AC1: Backend recebe payment_method_id no signup
- [ ] `POST /v1/auth/signup` aceita payload opcional `{ email, password, cnae, payment_method_id? }`
- [ ] Quando `payment_method_id` presente, backend chama `stripe.Customer.create(email=...)` antes de criar user
- [ ] Backend anexa PM via `stripe.PaymentMethod.attach(pm_id, customer=cus_id)` + `stripe.Customer.modify(invoice_settings.default_payment_method=pm_id)`
- [ ] Backend cria Subscription: `stripe.Subscription.create(customer=cus_id, items=[{price: STRIPE_SMARTLIC_PRO_PRICE_ID}], trial_period_days=14, default_payment_method=pm_id)`
- [ ] Respeita idempotência: `Idempotency-Key` header do Stripe com chave `signup-{user_email}-{date_utc}`

### AC2: Persistência em `profiles`
- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_add_stripe_default_pm_id.sql` adiciona coluna `stripe_default_pm_id TEXT NULL` em `profiles`
- [ ] Migration down `.down.sql` faz `DROP COLUMN`
- [ ] Signup atualiza `profiles.stripe_customer_id`, `profiles.stripe_subscription_id`, `profiles.stripe_default_pm_id`, `profiles.subscription_status='trialing'`, `profiles.plan_type='free_trial'`
- [ ] Se Stripe falhar após user criado, subscription fica como null mas user continua ativo (grace period via SUBSCRIPTION_GRACE_DAYS já existente)

### AC3: Response JSON retorna `trial_end_ts`
- [ ] Pydantic schema `SignupResponse` inclui `trial_end_ts: int | None` (Unix epoch seconds)
- [ ] Quando signup cria subscription com trial, retorna timestamp do trial_end do Stripe
- [ ] Quando signup sem cartão (legacy path), retorna trial_end_ts calculado localmente (now + 14d)

### AC4: Webhook handler para `customer.subscription.trial_will_end`
- [ ] `backend/webhooks/stripe.py` adiciona handler para `customer.subscription.trial_will_end` (3 dias antes do trial acabar)
- [ ] Handler loga estruturado + dispara Sentry breadcrumb (fingerprint `["stripe", "trial_will_end", user_id]`)
- [ ] Idempotência via Redis key `stripe_event:{event.id}` com TTL 7d (rejeita eventos duplicados)

### AC5: Testes backend ≥ 85% cobertura
- [ ] `backend/tests/test_signup_with_card.py` — 10+ test cases:
  - sucesso com PM válido
  - PM inválido (Stripe 400)
  - email duplicado (retorna 409)
  - CNAE inválido (retorna 400)
  - Stripe timeout (fallback: user criado sem subscription)
  - idempotency key repetido retorna mesma response
- [ ] `backend/tests/test_webhook_trial_will_end.py` — handler + idempotência
- [ ] Coverage ≥ 85% nos arquivos novos (`routes/auth_signup.py`, `services/stripe_signup.py`)

---

## Arquivos (Criar/Modificar)

**Backend:**
- `backend/routes/auth.py` (modificar — adicionar `payment_method_id` opcional ao signup handler)
- `backend/services/stripe_signup.py` (novo — funções `create_stripe_customer_and_subscription`)
- `backend/webhooks/stripe.py` (modificar — handler `customer.subscription.trial_will_end`)
- `backend/schemas.py` (modificar — `SignupRequest`, `SignupResponse` com `payment_method_id`, `trial_end_ts`)

**Database:**
- `supabase/migrations/YYYYMMDDHHMMSS_add_stripe_default_pm_id.sql` + `.down.sql`

**Tests:**
- `backend/tests/test_signup_with_card.py` (novo)
- `backend/tests/test_webhook_trial_will_end.py` (novo)

**Config:**
- `backend/config/features.py` (pre-existe; nenhuma mudança nesta sub-story — flag `TRIAL_REQUIRE_CARD_ROLLOUT_PCT` entra em CONV-003b)

---

## Fora de Escopo (delegado para sub-stories seguintes)

- **CONV-003b:** Frontend 2-step PaymentElement + feature flag A/B + testes frontend
- **CONV-003c:** Email D-1 cron + cancel one-click endpoint + Mixpanel+Prometheus observability + invoice.* webhooks + rollback docs

---

## Definition of Done

- [ ] AC1-AC5 todos marcados `[x]`
- [ ] Testado via curl em staging (documentar payload de exemplo no PR body)
- [ ] Migration aplicada em staging via `supabase db push`
- [ ] PR mergeado para `main`
- [ ] Link do CI run documentado no Change Log

---

## Change Log

- **2026-04-19** — @sm (River): Sub-story criada a partir da decomposição de STORY-CONV-003. Status Ready.
- **2026-04-20** — @dev (Wave 3 session): **Partial scaffolding shipped** — DB foundation only.
  - AC2 partial: migration `supabase/migrations/20260420000003_add_profiles_stripe_default_pm_id.sql` + down pareado cria coluna nullable `profiles.stripe_default_pm_id` (TEXT) + índice parcial `idx_profiles_stripe_default_pm_id WHERE NOT NULL`. Column unused até AC1 ligar backend writes.
  - Colunas `stripe_customer_id` e `stripe_subscription_id` já existiam em `profiles` (migration 001, não precisam novo ADD COLUMN).
  - Test stubs (AC5) **NÃO criados** — Zero Quarentena policy (EPIC-BTS): stubs `pytest.mark.skip` com rota ainda inexistente geram ruído. Tests reais serão escritos na sessão AC1 junto com o código de produção.
  - Route/schema (AC1/AC3/AC4) **NÃO iniciados** — endpoint `/v1/auth/signup` ainda não existe (signup atual é Supabase Auth direto do frontend). Criação do endpoint + lógica Stripe + webhook é trabalho de 3-4h próxima sessão com founder hands (advisor guidance: evitar Stripe integration via agente).
  - Status permanece `Ready` — scaffolding não começa InProgress; AC1 ainda é o trabalho principal.
  - Decisão estratégica: commit separado da migration permite CI exercitar o `deploy.yml` auto-apply path sem acoplamento a código Stripe pendente.
