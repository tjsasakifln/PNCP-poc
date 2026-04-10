# STORY-422: Frontend SSE Connection closed — Retry + Cleanup

**Priority:** P2 — Medium (34 eventos mas causa UX ruim ao cancelar buscas)
**Effort:** M (1-2 days)
**Squad:** @dev
**Status:** Draft
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issues:**
- https://confenge.sentry.io/issues/7387910087/ (34 eventos)
- https://confenge.sentry.io/issues/7389359900/ (1 evento)
- https://confenge.sentry.io/issues/7389229679/ (1 evento)
**Sprint:** Sprint rotina (1w-2w)

---

## Contexto

Frontend está gerando `Error: Connection closed` em 34+ eventos Sentry durante SSE (Server-Sent Events) de busca.

**Causa mapeada:**
- `frontend/app/buscar/hooks/execution/useSearchAPI.ts:168-231` usa `AbortController` com timeout fixo de 65s:
  ```typescript
  const abortController = new AbortController();
  abortControllerRef.current = abortController;
  const clientTimeoutId = setTimeout(() => abortController.abort(), 65_000);
  ```
- Quando `abortController.abort()` dispara ou usuário navega fora, fetch é cancelado e dispara "Connection closed"
- `useSearchSSEHandler.ts` **não tem `finally` block** que fecha EventSource limpo — listeners ficam dangling
- **Sem retry:** se abort acontece ANTES de `stream_complete`, não há segunda tentativa — usuário vê erro silencioso

**Impacto:**
- Usuários que cancelam busca (navegam fora, clicam X, time-out) geram ruído no Sentry
- Não distinguimos user_cancelled de network_abort
- Sem retry automático em caso de network blip

**Observação:** parte dos eventos pode ser legítimo (usuário cancelou de propósito) — precisa ser filtrado no Sentry antes de contar como bug.

---

## Acceptance Criteria

### AC1: Distinguir tipos de close
- [ ] Em `useSearchAPI.ts:168-231`, quando `abortController.abort()` é disparado, marcar razão:
  ```typescript
  abortController.abort(new Error('USER_CANCELLED')); // ou 'TIMEOUT' ou 'NAVIGATION'
  ```
- [ ] No catch, inspecionar `signal.reason` e decidir:
  - `USER_CANCELLED` → não reportar ao Sentry (comportamento esperado)
  - `TIMEOUT` → reportar + retry automático
  - `NAVIGATION` → não reportar
  - `UNKNOWN` / network error → reportar + retry
- [ ] Tag Sentry event com `search_close_reason` para filtragem

### AC2: Retry automático único
- [ ] Se close foi por `TIMEOUT` ou `UNKNOWN` **antes** de `stream_complete`, fazer **1 retry** com backoff 2s
- [ ] Usar novo `search_id` no retry para evitar conflito com backend state
- [ ] Exibir banner "Reconectando..." durante retry (componente `DegradationBanner` já existe)
- [ ] Se segundo retry também falha, mostrar erro claro + botão "tentar novamente manualmente"

### AC3: Cleanup garantido em `useSearchSSEHandler`
- [ ] Adicionar `finally` block que:
  - [ ] Fecha EventSource (`eventSource.close()`)
  - [ ] Remove todos os listeners (`removeEventListener`)
  - [ ] Limpa `abortControllerRef.current = null`
  - [ ] Limpa `clientTimeoutId` via `clearTimeout`
- [ ] Usar `useEffect` cleanup para garantir execução ao unmount do componente

### AC4: Telemetria Sentry
- [ ] Breadcrumbs com eventos `sse_start`, `sse_progress`, `sse_close`, `sse_error`
- [ ] Custom context no Sentry:
  ```typescript
  Sentry.setContext('search_sse', {
    search_id: ...,
    elapsed_ms: ...,
    events_received: ...,
    stream_complete: true | false,
  });
  ```
- [ ] Filter rules no Sentry: ignorar eventos com `close_reason: USER_CANCELLED`

### AC5: Tests
- [ ] Jest test em `frontend/__tests__/hooks/useSearchAPI.test.ts`:
  - [ ] User cancela → nenhum erro reportado
  - [ ] Timeout → retry automático + success no segundo
  - [ ] Network error persistente → retry + error final
  - [ ] Cleanup: EventSource fechado ao unmount
- [ ] Test em `useSearchSSEHandler.test.ts` cobrindo finally cleanup

### AC6: UX
- [ ] Quando retry acontece, mostrar feedback visual sutil (ex: "Reconectando..." no banner)
- [ ] Sem retry infinito — max 1 retry automático para não frustrar usuário
- [ ] Botão "Tentar novamente" visível se retry falha

### AC7: Verificação pós-deploy
- [ ] Monitorar Sentry issue 7387910087 por 1 semana
- [ ] Volume de eventos deve cair **>80%** (remoção de user_cancelled)
- [ ] Eventos remanescentes devem ter `close_reason != USER_CANCELLED` — investigar individualmente

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `frontend/app/buscar/hooks/execution/useSearchAPI.ts` | Linhas 168-231 — abort reason + retry |
| `frontend/app/buscar/hooks/execution/useSearchSSEHandler.ts` | `finally` cleanup |
| `frontend/app/buscar/hooks/execution/useSearchState.ts` | (Se existir) expose retry state |
| `frontend/app/buscar/components/DegradationBanner.tsx` | Reusar para "Reconectando..." |
| `frontend/__tests__/hooks/useSearchAPI.test.ts` | Tests de close reason + retry |
| `frontend/__tests__/hooks/useSearchSSEHandler.test.ts` | Test de cleanup |
| `frontend/lib/sentry.ts` | Filter rule para USER_CANCELLED |

---

## Implementation Notes

- **AbortSignal.reason é padrão moderno:** supported em Chrome 100+, Firefox 97+, Safari 15.4+. Verificar se o target do SmartLic inclui navegadores legacy — se sim, usar polyfill.
- **User cancellation é feature:** usuários cancelam buscas de propósito (ex: digitaram filtro errado). NÃO é bug. Essa story separa o ruído do sinal.
- **Backend coordination:** verificar se `search_id` pode ser reutilizado no retry ou precisa ser novo (ver `routes/search.py` para state management).
- **SWR cache interaction:** se usuário cancela e retenta com mesmo filtro, SWR pode servir stale cache em vez de re-executar. Testar esse caminho.
- **Não aumentar timeout:** manter 65s — timeout é proteção contra requests travadas no servidor. Aumentar não resolve o bug.

---

## Dev Notes (preencher durante implementação)

<!-- @dev: documentar ratio user_cancelled vs network_abort descoberto via telemetria -->

---

## Verification

1. **Unit:** `npm test -- useSearchAPI` passa 100%
2. **Manual:** `/buscar`, iniciar busca, clicar X → sem erro no console
3. **Manual:** `/buscar`, iniciar busca, network offline → retry automático + banner
4. **Staging:** 100 buscas simuladas → volume Sentry cai >80%
5. **Produção:** Sentry issue 7387910087 em <5 eventos/semana após deploy

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
