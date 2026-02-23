# GTM-ARCH-001: Migrar Busca para Async Job Pattern (Eliminar 524 Timeout)

## Epic
Root Cause — Arquitetura (EPIC-GTM-ROOT)

## Sprint
Sprint 6: GTM Root Cause — Tier 1

## Prioridade
P0

## Estimativa
32h

## Descricao

Railway impoe hard timeout de ~120s no proxy HTTP. O pipeline de busca do SmartLic esta configurado com timeout chain de 360-480s (FE 480s > Pipeline 360s > Consolidation 300s > PerSource 180s > PerUF 90s). Toda busca que excede 120s recebe HTTP 524 do Railway antes de completar. Na pratica, buscas multi-UF com 5+ estados SEMPRE excedem 120s, tornando o pipeline inteiro dead code em producao.

### Situacao Atual

| Componente | Comportamento | Problema |
|------------|---------------|----------|
| `POST /buscar` | Processa sincrono por ate 360s, retorna JSON | Railway mata em ~120s com 524 |
| `search_pipeline.py` | Timeout chain 360s | Dead code — nunca completa em prod |
| `consolidation.py` | Timeout 300s | Dead code acima de 120s |
| `useSearch.ts` | Espera resposta do POST | Timeout do frontend 480s nunca atingido — Railway mata antes |
| `job_queue.py` (ARQ) | Existe para LLM+Excel apenas | Nao usado para busca principal |
| SSE `/buscar-progress/{id}` | Reporta progresso | Funciona, mas resultado chega por POST (que falha) |

### Evidencia da Investigacao (Squad Root Cause 2026-02-23)

| Finding | Agente | Descricao |
|---------|--------|-----------|
| ARCH-1 | Architect | Railway 524: hard timeout ~120s mata 100% das buscas multi-UF |
| ARCH-10 | Architect | POST+SSE dual-connection incompativel com async — POST bloqueia worker |
| ARCH-2 | Architect | Sync fallback (`PNCPClient` com `requests.Session`) bloqueia event loop |
| ARCH-5 | Data Engineer | Cache per-user nao protege trial users (sem cache, busca full) |

## Criterios de Aceite

### Fluxo Async

- [ ] AC1: `POST /buscar` retorna em <2s com `{ search_id, status: "queued" }` — NAO processa busca inline
- [ ] AC2: Worker ARQ processa busca em background via `search_pipeline.executar_busca_completa()`
- [ ] AC3: SSE `/buscar-progress/{search_id}` entrega resultado parcial (per-UF) e final
- [ ] AC4: Frontend `useSearch.ts` adaptado: POST inicia → SSE recebe resultado → nao depende de POST response body
- [ ] AC5: Timeout do Railway (120s) se torna irrelevante — POST retorna imediato, Worker sem limite HTTP

### Compatibilidade

- [ ] AC6: Fallback inline mantido quando Redis/ARQ indisponivel (comportamento atual preservado)
- [ ] AC7: `search_id` gerado no POST e reutilizado no SSE (ja existe essa logica — manter)
- [ ] AC8: Quota consumida no POST (antes de enfileirar), nao no Worker

### Rollback e Feature Flag

- [ ] AC12: Feature flag `SEARCH_ASYNC_ENABLED` (default `false` em config.py). Quando `false`, comportamento sincrono atual preservado integralmente. Rollout gradual: flag on → 10% → 50% → 100%.
- [ ] AC13: Quando flag `true` e Worker falha em processar dentro de 30s, fallback automatico para inline (sem intervencao manual, sem perda de busca)

### Metas de Tempo (Trial User)

- [ ] AC14: Trial user com cache global quente (via ARCH-002): resultado em <10s
- [ ] AC15: Trial user sem cache, fontes live: resultado parcial (primeira UF) em <15s via SSE, resultado completo em <60s

### Compatibilidade SSE (CRIT-012)

- [ ] AC16: SSE mantem contrato existente de eventos (`progress`, `uf_complete`, `search_complete`, `llm_ready`, `excel_ready`, `error`). Frontend nao precisa saber se resultado veio de inline ou Worker.
- [ ] AC17: Heartbeat SSE (15s, CRIT-012) mantido durante processamento do Worker — Worker emite eventos via tracker existente

### Observabilidade

- [ ] AC18: Metrica `search_job_duration_seconds` (histogram) no Worker
- [ ] AC19: Log estruturado: `{ search_id, queued_at, started_at, completed_at, status }`
- [ ] AC20: SSE event `error` se Worker falhar (com `error_code` do CRIT-009)

## Testes Obrigatorios

```bash
cd backend && pytest -k "test_search_async or test_job_queue" --no-coverage
```

- [ ] T1: POST /buscar retorna 202 com search_id quando ARQ disponivel e flag on
- [ ] T2: Worker processa busca e persiste resultado
- [ ] T3: SSE entrega resultado quando Worker completa
- [ ] T4: Fallback inline quando ARQ indisponivel
- [ ] T5: Fallback inline quando `SEARCH_ASYNC_ENABLED=false`
- [ ] T6: Quota consumida no POST, nao no Worker
- [ ] T7: Worker timeout nao afeta HTTP response
- [ ] T8: Worker falha em 30s → fallback automatico para inline
- [ ] T9: SSE contrato mantido (mesmos eventos) em modo async e inline
- [ ] T10: Heartbeat 15s emitido durante processamento do Worker

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/routes/search.py` | Modificar — POST retorna imediato, enfileira job |
| `backend/job_queue.py` | Modificar — adicionar `search_job` task |
| `backend/search_pipeline.py` | Modificar — expor funcao para Worker consumir |
| `backend/progress.py` | Modificar — Worker emite eventos de resultado |
| `frontend/app/buscar/hooks/useSearch.ts` | Modificar — nao depender de POST response body |
| `frontend/app/api/buscar/route.ts` | Modificar — proxy nao precisa esperar 480s |
| `backend/schemas.py` | Modificar — response schema para 202 Accepted |
| `backend/config.py` | Modificar — adicionar `SEARCH_ASYNC_ENABLED` flag |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Bloqueia | GTM-ARCH-002 | Cache global depende de busca funcional |
| Bloqueia | GTM-INFRA-001 | Sync fallback less critical after async |
| Paralela | GTM-PROXY-001 | Pode ser feita em paralelo |

## Notas Tecnicas

### Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|----------|
| ARQ/Redis indisponivel | Fallback inline preservado (zero regression) |
| Worker crash mid-search | SSE timeout + error event + fallback inline em 30s (AC13) |
| Race condition POST vs SSE | search_id garante vinculo; SSE espera tracker |
| Quota double-count | Consumir quota no POST, Worker nao verifica |
| Deploy quebra SSE existente | Feature flag off por default (AC12); rollout gradual |
| Worker nao emite heartbeat | Worker usa tracker existente; heartbeat mantido (AC17) |
