# CRIT-008: Resiliencia do Frontend Durante Restarts do Backend

## Epic
Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 5: Resiliencia de Producao

## Prioridade
P0

## Estimativa
16h

## Descricao

Quando o backend reinicia (deploy, crash, restart policy), o frontend exibe dois sinais graves simultaneamente sem explicacao util ao usuario:

1. **Banner "Usando lista offline de setores"** — fetch de setores falha 3x com backoff (1s, 2s) e cai no `SETORES_FALLBACK` hardcoded
2. **"Erro no backend"** — busca falha com mensagem generica, sem indicacao de que e transiente

O usuario nao tem como saber que o problema e temporario e que basta aguardar 30 segundos. O sistema deveria:
- Usar cache expirado (stale) em vez de fallback hardcoded para setores
- Diferenciar erro transiente (restart) de erro permanente (bug)
- Oferecer retry automatico com countdown

### Situacao Atual

| Componente | Comportamento atual | Problema |
|------------|---------------------|----------|
| Setores fetch | 3 tentativas (0s, 1s, 2s) → fallback hardcoded | Cache localStorage (5min TTL) ignorado se expirado; fallback nao tem `description` atualizado |
| Busca | 1 tentativa → "Erro no backend" | Nenhum retry automatico; nenhuma indicacao de transitoriedade |
| Health probe | Loga `Backend health check failed with status: 404` | Mensagem nos logs confunde com problema de infra; nao envia telemetria |
| Banner offline | Aparece e fica ate pagina recarregar | Nao tenta auto-recovery periodico |

### Evidencia da Investigacao (CRIT-INVESTIGATION 2026-02-20)

**Fluxo capturado:**
1. Backend reinicia → indisponivel por ~10-30s
2. Frontend `GET /api/setores` → proxy → `${BACKEND_URL}/v1/setores` → falha
3. 3 tentativas com backoff (1s, 2s) → todas falham → `setoresUsingFallback = true`
4. Banner aparece: "Usando lista offline de setores. Alguns setores novos podem nao aparecer."
5. Usuario tenta busca → `POST /api/buscar` → falha → "Erro no backend"
6. "Detalhes tecnicos" praticamente vazios (apenas timestamp + mensagem generica)

**Confirmacao ao vivo:** Backend saudavel apos restart. Problema e 100% transiente.

## Criterios de Aceite

### Setores: Stale-While-Revalidate no Frontend

- [x] AC1: Quando fetch de setores falha e existe cache localStorage expirado (>5min), usar o cache expirado em vez do `SETORES_FALLBACK` hardcoded
  - `useSearchFilters.ts:fetchSetores()` deve verificar localStorage ANTES de cair no fallback
  - Novo estado: `setoresUsingStaleCache: boolean` (diferente de `setoresUsingFallback`)
  - Banner diferenciado: "Usando setores em cache. Atualizando em segundo plano..." (amarelo claro)
  - Fallback hardcoded so deve ser usado se NAO houver cache nenhum (primeira visita)

- [x] AC2: Apos usar cache stale, tentar revalidar em background a cada 30 segundos (max 5 tentativas)
  - Implementar `setInterval` com cleanup no `useEffect` return
  - Se revalidacao bem-sucedida: atualizar setores + cache + remover banner silenciosamente
  - Se todas 5 tentativas falharem: manter cache stale + mostrar banner com "Tentar atualizar" manual
  - Nao bloquear interacao do usuario durante revalidacao

- [x] AC3: Banner de setores deve diferenciar 3 estados:
  - `stale_cache`: "Usando setores em cache (atualizado ha X min). Atualizando..." — tom informativo (azul)
  - `fallback`: "Usando lista offline de setores." — tom warning (amarelo) — somente quando nao ha cache
  - `recovered`: Banner desaparece com fade-out quando setores atualizados com sucesso

### Busca: Deteccao de Erro Transiente + Auto-Retry

- [x] AC4: Quando busca falha com HTTP 502/503/504 ou network error, frontend deve classificar como "erro transiente"
  - Novo tipo em `error-messages.ts`: `TRANSIENT_ERROR`
  - Mensagem: "O servidor esta reiniciando. Tentando novamente em {countdown}s..."
  - Diferente de erros permanentes (400, 401, 403, 422) que nao fazem retry

- [x] AC5: Para erros transientes, implementar auto-retry com countdown visual
  - Countdown: 10s → 20s → 30s (backoff exponencial truncado)
  - Maximo 3 tentativas automaticas
  - UI: barra de progresso circular com countdown + botao "Tentar agora" + botao "Cancelar"
  - Se todas 3 falharem: mostrar erro final com opcao manual

- [x] AC6: Erros permanentes (400, 401, 403, 422, 429) NAO devem ter auto-retry
  - Manter comportamento atual para esses codigos
  - 429 (rate limit) deve mostrar: "Limite de buscas atingido. Tente novamente em X minutos."

### Health Probe: Telemetria Estruturada

- [x] AC7: Frontend health probe (`/api/health/route.ts`) deve emitir evento de telemetria quando backend esta indisponivel
  - Usar `analytics_events` (Mixpanel) se disponivel, senao `console.warn`
  - Evento: `backend_health_check_failed` com campos: `status`, `timestamp`, `latency_ms`, `backend_url`
  - Rate limit: max 1 evento por minuto (evitar flood)

- [x] AC8: Log do health probe deve ser mais descritivo que `Backend health check failed with status: 404`
  - Incluir: URL tentada, tempo de resposta, headers relevantes
  - Formato: `[HealthCheck] Backend probe failed: GET ${url} → ${status} (${latencyMs}ms)`
  - Se `status === 404`: adicionar nota `(endpoint may not exist or backend may be restarting)`

### UX: Indicador Global de Conectividade

- [x] AC9: Implementar indicador discreto de conectividade do backend no header da pagina de busca
  - Quando backend saudavel: nada visivel (estado default)
  - Quando backend indisponivel: dot vermelho pulsante + tooltip "Servidor reiniciando..."
  - Quando backend recupera: dot verde por 3s → desaparece
  - Componente: `BackendStatusIndicator.tsx` em `components/`
  - Fonte de dados: polling do `/api/health` a cada 30s (somente quando pagina esta visivel — `document.visibilityState`)

- [x] AC10: Quando `BackendStatusIndicator` detecta backend offline, pre-informar o usuario ANTES de tentar busca
  - Se usuario clicar "Buscar" com backend offline: mostrar toast "Servidor indisponivel no momento. A busca sera iniciada quando o servidor estiver disponivel." + enfileirar busca
  - Quando backend voltar (detected via polling): executar busca enfileirada automaticamente + toast "Servidor disponivel. Executando busca..."

## Testes Obrigatorios

### Frontend (jest)

```bash
cd frontend && npm test -- --testPathPattern="search-resilience|backend-status|useSearchFilters" --no-coverage
```

- [x] T1: `useSearchFilters` — cache stale usado quando fetch falha e cache expirado existe
- [x] T2: `useSearchFilters` — fallback hardcoded usado quando nenhum cache existe
- [x] T3: `useSearchFilters` — revalidacao background atualiza setores e remove banner
- [x] T4: `useSearchFilters` — revalidacao background para apos 5 tentativas falhas
- [x] T5: `useSearch` — erro transiente (502/503/504) dispara auto-retry com countdown
- [x] T6: `useSearch` — erro permanente (400/401/403) NAO dispara auto-retry
- [x] T7: `useSearch` — countdown visual decrementa corretamente
- [x] T8: `useSearch` — "Tentar agora" durante countdown executa retry imediato
- [x] T9: `useSearch` — "Cancelar" durante countdown cancela retry e mostra erro final
- [x] T10: `useSearch` — auto-retry bem-sucedido na 2a tentativa mostra resultados normalmente
- [x] T11: `BackendStatusIndicator` — mostra dot vermelho quando backend offline
- [x] T12: `BackendStatusIndicator` — mostra dot verde 3s quando backend recupera
- [x] T13: `BackendStatusIndicator` — nao faz polling quando pagina nao esta visivel
- [x] T14: Health route — emite evento telemetria quando backend falha (max 1/min)

### Pre-existing baseline
- Frontend: ~51 fail / ~1969 pass — nenhuma regressao (15 suites pre-existentes, 0 novas)

## Definicao de Pronto

- [x] Todos os ACs implementados e checkboxes marcados
- [x] 14 testes novos passando
- [x] Zero regressoes no baseline frontend
- [x] TypeScript compila sem erros (`npx tsc --noEmit`)
- [ ] Testado manualmente: simular backend offline → verificar UX de recovery
- [x] Story file atualizado com `[x]` em todos os checkboxes

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/app/buscar/hooks/useSearchFilters.ts` | Modificar — stale cache logic, revalidacao background |
| `frontend/app/buscar/hooks/useSearch.ts` | Modificar — transient error detection, auto-retry |
| `frontend/app/buscar/components/SearchForm.tsx` | Modificar — 3 estados de banner (stale/fallback/recovered) |
| `frontend/app/api/health/route.ts` | Modificar — telemetria estruturada, log descritivo |
| `frontend/lib/error-messages.ts` | Modificar — adicionar TRANSIENT_ERROR type |
| `frontend/components/BackendStatusIndicator.tsx` | Criar — indicador de conectividade |
| `frontend/app/buscar/page.tsx` | Modificar — integrar BackendStatusIndicator |
| `frontend/__tests__/search-resilience.test.tsx` | Criar — testes T1-T14 |

## Notas Tecnicas

### Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|----------|
| Polling `/api/health` a cada 30s pode gerar carga | Usar `document.visibilityState` — so faz polling quando pagina visivel |
| Auto-retry pode mascarar erros reais | So retry para 502/503/504/network; erros 4xx nunca fazem retry |
| Cache stale pode ter setores desatualizados | Sempre tenta revalidar em background; stale e melhor que hardcoded |
| Busca enfileirada pode ser executada em contexto stale | Reenfileirar com parametros originais; timeout de 2min para busca enfileirada |

### Pitfalls Conhecidos
- `document.visibilityState` nao disponivel em SSR — guard com `typeof document !== 'undefined'`
- `setInterval` deve ser limpo no `useEffect` return para evitar memory leak
- Polling do health deve usar `AbortController` com timeout de 5s (mesmo que health route)

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Paralela | CRIT-009 | Observabilidade do erro complementa esta story |
| Paralela | CRIT-010 | Readiness gate reduz frequencia deste problema |
| Nenhuma bloqueante | — | Pode ser implementada independentemente |
