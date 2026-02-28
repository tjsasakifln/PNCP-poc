# STORY-327: Unificar contadores de oportunidades — eliminar contradição raw vs filtrado

**Prioridade:** P0 (UX crítico)
**Complexidade:** M (Medium)
**Sprint:** CRIT-SEARCH
**Depende de:** STORY-326

## Problema

Após STORY-326, o usuário verá **dois números potencialmente muito distantes**: o grid de UF mostra o total filtrado (ex: 47 relevantes) enquanto o banner inferior mostra o total bruto (ex: 1930 de todas as fontes). Quando a filtragem rejeita tudo (0 relevantes de 1930 raw), o usuário vê "0" no topo e "1930" embaixo — pensando que o sistema perdeu 1930 resultados.

**Evidência:** Screenshot mostra "0 oportunidades" + "1930 oportunidades encontradas até agora" simultâneamente.

## Causa Raiz

Dois pipelines SSE independentes alimentam dois componentes sem coordenação:

- `partialProgress.totalSoFar` = soma de `record_count` dos eventos `source_complete` (raw, pré-filtragem)
- `ufTotalFound` = soma de `count` dos eventos `uf_status` (pós-busca PNCP, pré-filtragem setorial)
- Não existe evento SSE que comunique "de X encontradas, Y são relevantes"

## Critérios de Aceite

- [ ] AC1: O banner inferior durante a busca deve exibir formato **"X relevantes de Y analisadas"** (padrão Algolia), onde Y = totalSoFar (raw) e X = total filtrado
- [ ] AC2: Durante a fase de filtragem (X ainda desconhecido), exibir "Analisando Y licitações encontradas — aplicando filtros do setor..." em vez de apenas "Y encontradas"
- [ ] AC3: Se a busca completar com 0 resultados filtrados e Y > 0, exibir sugestão: "Nenhuma oportunidade relevante entre Y licitações. Tente ampliar o período ou selecionar mais estados."
- [ ] AC4: O `UfProgressGrid` header deve ser "Relevantes: N oportunidades até agora" para diferenciar de "encontradas" (raw) no banner inferior
- [ ] AC5: O backend deve emitir novo evento SSE `filter_summary` ao final da filtragem com breakdown: `{ total_raw, total_filtered, rejected_keyword, rejected_value, rejected_llm }`
- [ ] AC6: Teste de integração SSE: simular pipeline 100 raw → 15 filtrados → verificar ambos contadores
- [ ] AC7: O `SearchResults.tsx` não deve mostrar `totalSoFar` isoladamente sem contexto

## Arquivos Afetados

- `frontend/hooks/useSearchSSE.ts` (novo estado/derivado raw vs filtered)
- `frontend/app/buscar/components/SearchResults.tsx` (refatorar banner)
- `frontend/app/buscar/components/UfProgressGrid.tsx` (label "Relevantes")
- `backend/search_pipeline.py` (emit `filter_summary` event)
- `backend/progress.py` (novo `emit_filter_summary()`)
- `frontend/__tests__/components/SearchResults-counters.test.tsx` (novo)
