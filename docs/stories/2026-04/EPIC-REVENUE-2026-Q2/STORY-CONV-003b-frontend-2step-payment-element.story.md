# STORY-CONV-003b: Frontend Signup 2-Step com Stripe PaymentElement + Feature Flag A/B

**Priority:** P0 — Ativa o fluxo de coleta de cartão para usuários reais
**Effort:** M (1-2 dias)
**Squad:** @dev + @qa + @ux-design-expert (revisão copy)
**Status:** Done (PR #432 merged `c9c29f3f` — 2026-04-20)
**Epic:** [EPIC-REVENUE-2026-Q2](EPIC.md)
**Parent:** [STORY-CONV-003](STORY-CONV-003-cartao-obrigatorio-trial-stripe.story.md) (superseded)
**Depends on:** [STORY-CONV-003a](STORY-CONV-003a-backend-stripe-signup.story.md) (backend deve estar em main)

---

## Contexto

Integra o frontend de signup ao endpoint `POST /v1/auth/signup` já preparado em CONV-003a para aceitar `payment_method_id`. Usuário em `/signup` passa por 2 steps: (1) email+senha+CNAE; (2) PaymentElement do Stripe. A/B test via feature flag `TRIAL_REQUIRE_CARD_ROLLOUT_PCT` distribui signups entre o novo flow e o legacy (50/50 default).

---

## Acceptance Criteria

### AC1: Página `/signup` com fluxo 2-step
- [ ] Step 1: email + senha + CNAE (campos existentes, UI inalterada)
- [ ] Step 2: Stripe PaymentElement montado via `@stripe/react-stripe-js` — só aparece se rollout ativou
- [ ] Botão "Criar conta" desabilitado até PaymentElement sinalizar cartão válido (client-side validation)
- [ ] Componente `CardCollect.tsx` isolado em `frontend/app/signup/components/`
- [ ] Copy explícito acima do PaymentElement: "Cartão não será cobrado hoje. Cobrança automática em 14 dias. Cancele a qualquer momento em 1 clique."

### AC2: Integração com Stripe SetupIntent
- [ ] Backend (ou função server-side Next) expõe `POST /v1/billing/setup-intent` que retorna `client_secret`
- [ ] Frontend usa `stripe.confirmSetup()` com `client_secret` obtido, redirect URL desabilitado (modo in-page)
- [ ] On success: PM id coletado; armazenado em state local
- [ ] On failure: erro exibido via `Toast`, usuário pode retentar

### AC3: Feature flag `TRIAL_REQUIRE_CARD_ROLLOUT_PCT`
- [ ] Env var `NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=50` (0-100)
- [ ] Distribuição via hash determinístico do email (SHA-256 → mod 100 < rollout_pct)
- [ ] Se rollout NÃO ativou: fluxo legacy 1-step (sem Step 2), payload sem `payment_method_id`
- [ ] Se rollout ATIVOU: fluxo 2-step, payload com `payment_method_id`

### AC4: Estado pós-signup
- [ ] Response JSON contém `trial_end_ts` → frontend exibe countdown visível em `/dashboard` + `/buscar`
- [ ] localStorage armazena `trial_end_ts` para rehidratação (TTL 1h)

### AC5: Testes frontend ≥ 75% cobertura
- [ ] `frontend/__tests__/signup/CardCollect.test.tsx` — render, loading state, erro, success
- [ ] `frontend/__tests__/signup/signup-flow.test.tsx` — E2E 2-step com Stripe mocked via `@stripe/react-stripe-js` testing utilities
- [ ] `frontend/__tests__/signup/rollout-hash.test.ts` — distribuição 50/50 com tolerância (N=1000)

---

## Arquivos (Criar/Modificar)

**Frontend:**
- `frontend/app/signup/page.tsx` (modificar — state machine 2-step com branch via rollout)
- `frontend/app/signup/components/CardCollect.tsx` (novo)
- `frontend/app/signup/components/TrialTermsNotice.tsx` (novo)
- `frontend/app/signup/hooks/useRolloutBranch.ts` (novo — hash determinístico)
- `frontend/lib/stripe-client.ts` (modificar — exportar `loadStripe`, `getElements` helpers)

**Backend (minimal):**
- `backend/routes/billing.py` (modificar — endpoint `POST /v1/billing/setup-intent` se ainda não existe)

**Config:**
- `frontend/.env.example` (documentar `NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT`)
- `frontend/.env.local.example` (documentar em staging)

**Tests:**
- `frontend/__tests__/signup/CardCollect.test.tsx` (novo)
- `frontend/__tests__/signup/signup-flow.test.tsx` (novo)
- `frontend/__tests__/signup/rollout-hash.test.ts` (novo)

---

## Fora de Escopo (delegado)

- **CONV-003c:** Email D-1 cron + cancel one-click endpoint + Mixpanel/Prometheus observability + invoice webhooks + rollback docs

---

## Definition of Done

- [ ] AC1-AC5 todos `[x]`
- [ ] Smoke test manual em staging: signup no branch "com cartão" cria Stripe Customer + Subscription
- [ ] Smoke test em staging: signup no branch "sem cartão" (legacy) continua funcionando
- [ ] PR mergeado para `main`

---

## Change Log

- **2026-04-19** — @sm (River): Sub-story criada a partir da decomposição de STORY-CONV-003. Status Ready. Bloqueia até CONV-003a mergeada.
- **2026-04-20 (flickering-llama)** — @dev: Implementação completa — backend `/v1/billing/setup-intent` + frontend 2-step com PaymentElement + A/B rollout via SHA-256(email)%100. 28 tests passando local (4 backend + 14 frontend + 10 integration). PR #432 aberto.
- **2026-04-20 (temporal-bonbon evening)** — @devops: PR #432 rebased em main pós drift-sweep PR #436 merge (commit `1270f909`). Backend Tests SUCCESS. Mergeado via squash commit `c9c29f3f`. **Status: Done.** Próximo passo: @devops Railway var `NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=10` para ativar canário em horário comercial D+1.
