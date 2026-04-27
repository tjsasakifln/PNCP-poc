# RES-BE-006: God-Module Split — `metrics.py` (1251L, 108 fan-in)

**Priority:** P1
**Effort:** L (5-7 dias)
**Squad:** @architect + @dev (architect lidera)
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 5 (2026-06-03 → 2026-06-09) — após RES-BE-005 (lições aprendidas)
**Dependências bloqueadoras:** [RES-BE-001](RES-BE-001-audit-execute-without-budget.md), [RES-BE-005](RES-BE-005-godmodule-split-pipeline.md) (validar pattern primeiro), [RES-BE-009](RES-BE-009-test-suite-triage.md)

---

## Contexto

`backend/metrics.py` tem **1251 linhas** e ~50 métricas Prometheus (`smartlic_*`). Análise de fan-in identificou **108 importadores** — qualquer mudança em metrics força recompilação completa do projeto e pode quebrar 108 módulos. Isso é o pior god-module em fan-in do backend.

Pior ainda: porque `metrics.py` é importado em paths críticos (`pipeline/budget.py`, `cache/negative_cache.py` futuro, `routes/*.py`), import circular é risco constante. Stories como RES-BE-003 (negative cache) e RES-BE-004 (datalake observability) precisam adicionar métricas — sem split, cada adição vira ponto de fricção.

Solução: split em 4 sub-módulos por **tipo de métrica** + façade backward-compatible. 108 importadores **não precisam mudar** porque `metrics.py` reescrito como `from .counters import *`, `from .histograms import *` etc. Mudança transparente.

Esta story é P1 mas effort L pelo blast radius. Sprint 5 (após RES-BE-005 mergeado e estabilizado) para aplicar lições.

---

## Acceptance Criteria

### AC1: Estrutura alvo

- [ ] Criar pacote `backend/metrics/`:
  ```
  backend/metrics/
  ├── __init__.py        # façade — `from .counters import *` etc.
  ├── counters.py        # Counter() instances (~400L)
  ├── histograms.py      # Histogram() instances (~250L)
  ├── gauges.py          # Gauge() instances (~150L)
  ├── registry.py        # CollectorRegistry, helpers, custom collectors (~250L)
  └── README.md          # how-to-add-metric guide
  ```
- [ ] Total LOC consolidado <= 1251L (excluindo docstrings adicionais)

### AC2: Migração por tipo

- [ ] **counters.py:** todas instâncias `Counter("smartlic_*")` (estimativa: ~30 counters):
  - `PIPELINE_BUDGET_EXCEEDED_TOTAL`, `FILTER_DECISIONS_BY_SETOR_TOTAL`, `LLM_FALLBACK_REJECTS_TOTAL`, etc.
- [ ] **histograms.py:** todas `Histogram(...)`:
  - `HTTP_REQUEST_DURATION_SECONDS`, `LLM_LATENCY_SECONDS`, etc.
- [ ] **gauges.py:** todas `Gauge(...)`:
  - `DB_POOL_IN_USE`, `CIRCUIT_BREAKER_STATE` (futuro RES-BE-012), etc.
- [ ] **registry.py:** `CollectorRegistry` custom (se existir), helpers `_record_*()`, custom collectors

### AC3: Façade backward-compatible

- [ ] Reescrever `backend/metrics.py` (mantém arquivo único antigo) **OU** criar `backend/metrics/__init__.py` que reexporta tudo:
  ```python
  """Prometheus metrics façade. Sub-modules under backend/metrics/."""
  from metrics.counters import *  # noqa: F401, F403
  from metrics.histograms import *  # noqa: F401, F403
  from metrics.gauges import *  # noqa: F401, F403
  from metrics.registry import *  # noqa: F401, F403
  ```
- [ ] Decisão de design: manter `metrics.py` arquivo OU virar pacote? **TODO @architect:** se `backend/metrics.py` arquivo coexiste com `backend/metrics/` pacote, Python vai dar erro. Solução: deletar `metrics.py` arquivo, manter `backend/metrics/__init__.py` como façade. Importadores `from metrics import X` continuam funcionando.
- [ ] **ZERO mudanças** em 108 importadores

### AC4: Testes — sem regressão

- [ ] Testes existentes em `backend/tests/test_metrics*.py` continuam passando sem alteração
- [ ] Adicionar `backend/tests/metrics/test_facade_integrity.py`:
  - Importa cada símbolo exportado pela façade
  - Confirma que todos são instâncias de `Counter`, `Histogram`, ou `Gauge`
  - Confirma que `__all__` consolidado da façade == união de `__all__` dos sub-módulos
- [ ] Cobertura ≥85% (medir via `pytest --cov=backend/metrics`)

### AC5: Migration safety — testes de import

- [ ] Test `test_no_circular_imports.py`:
  - Import de cada sub-módulo isolado (`importlib.import_module("metrics.counters")`)
  - Sem ImportError, sem RecursionError
- [ ] Test `test_all_108_importers_resolve.py`:
  - Lista os 108 importadores via `grep -rn "from metrics import\|import metrics" backend/ frontend/`
  - Para cada, verifica que símbolos importados existem
  - Falha se algum símbolo "perdido" (símbolo movido sem re-export)

### AC6: Documentação — guide de "como adicionar métrica"

- [ ] `backend/metrics/README.md`:
  ```markdown
  # Metrics — How to Add a New Metric

  ## Decision tree
  - **Counter** (sempre crescente): `counters.py`
  - **Histogram** (distribuição valores): `histograms.py`
  - **Gauge** (valor atual): `gauges.py`

  ## Naming convention
  - prefix `smartlic_`
  - snake_case
  - suffix `_total` (counter), `_seconds` (histogram time), `_bytes` (histogram size)
  ...
  ```
- [ ] `.claude/rules/architecture-detail.md` atualizado: substituir referência única por listagem dos 4 sub-módulos

### AC7: Validação fan-in

- [ ] Pós-split, rodar `grep -rln "from metrics import\|^import metrics" backend/ | wc -l` e confirmar ≥108 (não diminuiu)
- [ ] Nenhum importador atualizou seu import (zero-impact externo)
- [ ] Se algum sub-módulo precisa import absoluto direto (e.g. `from metrics.counters import X`), documentar como exceção

### AC8: Testes (gate final)

- [ ] Suite total backend passa sem regressão (5131+ tests passing, 0 failures)
- [ ] CI tempo total <8min mantido
- [ ] `/metrics` endpoint produção retorna mesmas métricas (validar via diff staging vs prod)

---

## Scope

**IN:**
- Split `metrics.py` em 4 sub-módulos por tipo
- Façade `__init__.py` re-exportador
- Testes de integridade façade + circular imports + 108 importers
- Documentação `metrics/README.md` + arquitetura
- Validação produção (staging diff)

**OUT:**
- Adicionar novas métricas (escopo paralelo: RES-BE-003, RES-BE-004, RES-BE-010, RES-BE-012)
- Remover métricas obsoletas — escopo separado
- Migrar para OpenMetrics 1.0 — escopo futuro
- Custom collectors avançados — escopo futuro
- Renaming de métricas — proibido (quebra Grafana/Prometheus alerts)

---

## Definition of Done

- [ ] 4 sub-módulos criados (counters, histograms, gauges, registry)
- [ ] Façade `__init__.py` re-exporta toda API pública
- [ ] 108 importadores resolvem sem mudança
- [ ] Testes de integridade passam
- [ ] Cobertura ≥85% nas linhas tocadas
- [ ] Suite backend passa sem regressão
- [ ] Endpoint `/metrics` produção idêntico (smoke diff staging vs prod)
- [ ] CodeRabbit clean (CRITICAL=0, HIGH=0)
- [ ] PR review por @architect (Aria) e @qa (Quinn) com verdict PASS
- [ ] `metrics/README.md` criado
- [ ] CLAUDE.md + architecture-detail.md atualizados
- [ ] QA loop max 2 iterações

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/metrics.py` (deletar — vira pacote)
- `/mnt/d/pncp-poc/backend/metrics/__init__.py` (novo — façade)
- `/mnt/d/pncp-poc/backend/metrics/counters.py` (novo)
- `/mnt/d/pncp-poc/backend/metrics/histograms.py` (novo)
- `/mnt/d/pncp-poc/backend/metrics/gauges.py` (novo)
- `/mnt/d/pncp-poc/backend/metrics/registry.py` (novo)
- `/mnt/d/pncp-poc/backend/metrics/README.md` (novo)
- `/mnt/d/pncp-poc/backend/tests/metrics/test_facade_integrity.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/metrics/test_no_circular_imports.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/metrics/test_all_108_importers_resolve.py` (novo)

### Padrão referência

- RES-BE-005 (filter/pipeline split) — usar lessons learned: PR sequencial, façade slim, fixtures
- `backend/cache/` package estrutura — façade pattern já validado

### Decisão de design: arquivo vs pacote

**Recomendação @architect:** transformar `metrics.py` arquivo em `backend/metrics/` pacote. Python resolve `from metrics import X` via `__init__.py` automaticamente. Isso EXIGE:

1. `git rm backend/metrics.py` (no commit)
2. `mkdir backend/metrics`
3. Criar `__init__.py` + 4 sub-módulos no mesmo commit
4. **Atenção CI:** se algum import lazy carrega `metrics` durante tests collection, pode falhar até `__init__.py` estar populado. Validar com pytest dry run antes de push.

### Process — ordem sugerida

1. Read `metrics.py` integral; categorizar cada métrica (Counter/Histogram/Gauge/helper)
2. Branch: `refactor/RES-BE-006-metrics-split`
3. Commit 1: criar `metrics/__init__.py` vazio com TODOs (CI vai falhar — esperado em branch)
4. Commit 2..5: criar cada sub-módulo, mover métricas, ajustar `__all__`
5. Commit 6: reescrever `__init__.py` como façade completa
6. Commit 7: deletar `metrics.py` arquivo
7. Run pytest local — full suite — confirmar zero regressão
8. Push, CI valida 108 importers

### Frameworks de teste

- pytest 8.x
- File location: `backend/tests/metrics/test_*.py`
- Marks: `@pytest.mark.timeout(30)`
- Fixtures: usar `prometheus_client.CollectorRegistry()` isolado para evitar leakage entre testes (como já feito em `test_metrics.py` existente)

### Convenções

- Imports absolutos: `from metrics.counters import X` (em sub-módulos para evitar relativo)
- `__all__` explícito por sub-módulo
- Type hints obrigatórios
- Cada sub-módulo ≤500L (manter coesão)

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| ImportError em algum dos 108 importadores | Símbolo perdido — adicionar ao `__all__` correspondente; smoke test todos imports antes de merge |
| `/metrics` endpoint produção muda output (perdeu métrica) | Diff staging vs prod ANTES de deploy; rollback PR se diff |
| Circular import (metrics ↔ pipeline.budget ↔ ...) | Refator: extrair `metrics/types.py` com classes neutras; importar sob demanda dentro de funções |
| Grafana panels quebram | Métricas não foram renomeadas (proibido); se quebrar, é bug — restaurar nome via grep histórico |
| QA loop excede 5 iterações | Escalar @aiox-master; possível split em 2 PRs (counters+histograms vs gauges+registry) |

**Rollback completo:** revert PR. Façade preserva API; consumidores não percebem rollback. **MAS:** rollback de `git rm metrics.py` requer cuidado — verificar com `git revert` que arquivo é restaurado.

---

## Dependencies

**Entrada:**
- [RES-BE-001](RES-BE-001-audit-execute-without-budget.md) — gate CI
- [RES-BE-005](RES-BE-005-godmodule-split-pipeline.md) — validar pattern de façade primeiro
- [RES-BE-009](RES-BE-009-test-suite-triage.md) — suite saudável

**Saída:** Habilita stories que adicionam métricas (RES-BE-003, RES-BE-010, RES-BE-012) a editar arquivos pequenos focados, reduzindo fricção.

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | LOC + fan-in numéricos (1251L, 108) — escopo preciso. |
| 2 | Complete description | ✓ | Liga fan-in 108 → import circular risk → fricção em RES-BE-003/004. |
| 3 | Testable acceptance criteria | ✓ | 8 ACs incluindo `test_all_108_importers_resolve.py` (gate quantitativo). |
| 4 | Well-defined scope | ✓ | IN/OUT explicitos; renaming proibido (Grafana stability). |
| 5 | Dependencies mapped | ✓ | Entrada RES-BE-001+005+009; saída habilita RES-BE-003/010/012. |
| 6 | Complexity estimate | ✓ | L (5-7 dias) coerente — Sprint 5 após RES-BE-005 estabilizado. |
| 7 | Business value | ✓ | "Reduz fricção em adicionar métricas; risk de import circular eliminado." |
| 8 | Risks documented | ✓ | 5 riscos incluindo `git rm metrics.py` rollback nuance — atenção operacional. |
| 9 | Criteria of Done | ✓ | 12 itens incluindo smoke diff `/metrics` staging vs prod. |
| 10 | Alignment with PRD/Epic | ✓ | Habilita stories que adicionam métricas (RES-BE-003/010/012) — alinhado com Goal do EPIC. |

### Required Fixes

Nenhuma — TODO @architect em AC3 (decisão arquivo vs pacote) tem recomendação clara em Dev Notes ("transformar `metrics.py` arquivo em `backend/metrics/` pacote") + checklist de execução em "Process — ordem sugerida". @architect tem material suficiente para decidir no Phase 3.

### Observations

- Test `test_all_108_importers_resolve.py` é gate quantitativo forte — protege contra símbolo "perdido" no façade.
- Sprint 5 (após RES-BE-005 mergeado) é sequenciamento correto — aplica lições aprendidas do split anterior.
- Renaming proibido é regra clara (quebra Grafana alerts) — boa governança.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — split god-module metrics.py (108 fan-in) | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Story exemplar — 108 importer test gate quantitativo. Status: Draft → Ready. | @po (Pax) |
