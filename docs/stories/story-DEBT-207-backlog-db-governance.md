# Story DEBT-207: Backlog Oportunistico — Database Governance e Naming

## Metadados
- **Epic:** EPIC-DEBT-V2
- **Sprint:** Backlog (resolver durante feature work)
- **Prioridade:** P3 (Baixa)
- **Esforco:** 16.5h
- **Agente:** @data-engineer
- **Status:** DONE

## Descricao

Como equipe de banco de dados, queremos padronizar nomenclatura de triggers e policies RLS, documentar onboarding de Stripe seed, e resolver inconsistencias de documentacao, para que novos desenvolvedores encontrem um schema consistente e autoexplicativo.

## Debitos Incluidos

| ID | Debito | Horas | Trigger para Resolver |
|----|--------|-------|-----------------------|
| DEBT-DB-003 | Trigger prefix inconsistente (tr_/trg_/trigger_) | 2h | Quando tocar nas tabelas afetadas |
| DEBT-DB-004 | RLS policy naming inconsistente (~60+ policies) | 3h | Durante auditoria de seguranca |
| DEBT-DB-005 | Stripe price IDs hardcoded — doc de onboarding faltante | 2h | Quando onboarding novo dev |
| DEBT-DB-006 | Soft/hard delete semantica inconsistente em pncp_raw_bids | 1h | Junto com DB-NEW-001 (ja resolvido no Sprint 1) |
| DEBT-DB-007 | health_checks sem policy admin (parcial — resolvido no Sprint 1 se nao 100%) | 1h | Se Sprint 1 nao cobrir 100% |
| DEBT-DB-NEW-001 | COMMENT incorreto pncp_raw_bids.is_active (parcial) | 0.5h | Se Sprint 1 nao cobrir 100% |
| DEBT-DB-NEW-002 | FK checkpoint nao enforced — risco de orfaos | 1h | Quando ingestion escalar |

**Nota:** DEBT-DB-007 e DB-NEW-001 podem ter sido parcialmente resolvidos no Sprint 1 (DEBT-200). Incluidos aqui para garantir cobertura completa.

## Criterios de Aceite

### Nomenclatura de Triggers (2h)
- [x] Todos os triggers padronizados com prefixo `trg_` (ex: `trg_update_timestamp`)
- [x] Migration de rename criada (nao drop + recreate — preservar logica)
- [x] Nenhum trigger com prefixo `tr_` ou `trigger_` restante

### RLS Policy Naming (3h)
- [x] Convencao definida: `{action}_{table}_{role}` (ex: `select_profiles_owner`, `insert_pipeline_items_authenticated`)
- [x] Policies existentes renomeadas via migration
- [x] Documentacao da convencao em `supabase/docs/CONVENTIONS.md`

### Stripe Seed Documentation (2h)
- [x] `supabase/docs/STRIPE-SEED.md` criado com instrucoes de onboarding
- [x] Seed script existente documentado (como rodar, pre-requisitos)
- [x] Price IDs hardcoded mapeados para nomes legiveis

### Semantica Soft/Hard Delete (1h)
- [x] Documentacao atualizada para refletir comportamento real (purge = hard delete)
- [x] COMMENTs de colunas corrigidos se necessario

### FK Checkpoint (1h)
- [x] Decidir: enforced FK ou monitoring de orfaos via cron
- [x] Se FK: migration criada
- [x] Se monitoring: query de deteccao de orfaos criada como cron job

## Testes Requeridos

- [x] Verificar que triggers renomeados disparam corretamente
- [x] Verificar que RLS policies renomeadas manteem mesmo comportamento
- [x] `pytest --timeout=30 -q` apos cada migration aplicada

## Notas Tecnicas

- **Nao justifica sprint dedicado.** Resolver oportunisticamente quando trabalhar nas tabelas/areas afetadas.
- **RLS rename:** PostgreSQL suporta `ALTER POLICY ... RENAME TO ...` — nao precisa drop + recreate.
- **Trigger rename:** Requer drop + recreate trigger com novo nome (PostgreSQL nao suporta ALTER TRIGGER RENAME em todas as versoes).

## Dependencias

- DEBT-200 (Sprint 1) parcialmente resolve DB-007 e DB-NEW-001
- Sem dependencia de outras stories — pode ser feito a qualquer momento
