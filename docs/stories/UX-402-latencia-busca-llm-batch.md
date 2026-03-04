# STORY-402: Reduzir latência do pipeline de busca — LLM zero-match em batch

**Prioridade:** P0
**Esforço:** L
**Squad:** team-bidiq-backend

## Contexto
Buscas com 1 UF levam ~60s, sendo que ~8s são gastos em chamadas LLM zero-match (51 chamadas sequenciais via ThreadPoolExecutor max 10 workers). Cada chamada custa ~100-200ms. O pipeline inteiro está limitado pelo timeout de 110s (STAB-003), mas 60s para 1 UF é inaceitável para UX. O gargalo está no loop de zero-match que faz 1 chamada LLM por licitação com 0% keyword density.

## Problema (Causa Raiz)
- `backend/filter.py:2950-3076`: Loop `for lic in zero_match_pool` faz chamadas LLM individuais via `ThreadPoolExecutor(max_workers=10)`.
- Para 51 licitações no pool, são ~6 batches de 10 = ~6 roundtrips de ~200ms = ~1.2s best case, mas na prática ~8s com overhead e throttling.
- Cada chamada envia o mesmo `system_prompt` + contexto do setor. Batch prompt (enviar N objetos em 1 chamada) reduziria para 2-3 chamadas totais.

## Critérios de Aceitação
- [ ] AC1: Implementar `_classify_zero_match_batch()` em `llm_arbiter.py` que envia até 20 objetos por chamada LLM, recebendo lista de YES/NO como resposta.
- [ ] AC2: Ajustar `filter.py` para chamar batch em vez de loop individual. Fallback para chamadas individuais se batch falhar.
- [ ] AC3: Latência total do zero-match para 50 licitações deve ser < 2s (medido via métrica Prometheus `smartlic_llm_zero_match_batch_duration_seconds`).
- [ ] AC4: Manter contadores existentes (`llm_zero_match_calls`, `llm_zero_match_aprovadas`, `llm_zero_match_rejeitadas`) compatíveis.
- [ ] AC5: Se a resposta batch do LLM vier com quantidade diferente de itens, rejeitar todas (zero noise philosophy) e logar warning.
- [ ] AC6: Feature flag `LLM_ZERO_MATCH_BATCH_ENABLED` (default: True). Quando False, usa loop individual existente.
- [ ] AC7: Limite de timeout por batch: 5s. Se exceder, rejeitar pendentes e continuar pipeline.
- [ ] AC8: Métrica Prometheus: `smartlic_llm_zero_match_batch_size` histogram para monitorar distribuição de tamanhos.

## Arquivos Impactados
- `backend/llm_arbiter.py` — Nova função `_classify_zero_match_batch()` com prompt multi-item.
- `backend/filter.py` — Substituir loop individual por chamadas batch.
- `backend/config.py` — Nova feature flag `LLM_ZERO_MATCH_BATCH_ENABLED`.
- `backend/metrics.py` — Novas métricas de batch.

## Testes Necessários
- [ ] Teste unitário: batch com 20 itens retorna 20 respostas YES/NO.
- [ ] Teste unitário: batch com resposta incompleta (15 respostas para 20 itens) rejeita todas.
- [ ] Teste unitário: batch com falha LLM faz fallback para individual.
- [ ] Teste unitário: feature flag False usa loop individual.
- [ ] Teste de integração: busca com 50 zero-match items completa em < 2s (LLM mockado).
- [ ] Teste de regressão: resultados idênticos entre batch e individual para mesmos dados.

## Notas Técnicas
- Prompt batch: enviar lista numerada de objetos, pedir resposta como lista numerada de YES/NO. Exemplo:
  ```
  Classifique cada objeto como relevante (YES) ou irrelevante (NO) para o setor "{setor}":
  1. "Aquisição de computadores..."
  2. "Serviço de limpeza..."
  Responda APENAS com uma lista numerada de YES ou NO.
  ```
- GPT-4.1-nano suporta até ~128K tokens. 20 objetos com ~100 chars cada = ~2K tokens input. Seguro.
- Manter `_confidence_score` capped em 70 para zero-match (D-02 AC4).
- `ThreadPoolExecutor` pode ser mantido para paralelizar os batches (se houver >20 itens, 2 batches em paralelo).
