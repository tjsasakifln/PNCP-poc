# STORY-TD-002: RLS + Trigger Cleanup + Accessibility + Branding

**Epic:** Resolucao de Debito Tecnico
**Tier:** 0
**Area:** Database / Frontend / Backend
**Estimativa:** 7.5h (5.5h codigo + 2h testes)
**Prioridade:** P0
**Debt IDs:** C-02, H-01, FE-12, FE-13, FE-07, FE-24, TD-P03, TD-P04

## Objetivo

Story combinada de quick wins que nao requerem refatoracao profunda. Resolve: (1) tabelas sem RLS policies explicitas, (2) trigger functions duplicadas, (3) acessibilidade critica no sidebar, (4) branding residual "BidIQ", e (5) consolidacao de constantes.

## Acceptance Criteria

### Database: RLS Policies (C-02) — 1h
- [ ] AC1: Adicionar RLS policies explicitas para `health_checks` (SELECT/INSERT/UPDATE/DELETE para service_role)
- [ ] AC2: Adicionar RLS policies explicitas para `incidents` (SELECT/INSERT/UPDATE/DELETE para service_role)
- [ ] AC3: Verificar que nenhuma tabela no schema public tem RLS habilitado sem policies (`SELECT tablename FROM pg_tables WHERE schemaname='public'` cross-ref com `pg_policies`)

### Database: Trigger Consolidation (H-01) — 2h
- [ ] AC4: Identificar as 3 trigger functions `updated_at` duplicadas (nomes e tabelas)
- [ ] AC5: Consolidar em uma unica function `set_updated_at()` reutilizada por todos os triggers
- [ ] AC6: Migration DROP das functions duplicadas + CREATE OR REPLACE da consolidada
- [ ] AC7: Verificar que todos triggers `updated_at` funcionam apos consolidacao (UPDATE em cada tabela e checar timestamp)

### Frontend: Accessibility (FE-12 + FE-13) — 2h
- [ ] AC8: Adicionar `aria-label` em todos os botoes icon-only do Sidebar (minimo: toggle, navigation items sem texto visivel)
- [ ] AC9: Adicionar `aria-hidden="true"` em todos SVGs decorativos do Sidebar
- [ ] AC10: Axe DevTools audit do Sidebar retorna zero violations de acessibilidade
- [ ] AC11: Testes unitarios verificam presenca de aria-labels nos botoes icon-only

### Frontend: SVG Cleanup (FE-07) — 1.5h
- [ ] AC12: Substituir SVGs inline no Sidebar (~75 linhas) por icones do `lucide-react`
- [ ] AC13: Manter visual identico (tamanho, cor, posicionamento)
- [ ] AC14: Verificar que `lucide-react` ja esta no `package.json` (ou adicionar se necessario)

### Frontend: APP_NAME Consolidation (FE-24) — 0.5h
- [ ] AC15: Criar constante `APP_NAME = "SmartLic"` em `lib/constants.ts` (ou arquivo similar existente)
- [ ] AC16: Substituir todas 5+ redeclaracoes de APP_NAME nos arquivos por import da constante
- [ ] AC17: Grep confirma zero declaracoes locais de `APP_NAME` fora de `lib/constants`

### Backend: Branding Cleanup (TD-P03 + TD-P04) — 0.5h
- [ ] AC18: Alterar User-Agent header de "BidIQ" para "SmartLic" em todos HTTP clients (`pncp_client.py`, `portal_compras_client.py`, `compras_gov_client.py`)
- [ ] AC19: Atualizar `pyproject.toml` name de "bidiq-uniformes-backend" para "smartlic-backend"
- [ ] AC20: Grep confirma zero ocorrencias de "BidIQ" em User-Agent strings no backend

## Technical Notes

**RLS policy pattern para service_role-only tables:**
```sql
ALTER TABLE health_checks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all" ON health_checks
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
```

**Trigger consolidation pattern:**
```sql
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Then for each table:
DROP TRIGGER IF EXISTS set_updated_at ON table_name;
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON table_name
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
```

**lucide-react icons:** Verificar mapeamento 1:1 com SVGs atuais. Icones comuns: `Menu`, `X`, `ChevronLeft`, `ChevronRight`, `Home`, `Search`, `Settings`, `User`, `BarChart3`, `Kanban`, `History`, `MessageSquare`, `HelpCircle`.

## Dependencies

- Nenhuma — independente de TD-001
- Pode ser executada em paralelo com TD-001

## Definition of Done
- [ ] Migration(s) criada(s) em `supabase/migrations/`
- [ ] Migration(s) aplicada(s) no Supabase Cloud
- [ ] Zero tabelas com RLS habilitado sem policies
- [ ] Uma unica function `set_updated_at()` no schema
- [ ] Axe audit do Sidebar passa sem violations
- [ ] Zero "BidIQ" em User-Agent strings
- [ ] All 5774+ backend tests passing
- [ ] All 2681+ frontend tests passing
- [ ] No regressions
- [ ] Reviewed by @data-engineer (DB parts) and @ux-design-expert (FE parts)
