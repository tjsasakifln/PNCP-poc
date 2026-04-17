# STORY-6.6: Mutation Testing Stryker (G-012)

**Priority:** P3 | **Effort:** M (8-16h) | **Squad:** @qa + @dev | **Status:** Ready for Review
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 7+

## Story
**As a** SmartLic, **I want** mutation testing em backend critical paths, **so that** test quality (não só coverage) seja medido.

## Acceptance Criteria
- [x] AC1: `mutmut>=2.4.0` setup — `backend/requirements-dev.txt` + `backend/setup.cfg` com config para 4 módulos
- [x] AC2: Baseline documentado em `backend/tests/mutation_baseline.md` (run bloqueado por limitação de ambiente — ver detalhe abaixo)
- [ ] AC3: Mutation score >70% — **DEFERRED**: baseline será medido pelo CI semanal na primeira run pós-merge (domingo 6am UTC). Ver follow-up abaixo.
- [x] AC4: `.github/workflows/mutation-testing.yml` — weekly Sunday 6am UTC + workflow_dispatch, artifact upload, GitHub Step Summary

## Tasks
- [x] Tool setup (mutmut + setup.cfg config)
- [ ] Run + fix surviving mutants — *deferred to CI; ambiente Windows sem WSL2*
- [x] CI workflow (mutation-testing.yml)

## Dev Notes

### Limitação de Ambiente (Windows — mutmut issue #397)

`mutmut` **não suporta Windows nativo**
([issue #397](https://github.com/boxed/mutmut/issues/397)).
O ambiente de desenvolvimento é Windows 11 Pro. WSL2 não está disponível
(virtualização não habilitada na máquina).

**Consequência:** AC2 produz o documento de baseline com escopo estimado, mas
sem scores reais. A primeira run do workflow semanal (`mutation-testing.yml`)
produzirá os scores definitivos.

### Configuração aplicada

```ini
[mutmut]
paths_to_mutate=filter/,llm_arbiter/,consolidation/,quota/
tests_dir=tests/
runner=python -m pytest -x -q --timeout=30 --ignore=tests/fuzz --ignore=tests/integration
```

**Escopo estimado:** ~26 arquivos, ~7.200 linhas, ~1.150-1.650 mutantes.

### AC3 — Baseline Medido

**AC3 baseline medido: PENDENTE (bloqueado por ambiente Windows)**

Após a primeira run CI (domingo pós-merge), atualizar `backend/tests/mutation_baseline.md`
com os scores reais. Se todos os 4 módulos ≥ 70%, marcar `[x]` aqui.
Se algum módulo < 70%, criar **STORY-6.6.1 (mutation tuning)** com adições de
testes para os mutantes sobreviventes.

### Módulos por ordem de execução (menor → maior)

1. `consolidation/` (~1.100 linhas)
2. `quota/` (~1.600 linhas)
3. `llm_arbiter/` (~1.600 linhas)
4. `filter/` (~2.900 linhas — deixar por último)

## File List
| File | Action |
|------|--------|
| `backend/requirements-dev.txt` | Modified — added `mutmut>=2.4.0` |
| `backend/setup.cfg` | Created — `[mutmut]` config section |
| `backend/tests/mutation_baseline.md` | Created — baseline doc with scope + Windows limitation |
| `.github/workflows/mutation-testing.yml` | Created — weekly cron + manual dispatch |

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-16 | 1.1 | AC1+AC2+AC4 complete; AC3 deferred — mutmut not available on Windows dev env (no WSL2). Baseline document created; scores pending first CI run. | @qa + @dev |
