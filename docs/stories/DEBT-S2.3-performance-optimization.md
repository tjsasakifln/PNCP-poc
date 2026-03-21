# DEBT-S2.3: Database Performance + Schema Fixes
**Epic:** EPIC-DEBT
**Sprint:** 2
**Priority:** P2
**Estimated Hours:** 16.5h
**Assignee:** TBD

## Objetivo

Resolver debitos de performance e integridade do banco de dados: rewrite de queries com correlated subqueries, adicionar metricas de drift, versionamento de JSONB, e batch de fixes menores (nullable columns, cache warmer filter, OAuth docs, down migrations, CHECK constraints).

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| DB-03 | `get_conversations_with_unread_count()` COUNT(*) OVER() antes de LIMIT/OFFSET. | MEDIUM | 3h |
| DB-28 | `conversations` correlated subquery per row. 50 subqueries por page. Mais impactante que DB-03. | MEDIUM | 2h |
| DB-04 | `profiles.plan_type` sem metrica de drift granular. Reconciliacao ja funciona. | MEDIUM | 1h |
| DB-30 | `search_results_store`/`search_results_cache` JSONB sem versionamento. Dados antigos e novos coexistem. | MEDIUM | 4h |
| DB-08 | `search_state_transitions.user_id` nullable. Adicionado para backfill. Requer verificacao producao. | MEDIUM | 1h |
| DB-10 | System cache warmer em `auth.users`. Conta sentinela aparece em listings admin. | MEDIUM | 0.5h |
| DB-11 | OAuth tokens no public schema. AES-256 na app layer. | MEDIUM | 2h |
| DB-13 | Sem down migrations. Criar rollback apenas para billing e RLS. | MEDIUM | 2h |
| DB-17 | `organizations.plan_type` CHECK permissivo. 13 valores incluindo legacy. | MEDIUM | 0.5h |

## Acceptance Criteria

- [ ] AC1: `get_conversations_with_unread_count()` reescrita com LEFT JOIN (sem window function pre-LIMIT)
- [ ] AC2: Correlated subquery de `unread_count` substituida por LEFT JOIN com GROUP BY
- [ ] AC3: Query de conversations executa em <10ms com 500 rows (EXPLAIN ANALYZE)
- [ ] AC4: Metrica Prometheus `smartlic_plan_drift_total` com label `divergence_type` (plan_mismatch, period_mismatch, etc.)
- [ ] AC5: `search_results_store` e `search_results_cache` tem coluna `schema_version INTEGER DEFAULT 1`
- [ ] AC6: Backend valida `schema_version` ao ler JSONB e trata versoes antigas gracefully
- [ ] AC7: `search_state_transitions.user_id` e NOT NULL (apos confirmar zero NULLs em producao)
- [ ] AC8: Cache warmer account filtrada de listings admin (`WHERE id != cache_warmer_id`)
- [ ] AC9: Documentacao de schema de OAuth tokens (localizacao, encriptacao, rotation procedure)
- [ ] AC10: Down migrations criadas para: billing tables e RLS policies
- [ ] AC11: `organizations.plan_type` CHECK atualizado para remover valores legacy nao mais usados

## Tasks

### Track 1: Conversations Performance (5h)
- [ ] T1: Analisar `get_conversations_with_unread_count()` atual com EXPLAIN ANALYZE
- [ ] T2: Reescrever com LEFT JOIN + GROUP BY (eliminar window function e correlated subquery)
- [ ] T3: Criar migration com nova funcao
- [ ] T4: Testar com volume de producao simulado

### Track 2: JSONB Versioning (4h)
- [ ] T5: Criar migration: ADD COLUMN `schema_version INTEGER DEFAULT 1` em `search_results_store` e `search_results_cache`
- [ ] T6: Atualizar backend write para incluir `schema_version`
- [ ] T7: Atualizar backend read para validar `schema_version` e tratar versoes antigas

### Track 3: Batch Fixes (7.5h)
- [ ] T8: Adicionar metrica `smartlic_plan_drift_total` em `stripe_reconciliation.py` (1h)
- [ ] T9: Verificar NULLs em producao para `search_state_transitions.user_id`, se zero: ALTER COLUMN NOT NULL (1h)
- [ ] T10: Filtrar cache warmer account de admin listings (0.5h)
- [ ] T11: Documentar schema OAuth tokens + rotation procedure (2h)
- [ ] T12: Criar down migrations para billing tables e RLS policies (2h)
- [ ] T13: Atualizar `organizations.plan_type` CHECK -- remover valores legacy (0.5h)

## Testes Requeridos

- [ ] `test_conversations_query.py`: nova query retorna mesmos resultados que antiga
- [ ] `test_conversations_query.py`: EXPLAIN ANALYZE mostra <10ms para 500 rows
- [ ] `test_jsonb_versioning.py`: write inclui schema_version
- [ ] `test_jsonb_versioning.py`: read trata schema_version=1 e ausente (legacy)
- [ ] `test_plan_drift.py`: metrica incrementada quando drift detectado
- [ ] Down migrations: `supabase db push` + `supabase db reset` funcionam
- [ ] Backend test count >= 7332

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **DB-03 + DB-28 devem ser resolvidos juntos** -- ambos sao sobre a mesma funcao `get_conversations_with_unread_count()`.
- **DB-08:** Verificar em producao ANTES de criar migration NOT NULL. Query: `SELECT COUNT(*) FROM search_state_transitions WHERE user_id IS NULL`.
- **DB-13:** Down migrations apenas para tabelas criticas (billing, RLS). Nao criar para todas 35 migrations.
- **DB-11:** Nao e um fix de codigo, e documentacao. OAuth tokens JA estao encriptados com AES-256.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secao "Database"
- Conversations: `supabase/migrations/` (funcao `get_conversations_with_unread_count`)
- Cache: `backend/search_cache.py`
- Reconciliation: `backend/stripe_reconciliation.py`
- OAuth: `backend/oauth.py`
