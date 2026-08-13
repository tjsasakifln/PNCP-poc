# Inventário de sunset SaaS — #2111

**Data:** 2026-08-13  
**Freeze owner:** @dev  
**Freeze registrado:** flag `SAAS_COMMERCE_ENABLED` default `false` (onda 1)  
**Autoridade:** [ADR-STRAT-001](../adr/ADR-STRAT-001-smartlic-confenge-inbound.md)

Categorias: `KEEP + ADAPT` · `SUNSET NOW` · `SUNSET AFTER DEPENDENCY` · `REPLACE` · `DEFER`

## Onda 1 (este ciclo) — Freeze

Impossível iniciar nova assinatura, trial, checkout, upgrade comercial ou plano. Componentes de migração/SEO/webhook **não** são destruídos.

| Superfície | Destino | Onda |
|------------|---------|------|
| `SAAS_COMMERCE_ENABLED` (default false) | SUNSET NOW (kill switch) | 1 |
| `POST /checkout` | SUNSET NOW → 410 | 1 |
| `POST /api/checkout/one-time` | SUNSET NOW → 410 | 1 |
| `POST /api/checkout/api-subscription` | SUNSET NOW → 410 | 1 |
| `POST /founding/checkout` | SUNSET NOW → 410 | 1 |
| `POST /intel-reports/checkout` | SUNSET NOW → 410 | 1 |
| `POST /billing/setup-intent` | SUNSET NOW → 410 | 1 |
| `POST /api/subscriptions/upgrade-to-lifetime` | SUNSET NOW → 410 | 1 |
| `POST /api/subscriptions/update-billing-period` | SUNSET NOW → 410 | 1 |
| `POST /trial/extend` | SUNSET NOW → 410 | 1 |
| `POST /auth/signup` (trial/card) | SUNSET NOW → 410 | 1 |

## Inventário por família

### Stripe SDK / secrets / env

| Item | Destino | Notas |
|------|---------|-------|
| `stripe` em `backend/requirements.txt` | SUNSET AFTER DEPENDENCY | Remover na onda 4 após zero uso |
| `STRIPE_SECRET_KEY`, price IDs, webhook secret | SUNSET AFTER DEPENDENCY | Não apagar secret até onda 3 |
| Frontend `@stripe/*` / Checkout.js | SUNSET AFTER DEPENDENCY | #2113/#2114 antes de tirar script |
| `ADR-BILL-SYNC-001` | SUNSET (Deprecated) | Feito em #1262 |

### Rotas backend (criar receita)

Ver onda 1. GET `/plans`, GET founding availability, GET subscription status = `KEEP + ADAPT` (leitura / clientes existentes) até onda 2–3.

### Rotas que permanecem na onda 1

| Item | Destino | Motivo |
|------|---------|--------|
| `POST /webhooks/stripe` | SUNSET AFTER DEPENDENCY | Eventos de assinaturas já existentes |
| `POST /api/subscriptions/cancel` | KEEP + ADAPT | Cliente legado precisa encerrar |
| `POST /billing-portal` | SUNSET AFTER DEPENDENCY | Portal do cliente existente |
| Admin billing sync | SUNSET AFTER DEPENDENCY | Reconciliação até onda 3 |

### Frontend / URLs públicas

| Item | Destino | Motivo |
|------|---------|--------|
| `/pricing`, `/planos`, `/signup`, `/fundadores` | SUNSET AFTER DEPENDENCY | Redirect só com #2113 + copy #2114 |
| CTAs pSEO → `/signup` | REPLACE | Onda 2 / #2114 |
| `/consultoria-b2g`, LeadCapture | KEEP + ADAPT | Destino do 410 `next` |

### Workers / emails / CI

| Item | Destino | Onda |
|------|---------|------|
| Trial emails, dunning, founders welcome | SUNSET AFTER DEPENDENCY | 3 |
| Stripe webhook handlers | SUNSET AFTER DEPENDENCY | 3 |
| Gates CI de billing | SUNSET AFTER DEPENDENCY | 4 |
| Testes de checkout | KEEP + ADAPT | Exercitam legado com flag on |

### Auth / admin / dados

| Item | Destino | Motivo |
|------|---------|--------|
| Supabase Auth admin | KEEP + ADAPT | Admin interno |
| Tabelas `profiles.plan_type`, `events_processed` | KEEP + ADAPT | Retenção fiscal/PII até política |
| Quotas / entitlements | SUNSET AFTER DEPENDENCY | Deixam de autorizar busca pública |

### Crawler / DataLake

Fora deste sunset — REPLACE via #2108, não migrar para Netcup.

## Contagens (repo no momento da auditoria)

- ~318 arquivos mencionam Stripe
- ~1.106 billing/checkout/subscription/quota/trial
- Rotas comerciais listadas acima: freeze aplicado na onda 1

## Rollback da onda 1

`SAAS_COMMERCE_ENABLED=true` no ambiente (Railway) reabre o legado sem revert de código. Não usar em produção.
