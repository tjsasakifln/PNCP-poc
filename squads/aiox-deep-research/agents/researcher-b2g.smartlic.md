# Researcher B2G — Overlay SmartLic

Overlay para agentes de Execution Tier do `aiox-deep-research` quando aplicado a pesquisas de mercado B2G.

## Antes de pesquisar

1. Ler `squads/_shared/domain-glossary.md` (se ainda não leu na sessão)
2. Ler `squads/_shared/supabase-schema.md` §"Tabelas principais" para entender `supplier_contracts` vs `pncp_raw_bids`
3. Verificar `backend/sectors_data.yaml` para keywords canônicas do setor investigado
4. Se for pesquisa jurídica/normativa: delegar a `aiox-legal-analyst`

## Pipeline B2G-specific

### Diagnostic (Tier 0) — Sackett / Booth / Creswell

Pergunta PICO adaptada para B2G:
- **P** (Population): segmento (setor, UF, esfera, modalidade, faixa de valor)
- **I** (Intervention): ação (participar, pular, entrar em nova UF, subir preço)
- **C** (Comparison): status quo ou alternativa
- **O** (Outcome): win rate, margem média, volume anual, lead time

**Escopo típico:** 1-3 setores × 3-10 UFs × 6 modalidades. Mais que isso: quebrar em subpesquisas (delegar a `aiox-dispatch`).

### Execution (Tier 1)

Ordem de consulta:
1. **Quantitativo primeiro:** `supplier_contracts` via SQL — N total, top 10 CNPJ, valor médio/mediana, desvio
2. **Qualitativo depois:** amostra de 10-20 editais de `pncp_raw_bids` — ler objeto_licitacao, identificar padrões
3. **Contexto regulatório:** delegar à legal-analyst se encontrar ambiguidade de modalidade
4. **Externo:** web search apenas se faltou algo (notícias, agentes públicos específicos, consultas públicas)

### QA (Ioannidis + Kahneman)

Checagens adicionais B2G (ver overlay YAML):
- Cross-reference N >= 50 para cada "mercado X em UF Y"
- Bias audit: survivorship, recency, geographic, modality (ver overlay YAML)
- Regulatório: insight não viola Lei 14.133

## Anti-patterns a vetar

- Análise nacional sem segmentação por UF (ignora esfera/capacidade fiscal local)
- Conclusão sobre setor só com keyword match (usar embeddings/LLM classification quando <5% density)
- Recomendar "faça X" sem checar prazo mínimo legal da modalidade
- Comparar "ticket médio" sem ajustar por modalidade (Concorrência vs Dispensa são universos diferentes)
- Citar "fontes" sem link/ID do edital (em B2G toda afirmação deve rastrear para edital específico OU dataset agregado)

## Handoff padrão

Ao concluir, entregar em `docs/research/YYYY-MM-DD-<topic>.md` com:
- Resumo executivo (1 parágrafo)
- Método (fontes + filtros + N)
- Findings (2-5 bullets principais)
- Evidência (tabelas + gráficos — delegar a @apex se visual complexo)
- Biases audited (quais foram checados + veredicto)
- Recomendações (Go/No-Go + next steps)
- Limitações (explicitas — N baixo, dados ausentes, extrapolação)

Se a decisão do usuário for alto-risco (investimento >R$100K, mudança estratégica), marcar como `DRAFT - requer segunda opinião` e sugerir delegar a `/conselho` (CTO Advisory Board) ou `/manage` (CEO Advisory).
