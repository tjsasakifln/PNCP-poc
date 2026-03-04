# STORY-COPY-380: Padronizar terminologia "análises" em vez de "buscas" em todo user-facing copy

**Prioridade:** P3 (consistência terminológica)
**Escopo:** Frontend e backend — múltiplos arquivos
**Estimativa:** L
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

O codebase alterna entre "buscas" e "análises" para descrever a mesma ação. CLAUDE.md proíbe "busca" em texto user-facing.

- **Cluster 4 (Godin):** Terminologia inconsistente fragmenta identidade de marca.
- **Cluster 3 (Geisler):** "Uma palavra = uma coisa. Sempre."
- **Cluster 3 (Handley):** Style guide é contrato com o usuário.

A palavra correta é "análise" porque:
1. É o que o usuário realmente recebe (filtrado + classificado + avaliado por IA), não apenas uma "busca"
2. "Análise" implica trabalho intelectual e justifica o preço

## Critérios de Aceitação

- [ ] AC1: Audit completo de strings user-facing que usam "busca(s)" → substituir por "análise(s)" onde aplicável
- [ ] AC2: Exceções permitidas: "Buscar oportunidades" como label de botão/CTA principal (verbo é ok); "buscar" como verbo de ação em tour steps
- [ ] AC3: "Buscando licitações" em loading → "Analisando oportunidades" (coberto por STORY-COPY-376)
- [ ] AC4: Dashboard stats: "buscas realizadas" → "análises realizadas"
- [ ] AC5: Navigation: menu item "Buscar" pode permanecer (é verbo, não substantivo)
- [ ] AC6: Testes atualizados para novas strings

## Copy Recomendada

Regra geral:
- **Substantivo:** "análise(s)" (nunca "busca(s)")
- **Verbo:** "analisar" preferido, "buscar" tolerado em CTAs de ação
- **Loading:** "Analisando..." (nunca "Buscando...")

## Princípios Aplicados

- **Godin (Brand):** Consistência terminológica = identidade de marca
- **Geisler (SaaS Conversion):** Uma palavra, um significado, sempre
- **Handley (Brand):** Style guide é contrato com o usuário

## Evidência

- Atual: "buscas" e "análises" usados intercambiavelmente em dashboard, quota messages, loading states
- Regra CLAUDE.md: "busca" listed as banned term in user-visible text
