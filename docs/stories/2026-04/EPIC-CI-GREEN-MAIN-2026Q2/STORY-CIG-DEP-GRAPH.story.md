# STORY-CIG-DEP-GRAPH — Dependency Review — habilitar Dependency Graph OU remover required-check

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
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

- [ ] AC1: Decisão registrada em "Root Cause Analysis" entre 2 opções: (a) habilitar Dependency Graph em `Settings → Code security and analysis` (preferível); (b) remover job `Dependency Review` da required-checks list com justificativa técnica (ex.: "plano do repo não expõe dep-graph, custo de viabilizar > benefício").
- [ ] AC2: Se (a): último run da CodeQL Security Scan em `main` mostra job `Dependency Review` com conclusion `SUCCESS`. Link run ID no Change Log. Se (b): `gh api repos/tjsasakifln/PNCP-poc/branches/main/protection` confirma remoção do check; `Dependency Review` não aparece mais como required.
- [ ] AC3: Causa raiz documentada: por que dep-graph estava desabilitado (setting do repo? plan constraint? toggle acidental?). Sem "Fix: habilitei, foi". Explicar o "por quê" da desativação anterior.
- [ ] AC4: N/A (story de configuração, não há cobertura de código).
- [ ] AC5 (NEGATIVO): Se opção (b) foi escolhida, required-checks list tem apenas **1 item removido** (Dependency Review) — nenhum outro check foi silenciosamente degradado na mesma mudança. `gh api` diff anexado ao Change Log.

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

_(preenchido por @dev em Implement após confirmar causa)_

## File List (preditiva, a confirmar em Implement)

- `.github/workflows/codeql.yml (se remover job)`
- `Settings → Code security and analysis (Dependency Graph toggle)`
- `Branch protection rules (required checks)`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)



## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
