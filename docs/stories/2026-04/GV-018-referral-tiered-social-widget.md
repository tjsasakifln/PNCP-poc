# GV-018: Referral Tiered Rewards + Social Share Widget (Extends STORY-289)

**Priority:** P0
**Effort:** S (5 SP, 2-3 dias)
**Squad:** @dev
**Status:** Ready (blocked by STORY-289)
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 1
**Pré-requisito:** STORY-289 Done (referral infra básica: link único + tabela `referrals` + email notification + página `/indicar`).

---

## Contexto

STORY-289 (TODO) entrega referral base: "indique 1 colega = 7d trial grátis para ambos", link único por user, tabela referrals, página /indicar simples.

Gap:
1. Sem tier progression (flat 7d para sempre)
2. Sem widget visual no dashboard (user esquece de compartilhar)
3. Sem social share buttons pré-preenchidos (friction alto)

Esta story **ESTENDE 289** — não duplica infra. Add 3 layers incrementais:
1. Tier logic (3 aceites = +30d, 10 = cupom 50% anual)
2. Widget dashboard com progress bar
3. Social share buttons LinkedIn/WhatsApp/Email

---

## Acceptance Criteria

### AC1: Tier logic backend

- [ ] `backend/services/referral_rewards.py` estende STORY-289:
  - Trigger on referral `status='completed'` (signup activated)
  - Count user's `accepted_referrals`
  - Apply tier bonus:
    - 1 = +7d trial extend (pré-existente 289 — não re-aplicar)
    - 3 = +30d bônus adicional (total: 7+7+7+30 = 51d trial)
    - 10 = cupom Stripe 50% primeiro mês anual (`REFERRAL_TIER3`)
  - Email notification "Parabéns — você alcançou tier {N}"
- [ ] Cupom Stripe criado via API (once-only per user)
- [ ] Métrica `smartlic_referral_tier_reached_total{tier}`

### AC2: Widget dashboard

- [ ] `frontend/components/ReferralWidget.tsx`:
  - Lazy-load no `/dashboard` (import dynamic)
  - Renderiza apenas se user tem `referral_code` (backend gerado em 289)
  - Conteúdo:
    - Header: "Indique e ganhe recompensas"
    - Progress bar: "X aceites — próxima tier em Y"
    - Link referral formatted + copy-to-clipboard button
    - Tier preview cards: 1 (7d), 3 (+30d), 10 (50% anual)
    - Social share buttons (AC3)
  - Collapsed by default, expand click

### AC3: Social share buttons pré-preenchidos

- [ ] LinkedIn:
  - URL: `https://linkedin.com/sharing/share-offsite/?url={referral_link}&summary=Descubra licitações públicas com SmartLic — 14 dias grátis`
- [ ] WhatsApp:
  - URL: `https://wa.me/?text={encoded_text}` com template: "Oi, tô usando SmartLic para encontrar licitações públicas compatíveis com nosso CNPJ — vale testar, 14 dias grátis: {referral_link}"
- [ ] Email:
  - `mailto:?subject=...&body=...` pre-filled
- [ ] Copy link:
  - Native `navigator.clipboard.writeText` + toast confirmation
- [ ] Cada share emite `referral_share_clicked` com channel

### AC4: Estender página `/indique`

- [ ] `frontend/app/indique/page.tsx` (criada em 289):
  - Adicionar progress bar tier
  - Adicionar social share buttons (AC3 mesmos componentes)
  - Tabela "Minhas indicações" (já em 289) mantém

### AC5: Dashboard counter realtime

- [ ] Widget atualiza contagem em real-time (SWR hook `useReferralStats`)
- [ ] Endpoint `/v1/referral/stats` (já existe 289) — verificar se retorna tier data; se não, estender

### AC6: Tracking

- [ ] Mixpanel eventos novos (289 tem os básicos):
  - `referral_widget_viewed`
  - `referral_widget_expanded`
  - `referral_link_copied`
  - `referral_share_clicked` com `channel`
  - `referral_tier_reached` (backend emite via backend events)

### AC7: Backward compat 289

- [ ] Reward flat 7d de 289 permanece funcional para todos aceites
- [ ] Tier logic é ADICIONAL, não substitui
- [ ] Users com aceites pré-GV-018 não perdem rewards

### AC8: Testes

- [ ] Unit tier logic (casos limítrofes: 2, 3, 9, 10, 11 aceites)
- [ ] Unit `ReferralWidget` snapshot
- [ ] E2E Playwright: user acumula 3 aceites → verifica bonus 30d aplicado + email notificação
- [ ] Regression: STORY-289 tests continuam passando

---

## Scope

**IN:**
- Tier logic backend (3 tiers)
- Widget dashboard lazy-load
- Social share buttons
- Extensão página /indique
- Realtime counter
- Tracking

**OUT:**
- Referral gamification avançada (leaderboards) — v2
- Custom rewards user-chosen (dinheiro vs trial) — v2
- Referral para usuários free (manter paid-only — incentiva upgrade)

---

## Dependências

- **STORY-289** (TODO) — **deve estar Done antes de Sprint 1 desta story**
- **STORY-449** (Done) — toast pós-busca já aponta para /indique; sem mudança
- Stripe API para cupom creation

---

## Riscos

- **STORY-289 delay:** se 289 não entrega a tempo, GV-018 também atrasa. Mitigação: coordenar com PM prio Sprint.
- **Gaming via self-invites:** reward on_activation (não on_invite) + email/IP detection — já endereçado 289
- **Cupom Stripe rate limit:** Stripe permite ~100 cupons/hora; se 10 users/hora atingem tier 10, OK

---

## Arquivos Impactados

### Novos
- `frontend/components/ReferralWidget.tsx`
- `frontend/__tests__/components/ReferralWidget.test.tsx`

### Modificados
- `backend/services/referral_rewards.py` (estende 289 com tier logic)
- `frontend/app/indique/page.tsx` (criado em 289 — adiciona progress + social)
- `frontend/app/dashboard/page.tsx` (integra widget lazy)
- `backend/routes/referral.py` (se precisar estender `/stats` com tier data)
- `backend/templates/emails/referral_tier_reached.html` (novo)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — extensão STORY-289 sem duplicar infra; tier + social widget |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO blocked**. Pré-requisito STORY-289 deve estar Done antes de iniciar. Status Draft → Ready (blocked). |
