# EPIC-BTS-2026Q2 — Backend Tests Structural Stabilization

**Status:** Ready
**Priority:** P0 — Gate Blocker (Backend Tests red em main há 20+ runs consecutivos)
**Estimated Effort:** L (10-16h distribuído em 10 stories)
**Sprint:** 2026-Q2-S5 (próximo sprint após sessão de 2026-04-19)
**Owner:** @pm (Morgan) orchestration; @dev + @qa + @data-engineer execution

---

## Problema

`Backend Tests (PR Gate)` workflow falha em **208 testes em 68 arquivos** desde 2026-04-17, causando o CI-main-red state documentado em `docs/stories/2026-04/EPIC-CI-GREEN-MAIN-2026Q2`. A meta-story `STORY-CIG-BACKEND-SWEEP` (PR #383) já triagiou o conjunto em 30 stories-filhas, das quais 24 foram Done via Wave #386 (`45e4f70b`), 8+ foram fechadas como drift em PR #393 (2026-04-19), mas o gate do CI **segue vermelho** — runs de merge continuam via admin-bypass como único mecanismo de ship, violando a disciplina de Zero Quarentena.

Este epic ataca as 208 falhas remanescentes em **10 stories agrupadas por causa raiz** (não por arquivo), priorizando superfícies de alto impacto (quota, pipeline, consolidação) sobre edge cases.

---

## Hipóteses de Causa Raiz (por categoria)

Com base em inspeção de amostras representativas, as 208 falhas se distribuem em 5 categorias principais:

1. **Mock-drift** (~60%) — refactors movem símbolos, mocks continuam apontando para paths antigos (mesmo padrão das 8 drift stories fechadas em PR #393 via verificação empírica)
2. **Assertion-drift** (~20%) — valores esperados no teste ficaram atrás dos valores de produção (ex: STORY-4.4 Time Budget Waterfall já tocou 9 timeout asserts)
3. **Integration externa não disponível** (~10%) — testes que precisam de Redis/Supabase/OpenAI real em CI
4. **Imports quebrados** (~5%) — ex: PNCP_TIMEOUT_PER_UF_DEGRADED migrado de `pncp_client` para `config.pncp` (fixado em PR #392)
5. **Flakiness** (~5%) — testes com race conditions, timing sensíveis (ex: asyncio tasks não aguardadas)

---

## Meta

- **CI Green:** `Backend Tests (PR Gate)` passa com 0 failed por **10 runs consecutivos** em main
- **Zero Quarentena:** nenhum `@pytest.mark.skip` ou `@pytest.mark.xfail` novo introduzido nesta epic (exceções documentadas via STORY-CIG-BACKEND-SWEEP triage row com severidade aprovada por @po)
- **Coverage:** threshold 70% mantido (não regrede)

---

## Stories (10)

| ID | Escopo | Testes | Effort | Prioridade |
|----|--------|--------|--------|------------|
| STORY-BTS-001 | Quota & Plan Capabilities | 35 failures | M (3-5h) | P0 |
| STORY-BTS-002 | Pipeline Resilience Layer | 30 failures | M (3-5h) | P0 |
| STORY-BTS-003 | Database Optimization & Reconciliation | 15 failures | S (2-3h) | P1 |
| STORY-BTS-004 | LLM Zero-Match & Filter Pipeline | 16 failures | S (2-3h) | P1 |
| STORY-BTS-005 | Consolidation & Multi-Source | 19 failures | M (3-5h) | P1 |
| STORY-BTS-006 | Search Pipeline & Async Flow | 13 failures | S (2-3h) | P1 |
| STORY-BTS-007 | Integration Tests (real external services) | 5 failures | S (2-3h) | P2 |
| STORY-BTS-008 | Critical Path & Concurrency | 18 failures | M (3-5h) | P1 |
| STORY-BTS-009 | Observability & Infra Drift | 20 failures | S (2-3h) | P2 |
| STORY-BTS-010 | Billing, Partners, Feature Flags | 15 failures | S (2-3h) | P1 |

**Mapeamento total:** 186 failures nas 10 stories + ~22 misc (re-triagem feita em STORY-BTS-003/005/009 conforme RCA confirmar).

---

## Ordem de Execução Recomendada

```
Wave 1 (P0): BTS-001 + BTS-002 (desbloqueiam 65 testes, 31% do total, foundation quota+pipeline)
Wave 2 (P1): BTS-003 + BTS-004 + BTS-005 + BTS-006 + BTS-008 + BTS-010 (98 testes, 47%)
Wave 3 (P2): BTS-007 + BTS-009 (25 testes, 12%)
```

Stories podem ir em paralelo por @dev distintos — dependências documentadas por story.

---

## Escopo fora do epic (Kill List)

- **Não reescrever tests-vizinhos-que-passam.** Cada story corrige apenas o seu subset de failures; se `pytest` passa já, não tocar.
- **Não introduzir novos tests.** Apenas restaurar o gate atual. Novos tests vão para stories de feature.
- **Não refatorar produção além do mínimo necessário para teste passar.** Mock-drift é geralmente fix no teste, não na produção.

---

## Definition of Done do Epic

- [ ] Todas 10 stories `Status: Done`
- [ ] `pytest backend/tests/ -q --timeout=30` PASS local (0 failed)
- [ ] `gh run list --branch main --limit 10 --workflow "Backend Tests (PR Gate)" --json conclusion` retorna 10 `success` consecutivos
- [ ] `EPIC-CI-GREEN-MAIN-2026Q2` pode ser fechado (Backend track completa)
- [ ] Branch protection rules de main podem voltar a ser **enforced** (sem admin-bypass)

---

## Change Log

- **2026-04-19** — @sm (River) + @pm (Morgan): Epic criado. 208 failures triagiadas em 10 stories. Status Ready.
