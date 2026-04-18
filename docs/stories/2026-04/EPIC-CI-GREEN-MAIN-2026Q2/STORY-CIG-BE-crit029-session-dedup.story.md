# STORY-CIG-BE-crit029-session-dedup — Session dedup logic bypass (sem `.filter()`) — 8 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate (possível regressão de dedup)
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_crit029_session_dedup.py` roda em `backend-tests.yml` e falha em **8 testes** do triage row #13/30. Causa raiz classificada como **assertion-drift**: a lógica de dedup de session bypass perdeu uma chamada `.filter()` em algum ponto da query. Os testes esperam que sessões duplicadas sejam filtradas, mas o código atual retorna duplicatas.

CRIT-029 é fix histórico de duplicação; regressão aqui tem impacto direto em UX de histórico de buscas.

**Arquivos principais afetados:**
- `backend/tests/test_crit029_session_dedup.py` (8 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Possível **prod-bug real** — refactor pode ter acidentalmente removido `.filter()` na query Supabase. Validar com `git log -p backend/routes/sessions.py` e comparar contra versão antiga que passava.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_crit029_session_dedup.py -v` retorna exit code 0 localmente (8/8 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" distinguindo (a) assertion-drift benigna vs (b) prod-bug real (regressão CRIT-029). Se (b), adicionar teste de regressão.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_crit029_session_dedup.py -v` isolado.
- [ ] `git log -p --follow backend/routes/sessions.py backend/session_manager.py` — identificar quando `.filter()` sumiu (se sumiu).
- [ ] Se (b) prod-bug: abrir issue P1, marcar `Status: Blocked` até decisão @po.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #13/30)

## Stories relacionadas no epic

- STORY-CIG-BE-sessions-ensure-profile (#12 — mesma área sessions)
- STORY-CIG-BE-story-drift-search-session-lifecycle (#26 — mesma área)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #13/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. **Atenção @po:** investigar prod-bug (regressão CRIT-029) vs assertion-drift.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. Prod-bug hipótese documentada com escalation path (`Status: Blocked` se confirmado). Se @dev classificar (b) regressão CRIT-029, abrir issue P1 e escalar para @po.
