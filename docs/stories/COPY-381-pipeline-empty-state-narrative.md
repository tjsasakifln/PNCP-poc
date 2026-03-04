# STORY-COPY-381: Pipeline empty state com narrativa de convite

**Prioridade:** P3 (polish — pipeline é página de retenção)
**Escopo:** `frontend/app/pipeline/page.tsx`
**Estimativa:** XS
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

O empty state atual do pipeline é funcional mas clínico.

- **Cluster 2 (Richards):** First-time empty states devem ser convites, não instruções.
- **Cluster 4 (Miller/StoryBrand):** O usuário é o herói entrando num espaço novo — o guia deve fazer ele se sentir no lugar certo.
- **Cluster 6 (Ladeira):** Leveza + direcionamento.

## Critérios de Aceitação

- [ ] AC1: Title: "Seu Pipeline de Oportunidades" → "Aqui você acompanha suas oportunidades"
- [ ] AC2: Description: "Arraste licitações para cá e acompanhe do início ao fim." → "Encontre oportunidades na busca e traga para cá. Arraste entre as colunas para acompanhar cada etapa."
- [ ] AC3: Steps reescritos:
  - "Busque licitações em Buscar" → "Faça uma análise em Buscar"
  - "Clique em Acompanhar numa oportunidade" → "Clique em Acompanhar na oportunidade desejada"
  - "Arraste entre as colunas conforme avança" → "Arraste entre colunas conforme o processo avança"
- [ ] AC4: Testes atualizados

## Copy Recomendada

```
// Title
"Aqui você acompanha suas oportunidades"

// Description
"Encontre oportunidades na busca e traga para cá.
Arraste entre as colunas para acompanhar cada etapa."

// Steps
1. "Faça uma análise em Buscar"
2. "Clique em Acompanhar na oportunidade desejada"
3. "Arraste entre colunas conforme o processo avança"
```

## Princípios Aplicados

- **Richards (UX Writing):** First-time empty = invitation, not instruction
- **Miller (StoryBrand):** "Customer enters a space; the guide makes them feel at home"
- **Ladeira (Copy Brasileira):** Leveza + direcionamento

## Evidência

- Atual: `pipeline/page.tsx:327-333` — funcional, clínico
- Best practice 2026: "Two parts instruction, one part delight" para empty states
