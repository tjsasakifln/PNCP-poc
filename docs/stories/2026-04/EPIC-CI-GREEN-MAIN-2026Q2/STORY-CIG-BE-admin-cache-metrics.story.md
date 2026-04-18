# STORY-CIG-BE-admin-cache-metrics — Admin cache metrics retornam zero (source moved) — 3 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P2 — Gate
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_admin_cache.py` roda em `backend-tests.yml` e falha em **3 testes** do triage row #15/30. Causa raiz classificada como **mock-drift**: a fonte dos metrics do endpoint `/admin/cache` moveu (provavelmente de `search_cache.METRICS_CACHE_HITS` para outro módulo), fazendo a view retornar zero.

**Arquivos principais afetados:**
- `backend/tests/test_admin_cache.py` (3 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Métricas Prometheus foram centralizadas em `backend/metrics.py`; admin endpoint continua lendo de `search_cache.*` que está vazio. Validar com `grep -rn "METRICS_CACHE\\|cache_hits\\|cache_metrics" backend/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_admin_cache.py -v` retorna exit code 0 localmente (3/3 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift). Path antes→depois das métricas.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_admin_cache.py -v` isolado.
- [ ] Mapear onde os métricos vivem agora.
- [ ] Decidir: atualizar endpoint admin para nova source OU atualizar testes/mocks.
- [ ] Preferir corrigir endpoint se produção realmente retornar zero (prod-bug).
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #15/30)

## Stories relacionadas no epic

- STORY-CIG-BE-cache-redis-cascade (#8 — mesma área cache)
- STORY-CIG-BE-cache-warming-dispatch (#9 — mesma área cache)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #15/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
