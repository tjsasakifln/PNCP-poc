# STORY-CIG-BE-story-drift-search-session-lifecycle — Register/update session + ux351 dedup + arq search persist — 7 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P2 — Gate (depende de story foundation)
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suítes que cobrem o ciclo de vida completo de search sessions rodam em `backend-tests.yml` e falham em **7 testes** do triage row #26/30. Classificação pelo triage: **mock-drift** combinado com **assertion-drift** — três arquivos cobrem três aspectos do mesmo fluxo (register/update, dedup ux351, persist via ARQ).

Esta story **depende de STORY-CIG-BE-sessions-ensure-profile (#12/30)**: o fix do profile-ensure muda o contrato interno de `save_search_session` e afeta os mocks destes 7 testes. Abrir após #12 em `InReview` ou `Done`.

**Arquivos principais afetados:**
- `backend/tests/test_search_session_lifecycle.py`
- `backend/tests/test_ux351_session_dedup.py`
- `backend/tests/test_story363_arq_search.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Três fluxos (register/update, dedup, persist) compartilham mocks em `backend/session_manager.py` ou similar. Drift recente alterou assinaturas. Validar com `grep -rn "register_search_session\\|update_search_session\\|arq.*search" backend/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_search_session_lifecycle.py backend/tests/test_ux351_session_dedup.py backend/tests/test_story363_arq_search.py -v` retorna exit code 0 localmente (7/7 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 3 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis". Listar separadamente os 3 fluxos (register/update vs dedup vs ARQ persist) e indicar se fix é uniforme ou heterogêneo.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados. Mocks de ARQ devem seguir o padrão de conftest autouse `_isolate_arq_module` (CLAUDE.md).

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Confirmar que STORY-CIG-BE-sessions-ensure-profile (#12) está `Done` ou `InReview` antes de começar.
- [ ] Rodar as 3 suítes isoladas e capturar erros (expected vs received).
- [ ] Mapear quais dos 3 fluxos são mock-drift puro vs assertion-drift vs ambos.
- [ ] Validar que mocks de ARQ respeitam `_isolate_arq_module` conforme CLAUDE.md (não fazer `sys.modules["arq"] = MagicMock()` sem cleanup).
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #26/30)
- **Bloqueada por:** STORY-CIG-BE-sessions-ensure-profile (#12/30) — deve estar `Done` ou `InReview`.

## Stories relacionadas no epic

- STORY-CIG-BE-sessions-ensure-profile (#12 — bloqueia esta)
- STORY-CIG-BE-crit029-session-dedup (#13 — mesma área sessions)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #26/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. Dep de #12 explicitamente documentada.
