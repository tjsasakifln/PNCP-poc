# GTM-STAB-006 — SSE Proxy Resilience e Graceful Error Handling

**Status:** To Do
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
- [ ] `app/api/buscar-progress/[id]/route.ts` — wrap pipe em try/catch:
  - Se pipe error + backend alive: retry pipe uma vez (5s delay)
  - Se pipe error + backend dead: enviar SSE `error` event com payload structured
  - Se pipe error + partial data disponível: enviar SSE `degraded` com partial results
- [ ] Nunca propagate "failed to pipe response" raw para Sentry — capturar e traduzir
- [ ] Log structured: `{ error_type: "pipe_broken", search_id, elapsed_ms, bytes_transferred }`

### AC2: Frontend error UX humanizada
- [ ] Substituir mensagem de erro atual por UX contextual:
  | Cenário | Mensagem | Ação |
  |---------|----------|------|
  | Timeout (524) | "A busca demorou mais que o esperado" | [Tentar com menos estados] [Tentar novamente] |
  | Partial fail | "Resultados parciais: 2 de 4 estados responderam" | Mostrar resultados + [Buscar estados restantes] |
  | Backend down | "Nossos servidores estão se atualizando" | [Tentar em 30 segundos] com countdown |
  | All sources fail | "As fontes oficiais estão indisponíveis" | [Ver último resultado salvo] [Tentar em 5 min] |
- [ ] Tom: empático e orientado à ação, NUNCA técnico
- [ ] Cores: azul/amarelo para atenção, NUNCA vermelho (vermelho = pânico)
- [ ] Botão primário: azul "Tentar novamente" (não vermelho)

### AC3: Auto-recovery on timeout
- [ ] Quando 524/timeout detectado no frontend:
  1. Verificar se há partial results em cache (localStorage key `last_search_{search_id}`)
  2. Se sim: exibir partial results + banner "Resultados da tentativa anterior"
  3. Se não: exibir empty state com sugestão de reduzir escopo
  4. Auto-retry com escopo reduzido (menos UFs, ou período menor) em background
- [ ] Auto-retry silencioso: resultado aparece sem ação do usuário
- [ ] Máximo 2 auto-retries, depois oferecer ação manual

### AC4: Partial results persistence
- [ ] A cada SSE `partial_results` ou `uf_complete`, salvar em localStorage:
  ```javascript
  localStorage.setItem(`search_partial_${searchId}`, JSON.stringify({
    items: [...],
    timestamp: Date.now(),
    ufs_completed: ["SP", "ES"],
    ufs_pending: ["MG", "RJ"]
  }));
  ```
- [ ] Se conexão SSE morre, recuperar partial results do localStorage
- [ ] TTL de 30 minutos para partial results (não stale data)
- [ ] Limpar após busca completa com sucesso

### AC5: SSE reconnection
- [ ] Se SSE connection drops mas search_id é válido:
  1. Tentar reconectar SSE em 3s (exponential: 3s, 6s, 12s)
  2. Se reconectar: continuar recebendo eventos (backend mantém tracker por 5 min)
  3. Se 3 tentativas falham: mostrar partial results + "Conexão instável"
- [ ] `EventSource.onerror` handler deve diferenciar:
  - Temporary disconnect → retry
  - Permanent failure (4xx) → stop + show error

### AC6: Sentry noise reduction
- [ ] "failed to pipe response" deve ser capturado como WARNING, não ERROR
- [ ] Adicionar `beforeSend` filter no Sentry config: skip "pipe" errors com elapsed > 110s (timeout esperado)
- [ ] Apenas pipe errors inesperados (< 30s, sem timeout) devem ir para Sentry como ERROR
- [ ] Meta: reduzir de 19 eventos para <2 por semana

### AC7: Testes
- [ ] Frontend: test SSE pipe break → error UX contextual (não erro bruto)
- [ ] Frontend: test auto-recovery → partial results exibidos após timeout
- [ ] Frontend: test SSE reconnection → 3 tentativas com backoff
- [ ] Frontend: test localStorage partial persistence → recovered on reconnect
- [ ] E2E: simular timeout via slow network → error UX aparece em <5s após disconnect

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
