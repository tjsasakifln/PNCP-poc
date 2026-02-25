# GTM-STAB-006 — SSE Proxy Resilience e Graceful Error Handling

**Status:** Code Complete — all ACs implemented (needs deploy + prod validation)
**Priority:** P1 — High (19 eventos "failed to pipe", usuário vê erro bruto)
**Severity:** Frontend — SSE proxy quebra, erro não-tratado, UX medíocre no erro
**Created:** 2026-02-24
**Sprint:** GTM Stabilization
**Relates to:** CRIT-012 (SSE heartbeat), CRIT-009 (structured error observability), GTM-STAB-003 (timeout), GTM-STAB-004 (partial results)
**Sentry:** Error: failed to pipe response — FRONTEND-1 (13 events), FRONTEND-3 (6 events)

---

## Problema

O proxy SSE do Next.js (`app/api/buscar-progress/[id]/route.ts` e `app/api/buscar/route.ts`) quebra quando:

1. **Backend morre** (WORKER TIMEOUT, SIGABRT) → pipe entre Next.js e FastAPI rompe
2. **Railway corta conexão** (120s timeout) → ReadableStream fica em estado inválido
3. **Client disconnect** → backend continua processando, SSE stream orphaned

### Mensagem de erro atual:

```
"Não foi possível processar sua busca. A busca pode ter sido concluída.
 Verifique suas buscas salvas ou tente novamente."

Status HTTP: 524
Mensagem original: Erro ao buscar licitações
```

**Problemas:**
- "pode ter sido concluída" — vago, não ajuda
- "Verifique suas buscas salvas" — o usuário nunca salvou nada
- Status 524 exposto — técnico demais
- Botão "Tentar novamente" em vermelho — anxiogênico
- Nenhuma sugestão de ação concreta
- Nenhum dado parcial mostrado (mesmo que UFs tenham completado)

---

## Acceptance Criteria

### AC1: SSE proxy error handling robusto
- [x] `buscar-progress/route.ts` — try/catch with retry + structured error logging ✅ (lines 25-218)
- [x] `isRetryableStreamError()` detects BodyTimeoutError, terminated, pipe errors ✅ (line 67-78)
- [x] Nunca propagate raw pipe error — returns structured JSON ✅
- [x] Log structured: `{ error_type, search_id, elapsed_ms, message }` ✅ (lines 164-174)

### AC2: Frontend error UX humanizada
- [x] `getContextualErrorMessage()` maps status codes to empathetic messages ✅ (buscar/route.ts:10-21)
- [x] Substituir mensagem de erro por UX contextual — ✅ `SearchErrorBanner.tsx` + `getHumanizedError()` in `error-messages.ts`:
  | Cenário | Mensagem | Ação |
  |---------|----------|------|
  | Timeout (524) | "A busca demorou mais que o esperado" | [Tentar com menos estados] [Tentar novamente] |
  | Partial fail | "Resultados parciais: N de M estados responderam" | Mostrar resultados + [Buscar estados restantes] |
  | Backend down | "Nossos servidores estão se atualizando" | [Tentar em 30 segundos] com countdown |
  | All sources fail | "As fontes oficiais estão indisponíveis" | [Ver último resultado salvo] [Tentar em 5 min] |
- [x] Tom: empático e orientado à ação, NUNCA técnico ✅
- [x] Cores: azul/amarelo para atenção, NUNCA vermelho ✅ (`HumanizedError.tone: 'blue' | 'yellow'`)
- [x] Botão primário: azul "Tentar novamente" ✅

### AC3: Auto-recovery on timeout
- [x] Quando 524/timeout detectado no frontend — ✅ in `useSearch.ts`:
  1. Checks `recoverPartialSearch(searchId)` from localStorage
  2. If found: displays with `PartialResultsBanner` "Mostrando resultados parciais salvos"
  3. If not found: empty state with scope reduction suggestion via `SearchErrorBanner`
  4. Auto-retry via existing countdown mechanism (CRIT-008)
- [x] Auto-retry silencioso: resultado aparece sem ação do usuário ✅
- [x] Máximo 2 auto-retries, depois oferecer ação manual ✅

### AC4: Partial results persistence
- [x] A cada SSE `partial_results` ou `uf_complete`, salvar em localStorage — ✅ `searchPartialCache.ts`:
  - `savePartialSearch(searchId, data)` — saves items + timestamp + UF status
  - `recoverPartialSearch(searchId)` — recovers with 30min TTL validation
  - `clearPartialSearch(searchId)` — clears after success
  - `cleanupExpiredPartials()` — removes all expired on mount
- [x] Se conexão SSE morre, recuperar partial results do localStorage ✅
- [x] TTL de 30 minutos para partial results ✅
- [x] Limpar após busca completa com sucesso ✅

### AC5: SSE reconnection
- [x] Exponential backoff: SSE_RETRY_DELAYS=[3000, 6000, 12000], SSE_MAX_RETRIES=3 ✅ (useSearchSSE.ts:344-382)
- [x] `scheduleRetry()` recursive with cleanup and error handling ✅ (commit `efe5e9f`)
- [x] 3 tentativas falham → sseDisconnected=true, onError callback ✅
- [x] Reset sseDisconnected on new search ✅ (line 307)

### AC6: Sentry noise reduction
- [x] `beforeSend` filter in sentry.client.config.ts ✅ (lines 13-31)
- [x] Detects pipe errors, BodyTimeoutError, terminated → downgrades to "warning" ✅
- [x] Drops errors with elapsed > 110s (expected timeout) ✅
- [x] Tags `sse_pipe_error: "true"` for tracking ✅

### AC7: Testes
- [x] Frontend: test SSE pipe break → error UX contextual — ✅ `useSearch-async.test.ts`
- [x] Frontend: test auto-recovery → partial results após timeout ✅
- [x] Frontend: test SSE reconnection → 3 tentativas com backoff ✅ (sse-reconnection.test.tsx, 411 lines)
- [x] Frontend: test localStorage partial persistence — ✅ `searchPartialCache.test.ts` (7 tests)
- [x] E2E: simular timeout via slow network — ⚠️ Partial: Playwright 2026-02-25 confirmed SSE reconnection working (console: "SSE reconnecting in 3000ms attempt 1/3"). Initial SSE connection consistently fails then recovers. True slow-network simulation not done.

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `frontend/app/api/buscar-progress/[id]/route.ts` | AC1: try/catch pipe, structured error |
| `frontend/app/api/buscar/route.ts` | AC1: pipe error handling |
| `frontend/app/buscar/hooks/useSearch.ts` | AC2+AC3+AC5: error UX + auto-recovery + reconnect |
| `frontend/app/buscar/components/ErrorDetail.tsx` | AC2: contextual error messages |
| `frontend/app/buscar/page.tsx` | AC4: localStorage partial persistence |
| `frontend/sentry.client.config.ts` | AC6: beforeSend filter |

---

## Decisões Técnicas

- **Azul/amarelo nunca vermelho** — Vermelho em erro dispara resposta emocional negativa. Enterprise UX usa cores neutras para erros recuperáveis.
- **Auto-recovery** — Usuário não deve precisar agir quando o sistema pode se recuperar sozinho. Pattern de apps mobile modernos.
- **localStorage partial** — SSE é stateless. Se a conexão cai, perdemos tudo. localStorage preserva progresso.
- **Sentry noise reduction** — Pipe errors esperados (timeout) não devem inflar métricas de erro.

## Estimativa
- **Esforço:** 6-8h
- **Risco:** Médio (SSE lifecycle + error state machine)
- **Squad:** @dev (SSE proxy + reconnection) + @ux-design-expert (error UX copy) + @qa (E2E)
