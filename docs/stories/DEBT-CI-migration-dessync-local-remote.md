# DEBT-CI — Migration Check Post-Merge Alert: dessync local vs remote + deploy.yml timeout

**Status:** Ready
**Type:** Debt (CI alert red recorrente + deploy auto-apply quebrado)
**Priority:** P1 — degrada trust em main alerts + bloqueia auto-apply migration futuro
**Owner:** @data-engineer + @devops
**Origem:** sessão temporal-dongarra 2026-04-23 (Phase 0 probe)
**Depende de:** —

---

## Problema

Dois sintomas correlatos detectados:

### Sintoma 1 — Migration Check (Post-Merge Alert) falha 3x em <24h

Runs: `24821112767` (06:46Z), `24816009176` (04:02Z), `24812926886` (02:12Z) — todos exit 1 no step "Check for unapplied migrations".

### Sintoma 2 — Deploy to Production pós-#470 falhou

Run `24809132182` (2026-04-23 ~01:12Z): job `Apply Pending Migrations` falhou no step "Check for pending migrations" — `supabase migration list --linked` travou por 2m31s (01:12:58 → 01:15:28) e retornou exit 1 silencioso. Bash `-e` propagou exit, job morreu. Migration do PR #470 (`20260422120000_add_api_status_to_health_checks`) **nunca foi aplicada em prod**.

## Root Cause (hipóteses)

### H1 — Dessync `supabase_migrations` tracking table

Probe local (`npx supabase db push --linked`) detectou **10 migrations "local antes da última remota"** que normalmente deveriam ter sido aplicadas:

```
20260414132000_backfill_pncp_raw_bids_dates.sql
20260414133000_search_datalake_coalesce_dates.sql
20260415120000_fts_portuguese_smartlic.sql
20260415120001_search_datalake_use_portuguese_smartlic.sql
20260415140000_story56_db_medium_fixes.sql
20260416120000_story64_schedule_health_checks_cleanup.sql
20260416120100_story64_comment_crawl_batch_id.sql
20260416120200_story64_search_results_store_cascade.sql
20260420000001_create_founding_leads.sql
20260420000002_add_profiles_cnae_primary.sql
```

`supabase migration list --linked` mostra dual-row pattern — algumas migrations têm Local+Remote populated, outras só Local. Sugere que o tracking table do remote perdeu linhas, OR migrations foram aplicadas out-of-order (manual psql, não via supabase CLI), OR dual-row é artefato de CLI version mismatch.

### H2 — Deploy workflow hang no supabase CLI call

`supabase migration list --linked` no CI runner demora >2.5min silenciosos antes de crash/exit. Local (WSL2) roda em ~3s. Network/DNS/rate-limit do runner GH Actions suspeito, mas não provado.

### H3 — Migrations já aplicadas manualmente via psql

Se alguém rodou `psql -f migration.sql` direto sem `INSERT INTO supabase_migrations.schema_migrations`, o DDL foi aplicado mas o tracking table não tem a linha. `supabase db push` então "detecta" como unapplied.

## Critérios de Aceite

### Diagnóstico (AC1–AC3)

- [ ] **AC1:** Executar query direta no Supabase: `SELECT version FROM supabase_migrations.schema_migrations ORDER BY version` e comparar com `ls supabase/migrations/*.sql`. Documentar quais estão em disk mas não em tracking table.
- [ ] **AC2:** Para cada migration "faltante" no tracking, verificar empiricamente se o DDL foi aplicado (ex: para `20260422120000`, `SELECT column_name FROM information_schema.columns WHERE table_name='health_checks' AND column_name='api_status'`). Classificar: (a) aplicadas sem tracking, (b) não aplicadas.
- [ ] **AC3:** Documentar timeline (via git log em `supabase/migrations/`) de quando cada migration foi adicionada e comparar com deploys de main no período.

### Fix tracking (AC4–AC5)

- [ ] **AC4:** Para migrations classificadas como "aplicadas sem tracking" — usar `supabase migration repair --status applied <version>` para cada. Rollback via `repair --status reverted` se necessário.
- [ ] **AC5:** Para migrations genuinamente não aplicadas — rodar DDL manualmente com idempotency verification, depois `repair --status applied`. Nunca `db push --include-all` sem auditoria individual.

### Fix deploy.yml (AC6–AC8)

- [ ] **AC6:** Adicionar `timeout 60` no comando `supabase migration list --linked` em `deploy.yml::apply-migrations::Check for pending migrations` para prevenir hang silent de 2.5min.
- [ ] **AC7:** Substituir `bash -e` strictness pelo `set +e` local no bloco `OUTPUT=$(...)` — capturar exit code em variável e decidir explicitamente se falha ou segue com has_pending=unknown + warning.
- [ ] **AC8:** Após fix, re-trigger `gh workflow run "Deploy to Production (Railway)"` manualmente em commit benign de main e observar que apply-migrations roda verde (sem pending) ou aplica limpo.

### Validação (AC9)

- [ ] **AC9:** Após AC4/AC5, rodar `gh workflow run "Migration Check (Post-Merge Alert)"` — deve retornar verde. Alert fica estável por 48h consecutivas (daily cron + post-merge triggers).

## Arquivos a modificar

- `.github/workflows/deploy.yml` (AC6, AC7) — adicionar timeout + capturar exit code
- `supabase/migrations/` (AC4, AC5) — nenhuma mudança de arquivo; apenas `repair` via CLI
- Novo: `docs/ops/migration-dessync-2026-04-23.md` (AC1, AC2, AC3) — audit trail

## Riscos

- **R1 (Alto):** `supabase migration repair --status applied <version>` em migration não realmente aplicada gera dessync reverso (tracking says yes, schema says no). Mitigação: AC2 exige verificação empírica por migration antes de AC4.
- **R2 (Médio):** `--include-all` tentativo pode re-executar DDL não idempotente e quebrar (ex: `CREATE TYPE` duplicado). Mitigação: AC5 força DDL manual com idempotency first.
- **R3 (Baixo):** Fix timeout em `deploy.yml` pode mascarar problema de network real do runner. Mitigação: AC8 valida fluxo end-to-end em deploy real.

## Dependências

- Acesso Supabase (token + project ref) — já disponível via `.env` local e secrets GH.
- Psql client para queries direct contra remote Supabase.

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-23 | @sm River (via temporal-dongarra session) | Story criada após Phase 0 probe detectar dessync sistêmico |
