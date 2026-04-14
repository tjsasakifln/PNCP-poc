# STORY-2.3: Humanizar Error Messages (TD-FE-016)

**Priority:** P1 (UX killer — "Erro inesperado" frustra usuários)
**Effort:** S (4-8h)
**Squad:** @ux-design-expert + @dev
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** usuário SmartLic encontrando erro,
**I want** mensagens claras e acionáveis (ex: "Não conseguimos buscar agora — aguarde 1min e tente novamente"),
**so that** eu saiba o que fazer e me sinta menos frustrado.

---

## Acceptance Criteria

### AC1: Inventário de error messages

- [ ] Audit todos `throw new Error()` + `toast.error()` + `<ErrorBanner>` em `frontend/`
- [ ] Lista CSV com: arquivo, linha, mensagem atual, contexto

### AC2: Copy humanizada

- [ ] Top 20 errors (frequência via Sentry) reescritos com:
  - Linguagem clara (sem jargão técnico)
  - Causa provável (se conhecida)
  - Próxima ação sugerida (retry, refresh, contatar suporte)
- [ ] Sentry trace ID copyable em error UI (botão "Copiar código de erro")

### AC3: Componente `<ErrorMessage>` padronizado

- [ ] Novo component em `frontend/components/ErrorMessage.tsx`
- [ ] Props: `title`, `description`, `actionLabel`, `onAction`, `sentryEventId`
- [ ] Substitui inline error banners

### AC4: Telemetria

- [ ] Mixpanel event `error_message_shown` com `error_type`, `page`
- [ ] Analytics dashboard pra ver quais errors mais frequentes

---

## Tasks / Subtasks

- [ ] Task 1: Audit + inventário (AC1)
- [ ] Task 2: Reescrever top 20 (AC2)
- [ ] Task 3: Component novo (AC3)
- [ ] Task 4: Migrar 10 callsites priority (AC2-3)
- [ ] Task 5: Telemetria (AC4)

## Dev Notes

- Sentry pode export top errors via API
- Pattern atual: `toast.error("Erro inesperado")` — substituir por componente

## Testing

- Snapshot tests novos `<ErrorMessage>`
- Playwright: trigger error → assert clear copy

## Definition of Done

- [ ] 20 top errors humanizados
- [ ] Component padrão criado + adotado em 10+ callsites
- [ ] Mixpanel events fluindo

## Risks

- **R1**: Copy approval lenta — mitigation: @ux pre-aprova guidelines

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
