# CRIT-014 — Missing Supabase RPC Functions em Produção

**Status:** pending
**Priority:** P0 — Production (498 eventos em 1 semana, analytics completamente quebrado)
**Origem:** Análise Sentry (2026-02-21) — SMARTLIC-BACKEND-2, 3, 4, 5, 1
**Componentes:** supabase/migrations/019, backend/routes/analytics.py, backend/quota.py, backend/routes/messages.py

---

## Contexto

O Sentry mostra **498 eventos** de erros PGRST202 ("Could not find the function") em 1 semana para 3 RPC functions que existem no código mas **nunca foram deployadas** para o Supabase de produção.

O dashboard de analytics está **completamente inoperante** — cada visita gera 3 erros (analytics.py + middleware logging).

## Impacto em Produção

| Function | Endpoint | Eventos/Semana | Status Sentry |
|----------|----------|----------------|---------------|
| `get_analytics_summary()` | `GET /analytics/summary` | **498** (3 issues) | ONGOING |
| `check_and_increment_quota()` | `POST /v1/buscar` | 3 | ONGOING |
| `get_conversations_with_unread_count()` | `GET /v1/api/messages/conversations` | 3 | ONGOING |

### Fallbacks Existentes

- **analytics.py**: Retorna zeros quando RPC falha (linhas 127-137) — dashboard mostra valores zerados
- **quota.py**: Fallback para upsert atômico (linhas 387-390) — quota funciona mas sem atomicidade
- **messages.py**: Retorna lista vazia (linhas 134-135) — conversas não aparecem

## Causa Raiz

As 3 functions estão definidas em migrações que existem no repositório mas **não foram aplicadas** ao Supabase de produção:

| Function | Migração | Status |
|----------|----------|--------|
| `get_analytics_summary` | `supabase/migrations/019_rpc_performance_functions.sql` | **NÃO APLICADA** |
| `get_conversations_with_unread_count` | `supabase/migrations/019_rpc_performance_functions.sql` | **NÃO APLICADA** |
| `check_and_increment_quota` | `supabase/migrations/003_atomic_quota_increment.sql` | Provavelmente aplicada (antiga), verificar |

## Acceptance Criteria

### Deploy de Migrações

- [ ] **AC1:** Verificar status de todas as migrações pendentes: `npx supabase migration list`
- [ ] **AC2:** Aplicar migração 019 (`019_rpc_performance_functions.sql`) que cria `get_analytics_summary` e `get_conversations_with_unread_count`
- [ ] **AC3:** Verificar se migração 003 (`003_atomic_quota_increment.sql`) está aplicada — se não, aplicar
- [ ] **AC4:** Executar `npx supabase db push` para aplicar todas as migrações pendentes

### Validação PostgREST

- [ ] **AC5:** Após aplicar migrações, forçar reload do schema cache: `NOTIFY pgrst, 'reload schema'`
- [ ] **AC6:** Verificar que as functions existem: `SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name IN ('get_analytics_summary', 'get_conversations_with_unread_count', 'check_and_increment_quota')`

### Validação Funcional

- [ ] **AC7:** Testar `GET /analytics/summary` em produção — deve retornar dados reais (não zeros)
- [ ] **AC8:** Testar `GET /v1/api/messages/conversations` — deve retornar conversas existentes
- [ ] **AC9:** Testar busca completa — quota atômica deve funcionar sem fallback

### Monitoramento

- [ ] **AC10:** Monitorar Sentry por 24h — PGRST202 não deve mais aparecer
- [ ] **AC11:** Verificar logs Railway: `railway logs | grep PGRST202` — deve estar limpo
- [ ] **AC12:** Marcar issues SMARTLIC-BACKEND-1, 2, 3, 4, 5 como resolvidos no Sentry

## Procedimento de Deploy

```bash
# 1. Verificar migrações pendentes
export SUPABASE_ACCESS_TOKEN=$(grep SUPABASE_ACCESS_TOKEN .env | cut -d '=' -f2)
npx supabase link --project-ref fqqyovlzdzimiwfofdjk
npx supabase migration list

# 2. Aplicar migrações pendentes
npx supabase db push

# 3. Verificar que functions existem
npx supabase db execute "SELECT routine_name FROM information_schema.routines WHERE routine_schema = 'public' AND routine_name LIKE 'get_%' OR routine_name = 'check_and_increment_quota'"

# 4. Forçar reload do schema cache
npx supabase db execute "NOTIFY pgrst, 'reload schema'"

# 5. Testar endpoints
curl -s https://api.smartlic.tech/analytics/summary -H "Authorization: Bearer $TOKEN" | jq .
```

## Arquivos Relevantes (não requerem mudança de código)

| Arquivo | Papel |
|---------|-------|
| `supabase/migrations/019_rpc_performance_functions.sql` | Define as 2 functions (STORY-202) |
| `supabase/migrations/003_atomic_quota_increment.sql` | Define check_and_increment_quota |
| `backend/routes/analytics.py:74-78` | Chama get_analytics_summary via RPC |
| `backend/routes/messages.py:98-104` | Chama get_conversations_with_unread_count via RPC |
| `backend/quota.py:465-472` | Chama check_and_increment_quota via RPC |

## Referências

- CRIT-013 (Missing search_state_transitions) — mesmo padrão de migração não aplicada
- STORY-202 (Horizontal Scaling) — criou migração 019
- Sentry: SMARTLIC-BACKEND-1, 2, 3, 4, 5

## Definition of Done

- [ ] Todas as migrações pendentes aplicadas em produção
- [ ] Dashboard de analytics retornando dados reais
- [ ] Zero erros PGRST202 no Sentry por 24h
- [ ] Conversas e quota atômica funcionando
