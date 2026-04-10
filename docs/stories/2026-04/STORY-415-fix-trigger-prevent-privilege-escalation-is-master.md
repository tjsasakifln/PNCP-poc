# STORY-415: Fix Trigger `prevent_privilege_escalation` referenciando `is_master` inexistente

**Priority:** P0 — Blocks Stripe Reconciliation
**Effort:** S (0.5 day)
**Squad:** @data-engineer
**Status:** Draft
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issue:** https://confenge.sentry.io/issues/7388075442/ (6+ eventos)
**Sprint:** Emergencial (0-48h)

---

## Contexto

O trigger `prevent_privilege_escalation()` definido em `supabase/migrations/20260404000000_security_hardening_rpc_rls.sql:269-305` referencia `NEW.is_master` no body:

```sql
CREATE OR REPLACE FUNCTION prevent_privilege_escalation()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE v_role TEXT;
BEGIN
    IF (NEW.is_admin IS DISTINCT FROM OLD.is_admin) OR
       (NEW.is_master IS DISTINCT FROM OLD.is_master) OR  -- <-- aqui
       (NEW.plan_type IS DISTINCT FROM OLD.plan_type) THEN
        -- ... validation ...
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER protect_profiles_escalation
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION prevent_privilege_escalation();
```

**Problema:** a coluna `is_master` **não existe** em `profiles` (ou foi removida em migration posterior). Toda UPDATE em `profiles` falha com:

```
APIError: record "new" has no field "is_master" (code 42703)
```

**Endpoints afetados:**
- `backend/services/stripe_reconciliation.py` — reconcile_subscriptions cron
- `backend/admin.py:358` — `assign_plan()` (admin UI)
- Qualquer código que faz UPDATE em `profiles`

**Sentry:** 6+ eventos, incluindo "Failed to assign plan smartlic_pro to user a18e0a77-..."

**Quando quebrou:** Migration `20260404000000` foi criada em 04/04/2026 (6 dias atrás). Ou a coluna `is_master` foi removida depois, ou nunca existiu e a migration foi escrita assumindo incorretamente.

---

## Acceptance Criteria

### AC1: Decisão de fix (investigar primeiro)
- [ ] Confirmar se `profiles.is_master` existe via `psql` ou Supabase dashboard — se não existe, confirmar decisão via `git log -p supabase/migrations/ | grep -i "is_master"`
- [ ] Consultar feature owner: a funcionalidade `is_master` ainda é necessária? Ver `backend/auth.py`, `backend/authorization.py`, `routes/admin.py` para uso
- [ ] **Opção A:** Adicionar coluna `is_master BOOLEAN DEFAULT FALSE` em `profiles` (se feature ainda ativa)
- [ ] **Opção B:** Remover referência a `NEW.is_master` do trigger (se feature descontinuada)
- [ ] Documentar decisão no Dev Notes

### AC2: Migration de correção
- [ ] Criar `supabase/migrations/2026041001_fix_is_master_trigger.sql`
- [ ] **Se Opção A:**
  ```sql
  ALTER TABLE profiles ADD COLUMN IF NOT EXISTS is_master BOOLEAN NOT NULL DEFAULT FALSE;
  -- Trigger já deve funcionar após isso
  ```
- [ ] **Se Opção B:**
  ```sql
  CREATE OR REPLACE FUNCTION prevent_privilege_escalation()
  RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER
  AS $$
  BEGIN
      IF (NEW.is_admin IS DISTINCT FROM OLD.is_admin) OR
         (NEW.plan_type IS DISTINCT FROM OLD.plan_type) THEN
          -- ... validation sem is_master ...
      END IF;
      RETURN NEW;
  END;
  $$;
  ```
- [ ] Aplicar via `supabase db push` (após validação em staging)

### AC3: Testes
- [ ] Teste em `backend/tests/test_admin.py` cobrindo `assign_plan()` — mock Supabase retornando `profiles` row e validar UPDATE não dispara erro
- [ ] Teste em `backend/tests/test_stripe_reconciliation.py` cobrindo o flow completo com UPDATE
- [ ] Teste manual via `curl`:
  ```bash
  curl -X POST $PROD_URL/admin/assign_plan \
    -H "Authorization: Bearer $ADMIN_JWT" \
    -d '{"user_id":"...","plan":"smartlic_pro"}'
  ```

### AC4: Validação do trigger
- [ ] Via SQL direto no Supabase:
  ```sql
  UPDATE profiles SET plan_type = plan_type WHERE id = (SELECT id FROM profiles LIMIT 1);
  -- Deve executar sem erro 42703
  ```
- [ ] `SELECT pg_trigger_depth()` durante UPDATE retorna >0 (confirma trigger ativo)

### AC5: Verificação pós-deploy
- [ ] Monitorar Sentry issue 7388075442 por 6h — zero novos eventos
- [ ] Rodar manualmente `stripe_reconciliation` job e validar 0 erros
- [ ] Testar admin `assign_plan` via UI ou API
- [ ] Marcar issue como **Resolved** no Sentry

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `supabase/migrations/2026041001_fix_is_master_trigger.sql` | **Nova migration** (Opção A ou B) |
| `backend/admin.py` | Linha ~358 — possivelmente remover refs a `is_master` se Opção B |
| `backend/services/stripe_reconciliation.py` | Validar que não referencia `is_master` |
| `backend/auth.py` / `backend/authorization.py` | Revisar uso de `is_master` |
| `backend/tests/test_admin.py` | Regression test `assign_plan` |
| `backend/tests/test_stripe_reconciliation.py` | Regression test reconcile flow |

---

## Implementation Notes

- **Feature owner decision:** provavelmente `@pm` ou `@po` precisa decidir se `is_master` role é mantido. Se for funcionalidade de admin super-user, vale manter (Opção A). Se foi descontinuado em favor de `is_admin`, remover (Opção B).
- **Race condition risk:** o trigger é `BEFORE UPDATE FOR EACH ROW` — não há race condition porque é transação single-row.
- **Rollback plan:** se migration quebrar algo, reverter via:
  ```sql
  ALTER TABLE profiles DROP COLUMN IF EXISTS is_master;  -- se Opção A
  -- ou restaurar versão anterior do trigger via migration reversa
  ```
- **Crítico:** como esse trigger está bloqueando `stripe_reconciliation`, há risco de subscriptions com status dessincronizado. Após fix, rodar `python -m backend.services.stripe_reconciliation --force` para reconciliar pendentes.

---

## Dev Notes (preencher durante implementação)

<!-- @data-engineer: documentar decisão feita (A ou B) e razão -->

---

## Verification

1. **Local:** aplicar migration em Supabase staging + UPDATE teste em `profiles` não dispara erro
2. **Staging:** `railway logs --filter "is_master"` = vazio após deploy
3. **Produção:** monitorar Sentry issue 7388075442 por 6h
4. **Funcional:** admin consegue fazer `assign_plan` via UI sem erro; `stripe_reconciliation` cron job completa sem warnings

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-10 | @sm (River) | Story criada a partir do incidente multi-causa |
