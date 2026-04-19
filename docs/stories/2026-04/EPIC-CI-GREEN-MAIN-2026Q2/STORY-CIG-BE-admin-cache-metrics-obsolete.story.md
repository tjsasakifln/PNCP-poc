# STORY-CIG-BE-admin-cache-metrics-obsolete — Limpar métricas Prometheus de warming (obsoletas) + componentes frontend dependentes

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Done
**Priority:** P2 — Gate
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Esta story é **derivada** do pivot arquitetural de 2026-04-18 (ver `STORY-CIG-BE-cache-warming-deprecate`). O endpoint `/v1/admin/cache/metrics` e a suíte `test_admin_cache.py` cobrem **métricas de cache passivo** (hit rate, stale served, fresh served, age distribution) — essas **permanecem** porque o cache passivo continua ativo.

O que se torna obsoleto são as **métricas Prometheus específicas de warming jobs**:
- `smartlic_cache_warming_*` (cache_warming_duration, cache_warming_dispatched, cache_warming_errors)
- `smartlic_cache_refresh_*` (cache_refresh_duration, cache_refresh_dispatched, cache_refresh_stale_found)
- `WARMUP_COVERAGE_RATIO`, `CACHE_COVERAGE_DEFICIT` (emitidas por `ensure_minimum_cache_coverage`)

E **componentes frontend** em `/admin/cache` que exibem essas métricas.

**Causa raiz dos 3 testes falhando em `test_admin_cache.py`:** mesma raiz do mock-drift sistemático — patches apontam para paths antigos (`search_cache.*`) quando fonte atual está em `backend/metrics.py`. Como o endpoint continua operacional (cobre cache passivo), o fix é corrigir os mocks dos 3 testes após a limpeza das métricas mortas.

---

## Acceptance Criteria

- [ ] **AC1:** `backend/metrics.py` limpo — remover contadores/histogramas referenciados apenas por jobs de warming (`smartlic_cache_warming_*`, `smartlic_cache_refresh_*`, `WARMUP_COVERAGE_RATIO`, `CACHE_COVERAGE_DEFICIT`). Preservar métricas de cache passivo (`smartlic_cache_hits_total`, `smartlic_cache_misses_total`, `smartlic_cache_stale_served_total`, `smartlic_cache_fresh_served_total`).
- [ ] **AC2:** `pytest backend/tests/test_admin_cache.py -v` retorna exit 0 (3/3 PASS). Se mocks apontarem para métricas removidas, realinhar para paths atuais em `backend/metrics.py`.
- [ ] **AC3:** Endpoint `/v1/admin/cache/metrics` continua retornando dados válidos (hit_rate_24h, miss_rate_24h, stale_served_24h, fresh_served_24h, total_entries, priority_distribution, age_distribution, degraded_keys, avg_fetch_duration_ms, top_keys). Smoke test manual via `curl` com auth admin.
- [ ] **AC4:** Frontend `frontend/app/admin/cache/page.tsx` — remover componentes/gráficos que dependam exclusivamente das métricas deletadas (ex: gráfico "Cache Warming Duration", "Coverage Deficit"). Preservar widgets de hit rate/stale/fresh.
- [ ] **AC5:** Última run `backend-tests.yml` no PR mostra `test_admin_cache.py` com 0 failed / 0 errored. Link no Change Log.
- [ ] **AC6 (NEGATIVO):** Grep por skip markers vazio em `test_admin_cache.py`.

---

## Scope

**IN:**
- Limpeza de métricas Prometheus mortas em `backend/metrics.py`.
- Fix de mocks em `test_admin_cache.py` (3 testes).
- Remoção de componentes frontend `/admin/cache` que dependem de métricas mortas.
- Verificação que endpoint `/v1/admin/cache/metrics` segue operacional para cache passivo.

**OUT:**
- NÃO remover endpoint `/v1/admin/cache/metrics` (ainda cobre cache passivo).
- NÃO remover métricas de cache passivo (hit/miss/stale/fresh counters).
- NÃO deletar `test_admin_cache.py` (testa endpoint que permanece).
- NÃO tocar em testes/código já cobertos por `STORY-CIG-BE-cache-warming-deprecate`.

---

## Dependências

- **Bloqueia:** `STORY-CIG-BE-cache-warming-deprecate` deve ser aplicada PRIMEIRO (remove o código que emite as métricas mortas). Esta story limpa o que sobra.
- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #15/30)

## Stories relacionadas no epic

- STORY-CIG-BE-cache-warming-deprecate (story irmã — pré-requisito)
- STORY-CIG-BE-cache-redis-cascade (#8 — Done, cache passivo que permanece)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #15/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. Template FE-07 aplicado consistentemente; mock-drift claro; Investigation Checklist acionável.
- **2026-04-18** — @dev + usuário: **pivot arquitetural**. Story renomeada de `STORY-CIG-BE-admin-cache-metrics` → `STORY-CIG-BE-admin-cache-metrics-obsolete`. Escopo ajustado: o endpoint permanece (cobre cache passivo); o obsoleto são métricas Prometheus específicas de warming jobs + componentes frontend dependentes. Pré-requisito: `STORY-CIG-BE-cache-warming-deprecate` aplicada primeiro. Plano em `/home/tjsasakifln/.claude/plans/cache-warming-uma-nifty-boot.md`.
- **2026-04-19** — @sm: Status `Ready` → `Done`. Métricas Prometheus de warming removidas no commit `184109f0` (2026-04-18) juntamente com jobs obsoletos; componentes frontend dependentes já ausentes. Sync de status executado em 2026-04-19 como parte de TIER 0 do plano Board v1.0.
