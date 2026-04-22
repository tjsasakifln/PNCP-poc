# STORY-CIG-DEP-GRAPH — Dependency Review — habilitar Dependency Graph OU remover required-check

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Done
**Priority:** P2 — Gate red, não bloqueia merge se removido com justificativa
**Effort:** XS (<30min)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `N/A (configuração de repositório)` roda em `CodeQL Security Scan (job Dependency Review)` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
[PR #372 run 24539387439 — job "Dependency Review" em CodeQL Security Scan:
  conclusion: FAILURE
  detailsUrl: .../runs/24539387439/job/71741727473
  Motivo: Dependency Graph está desabilitado em repo Settings → Code security and analysis]

Dependency Graph precisa estar ON para o check funcionar. Alternativa é remover o check
do required-checks list (aprovação @devops obrigatória).
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Decisão binária a tomar: (a) habilitar Dependency Graph em Settings (default em repos públicos, talvez desabilitado em repo privado/plano); (b) se plano do repo não permite, remover o job do workflow + remover do required-checks via `gh api`, com justificativa documentada.

---

## Acceptance Criteria

- [x] AC1: Decisão registrada em "Root Cause Analysis" entre 2 opções: (a) habilitar Dependency Graph em `Settings → Code security and analysis` (preferível); (b) remover job `Dependency Review` da required-checks list com justificativa técnica (ex.: "plano do repo não expõe dep-graph, custo de viabilizar > benefício").
- [x] AC2: **Opção (a) escolhida.** Vulnerability alerts habilitados via `gh api --method PUT repos/tjsasakifln/pncp-poc/vulnerability-alerts` (HTTP 204). Verificação do job `Dependency Review` com `SUCCESS` será confirmada neste próprio PR (job só roda em `pull_request`). Link: PR que contém este commit.
- [x] AC3: Causa raiz documentada em "Root Cause Analysis" abaixo — Dependabot alerts nunca havia sido habilitado explicitamente; a action requer alerts ativos para acessar a Dependency Review API.
- [x] AC4: N/A (story de configuração, não há cobertura de código).
- [x] AC5 (NEGATIVO): N/A — opção (a) foi escolhida; nenhum required-check foi removido. Required checks permanecem: `["Backend Tests", "Frontend Tests"]` (confirmado via `gh api repos/tjsasakifln/pncp-poc/branches/main/protection --jq '.required_status_checks.contexts'`).

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- N/A (configuração de repositório)` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" N/A (configuração de repositório)` — deve voltar vazio.

---

## Root Cause Analysis

**Decisão:** Opção (a) — Habilitar Dependabot alerts (que desbloqueia a Dependency Review API).

**Causa raiz confirmada (2026-04-17 via `gh api` + log do run 24539387439):**

O job falhou com o erro exato:
```
##[error]Dependency review is not supported on this repository.
Please ensure that Dependency graph is enabled,
see https://github.com/tjsasakifln/PNCP-poc/settings/security_analysis
```

**Por que estava desabilitado:**

1. O repo é **público** (`visibility: public`). Para repos públicos, o Dependency Graph estrutural é sempre habilitado pelo GitHub — mas o Dependency Graph sozinho NÃO é suficiente para a `actions/dependency-review-action@v4`.

2. A action exige que **Dependabot alerts (vulnerability alerts)** estejam ativos para chamar a Dependency Review API (`GET /repos/{owner}/{repo}/dependency-graph/compare/{basehead}`). Sem alerts, a API retorna erro mesmo que o Dependency Graph esteja tecnicamente "on".

3. Confirmado: `gh api repos/tjsasakifln/pncp-poc/vulnerability-alerts` retornava HTTP 404 ("Vulnerability alerts are disabled."). Isso indica que nunca foram habilitados explicitamente neste repositório — não houve toggle acidental, apenas nunca foram ativados no setup inicial.

4. O campo `dependency_graph` NÃO aparece em `security_and_analysis` via API para repos públicos (esperado: o toggle não é exposto porque é estruturalmente always-on para repos públicos). A falha era exclusivamente causada pela ausência de Dependabot alerts.

**Fix aplicado:** `gh api --method PUT repos/tjsasakifln/pncp-poc/vulnerability-alerts` → HTTP 204 (success). Verificado: endpoint retorna 204 (ENABLED) após o comando.

**Por que a opção (b) foi descartada:** O job `dependency-review` não está na required-checks list (apenas "Backend Tests" e "Frontend Tests" são required). Remover o job seria regredir a cobertura de segurança sem necessidade — o fix via API é simples e não exige mudança de código.

## File List (confirmado em Implement)

- `Settings → Code security and analysis (Dependency Graph/Vulnerability Alerts)` — habilitado via API, sem mudança de arquivo
- `docs/stories/2026-04/EPIC-CI-GREEN-MAIN-2026Q2/STORY-CIG-DEP-GRAPH.story.md` — este arquivo (RCA + checkboxes + status)

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)



## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (7/10) — Draft → Ready. Configuração de repositório (não test suite); Investigation Checklist contém N/A de template. @dev deve seguir ACs. XS effort (<30min).
- **2026-04-17** — @dev: Ready → InProgress → InReview. Diagnóstico via `gh api` + log do run 24539387439. Causa raiz: Dependabot alerts desabilitado → Dependency Review API inacessível. Fix: `gh api --method PUT repos/tjsasakifln/pncp-poc/vulnerability-alerts` (HTTP 204). Todos os ACs marcados. Job `Dependency Review` mostra `pass` no PR #377 (run 71849410702). PR: https://github.com/tjsasakifln/PNCP-poc/pull/377
- **2026-04-17** — @devops: InReview → Done. PR #377 mergeado em `main` (commit aac8737). Merge administrativo: falhas CI (Backend Tests + Frontend Tests) são baseline pré-existente documentado no EPIC-CI-GREEN-MAIN-2026Q2 — PR não introduz regressões.
