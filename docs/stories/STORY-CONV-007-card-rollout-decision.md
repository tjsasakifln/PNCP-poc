# STORY-CONV-007: Decisão card-capture rollout 10% (CONDITIONAL — data-driven)

## Status

Approved

> Blocked precondition: aguarda 30d de dados Mixpanel pós STORY-GROW-001 ship. Story permanece Approved para fila; @sm/@po não re-validam quando precondition resolver.

## Story

**As a** product/growth team enfrentando cenário onde 10% dos signups recebem branch "card" (cartão obrigatório no signup),
**I want** decisão data-driven sobre manter, escalar a 0% ou mover capture para post-trial (depois de provar valor),
**so that** não desperdice 10% do tráfego em fricção desnecessária — ou perpetue dead code se branch deveria ter sido desativada.

## Acceptance Criteria

1. **PRECONDITION:** STORY-GROW-001 entregue + ≥30 dias de dados Mixpanel acumulados; mínimo 50 signups em cada branch (legacy/card) para significância básica (não power formal, mas direcional).
2. Análise comparativa: @analyst extrai do Mixpanel funnel `signup_start → signup_completed → first_search_executed → trial_active_day_3` para cada branch. Métrica primária: signup completion rate.
3. ADR `docs/adr/NNN-card-rollout-decision.md` registrando: dados observados, decisão (manter 10% / escalar a 0% / mover para post-trial / aumentar PCT), rationale.
4. Implementação da decisão:
   - **Se manter:** sem mudança de código, atualizar PCT no Railway se decidido outro valor
   - **Se escalar a 0%:** `NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=0` em Railway + deprecar `useRolloutBranch.ts` (não delete; comentário "deprecated 2026-XX-XX, ver ADR-NNN") + remover branch "card" do signup form em PR seguinte
   - **Se mover post-trial:** novo flow capture cartão em day-7 in-app prompt; remover capture do signup
5. Coordenação com STORY-CONV-005 (PostHog): se já entregue, migrar para PostHog feature flag em vez de Railway env var.
6. Validação pós-decisão: monitorar funnel signup→first_search por 14d, confirmar que decisão não regrediu métrica.
7. Documentação atualizada em `docs/guides/conversion-funnel.md` (criar se não existe) — onde está o capture de cartão hoje, motivação.

## Tasks / Subtasks

- [ ] Task 0 — **Aguardar precondição** (AC: 1)
  - [ ] Calendário: revisitar 30d após STORY-GROW-001 ship
- [ ] Task 1 — Análise dados (AC: 2)
  - [ ] @analyst Mixpanel JQL ou Funnels nativo
  - [ ] Quebra por branch (legacy / card) com props
  - [ ] Considerar bias (mesmo que rollout é determinístico SHA256, amostra <50 não é robusta)
- [ ] Task 2 — ADR (AC: 3)
  - [ ] @architect formaliza decisão com data
- [ ] Task 3 — Implementar decisão (AC: 4, 5)
  - [ ] Caminho varia conforme decisão
  - [ ] Se PostHog migration: feature flag central
- [ ] Task 4 — Monitorar (AC: 6)
  - [ ] Dashboard com métrica chave; alerta se regredir >10%
- [ ] Task 5 — Documentação (AC: 7)

## Dev Notes

**Plano:** Wave 3, story 13 — **CONDITIONAL** descoberta pós Wave 0.

**Wave 0 evidence (2026-04-26):**
- `railway variables --service bidiq-frontend --kv | grep ROLLOUT` retornou:
  - `NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=10`
- Não é dead code — 10% real do tráfego signup está na branch "card"
- Hook em `frontend/app/signup/hooks/useRolloutBranch.ts` é determinístico (SHA256 % 100)

**Audit evidence (Agent 2):**
- "STORY-CONV-003b menciona 'card branch disabled (PCT=0)'" — comentário no código pode estar desatualizado vs realidade prod
- Bias possível: usuários no branch card podem ser mais "sérios" (continuam apesar fricção) ou mais hesitantes (abandonam) — análise precisa cruzar com qualidade do trial (uso, retention)

**Cuidado advisor:** "Roda antes de criar story" — esta story é o follow-up, não o trabalho cego. Não implementar mudança sem dados.

**Files mapeados:**
- `frontend/app/signup/hooks/useRolloutBranch.ts` (avaliar)
- `frontend/app/signup/page.tsx:155-182` (card branch UI)
- Railway var `NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT`
- `docs/adr/NNN-card-rollout-decision.md` (criar)
- `docs/guides/conversion-funnel.md` (criar)

### Testing

- Análise: planilha CSV + cálculo signal vs noise
- Manual: A/B vista do branch card vs legacy (Playwright se necessário verificar UX)

## Dependencies

- **Bloqueado por:** STORY-GROW-001 + 30 dias de dados
- **Não bloqueia:** stories Wave 4

## Owners

- Primary: @analyst (análise), @architect (ADR), @dev (impl da decisão), @devops (Railway var)
- Quality: @qa (monitor pós-decisão)

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-26 | 0.1 | Initial draft via /sm — descoberta Wave 0 (PCT=10 ATIVO) | @sm (River) |
