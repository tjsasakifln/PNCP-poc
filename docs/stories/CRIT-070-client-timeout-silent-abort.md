# CRIT-070: Client Timeout Silencioso — Busca Reseta para Tela Inicial

**Prioridade:** P0 — Hotfix
**Componente:** Frontend — useSearchExecution.ts
**Origem:** Incidente 2026-03-06 — Busca com 8520 resultados (search_id `195c884f`) completou no backend em 224s (HTTP 200), mas frontend abortou em 115s e voltou para tela inicial sem feedback
**Status:** DONE
**Dependencias:** Nenhuma (fix isolado)
**Estimativa:** 30min

## Problema

Quando a busca demora >115s, o `AbortController` do client (`useSearchExecution.ts:313-315`) aborta o fetch. O handler de `AbortError` (linha 569-577) tenta `recoverPartialSearch()`, mas se nao houver partial salvo, faz `return` silencioso. O `finally` block seta `loading=false` com `result=null` e `error=null` — UI volta ao estado inicial sem qualquer feedback.

### Timeline do incidente (search_id `195c884f`)

```
T+0s     POST /v1/buscar enviado + SSE conectado
T+0-115s SSE mostrando progresso (8500+ encontrados, 27 UFs)
T+115s   abortController.abort() dispara — fetch cancelado
T+115s   catch(AbortError) → recoverPartialSearch() → null → return silencioso
T+115s   finally → setLoading(false), result=null, error=null → TELA INICIAL
T+191s   Backend completa pipeline (8520 raw, 7115 filtrados)
T+224s   Backend retorna HTTP 200 — mas ninguem le a resposta
```

### Desalinhamento de timeouts

```
Client (browser):   115s ← ABORTA AQUI (causa raiz)
Proxy POST:         180s ← nunca atingido
Backend pipeline:   191s ← completou com sucesso
Backend total:      224s ← retornou HTTP 200
```

O CRIT-060 corrigiu o proxy de 115s→180s, mas o **client-side** ficou em 115s.

### Evidencia nos logs Railway

```
[WARN] [STAB-003] Time budget exceeded after filter (191.0s > 90s)
[INFO] POST /v1/buscar -> 200 (224588ms)
```

Backend processou com sucesso. O problema e exclusivamente no frontend.

## Acceptance Criteria

### AC1: Alinhar client timeout com proxy timeout
- [x] Mudar `clientTimeoutId` de `115_000` → `185_000` ms em `useSearchExecution.ts:313-315`
- [x] Client timeout deve ser >= proxy timeout (180s) para evitar abort antes do proxy responder
- [x] Comentario: `// CRIT-070: Client timeout >= proxy (180s). Chain: Railway(300s) > Gunicorn(180s) > Proxy(180s) >= Client(185s)`

### AC2: Abort sem partial deve mostrar erro, nunca retornar silenciosamente
- [x] Em `useSearchExecution.ts` catch block para `AbortError` (linha 569-577): quando `recoverPartialSearch()` retorna null, setar `SearchError` com:
  - `message`: "A análise demorou mais que o esperado. Tente com menos estados."
  - `httpStatus`: 524
  - `errorCode`: "CLIENT_TIMEOUT"
- [x] Chamar `startAutoRetry(searchError, setError)` para permitir retry automatico
- [x] Nunca fazer `return` silencioso sem setar erro ou resultado

### AC3: Alinhar finalizing timer
- [x] Mudar `finalizingTimer` de `100_000` → `160_000` ms (coerente com novo client timeout de 185s)
- [x] Usuario ve "Finalizando..." nos ultimos ~25s antes do timeout

### AC4: Log de rastreabilidade
- [x] Adicionar `console.warn('[CRIT-070] Client timeout triggered', { searchId: newSearchId, elapsed: Date.now() - searchStartTime })` no abort handler

### AC5: Testes
- [x] Teste: abort sem partial → mostra SearchError com httpStatus 524
- [x] Teste: abort com partial → mostra partial results (comportamento existente preservado)
- [x] Teste: timeout value e 185_000 (nao 115_000)
- [x] Teste: startAutoRetry e chamado no caso de abort sem partial

## File List

| Arquivo | Mudanca |
|---------|---------|
| `frontend/app/buscar/hooks/useSearchExecution.ts` | Timeout 115s→185s, abort handler com erro, finalizing timer |
| `frontend/__tests__/buscar/` | Novos testes para abort handling |

## Referencia

- Google SRE Book: [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/) — client timeout < server timeout e anti-pattern
- CRIT-060: Corrigiu proxy 115s→180s mas nao corrigiu client
- CRIT-012: SSE heartbeat gap (corrigido)
