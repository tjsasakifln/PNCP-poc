# GTM-STAB-007 — Cache Warming para Buscas Populares

> **⚠️ SUPERSEDED 2026-04-18** — Layer 3 cache warming proativo removido. DataLake Supabase (~50K bids + 2M+ contratos) é fonte de consulta primária com latência <100ms; pré-população virou overhead puro. Ver `STORY-CIG-BE-cache-warming-deprecate` em `docs/stories/2026-04/EPIC-CI-GREEN-MAIN-2026Q2/`. Código/testes/flags removidos no branch `fix/cig-be-wave2-tier1-plus-tier2`. Cache passivo + SWR por-request permanecem.

**Status:** SUPERSEDED (originalmente Code Complete)
**Priority:** P1 — High (transforma busca de 60-120s em <2s)
**Severity:** Performance — sem cache, toda busca é fresh API call
**Created:** 2026-02-24
**Sprint:** GTM Stabilization
**Relates to:** GTM-STAB-001 (migrations), GTM-RESILIENCE-B01 (SWR background refresh), GTM-RESILIENCE-B02 (hot/warm/cold)

---

## Problema

Com o cache quebrado (GTM-STAB-001), toda busca vai direto para PNCP/PCP/ComprasGov. Mesmo após fix do cache, a **primeira busca de cada combinação** setor+UFs+período ainda será lenta (30-90s).

Para experiência enterprise, as buscas mais comuns devem ser **instantâneas** (<2s).

### Padrão de buscas esperado:

- 15 setores × 27 UFs × 1 período = ~400 combinações possíveis
- Na prática: ~80% das buscas concentram em ~30 combinações (top setores + top UFs)
- Top 5 setores: vestuario, informatica, engenharia, saude, facilities
- Top 5 UFs: SP, MG, RJ, BA, RS
- Período: default 10 dias (fixo)

### Benefício:

- Busca cached: **<2s** (Supabase read + InMemory hit)
- Busca fresh: **30-90s** (PNCP + filtro + LLM)
- Cache warming: transformar 80% das buscas em cached

---

## Acceptance Criteria

### AC1: Cron job de cache warming
- [x] `cache_warming_job()` in job_queue.py (lines 729-830) ✅ (commit `899ee07`)
- [x] Executa a cada 4h via ARQ cron ✅ (cron_jobs.py:44-52)
- [ ] Lista de combinações a aquecer:
  ```python
  WARM_COMBINATIONS = [
      # Top 5 setores × Top 10 UFs = 50 combinações
      {"setor": "vestuario", "ufs": ["SP"]},
      {"setor": "vestuario", "ufs": ["MG"]},
      {"setor": "vestuario", "ufs": ["RJ"]},
      # ... etc
  ]
  ```
- [x] Cada combinação = busca completa ✅
- [x] Rate limiting: max 2 simultâneas, delay between ✅
- [x] Top 50 combinações ✅ (job_queue.py:778)

### AC2: Smart warming baseado em analytics
- [x] Queries `search_sessions` for top combinations dynamically ✅ (job_queue.py:757-778)
- [x] Sorts by frequency, takes top 50 ✅
- [x] Data-driven, not hardcoded ✅

### AC3: Warming com budget de tempo
- [x] Budget: `CACHE_WARMING_BUDGET_MINUTES * 60` (default 30min) ✅ (job_queue.py:752)
- [x] Checks elapsed vs budget: `if time.monotonic() - start > budget_s: break` ✅ (line 786-788)
- [x] Structured log: `cache_warming_cycle` with duration_ms, warmed count ✅ (line 668)

### AC4: Não interferir com buscas de usuário
- [x] Warming jobs usam prioridade BAIXA — ✅ `WARMING_BATCH_DELAY_S=3.0` between each request, sequential (not parallel)
- [x] Se busca de usuário em andamento, pausar warming — ✅ `_warming_wait_for_idle()` checks `ACTIVE_SEARCHES` gauge, 3 pause cycles × 10s
- [x] Circuit breaker: se PNCP rate-limited durante warming, parar imediatamente — ✅ checks `is_degraded` + 429 detection stops warming entirely
- [x] User_id para warming: `WARMING_USER_ID = "00000000-0000-0000-0000-000000000000"` ✅

### AC5: Startup warming (cold start)
- [x] `warmup_top_params()` in cron_jobs.py (lines 195-239) ✅
- [x] Queries top 10 popular params, enqueues background revalidation ✅
- [x] Non-blocking: `asyncio.create_task()` ✅ (line 296)
- [x] Covers redeploy scenarios ✅

### AC6: Testes
- [x] Backend: test cache_warming_job executa e salva cache para N combinações — ✅ `test_cache_warming_noninterference.py`
- [x] Backend: test smart warming query retorna top combinações por frequência ✅
- [x] Backend: test budget timeout para warming em 30min ✅
- [x] Backend: test warming pausa quando busca de usuário ativa ✅ (8 tests total)

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `backend/job_queue.py` | AC1: cache_warming_job function |
| `backend/cron_jobs.py` | AC1+AC5: scheduling + startup warming |
| `backend/search_cache.py` | AC2: query popular combinations |
| `backend/config.py` | AC1: CACHE_WARMING_ENABLED, CACHE_WARMING_INTERVAL, CACHE_WARMING_CONCURRENCY |
| `backend/metrics.py` | AC3: warming metrics |

---

## Decisões Técnicas

- **ARQ job > asyncio.create_task** — Warming é heavy (50 API calls). Deve rodar no worker process, não no web process.
- **4h interval** — Alinhado com InMemory TTL. Cache aquecido a cada 4h garante que nunca expira antes do próximo aquecimento.
- **Smart warming** — Lista estática funciona no MVP, mas analytics-driven escala melhor quando mais usuários entram.
- **System user_id** — Warming cache precisa de user_id para salvar. Usar UUID fixo de "system" e garantir que profiles tem esse UUID.

## Estimativa
- **Esforço:** 4-6h
- **Risco:** Baixo (job isolado, não afeta pipeline)
- **Squad:** @dev (cron + warming job) + @data-engineer (smart query) + @qa (validation)
