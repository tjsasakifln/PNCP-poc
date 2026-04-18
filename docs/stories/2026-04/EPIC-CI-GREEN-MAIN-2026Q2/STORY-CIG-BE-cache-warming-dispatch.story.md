# STORY-CIG-BE-cache-warming-dispatch — Mocks de decorator/import target drift em loop de warming — 15 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suítes que cobrem cache warming rodam em `backend-tests.yml` e falham em **15 testes** do triage row #9/30. Causa raiz classificada como **mock-drift**: o loop de warming de cache (global warmup + adaptive warmup CRIT-055) usa decorators/import targets diferentes dos que os testes patcham. Alguns testes também cobrem `harden018_cache_dir_maxsize` (limite de dir cache).

**Arquivos principais afetados:**
- `backend/tests/test_cache_warming_noninterference.py`
- `backend/tests/test_harden018_cache_dir_maxsize.py`
- `backend/tests/test_cache_refresh.py`
- `backend/tests/test_crit055_warmup_adaptive.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Decorators como `@cache_warmup_scheduled` foram renomeados ou o entry point foi movido de `cache_warmup.py` para módulo ARQ. Validar com `grep -rn "cache_warmup\\|warmup_adaptive\\|refresh_cache" backend/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_cache_warming_noninterference.py backend/tests/test_harden018_cache_dir_maxsize.py backend/tests/test_cache_refresh.py backend/tests/test_crit055_warmup_adaptive.py -v` retorna exit code 0 localmente (15/15 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 4 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift). Tabela antes→depois dos decorators/paths.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 4 suítes isoladas.
- [ ] `grep -rn "cache_warmup\\|warmup_adaptive\\|refresh_cache\\|@cache_" backend/`.
- [ ] Validar mocks de ARQ seguem `_isolate_arq_module` (CLAUDE.md).
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #9/30)

## Stories relacionadas no epic

- STORY-CIG-BE-cache-redis-cascade (#8 — mesma área cache)
- STORY-CIG-BE-admin-cache-metrics (#15 — admin view do mesmo sistema)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #9/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
