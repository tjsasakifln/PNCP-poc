# STORY-GROW-001: Mixpanel funnel coverage audit + 12 critical events

## Status

Approved

## Story

**As a** product/growth team com baseline de 2 signups/mês contra 9.9k impressões,
**I want** instrumentação completa do funil landing→subscription via Mixpanel com 12 eventos críticos,
**so that** possamos diagnosticar onde usuários abandonam e priorizar otimizações com dados reais (não suposição).

## Acceptance Criteria

1. Audit inicial: query Mixpanel JQL retorna lista de eventos atualmente disparados em prod nos últimos 7d, com volume e cobertura por sessão (% sessions com cada evento).
2. Wrapper `frontend/lib/analytics.ts` existe e expõe `track(event, props)` com tipos TypeScript estritos para os 12 eventos críticos; backend tem helper paritário em `backend/analytics_events.py` (já existe lazy-init, validar).
3. Os 12 eventos críticos são instrumentados e capturados em prod: `landing_view`, `cta_click`, `pricing_viewed`, `signup_start`, `signup_email_sent`, `signup_email_confirmed`, `onboarding_step_n` (n=1,2,3), `first_search_executed`, `paywall_shown`, `upgrade_cta_clicked`, `trial_day_n`, `subscription_started`.
4. `distinct_id` é o mesmo entre frontend e backend para um dado usuário (paridade auth.users.id ou anonymous_id pré-signup).
5. Mixpanel Live View mostra os 12 eventos com volume real >24h após deploy; relatório (em `docs/qa/`) lista cobertura % antes/depois da instrumentação.
6. Sample test: um real user_id é rastreável de `landing_view` até `subscription_started` (ou ao menos `first_search_executed` no estado atual) na ferramenta People de Mixpanel.

## Tasks / Subtasks

- [ ] Task 1 — Audit cobertura atual (AC: 1)
  - [ ] Rodar Mixpanel JQL listando eventos+volume últimos 7d em prod
  - [ ] Mapear gaps vs lista dos 12 críticos
  - [ ] Documentar cobertura inicial em `docs/qa/mixpanel-coverage-pre-grow001.md`
- [ ] Task 2 — Wrapper `frontend/lib/analytics.ts` (AC: 2)
  - [ ] Confirmar se já existe (provavelmente sim — Mixpanel token já ativo); se sim, expandir tipos
  - [ ] Tipos TS estritos para cada evento + props expected
- [ ] Task 3 — Instrumentar gaps (AC: 3, 4)
  - [ ] Para cada evento missing, identificar call site exato (landing page, signup, onboarding, search route)
  - [ ] Garantir paridade `distinct_id` frontend↔backend (passar user_id após auth)
- [ ] Task 4 — Validação ponta-a-ponta (AC: 5, 6)
  - [ ] Logout → signup novo → onboarding → first_search via Mixpanel Live View
  - [ ] Relatório cobertura pós-instrumentação

## Dev Notes

**Plano:** `/home/tjsasakifln/.claude/plans/precisamos-de-stories-para-jiggly-nebula.md` — Wave 1

**Wave 0 confirmou:**
- `NEXT_PUBLIC_MIXPANEL_TOKEN=bc41...` ATIVO em `bidiq-frontend` (Railway)
- `MIXPANEL_TOKEN=bc41...` ATIVO em `bidiq-backend` (Railway)
- Token está vivo — escopo é instrumentação de eventos faltantes, **não** setup de plataforma.

**Endereça lacunas do audit:** B1 (Mixpanel events não trackeados) + parcial C4 (trial-specific events).

**Files relevantes (mapeados no audit):**
- `frontend/lib/analytics.ts` (criar/expandir)
- `backend/analytics_events.py` (lazy-init existe)
- `frontend/app/page.tsx` (landing_view)
- `frontend/app/signup/page.tsx` (signup_*)
- `frontend/app/onboarding/page.tsx` (onboarding_step_n)
- `frontend/app/buscar/page.tsx` + `useSearchOrchestration.ts` (first_search_executed)

**Bloqueador upstream:** Esta story destrava AC mensurável de TODAS stories Wave 2-3 e BACKLOG-1..5. Priorize.

### Testing

- Unit: cobertura tipos TS para `track()` (jest)
- Integration: backend `analytics_events.py` com Mixpanel mock
- E2E manual: Mixpanel Live View durante full funnel test em staging

## Dependencies

- **Bloqueia:** STORY-CONV-002 (AC mensurável), STORY-CONV-007, todo BACKLOG (eventos pré-requisito)
- **Bloqueado por:** nenhum

## Owners

- Primary: @dev (frontend+backend)
- Quality: @qa
- Optional consult: @architect (se mudança de wrapper API)

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm baseado em plano de crescimento | @sm (River) |
