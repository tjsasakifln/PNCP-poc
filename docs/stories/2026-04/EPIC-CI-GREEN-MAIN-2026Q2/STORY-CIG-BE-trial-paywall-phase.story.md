# STORY-CIG-BE-trial-paywall-phase — `get_trial_phase` sempre retorna `full_access` (lógica revertida) — 15 testes prod-bug candidato

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Done
**Priority:** P1 — Gate Blocker (possível regressão de revenue)
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops, @po (se confirmado bug real de paywall)

---

## Contexto

Suítes de paywall/trial rodam em `backend-tests.yml` e falham em **15 testes** do triage row #11/30. Classificação pelo triage é **assertion-drift**, mas a função afetada (`get_trial_phase`) é um dos pontos mais sensíveis do produto (STORY-264/277/319/320 — trial de 14 dias, paywall pós-trial). O triage anota: *"`get_trial_phase` sempre retorna `full_access` — lógica revertida"*.

Duas hipóteses precisam ser distinguidas em Implement:

1. **Assertion-drift benigna:** logic atual é correta; testes asseguram fases antigas (`trial_active` / `trial_expired` / `paywall`) que foram consolidadas em um único retorno `full_access` para plano SmartLic Pro.
2. **Prod-bug real:** paywall está desativado em produção por acidente — usuários com trial expirado estão recebendo `full_access` indevidamente. Neste caso, story vira bugfix P0 e exige pair com @po.

Decisão entre (1) e (2) só é possível após leitura do módulo real + diff histórico de `get_trial_phase`.

**Esta story desbloqueia stories downstream:**
- STORY-CIG-BE-story-drift-trial-email-sequence (#24/30, depende desta)

**Arquivos principais afetados:**
- `backend/tests/test_story320_paywall.py`
- `backend/tests/test_trial_block.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Provável **bug real** dado que o triage chamou "lógica revertida" explicitamente — mas validar com `git log backend/quota.py backend/services/billing.py -p` antes de rotular como regressão.

---

## Acceptance Criteria

- [x] AC1: `pytest backend/tests/test_story320_paywall.py backend/tests/test_trial_block.py -v` retorna exit code 0 localmente — **36/36 PASS** (evidência no commit Wave #386, sub-commit "CIG Wave 1 — sessions/paywall/buscar/sse mock paths post-package refactors").
- [x] AC2: Última run de `backend-tests.yml` pós-merge de PR #386 na main mostra as 2 suítes com 0 failed / 0 errored. Link: https://github.com/tjsasakifln/PNCP-poc/actions (Wave #386 merge 2026-04-19).
- [x] AC3: Causa raiz — **(1) assertion-drift benigna** (mock-path drift). Ver "Root Cause Analysis" abaixo. Não é prod-bug: `get_trial_phase` retorna corretamente; quebra era `patch("quota.check_quota")` em testes após `quota` virar package com `plan_enforcement` sub-módulo. Logic de paywall está intacta.
- [x] AC4: Cobertura backend não regrediu. Threshold 70% mantido. Nenhuma mudança de código de produção, apenas mocks de teste.
- [x] AC5 (NEGATIVO): Zero novos skip/xfail markers introduzidos. Skip markers baseline = 51, pós-Wave = 51 (validado commit level).

---

## Investigation Checklist (para @dev, fase Implement)

- [x] Rodar as 2 suítes isoladas e capturar mensagens de erro.
- [x] `git log --follow -p backend/quota.py backend/services/billing.py` — confirmado: `quota.py` virou package `quota/` com `plan_enforcement.py`, `plan_auth.py`, `session_tracker.py`, `quota_atomic.py`. `get_trial_phase` permanece funcional no facade `quota/__init__.py`.
- [x] Classificar: **(1) assertion-drift benigna** — logic correta, mocks desatualizados.
- [x] N/A — não é prod-bug.
- [x] Feature flag `SUBSCRIPTION_GRACE_DAYS=3` respeitada (CLAUDE.md).
- [x] Quota enforcement (`check_and_increment_quota_atomic`) invocada — mocks atualizados para `quota.plan_enforcement.check_quota` onde aplicável.
- [x] Cobertura não regrediu.
- [x] N/A — `test_post_pipeline_blocked` está fora do escopo desta story (triage move-to-integration-external row 1; tratado em story separada).

---

## Root Cause Analysis

**Causa raiz:** Mock-drift após refactor do módulo `quota` para package.

**Antes (módulo único `quota.py`):**
```python
from quota import check_quota, _ensure_profile_exists, get_trial_phase
```

**Depois (package `quota/`):**
```python
# quota/__init__.py (facade)
from quota.plan_enforcement import check_quota, _ensure_profile_exists
from quota.plan_auth import require_active_plan
# get_trial_phase permanece no __init__

# Mas `require_active_plan` faz import direto:
# quota/plan_auth.py
from quota.plan_enforcement import check_quota
```

**Impact nos testes:** Testes fazem `@patch("quota.check_quota")` e o facade é correto, **mas `plan_auth` já fez `from quota.plan_enforcement import check_quota`** no carregamento inicial — o patch no facade não intercepta o binding local em `plan_auth`.

**Fix (commit Wave #386):** Mudar `@patch("quota.check_quota")` → `@patch("quota.plan_enforcement.check_quota")` para testes que exercitam `require_active_plan` callsites. `_apply_trial_paywall` continua fazendo `from quota import get_trial_phase` (facade), então tests de truncamento continuam patchando `quota.get_trial_phase`. Logger patch também migrado para `quota.plan_auth.logger`. `test_paid_plan_can_post_pipeline` requisitava `quota.check_quota` mock para `pipeline.py:42` dynamic import.

**Resultado:** 36/36 PASS.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #11/30)
- **Bloqueia:** STORY-CIG-BE-story-drift-trial-email-sequence (#24/30)

## Stories relacionadas no epic

- STORY-CIG-BE-story-drift-trial-email-sequence (#24 — dep)
- STORY-CIG-BE-endpoints-story165-plan-rename (#20 — mesma área billing/plano)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #11/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. **Atenção @po:** triagem anotou "lógica revertida" — validar prod-bug vs assertion-drift é obrigatório antes de GO.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO com ressalva (7/10)** — Draft → Ready (**Wave 1 foundation**). Ambiguidade (1) assertion-drift vs (2) prod-bug real é estruturalmente aceitável em Draft — Investigation Checklist tem escalation path documentado. **Se @dev confirmar (2) prod-bug em Implement**, Status volta a `Blocked` e @po escala para **P0 bugfix** (regressão de revenue/paywall tem impacto direto em MRR). Bloqueia #24.
- **2026-04-19** — @dev: Implementação resolvida via PR #386 (EPIC-CI-GREEN Wave 1 — Foundation). Classificação confirmada: **(1) assertion-drift benigna** (mock-path migration após quota → package). Zero mudanças de código de produção. 36/36 tests PASS (test_story320_paywall.py + test_trial_block.py). Status: Ready → InProgress → InReview.
- **2026-04-19** — @qa (Quinn): QA Gate **PASS**. Evidência empírica: commit Wave #386 sub-commit "CIG Wave 1 — sessions/paywall/buscar/sse mock paths post-package refactors" mostra 36/36 PASS. Código de produção intacto — validado por `git diff backend/quota/ backend/services/billing.py` vazio no PR. RCA distingue claramente assertion-drift de prod-bug com evidência estrutural. AC1-5 atendidos. Não bloqueia #24 (trial-email-sequence); desbloqueio confirmado.
- **2026-04-19** — @devops (Gage): PR #386 merged em `main` (commit 45e4f70b) em 2026-04-19T19:14:13Z. Status: InReview → Done. Cache-warming deprecation + 24 CIG-BE stories fechadas no mesmo Wave.
