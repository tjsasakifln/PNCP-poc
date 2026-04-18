# STORY-CIG-BE-cache-redis-cascade — Enum L1/L2/L3 mudou (REDIS vs LOCAL vs MISS) — 21 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suítes de cache rodam em `backend-tests.yml` e falham em **21 testes** do triage row #8/30 (ver `backend-failure-triage.md`). Causa raiz classificada pelo triage como **mock-drift / assertion-drift**: as enums semânticas do cascade de cache (InMemory L1 + Supabase L2 + search_results_cache L3) mudaram entre `REDIS`, `LOCAL`, `MISS` e os testes ainda asseguram os nomes antigos.

A arquitetura de cache é documentada no CLAUDE.md (Layer 3: SWR, 4h L1 / 24h L2). Esta story não revisita a arquitetura — só realinha os testes à nomenclatura real produção.

**Arquivos principais afetados:**
- `backend/tests/test_search_cache.py`
- `backend/tests/test_cache_correctness.py`
- `backend/tests/test_cache_multi_level.py`
- `backend/tests/test_cache_multilevel_integration.py`
- `backend/tests/test_cache_global_warmup.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Assertion-drift + mock-drift combinados. Os testes importam `CacheLevel.REDIS` / `CacheLevel.LOCAL` mas a enum atual pode ter consolidado em `CacheLevel.L1/L2/L3` ou movido para módulo diferente. Validar via `grep -rn "class CacheLevel\\|CacheLevel\\." backend/`. Patching alvo documentado em CLAUDE.md (`supabase_client.get_supabase`, não `search_cache.get_supabase`) deve ser respeitado.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_search_cache.py backend/tests/test_cache_correctness.py backend/tests/test_cache_multi_level.py backend/tests/test_cache_multilevel_integration.py backend/tests/test_cache_global_warmup.py -v` retorna exit code 0 localmente (21+/21+ PASS, 0 skipped introduzidos).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 5 suítes acima com **0 failed / 0 errored**. Link para run ID no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift / assertion-drift). Listar símbolos renomeados (antes → depois) em tabela.
- [ ] AC4: Cobertura backend **não caiu** vs. último run verde conhecido (diff `coverage-summary.json` no Change Log). Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): `grep -nE "@pytest\\.mark\\.skip|pytest\\.skip\\(|@pytest\\.mark\\.xfail|\\.only\\("` vazio em todos os arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 5 suítes isoladas e capturar mensagens de erro reais (mock path, assertion expected vs received).
- [ ] Classificar categoria real por arquivo: (a) mock-drift, (b) assertion-drift, (c) import.
- [ ] Mapear enum antes→depois: buscar com `grep -rn "CacheLevel\\|CacheSource" backend/`.
- [ ] Confirmar que patching alvo segue padrão CLAUDE.md (`supabase_client.get_supabase`).
- [ ] Se mudança em produção for recente e não intencional: escalar para @architect — possível regressão de feature flag.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #8/30)

## Stories relacionadas no epic

- STORY-CIG-BE-cache-warming-dispatch (mesmo módulo cache, outro drift)
- STORY-CIG-BE-admin-cache-metrics (admin view do mesmo sistema)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #8/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
