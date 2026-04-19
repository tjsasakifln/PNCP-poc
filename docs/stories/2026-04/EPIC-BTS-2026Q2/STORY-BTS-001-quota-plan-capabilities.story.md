# STORY-BTS-001 — Quota & Plan Capabilities (35 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P0 — Foundation (quota toca praticamente todas as rotas autenticadas)
**Effort:** M (3-5h)
**Agents:** @dev + @qa
**Status:** Ready

---

## Contexto

35 testes falhando em 3 arquivos cobrem o sistema de quota + plan capabilities (TD-007 refatorou quota.py em quota_core + quota_atomic + plan_enforcement em 2026-04). Refactor quebrou mock targets que ainda apontam para paths pré-split (`quota.X` no lugar de `quota.plan_enforcement.X` ou vice-versa).

**Amostra confirmada em PR #393** (STORY-CIG-BE-endpoints-story165-plan-rename): route code usa `import quota as _quota` then `_quota.check_quota(...)`, mas testes patchavam `quota.plan_enforcement.check_quota`. Fix foi trocar patch target para `quota.check_quota`. Mesmo padrão aplica aqui.

---

## Arquivos (tests)

- `backend/tests/test_quota.py` (22 failures)
- `backend/tests/test_plan_capabilities.py` (8 failures)
- `backend/tests/test_quota_race_condition.py` (5 failures)

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_quota.py backend/tests/test_plan_capabilities.py backend/tests/test_quota_race_condition.py -v --timeout=30` retorna exit code 0 localmente (35/35 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra os 3 arquivos com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz documentada por sub-grupo (quota core, plan_enforcement, race-condition). Tabela antes→depois dos patch targets se aplicável.
- [ ] AC4: Cobertura backend **não caiu** (threshold 70% mantido).
- [ ] AC5 (NEGATIVO): `grep -nE "@pytest\\.mark\\.skip|pytest\\.skip\\(|@pytest\\.mark\\.xfail" backend/tests/test_quota*.py backend/tests/test_plan_capabilities.py` vazio (Zero Quarentena policy).

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
