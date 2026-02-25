# GTM-STAB-000 — Sprint Plan: Estabilização GTM

**Status:** In Progress
**Priority:** P0 — Sprint inteira é blocker para GTM
**Created:** 2026-02-24
**Revised:** 2026-02-24 (post full-squad review: @architect, @qa, @devops)
**Last Updated:** 2026-02-25 (AC audit — squad verification of all 10 stories, 86/163 ACs marked done)
**Sprint Owner:** Tiago Sasaki
**Goal:** Garantir experiência premium enterprise para GTM launch

---

## Contexto

Diagnóstico realizado em 2026-02-24 baseado em:
- Teste manual em produção (screenshots com 0 resultados + 524)
- Sentry analysis (11 issues ativos, 62+ eventos em 14 dias)
- Railway logs (Redis TimeoutError, ARQ crash loop, WORKER TIMEOUT)
- Codebase analysis (git diff de 8 arquivos modificados, pipeline completo)

### Cadeia de Falhas Identificada

```
Migration não aplicada (params_hash_global)
  └→ Cache global quebrado
     └→ Toda busca = fresh API call
        └→ Busca leva >120s
           └→ Railway proxy timeout (524)
              └→ Worker killed (SIGABRT)
                 └→ SSE stream morre
                    └→ "Erro ao buscar licitações"

Redis instável (Railway addon)
  └→ ARQ worker crash loop
     └→ LLM summary + Excel falham
        └→ Resultado incompleto

Filtro agressivo para termos livres
  └→ 0 resultados + check verde
     └→ UX confusa → percepção de produto quebrado
```

---

## Squad Review Findings (2026-02-24)

### @architect — 2 RED, 3 YELLOW
- **RED GTM-STAB-003:** `validate_timeout_chain()` em `pncp_client.py:105-133` vai SOBRESCREVER novos valores com safe defaults. `DEGRADED_GLOBAL_TIMEOUT=360` em `consolidation.py:75` ignora env vars e derrota o propósito. 12+ tests hardcoded quebram. Gunicorn 120 = Railway 120 = zero margin.
- **RED GTM-STAB-004:** Filtragem per-UF é impossível hoje (filtro roda DEPOIS de coletar todas UFs). `partial_results` SSE event não existe no ProgressTracker. Two-phase pipeline é refactor major.
- **CRITICAL FINDING:** GTM-STAB-009 (async search) já está **80% implementado**. `SEARCH_ASYNC_ENABLED` flag existe, `search_job()` existe em `job_queue.py:404`, frontend já trata 202. Deveria ser P0, não P2.

### @qa — Regression Impact Matrix
- **175-253 test changes** no sprint total (130-185 novos + 45-68 updates)
- **GTM-STAB-003:** 12-15 tests quebram (hardcoded timeout values em `test_timeout_chain.py`)
- **GTM-STAB-004:** VERY HIGH risk (15-20 novos, 5-8 quebram)
- **GTM-STAB-009:** EXTREME risk se feito do zero, mas LOW risk se apenas habilitar flag existente
- **CRITICAL:** ARQ mock conflict — 3 shapes competindo em 3 test files. Precisa de conftest unificado.
- **CRITICAL:** STORY-267 DEVE ser commitado ANTES de STAB-005 (mesmos arquivos)

### @devops — 2 CRITICAL
- **CRITICAL:** `_get_redis_settings()` em `job_queue.py:54` NÃO seta `ssl=True` para `rediss://` scheme. Worker FALHA ao conectar no Upstash sem esse fix.
- **CRITICAL:** Worker service pode NÃO existir no Railway. Deve verificar com `railway service list`.
- **HIGH:** FK migration falha se existirem orphan user_ids em `search_results_cache` → verificar SQL antes.
- **HIGH:** `DEGRADED_GLOBAL_TIMEOUT=360` em `consolidation.py:181-189` sobrescreve timeout chain durante degradação.
- **MEDIUM:** Gunicorn timeout deve ser 115s (não 120) para ter 5s margin abaixo do Railway.

---

## Sequência de Execução REVISADA

### Fase 0: Prerequisitos (30min) — LIMPAR TERRENO

| # | Task | Esforço | Squad |
|---|------|---------|-------|
| 0a | ~~Commit STORY-267 com feature flags off~~ | 15min | @dev | ✅ b6d69c4 |
| 0b | Verificar `railway service list` — criar worker se não existir | 15min | @devops | ❓ pending |
| 0c | Verificar orphan user_ids em search_results_cache | 5min | @devops | ❓ pending |

**Gate 0:** STORY-267 commitado ✅. Worker service ❓. Orphan user_ids ❓.

### Fase 1: Infra Crítica (Dia 1) — DESBLOQUEIA TUDO

| # | Story | Esforço | Squad | Depende de |
|---|-------|---------|-------|------------|
| 1 | **GTM-STAB-001** Apply Missing Migrations | 1-2h | @devops + @qa | Gate 0 | Migration file committed (d233ab8), needs `supabase db push` |
| 2 | **GTM-STAB-002** Redis/ARQ Worker Stability | 3-4h | @devops + @dev | Gate 0 | ✅ Code shipped (899ee07) — ARQ retry, ssl, restart loop, cache warming |

**Atualizações pós-review:**
- STAB-001: Adicionar check de orphan user_ids ANTES de FK migration
- STAB-002: Adicionar `ssl=True` para `rediss://` scheme em `_get_redis_settings()`. Usar Upstash Pay-as-you-go (não free tier — limites de commands/dia). Não usar `exec` removal — Railway auto-restart é suficiente.

**Gate 1:** Cache funcional + Worker estável antes de prosseguir.

**Validação Gate 1:**
- [ ] Sentry CRIT-001 = 0 novos eventos
- [ ] Busca retorna cache hit na segunda tentativa
- [ ] ARQ worker sobrevive >1h sem crash
- [ ] `railway logs` sem Redis TimeoutError

### Fase 2: Async + Timeout + UX (Dias 2-3) — KILL THE ROOT CAUSE

| # | Story | Esforço | Squad | Depende de |
|---|-------|---------|-------|------------|
| 3 | **GTM-STAB-009** Enable Async Search (reclassificado P0) | 4-6h | @dev + @qa | Gate 1 | Not started — NEXT PRIORITY |
| 4 | **GTM-STAB-003** Timeout Chain Railway Fit (defense-in-depth) | 4-6h | @dev + @qa | Gate 1 | ✅ Code shipped (899ee07) — 110s pipeline, skip LLM/viab after budget |
| 5 | **GTM-STAB-005** Filter Zero Results UX | 6-8h | @ux + @dev + @qa | Gate 0 | ✅ Code shipped (899ee07) — filter_summary, auto-relaxation, FE empty state |

**Reordenamento crítico (@architect):** STAB-009 é a solução REAL (POST retorna em <1s, pipeline no worker sem timeout de proxy). STAB-003 vira defense-in-depth caso async falhe. STAB-009 é 80% pronto — habilitar flag + testar E2E + fix edge cases.

**Atualizações pós-review:**
- STAB-009: Reescrita como "Enable & Stabilize" (não "build from scratch"). Esforço cai de 12-16h para 4-6h.
- STAB-003: Adicionar ACs para `validate_timeout_chain()` update, `DEGRADED_GLOBAL_TIMEOUT` cap, Gunicorn 115s (não 120), `test_timeout_chain.py` full rewrite. Per-UF 45s (não 30s).
- STAB-005: Hard dependency em STORY-267 commitado (Fase 0a). Adicionar AC para `filter_stats` field em BuscaResponse.

**Gate 2:** Zero 524s + async funcional + UX educativa.

**Validação Gate 2:**
- [ ] 10 buscas consecutivas com 4 UFs = 0 erros 524
- [ ] POST /buscar retorna 202 em <1s (async mode)
- [ ] Resultado final chega via SSE/polling em <60s
- [ ] `SEARCH_ASYNC_ENABLED=false` rollback funciona em <60s
- [ ] Busca com termos livres que zera → empty state educativo
- [ ] UF timeout → "Sem oportunidades" amarelo (não verde com 0)

### Fase 3: SSE + Cache + Observability (Dias 3-4) — POLISH

| # | Story | Esforço | Squad | Depende de |
|---|-------|---------|-------|------------|
| 6 | **GTM-STAB-006** SSE Proxy Resilience | 6-8h | @dev + @ux + @qa | 003 | Not started |
| 7 | **GTM-STAB-007** Cache Warming | 4-6h | @dev + @data + @qa | 001, 002 | ✅ Code shipped (899ee07) — config + job impl |
| 8 | **GTM-STAB-008** Monitoring + Alertas | 4-6h | @devops + @dev | Gate 2 | ✅ Code shipped (899ee07) — GET /health endpoint |

**Atualizações pós-review:**
- STAB-006: SSE reconnection deve ser no `useSearchSSE.ts` hook customizado (NÃO native EventSource)
- STAB-007: Adicionar system user_id em profiles (UUID fixo) como sub-migration de STAB-001. Circuit breaker reset após infra fix.
- STAB-008: `/metrics` endpoint DEVE ter METRICS_TOKEN configurado antes de expor publicamente

**Gate 3:** SSE resiliente + buscas populares <2s + dashboard operacional.

### Fase 4: Progressive Delivery (Dia 5) — DE-SCOPED

| # | Story | Esforço | Squad | Depende de |
|---|-------|---------|-------|------------|
| 9 | **GTM-STAB-004** Never Lose Collected Data (de-scoped) | 4-6h | @dev + @qa | 003, 009 |

**De-scoping crítico (@architect + @qa):** A story original (progressive per-UF rendering + two-phase pipeline) é refactor major com risco VERY HIGH. O que importa para estabilização:
- **KEEP AC5:** "Nunca perder dados já coletados" — se consolidation timeout, retornar partial result
- **KEEP AC6:** "Nunca HTTP 5xx quando há dados" — se ≥1 UF retornou, retornar 200 partial
- **DEFER:** AC1 (partial_results SSE), AC2 (two-phase pipeline), AC3 (progressive rendering), AC4 (UF counts)
- Esforço cai de 8-12h para 4-6h. Risco cai de VERY HIGH para MEDIUM.

---

## Esforço Total REVISADO

| Fase | Stories | Esforço | Timeline |
|------|---------|---------|----------|
| Fase 0 | Prerequisites | 30min | Dia 1 (início) |
| Fase 1 | 001, 002 | 4-6h | Dia 1 |
| Fase 2 | 009, 003, 005 | 14-20h | Dias 2-3 |
| Fase 3 | 006, 007, 008 | 14-20h | Dias 3-4 |
| Fase 4 | 004 (de-scoped) | 4-6h | Dia 5 |
| **Total** | **9 stories** | **37-53h** | **5 dias** |

*Redução de 48-68h para 37-53h via de-scoping de STAB-004 e reclassificação de STAB-009*

---

## Critérios de Sucesso GTM

Após completar Fases 1-3 (mínimo para GTM):

| Métrica | Antes | Meta |
|---------|-------|------|
| Taxa de 524 | ~60% das buscas | <1% (async elimina) |
| Busca cached | N/A (cache quebrado) | <2s |
| Busca fresh | 60-120s (timeout) | <1s response + <60s resultado |
| Zero results | Check verde + 0 | Empty state educativo |
| Sentry unresolved | 11 issues | 0 issues |
| WORKER TIMEOUT | 4/semana | 0/semana (async elimina) |
| LLM summary delivery | ~50% (ARQ crash) | >95% |
| Redis uptime | Instável (crash loop) | >99.5% (Upstash) |

---

## Riscos REVISADOS (pós-review)

| Risco | Prob | Mitigação |
|-------|------|-----------|
| Upstash TLS: ssl=True missing | ALTA (bug existe hoje) | Fix code ANTES de mudar REDIS_URL |
| Worker service não existe | MÉDIA | Verificar Gate 0. Criar se necessário |
| FK migration falha (orphan user_ids) | MÉDIA | SQL check ANTES de migration |
| `DEGRADED_GLOBAL_TIMEOUT=360` overrides chain | ALTA | Cap degraded timeout em STAB-003 |
| `validate_timeout_chain()` safe defaults override | ALTA | Update function + safe defaults em STAB-003 |
| 12-15 timeout tests quebram | CERTA | Full rewrite de test_timeout_chain.py em STAB-003 |
| ARQ mock conflict (3 competing shapes) | ALTA | Unificar em conftest.py shared fixture |
| STORY-267 uncommitted conflicts com STAB-005 | CERTA | Gate 0: commit primeiro |
| Async search edge cases | MÉDIA | Feature flag rollback em <60s |
| Timeout reduction causa mais partial results | ALTA (esperado) | Partial > 524. Async é primary fix. |

---

## STORY-267 (Term Search Parity) — Status

O git diff mostra 375 linhas de mudanças em 8 arquivos para STORY-267 (paridade termos vs setores). Estas mudanças estão **não commitadas** e incluem:

- `config.py`: 4 feature flags (all default false)
- `filter.py`: term-aware LLM prompts, skip sector ceiling/proximity/co-occurrence
- `llm_arbiter.py`: `_build_term_search_prompt()` nova função
- `synonyms.py`: `find_term_synonym_matches()` cross-sector
- `viability.py`: generic value range for term searches
- `metrics.py`: 3 new term search metrics
- `schemas.py`: `match_relaxed` field
- `search_pipeline.py`: pass custom_terms through pipeline

**HARD GATE:** Commitar STORY-267 separadamente (feature flags off) ANTES de iniciar qualquer GTM-STAB story. Fase 0, Task 0a.

---

## Deployment Sequence (@devops)

### Env Var Changes (todas as fases)

| Service | Variable | Story | Action | Value |
|---------|----------|-------|--------|-------|
| bidiq-backend | `REDIS_URL` | 002 | UPDATE | `rediss://default:xxx@xxx.upstash.io:6379` |
| bidiq-worker | `REDIS_URL` | 002 | UPDATE | Same Upstash URL |
| bidiq-backend | `GUNICORN_TIMEOUT` | 003 | SET | `115` |
| bidiq-backend | `GUNICORN_GRACEFUL_TIMEOUT` | 003 | SET | `30` |
| bidiq-backend | `CACHE_WARMING_ENABLED` | 007 | SET | `true` |
| bidiq-backend | `METRICS_TOKEN` | 008 | SET | (generate secure token) |
| bidiq-backend | `SEARCH_ASYNC_ENABLED` | 009 | SET | `true` (when ready) |

### Deploy Order

1. Database migrations (Supabase CLI) — antes de tudo
2. Backend (web) — novas APIs devem estar live antes do frontend
3. Worker — pode atrasar sem impacto (ARQ roda jobs com código antigo)
4. Frontend — consome APIs que já devem existir

### Rollback Levers

- `SEARCH_ASYNC_ENABLED=false` → rollback async em <60s (feature flag cache)
- `CACHE_WARMING_ENABLED=false` → desliga warming instantaneamente
- `REDIS_URL` revert → volta para Railway Redis addon (se não removido)
- `GUNICORN_TIMEOUT=180` → volta timeout antigo sem redeploy

---

## E2E Production Validation (2026-02-25)

### Test 1: Sector search — Vestuário, 4 UFs (ES, MG, RJ, SP)
- **Result:** Pipeline completed ~120s, no 524 error
- **UF Status:** All 4 UFs showed "Indisponível" (PNCP likely rate-limiting)
- **Filter Stats:** "132 licitações encontradas nas fontes oficiais, mas nenhuma corresponde ao setor"
- **Empty State:** "Verificar setor" action button shown
- **Async:** search_job() confirmed via Railway logs (STAB-009 working)

### Test 2: Terms search — "calibração de equipamentos metrológicos industriais especializados"
- **Result:** 10 results from 132 analyzed in ~3s (cache hit from previous session)
- **Auto-relaxation:** Working (specific terms → broad results via level 3)
- **Filter Stats:** "10 oportunidades selecionadas de 132 analisadas"
- **SSE:** Initial connection fails, reconnection succeeds (consistent pattern)

### Health Endpoint
- Redis: UP (2ms), Supabase: UP (272ms), ARQ Worker: UP, PNCP: UP

### Bugs Found During Validation
1. **Error alert persists alongside results** — "Não foi possível obter os resultados" shown alongside 10 results
2. **AI summary uses sector name for terms search** — "licitações de Vestuário e Uniformes" even on terms mode
3. **Negative days in urgency** — "encerra em -21 dia(s)" for expired bids still displayed
4. **SSE initial connection always fails** — Every search shows SSE failure then reconnection success

### Test Results (Automated)
- Backend: 933/933 pass, 5 skip, 0 fail
- Frontend: 335/336 pass, 1 fail (fixed: useSearchSSE sseAvailable reset)
- New tests: test_stab005_auto_relaxation.py (8 tests, pass)
