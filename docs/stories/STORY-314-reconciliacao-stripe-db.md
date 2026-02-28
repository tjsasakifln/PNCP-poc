# STORY-314: Reconciliacao Stripe ⇒ DB

**Epic:** EPIC-PRE-GTM-2026-02
**Sprint:** Sprint 2 (Launch)
**Priority:** HIGH
**Story Points:** 5 SP
**Estimate:** 2-3 dias
**Owner:** @dev + @data-engineer

---

## Problem

O sistema depende 100% de webhooks Stripe para sincronizar estado de assinaturas no banco. Se um webhook falha, e processado fora de ordem, ou o servidor estava fora do ar durante o evento, o DB fica dessincronizado do Stripe. Nao existe mecanismo de reconciliacao batch para detectar e corrigir essas divergencias. Riscos: usuario pago sem acesso, usuario inadimplente com acesso, revenue leak.

## Solution

Criar worker de reconciliacao batch que periodicamente compara estado Stripe (source of truth) com estado do DB local, detecta divergencias, e corrige automaticamente com logging auditavel.

---

## Acceptance Criteria

### Backend — Reconciliation Worker

- [ ] **AC1:** Criar `backend/services/stripe_reconciliation.py` com funcao `reconcile_subscriptions()`:
  - Lista todas assinaturas ativas no Stripe via `stripe.Subscription.list(status='all', limit=100)`
  - Compara com `user_subscriptions` no Supabase
  - Detecta divergencias em: `is_active`, `plan_id`, `billing_period`, `subscription_status`, `expires_at`
- [ ] **AC2:** Para cada divergencia detectada:
  - Log estruturado: `{ user_id, field, stripe_value, db_value, action_taken }`
  - Auto-fix: atualizar DB para match Stripe (Stripe e source of truth)
  - Sincronizar `profiles.plan_type` (manter pattern existente)
  - Invalidar cache Redis (manter pattern existente)
- [ ] **AC3:** Detectar "orphan subscriptions" — assinaturas no Stripe sem match no DB:
  - Log como WARNING
  - Criar registro em `user_subscriptions` se customer_email match com profiles
  - Caso contrario: log para investigacao manual
- [ ] **AC4:** Detectar "zombie subscriptions" — assinaturas ativas no DB mas canceladas/expired no Stripe:
  - Auto-fix: desativar no DB (`is_active = false`)
  - Sincronizar `profiles.plan_type`

### Backend — Scheduling

- [ ] **AC5:** Criar ARQ task `reconcile_stripe` em `cron_jobs.py`:
  - Executar diariamente as 03:00 BRT (06:00 UTC) — horario de baixo trafego
  - Configuravel via `RECONCILIATION_ENABLED` e `RECONCILIATION_HOUR_UTC` em config.py
- [ ] **AC6:** Protecao contra execucao duplicada:
  - Lock Redis com TTL de 30 minutos (`smartlic:reconciliation:lock`)
  - Se lock existe, skip execution

### Backend — Reconciliation Report

- [ ] **AC7:** Criar tabela `reconciliation_log`:
  - `id`, `run_at`, `total_checked`, `divergences_found`, `auto_fixed`, `manual_review`, `duration_ms`
- [ ] **AC8:** Ao final de cada execucao, salvar report na tabela
- [ ] **AC9:** Se divergencias > 0: enviar email de alerta para admin
- [ ] **AC10:** Endpoint admin `GET /admin/reconciliation/history` com ultimos 30 runs

### Backend — Metricas

- [ ] **AC11:** Metricas Prometheus:
  - `smartlic_reconciliation_runs_total`
  - `smartlic_reconciliation_divergences_total` (labels: field, direction: stripe_ahead|db_ahead)
  - `smartlic_reconciliation_fixes_total`
  - `smartlic_reconciliation_duration_seconds`

### Frontend — Admin Dashboard

- [ ] **AC12:** Widget no admin dashboard mostrando:
  - Ultimo run: data/hora, divergencias, fixes
  - Status: verde (0 divergencias) / amarelo (< 5) / vermelho (>= 5)
- [ ] **AC13:** Botao "Executar reconciliacao agora" (trigger manual via API)

### Testes

- [ ] **AC14:** Testes para cada tipo de divergencia (status, plan, billing_period, expires_at)
- [ ] **AC15:** Testes para orphan e zombie detection
- [ ] **AC16:** Teste de lock/dedup
- [ ] **AC17:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Webhook idempotency | `backend/webhooks/stripe.py:55-149` | Existe |
| stripe_webhook_events table | Supabase migration | Existe |
| Plan type sync pattern | Todos os webhook handlers | Existe (replicar) |
| Cache invalidation | Redis pattern em webhooks | Existe (replicar) |
| ARQ queue | `backend/job_queue.py` | Existe |
| Stripe SDK | `requirements.txt` → stripe | Existe |
| Admin routes | `backend/routes/admin.py` | Existe |

## Files Esperados (Output)

**Novos:**
- `backend/services/stripe_reconciliation.py`
- `backend/tests/test_stripe_reconciliation.py`
- `supabase/migrations/XXXXXXXX_add_reconciliation_log.sql`

**Modificados:**
- `backend/cron_jobs.py`
- `backend/config.py`
- `backend/metrics.py`
- `frontend/app/admin/page.tsx` (widget)

## Dependencias

- Stripe API key com permissao de leitura de subscriptions
- STORY-309 (dunning) — reconciliacao pode detectar usuarios stuck em past_due

## Riscos

- Rate limit Stripe API: `Subscription.list()` com pagination (100/page) — monitorar
- Reconciliacao NAO deve sobrescrever estado durante dunning ativo (past_due e valido, nao e divergencia)
- Cuidado com timezone: Stripe retorna UTC, DB pode ter timezone mismatch
