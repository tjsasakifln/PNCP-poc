# STORY-CONV-005: A/B testing platform via PostHog Cloud (não self-host)

## Status

Approved

## Story

**As a** time de growth precisando otimizar copy/UX/preços com base em dados,
**I want** plataforma de A/B testing integrada (frontend+backend) com dashboard de variants e significância estatística,
**so that** decisões de produto saiam de opinião para experimento mensurável — sem semanas de infra (PostHog Cloud) nem ad-hoc rollout via SHA256 sem dashboard (estado atual).

## Acceptance Criteria

1. PostHog Cloud (free tier 1M events/mês) configurado para o projeto SmartLic; project key seguro em Railway secrets (`POSTHOG_API_KEY`, `NEXT_PUBLIC_POSTHOG_KEY`).
2. SDK PostHog integrado em `frontend/lib/analytics.ts` (extensão da STORY-GROW-001) e `backend/analytics_events.py` — paridade `distinct_id`.
3. Hook `useFeatureFlag(flagKey)` substitui `useRolloutBranch()` no frontend (deprecação do SHA256 ad-hoc).
4. Migração: feature flag existente `trial_require_card_rollout` movida para PostHog (mantém PCT atual=10 inicialmente; ajustes via dashboard).
5. Primeiro experimento "hello-world" rodando: hero copy variant (depende STORY-CONV-002 já entregue) — variant A vs B com ≥100 users/variant em 30d.
6. Dashboard PostHog mostra: pageviews, eventos custom (12 da STORY-GROW-001), funnel landing→subscription, retenção 30d.
7. Documentação `docs/guides/posthog-experiments.md` para o time: como criar experimento, como interpretar resultados, quando declarar vencedor.
8. Privacidade: PostHog configurado com IP masking + cookieless mode (compliance LGPD); banner de consent não bloqueante atualizado.

## Tasks / Subtasks

- [ ] Task 1 — Conta + setup PostHog (AC: 1)
  - [ ] @devops cria account/project + obtém keys
  - [ ] Railway vars adicionadas
- [ ] Task 2 — SDK integration (AC: 2, 6)
  - [ ] Frontend: `posthog-js` no `lib/analytics.ts` ao lado de Mixpanel (envio dual durante migração)
  - [ ] Backend: `posthog-python` em `analytics_events.py`
  - [ ] `distinct_id` shared
- [ ] Task 3 — Feature flags + migração (AC: 3, 4)
  - [ ] `useFeatureFlag` hook
  - [ ] Migrar `trial_require_card_rollout` (depende STORY-CONV-007 — provavelmente paralelo)
  - [ ] Deprecar `frontend/app/signup/hooks/useRolloutBranch.ts` quando todos call sites migrados
- [ ] Task 4 — Primeiro experimento (AC: 5)
  - [ ] Variants hero copy (3 do @ux-design-expert via STORY-CONV-002)
  - [ ] Métrica: `cta_click → signup_completed`
  - [ ] Plan rodar 30d, sample size mínimo
- [ ] Task 5 — Privacy + LGPD (AC: 8)
  - [ ] @analyst review + IP masking config
  - [ ] Cookieless / persistence em localStorage com consent
- [ ] Task 6 — Documentação (AC: 7)
  - [ ] Guide com screenshots para próximos experimentos

## Dev Notes

**Plano:** Wave 3, story 11.

**Advisor warning explícito:**
- **NÃO self-host GrowthBook** — semanas de infra para projeto pre-PMF (memória `project_railway_runners_cost_2026_04` mostra Railway já saturada)
- PostHog Cloud free tier resolve em 1 dia
- Alternative: Statsig free tier (também válido — @architect decide via ADR se desviar)

**Audit evidence:**
- `frontend/app/signup/hooks/useRolloutBranch.ts` é SHA256 % 100 ad-hoc, sem dashboard, sem analytics de variant
- Migração mantém PCT=10 atual (decisão de mover para 0% ou outro valor é da STORY-CONV-007 baseada em dados pós STORY-GROW-001)

**Files mapeados:**
- `frontend/lib/analytics.ts` (estender)
- `backend/analytics_events.py` (estender)
- `frontend/lib/feature-flags.ts` (criar — wrapper PostHog)
- `frontend/app/signup/hooks/useRolloutBranch.ts` (deprecar, não delete imediato)
- `docs/guides/posthog-experiments.md` (criar)
- `docs/adr/NNN-ab-testing-platform.md` (criar — confirmar PostHog vs Statsig)

### Testing

- Unit: feature flag hook com PostHog mock
- Integration: SDK envia evento + flag retorna variant
- Manual: dashboard PostHog mostra dados reais 24h pós deploy

## Dependencies

- **Bloqueado por:** STORY-GROW-001 (analytics base)
- **Cooperativo com:** STORY-CONV-007 (decisão card rollout) — pode ser feito antes ou depois mas idealmente STORY-CONV-005 primeiro para ter ferramenta certa de medição
- **Bloqueia:** BACKLOG-5 (trial scarcity opcional precisa A/B framework)

## Owners

- Primary: @architect (ADR PostHog vs Statsig), @devops (setup), @dev (impl)
- Compliance: @analyst (LGPD)
- Quality: @qa

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm — PostHog Cloud (não self-host) por advisor warning | @sm (River) |
