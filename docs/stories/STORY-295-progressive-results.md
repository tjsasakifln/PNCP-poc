# STORY-295: Progressive Results Delivery

**Sprint:** 1 — Make It Reliable
**Size:** XL (16-24h)
**Root Cause:** RC-5
**Depends on:** STORY-292
**Blocks:** STORY-296, STORY-298
**Industry Standard:** [Meta-Search Pattern](https://en.wikipedia.org/wiki/Metasearch_engine) (Skyscanner, Google Flights, Kayak)

## Contexto

Hoje `asyncio.gather()` espera TODAS as fontes (PNCP + PCP + ComprasGov) para todas as UFs antes de retornar qualquer resultado. Se PNCP-SP demora 60s e PNCP-RJ demora 5s, o usuário espera 60s para ver qualquer coisa.

Meta-search engines (Skyscanner, Google Flights, Kayak) mostram resultados à medida que cada fonte responde. O usuário vê progresso real e pode agir antes do pipeline terminar.

## Acceptance Criteria

### Backend
- [ ] AC1: Cada UF/fonte que completa publica resultado parcial via SSE event `partial_results`
- [ ] AC2: Evento SSE contém: `{ type: "partial_results", source, uf, items: [...], total_so_far, progress }`
- [ ] AC3: Resultados parciais persistidos incrementalmente em Redis (não esperar tudo)
- [ ] AC4: Resultado final (`status=completed`) é a consolidação de todos os parciais
- [ ] AC5: Se uma fonte falha, resultados das outras fontes são entregues (não all-or-nothing)
- [ ] AC6: Timeout por fonte: 90s. Se estourar, consolida o que tem e marca fonte como `timed_out`
- [ ] AC7: SSE event `source_complete` quando uma fonte termina (success ou timeout)
- [ ] AC8: SSE event `source_error` quando uma fonte falha com detalhes

### Frontend
- [ ] AC9: Resultados aparecem na tabela à medida que SSE `partial_results` chega
- [ ] AC10: Indicador visual por fonte: ✓ completa, ⏳ em progresso, ✗ falhou, ⏱ timeout
- [ ] AC11: Counter "X de Y oportunidades encontradas até agora" atualiza em real-time
- [ ] AC12: Botão "Ver resultados parciais" aparece após primeira fonte completar
- [ ] AC13: Download Excel disponível com resultados parciais (não espera tudo)
- [ ] AC14: Banner: "Busca em andamento — resultados parciais disponíveis"

### Quality
- [ ] AC15: Teste: 1 fonte rápida + 1 lenta → resultados parciais em <10s
- [ ] AC16: Teste: 1 fonte falha → outras fontes entregam resultado
- [ ] AC17: Teste: todas as fontes timeout → empty result com error details
- [ ] AC18: Testes existentes passando

## Technical Notes

```
ANTES:
  gather(PNCP, PCP, ComprasGov) → wait ALL → consolidate → return

DEPOIS:
  for each source:
    as_completed(source_tasks) → emit partial → persist → SSE
  final consolidation when all done (or timed out)
```

A mudança principal é trocar `asyncio.gather()` por `asyncio.as_completed()` no `consolidation.py`, emitindo resultados intermediários via o tracker.

## Files to Change

- `backend/consolidation.py` — `as_completed()` com emissão incremental
- `backend/search_pipeline.py` — suporte a partial results no pipeline
- `backend/progress.py` — novos event types (partial_results, source_complete, source_error)
- `backend/schemas.py` — PartialResultEvent schema
- `frontend/hooks/useSearch.ts` — handle partial_results SSE events
- `frontend/app/buscar/page.tsx` — incremental table rendering
- `frontend/app/buscar/components/SourceStatusGrid.tsx` — NEW: per-source status

## Definition of Done

- [ ] Primeiro resultado visível em <10s (era >60s)
- [ ] Falha de 1 fonte não impacta resultados das outras
- [ ] Todos os testes passando
- [ ] PR merged
