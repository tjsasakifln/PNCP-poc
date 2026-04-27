# RES-BE-005: God-Module Split — `filter/pipeline.py` (1918L)

**Priority:** P1
**Effort:** L (5-7 dias)
**Squad:** @architect + @dev (architect lidera)
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 4 (2026-05-27 → 2026-06-02) — paralelizável com RES-BE-007
**Dependências bloqueadoras:** [RES-BE-001](RES-BE-001-audit-execute-without-budget.md), [RES-BE-009](RES-BE-009-test-suite-triage.md) (suite saudável necessária para detectar regressões)

---

## Contexto

`backend/filter/pipeline.py` tem **1918 linhas** e mistura 4 responsabilidades:

1. **Rules** — keyword/density matching, term parsing
2. **Scoring** — relevance scoring, viability factors
3. **Exclusions** — exclusões setoriais, status filters, value range filters
4. **Context** — search context state, session state, feature flag dispatch

Coesão baixa (LCOM = alta) → blast radius alto: qualquer mudança em scoring quebra exclusions tests, qualquer mudança em rules força re-run de toda a suite (>4min). Auditoria pós-P0 mediu **fan-in 47 importadores** e fan-out **23 dependências**.

Esta story split em 4 sub-módulos coesos, mantendo `pipeline.py` como **facade re-exportador** para zero-impact em consumidores. Effort L pelo volume + necessidade de QA loop pesado (cobertura ≥85%, sem regressão funcional).

Baseado em pattern bem-sucedido: backend já fez split similar em `cache/` (manager, swr, admin, local_file, redis, supabase) — replicar.

---

## Acceptance Criteria

### AC1: Estrutura alvo

- [ ] Criar pacote `backend/filter/` (já existe como módulo? confirmar via `ls`. TODO @architect: validar) com sub-módulos:
  ```
  backend/filter/
  ├── __init__.py        # re-export shim
  ├── pipeline.py        # facade (slim, ~200L) — só orquestra
  ├── rules.py           # keyword/density matching, term parsing (~400L)
  ├── scoring.py         # relevance scoring, viability factors (~500L)
  ├── exclusions.py      # exclusões setoriais, status, value range (~400L)
  └── context.py         # search context state, feature flag dispatch (~400L)
  ```
- [ ] Total LOC consolidado igual ou menor que 1918L (ganho de coesão, não bloat)

### AC2: Migração de classes/funções

- [ ] Mapear cada símbolo público de `pipeline.py` original para seu novo módulo:
  - `apply_keyword_filter`, `parse_terms`, `match_density` → `rules.py`
  - `score_relevance`, `compute_viability`, `rank_results` → `scoring.py`
  - `filter_by_uf`, `filter_by_value`, `apply_sector_exclusions`, `apply_status_filter` → `exclusions.py`
  - `SearchContext`, `dispatch_filter_pipeline`, feature flag handlers → `context.py`
- [ ] Funções privadas (prefix `_`) movem com seus consumidores
- [ ] `__all__` em cada sub-módulo exporta apenas API pública

### AC3: Façade `pipeline.py` re-exportador

- [ ] Reescrever `pipeline.py` como façade slim:
  ```python
  """Filter pipeline facade. Sub-modules under backend/filter/."""
  from .rules import apply_keyword_filter, parse_terms, match_density
  from .scoring import score_relevance, compute_viability, rank_results
  from .exclusions import filter_by_uf, filter_by_value, apply_sector_exclusions, apply_status_filter
  from .context import SearchContext, dispatch_filter_pipeline

  __all__ = [
      "apply_keyword_filter", "parse_terms", "match_density",
      "score_relevance", "compute_viability", "rank_results",
      "filter_by_uf", "filter_by_value", "apply_sector_exclusions", "apply_status_filter",
      "SearchContext", "dispatch_filter_pipeline",
  ]
  ```
- [ ] **ZERO mudanças** em consumidores externos — `from filter.pipeline import X` continua funcionando
- [ ] `__init__.py` do pacote re-exporta para suportar `from filter import X`

### AC4: PRs sequenciais (chunked rollout)

- [ ] **PR 1:** Extract — criar `rules.py`, `scoring.py`, `exclusions.py`, `context.py`; mover código; `pipeline.py` torna-se façade. **Testes existentes devem passar SEM alteração.**
- [ ] **PR 2 (opcional):** Migrar consumidores internos críticos para imports diretos (`from filter.rules import X`) — facilita futura remoção do façade
- [ ] **PR 3 (opcional, futuro):** Marcar `pipeline.py` como deprecated; emitir DeprecationWarning em imports
- [ ] Esta story cobre PR 1 obrigatoriamente; PR 2 opcional se tempo permite

### AC5: Cobertura de testes ≥85%

- [ ] Cada sub-módulo tem teste correspondente:
  - `backend/tests/filter/test_rules.py`
  - `backend/tests/filter/test_scoring.py`
  - `backend/tests/filter/test_exclusions.py`
  - `backend/tests/filter/test_context.py`
- [ ] Testes existentes em `backend/tests/test_filter*.py` continuam passando sem modificação
- [ ] Cobertura medida via `pytest --cov=backend/filter --cov-report=term-missing`
- [ ] Linhas tocadas (split + nova organização): cobertura ≥85%
- [ ] Edge cases adicionais por sub-módulo (mínimo 3 novos testes por módulo)

### AC6: Performance — sem regressão

- [ ] Benchmark micro: `pytest backend/tests/perf/test_filter_pipeline_bench.py`
  - Mede tempo de `dispatch_filter_pipeline()` em payload realista (1000 bids)
  - Pre-split baseline registrado em `docs/perf/filter-pipeline-baseline-2026-04-28.md`
  - Pós-split: latência mediana < 110% baseline (até 10% overhead aceitável por imports)
- [ ] Profile com `cProfile` se overhead >10%; otimizar imports lazy se necessário

### AC7: Documentação

- [ ] Cada sub-módulo tem docstring de módulo (3-5 linhas explicando responsabilidade)
- [ ] `backend/filter/__init__.py` tem comentário-mapa "this package replaces the 1918L pipeline.py god-module"
- [ ] Atualizar `.claude/rules/architecture-detail.md` (CLAUDE.md auto-load) na linha "Filtering" — substituir referência única por listagem dos 4 sub-módulos
- [ ] Diagrama (ASCII ou mermaid) em `docs/architecture/filter-pipeline-decomposition.md` mostrando responsabilidades

### AC8: Testes (gate final)

- [ ] Suite total backend passa sem regressão (5131+ tests passing, 0 failures)
- [ ] Suite tempo total CI mantido <8min (alvo após RES-BE-009)
- [ ] Cobertura por sub-módulo ≥85%
- [ ] Sem novos warnings em pytest (DeprecationWarning, etc.)

---

## Scope

**IN:**
- Split `pipeline.py` em 4 sub-módulos
- Façade re-exportador
- Testes por sub-módulo com cobertura ≥85%
- Benchmark perf pre/post
- Documentação arquitetural

**OUT:**
- Refator de lógica interna (e.g. otimizar scoring) — apenas re-organizar
- Remoção do façade (PR 3, futuro)
- Migrar consumidores externos (PR 2 — opcional nesta story)
- Type-hints adicionar onde faltam (escopo separado se quiser, deferir)
- Renaming de funções públicas — proibido nesta story (zero-impact externo)

---

## Definition of Done

- [ ] 4 sub-módulos criados com responsabilidades claras
- [ ] Façade `pipeline.py` slim (<300L) re-exportando API pública
- [ ] Cobertura testes ≥85% por sub-módulo
- [ ] Suite backend passa sem regressão
- [ ] Benchmark micro: latência mediana <110% baseline
- [ ] Documentação `docs/architecture/filter-pipeline-decomposition.md` criada
- [ ] `.claude/rules/architecture-detail.md` atualizado
- [ ] CodeRabbit review clean (CRITICAL=0, HIGH=0)
- [ ] PR review por @architect (Aria) — review obrigatório de design — e @qa (Quinn) com verdict PASS
- [ ] CLAUDE.md atualizado (referência ao novo pacote)
- [ ] QA loop max 2 iterações (effort grande, esperado feedback)

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/filter/pipeline.py` (1918L → ~200L façade)
- `/mnt/d/pncp-poc/backend/filter/rules.py` (novo)
- `/mnt/d/pncp-poc/backend/filter/scoring.py` (novo)
- `/mnt/d/pncp-poc/backend/filter/exclusions.py` (novo)
- `/mnt/d/pncp-poc/backend/filter/context.py` (novo)
- `/mnt/d/pncp-poc/backend/filter/__init__.py` (novo ou existente — re-export)
- `/mnt/d/pncp-poc/backend/tests/filter/test_rules.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/filter/test_scoring.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/filter/test_exclusions.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/filter/test_context.py` (novo)
- `/mnt/d/pncp-poc/docs/architecture/filter-pipeline-decomposition.md` (novo)

### Padrão referência

- Split bem-sucedido similar: `backend/cache/` (manager, swr, admin, local_file, redis, supabase) — usar como template
- `backend/filter_stats.py`, `term_parser.py`, `synonyms.py`, `status_inference.py` já existem como módulos relacionados — verificar se algum overlap (provavelmente não; mas TODO @architect: validar)

### Process — ordem sugerida

1. **Read** `pipeline.py` integral; mapear símbolos em planilha (símbolo → sub-módulo)
2. **Branch:** `refactor/RES-BE-005-filter-pipeline-split`
3. **PR 1 commit 1:** criar sub-módulos vazios com docstrings e `__all__ = []`
4. **PR 1 commit 2..N:** mover símbolos um a um, rodando suite completa após cada move
5. **PR 1 commit final:** reescrever `pipeline.py` como façade
6. CodeRabbit pass + QA gate

### Frameworks de teste

- pytest 8.x + pytest-asyncio
- File location: `backend/tests/filter/test_<submodule>.py`
- Marks: `@pytest.mark.timeout(30)` (testes complexos podem precisar)
- Fixtures: reusar fixtures existentes em `conftest.py` para `pncp_raw_bids` mock data

### Convenções

- Imports absolutos (Constitution Article VI): `from filter.rules import X` (não `from .rules import X` em testes)
- Type hints obrigatórios em sub-módulos novos
- Logger por módulo: `logger = logging.getLogger(__name__)`
- `__all__` explícito em cada sub-módulo

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| Suite backend regride (testes failing) | Revert commit ofensivo dentro do PR; identificar símbolo que tinha import circular |
| Performance regride >10% em benchmark | Investigar imports lazy ou cache de função; se irrecuperável, revert PR e abrir refator alternativo |
| Consumidor externo quebra (e.g. import direto de função privada) | Adicionar símbolo ao façade ou no `__init__.py`; documentar antipattern |
| QA loop excede 5 iterações | Escalar para @aiox-master; possível split em 2 stories (rules+exclusions vs scoring+context) |
| Imports circulares em runtime | Refator: extrair classe/função compartilhada para módulo neutro (e.g. `backend/filter/types.py`) |

**Rollback completo:** revert PR. Façade preserva API; consumidores não percebem rollback.

---

## Dependencies

**Entrada:**
- [RES-BE-001](RES-BE-001-audit-execute-without-budget.md) — gate CI ativo
- [RES-BE-009](RES-BE-009-test-suite-triage.md) — suite saudável <8min CI necessário para QA loop iterativo

**Saída:** Nenhuma direta — refator interno, mas habilita futuro: stories de feature em filter ficam mais fáceis de testar isoladamente.

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO (conditional)
**Score:** 8/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | God-module split com LOC explícito (1918L). |
| 2 | Complete description | ✗ | Description menciona apenas `pipeline.py` mas filter/ JÁ É um pacote com 7 módulos siblings (keywords.py 40KB, density.py, stats.py, status.py, uf.py, value.py, utils.py). Story não reconhece esses siblings; proposta de submódulos (rules/scoring/exclusions/context) pode colidir/duplicar com existing. |
| 3 | Testable acceptance criteria | ✓ | 8 ACs incluindo benchmark perf (<110% baseline) e cobertura ≥85% por sub-módulo. |
| 4 | Well-defined scope | ✗ | Scope IN/OUT não delimita relação com siblings existentes (e.g. proposto `exclusions.py` vs existing `value.py`+`uf.py`). Risk Required Fix antes de PR 1. |
| 5 | Dependencies mapped | ✓ | Entrada RES-BE-001+009; saída horizontal. |
| 6 | Complexity estimate | ✓ | L (5-7 dias) coerente, mas conditional: se houver merge necessário com siblings existentes, pode escalar. |
| 7 | Business value | ✓ | "Blast radius alto, testes lentos, fan-in 47" — claro. |
| 8 | Risks documented | ✓ | Inclui imports circulares + escalation @aiox-master se QA loop excede 5. |
| 9 | Criteria of Done | ✓ | 11 itens DoD incluindo @architect review de design obrigatório. |
| 10 | Alignment with PRD/Epic | ✓ | Métrica EPIC #6 (suite CI <8min) habilitada por este split. |

### Required Fixes (antes de @dev iniciar Phase 3)

- [ ] **@architect (Aria) deve clarificar AC1**: como os 4 sub-módulos propostos (rules.py, scoring.py, exclusions.py, context.py) interagem com os 7 siblings existentes em `backend/filter/` (keywords.py, density.py, stats.py, status.py, uf.py, value.py, utils.py). Cenários a decidir:
  - (a) renomear sub-módulos propostos para evitar overlap (e.g. `rules.py` → conteúdo migra para `keywords.py` existente);
  - (b) consolidar siblings em sub-módulos novos (e.g. `uf.py` + `value.py` → `exclusions.py`);
  - (c) manter siblings + adicionar 4 novos (mas redefinir responsabilidades para não duplicar).
- [ ] Decisão registrada via `decision-recorder.js` antes do PR 1 commit 1.

### Observations

- TODO @architect existente em AC1 ("validar se filter/ é package ou módulo único") é parcialmente respondido por evidência empírica: `ls backend/filter/` mostra package com `__init__.py` + 7 siblings + pipeline.py (88KB). Required Fix acima formaliza a clarificação que falta.
- Façade preservada via shim — backward-compat externa garantida, mitigando risco de regressão de imports.
- Effort L permite QA loop iterativo; @qa Quinn deve validar cobertura por sub-módulo após decisão de @architect.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — split god-module filter/pipeline.py | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO conditional (8/10). Required Fix: @architect clarificar interação com 7 siblings existentes em filter/ antes de PR 1. Status: Draft → Ready (com gate em Phase 3). | @po (Pax) |
