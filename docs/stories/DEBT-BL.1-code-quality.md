# DEBT-BL.1: Code Quality -- Dead Code, Naming, Documentation
**Epic:** EPIC-DEBT
**Sprint:** Backlog
**Priority:** P3
**Estimated Hours:** 28h
**Assignee:** TBD

## Objetivo

Resolver debitos de baixo risco que melhoram qualidade de codigo, limpeza, e documentacao. Inclui items de sistema, database, e frontend que podem ser resolvidos oportunisticamente durante sprints regulares. Varios items tem 0h estimado (aceitos como estao, apenas documentar convencao going forward).

## Debitos Incluidos

### Sistema

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| SYS-19 | Comentarios com Issue numbers sem links. Muitos refs a Issues sem URLs. | LOW | 4h |
| SYS-20 | SEO pages hardcoded. Rotas estaticas, nao CMS-driven. | LOW | 8h |

### Database

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| DB-05 | `partner_referrals` orfaos acumulam. <50 rows em producao. | LOW | 0.5h |
| DB-09 | `classification_feedback` FK ordering inconsistente entre migrations. | LOW | 0.5h |
| DB-12 | Tres convencoes de nomes em migrations. Aceitar, documentar convencao para futuras. | LOW | 0h |
| DB-14 | Cache cleanup trigger COUNT a cada INSERT. Overhead negligenciavel (<1ms). | LOW | 0h |
| DB-15 | `alert_sent_items` retention scan. Index cobre. Nao e full scan. | LOW | 0h |
| DB-18 | `stripe_price_id` deprecated em `plans`. Coluna nao mais usada. Pode dropar. | LOW | 1h |
| DB-19 | `created_at` nullable inconsistente em `user_oauth_tokens` e `plan_billing_periods`. | LOW | 0.5h |
| DB-21 | `trial_email_log` sem policy explicita. `service_role` bypassa RLS. Documentar. | LOW | 0.5h |
| DB-22 | Org admins sem UPDATE. Backend handles via service role. | LOW | 0.5h |
| DB-23 | Migration 027b superseded. IF NOT EXISTS garante idempotencia. | LOW | 0h |
| DB-24 | Legacy `backend/migrations/`. 7 arquivos redundantes. Adicionar DEPRECATED.md. | LOW | 0.5h |
| DB-25 | Constraint names inconsistentes. 5+ padroes. Cosmetico. | LOW | 0h |
| DB-26 | Trigger names inconsistentes. 4 padroes. Cosmetico. | LOW | 0h |
| DB-27 | `pipeline_items.search_id` TEXT vs UUID. Auto-casts. FK nao necessaria. | LOW | 0.5h |
| DB-29 | `monthly_quota` sem retention. 1 row/user/mes. 24,000 rows em 2 anos. | LOW | 0.5h |
| DB-31 | `profiles.plan_type` CHECK nao escala. Novo plano requer migration. Documentar armadilha. | MEDIUM | 0.5h |

### Frontend

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| FE-05 | Cores hex raw em global-error.tsx. By design (root layout failed). | LOW | 0.5h |
| FE-08 | Image optimization. 4 imagens em `/public`, HeroSection ja usa next/image. | LOW | 2h |
| FE-10 | Blog/SEO pages sem loading states. Server Components com static/ISR. | LOW | 2h |
| FE-11 | Animacoes duplicadas CSS + Tailwind. Redundancia, nao conflito. | LOW | 2h |
| FE-15 | Admin pages sem responsive. <5 usuarios internos, todos desktop. | LOW | 1h |
| FE-17 | Pull-to-refresh desktop hack CSS. Abordagem padrao, nao fragil. | LOW | 1h |
| FE-23 | 59 API route files. Standalone output, impacto em cold start e teorico. | LOW | 0h |
| FE-25 | Tailwind content paths com `pages/`. Diretorio nao existe, zero impacto. | LOW | 0.5h |
| FE-27 | NProgress vs built-in Next.js. Funciona bem, nao e debt real. | LOW | 0h |
| FE-28 | Formatacao de datas inconsistente. 25 arquivos com padroes mistos. | LOW | 3h |
| FE-29 | Toast vs banner inconsistente. Falta documentacao da convencao. | LOW | 4h |
| FE-30 | Shepherd arrow hidden. Remove conexao visual com target. | LOW | 1h |
| FE-32 | Framer Motion bundle. Isolado em landing pages, tree-shaking funciona. | LOW | 0h |
| FE-33 | Error pages usam tokens inconsistentes (inline var vs Tailwind). | LOW | 2h |

## Acceptance Criteria

- [ ] AC1: Issue references em comentarios incluem URLs completas (SYS-19)
- [ ] AC2: SEO pages avaliadas para potencial CMS migration (SYS-20, pode ser aceito como esta)
- [ ] AC3: `partner_referrals` retention job criado (12 meses) (DB-05)
- [ ] AC4: `stripe_price_id` column dropada de `plans` (DB-18, depende de DEBT-S0.2)
- [ ] AC5: `created_at` NOT NULL em `user_oauth_tokens` e `plan_billing_periods` (DB-19)
- [ ] AC6: DEPRECATED.md adicionado em `backend/migrations/` (DB-24)
- [ ] AC7: `monthly_quota` retention job criado (24 meses) (DB-29)
- [ ] AC8: Convencao de naming para constraints/triggers documentada em contributing guide (DB-12, DB-25, DB-26)
- [ ] AC9: Formatacao de datas padronizada com helper function (FE-28)
- [ ] AC10: Toast vs banner convencao documentada (FE-29)
- [ ] AC11: Tailwind content paths corrigidos (remover `pages/`) (FE-25)

## Tasks

Os tasks sao agrupados por esforco para permitir resolucao oportunistica:

### Quick Wins (<1h cada, total ~6h)
- [ ] T1: DB-05 -- pg_cron retention para partner_referrals (12 meses)
- [ ] T2: DB-19 -- ALTER COLUMN created_at SET NOT NULL (2 tabelas)
- [ ] T3: DB-21 -- Documentar RLS policy para trial_email_log
- [ ] T4: DB-22 -- Documentar que org admin UPDATE e via service role
- [ ] T5: DB-24 -- Adicionar DEPRECATED.md em backend/migrations/
- [ ] T6: DB-27 -- Documentar search_id TEXT vs UUID decision
- [ ] T7: DB-29 -- pg_cron retention para monthly_quota (24 meses)
- [ ] T8: DB-31 -- Documentar plan_type CHECK armadilha
- [ ] T9: FE-05 -- Adicionar comentario explicando hex raw by design
- [ ] T10: FE-25 -- Remover `pages/` de Tailwind content paths
- [ ] T11: DB-09 -- Documentar FK ordering inconsistencia

### Small Items (1-4h cada, total ~22h)
- [ ] T12: SYS-19 -- Script para adicionar URLs a Issue references em comentarios (4h)
- [ ] T13: DB-18 -- Migration DROP COLUMN stripe_price_id (1h)
- [ ] T14: FE-08 -- Otimizar 4 imagens em /public com next/image onde falta (2h)
- [ ] T15: FE-10 -- Adicionar loading.tsx em blog/SEO pages (2h)
- [ ] T16: FE-11 -- Remover animacoes CSS duplicadas (manter Tailwind) (2h)
- [ ] T17: FE-15 -- Paliativo responsive para admin (overflow-x-auto) (1h)
- [ ] T18: FE-17 -- Documentar pull-to-refresh pattern como aceito (1h)
- [ ] T19: FE-28 -- Criar `utils/formatDate.ts` e migrar 25 arquivos (3h)
- [ ] T20: FE-29 -- Documentar convencao toast vs banner + implementar (4h)
- [ ] T21: FE-30 -- Restaurar Shepherd arrow (1h)
- [ ] T22: FE-33 -- Padronizar tokens em error pages (2h)

### Larger Items (>4h)
- [ ] T23: SYS-20 -- Avaliar SEO pages para CMS (pode decidir aceitar como esta) (8h)

### Zero-Effort (documentar apenas)
- [ ] T24: DB-12 -- README com convencao de naming para migrations futuras
- [ ] T25: DB-14 -- Aceitar cleanup trigger overhead como negligenciavel
- [ ] T26: DB-15 -- Aceitar alert_sent_items scan (index cobre)
- [ ] T27: DB-23 -- Aceitar migration 027b superseded (idempotente)
- [ ] T28: DB-25, DB-26 -- Documentar convencao de naming going forward
- [ ] T29: FE-23 -- Aceitar 59 API routes (standalone output, nao e problema real)
- [ ] T30: FE-27 -- Aceitar NProgress (nao e debt real)
- [ ] T31: FE-32 -- Aceitar Framer Motion (tree-shaking funciona)

## Testes Requeridos

- [ ] Retention jobs rodam sem erros em staging
- [ ] NOT NULL migrations aplicam sem data loss
- [ ] `npm run build` sem erros apos mudancas FE
- [ ] formatDate helper funciona com todos padroes existentes

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **Esta story e de resolucao oportunistica** -- items podem ser feitos individualmente durante sprints regulares.
- **9 items tem 0h** (aceitos como estao). O "task" e documentar a decisao.
- **DB-18 depende de DEBT-S0.2** (Stripe IDs em config table) estar completo antes de dropar a coluna.
- **SYS-20 (8h)** pode ser decidido como "aceitar" apos avaliacao -- SEO pages hardcoded funcionam para volume atual.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` (todas secoes)
- Database items: secao "Database"
- Frontend items: secao "Frontend"
- Sistema items: secao "Sistema"
