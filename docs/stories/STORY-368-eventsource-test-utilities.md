# STORY-368 — EventSource Test Utilities (Shared Mock Infrastructure)

**Status:** completed
**Priority:** P2 — Test Infrastructure (10+ test files com mock duplicado)
**Origem:** Conselho CTO Advisory — Analise de falhas SSE no STORY-365 (2026-03-03)
**Componentes:** frontend/__tests__/utils/, frontend/jest.setup.js
**Depende de:** STORY-366 (Lazy Supabase Client)
**Bloqueia:** nenhuma
**Estimativa:** ~3h

---

## Contexto

Cada test file que testa SSE cria sua propria implementacao de `MockEventSource`. Foram identificadas **6 implementacoes distintas** espalhadas em 10 test files:

| Padrao | Arquivos | Caracteristicas |
|--------|----------|-----------------|
| `jest.setup.js` global | 1 | Auto-trigger `onerror` apos 0ms (!), nao suporta `addEventListener` real, nao suporta `lastEventId` |
| `class MockEventSource` com static instances | `gtm-fix-040-042-043.test.tsx` | Tracking de instances, `readyState` |
| `mockEventSources: any[]` com factory | `gtm-fix-033-sse-resilience.test.tsx` | Array tracking, sem `lastEventId` |
| `interface MockEventSource + makeMockES()` | `crit-052`, `sse-reconnection`, `useSearchSSE-uf-count` | Mais completo, `readyState`, `close()` |
| `mockEventSource: any` singleton | `job-queue-integration`, `useSearchProgress` | Mais simples, sem tracking |
| `useUfProgress-reconnection.test.tsx` | 1 | Hybrid com `lastEventId` support |

### Problemas

1. **Auto-trigger `onerror` em 0ms** no `jest.setup.js` global (linha 38) faz TODOS os EventSources falharem imediatamente. Testes que nao sobrescrevem o mock herdam esse comportamento destrutivo.
2. **6 implementacoes diferentes** significa 6 superficies de manutencao. Quando o contrato SSE muda (ex: novo campo `lastEventId`), cada mock precisa ser atualizado separadamente.
3. **`addEventListener` ignorado** no mock global — testes que usam named events (`uf_status`, `batch_progress`) precisam sobrescrever o mock inteiro.
4. **Sem helper `simulateMessage()`** — cada teste constroi manualmente `MessageEvent` objects ou invoca `onmessage` diretamente, com inconsistencias no formato.
5. **`lastEventId` nao propagado** em 4 das 6 implementacoes — testes de reconnect com `Last-Event-ID` sao frageis.

### Solucao

Criar um `MockEventSource` class compartilhado em `__tests__/utils/mock-event-source.ts` com API rica (`simulateMessage`, `simulateError`, `simulateOpen`) e instalar no `jest.setup.js` como global default.

## Acceptance Criteria

### AC1: Shared MockEventSource class

- [x] Novo arquivo `frontend/__tests__/utils/mock-event-source.ts` exporta `MockEventSource` class com:
  - `constructor(url: string)` — registra instance em `MockEventSource.instances` static array
  - `readyState`: `0` (CONNECTING) -> `1` (OPEN) -> `2` (CLOSED) — segue spec W3C
  - `onopen`, `onmessage`, `onerror` handlers
  - `addEventListener(type, listener)` — registra listeners por event type (funcional, nao no-op)
  - `removeEventListener(type, listener)` — remove listeners
  - `close()` — seta `readyState = 2` (handlers preservados per W3C spec)
  - `url` property (readonly)
  - `lastEventId` property (set automaticamente quando `simulateMessage` inclui `id` field)

### AC2: Helper methods

- [x] `simulateOpen()` — seta `readyState = 1`, chama `onopen`
- [x] `simulateMessage(data: string | object, options?: { id?: string, event?: string })` — se `event` fornecido, dispatcha via `addEventListener` listeners; senao, chama `onmessage`
  - Se `data` e object, faz `JSON.stringify` automaticamente
  - Se `options.id` fornecido, seta `lastEventId` e inclui no `MessageEvent`
- [x] `simulateError()` — chama `onerror` com `Event('error')`
- [x] `static instances: MockEventSource[]` — permite testes acessarem a instancia criada pelo hook
- [x] `static reset()` — limpa `instances` array (chamado no `beforeEach` global)

### AC3: jest.setup.js atualizado

- [x] Mock global de `EventSource` usa o novo `MockEventSource` de `__tests__/utils/mock-event-source.ts`
- [x] **NAO auto-trigger `onerror`** (remover o `setTimeout(() => onerror, 0)` atual)
- [x] `MockEventSource.reset()` chamado em `beforeEach` global para limpar instances entre testes

### AC4: Migrar testes existentes

- [x] Pelo menos 6 dos 10 test files com mock customizado migrados para usar o shared `MockEventSource`:
  - `gtm-fix-040-042-043.test.tsx`
  - `gtm-fix-033-sse-resilience.test.tsx`
  - `hooks/crit-052-sse-progress-regression.test.tsx`
  - `hooks/sse-reconnection.test.tsx`
  - `hooks/useSearchSSE-uf-count.test.tsx`
  - `hooks/useSearchProgress.test.ts`
  - `hooks/useUfProgress-reconnection.test.tsx` (7th file — bonus)
- [x] Testes que precisam de comportamento especifico (ex: `job-queue-integration`) podem manter mock local, mas devem documentar por que

### AC5: Documentacao

- [x] JSDoc completo no `MockEventSource` class
- [x] Exemplo de uso no topo do arquivo:
  ```typescript
  // Uso basico
  const { MockEventSource } = require('../utils/mock-event-source');
  const es = MockEventSource.instances[0];
  es.simulateOpen();
  es.simulateMessage({ stage: 'uf_status', detail: { uf: 'SP' } }, { id: '1' });
  es.simulateError();
  ```

### AC6: Verificacao

- [x] `npm test` com 4387+ passing, 0 new failures (21 pre-existing failures in unrelated suites)
- [x] Nenhum teste depende do comportamento "auto-trigger onerror em 0ms"
- [x] `MockEventSource.instances` e resetado entre testes (sem vazamento de estado)

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `frontend/__tests__/utils/mock-event-source.ts` | **NOVO** — shared MockEventSource class |
| `frontend/jest.setup.js` | Substituir mock inline por import do shared class, remover auto-error |
| `frontend/__tests__/gtm-fix-040-042-043.test.tsx` | Remover `class MockEventSource` local, usar shared |
| `frontend/__tests__/gtm-fix-033-sse-resilience.test.tsx` | Remover factory local, usar shared |
| `frontend/__tests__/hooks/crit-052-sse-progress-regression.test.tsx` | Remover `makeMockES`, usar shared |
| `frontend/__tests__/hooks/sse-reconnection.test.tsx` | Remover `makeMockES`, usar shared |
| `frontend/__tests__/hooks/useSearchSSE-uf-count.test.tsx` | Remover `makeMockES`, usar shared |
| `frontend/__tests__/hooks/useSearchProgress.test.ts` | Usar shared MockEventSource |
| `frontend/__tests__/hooks/useUfProgress-reconnection.test.tsx` | Usar shared se compativel |

## Notas Tecnicas

### W3C EventSource spec relevante

- `readyState`: 0=CONNECTING, 1=OPEN, 2=CLOSED
- `onmessage` recebe eventos sem nome (campo `event:` ausente no SSE stream)
- `addEventListener('uf_status', ...)` recebe eventos com `event: uf_status` no SSE stream
- `lastEventId` e setado pelo campo `id:` no SSE stream e enviado automaticamente no header `Last-Event-ID` em reconnects
- O browser nativo auto-reconnecta com intervalo default de 3s (override via `retry:` field)

### Por que remover o auto-error em 0ms

O mock atual em `jest.setup.js` (linha 37-39) faz:
```javascript
setTimeout(() => { if (this.onerror) this.onerror(new Event('error')); }, 0);
```

Isso foi adicionado para "simular falha de conexao e trigger fallback para progresso simulado". Porem, esse comportamento:
1. Faz QUALQUER teste que use EventSource (sem mock explicito) receber um erro inesperado
2. Causa race conditions em testes que configuram handlers apos o `new EventSource()` (o erro chega antes do handler ser setado)
3. Nao corresponde ao comportamento real — o browser tenta conectar e so dispara `onerror` se falhar

### MessageEvent mock

O `simulateMessage` deve criar um objeto compativel com `MessageEvent`:
```typescript
const messageEvent = {
  data: typeof data === 'string' ? data : JSON.stringify(data),
  lastEventId: options?.id ?? '',
  origin: '',
  ports: [],
  source: null,
  type: options?.event ?? 'message',
};
```

### Interacao com STORY-367

Se STORY-367 (consolidacao de hooks) for executado primeiro, havera menos test files para migrar. Se STORY-368 for primeiro, STORY-367 se beneficia do mock compartilhado para escrever novos testes. A ordem ideal e: 366 -> 368 -> 367.
