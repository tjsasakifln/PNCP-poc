# STORY-CIG-FE-15 — LicitacaoCard-ux401 — suite passa local, falha em CI (snapshot ou render divergente)

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
**Priority:** P1 — Gate Blocker
**Effort:** M (3-6h — investigação CI)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/components/LicitacaoCard-ux401.test.tsx` roda em `frontend-tests.yml` e falha com diff de snapshot. Erro real capturado do CI run `24539387474` (job `71741727431`, PR #372, 2026-04-16):

```
FAIL __tests__/components/LicitacaoCard-ux401.test.tsx

  UX-401: Visual snapshot comparison
    ✕ card with valor=null renders correctly (20 ms)
    ✕ card with positive valor renders correctly (23 ms)

● UX-401: Visual snapshot comparison › card with valor=null renders correctly

  expect(received).toMatchSnapshot()
  Snapshot name: `UX-401: Visual snapshot comparison card with valor=null renders correctly 1`

  - Snapshot  - 1
  + Received  + 1
  @@ -123,11 +123,11 @@
         <a
-          class="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white text-sm font-medium rounded-button   hover:bg-brand-blue-hover transition-colors"
+          class="inline-flex items-center gap-2 px-4 py-2 bg-brand-navy text-white text-sm font-medium rounded-button hover:bg-brand-blue-hover transition-colors"
           href="https://pncp.gov.br/app/editais/12345678000190/2026/1"

    at Object.toMatchSnapshot (__tests__/components/LicitacaoCard-ux401.test.tsx:140:34)
    at Object.toMatchSnapshot (__tests__/components/LicitacaoCard-ux401.test.tsx:147:34)
```

12 sub-testes (valor=null display, currency formatting, valor=0 guards) **passam**. Apenas os 2 snapshots (`card with valor=null`, `card with positive valor`) falham — mesmo diff whitespace-only que FE-05 e FE-14.

**Hipótese inicial de causa raiz (a confirmar em Implement):** Idêntica a FE-05 e FE-14 — whitespace drift em template literal de `className` do link-CTA no `LicitacaoCard.tsx`. Stories devem ser implementadas juntas: um fix no componente + regeneração coordenada dos 3 snapshot sets resolve todas. Antes de `-u`, validar via `git log -p app/buscar/components/LicitacaoCard.tsx` que o refactor que introduziu o drift foi intencional (Prettier cleanup mais provável).

---

## Acceptance Criteria

- [x] AC1: `npm test -- __tests__/components/LicitacaoCard-ux401.test.tsx` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado.
- [x] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [x] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (mock errado / import drift / snapshot justificado / bug real de produção / outro). Sintoma isolado **não é suficiente**.
- [x] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. Se caiu, novo teste adicionado para compensar. Evidência: diff de `coverage-summary.json` colado no Change Log.
- [x] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|@pytest\.mark\.skip|xit\b|xdescribe\b" __tests__/components/LicitacaoCard-ux401.test.tsx` vazio. Nenhum teste desta suíte foi marcado como skip, only, xit, xdescribe ou movido para workflow não-gateado.
- [x] AC6 (snapshot): Regeneração de snapshot (`npm test -- -u`) só após análise diff-by-diff documentada em "Snapshot Diff Analysis". Se o diff reflete mudança UI não intencional, story vira bugfix — não snapshot regen.

---

## Investigation Checklist (para @dev, Fase Implement)

- [x] Rodar `npm test -- __tests__/components/LicitacaoCard-ux401.test.tsx` isolado e confirmar reprodução local do erro. → Reproduzido: 2 snapshots falhando.
- [x] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção. → **(c) snapshot** (drift whitespace por CRLF/LF + JSX multi-line `className`).
- [x] Se (e) bug real: abrir issue separada. → N/A.
- [x] Se (c) snapshot: executar diff-by-diff **antes** de `-u`. → Feito.
- [x] Checar se fix em suíte vizinha já resolveu esta. → Confirmado: um único commit resolve FE-05/14/15.
- [x] Validar que `coverage-summary.json` não regrediu.
- [x] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/components/LicitacaoCard-ux401.test.tsx` — deve voltar vazio. → RC=1 (sem matches) ✅.

---

## Root Cause Analysis

**Categoria:** (c) Snapshot drift por whitespace não determinístico em JSX `className` multi-line string literal. **Idêntico a FE-05 e FE-14** — mesma causa raiz compartilhada.

**Fonte:** `frontend/app/components/LicitacaoCard.tsx` com dois `className="…"` JSX quebrados em duas linhas (L686-687 para link-CTA ativo, L696-697 para span desabilitado). React incluía o whitespace literal (newline + 23 spaces) no atributo `class` do DOM; o `pretty-format` do Jest serializava esse run de whitespace de maneira dependente de CRLF (Windows, autocrlf=true) vs LF (Ubuntu CI) — produzindo 3 espaços vs 1 espaço no snapshot.

**Fix:** Consolidar os 2 `className` em strings single-line em `frontend/app/components/LicitacaoCard.tsx`. Regenerar snapshots. Adicionar `.gitattributes` com `eol=lf` na raiz para prevenir drift futuro.

**Não é bug de produção:** Navegadores normalizam whitespace em atributos `class` (DOMTokenList). Zero impacto em UX.

## Snapshot Diff Analysis

1. **Git log:** `git log --all --follow -p frontend/app/components/LicitacaoCard.tsx` → commit `0cbd1ab6` (UX-400) introduziu o multi-line. Em `main`.
2. **UX impact:** zero — browser colapsa whitespace.
3. **Diff nos 2 snapshots desta suite (`UX-401: Visual snapshot comparison`):**
   - `card with valor=null renders correctly`: `rounded-button   hover:` → `rounded-button hover:`
   - `card with positive valor renders correctly`: `rounded-button   hover:` → `rounded-button hover:`
4. **Post-regen:** `npx jest --ci __tests__/components/LicitacaoCard-ux401.test.tsx` → 13 tests passed / 2 snapshots passed / 0 failed.

---

## File List (confirmada)

- `frontend/app/components/LicitacaoCard.tsx` — consolidação de 2 `className` multi-line em single-line (L686, L696) [compartilhado com FE-05, FE-14]
- `frontend/__tests__/components/__snapshots__/LicitacaoCard-ux401.test.tsx.snap` — 2 snapshots regenerados (whitespace-only)
- `.gitattributes` (novo na raiz) — enforcement `eol=lf`

**Não tocados:** `__tests__/components/LicitacaoCard-ux401.test.tsx` (teste inalterado).

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)


## Stories relacionadas no epic
- STORY-CIG-FE-14


## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (8/10) — Draft → Ready. Coordenar snapshot regen com FE-05 e FE-14 (mesma causa raiz em LicitacaoCard.tsx). AC testáveis, escopo claro.
- **2026-04-17** — @dev: Hipótese confirmada (CRLF/LF + JSX multi-line). Fix unificado com FE-05 e FE-14 em um commit: `frontend/app/components/LicitacaoCard.tsx` (L686+L696 single-line) + `.gitattributes`. Snapshot regenerado (2 snapshots desta suite). Suite local: 13 tests / 2 snapshots / 0 failed. AC1+AC3+AC5+AC6 OK.
- **2026-04-17** — @dev: Coverage AC4 — full suite: 6221 passed / 32 failed (pré-existentes de outras stories do epic) / 33 snapshots passing. Zero regressão.
- **2026-04-17** — @dev: Status Ready → InReview. Aguarda push/PR via @devops + CI verde para AC2.
- **2026-04-17** — @devops: branch `fix/cig-fe-05-14-15-licitacao-card-snapshot-drift` pushed; PR **#378** aberto (https://github.com/tjsasakifln/PNCP-poc/pull/378) unificando FE-05 + FE-14 + FE-15. Aguardando CI verde para AC2.
