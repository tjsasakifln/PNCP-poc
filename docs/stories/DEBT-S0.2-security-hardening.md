# DEBT-S0.2: Security Hardening -- Stripe IDs + Dependencies
**Epic:** EPIC-DEBT
**Sprint:** 0
**Priority:** P0
**Estimated Hours:** 3.5h
**Assignee:** TBD

## Objetivo

Eliminar riscos de seguranca imediatos: (1) remover Stripe price IDs de producao hardcoded em migrations que podem causar cobrancas reais em staging, e (2) corrigir dependencia de producao listada como devDependency.

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| DB-01 | Stripe price IDs hardcoded em 5 migration files com `price_1*` IDs de producao. Staging pode cobrar precos reais. | CRITICAL | 3h |
| FE-19 | react-hook-form em devDependencies. Usado em producao (signup, onboarding). Funciona porque Next.js bundla tudo, mas semanticamente incorreto. | MEDIUM | 0.5h |

## Acceptance Criteria

- [ ] AC1: Nova migration cria config table ou popula `plan_billing_periods` via `current_setting()` para Stripe price IDs
- [ ] AC2: Seed script para staging/dev popula price IDs de env vars (nao hardcoded)
- [ ] AC3: Fresh install via `seed.sql` funciona com price IDs de test-mode do Stripe
- [ ] AC4: Migrations existentes NAO sao editadas (imutabilidade de migrations respeitada)
- [ ] AC5: `grep -r 'price_1' supabase/migrations/` retorna apenas migrations historicas ja aplicadas
- [ ] AC6: `react-hook-form` movido de devDependencies para dependencies em `package.json`
- [ ] AC7: `npm install --production` inclui react-hook-form

## Tasks

- [ ] T1: Criar nova migration que adiciona config table ou atualiza `plan_billing_periods` para ler price IDs de `current_setting()`
- [ ] T2: Criar seed script (`scripts/seed-stripe-ids.sql`) que popula IDs via env vars
- [ ] T3: Documentar procedimento de setup de staging com Stripe test-mode IDs
- [ ] T4: Testar fresh install em ambiente limpo
- [ ] T5: Mover `react-hook-form` de devDependencies para dependencies no `frontend/package.json`
- [ ] T6: Verificar que `npm run build` continua funcionando

## Testes Requeridos

- [ ] Fresh install com seed script popula price IDs corretos
- [ ] Backend billing endpoints funcionam com novos IDs
- [ ] `npm run build` sem erros apos mudanca de dependencias
- [ ] Stripe checkout flow funciona em staging com test-mode IDs

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **NAO editar migrations existentes.** Criar nova migration que sobrescreve os valores.
- DB-01 desbloqueia DB-18 (drop deprecated `stripe_price_id` column) no Backlog.
- FE-19 e um quick fix de 5 minutos mas semanticamente importante para `npm install --production`.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secao "Database" (DB-01) e "Frontend" (FE-19)
- Migrations: `supabase/migrations/`
- Package.json: `frontend/package.json`
