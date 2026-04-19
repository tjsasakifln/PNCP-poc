# STORY-CIG-BE-cache-warming-deprecate — Deprecar cache warming proativo (Layer 3 jobs) + zerar baseline de testes relacionados

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate Blocker
**Effort:** L (8-16h)
**Agents:** @dev, @qa, @devops

---

## Contexto

A premissa original desta story era "consertar mock-drift dos testes de cache warming". Após reavaliação arquitetural em 2026-04-18, essa premissa foi invalidada: **cache warming proativo (Layer 3 jobs) é obsoleto**.

O Supabase agora armazena localmente ~50k licitações abertas (`pncp_raw_bids`) + 2M+ contratos históricos (estratégia 100% orgânica de inbound via SEO). Toda consulta de busca vai ao DB via `search_datalake` RPC (Layer 2) com índice GIN full-text, retorno <100ms. Pré-aquecer `search_results_cache` rodando buscas completas em background virou **overhead puro** — o sistema foi desenhado para APIs lentas (PNCP/PCP/ComprasGov), não para DB local rápido.

Consertar mocks dos testes de warming seria **trabalho inútil**. O trabalho frutífero é **remover o código obsoleto**, deletar os testes e alinhar documentação/stories ao novo modelo arquitetural.

**O que SAI (jobs proativos):**
- `cron/cache.py`: `warmup_specific_combinations`, `warmup_top_params`, `_warmup_startup_and_periodic`, `start_warmup_task`, `start_coverage_check_task`, `ensure_minimum_cache_coverage`, `_get_prioritized_ufs`
- `jobs/cron/cache_ops.py`: **arquivo inteiro** (duplicado de `cron/cache.py`, herança DEBT-v3-S3)
- `jobs/queue/jobs.py`: funções `cache_warming_job`, `cache_refresh_job`
- `jobs/queue/config.py`: registros ARQ dos dois jobs acima
- `startup/lifespan.py`: `task_registry.register("warmup", ...)` e `("coverage_check", ...)`
- `cache/admin.py`: `get_popular_ufs_from_sessions`, `get_stale_entries_for_refresh`, `get_top_popular_params`
- `config/pipeline.py`: flags `WARMUP_ENABLED`, `CACHE_WARMING_ENABLED`, `CACHE_REFRESH_ENABLED`, `CACHE_WARMING_POST_DEPLOY_ENABLED` + constantes associadas
- `config/features.py`: entrada `CACHE_WARMING_ENABLED` da registry
- Testes: `test_cache_warming_noninterference.py`, `test_cache_refresh.py`, `test_crit055_warmup_adaptive.py`, `test_cache_global_warmup.py`, `test_cache_refresh_enabled.py`, `test_ensure_minimum_coverage.py`

**O que FICA (cache passivo SWR por-request):**
- Tabela Supabase `search_results_cache` (cache on-demand, populado por requests reais)
- L1 `InMemoryCache` + L2 Redis (cache em memória/Redis por-request)
- `cache/swr.py::trigger_background_revalidation` (SWR reativo por-request)
- `cache/local_file.py` (L3 local file cache passivo + eviction)
- Layer 1 ingestion ETL (ortogonal — não muda)

---

## Acceptance Criteria

- [ ] **AC1:** Todas as funções/módulos listados em "O que SAI" removidos do codebase. Grep `warmup_specific_combinations|warmup_top_params|cache_warming_job|cache_refresh_job|ensure_minimum_cache_coverage|start_warmup_task|start_coverage_check_task|WARMUP_ENABLED|CACHE_WARMING_ENABLED|CACHE_REFRESH_ENABLED|CACHE_WARMING_POST_DEPLOY_ENABLED` sobre `backend/**/*.py` (excluindo tests deletados e CHANGELOG) retorna zero hits.
- [ ] **AC2:** Arquivo `backend/jobs/cron/cache_ops.py` deletado (via `git rm`).
- [ ] **AC3:** 6 arquivos de teste listados em "O que SAI" deletados (via `git rm`). `test_harden018_cache_dir_maxsize.py` e `test_admin_cache.py` **preservados** (cobrem cache passivo).
- [ ] **AC4:** `cd backend && ruff check .` retorna exit 0. `mypy .` não introduz novos erros em módulos tocados.
- [ ] **AC5:** `pytest backend/tests/ --timeout=30 -q` retorna exit 0, zero failures, zero errors. Número total de testes diminui (~50 testes removidos entre os 6 arquivos).
- [ ] **AC6:** `backend-tests.yml` no PR desta story passa com 0 failed / 0 errored. Link no Change Log.
- [ ] **AC7:** CLAUDE.md seção "Data Architecture (3 Layers)" atualizada: Layer 3 reescrita para "cache passivo por-request" + menção a 2M contratos em Layer 1. `.claude/rules/architecture-detail.md` atualizado. ROADMAP.md recebe entrada 2026-04 cache warming deprecation. CHANGELOG.md recebe entrada breaking.
- [ ] **AC8:** Stories históricas GTM-STAB-007, CRIT-081, CRIT-055, GTM-ARCH-002 marcadas como Superseded com referência a esta story.
- [ ] **AC9:** Migrations `warming_user_profile.sql` e `debt009_ban_cache_warmer.sql` **não são tocadas** (histórico já aplicado; conta banida permanece banida agora por razão ainda mais forte).
- [ ] **AC10 (NEGATIVO):** Zero `@pytest.mark.skip` markers adicionados em testes — remoção é via `git rm`, não skip.

---

## Scope

**IN:**
- Remoção de código de produção (jobs, flags, funções admin consumidas só por jobs, façades órfãs).
- Deleção de 6 arquivos de teste via `git rm`.
- Renomear story `CIG-BE-admin-cache-metrics` → `CIG-BE-admin-cache-metrics-obsolete` (separada, mesmo PR ou adjacente).
- Atualização de documentação autoritativa (CLAUDE.md, architecture-detail.md, ROADMAP, CHANGELOG, PRD, README).
- Marcar stories históricas como Superseded.

**OUT:**
- NÃO remover tabela Supabase `search_results_cache` (cache passivo ainda usa).
- NÃO remover L1/L2 InMemory/Redis (cache passivo ainda usa).
- NÃO remover `swr.py::trigger_background_revalidation` (SWR reativo por-request permanece).
- NÃO mexer em Layer 1 ingestion (ETL de bids + contratos é ortogonal).
- NÃO mexer em migrations `warming_user_profile.sql` / `debt009_ban_cache_warmer.sql`.
- NÃO deletar stories históricas — apenas marcar Superseded.
- NÃO alterar endpoint `/v1/admin/cache/metrics` (cobre cache passivo — fica). Métricas mortas específicas de warming (`smartlic_cache_warming_*`, `smartlic_cache_refresh_*`) tratadas em story irmã `CIG-BE-admin-cache-metrics-obsolete`.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Story irmã:** STORY-CIG-BE-admin-cache-metrics-obsolete (limpeza de métricas Prometheus mortas + componentes frontend dependentes)
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage rows #9/30 e #15/30)

## Stories relacionadas no epic

- STORY-CIG-BE-cache-redis-cascade (#8 — Done, cobre cache passivo que permanece)
- STORY-CIG-BE-admin-cache-metrics-obsolete (story irmã)

## Stories substituídas (Superseded)

- GTM-STAB-007 (Cache Warming para Buscas Populares)
- CRIT-081 (Cache Warmup Periódico Ininterrupto)
- CRIT-055 (Warmup Adaptativo Baseado em Buscas Reais)
- GTM-ARCH-002 (Cache Global + Warmup Cron)

---

## Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Cache hit rate cai nas primeiras horas pós-deploy (cold cache) | Aceito — DB queries <100ms tornam irrelevante. Monitorar `smartlic_search_duration_seconds` p95 nas 24h pós-deploy |
| Importar código morto em runtime não detectado por ruff/mypy | Mitigado — grep final + `pytest --collect-only` detecta import errors |
| Flags removidas quebram env de produção (Railway) | Mitigado — remoção de `os.getenv(..., "true")` apenas elimina leitura; env vars residuais no Railway são silenciosamente ignoradas |
| Perda de capacidade de kill-switch emergencial | Intencional — decisão é deprecação definitiva, não flag-off |

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #9/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. 15 testes mock-drift; validar `_isolate_arq_module` conforme CLAUDE.md.
- **2026-04-18** — @dev + usuário: **pivot arquitetural**. Premissa "mock-drift fix" invalidada após reavaliação. DataLake Supabase (50k bids + 2M contratos) é fonte primária; cache warming proativo obsoleto. Story renomeada de `STORY-CIG-BE-cache-warming-dispatch` → `STORY-CIG-BE-cache-warming-deprecate`. Escopo pivotado de "fix mocks" para "deprecar código + deletar testes + alinhar docs". Plano aprovado em `/home/tjsasakifln/.claude/plans/cache-warming-uma-nifty-boot.md`.
