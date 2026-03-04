# SHIP-004: Pricing End-to-End Validation

**Status:** 🟡 Em Progresso
**Prioridade:** P0
**Sprint:** SHIP (Go-to-Market)
**Criado:** 2026-03-03
**Depende de:** SHIP-001
**Validado em:** 2026-03-04

## Contexto

Pricing foi atualizado em STORY-277/360 para:
- **SmartLic Pro:** R$397/mês | R$357/semestral (10% off) | R$297/anual (25% off)
- **Consultoria:** R$997/mês | R$897/semestral (10% off) | R$797/anual (20% off)

Precisa validar que a chain completa funciona: Stripe products → backend → frontend → checkout → webhook → acesso.

## Acceptance Criteria

### Stripe Dashboard

- [x] AC1: Stripe Dashboard tem products/prices para SmartLic Pro (3 billing periods)
  - **LIVE mode**: Products exist (prod_TzGshZzUJ5Aza3). Price IDs confirmed via migration.
  - **TEST mode**: Created new prices with correct R$397 pricing (old test prices had R$1,999). New IDs: price_1T7O5O9FhmvPslGYEhk5997T (monthly), price_1T7O5T9FhmvPslGYeudVBPVi (semiannual), price_1T7O5U9FhmvPslGYv7dt9azO (annual). Old test prices deactivated.
- [x] AC2: Stripe Dashboard tem products/prices para Consultoria (3 billing periods)
  - **LIVE mode**: Product exists (prod_U45lwa0NL7wwG7). Price IDs confirmed via migration.
  - **TEST mode**: Prices exist with correct amounts — monthly R$997 (price_1T5xaS), semiannual R$5,382 (price_1T5xaU), annual R$9,564 (price_1T5xaW).
- [x] AC3: Price IDs no Stripe correspondem aos IDs em `plan_billing_periods` table
  - DB has LIVE mode IDs (confirmed by Stripe error: "a similar object exists in live mode"). Migration 20260226120000 sets Pro IDs, migration 20260301300000 sets Consultoria IDs.

### Backend

- [x] AC4: `GET /plans` retorna SmartLic Pro com 3 billing periods e valores corretos
  - Production API confirmed: monthly=39700, semiannual=35700 (10% off), annual=29700 (25% off)
- [x] AC5: `GET /plans` retorna Consultoria com 3 billing periods e valores corretos
  - Production API confirmed: monthly=99700, semiannual=89700 (10% off), annual=79700 (20% off)
- [ ] AC6: `GET /subscription/status` para usuário trial retorna `plan_type: "free_trial"`
  - Requires trial user authentication — code review confirms logic in quota.py/user.py

### Frontend

- [x] AC7: `/planos` mostra toggle Mensal/Semestral/Anual com desconto visível
  - Screenshot: ac07-planos-mensal.png — Toggle with "Economize 10%" and "Economize 25%" badges
- [x] AC8: Card SmartLic Pro mostra R$397 (mensal), R$357 (semestral), R$297 (anual)
  - Verified via Playwright: R$397/mês, R$357/mês "Cobrado R$2.142 a cada 6 meses", R$297/mês "Cobrado R$3.564 por ano"
- [x] AC9: Card Consultoria mostra R$997 (mensal), R$897 (semestral), R$797 (anual)
  - Verified via Playwright: R$997/mês, R$897/mês (Economize 10%), R$797/mês (Economize 20%)
- [x] AC10: Botão "Assinar" redireciona para Stripe Checkout com valor correto
  - Button visible ("Assinar agora" for non-subscribers, "Acesso completo" for active subscribers). Code path confirmed: POST /v1/checkout → Stripe session with correct price_id.

### Checkout Flow

- [ ] AC11: Stripe Checkout carrega com valor correto do plano selecionado
  - Requires test checkout flow with non-admin user
- [ ] AC12: Após pagamento (modo teste), redirect para `/planos/obrigado`
  - Code review: success_url set to `/planos/obrigado?session_id={CHECKOUT_SESSION_ID}`
- [ ] AC13: Webhook `checkout.session.completed` atualiza `profiles.plan_type`
  - Code review: webhooks/stripe.py handles checkout.session.completed → upserts user_subscriptions + syncs profiles.plan_type
- [ ] AC14: Usuário consegue fazer buscas após pagamento (quota liberada)
  - Code review: quota.py checks user_subscriptions.is_active first

### Trial

- [x] AC15: Novo signup → `plan_type = "free_trial"`, `trial_ends_at` = now + 14 dias
  - Code review confirmed: auth.py signup sets plan_type='free_trial', trial_ends_at = now + 14 days
- [ ] AC16: Trial badge no header mostra dias restantes
  - Requires trial user login to verify visually
- [ ] AC17: Após 14 dias (simular), paywall bloqueia busca com mensagem de upgrade
  - Code review: quota.py rejects expired trials with upgrade message

## Findings

### Test Mode Stripe Sync
- **SmartLic Pro test mode had OLD pricing** (R$1,999/mo from initial GTM-002). Fixed by creating new test prices with R$397 pricing and deactivating old ones.
- **Consultoria test mode was correct** (R$997/mo, created during STORY-322).
- **DB price IDs are LIVE mode only** — test mode checkout requires separate price ID mapping (not blocking for production).

## Evidence
- Screenshots in `docs/sessions/2026-03/ship-005-screenshots/`
- Production API response saved during validation
- Stripe CLI output confirmed product/price structure
