# STORY-367 — Consolidacao dos SSE Hooks (Eliminar Divergencia de Retry)

**Status:** completed
**Priority:** P2 — Debito tecnico (3 estrategias de retry divergentes)
**Origem:** Conselho CTO Advisory — Analise de falhas SSE no STORY-365 (2026-03-03)
**Componentes:** frontend/hooks/useSearchSSE.ts, frontend/hooks/useSearchProgress.ts, frontend/app/buscar/hooks/useUfProgress.ts
**Depende de:** STORY-365 (SSE Heartbeat & Auto-Reconnection), STORY-366 (Lazy Supabase Client)
**Bloqueia:** nenhuma
**Estimativa:** ~5h

---

## Contexto

Existem **3 hooks SSE** no frontend, cada um com estrategia de reconnection diferente:

| Hook | Arquivo | Retries | Backoff | Polling Fallback | Origem |
|------|---------|---------|---------|------------------|--------|
| `useSearchSSE` | `hooks/useSearchSSE.ts` | 3 | 0ms, 3s, 6s | Nao | CRIT-052/STAB-006 |
| `useSearchProgress` | `hooks/useSearchProgress.ts` | 1 | 2s fixo | Nao | GTM-FIX-033 (deprecated) |
| `useUfProgress` | `app/buscar/hooks/useUfProgress.ts` | 3 | 1s, 2s, 4s | Sim (5s polling) | STORY-365 |

### Problemas

1. **3 estrategias diferentes** para o mesmo endpoint SSE (`/api/buscar-progress`) cria UX inconsistente
2. `useSearchProgress` esta marcado como `@deprecated` (CRIT-006 AC9) mas ainda existe e ainda e importado em testes
3. `useUfProgress` (STORY-365) duplica funcionalidade de `useSearchSSE` — ambos fazem parse de `uf_status` e `batch_progress`
4. `useSearchSSE` (509 linhas) ja incorporou toda logica de UF progress do `useUfProgress` original
5. Quando `useSearchSSE` e `useUfProgress` rodam simultaneamente para o mesmo `search_id`, abrem 2 EventSource connections para a mesma URL

### Solucao

Consolidar em um unico hook (`useSearchSSE`) com a melhor estrategia de cada:
- Backoff do STORY-365: 1s, 2s, 4s (mais conservador que 0ms/3s/6s)
- Polling fallback do STORY-365 (5s polling via `/v1/search/{id}/status`)
- `Last-Event-ID` forwarding do STORY-365
- Monotonic progress (high-water mark) do CRIT-052
- Deprecar e remover `useSearchProgress` e `useUfProgress`

## Acceptance Criteria

### AC1: Estrategia de retry unificada

- [x] `useSearchSSE` adota backoff `[1000, 2000, 4000]` ms (padrao STORY-365, mais defensivo)
- [x] Max 3 tentativas de reconnect (mantido)
- [x] Apos 3 falhas, ativa polling fallback via `GET /v1/search/{id}/status` a cada 5s (do STORY-365 AC9)
- [x] Constantes extraidas como named constants: `SSE_RECONNECT_BACKOFF_MS`, `SSE_MAX_RETRIES`, `SSE_POLLING_INTERVAL_MS`

### AC2: Remover useSearchProgress

- [x] `hooks/useSearchProgress.ts` deletado
- [x] Todos os imports atualizados para `useSearchSSE`
- [x] `__tests__/hooks/useSearchProgress.test.ts` atualizado para testar `useSearchSSE` com interface equivalente
- [x] Zero referencias restantes a `useSearchProgress` no codebase (exceto CHANGELOG)

### AC3: Absorver useUfProgress no useSearchSSE

- [x] `useSearchSSE` incorpora polling fallback (AC9 do STORY-365)
- [x] `useSearchSSE` incorpora `isTerminalRef` guard para nao reconectar apos `complete`/`error`/`degraded`
- [x] `app/buscar/hooks/useUfProgress.ts` mantido como **re-export fino** de `useSearchSSE` para backward compatibility:
  ```typescript
  export function useUfProgress(opts) {
    const sse = useSearchSSE({ ...opts, selectedUfs: opts.selectedUfs });
    return { ufStatuses: sse.ufStatuses, totalFound: sse.ufTotalFound, ... };
  }
  ```
- [x] `app/buscar/page.tsx` (ou equivalente) NAO abre 2 EventSource connections para o mesmo search_id

### AC4: Single EventSource per search_id

- [x] Se `useSearchSSE` e chamado multiplas vezes com o mesmo `searchId` (via useUfProgress wrapper + uso direto), apenas UMA EventSource connection e aberta
- [x] Implementar via ref sharing ou via verificacao de `searchId` antes de criar nova connection

### AC5: Testes

- [x] Testes de `useSearchSSE` cobrem:
  - Reconnect com backoff 1s/2s/4s (usar `jest.useFakeTimers()`)
  - Polling fallback apos 3 falhas
  - Terminal event previne reconnect
  - `Last-Event-ID` incluido na URL de reconnect
  - Monotonic progress (high-water mark) mantido apos reconnect
- [x] Testes de `useUfProgress` wrapper validam que retorno e compativel
- [x] Zero regressoes: `npm test` com 2681+ passing, 0 failures

### AC6: Documentacao inline

- [x] JSDoc no topo de `useSearchSSE.ts` lista todas as estrategias de resiliencia com referencia a stories
- [x] Tabela de constantes com valores e justificativas

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `frontend/hooks/useSearchSSE.ts` | Adotar backoff [1s,2s,4s], polling fallback, terminal guard |
| `frontend/hooks/useSearchProgress.ts` | **DELETAR** |
| `frontend/app/buscar/hooks/useUfProgress.ts` | Reduzir a thin wrapper sobre useSearchSSE |
| `frontend/app/buscar/page.tsx` | Verificar que nao abre 2 SSE connections |
| `frontend/__tests__/hooks/useSearchProgress.test.ts` | Migrar para testar useSearchSSE |
| `frontend/__tests__/hooks/useUfProgress-reconnection.test.tsx` | Atualizar para usar wrapper |
| `frontend/__tests__/gtm-fix-033-sse-resilience.test.tsx` | Atualizar para useSearchSSE |

## Notas Tecnicas

### Por que 1s/2s/4s e melhor que 0ms/3s/6s

O backoff `[0, 3000, 6000]` atual (STAB-006) usa retry imediato (0ms) na primeira falha. Isso foi intencional para o "async race condition" onde o tracker ainda nao existe. Porem, com STORY-365 (Redis-backed progress state), essa race condition desaparece — o endpoint pode retornar eventos do Redis mesmo sem tracker ativo.

### Verificacao de conexao duplicada

Buscar no `page.tsx` por chamadas a `useSearchSSE` e `useUfProgress` com o mesmo `searchId`. Se ambos estao presentes, e uma conexao duplicada.

### isTerminalRef pattern

O `useUfProgress` do STORY-365 ja implementa `isTerminalRef` — um ref booleano que e setado `true` quando um evento terminal (`complete`, `error`, `degraded`) chega. Isso previne reconnect apos busca finalizada. O `useSearchSSE` atual faz `cleanup()` no terminal mas nao previne que o `scheduleRetry()` ja agendado crie uma nova conexao.

### Polling fallback endpoint

O polling usa `GET /api/buscar?endpoint=search/{id}/status` (proxy para `/v1/search/{id}/status`). Este endpoint retorna `{ status: 'pending' | 'processing' | 'completed' | 'error', ... }`. O polling deve parar quando status e `completed` ou `error`.

### Migracao incremental

1. Primeiro: adicionar polling fallback e terminal guard ao `useSearchSSE`
2. Segundo: converter `useUfProgress` em thin wrapper
3. Terceiro: deletar `useSearchProgress` e migrar testes
4. Quarto: verificar zero conexoes duplicadas
