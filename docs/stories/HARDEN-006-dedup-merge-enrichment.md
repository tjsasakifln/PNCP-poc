# HARDEN-006: Dedup com Merge-Enrichment (não Discard)

**Severidade:** CRITICA
**Esforço:** 1h
**Quick Win:** Nao
**Origem:** Conselho CTO — Auditoria de Fragilidades (2026-03-06)

## Contexto

Dedup em `consolidation.py:747-802` mantém registro de maior prioridade (PNCP=1 > PCP=2). Se PNCP retorna dados incompletos (timeout parcial) e PCP tem dados completos, o sistema descarta o registro completo e mantém o incompleto.

## Problema

- Usuário vê licitação sem valor_estimado quando PCP tinha essa informação
- Dedup é "keep-one" quando deveria ser "merge-best-fields"
- Perda de dados por design

## Critérios de Aceitação

- [x] AC1: Dedup faz merge de campos vazios do registro vencedor com campos do perdedor
- [x] AC2: Campos candidatos a merge: `valor_estimado`, `modalidade`, `orgao_nome`, `objeto`
- [x] AC3: Campo `_{field}_source` rastreável (auditoria de qual fonte preencheu)
- [x] AC4: Metric `smartlic_dedup_fields_merged_total` com label `field`
- [x] AC5: Teste unitário com cenário PNCP-incompleto + PCP-completo
- [x] AC6: Teste unitário com cenário ambos completos (sem merge necessário)
- [x] AC7: Zero regressions

## Arquivos Afetados

- `backend/consolidation.py` — _dedup_records() ou equivalente
- `backend/tests/test_consolidation.py` — novos testes
