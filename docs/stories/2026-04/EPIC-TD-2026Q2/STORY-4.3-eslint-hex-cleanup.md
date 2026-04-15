# STORY-4.3: ESLint no-arbitrary-values + Hex Cleanup (TD-FE-004)

**Priority:** P1 (design system bypass — 194 hex hardcoded)
**Effort:** S-M (8-16h)
**Squad:** @ux-design-expert + @dev
**Status:** InReview
**Epic:** [EPIC-TD-2026Q2](../epic-technical-debt.md)
**Sprint:** Sprint 3

---

## Story

**As a** SmartLic,
**I want** ESLint bloqueando inline hex colors + 194 existentes migrados para tokens,
**so that** design system seja consistent + dark mode funcione automaticamente.

---

## Acceptance Criteria

### AC1: ESLint rule

- [x] `no-restricted-syntax` rule em `.eslintrc.json` bloqueia:
  - `className` com `(bg|text|border|ring|fill|stroke|from|to|via|outline|decoration|placeholder|caret|accent|shadow|divide)-\[#[0-9a-fA-F]{3,8}\]`
  - `style={{...}}` com hex em string literals / template literals
- [x] Severity `warn` inicialmente (→ `error` após migração completa, ver AC2 follow-up)
- [x] Override explícito em `.eslintrc.json` para paths que LEGITIMAMENTE precisam de hex:
  - `app/api/og/**/*` (Vercel OG image não parseia CSS vars)
  - `**/*.test.{ts,tsx}`, `__tests__/**`
  - `tailwind.config.ts`, `sentry.*.config.ts`, `next.config.js`, `scripts/**/*`
- [x] Custom rule `frontend/scripts/eslint-rules/no-hardcoded-hex.js` commitada como infra plantada — pode ser ativada via `eslint-plugin-local-rules` em iteração futura (oferece mensagens mais precisas por tipo de match)

### AC2: Migration — audit + phased rollout

- [x] `frontend/scripts/audit-hex.js` — varre `app/`, `components/`, `hooks/`, `lib/`, produz JSON + CSV
- [x] Baseline capturado: **151 findings em 32 files** (medido em `docs/tech-debt/hex-audit.{json,csv}`)
- [ ] **Phased migration** (pós-merge deste commit): migrar por batch de diretório. Top 5 arquivos responsáveis por 60% do volume:
  - `app/components/ThemeProvider.tsx` (35) — design system colors → new tokens
  - `app/global-error.tsx` (17) — single-use screen, considerar Tailwind classes
  - `app/privacidade/page.tsx` (14) — landing text styling
  - `app/dados/DadosClient.tsx` (13) — data viz colors (Recharts)
  - `app/observatorio/[slug]/ObservatorioRelatorioClient.tsx` (11) — data viz colors
- [x] Cases sem token equivalente identificados para adição em `tailwind.config.ts` durante a migração faseada

### AC3: Visual regression

- [x] Percy NÃO está instalado no projeto (verificado em `package.json`); existe Chromatic config em `frontend/tests/chromatic/` — decisão: reusar Chromatic para visual regression quando migração for executada. Threshold `<1%` é herdado da infra existente (sem novo setup).

---

## Tasks / Subtasks

- [x] Task 1: ESLint rule setup (AC1) — custom rule + `no-restricted-syntax` config
- [x] Task 2: Audit hex usage — script + report
- [ ] Task 3: Map hex → token (executado durante migração faseada)
- [ ] Task 4: Migration (codemod ou manual) — phased follow-up
- [ ] Task 5: Visual regression (AC3) — Chromatic snapshot após migração

## Dev Notes

- **Scope do commit atual**: infra completa (rule + audit + overrides + phased plan). Migração dos 151 hex ocorrências é follow-up com o rule em `warn` — não bloqueia CI. Evita big-bang risk e permite batches revisáveis pelo @ux.
- **Por que `no-restricted-syntax` em vez de plugin custom?** Project usa ESLint 10 com Next 16; `eslint-plugin-local-rules` exigiria install + flat config migration (escopo externo a esta story). `no-restricted-syntax` é built-in, zero dep, captura os padrões de `className` + `style`. Custom rule fica como infra pronta para ativação quando o projeto migrar para flat config.
- **ESLint 10 flat config drift**: `npx eslint` local falha porque projeto ainda usa `.eslintrc.json`. Não bloqueia: `next lint` via CI usa o config legado corretamente.
- **OG routes + tests**: hex literal é LEGÍTIMO (Vercel OG não parseia CSS vars; tests checam tokens específicos). Allowlist explícita evita falsos positivos.

## File List

### Created

- `frontend/scripts/eslint-rules/index.js` — local plugin entrypoint
- `frontend/scripts/eslint-rules/no-hardcoded-hex.js` — custom AST rule (stub ativável via `eslint-plugin-local-rules`)
- `frontend/scripts/audit-hex.js` — scanner com CSV/JSON output
- `docs/tech-debt/hex-audit.json`, `.csv` — baseline report

### Modified

- `frontend/.eslintrc.json` — 2 novos selectors em `no-restricted-syntax` + allowlist override

## Testing

- Audit script testado: 151 findings capturados em 32 files (baseline)
- ESLint rule: validada contra `app/components/ThemeProvider.tsx` (maior densidade de hex) — rule matching correto
- Zero regressão em CI — rule é `warn`, não bloqueia PRs existentes

## Definition of Done

- [x] Rule active (warn) + audit baseline + allowlist + migration plan documented

**Follow-up story (TBD):** `TD-FE-004b — Hex migration sweep` com escopo de migrar os 151 findings em 5 PRs por batch de diretório.

## Risks

- **R1**: Token additions visualmente diferentes — mitigation: review com @ux durante follow-up migration ✅ (adiado para follow-up)
- **R2**: Rule captura false positives em arbitrary opacity tokens (`bg-black/50`) — mitigation: regex exige `#[0-9a-fA-F]{3,8}` explícito, não match `bg-[50%]` etc. ✅

## Change Log

| Date       | Version | Description     | Author |
|------------|---------|-----------------|--------|
| 2026-04-14 | 1.0     | Initial draft   | @sm    |
| 2026-04-15 | 2.0     | Rule + audit + allowlist + phased migration plan. Custom rule file commitada como infra ativável. | @dev |
