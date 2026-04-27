# SEO-PROG-010: Lighthouse CI gate (LCP<2.5s, INP<200ms, CLS<0.1, TTFB<600ms — 5 sample routes)

**Priority:** P1
**Effort:** M (3 dias)
**Squad:** @devops + @dev
**Status:** Ready
**Epic:** [EPIC-SEO-PROG-2026-Q2](EPIC-SEO-PROG-2026-Q2.md)
**Sprint:** Sprint 4 (20–26/mai)
**Sprint Window:** 2026-05-20 → 2026-05-26
**Bloqueado por:** SEO-PROG-009 (bundle ≤1.15MB para baseline limpo)

---

## Contexto

Sem Lighthouse CI gate, regressões em Core Web Vitals (LCP, INP, CLS, TTFB) entram em produção silenciosamente. Memory `reference_smartlic_baseline_2026_04_24` documenta posição GSC média 7.1 — Core Web Vitals ruins é hipótese forte. Após SEO-PROG-001..005 (ISR) + SEO-PROG-009 (bundle reduction), precisamos **gate em CI** para prevenir reincidência.

**Estado atual:**

- Sem Lighthouse CI workflow
- Sem budgets formalizados (SEO-PROG-001..005 declaram budgets em DoD mas sem enforcement automático)
- Bundle size já tem CI gate via `.size-limit.js` (precedente padrão)

**Métricas alvo** (CrUX p75 — Google ranking inputs):

| Métrica | Threshold | Justificativa |
|---|---|---|
| LCP | < 2.5s | Google "Good" threshold; ranking factor confirmado |
| INP | < 200ms | Google "Good" 2024 update (substituiu FID) |
| CLS | < 0.1 | Visual stability; impacta UX percebida |
| TTFB | < 600ms | Lighthouse opinion threshold; ISR backed |

**Sample routes** (5 representativas, conforme epic Validation Framework):

1. `/cnpj/{TOP_CNPJ}` — single-segment dinâmico SSG/ISR (SEO-PROG-001)
2. `/orgaos/{TOP_SLUG}` — single-segment SSG/ISR (SEO-PROG-002)
3. `/itens/{TOP_CATMAT}` — alta cardinalidade SSG/ISR (SEO-PROG-003)
4. `/observatorio/{TOP_SLUG}` — evergreen SSG/ISR (SEO-PROG-004)
5. `/blog/licitacoes/{TOP_SETOR}/{TOP_UF}` — programmatic combo já estável

**Por que P1 (não P0):** rotas SSR→ISR migrations (P0) são prerequisitos. Sem ISR, Lighthouse mediria SSR cold → falsos positivos. Após Sprint 3 estabilizar, gate pode ser instalado com confiança.

---

## Acceptance Criteria

### AC1: Lighthouse CI workflow GitHub Actions

**Given** queremos rodar Lighthouse em PRs que tocam frontend
**When** @devops cria workflow
**Then**:

- [ ] Criar `.github/workflows/lighthouse.yml`:

```yaml
name: Lighthouse CI

on:
  pull_request:
    paths:
      - 'frontend/**'
      - '.github/workflows/lighthouse.yml'
      - 'lighthouserc.json'

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install Lighthouse CI
        run: npm install -g @lhci/cli@0.13.x

      - name: Run Lighthouse CI
        run: lhci autorun --config=./lighthouserc.json
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
```

- [ ] Workflow só roda em PRs (não push to main, evita custo Actions)
- [ ] Timeout 15min (cap defensivo)
- [ ] Concurrency cancel-in-progress: PR push superseed run anterior

### AC2: `lighthouserc.json` com budgets enforced

**Given** queremos thresholds explícitos
**When** @devops cria config
**Then**:

- [ ] Criar `lighthouserc.json` na raiz do repo:

```json
{
  "ci": {
    "collect": {
      "url": [
        "https://staging.smartlic.tech/cnpj/${LHCI_TOP_CNPJ}",
        "https://staging.smartlic.tech/orgaos/${LHCI_TOP_ORGAO_SLUG}",
        "https://staging.smartlic.tech/itens/${LHCI_TOP_CATMAT}",
        "https://staging.smartlic.tech/observatorio/${LHCI_TOP_OBSERVATORIO_SLUG}",
        "https://staging.smartlic.tech/blog/licitacoes/saude/SP"
      ],
      "numberOfRuns": 3,
      "settings": {
        "preset": "desktop"
      }
    },
    "assert": {
      "assertions": {
        "largest-contentful-paint": ["error", {"maxNumericValue": 2500}],
        "interaction-to-next-paint": ["error", {"maxNumericValue": 200}],
        "cumulative-layout-shift": ["error", {"maxNumericValue": 0.1}],
        "server-response-time": ["error", {"maxNumericValue": 600}],
        "categories:performance": ["warn", {"minScore": 0.85}],
        "categories:seo": ["error", {"minScore": 0.95}],
        "categories:accessibility": ["warn", {"minScore": 0.90}]
      }
    },
    "upload": {
      "target": "temporary-public-storage"
    }
  }
}
```

- [ ] **fail_threshold**: `error` em LCP/INP/CLS/TTFB falha PR; `warn` em score-level alerta sem blocker
- [ ] **numberOfRuns: 3**: median p75 — reduz flakiness CI
- [ ] **preset: desktop**: SEO B2G pessoal usa desktop predominante; mobile audit em SEO-PROG-010-FOLLOWUP (defer)

### AC3: Top route fixtures via env vars

**Given** sample routes precisam de IDs reais (CNPJ top, slug top, etc.)
**When** workflow executa
**Then**:

- [ ] Workflow set env vars antes de Lighthouse:

```yaml
- name: Resolve top route fixtures
  id: fixtures
  run: |
    echo "LHCI_TOP_CNPJ=$(curl -s https://api.smartlic.tech/v1/sitemap/fornecedores-cnpj?limit=1 | jq -r '.cnpjs[0]')" >> $GITHUB_ENV
    echo "LHCI_TOP_ORGAO_SLUG=$(curl -s https://api.smartlic.tech/v1/sitemap/orgaos?limit=1 | jq -r '.orgaos[0]')" >> $GITHUB_ENV
    echo "LHCI_TOP_CATMAT=$(curl -s https://api.smartlic.tech/v1/sitemap/itens?limit=1 | jq -r '.catmats[0]')" >> $GITHUB_ENV
    echo "LHCI_TOP_OBSERVATORIO_SLUG=$(curl -s https://api.smartlic.tech/v1/observatorio/slugs | jq -r '.slugs[0]')" >> $GITHUB_ENV
```

- [ ] Fallback hardcoded se backend indisponível (não bloquear PR por flakiness backend)
- [ ] Substituição via `${VAR}` no `lighthouserc.json` (Lighthouse CI suporta env interpolation)

### AC4: PR comment with results

**Given** queremos visibility direto na PR
**When** Lighthouse roda
**Then**:

- [ ] PR recebe comment automatizado com:
  - Tabela: Route × {LCP, INP, CLS, TTFB, Performance Score}
  - Diff vs base branch (main) se baseline disponível (LH Server opcional, defer)
  - Link para Lighthouse public storage URL (artifact)
- [ ] Implementação via `treosh/lighthouse-ci-action@v11` ou comment custom via `actions/github-script`

### AC5: Manual workflow_dispatch

**Given** queremos rodar Lighthouse on-demand contra prod
**When** @devops adiciona trigger manual
**Then**:

- [ ] Workflow tem `workflow_dispatch` input `target_url` (default `https://smartlic.tech`):

```yaml
on:
  workflow_dispatch:
    inputs:
      target_url:
        description: 'Target URL (production or staging)'
        required: false
        default: 'https://smartlic.tech'
```

- [ ] Permite QA validar prod sob demanda

### AC6: Documentation + runbook

**Given** dev pode receber Lighthouse fail e não saber como debugar
**When** @devops adiciona docs
**Then**:

- [ ] `docs/runbooks/lighthouse-ci-failure.md`:
  - Como reproduzir local: `npx @lhci/cli autorun --config=./lighthouserc.json`
  - Common causes: bundle regressão, image bloat, blocking script, layout shift
  - Como inspecionar artifact (link no PR comment)
  - Como obter waiver (escalate @qa + @architect com justificativa)
- [ ] Link no `frontend/CONTRIBUTING.md` (se existe) ou `frontend/README.md`

### AC7: Testes do workflow

- [ ] PR sintético com regressão proposital (e.g., adicionar `<img src=huge.png>` 5MB) → workflow falha esperadamente
- [ ] PR sintético com fix → workflow passa
- [ ] Documentar test PRs em PR description

---

## Scope

**IN:**
- Workflow `.github/workflows/lighthouse.yml`
- `lighthouserc.json` config
- 5 sample routes (mix entity + programmatic)
- Top route fixtures via backend API
- PR comment automation
- Manual workflow_dispatch
- Runbook docs

**OUT:**
- Lighthouse Server self-hosted (defer; usar temporary-public-storage)
- Mobile preset audit (defer follow-up)
- Performance budget JSON (Webpack performance budgets — already in `.size-limit.js`)
- Real User Monitoring (RUM) — out-of-scope; usar GSC CrUX como verdade
- Lighthouse on push to main (defer; PR-only é suficiente)

---

## Definition of Done

- [ ] Workflow `lighthouse.yml` ativo em prod
- [ ] PR sintético com regressão LCP > 2.5s **falha** corretamente
- [ ] PR sintético healthy **passa**
- [ ] PR comment automatizado funcional (testado em PR teste)
- [ ] Manual workflow_dispatch funcional
- [ ] Runbook docs em `docs/runbooks/lighthouse-ci-failure.md`
- [ ] CodeRabbit clean
- [ ] PR aprovado @qa + @devops
- [ ] Change Log epic atualizado
- [ ] @qa documenta processo de waiver em runbook

---

## Dev Notes

### Paths absolutos

- **Workflow novo:** `/mnt/d/pncp-poc/.github/workflows/lighthouse.yml`
- **Config:** `/mnt/d/pncp-poc/lighthouserc.json` (root)
- **Runbook:** `/mnt/d/pncp-poc/docs/runbooks/lighthouse-ci-failure.md`
- **Bundle size precedente:** `/mnt/d/pncp-poc/frontend/.size-limit.js` (mesmo pattern de CI gate)
- **Frontend tests workflow:** `/mnt/d/pncp-poc/.github/workflows/frontend-tests.yml`

### Reference

- [Lighthouse CI GitHub Action](https://github.com/treosh/lighthouse-ci-action)
- [Lighthouse CI configuration](https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md)
- [Web Vitals thresholds](https://web.dev/articles/vitals)

### Padrões existentes

- `.github/workflows/frontend-tests.yml` é o exemplo canônico de workflow Node.js — replicar setup-node + cache.
- `.github/workflows/api-types-check.yml` é exemplo de gate que **falha PR** se condition not met — replicar exit 1 pattern.
- Concurrency block (cancel-in-progress) já usado em `.github/workflows/backend-tests.yml`.

### Memory caveat

- Memory `feedback_concurrent_jobs_cap.md`: Free/Pro tier GH Actions cap 20 concurrent ubuntu-latest. Lighthouse adiciona ~3-5min. Monitorar custo via `gh api /repos/{owner}/{repo}/actions/billing/workflow-usage`.

### Testing standards

- Test PRs devem usar branch dedicada `test/lighthouse-ci-{regression|healthy}` para não poluir history.
- Manual smoke: rodar `npx @lhci/cli autorun --config=./lighthouserc.json` localmente contra staging antes de merge.

### Top route fixtures fallback

- Se backend `/v1/sitemap/...?limit=1` retorna vazio em CI, usar fixture hardcoded (e.g., `LHCI_TOP_CNPJ=12345678000100`). Add via env var no workflow with `||` fallback.

---

## Risk & Rollback

### Triggers

| Trigger | Threshold | Ação |
|---|---|---|
| Lighthouse workflow flaky (false positives) | >20% PRs fail sem regressão real | Soft rollback: `assert` para `warn` |
| Backend API fixture lookup fail | timeout/5xx | Fallback hardcoded fixtures |
| Workflow custo excessivo | >100min/dia | Reduzir `numberOfRuns` 3→2 |

### Ações

1. **Soft rollback:** mudar assertions de `error` para `warn` (não bloqueia PR mas mantém visibility).
2. **Hard rollback:** desabilitar workflow via `if: false` (delegar @devops).

---

## Dependencies

### Entrada

- SEO-PROG-009 (bundle ≤1.15MB)
- SEO-PROG-001..005 (rotas ISR estáveis)

### Saída

- SEO-PROG-012 (schema expansion deve passar Lighthouse SEO category 0.95+)

### Paralelas

- SEO-PROG-011 (RelatedPages — pode quebrar bundle budget; coordenar com Lighthouse gate)

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | Clear and objective title | OK | Título preciso: thresholds + 5 sample routes |
| 2 | Complete description | OK | Justifica prerequisito (Sprint 3 ISR estável) e métricas com baselines Google "Good" |
| 3 | Testable acceptance criteria | OK | AC1-AC7 testáveis; AC7 inclui PR sintético com regressão proposital |
| 4 | Well-defined scope (IN/OUT) | OK | OUT exclui: LH self-hosted, mobile preset, RUM, push to main |
| 5 | Dependencies mapped | OK | Bloqueado por SEO-PROG-009 (bundle limpo); 001-005 ISR estáveis |
| 6 | Complexity estimate | OK | Effort M (3 dias) consistente: workflow + config + fixtures + PR comment |
| 7 | Business value | OK | Previne regressão silenciosa; cita CrUX p75 como Google ranking inputs |
| 8 | Risks documented | OK | 3 triggers + memory caveat (cap concurrent jobs 20) |
| 9 | Criteria of Done | OK | 11 itens; PR sintético healthy + regressão validados |
| 10 | Alignment with PRD/Epic | OK | Sample routes match epic Validation Framework; **NÃO duplica check existente** (não há lighthouse workflow atual) |

### Observations

- **Verificação anti-duplicação:** epic Validation Framework cita "Lighthouse CI thresholds (PR gate)" como gap — story preenche corretamente. Não duplica `.size-limit.js` (bundle) nem `frontend-tests.yml`.
- AC2 thresholds binários (LCP/INP/CLS/TTFB como `error`, scores como `warn`) é decisão pragmática anti-flakiness.
- AC3 fixtures via backend API com fallback hardcoded é defesa contra backend flakiness em CI.
- AC4 PR comment com diff vs base é DX excelente — encurta loop de feedback.
- Memory `feedback_concurrent_jobs_cap.md` reconhecida em Dev Notes (cap 20 concurrent ubuntu-latest).

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — Lighthouse CI gate 5 sample routes | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Não duplica check existente; preenche gap epic. Status Draft→Ready. | @po (Pax) |
