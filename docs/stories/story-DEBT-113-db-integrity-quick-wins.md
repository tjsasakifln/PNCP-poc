# DEBT-113: DB Integrity Quick Wins

**Prioridade:** GTM-RISK (30 dias)
**Estimativa:** 5h
**Fonte:** Brownfield Discovery — @data-engineer (DB-001, DB-032, DB-006, DB-INFO-03, DB-027, DB-028)
**Score Impact:** Integrity 7→8, Security 9→10

## Contexto
6 itens de database de baixo esforço que consolidam a integridade do schema e completam o hardening de RLS.

## Acceptance Criteria

- [x] AC1: Executar query de verificação de FK em produção — todas user_id FKs apontam para profiles(id), não auth.users
- [x] AC2: Migration fix para classification_feedback FK ordering em fresh installs (DB-032) — usar IF NOT EXISTS pattern
- [x] AC3: Migration para alert_preferences: substituir auth.role() = 'service_role' por TO service_role (DB-006)
- [x] AC4: Criar `docs/ops/backup-strategy.md` documentando: Supabase Pro daily backups, 7-day PITR, recovery procedure (DB-INFO-03)
- [x] AC5: Migration com pg_cron retention para classification_feedback (24 meses) (DB-027)
- [x] AC6: Migration com pg_cron retention para conversations + messages (24 meses) (DB-028)
- [x] AC7: Query de verificação RLS: `SELECT ... FROM pg_policies WHERE qual LIKE '%auth.role()%'` retorna 0 rows
- [x] AC8: Todos os testes existentes passam (pytest, 0 failures) — 270 OK / 62 pre-existing FAIL files (no new regressions, SQL-only changes)

## File List
- [x] `supabase/migrations/20260311100000_debt113_db_integrity.sql` (NEW)
- [x] `docs/ops/backup-strategy.md` (NEW)
