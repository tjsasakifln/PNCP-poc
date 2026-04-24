# GV-017: Exit-Intent Trial Offer com Countdown 24h

**Priority:** P1
**Effort:** XS (3 SP, 1-2 dias)
**Squad:** @dev
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 2

---

## Contexto

Dia 14 do trial é peak de urgência. User que tentar sair (mouse → top viewport, tab blur) perdeu = user perdido. Exit-intent modal com 20% off + countdown 24h é lever clássico para recuperar 3-5% de quem ia churnar.

---

## Acceptance Criteria

### AC1: Detection exit-intent

- [ ] `frontend/hooks/useExitIntent.ts`:
  - Desktop: mouseleave event no topo do viewport (`e.clientY <= 5` + `e.relatedTarget === null`)
  - Mobile: `visibilitychange` para hidden após scroll 50%+ (proxy de "pulling away")
  - Only fires on D14 trial (último dia)
  - Only fires once per user (localStorage flag)

### AC2: Modal `ExitIntentTrialModal`

- [ ] `frontend/components/ExitIntentTrialModal.tsx`:
  - Trigger: `useExitIntent().triggered` no último dia trial
  - Content:
    - Headline: "Antes de sair... 20% off no anual"
    - Value prop: "R$ 397 → R$ 317/mês anual (25% off + 20% cupom LASTCHANCE)"
    - Countdown visual 24h (localStorage timestamp)
    - CTA: "Aplicar cupom e assinar" → `/planos?coupon=LASTCHANCE20&billing=annual`
    - Skip button: "Não, obrigado" (registra dismiss)
  - Confetti-free (tone sério para B2G)

### AC3: Stripe coupon

- [ ] Admin setup via Stripe API: cupom `LASTCHANCE20` (20% off primeiro mês anual, one-time use per customer)
- [ ] Backend validate cupom no checkout (já feito via Stripe)

### AC4: Tracking

- [ ] Mixpanel:
  - `exit_intent_shown` (modal mount)
  - `exit_intent_dismissed`
  - `exit_intent_converted` (checkout completado dentro 24h do show)
- [ ] Funnel metric: conversion rate por cohort D14 com modal vs sem (A/B natural via GV-001)

### AC5: Respeita frequência

- [ ] Uma vez por user forever (localStorage `exit_intent_shown_at`)
- [ ] Não re-dispara em sessões subsequentes
- [ ] Opt-out via `prefers-reduced-motion` ou setting "minimizar popups"

### AC6: Testes

- [ ] Unit `useExitIntent` — trigger conditions
- [ ] E2E Playwright: simulate D14 user → trigger mouseleave top → modal shown → dismiss → verify não re-dispara

---

## Scope

**IN:**
- Hook detection
- Modal + countdown
- Cupom Stripe
- Tracking

**OUT:**
- Exit-intent em outras páginas (só trial expiry relevante)
- Múltiplos cupons escalonados (v2)
- Exit-intent para paid users (outcome metric is churn not trial convert)

---

## Dependências

- **Nenhuma** — independente
- Stripe API (cupom setup)

---

## Riscos

- **Over-firing (dispara em false positives):** threshold conservador + uma vez lifetime
- **Cupom abuse:** Stripe one-time use per customer enforced
- **Backlash "dark pattern":** skip button visível + fácil; LGPD-compliant (tracking com consent)

---

## Arquivos Impactados

### Novos
- `frontend/hooks/useExitIntent.ts`
- `frontend/components/ExitIntentTrialModal.tsx`
- `frontend/__tests__/hooks/useExitIntent.test.ts`

### Modificados
- `frontend/app/(protected)/layout.tsx` (monta hook global em protected layout)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — clássico exit-intent com tone B2G conservador |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
