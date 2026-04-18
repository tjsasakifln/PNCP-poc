# STORY-CIG-BE-sessions-ensure-profile — `_ensure_profile_exists` não chamado em `save_search_session` — 7 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_sessions.py` roda em `backend-tests.yml` e falha em **7 testes** do triage row #12/30. Causa raiz classificada pelo triage como **mock-drift**: `save_search_session()` não invoca mais `_ensure_profile_exists()` — os testes assertam essa chamada via mock spy.

Duas hipóteses em Implement:

1. **Assertion-drift:** `_ensure_profile_exists` foi movido para middleware/interceptor upstream (auth layer já garante profile). Testes precisam ser atualizados.
2. **Bug real:** FK constraint a `profiles.id` pode falhar quando nova sessão é criada para user recém-onboardado. Validar em staging.

**Esta story desbloqueia stories downstream:**
- STORY-CIG-BE-story-drift-search-session-lifecycle (#26/30, depende desta)

**Arquivos principais afetados:**
- `backend/tests/test_sessions.py` (7 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Provavelmente (1) mock-drift após refatoração que moveu `_ensure_profile_exists` para `auth.py` ou middleware de rota. Confirmar via `grep -rn "_ensure_profile_exists\\|def save_search_session" backend/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_sessions.py -v` retorna exit code 0 localmente (7/7 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra `test_sessions.py` com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" distinguindo (1) mock-drift vs (2) prod-bug FK constraint.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): `grep -nE "@pytest\\.mark\\.skip|pytest\\.skip\\(|@pytest\\.mark\\.xfail|\\.only\\("` vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_sessions.py -v` isolado e capturar falhas.
- [ ] `grep -rn "_ensure_profile_exists\\|def save_search_session" backend/` — identificar onde a lógica de profile-ensure vive atualmente.
- [ ] Validar que OAuth flow (routes/auth_oauth.py) ou signup flow garante profile existência upstream.
- [ ] Se (2) bug FK real: abrir issue P1, marcar `Status: Blocked` até decisão @po.
- [ ] Se (1) drift: atualizar mock spies para bater o novo entry point.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #12/30)
- **Bloqueia:** STORY-CIG-BE-story-drift-search-session-lifecycle (#26/30)

## Stories relacionadas no epic

- STORY-CIG-BE-story-drift-search-session-lifecycle (#26 — dep)
- STORY-CIG-BE-crit029-session-dedup (#13 — mesma área sessions)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #12/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
