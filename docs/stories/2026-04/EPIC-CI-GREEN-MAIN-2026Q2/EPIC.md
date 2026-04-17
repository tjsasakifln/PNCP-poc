# EPIC-CI-GREEN-MAIN-2026Q2 — Consertar todos os testes falhando, levar `main` de vermelho a verde sustentável

**Sprint-alvo:** 2026-Q2-S4 (sucessor direto de `EPIC-CI-RECOVERY-2026Q2`)
**Status:** Draft
**Priority:** P0 — credibilidade do CI como gate de qualidade
**Owner:** @pm (coordenação), @dev (implementação), @qa (validação), @devops (push/PR)
**Início esperado:** após merge de PR #372

---

## Contexto

O CI de `main` em `tjsasakifln/PNCP-poc` está vermelho há mais de 200 runs consecutivos desde 2026-04-07. A iniciativa predecessora `EPIC-CI-RECOVERY-2026Q2` (STORY-CI-1/2/3/4 + PR #372) **destravou gates** bloqueantes:

| Story | Fix | Status |
|-------|-----|--------|
| STORY-CI-1 | `pytest-timeout` adicionado ao matrix `tests.yml` | Done |
| STORY-CI-2 | f-string backslash em `backend/llm.py` para Python 3.11 | Done |
| STORY-CI-3 | Next.js 16.2.2 → 16.2.3 (GHSA-q4gf-8mx6-v5v3 DoS HIGH) | Done |
| STORY-CI-4 | `frontend/.npmrc` com `legacy-peer-deps=true` (Storybook 8.6 × Next 16) | PR #372 |

Esses fixes **desbloquearam a execução** dos testes, mas **não consertaram os testes de fato falhando**. Run pós-destravamento (PR #372, 2026-04-16, run `24539387474`) confirma o estado real:

| Workflow / Job | Verdict | Falhas reais |
|----------------|---------|--------------|
| `frontend-tests.yml` – Frontend Tests (PR Gate) | `FAILURE` | 38 failed + 5 snapshots + 61 skipped; 19 suítes vermelhas |
| `tests.yml` – Frontend Tests (matrix) | `FAILURE` | mesmas 19 suítes |
| `tests.yml` – Backend Tests (3.11) | `FAILURE` | timeout HTTPS real + baseline histórica de 292 pre-existing |
| `tests.yml` – Backend Tests (3.12) | `CANCELLED` | fail-fast do matrix após 3.11 |
| `tests.yml` – End-to-End Tests | `SKIPPED` | dependência do Frontend Tests passar |
| Chromatic Visual Regression | `FAILURE` | snapshot drift |
| CodeQL – Dependency Review | `FAILURE` | Dependency Graph desabilitado em repo settings |

Este epic (**EPIC-CI-GREEN-MAIN-2026Q2**) executa o trabalho que o predecessor não fez: **consertar cada suíte vermelha até 0 failed / 0 errored / snapshots estáveis**, mantendo cobertura baseline (backend 70% / frontend 60%).

---

## Meta quantificada

Condição de saída do epic (agregada — **não se aplica a stories filhas individualmente**):

- [ ] `frontend-tests.yml` mostra **0 failed** por 10 runs consecutivos em `main`
- [ ] `tests.yml` matriz (3.11 + 3.12) mostra **0 failed** por 10 runs consecutivos em `main`
- [ ] `End-to-End Tests` deixa de ser `SKIPPED` e passa verde
- [ ] Cobertura backend ≥ 70%, frontend ≥ 60% (não cai vs. último run verde conhecido)
- [ ] `Dependency Review` verde ou removido com justificativa aprovada por @devops
- [ ] `pytest --collect-only` conta os mesmos testes da baseline (provando ausência de skip introduzido)
- [ ] `grep -rnE "\.(skip|only)\(|@pytest\.mark\.skip" frontend/__tests__ backend/tests` não revela marcadores novos vs. baseline

Stories filhas fecham com critério isolado (sua suíte verde + AC1-5 atendidos). Esta meta agregada é **só do epic**.

---

## Escopo

### IN
- Workflow `frontend-tests.yml`
- Workflow `tests.yml` (jobs: `Backend Tests (3.11)`, `Backend Tests (3.12)`, `Frontend Tests`, `End-to-End Tests`, `Integration Tests`)
- Workflow `backend-tests.yml` (gate dedicado backend — CLAUDE.md cita)
- CodeQL Dependency Review
- As 19 suítes frontend listadas no índice abaixo
- Backend matrix 3.11 timeout HTTPS + baseline 292 pre-existing

### OUT
_(nenhum — todas as suítes listadas pelo usuário entram no epic. Decisões de "remover check" aparecem dentro de stories individuais, com justificativa e aprovação @devops, nunca preemptivamente aqui.)_

---

## Política de conserto real (NÃO NEGOCIÁVEL)

1. **Zero quarentena.** Nenhuma story pode ter como AC "marcar teste como skip", `@pytest.mark.skip`, `it.skip`, `describe.skip`, `xit`, `xdescribe`, `test.skip`, `pytest.skip()`, `it.only`, `describe.only`, mover para suite não-gateada, ou `--passWithNoTests`. Se o teste existe, ele roda e passa.
2. **Root cause obrigatório.** Cada story descreve a CAUSA RAIZ (mock errado, assertion stale, drift implementação vs teste, bug real de código), não apenas o sintoma.
3. **Código de produção pode mudar** se o teste revelar bug real. Nesse caso a story vira feature/bugfix e precisa de pairing com stakeholder de produto.
4. **Snapshot regeneration** (`npm test -- -u`) só é aceitável após análise diff-by-diff documentada confirmando que a mudança de UI foi intencional e já está mergeada. Caso contrário, investigar regressão.
5. **Zero snapshots regenerados cegamente.**
6. **Cobertura não pode cair** vs. último run verde conhecido (backend 70%, frontend 60%).
7. **Os 292 pre-existing backend failures não são aceitos como "pre-existing" a partir deste epic.** Ou são consertados, ou movidos para um workflow `integration-external.yml` separado (que roda com infra provisionada, não é gate de PR) — exceção documentada caso a caso, não default.

Uma story que viola qualquer desses pontos falha @po `*validate-story-draft` e NUNCA deve ser mergeada.

---

## Índice de stories

Template de AC aplicável a todas as stories de suíte (AC6 só em stories snapshot):

- **AC1**: comando exato (`npm test -- <path>` ou `pytest <path>`) retorna exit 0 localmente com `.npmrc` aplicado
- **AC2**: 0 failed / 0 errored no CI; evidência em run ID registrado no Change Log
- **AC3**: causa raiz descrita e corrigida (mock / import / snapshot / bug real)
- **AC4**: cobertura da suíte não caiu; evidência `coverage-summary.json`
- **AC5 (NEGATIVO)**: nenhum skip/only/xit introduzido
- **AC6 (snapshot apenas)**: `-u` só após diff-by-diff analisado

### Frontend (19 stories)

| # | Story | Suíte | Fase | Owner |
|---|-------|-------|------|-------|
| 01 | `STORY-CIG-FE-01-navigation-shell` | `__tests__/navigation-shell.test.tsx` | 3 | @dev |
| 02 | `STORY-CIG-FE-02-reports-pdf-options` | `__tests__/reports/pdf-options.test.tsx` | 5 | @dev |
| 03 | `STORY-CIG-FE-03-a11y-jest-axe-suite` | `__tests__/a11y/jest-axe-suite.test.tsx` | 5 | @dev |
| 04 | `STORY-CIG-FE-04-empty-states` | `__tests__/empty-states.test.tsx` | 3 | @dev |
| 05 | `STORY-CIG-FE-05-theme-provider-ux410-wcag` | `__tests__/components/ThemeProvider-ux410-wcag.test.tsx` | 2 | @dev |
| 06 | `STORY-CIG-FE-06-button-component` | `__tests__/button-component.test.tsx` | 2 | @dev |
| 07 | `STORY-CIG-FE-07-use-search-filters-isolated` | `__tests__/hooks/useSearchFilters-isolated.test.tsx` | 1 | @dev |
| 08 | `STORY-CIG-FE-08-use-search-filters` | `__tests__/hooks/useSearchFilters.test.ts` | 1 | @dev |
| 09 | `STORY-CIG-FE-09-mobile-header` | `__tests__/mobile-header.test.tsx` | 2 | @dev |
| 10 | `STORY-CIG-FE-10-chromatic-visual-regression` | `tests/chromatic/visual-regression.spec.ts` | 7 | @dev, @devops |
| 11 | `STORY-CIG-FE-11-search-state-machine` | `__tests__/search-state-machine.test.tsx` | 3 | @dev |
| 12 | `STORY-CIG-FE-12-admin-partners` | `__tests__/admin/partners.test.tsx` | 3 | @dev |
| 13 | `STORY-CIG-FE-13-debt105-error-boundaries` | `__tests__/debt105-error-boundaries.test.tsx` | 2 | @dev |
| 14 | `STORY-CIG-FE-14-licitacao-card-ux400` | `__tests__/components/LicitacaoCard-ux400.test.tsx` | 4 | @dev |
| 15 | `STORY-CIG-FE-15-licitacao-card-ux401` | `__tests__/components/LicitacaoCard-ux401.test.tsx` | 4 | @dev |
| 16 | `STORY-CIG-FE-16-historico-buttons` | `__tests__/components/historico-buttons.test.tsx` | 2 | @dev |
| 17 | `STORY-CIG-FE-17-observatorio-page` | `__tests__/app/observatorio-page.test.tsx` | 3 | @dev |
| 18 | `STORY-CIG-FE-18-tour-component` | `__tests__/components/Tour.test.tsx` | 2 | @dev |
| 19 | `STORY-CIG-FE-19-sector-sync` | `__tests__/sector-sync.test.ts` | 1 | @dev |

### Backend (2 stories)

| # | Story | Escopo | Fase | Owner |
|---|-------|--------|------|-------|
| 20 | `STORY-CIG-BE-HTTPS-TIMEOUT` | timeout HTTPS real em `Backend Tests (3.11)` | 6 | @dev |
| 21 | `STORY-CIG-BACKEND-SWEEP` | triage dos 292 pre-existing failures → N stories filhas | 6 | @dev, @qa, @po |

### Infra de repositório (1 story)

| # | Story | Escopo | Fase | Owner |
|---|-------|--------|------|-------|
| 22 | `STORY-CIG-DEP-GRAPH` | habilitar Dependency Graph OU remover required-check com justificativa | 7 | @devops |

---

## Ordem de execução (fases)

| Fase | Descrição | Stories | Justificativa |
|------|-----------|---------|---------------|
| 0 | Pré-requisito externo | — | PR #372 merged |
| 1 | Hooks e utils (podem desbloquear outras) | FE-07, FE-08, FE-19 | menor blast-radius, base de muitos componentes |
| 2 | Components isolados | FE-05, FE-06, FE-09, FE-13, FE-16, FE-18 | independentes entre si, rodam paralelos |
| 3 | Páginas e fluxos | FE-01, FE-04, FE-11, FE-12, FE-17 | dependem de Fase 1-2 para contexto limpo |
| 4 | Cards (snapshots) | FE-14, FE-15 | devem rodar juntos; diff de snapshot analisado de uma vez |
| 5 | Reports e a11y | FE-02, FE-03 | dependências externas (reportlab, jest-axe) a investigar |
| 6 | Backend | BE-HTTPS-TIMEOUT (paralelo com Fases 1-5), BACKEND-SWEEP (sequencial após BE-HTTPS) | sweep contamina baseline se rodar antes |
| 7 | Infra repo + Chromatic | DEP-GRAPH, FE-10 | decisões binárias, melhor depois das suítes consertadas |
| 8 | Saída | — | 10 runs verdes consecutivos em main |

---

## Dependências entre stories

```
FE-07 ──┐
FE-08 ──┼── FE-11 ── FE-01
        │
FE-19 ──┘

FE-04 depende de confirmação de que SearchEmptyState foi movida (memory/MEMORY.md)
FE-14 e FE-15 rodam juntos (mesma base de componente LicitacaoCard)
FE-03 bloqueia verificação de a11y regressions em FE-05, FE-06, FE-13, FE-14, FE-15

BACKEND-SWEEP produz N stories filhas (fora do escopo desta sessão @sm)
```

---

## Paths críticos referenciados

- `docs/stories/2026-04/EPIC-CI-RECOVERY-2026Q2/STORY-CI-[1-4]*.story.md` — template replicado
- `.claude/rules/story-lifecycle.md` — status progression + 10-point validation
- `CLAUDE.md` — Testing Strategy, jest `moduleNameMapper @/ → <rootDir>/`, anti-hang rules
- `jest.setup.js` — polyfills `crypto.randomUUID` + `EventSource`
- `backend/pyproject.toml` — `timeout = 30.0`, `timeout_method = thread`
- `memory/MEMORY.md` — `frontend-test-baseline.md` (16 pre-existing em 2026-04-03), `SearchEmptyState` movida

---

## Change Log

- **2026-04-16** — @sm: epic criado com 22 stories (19 FE + 2 BE + 1 infra) após destravamento do predecessor EPIC-CI-RECOVERY-2026Q2; política conserto-real estabelecida; ordem de fases definida.
