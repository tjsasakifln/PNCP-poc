# CRIT-050: CI Gate para Migrações Pendentes em Produção

**Epic:** DevOps / Continuous Delivery
**Sprint:** Sprint 5
**Priority:** P2 — MEDIUM
**Story Points:** 3 SP
**Estimate:** 2-3 horas
**Owner:** @devops

---

## Problem

CRIT-039 (Feb 28) e CRIT-045 (Mar 1) tiveram a mesma root cause: migrações comitadas no repo mas não aplicadas ao Supabase de produção. Isso é um padrão recorrente:

1. Dev cria migração em `supabase/migrations/`
2. Code é merged e deployado no Railway
3. Código referencia tabelas/colunas novas
4. Supabase não tem essas tabelas → PGRST205 → CB cascade → incidente

**Frequência:** 2x em 3 dias (Feb 28, Mar 1)

---

## Solução

Criar um CI check que detecta migrações locais não aplicadas em produção ANTES do merge.

---

## Acceptance Criteria

### CI Gate

- [x] **AC1:** Criar GitHub Actions workflow `.github/workflows/migration-gate.yml` que roda em PRs que tocam `supabase/migrations/`
- [x] **AC2:** O workflow deve:
  1. Listar migrações locais em `supabase/migrations/`
  2. Comparar com migrações aplicadas via `supabase migration list --linked`
  3. Se houver pendentes: **WARNING** no PR (não bloqueia, mas chama atenção)
- [x] **AC3:** Adicionar step no deploy workflow que executa `supabase db push --include-all` automaticamente após deploy do backend
- [x] **AC4:** Adicionar step de `NOTIFY pgrst, 'reload schema'` após `db push` para forçar cache refresh

### Post-Deploy Verification

- [x] **AC5:** Após `db push`, verificar que `GET /v1/health` não retorna erros PGRST205 (smoke test)
- [x] **AC6:** Se `db push` falhar, o deploy deve ser marcado como DEGRADED (não rollback, mas alerta)

### Documentação

- [x] **AC7:** Documentar o novo fluxo em CLAUDE.md seção "Git Workflow"

---

## Notas

- `supabase db push` requer `SUPABASE_ACCESS_TOKEN` e `--project-ref`
- O `migration-check.yml` existente já verifica presença de migrações — expandir para verificar aplicação
- Alternativa mais simples: checklist de deploy manual com step obrigatório de `supabase db push`
- Considerar `supabase db push --dry-run` no PR para preview
