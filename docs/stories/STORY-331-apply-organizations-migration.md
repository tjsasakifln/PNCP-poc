# STORY-331: Aplicar migração de organizations e suprimir PGRST205

**Prioridade:** P1 (infra — ASGI exceptions contínuas)
**Complexidade:** S (Small)
**Sprint:** CRIT-SEARCH

## Problema

O endpoint `GET /v1/organizations/me` retorna erro PGRST205 ("public.organization_members not in schema cache") em **cada request**. Causa ASGI unhandled exceptions, spam de logs, e incrementa contadores de erro no Sentry.

**Evidência:** Logs Railway 2026-02-28: `APIError: {'message': "Could not find the table 'public.organization_members'", 'code': 'PGRST205'}` + `Unhandled error on /v1/organizations/me` + `Exception in ASGI application`.

## Causa Raiz

Migração de organizations existe no repo mas NÃO foi aplicada no Supabase de produção. PostgREST não encontra a tabela → PGRST205.

## Critérios de Aceite

- [x] AC1: Aplicar migração pendente via `npx supabase db push`
- [x] AC2: `GET /v1/organizations/me` retorna 200 (ou 404 se usuário não tem org) — não 500/PGRST205
- [x] AC3: Guard defensivo no router: PGRST205 → HTTP 503 "Feature not yet available" (não propagar como 500)
- [x] AC4: Verificar que `migration-check.yml` passa (diff zerado)
- [x] AC5: Listar e documentar TODAS as migrações pendentes (incluindo `20260227120000_concurrency_safety.sql`)

## AC5: Migrações Pendentes — Audit (2026-02-28)

**Antes da aplicação**, 3 migrações estavam pendentes (LOCAL sem REMOTE):

| Timestamp | Arquivo | Status |
|-----------|---------|--------|
| `20260228110000` | `story321_trial_email_6.sql` | **Aplicada** (renomeada de `20260228100000` — timestamp duplicado) |
| `20260228170000` | `trial_14_days.sql` | **Aplicada** |
| `20260301100000` | `create_organizations.sql` | **Aplicada** (resolve PGRST205) |
| `20260301200000` | `create_partners.sql` | **Aplicada** |

**Nota sobre `20260227120000_concurrency_safety.sql`:** Este arquivo NÃO existe. Foi splitado em 4 migrações menores, todas já aplicadas:
- `20260227120001_concurrency_stripe_webhook.sql`
- `20260227120002_concurrency_pipeline_version.sql`
- `20260227120003_concurrency_quota_rpc.sql`
- `20260227120004_concurrency_quota_rpc_grant.sql`

**Pós-aplicação:** `supabase migration list --linked` mostra 100% LOCAL = REMOTE. Zero pendentes.

## Arquivos Afetados

- `supabase/migrations/20260228100000_story321_trial_email_6.sql` → renomeada para `20260228110000_story321_trial_email_6.sql` (fix timestamp duplicado)
- `backend/routes/organizations.py` (guard defensivo PGRST205 → 503, importa `_is_schema_error`)
- `backend/tests/test_organizations_pgrst205_guard.py` (9 novos testes)
