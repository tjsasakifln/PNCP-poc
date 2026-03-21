# DEBT-S0.3: Test Infrastructure -- Eliminar Pollution
**Epic:** EPIC-DEBT
**Sprint:** 0
**Priority:** P0
**Estimated Hours:** 12h
**Assignee:** TBD

## Objetivo

Eliminar test pollution que causa flaky tests e bloqueia velocidade do time. Atualmente 8+ padroes de poluicao documentados (sys.modules injection, importlib.reload, MagicMock leakage, global singletons). `run_tests_safe.py --parallel` mitiga cross-file mas intra-file persiste. 4 quota tests sao flaky. Meta: zero flakes em modo sequencial.

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| SYS-14 | Test pollution documentada mas nao eliminada. 8+ padroes (sys.modules, importlib.reload, MagicMock leakage, global singletons). 4 quota tests flaky. Bloqueia velocidade de todo o time. | MEDIUM (elevado a P0) | 12h |

## Acceptance Criteria

- [ ] AC1: `python scripts/run_tests_safe.py --parallel 1` (modo sequencial, sem isolamento subprocess) passa 100% dos testes sem flakes
- [ ] AC2: Zero usos de `sys.modules["arq"] = MagicMock()` sem cleanup (usar conftest fixture exclusivamente)
- [ ] AC3: Zero usos de `importlib.reload()` em testes (substituir por monkeypatch ou conftest fixtures)
- [ ] AC4: Todos global singletons (supabase_cb, plan cache, etc.) resetados via conftest autouse fixtures
- [ ] AC5: 4 quota tests flaky passam consistentemente em 10 execucoes consecutivas
- [ ] AC6: Nenhum teste usa `asyncio.get_event_loop().run_until_complete()` (usar `async def` + `@pytest.mark.asyncio`)
- [ ] AC7: Baseline de flaky tests documentado: 0

## Tasks

- [ ] T1: Auditar todos usos de `sys.modules[...]` em testes -- listar arquivos e padroes
- [ ] T2: Substituir `sys.modules["arq"]` raw por conftest `_isolate_arq_module` fixture
- [ ] T3: Eliminar todos `importlib.reload()` patterns -- substituir por `monkeypatch.setattr` ou fixtures
- [ ] T4: Identificar e resetar todos global singletons em conftest autouse fixtures
- [ ] T5: Corrigir 4 quota tests flaky (identificar dependencia de estado compartilhado)
- [ ] T6: Substituir `run_until_complete()` por `async def` + `@pytest.mark.asyncio` onde existir
- [ ] T7: Rodar full suite 10x consecutivo para validar zero flakes
- [ ] T8: Documentar padroes proibidos em CLAUDE.md / contributing guide

## Testes Requeridos

- [ ] `run_tests_safe.py --parallel 1` passa 100% (modo sequencial)
- [ ] `run_tests_safe.py --parallel 4` passa 100% (modo paralelo)
- [ ] 10 execucoes consecutivas sem flakes
- [ ] Backend test count >= 7332 (nenhum teste removido)

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **Elevado a P0 por @qa** -- test pollution bloqueia velocidade de PRs de todo o time.
- Padroes conhecidos de pollution estao documentados em MEMORY.md secao "Critical test pollution patterns to avoid".
- Rodar full suite apos cada fix individual -- pollution fixes podem quebrar testes que dependiam do estado poluido.
- `_isolate_arq_module` conftest autouse fixture ja existe -- garantir que TODOS os testes usam ela.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secao "Sistema" (SYS-14)
- Conftest: `backend/tests/conftest.py`
- Safe runner: `scripts/run_tests_safe.py`
- MEMORY.md: secao "Critical test pollution patterns to avoid"
