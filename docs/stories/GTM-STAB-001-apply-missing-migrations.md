# GTM-STAB-001 — Aplicar Migrations Pendentes em Produção

**Status:** To Do
**Priority:** P0 — Blocker (sistema não funciona sem isso)
**Severity:** Infra — coluna inexistente causa FATAL em cada startup
**Created:** 2026-02-24
**Sprint:** GTM Stabilization (imediato)
**Relates to:** GTM-ARCH-002 (cache global cross-user), CRIT-001 (schema validation)
**Sentry:** CRIT-001 (20 events, ESCALATING, FATAL), APIError FK constraint (11 events)

---

## Problema

Duas falhas críticas no banco de produção impedem o funcionamento correto do cache:

### 1. Coluna `params_hash_global` inexistente

A migration `20260223100000_add_params_hash_global.sql` existe no repositório mas **nunca foi aplicada em produção**. Consequências:

- **Startup FATAL** — A cada restart/deploy, `_check_cache_schema()` em `main.py:234` detecta coluna faltando e emite log CRITICAL para Sentry (20 ocorrências, escalating)
- **Cache write falha** — `_save_to_supabase()` em `search_cache.py:196` tenta inserir `params_hash_global` → PostgREST rejeita coluna desconhecida → APIError
- **Cache global quebrado** — `_get_global_fallback_from_supabase()` em `search_cache.py:299` faz `.eq("params_hash_global", ...)` em coluna inexistente → erro
- **Cascata**: sem cache → toda busca vai pro PNCP/PCP → lento → timeout → 524

### 2. Foreign Key constraint `search_results_cache_user_id_fkey`

O Sentry mostra 11 eventos de `APIError: insert or update on table "search_results_cache" violates foreign key constraint "search_results_cache_user_id_fkey"`. A tabela referencia `auth.users(id)` (migration 026), mas:

- Usuários criados via signup podem ter delay na propagação auth.users → profiles
- Background cache refresh (cron_jobs) pode usar user_ids de sessões expiradas
- A migration 018 padronizou FKs para profiles em OUTRAS tabelas, mas search_results_cache ficou apontando para auth.users

### Impacto

- **100% dos deploys** geram FATAL no Sentry
- **Cache não funciona** → cada busca é uma chamada fresh ao PNCP
- **Tempo de resposta 3-10x maior** sem cache
- Cascata direta para WORKER TIMEOUT e 524

---

## Acceptance Criteria

### AC1: Aplicar migration params_hash_global
- [ ] Executar `20260223100000_add_params_hash_global.sql` no Supabase de produção
- [ ] Verificar que coluna existe: `SELECT column_name FROM information_schema.columns WHERE table_name = 'search_results_cache' AND column_name = 'params_hash_global'`
- [ ] Após deploy, Sentry NÃO deve mais registrar `CRIT-001: MISSING columns`

### AC2: Fix foreign key constraint
- [ ] Criar migration para alterar FK de `auth.users(id)` para `profiles(id)` (padrão do projeto, conforme migration 018)
- [ ] Migration deve ser idempotente (IF EXISTS / IF NOT EXISTS)
- [ ] Backfill: verificar que todos user_ids existentes têm correspondência em profiles

### AC3: Validar cache funcional pós-migration
- [ ] Fazer uma busca real (setor=vestuario, UFs=[SP], 10 dias)
- [ ] Verificar no Supabase que row foi criada em search_results_cache com params_hash_global preenchido
- [ ] Fazer mesma busca novamente → deve retornar do cache (verificar log "cache hit")
- [ ] Fazer mesma busca com outro usuário → global fallback deve funcionar

### AC4: Resolver issue APIError no Sentry
- [ ] Após AC1+AC2, monitorar Sentry por 1h
- [ ] CRIT-001 deve ter 0 novos eventos
- [ ] APIError FK constraint deve ter 0 novos eventos
- [ ] Resolver ambos issues no Sentry como "fixed"

### AC5: Prevenir reincidência
- [ ] Adicionar step no CI/CD que verifica se todas migrations locais foram aplicadas em produção
- [ ] OU adicionar warning no `railway up` pre-deploy hook
- [ ] Documentar processo de migration no CLAUDE.md se ainda não estiver

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `supabase/migrations/20260223100000_add_params_hash_global.sql` | Aplicar em produção |
| Nova migration: `20260224_fix_cache_user_fk.sql` | Criar — alterar FK para profiles |
| `backend/main.py:197-250` | Verificar que _check_cache_schema() passa |
| `backend/search_cache.py:180-229` | Verificar que _save_to_supabase() funciona |
| `backend/search_cache.py:284-303` | Verificar que global fallback funciona |

---

## Execução

```bash
# 1. Aplicar migration via Supabase CLI
export SUPABASE_ACCESS_TOKEN=$(grep SUPABASE_ACCESS_TOKEN .env | cut -d '=' -f2)
npx supabase db push

# 2. Verificar
npx supabase db diff

# 3. Redeploy backend para que _check_cache_schema() valide
railway up
```

## Estimativa
- **Esforço:** 1-2h (maioria é execução + validação)
- **Risco:** Baixo (migrations são idempotentes, IF NOT EXISTS)
- **Squad:** @devops (execução) + @qa (validação)
