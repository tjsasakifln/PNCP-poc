# STORY-CIG-BE-alerts-endpoint-404 — Rotas de alerts 404 (POST/GET/PATCH/DELETE) — 13 testes route-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suítes `test_alerts.py` e `test_alert_matcher.py` rodam em `backend-tests.yml` e falham em **13 testes** do triage row #5/30. Causa raiz classificada como **route-drift**: todos os verbos REST (POST/GET/PATCH/DELETE) nas rotas de alerts retornam 404 em TestClient. Possivelmente movidas para `/v1/alerts` ou `/pipeline/alerts` (CLAUDE.md route map mostra `GET /pipeline/alerts`).

**Arquivos principais afetados:**
- `backend/tests/test_alerts.py`
- `backend/tests/test_alert_matcher.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Refactor de `routes/alerts.py` → `routes/pipeline/alerts.py` (ou package) mudou prefix. Validar com `grep -rn "@router.*alert" backend/routes/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_alerts.py backend/tests/test_alert_matcher.py -v` retorna exit code 0 localmente (13/13 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (route-drift). Tabela antes→depois.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 2 suítes isoladas.
- [ ] `grep -rn "@router.*alert\\|/alerts\\|/v1/alerts" backend/routes/ backend/main.py`.
- [ ] Validar que frontend (`frontend/app/api/` proxies) não quebra com a decisão tomada.
- [ ] Atualizar testes para novo path OU adicionar alias de backward-compat.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #5/30)

## Stories relacionadas no epic

- STORY-CIG-BE-buscar-route-404 (#6 — mesmo padrão de route drift)
- STORY-CIG-BE-story364-excel-lifecycle (#4 — mesmo padrão de route drift)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #5/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
