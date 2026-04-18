# STORY-CIG-BE-consolidation-helpers-private — `ConsolidationService` perdeu helpers privados (`_tokenize_objeto`, `_jaccard`, `_deduplicate`, `_deduplicate_fuzzy`, `_wrap_source`) — 30 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker (maior impacto de 30 stories)
**Effort:** L (8h+)
**Agents:** @dev, @qa, @devops, @architect (para revisar se API pública nova é suficiente)

---

## Contexto

Suítes que testam consolidation/dedup rodam em `backend-tests.yml` e falham em **30 testes** do triage row #10/30 — a maior concentração de testes afetados em uma única causa raiz. Classificação pelo triage: **mock-drift**.

O módulo `backend/consolidation.py` (ou `backend/consolidation/` caso tenha virado package no refactor recente) perdeu/renomeou os helpers privados abaixo, que 30 testes patcham diretamente:

- `ConsolidationService._tokenize_objeto`
- `ConsolidationService._jaccard`
- `ConsolidationService._deduplicate`
- `ConsolidationService._deduplicate_fuzzy`
- `ConsolidationService._wrap_source`
- Além de `consolidation.source_health_registry` ao nível de módulo.

Os testes fazem `patch.object(ConsolidationService, "_deduplicate")` etc., o que significa (a) os helpers continuam existindo mas foram renomeados, (b) foram inlinados em métodos públicos, ou (c) foram extraídos para módulos separados. A decisão entre (a)/(b)/(c) não é trivial: se (b)/(c), os testes precisam ser reescritos para patchar **entry points públicos** (preferível, menor acoplamento) em vez de helpers privados.

**Esta story desbloqueia stories downstream:**
- STORY-CIG-BE-story-drift-consolidation-multisource (#23/30, depende desta)

**Arquivos principais afetados:**
- `backend/tests/test_fuzzy_dedup.py`
- `backend/tests/test_consolidation_early_return.py`
- `backend/tests/test_debt103_llm_search_resilience.py`
- `backend/tests/test_multisource_orchestration.py`
- `backend/tests/test_bulkhead.py`
- `backend/tests/test_crit_016_sentry_bugs.py`
- `backend/tests/test_story252_resilience.py`

**Hipótese inicial de causa raiz (a confirmar em Implement):** mock-drift pós-refactor de consolidation. @architect pode ser necessário para decidir se API pública atual (`consolidate()`, `dedup()`) é suficiente, ou se os helpers privados devem voltar para a superfície testável.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_fuzzy_dedup.py backend/tests/test_consolidation_early_return.py backend/tests/test_debt103_llm_search_resilience.py backend/tests/test_multisource_orchestration.py backend/tests/test_bulkhead.py backend/tests/test_crit_016_sentry_bugs.py backend/tests/test_story252_resilience.py -v` retorna exit code 0 localmente (30+/30+ PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 7 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis". Tabela antes→depois de cada símbolo removido. Se adaptação do teste for reestruturar patching para API pública, justificar em 1 parágrafo.
- [ ] AC4: Cobertura backend **não caiu** (threshold 70% mantido).
- [ ] AC5 (NEGATIVO): `grep -nE "@pytest\\.mark\\.skip|pytest\\.skip\\(|@pytest\\.mark\\.xfail|\\.only\\("` vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar as 7 suítes isoladas e capturar AttributeError reais.
- [ ] `grep -rn "class ConsolidationService\\|def _tokenize_objeto\\|def _jaccard\\|def _deduplicate\\|def _wrap_source\\|source_health_registry" backend/` — mapear nomes reais atuais.
- [ ] Decidir entre (a) restaurar helpers como atributos públicos (protegidos vs privados), (b) reescrever testes para bater API pública atual.
- [ ] Se (a) e exigir mudança de produção: pair com @architect, justificar em RCA.
- [ ] Se (b): manter cobertura (pode ser necessário adicionar testes de unidade menor para compensar).
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #10/30)
- **Bloqueia:** STORY-CIG-BE-story-drift-consolidation-multisource (#23/30)

## Stories relacionadas no epic

- STORY-CIG-BE-story-drift-consolidation-multisource (#23 — dep)
- STORY-CIG-BE-llm-arbiter-internals (#14 — mesmo padrão de private refactor drift)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #10/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`. Nota: maior volume do epic (30 testes) — considerar split em sub-stories se @po identificar RCA heterogênea após Investigation.
