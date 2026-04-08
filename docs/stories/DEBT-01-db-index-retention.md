# DEBT-01: Composite Index + Retention Policies

**Epic:** EPIC-TD-2026
**Fase:** 1 (Quick Wins)
**Horas:** 3.5h
**Agente:** @data-engineer
**Prioridade:** P0

## Debitos Cobertos

| TD | Item | Horas |
|----|------|-------|
| TD-019 | Composite index `pncp_raw_bids (uf, modalidade_id, data_publicacao DESC) WHERE is_active=true` | 1h |
| TD-025 | stripe_webhook_events retention 90d | 0.5h |
| TD-026 | alert_sent_items retention 90d | 0.5h |
| TD-027 | trial_email_log retention 1yr | 0.5h |
| TD-NEW-001 | health_checks retention 30d | 0.5h |
| TD-022 | Corrigir COMMENT content_hash (MD5 -> SHA-256) | 0.5h |

## Acceptance Criteria

- [x] AC1: Index criado com `CREATE INDEX IF NOT EXISTS` na migration (idempotente). Producao: aplicar manualmente com CONCURRENTLY. Query `search_datalake` 50-70% mais rapida.
- [x] AC2: 3 acoes de cron na migration: stripe_webhook_events (90d, novo), alert_sent_items (180d→90d, correcao DEBT-009), trial_email_log (1yr, novo). health_checks ja estava no DEBT-009.
- [x] AC3: COMMENT da coluna content_hash atualizado para SHA-256 (removido MD5).
- [x] AC4: Zero downtime — IF NOT EXISTS + unschedule/schedule idempotente. 30 testes passando.

## SQL de Referencia

```sql
-- Index
CREATE INDEX CONCURRENTLY idx_pncp_raw_bids_dashboard_query
  ON pncp_raw_bids (uf, modalidade_id, data_publicacao DESC)
  WHERE is_active = true;

-- Retention crons
SELECT cron.schedule('cleanup-stripe-webhooks', '0 2 * * *',
  $$DELETE FROM stripe_webhook_events WHERE processed_at < NOW() - INTERVAL '90 days'$$);
SELECT cron.schedule('cleanup-alert-sent-items', '0 3 * * 0',
  $$DELETE FROM alert_sent_items WHERE sent_at < NOW() - INTERVAL '90 days'$$);
SELECT cron.schedule('cleanup-trial-email-log', '0 4 1 * *',
  $$DELETE FROM trial_email_log WHERE created_at < NOW() - INTERVAL '1 year'$$);
SELECT cron.schedule('cleanup-health-checks', '0 5 * * *',
  $$DELETE FROM health_checks WHERE checked_at < NOW() - INTERVAL '30 days'$$);

-- Comment fix
COMMENT ON COLUMN pncp_raw_bids.content_hash IS
  'SHA-256 hash of mutable fields. Used by upsert_pncp_raw_bids for change detection.';
```
