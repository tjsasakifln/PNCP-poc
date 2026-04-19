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

## Stories (11 após split @po 2026-04-19)

| ID | Escopo | Testes | Effort | Prioridade | @po Status |
|----|--------|--------|--------|------------|------------|
| STORY-BTS-001 | Quota & Plan Capabilities | 35 failures | M (3-5h) | P0 | ✅ GO 8/10 |
| STORY-BTS-002 | Pipeline Resilience Layer | 30 failures | M (3-5h) | P0 | ✅ GO 8/10 |
| STORY-BTS-003 | Database Optimization & Reconciliation | 15 failures | S (2-3h) | P1 | ✅ GO 7/10 |
| STORY-BTS-004 | LLM Zero-Match & Filter Pipeline | 16 failures | S (2-3h) | P1 | ✅ GO 7/10 |
| STORY-BTS-005 | Consolidation & Multi-Source | 19 failures | M (3-5h) | P1 | ✅ GO 7/10 |
| STORY-BTS-006 | Search Pipeline & Async Flow | 13 failures | S (2-3h) | P1 | ✅ GO 7/10 |
| STORY-BTS-007 | Integration Tests → External Workflow | 5 failures | S (2-3h) | P2 | Ready (re-valida após correção 2026-04-19) |
| STORY-BTS-008 | Critical Path & Concurrency | 18 failures | M (3-5h) | P1 | ✅ GO 8/10 |
| STORY-BTS-009 | Observability & Infra Drift | 20 failures | S (2-3h) | P2 | ✅ GO 7/10 |
| ~~STORY-BTS-010~~ | ~~Billing, Partners, Feature Flags + Misc~~ | — | — | — | ❌ Superseded (split) |
| STORY-BTS-010a | Billing, Partners & Feature Flags | 14 failures | M (3-5h) | P1 | Ready (criada 2026-04-19 pós-split) |
| STORY-BTS-010b | PNCP, Security & Infra Misc | 16 failures | M (3-5h) | P1 | Ready (criada 2026-04-19 pós-split; `test_digest_job` reatribuído de BTS-010a) |

**Mapeamento total:** 201 failures cobertas nas 11 stories ativas (35+30+15+16+19+13+5+18+20+14+16) + ~7 misc (a confirmar via RCA). Após re-validação @po 2026-04-19, BTS-010a=14 e BTS-010b=16 (total 30 = original BTS-010, contagens reconciliadas).

---

## Ordem de Execução Recomendada

```
Wave 1 (P0): BTS-001 + BTS-002 (65 testes, foundation quota+pipeline)
Wave 2 (P1): BTS-003 + BTS-004 + BTS-005 + BTS-006 + BTS-008 + BTS-010a + BTS-010b (112 testes)
Wave 3 (P2): BTS-007 + BTS-009 (25 testes)
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
- **2026-04-19** — @po (Pax): Validação completa. 8 stories GO (BTS-001/002/003/004/005/006/008/009). 2 NO-GO corrigidas no mesmo dia: BTS-007 (AC bifurcado — direção (a) emitida), BTS-010 (DoD impreciso — split em 010a+010b aprovado). Matriz + análise individual em `po-validation-report.md`.
- **2026-04-19** — @sm (River): Correções aplicadas. BTS-007 reescrita (path (a) único, +Valor/Riscos). BTS-010 marcada Superseded, criadas BTS-010a (billing 14 testes, M) e BTS-010b (PNCP/security 13 testes, M). Epic stories: 10 → 11 ativas. Todas Ready.
- **2026-04-19** — @po (Pax): Re-validação 11/11 GO. Reconciliação BTS-010a/010b: `test_digest_job.py` movido de 010a para 010b (afinidade jobs/cron); contagens corrigidas → BTS-010a=14 (5 arquivos), BTS-010b=16 (12 arquivos), soma=30 = original BTS-010. EPIC **APROVADO** para implementação. Detalhes em `po-validation-report.md` seção "Re-validação 2026-04-19 (pós-correções)".
