# STORY-TD-003: RLS Policy Standardization (8 tabelas auth.role())

**Epic:** Resolucao de Debito Tecnico
**Tier:** 1
**Area:** Database
**Estimativa:** 2h (1.5h codigo + 0.5h testes)
**Prioridade:** P1
**Debt IDs:** H-04, H-05, H-06, M-09, DA-01, DA-02

## Objetivo

Padronizar RLS policies em 8 tabelas que usam `auth.role() = 'service_role'` no USING clause. O padrao correto no Supabase e usar `TO service_role` na policy declaration (mais performante, sem function call por row). Isso elimina um anti-pattern que afeta performance em queries com muitas rows e reduz risco de bypass se `auth.role()` retornar valor inesperado.

**Tabelas afetadas:**
1. `alert_preferences` (H-04)
2. `reconciliation_log` (H-05)
3. `organizations` (H-06)
4. `org_members` (H-06)
5. `classification_feedback` (M-09)
6. `partners` (DA-01)
7. `partner_referrals` (DA-01)
8. `search_results_store` (DA-02)

## Acceptance Criteria

- [x] AC1: Criar migration que para cada uma das 8 tabelas: DROP a policy existente que usa `auth.role()` e CREATE nova policy com `TO service_role`
- [x] AC2: Cada tabela tem policy cobrindo ALL operations (SELECT, INSERT, UPDATE, DELETE) para service_role
- [x] AC3: Tabelas que tambem tem user-facing policies (ex: classification_feedback com auth.uid()) mantem essas intactas
- [ ] AC4: Query de verificacao confirma zero policies com `auth.role()` no schema public:
  ```sql
  SELECT schemaname, tablename, policyname, qual
  FROM pg_policies
  WHERE schemaname = 'public' AND qual LIKE '%auth.role()%';
  ```
  Resultado: 0 rows.
- [ ] AC5: Backend smoke test confirma que operacoes service_role continuam funcionando (health check, cache write, etc.)
- [ ] AC6: Todos 5774+ backend tests passam sem regressao

## Technical Notes

**Pattern de migracao (repetir para cada tabela):**
```sql
-- Drop old policy using auth.role()
DROP POLICY IF EXISTS "service_role_access" ON alert_preferences;

-- Create new policy using TO clause (correct pattern)
CREATE POLICY "service_role_all" ON alert_preferences
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
```

**Importante:** Algumas tabelas podem ter MULTIPLAS policies (service_role + authenticated user). Somente substituir a policy de service_role. Nunca remover policies de `auth.uid()`.

**Verificacao pos-migration:**
```sql
-- Should return 0 rows
SELECT tablename, policyname FROM pg_policies
WHERE schemaname = 'public' AND qual LIKE '%auth.role()%';

-- Should return 8+ rows (one per table)
SELECT tablename, policyname FROM pg_policies
WHERE schemaname = 'public' AND roles @> ARRAY['service_role']::name[];
```

## Dependencies

- TD-001 (FK standardization) deve ser aplicada primeiro — para evitar conflitos de migration ordering
- Pode rodar em paralelo com TD-004 (backend) e TD-005 (frontend)

## Definition of Done
- [x] Migration criada em `supabase/migrations/`
- [ ] Migration aplicada no Supabase Cloud via `supabase db push`
- [ ] Zero policies com `auth.role()` no schema public
- [x] 8 tabelas com policies `TO service_role`
- [x] User-facing policies inalteradas
- [x] All backend tests passing
- [x] No regressions
- [ ] Reviewed by @data-engineer
