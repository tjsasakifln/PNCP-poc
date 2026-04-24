# SEN-BE-002: Schema drift — colunas ausentes em `profiles` e `search_sessions`

**Status:** Ready
**Origem:** Sentry unresolved — issues 7407804459 (10 evt) + 7407623714 (5 evt)
**Prioridade:** P1 — Alto (endpoints `/v1/me/profile-context` e `/v1/analytics/trial-value` quebram)
**Complexidade:** S (Small)
**Owner:** @data-engineer
**Tipo:** Migration / Data

---

## Problema

Código backend está consultando duas colunas que não existem no schema de produção:

1. `profiles.profile_context` — `APIError: column profiles.profile_context does not exist` (10 eventos; culprit: `supabase_client.sb_execute`)
2. `search_sessions.top_result_objeto` — `Error fetching trial value for 39b32b6f-***: {'message': 'column search_sessions.top_result_objeto does not exist', 'code': '42703'}` (5 eventos; culprit: `routes.analytics.get_trial_value`)

Causa provável: migration aplicada em local/staging mas não em produção (drift CRIT-050/CRIT-039 recorrência) OU migration revertida sem o código correspondente.

Impacto:
- Endpoint `PUT/GET /v1/profile/context` retorna 500
- Endpoint `GET /v1/analytics/trial-value` retorna 500 — bloqueia métrica de trial usada em onboarding
- Primeiro seen: `2026-04-13`; ainda recebendo eventos em `2026-04-22` — 9 dias vivos sem fix

---

## Critérios de Aceite

- [ ] **AC1:** Identificar migration que adiciona `profiles.profile_context` — conferir se está em `supabase/migrations/` mas não aplicada em produção
- [ ] **AC2:** Identificar migration de `search_sessions.top_result_objeto` — idem
- [ ] **AC3:** Se migration não existe: criar `supabase/migrations/YYYYMMDDHHMMSS_sen_be_002_profile_context_columns.sql` + `.down.sql` pareado
- [ ] **AC4:** `npx supabase db push` aplicado em produção — verificar via `npx supabase migration list` remoto
- [ ] **AC5:** Sentry issues `7407804459` + `7407623714` param de receber eventos (verificar `lastSeen` em 48h)
- [ ] **AC6:** Smoke test pós-deploy: `curl https://api.smartlic.tech/v1/analytics/trial-value` (autenticado) retorna 200
- [ ] **AC7:** PostgREST schema reload enviado via `NOTIFY pgrst, 'reload schema'` pós-migration (evita PGRST205 cache)

### Anti-requisitos

- NÃO fazer rollback do código — colunas são requisito de feature ativa
- NÃO adicionar `try/except: pass` para mascarar — schema deve ser consistente

---

## Referência de implementação

Rotas afetadas (confirmar):
- `backend/routes/user.py::get_profile_context` / `put_profile_context`
- `backend/routes/analytics.py::get_trial_value`

Pipeline CI (CRIT-050) deveria ter pegado: `migration-check.yml` no push para main. Verificar se migration-gate.yml está ativo e por que drift passou.

---

## Riscos

- **R1 (Médio):** Column novo em `profiles` (~usuários ativos) pode precisar backfill default — definir explicitamente na migration
- **R2 (Baixo):** `search_sessions.top_result_objeto` é analítico — NULL tolerável para rows históricas

## Dependências

- Acesso Supabase CLI com `SUPABASE_ACCESS_TOKEN`
- Revisar `.github/workflows/deploy.yml` para confirmar auto-apply migration está funcional (CRIT-050)

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada a partir de Sentry scan — schema drift 9 dias vivo |
| 2026-04-23 | @po | Validação 10/10 → **GO**. LIVE (lastSeen 2026-04-22). Nota: HOTFIX-001 fixou coluna `sectors` — esta story trata colunas DIFERENTES (profile_context, top_result_objeto). Promovida Draft → Ready |
