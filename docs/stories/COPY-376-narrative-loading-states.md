# STORY-COPY-376: Loading states narrativos que constroem confiança durante a busca

**Prioridade:** P1 (conversão — loading é o momento de maior ansiedade do usuário)
**Escopo:** `frontend/components/LoadingProgress.tsx`, `frontend/components/EnhancedLoadingProgress.tsx`, `frontend/hooks/useSearchPolling.ts`
**Estimativa:** M
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

Loading states são o microcopy de maior ROI: o usuário está preso olhando, então cada segundo é oportunidade de construir confiança.

- **Cluster 2 (Saito):** Loading states são o microcopy de maior ROI.
- **Cluster 4 (Miller/StoryBrand):** Durante o loading, o usuário é o herói esperando — o guia (SmartLic) deve narrar o que está fazendo por ele.
- **Cluster 8 (Kramer):** Narrative loading states reduzem perceived wait time em 30-40%.

## Critérios de Aceitação

- [ ] AC1: `useSearchPolling.ts` — Substituir mensagens de status por versões narrativas:
  - `validating` → "Preparando sua análise..."
  - `fetching`/`execute`/`fetch` → "Consultando fontes oficiais..."
  - `filtering`/`filter` → "Classificando por relevância para seu setor..."
  - `ranking` → "Ordenando as melhores oportunidades..."
  - `complete` → "Análise concluída"
- [ ] AC2: `LoadingProgress.tsx:40` — "Buscando licitações..." → "Analisando oportunidades..."
- [ ] AC3: `EnhancedLoadingProgress.tsx:296` — "Buscando licitações, {N}% completo" → "Analisando oportunidades, {N}% concluído"
- [ ] AC4: `EnhancedLoadingProgress.tsx:453,463` — "Buscando em todo o Brasil..." → "Analisando em todo o Brasil..."
- [ ] AC5: Testes atualizados para novas strings

## Copy Recomendada

```
"Preparando sua análise..."
"Consultando fontes oficiais..."
"Classificando por relevância para seu setor..."
"Ordenando as melhores oportunidades..."
"Análise concluída"
```

## Princípios Aplicados

- **Saito (UX Writing):** Loading states são o microcopy de maior ROI
- **Miller (Brand/StoryBrand):** Narrar o trabalho transforma espera em história
- **Kramer (PLG):** Narrative loading reduz perceived wait time em 30-40%

## Evidência

- Atual: "Buscando dados...", "Filtrando resultados..." — genérico, não constrói confiança
- Best practice 2026: Narrative loading > generic loading para perceived wait time e trust
