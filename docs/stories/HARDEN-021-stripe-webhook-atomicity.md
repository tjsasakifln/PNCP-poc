# HARDEN-021: Stripe Webhook Idempotency Atômica (ON CONFLICT)

**Severidade:** MEDIA
**Esforço:** 15 min
**Quick Win:** Nao
**Origem:** Conselho CTO — Auditoria de Fragilidades (2026-03-06)

## Contexto

Webhook faz check+insert em duas operações separadas para idempotency. Dois webhooks simultâneos com mesmo event_id podem ambos passar o check, causando race condition no update de profiles.plan_type.

## Critérios de Aceitação

- [x] AC1: Substituir SELECT+INSERT por INSERT ON CONFLICT DO NOTHING
- [x] AC2: Se insert retorna empty (conflict), skip processing
- [x] AC3: Teste com webhooks concorrentes simulados
- [x] AC4: Zero regressions

## Arquivos Afetados

- `backend/webhooks/stripe.py` — idempotency check
- `backend/tests/` — testes de webhook
