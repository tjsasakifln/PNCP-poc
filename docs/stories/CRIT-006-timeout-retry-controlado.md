# CRIT-006: Implementar Timeout e Retry Controlado

## Epic
Consistencia Estrutural do Sistema (EPIC-CRIT)

## Sprint
Sprint 3: Contrato (paralelo com CRIT-005)

## Prioridade
P1

## Estimativa
14h

## Descricao

Quando uma busca excede o timeout, o sistema nao tem mecanismo controlado de terminacao. O frontend fica pendurado ate o proxy AbortController disparar (8 min), o backend nao marca a busca como expirada, e nao ha possibilidade de retomada. Alem disso, varios problemas de UX tornam a experiencia de timeout frustrante e desinformativa.

### Problemas documentados:

1. **Tracker TTL (300s) < Pipeline FETCH_TIMEOUT (360s)** — tracker pode ser removido antes da busca emitir terminal event (progress.py:288)
2. **Dual EventSource** — `useSearchProgress` + `useUfProgress` abrem 2 conexoes SSE independentes, dobrando carga e com retry descoordenado
3. **Mensagem SSE disconnect enganosa** — "Finalizando busca..." implica conclusao iminente quando pode faltar minutos
4. **Cancel button aparece so apos 10s** — usuario preso sem escape
5. **Cooldown de retry fixo (30s)** — agressivo demais apos timeout de 6 min
6. **Overtime messages baseadas em tempo, nao progresso** — "Quase pronto" pode aparecer com progresso em 50%
7. **Excel botao funcional para job falhado** — `excel_status="failed"` mas botao clicavel resulta em 404 enganoso
8. **Progresso-para-erro destroi estado** — apos 6+ min de progresso visivel, tudo apagado instantaneamente

### Timeout chain documentada:
```
Gunicorn(600s) > FE Proxy(480s) > Pipeline(360s) > Consolidation(300s) >
Per-Source(180s) > Per-UF(90s) > Per-Modality(60s) > Per-Page(30s)
```

## Especialistas Consultados
- UX Architect (Failure Experience Specialist)
- Systems Architect (Timeout Chain Specialist)

## Evidencia da Investigacao

### Tracker TTL vs FETCH_TIMEOUT:
- `_TRACKER_TTL = 300` em `progress.py:288`
- `SEARCH_FETCH_TIMEOUT = 360` em `search_pipeline.py:785`
- `_cleanup_stale()` chamado em `progress.py:297` (na criacao de novo tracker)

### Dual EventSource:
- `useSearchProgress.ts` (L99-294): EventSource + 1 retry + 2s delay
- `useUfProgress.ts` (L143-192): EventSource independente ao mesmo endpoint
- Nao coordenados — um pode estar conectado enquanto outro falhou

### User journey mais frustrante (timeout de 8 min):
```
User clica "Buscar" -> Progresso comeca (0%)
-> SSE conecta, UFs mostram "fetching" (10%)
-> 3 min: Alguns UFs completam, progresso em 45%
-> 5 min: Overtime message aparece
-> 8 min: AbortController dispara
-> TODO progresso desaparece INSTANTANEAMENTE
-> Card de erro vermelho: "A busca demorou demais..."
-> Botao "Tentar novamente" (30s cooldown)
-> User espera 30s, clica retry
-> Ciclo inteiro reinicia do 0%
```

## Criterios de Aceite

### Backend Timeout Control
- [ ] AC1: Quando Pipeline FETCH_TIMEOUT dispara, marcar busca como `status='timed_out'` em `search_sessions` (CRIT-002)
- [ ] AC2: Persistir `error_message` com detalhes: elapsed time, UFs completados, UFs pendentes
- [ ] AC3: Se UFs ja retornaram dados quando timeout ocorre, salvar resultados parciais em `search_sessions`
- [ ] AC4: Criar endpoint `POST /v1/search/{search_id}/retry` que reprocessa apenas UFs faltantes (nao todo o search)
- [ ] AC5: Retry endpoint deve reaproveitar dados ja coletados do cache/session (nao refetch tudo)

### Tracker TTL Alignment
- [ ] AC6: `_TRACKER_TTL` em `progress.py` DEVE ser >= `SEARCH_FETCH_TIMEOUT` + 60s margem: `300 -> 420`
- [ ] AC7: `_cleanup_stale()` NAO deve remover trackers cuja busca tem `status='processing'` no banco
- [ ] AC8: Adicionar teste que verifica `_TRACKER_TTL >= SEARCH_FETCH_TIMEOUT`

### SSE Consolidation
- [ ] AC9: Consolidar `useSearchProgress` + `useUfProgress` em hook unico `useSearchSSE`
- [ ] AC10: Unica instancia de EventSource gerencia todos os event types
- [ ] AC11: Dispatch de eventos para consumers separados via callback pattern
- [ ] AC12: Retry coordenado: se conexao cai, um unico retry para a conexao consolidada

### SSE Disconnect Message
- [ ] AC13: Mudar "Finalizando busca..." para "O progresso em tempo real foi interrompido. A busca continua no servidor e os resultados serao exibidos quando prontos."
- [ ] AC14: Mostrar estimativa baseada em UFs completados vs total (se disponivel)

### Cancel Button
- [ ] AC15: Cancel button DEVE aparecer desde o inicio do loading (nao apos 10s)
- [ ] AC16: Cancel deve enviar signal ao backend (`POST /v1/search/{search_id}/cancel` ou via header)
- [ ] AC17: Backend ao receber cancel: marcar busca como `status='cancelled'`, parar pipeline

### Retry Cooldown Scaling
- [ ] AC18: Cooldown escalado por tipo de erro:
  - Network error: 10s
  - Timeout: 15s
  - Rate limit (429): 30s
  - Server error (500): 20s
- [ ] AC19: Retry button deve mostrar countdown (ja existe, manter)

### Overtime Messages
- [ ] AC20: Vincular overtime messages ao progresso REAL (nao so tempo):
  - Progresso > 80%: "Quase pronto, finalizando..."
  - Progresso 50-80%: "Processando resultados..."
  - Progresso < 50% + overtime: "Esta busca esta demorando mais que o normal"
- [ ] AC21: Se progress stale (nao muda por 30s): "Aguardando resposta das fontes..."

### Partial Results on Timeout
- [ ] AC22: Quando timeout ocorre mas `succeeded_ufs` nao vazio, mostrar resultados parciais com `PartialTimeoutBanner`
- [ ] AC23: `PartialTimeoutBanner` deve mostrar: UFs completos, UFs faltantes, botao "Buscar estados restantes"
- [ ] AC24: Botao "Buscar estados restantes" deve usar endpoint de retry (AC4) com apenas UFs faltantes

### Error Detail Section
- [ ] AC25: Adicionar secao collapsible "Detalhes tecnicos" em todo card de erro com: search_id, timestamp, erro tecnico original
- [ ] AC26: Incluir botao "Copiar detalhes" para facilitar report de problemas

## Testes Obrigatorios

- [ ] Timeout marca busca como timed_out (nao failed ou empty)
- [ ] Partial results mostrados em vez de erro quando UFs parciais disponiveis
- [ ] Tracker TTL >= FETCH_TIMEOUT (assertion no test_timeout_chain.py)
- [ ] Cancel button aparece imediatamente no loading
- [ ] Retry cooldown varia por tipo de erro
- [ ] Dual EventSource consolidado em conexao unica
- [ ] Overtime messages baseadas em progresso real
- [ ] Retry endpoint reprocessa apenas UFs faltantes
- [ ] SSE disconnect message nao diz "Finalizando"
- [ ] Erro tecnico detail mostra search_id

## Definicao de Pronto

1. Timeout resulta em estado `timed_out` persistido (nao desaparecimento)
2. Resultados parciais SEMPRE preservados em timeout (nao descartados)
3. Usuario pode retomar busca com apenas UFs faltantes
4. Cancel button disponivel desde o inicio
5. Uma unica conexao SSE (nao duas)
6. Mensagens de overtime refletem progresso real
7. Zero regressao nos testes existentes

## Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|-----------|
| Retry de UFs faltantes pode dar resultados inconsistentes (mix de timestamps) | Mostrar banner "Resultados de momentos diferentes" |
| Cancel no backend pode nao parar threads ja lancadas | Usar asyncio.Event para cooperative cancellation |
| Consolidar SSE pode quebrar frontend | Feature flag USE_CONSOLIDATED_SSE |

## Arquivos Envolvidos

### Backend (modificar):
- `backend/progress.py` L288 — _TRACKER_TTL adjustment
- `backend/search_pipeline.py` L785, L1068, L1317 — timeout handlers
- `backend/routes/search.py` — cancel endpoint, retry endpoint

### Frontend (modificar):
- `frontend/hooks/useSearchProgress.ts` — consolidar
- `frontend/app/buscar/hooks/useUfProgress.ts` — merge
- `frontend/app/buscar/hooks/useSearch.ts` — retry logic, cancel
- `frontend/components/EnhancedLoadingProgress.tsx` — cancel timing, overtime messages
- `frontend/app/buscar/components/SearchResults.tsx` — cooldown scaling, error detail

### Frontend (criar):
- `frontend/hooks/useSearchSSE.ts` — consolidated SSE hook
- `frontend/app/buscar/components/PartialTimeoutBanner.tsx` — timeout with partial data
- `frontend/app/buscar/components/ErrorDetail.tsx` — collapsible technical detail

## Dependencias

- **Bloqueada por:** CRIT-003 (state machine necessario para status timed_out)
- **Paralela com:** CRIT-005
- **Bloqueia:** CRIT-007 (testes E2E precisam do timeout controlado)
