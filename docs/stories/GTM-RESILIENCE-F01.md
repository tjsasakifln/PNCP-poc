# GTM-RESILIENCE-F01 --- Job Queue para LLM + Excel em Background (ARQ)

| Campo | Valor |
|-------|-------|
| **Track** | F: Infra para Escala |
| **Prioridade** | P2 |
| **Sprint** | 4 |
| **Estimativa** | 8-12 horas (4 tracks paralelizaveis) |
| **Gaps** | I-03, I-04 |
| **Dependencias** | GTM-RESILIENCE-B04 (Redis provisionado na Railway) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

O pipeline de busca do SmartLic executa 7 estagios sequenciais dentro de um unico request HTTP. Os estagios 6 (resumo LLM via GPT-4.1-nano) e 7 (geracao de Excel via openpyxl + upload para storage) rodam **inline no contexto do request**, bloqueando o gunicorn worker por 10-30 segundos adicionais apos o fetch e filtragem ja terem completado.

Com `WEB_CONCURRENCY=2` (2 workers gunicorn+uvicorn), apenas 2 buscas podem executar simultaneamente. Se ambos os workers estiverem no estagio LLM/Excel, a terceira busca entra em fila do gunicorn e o usuario ve timeout.

### Situacao Atual

- **LLM inline**: `gerar_resumo()` chamada sincrona em `search_pipeline.py` L1246, bloqueia 3-10s (GPT-4.1-nano, max_tokens=500, temp=0.3)
- **Excel inline**: `create_excel()` + `upload_excel()` em `search_pipeline.py` L1281-1306, bloqueia 2-8s (openpyxl + upload Supabase Storage)
- **Unica background task**: `cron_jobs.py` executa cleanup de cache local a cada 6h via `asyncio.create_task()`
- **Sem job queue**: Nenhuma lib de filas instalada (sem Celery, ARQ, APScheduler)
- **Redis**: `redis==5.3.1` instalado em requirements.txt, mas nao provisionado em producao (InMemoryCache fallback ativo)
- **SSE**: `ProgressTracker` em `progress.py` ja suporta Redis pub/sub e emite eventos por estagio ("llm", "excel", "complete")

### Impacto

- 2 workers = 2 buscas concorrentes maximo
- Busca de 27 UFs: ~60-180s fetch + 10-30s LLM/Excel = worker bloqueado por 70-210s total
- Escalabilidade horizontal limitada pelo custo do estagio de geracao, nao do fetch

---

## Problema

A geracao de resumo LLM e planilha Excel roda **dentro do request HTTP**, bloqueando gunicorn workers por 10-30 segundos desnecessariamente. Os resultados da busca ja estao prontos no final do estagio 5 (filtragem), mas o usuario precisa esperar os estagios 6-7 completarem antes de receber qualquer dado. Com apenas 2 workers, isso limita a capacidade do sistema a 2 buscas simultaneas antes de degradacao.

---

## Solucao

Adotar **ARQ** (async Redis queue, compativel com asyncio) como job queue leve para desacoplar o trabalho pesado do request HTTP:

1. **Instalar ARQ** (`arq>=0.26`) e configurar worker pool conectado ao Redis
2. **Mover geracao LLM** para background job: `LLMSummaryJob` recebe `search_id` + `licitacoes_filtradas`, executa `gerar_resumo()`, persiste resultado
3. **Mover geracao Excel** para background job: `ExcelGenerationJob` recebe `search_id` + `licitacoes_filtradas`, executa `create_excel()` + `upload_excel()`, persiste URL
4. **Retorno imediato**: Apos estagio 5, retornar resultados da busca ao usuario via HTTP 200 com `llm_status: "processing"` e `excel_status: "processing"`
5. **Notificacao via SSE**: Quando jobs completam, emitir eventos SSE ("llm_ready", "excel_ready") via `ProgressTracker`
6. **Fallback inline**: Se Redis indisponivel ou ARQ health check falhar, executar LLM/Excel inline (modo degradado sincrono) — nenhuma regressao

---

## Acceptance Criteria

### Track 1 --- Infraestrutura ARQ (P0)

- [ ] **AC1**: Dependencia `arq>=0.26,<1.0` adicionada a `requirements.txt`
- [ ] **AC2**: Modulo `backend/job_queue.py` criado com: `get_arq_pool()`, `enqueue_job()`, `is_queue_available()`, `WorkerSettings`
- [ ] **AC3**: ARQ conecta ao mesmo Redis de `REDIS_URL` (env var ja existente no projeto)
- [ ] **AC4**: Health check de ARQ integrado ao endpoint `GET /v1/health` existente com campo `queue: "healthy" | "unavailable"`
- [ ] **AC5**: Worker ARQ iniciavel via `arq backend.job_queue.WorkerSettings` (separado do gunicorn)
- [ ] **AC6**: Dockerfile atualizado com processo worker ARQ (ou script de start separado para Railway)

### Track 2 --- Job de Resumo LLM (P0)

- [ ] **AC7**: Funcao `llm_summary_job(ctx, search_id, licitacoes, sector_name)` registrada no ARQ WorkerSettings
- [ ] **AC8**: Job executa `gerar_resumo()` com fallback para `gerar_resumo_fallback()` (mesma logica atual de search_pipeline.py L1246-1253)
- [ ] **AC9**: Resultado do resumo persistido em `search_cache` (Supabase) com campo `resumo_json` vinculado ao `search_id`
- [ ] **AC10**: Se job falhar apos 2 retries, persistir resumo fallback (nunca retornar None)
- [ ] **AC11**: Tempo maximo de execucao do job: 30s (ARQ `timeout` setting)

### Track 3 --- Job de Geracao Excel (P0)

- [ ] **AC12**: Funcao `excel_generation_job(ctx, search_id, licitacoes, quota_info)` registrada no ARQ WorkerSettings
- [ ] **AC13**: Job executa `create_excel()` + `upload_excel()` (mesma logica atual de search_pipeline.py L1279-1306)
- [ ] **AC14**: URL assinada da planilha persistida em `search_cache` (Supabase) com campo `excel_url` vinculado ao `search_id`
- [ ] **AC15**: Se job falhar apos 2 retries, marcar `excel_status: "failed"` com mensagem de erro amigavel
- [ ] **AC16**: Tempo maximo de execucao do job: 60s (ARQ `timeout` setting)

### Track 4 --- Integracao Pipeline + SSE (P0)

- [ ] **AC17**: `search_pipeline.py` estagio 6-7 modificado: se queue disponivel, enfileirar jobs e retornar imediatamente com `llm_status: "processing"` e `excel_status: "processing"`
- [ ] **AC18**: Response `BuscaResponse` (schemas.py) atualizado com campos opcionais `llm_status: Optional[str]` e `excel_status: Optional[str]`
- [ ] **AC19**: Quando job LLM completa, emitir evento SSE `{"stage": "llm_ready", "progress": 85, "message": "Resumo pronto"}` via `ProgressTracker`
- [ ] **AC20**: Quando job Excel completa, emitir evento SSE `{"stage": "excel_ready", "progress": 98, "message": "Planilha pronta para download", "detail": {"download_url": "..."}}` via `ProgressTracker`
- [ ] **AC21**: Frontend `useSearch.ts` atualizado para receber eventos "llm_ready" e "excel_ready" e atualizar UI progressivamente
- [ ] **AC22**: Se `is_queue_available()` retorna False, executar LLM/Excel inline como hoje (zero regressao)

### Track 5 --- Testes (P0)

- [ ] **AC23**: Testes unitarios para `job_queue.py`: pool creation, health check, enqueue, fallback quando Redis indisponivel (6+ testes)
- [ ] **AC24**: Testes unitarios para `llm_summary_job`: execucao normal, fallback, timeout, persistencia (4+ testes)
- [ ] **AC25**: Testes unitarios para `excel_generation_job`: execucao normal, upload falha, timeout, persistencia (4+ testes)
- [ ] **AC26**: Teste de integracao: pipeline completo com queue mockado retorna imediatamente + emite SSE quando job completa
- [ ] **AC27**: Teste de integracao: pipeline completo com queue indisponivel executa inline (regressao zero)
- [ ] **AC28**: Todos os testes existentes do pipeline continuam passando (baseline: ~3400 pass)

---

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/requirements.txt` | Adicionar `arq>=0.26,<1.0` |
| `backend/job_queue.py` | **NOVO** --- ARQ pool, worker settings, enqueue helpers |
| `backend/search_pipeline.py` | Estagio 6-7: enfileirar jobs se queue disponivel, senao inline |
| `backend/schemas.py` | Campos `llm_status`, `excel_status` em BuscaResponse |
| `backend/progress.py` | Novos eventos SSE: "llm_ready", "excel_ready" |
| `backend/main.py` | Registrar ARQ pool no lifespan (startup/shutdown) |
| `backend/Dockerfile` | Worker ARQ como processo separado ou script de start |
| `backend/cron_jobs.py` | Opcional: migrar cache cleanup para job ARQ periodico |
| `frontend/hooks/useSearch.ts` | Receber eventos "llm_ready" / "excel_ready" |
| `frontend/types/` | Atualizar interface BuscaResponse com campos opcionais |
| `backend/tests/test_job_queue.py` | **NOVO** --- Testes de ARQ pool e jobs |
| `backend/tests/test_search_pipeline.py` | Atualizar para mode queue vs inline |

---

## Dependencias

| Dependencia | Tipo | Status |
|-------------|------|--------|
| **GTM-RESILIENCE-B04** (Redis provisionado) | Hard | Necessario para ARQ funcionar em producao |
| `redis==5.3.1` | Instalado | Ja em requirements.txt |
| `arq>=0.26` | Nova | A instalar |
| SSE/ProgressTracker | Existente | Ja suporta Redis pub/sub |
| Supabase Storage | Existente | Ja usado para upload de Excel |

---

## Definition of Done

- [ ] ARQ worker pool inicia e conecta ao Redis sem erros
- [ ] Busca com queue disponivel retorna resultados em <5s apos filtragem (estagios 1-5)
- [ ] Resumo LLM chega via SSE em <15s apos retorno da busca
- [ ] Excel chega via SSE em <15s apos retorno da busca
- [ ] Busca com queue indisponivel funciona identicamente ao comportamento atual (inline)
- [ ] Health endpoint reporta status da queue
- [ ] Todos os testes existentes passam sem regressao
- [ ] 18+ novos testes passando
- [ ] Documentacao inline nos modulos novos
- [ ] Worker ARQ deployavel na Railway como processo separado

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|---------------|---------|-----------|
| Redis nao provisionado bloqueia a feature | Alta | Alto | Fallback inline (AC22) garante zero regressao |
| Worker ARQ crash perde jobs | Media | Medio | ARQ tem retry built-in (2 tentativas); fallback persiste resultado minimo |
| SSE desconecta antes do job completar | Media | Baixo | Frontend pode fazer GET `/buscar/{search_id}/status` como polling fallback |
| Custo Railway de processo extra (ARQ worker) | Baixa | Baixo | Worker ARQ usa ~128MB RAM; custo marginal no plano atual |
| Race condition: resultado inline + job duplicado | Baixa | Baixo | Flag `queue_mode` no SearchContext impede execucao duplicada |

---

## Notas Tecnicas

### Por que ARQ e nao Celery?

- **ARQ e nativo asyncio** --- compativel com FastAPI sem bridges
- **Usa Redis diretamente** --- ja instalado, sem RabbitMQ
- **Leve** (~300 linhas de codigo) vs Celery (~50k linhas)
- **Worker embutivel** no mesmo processo ou separado
- **Retry e timeout** built-in com configuracao simples

### Fluxo com Queue (proposto)

```
[Request] --> [Estagios 1-5: Fetch+Filter] --> [HTTP 200 com resultados]
                                                      |
                                            [Enqueue LLM Job]
                                            [Enqueue Excel Job]
                                                      |
                                              [ARQ Worker Pool]
                                                /            \
                                      [LLM Job]              [Excel Job]
                                           |                       |
                                   [Persist resumo]     [Upload + Persist URL]
                                           |                       |
                                   [SSE: llm_ready]     [SSE: excel_ready]
```

### Fluxo sem Queue (fallback inline)

```
[Request] --> [Estagios 1-5: Fetch+Filter] --> [Estagio 6: LLM inline] --> [Estagio 7: Excel inline] --> [HTTP 200]
```

Identico ao comportamento atual. Zero regressao.
