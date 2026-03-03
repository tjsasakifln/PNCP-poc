# SHIP-001: Deploy Atômico — Migrations + Code + Smoke Test

**Status:** 🔴 Pendente
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

- [ ] AC1: `supabase db push --include-all` aplica todas as 35+ migrations sem erro
- [ ] AC2: `NOTIFY pgrst, 'reload schema'` executado após push
- [ ] AC3: Smoke test valida que NENHUM endpoint retorna PGRST205
- [ ] AC4: Se PGRST205 persistir, pause+unpause projeto no Supabase dashboard
- [ ] AC5: `railway up --service smartlic-backend` deploya backend com todos os fixes
- [ ] AC6: `railway up --service bidiq-frontend` deploya frontend com CRIT-052 SSE fix
- [ ] AC7: Smoke test pós-deploy: `POST /buscar` com setor real retorna resultados (não 500)
- [ ] AC8: Smoke test pós-deploy: `GET /plans` retorna pricing correto (R$397/R$357/R$297)
- [ ] AC9: Smoke test pós-deploy: `GET /health` retorna status "healthy"
- [ ] AC10: Verificar Sentry — nenhum novo erro nos 15min pós-deploy

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
