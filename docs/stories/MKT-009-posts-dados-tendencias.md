# MKT-009 — Posts de Dados e Tendências Exclusivos (5 posts)

**Status:** pending
**Priority:** P1 — Linkbait natural + credibilidade + diferenciação
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** frontend/app/blog/ (conteúdo editorial)
**Esforço:** 4-5 dias
**Timeline:** Mês 1-3

---

## Contexto

Posts de data-journalism com dados exclusivos que só o SmartLic pode fornecer (PNCP + PCP + ComprasGov consolidados). Estes posts são linkbait natural — jornalistas, consultores, blogs de setor e até órgãos governamentais citam dados de mercado. Constroem autoridade e backlinks orgânicos.

### Evidências

- Dados exclusivos = vantagem defensável (ninguém mais tem 3 fontes consolidadas)
- Posts data-driven geram backlinks orgânicos (jornalistas citam)
- "Quantas licitações o governo publica por dia?" é uma busca sem resposta atualizada

## Posts a Criar

### Mês 1 (prioridade máxima — linkbait)

- [ ] **Post 18:** "Quantas Licitações o Governo Brasileiro Publica por Dia? (Dados Reais de 2026)" — 2.500 palavras
  - Keywords: "quantas licitações por dia", "licitações Brasil números"
  - Schema: FAQPage + Dataset + Article
  - Dados: volume diário/semanal/mensal, distribuição por esfera (federal/estadual/municipal), por modalidade
  - Gráfico interativo ou tabela visual
  - **Destaque:** nenhum outro site tem esse dado consolidado
  - Atualizar mensalmente (freshness signal)

- [ ] **Post 19:** "Ranking de UFs por Volume de Licitações em 2026: Onde Estão os Contratos?" — 2.200 palavras
  - Keywords: "licitações por estado", "ranking licitações UF"
  - Schema: FAQPage + Dataset + ItemList
  - Dados: ranking 27 UFs, % do total, valor acumulado, setor predominante por UF
  - Mapa do Brasil com heatmap de volume
  - Insight: concentração vs. distribuição geográfica

### Mês 2

- [ ] **Post 20:** "Sazonalidade de Licitações no Brasil: Quais Meses Têm Mais Editais?" — 2.500 palavras
  - Keywords: "sazonalidade licitações", "melhor época para licitação"
  - Schema: FAQPage + Dataset + Article
  - Dados: volume por mês (gráfico barras), padrões trimestrais, impacto do ciclo orçamentário
  - Insight prático: quando intensificar monitoramento por setor

- [ ] **Post 21:** "Valor Médio de Licitações por Setor: Benchmarks para Decidir Onde Competir" — 2.800 palavras
  - Keywords: "valor médio licitação", "quanto vale uma licitação"
  - Schema: FAQPage + Dataset + Article
  - Dados: mediana e quartis por setor, outliers, faixa ideal para PMEs
  - Framework: "seu setor vs. o benchmark — onde você está?"
  - Conecta com viabilidade SmartLic (fator valor = 25% do score)

### Mês 3

- [ ] **Post 22:** "Pregão Eletrônico vs. Concorrência: Distribuição por Modalidade em 2026" — 2.200 palavras
  - Keywords: "pregão eletrônico", "modalidades licitação 2026"
  - Schema: FAQPage + Dataset
  - Dados: % pregão eletrônico, concorrência, dispensa, SRP
  - Contexto: Lei 14.133 e impacto nas modalidades
  - Dica prática: qual modalidade priorizar por setor

## Acceptance Criteria

### AC1 — Dados exclusivos obrigatórios

- [ ] Cada post usa dados reais extraídos do SmartLic (não estimativas)
- [ ] Dados devem ter data de referência visível ("dados de fevereiro 2026")
- [ ] Metodologia transparente: "Analisamos X licitações publicadas entre [data] e [data] nas fontes PNCP, PCP e ComprasGov"
- [ ] Badge de credibilidade: "Dados SmartLic — 3 fontes oficiais consolidadas"

### AC2 — Visualizações

- [ ] Pelo menos 2 visualizações por post (gráficos, tabelas, mapas)
- [ ] Tabelas com dados precisos (não aproximações)
- [ ] Alt text descritivo em todos os visuais
- [ ] Visualizações otimizadas para sharing (dark social — WhatsApp, Telegram)

### AC3 — Estratégia de atualização

- [ ] Posts 18 e 19 atualizados mensalmente (freshness signal + reindexação)
- [ ] Data de última atualização visível no topo do post
- [ ] Changelog breve: "Atualização fev/2026: volume subiu 12% vs. jan/2026"

### AC4 — SEO e schema

- [ ] Schema `Dataset` com data de coleta, cobertura, licenciamento
- [ ] Front-loaded: dado mais impactante nos primeiros 200 palavras
- [ ] FAQ: 5 perguntas sobre os dados (40-60 palavras cada)
- [ ] Internal links para panoramas (MKT-004) e páginas programáticas (MKT-003)

### AC5 — Distribuição (alimenta MKT-010)

- [ ] Cada post gera: 3 dados-chave para posts LinkedIn, 1 infográfico para WhatsApp
- [ ] Dados formatados para fácil extração e sharing
- [ ] Citação sugerida: "Fonte: SmartLic — smartlic.tech/blog/[slug]"

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Dados imprecisos gerarem descrédito | Metodologia transparente, fontes oficiais citadas, margem de erro quando aplicável |
| Posts desatualizados perderem valor | Atualização mensal para posts 18/19; badge de data visível em todos |
| Concorrentes copiarem dados | Primeira-mover advantage + atualização frequente + citação da fonte SmartLic |
| Volume de dados insuficiente no início | Usar dados de 90 dias retroativos; complementar com dados históricos PNCP |

## Definição de Pronto

- [ ] 5 posts publicados com dados reais
- [ ] Visualizações renderizando corretamente
- [ ] Schema `Dataset` validado
- [ ] Estratégia de atualização mensal documentada
- [ ] Commit com tag `MKT-009`
