# Panorama de Licitações 2026 T1 — Outline do Relatório

**Título:** Panorama das Licitações Públicas Brasileiras — 1º Trimestre de 2026
**Subtítulo:** Um raio-X data-driven de R$ [X] bilhões em editais publicados no PNCP entre janeiro e março de 2026 — tendências, modalidades, setores e o que esperar do resto do ano.

**Publicação prevista:** 15 de abril de 2026 (2 semanas após fechamento do trimestre)
**Formato:** Landing page HTML + PDF downloadable (gated por email) + posts de redes sociais derivados
**Autor:** Equipe SmartLic — CONFENGE Avaliações e Inteligência Artificial LTDA
**Fonte primária:** Base de dados SmartLic, agregando Portal Nacional de Contratações Públicas (PNCP), Portal de Compras Públicas v2 e ComprasGov v3

---

## Objetivo estratégico

1. **Digital PR:** gerar 10+ menções em mídia B2B brasileira (Valor, Exame, StartSe, Baguete etc.) via pitch de jornalistas, resultando em backlinks de DA 70+.
2. **Lead gen:** download gate captura emails qualificados (empresas B2G interessadas em dados de mercado) → MQLs para trial SmartLic.
3. **SEO:** landing page `/relatorio-2026-t1` otimizada para queries como "licitações 2026", "panorama licitações Brasil", "dados PNCP 2026".
4. **Thought leadership:** posicionar SmartLic como "o Nubank-report do mundo B2G" — fonte obrigatória de dados de mercado.

---

## Estrutura do relatório (8 seções)

### Seção 1 — Sumário Executivo (1 página)

**Conteúdo (bullets):**
- Total de editais publicados no trimestre (contagem)
- Valor total estimado agregado (R$ bilhões)
- Variação YoY (vs T1 2025) em volume e valor
- Top 3 modalidades por volume
- Top 3 UFs por valor total
- Top 3 setores (categorização setorial SmartLic)
- Principais achados em 5 bullets
- Metodologia resumida em 1 parágrafo

**SQL:**
```sql
-- Métricas macro T1 2026
SELECT
  COUNT(*) AS total_editais,
  SUM(COALESCE(valor_total_estimado, 0)) AS valor_total_bi,
  COUNT(DISTINCT orgao_cnpj) AS orgaos_compradores,
  COUNT(DISTINCT uf) AS ufs_ativas
FROM pncp_raw_bids
WHERE data_publicacao_pncp >= '2026-01-01'
  AND data_publicacao_pncp < '2026-04-01'
  AND is_active = true;

-- Comparação YoY T1 2025 vs T1 2026
SELECT
  EXTRACT(YEAR FROM data_publicacao_pncp) AS ano,
  COUNT(*) AS editais,
  SUM(COALESCE(valor_total_estimado, 0)) AS valor_total
FROM pncp_raw_bids
WHERE (data_publicacao_pncp BETWEEN '2025-01-01' AND '2025-03-31')
   OR (data_publicacao_pncp BETWEEN '2026-01-01' AND '2026-03-31')
GROUP BY 1
ORDER BY 1;
```

---

### Seção 2 — Volume e Valor: A Fotografia Macro (2 páginas)

**Conteúdo (bullets):**
- Gráfico de linha: editais por semana ao longo do trimestre
- Gráfico de barras: valor total estimado por mês (jan/fev/mar)
- Picos e vales: quais semanas concentraram mais publicações e por quê (feriados, fechamento de orçamento)
- Comparativo YoY: crescimento/queda de volume e valor
- Ticket médio por edital (valor total / contagem)
- Distribuição de valores: quantis P25, P50, P90, P99

**SQL:**
```sql
-- Volume semanal
SELECT
  DATE_TRUNC('week', data_publicacao_pncp) AS semana,
  COUNT(*) AS editais,
  SUM(COALESCE(valor_total_estimado, 0)) AS valor_total
FROM pncp_raw_bids
WHERE data_publicacao_pncp >= '2026-01-01'
  AND data_publicacao_pncp < '2026-04-01'
GROUP BY 1
ORDER BY 1;

-- Distribuição de valores (quantis)
SELECT
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor_total_estimado) AS p25,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY valor_total_estimado) AS p50,
  PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY valor_total_estimado) AS p90,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY valor_total_estimado) AS p99,
  AVG(valor_total_estimado) AS media
FROM pncp_raw_bids
WHERE data_publicacao_pncp >= '2026-01-01'
  AND data_publicacao_pncp < '2026-04-01'
  AND valor_total_estimado > 0;
```

---

### Seção 3 — Mapa do Brasil: UFs em Destaque (2 páginas)

**Conteúdo:**
- Mapa coroplético do Brasil por volume de editais
- Tabela Top 10 UFs por valor total estimado
- Tabela Top 10 UFs por número de editais
- Insight: "UFs subestimadas" — estados com crescimento YoY acima da média nacional
- Região Sul vs Sudeste vs Nordeste vs Norte vs Centro-Oeste: distribuição
- Caso especial: concentração dos 5 maiores valores (qual edital, qual órgão, qual UF)

**SQL:**
```sql
-- Top UFs por volume e valor
SELECT
  uf,
  COUNT(*) AS editais,
  SUM(COALESCE(valor_total_estimado, 0)) AS valor_total,
  AVG(COALESCE(valor_total_estimado, 0)) AS ticket_medio
FROM pncp_raw_bids
WHERE data_publicacao_pncp >= '2026-01-01'
  AND data_publicacao_pncp < '2026-04-01'
  AND uf IS NOT NULL
GROUP BY uf
ORDER BY valor_total DESC;

-- Top 5 maiores editais do trimestre
SELECT
  orgao_entidade,
  uf,
  objeto_compra,
  valor_total_estimado,
  data_publicacao_pncp
FROM pncp_raw_bids
WHERE data_publicacao_pncp >= '2026-01-01'
  AND data_publicacao_pncp < '2026-04-01'
ORDER BY valor_total_estimado DESC NULLS LAST
LIMIT 5;
```

---

### Seção 4 — Modalidades: O Fim do Pregão Presencial? (2 páginas)

**Conteúdo:**
- Gráfico pizza: distribuição por modalidade (4=Concorrência, 5=Pregão Eletrônico, 6=Pregão Presencial, 7=Leilão, 8=Inexigibilidade, 12=Dispensa)
- Evolução YoY: Pregão Eletrônico (mod 5) vs Presencial (mod 6) — a digitalização em ritmo
- Ticket médio por modalidade
- Qual modalidade cresce mais? (delta YoY)
- Impacto da Nova Lei 14.133/21 pós-revogação das leis antigas
- Insight: Dispensas (mod 12) estão crescendo? Isso é bom ou ruim?

**SQL:**
```sql
-- Distribuição por modalidade
SELECT
  modalidade_id,
  CASE modalidade_id
    WHEN 4 THEN 'Concorrência'
    WHEN 5 THEN 'Pregão Eletrônico'
    WHEN 6 THEN 'Pregão Presencial'
    WHEN 7 THEN 'Leilão'
    WHEN 8 THEN 'Inexigibilidade'
    WHEN 12 THEN 'Dispensa'
    ELSE 'Outras'
  END AS modalidade_nome,
  COUNT(*) AS editais,
  SUM(COALESCE(valor_total_estimado, 0)) AS valor_total,
  AVG(COALESCE(valor_total_estimado, 0)) AS ticket_medio
FROM pncp_raw_bids
WHERE data_publicacao_pncp >= '2026-01-01'
  AND data_publicacao_pncp < '2026-04-01'
GROUP BY modalidade_id
ORDER BY editais DESC;

-- Crescimento YoY por modalidade
SELECT
  EXTRACT(YEAR FROM data_publicacao_pncp) AS ano,
  modalidade_id,
  COUNT(*) AS editais
FROM pncp_raw_bids
WHERE (data_publicacao_pncp BETWEEN '2025-01-01' AND '2025-03-31')
   OR (data_publicacao_pncp BETWEEN '2026-01-01' AND '2026-03-31')
GROUP BY 1, 2
ORDER BY 2, 1;
```

---

### Seção 5 — Setores Quentes: Onde o Dinheiro Público Vai (2 páginas)

**Conteúdo:**
- Top 10 setores por valor total (usando classificação SmartLic dos 15 setores — TI, Construção Civil, Saúde, Educação, Limpeza, Segurança, Alimentação, Consultoria, etc.)
- Setores com maior ticket médio
- Setores com mais editais de alta viabilidade (filtro: modalidade 5 + valor > R$100k + timeline > 15 dias)
- Insight narrativo: setor surpresa do trimestre
- Análise qualitativa: palavras-chave mais frequentes em objetos de compra

**SQL:**
```sql
-- Palavras-chave mais frequentes no objeto de compra (via full-text)
-- Requer extensão pg_trgm ou aggregate de unnest(string_to_array)
SELECT
  palavra,
  COUNT(*) AS ocorrencias
FROM (
  SELECT unnest(string_to_array(lower(regexp_replace(objeto_compra, '[^a-záéíóúâêôãõç ]', ' ', 'g')), ' ')) AS palavra
  FROM pncp_raw_bids
  WHERE data_publicacao_pncp >= '2026-01-01'
    AND data_publicacao_pncp < '2026-04-01'
) t
WHERE length(palavra) > 4
  AND palavra NOT IN ('para','pelo','pela','sobre','entre','desde','durante','contratacao','aquisicao','servico','servicos','prestacao')
GROUP BY palavra
ORDER BY ocorrencias DESC
LIMIT 50;

-- Editais "high-value" por setor (exige join com classificação setorial SmartLic)
-- Placeholder: exportar objetos e classificar via pipeline LLM interno
SELECT
  uf,
  modalidade_id,
  COUNT(*) AS editais_hv,
  SUM(valor_total_estimado) AS valor_hv
FROM pncp_raw_bids
WHERE data_publicacao_pncp >= '2026-01-01'
  AND data_publicacao_pncp < '2026-04-01'
  AND valor_total_estimado > 100000
  AND modalidade_id = 5
GROUP BY uf, modalidade_id
ORDER BY valor_hv DESC;
```

---

### Seção 6 — Concentração de Órgãos Compradores (1 página)

**Conteúdo:**
- Top 20 órgãos compradores por valor total
- Distribuição União / Estados / Municípios / Autarquias
- Índice de concentração: os top 10 órgãos representam X% do valor total
- Insight: "compradores invisíveis" — órgãos pouco conhecidos com grandes orçamentos
- Tabela: órgão, CNPJ, esfera, valor total, nº editais

**SQL:**
```sql
-- Top 20 órgãos por valor
SELECT
  orgao_cnpj,
  orgao_entidade,
  esfera_id,
  COUNT(*) AS editais,
  SUM(COALESCE(valor_total_estimado, 0)) AS valor_total
FROM pncp_raw_bids
WHERE data_publicacao_pncp >= '2026-01-01'
  AND data_publicacao_pncp < '2026-04-01'
GROUP BY 1, 2, 3
ORDER BY valor_total DESC
LIMIT 20;

-- Distribuição por esfera
SELECT
  esfera_id,
  COUNT(*) AS editais,
  SUM(COALESCE(valor_total_estimado, 0)) AS valor_total
FROM pncp_raw_bids
WHERE data_publicacao_pncp >= '2026-01-01'
  AND data_publicacao_pncp < '2026-04-01'
GROUP BY esfera_id
ORDER BY valor_total DESC;
```

---

### Seção 7 — Tendências e Projeções para o Resto de 2026 (1 página)

**Conteúdo:**
- Projeção de volume para T2-T4 baseada em sazonalidade histórica
- Setores que devem acelerar (educação volta às aulas, saúde pós-orçamento)
- Alertas: setores com queda suspeita
- Efeito ano eleitoral (se aplicável) — análise narrativa
- Recomendação para empresas B2G: onde focar esforço no T2

---

### Seção 8 — Metodologia e Limitações (1 página)

**Conteúdo:**
- Fontes de dados (PNCP, PCP v2, ComprasGov v3)
- Período exato: 2026-01-01 a 2026-03-31
- Critérios de dedup (content_hash, priority-based)
- Tratamento de valores zero/nulos
- Limitações: editais sem valor declarado, retificações, cancelamentos
- Link para dataset público (opcional — liberar CSV sumarizado via gate de email)
- Disclaimer: SmartLic e CONFENGE não se responsabilizam por decisões de negócio tomadas com base no relatório

---

## Design da Landing Page `/relatorio-2026-t1`

**Estrutura visual:**

1. **Hero (full-width, gradient background):**
   - Título H1: "Panorama das Licitações Públicas Brasileiras — T1 2026"
   - Subtítulo: "R$ [X] bilhões em editais analisados. O raio-X mais completo já publicado."
   - Botão primário: "Baixar relatório gratuito (PDF, 32 páginas)" → abre modal de download gate
   - Selo: "Dados verificados do PNCP oficial"

2. **KPIs destacados (cards grandes, 4 colunas):**
   - [X] mil editais publicados
   - R$ [X] bi em valor total
   - [X]% crescimento YoY
   - [X] UFs cobertas

3. **Teaser de gráficos (3-4 previews com blur parcial):**
   - Mapa do Brasil
   - Evolução semanal
   - Top setores
   - Modalidades

4. **Download gate (modal ou inline):**
   - Campos: Nome, Email corporativo, Empresa, Cargo (dropdown: Sócio/Diretor, Gestor B2G, Consultor, Analista, Outro)
   - Checkbox opt-in: "Quero receber insights mensais da SmartLic"
   - CTA: "Baixar agora"
   - Após submit: redirect para PDF + email de confirmação com link permanente

5. **Social proof strip:**
   - Logos: CONFENGE, Supabase, Railway, Next.js (parceiros técnicos)
   - Depoimento curto de beta user (1-2 frases)

6. **Social share:**
   - Botões Twitter/X, LinkedIn, WhatsApp, Email
   - Texto pré-preenchido: "Acabei de baixar o Panorama de Licitações 2026 T1 da @smartlic_br — dados impressionantes do PNCP. Recomendo: [link]"

7. **CTA final (footer do PDF e da landing):**
   - "Quer os dados em tempo real direto no seu pipeline? Teste SmartLic grátis por 14 dias."
   - Botão: "Começar trial gratuito" → /signup?utm_source=relatorio_t1_2026

**SEO on-page:**
- Title: "Panorama Licitações Públicas 2026 T1 | Relatório SmartLic"
- Meta description: "Análise completa dos editais publicados no PNCP em T1 2026: volume, valores, UFs, modalidades e setores. Baixe gratuitamente."
- Schema.org: `Report` + `Organization`
- H1 único, H2 por seção, alt em todas as imagens, canonical para smartlic.tech/relatorio-2026-t1

---

## Lista de 20 jornalistas/redações para pitch

| # | Veículo | Contato sugerido | Pauta sugerida |
|---|---------|-------------------|----------------|
| 1 | Valor Econômico | Redação Empresas / editoria Tecnologia | "Startups usam IA para decifrar R$X bi do PNCP" |
| 2 | Exame | Editoria Negócios / PME | "Como PMEs podem achar editais públicos relevantes com IA" |
| 3 | StartSe | Redação startups | "SmartLic publica panorama inédito das licitações públicas" |
| 4 | Neofeed | Editoria tech / government | "O mercado B2G de R$X bi que ninguém mapeava direito" |
| 5 | Baguete | Redação TI corporativa | "Dados do PNCP revelam retrato do T1 2026" |
| 6 | TI Inside | Editoria mercado | "Pregão eletrônico domina T1 com X% das compras" |
| 7 | Convergência Digital | Editoria governo | "Transformação digital em números: PNCP T1 2026" |
| 8 | IT Forum | Redação TI empresarial | "GovTech brasileira publica relatório inédito" |
| 9 | CIO Brasil | Editoria liderança | "Como CIOs de empresas B2G usam dados para priorizar editais" |
| 10 | IDG Now | Editoria mercado TI | "IA na gestão de propostas para setor público" |
| 11 | Estadão Link | Redação tech | "SmartLic mapeia R$X bi em editais públicos no T1" |
| 12 | Folha Mercado | Editoria empresas | "O caos do PNCP agora tem um raio-X" |
| 13 | InfoMoney | Editoria negócios | "Setor público movimentou R$X bi em compras no T1" |
| 14 | InvestNews | Editoria empresas | "GovTech brasileira revela números do PNCP" |
| 15 | Canaltech | Redação tech | "IA ajuda empresas a encontrar editais públicos relevantes" |
| 16 | Olhar Digital | Redação tech | "Startup usa IA para organizar as licitações públicas" |
| 17 | Tecmundo | Editoria negócios/tech | "Como funciona o sistema de licitações do Brasil em 2026" |
| 18 | MundoRH | Editoria gestão/PME | "PMEs e licitações: o guia de dados do T1" |
| 19 | TI Especialistas | Comunidade editorial | "Arquitetura de um sistema de ingestão do PNCP" (pauta técnica) |
| 20 | Época Negócios | Editoria empreendedorismo | "Uma startup quer ser o Nubank das licitações públicas" |

**Como chegar aos contatos:**
- LinkedIn Sales Navigator para identificar o jornalista específico por editoria
- Muck Rack (se budget permitir) ou Escavador para listas de contato
- Redações têm emails padrão `redacao@veiculo.com.br` — começar por aí e pedir redirect
- Para veículos grandes (Valor, Exame, Folha), identificar jornalista específico de tecnologia/empresas no LinkedIn e mandar InMail

---

## Copy do email de pitch

**Subject:** [Exclusivo] Panorama T1 2026 das licitações públicas — R$[X] bi analisados

**Corpo:**

> Olá [nome do jornalista],
>
> Sou Tiago Sasaki, founder da SmartLic — uma plataforma B2G brasileira que usa IA para analisar editais públicos no PNCP.
>
> Acabamos de fechar o **Panorama das Licitações Públicas Brasileiras — T1 2026**, um relatório de 32 páginas com dados inéditos sobre o primeiro trimestre: volume, valores, modalidades, UFs em destaque e os setores mais aquecidos. É a análise mais completa que conhecemos até hoje sobre esse mercado.
>
> **Alguns highlights que podem virar pauta:**
>
> - Foram publicados [X] mil editais no T1, somando R$[X] bilhões em valor estimado (+[X]% YoY)
> - [UF] lidera em valor total, com [R$X bi] — e o crescimento de [UF2] surpreendeu
> - Pregão Eletrônico já representa [X]% dos editais (vs [X]% em 2025) — a digitalização em ritmo acelerado
> - O setor de [setor surpresa] teve o maior crescimento YoY, com +[X]%
> - Os top 10 órgãos compradores concentram [X]% do valor total — e alguns são quase desconhecidos do grande público
>
> Posso enviar o relatório em PDF antes do embargo público (15/04) para exclusividade. Se fizer sentido para a pauta do [veículo], topo também dar uma entrevista ou fornecer dados customizados (ex: recorte regional, setorial).
>
> O dataset é 100% verificável — puxamos diretamente do PNCP oficial, Portal de Compras Públicas e ComprasGov.
>
> Link para a landing page pública (a partir de 15/04): https://smartlic.tech/relatorio-2026-t1
>
> Me avise se houver interesse? Posso mandar o PDF hoje mesmo.
>
> Abraço,
>
> Tiago Sasaki
> Founder, SmartLic
> CONFENGE Avaliações e Inteligência Artificial LTDA
> tiago.sasaki@confenge.com.br | +55 [telefone]
> https://smartlic.tech

---

## Timeline de execução

| Fase | Datas | Responsável | Entregáveis |
|------|-------|-------------|-------------|
| **1. Coleta de dados** | 01-05/04 | Data engineer | SQLs executados, CSVs exportados |
| **2. Análise e redação** | 05-10/04 | Analyst + Founder | Draft texto completo em Google Doc |
| **3. Design PDF** | 08-11/04 | Designer (freelance ou Canva) | PDF de 32 páginas com gráficos |
| **4. Landing page dev** | 08-12/04 | Dev frontend | `/relatorio-2026-t1` em produção |
| **5. QA e review** | 12-13/04 | QA + Founder | Validação final, tipos, números cruzados |
| **6. Embargoed pitch** | 10-14/04 | Founder | Envio para 20 jornalistas com embargo 15/04 |
| **7. Publicação pública** | 15/04 | Founder | Landing live, social posts, email para base |
| **8. Outreach ampliado** | 15-22/04 | Founder | Follow-ups, entrevistas, LinkedIn posts |
| **9. Ampliação** | 22/04-01/05 | Marketing | Repurpose em posts LinkedIn, Twitter threads, webinar |

**Meta:** 10+ menções em veículos B2B brasileiros, 500+ downloads do PDF (= 500 MQLs), 50+ trials iniciados via UTM do relatório nos primeiros 30 dias pós-publicação.
