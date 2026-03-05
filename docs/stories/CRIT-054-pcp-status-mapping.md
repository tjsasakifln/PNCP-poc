# CRIT-054: Mapeamento de Status PCP v2 Incompativel com Filtro

**Prioridade:** HIGH
**Componente:** Backend — portal_compras_client.py, status_inference.py, filter.py
**Origem:** Incidente 2026-03-05 — 95/104 licitacoes PCP v2 rejeitadas pelo filtro de status
**Status:** COMPLETED

## Problema

Quando PNCP esta indisponivel, o PCP v2 e a unica fonte de dados. Mas 95 de 104 licitacoes do PCP v2 foram rejeitadas pelo filtro `status=recebendo_proposta`.

O PCP v2 usa nomenclatura de status diferente do PNCP, e o `status_inference.py` nao mapeia corretamente os status do PCP v2 para o enum interno.

Resultado: backup de fonte e inutil — 91% descartado antes de chegar ao filtro de keywords.

### Root Cause

PCP v2 "Encerrado" means "session ended" (bidding phase closed) = `em_julgamento`.
PNCP "Encerrada" means process fully finalized = `encerrada`.
`status_inference.py` had no PCP v2 awareness — text match "encerrad*" → `encerrada` for ALL sources.

### Evidencia nos Logs

```json
{"rejected": {"status": 95, "modalidade": 9, "keyword": 0}}
```

Zero licitacoes chegaram ao filtro de keywords. Todas eliminadas por status/modalidade.

## Acceptance Criteria

### AC1: Mapear status PCP v2
- [x] Auditar todos os valores de status retornados pelo PCP v2 (`portal_compras_client.py`)
- [x] Mapear para o enum interno: `recebendo_proposta`, `aberta`, `encerrada`, etc.
- [x] Documentar mapeamento em comentario no codigo

### AC2: Tratamento de status desconhecido
- [x] Se PCP v2 retorna status nao mapeado, tratar como `desconhecido` (nao rejeitar)
- [x] Licitacoes com status `desconhecido` passam pelo filtro de status (fail-open para PCP v2)
- [x] Log warning: `"PCP v2 status unmapped: '{status_value}' — treating as unknown (pass-through)"`

### AC3: Status inference para PCP v2
- [x] `status_inference.py` deve usar heuristicas para PCP v2:
  - Se `data_proposta_ate` > hoje → `recebendo_proposta`
  - Se `data_proposta_ate` < hoje → `em_julgamento` (nota: corrigido de `encerrada`)
  - Se nao tem data_proposta → `desconhecido` (pass-through)
- [x] Heuristicas aplicadas ANTES do filtro de status no pipeline

### AC4: Filtro de status tolerante quando fonte unica
- [x] Se PNCP esta degraded/failed e PCP v2 e a unica fonte:
  - Relaxar filtro de status para PCP v2 (aceitar `desconhecido`)
  - Adicionar badge visual: `_status_unconfirmed=True` nos resultados PCP v2
- [x] Se PNCP esta healthy: manter filtro estrito

### AC5: Testes
- [x] Test: PCP v2 com status mapeavel → filtro funciona normalmente
- [x] Test: PCP v2 com status desconhecido → pass-through (nao rejeitado)
- [x] Test: inferencia por data funciona corretamente
- [x] Test: PNCP down + PCP v2 unica fonte → filtro relaxado

### AC6: Metricas
- [x] `smartlic_pcp_status_unmapped_total` counter
- [x] `smartlic_filter_passthrough_total` (labels: reason=unknown_status)

## Arquivos Afetados

- `backend/clients/portal_compras_client.py` — documentar status possiveis (AC1)
- `backend/status_inference.py` — PCP_V2_STATUS_MAP + _inferir_status_pcp_v2() (AC1/AC2/AC3)
- `backend/filter.py` — filtro status tolerante para PCP v2 desconhecido (AC4)
- `backend/search_pipeline.py` — propagar pncp_degraded para filtro (AC4)
- `backend/metrics.py` — PCP_STATUS_UNMAPPED_TOTAL + FILTER_PASSTHROUGH_TOTAL (AC6)
- `backend/tests/test_crit054_pcp_status_mapping.py` — 55 testes (AC5)

## Test Results

55 passed, 0 failed (CRIT-054 tests).
306 passed in related suites (status_inference, status_filter, filter, portal_compras), 0 new regressions.
