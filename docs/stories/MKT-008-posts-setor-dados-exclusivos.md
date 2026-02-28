# MKT-008 — Posts por Setor com Dados Exclusivos (5 posts)

**Status:** pending
**Priority:** P2 — Captura setorial + topical authority
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** frontend/app/blog/ (conteúdo editorial)
**Esforço:** 4-5 dias
**Timeline:** Mês 1-3

---

## Contexto

Deep-dives setoriais que combinam conteúdo editorial com dados exclusivos do SmartLic. Cada post é o "guia definitivo" para empresas de um setor específico encontrarem e vencerem licitações. Servem como pillar pages para as páginas programáticas setor×UF.

### Evidências

- Lacuna de mercado: conteúdo existente (Zenite, ConLicitação) é jurídico, não setorial
- SmartLic pode fornecer dados exclusivos por setor (contagem, valores, tendências)
- Posts setoriais atraem tráfego qualificado com intenção específica

## Posts a Criar

### Mês 1

- [ ] **Post 13:** "Licitações de Saúde em 2026: Onde Estão as Oportunidades e Como Chegar Primeiro" — 3.000 palavras
  - Keywords: "licitações de saúde", "editais saúde", "medicamentos licitação"
  - Schema: FAQPage + Article + Dataset
  - Dados: volume por UF, faixa de valores típica, sazonalidade, modalidades
  - Subsegmentos: medicamentos, equipamentos hospitalares, materiais de laboratório
  - Dicas setoriais: certificações necessárias, SRP vs. pregão
  - Linka para: páginas programáticas de saúde em cada UF

- [ ] **Post 14:** "Licitações de Engenharia Civil: Como Filtrar por Valor, Região e Modalidade" — 2.800 palavras
  - Keywords: "licitações engenharia civil", "obras públicas licitação"
  - Schema: FAQPage + HowTo + Dataset
  - Dados: distribuição por tipo de obra, valores medianos, UFs com mais investimento
  - Foco: como qualificar rapidamente (viabilidade SmartLic para engenharia)

### Mês 2

- [ ] **Post 15:** "Empresas de Facilities: Como Encontrar Contratos de Limpeza, Portaria e Manutenção no PNCP" — 2.800 palavras
  - Keywords: "licitação limpeza", "contrato facilities governo", "portaria licitação"
  - Schema: FAQPage + HowTo
  - Dados: contratos recorrentes vs. pontuais, ata de registro de preços
  - Foco: volume de renovação de contratos, SRP como oportunidade

- [ ] **Post 16:** "Licitações de Software e TI: O Setor que Mais Cresce em Compras Públicas" — 2.500 palavras
  - Keywords: "licitação software", "TI governo", "compras públicas tecnologia"
  - Schema: FAQPage + Article + Dataset
  - Dados: crescimento YoY, Lei 14.133 e aquisição de software, SaaS governamental
  - Foco: como empresas de software competem em pregão eletrônico

### Mês 3

- [ ] **Post 17:** "Vigilância e Segurança Patrimonial: Mapeando Editais em 27 Estados" — 2.500 palavras
  - Keywords: "licitação vigilância", "segurança patrimonial governo"
  - Schema: FAQPage + Article
  - Dados: distribuição geográfica, contratos plurianuais, exigências técnicas

## Acceptance Criteria

### AC1 — Cada post deve conter

- [ ] Dados exclusivos do SmartLic (contagem, valores, tendências do setor)
- [ ] Subsegmentação dentro do setor (baseada em keywords do `sectors_data.yaml`)
- [ ] Mapa de calor ou tabela de distribuição por UF
- [ ] Framework de qualificação adaptado ao setor (viabilidade 4 fatores)
- [ ] Front-loaded: insight principal nos primeiros 200 palavras
- [ ] FAQ: 5-7 perguntas setoriais (40-60 palavras cada)

### AC2 — Internal linking (pillar page strategy)

- [ ] Link bidirecional com todas as páginas programáticas do setor (MKT-003)
- [ ] Link para panorama do setor (MKT-004)
- [ ] Link para posts existentes que mencionam o setor
- [ ] Link para post de comparação relevante (MKT-007)

### AC3 — CTAs setorializados

- [ ] CTA inline: "Encontre licitações de {setor} em sua região — teste grátis 30 dias"
- [ ] CTA final: link para `/signup?sector={setor_id}&utm_source=blog`

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Dados insuficientes para setores menores | Começar pelos 5 setores de maior volume; adiar setores com volume baixo |
| Sobreposição com Panorama (MKT-004) | Panorama = dados agregados nacionais; Posts setoriais = guia prático + como competir |
| Keywords do setor muito competitivas | Focar em long-tail: "licitação de medicamentos em SP" > "licitação saúde" |

## Definição de Pronto

- [ ] 5 posts publicados (1/semana no mês 1-2, depois mensal)
- [ ] Dados exclusivos em todos os posts
- [ ] Internal linking bidirecional com páginas programáticas
- [ ] Schema validado
- [ ] Commit com tag `MKT-008`
