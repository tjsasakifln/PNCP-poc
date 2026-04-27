# STORY-CONV-003: Onboarding skip-to-search (defaults inferidos)

## Status

Approved

## Story

**As a** novo trial user que terminou signup e quer "ver o produto" antes de configurar nada,
**I want** opção de pular o onboarding 3-step e ir direto a `/buscar` com defaults sensatos,
**so that** eu experimente valor (resultados de busca reais) em ≤4 cliques desde a landing — sem fricção administrativa.

## Acceptance Criteria

1. Step 3 do onboarding (`frontend/app/onboarding/page.tsx`) mostra botão secundário "Pular tudo, ir direto buscar" além do CTA primário de submit.
2. Ao clicar skip: backend popula perfil com defaults — CNAE inferido por IP geolocation (ou "9999" wildcard se inferência falhar), UF=todas (lista completa de 27), `onboarding_skipped=true`.
3. Mixpanel evento `onboarding_skipped` capturado com prop `step_at_skip` (1, 2 ou 3) e `defaults_applied: { cnae, ufs }`.
4. User é redirecionado a `/buscar` com filtros pré-populados pelos defaults (visíveis e editáveis).
5. CTA no `/buscar` page: banner não-bloqueante "Configure suas preferências para resultados melhores → Voltar ao onboarding" (skip-uma-vez aparece após 2 buscas).
6. User landing→primeira_busca em ≤4 cliques (medido via Mixpanel funnel pós STORY-GROW-001):
   - `landing_view` → `cta_click` → `signup_completed` → `first_search_executed`
7. Steps 1 e 2 mantêm "Pular" existente (não regredir UX atual).
8. Backend não cria estado inválido (CNAE wildcard "9999" deve ser tratado em queries downstream).

## Tasks / Subtasks

- [ ] Task 1 — Botão skip no Step 3 (AC: 1)
  - [ ] Adicionar em `frontend/app/onboarding/page.tsx:204-245`
  - [ ] Texto secundário, não competir com CTA primário
- [ ] Task 2 — Defaults inference (AC: 2, 8)
  - [ ] Backend: CNAE por IP geolocation (TBD lib — talvez já existe `request.headers["X-Forwarded-For"]` + free GeoIP)
  - [ ] UF=todas (constante `BRAZILIAN_UFS`)
  - [ ] Validar downstream queries aceitam wildcards
- [ ] Task 3 — Tracking (AC: 3)
  - [ ] `onboarding_skipped` event com props
- [ ] Task 4 — `/buscar` banner (AC: 5)
  - [ ] Componente `<OnboardingResumeBanner />` reutilizável
  - [ ] Trigger após 2 buscas (localStorage counter)
- [ ] Task 5 — Validação funnel (AC: 6)
  - [ ] Playwright E2E: landing→signup→skip→primeira busca em 4 cliques
  - [ ] Mixpanel funnel report

## Dev Notes

**Plano:** Wave 3, story 9.

**Audit evidence:**
- `frontend/app/onboarding/page.tsx:204-245` é o submit step
- `:326-331` mostra "Pular por agora" — mas só nos passos 1-2 (Audit Agent 2 confirmou)
- Step 3 não tem skip — força user fazer análise antes de ver produto

**Files mapeados:**
- `frontend/app/onboarding/page.tsx` (edit)
- `backend/routes/user.py` ou `backend/auth.py` (criar profile com defaults)
- `frontend/app/buscar/page.tsx` (banner conditional)
- `frontend/components/OnboardingResumeBanner.tsx` (criar)

**Não inventar:** GeoIP lib específica e CNAE wildcard "9999" são propostas — confirmar com @architect/@analyst durante refinement.

### Testing

- Unit: defaults inference (jest backend)
- E2E: Playwright skip path + 2 buscas + banner visible
- Manual: Mixpanel `onboarding_skipped` + `first_search_executed` linked via distinct_id

## Dependencies

- **Bloqueado por:** STORY-GROW-001 (AC 3, 6 dependem tracking)
- **Não bloqueia:** STORY-CONV-002, STORY-CONV-004 (paralelo)

## Owners

- Primary: @ux-design-expert (copy + flow), @dev (impl)
- Quality: @qa

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm | @sm (River) |
