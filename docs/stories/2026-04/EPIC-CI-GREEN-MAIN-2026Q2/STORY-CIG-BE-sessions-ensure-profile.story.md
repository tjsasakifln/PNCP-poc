# STORY-CIG-BE-sessions-ensure-profile — `_ensure_profile_exists` não chamado em `save_search_session` — 7 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
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

- [x] AC1: `pytest backend/tests/test_sessions.py -v` retorna exit code 0 localmente (11/11 PASS, inclui os 7 anteriormente quebrados). **Evidence:** `11 passed in 3.77s` — ver Change Log 2026-04-18 entry @dev.
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra `test_sessions.py` com **0 failed / 0 errored**. Link no Change Log. *(pendente pós-push @devops)*
- [x] AC3: Causa raiz descrita em "Root Cause Analysis" distinguindo (1) mock-drift vs (2) prod-bug FK constraint. Confirmado (1) mock-drift — ver RCA abaixo.
- [x] AC4: Cobertura backend **não caiu**. Apenas alteração de strings `@patch(...)` em arquivo de teste — sem impacto em cobertura de prod.
- [x] AC5 (NEGATIVO): `grep -nE "@pytest\\.mark\\.skip|pytest\\.skip\\(|@pytest\\.mark\\.xfail|\\.only\\("` vazio em `backend/tests/test_sessions.py` (exit 1 = no match).

---

## Root Cause Analysis

**Categoria confirmada:** (1) **Mock-drift pós DEBT-07 package split** — NÃO é prod-bug FK constraint.

**Mecanismo do drift:**
1. `save_search_session()` em `backend/quota/session_tracker.py:275-300` faz **import lazy local** (dentro do corpo da função):
   ```python
   from quota.plan_enforcement import _ensure_profile_exists
   ```
2. Como o `import` resolve a referência direto em `quota.plan_enforcement`, o bind local do nome `_ensure_profile_exists` dentro do scope de `save_search_session` aponta para `quota.plan_enforcement._ensure_profile_exists`, **não** para `quota._ensure_profile_exists` (que é apenas reexport em `quota/__init__.py:51,101`).
3. Os 7 testes usavam `@patch("quota._ensure_profile_exists")` — mas `unittest.mock.patch` substitui o attribute **no módulo alvo**, e o código de produção nunca olha `quota._ensure_profile_exists`. Resultado: o mock "funcionava" (sem erro de patch), mas a função real rodava, tentava `len(Mock)` no supabase mock e falhava com `object of type 'Mock' has no len()`, retornando `False` — daí os logs `Cannot save session: profile missing for user ...` em todos os 7 testes.

**Padrão idêntico ao da STORY-CIG-BE-crit029-session-dedup (Batch B, commit `c632a56d`)** — mesma área `quota/session_tracker.py`, mesma função alvo, mesma correção: mover patches de `quota.X` → `quota.plan_enforcement.X`.

**Validação de ausência de prod-bug:**
- Produção usa import direto de `quota.plan_enforcement._ensure_profile_exists` (linha 294) — não há FK constraint violation possível via este path.
- `_ensure_profile_exists` existe intacto em `backend/quota/plan_enforcement.py:456`.
- Nenhuma mudança em código de produção foi necessária.

**Fix aplicado:** 7 ocorrências de `@patch("quota._ensure_profile_exists")` → `@patch("quota.plan_enforcement._ensure_profile_exists")`.

---

## File List

- `backend/tests/test_sessions.py` — 7 patch paths atualizados (linhas 156, 191, 222, 258, 343, 388, 428)

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
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (8/10)** — Draft → Ready. **Wave 1 foundation** — bloqueia #26. Se @dev confirmar (2) FK constraint bug, escalar para @po; caso contrário (1) mock-drift, fix direto.
- **2026-04-18** — @dev (Dex): Implement → **RCA conclusivo: (1) mock-drift**. Aplicado fix em 7 patch-paths `quota._ensure_profile_exists` → `quota.plan_enforcement._ensure_profile_exists` em `backend/tests/test_sessions.py`. Mesmo padrão do commit `c632a56d` (Batch B crit029). Teste local: `11 passed in 3.77s` (4 previously passing + 7 previously failing, agora todos PASS). Sem mudança em prod code. AC5 negativo: 0 skip/xfail markers. Status Ready → InReview.
