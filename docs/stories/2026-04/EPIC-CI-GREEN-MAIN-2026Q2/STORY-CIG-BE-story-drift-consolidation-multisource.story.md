# STORY-CIG-BE-story-drift-consolidation-multisource — `source_count` 1 vs 2 após consolidação — 5 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P2 — Gate (pequeno, depende de story foundation)
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suítes `test_consolidation_multisource.py` e `test_story252_resilience.py` rodam em `backend-tests.yml` e falham em **5 testes** do triage row #23/30. Causa raiz classificada como **assertion-drift**: o número de sources efetivamente consolidados mudou de 1 para 2 (ou vice-versa) após refactor recente de `ConsolidationService`.

Esta story **depende de STORY-CIG-BE-consolidation-helpers-private (#10/30)**: a API pública que esses 5 testes validam pode mudar como consequência daquela story. Abrir esta story só após #10 estar em `InReview` ou `Done`.

**Arquivos principais afetados:**
- `backend/tests/test_consolidation_multisource.py`
- `backend/tests/test_story252_resilience.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** Número de sources ativas mudou com feature flags (`DATALAKE_QUERY_ENABLED` default true). Quando datalake responde, `source_count` pode legitimamente ser 1 (datalake) vs 2 (datalake + legacy fallback). Validar contra CLAUDE.md Layer 2/3 architecture.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_consolidation_multisource.py backend/tests/test_story252_resilience.py -v` retorna exit code 0 localmente (5/5 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" (assertion-drift). Especificar condições (`DATALAKE_QUERY_ENABLED=true/false`, sources disponíveis) que determinam `source_count` esperado.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Confirmar que STORY-CIG-BE-consolidation-helpers-private (#10) está Done ou InReview antes de começar.
- [ ] Rodar as 2 suítes isoladas e capturar expected vs received source_count.
- [ ] Mapear: com que flags `DATALAKE_QUERY_ENABLED` e com quantas sources mockadas os testes rodam.
- [ ] Decidir se fix é (a) ajustar assertion ou (b) garantir que teste roda com flags/mocks deterministicamente.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #23/30)
- **Bloqueada por:** STORY-CIG-BE-consolidation-helpers-private (#10/30) — deve estar `Done` ou `InReview` antes de @po validar esta.

## Stories relacionadas no epic

- STORY-CIG-BE-consolidation-helpers-private (#10 — bloqueia esta)
- STORY-CIG-BE-crit052-canary-refactor (#7 — mesma área pipeline)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #23/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. Dep de #10 explicitamente documentada — @po deve validar esta por último na Wave 1+2.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready (Wave 2). Blocker de #10 corretamente declarado em "Bloqueada por"; @dev deve aguardar #10 Done/InReview antes de iniciar Implement. Especificar flags `DATALAKE_QUERY_ENABLED` em AC3 é boa disciplina.
