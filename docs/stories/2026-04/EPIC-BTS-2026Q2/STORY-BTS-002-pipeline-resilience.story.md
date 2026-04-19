# STORY-BTS-002 — Pipeline Resilience Layer (30 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P0 — Foundation (pipeline = rota `/buscar`, coração do produto)
**Effort:** M (3-5h)
**Agents:** @dev + @qa + @architect (para RCA se revelar prod bug)
**Status:** Ready

---

## Contexto

30 testes cobrindo resilience do pipeline de busca — timeout waterfall (STORY-4.4 TD-SYS-003), LLM fallback, circuit breakers, retry logic. Maior bloco após quota.

Padrão observado: STORY-4.4 tightened defaults (`pipeline(100) > consolidation(90) > per_source(70) > per_uf(25)`). Testes que hardcoded valores antigos falham. Além disso, `backend/pipeline/` foi refatorado em stages (`generate`, `persist`, `filter`, etc.) e mocks podem patchar módulo pre-refactor.

---

## Arquivos (tests)

- `backend/tests/test_debt103_llm_search_resilience.py` (13 failures)
- `backend/tests/test_debt110_backend_resilience.py` (9 failures)
- `backend/tests/test_pipeline_resilience.py` (5 failures)
- `backend/tests/test_pipeline.py` (3 failures)

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_debt103_llm_search_resilience.py backend/tests/test_debt110_backend_resilience.py backend/tests/test_pipeline_resilience.py backend/tests/test_pipeline.py -v --timeout=30` retorna exit code 0 (30/30 PASS).
- [ ] AC2: `backend-tests.yml` run no PR desta story mostra 4 arquivos com **0 failed**. Link no Change Log.
- [ ] AC3: Causa raiz RCA distinguindo (a) assertion-drift de timeout vs (b) mock-drift de module path vs (c) prod bug de resilience. Se (c), escalar para @architect antes de mergear.
- [ ] AC4: Cobertura backend não caiu.
- [ ] AC5 (NEGATIVO): zero `@pytest.mark.skip` ou `xfail` novos.

---

## Investigation Checklist

- [ ] Rodar cada arquivo isolado
- [ ] `grep -rn "PNCP_TIMEOUT\\|FETCH_TIMEOUT\\|PIPELINE_TIMEOUT\\|CONSOLIDATION_TIMEOUT" backend/tests/test_debt*.py backend/tests/test_pipeline*.py` — verificar se hardcoded
- [ ] Validar invariante `test_timeout_invariants.py` continua verde (não pode regredir)
- [ ] Para LLM resilience: confirmar `@patch("llm_arbiter._get_client")` continua sendo o target correto

---

## Dependências

- **Bloqueia:** BTS-005 (consolidation usa pipeline), BTS-006 (search_async usa pipeline)
- **Bloqueado por:** BTS-001 (quota é pré-req de pipeline)

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready.
