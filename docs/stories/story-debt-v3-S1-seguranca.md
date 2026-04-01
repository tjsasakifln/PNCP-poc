# Story: Seguranca DB — SECURITY DEFINER + Retention

**Story ID:** DEBT-v3-S1
**Epic:** DEBT-v3 (Pre-GTM Technical Surgery)
**Sprint:** S1 (Dias 1-3)
**Priority:** P0
**Estimated Hours:** 15h
**Lead:** @data-engineer
**Execute:** @dev
**Validate:** @qa

---

## Objetivo

Eliminar todas as vulnerabilidades de SECURITY DEFINER sem SET search_path e implementar retention automatica para tabelas de crescimento ilimitado. Uma migration unica, idempotente.

---

## Debitos Cobertos

| ID | Debt | Severity | Hours |
|----|------|----------|-------|
| DB-001 | `handle_new_user()` sem SET search_path (8a redefinicao) | HIGH | 1h |
| DB-022 | `get_conversations_with_unread_count()` e `get_analytics_summary()` sem SET search_path | LOW | 1h |
| DB-021 | `check_and_increment_quota()` e `increment_quota_atomic()` sem SECURITY DEFINER + search_path | MEDIUM | 1h |
| DB-008 | search_state_transitions, classification_feedback, alert_runs, mfa_recovery_attempts sem retention | HIGH | 4h |
| DB-023 | search_sessions sem retention para estados terminais | MEDIUM | 2h |
| DB-010 | Sem VACUUM ANALYZE para pncp_raw_bids apos purge diario | MEDIUM | 2h |
| DB-014 | Index redundante em alert_preferences.user_id | LOW | 0.5h |
| DB-015 | GIN index nao usado em google_sheets_exports | LOW | 0.5h |
| DB-011 | 4 triggers com prefixo legacy (tr_, trigger_) | LOW | 1h |
| DB-019 | Composite indexes faltando (search_state_transitions, classification_feedback) | LOW | 2h |

---

## Acceptance Criteria

### Seguranca (3h)
- [ ] AC1: `grep -rn "SECURITY DEFINER" supabase/migrations/ | grep -v "SET search_path"` retorna **0 linhas** apos migration aplicada
- [ ] AC2: Funcoes afetadas: `handle_new_user`, `get_conversations_with_unread_count`, `get_analytics_summary`, `check_and_increment_quota`, `increment_quota_atomic` — todas com `SET search_path = public`
- [ ] AC3: Teste: `SELECT proname, prosecdef FROM pg_proc WHERE prosecdef = true` lista apenas funcoes com search_path configurado

### Retention (8h)
- [ ] AC4: pg_cron job para `search_state_transitions`: DELETE WHERE created_at < now() - interval '90 days' — rodando diariamente 05:00 UTC
- [ ] AC5: pg_cron job para `classification_feedback`: DELETE WHERE created_at < now() - interval '180 days'
- [ ] AC6: pg_cron job para `alert_runs`: DELETE WHERE created_at < now() - interval '90 days'
- [ ] AC7: pg_cron job para `mfa_recovery_attempts`: DELETE WHERE created_at < now() - interval '30 days'
- [ ] AC8: pg_cron job para `search_sessions`: DELETE WHERE status IN ('completed','failed','expired') AND updated_at < now() - interval '180 days'
- [ ] AC9: `SELECT count(*) FROM cron.job WHERE command LIKE '%DELETE%'` retorna >= 5
- [ ] AC10: pg_cron VACUUM ANALYZE para pncp_raw_bids rodando 07:30 UTC (30 min apos purge)
- [ ] AC11: pg_cron semanal para `check_pncp_raw_bids_bloat()`

### Indexes e Cleanup (4h)
- [ ] AC12: `DROP INDEX IF EXISTS` para alert_preferences.user_id redundante e google_sheets_exports GIN
- [ ] AC13: 4 triggers renomeados: `tr_*` → `trg_*` ou `trigger_*` → `trg_*` (match padrao do codebase)
- [ ] AC14: Composite indexes criados: `search_state_transitions(search_id, to_state)`, `classification_feedback(setor_id, created_at DESC)`

### Entrega
- [ ] AC15: Migration UNICA (nao multiplas) em `supabase/migrations/`
- [ ] AC16: Migration idempotente (IF EXISTS / IF NOT EXISTS em todas as operacoes)
- [ ] AC17: `supabase db push` executa sem erro em staging
- [ ] AC18: Backend tests: `python scripts/run_tests_safe.py --parallel 4` → 0 novos failures

---

## Technical Notes

- Todas as correcoes de SECURITY DEFINER devem usar `CREATE OR REPLACE FUNCTION` com o corpo completo (nao apenas ALTER)
- Retention periods baseados na recomendacao do @data-engineer: 90d para transient, 180d para analytics, 30d para security
- pg_cron jobs devem usar `cron.schedule()` com nomes descritivos: `retention_search_state_transitions`, etc.
- VACUUM ANALYZE para pncp_raw_bids deve rodar APOS o purge daily (07:00 UTC purge → 07:30 UTC VACUUM)

---

## Definition of Done

- [ ] Todos os ACs passam
- [ ] 0 funcoes SECURITY DEFINER sem SET search_path
- [ ] 5+ pg_cron retention jobs ativos
- [ ] Zero novos test failures
- [ ] Migration aplicada em staging e validada
