# DEBT-S1.2: Database Integrity + Backend Hardening
**Epic:** EPIC-DEBT
**Sprint:** 1
**Priority:** P1
**Estimated Hours:** 22.5h
**Assignee:** TBD

## Objetivo

Corrigir integridade de schema do banco (triggers, retention, nullable columns) e hardening de backend (request timeout, health canary, worker liveness, search decomposition). Agrupa items que podem ser resolvidos em paralelo e que desbloqueiam estabilidade operacional.

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| SYS-05 | Health canary nao detecta PNCP page size limit. Canary usa `tamanhoPagina=10`, passa quando max e 50. | HIGH | 4h |
| SYS-08 | Sem request timeout no nivel da aplicacao. Gunicorn 180s, Railway ~300s, mas sem middleware. | HIGH | 4h |
| SYS-09 | Worker liveness depende do Redis. `_worker_alive_cache` sem alerta para ausencia prolongada. | HIGH | 4h |
| SYS-10 | Search decomposition backward-compat re-exports frageis (DEBT-115). | HIGH | 4h |
| DB-02 | `handle_new_user()` omite `trial_expires_at`. App layer compensa via `created_at + TRIAL_DURATION_DAYS`. | HIGH | 1.5h |
| DB-06 | `user_subscriptions` sem retention. Dunning retries acumulam 5-10 rows/user/mes. | HIGH | 1h |

## Acceptance Criteria

- [ ] AC1: Health canary inclui request com `tamanhoPagina=50` e valida que retorna dados (nao HTTP 400)
- [ ] AC2: Middleware de request timeout configuravel (default 120s) que retorna 504 ao exceder
- [ ] AC3: Alerta (log WARNING + metrica Prometheus) quando worker esta ausente por >5 minutos
- [ ] AC4: Re-exports de backward-compat em `routes/search.py` removidos; imports diretos dos sub-modulos
- [ ] AC5: `handle_new_user()` trigger insere `trial_expires_at = NOW() + interval '14 days'`
- [ ] AC6: pg_cron job de retention para `user_subscriptions` (manter 24 meses, WHERE `is_active = false`)
- [ ] AC7: Todos os callers de `routes/search` atualizados para imports diretos

## Tasks

- [ ] T1: Atualizar health canary em `health.py` para incluir teste com `tamanhoPagina=50`
- [ ] T2: Criar middleware de request timeout em `backend/middleware/timeout.py`
- [ ] T3: Registrar middleware no app_factory
- [ ] T4: Adicionar alerta de worker ausente em `job_queue.py` (log + metrica `smartlic_worker_absent_total`)
- [ ] T5: Remover re-exports de `routes/search.py` e atualizar imports em toda a codebase
- [ ] T6: Criar migration: ALTER FUNCTION `handle_new_user()` para incluir `trial_expires_at`
- [ ] T7: Criar migration: pg_cron job `cleanup_old_subscriptions` (retention 24 meses)
- [ ] T8: Testar fresh user creation com trigger atualizado

## Testes Requeridos

- [ ] `test_health.py`: canary detecta quando PNCP rejeita tamanhoPagina=50
- [ ] `test_timeout_middleware.py`: request que excede timeout retorna 504
- [ ] `test_worker_liveness.py`: alerta disparado apos worker ausente >5min
- [ ] Verificar que imports de `routes/search` sub-modulos funcionam apos remocao de re-exports
- [ ] `test_handle_new_user.py`: novo usuario tem `trial_expires_at` preenchido
- [ ] `test_subscription_retention.py`: rows com `is_active=false` mais velhas que 24 meses sao removidas

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **DB-02 e DB-06 podem ser migrations separadas** mas no mesmo PR para review conjunto.
- SYS-10: Listar todos arquivos que importam de `routes.search` antes de remover re-exports.
- SYS-08: Timeout middleware deve ser compativel com SSE endpoints (excluir `/buscar-progress/`).
- SYS-05: PNCP pode mudar `tamanhoPagina` max novamente -- considerar parametrizar o valor testado.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secoes "Sistema" e "Database"
- Health: `backend/health.py`
- Worker: `backend/job_queue.py`
- Search routes: `backend/routes/search.py` e sub-modulos
- Trigger: `supabase/migrations/` (handle_new_user)
