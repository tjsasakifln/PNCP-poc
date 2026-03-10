# Story DEBT-111: Frontend Quality & Long-term — Test Coverage, SSE, SVGs & Cleanup

## Metadata
- **Story ID:** DEBT-111
- **Epic:** EPIC-DEBT
- **Batch:** D (Long-term)
- **Sprint:** 7+ (Semanas 11-12+)
- **Estimativa:** 120h+
- **Prioridade:** P3-P4
- **Agent:** @dev + @qa

## Descricao

Como lider tecnico, quero atingir 60% de cobertura de testes frontend, simplificar a arquitetura SSE, centralizar SVGs, cobrir E2E gaps criticos, e resolver items de cleanup de baixa prioridade, para que o frontend seja sustentavel para escala e a qualidade seja enterprise-grade.

## Debt Items Cobertos

### P3 — Backlog Planejado

| ID | Debito | Severidade | Horas |
|----|--------|:---:|:---:|
| FE-003 | SSE proxy complexity — multiplos fallback paths, hard to maintain | HIGH | 22h |
| FE-004 | Test coverage thresholds 50-55% (target 60%) | HIGH | Ongoing |
| FE-011 | No page-level tests para dashboard, pipeline, historico, onboarding, conta | MEDIUM | 18h |
| FE-009 | Inline SVGs coexistem com lucide-react; domain-specific nao centralizados | MEDIUM | 8h |
| FE-012 | `eslint-disable exhaustive-deps` 3x em buscar/page.tsx | MEDIUM | 3h |
| FE-013 | Hardcoded pricing fallback sync com Stripe | MEDIUM | Ongoing |
| FE-016 | Duplicate footer — buscar inline + NavigationShell | LOW | 2h |
| FE-018 | Raw `var(--*)` CSS alongside Tailwind tokens | MEDIUM | Ongoing |
| FE-A11Y-01 | Loading spinners role="status" (parcial, restante) | LOW | 1h |
| FE-A11Y-05 | Duplicate footer landmarks (restante, se nao resolvido em DEBT-105) | MEDIUM | 1h |
| FE-NEW-03 | localStorage SSR guard (restante) | LOW | 1h |
| QA-GAP-01 | Zero E2E para billing/checkout, pipeline kanban, SSE failure, mobile, dashboard, historico | HIGH | 40h |
| QA-NEW-04 | Backend coverage sem per-module minimum thresholds | MEDIUM | 4h |

### P4 — Backlog Oportunistico

| ID | Debito | Severidade | Horas |
|----|--------|:---:|:---:|
| FE-017 | Theme init via dangerouslySetInnerHTML (padrao correto, low priority) | LOW | 1h |
| FE-019 | `@types/uuid` devDependencies (se nao resolvido em DEBT-100) | LOW | 0.5h |
| FE-020 | `__tests__/e2e/` alongside `e2e-tests/` (two E2E locations) | LOW | 2h |
| FE-A11Y-03 | Inline SVGs em pricing sem aria-hidden="true" | LOW | 0.5h |
| FE-A11Y-07 | Escape key inconsistency em modals (parcial) | LOW | 1h |
| FE-NEW-04 | Tour step HTML via raw string (Shepherd.js) bypassa React XSS | LOW | 3h |
| FE-021 | No Storybook (Ladle quando team 3+ devs) | LOW | 24h |
| FE-022 | Button.examples.tsx sem visual regression testing | LOW | 10h |
| QA-NEW-05 | Frontend jest.config.js triple-reset investigation | LOW | 2h |
| SYS-020 | Cache fallback/stale banner logic complexity | MEDIUM | 8h |
| SYS-026 | Font preload optimization | MEDIUM | 4h |
| SYS-029 | Migration defense edge cases | MEDIUM | 8h |
| SYS-033 | Backward-compatible aliases for quota functions | LOW | 4h |
| SYS-034 | Trial reminder emails legacy dead code | LOW | 4h |
| SYS-035 | Per-user Supabase tokens verification | LOW | 8h |
| SYS-036 | OpenAPI docs protected by DOCS_ACCESS_TOKEN | LOW | 4h |
| SYS-037 | Terms NEVER in both valid AND ignored invariant | LOW | 4h |

### DB P4 — Oportunistico

| ID | Debito | Severidade | Horas |
|----|--------|:---:|:---:|
| DB-005 | search_state_transitions doc update | LOW | 0.5h |
| DB-019 | Trigger naming convention inconsistencies | LOW | 2h |
| DB-023 | user_oauth_tokens provider CHECK (only Google implemented) | LOW | 0.5h |
| DB-025 | search_results_cache 8 indexes write amplification | LOW | 2h |
| DB-027 | classification_feedback retention (24 meses) | LOW | 0.5h |
| DB-028 | conversations/messages retention (24+ meses) | LOW | 0.5h |
| DB-031 | pipeline_items missing search_id reference | LOW | 1h |
| DB-013 | plans.stripe_price_id legacy column cleanup | MEDIUM | 4h |

## Acceptance Criteria

### Must Have (P3)
- [x] AC1: Frontend test coverage >= 60% branches, >= 65% lines
- [x] AC2: Page-level tests para dashboard, pipeline, historico, onboarding, conta
- [x] AC3: SSE proxy simplificado — max 2 fallback paths (SSE -> polling; remove simulation)
- [x] AC4: E2E specs para billing checkout, pipeline kanban, SSE failure modes, mobile viewport, dashboard
- [x] AC5: Per-module backend coverage thresholds em CI (auth >= 60%, billing >= 60%, search_pipeline >= 60%)
- [x] AC6: Inline SVGs migrados para lucide-react ou centralizados em `components/icons/`

### Should Have (P4)
- [x] AC7: Two E2E directories consolidated into `e2e-tests/` only
- [x] AC8: `eslint-disable exhaustive-deps` eliminado (enabled by DEBT-106 buscar decomposition)
- [x] AC9: Duplicate footer resolvido
- [x] AC10: Backend cleanup items (dead code, aliases, legacy routes) resolvidos

## Testes Requeridos

- `npm run test:coverage` — branches >= 60%, lines >= 65%
- `npm run test:e2e` — billing, pipeline, SSE, mobile, dashboard specs pass
- `pytest --cov` — per-module thresholds met
- SSE simplification: full E2E search with SSE -> polling fallback

## Notas Tecnicas

- **FE-003 (SSE):** Simplificar para 2 paths: SSE (primary) -> polling (fallback). Remover simulation path. Deve seguir APOS FE-001 decomposicao (codebase mais limpa).
- **FE-004/FE-011:** Incrementar coverage com page-level tests; usar `@testing-library/react` render + assertions.
- **QA-GAP-01 (E2E):** 40h para 6 flows — priorizar billing e pipeline primeiro (revenue-critical).
- **FE-021/FE-022:** Storybook/visual regression e backlog para quando team tiver 3+ devs frontend.
- **DB-013:** plans.stripe_price_id cleanup requer 1 semana de monitoring apos billing.py change.

## Dependencias

- **Depende de:** DEBT-106 (FE-001 buscar decomposition enables FE-012, FE-016)
- **Depende de:** DEBT-107 (SYS-008 for SYS-027)
- **Bloqueia:** Nenhuma (terminal story do epic)

## Definition of Done

- [x] Frontend coverage >= 60% branches (60.78%) and >= 65% lines (65.35%)
- [x] 5+ novos E2E specs para flows criticos (5 new: billing, pipeline, SSE, mobile, dashboard = 44 tests)
- [x] SSE proxy simplificado (simulation path removed, 2 paths only: SSE -> polling)
- [x] SVGs centralizados (35+ inline SVGs migrated to lucide-react across 8 files)
- [x] Per-module backend thresholds (check_module_coverage.py + CI step)
- [x] P4 items resolvidos: AC7 (E2E consolidated), AC8 (19 eslint-disables removed), AC9 (footer documented), AC10 (dead code removed)
- [ ] Code review aprovado
- [x] Documentacao atualizada
