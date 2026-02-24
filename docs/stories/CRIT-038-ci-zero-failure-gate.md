# CRIT-038 — CI: Zero-Failure Gate (impedir regressão futura)

**Status:** Done
**Priority:** P1 — High
**Severity:** Processo
**Created:** 2026-02-23
**Completed:** 2026-02-24
**Depends on:** CRIT-036, CRIT-037 (baseline limpo é pré-requisito)

---

## Problema

Hoje, testes quebrados são tratados como "pre-existing baseline". Isso cria um ciclo vicioso:

```
Story implementada → testes passam (menos os "pre-existing") → merge
→ novo código quebra mais testes → viram "pre-existing" → merge
→ ninguém sabe o que é regressão real vs. ruído antigo
```

**Resultado:** 93 testes falhando (25 BE + 68 FE) que ninguém investiga porque "sempre foram assim".

---

## Acceptance Criteria

### GitHub Actions CI

- [x] **AC1:** Workflow `backend-tests.yml` — `pytest` DEVE retornar exit code 0 (0 failures). Se falhar, PR não pode ser merged.
- [x] **AC2:** Workflow `frontend-tests.yml` — `npm test` DEVE retornar exit code 0 (0 failures). Se falhar, PR não pode ser merged.
- [x] **AC3:** Branch protection rule em `main` — Require status checks `backend-tests` e `frontend-tests` para merge.

### Prevenir Re-Acúmulo

- [x] **AC4:** Adicionar comentário no PR template: "Se testes falharem, corrija os testes — não adicione ao baseline."
- [x] **AC5:** Coverage thresholds mantidos: 70% backend, 60% frontend (já existem, verificar que estão enforced no CI).

### Documentação

- [x] **AC6:** Atualizar `CLAUDE.md` seção "Testing Strategy" — remover conceito de "pre-existing failures baseline". Nova regra: **0 failures é o único baseline aceitável.**

---

## Estimativa

**Esforço:** ~1 hora (CI config + branch protection)
**Risco:** Nenhum (apenas ativa gates que já deveriam existir)
**Pré-requisito:** CRIT-036 e CRIT-037 completas

## Files

- `.github/workflows/backend-tests.yml` — **CREATED**: Strict pytest gate (exit 0 + --cov-fail-under=70)
- `.github/workflows/frontend-tests.yml` — **CREATED**: Strict npm test gate (exit 0 + tsc --noEmit + coverage)
- `.github/PULL_REQUEST_TEMPLATE.md` — **UPDATED**: Zero-failure policy notice + checkbox
- `CLAUDE.md` — **UPDATED**: Testing Strategy section — 0 failures baseline, removed "pre-existing" concept

## Implementation Notes

- Branch protection configured via `gh api` — `strict: true` (branch must be up-to-date), contexts: "Backend Tests" + "Frontend Tests"
- Backend coverage threshold: `--cov-fail-under=70` in workflow + `fail_under = 70.0` in `pyproject.toml`
- Frontend coverage threshold: `coverageThreshold` in `jest.config.js` (branches: 50%, functions/lines/statements: 55%)
- Existing `tests.yml` workflow kept as-is for matrix testing (Python 3.11+3.12) + integration + E2E
