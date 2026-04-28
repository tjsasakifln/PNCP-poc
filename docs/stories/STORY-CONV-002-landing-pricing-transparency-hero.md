# STORY-CONV-002: Landing pricing transparency + hero CTA "14 dias grátis sem cartão"

## Status

Approved

## Story

**As a** visitante chegando em `/` via SEO/marketing,
**I want** entender em <3 segundos: o que é SmartLic, que tem 14 dias grátis sem cartão, e quanto custa depois,
**so that** decida investir 1 minuto no signup com expectativa correta — em vez de bouncear por dúvida sobre preço/compromisso.

## Acceptance Criteria

1. Hero `frontend/app/page.tsx` exibe nos primeiros 3s (acima da dobra): título principal + subtítulo + badge "14 dias grátis · Sem cartão · R$297/mês depois" + CTA primário ("Começar trial grátis").
2. Navegação principal inclui link explícito para `/pricing` (texto: "Preços").
3. Section "Pricing Preview" na home com 3 tiers (mensal R$397 / semestral R$357 / anual R$297) em cards comparáveis + ROI calc resumido (mensagem tipo "1 contrato encontrado paga 12 meses").
4. CTA secundário "Ver todos os planos →" ao final da Pricing Preview leva a `/pricing`.
5. Mixpanel evento `pricing_viewed` dispara em scroll-into-view do Pricing Preview ou clique em link nav (depende STORY-GROW-001).
6. Mixpanel evento `cta_click` distingue hero CTA vs pricing CTA via prop `cta_location`.
7. Mensuração pós-deploy: `cta_click → signup_start` conversion ≥10% (vs baseline TBD pós STORY-GROW-001).
8. Mobile (≤640px): hero permanece legível; CTA visível sem scroll.

## Tasks / Subtasks

- [ ] Task 1 — Hero copy + badge (AC: 1, 8)
  - [ ] @ux-design-expert produz copy hero (não usar lorem; 3 variações para A/B futuro via STORY-CONV-005)
  - [ ] Badge "14 dias grátis · Sem cartão" visualmente proeminente
  - [ ] Mobile-first responsive
- [ ] Task 2 — Nav link `/pricing` (AC: 2)
  - [ ] Adicionar entry no header
- [ ] Task 3 — Pricing Preview section (AC: 3, 4)
  - [ ] Reusar dados de `/plans` API ou hook `usePlans()` se existir
  - [ ] 3 cards (não inventar preços — pegar do DB via STORY-277 baseline)
  - [ ] ROI calc resumido (aproximação simples; detalhado fica em `/pricing`)
- [ ] Task 4 — Tracking (AC: 5, 6)
  - [ ] `pricing_viewed` em IntersectionObserver ou nav click
  - [ ] `cta_click` com prop `cta_location: 'hero'|'pricing_preview'|'final'`
- [ ] Task 5 — Smoke + Lighthouse (AC: 8)
  - [ ] Mobile audit
  - [ ] CWV LCP <2.5s mantido

## Dev Notes

**Plano:** Wave 3, story 8.

**Audit evidence:**
- `frontend/app/page.tsx` é landing genérica sem link para `/pricing` (Audit Agent 2 confirmou)
- "14 dias grátis" mencionado apenas uma vez em `/pricing` linha 415 — invisível no funnel inicial
- Hero atual sem urgência/clareza (Audit Agent 2: "1.3% CTR muito baixo para SaaS B2G")

**Pricing source-of-truth (CLAUDE.md):**
- SmartLic Pro Mensal R$397, Semestral R$357 (10% off), Anual R$297 (25% off)
- Trial 14 dias gratuito sem cartão (STORY-264/277/319)
- **Não inventar preços** — buscar via `plan_billing_periods` table sync Stripe

**Files mapeados:**
- `frontend/app/page.tsx` (edit principal)
- `frontend/components/Hero*.tsx` (TBD nome exato)
- `frontend/hooks/usePlans.ts` (verificar se existe; reusar)
- `frontend/lib/analytics.ts` (track helper de STORY-GROW-001)

### Testing

- Unit: snapshot de Pricing Preview com fixture plans
- E2E: Playwright valida hero + scroll → pricing_viewed event
- Visual: Percy ou screenshot diff

## Dependencies

- **Bloqueado por:** STORY-GROW-001 (AC 5, 6, 7 dependem de tracking funcionando)
- **Não bloqueia:** STORY-CONV-003 (paralelizável)

## Owners

- Primary: @ux-design-expert (copy + layout), @dev (impl)
- Quality: @qa (mobile + tracking)

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm | @sm (River) |
