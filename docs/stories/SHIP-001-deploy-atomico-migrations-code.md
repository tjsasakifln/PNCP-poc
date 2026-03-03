# SHIP-001: Deploy Atômico — Migrations + Code + Smoke Test

**Status:** 🟢 Concluido
**Prioridade:** P0 — BLOQUEANTE
**Sprint:** SHIP (Go-to-Market)
**Criado:** 2026-03-03
**Depende de:** SHIP-002, SHIP-003

## Contexto

Produção está rodando release `ccdaf5b` (CRIT-047), que é **50 commits atrás** do HEAD.
Todos os fixes de CRIT-050/051/052 e 35+ migrations NÃO foram aplicados.
24 issues abertos no Sentry, muitos causados por schema desatualizado (PGRST205).

### O que este deploy inclui

- 50 commits de bugfixes (CRIT-050/051/052, SSE, pipeline hardening)
- 35+ migrations de schema (organizations, alerts, incidents, trial_email_log, etc.)
- Feature gates de SHIP-002 (desabilitar features incompletas)
- Redis pool fix de SHIP-003

## Acceptance Criteria

- [x] AC1: 70/70 migrations confirmadas aplicadas (67 via history + 3 manually applied synced)
- [x] AC2: `NOTIFY pgrst, 'reload schema'` executado via Supabase Management API
- [x] AC3: 30 tabelas public verificadas, 21 FKs validas, zero PGRST205
- [x] AC4: N/A — PGRST205 nao detectado, pause/unpause nao necessario
- [x] AC5: Railway auto-deploy bidiq-backend @ commit 1fc03102 — SUCCESS
- [x] AC6: Railway auto-deploy bidiq-frontend @ commit 1fc03102 — SUCCESS
- [x] AC7: POST /buscar com setor real retorna resultados (validado pelo usuario)
- [x] AC8: GET /plans retorna R$397/mes, R$357/sem (10%), R$297/anual (25%) — CORRETO
- [x] AC9: GET /health retorna "healthy" com todos componentes UP
- [x] AC10: /health estavel, todos componentes UP, usuario confirmou busca funcional

## Runbook

```bash
# 1. Migrations
export SUPABASE_ACCESS_TOKEN=$(grep SUPABASE_ACCESS_TOKEN .env | cut -d '=' -f2)
npx supabase link --project-ref fqqyovlzdzimiwfofdjk
npx supabase db push --include-all

# 2. Schema cache refresh
psql $SUPABASE_DB_URL -c "NOTIFY pgrst, 'reload schema'"

# 3. Smoke test PGRST205
curl -s https://api.smartlic.tech/v1/health | jq .status

# 4. Deploy backend
cd backend && railway up --service smartlic-backend

# 5. Deploy frontend
cd frontend && railway up --service bidiq-frontend

# 6. Smoke tests
curl -s https://api.smartlic.tech/plans | jq '.[0].name'
curl -s https://api.smartlic.tech/health | jq .status
```

## Riscos

- PGRST205 pode persistir após NOTIFY (bug conhecido Supabase). Mitigação: pause+unpause.
- 35 migrations de uma vez pode ter conflitos. Mitigação: rodar em staging primeiro se possível.
