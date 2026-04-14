# STORY-2.4: SSE Reconnection Feedback Banner (TD-FE-013)

**Priority:** P1 (UX confusion — usuário olha spinner sem saber se conexão caiu)
**Effort:** S (4-8h)
**Squad:** @dev + @ux-design-expert
**Status:** Draft
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 1

---

## Story

**As a** usuário aguardando resultados em `/buscar`,
**I want** banner amarelo "Conexão lenta, reconectando..." com botão retry quando SSE cai,
**so that** eu saiba o sistema está funcionando e não fique olhando spinner indefinido.

---

## Acceptance Criteria

### AC1: Detection de SSE drop

- [ ] `EventSource.onerror` triggera state `connectionStatus: 'reconnecting'`
- [ ] Após 3 retries falhados (15s total), state `'failed'`

### AC2: UI feedback

- [ ] Banner amarelo (warning) com ícone WiFi-off
- [ ] Texto: "Conexão lenta. Tentando reconectar... ({tentativa}/3)"
- [ ] Quando `'failed'`: banner vermelho + botão "Tentar novamente" → recarrega busca

### AC3: Polling fallback notification

- [ ] Se SSE falha definitivamente mas polling funciona, banner azul "Modo polling — atualizações a cada 3s"

### AC4: Telemetria

- [ ] Mixpanel `sse_reconnect_attempt` + `sse_failed_fallback_polling`

---

## Tasks / Subtasks

- [ ] Task 1: Update `useSearchOrchestration` hook com state machine (AC1)
- [ ] Task 2: Banner component (AC2-3)
- [ ] Task 3: Integrate em `/buscar` page (AC2)
- [ ] Task 4: Telemetria (AC4)
- [ ] Task 5: E2E simulate dropped connection

## Dev Notes

- SSE chain documented em CLAUDE.md (bodyTimeout 0, heartbeat 15s, Railway 60s, SSE 120s timeout)
- Polling fallback já existe — só precisa surface em UI

## Testing

- E2E: kill SSE conn via DevTools, assert banner aparece
- Unit: hook state transitions

## Definition of Done

- [ ] Banner mostrado em scenarios de reconnect/fail
- [ ] Polling fallback surfaced
- [ ] Telemetria fluindo
- [ ] E2E test

## Risks

- **R1**: False positive em conexões lentas mas funcionais — mitigation: threshold 3 retries

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
