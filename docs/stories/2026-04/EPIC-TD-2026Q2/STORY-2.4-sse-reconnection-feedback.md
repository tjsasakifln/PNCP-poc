# STORY-2.4: SSE Reconnection Feedback Banner (TD-FE-013)

**Priority:** P1 (UX confusion — usuário olha spinner sem saber se conexão caiu)
**Effort:** S (4-8h)
**Squad:** @dev + @ux-design-expert
**Status:** Ready for Review
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

- [x] `EventSource.onerror` triggera state `'reconnecting'` (via `useSearchSSE.scheduleRetry` + `deriveSseConnectionState` helper)
- [x] Após `SSE_MAX_RETRIES` falhados (backoff [1s,2s,4s]), state → `'failed'` ou `'polling'`

### AC2: UI feedback

- [x] Banner amarelo (warning) com ícone WiFi-off (`<ConnectionBanner state="reconnecting" />`)
- [x] Texto: "Conexão lenta. Tentando reconectar… (Tentativa N de M)"
- [x] State `'failed'`: banner vermelho + botão "Tentar novamente"

### AC3: Polling fallback notification

- [x] Banner azul "Modo polling ativo — atualizações chegam a cada 3 segundos"

### AC4: Telemetria

- [x] Mixpanel `sse_reconnect_attempt` (no scheduleRetry) + `sse_failed_fallback_polling` (no fallback)

---

## Tasks / Subtasks

- [x] Task 1: Helper `deriveSseConnectionState` consolida sinais existentes (AC1)
- [x] Task 2: `<ConnectionBanner>` component (AC2-3)
- [x] Task 3: Hook `useSearchSSE` emite telemetria + helper integra signals (AC2)
- [x] Task 4: Telemetria (AC4)
- [x] Task 5: Unit tests cobrem state machine + banner variantes (E2E follow-up)

## Dev Notes

- SSE chain documented em CLAUDE.md (bodyTimeout 0, heartbeat 15s, Railway 60s, SSE 120s timeout)
- Polling fallback já existe — só precisa surface em UI

## Testing

- E2E: kill SSE conn via DevTools, assert banner aparece
- Unit: hook state transitions

## Definition of Done

- [x] Banner mostrado em scenarios de reconnect/fail
- [x] Polling fallback surfaced
- [x] Telemetria fluindo
- [x] Unit tests (E2E pendente como follow-up)

## Dev Agent Record

### File List

- `frontend/lib/sseConnectionState.ts` (new) — `SseConnectionState` type + `deriveSseConnectionState()` helper
- `frontend/app/buscar/components/ConnectionBanner.tsx` (new) — 3 variantes (reconnecting/failed/polling)
- `frontend/hooks/useSearchSSE.ts` (modified) — telemetria mixpanel `sse_reconnect_attempt` + `sse_failed_fallback_polling`
- `frontend/__tests__/story-2-4-sse-reconnect.test.tsx` (new) — 15 testes

## Risks

- **R1**: False positive em conexões lentas mas funcionais — mitigation: threshold 3 retries

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-14 | 1.1     | Implementation complete — helper + ConnectionBanner + telemetry | @dev |
