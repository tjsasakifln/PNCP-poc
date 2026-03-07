# HARDEN-028: Stripe Webhook Events Purge (90 dias)

**Severidade:** BAIXA
**Esforço:** 10 min
**Quick Win:** Nao
**Origem:** Conselho CTO — Auditoria de Fragilidades (2026-03-06)

## Contexto

Cada webhook event é salvo em `stripe_webhook_events` para idempotency/audit, mas não há purge. Tabela cresce indefinidamente — bloat de DB, queries lentas, custo de storage.

## Critérios de Aceitação

- [x] AC1: Cron job (ou Supabase scheduled function) deleta eventos > 90 dias
- [x] AC2: Roda diariamente
- [x] AC3: Log count de eventos deletados
- [x] AC4: Teste unitário

## Arquivos Afetados

- `backend/cron_jobs.py` — `purge_old_stripe_events()` + `start_stripe_events_purge_task()`
- `backend/main.py` — registra task no lifespan
- `backend/tests/test_harden028_stripe_events_purge.py` — 6 testes
