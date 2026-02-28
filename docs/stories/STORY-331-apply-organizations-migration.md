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

- [ ] AC1: Aplicar migração pendente via `npx supabase db push`
- [ ] AC2: `GET /v1/organizations/me` retorna 200 (ou 404 se usuário não tem org) — não 500/PGRST205
- [ ] AC3: Guard defensivo no router: PGRST205 → HTTP 503 "Feature not yet available" (não propagar como 500)
- [ ] AC4: Verificar que `migration-check.yml` passa (diff zerado)
- [ ] AC5: Listar e documentar TODAS as migrações pendentes (incluindo `20260227120000_concurrency_safety.sql`)

## Arquivos Afetados

- `supabase/migrations/` (aplicar, não modificar)
- `backend/routes/organizations.py` (guard defensivo)
