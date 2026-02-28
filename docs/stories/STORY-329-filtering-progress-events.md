# STORY-329: Emitir eventos de progresso granular durante a fase de filtragem

**Prioridade:** P1 (UX — barra congelada)
**Complexidade:** M (Medium)
**Sprint:** CRIT-SEARCH

## Problema

A barra de progresso fica **congelada em 70%** por até **197+ segundos** durante a fase de filtragem. O `stage_filter()` emite apenas 2 eventos: início (60%) e fim (70%). Com 1803 items passando por keyword matching + LLM zero-match, essa fase pode ser extremamente longa sem feedback visual.

**Evidência:** Screenshot mostra "Aplicando filtros em 1803 licitacoes..." a 70% com 197s decorridos.

## Causa Raiz

`search_pipeline.py:stage_filter()` executa `aplicar_todos_filtros()` como uma única chamada sem callback de progresso. O LLM zero-match (GPT-4.1-nano batched) é o trecho mais lento e não emite progresso intermediário. O frontend vê silêncio de 30-120s+ entre "filtering started" e "complete".

## Critérios de Aceite

- [ ] AC1: `aplicar_todos_filtros()` em `filter.py` aceita callback opcional `on_progress(processed: int, total: int)` chamado a cada 50 items ou 5% do total
- [ ] AC2: `stage_filter()` conecta callback ao tracker: `emit("filtering", progress, f"Filtrando: {processed}/{total}")` com progress interpolando de 60→70
- [ ] AC3: O LLM zero-match em batch emite progresso: "Classificação IA: {n}/{total} sem keywords" com progress 65-70
- [ ] AC4: Se filtragem > 30s, emitir flag `is_long_running=true` → frontend mostra "Volume grande, pode levar até 2 min"
- [ ] AC5: Se LLM timeout (skip after 90s per STAB-003), emitir evento `llm_skipped` com motivo
- [ ] AC6: Frontend `EnhancedLoadingProgress` anima suavemente entre micro-steps (60→62→64→66→68→70)
- [ ] AC7: Teste backend com mock callback verificando chamadas a cada 50 items
- [ ] AC8: Teste frontend simulando sequência 60→62→...→70 verificando animação

## Arquivos Afetados

- `backend/filter.py` (callback `on_progress`)
- `backend/search_pipeline.py` (stage_filter: conectar callback)
- `backend/llm_arbiter.py` (progresso batch)
- `backend/progress.py` (`emit_filter_progress()` se necessário)
- `frontend/app/buscar/components/EnhancedLoadingProgress.tsx`
- `backend/tests/test_filter_progress_callback.py` (novo)
