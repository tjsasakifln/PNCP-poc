# STORY-TD-001: Verificacao de Producao e Migration 027

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 0: Verificacao e Quick Wins

## Prioridade
P0

## Estimativa
8h

## Descricao

Esta story e o prerequisito absoluto de toda a resolucao de debito tecnico. Abrange tres atividades criticas:

1. **Verificacao do estado real de producao** -- Executar queries V1-V5 no Supabase SQL Editor para entender se o banco foi modificado manualmente fora de migrations (coluna `status` em `user_subscriptions`, default de `plan_type` em `profiles`, trigger de sync).

2. **Correcao dos 4 code paths com `plan_type = 'free'` invalido** -- O CHECK constraint da migration 020 aceita apenas `free_trial`, `consultor_agil`, `maquina`, `sala_guerra`, `master`. Porem, 4 locais no codigo usam `'free'` que viola este constraint:
   - `quota.py` linha 791: `_ensure_profile_exists()` (DB-06, CRITICAL)
   - `quota.py` linha 522: fallback `get("plan_type", "free")` (DB-16, LOW)
   - Migration 001: column default `'free'::text` (DB-02, CRITICAL)
   - `admin.py` linha 246: `CreateUserRequest` default (DB-15, MEDIUM)

3. **Migration 027** -- Corrigir column default de `profiles.plan_type`, recriar `handle_new_user()` com `plan_type = 'free_trial'`, e fechar vulnerabilidades RLS em `pipeline_items` e `search_results_cache`:
   - `pipeline_items`: RLS `FOR ALL USING(true)` permite cross-user access (DB-03, HIGH/SAFETY)
   - `search_results_cache`: mesmo pattern (DB-04, HIGH/SAFETY)

**Impacto de negocio:** Sem esta correcao, novos usuarios podem nao conseguir se cadastrar corretamente, e dados de clientes podem ser acessados por outros usuarios autenticados. Risco estimado: R$ 150.000+.

## Itens de Debito Relacionados
- DB-02 (CRITICAL): `handle_new_user()` trigger + column default `'free'` viola CHECK
- DB-06 (CRITICAL): `_ensure_profile_exists()` usa `plan_type: "free"` violando CHECK
- DB-03 (HIGH): `pipeline_items` RLS overly permissive -- cross-user access
- DB-04 (HIGH): `search_results_cache` RLS overly permissive -- cross-user access
- DB-15 (MEDIUM): admin.py `CreateUserRequest` default "free"
- DB-16 (LOW): quota.py fallback "free" (mitigado por mapping)

## Criterios de Aceite

### Verificacao de Producao (Dia 1 manha)
- [ ] Query V1 executada: coluna `status` em `user_subscriptions` verificada
- [ ] Query V2 executada: default de `profiles.plan_type` verificado
- [ ] Query V3 executada: distribuicao de `plan_type` verificada
- [ ] Query V4 executada: criacoes recentes validadas
- [ ] Query V5 executada: trigger de sync verificado
- [ ] Resultado documentado em comentario na story

### Backend Code Fixes (Dia 1 tarde)
- [ ] `quota.py` linha ~791: `_ensure_profile_exists()` usa `plan_type = 'free_trial'` (nao `'free'`)
- [ ] `quota.py` linha ~522: fallback `get("plan_type", "free_trial")` (nao `'free'`)
- [ ] `admin.py` linha ~246: `CreateUserRequest` default `'free_trial'` (nao `'free'`)
- [ ] Backend deployed com fixes antes da migration
- [ ] `grep -r "plan_type.*free['\"]" backend/` retorna zero matches de `"free"` sem `_trial`

### Migration 027 (Dia 2 manha)
- [ ] Column default de `profiles.plan_type` alterado para `'free_trial'::text`
- [ ] `handle_new_user()` recriado com `plan_type = 'free_trial'`
- [ ] RLS de `pipeline_items`: policy scoped a `service_role` + policy `user_id = auth.uid()` para authenticated
- [ ] RLS de `search_results_cache`: policy scoped a `service_role` + policy `user_id = auth.uid()` para authenticated
- [ ] Migration aplicada com sucesso via `npx supabase db push`

### Validacao Pos-Deploy (Dia 2 tarde)
- [ ] Query V6 executada: RLS policies verificadas por role
- [ ] Query V7 executada: column default retorna `'free_trial'::text`
- [ ] Query V8 executada: ultimo usuario criado tem `plan_type = 'free_trial'`

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| SEC-T01 | `pipeline_items` NAO permite SELECT cross-user via PostgREST com authenticated key | Integracao SQL | P0 |
| SEC-T02 | `search_results_cache` NAO permite SELECT cross-user | Integracao SQL | P0 |
| SEC-T03 | INSERT em `pipeline_items` com `user_id` de outro usuario FALHA com RLS error | Integracao SQL | P0 |
| REG-T01 | Novo usuario signup: profile com `plan_type = 'free_trial'` | E2E | P0 |
| REG-T02 | `_ensure_profile_exists()` cria profile com `plan_type = 'free_trial'` | Unitario | P0 |
| REG-T04 | Stripe webhooks processam apos correcao de RLS | Integracao | P0 |

## Dependencias
- **Blocks:** STORY-TD-004 (seguranca DB restante depende de resultado das queries V1-V5)
- **Blocks:** STORY-TD-016 (DB improvements dependem de estado pos-migration 027)
- **Blocked by:** Nenhuma -- esta e a primeira story

## Riscos
- **CR-01:** Migration 027 pode falhar se banco foi modificado manualmente fora de migrations
- **CR-03:** Correcao de RLS pode bloquear funcionalidade se backend nao usa service_role key
- **CR-05:** Correcao parcial de plan_type cria inconsistencia pior -- todos os 4 code paths devem ser corrigidos atomicamente

## Rollback Plan

```sql
-- ROLLBACK migration 027 (executar na ordem inversa)

-- 1. Restaurar RLS de search_results_cache (REINTRODUZ DB-04)
DROP POLICY IF EXISTS "Service role full access on search_results_cache"
  ON search_results_cache;
CREATE POLICY "Service role full access on search_results_cache"
  ON search_results_cache FOR ALL
  USING (true) WITH CHECK (true);

-- 2. Restaurar RLS de pipeline_items (REINTRODUZ DB-03)
DROP POLICY IF EXISTS "Service role full access on pipeline_items"
  ON public.pipeline_items;
CREATE POLICY "Service role full access on pipeline_items"
  ON public.pipeline_items FOR ALL
  USING (true) WITH CHECK (true);

-- ATENCAO: NAO reverter column default de plan_type.
-- Manter 'free_trial' pois 'free' viola o CHECK constraint.

-- ATENCAO: NAO reverter handle_new_user() para versao 024.
-- Reintroduziria DB-02.
```

**ALERTA:** Rollback de RLS reintroduz vulnerabilidade cross-user. Usar como ultimo recurso.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + integracao)
- [ ] CI/CD green
- [ ] Documentacao atualizada (resultado das queries V1-V5 documentado)
- [ ] Deploy em producao verificado (queries V6-V8)
- [ ] Zero matches de `plan_type = "free"` (sem `_trial`) no backend
