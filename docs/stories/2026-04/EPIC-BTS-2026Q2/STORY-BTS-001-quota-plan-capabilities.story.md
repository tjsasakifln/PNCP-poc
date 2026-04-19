# STORY-BTS-001 — Quota & Plan Capabilities (35 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P0 — Foundation (quota toca praticamente todas as rotas autenticadas)
**Effort:** M (3-5h) — actual ~1.5h
**Agents:** @dev + @qa
**Status:** InReview
**PR:** [#396](https://github.com/tjsasakifln/PNCP-poc/pull/396)

---

## Contexto

35 testes falhando em 3 arquivos cobrem o sistema de quota + plan capabilities (TD-007 refatorou quota.py em quota_core + quota_atomic + plan_enforcement em 2026-04). Refactor quebrou mock targets que ainda apontam para paths pré-split (`quota.X` no lugar de `quota.plan_enforcement.X` ou vice-versa).

**Amostra confirmada em PR #393** (STORY-CIG-BE-endpoints-story165-plan-rename): route code usa `import quota as _quota` then `_quota.check_quota(...)`, mas testes patchavam `quota.plan_enforcement.check_quota`. Fix foi trocar patch target para `quota.check_quota`. Mesmo padrão aplica aqui.

---

## Arquivos (tests)

**Scope reconciliation 2026-04-19 (pós-implementação):** Triage indicated 35 failures across 3 files. Empirical baseline on main showed only 9 failing (all in `test_plan_capabilities.py`). The other 26 had been fixed ambient to earlier CIG waves.

- `backend/tests/test_quota.py` — baseline: **41/41 PASS** (triage claimed 22 fails, no longer accurate)
- `backend/tests/test_plan_capabilities.py` — **9 fails fixed** (claimed 8, delta: +1 — `test_trial_expired_blocks_user` wasn't in original triage)
- `backend/tests/test_quota_race_condition.py` — baseline: **14/14 PASS** (triage claimed 5 fails, no longer accurate)

Actual test debt addressed: **9 failures → 0**. Story scope aligned with this reality; AC1 adjusted accordingly.

---

## Acceptance Criteria

- [x] AC1: `pytest backend/tests/test_quota.py backend/tests/test_plan_capabilities.py backend/tests/test_quota_race_condition.py -v --timeout=30` returns exit code 0 locally — **99/99 PASS in 8.37s**.
- [ ] AC2: `backend-tests.yml` run on PR #396 shows 3 files with 0 failed/0 errored. Link pending CI run.
- [x] AC3: Root cause documented by sub-group in PR #396 commit body (Category A: new plans; Category B: patch target drift post TD-007; Category C: production behavior change). Before→after table of patch targets embedded.
- [ ] AC4: Backend coverage preserved (threshold 70%) — pending CI report.
- [x] AC5 (NEGATIVE): `grep -nE "@pytest\\.mark\\.(skip|xfail)|pytest\\.skip\\(" backend/tests/test_quota*.py backend/tests/test_plan_capabilities.py` empty (Zero Quarentena preserved).

---

## Investigation Checklist

- [ ] Rodar cada arquivo isolado, capturar os 3 primeiros erros de cada (padrão de falha)
- [ ] `grep -rn "patch.*quota\\.\\(plan_enforcement\\|quota_core\\|quota_atomic\\)" backend/tests/test_quota*.py`
- [ ] Cross-check com `backend/routes/*.py` onde cada função é usada — descobrir o **local de lookup** real
- [ ] Para race conditions: verificar se `asyncio.gather` ou locks assumem API antiga

---

## Dependências

- **Bloqueia:** BTS-002, BTS-006, BTS-008 (todos consomem quota)
- **Bloqueado por:** nenhum

---

## Change Log

- **2026-04-19** — @sm (River): Story criada do triage EPIC-BTS. Status Ready.
- **2026-04-19** — @po (Pax): Validação GO — 8/10. Gaps: P4 escopo implícito, P8 sem seção de riscos. Ambos sistêmicos no template; não bloqueiam. Story confirmada Ready.
- **2026-04-19** — @dev: Implementação completa. Baseline reconciliado (35 claimed → 9 actual). 9 failures em `test_plan_capabilities.py` endereçadas via 3 causas raiz: (A) novos planos `founding_member`/`consultoria`, (B) patch target drift post TD-007 (`quota.X` → `quota.plan_enforcement.X`, `quota.datetime` → `quota.quota_atomic.datetime`), (C) mudanças de comportamento em produção (upsert fallback removido; trial grace period 48h). 99/99 tests PASS local. AC1, AC3, AC5 fechados; AC2/AC4 pendentes de CI run em PR #396. Status Ready → InReview.
