# STORY-CIG-BE-crit029-session-dedup — Session dedup logic bypass (sem `.filter()`) — 8 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
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

- [x] AC1: `pytest backend/tests/test_crit029_session_dedup.py -v` retorna exit code 0 localmente (12/12 PASS — 8 antes falhavam + 4 já passavam).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log. *(a validar em CI após push)*
- [x] AC3: Causa raiz descrita em "Root Cause Analysis" — classificação **(a) assertion-drift benigna**. Prod-bug CRIT-029 NÃO regrediu; o fix histórico `.filter()` com PG array literals (`{val1,val2}`) segue intacto em `backend/quota/session_tracker.py:72-73`.
- [x] AC4: Cobertura backend não afetada — edit é test-only, sem toque em prod.
- [x] AC5 (NEGATIVO): grep por `@pytest.mark.skip|pytest.skip\(|@pytest.mark.xfail|\.only\(` vazio em `backend/tests/test_crit029_session_dedup.py`.

---

## Investigation Checklist (para @dev, fase Implement)

- [x] Rodar `pytest backend/tests/test_crit029_session_dedup.py -v` isolado → baseline 8 failed / 4 passed.
- [x] `git log -p --follow backend/quota/session_tracker.py` + `git show d46e812348c4c22bba15c426dad5c2397b09e56b` + `git show fa42e0c82bbcc1d4f55b0ba74be5b237fd14096e` — identificada origem do drift (DEBT-07 package split).
- [x] Classificado **(a) assertion-drift**. Não há prod-bug; `.filter()` com PG array literal está presente e correto. Nenhuma issue P1 necessária.
- [x] Cobertura não regrediu (mudança test-only).
- [x] Grep de skip markers vazio.

---

## Root Cause Analysis — (a) assertion-drift benigna

**Classificação:** (a) assertion-drift (test-stale). **NÃO é regressão CRIT-029.**

### Contexto histórico
- **CRIT-029 original fix** (commit `d46e8123`, Fev 2026): `register_search_session` vivia em `backend/quota.py` (arquivo único, 1660 LOC). O fix trocou `.eq("sectors", list)` → `.filter("sectors", "eq", "{val1,val2}")` com PG array literals e sorted arrays no INSERT. Testes introduziram o pattern `FluidMock` e `@patch("quota._ensure_profile_exists", return_value=True)`.
- **DEBT-07 package split** (commit `fa42e0c8`, Abr 2026): `quota.py` foi decomposto em `quota/{quota_core, quota_atomic, plan_enforcement, plan_auth, session_tracker}.py`. `_ensure_profile_exists` migrou para `quota.plan_enforcement`. `register_search_session` migrou para `quota.session_tracker` e passou a fazer `from quota.plan_enforcement import _ensure_profile_exists` em runtime. O `quota/__init__.py` re-exporta ambos para preservar `from quota import X` (AC2 do DEBT-07), mas o patch-path relativo ao runtime binding **não foi atualizado** nos testes.

### Mecanismo da falha
O decorator `@patch("quota._ensure_profile_exists", return_value=True)` substitui o atributo re-exportado em `quota/__init__.py`, mas `register_search_session` resolve `_ensure_profile_exists` via `from quota.plan_enforcement import _ensure_profile_exists` (dentro da função), usando o **binding original** no módulo `quota.plan_enforcement` — que não é alterado pelo patch no facade.

Resultado: `_ensure_profile_exists` real é executado → retorna `True` (perfil genuíno criado via `Created missing profile for user user***` nos logs) → execução prossegue, mas o contador de chamadas `sb.table(...)` nos testes fica desalinhado (o teste assume 3 calls; na realidade ocorre 1 call extra devido ao `_ensure_profile_exists` internamente consultar o mock).

### Evidência de que prod-code está correto
`backend/quota/session_tracker.py:60-89`:
```python
sectors_pg = "{" + ",".join(sorted_sectors) + "}"
ufs_pg = "{" + ",".join(sorted_ufs) + "}"
existing_params = await sb_execute(
    sb.table("search_sessions")
    .select("id, created_at")
    .eq("user_id", user_id)
    .filter("sectors", "eq", sectors_pg)   # ← CRIT-029 fix PRESENTE
    .filter("ufs", "eq", ufs_pg)            # ← CRIT-029 fix PRESENTE
    .eq("data_inicial", data_inicial)
    .eq("data_final", data_final)
    .gte("created_at", cutoff)
    .order("created_at", desc=True)
    .limit(1)
)
```

### Fix aplicado (test-only)
Substituído em todas as ocorrências:
```python
@patch("quota._ensure_profile_exists", return_value=True)
# ↓
@patch("quota.plan_enforcement._ensure_profile_exists", return_value=True)
```

Alinha o patch-target com o namespace canônico onde `register_search_session` faz o lookup. 12/12 PASS após o fix.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #13/30)

## Stories relacionadas no epic

- STORY-CIG-BE-sessions-ensure-profile (#12 — mesma área sessions)
- STORY-CIG-BE-story-drift-search-session-lifecycle (#26 — mesma área)

---

## File List

- `backend/tests/test_crit029_session_dedup.py` (test-only; 8 occurrences of `@patch("quota._ensure_profile_exists", ...)` → `@patch("quota.plan_enforcement._ensure_profile_exists", ...)`)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #13/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. **Atenção @po:** investigar prod-bug (regressão CRIT-029) vs assertion-drift.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. Prod-bug hipótese documentada com escalation path (`Status: Blocked` se confirmado). Se @dev classificar (b) regressão CRIT-029, abrir issue P1 e escalar para @po.
- **2026-04-18** — @dev: Investigation complete. Verdict **(a) assertion-drift**, NÃO prod-bug. Root cause: DEBT-07 package split (`fa42e0c8`) moveu `_ensure_profile_exists` para `quota.plan_enforcement`, mas patch path `quota._ensure_profile_exists` não foi atualizado. Fix test-only: 8 patch targets reapontados para `quota.plan_enforcement._ensure_profile_exists`. **Result: 12/12 PASS** (antes: 8 failed / 4 passed). Sem toque em prod code. Status Ready → InReview. AC1/AC3/AC4/AC5 checked; AC2 aguarda CI.
