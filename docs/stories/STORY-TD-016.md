# STORY-TD-016: DB Improvements -- FK, Analytics, Triggers

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 2: Consolidacao e Refatoracao

## Prioridade
P2

## Estimativa
16h

## Descricao

Esta story resolve melhorias de banco de dados de media prioridade que melhoram consistencia, performance e manutencao.

1. **FK standardization (DB-07, MEDIUM, 2h)** -- `pipeline_items` e `search_results_cache` usam FK para `auth.users` em vez de `profiles`, regressao do padrao estabelecido na migration 018. Embora funcionalmente benigno (1:1 com ON DELETE CASCADE), cria inconsistencia no schema. Corrigir para usar FK -> `profiles.id`.

2. **Analytics date filter + top-dimensions RPC (DB-09 + DB-17, MEDIUM, 10h combinados)** -- Dois endpoints de analytics carregam dados sem filtragem adequada:
   - `time-series` (DB-09): filtra por `range_days` mas `top-dimensions` (linhas 206-245) carrega TODAS as sessions sem date filter.
   - `top-dimensions` (DB-17): fetch sem limite temporal, cresce linearmente com sessoes.
   Criar RPCs otimizadas com date filter e limit. Meta: < 2s (P95) para usuario com 500+ sessions.

3. **Consolidacao trigger handle_new_user() (DB-11, MEDIUM, 3h)** -- Trigger redefinido 4 vezes (migrations 001, 007, 016, 024). Versao 024 omitiu `plan_type = 'free_trial'`. Versao 027 (de TD-001) corrigiu. Consolidar em versao definitiva com documentacao da evolucao. Depende de DB-02 estar estavel (TD-001 concluida).

4. **Consolidar funcao duplicada (DB-13, LOW, 0.5h)** -- `pipeline_items` usa `update_pipeline_updated_at()` separada em vez do compartilhado `update_updated_at()`. Consolidar.

5. **quota.py fallback fix (DB-16, LOW, 0.25h)** -- `quota.py` linha 522 tem fallback `get("plan_type", "free")` que retorna valor invalido. PLAN_TYPE_MAP em L529 mitiga, mas fragil. Mudar default para `"free_trial"`.

## Itens de Debito Relacionados
- DB-07 (MEDIUM): FK para `auth.users` em vez de `profiles` em pipeline_items e cache
- DB-09 (MEDIUM): `search_sessions` time-series carrega todas as rows
- DB-17 (MEDIUM): `top-dimensions` sem date filter
- DB-11 (MEDIUM): `handle_new_user()` trigger redefinido 4 vezes
- DB-13 (LOW): `update_pipeline_updated_at()` funcao duplicada
- DB-16 (LOW): quota.py fallback "free" -> "free_trial"

## Criterios de Aceite

### FK Standardization
- [ ] `pipeline_items` FK referencia `profiles.id` (nao `auth.users.id`)
- [ ] `search_results_cache` FK referencia `profiles.id`
- [ ] ON DELETE CASCADE preservado
- [ ] Dados existentes nao afetados pela migracao

### Analytics Optimization
- [ ] `top-dimensions` endpoint aceita parametro de date range
- [ ] Query usa date filter (nao carrega todas as sessions)
- [ ] RPC otimizada com limit
- [ ] Pagina de analytics carrega em < 2s para usuario com 500+ sessions (P95)
- [ ] `time-series` e `top-dimensions` combinados em endpoint eficiente

### Trigger Consolidation
- [ ] `handle_new_user()` tem versao unica e documentada
- [ ] Evolucao do trigger documentada (001 -> 007 -> 016 -> 024 -> 027 -> consolidada)
- [ ] Versao consolidada inclui `plan_type = 'free_trial'`
- [ ] Signup funciona corretamente com trigger consolidado

### Cleanup
- [ ] `update_pipeline_updated_at()` removida; usa `update_updated_at()` compartilhada
- [ ] `quota.py` fallback usa `"free_trial"` (nao `"free"`)

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| PERF-T01 | Analytics page load, usuario 500+ sessions < 2s (P95) | Load test | P2 |
| REG-T01 | Signup funciona com trigger consolidado | E2E | P2 |
| -- | FK constraints validas apos migracao | SQL verify | P2 |

## Dependencias
- **Blocks:** Nenhuma
- **Blocked by:** STORY-TD-001 (migration 027 e correcao de DB-02 devem estar estaveis)

## Riscos
- **CR-06:** Consolidacao de trigger pode conflitar com extensoes. Fazer APOS signup validado.
- FK migration pode falhar se existirem orphan records. Verificar antes.
- Analytics RPC precisa ser testada com volume real de dados.

## Rollback Plan
- FK migration reversivel (ALTER CONSTRAINT de volta para auth.users)
- Analytics: manter endpoint original como fallback se RPC causar problemas
- Trigger: manter versao 027 se consolidacao causar regressao

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + integracao + load test)
- [ ] CI/CD green
- [ ] Migration aplicada com sucesso
- [ ] Documentacao de trigger atualizada
- [ ] Deploy em staging verificado
- [ ] Analytics page testada com dados reais
