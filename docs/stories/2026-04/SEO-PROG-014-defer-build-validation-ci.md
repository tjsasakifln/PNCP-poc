# SEO-PROG-014: Defer build SSG output validation para CI (workaround WSL build inviável)

**Priority:** P2
**Effort:** S (1 dia)
**Squad:** @devops
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 6 (03–09/jun)
**Sprint Window:** 2026-06-03 → 2026-06-09
**Bloqueado por:** — (independente)

---

## Contexto

Memory `feedback_wsl_next16_build_inviavel.md` (2026-04-24) documenta:

> **WSL npm build inviável em monorepo 3k+ pages**: OOM/timeout mesmo com 8GB heap; defer AC de build output para CI; `--experimental-build-mode=compile` candidato workaround

Este é um **constraint operacional crônico** que afeta SEO-PROG-001..006. Sprint 5 entrega 5000+ SSG pages só em `/itens/[catmat]` — WSL local não roda esse build, então:

1. **Devs não validam SSG output localmente** → confiam em CI 100% para build correctness
2. **CI workflow atual não valida output específico** (apenas que `npm run build` exits 0; não que N pages foram geradas)
3. **`--experimental-build-mode=compile`** é candidato Next.js 16 para skip SSG render — útil para iteração local, mas precisa de validation pattern documented

**Sintomas observáveis** (sem esta story):

- Story SEO-PROG-003 (top-5000 CATMATs) merge e CI passa, mas só 200 HTMLs gerados (regressão silenciosa do `_MAX_STATIC_CATMATS = 200` original).
- Dev local não percebe (WSL build crashed antes mesmo de page render).
- Detectado apenas em production via GSC URL Inspection ou sitemap shard count.

**Por que P2:** P0/P1 stories são funcionais sem isto (CI passa, prod funciona). Mas é dívida operacional — sem validation explícita, regressões SSG passam sem ruído.

**Por que esforço S:** workflow novo + documentação. Sem código complexo.

---

## Acceptance Criteria

### AC1: CI workflow `frontend-build-output-check.yml`

**Given** queremos validar SSG output count contra expectativa
**When** @devops cria workflow
**Then**:

- [ ] Criar `.github/workflows/frontend-build-output-check.yml`:

```yaml
name: Frontend Build Output Check

on:
  pull_request:
    paths:
      - 'frontend/app/cnpj/**'
      - 'frontend/app/orgaos/**'
      - 'frontend/app/itens/**'
      - 'frontend/app/observatorio/**'
      - 'frontend/app/fornecedores/**'
      - 'frontend/.size-limit.js'
      - '.github/workflows/frontend-build-output-check.yml'

jobs:
  build-output-check:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install
        run: cd frontend && npm ci --legacy-peer-deps

      - name: Build
        env:
          BACKEND_URL: ${{ secrets.STAGING_BACKEND_URL || 'https://api.smartlic.tech' }}
          NEXT_PUBLIC_BACKEND_URL: ${{ secrets.STAGING_BACKEND_URL || 'https://api.smartlic.tech' }}
          NEXT_PUBLIC_CANONICAL_URL: 'https://smartlic.tech'
          NEXT_PUBLIC_ENVIRONMENT: 'production'
          NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.NEXT_PUBLIC_SUPABASE_ANON_KEY }}
        run: cd frontend && npm run build

      - name: Validate SSG output counts
        run: |
          cd frontend
          # Expected minimum counts per route (SEO-PROG-001..005 baselines)
          declare -A EXPECTED_MIN=(
            ["app/cnpj/[cnpj]"]=900
            ["app/orgaos/[slug]"]=1800
            ["app/itens/[catmat]"]=4500
            ["app/observatorio/[slug]"]=20
            ["app/fornecedores/[cnpj]/[uf]"]=900
          )
          for route in "${!EXPECTED_MIN[@]}"; do
            min=${EXPECTED_MIN[$route]}
            count=$(find ".next/server/$route" -name '*.html' 2>/dev/null | wc -l)
            echo "$route: $count HTMLs (min: $min)"
            if [ "$count" -lt "$min" ]; then
              echo "ERROR: $route built only $count HTMLs (expected min $min)"
              exit 1
            fi
          done

      - name: Upload build manifest
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: build-manifest-${{ github.run_id }}
          path: |
            frontend/.next/build-manifest.json
            frontend/.next/server/pages-manifest.json
          retention-days: 7
```

- [ ] Counts mínimos baseados em SEO-PROG-001..005 baselines (900/1800/4500/20/900)
- [ ] Tolerância 10% abaixo do target (se SEO-PROG-001 declara top-1000 CNPJs, mínimo 900)
- [ ] Fallback para staging backend URL se secret não set

### AC2: Workflow_dispatch para validação on-demand

- [ ] Workflow tem `workflow_dispatch` trigger
- [ ] Permite QA rodar manualmente em qualquer branch

### AC3: Documentação dev workflow local

**Given** devs precisam workflow alternativo para WSL/local
**When** @devops adiciona docs
**Then**:

- [ ] Criar/atualizar `frontend/README.md` seção "Build Local Workaround":

```markdown
## Build Local em WSL/Linux

Em WSL, `npm run build` em monorepo SmartLic OOM/timeout mesmo com `NODE_OPTIONS=--max-old-space-size=8192`.
Memory: `feedback_wsl_next16_build_inviavel.md`.

### Workarounds

#### 1. Compile-only mode (rápido, skip SSG)

```bash
cd frontend
NODE_OPTIONS="--max-old-space-size=4096" npx next build --experimental-build-mode=compile
```

Compila código + types sem renderizar SSG pages. Útil para iteração rápida (lint, type check, bundle analyzer).

#### 2. SSG count limit override (slow, completes)

```bash
cd frontend
SEO_TOP_CATMAT_LIMIT=200 \
SEO_TOP_CNPJ_LIMIT=200 \
SEO_TOP_ORGAOS_LIMIT=200 \
NODE_OPTIONS="--max-old-space-size=8192" \
npm run build
```

Reduz universo SSG para 200 pages/route — completa em ~3min em WSL 8GB.

#### 3. Validar SSG output em CI

Para validação completa de SSG output count, push em PR e veja workflow `frontend-build-output-check.yml`.
Não tente reproduzir contagem total localmente.
```

- [ ] Link de `frontend/README.md` para esta seção
- [ ] Add memory check em PR template (devops): "validei SSG output count via CI workflow"

### AC4: Env var matrix nos page.tsx

**Given** queremos override SSG count via env (workaround AC3 #2)
**When** @dev valida que SEO-PROG-001..005 já implementaram
**Then**:

- [ ] Confirmar que SEO-PROG-001..005 implementaram env vars de override (verificar `_MAX_STATIC_CATMATS = parseInt(process.env.SEO_TOP_CATMAT_LIMIT ?? '5000', 10)` em itens, e similares)
- [ ] Se algum não implementou, abrir issue cross-cut para back-port

### AC5: Sentry alert workflow failure

**Given** falha em CI build-output-check pode ser missed em PR queue
**When** workflow falha
**Then**:

- [ ] GH Actions notification para Slack/email (TODO @devops: configurar conforme infra atual)
- [ ] PR comment automático com link para artifact build-manifest

---

## Scope

**IN:**
- Workflow `.github/workflows/frontend-build-output-check.yml`
- Counts mínimos por rota (5 entry points)
- Manual workflow_dispatch
- Docs `frontend/README.md` workarounds (compile-mode + count limit)
- Audit env vars override em SEO-PROG-001..005

**OUT:**
- Self-hosted runners para builds maiores (escopo `project_railway_runners_cost_2026_04`; defer)
- Build cache cross-PR (defer; Railway already caches deps)
- Visual regression em SSG output (defer; HTML count é proxy aceitável)
- Bundle analyzer per-route (defer; SEO-PROG-009 cobre via overall)

---

## Definition of Done

- [ ] Workflow ativo + falha esperadamente em PR sintético com `_MAX_STATIC_CATMATS=50` (regressão count)
- [ ] Workflow passa em PR healthy
- [ ] Manual workflow_dispatch funcional
- [ ] Docs `frontend/README.md` seção "Build Local Workaround" presente
- [ ] Memory `feedback_wsl_next16_build_inviavel.md` atualizada com referência cruzada a esta story
- [ ] Env vars override validados em SEO-PROG-001..005 (cross-check)
- [ ] CodeRabbit clean
- [ ] PR aprovado @qa + @devops
- [ ] Change Log atualizado

---

## Dev Notes

### Paths absolutos

- **Workflow novo:** `/mnt/d/pncp-poc/.github/workflows/frontend-build-output-check.yml`
- **README:** `/mnt/d/pncp-poc/frontend/README.md`
- **Memory referência:** `feedback_wsl_next16_build_inviavel.md`

### Reference

- [Next.js 16 — experimental build modes](https://nextjs.org/blog/next-16) — `--experimental-build-mode=compile`
- Memory `feedback_wsl_next16_build_inviavel.md` (2026-04-24)
- Memory `project_railway_runners_cost_2026_04.md` (2026-04-23) — self-hosted custaria $135/mês; OK GH Hosted

### Padrões existentes

- `.github/workflows/frontend-tests.yml` — npm ci + setup-node pattern
- `.github/workflows/api-types-check.yml` — fail PR pattern (exit 1)
- `concurrency: cancel-in-progress: true` para evitar duplicação

### Testing standards

- Sintetizar PR test:
  - Branch `test/seo-prog-014-regression`: edit `frontend/app/itens/[catmat]/page.tsx` setando `_MAX_STATIC_CATMATS = 50` (force regressão)
  - Push + verificar workflow falha com error claro
- Branch `test/seo-prog-014-healthy`: revert + verify pass

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Detecção |
|---|---|---|
| Workflow flaky (false positives) | >10% PRs fail sem regressão | Soft rollback |
| Workflow custo excessivo | >50min/PR | Reduce expected_min ou skip jobs |
| Build memory limit hit em GH Hosted | OOM em ubuntu-latest | Investigar self-hosted custo (out-of-scope) |

### Ações

1. **Soft:** ajustar `EXPECTED_MIN` para tolerância maior (e.g., 80% do target em vez de 90%).
2. **Hard:** desabilitar workflow via `if: false` (defer enforcement, manter visibility via artifact).

---

## Dependencies

### Entrada

- SEO-PROG-001..005 (env vars `SEO_TOP_*_LIMIT` implementadas)

### Saída

- Nenhuma direta (P2 terminal)

### Paralelas

- SEO-PROG-013 (independente)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: defer build validation CI + workaround WSL |
| 2 | Complete description | OK | Reconhece constraint operacional crônico (memory `feedback_wsl_next16_build_inviavel.md`) e sintomas observáveis |
| 3 | Testable acceptance criteria | OK | AC1-AC5 testáveis; AC1 inclui counts mínimos e PR sintético |
| 4 | Well-defined scope (IN/OUT) | OK | OUT lista 4 deferidos (self-hosted runners, build cache cross-PR, visual regression, bundle per-route) |
| 5 | Dependencies mapped | OK | Bloqueado por SEO-PROG-001..005 (env vars `SEO_TOP_*_LIMIT`) |
| 6 | Complexity estimate | OK | Effort S (1 dia) apropriado: workflow + docs |
| 7 | Business value | OK | Previne regressões SSG silenciosas (200 HTMLs vs 5000 esperados) |
| 8 | Risks documented | OK | 3 triggers; soft rollback ajusta tolerância (90%→80%) |
| 9 | Criteria of Done | OK | 9 itens; PR sintético regressão valida workflow |
| 10 | Alignment with PRD/Epic | OK | Memory cross-cut: `feedback_wsl_next16_build_inviavel` + `project_railway_runners_cost_2026_04` (self-hosted defer) |

### Observations

- AC1 EXPECTED_MIN counts (90% do target SEO-PROG-001..005): tolerância para variações de produção bem calibrada.
- AC4 cross-check de env vars override em SEO-PROG-001..005 é validação operacional importante (sem quebra silenciosa do override).
- AC3 docs com 3 workarounds (compile-mode, count limit, CI defer) é DX excelente para devs WSL.
- Sequenciamento Sprint 6 (após SEO-PROG-001..005 implementadas) é correto: counts reais conhecidos.
- Memory `project_railway_runners_cost_2026_04.md` reconhecido para justificar GH Hosted (vs $135/mês self-hosted).

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — defer build validation CI + WSL workarounds documentados | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Workaround crônico WSL com tolerância 90% calibrada. Status Draft→Ready. | @po (Pax) |
