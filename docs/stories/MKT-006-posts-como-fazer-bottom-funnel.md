# MKT-006 — Posts "Como Fazer" Bottom-of-Funnel (8 posts)

**Status:** pending
**Priority:** P1 — Conversão direta (maior intenção comercial)
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** frontend/app/blog/ (conteúdo editorial)
**Esforço:** 5-7 dias (2 posts/semana × 4 semanas)
**Timeline:** Semana 1-4

---

## Contexto

Posts práticos de "como fazer" com dados reais do SmartLic. Diferente dos 30 posts existentes (que são educacionais/estratégicos), estes são tutoriais orientados à ação que mostram o produto resolvendo problemas reais. Conteúdo bottom-of-funnel converte 3-5x mais que educacional.

### Evidências

- Bottom-of-funnel converte 3-5x mais (Demand Gen Report)
- Product-led content: posts que mostram o produto convertem melhor que os que não mencionam
- Posts 2.000+ palavras: 293% mais tráfego orgânico (Semrush)
- Front-load answers: 44.2% das citações de IA vêm dos primeiros 30% do texto

## Posts a Criar

### Semana 1

- [ ] **Post 1:** "Como Encontrar Licitações do Seu Setor em 5 Minutos (Passo a Passo com Dados Reais)" — 2.500 palavras
  - Keyword principal: "como encontrar licitações"
  - Schema: HowTo + FAQPage + Article
  - Mostra o SmartLic em ação: busca → filtro → resultado
  - Screenshots/GIFs do produto

- [ ] **Post 2:** "Filtro de UF em Licitações: Como Monitorar Apenas os Estados que Importam para Sua Empresa" — 2.200 palavras
  - Keyword: "monitorar licitações por estado"
  - Schema: HowTo + FAQPage
  - Foco no filtro geográfico do SmartLic

### Semana 2

- [ ] **Post 3:** "Como Avaliar se Vale a Pena Participar de uma Licitação (Framework de 4 Fatores)" — 2.800 palavras
  - Keyword: "vale a pena participar de licitação"
  - Schema: HowTo + FAQPage + Article
  - Explica o framework de viabilidade do SmartLic (modalidade, timeline, valor, geografia)
  - Complementa posts existentes mas com ângulo prático/tutorial

- [ ] **Post 4:** "Como Montar um Pipeline de Editais: Do Achado ao Contrato Assinado" — 2.500 palavras
  - Keyword: "pipeline de licitações"
  - Schema: HowTo + FAQPage
  - Mostra o Kanban do SmartLic em ação

### Semana 3

- [ ] **Post 5:** "Como Exportar Licitações para Excel e Criar Relatórios para Diretoria em 10 Minutos" — 2.000 palavras
  - Keyword: "exportar licitações excel"
  - Schema: HowTo + FAQPage + VideoObject
  - Tutorial prático da funcionalidade de export

- [ ] **Post 6:** "PNCP, Portal de Compras Públicas e ComprasGov: Como Buscar em Todas as Fontes ao Mesmo Tempo" — 2.800 palavras
  - Keyword: "buscar licitações PNCP", "portal de compras públicas"
  - Schema: FAQPage + Article + Dataset
  - Explica o diferencial multi-fonte do SmartLic

### Semana 4

- [ ] **Post 7:** "Como Usar IA para Classificar Licitações por Relevância (e Parar de Ler Edital Irrelevante)" — 2.500 palavras
  - Keyword: "classificar licitações com IA"
  - Schema: HowTo + FAQPage + Article
  - Mostra a classificação IA do SmartLic

- [ ] **Post 8:** "Licitações de Informática: Guia Completo para Encontrar, Qualificar e Priorizar Oportunidades" — 3.000 palavras
  - Keyword: "licitações de informática"
  - Schema: HowTo + FAQPage + Article + BreadcrumbList
  - Deep-dive no setor de maior volume

## Acceptance Criteria (para todos os posts)

### AC1 — Estrutura de cada post

- [ ] Front-loaded: resposta-chave nos primeiros 200 palavras
- [ ] 2 CTAs: inline (após ~40% do conteúdo) + final (botão para `/signup`)
- [ ] FAQ schema: 5 perguntas, 40-60 palavras cada resposta
- [ ] 3+ internal links para posts existentes + 2 para páginas programáticas (quando disponíveis)
- [ ] UTM tracking: `utm_source=blog&utm_medium=editorial&utm_content=[slug]`

### AC2 — Elementos visuais

- [ ] Screenshots/GIFs do SmartLic em ação (pelo menos 3 por post)
- [ ] Tabelas de dados reais quando aplicável
- [ ] Infográficos ou diagramas para frameworks (viabilidade, pipeline)

### AC3 — SEO técnico

- [ ] Meta title ≤ 60 chars, meta description 150-160 chars
- [ ] Schema JSON-LD conforme especificado por post
- [ ] Canonical URL, OG tags
- [ ] Alt text em todas as imagens

### AC4 — Cadência de publicação

- [ ] 2 posts por semana (segunda e quinta)
- [ ] Cada post gera 5-7 micro-conteúdos para LinkedIn (ver MKT-010)

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Screenshots ficam desatualizadas quando UI muda | Usar screenshots de regiões estáveis da UI; manter repositório de assets atualizável |
| Sobreposição com posts existentes (ex: viabilidade) | Ângulo diferente: existentes são estratégicos, estes são tutoriais práticos |
| Cadência de 2/semana insustentável | Buffer de 2 posts prontos antes de iniciar publicação; reduzir para 1/semana se necessário |
| Posts não convertem sem produto visível | Cada post mostra o SmartLic — product-led content, não conteúdo genérico |

## Definição de Pronto

- [ ] 8 posts publicados (2/semana × 4 semanas)
- [ ] Schema validado em todos
- [ ] CTAs funcionais com UTM tracking
- [ ] Internal links bidirecionais
- [ ] Commit com tag `MKT-006`
