# GTM-INFRA-003: Background Revalidation Multi-Source + Skip Quota em Cache

## Epic
Root Cause — Infraestrutura (EPIC-GTM-ROOT)

## Sprint
Sprint 8: GTM Root Cause — Tier 3

## Prioridade
P2

## Estimativa
8h

## Descricao

A background revalidation (GTM-RESILIENCE-B01) so usa PNCP como fonte, falhando exatamente quando PNCP esta offline — que e quando revalidation e mais necessaria. Alem disso, quota e consumida mesmo quando a resposta vem de cache stale, desperdicando o limite do usuario em dados velhos.

### Situacao Atual

| Componente | Comportamento | Problema |
|------------|---------------|----------|
| `search_cache.py` revalidation | Usa PNCP-only via `pncp_client` | Falha quando PNCP down |
| `quota.py` | Quota consumida em toda busca | Cache stale consome quota |
| `search_pipeline.py` | `check_and_increment_quota_atomic()` | Chamado antes de verificar cache |

### Evidencia da Investigacao (Squad Root Cause 2026-02-23)

| Finding | Agente | Descricao |
|---------|--------|-----------|
| DATA-005 | Data Engineer | Revalidation PNCP-only falha quando mais precisa |
| DATA-008 | Data Engineer | Quota consumida em respostas cache stale |

## Criterios de Aceite

### Revalidation Multi-Source

- [x] AC1: `_do_revalidation()` usa `ConsolidationService` (3 fontes) em vez de PNCP-only
- [x] AC2: Se PNCP falha durante revalidation, PCP+ComprasGov fornecem resultado parcial
- [x] AC3: Resultado parcial de revalidation e melhor que cache stale (atualiza cache)
- [x] AC4: Revalidation fallback order: PNCP+PCP+ComprasGov → PCP+ComprasGov → manter stale

### Skip Quota em Cache

- [x] AC5: Quando resposta vem 100% de cache (L1 ou L2), NAO consumir quota
- [x] AC6: Flag `from_cache: bool` na response para frontend saber
- [x] AC7: Quota consumida apenas quando busca vai para fonte live (total ou parcial)
- [x] AC8: Stale-while-revalidate: quota da revalidation nao e atribuida ao user (e "sistema")

### Observabilidade

- [x] AC9: Metrica `cache_quota_skipped_total` — quantas vezes quota foi economizada por cache
- [x] AC10: Log: `Quota skipped for user {user_id}: response fully cached (params_hash={hash})`

## Testes Obrigatorios

```bash
cd backend && pytest -k "test_revalidation or test_quota_cache" --no-coverage
```

- [x] T1: Revalidation usa ConsolidationService
- [x] T2: Revalidation parcial (sem PNCP) atualiza cache
- [x] T3: Cache hit nao consome quota
- [x] T4: Live search consome quota normalmente
- [x] T5: Revalidation nao consome quota do user

## Arquivos Afetados

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/search_cache.py` | Modificar — `_do_revalidation()` usa ConsolidationService |
| `backend/search_pipeline.py` | Modificar — skip quota quando cache hit |
| `backend/quota.py` | Modificar — aceitar flag `skip_quota` |
| `backend/consolidation.py` | Modificar — expor para revalidation |
| `backend/metrics.py` | Modificar — adicionar `cache_quota_skipped_total` |

## Dependencias

| Tipo | Story | Motivo |
|------|-------|--------|
| Complementa | GTM-ARCH-002 | Cache global + revalidation multi-source = protecao completa |
| Paralela | GTM-INFRA-001 | Independente |
