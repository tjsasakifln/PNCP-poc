# CRIT-002: Persistir Busca Sincronicamente Antes de Iniciar Processamento

## Epic

**EPIC-CRIT** — Consistencia Estrutural do Sistema

## Sprint

Sprint 2: Consistencia

## Prioridade

**P0** — Integridade de dados. Buscas que consomem quota e desaparecem sem rastro representam cobranca indevida e perda de confianca do usuario.

## Estimativa

16h (8h backend schema+pipeline, 4h error handling+observability, 2h frontend, 2h testes)

## Descricao

### Problema

A tabela `search_sessions` **so recebe INSERT no Stage 7** — o ULTIMO estagio de um pipeline de 7 estagios. A quota, por sua vez, e consumida no **Stage 1** — o PRIMEIRO estagio — e de forma **irreversivel** (funcao Postgres atomica `check_and_increment_quota_atomic`).

Isso cria **13 caminhos de falha documentados** onde a busca "desaparece" sem rastro: o usuario paga (quota decrementada), mas nao tem nenhum registro no historico. O sistema atual nao possui colunas `status`, `error_message`, `started_at` ou `duration_ms` na tabela `search_sessions` — suporta apenas buscas "completadas" com sucesso.

### Filosofia

> **"Toda busca que consome quota DEVE existir no historico do usuario — seja como sucesso, falha, ou timeout."**

O registro da sessao deve ser a PRIMEIRA operacao apos autenticacao, nao a ultima. Mesmo que o processamento falhe, o usuario tem visibilidade do que aconteceu e por que.

### Pipeline Atual (7 Estagios)

```
Stage 1: ValidateRequest  (search_pipeline.py:556)  -> check_and_increment_quota_atomic() [COMMITTED - IRREVERSIBLE]
Stage 2: PrepareSearch     (search_pipeline.py:644)  -> parse terms, resolve sector
Stage 3: ExecuteSearch     (search_pipeline.py:734)  -> PNCP/PCP calls + cache write
Stage 4: FilterResults     (search_pipeline.py:1373) -> keyword/LLM filtering
Stage 5: EnrichResults     (search_pipeline.py:1499) -> viability assessment
Stage 6: GenerateOutput    (search_pipeline.py:1581) -> LLM summary + Excel
Stage 7: Persist           (search_pipeline.py:1954) -> save_search_session() [UNICO INSERT]
```

### Impacto

- `save_search_session()` (quota.py:861-927) faz o INSERT com 1 retry, retorna `None` silenciosamente em falha persistente
- `check_and_increment_quota_atomic` (quota.py:437) e uma funcao Postgres atomica — committed imediatamente, sem rollback
- Frontend (`app/historico/page.tsx`) nao tem fallback — interface `SearchSession` (linhas 11-23) nao possui campo `status`

## Especialistas Consultados

- **@architect** — Impacto na latencia de Stage 1 (adicionando DB write antes de quota)
- **@data-engineer** — Schema migration idempotente, backfill de dados existentes
- **@dev** — Pipeline instrumentation em todos os 7 estagios
- **@qa** — Cobertura dos 13 cenarios de falha

## Evidencia da Investigacao

### 13 Cenarios de Falha Documentados

Cada cenario abaixo resulta em **quota consumida, sessao NAO registrada**:

| ID | Cenario | Stage de Falha | Quota | Cache | Sessao |
|----|---------|----------------|-------|-------|--------|
| F1 | Server timeout (gunicorn kill worker) | Qualquer | SIM | Parcial | NAO |
| F2 | PNCP API falha completa | 3 | SIM | NAO | NAO |
| F3 | AllSourcesFailedError | 3 | SIM | NAO | NAO |
| F4 | Filter logic crash | 4 | SIM | SIM (raw) | NAO |
| F5 | LLM + fallback fail | 6 | SIM | SIM | NAO |
| F6 | Excel crash | 6 | SIM | SIM | NAO |
| F7 | DB INSERT fails at Stage 7 | 7 | SIM | SIM | NAO |
| F8 | Client disconnects | Qualquer | SIM | Parcial | NAO |
| F9 | Memory error (OOM) | Qualquer | SIM | Parcial | NAO |
| F10 | Pipeline timeout (asyncio.TimeoutError) | 3 | SIM | Parcial | NAO |
| F11 | PNCPDegradedError sem cache fallback | 3 | SIM | NAO | NAO |
| F12 | Rate limit 429 apos quota | 3 | SIM | NAO | NAO |
| F13 | Unhandled exception em qualquer stage | Qualquer | SIM | Parcial | NAO |

### Evidencia no Codigo

1. **Quota irreversivel** — `quota.py:606`: `check_and_increment_quota_atomic()` e Postgres function (migration `003_atomic_quota_increment.sql`), committed imediatamente
2. **INSERT apenas no Stage 7** — `search_pipeline.py:2011` e `search_pipeline.py:2035`: unicos pontos onde `save_search_session()` e chamado
3. **Tabela sem lifecycle columns** — `search_sessions` nao possui `status`, `error_message`, `error_code`, `started_at`, `pipeline_stage`
4. **Error handlers silenciosos** — `routes/search.py:501-544`: 4 exception handlers (PNCPRateLimitError, PNCPAPIError, HTTPException, Exception) — nenhum atualiza sessao
5. **Pipeline error handlers** — `search_pipeline.py:983-1340`: handlers para AllSourcesFailedError, TimeoutError, PNCPDegradedError — nenhum persiste estado
6. **SearchContext** — `search_context.py:90-92`: `session_id` so e populado no Stage 7; `response_state` (linha 64) existe mas nunca e persistido
7. **Frontend interface** — `frontend/app/historico/page.tsx:11-23`: `SearchSession` interface sem campo `status`

## Criterios de Aceite

### Schema Changes

- [ ] **AC1: Migration `007_search_session_lifecycle.sql`** — Adicionar colunas a `search_sessions`:
  - `status TEXT NOT NULL DEFAULT 'created' CHECK (status IN ('created', 'processing', 'completed', 'failed', 'timed_out', 'cancelled'))`
  - `error_message TEXT` (nullable — descricao estruturada do erro)
  - `error_code TEXT` (nullable — machine-readable: `'sources_unavailable'`, `'timeout'`, `'filter_error'`, `'llm_error'`, `'db_error'`, `'quota_exceeded'`, `'unknown'`)
  - `started_at TIMESTAMPTZ NOT NULL DEFAULT now()` (quando usuario iniciou)
  - `completed_at TIMESTAMPTZ` (nullable — quando processamento terminou)
  - `duration_ms INTEGER` (nullable — computed: completed_at - started_at)
  - `search_id UUID` (nullable — correlaciona com SSE/job queue)
  - `pipeline_stage TEXT` (nullable — ultimo estagio alcancado: `'validate'`, `'prepare'`, `'execute'`, `'filter'`, `'enrich'`, `'generate'`, `'persist'`)
  - `raw_count INTEGER DEFAULT 0` (itens buscados antes de filtragem)
  - `response_state TEXT` (nullable: `'live'`, `'cached'`, `'degraded'`, `'empty_failure'`)

- [ ] **AC2: Migration idempotente** — Usar `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` para cada coluna. A migration deve ser segura para rodar multiplas vezes.

- [ ] **AC3: Backfill de dados existentes** — Ao final da migration:
  ```sql
  UPDATE search_sessions
  SET status = 'completed',
      started_at = COALESCE(created_at, now()),
      pipeline_stage = 'persist',
      response_state = 'live'
  WHERE status = 'created';
  ```
  Isso garante que sessoes pre-existentes (todas completadas com sucesso) reflitam o status correto.

### Pre-registration Flow

- [ ] **AC4: Criar `register_search_session()`** em `quota.py` — nova funcao que performa INSERT com `status='created'` ANTES da quota ser consumida.
  - Parametros: `user_id`, `sectors`, `ufs`, `data_inicial`, `data_final`, `custom_keywords`, `search_id`
  - Retorno: `session_id (str)` on success, `None` on failure
  - O INSERT deve conter apenas os campos de input (sem resultados — esses vem depois)
  - Retry: 1 tentativa apos 0.3s (mesma logica de `save_search_session()`)

- [ ] **AC5: Mover registro de sessao para Stage 1 (`stage_validate`)** — A sequencia no `search_pipeline.py:stage_validate()` deve ser:
  1. Rate limiting check (existente, linhas 569-591)
  2. **`register_search_session()`** — INSERT com `status='created'` (NOVO)
  3. `check_and_increment_quota_atomic()` — quota check (existente, linha 606)
  - Se registro falha: **NAO consumir quota**, retornar 503 (melhor ser honesto)
  - Se quota falha apos registro: `update_search_session_status(session_id, 'failed', error_code='quota_exceeded')`
  - Armazenar `ctx.session_id` imediatamente apos registro

- [ ] **AC6: Criar `update_search_session_status()`** em `quota.py` — helper function para updates:
  - Parametros: `session_id`, `status`, `pipeline_stage=None`, `error_message=None`, `error_code=None`, `raw_count=None`, `response_state=None`, `completed_at=None`, `duration_ms=None`
  - Apenas atualiza campos nao-None (dynamic UPDATE)
  - Non-blocking: log ERROR em falha mas NAO levanta excecao
  - 1 retry com 0.3s delay

- [ ] **AC7: Stage 1 — set `status='processing'`** — Apos quota check passar, atualizar sessao:
  ```python
  await update_search_session_status(ctx.session_id, status='processing', pipeline_stage='validate')
  ```

### Pipeline Stage Tracking

- [ ] **AC8: Stage 3 — tracking de execucao** — No inicio de `stage_execute` (search_pipeline.py:734):
  ```python
  await update_search_session_status(ctx.session_id, pipeline_stage='execute')
  ```
  Ao final do stage (antes de retornar), se `ctx.licitacoes_raw` existe:
  ```python
  await update_search_session_status(ctx.session_id, raw_count=len(ctx.licitacoes_raw))
  ```

- [ ] **AC9: Stage 4 — tracking de filtragem** — No inicio de `stage_filter` (search_pipeline.py:1373):
  ```python
  await update_search_session_status(ctx.session_id, pipeline_stage='filter')
  ```

- [ ] **AC10: Stage 6 — tracking de geracao** — No inicio de `stage_generate` (search_pipeline.py:1581):
  ```python
  await update_search_session_status(ctx.session_id, pipeline_stage='generate')
  ```

- [ ] **AC11: Stage 7 — completion** — Refatorar `stage_persist` (search_pipeline.py:1954) para:
  - Usar `update_search_session_status()` ao inves de `save_search_session()` para o UPDATE final
  - Set `status='completed'`, `completed_at=now()`, `pipeline_stage='persist'`
  - Preencher todos os campos de resultado (`total_raw`, `total_filtered`, `valor_total`, `resumo_executivo`, `destaques`, `response_state`, `duration_ms`)
  - `save_search_session()` continua existindo mas so e chamado se `ctx.session_id` for `None` (backward compat / graceful degradation AC23)

### Error Handling

- [ ] **AC12: Exception handlers em `routes/search.py`** — Cada um dos 4 handlers (linhas 501-544) deve chamar `update_search_session_status()`:
  - `PNCPRateLimitError` (501): `status='failed'`, `error_code='sources_unavailable'`, `error_message=f"PNCP rate limit: retry after {retry_after}s"`
  - `PNCPAPIError` (516): `status='failed'`, `error_code='sources_unavailable'`, `error_message=str(e)[:500]`
  - `HTTPException` (530): `status='failed'`, `error_code='unknown'`, `error_message=f"HTTP {exc.status_code}: {exc.detail}"`
  - `Exception` (536): `status='failed'`, `error_code='unknown'`, `error_message=f"{type(e).__name__}: {str(e)[:300]}"`

- [ ] **AC13: Exception handlers em `search_pipeline.py` Stage 3** — Handlers nas linhas 983-1340 devem atualizar `pipeline_stage` e `response_state`:
  - `AllSourcesFailedError` (983): `pipeline_stage='execute'`, `response_state='empty_failure'`
  - `asyncio.TimeoutError` (1066): `pipeline_stage='execute'`, `response_state='degraded'`
  - `PNCPDegradedError` (1259): `pipeline_stage='execute'`, `response_state='degraded'`
  - `Exception` generico (1122): `pipeline_stage='execute'`, `response_state='empty_failure'`
  - Nota: esses handlers ja fazem cache fallback — o update de sessao e ADICIONAL, nao substitui a logica existente

- [ ] **AC14: Timeout handling** — Em `asyncio.TimeoutError` (tanto no pipeline quanto na route):
  - `status='timed_out'`
  - `error_message` deve incluir tempo decorrido: `f"Pipeline timeout after {elapsed_ms}ms (limit: {timeout_ms}ms)"`
  - `error_code='timeout'`

- [ ] **AC15: SIGTERM handler** — No shutdown do servidor (main.py ou start.sh lifecycle):
  - Registrar handler para `signal.SIGTERM`
  - Na execucao: `UPDATE search_sessions SET status = 'timed_out', error_message = 'Server shutdown (SIGTERM)', completed_at = now() WHERE status IN ('created', 'processing')`
  - Log CRITICAL: `"Marking {n} in-flight sessions as timed_out due to SIGTERM"`
  - Timeout para o handler: 5s max (nao bloquear shutdown)

### Quota Compensation Strategy

- [ ] **AC16: Manter quota consumida (Option B)** — Buscas falhadas manteem a quota decrementada, mas aparecem no historico como "falha". Justificativa:
  - Evita race conditions de compensacao
  - Mantem audit trail completo
  - Usuario ve exatamente o que aconteceu
  - Operador pode fazer compensacao manual se necessario
  - Documenta a decisao como ADR no topo do PR

- [ ] **AC17: Historico mostra buscas falhadas** — A pagina `/historico` (`frontend/app/historico/page.tsx`) deve:
  - Renderizar buscas `failed`/`timed_out` com badge vermelho/laranja distinto
  - Mostrar `error_message` truncada (max 100 chars)
  - Exibir botao "Tentar novamente" que pre-popula os mesmos parametros no `/buscar`
  - Buscas `cancelled` aparecem com badge cinza

### Frontend Integration

- [ ] **AC18: Tipo `SearchSessionStatus`** — Adicionar ao frontend types (interface `SearchSession` em `app/historico/page.tsx`):
  ```typescript
  type SearchSessionStatus = 'created' | 'processing' | 'completed' | 'failed' | 'timed_out' | 'cancelled';

  interface SearchSession {
    // ... campos existentes ...
    status: SearchSessionStatus;
    error_message: string | null;
    error_code: string | null;
    duration_ms: number | null;
    pipeline_stage: string | null;
    started_at: string;
    response_state: string | null;
  }
  ```

- [ ] **AC19: Endpoint `/v1/sessions` inclui novos campos** — O endpoint de historico (backend `routes/sessions.py` ou equivalente proxy `frontend/app/api/sessions/route.ts`) deve retornar `status`, `error_message`, `error_code`, `duration_ms`, `pipeline_stage`, `started_at`, `response_state` em cada sessao.

- [ ] **AC20: UI de historico renderiza status** — Componente de card de sessao deve:
  - `completed` (default): badge verde "Concluida" + icone check (comportamento atual)
  - `failed`: badge vermelho "Falhou" + icone X + `error_message` + botao "Tentar novamente"
  - `timed_out`: badge laranja "Timeout" + icone relogio + `error_message` + botao "Tentar novamente"
  - `processing`: badge azul pulsante "Processando..." (raro — so aparece se pagina carregou mid-search)
  - `cancelled`: badge cinza "Cancelada"
  - `created`: badge cinza "Iniciada" (transitorio, nao deveria persistir)

### Observability

- [ ] **AC21: Prometheus counter** — Em `metrics.py`, adicionar:
  ```python
  search_session_status = Counter(
      "smartlic_search_session_status_total",
      "Search session status transitions",
      ["status"]  # labels: created, processing, completed, failed, timed_out
  )
  ```
  Incrementar em cada chamada a `register_search_session()` (label `created`) e `update_search_session_status()` (label conforme novo status).

- [ ] **AC22: Structured logging** — Em cada transicao de status, emitir log estruturado:
  ```python
  logger.info(json.dumps({
      "event": "search_session_status_change",
      "session_id": session_id[:8] + "***",
      "search_id": search_id or "no_id",
      "old_status": old_status,
      "new_status": new_status,
      "pipeline_stage": stage,
      "elapsed_ms": elapsed_ms,
      "user_id": mask_user_id(user_id),
  }))
  ```

### Safety (Degradacao Graceful)

- [ ] **AC23: Falha no registro NAO bloqueia busca** — Se `register_search_session()` falhar:
  - Log `logger.critical("Failed to register search session — continuing without session tracking")`
  - `ctx.session_id = None`
  - Pipeline continua normalmente (comportamento pre-existente sem sessao e melhor que bloquear tudo)
  - No Stage 7, se `ctx.session_id is None`, faz fallback para `save_search_session()` completo (comportamento atual)

- [ ] **AC24: Updates de status sao non-blocking** — Todas as chamadas a `update_search_session_status()` devem:
  - Executar em fire-and-forget (nao aguardar resultado no caminho critico)
  - Log ERROR em falha mas NUNCA propagar excecao
  - NAO adicionar latencia perceptivel ao pipeline (target: <5ms por update)
  - Usar `asyncio.create_task()` com error handler para nao perder exceptions silenciosamente

## Testes Obrigatorios

### Unit Tests — Backend

| # | Teste | Arquivo | AC |
|---|-------|---------|-----|
| T1 | Sessao criada ANTES da quota ser consumida | `test_search_session_lifecycle.py` | AC4, AC5 |
| T2 | Sessao atualizada para 'processing' apos quota pass | `test_search_session_lifecycle.py` | AC7 |
| T3 | Sessao atualizada para 'completed' apos Stage 7 | `test_search_session_lifecycle.py` | AC11 |
| T4 | Sessao atualizada para 'failed' em AllSourcesFailedError | `test_search_session_lifecycle.py` | AC12, AC13 |
| T5 | Sessao atualizada para 'timed_out' em asyncio.TimeoutError | `test_search_session_lifecycle.py` | AC14 |
| T6 | Quota NAO consumida se registro de sessao falha | `test_search_session_lifecycle.py` | AC5 |
| T7 | Busca continua mesmo se update de sessao falha (graceful degradation) | `test_search_session_lifecycle.py` | AC23 |
| T8 | Migration idempotente (rodar 2x sem erro) | `test_search_session_lifecycle.py` | AC2 |
| T9 | SIGTERM handler marca sessoes 'processing' como 'timed_out' | `test_search_session_lifecycle.py` | AC15 |
| T10 | Backfill seta status='completed' em sessoes existentes | `test_search_session_lifecycle.py` | AC3 |
| T11 | `update_search_session_status()` ignora campos None | `test_search_session_lifecycle.py` | AC6 |
| T12 | `update_search_session_status()` retry funciona em transient error | `test_search_session_lifecycle.py` | AC6 |
| T13 | Prometheus counter incrementa em cada transicao | `test_search_session_lifecycle.py` | AC21 |
| T14 | Structured log emitido em cada transicao | `test_search_session_lifecycle.py` | AC22 |

### Failure Scenario Tests (1 por cenario investigado)

| # | Cenario | Teste | Status Esperado | Error Code Esperado |
|---|---------|-------|----------------|---------------------|
| F1 | Server timeout (gunicorn kill) | `test_f1_server_timeout` | `timed_out` | `timeout` |
| F2 | PNCP API falha completa | `test_f2_pncp_total_failure` | `failed` | `sources_unavailable` |
| F3 | AllSourcesFailedError | `test_f3_all_sources_failed` | `failed` | `sources_unavailable` |
| F4 | Filter logic crash | `test_f4_filter_crash` | `failed` | `filter_error` |
| F5 | LLM + fallback fail | `test_f5_llm_crash` | `failed` | `llm_error` |
| F6 | Excel crash | `test_f6_excel_crash` | `failed` | `llm_error` |
| F7 | DB INSERT fails Stage 7 | `test_f7_db_insert_fail` | `completed` via fallback | `db_error` |
| F8 | Client disconnects | `test_f8_client_disconnect` | `timed_out` | `timeout` |
| F9 | OOM | `test_f9_oom` (simulated MemoryError) | `failed` | `unknown` |
| F10 | Pipeline timeout | `test_f10_pipeline_timeout` | `timed_out` | `timeout` |
| F11 | PNCPDegradedError sem cache | `test_f11_degraded_no_cache` | `failed` | `sources_unavailable` |
| F12 | Rate limit pos-quota | `test_f12_rate_limit_post_quota` | `failed` | `sources_unavailable` |
| F13 | Unhandled exception | `test_f13_unhandled_exception` | `failed` | `unknown` |

### Frontend Tests

| # | Teste | Arquivo | AC |
|---|-------|---------|-----|
| FE1 | Historico renderiza badge verde para 'completed' | `test_historico_status_badges.tsx` | AC20 |
| FE2 | Historico renderiza badge vermelho para 'failed' com error_message | `test_historico_status_badges.tsx` | AC20 |
| FE3 | Historico renderiza badge laranja para 'timed_out' | `test_historico_status_badges.tsx` | AC20 |
| FE4 | Botao "Tentar novamente" navega para /buscar com params | `test_historico_status_badges.tsx` | AC17 |
| FE5 | Interface SearchSession inclui campos de status | `test_historico_status_badges.tsx` | AC18 |

### Integration Tests

| # | Teste | Descricao |
|---|-------|-----------|
| I1 | Pipeline end-to-end com sucesso | Session transitions: created -> processing -> completed |
| I2 | Pipeline end-to-end com falha no Stage 3 | Session transitions: created -> processing -> failed |
| I3 | Pipeline end-to-end com timeout | Session transitions: created -> processing -> timed_out |

## Definicao de Pronto

- [ ] Migration `007_search_session_lifecycle.sql` aplicada e idempotente
- [ ] Backfill de sessoes existentes executado com sucesso
- [ ] `register_search_session()` criada e chamada em Stage 1 antes de quota
- [ ] `update_search_session_status()` criada e chamada em cada transicao
- [ ] Todos os 4 exception handlers em `routes/search.py` atualizam sessao
- [ ] Todos os exception handlers relevantes em `search_pipeline.py` atualizam sessao
- [ ] SIGTERM handler registrado e funcional
- [ ] Frontend renderiza status badges no historico
- [ ] Prometheus counter `search_session_status_total` funcional
- [ ] Structured logs em cada transicao
- [ ] 14 unit tests + 13 failure scenario tests + 5 frontend tests + 3 integration tests passando
- [ ] Zero regressao nos testes pre-existentes (baseline: ~34 fail BE / ~42 fail FE)
- [ ] Graceful degradation verificada (falha no registro nao bloqueia busca)
- [ ] PR aprovado com ADR documentando decisao de quota (Option B)

## Riscos e Mitigacoes

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|--------------|---------|-----------|
| R1 | DB write adicional no Stage 1 aumenta latencia | Alta | Baixo (~5-10ms) | Supabase connection pooling ja existe. Timeout de 2s no INSERT. Monitorar via `search_duration_seconds` histogram. |
| R2 | Falha no update de sessao nos exception handlers mascara erro original | Media | Medio | `update_search_session_status()` e fire-and-forget com try/except proprio. Log do erro original SEMPRE vem primeiro. |
| R3 | SIGTERM handler nao executa em SIGKILL (Railway force-kill) | Alta | Baixo | Railway envia SIGTERM primeiro, aguarda `graceful-timeout` (60s atualmente). SIGKILL so se processo nao terminar. Sessoes orfas podem ser identificadas via cron job: `WHERE status IN ('created','processing') AND started_at < now() - interval '10 minutes'`. |
| R4 | Race condition entre register_search_session e quota increment | Baixa | Alto | Execucao sequencial (nao paralela). Se registro falha -> nao consome quota. Se quota falha -> update sessao para 'failed'. Nao ha estado inconsistente possivel. |
| R5 | Backfill incorreto de sessoes existentes | Baixa | Medio | Backfill conservador: assume `completed` para todas as existentes (correto, ja que so eram inseridas em sucesso). Validar contagem antes/depois. |
| R6 | Volume de UPDATE statements sobrecarrega DB | Baixa | Baixo | Max 4-5 updates por busca (created, processing, stage tracking, completed). Supabase free tier suporta facilmente. Updates sao fire-and-forget, nao bloqueiam pipeline. |

## Arquivos Envolvidos

### Backend — Modificados

| Arquivo | Tipo de Mudanca | ACs |
|---------|----------------|-----|
| `backend/migrations/007_search_session_lifecycle.sql` | **NOVO** — Migration com ALTER TABLE + backfill | AC1, AC2, AC3 |
| `backend/quota.py` | **MODIFICADO** — `register_search_session()` + `update_search_session_status()` | AC4, AC6 |
| `backend/search_pipeline.py` | **MODIFICADO** — Chamadas de tracking em todos os stages | AC5, AC7, AC8, AC9, AC10, AC11 |
| `backend/search_context.py` | **MODIFICADO** — Garantir `session_id` setado no Stage 1 | AC5 |
| `backend/routes/search.py` | **MODIFICADO** — Exception handlers atualizam sessao | AC12, AC14 |
| `backend/metrics.py` | **MODIFICADO** — Counter `search_session_status_total` | AC21 |
| `backend/main.py` | **MODIFICADO** — SIGTERM handler (ou `start.sh`) | AC15 |

### Backend — Novos

| Arquivo | Descricao | ACs |
|---------|-----------|-----|
| `backend/tests/test_search_session_lifecycle.py` | **NOVO** — 14 unit tests + 13 failure scenarios + 3 integration | T1-T14, F1-F13, I1-I3 |

### Frontend — Modificados

| Arquivo | Tipo de Mudanca | ACs |
|---------|----------------|-----|
| `frontend/app/historico/page.tsx` | **MODIFICADO** — Interface `SearchSession` + status badges + "Tentar novamente" | AC17, AC18, AC20 |
| `frontend/app/api/sessions/route.ts` | **MODIFICADO** — Incluir novos campos na response | AC19 |

### Frontend — Novos

| Arquivo | Descricao | ACs |
|---------|-----------|-----|
| `frontend/__tests__/pages/HistoricoStatusBadges.test.tsx` | **NOVO** — 5 testes de renderizacao de status | FE1-FE5 |

## Dependencias

### Bloqueado Por

| ID | Titulo | Motivo |
|----|--------|--------|
| **CRIT-001** | Alinhamento de schema base | Schema de `search_sessions` deve estar estavel antes de adicionar lifecycle columns |

### Bloqueia

| ID | Titulo | Motivo |
|----|--------|--------|
| **CRIT-003** | State machine formal para search lifecycle | Necessita da coluna `status` com CHECK constraint para definir transicoes validas |

### Relacionado

| ID | Titulo | Relacao |
|----|--------|---------|
| GTM-RESILIENCE-F01 | ARQ Job Queue | `search_id` UUID correlaciona sessao com jobs ARQ |
| GTM-RESILIENCE-E03 | Prometheus Metrics | Novo counter se adiciona ao existente `metrics.py` |
| GTM-RESILIENCE-B01 | SWR Cache | Sessao tracka `response_state` que inclui `cached` |
