# STORY-433: Quick Wins de Backlinks — SEBRAE, HARO, Listings e Dataset Público

**Priority:** P1 — Sair do Google Sandbox (1 backlink DA 80+ = saída garantida)
**Effort:** S (0,5–1 dia de trabalho + ações assíncronas contínuas)
**Squad:** @devops (coordenação) + founder (execução de outreach)
**Status:** InProgress
**Epic:** [EPIC-SEO-ORGANIC-2026-04](EPIC-SEO-ORGANIC-2026-04.md)
**Sprint:** Sprint 2 (pode começar imediatamente, paralelo com outras stories)

---

## Contexto

Domínios novos ficam no **Google Sandbox** por 1-3 meses independentemente da qualidade do conteúdo. O único gatilho comprovado para sair mais rápido é **1 backlink de autoridade real (DA > 60)**. Com 0 backlinks externos hoje, a prioridade é conseguir os primeiros 5-10 RDs de qualidade antes que o Observatório (STORY-431) gere tráfego orgânico suficiente para atrair links naturais.

**Por que esses 4 canais:**
1. **Listings (Product Hunt, Indie Hackers, StartSe, Distrito):** 5+ backlinks DA 70+ em uma semana, gratuitos, sem aprovação editorial — só criar perfil e submeter. O mais rápido possível.
2. **Dataset no Kaggle:** Backlinks acadêmicos de longa duração — comunidade de data science compartilha por anos. "Brazilian Public Procurement Dataset 2026" é único e relevante.
3. **HARO/Connectively (Help a Reporter Out):** Responder perguntas de jornalistas sobre compras públicas = 1 link editorial DA 60+ a cada 10 respostas. Taxa de conversão: 5-15%.
4. **SEBRAE pitch direto:** DA 80+ = o backlink mais valioso disponível no nicho. Abordar com conteúdo já pronto (não só um pedido).

**Regra crítica:** Velocidade de link building segura em domínio novo = **4-12 novos RDs/mês**. Acima disso com pouco tráfego levanta flags. Esta story mira os primeiros 10-15 RDs nas primeiras 4 semanas — dentro da janela segura se distribuídos organicamente.

---

## Acceptance Criteria

### AC1: Listings — submissão em 5 plataformas (meta: 5 backlinks DA 60-80 em 7 dias)

- [ ] **Product Hunt:** Criar perfil do SmartLic em `producthunt.com`. Preencher:
  - Tagline (60 chars max): "Inteligência de licitações públicas com IA — encontre os editais certos"
  - Description (260 chars max): pitch completo com diferencial (IA zero-match + viabilidade 4 fatores)
  - Screenshots: home + buscar + resultado com badge de viabilidade
  - URL: `https://smartlic.tech`
  - Maker: tiago.sasaki@confenge.com.br
  - **NÃO lançar ainda** — apenas criar produto e salvar como draft. O lançamento requer coordinação separada (upvotes de comunidade). Submeter para revisão da equipe PH.
  
- [ ] **Indie Hackers:** Criar perfil em `indiehackers.com/product`. Preencher: nome, URL, descrição, receita atual, métricas (trials ativos). Post na comunidade: "Show IH: SmartLic — B2G intelligence platform for Brazilian government procurement"

- [ ] **StartSe** (`startse.com.br`): Cadastrar SmartLic no diretório de startups. Preencher: categoria (GovTech/LegalTech), estágio (Seed/Pre-Seed), fundação, CNPJ CONFENGE.

- [ ] **Distrito** (`distrito.me`): Submeter para base de dados de startups brasileiras. Formulário em `distrito.me/startups/submit`.

- [ ] **BetaList** (`betalist.com`): Submeter como product in beta. Aprovação: 2-7 dias. Preencher: nome, tagline, website, categoria.

- [x] Documentar em `docs/seo/backlinks-log.md` cada submission com: plataforma, data, URL do perfil/post, status (pendente/publicado), DA estimado.

### AC2: Dataset público no Kaggle (meta: backlinks acadêmicos de longa duração)

- [ ] Criar dataset no Kaggle em `kaggle.com/datasets`:
  - **Título:** "Brazilian Public Procurement 2026 — PNCP Processed by AI"
  - **Descrição:** "Monthly snapshot of public procurement notices from Brazil's PNCP portal, processed and classified by sector using GPT-4.1-nano. Includes viability scores, sector classification, and geographic data for 27 Brazilian states."
  - **Licença:** CC BY 4.0 (permite reuso com atribuição)
  - **Conteúdo:** CSV com colunas: `id, setor, uf, modalidade, valor_estimado, data_publicacao, data_abertura, orgao_nome, classificacao_ia, score_viabilidade`
  - **Fonte:** SmartLic Observatório (smartlic.tech/observatorio) — incluir no README do dataset
  - **Atualização:** mensal (alinhar com relatório do Observatório)
  
- [ ] Exportar ~5.000 registros anonimizados (sem `cnpj_contratante` para privacidade) do datalake para o CSV
- [ ] Upload no Kaggle com conta `tiago.sasaki@confenge.com.br`
- [ ] Compartilhar dataset em comunidades:
  - r/datasets no Reddit
  - Escola de Dados (escoladedados.org) — seção "Fontes de Dados"
  - ABRAJI (abraji.org.br) — contato direto por email

### AC3: HARO/Connectively — sistema de resposta a jornalistas (meta: 3-5 backlinks/mês sustentados)

- [ ] Criar conta em `connectively.us` (novo HARO) com perfil:
  - Nome: Tiago Sasaki
  - Empresa: SmartLic / CONFENGE
  - Expertise: "Brazilian government procurement, public tenders, B2G intelligence, GovTech"
  - Bio: focada em credibilidade (dados PNCP, IA classificação, fundador)
  
- [ ] Configurar alertas diários para keywords: "licitações", "compras públicas", "governo", "fornecedores governo", "transparência", "PNCP", "pregão eletrônico", "Lei 14.133"
  
- [x] **Protocolo de resposta** (documentar em `docs/seo/haro-protocolo.md`):
  - Tempo máximo de resposta: 4h após receber query (jornalistas têm deadline apertado)
  - Formato: 2-3 parágrafos com dado específico + estatística + citação de fonte
  - Sempre incluir: "Tiago Sasaki, fundador do SmartLic (smartlic.tech) — plataforma de inteligência em licitações públicas"
  - Tom: especialista prático, não vendedor
  - Exemplo de pitch de dados: "Segundo dados do SmartLic Observatório, em março/2026 foram publicados X editais no setor de TI, com valor médio de R$ Y por licitação — crescimento de Z% vs. mesmo período de 2025"
  
- [ ] Responder mínimo 3 queries/dia relevantes durante o primeiro mês
- [ ] Registrar respostas em `docs/seo/backlinks-log.md` com: query título, veículo, data resposta, resultado (publicado/não)

### AC4: SEBRAE — pitch de conteúdo co-branded (meta: 1 backlink DA 80+)

- [x] Preparar documento de proposta para o SEBRAE (`docs/seo/sebrae-pitch.md`):
  - **Produto da proposta:** Artigo exclusivo para `sebrae.com.br/sites/PortalSebrae/artigos/`
  - **Título sugerido:** "Como MEIs e MEs Podem Vender para o Governo em 2026 — Dados Exclusivos"
  - **Diferencial:** estatísticas proprietárias do SmartLic (total de editais para MPEs por UF, setores mais acessíveis, valor médio de contratos ganhos por empresas de pequeno porte)
  - **O que o SmartLic oferece:** artigo redigido e revisado, dados exclusivos do datalake, fato verificável via PNCP, atualização anual
  - **O que o SEBRAE ganha:** conteúdo com dados originais que não tem em nenhum outro portal, relevante para seus 17M+ empresas cadastradas
  - **Ponto de contato sugerido:** Portal SEBRAE → Seção "Para parceiros de conteúdo" ou editorial@sebrae.com.br
  
- [ ] Identificar o canal de contato correto:
  - [ ] Verificar em `sebrae.com.br` se existe seção de parcerias/conteúdo
  - [ ] Procurar no LinkedIn: "editor conteúdo SEBRAE Nacional" ou "gerente portal SEBRAE"
  - [ ] Alternativa: SEBRAE Estadual (SP, MG, RJ) que são mais acessíveis que o Nacional
  
- [ ] Enviar proposta com artigo já redigido em draft (não pedir permissão para escrever — entregar pronto para revisão)
- [ ] Follow-up em 7 dias se não houver resposta
- [ ] Registrar em `docs/seo/backlinks-log.md`

### AC5: Wikipedia edit sprint (meta: autoridade de entidade — nofollow, mas forte sinal)

- [ ] Editar os seguintes artigos na Wikipedia PT-BR adicionando estatísticas do SmartLic Observatório como referência:
  - `pt.wikipedia.org/wiki/Portal_Nacional_de_Contratações_Públicas` — adicionar dado de volume mensal de editais com fonte SmartLic Observatório
  - `pt.wikipedia.org/wiki/Pregão_(licitação)` — adicionar estatística de % de uso do pregão eletrônico em 2025/2026
  - `pt.wikipedia.org/wiki/Lei_14.133` — adicionar impacto em volume de licitações pós-lei
  - `pt.wikipedia.org/wiki/Licitação` — adicionar dado de volume total do mercado
  - `pt.wikipedia.org/wiki/Compras_governamentais` — adicionar estatísticas do mercado BR
  
- [ ] Cada edição deve:
  - Incluir referência formatada `<ref>SmartLic Observatório. "Raio-X das Licitações — Março 2026". https://smartlic.tech/observatorio/raio-x-marco-2026. Consultado em {data}.</ref>`
  - Ser factualmente precisa e verificável
  - Seguir estilo neutro da Wikipedia (não marketeiro)
  - Não ser revertida (edições com fonte confiável costumam sobreviver)
  
- [ ] **Nota:** edições Wikipedia são nofollow — objetivo é sinal de entidade ao Google, não PageRank

### AC6: Log centralizado de backlinks

- [x] Criar `docs/seo/backlinks-log.md` com estrutura:
  ```markdown
  # SmartLic — Backlinks Log
  
  | Data | Domínio | DA | URL | Tipo | Status | Notas |
  |------|---------|-----|-----|------|--------|-------|
  | 2026-04-11 | producthunt.com | 91 | ... | Listing | Pendente | |
  ```
  
- [x] Criar `docs/seo/haro-protocolo.md` com template de resposta e registro de queries respondidas
- [x] Criar `docs/seo/sebrae-pitch.md` com o documento de proposta completo

---

## Scope

**IN:**
- Criação de perfis em listings (Product Hunt, IH, StartSe, Distrito, BetaList)
- Upload de dataset no Kaggle com CSV exportado do datalake
- Conta e protocolo HARO/Connectively
- Documento de pitch para SEBRAE
- Edições Wikipedia com dados reais
- `docs/seo/` — novos arquivos de documentação e log

**OUT:**
- Compra de backlinks (explicitamente proibido — risco de penalidade Google)
- Guest posts pagos
- Automação de respostas HARO (requer toque humano para parecer autêntico)
- Implementação de código no frontend/backend

---

## Dependências

- STORY-431 (Observatório) publicado antes das edições Wikipedia (precisa da URL do relatório como referência)
- Dados do datalake exportados para o CSV do Kaggle (query simples, sem story separada)
- Conta Google/Kaggle do fundador

---

## Riscos

- **Product Hunt "lançamento":** Criar perfil agora, mas o lançamento (que gera buzz e votos) deve ser coordenado — não lançar sem comunidade preparada. Foco nesta story é apenas o backlink de perfil.
- **SEBRAE pode demorar:** Ciclo de aprovação de conteúdo em organizações grandes = 30-90 dias. Iniciar agora para que o backlink chegue em 60-90 dias.
- **HARO taxa de conversão baixa (5-15%):** Requer volume e consistência. 3 respostas/dia × 30 dias = 90 respostas → ~10 matérias publicadas → ~10 backlinks. É um jogo de números.

---

## Dev Notes

_(a preencher pelo @devops/founder durante execução)_

---

## Arquivos Impactados

- `docs/seo/backlinks-log.md` (novo)
- `docs/seo/haro-protocolo.md` (novo)
- `docs/seo/sebrae-pitch.md` (novo)
- Nenhum arquivo de código alterado

---

## Definition of Done

- [ ] Perfil publicado em pelo menos 3 das 5 plataformas de listing (links documentados)
- [ ] Dataset no Kaggle publicado com ≥1.000 rows de dados reais
- [ ] Conta HARO criada + protocolo documentado + primeira resposta enviada
- [ ] Pitch SEBRAE enviado (email enviado ou formulário submetido)
- [ ] Mínimo 3 edições Wikipedia publicadas e não revertidas após 72h
- [ ] `docs/seo/backlinks-log.md` com todas as ações registradas

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — quick wins são ações humanas de alto impacto com resultado em dias/semanas. 1 backlink SEBRAE (DA 80+) vale mais que 100 de DA 20. |
