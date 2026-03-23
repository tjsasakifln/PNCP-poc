# CRIT-080: Restauração Imediata do Deploy Pipeline + Deploy Manual

**Status:** Draft
**Priority:** P0 — BLOCKER (sistema inoperante em produção)
**Epic:** Infraestrutura Crítica
**Agent:** @devops

---

## Contexto

O sistema SmartLic está **completamente inoperante** em produção desde ~22/03/2026. TODOS os requests POST retornam 502 (SIGSEGV) porque:

1. **5 commits de fix** existem em `origin/main` (223997ed → 7d41fbc8) que corrigem o SIGSEGV
2. **NENHUM foi deployado** porque GitHub Actions está com billing pendente/limite excedido
3. A versão em produção (`ccdaf5b`) ainda tem Sentry tracing habilitado + jemalloc LD_PRELOAD → crash em POST

**Mensagem do GitHub Actions:**
> "The job was not started because recent account payments have failed or your spending limit needs to be increased."

## Causa Raiz

Triple interaction fork-unsafe:
- `jemalloc LD_PRELOAD` intercepta `malloc()` do OpenSSL
- `cryptography>=46` com Python 3.12 usa OpenSSL interno
- Sentry `StarletteIntegration._sentry_receive` hook no ASGI lifecycle

GET requests funcionam (sem auth/TLS). POST requests crasham com SIGSEGV (auth → Supabase JWT → TLS handshake).

## Acceptance Criteria

### Fase 1: Deploy Imediato (< 30 min)

- [ ] **AC1**: Deploy manual via `railway up --service bidiq-backend` a partir do diretório `backend/` com o código atual de `main` (que já tem os fixes 223997ed, 93d7cf52, 7d41fbc8)
- [ ] **AC2**: Validar que `POST /v1/buscar` retorna 200/202 (não 502) com curl autenticado
- [ ] **AC3**: Validar que `POST /debug/post-test` retorna 200 (endpoint de diagnóstico)
- [ ] **AC4**: Validar que `/health` retorna status `healthy` com versão >= `223997ed`
- [ ] **AC5**: Executar busca real via https://smartlic.tech com usuário logado — resultados aparecem

### Fase 2: Restaurar CI/CD (< 2h)

- [ ] **AC6**: Resolver billing do GitHub Actions (verificar Settings > Billing & plans > Actions)
- [ ] **AC7**: Confirmar que TODOS os workflows voltaram a funcionar (rodar `gh workflow run deploy.yml`)
- [ ] **AC8**: Ampliar `paths:` filter em `deploy.yml` para incluir arquivos de infra:
  ```yaml
  paths:
    - 'backend/**'
    - 'frontend/**'
    - '.github/workflows/deploy.yml'
    - 'railway.toml'
  ```

### Fase 3: Prevenir Recorrência

- [ ] **AC9**: Adicionar health check de POST no smoke test do deploy (não apenas GET `/health`):
  ```bash
  curl -f -X POST https://api.smartlic.tech/debug/post-test
  ```
- [ ] **AC10**: Criar alerta automático quando GitHub Actions billing falha (webhook ou cron check):
  ```bash
  gh api /repos/{owner}/{repo}/actions/runs --jq '.workflow_runs[:1] | .[].conclusion'
  ```
- [ ] **AC11**: Documentar em CLAUDE.md: "Se deploy falha silenciosamente, verificar GitHub Actions billing PRIMEIRO"

## Verificação de Sucesso

```bash
# Deve retornar 200/202, NÃO 502
curl -s -X POST https://api.smartlic.tech/debug/post-test | jq .status
# Deve retornar versão >= 223997ed
curl -s https://api.smartlic.tech/health | jq .version
```

## Impacto

- **Sem este fix:** Sistema 100% inoperante para todos os usuários
- **Com este fix:** Sistema volta a funcionar imediatamente

## Notas Técnicas

- O `railway up` bypassa GitHub Actions e deploya diretamente
- Railway auto-deploy do GitHub pode estar desconectado — verificar também Railway > Settings > Deploy triggers
- O endpoint `POST /debug/post-test` pode ser removido após validação (commit 2aa91b35)
