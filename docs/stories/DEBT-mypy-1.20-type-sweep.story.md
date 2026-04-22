# DEBT-mypy-1.20: Type Sweep para desbloquear mypy 1.20.1

**Sprint:** 2026-Q2 (oportunidade)
**Effort:** 4-8h (estimativa: depende do volume de type errors expostos)
**Priority:** MEDIUM
**Agent:** @dev (Dex)
**Status:** Ready
**Owner:** @dev
**Source:** Dependabot PR #413 (bump mypy 1.15.0 → 1.20.1)

## Context

Dependabot abriu PR #413 propondo bump de `mypy==1.15.0` para `mypy==1.20.1` em `backend/requirements-dev.txt`. mypy 1.20 introduz novas checks que expõem type errors pré-existentes no código — merge silencioso causaria quebra imediata no lint/typecheck em main (cluster pre-existing mas amplificado).

Sessões anteriores (floofy-sparkle 2026-04-20, ci-destravamento 2026-04-21) flagaram como decisão pendente. Decisão do usuário (2026-04-21): criar story DEBT, fechar #413, Dependabot reabre automaticamente em versões futuras (1.21+).

**Por que não pinar em 1.15 permanentemente:** 1.15 é de 2025-02; ecosystem está em 1.20+. Perder features como better PEP 695 support, improved overload resolution, narrower generic inference. Type errors que 1.20 detecta **são reais** — pinar é dívida crescente.

## Scope

| Task | Horas est. |
|------|-----------|
| Instalar mypy 1.20.1 em venv local + rodar contra `backend/` | 0.5h |
| Categorizar errors por módulo (top-N offenders) | 0.5h |
| Fix incremental por categoria (ou silenciar com justificativa via `# type: ignore[code]`) | 2-5h |
| Bump `mypy==1.20.1` em `backend/requirements-dev.txt` | 0.1h |
| Validar CI lint step passa | 0.3h |
| Fechar PR #413 com comentário linkando esta story + nova PR | 0.1h |

**IN scope:**
- Apenas `backend/` (frontend usa tsc, fora do escopo)
- Fix ou silenciar todos os novos errors de 1.20 contra o código atual
- Bump mypy para 1.20.1 no requirements-dev.txt

**OUT of scope:**
- Reformulação de type system (ex: migrar dict → TypedDict em massa)
- Remoção de `--ignore-missing-imports` flag global (pode ser subsequent story)
- Upgrade para 1.21+ (Dependabot reabrirá)

## Acceptance Criteria

- [ ] AC1: `mypy --config-file=backend/pyproject.toml backend/` roda clean em mypy 1.20.1 (zero errors)
- [ ] AC2: Cada novo `# type: ignore[code]` adicionado tem **comentário justificando** (não vazio)
- [ ] AC3: `backend/requirements-dev.txt` tem `mypy==1.20.1`
- [ ] AC4: CI workflow `Backend Code Quality` (ou equivalente) passa em PR de bump
- [ ] AC5: Nenhuma nova flag permissiva adicionada a `[tool.mypy]` (ex: `ignore_errors = true`, `--ignore-missing-imports` novo)
- [ ] AC6: PR #413 fechado com comentário "superseded by <new PR URL>"
- [ ] AC7: Lista dos top-N módulos com type errors documentada no PR body (para visibilidade do débito restante)

## Dependencies

- **Prerequisite:** Nenhuma — isolado de outros PRs
- **Unblocks:** Futuros Dependabot bumps de mypy (1.21+) podem mergear direto
- **Related:** PR #413 (Dependabot — será fechada como parte desta story)

## Risks

| Risk | Mitigação |
|------|-----------|
| Volume de errors > 50 | Categorizar + priorizar. Silenciar com `# type: ignore` onde fix é não-trivial. Fix real em story subsequente. |
| Novo error em código crítico (auth, billing) | Priorizar esses módulos primeiro; fix real (não `# type: ignore`) |
| Regressão funcional | Rodar `pytest` completo antes de push |
| mypy 1.21 sair antes do merge | Update target para 1.21.x — Dependabot já indicará |

## Tests Required

- [ ] Test: `mypy --no-incremental backend/` passes em 1.20.1 (0 errors, 0 warnings)
- [ ] Test: Pytest full suite (`pytest backend/ --timeout=30`) passa — zero regressions
- [ ] Test: CI workflow `Backend Code Quality` verde no PR

## Definition of Done

- [ ] Todos os ACs marcados
- [ ] PR aprovado por @qa (CONCERNS permitido se houver `# type: ignore` justificados)
- [ ] @devops faz merge após CI 100% verde
- [ ] PR #413 fechado com comentário de supersede

## Change Log

| Data | Autor | Evento |
|------|-------|--------|
| 2026-04-21 | @sm | Story created (Draft) |
| 2026-04-21 | @sm | Status → Ready (decisão do usuário na sessão prancy-pudding) |
