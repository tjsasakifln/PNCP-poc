# STORY-INCIDENT 2026-04-23 — api.smartlic.tech DOWN por Railway rootDirectory bug

**Status:** Open (user aplicando fix)
**Type:** Incident P0 (prod backend totalmente down)
**Priority:** 🔴 P0 — api.smartlic.tech retorna 404 "Application not found"
**Started:** 2026-04-23T12:34:19Z (push merge #487 triggerou primeiro deploy FAILED)
**Detected:** 2026-04-23T13:02Z (sessão temporal-dongarra, user reportou "Could not find root directory: /backend")
**Owner:** @devops + user (Railway dashboard access necessário)
**Origem:** sessão temporal-dongarra 2026-04-23

---

## Impacto

- **api.smartlic.tech/health**: 404 "Application not found" (Railway padrão quando nenhum deploy ativo)
- **api.smartlic.tech (todas rotas)**: DOWN
- **smartlic.tech (frontend)**: 200 (outra infra, não afetado)
- **Usuários**: não conseguem fazer busca, login backend-dependent, pagamentos, SSE, webhooks Stripe

## Root Cause

Railway platform mudou comportamento entre 2026-04-23T02:12Z e 2026-04-23T12:34Z. Nos deploys pós-mudança, o campo `rootDirectory` é setado para `/backend` (leading slash) inferido do `configFile: /backend/railway.toml`, mas o Railpack builder rejeita com:

```json
{
  "configErrors": ["Could not find root directory: /backend"]
}
```

O deploy REMOVED do #489 (99d99db8, 02:12Z) tinha metadata idêntica (`"rootDirectory": "/backend"`) e **funcionou** — build completou, imageDigest presente. Após ~10h gap, o mesmo config falha.

**Env var `RAILWAY_SERVICE_ROOT_DIRECTORY=backend`** (sem slash) está correta mas Railway parece ignorá-la em favor do inferred path com slash.

## 4 Deploys Failed Timeline

| Deploy ID | Timestamp | Commit | Trigger | Status |
|-----------|-----------|--------|---------|--------|
| `511afefb` | 12:34:19Z | c817ada (merge #487) | GitHub push | FAILED configError |
| `13fc89a6` | 12:34:44Z | 44290fd (merge #479) | GitHub push | FAILED configError |
| `ce6a758d` | 12:34:55Z | 44290fd | CI retry | FAILED configError |
| `6735f941` | 12:34:56Z | — | `railway up` fallback | FAILED configError (via RAILPACK) |

`apply-migrations` job SKIP (deploy-backend falhou → chain break) → migration do PR #470 (`add_api_status_to_health_checks`) **continua unapplied** em prod (correlacionado com STORY-DEBT-CI-migration-dessync).

## Fix Sugerido (aguardando user)

Via Railway Dashboard:
1. https://railway.app → projeto `bidiq-uniformes` → service `bidiq-backend`
2. Settings → Source → **Root Directory**
3. Limpar o campo OU mudar `/backend` → `backend` (sem leading slash)
4. Salvar → Railway triggera novo deploy automaticamente

Alternativa via CLI (menos recomendada — MCP Railway tool não expõe rootDirectory):
- Remover o campo inteiro e deixar Railway usar `railway.toml` from `backend/`
- Ou criar `railway.toml` na raiz do repo com `[service] rootDirectory = "backend"`

## Critérios de Aceite

- [ ] **AC1:** Railway service `bidiq-backend` setting "Root Directory" = `backend` (sem slash) OU vazio
- [ ] **AC2:** Próximo deploy (auto-triggered pelo save) retorna `status: SUCCESS` com `imageDigest` set
- [ ] **AC3:** `curl -sf https://api.smartlic.tech/health` retorna HTTP 200 JSON `{"status":"healthy"...}`
- [ ] **AC4:** Deploy cascade: re-trigger `Deploy to Production` workflow do último commit main (c817ada ou 44290fd) → verde
- [ ] **AC5:** `apply-migrations` roda e aplica `20260422120000_add_api_status_to_health_checks` em Supabase prod (checar `supabase migration list --linked` pós-deploy)
- [ ] **AC6:** Slack Deploy Notification = green após fix

## Riscos Pós-Fix

- **R1 (Médio):** Se Railway salvar campo vazio, pode tentar buildar da raiz do repo (sem `Dockerfile`) → novo erro. Testar primeiro com `backend` (sem slash) antes de limpar.
- **R2 (Baixo):** Migration `20260422120000` vai aplicar automaticamente pós-deploy-success (já tem `IF NOT EXISTS` idempotent); bate com STORY-DEBT-CI-migration-dessync que tem fix timeline separado.

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-23 | temporal-dongarra session | Story criada com diagnóstico completo via mcp Railway list-deployments; user iniciando fix manual dashboard |
