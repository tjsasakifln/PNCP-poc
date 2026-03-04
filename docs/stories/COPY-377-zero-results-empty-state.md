# STORY-COPY-377: Reescrever empty state de zero resultados com validação + alternativas concretas

**Prioridade:** P2 (sentimento — zero resultados é momento de maior frustração)
**Escopo:** `frontend/app/buscar/page.tsx` (OnboardingEmptyState), `frontend/app/buscar/components/ZeroResultsSuggestions.tsx`
**Estimativa:** S
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

Empty states devem validar o esforço, explicar o porquê, e oferecer alternativa concreta. O estado atual é correto mas frio.

- **Cluster 2 (Richards):** "Two parts instruction, one part delight" para empty states.
- **Cluster 4 (Jiwa):** Empatia antes de solução — validar o esforço do usuário.
- **Cluster 6 (Ladeira):** Leveza sem humor forçado: "pode mudar nos próximos dias" (esperança sem promessa).

## Critérios de Aceitação

- [ ] AC1: Headline do OnboardingEmptyState: "Nenhuma oportunidade encontrada para seu perfil" → "Sua busca foi concluída"
- [ ] AC2: Subtexto: "Não encontramos oportunidades recentes para o seu perfil. Isso é normal para segmentos muito específicos." → "Não encontramos oportunidades compatíveis no período selecionado. Isso acontece em buscas mais específicas — e pode mudar nos próximos dias."
- [ ] AC3: Sugestões reescritas com copy ativa:
  - "Adicionar mais estados" → "Incluir estados vizinhos"
  - "Ampliar a faixa de valor" → "Ampliar a faixa de valor estimado"
  - "Expandir o período de análise" → "Estender o período para 15 ou 30 dias"
- [ ] AC4: CTA "Ajustar Filtros" → "Refinar busca"
- [ ] AC5: Testes atualizados

## Copy Recomendada

```
// Headline
"Sua busca foi concluída"

// Subtexto
"Não encontramos oportunidades compatíveis no período selecionado.
Isso acontece em buscas mais específicas — e pode mudar nos próximos dias."

// Sugestões
"Para ampliar resultados, tente:"
- "Incluir estados vizinhos"
- "Ampliar a faixa de valor estimado"
- "Estender o período para 15 ou 30 dias"

// CTA
"Refinar busca"
```

## Princípios Aplicados

- **Richards (UX Writing):** "Two parts instruction, one part delight" para empty states
- **Jiwa (Brand):** Empatia antes de solução — validar o esforço do usuário
- **Ladeira (Copy Brasileira):** Leveza = "pode mudar nos próximos dias" (esperança sem promessa)

## Evidência

- Atual: `buscar/page.tsx:98-116` — correto mas frio
- Best practice 2026: Empty states devem contextualizar zero como temporário, não definitivo
