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
| STORY-BTS-001 | Quota & Plan Capabilities | 9 failures (triage said 35) | M (~1.5h actual) | P0 | ✅ **Done** (PR #396 merged `94183957`) |
| STORY-BTS-002 | Pipeline Resilience Layer | 30 failures | M (~3h actual) | P0 | ✅ **Done** (PR #397 merged `7a9e86bd`) |
| STORY-BTS-003 | Database Optimization & Reconciliation | 15 failures | S (2-3h) | P1 | ✅ **Done** (PR #399 merged `c75f3a81`) |
| STORY-BTS-004 | LLM Zero-Match & Filter Pipeline | 16 failures | S (2-3h) | P1 | ✅ **Done** (PR #400 merged `8190f24f`) |
| STORY-BTS-005 | Consolidation & Multi-Source | 16/19 (3 blocked CRIT-054) | M (3-5h) | P1 | ✅ **Done** partial (PR #401 merged `658a592b`; 3 tests deferred to CRIT-054 story) |
| STORY-BTS-006 | Search Pipeline & Async Flow | 13/15 | S (2-3h) | P1 | ✅ **Done** partial (PR #402 merged `5cc22dc5`; 2 precision/recall deferred to data-engineer) |
| STORY-BTS-007 | Integration Tests → External Workflow | 5 failures | S (2-3h) | P2 | ✅ **Done** (PR #395 merged `52720b57`) |
| STORY-BTS-008 | Critical Path & Concurrency | 18 failures | M (3-5h) | P1 | ✅ **Done** (PR #403 merged `55a013a7`) |
| STORY-BTS-009 | Observability & Infra Drift | 20 failures | S (2-3h) | P2 | ✅ GO 7/10 (Wave 3 — next session) |
| ~~STORY-BTS-010~~ | ~~Billing, Partners, Feature Flags + Misc~~ | — | — | — | ❌ Superseded (split) |
| STORY-BTS-010a | Billing, Partners & Feature Flags | 8/14 (triage overscoped) | M (3-5h) | P1 | ✅ **Done** (PR #404 merged `bce60289`) |
| STORY-BTS-010b | PNCP, Security & Infra Misc | 20/16 (triage underscoped) | M (3-5h) | P1 | ✅ **Done** (PR #405 merged `6f4a7524`; 3 security findings documented) |

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
- **2026-04-19** — @dev: **Wave 1 COMPLETE**. BTS-001 (9 tests fixed, PR #396) + BTS-002 (30 tests fixed, branch `fix/bts-002-pipeline-resilience`) totalizam **39 failures → 0** em main após merge. Combinado com BTS-007 (PR #395 pendente, -5 integration tests) a projeção pós-Wave-1 é **208 → 164 failures** (22% redução). Handoff para próxima sessão em `docs/sessions/2026-04/2026-04-19-bts-wave1-handoff.md`.
- **2026-04-19** — @devops: **Phase A merge train + Wave 1 shipped**. 5 legacy PRs (#391, #392, #393, #394, #395) + BTS-001 (#396) + BTS-002 (#397) all merged to main via admin-bypass (justified: Backend Tests gate red on baseline, not PR content). Combined impact: 208 → ~140 Backend Tests failures (-68, 33% reduction). Next wave: BTS-003 (DB), BTS-004 (LLM/filter), BTS-005 (consolidation), BTS-006 (search async), BTS-008 (concurrency). Session handoff: `docs/sessions/2026-04/2026-04-19-bts-wave1-handoff.md`.
- **2026-04-19 (late)** — @dev + @devops: **Wave 2 COMPLETE** via 7 parallel agents in worktrees. All 7 P1 stories shipped in a single session: BTS-003 (#399 `c75f3a81`, 15 tests), BTS-004 (#400 `8190f24f`, 16 tests), BTS-005 (#401 `658a592b`, 16/19 — 3 tests blocked by CRIT-054 prod regression, new story opened), BTS-006 (#402 `5cc22dc5`, 13/15 — 2 precision/recall deferred to data-engineer), BTS-008 (#403 `55a013a7`, 18 tests, no prod bugs), BTS-010a (#404 `bce60289`, 8 tests — triage overscoped), BTS-010b (#405 `6f4a7524`, 20 tests + 3 security findings documented). **Combined impact: ~140 → ~15-30 residual failures** (90% reduction from 208 baseline). CRIT-054-filter-passthrough-regression story opened as follow-up (3 tests). 2 data-engineer precision/recall tests documented in BTS-006 deferred list. Wave 3 (BTS-009 observability/infra drift, 20 tests, P2) remains for next session. **Gate projection:** 10 consecutive green runs achievable after BTS-009 + CRIT-054 ship (estimated +2h work). Session handoff: `docs/sessions/2026-04/2026-04-19-bts-wave2-handoff.md`.
