# PM BRIEFING: Sistema Inconsistente Entre Camadas

**Data:** 2026-02-20
**Squad:** Full investigation (Architect x2, Data Engineer, Backend Engineer, UX Architect, QA Architect, Observability Architect)
**Objetivo:** Municiar o PM com evidencias concretas para criacao de stories que ressuscitem a utilidade do sistema
**Status:** INVESTIGACAO CONCLUIDA — Zero implementacao, 100% evidencia

---

## DIAGNOSTICO EXECUTIVO

O sistema possui camadas sofisticadas de resiliencia (retry, circuit breaker, cache SWR, fila distribuida), mas **falha em sua razao de existir**: encontrar, analisar e apresentar oportunidades de licitacao. A raiz nao e instabilidade — e **inconsistencia estrutural entre banco, backend e orquestracao assincrona**.

### Os 7 Problemas Fundamentais (em ordem de severidade)

| # | Problema | Severidade | Impacto Direto |
|---|---------|-----------|----------------|
| 1 | Schema drift — coluna `sources_json` nao existe em producao | **CRITICO** | Cache quebra silenciosamente, busca falha |
| 2 | Busca so e registrada apos 100% do processamento (Stage 7 de 7) | **CRITICO** | Buscas "desaparecem" sem rastro |
| 3 | Quota consumida no Stage 1, sessao salva no Stage 7 | **CRITICO** | Usuario paga por buscas que nunca ve |
| 4 | Nenhum estado de busca persiste — tudo in-memory | **CRITICO** | Restart do servidor = perda total |
| 5 | HTTP 200 mascarando falhas reais (14 locais) | **ALTO** | Monitoramento cego, usuario desinformado |
| 6 | Tres IDs de correlacao independentes, nunca conectados | **ALTO** | Impossivel reconstruir jornada de busca |
| 7 | Zero infraestrutura de testes de integracao | **ALTO** | Falhas cascata sao invisiveis |

---

## STORY 1: Alinhar Schema e Evitar Drift

### Evidencia

**Achado critico:** Duas migrations compartilham o prefixo `027_`:
- `027_fix_plan_type_default_and_rls.sql` (2026-02-15, commit `1d14de6`)
- `027_search_cache_add_sources_and_fetched_at.sql` (2026-02-17, commit `c1b80bc`)

A segunda **nunca foi aplicada em producao** porque o Supabase registrou a primeira como migration `027` e ignorou/pulou a segunda. Resultado: colunas `sources_json` e `fetched_at` nao existem na tabela `search_results_cache`.

**Impacto em cascata:**
- `search_cache.py` referencia `sources_json` em 7 locais (lines 182, 213, 229, 716, 1425, 1460)
- `search_cache.py` referencia `fetched_at` em 4 locais (lines 183, 213, 225, 1232)
- Erro em producao: `"column search_results_cache.sources_json does not exist"`
- `fetched_at` mascarado por fallback silencioso: `row.get("fetched_at") or row.get("created_at")`

**Tabela de drift:**

| Coluna | Migration | Existe em Prod? | Referenciada no Codigo? |
|--------|-----------|-----------------|------------------------|
| `sources_json` | 027_search_cache (NAO APLICADA) | **NAO** | SIM (7 locais) |
| `fetched_at` | 027_search_cache (NAO APLICADA) | **NAO** | SIM (4 locais) |
| `last_success_at` | 031_cache_health | Provavelmente SIM | SIM |
| `priority` | 032_cache_priority | Provavelmente SIM | SIM |

**Agravante:** Nenhum modelo Pydantic define o schema da tabela `search_results_cache`. O schema e implicitamente definido em 5 arquivos de migration + multiplas funcoes Python.

### Acceptance Criteria Sugeridos

- AC1: Criar migration idempotente `033_fix_missing_cache_columns.sql` com `ADD COLUMN IF NOT EXISTS`
- AC2: Renomear ou remover a migration duplicada `027_search_cache_add_sources_and_fetched_at.sql`
- AC3: Criar modelo Pydantic `SearchResultsCacheRow` como fonte unica de verdade
- AC4: Adicionar health check de startup que valida colunas esperadas vs existentes (`information_schema.columns`)
- AC5: Adicionar validacao em CI que detecta prefixos de migration duplicados
- AC6: Atualizar SCHEMA.md para incluir todas as colunas ate migration 032
- AC7: Backfill `sources_json` e `fetched_at` para registros existentes

### Arquivos Envolvidos

- `supabase/migrations/027_search_cache_add_sources_and_fetched_at.sql`
- `supabase/migrations/027_fix_plan_type_default_and_rls.sql`
- `backend/search_cache.py` (lines 182, 213, 229, 716, 1232, 1425, 1460)
- `backend/routes/health.py` (line 56)
- Nova migration: `033_fix_missing_cache_columns.sql`
- Novo modelo: schema validation em `backend/models/cache.py` ou similar

---

## STORY 2: Persistir Busca ANTES do Processamento

### Evidencia

**Achado critico:** A tabela `search_sessions` so recebe INSERT no Stage 7 (`stage_persist`) — o ULTIMO estagio do pipeline de 7 estagios.

**Fluxo atual (search_pipeline.py):**
```
Stage 1: ValidateRequest -> check_and_increment_quota_atomic() [COMMITADO NO DB - IRREVERSIVEL]
Stage 2: PrepareSearch -> parse terms, load sector
Stage 3: ExecuteSearch -> PNCP/PCP API calls + cache write
Stage 4: FilterResults -> keyword/LLM filtering
Stage 5: EnrichResults -> viability assessment
Stage 6: GenerateOutput -> LLM summary + Excel
Stage 7: Persist -> save_search_session() [UNICO PONTO DE REGISTRO]
```

**13 cenarios documentados onde buscas "desaparecem":**

| # | Cenario | Quota Consumida? | Cache Escrito? | Sessao Salva? |
|---|---------|-----------------|----------------|---------------|
| F1 | Server timeout (gunicorn mata worker) | SIM | TALVEZ | NAO |
| F2 | PNCP API falha completamente | SIM | NAO | NAO |
| F3 | AllSourcesFailedError | SIM | NAO | NAO |
| F4 | Filter logic crash (Stage 4) | SIM | SIM (raw) | NAO |
| F5 | LLM + fallback falham | SIM | SIM | NAO |
| F6 | Excel generation crash | SIM | SIM | NAO |
| F7 | Supabase INSERT falha no Stage 7 | SIM | SIM | NAO |
| F8 | Cliente desconecta | SIM | TALVEZ | NAO |
| F12 | Pipeline timeout (asyncio.TimeoutError) | SIM | TALVEZ | NAO |
| F13 | OOM durante processamento grande | SIM | TALVEZ | NAO |

**Agravante:** A tabela `search_sessions` NAO tem coluna `status`. So aceita buscas "completas". Impossivel registrar "in_progress", "failed" ou "timed_out".

**Schema atual de `search_sessions` (migration 001):**
```sql
id UUID PK, user_id UUID FK, sectors text[], ufs text[], data_inicial date,
data_final date, custom_keywords text[], total_raw int, total_filtered int,
valor_total numeric, resumo_executivo text, destaques text[],
excel_storage_path text, created_at timestamptz
-- NAO TEM: status, error, error_message, started_at, duration_ms
```

### Acceptance Criteria Sugeridos

- AC1: Adicionar colunas `status` (enum: created/processing/completed/failed/timed_out), `error_message`, `started_at`, `duration_ms` na tabela `search_sessions`
- AC2: Inserir registro com `status='created'` IMEDIATAMENTE antes da quota ser consumida (Stage 1)
- AC3: Atualizar para `status='processing'` quando pipeline inicia
- AC4: Atualizar para `status='completed'` no Stage 7 com dados finais
- AC5: Atualizar para `status='failed'` em qualquer exception handler com `error_message` estruturado
- AC6: Atualizar para `status='timed_out'` em timeout com possibilidade de retomada
- AC7: Se `check_and_increment_quota_atomic()` commitou mas search falhou, implementar compensacao (devolver quota ou registrar busca como "failed" consumindo quota)
- AC8: `created_at` deve representar INICIO (nao conclusao) da busca
- AC9: Historico de buscas do usuario deve mostrar buscas failed/timed_out com mensagem clara

### Arquivos Envolvidos

- `supabase/migrations/001_profiles_and_sessions.sql` (schema referencia)
- Nova migration: `034_add_search_session_status.sql`
- `backend/search_pipeline.py` (lines 556-639 Stage 1, lines 1954-2055 Stage 7)
- `backend/quota.py` (lines 861-927 `save_search_session()`)
- `backend/routes/search.py` (lines 328-544 wrapper)

---

## STORY 3: Implementar State Machine de Busca

### Evidencia

**Achado critico:** Nenhum estado de busca persiste em banco. Tudo e in-memory.

**Armazenamento atual de estado:**

| Storage | O que rastreia | TTL | Sobrevive restart? |
|---------|---------------|-----|-------------------|
| `_active_trackers` dict (progress.py:287) | ProgressTracker registry | 5 min | **NAO** |
| Redis `bidiq:progress:{search_id}` | Metadata do tracker | 5 min | Sim (se Redis) |
| Redis pub/sub channel | SSE event streaming | Efemero | **NAO** |
| `_background_results` dict (search.py:61) | A-04 background results | 10 min | **NAO** |
| `_active_background_tasks` dict (search.py:63) | asyncio.Task refs | Ate completar | **NAO** |

**SSE events — 16 tipos mapeados, nenhum persistido:**

| Evento Terminal | Significado |
|----------------|-------------|
| `complete` | Sucesso total |
| `degraded` | Dados servidos mas nao frescos |
| `error` | Falha real |
| `refresh_available` | Background fetch concluiu |

**Race condition SSE vs POST:** O POST retorna quando `pipeline.run()` completa. O wrapper emite o evento SSE terminal logo apos. Mas o frontend pode receber o terminal SSE ANTES ou DEPOIS do POST response. Sao racing.

**Tracker TTL vs Fetch Timeout:** Tracker TTL = 5 min (`_TRACKER_TTL=300`), Pipeline FETCH_TIMEOUT = 6 min (360s). Se busca demora entre 5-6 min, tracker pode ser removido antes da busca completar.

### Acceptance Criteria Sugeridos

- AC1: Criar tabela `search_executions` com state machine explicito: `created -> processing -> completed | failed | timed_out`
- AC2: Cada transicao de estado persiste em banco com timestamp
- AC3: Eventos SSE sao derivados do estado persistido (nao o contrario)
- AC4: Se SSE cai e reconecta, novo EventSource recebe estado atual do banco (nao depende de Queue in-memory)
- AC5: Se servidor reinicia, buscas in-flight sao marcadas como `timed_out` (cron ou startup check)
- AC6: Frontend poll endpoint para estado quando SSE esta indisponivel
- AC7: `search_id` e a chave primaria do estado (correlacao unica)
- AC8: Eliminar race condition: POST response deve carregar `final_state` do banco
- AC9: Tracker TTL >= Pipeline timeout (300s -> 420s ou mais)

### Arquivos Envolvidos

- Nova migration: `035_search_executions.sql`
- `backend/progress.py` (refatorar para ser derivado de estado persistido)
- `backend/routes/search.py` (lines 100-194 SSE, lines 328-544 POST)
- `backend/search_pipeline.py` (emitir transicoes de estado)
- `frontend/hooks/useSearchProgress.ts` (polling fallback)
- `frontend/app/buscar/hooks/useSearch.ts` (consumir estado persistido)

---

## STORY 4: Propagar Correlation ID Ponta a Ponta

### Evidencia

**Achado critico:** Tres mecanismos de identidade independentes, NUNCA conectados:

| ID | Escopo | Gerado | Propagado ate |
|----|--------|--------|---------------|
| `X-Correlation-ID` | Sessao browser (per-tab) | Frontend (`correlationId.ts`) | **DESCARTADO no proxy Next.js** |
| `X-Request-ID` | Request HTTP (per-call) | Next.js proxy OU backend middleware | PNCP API, OpenAI API, audit logs |
| `search_id` | Busca (per-search) | Frontend (`crypto.randomUUID()`) | SSE channel, ARQ jobs, Redis keys |

**10 gaps de correlacao identificados:**

| Gap | Descricao | Impacto |
|-----|-----------|---------|
| GAP 1 | Frontend `X-Correlation-ID` descartado no proxy (route.ts gera novo `X-Request-ID`) | Nao correlaciona browser -> backend |
| GAP 2 | SSE proxy nao forwarda headers de correlacao | SSE requests sem correlacao |
| GAP 3 | `search_id` nao esta em ContextVar/log context | Nao da para grep logs por search_id |
| GAP 4 | `filter.py` gera proprio `trace_id` independente (8 chars) | Filter decisions orfas |
| GAP 5 | `consolidation.py` nao tem `search_id` | Multi-source fetch sem correlacao |
| GAP 6 | ARQ: `_trace_id`/`_span_id` injetados mas **NUNCA consumidos** (silently lost) | Jobs sem tracing |
| GAP 7 | Worker process nao tem `request_id_var` ContextVar | Job logs mostram `request_id="-"` |
| GAP 8 | SSE events incluem `trace_id` mas nao `request_id`/`search_id` | Correlacao SSE->HTTP requer OTel |
| GAP 9 | Download proxy nao forwarda correlacao | Download orfao do search |
| GAP 10 | Nenhum ponto no codigo conhece os 3 IDs simultaneamente | Impossivel join |

**Pode reconstruir jornada de busca dos logs?** **NAO.**

| Cenario | Possivel? |
|---------|-----------|
| Log lines de um HTTP request | SIM (grep request_id) |
| SSE events de uma busca | SIM (grep search_id em Redis) |
| Correlacionar HTTP -> SSE | PARCIAL (timing) |
| Busca -> PNCP API calls | SIM (se OTel ativo) |
| Busca -> ARQ background job | **NAO** |
| Browser -> Backend | **NAO** |
| Filter decisions -> busca | **NAO** |

### Acceptance Criteria Sugeridos

- AC1: Proxy Next.js deve forwardar `X-Correlation-ID` do browser como `X-Correlation-ID` (alem do `X-Request-ID`)
- AC2: Adicionar `search_id` a um ContextVar no backend (`search_id_var`)
- AC3: Incluir `search_id` no log format de producao (junto com `request_id`, `trace_id`)
- AC4: ARQ jobs devem aceitar e restaurar `_trace_id`/`_span_id` de kwargs
- AC5: Worker process deve setar `request_id_var` com `search_id` no inicio do job
- AC6: `filter.py` deve usar `search_id` do pipeline em vez de gerar trace proprio
- AC7: SSE events devem incluir `search_id` em `ProgressEvent.to_dict()`
- AC8: Download proxy deve forwardar `X-Request-ID`/`X-Correlation-ID`
- AC9: Criar endpoint `GET /v1/search-trace/{search_id}` que retorna timeline completa
- AC10: Log line deve ter formato: `{timestamp} | {request_id} | {search_id} | {trace_id} | {module} | {message}`

### Arquivos Envolvidos

- `frontend/app/api/buscar/route.ts` (line 69-73 — forwardar header)
- `frontend/app/api/buscar-progress/route.ts` (lines 27-31)
- `frontend/app/api/download/route.ts` (lines 26-29)
- `backend/middleware.py` (lines 39-89 — ler `X-Correlation-ID`, adicionar `search_id_var`)
- `backend/config.py` (lines 109-145 — log format)
- `backend/progress.py` (lines 33-45 — `ProgressEvent.to_dict()`)
- `backend/filter.py` (lines 2521-2522 — substituir trace interno)
- `backend/job_queue.py` (lines 136-145, 231, 273 — fix trace propagation)
- `backend/consolidation.py` (adicionar search_id)

---

## STORY 5: Garantir Consistencia de Status e Erro

### Evidencia

**Achado critico:** 14 locais onde excecoes sao capturadas e HTTP 200 retornado com dados degradados. Apenas 3 locais produzem HTTP error codes genuinos.

**O padrao "Success Theater":**
```
Pipeline Stage 3 -> AllSourcesFailedError
  -> tenta cache cascade
  -> cache encontrado: HTTP 200, response_state="cached"
  -> sem cache: HTTP 200, response_state="empty_failure", licitacoes=[]
```

**Mapa de erro completo — o que o usuario VE vs o que ACONTECEU:**

| Cenario | HTTP | response_state | O que usuario ve | O que aconteceu |
|---------|------|---------------|------------------|-----------------|
| Sucesso total | 200 | "live" | Resultados normais | Tudo OK |
| PNCP down + cache | 200 | "cached" | Resultados + CacheBanner | Dados de horas atras |
| Todas fontes down + cache | 200 | "cached" | Igual acima | NENHUMA fonte funciona |
| Todas fontes down + SEM cache | 200 | "empty_failure" | **Lista vazia** (sem erro!) | Sistema completamente quebrado |
| LLM falha | 200 | - | Resumo fallback **identico visualmente** | IA nao funcionou |
| Excel falha (ARQ) | 200 | - | Botao download FUNCIONAL mas clique da 404 | Excel nao gerou |
| Stripe down | 200 | - | status="pending" para assinante ativo | Billing invisivel |
| Trial status falha | 200 | - | plan="free_trial", is_expired=true | Pago parece expirado |

**Achados de UX criticos:**

| Issue | Severidade | Descricao |
|-------|-----------|-----------|
| `degradation_guidance` NAO exibido | P0 | Quando `response_state="empty_failure"`, usuario ve lista vazia, sem saber que fontes falharam |
| Excel botao funcional para job falhado | P0 | `excel_status="failed"` mas botao download renderiza normalmente. Click resulta em 404 enganoso |
| LLM fallback invisivel | P1 | Nenhuma indicacao visual que resumo e automatico vs IA |
| 502 sempre culpa PNCP | P1 | `error-messages.ts` mapeia 502 para "PNCP indisponivel" mas pode ser qualquer falha |
| Progresso-para-erro destroi estado | P0 | Apos 6+ min de progresso visivel, erro apaga tudo instantaneamente |

### Acceptance Criteria Sugeridos

- AC1: Adicionar header `X-Response-State` que espelha `response_state` em toda resposta `/buscar`
- AC2: Criar Prometheus counter `search_response_state_total{state="live|cached|degraded|empty_failure"}`
- AC3: Exibir `degradation_guidance` no frontend quando `response_state="empty_failure"` (diferenciar "sem resultados" de "fontes indisponiveis")
- AC4: Desabilitar botao download quando `excel_status="failed"` — mostrar "Excel indisponivel"
- AC5: Adicionar badge de proveniencia no resumo: "Resumo por IA" vs "Resumo automatico"
- AC6: Corrigir mapeamento 502 para mensagem neutra (nao culpar PNCP especificamente)
- AC7: Na transicao progresso->erro por timeout, preservar progresso por 5s com overlay "Busca expirou" antes de limpar
- AC8: Se UFs ja retornaram dados quando timeout ocorre, mostrar resultados parciais em vez de erro
- AC9: Endpoint `/buscar-progress` deve retornar estado consistente quando search_id nao existe (nao 200 com "Search not found" dentro de SSE)

### Arquivos Envolvidos

- `backend/routes/search.py` (lines 478-544 — adicionar header)
- `backend/search_pipeline.py` (lines 983-1175 — 5 catch blocks)
- `frontend/app/buscar/components/SearchResults.tsx` (lines 697-738 — Excel button)
- `frontend/lib/error-messages.ts` (line 502 mapping)
- `frontend/app/buscar/hooks/useSearch.ts` (lines 237-239, 424-425 — preservar estado)
- `frontend/components/EnhancedLoadingProgress.tsx` (timeout overlay)
- `backend/routes/analytics.py` (lines 329-338 — trial-value swallowed error)
- `backend/routes/user.py` (lines 169-178 — trial-status swallowed error)
- `backend/routes/billing.py` (lines 209-210 — subscription status swallowed)

---

## STORY 6: Implementar Timeout e Retry Controlado

### Evidencia

**Mapa completo de timeouts (19 niveis):**

```
Gunicorn(600s) > FE Proxy(480s) > Pipeline(360s) > Consolidation(300s) >
Per-Source(180s) > Per-UF(90s) > Per-Modality(60s) > Per-Page(30s)
```

**O que acontece em CADA nivel de timeout:**

| Nivel | Timeout | O que acontece | O que usuario ve |
|-------|---------|---------------|------------------|
| Gunicorn | 600s | Worker morto por SIGKILL | SSE cai, POST falha (502/503) |
| FE Proxy | 480s | AbortController dispara | "A busca demorou demais" + retry 30s |
| Pipeline | 360s | asyncio.TimeoutError | Cache ou 502 |
| Per-UF | 90s | UF skipada | UF em vermelho no grid, resultados parciais |
| ARQ Job | 60s | 3 retries, fallback | LLM: fallback silencioso. Excel: botao bugado |
| SSE Tracker | 300s (TTL) | Tracker removido do registry | **Potencial: tracker removido antes da busca terminar** |

**Bug critico de timing:** Tracker TTL (300s) < Pipeline FETCH_TIMEOUT (360s). Se busca demora 5-6 min, tracker e limpo por `_cleanup_stale()` antes da busca emitir evento terminal.

**Mensagem de SSE quando desconecta:** "Finalizando busca..." — **enganosa**, implica conclusao iminente quando pode faltar minutos.

**Dual EventSource:** Frontend abre DUAS conexoes SSE independentes (`useSearchProgress` + `useUfProgress`). Dobro de carga, logica de retry descoordenada.

### Acceptance Criteria Sugeridos

- AC1: Backend deve marcar busca como `timed_out` quando Pipeline timeout dispara (nao "cached" ou "empty")
- AC2: Persister erro e timestamp em `search_sessions.error_message` e `search_sessions.status='timed_out'`
- AC3: Permitir retomada/reprocessamento de busca timed_out (endpoint `POST /v1/search/{search_id}/retry`)
- AC4: Tracker TTL >= Pipeline FETCH_TIMEOUT + margem (420s+)
- AC5: Consolidar dual EventSource em conexao unica com dispatch de eventos
- AC6: Adicionar polling fallback (`GET /v1/search/{search_id}/status`) quando SSE indisponivel
- AC7: Implementar heartbeat detection no frontend (se nenhum SSE event por 60s -> verificar estado via polling)
- AC8: Corrigir mensagem de SSE desconectado: "O progresso em tempo real foi interrompido. A busca continua no servidor."
- AC9: Cancel button no loading deve aparecer desde o inicio (nao apos 10s)
- AC10: Implementar cooldown escalado: 10s para network errors, 15s para timeouts, 30s para rate limits

### Arquivos Envolvidos

- `backend/progress.py` (line 288 — `_TRACKER_TTL`)
- `backend/search_pipeline.py` (lines 785, 1068, 1317 — timeout handlers)
- `frontend/hooks/useSearchProgress.ts` (consolidar com useUfProgress)
- `frontend/app/buscar/hooks/useUfProgress.ts` (merge into single SSE)
- `frontend/components/EnhancedLoadingProgress.tsx` (cancel button timing, overtime messages)
- `frontend/app/buscar/components/SearchResults.tsx` (retry cooldown scaling)
- `frontend/app/buscar/hooks/useSearch.ts` (polling fallback)

---

## STORY 7: Testes de Falha End-to-End

### Evidencia

**Situacao atual:**
- `backend/tests/integration/` — **NAO EXISTE**
- CI/CD `tests.yml` tem job `integration-tests` que e um **STUB** (`echo "will be implemented in issue #27"`)
- `useSearch.test.ts` esta em **quarentena** (`__tests__/quarantine/`)
- Todos os testes de falha existentes sao unit-level com mocks

**7 cenarios P0 sem teste (buscas desaparecem):**

| # | Cenario | Backend? | Frontend? | Integracao? |
|---|---------|----------|-----------|-------------|
| 1 | Pipeline failure cascade completo | NAO | NAO | NAO |
| 2 | Queue dispatch falha -> inline fallback | NAO | NAO | NAO |
| 3 | Supabase totalmente indisponivel | NAO | NAO | NAO |
| 4 | Todas fontes + todos caches falham simultaneamente | NAO | NAO | NAO |
| 5 | Cliente nunca conecta SSE, POST retorna completo | NAO | NAO | NAO |
| 6 | Frontend 504 gateway timeout | NAO | NAO | NAO |
| 7 | Queue dispatch -> worker fail -> inline fallback verificado | NAO | NAO | NAO |

**10 cenarios P1 sem teste:**

| # | Cenario |
|---|---------|
| 1 | Cache schema mismatch (coluna faltando) |
| 2 | search_results_cache tabela nao existe |
| 3 | Profiles table read falha durante quota check |
| 4 | Worker process crash mid-job |
| 5 | PNCP tamanhoPagina muda de novo (canary) |
| 6 | ProgressTracker queue perdido mid-search |
| 7 | SSE connection drops, search completa server-side |
| 8 | Partial results + timeout -> usuario recebe parcial |
| 9 | Server restart mid-search |
| 10 | Auth token expira mid-search |

**Testes que EXISTEM (cobertura parcial):**
- `test_search_cache.py` (19 tests) — cache failures individuais
- `test_pncp_client.py` (42 tests) — retry, rate limit, circuit breaker
- `test_job_queue.py` (42 tests) — pool mgmt, job failures individuais
- `test_pipeline_resilience.py` (12 tests) — source failures com cache
- `__tests__/api/buscar.test.ts` (12 tests) — proxy error codes

### Acceptance Criteria Sugeridos

- AC1: Criar `backend/tests/integration/` com infraestrutura pytest
- AC2: Implementar 7 testes P0 de failure cascade (pipeline real, nao mocked stages)
- AC3: Tirar `useSearch.test.ts` da quarentena e corrigir
- AC4: Adicionar testes frontend para 504, SSE failure recovery, retry flow
- AC5: Adicionar Playwright E2E test: "busca com todas fontes down"
- AC6: Adicionar canary test: schema cache table structure validation
- AC7: Adicionar canary test: PNCP tamanhoPagina limit verification
- AC8: CI: habilitar job `integration-tests` (remover stub)
- AC9: Cada cenario P0 deve ter assertion de: (a) busca registrada, (b) estado final consistente, (c) usuario recebe feedback deterministico
- AC10: Worker crash recovery test: job disparado -> worker simulado crash -> verificar que frontend nao fica "processing" indefinidamente

### Arquivos Envolvidos

- Novo diretorio: `backend/tests/integration/`
- Novo arquivo: `backend/tests/integration/test_failure_cascades.py`
- Novo arquivo: `backend/tests/integration/test_schema_canary.py`
- `.github/workflows/tests.yml` (lines 190-219 — habilitar integration job)
- `frontend/__tests__/quarantine/hooks/useSearch.test.ts` -> mover para `__tests__/hooks/`
- Novo arquivo: `frontend/__tests__/hooks/useSearch-failures.test.ts`
- Novo E2E: `frontend/e2e-tests/failure-scenarios.spec.ts`

---

## DEPENDENCIAS ENTRE STORIES

```
STORY 1 (Schema Drift) ──────> pode ser feita independente (P0, dia 1)
                                   |
STORY 2 (Persistir Busca) ────> depende de STORY 1 (tabela precisa estar alinhada)
                                   |
STORY 3 (State Machine) ─────> depende de STORY 2 (precisa da tabela com status)
                                   |
STORY 4 (Correlation ID) ────> pode ser feita em paralelo com STORY 2/3
                                   |
STORY 5 (Status/Erro) ───────> depende de STORY 2 (precisa saber estado da busca)
                                   |
STORY 6 (Timeout/Retry) ─────> depende de STORY 3 (precisa do state machine)
                                   |
STORY 7 (Testes E2E) ────────> depende de STORIES 2,3,5 (precisa do contrato correto para testar)
```

### Ordem de execucao recomendada:

```
Sprint 1 (Fundacao):
  [PARALELO] STORY 1 (Schema Drift) + STORY 4 (Correlation ID)

Sprint 2 (Consistencia):
  [SEQUENCIAL] STORY 2 (Persistir Busca) -> STORY 3 (State Machine)

Sprint 3 (Contrato):
  [PARALELO] STORY 5 (Status/Erro) + STORY 6 (Timeout/Retry)

Sprint 4 (Validacao):
  STORY 7 (Testes E2E) — valida tudo acima
```

---

## METRICAS DE SUCESSO

Apos implementacao das 7 stories, o sistema deve:

1. **Zero buscas fantasma:** Toda busca iniciada DEVE ter registro em banco com estado final (completed/failed/timed_out)
2. **Quota justa:** Se busca falha, quota e compensada ou busca registrada como failed
3. **Observabilidade:** Dado um `search_id`, reconstruir a jornada completa (frontend -> backend -> PNCP -> filter -> LLM -> persist) em < 5 min
4. **Erro honesto:** Se fontes estao indisponiveis, usuario ve "Fontes indisponiveis" e NAO lista vazia
5. **Cache transparente:** Se dados sao de cache, usuario ve badge com idade e botao de refresh
6. **Timeout digno:** Se busca expira, resultados parciais sao preservados (nao descartados)
7. **Testes de falha:** 100% dos cenarios P0 com testes automatizados, zero stub em CI

---

## ANEXOS

### Arquivos de evidencia completos

Os relatorios detalhados de cada agente investigador estao em:
- Schema Drift: Agent a25bcb2 output
- State Machine: Agent aa8f4ca output
- Atomicity: Agent a249bdb output
- Correlation: Agent ab98fb3 output
- Superficial Success: Agent a649404 output
- Timeout/UX: Agent ae0d2ae output
- Test Gaps: Agent a444b15 output

### Contagem de evidencia

| Investigacao | Arquivos analisados | Gaps encontrados | LOC referenciados |
|-------------|-------------------|-----------------|-------------------|
| Schema Drift | 12 | 6 | ~50 |
| State Machine | 8 | 8 | ~100 |
| Atomicity | 6 | 6 + 13 failure paths | ~80 |
| Correlation | 15 | 10 | ~120 |
| Superficial Success | 14 | 14 (200-masking) + 5 (UX) | ~150 |
| Timeout/UX | 22 | 2 P0 + 5 P1 + 5 P2 | ~200 |
| Test Gaps | 20+ | 7 P0 + 10 P1 + 8 P2 | ~100 |
| **TOTAL** | **~100** | **~80 gaps** | **~800** |
