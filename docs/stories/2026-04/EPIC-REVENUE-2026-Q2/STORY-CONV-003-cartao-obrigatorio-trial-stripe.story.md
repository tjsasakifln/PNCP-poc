# STORY-CONV-003: Cartão Obrigatório no Trial via Stripe PaymentElement

**Priority:** P0 — Maior lift single-shot documentado (+170% conversão)
**Effort:** M (5-7 dias)
**Squad:** @dev + @qa + @data-engineer (migration)
**Status:** Ready
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Sprint:** Wave Receita D+1 a D+14

---

## Contexto

Benchmark de mercado SaaS B2B 2025 (fontes: 1Capture, Averi.ai, Sikdar Technologies) mostra que **trial opt-out** (cartão coletado no signup, cobrança automática após período gratuito) converte **2.7x mais** que **trial opt-in** (cartão coletado apenas no checkout pós-trial):

- Trial opt-in: 18.2% trial-to-paid
- Trial opt-out: 48.8% trial-to-paid
- Lift observado: **+169%**

SmartLic hoje opera no modelo opt-in. Signup em `/signup` cria usuário + profile com `plan_type='free_trial'`, `subscription_status='trialing'`, sem tocar Stripe. Stripe Customer só é criado quando usuário clica em "Assinar" em `/planos` pós-trial.

Resultado: 14 dias depois do signup, o usuário precisa tomar **duas decisões**:
1. "Valeu a pena?" (mental)
2. "Vou tirar meu cartão?" (friction)

Mover cartão para signup colapsa ambas em uma única decisão no momento de maior entusiasmo. Cancelamento one-click preserva confiança.

**Impacto esperado:** +25-30pp em trial-to-paid conversion (baseline ~3% → meta 30%+). Maior alavanca única do plano 90d.

---

## Acceptance Criteria

### AC1: Coleta de cartão integrada ao signup
- [ ] Página `/signup` apresenta fluxo em 2 steps: (1) email+senha+CNAE, (2) cartão via Stripe PaymentElement
- [ ] Step 2 só habilita submit após PaymentElement validar cartão (cliente-side)
- [ ] Componente `CardCollect.tsx` isolado em `frontend/app/signup/components/`
- [ ] Indicador visual claro: "Cartão não será cobrado hoje. Cobrança automática em 14 dias, cancele a qualquer momento."

### AC2: Backend cria Stripe Customer + Subscription no signup
- [ ] `POST /v1/auth/signup` recebe `payment_method_id` (SetupIntent confirmado no frontend) junto com email/senha/CNAE
- [ ] Backend cria Stripe Customer (`stripe.Customer.create`)
- [ ] Backend anexa PM via `stripe.PaymentMethod.attach` + `stripe.Customer.modify(invoice_settings.default_payment_method)`
- [ ] Backend cria Subscription com `trial_period_days=14` + `default_payment_method=pm_id`
- [ ] Backend atualiza `profiles.stripe_customer_id`, `profiles.stripe_subscription_id`, `profiles.stripe_default_pm_id`
- [ ] Resposta JSON retorna `trial_end_ts` (Unix) para frontend exibir countdown

### AC3: Feature flag para rollout gradual (A/B test)
- [ ] Env var `TRIAL_REQUIRE_CARD_ROLLOUT_PCT=50` (0-100) controla % de signups que veem o novo fluxo
- [ ] Distribuição via hash determinístico do email (user consistency)
- [ ] Controle (sem cartão) mantém fluxo legacy — mesmo arquivo, branches condicionais
- [ ] Dashboard admin `/admin/billing` mostra contagem real-time de signups em cada ramo + conversion rate

### AC4: Email D-1 automático antes de charge
- [ ] ARQ cron job diário às 9h BRT (`backend/jobs/cron/trial_charge_warning.py`) identifica profiles com `trial_end_ts` entre 22h e 26h à frente
- [ ] Envia email via Resend com template `trial_charge_tomorrow.html`:
  - Subject: "Amanhã sua trial SmartLic expira — R$ 397 serão cobrados"
  - Body: CTA "Cancelar minha trial" (link one-click) + "Manter assinatura" (no-op)
- [ ] Template sanitizado contra XSS (Pydantic + escape nas variáveis)

### AC5: Cancelamento one-click sem contato
- [ ] Página `/conta/cancelar-trial` acessível via link assinado no email
- [ ] Link contém token JWT de 48h (payload `{user_id, action: "cancel_trial"}`)
- [ ] Ao acessar: verifica token, cancela Stripe Subscription (`stripe.Subscription.delete` com `prorate=False` já que é trial)
- [ ] Atualiza `profiles.subscription_status='canceled_trial'`
- [ ] Tela de confirmação: "Trial cancelada. Seu acesso continua até {trial_end_ts}. Você pode reativar a qualquer momento em /planos."

### AC6: Observabilidade completa
- [ ] Evento Mixpanel `trial_card_captured` no signup bem-sucedido (props: `rollout_branch`, `cnae`)
- [ ] Evento Mixpanel `trial_cancelled_before_charge` no cancel (props: `days_before_charge`)
- [ ] Evento Mixpanel `trial_converted_auto` no webhook `invoice.payment_succeeded` que segue `invoice.paid` do primeiro ciclo
- [ ] Métricas Prometheus: `smartlic_trial_signup_with_card_total{branch}`, `smartlic_trial_cancel_before_charge_total`, `smartlic_trial_auto_converted_total`

### AC7: Webhooks Stripe handlers
- [ ] `customer.subscription.trial_will_end` (3 dias antes) — logs + Sentry breadcrumb
- [ ] `invoice.payment_failed` — email "Pagamento falhou, atualize seu cartão" + retain access por 3 dias (grace period existente)
- [ ] `invoice.payment_succeeded` (primeiro após trial) — atualiza `profiles.plan_type='pro'` + dispara onboarding email
- [ ] Idempotência: handler rejeita eventos com `event.id` já processado (redis key TTL 7d)

### AC8: Testes backend ≥ 85% cobertura
- [ ] `test_signup_with_card.py` — 12+ test cases (sucesso, PM inválido, Stripe 402, duplicate email, etc.)
- [ ] `test_trial_charge_warning_cron.py` — detecção de trials expirando amanhã
- [ ] `test_cancel_trial_token.py` — JWT válido, expirado, revogado
- [ ] `test_webhook_subscription_handlers.py` — todos os 3 eventos + idempotência
- [ ] `test_feature_flag_rollout.py` — distribuição hash determinística 50/50 com tolerância

### AC9: Testes frontend ≥ 75% cobertura
- [ ] `__tests__/signup/CardCollect.test.tsx` — render, loading, erro, success
- [ ] `__tests__/signup/signup-flow.test.tsx` — e2e 2-step com Stripe mocked
- [ ] `__tests__/conta/cancel-trial.test.tsx` — fluxo cancelamento

### AC10: Rollback plan documentado
- [ ] Se conversion drop >50% em 7 dias: setar `TRIAL_REQUIRE_CARD_ROLLOUT_PCT=0` (via Railway vars, sem deploy)
- [ ] Documentação em `docs/runbooks/trial-card-rollback.md`

---

## Arquivos

**Frontend (novos + modificados):**
- `frontend/app/signup/page.tsx` (modificar — adicionar step 2)
- `frontend/app/signup/components/CardCollect.tsx` (novo)
- `frontend/app/signup/components/TrialTermsNotice.tsx` (novo)
- `frontend/app/conta/cancelar-trial/page.tsx` (novo)
- `frontend/lib/stripe-client.ts` (modificar — exportar `loadStripe` + `getElements`)

**Backend:**
- `backend/services/billing.py` (modificar — adicionar `create_trial_with_card`)
- `backend/routes/auth.py` (modificar — extender signup handler)
- `backend/routes/conta.py` (novo ou modificar — handler `POST /v1/conta/cancelar-trial`)
- `backend/webhooks/stripe.py` (modificar — handlers + idempotência)
- `backend/jobs/cron/trial_charge_warning.py` (novo)
- `backend/jobs/queue/definitions.py` (modificar — registrar cron)
- `backend/templates/emails/trial_charge_tomorrow.html` (novo)
- `backend/services/trial_cancel_token.py` (novo — JWT signing/verification)

**Database:**
- `supabase/migrations/20260420000001_add_stripe_default_pm_id.sql` (novo)
- `supabase/migrations/20260420000001_add_stripe_default_pm_id.down.sql` (novo — rollback)

**Config:**
- `backend/config/features.py` (adicionar `TRIAL_REQUIRE_CARD_ROLLOUT_PCT`)
- `.env.example` (documentar flag)

**Tests:**
- `backend/tests/test_signup_with_card.py` (novo)
- `backend/tests/test_trial_charge_warning_cron.py` (novo)
- `backend/tests/test_cancel_trial_token.py` (novo)
- `backend/tests/test_webhook_subscription_handlers.py` (modificar)
- `backend/tests/test_feature_flag_rollout.py` (novo)
- `frontend/__tests__/signup/CardCollect.test.tsx` (novo)
- `frontend/__tests__/signup/signup-flow.test.tsx` (novo)
- `frontend/__tests__/conta/cancel-trial.test.tsx` (novo)

---

## Riscos e Mitigações

**Risco 1:** Volume de signups cai 30-50% no curto prazo por fricção adicional
- **Mitigação:** A/B test `ROLLOUT_PCT=50` por 14 dias antes de enforce; métricas semanais

**Risco 2:** Usuários sem cartão corporativo disponível
- **Mitigação:** Manter fallback visível em `/pricing` — "Prefere conversar antes? Fale com vendas: [email]"

**Risco 3:** Stripe webhook eventos perdidos geram users em estado inconsistente
- **Mitigação:** Dashboard admin `/admin/billing/reconcile` com botão manual + cron diário reconciliação profiles vs Stripe

**Risco 4:** Charge-back rate aumenta (consentimento não claro)
- **Mitigação:** Copy explícito 2 vezes (no signup + no email D-1) + cancel one-click; Stripe charge-back rate <0.5% é DoD

---

## Definition of Done

- [ ] AC1-AC10 todos marcados `[x]`
- [ ] Feature flag em produção com rollout 50% por ≥14 dias
- [ ] ≥1 charge automático bem-sucedido após 14 dias (evidência log + Stripe dashboard)
- [ ] Dashboard `/admin/billing` mostra conversion rate diferenciado (cartão vs sem-cartão) com n≥30 signups por branch
- [ ] PR mergeado para `main`, CI verde
- [ ] `docs/runbooks/trial-card-rollback.md` commitado

---

## Dev Notes

**Stripe Setup (pré-requisito):**
1. Product "SmartLic Pro" com Price R$ 397/mês recurring (já existe)
2. Webhook endpoint `/webhooks/stripe` recebendo: `customer.subscription.*`, `invoice.*`, `payment_intent.*`
3. `STRIPE_WEBHOOK_SECRET` em Railway vars

**Ordem de implementação sugerida:**
1. AC2 (backend signup+Stripe) sem mudar frontend — testa via curl
2. AC8 (testes backend) — garante contrato
3. AC1 (frontend 2-step) integrado ao AC2
4. AC3 (feature flag) antes de AC4-7
5. AC4 (cron email) + AC5 (cancel) em paralelo
6. AC7 (webhooks) antes de AC6 (observabilidade depende de eventos)
7. AC6 (Mixpanel + Prometheus) como camada final
8. AC9 (testes frontend) + AC10 (rollback docs) antes de merge

**Zero Quarentena policy:** Nenhum teste skip/xfail novo. Se teste revela bug, corrige código.

---

## File List

_(populado pelo @dev durante execução)_

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-19 | @sm (River) | Story criada Ready. Subsídios do plano Board v1.0 (2026-04-19). |
