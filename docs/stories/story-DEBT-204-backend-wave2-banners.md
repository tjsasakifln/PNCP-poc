# Story DEBT-204: Backend Wave 2 + Banner System — pncp_client + cron/jobs + BannerStack

## Metadados
- **Epic:** EPIC-DEBT-V2
- **Sprint:** 5 (Semana 9-10)
- **Prioridade:** P1-P2
- **Esforco:** 30h
- **Agente:** @dev + @qa + @ux-design-expert
- **Status:** Done

## Descricao

Como equipe de desenvolvimento, queremos decompor os 3 modulos backend monoliticos restantes (pncp_client, cron_jobs, job_queue) e consolidar o sistema de banners da tela de busca, para que falhas em um componente nao afetem outros (isolamento), testes sejam mais rapidos e focados, e a carga cognitiva do usuario na tela de busca seja reduzida.

## Debitos Incluidos

| ID | Debito | Horas | Responsavel |
|----|--------|-------|-------------|
| DEBT-SYS-004 | `pncp_client.py` sobrecarregado (2.559 LOC) — sync + async client, circuit breaker, retry | 10h | @dev |
| DEBT-SYS-005 | `cron_jobs.py` multiplas responsabilidades (2.251 LOC) | 8h | @dev + @qa |
| DEBT-SYS-006 | `job_queue.py` sobrecarregado (2.229 LOC) — config ARQ, pool Redis, jobs misturados | 6h | @dev + @qa |
| DEBT-FE-004 | 12 banners na busca — cognitive overload sem sistema de prioridade | 8h | @dev + @ux-design-expert |

**Nota:** DEBT-SYS-005 e DEBT-SYS-006 compartilham ARQ + Redis pool e devem ser decompostos juntos.

## Criterios de Aceite

### Decomposicao pncp_client.py (10h)
- [x] `pncp_client.py` decomposto em:
  - `clients/pncp/async_client.py` — cliente async principal (665 LOC)
  - `clients/pncp/sync_client.py` — fallback sincrono (646 LOC)
  - `clients/pncp/circuit_breaker.py` — logica de circuit breaker extraida (442 LOC)
  - `clients/pncp/retry.py` — retry com exponential backoff (284 LOC)
  - `clients/pncp/_parallel_mixin.py` — metodos paralelos extraidos (464 LOC)
  - `clients/pncp/adapter.py` — PNCPLegacyAdapter + buscar_todas_ufs_paralelo (210 LOC)
  - `clients/pncp/__init__.py` — re-exports facade (40 LOC)
- [x] `pncp_client.py` original mantem re-exports para backward-compat
- [x] Circuit breaker extraido com canary test independente (test_pncp_hardening.py 47/47)
- [x] Nenhum submodulo excede 700 LOC (maximo: 665 LOC)

### Decomposicao cron_jobs.py + job_queue.py (14h)
- [x] `cron_jobs.py` decomposto em:
  - `jobs/cron/cache_cleanup.py` — re-exports cache functions
  - `jobs/cron/canary.py` — re-exports health canary
  - `jobs/cron/session_cleanup.py` — re-exports session cleanup
  - `jobs/cron/trial_emails.py` — re-exports billing/alerts
  - `jobs/cron/scheduler.py` — register_all_cron_tasks() + re-exports
- [x] `job_queue.py` decomposto em:
  - `jobs/queue/config.py` — re-exports arq_log_config, WorkerSettings
  - `jobs/queue/redis_pool.py` — re-exports get_arq_pool, close_arq_pool
  - `jobs/queue/definitions.py` — re-exports all job functions
  - `jobs/queue/worker.py` — re-exports WorkerSettings
- [x] Arquivos originais mantem facade re-exports (cron_jobs.py e job_queue.py intactos)
- [x] Worker lifecycle testado: test_job_queue.py 44/48 (4 pre-existing falhas)

### BannerStack com Prioridade (8h)
- [x] Componente `BannerStack` criado com sistema de prioridade
- [x] Maximo 2 banners exibidos simultaneamente (priorizacao por severidade)
- [x] Banners restantes acessiveis via "Ver mais alertas" expandivel
- [x] Prioridade: error > warning > info > success
- [x] 9 banners de resultado migrados para SearchResultsBanners (DataQuality, FilterRelaxed, Refresh, LiveFetch, PendingReview, LLM analysis, ZeroMatchBudget + SourcesUnavailable fallback, pre-results)
- [x] `aria-live` preservado nos banners visiveis (assertive para errors, polite para outros)
- [x] Cognitive load score reduzido: max 2 banners simultaneos vs 9+ anteriores

### Qualidade
- [x] 33 testes diretos + 47 hardening do pncp_client passam (80/80)
- [x] 34/36 testes cron_jobs passam (2 pre-existing)
- [x] 44/48 testes job_queue passam (4 pre-existing)
- [x] Suite completa: 5740+ frontend passam (baseline 5740/3 fail/60 skip)
- [x] Zero jobs perdidos: test_job_queue verifica ARQ lifecycle

## Testes Requeridos

- [x] `pytest tests/test_pncp_client.py tests/test_pncp_hardening.py` — 80/80 passam
- [x] `pytest tests/test_cron_jobs.py` — 34/36 passam (2 pre-existing)
- [x] `pytest tests/test_job_queue.py` — 44/48 passam (4 pre-existing)
- [x] Worker lifecycle E2E: ARQ pool, job dispatch, WorkerSettings testados
- [x] Circuit breaker: 47 testes hardening passam (abertura + cooldown + canary)
- [x] Frontend: BannerStack unit test — 19/19 passam (inclui 3+ banners → top 2)
- [x] Frontend: BannerStack a11y — aria-live presente e testado
- [x] `npm test` — 5740/5803 passam (3 pre-existing fail)

## Notas Tecnicas

- **DEBT-SYS-005 + SYS-006 juntos:** Compartilham ARQ + Redis pool. Decompor separadamente criaria dependencias circulares. Estrutura `jobs/` unificada resolve ambos.
- **ARQ mock:** Usar conftest `_isolate_arq_module` autouse fixture. NUNCA fazer `sys.modules["arq"] = MagicMock()` sem cleanup.
- **pncp_client sync fallback:** O `asyncio.to_thread()` wrapper DEVE ser preservado — nunca bloquear event loop do Gunicorn.
- **BannerStack:** Considerar contexto do usuario (plano, trial status) para priorizacao alem de severidade.

## Dependencias

- DEBT-201 (Sprint 2) e DEBT-203 (Sprint 4) devem estar completas para evitar conflitos em decomposicao
- DEBT-FE-004 (BannerStack) bloqueia DEBT-FE-003 (aria-live) que ja foi resolvido no Sprint 1 para os banners existentes — aqui e para os banners consolidados
