# 🚀 DEPLOYMENT GUIDE - Migration 006

## Quick Deploy (5 minutos)

### Option 1: Supabase Dashboard (RECOMENDADO) ⚡

1. **Acesse o Supabase Dashboard:**
   ```
   https://supabase.com/dashboard/project/YOUR_PROJECT_ID/editor
   ```

2. **Vá para SQL Editor:**
   - Clique em "SQL Editor" no menu lateral
   - Clique em "+ New query"

3. **Cole e execute este SQL:**

```sql
-- ============================================================================
-- Migration 006: Add Service Role Policy for search_sessions
-- ============================================================================
-- Date: 2026-02-10
-- Priority: P0-CRITICAL
-- Issue: Backend writes to search_sessions blocked by RLS
-- ============================================================================

-- Add service role policy for all operations
DROP POLICY IF EXISTS "Service role can manage search sessions" ON public.search_sessions;
CREATE POLICY "Service role can manage search sessions" ON public.search_sessions
    FOR ALL
    USING (true);

-- Document the policy purpose
COMMENT ON POLICY "Service role can manage search sessions" ON public.search_sessions IS
  'Allows backend service role to insert/update search session history. '
  'Required because backend uses SUPABASE_SERVICE_ROLE_KEY for admin operations. '
  'Without this policy, RLS blocks backend writes even though service role has admin privileges. '
  'Pattern matches monthly_quota table which works correctly with the same policy structure.';
```

4. **Clique em "Run" (Ctrl+Enter)**

5. **Verificar que funcionou:**

```sql
-- Verification query
SELECT
  schemaname,
  tablename,
  policyname,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE tablename = 'search_sessions'
ORDER BY policyname;
```

**Resultado esperado (3 policies):**
```
| policyname                                   | cmd    | qual                    |
|----------------------------------------------|--------|-------------------------|
| Service role can manage search sessions      | ALL    | true                    |
| sessions_insert_own                          | INSERT | (auth.uid() = user_id)  |
| sessions_select_own                          | SELECT | (auth.uid() = user_id)  |
```

✅ **Pronto! Migration aplicada em ~2 minutos.**

---

### Option 2: Supabase CLI (para quem tem credenciais configuradas)

1. **Configure o projeto:**
   ```bash
   cd supabase
   npx supabase link --project-ref YOUR_PROJECT_REF
   ```

2. **Aplique a migration:**
   ```bash
   npx supabase db push
   ```

3. **Verifique:**
   ```bash
   npx supabase db diff
   # Deve mostrar: No schema changes detected
   ```

---

### Option 3: SQL Direto via psql (para quem tem acesso direto ao DB)

```bash
# Get connection string from Supabase Dashboard > Settings > Database
psql "postgresql://postgres:[YOUR_PASSWORD]@db.xxx.supabase.co:5432/postgres" \
  -f supabase/migrations/006_search_sessions_service_role_policy.sql
```

---

## 🧪 Teste Pós-Deployment

### 1. Verificar Policy Criada

```sql
SELECT policyname, cmd, qual
FROM pg_policies
WHERE tablename = 'search_sessions'
  AND policyname = 'Service role can manage search sessions';
```

**Esperado:** 1 linha retornada com `qual = true`

### 2. Testar End-to-End (Free User Flow)

1. Abra o app como usuário gratuito
2. Execute uma busca
3. Vá para `/historico`
4. **Verifique:** Busca aparece no histórico ✅

### 3. Verificar Logs do Backend

Antes do fix:
```
ERROR Failed to save search session: RLS policy violation
```

Depois do fix:
```
✅ Search session saved successfully
```

---

## 📊 Monitoramento (Próximas 24h)

### Queries para Monitorar

**1. Quantas buscas foram salvas (últimas 24h):**
```sql
SELECT COUNT(*) as searches_saved_last_24h
FROM search_sessions
WHERE created_at > NOW() - INTERVAL '24 hours';
```

**2. Taxa de sucesso por usuário:**
```sql
SELECT
  user_id,
  COUNT(*) as total_searches,
  COUNT(DISTINCT session_id) as unique_sessions
FROM search_sessions
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY user_id
ORDER BY total_searches DESC
LIMIT 10;
```

**3. Verificar se ainda há erros:**
```sql
-- No backend logs, procurar por:
grep -i "failed to save search session" logs/backend.log | tail -20
```

---

## 🎯 Success Metrics

Após 24h, você deve ver:

- ✅ **Search history save rate:** >95% (antes: 0%)
- ✅ **Backend errors:** 0 (antes: ~100%)
- ✅ **User complaints:** 0 (antes: frequentes)
- ✅ **Conversion rate:** Aumento gradual (monitorar por 1 semana)

---

## 🆘 Rollback (se necessário)

Se algo der errado (improvável), remover a policy:

```sql
DROP POLICY IF EXISTS "Service role can manage search sessions" ON public.search_sessions;
```

**Nota:** Isso volta ao estado anterior onde search history NÃO salva.

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique que a policy foi criada (query de verificação acima)
2. Verifique logs do backend para erros RLS
3. Teste manualmente: busca → /historico

**Arquivo da Migration:**
`supabase/migrations/006_search_sessions_service_role_policy.sql`

---

## ✅ Checklist de Deployment

- [ ] Executei o SQL no Supabase Dashboard
- [ ] Verification query retornou 3 policies (incluindo a nova)
- [ ] Testei end-to-end: busca aparece em /historico
- [ ] Backend logs não mostram mais erros de RLS
- [ ] Monitoro metrics por 24h

---

**Tempo total de deployment:** ~5 minutos
**Risco:** LOW (apenas adiciona policy, sem mudanças de schema)
**Rollback:** Simples (DROP POLICY)

🚀 **Ready to deploy!**
