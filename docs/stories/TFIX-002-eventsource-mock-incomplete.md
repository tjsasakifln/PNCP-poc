# TFIX-002: Corrigir mock de EventSource no jest.setup.js (addEventListener)

**Status:** Pending
**Prioridade:** Alta
**Estimativa:** 2h
**Arquivos afetados:** 1 setup + 2 test files

## Problema

Testes que exercitam SSE (ux-transparente, sse-resilience) falham com `TypeError: eventSource.addEventListener is not a function` quando o hook `useSearchSSE.ts` tenta registrar listeners para eventos nomeados.

## Causa Raiz

O polyfill de `EventSource` em `jest.setup.js` define `addEventListener()` como **método vazio sem parâmetros**:

```javascript
// jest.setup.js (atual)
addEventListener() {}  // Empty — ignora argumentos, não armazena listeners
```

Porém `useSearchSSE.ts` (linhas 261, 275) chama:
```javascript
eventSource.addEventListener('uf_status', (e: MessageEvent) => { ... })
eventSource.addEventListener('batch_progress', (e: MessageEvent) => { ... })
```

Como o polyfill descarta os listeners silenciosamente, os testes não conseguem simular eventos nomeados nem disparar callbacks.

## Testes que serão corrigidos

- `ux-transparente.test.tsx`: 2 falhas (T7 retry on 500, retry on 502)
- Potencialmente outros testes futuros que usem SSE com eventos nomeados

## Critérios de Aceitação

- [ ] AC1: `EventSource` mock em `jest.setup.js` implementa `addEventListener(type, fn)` armazenando listeners por tipo
- [ ] AC2: `EventSource` mock implementa mecanismo para disparar eventos nomeados nos testes (ex: `dispatchEvent` ou `__emit`)
- [ ] AC3: `removeEventListener` funciona corretamente
- [ ] AC4: `ux-transparente.test.tsx` T7 (retry tests) passa — 0 falhas por EventSource
- [ ] AC5: `sse-resilience.test.tsx` não regride
- [ ] AC6: Manter compatibilidade com testes existentes que usam `onmessage`/`onerror`

## Solução

Reescrever o polyfill `EventSource` em `jest.setup.js` para:

```javascript
class MockEventSource {
  constructor(url) {
    this.url = url;
    this.readyState = 0;
    this._listeners = {};
    this.onmessage = null;
    this.onerror = null;
    this.onopen = null;
    // Auto-open
    setTimeout(() => {
      this.readyState = 1;
      if (this.onopen) this.onopen();
    }, 0);
  }
  addEventListener(type, fn) {
    if (!this._listeners[type]) this._listeners[type] = [];
    this._listeners[type].push(fn);
  }
  removeEventListener(type, fn) {
    if (!this._listeners[type]) return;
    this._listeners[type] = this._listeners[type].filter(l => l !== fn);
  }
  dispatchEvent(event) {
    const type = event.type || 'message';
    (this._listeners[type] || []).forEach(fn => fn(event));
  }
  close() { this.readyState = 2; }
}
```

Os testes podem então simular eventos via `dispatchEvent` ou precisa atualizar os testes para usar a nova interface.

## Arquivos

- `frontend/jest.setup.js` — reescrever EventSource mock
- `frontend/__tests__/story-257b/ux-transparente.test.tsx` — atualizar se necessário
- `frontend/__tests__/gtm-fix-033-sse-resilience.test.tsx` — verificar compatibilidade
