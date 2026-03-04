# STORY-COPY-372: Corrigir acentos em tour steps, mensagens de loading e empty states

**Prioridade:** P0 (profissionalismo)
**Escopo:** `frontend/app/buscar/page.tsx` (tour steps), `frontend/app/buscar/hooks/useSearch.ts`, `frontend/hooks/useSearchPolling.ts`
**Estimativa:** S
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

Acentos faltando em texto visível ao usuário transmitem descuido. Para compradores B2G (público conservador, avesso a risco), erros gramaticais levantam dúvida sobre a qualidade do produto inteiro.

- **Cluster 6 (Pessoa/Mohallem):** Em PT-BR, acentuação correta é sinal de profissionalismo básico.
- **Cluster 2 (Podmajersky):** Erros de escrita em microcopy transferem percepção de erro para o produto.

## Critérios de Aceitação

- [ ] AC1: Tour steps em `buscar/page.tsx`: "Defina o periodo" → "Defina o período", "orgao" → "órgão", "acompanha-las" → "acompanhá-las"
- [ ] AC2: `useSearch.ts:901`: "O periodo de busca nao pode exceder" → "O período de busca não pode exceder"; "Voce tentou" → "Você tentou"
- [ ] AC3: `useSearchPolling.ts`: Confirmar que todos os status messages têm acentos corretos
- [ ] AC4: Varredura geral em strings user-facing nos arquivos listados — nenhum acento faltando
- [ ] AC5: Testes que verificam strings literais atualizados

## Copy Recomendada

```
// Tour step search-period
'<span class="tour-step-counter">Passo 3 de 4</span><p>Defina o período para buscar editais recentes.</p>'

// Tour step results-card
'<span class="tour-step-counter">Passo 1 de 4</span><p>Cada card mostra uma oportunidade com data, valor e órgão.</p>'

// Tour step results-pipeline
'<span class="tour-step-counter">Passo 3 de 4</span><p>Clique em "Pipeline" para salvar oportunidades promissoras e acompanhá-las no kanban.</p>'

// useSearch date range error
`O período de busca não pode exceder ${max_allowed_days} dias (seu acesso atual). Você tentou buscar ${requested_days} dias. Reduza o período e tente novamente.`
```

## Princípios Aplicados

- **Pessoa (Copy Brasileira):** "A língua não erra; quem erra é quem a usa sem cuidado"
- **Podmajersky (UX Writing):** Erros de escrita em microcopy transferem percepção de erro para o produto

## Evidência

- Atual: `buscar/page.tsx:146-147` — "Defina o periodo" sem acento
- Atual: `buscar/page.tsx:162` — "orgao" sem acento
- Atual: `useSearch.ts:901` — "O periodo de busca nao pode exceder" sem acentos
