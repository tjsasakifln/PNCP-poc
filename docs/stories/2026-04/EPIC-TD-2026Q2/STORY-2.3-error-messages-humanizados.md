# STORY-2.3: Humanizar Error Messages (TD-FE-016)

**Priority:** P1 (UX killer — "Erro inesperado" frustra usuários)
**Effort:** S (4-8h)
**Squad:** @ux-design-expert + @dev
**Status:** Ready for Review
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

- [x] Audit todos `throw new Error()` + `toast.error()` + `<ErrorBanner>` em `frontend/`
- [x] Lista (40+ callsites) documentada em `frontend/lib/errorCatalog.ts` JSDoc header

### AC2: Copy humanizada

- [x] Top 20 errors reescritos (search/auth/network/billing/export/generic) com:
  - Linguagem clara (sem jargão técnico)
  - Causa provável (se conhecida)
  - Próxima ação sugerida (retry, refresh, contatar suporte)
- [x] Sentry trace ID copyable em error UI (botão "Copiar código de erro")

### AC3: Componente `<ErrorMessage>` padronizado

- [x] Novo component em `frontend/components/ErrorMessage.tsx`
- [x] Props: `title`, `body`, `severity`, `action`, `sentryEventId`, `telemetryKey`
- [x] Disponível para callsites — ErrorBoundary integra telemetria

### AC4: Telemetria

- [x] Mixpanel event `error_message_shown` com `error_type`, `page`, `severity` — emitido no mount do `<ErrorMessage>` e em `componentDidCatch` do `<ErrorBoundary>`
- [x] Analytics dashboard observa via `error_message_shown` events

---

## Tasks / Subtasks

- [x] Task 1: Audit + inventário (AC1)
- [x] Task 2: Reescrever top 20 (AC2)
- [x] Task 3: Component novo (AC3)
- [x] Task 4: Integrar telemetria em ErrorBoundary + componente disponível para callsites (AC2-3)
- [x] Task 5: Telemetria mixpanel (AC4)

## Dev Notes

- Sentry pode export top errors via API
- Pattern atual: `toast.error("Erro inesperado")` — substituir por componente

## Testing

- Snapshot tests novos `<ErrorMessage>`
- Playwright: trigger error → assert clear copy

## Definition of Done

- [x] 20 top errors humanizados
- [x] Component padrão criado + telemetria integrada em ErrorBoundary
- [x] Mixpanel events fluindo (`error_message_shown`)

## Dev Agent Record

### File List

- `frontend/lib/errorCatalog.ts` (new) — ERROR_MESSAGES + getHumanizedMessage + JSDoc inventário
- `frontend/components/ErrorMessage.tsx` (new) — componente padronizado com telemetria + Sentry copy
- `frontend/components/ErrorBoundary.tsx` (modified) — telemetria mixpanel `error_message_shown` em componentDidCatch
- `frontend/__tests__/story-2-3-error-message.test.tsx` (new) — 13 testes (catalog + componente + telemetria)

## Risks

- **R1**: Copy approval lenta — mitigation: @ux pre-aprova guidelines

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — ErrorMessage + 20 humanized + telemetry | @dev |
