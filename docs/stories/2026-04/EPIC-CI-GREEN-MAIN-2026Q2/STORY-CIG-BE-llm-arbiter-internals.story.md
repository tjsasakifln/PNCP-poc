# STORY-CIG-BE-llm-arbiter-internals — `_client` e `_hourly_cost_usd` moveram após `llm_arbiter` virar package — 9 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suítes `test_harden001_openai_timeout.py` e `test_llm_cost_monitoring.py` rodam em `backend-tests.yml` e falham em **9 testes** do triage row #14/30. Causa raiz classificada como **mock-drift**: o módulo `backend/llm_arbiter.py` virou package `backend/llm_arbiter/` e os símbolos `_client` e `_hourly_cost_usd` foram movidos para submódulos. Testes patcham o path antigo.

CLAUDE.md orienta especificamente: *"LLM: Mock at `@patch("llm_arbiter._get_client")` level"* — essa recomendação pode precisar ser atualizada pós-refactor.

**Arquivos principais afetados:**
- `backend/tests/test_harden001_openai_timeout.py`
- `backend/tests/test_llm_cost_monitoring.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** `_client` → `llm_arbiter.client._client` ou `llm_arbiter.classification._client`. Validar com `grep -rn "_client\\|_hourly_cost_usd\\|_get_client" backend/llm_arbiter/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_harden001_openai_timeout.py backend/tests/test_llm_cost_monitoring.py -v` retorna exit code 0 localmente (9/9 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift). Listar símbolos antes→depois e atualizar CLAUDE.md se orientação de patch path ficar obsoleta.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 2 suítes isoladas.
- [ ] `grep -rn "_client\\|_hourly_cost_usd\\|_get_client" backend/llm_arbiter/ backend/llm.py`.
- [ ] Atualizar mocks dos testes para novo path.
- [ ] Se CLAUDE.md orientação de patch path ficar incorreta: abrir PR separada ou incluir fix de docs nesta story.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #14/30)

## Stories relacionadas no epic

- STORY-CIG-BE-consolidation-helpers-private (#10 — mesmo padrão de refactor private drift)
- STORY-CIG-BE-asyncio-run-production-scan (#28 — static scan inclui `llm_arbiter/classification.py`)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #14/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (8/10)** — Draft → Ready. Se fix tornar CLAUDE.md mocking guidance (`@patch("llm_arbiter._get_client")`) obsoleto, incluir PR de docs update nesta story.
