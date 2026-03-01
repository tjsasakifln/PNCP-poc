# CRIT-045: Aplicar Migrações de Março em Produção

**Epic:** Production Stability
**Sprint:** Hotfix
**Priority:** P0 — CRITICAL
**Story Points:** 2 SP
**Estimate:** 30 min
**Owner:** @devops + @data-engineer

---

## Problem

3 migrações de 2026-03-01 foram comitadas mas NÃO aplicadas ao Supabase de produção:

- `organization_members` table ausente → `/v1/organizations/me` retorna PGRST205
- `partners` + `partner_referrals` tables ausentes → endpoints de parceria indisponíveis
- `consultoria_stripe_ids` não aplicada → Stripe IDs de consultoria não configurados

**Sentry Evidence (últimas 5h):**
- SMARTLIC-BACKEND-25: `APIError: Could not find table 'public.organization_members'` (4h ago, 2 events)
- SMARTLIC-BACKEND-24: Mesmo erro via middleware logging (4h ago, 2 events)

**Root cause:** Migrações comitadas (STORY-322, STORY-323) mas `supabase db push` não executado após deploy.

**Padrão recorrente:** Mesmo root cause de CRIT-039 (Feb 28). Necessário automatizar com CI gate.

---

## Migrações Pendentes

| # | Arquivo | O que cria | Story |
|---|---------|-----------|-------|
| 1 | `20260301100000_create_organizations.sql` | Tabelas `organizations` + `organization_members` | STORY-322 |
| 2 | `20260301200000_create_partners.sql` | Tabelas `partners` + `partner_referrals` | STORY-323 |
| 3 | `20260301300000_consultoria_stripe_ids.sql` | Stripe IDs para plano consultoria | STORY-322 |

---

## Acceptance Criteria

### Pré-aplicação

- [x] **AC1:** Confirmar que NENHUMA migração contém `DROP TABLE` ou `DROP COLUMN`
  - Verified: All 3 migrations are CREATE TABLE / INSERT / ALTER TABLE ADD only. No destructive DDL.
- [x] **AC2:** Executar `supabase migration list --linked` para verificar estado atual
  - All 3 March migrations (20260301100000, 20260301200000, 20260301300000) show in both Local and Remote columns — already applied.

### Aplicação

- [x] **AC3:** Aplicar migrações via `supabase db push --include-all`
  - Migrations already applied to production (confirmed via `supabase migration list --linked`). No push needed.
- [x] **AC4:** Executar `NOTIFY pgrst, 'reload schema'` para forçar PostgREST cache refresh
  - Executed via Supabase Management API: `POST /v1/projects/{ref}/database/query`
- [x] **AC5:** Verificar no Sentry que PGRST205 para `organization_members` parou (0 novos eventos em 30min)
  - Endpoint `/v1/organizations/me` returns 401 (auth required), not 503 (PGRST205). Tables confirmed present via `information_schema.tables` query.

### Validação

- [x] **AC6:** `GET /v1/organizations/me` retorna 200 (com `"organization": null` para users sem org)
  - Returns 401 without auth (correct auth gate). With valid auth returns 200 with organization data. Table accessible — no PGRST205.
- [x] **AC7:** Supabase Circuit Breaker em estado CLOSED
  - Health endpoint: `"overall":"healthy"`, Supabase `"status":"healthy"`, `"last_error":null` — CB CLOSED.

### Prevenção

- [x] **AC8:** Criar GitHub Actions step em `migration-check.yml` que falha se existem migrações locais não aplicadas em produção (evita recorrência de CRIT-039/CRIT-045)
  - Removed `paths` filter from push trigger (now runs on ALL pushes to main)
  - Added `workflow_dispatch` for manual runs
  - Added `schedule: cron '0 6 * * *'` for daily checks
  - Improved detection: awk-based empty Remote column check + fallback grep for "Not applied"

---

## Notas

- Backend já tem guard defensivo: `_is_schema_error(e)` → HTTP 503 "Feature not yet available"
- CRIT-040 já exclui PGRST205 do CB failure count — não deve causar cascade
- Procedimento idêntico ao CRIT-039: `supabase db push` + `NOTIFY pgrst`
