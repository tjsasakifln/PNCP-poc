# GTM-STAB-004 — Partial Results com Early Return e Streaming Progressivo

**Status:** To Do
**Priority:** P0 — Blocker (usuário vê 0 resultados + erro em vez de dados parciais)
**Severity:** Backend + Frontend — dados existem mas não chegam ao usuário
**Created:** 2026-02-24
**Sprint:** GTM Stabilization
**Relates to:** GTM-STAB-003 (timeout chain), CRIT-008 (frontend resilience), CRIT-012 (SSE heartbeat)
**Sentry:** CancelledError consolidation (3), failed to pipe response (19)

---

## Problema

O pipeline atual opera em modelo **tudo-ou-nada**: coleta TODAS as UFs, depois filtra, depois classifica, depois retorna. Se o processo total excede o timeout, o usuário perde TUDO — incluindo dados que já estavam coletados e prontos.

### Cenário observado (screenshot do usuário):

```
ES: ✓ 0 oportunidades    ← PNCP respondeu, dados coletados, mas tudo sumiu no 524
MG: ✗ Indisponível       ← PNCP timeout para essa UF
RJ: ✗ Indisponível       ← PNCP timeout para essa UF
SP: ✓ 0 oportunidades    ← Dados coletados, perdidos no 524
```

Resultado: após 105s de espera, o usuário vê um erro HTTP 524. Os dados de ES e SP que ESTAVAM disponíveis foram descartados.

### Experiência enterprise esperada:

```
ES: ✓ 12 oportunidades   ← Resultado entregue em ~15s
SP: ✓ 28 oportunidades   ← Resultado entregue em ~25s
MG: ⏳ Buscando...        ← Ainda em andamento
RJ: ⏳ Buscando...        ← Ainda em andamento
→ Exibindo 40 resultados (2 de 4 estados concluídos)
→ [MG e RJ ainda processando — resultados atualizarão automaticamente]
```

---

## Acceptance Criteria

### AC1: Pipeline Progressive — resultados parciais a cada batch de UFs
- [ ] Após cada UF completar no PNCP client, enviar resultados parciais via SSE
- [ ] Novo evento SSE: `partial_results` com payload:
  ```json
  {
    "type": "partial_results",
    "data": {
      "uf": "SP",
      "items_count": 28,
      "items": [...],  // Filtrados e scored para essa UF
      "elapsed_s": 12.5
    }
  }
  ```
- [ ] Frontend acumula resultados parciais e renderiza progressivamente
- [ ] Cada UF que completa aparece imediatamente nos resultados

### AC2: Two-phase pipeline — fetch rápido, enrich progressivo
- [ ] **Fase 1 (0-60s): Coleta + Filtro keyword-only**
  - Fetch todas UFs em paralelo (batch)
  - Aplicar apenas filtro keyword (sem LLM, sem viability)
  - Retornar resultados "básicos" assim que disponíveis
  - SSE event: `basic_results_ready` (resultados sem AI scoring)
- [ ] **Fase 2 (60-110s): Enrichment assíncrono**
  - LLM classification em background
  - Viability assessment em background
  - Cada bid enriched → SSE `bid_enriched` event atualiza no frontend
  - Se timeout antes de completar, resultados básicos permanecem (não perde nada)

### AC3: Frontend progressive rendering
- [ ] `useSearch` hook deve manter `partialResults` state separado de `finalResults`
- [ ] A cada `partial_results` SSE, merge com resultados existentes
- [ ] Exibir contador progressivo: "Exibindo N resultados (X de Y estados concluídos)"
- [ ] Quando `complete` chega, transicionar suavemente para resultado final
- [ ] Se timeout: manter partial results exibidos, mostrar banner "Alguns estados não responderam"

### AC4: UF progress grid melhorado
- [ ] `UfProgressGrid.tsx` — quando UF completa com resultados:
  - Mostrar "12 oportunidades" em verde (não apenas "✓")
  - Se 0 resultados: "Sem oportunidades" em amarelo (não verde com ✓)
- [ ] Quando UF timeout: "Indisponível — tentando novamente" (não apenas vermelho)
- [ ] Quando UF em retry: mostrar countdown "Retentando... 15s"

### AC5: Nunca perder dados já coletados
- [ ] Se consolidation timeout, retornar `ConsolidationResult` com o que já coletou
- [ ] Se pipeline timeout, retornar `BuscaResponse` com dados parciais (is_partial=true)
- [ ] Se gunicorn kill, dados parciais já foram enviados via SSE (não perdem)
- [ ] Testar: simular timeout após 2 de 4 UFs → usuário vê 2 UFs com resultados

### AC6: Response semântica — nunca "Erro" quando há dados
- [ ] Se ≥1 UF retornou dados: SEMPRE retornar HTTP 200 com resultados parciais
- [ ] HTTP 524/502/500 SÓ se 0 UFs retornaram E cache vazio
- [ ] Mensagem de erro contextual:
  - 3/4 UFs OK: "Resultados para ES, SP e MG. RJ não respondeu neste momento."
  - 1/4 UFs OK: "Resultados parciais disponíveis para SP. Outros estados com indisponibilidade temporária."
  - 0/4 UFs: "Fontes indisponíveis no momento. Tentaremos novamente em instantes." + auto-retry

### AC7: Testes
- [ ] Backend: test que simula 2/4 UFs timeout → retorna partial result com 2 UFs
- [ ] Backend: test que simula ALL UFs timeout → retorna cache stale ou error
- [ ] Frontend: test que simula partial_results SSE → renderiza progressivamente
- [ ] Frontend: test de timeout → partial results mantidos, banner exibido
- [ ] E2E: busca com 4 UFs em produção → pelo menos 2 UFs devem mostrar resultados em <30s

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `backend/search_pipeline.py` | AC1+AC2: progressive pipeline, two-phase, partial SSE |
| `backend/consolidation.py` | AC5: retornar parcial no timeout |
| `backend/pncp_client.py` | AC1: on_uf_complete callback com dados filtrados |
| `backend/progress.py` | AC1: novo evento `partial_results` |
| `backend/routes/search.py` | AC6: nunca 5xx quando há dados parciais |
| `frontend/app/buscar/hooks/useSearch.ts` | AC3: partialResults state + merge |
| `frontend/app/buscar/components/UfProgressGrid.tsx` | AC4: estados melhorados |
| `frontend/app/buscar/components/SearchResults.tsx` | AC3: progressive rendering |

---

## Decisões Técnicas

- **SSE partial_results** — Alternativa seria WebSocket ou polling. SSE é o mecanismo já implementado e funcional. Apenas adicionar novo event type.
- **Two-phase pipeline** — Inspirado em Google Search: resultados básicos em <1s, enrichment progressivo depois. Prioriza "algo rápido" sobre "tudo perfeito".
- **Nunca perder dados** — Princípio #1 do enterprise search. Se coletou, entrega. Timeout não é desculpa para perder trabalho já feito.
- **0 results + green check** — O check verde significa "API respondeu", não "encontrou oportunidades". Precisa de semântica visual diferente.

## Estimativa
- **Esforço:** 8-12h (mudança arquitetural significativa)
- **Risco:** Alto (toca pipeline core, SSE, frontend state management)
- **Squad:** @architect (design two-phase) + @dev (backend pipeline) + @dev (frontend progressive) + @qa (E2E validation)
