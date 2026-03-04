# STORY-COPY-378: Success state pós-busca que confirma valor do trabalho realizado

**Prioridade:** P2 (sentimento — understatement do que o SmartLic fez)
**Escopo:** `frontend/app/buscar/components/SearchResults.tsx` ou `frontend/app/buscar/page.tsx` (header de resultados)
**Estimativa:** S
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

Quando o SmartLic retorna 47 resultados de 1.200 analisados, o usuário vê "47 resultados" mas não sabe que 1.200 foram analisados e 1.153 foram descartados como irrelevantes. O "iceberg invisível" de filtragem precisa ser tornado visível.

- **Cluster 1 (Kennedy):** Tornar visível o trabalho invisível.
- **Cluster 5 (Kahneman):** Anchoring — número grande de analisados ancora percepção de valor.
- **Cluster 2 (Drugay):** Success states devem confirmar valor, não apenas completude.

## Critérios de Aceitação

- [x] AC1: Quando resultados retornam, exibir linha de contexto acima dos cards: "Analisamos {total_analyzed} oportunidades e selecionamos {total_results} compatíveis com seu perfil."
- [x] AC2: `total_analyzed` vem do campo `filter_stats.total_before_filter` (já disponível no backend response)
- [x] AC3: Se `total_analyzed` não estiver disponível, não exibir a linha (graceful degradation)
- [x] AC4: Estilo discreto (texto cinza, font-size sm) — informativo, não chamativo
- [x] AC5: Testes para os 3 cenários: com stats, sem stats, zero resultados

## Copy Recomendada

```
// Com stats disponíveis
"Analisamos {total_analyzed} oportunidades e selecionamos {total_results} compatíveis com seu perfil."

// Singular
"Analisamos {total_analyzed} oportunidades e selecionamos 1 compatível com seu perfil."
```

## Princípios Aplicados

- **Kennedy (Direct Response):** Tornar visível o trabalho invisível
- **Kahneman (Psicologia):** Anchoring — número grande de analisados ancora valor
- **Drugay (UX Writing):** Success states devem confirmar valor, não apenas completude

## Evidência

- Atual: Resultados mostram apenas contagem final, sem contexto de filtragem
- Backend já fornece: `filter_stats.total_before_filter` no response
