# CRIT-054: Mapeamento de Status PCP v2 Incompativel com Filtro

**Prioridade:** HIGH
**Componente:** Backend — portal_compras_client.py, status_inference.py, filter.py
**Origem:** Incidente 2026-03-05 — 95/104 licitacoes PCP v2 rejeitadas pelo filtro de status

## Problema

Quando PNCP esta indisponivel, o PCP v2 e a unica fonte de dados. Mas 95 de 104 licitacoes do PCP v2 foram rejeitadas pelo filtro `status=recebendo_proposta`.

O PCP v2 usa nomenclatura de status diferente do PNCP, e o `status_inference.py` nao mapeia corretamente os status do PCP v2 para o enum interno.

Resultado: backup de fonte e inutil — 91% descartado antes de chegar ao filtro de keywords.

### Evidencia nos Logs

```json
{"rejected": {"status": 95, "modalidade": 9, "keyword": 0}}
```

Zero licitacoes chegaram ao filtro de keywords. Todas eliminadas por status/modalidade.

## Acceptance Criteria

### AC1: Mapear status PCP v2
- [ ] Auditar todos os valores de status retornados pelo PCP v2 (`portal_compras_client.py`)
- [ ] Mapear para o enum interno: `recebendo_proposta`, `aberta`, `encerrada`, etc.
- [ ] Documentar mapeamento em comentario no codigo

### AC2: Tratamento de status desconhecido
- [ ] Se PCP v2 retorna status nao mapeado, tratar como `desconhecido` (nao rejeitar)
- [ ] Licitacoes com status `desconhecido` passam pelo filtro de status (fail-open para PCP v2)
- [ ] Log warning: `"PCP v2 status unmapped: '{status_value}' — treating as unknown (pass-through)"`

### AC3: Status inference para PCP v2
- [ ] `status_inference.py` deve usar heuristicas para PCP v2:
  - Se `data_proposta_ate` > hoje → `recebendo_proposta`
  - Se `data_proposta_ate` < hoje → `encerrada`
  - Se nao tem data_proposta → `desconhecido` (pass-through)
- [ ] Heuristicas aplicadas ANTES do filtro de status no pipeline

### AC4: Filtro de status tolerante quando fonte unica
- [ ] Se PNCP esta degraded/failed e PCP v2 e a unica fonte:
  - Relaxar filtro de status para PCP v2 (aceitar `desconhecido`)
  - Adicionar badge visual: "Status nao confirmado" nos resultados PCP v2
- [ ] Se PNCP esta healthy: manter filtro estrito

### AC5: Testes
- [ ] Test: PCP v2 com status mapeavel → filtro funciona normalmente
- [ ] Test: PCP v2 com status desconhecido → pass-through (nao rejeitado)
- [ ] Test: inferencia por data funciona corretamente
- [ ] Test: PNCP down + PCP v2 unica fonte → filtro relaxado

### AC6: Metricas
- [ ] `smartlic_pcp_status_unmapped_total` counter
- [ ] `smartlic_filter_passthrough_total` (labels: reason=unknown_status)

## Arquivos Afetados

- `backend/portal_compras_client.py` — documentar status possiveis
- `backend/status_inference.py` — heuristicas PCP v2
- `backend/filter.py` — filtro status tolerante para PCP v2
- `backend/search_pipeline.py` — propagar info de fonte unica para filtro
