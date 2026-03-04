# STORY-COPY-374: Substituir "Falar com vendas" por CTA de menor fricção na página de planos

**Prioridade:** P1 (conversão — CTA principal do plano Consultoria)
**Escopo:** `frontend/app/planos/page.tsx`, `frontend/__tests__/org/team-management.test.tsx`
**Estimativa:** XS
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

O CTA "Falar com vendas" para o plano Consultoria cria fricção desnecessária. O `onClick` já faz checkout direto — o copy não reflete a ação real.

- **Cluster 5 (Fogg):** "vendas" é a palavra de maior aversão em compra B2B.
- **Cluster 8 (Dunford/Bush):** CTA must match the actual next step (checkout, not "talk to sales").
- **Cluster 6 (Erico):** CTA deve refletir o que o usuário quer, não o que a empresa quer.

## Critérios de Aceitação

- [ ] AC1: `planos/page.tsx:611` — "Falar com vendas" → "Começar com Consultoria"
- [ ] AC2: Testes atualizados (`team-management.test.tsx` linhas 939, 941, 1011, 1018)

## Copy Recomendada

```
"Começar com Consultoria"
```

## Princípios Aplicados

- **Fogg (Psicologia):** Redução de fricção > aumento de motivação
- **Erico Rocha (Copy Brasileira):** CTA deve refletir o que o usuário quer
- **Bush (PLG):** CTA must match the actual next step

## Evidência

- Atual: `planos/page.tsx:611` — "Falar com vendas" (mas `onClick` já inicia checkout)
- Best practice 2026: Self-serve checkout CTAs convertem 2-4x melhor que "talk to sales" para sub-$1000/mo SaaS
