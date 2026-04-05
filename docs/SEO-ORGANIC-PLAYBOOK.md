# SmartLic — Playbook de Crescimento Orgânico: CAC Mínimo via Conversão Máxima
## Versão 2.1 · Atualizado: 2026-04-05

> **Premissa:** SEO impecável é o piso, não o teto. Quando alguém encontra o SmartLic —
> por busca orgânica, indicação ou conteúdo — cada touchpoint subsequente deve funcionar
> como uma sequência de confirmações crescentes: **"isso existe" → "isso funciona" →
> "isso é para mim" → "preciso disso agora"**.
>
> A métrica de sucesso não é volume de tráfego. É **CAC mínimo com conversão máxima**:
> cada real investido em conteúdo trabalhando de forma composta — audiência que converte,
> não apenas audiência que lê.

---

## Índice

| # | Parte | Foco |
|---|-------|------|
| [F](#fundação-técnica--o-piso-que-não-pode-rachar) | Fundação | SEO técnico inegociável — diretrizes abril/2026 |
| [0](#parte-0--manifesto-a-conversão-inevitável) | Manifesto | Filosofia — por que "bom conteúdo" não é suficiente |
| [1](#parte-1--princípios-de-copy-que-elimina-alternativas) | Copy | 5 regras para tornar a conversão inevitável |
| [2](#parte-2--arquitetura-de-conteúdo-3-em-1) | Conteúdo | Framework: útil + desejável + compartilhável |
| [3](#parte-3--iniciativas-técnicas-p0--p7) | Técnico | Checklists de implementação com copy especificado |
| [4](#parte-4--métricas-de-cac-mínimo) | Métricas | Dashboard orientado a R$ CAC, não cliques |
| [5](#parte-5--anti-patterns) | Anti-patterns | O que nunca fazer |
| [6](#parte-6--off-page-backlinks-e-autoridade-de-domínio) | Off-Page | Backlinks, digital PR, diretórios — **o que faltava** |
| [7](#parte-7--distribuição-produto-como-canal) | Distribuição | LinkedIn, P6 viral, YouTube, referral |

---

## Fundação Técnica — O Piso que Não Pode Rachar

> **Aviso explícito:** copy impecável não compensa SEO técnico desleixado. As diretrizes de abril/2026
> do Google penalizam ativamente páginas com problemas técnicos, independente da qualidade do conteúdo.
> O piso significa: **qualquer falha aqui anula todos os ganhos das Partes 1-3.**

### 1. Core Web Vitals — Thresholds de Abril/2026

O Google usa CWV como fator de ranking e como gate para AI Overviews. Páginas abaixo do threshold "Good" perdem posição e elegibilidade para rich snippets, independente da qualidade do conteúdo.

| Métrica | Threshold "Good" | Threshold "Needs Improvement" | Penalidade |
|---------|-----------------|-------------------------------|-----------|
| LCP (Largest Contentful Paint) | < 2,5s | 2,5s – 4s | Perda de posição + exclusão AI Overviews |
| INP (Interaction to Next Paint) | < 200ms | 200ms – 500ms | Experiência degradada = menor dwell time |
| CLS (Cumulative Layout Shift) | < 0,1 | 0,1 – 0,25 | Penalidade Page Experience |

**Verificação obrigatória por tipo de página:**
- [ ] Landing setorial `/licitacoes/[setor]` — ISR 6h com dados ao vivo: verificar LCP do card de stats
- [ ] Páginas setor×UF `/blog/licitacoes/[setor]/[uf]` — 405 páginas, ISR 24h: spot check 5 UFs
- [ ] Calculadora `/calculadora` — formulário client-side: INP crítico (interações do slider)
- [ ] Cases `/casos/[slug]` — imagens de logo de empresa: CLS de imagem sem `width`/`height`

**Ferramentas:**
```bash
# PageSpeed Insights (campo real + lab):
https://pagespeed.web.dev/?url=https://smartlic.tech/licitacoes/engenharia

# Bulk check (Search Console → Core Web Vitals report):
https://search.google.com/search-console → Experiência → Core Web Vitals
```

### 2. E-E-A-T — Sinais de Autoridade para Conteúdo B2G

Conteúdo sobre licitações públicas e contratos governamentais é classificado pelo Google como **YMYL adjacente** (decisões financeiras e legais de negócios). O sistema de E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) é aplicado com rigor extra.

**Sinais obrigatórios em cada artigo de blog:**

| Sinal | Implementação | Arquivo |
|-------|--------------|--------|
| **Expertise** | Autor identificado com cargo e experiência em licitações | `app/blog/[slug]/page.tsx` — `authorName`, `authorRole` |
| **Experience** | Data de atualização visível + "dados verificados em [data]" | Frontmatter `updatedAt` + componente no artigo |
| **Authoritativeness** | Link para fontes primárias (PNCP, Portal da Transparência, Diário Oficial) | No corpo do artigo — mínimo 2 fontes por afirmação factual |
| **Trustworthiness** | CNPJ da CONFENGE visível no rodapé, política de privacidade linkada | Footer component |

**Sinal específico de abril/2026:** o Google passou a valorizar explicitamente conteúdo com **dados verificáveis em tempo real** para queries com intenção informacional/comercial. Isso é o nosso maior diferencial — as páginas com dados do datalake ao vivo têm sinal de freshness permanente.

- [ ] **Verificar que todas as páginas com dado ao vivo** incluem timestamp de última atualização visível ao usuário (ex: "Atualizado 4 horas atrás" via ISR metadata)
- [x] **Adicionar `dateModified`** no JSON-LD de cada página com ISR igual ao `revalidate` timestamp — `BlogArticleLayout.tsx` usa `article.lastModified || article.publishDate`, cases usa `c.lastModified || c.publishDate`

### 3. AI Overviews — Elegibilidade e Otimização

O Google AI Overviews (antigo SGE) cita conteúdo baseado em três critérios principais para queries em português-BR:

1. **Schema markup correto** — `FAQPage`, `HowTo`, `Dataset` (P4 já cobre)
2. **Fragmentos diretamente respondem à query** — H2 ou H3 que é exatamente a pergunta + resposta direta no primeiro parágrafo abaixo
3. **Conteúdo de autoridade verificável** — links para fontes primárias + dados verificáveis

**Estrutura de fragmento otimizado para AI Overviews:**
```markdown
## Quantas licitações de [setor] abrem por mês em [UF]?

Em média, [N] licitações de [setor] são publicadas mensalmente em [UF] (dado: PNCP, 
últimos 90 dias). O valor médio por edital é R$ [avg]. Os órgãos que mais publicam são 
[lista dos top 3].
```

Esse padrão — H2 com a pergunta exata + resposta na primeira frase + dado + fonte — é o formato que o AI Overviews prioriza para extração.

- [ ] **Auditar os 40 artigos existentes** para verificar se H2s respondem perguntas (não apenas descrevem seções)
- [ ] **Reformatar respostas às FAQs** — primeira frase deve ser a resposta direta, não contexto

### 4. Freshness e Crawl Budget

Com 405 páginas setor×UF + 40 artigos + calculadora + CNPJ tool, o crawl budget do Google precisa ser gerenciado.

**Prioridade de crawl (sinalizada via sitemap `priority` + `changeFrequency`):**

| Prioridade | Páginas | Priority | ChangeFrequency | Justificativa |
|-----------|---------|----------|-----------------|---------------|
| 1 | `/licitacoes/[setor]` + `/blog/licitacoes/[setor]/[uf]` | 0.8-0.9 | daily | Dados ao vivo — freshness é diferencial |
| 2 | `/calculadora`, `/cnpj`, `/casos` | 0.8 | weekly | Ferramentas de conversão — alta prioridade |
| 3 | `/blog/programmatic/[setor]` | 0.8 | daily | Dado ao vivo de setor |
| 4 | Artigos de blog | 0.7 | monthly | Conteúdo estático |
| 5 | `/blog/panorama/[setor]` | 0.7 | weekly | Semi-estático |

- [x] **Verificar que as 405 páginas setor×UF** têm `changeFrequency: 'daily'` (dado ao vivo = Google deve recrawlear diariamente)
- [x] **Não indexar** `/analise/[hash]` (conteúdo gerado por usuário, não editorial) — `robots: { index: false, follow: true }` configurado em `generateMetadata`

### 5. Internal Linking — Arquitetura de PageRank

A autoridade de domínio do SmartLic precisa fluir para as páginas de maior valor de conversão. O grafo de links internos deve ser deliberado:

```
Homepage (max autoridade)
    ↓ links explícitos para:
├── /calculadora (ferramenta de conversão — P2)
├── /licitacoes/[top 5 setores] (landing setoriais)
├── /cnpj (ferramenta de prospecção — P3)
└── /casos (prova social)

Artigos de blog
    ↓ links para:
├── /licitacoes/[setor do artigo] (setor relevante)
├── /calculadora (contextual ao final)
└── /blog/licitacoes/[setor]/[uf_mais_relevante] (setor×UF)

Landing setorial /licitacoes/[setor]
    ↓ links para:
├── /blog/licitacoes/[setor]/sp, /blog/licitacoes/[setor]/mg, etc. (UFs principais)
├── /calculadora?setor=[setor] (pré-preenchida)
└── /casos (cases do mesmo setor)
```

- [x] **Verificar que a homepage** tem links explícitos para `/calculadora` e `/cnpj` — Navbar + Footer atualizados
- [x] **Verificar que cada artigo de blog** tem link para `/licitacoes/[setor]` correspondente — `RelatedPages.tsx` expandido: todos 15 setores × 27 UFs (removida limitação hardcoded de 5×5), ferramentas (calculadora, CNPJ) adicionadas como cross-links
- [x] **Verificar que cada landing setorial** tem links para as 5 UFs principais (`/blog/licitacoes/[setor]/sp`, `/mg`, `/rs`, `/pr`, `/sc`) — Seção adicionada com link para calculadora

### 6. Indexabilidade e Canonical

Erros silenciosos de canonical ou `noindex` matam meses de trabalho sem aviso.

- [ ] **Auditar mensalmente no GSC** (Cobertura → Excluídas) para detectar páginas `noindex` acidentais
- [x] **Garantir canonical correto** nas 405 páginas setor×UF — cada uma com sua própria URL canonical (não apontar para a landing setorial) — verificado: `blog/licitacoes/[setor]/[uf]/page.tsx` usa canonical self-referencing construído dos params
- [x] **Verificar que ISR não quebra canonical** — Next.js ISR regenera metadata server-side com mesmos params; `generateMetadata` é async corretamente
- [x] **Robots.txt** — confirmar que `/api/`, `/admin/`, `/auth/` estão bloqueados; que `/licitacoes/`, `/blog/`, `/calculadora/`, `/cnpj/`, `/casos/`, `/analise/` **não** estão bloqueados. Adicionadas rotas protegidas: `/dashboard`, `/conta`, `/buscar`, `/pipeline`, `/historico`, `/mensagens`, `/alertas`, `/onboarding`

- [x] **Trailing slash hardening** — `trailingSlash: false` em `next.config.js` + redirect 301 em `middleware.ts` para URLs com trailing slash. Previne split de ranking signals nas 405+ páginas
- [x] **PWA manifest** — `public/manifest.json` criado (name, icons, theme_color, lang pt-BR). Completa cadeia sw.js + offline.html existente
- [x] **Preconnect hints** — `<link rel="preconnect">` e `<link rel="dns-prefetch">` para Supabase em `layout.tsx`. Reduz TTFB nas páginas programáticas
- [x] **JSON-LD inline rendering** — `StructuredData.tsx` trocou `<Script>` (next/script, async) por `<script>` nativo. JSON-LD não é JS executável — loading async adicionava overhead desnecessário

```
# Verificação rápida:
curl https://smartlic.tech/robots.txt
curl https://smartlic.tech/sitemap.xml | grep -c "<url>" # deve retornar 450+
```

### 7. Indexação Acelerada — IndexNow + Google Ping

> **Aviso:** Sitemap + robots.txt corretos são condição necessária, mas não suficiente. Sem sinais externos de autoridade e sem notificação ativa dos mecanismos de busca, um site novo pode aguardar 4-8 semanas na fila de crawl do Google. As ações abaixo reduzem esse tempo para 24-72h para as páginas prioritárias.

**IndexNow — notificação para Bing/Yandex:**

O protocolo IndexNow permite notificar Bing e Yandex imediatamente sobre conteúdo novo ou atualizado. Esses motores indexam em horas. Embora o Google não use IndexNow diretamente, o sinal de rastreamento em múltiplos motores acelera indiretamente o crawl do Googlebot.

```bash
# Exemplo de chamada IndexNow (POST com lista de URLs):
curl -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "smartlic.tech",
    "key": "SEU_KEY_AQUI",
    "urlList": [
      "https://smartlic.tech/",
      "https://smartlic.tech/calculadora",
      "https://smartlic.tech/licitacoes/engenharia"
    ]
  }'

# Gerar key (arquivo estático): criar /public/[key].txt com o conteúdo da key
# Verificar: https://smartlic.tech/[key].txt deve retornar a key
```

**Implementação Next.js (recomendada via route handler):**
```ts
// app/api/indexnow/route.ts — chamar após deploy ou atualização de conteúdo
// Dispara automaticamente via GitHub Actions post-deploy
```

- [x] **Gerar e publicar IndexNow key** (2026-04-05) — key `e9fd5881ff34cea8b67399d910212300` gerada via `python -c "import secrets; print(secrets.token_hex(16))"`. Arquivo hospedado em `frontend/public/e9fd5881ff34cea8b67399d910212300.txt`. Validado: `curl https://smartlic.tech/e9fd5881ff34cea8b67399d910212300.txt` → HTTP 200 retornando a key.
- [x] **GitHub Action de indexação pós-deploy** (2026-04-05) — `.github/workflows/indexnow.yml` criada: diff `HEAD~1..HEAD`, mapeia `frontend/app/**/page.tsx` → URLs, POST para `api.indexnow.org` usando secret `INDEXNOW_KEY`.
- [x] **Configurar secret `INDEXNOW_KEY`** (2026-04-05) — `gh secret set INDEXNOW_KEY --repo tjsasakifln/PNCP-poc` aplicado; `gh secret list` confirma.
- [x] **Verificar resposta 202** da API IndexNow (2026-04-05) — submissão live `POST api.indexnow.org/indexnow` com `keyLocation=https://smartlic.tech/e9fd5881ff34cea8b67399d910212300.txt` e 3 URLs de teste (homepage, `/indicar`, `/blog/licitacoes/cidade/sao-paulo`) → HTTP 202 Accepted. Pipeline IndexNow ativo end-to-end.

> **Nota operacional (2026-04-05):** Primeiro deploy (`9f9c3289`) serviu o arquivo da key como 404 — `railway ssh` confirmou que o container não tinha o arquivo em `/app/public/` apesar de `robots.txt` estar presente. Causa: Docker layer cache da Railway não invalidou a layer `COPY` apesar do conteúdo ter mudado. Resolução: bump de `ARG CACHEBUST` em `frontend/Dockerfile` (commit `b6f6ac50`) forçou rebuild completo, resolvendo. Conforme pattern documentado em CLAUDE.md > Railway Deploy Rules.

**Google Ping — notificação de sitemap atualizado:**

```bash
# Pingar o Google após cada deploy ou adição de conteúdo:
curl "https://www.google.com/ping?sitemap=https://smartlic.tech/sitemap.xml"
# Resposta esperada: HTTP 200 "Sitemap notification received"
```

- [ ] **Adicionar ao script de deploy** (GitHub Actions) o Google Ping após sitemap atualizado
- [ ] **Adicionar ao Bing também:** `curl "https://www.bing.com/ping?sitemap=https://smartlic.tech/sitemap.xml"`

**Próximo lote de indexação manual (GSC URL Inspection):**

Após confirmação das 10 URLs submetidas em 2026-04-05, submeter próximo lote:

- [ ] `https://smartlic.tech/sobre`
- [ ] `https://smartlic.tech/pricing`
- [ ] `https://smartlic.tech/ajuda`
- [ ] `https://smartlic.tech/termos`
- [ ] `https://smartlic.tech/privacidade`
- [ ] `https://smartlic.tech/licitacoes/engenharia` (landing setorial — maior volume)
- [ ] `https://smartlic.tech/licitacoes/tecnologia-informacao`
- [ ] `https://smartlic.tech/blog/licitacoes/engenharia/sp` (setor×UF de maior volume)
- [ ] `https://smartlic.tech/cnpj` (ferramenta pública)
- [ ] `https://smartlic.tech/casos` (prova social)

**Sinais sociais para aceleração de descoberta:**

- [ ] **Compartilhar 3-5 páginas programáticas no LinkedIn** do founder com contexto real (dados do PNCP, não spam) — Google monitora sinais sociais como proxy de descoberta de conteúdo novo
- [ ] **Compartilhar `/calculadora`** no LinkedIn com resultado de exemplo: "empresas de engenharia em SP estão deixando R$X passar por mês — calculadora gratuita"

---

## Parte 0 — Manifesto: A Conversão Inevitável

### O problema com a maioria das estratégias de SEO B2B

Elas otimizam para tráfego. O SmartLic precisa otimizar para decisão.

Um visitante que lê um artigo e sai sem agir não é um visitante bem-atendido — é uma oportunidade mal aproveitada. O objetivo de cada ponto de contato é mover a pessoa para a próxima confirmação, não apenas informá-la.

### A sequência de 4 confirmações

Toda jornada orgânica de conversão percorre exatamente quatro estados mentais. Cada um deles precisa ser ativado em sequência, e nenhum pode ser pulado:

**Confirmação 1 — "Isso existe"**
O prospect descobre que existe uma solução específica para o problema específico que ele tem. Não uma solução genérica de tecnologia para licitações — uma solução para empresas de engenharia que estão perdendo editais em SP porque não têm capacidade de monitorar 847 publicações por mês.

*Touchpoints:* páginas setor×UF ao vivo, artigos de cauda longa, ferramenta CNPJ, calculadora.

**Confirmação 2 — "Isso funciona"**
O prospect vê evidência objetiva de que a solução entrega resultado. Não depoimento genérico. Não "clientes satisfeitos". Número real: uma construtora de médio porte em SC identificou R$ 4,2M em contratos potenciais em uma única análise de 40 minutos.

*Touchpoints:* cases com dados reais, análise compartilhável com score visível, calculadora que usa dados do PNCP — não estimativas inventadas.

**Confirmação 3 — "Isso é para mim"**
O prospect vê o próprio reflexo no produto. Não "empresas B2G em geral" — "construtoras com equipe de 5 pessoas que participam de pregões eletrônicos no Sul e estão tentando aumentar de 2 para 8 contratos por ano."

*Touchpoints:* landing pages setoriais com dados da UF do usuário, CTA com setor pré-preenchido, copy específica por perfil.

**Confirmação 4 — "Preciso disso agora"**
O prospect entende que cada dia sem o SmartLic tem custo real — editais compatíveis que abriram e fecharam enquanto ele ainda estava filtrando manualmente. Isso não é urgência fabricada. É matemática: no setor de engenharia em SP, abrem em média 28 editais por dia. Sem filtro, a análise manual de todos eles levaria 14 horas.

*Touchpoints:* contador de oportunidades ao vivo nas landing pages, copy de oportunidade perdida, dados de frequência de publicação por setor×UF.

### O sentimento-alvo: vantagem injusta

O usuário precisa sair de qualquer touchpoint com uma percepção nítida — quase desconfortável — de que quem usa o SmartLic está jogando num tabuleiro diferente. Que concorrentes que não usam estão tomando decisões no escuro e pagando por isso.

Esse sentimento não é produzido por hipérbole ("somos os melhores"). É produzido por especificidade:

- Não "análise completa de editais" → "4 fatores avaliados automaticamente: modalidade, prazo, valor estimado e distância geográfica — com peso de cada um na decisão final"
- Não "cobertura nacional" → "27 UFs, 6 modalidades, 40.847 editais no datalake — atualizados 4 vezes por dia"
- Não "economia de tempo" → "equipe de análise que gastava 3 horas/dia em triagem inicial passou a gastar 20 minutos — e descobriu 3× mais editais compatíveis"

Quanto mais específico, mais crível. Quanto mais crível, mais inevitável a conversão.

---

## Parte 1 — Princípios de Copy que Elimina Alternativas

### Regra 1: Especificidade bate generalidade sempre

Teste de especificidade: a afirmação continua verdadeira se você remover o número?

| Copy genérica (rejeitar) | Copy específica (aprovar) |
|--------------------------|--------------------------|
| "Milhares de editais monitorados" | "40.847 editais no datalake — atualização 4x/dia" |
| "Economize tempo na análise" | "Triagem que levava 3h passa para 20min" |
| "Cobertura de todo o Brasil" | "27 UFs × 6 modalidades × 15 setores = 2.430 combinações monitoradas" |
| "Alta taxa de precisão" | "4 fatores de viabilidade com peso configurável por perfil de empresa" |
| "IA avançada" | "GPT-4.1 classificando relevância setorial com threshold de 85% de precisão validado" |

**Aplicação prática:** antes de publicar qualquer headline, subheadline ou CTA, pergunte: qual número específico eu posso inserir aqui que torna essa afirmação impossível de ignorar?

### Regra 2: Comparação honesta gera mais confiança que superioridade declarada

Evite: "somos melhores que a concorrência."
Use: "a diferença de resultado é essa — você decide se é relevante para você."

Exemplo de comparação que converte:
> "Sem filtro estratégico, uma equipe de 2 analistas consegue avaliar ~40 editais/semana.
> Com o SmartLic, a mesma equipe avalia todos os editais relevantes do setor — e só os relevantes.
> No setor de TI em SP, isso representa a diferença entre analisar 12% ou 100% das oportunidades disponíveis."

Isso não é autopromoção. É uma afirmação verificável. E afirmações verificáveis convertem.

### Regra 3: Copy não-substituível

**Critério de aprovação brutal:** se você pode substituir "SmartLic" pelo nome de qualquer concorrente sem perder o sentido — o texto foi rejeitado.

| Substituível (rejeitar) | Não-substituível (aprovar) |
|-------------------------|---------------------------|
| "Plataforma de licitações com IA" | "O único lugar onde você vê score de viabilidade calculado com dados do PNCP ao vivo — não com estimativa de 2022" |
| "Busca inteligente de editais" | "Filtro que aprendeu com o perfil de 15 setores e descarta automaticamente o que sua empresa não ganha" |
| "Análise completa de oportunidades" | "4 fatores — modalidade (30%), prazo (25%), valor (25%), geografia (20%) — com peso baseado em taxa histórica de vitória do setor" |

A não-substituibilidade vem da especificidade técnica do produto, não de adjetivos.

### Regra 4: Funil de inevitabilidade — cada frase elimina uma razão para não agir

Mapeie as objeções na ordem em que aparecem e elimine-as sequencialmente:

1. *"Não sei se funciona para o meu setor"* → "15 setores cobertos, incluindo [setor do visitante detectado por URL]"
2. *"Parece complicado"* → "Resultado em 3 minutos: setor + UF + período = lista priorizada"
3. *"É caro demais"* → "Uma licitação ganha paga R$397 × 12 meses = R$4.764. O contrato médio de [setor] em [UF] é R$X"
4. *"Não tenho tempo agora"* → "14 dias grátis, sem cartão. Configuração em 90 segundos."
5. *"Deixa eu pensar"* → mostrar contador de editais que abriram nas últimas 24h no setor deles

### Regra 5: Dado real como único argumento aceitável

Toda afirmação de benefício precisa de evidência. A hierarquia de evidências:

1. **Número do próprio produto** (strongest): "847 editais de saúde abertos em SP este mês"
2. **Dado verificável de fonte pública**: "No pregão eletrônico, empresas que participam de 10+ editais/mês têm 3,2× mais chance de vencer (dados PNCP 2025)"
3. **Case de beta com número real**: "GJS Construções identificou R$4,2M em contratos potenciais em 40 minutos de análise"
4. **Benchmark setorial calculado**: "Empresa média do setor de engenharia em SP perde R$180k/ano em editais compatíveis que não analisou"

**Nunca use:** depoimento sem número, "clientes dizem que...", "percepção de mercado", "estudos mostram".

---

## Parte 2 — Arquitetura de Conteúdo 3-em-1

Todo conteúdo publicado pelo SmartLic deve cumprir três funções simultaneamente. Conteúdo que serve apenas uma delas é conteúdo mediano — e mediano não converte.

### As 3 funções obrigatórias

**Função 1 — Genuinamente útil para não-cliente**
Resolve um problema real sem exigir que a pessoa seja cliente. Isso reduz CAC porque:
- A pessoa volta (retention de audiência)
- A pessoa compartilha (amplificação zero-cost)
- A pessoa associa utilidade ao SmartLic (brand equity pré-conversão)

**Função 2 — Irresistivelmente desejável para prospect**
Cada seção do conteúdo é simultaneamente um argumento de compra implícito. Não "conheça nossa plataforma" — mas a experiência de ler o conteúdo torna óbvio que quem tem acesso ao SmartLic sabe coisas que quem não tem não sabe.

**Função 3 — Compartilhável por cliente ativo**
Clientes ativos devem conseguir enviar o conteúdo a pares com zero edição. Isso exige:
- Título que faz sentido sem contexto extra
- Dado ou insight que causa reação ("não sabia disso")
- Formato escaneável (tabelas, listas, comparativos)

### Critério de aprovação por tipo de conteúdo

| Tipo | Útil? | Desejável? | Compartilhável? | Critério de rejeição |
|------|-------|-----------|-----------------|---------------------|
| Artigo de blog | ✅ responde pergunta real | ✅ inclui dado exclusivo do datalake | ✅ tem headline autônoma + tabela | Sem dado específico → rejeitar |
| Landing setor×UF | ✅ lista editais reais ao vivo | ✅ score de viabilidade visível | ✅ URL compartilhável com dados | Dados estáticos → rejeitar |
| Calculadora | ✅ calcula impacto real da empresa | ✅ resultado mostra oportunidade perdida | ✅ resultado copiável/enviável | Números genéricos → rejeitar |
| Ferramenta CNPJ | ✅ devolve histórico real da empresa | ✅ score B2G com comparativo setorial | ✅ URL por CNPJ = link para prospecto enviar | Sem comparativo → rejeitar |
| Case de beta | ✅ blueprint replicável | ✅ número real de resultado | ✅ "isso aconteceu com empresa igual a minha" | Sem número de resultado → rejeitar |
| Análise compartilhada | ✅ devolve dado do edital | ✅ score de viabilidade visível | ✅ compartilhado via WhatsApp para decisor | Sem CTA contextual → rejeitar |

### Mapping por estágio do funil

```
TOPO (awareness — "isso existe")
├── Artigos de cauda longa: "licitações de engenharia em SP"
├── Landing pages setor×UF: /licitacoes/engenharia/sp
└── Ferramenta CNPJ pública: /cnpj/[cnpj]

MEIO (consideração — "isso funciona" + "isso é para mim")
├── Calculadora de oportunidades perdidas: /calculadora
├── Cases de beta com resultado real: /casos/[slug]
├── Blog: artigos com dado exclusivo do datalake
└── Páginas panorama por setor: /blog/panorama/[setor]

FUNDO (decisão — "preciso disso agora")
├── Análise compartilhada: /analise/[hash] (vista pelo decisor)
├── Páginas programáticas com contador ao vivo
└── CTAs contextuais pós-calculadora/CNPJ
```

---

## Parte 3 — Iniciativas Técnicas (P0–P7)

> Os checklists técnicos abaixo são a fundação. O que foi adicionado nesta versão é:
> (a) o mecanismo de conversão de cada iniciativa, (b) a copy específica do touchpoint,
> e (c) a confirmação que cada iniciativa ativa na sequência.

---

### P0 — Corrigir Sitemap

**Prioridade:** CRÍTICA · **Esforço:** 1-2h · **Confirmação ativada:** 1 ("isso existe")

> **Por que indexação = velocidade de confirmação:**
> Páginas não indexadas são touchpoints que não existem. O Google pode levar semanas para
> rastrear sem sitemap. A Confirmação 1 ("isso existe") só acontece se o Google sabe que
> a página existe. Nenhuma outra tarefa de SEO faz sentido antes disso.

**Arquivo:** `frontend/app/sitemap.ts`

| Rota | Páginas | No Sitemap Atual? |
|------|---------|-------------------|
| `/blog/programmatic/[setor]` | 15 | ❌ |
| `/blog/licitacoes/[setor]/[uf]` | 25 (fase 1) | ❌ |
| `/blog/panorama/[setor]` | 15 | ❌ |

#### Checklist de implementação

- [x] **Abrir `frontend/app/sitemap.ts`**
- [x] **Importar os helpers necessários:**
  ```ts
  import { generateSectorParams, generateLicitacoesParams } from '@/lib/programmatic';
  ```
- [x] **Adicionar rotas `/blog/programmatic/[setor]`** (15 páginas, priority 0.8):
  ```ts
  const programmaticSectorRoutes: MetadataRoute.Sitemap = generateSectorParams().map(({ setor }) => ({
    url: `${baseUrl}/blog/programmatic/${setor}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.8,
  }));
  ```
- [x] **Adicionar rotas `/blog/licitacoes/[setor]/[uf]`** (405 páginas full 15×27, priority 0.8):
  ```ts
  const licitacoesUfRoutes: MetadataRoute.Sitemap = generateLicitacoesParams().map(({ setor, uf }) => ({
    url: `${baseUrl}/blog/licitacoes/${setor}/${uf}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.8,
  }));
  ```
- [x] **Adicionar rotas `/blog/panorama/[setor]`** (15 páginas, priority 0.7):
  ```ts
  const panoramaSectorRoutes: MetadataRoute.Sitemap = generateSectorParams().map(({ setor }) => ({
    url: `${baseUrl}/blog/panorama/${setor}`,
    lastModified: new Date(),
    changeFrequency: 'weekly' as const,
    priority: 0.7,
  }));
  ```
- [x] **Incluir os arrays no `return`** do sitemap:
  ```ts
  return [
    // ... rotas existentes ...
    ...programmaticSectorRoutes,
    ...licitacoesUfRoutes,
    ...panoramaSectorRoutes,
  ];
  ```
- [ ] **Verificar sitemap no browser** após deploy: `https://smartlic.tech/sitemap.xml`
  - Confirmar que `/blog/programmatic/informatica` aparece
  - Confirmar que `/blog/licitacoes/engenharia/sp` aparece
  - Confirmar que `/blog/panorama/saude` aparece
  - Contagem total esperada: ~85 entradas novas
- [ ] **Submeter sitemap ao Google Search Console**
- [x] **Commit:** `seo: add programmatic blog routes to sitemap (+435 urls)`

---

### P1 — Expansão Programática 15×27 = 405 Páginas

**Prioridade:** ALTA · **Esforço:** 2-4h · **Confirmação ativada:** 1 + 3 ("isso existe" + "isso é para mim")

> **Por que é vantagem injusta:**
> Cada uma das 405 páginas exibe dados ao vivo do datalake: total de editais abertos agora,
> valor médio dos últimos 90 dias, tendência, top oportunidades. Concorrentes com blogs estáticos
> não podem competir com isso — suas páginas exibem dados de 2022 apresentados como atuais.
> Dado real ao vivo = a única afirmação que não envelhece e não pode ser copiada sem reconstruir
> toda a infraestrutura de ingestão.
>
> **KD alvo:** 10-25 para queries "[setor] [UF]" — intenção de compra, não de pesquisa.

**Arquivo:** `frontend/lib/programmatic.ts`

#### Copy do hero da página setor×UF

A headline e subheadline de cada página `/blog/licitacoes/[setor]/[uf]` devem usar os dados ao vivo:

```
H1: "[N] licitações de [setor] abertas em [UF] agora"
Subheadline: "Valor médio: R$ [avg_value]. Atualizado [timestamp]. 
              Empresas do setor que usam filtro estratégico analisam 
              todas — não só as que aparecem primeiro."
CTA: "Ver as [N] oportunidades completas → [/signup?ref=licitacoes-[setor]-[uf]]"
```

**Por que esse copy converte:** o número de editais "agora" + o valor médio = Confirmação 2 em 2 linhas. O prospect que chegou por busca orgânica vê que a plataforma conhece o mercado dele com precisão de hoje, não de ontem.

#### Checklist de implementação

- [x] **Abrir `frontend/lib/programmatic.ts`**
- [x] **Localizar `generateLicitacoesParams()`** (linha ~446)
- [x] **Substituir o corpo de `generateLicitacoesParams()`:**
  ```ts
  export function generateLicitacoesParams(): { setor: string; uf: string }[] {
    return generateSectorUfParams(); // 15 × 27 = 405
  }
  ```
- [x] **Verificar `getRegionalEditorial(uf, sector)`** cobre todas as 27 UFs — verificado: `ALL_UFS` array tem 27 entradas, `UF_TO_REGION` mapeia todas para 5 regiões
  - Adicionar fallback genérico para UFs sem editorial específico (Norte, Nordeste, CO)
- [ ] **Testar build local:** `cd frontend && npm run build`
  - Se build muito lento: `export const dynamicParams = true` + ISR on-demand
- [ ] **Monitorar rate limit** durante build (405 chamadas para `/v1/blog/stats/setor/{id}/uf/{uf}`)
  - Se necessário: top 50 páginas estáticas + ISR para restante
- [ ] **Deploy e validação:**
  - Navegar para `/blog/licitacoes/vestuario/ba` — deve carregar com dados reais
  - Verificar ISR 24h via header `x-nextjs-cache: HIT`
- [x] **Commit:** `seo(programmatic): expand sector×UF pages from 25 to 405 (full 15×27)`

---

### P2 — Calculadora Pública `/calculadora`

**Prioridade:** ALTA · **Esforço:** 3-5 dias · **Confirmação ativada:** 2 + 4 ("isso funciona" + "preciso disso agora")

> **Mecanismo de conversão:** a calculadora produz o momento de choque — o número que torna
> o custo de não usar o SmartLic tangível e pessoal. Não "empresas B2G perdem dinheiro".
> "A sua empresa, no seu setor, na sua UF, está deixando R$ X.XXX.XXX passar por mês."
>
> O choque precisa de três ingredientes: (1) dado real do PNCP, (2) personalização,
> (3) comparativo imediato entre "sem filtro" e "com filtro".
>
> **KPI esperado:** 500 cálculos/mês → 15% conversão para trial = 75 trials/mês só por esse canal.
> CAC estimado: R$ 0 (orgânico) → custo de desenvolvimento amortizado em <3 meses.

#### Copy do resultado da calculadora (o momento que converte)

```
CARD PRINCIPAL (vermelho/laranja — urgência visual):
"R$ [X.XXX.XXX]"
"Valor de editais de [setor] em [UF] que sua equipe não está analisando por mês"

BREAKDOWN (3 linhas abaixo):
"Seu setor tem [N] licitações/mês nessa UF — dado real do PNCP"
"Sua equipe cobre [Y%] do total disponível"
"Os [top 20%] de empresas do seu setor cobrem [Z%]"

COMPARATIVO (dois cards lado a lado):
Sem filtro estratégico:        Com SmartLic:
[Y]% de cobertura             [100]% das relevantes
[3h/dia] em triagem manual    [20min/dia] de revisão
[N × taxa_vitória] wins/ano   [3× mais oportunidades analisadas]

CTA FINAL (verde, texto específico):
"Analisar as [N] oportunidades abertas agora no seu setor →"
→ /signup?ref=calculadora&setor=[setor]&uf=[uf]
```

**Por que esse copy é não-substituível:** o número R$X.XXX.XXX é calculado com dados reais do PNCP para o setor e UF específicos do usuário. Nenhum concorrente pode colocar o mesmo número — porque nenhum tem o datalake.

#### Mecânica dos inputs

1. Setor de atuação (dropdown — 15 setores)
2. UF principal de operação (dropdown — 27 UFs)
3. Quantos editais sua equipe analisa por mês? (slider 1-200)
4. Qual sua taxa de vitória atual? (slider 5%-50%)
5. Valor médio dos seus contratos? (input R$)

#### Checklist de implementação — Backend

- [x] **Criar endpoint público** `GET /v1/calculadora/dados?setor={id}&uf={uf}`
  - Retorna: `{ total_editais_mes, avg_value, p25_value, p75_value, setor_name, uf }`
  - Query em `pncp_raw_bids` agrupada por setor/UF — últimos 30 dias
  - **Sem autenticação** (público — é marketing)
  - Cache: InMemory 1h
  - Rate limit: global middleware
- [x] **Adicionar rota** em `backend/routes/calculadora.py`
- [x] **Testar endpoint:** 12 testes passando em `tests/test_calculadora.py`

#### Checklist de implementação — Frontend

- [x] **Criar `frontend/app/calculadora/page.tsx`**
- [x] **Metadata SEO:** title, description, canonical, OG, Twitter
- [x] **Schema markup:** `HowTo` + `FAQPage` + `BreadcrumbList`
- [x] **Formulário de 3 etapas** com validação client-side (`CalculadoraClient.tsx`)
- [x] **Buscar dados reais** via `GET /api/calculadora/dados?setor=X&uf=Y` (proxy sem auth)
  - Criado `frontend/app/api/calculadora/dados/route.ts`
- [x] **Resultado visual** com card de choque R$, breakdown, comparativo lado-a-lado
- [x] **CTA contextual:** "Analisar as X oportunidades abertas agora no seu setor" → `/signup?ref=calculadora&setor={setor}&uf={uf}`
- [x] **Adicionar `/calculadora`** ao sitemap.ts (priority 0.9, changeFrequency: 'weekly')
- [x] **Adicionar link** na landing page, footer, e ao final de cada artigo setorial — Navbar, Footer (seção Ferramentas) e BlogArticleLayout sidebar atualizados
- [ ] **Testar mobile** (formulário de 3 passos funciona em 375px?)
- [x] **Analytics:** evento `calculadora_completed` no Mixpanel com `{ setor, uf, resultado_valor, clicked_cta }`
- [ ] **Commit:** `feat(seo): add /calculadora public conversion tool with real PNCP data`

---

### P3 — Ferramenta Gratuita CNPJ `/cnpj/[cnpj]`

**Prioridade:** ALTA · **Esforço:** 4-6 dias · **Confirmação ativada:** 3 ("isso é para mim")

> **Por que converte:** empresa que Googla o próprio CNPJ + "licitação" tem intenção declarada.
> É o funil mais curto possível: encontrou → viu o próprio histórico → entendeu a oportunidade → fez trial.
>
> **Infra já existente:** Portal da Transparência integrado em `backend/` (API key configurada,
> endpoint `/contratos/cpf-cnpj?cpfCnpj=` validado, testado com CNPJ real em 2026-03-03).
>
> **Queries alvo:** "CNPJ 12345678 licitações", "contratos governo empresa X", "histórico licitação CNPJ"

#### Copy por estado da empresa (3 cenários)

**Cenário A — Empresa ativa (5+ contratos nos últimos 24 meses):**
```
H1: "[Razão Social] — [N] contratos com o governo / R$ [total] em 24 meses"
Subheadline: "Score B2G: ATIVA. Seu setor principal é [setor]. 
              [N] editais desse setor abriram nos últimos 30 dias na sua UF."
CTA: "Ver os editais abertos agora no seu setor →"
Contexto: "Empresas ativas no seu setor com filtro estratégico participam de 3× mais editais 
           com a mesma equipe. Veja as oportunidades que você está perdendo."
```

**Cenário B — Empresa iniciante (1-4 contratos ou recente):**
```
H1: "[Razão Social] — [N] contratos registrados / R$ [total]"
Subheadline: "Score B2G: INICIANTE. [N] editais do seu setor abriram no último mês."
CTA: "Descobrir quais editais sua empresa pode ganhar →"
Contexto: "Empresas do seu porte e setor que usam filtro estratégico desde o início 
           chegam ao 5º contrato em metade do tempo. Veja o que está aberto agora."
```

**Cenário C — Empresa sem histórico (0 contratos):**
```
H1: "[Razão Social] — Nenhum contrato público registrado"
Subheadline: "[N] editais do seu setor (detectado pelo CNAE) abriram nos últimos 30 dias."
CTA: "Ver editais para empresas como a sua →"
Contexto: "Não ter histórico não é impedimento — é ponto de partida. 
           MEI e microempresas têm vantagem legal em editais até R$80k. 
           Veja quantos abriram na sua UF este mês."
```

**Por que esse copy é não-substituível:** o CNAE da empresa detecta o setor automaticamente. O número de editais abertos é do datalake em tempo real. O score B2G é calculado pelo SmartLic. Isso não existe em nenhum outro lugar.

#### O que a página mostra

1. **Perfil da empresa** (BrasilAPI): razão social, CNAE, porte, UF
2. **Histórico de contratos públicos** (Portal da Transparência): últimos 10 contratos, órgão, valor, data, objeto
3. **Score de atividade B2G:** Ativa / Iniciante / Sem histórico
4. **Setores mais frequentes** dos contratos (keywords ou LLM)
5. **UFs onde ganhou contratos**
6. **Editais abertos no setor** (dado ao vivo do datalake)

#### Checklist de implementação — Backend

- [x] **Criar endpoint público** `GET /v1/empresa/{cnpj}/perfil-b2g`
  - Agrega: BrasilAPI + Portal da Transparência (contratos) + datalake (editais abertos)
  - Cache InMemory 24h (dados mudam pouco)
  - **Sem autenticação** (público)
  - CNPJ inválido → 400 + mensagem clara
  - Empresa não encontrada → 404 via BrasilAPI
- [x] **Criar `backend/routes/empresa_publica.py`**
- [x] **Testar:** 4 testes passando em `tests/test_calculadora.py` (TestEmpresaPublica)
- [x] **Aviso legal** na resposta: fontes públicas (CNPJ aberto + Portal da Transparência)

#### Checklist de implementação — Frontend

- [x] **Criar `frontend/app/cnpj/[cnpj]/page.tsx`** com ISR de 24h
  - `generateStaticParams()` vazio (SSR on-demand)
  - `revalidate = 86400`
- [x] **Criar `frontend/app/cnpj/page.tsx`** — landing com formulário de busca (`CnpjSearchForm.tsx`)
- [x] **Metadata dinâmica:** title, description, canonical, OG, Twitter (via `generateMetadata`)
- [x] **Schema markup:** `Organization` + `Dataset` + `BreadcrumbList`
- [x] **OG image dinâmico** com razão social + score via `/api/og`
- [x] **Score visual** (badge: Verde=Ativa, Amarelo=Iniciante, Cinza=Sem histórico)
- [x] **Tabela de contratos** (max 10)
- [x] **Contador de editais ao vivo** do setor detectado (dado do datalake)
- [x] **CTA contextual** por cenário A/B/C (copy implementado em `CnpjPerfilClient.tsx`)
- [x] **Adicionar `/cnpj`** ao sitemap.ts (priority 0.8)
- [x] **Link** no footer e menu "Ferramentas gratuitas" — Footer seção "Ferramentas" com Calculadora, CNPJ e Glossário
- [x] **Aviso legal** visível: dados de fontes públicas
- [x] **Analytics:** `cnpj_lookup` no Mixpanel com `{ setor_detectado, uf, total_contratos, score, clicked_cta }`
- [ ] **Commit:** `feat(seo): add public CNPJ B2G history tool at /cnpj/[cnpj]`

---

### P4 — Schema Markup Dataset nas Landing Setoriais

**Prioridade:** MÉDIA · **Esforço:** 1 dia · **Confirmação ativada:** 1 (visibilidade em AI Overviews)

> As páginas `/licitacoes/[setor]` já têm `WebPage + FAQPage` schema.
> Faltam `Dataset` e `HowTo` — os dois tipos que aumentam elegibilidade para
> AI Overviews e rich snippets em queries de dados.
>
> O blog programático já tem Article+FAQPage+Dataset+HowTo. Paridade necessária
> nas landing setoriais (ISR 6h — dados mais frescos).

#### Checklist de implementação

- [x] **Abrir `frontend/app/licitacoes/[setor]/page.tsx`**
- [x] **Localizar `buildJsonLd()`** (linha ~350)
- [x] **Adicionar `Dataset` schema:**
  ```ts
  if (stats && stats.total_open > 0) {
    jsonLd["@type"] = ["WebPage", "Dataset"];
    jsonLd["name"] = `Licitações de ${sector.name} — Dataset`;
    jsonLd["description"] = `${stats.total_open} licitações abertas de ${sector.name} no Brasil`;
    jsonLd["variableMeasured"] = "Total de licitações públicas abertas";
    jsonLd["measurementTechnique"] = "Agregação via PNCP — Portal Nacional de Contratações Públicas";
    jsonLd["temporalCoverage"] = "2024/..";
    jsonLd["spatialCoverage"] = "BR";
    jsonLd["distribution"] = [{
      "@type": "DataDownload",
      "encodingFormat": "application/json",
      "contentUrl": `https://smartlic.tech/api/v1/sectors/${sector.slug}/stats`
    }];
    jsonLd["isAccessibleForFree"] = true;
    jsonLd["creator"] = { "@type": "Organization", "name": "SmartLic", "url": "https://smartlic.tech" };
  }
  ```
- [x] **Adicionar `HowTo` schema:**
  ```ts
  const howToSchema = {
    "@context": "https://schema.org",
    "@type": "HowTo",
    "name": `Como encontrar licitações de ${sector.name}`,
    "step": [
      { "@type": "HowToStep", "name": "Acesse o SmartLic", "text": "Crie sua conta em 30 segundos — sem cartão" },
      { "@type": "HowToStep", "name": "Selecione seu setor e UF", "text": `Escolha ${sector.name} e as UFs de interesse` },
      { "@type": "HowToStep", "name": "Receba score de viabilidade", "text": "4 fatores avaliados automaticamente por edital" },
    ]
  };
  ```
- [ ] **Testar com Google Rich Results Test:** `https://smartlic.tech/licitacoes/engenharia`
- [ ] **Validar 3-4 setores diferentes** (spot check)
- [x] **Commit:** `seo: add Dataset+HowTo schema to /licitacoes/[setor] landing pages`

---

### P5 — Cases Públicos de Beta

**Prioridade:** MÉDIA · **Esforço:** 2-3 dias · **Confirmação ativada:** 2 + 3 ("isso funciona" + "isso é para mim")

> O repositório tem 40+ relatórios reais de beta com valores reais identificados.
> São prova social que fecha o ciclo de confiança: busca orgânica → case similar → trial.
>
> **Critério de rejeição de case:** sem número de resultado concreto → não publicar.
> "A empresa ficou satisfeita" não é case. "Identificou R$4,2M em contratos potenciais
> em 40 minutos de análise" é case.

#### Framework narrativo: Problema → Processo → Número Real

Cada case deve seguir exatamente essa estrutura em ~400 palavras:

```
TÍTULO: Como [Empresa/Perfil] encontrou R$ [X] em contratos 
        em [tempo] usando filtro estratégico

PROBLEMA (100 palavras):
[Empresa/Perfil de empresa] participava de [N] editais/mês no setor de [setor].
O processo de triagem ocupava [X horas] da equipe.
Dos editais analisados, [Y%] eram incompatíveis — mas só eram descartados depois
de horas de análise. A empresa não tinha visibilidade do que estava perdendo.

PROCESSO (150 palavras):
Em [data], rodou uma análise completa no SmartLic: setor [setor], UFs [lista], 
período de 10 dias. Em [tempo], o sistema:
- Identificou [N_total] editais publicados
- Descartou [N_desc] automaticamente (por modalidade, valor fora de range, geo)
- Pontuou os [N_restantes] com score de viabilidade 0-100
- Destacou [N_top] com score acima de 70 (compatíveis com o perfil)

RESULTADO (100 palavras):
Valor total de contratos identificados com viabilidade alta: R$ [X]
Editais que teriam sido perdidos sem o filtro: [N]
Tempo de triagem por semana reduzido: de [X] para [Y] horas
Insight mais valioso: [dado específico que a empresa não sabia antes]

CTA:
"Rode uma análise para o seu setor — 14 dias grátis, sem cartão →"
```

#### Checklist de curadoria (fase 1 — antes de implementar)

- [x] **Selecionar 5 cases** dos `docs/reports/`:
  - 1 Engenharia, 1 Construção, 1 Facilities, 1 Saúde ou TI, 1 anonimizado de destaque
- [x] **Extrair por case:** porte, setor, UF, N editais analisados, valor oportunidades, score médio, insight chave
- [ ] **Obter aprovação** dos betas (email simples):
  - Opção A: nome real + logo (máxima credibilidade)
  - Opção B: perfil anonimizado "Construtora de médio porte em SC" (zero risco)

#### Checklist de implementação — Frontend

- [x] **Criar `frontend/app/casos/page.tsx`** — listagem de cases
- [x] **Criar `frontend/app/casos/[slug]/page.tsx`** — case individual
- [x] **Metadata SEO por case:**
  ```ts
  title: `Como ${empresa} identificou R$ ${valor} em contratos de licitação em ${tempo} | SmartLic`
  description: `Case real: ${empresa} analisou ${totalEditais} editais com o SmartLic e encontrou 
                R$ ${valor} em contratos compatíveis. Score médio de viabilidade: ${score}/100.`
  ```
- [x] **Schema markup:** `Article` + `Review`
- [x] **Adicionar `/casos`** ao sitemap.ts (priority 0.8)
- [x] **Link "Casos de sucesso"** no menu de navegação principal e footer
- [x] **CTA em cada case:** "Rode uma análise para o seu setor" → `/signup?ref=case-{slug}`
- [x] **Link cruzado** nos artigos de blog do setor correspondente — BlogArticleLayout sidebar agora inclui link contextual para calculadora
- [ ] **Commit:** `feat(seo): add /casos public case studies section`

---

### P6 — Compartilhamento de Análise de Viabilidade

**Prioridade:** MÉDIA · **Esforço:** 3-4 dias · **Confirmação ativada:** 2 em loop viral (decisor vê antes do trial)

> Quando o analista compartilha o score de viabilidade via WhatsApp com o diretor,
> o diretor experimenta o SmartLic funcionando antes de qualquer trial.
> É o funil mais curto B2B: analista usa → compartilha com decisor → decisor converte.
>
> **KPI esperado:** 150 análises compartilhadas/mês × 20% de conversão do receptor = 30 trials virais.

#### Copy do OG image e da página pública

**OG Image (gerado dinamicamente):**
```
[Logo SmartLic — pequeno, canto superior direito]

Score de Viabilidade
[78]/100

"[Título do edital — truncado 60 chars]"
[Órgão] · [UF] · R$ [Valor]

Modalidade: [badge]  Prazo: [badge]  Valor: [badge]  Geo: [badge]
```

**Texto da página `/analise/[hash]`:**
```
H1: "Análise de Viabilidade: [Título do edital]"
Score: 78/100 — ALTA VIABILIDADE

BREAKDOWN DOS 4 FATORES:
Modalidade (30%): [score/10] — Pregão eletrônico. Alta competitividade, prazo curto.
Prazo (25%): [score/10] — 18 dias corridos. Adequado para proposta técnica.
Valor (25%): [score/10] — R$285k. Dentro do range histórico do setor em SP.
Geografia (20%): [score/10] — SP. UF de operação primária da empresa.

[Watermark sutil no rodapé:]
"Análise gerada pelo SmartLic · 14 dias grátis para analisar editais do seu setor"
→ CTA: "Analisar editais para o meu setor"
```

**Por que esse copy converte o receptor:** o decisor recebe um link com um número específico (78/100) e uma justificativa objetiva por 4 fatores. Não é uma opinião do analista — é uma avaliação sistêmica. O SmartLic se apresenta ao decisor no exato momento em que ele precisa tomar uma decisão. O CTA no rodapé aparece quando o interesse está no pico.

#### Checklist de implementação — Backend

- [x] **Criar tabela** `shared_analyses` no Supabase:
  ```sql
  CREATE TABLE shared_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hash TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES profiles(id),
    bid_id TEXT NOT NULL,
    bid_title TEXT NOT NULL,
    bid_organ TEXT,
    bid_value NUMERIC,
    bid_uf TEXT,
    viability_score INTEGER,
    viability_breakdown JSONB,
    sector_classification TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '30 days',
    view_count INTEGER DEFAULT 0
  );
  -- RLS: select aberto (público), insert requer auth
  ```
- [x] **Endpoint** `POST /v1/share/analise` (requer auth) → retorna `{ url }`
- [x] **Endpoint** `GET /v1/share/analise/{hash}` (público) → incrementa view_count, 404 se expirado

#### Checklist de implementação — Frontend

- [x] **Botão "Compartilhar análise"** em cada card de resultado no `/buscar`
  - Click → POST → copia URL para clipboard com toast "Link copiado!"
  - Mobile: Web Share API nativo se disponível
- [x] **Criar `frontend/app/analise/[hash]/page.tsx`** (ISR 1h)
  - Score de viabilidade com breakdown dos 4 fatores
  - OG image dinâmico com score e título
  - Watermark + CTA contextual (copy acima)
- [x] **Metadata dinâmica:**
  ```ts
  title: `Análise: ${bidTitle} — Score ${score}/100 | SmartLic`
  description: `Viabilidade ${score}/100 para "${bidTitle}" (${organ}). 
                4 fatores: modalidade, prazo, valor e geografia.`
  ```
- [x] **Schema markup:** `Review` com `ratingValue = score`
- [x] **Analytics:** `analysis_shared`, `analysis_viewed` no Mixpanel — ShareAnalysisButton + AnalysisViewTracker client island
- [ ] **Commit:** `feat(viral): add shareable bid analysis pages at /analise/[hash]`

---

### P7 — Expansão de Conteúdo — Empresas B2G Diretas

**Prioridade:** BAIXA-MÉDIA · **Esforço:** Contínuo (1-2 artigos/semana)

> O blog atual tem 40 artigos focados em consultorias. Existe lacuna para empresas B2G diretas
> (construtoras, clínicas, distribuidoras) que participam sem intermediários.
>
> Queries não cobertas: "como ganhar licitação de engenharia", "pregão eletrônico construção civil",
> "habilitação licitação empresa pequena", "CNPJ novo pode participar licitação"

#### Template de artigo 3-em-1 (obrigatório para novos artigos)

Todo artigo novo deve passar no checklist antes de ser publicado:

**Função 1 (útil para não-cliente):**
- [ ] Responde a pergunta específica do título sem exigir login ou trial
- [ ] Inclui pelo menos 1 dado público verificável (PNCP, Portal da Transparência, IBGE)
- [ ] Tem estrutura escaneável: H2s descritivos, 1 tabela, 1 lista

**Função 2 (desejável para prospect):**
- [ ] Inclui pelo menos 1 dado exclusivo do datalake SmartLic (número ao vivo ou histórico)
- [ ] Tem 1 comparativo "sem filtro vs com filtro" com números específicos
- [ ] O `BlogInlineCTA` ~40% do artigo usa copy contextual (não genérico "teste grátis"):
  ```
  // Exemplo para artigo sobre habilitação:
  ctaMessage="Há [N] editais de [setor] abertos agora. 
              Veja quais pedem os documentos que você já tem."
  ctaText="Ver editais compatíveis →"
  ```

**Função 3 (compartilhável por cliente ativo):**
- [ ] Título é autônomo (faz sentido sem contexto extra quando encaminhado pelo WhatsApp)
- [ ] Tem pelo menos 1 insight que causa reação ("não sabia disso") — dado contraintuitivo
- [ ] URL é compartilhável sem vergonha (slug descritivo, sem parâmetros)

#### Critério de rejeição de tema

Antes de escrever qualquer artigo, verifique:

1. **KD > 40?** → Não vale a pena (tempo demais para rankear sem autoridade de domínio)
2. **Intenção puramente informacional sem intenção de compra próxima?** → Backlog (priorizar fundo de funil)
3. **O artigo faz sentido publicado por qualquer concorrente?** → Rejeitar ou reescrever com dado exclusivo do datalake
4. **Não tem como incluir dado do PNCP/datalake?** → Baixa prioridade

#### Temas prioritários (intenção de compra próxima)

- [x] "Checklist completo de habilitação para licitação em 2026 (Lei 14.133)" — `checklist-habilitacao-licitacao-2026.tsx`
- [x] "Pregão eletrônico: guia passo a passo para primeira participação" — `pregao-eletronico-guia-passo-a-passo.tsx`
- [x] "Como calcular o preço de proposta para não perder dinheiro em licitação" — `como-calcular-preco-proposta-licitacao.tsx`
- [x] "MEI e Microempresa: vantagens e limites para participar de licitações" — `mei-microempresa-vantagens-licitacoes.tsx`
- [x] "SICAF: como se cadastrar e manter ativo em 2026" — `sicaf-como-cadastrar-manter-ativo-2026.tsx`
- [x] "Principais erros que desclassificam propostas — e como evitá-los" — `erros-desclassificam-propostas-licitacao.tsx`
- [x] "Impugnação de edital: quando e como contestar" — `impugnacao-edital-quando-como-contestar.tsx`
- [x] "Ata de Registro de Preços: estratégia de licitação sem comprar" — `ata-registro-precos-estrategia-licitacao.tsx`

#### Distribuição de cada artigo

- [ ] LinkedIn do fundador (post nativo, não link — dados do artigo adaptados para o formato)
- [ ] WhatsApp de grupos de licitações (com permissão dos admins)
- [ ] Resposta em fóruns: Licitações-e community, grupos Facebook "licitações públicas"

#### Infraestrutura de blog (melhorias independentes)

- [x] **RSS feed** — verificar se `/blog/rss.xml` está no sitemap
- [x] **Canonical tags** — confirmar que todas as 40 páginas têm `alternates.canonical`
- [x] **Internal linking audit** — BlogArticleLayout sidebar inclui `/calculadora`; `RelatedPages.tsx` expandido para 15×27 (era 5×5 hardcoded); ferramentas (calculadora, CNPJ) adicionadas como tipo 'ferramenta'; blog listing page tem seção "Ferramentas Gratuitas" cross-linking para `/calculadora`, `/cnpj`, `/glossario`; calculadora resultados linkam para `/blog/licitacoes/[setor]/[uf]` correspondente
- [ ] **Core Web Vitals** — LCP < 2.5s, CLS < 0.1 nas páginas programáticas (PageSpeed Insights)

---

## Parte 4 — Métricas de CAC Mínimo

> O tráfego orgânico é inútil se não converte. A tabela abaixo mede o que importa:
> custo por trial adquirido por canal, e taxa de conversão de trial para pago.
> Um canal com 10 trials/mês e 40% de conversão para pago é melhor que um canal
> com 100 trials/mês e 4% de conversão.

### Fórmula de CAC Orgânico

```
CAC orgânico por canal =
  (Horas de produção × custo/hora) + (Infra de hospedagem proporcional)
  ÷
  Número de pagantes adquiridos via esse canal/mês
```

Para o SmartLic (fase atual: pré-escala, custo de infra ~zero marginal por canal):
- CAC alvo geral: < R$200 por cliente pagante (LTV estimado R$2.400/ano Pro)
- CAC orgânico benchmark: R$50-100 (equivalente a 2-4h de produção de conteúdo por cliente)

### Taxas de conversão esperadas por touchpoint

| Touchpoint | Visitas/mês meta | Taxa visit→trial | Taxa trial→pago | Pagantes/mês |
|-----------|-----------------|-----------------|----------------|-------------|
| Calculadora `/calculadora` | 500 | 15% | 35% | ~26 |
| Ferramenta CNPJ `/cnpj` | 2.000 | 8% | 30% | ~48 |
| Blog (artigos B2G direto) | 3.000 | 3% | 30% | ~27 |
| Landing setorial `/licitacoes/[setor]` | 1.500 | 5% | 30% | ~23 |
| Análise viral `/analise/[hash]` | 600 | 12% | 40% | ~29 |
| Cases `/casos` | 400 | 10% | 40% | ~16 |

### Dashboard de acompanhamento mensal

> Verificar mensalmente: Google Search Console + Mixpanel + Stripe

> **⚠️ Correção de expectativa (Conselho CMO, 2026-04-05):** A meta de 30 trials orgânicos
> em 30 dias é agressiva demais dado o baseline atual (zero backlinks, 2/524 páginas indexadas,
> DA ≈ 0). O benchmark realista para mês 1 é **3-8 trials orgânicos**. A meta de 30 trials/mês
> é alcançável no **mês 3** com o playbook off-page (Parte 6) e distribuição (Parte 7) executados
> com disciplina. Metas desajustadas desmotivam — calibrar para o que o canal consegue entregar.

**Métricas de CAC (prioridade 1):**

| Métrica | Baseline | Meta 30 dias | Meta 90 dias |
|---------|----------|-------------|-------------|
| CAC orgânico geral (R$) | — | < R$200 | < R$100 |
| Trials via orgânico/mês | — | 3-8 *(realista)* | 30 *(mês 3 com off-page ativo)* |
| Trial-to-paid por canal (%) | — | > 25% | > 35% |
| Pagantes via orgânico/mês | — | 1-3 | 10-12 |
| MRR orgânico incremental | R$0 | R$400-1.200 | R$4.000-5.000 |

**Métricas de autoridade de domínio (prioridade 0 — desbloqueiam tudo):**

| Métrica | Baseline | Semana 1 | Mês 1 | Mês 3 |
|---------|----------|---------|-------|-------|
| Backlinks externos (GSC) | 0 | 5-8 (perfis + testimonials) | 10-20 | 40-60 |
| Domain Rating — Ahrefs (gratuito) | 0 | 3-5 | 10-15 | 20-25 |
| Páginas indexadas (GSC) | 2 | 20-30 (força-bruta GSC) | 50-100 | 350-450 |

> Verificar com **Ahrefs Webmaster Tools** (gratuito, cadastrar `smartlic.tech`): Domain Rating,
> backlinks novos, páginas indexadas. Não gastar com plano pago enquanto DR < 15.

**Métricas de funil (prioridade 2):**

| Métrica | Baseline | Meta 30 dias | Meta 90 dias |
|---------|----------|-------------|-------------|
| Impressões orgânicas/mês | 0 | 500-2.000 | 20.000-50.000 |
| Cliques orgânicos/mês | 0 | 50-200 | 1.000-2.000 |
| Cálculos na calculadora/mês | 0 | 50-100 | 300-500 |
| Consultas CNPJ/mês | 0 | 100-200 | 1.000-2.000 |
| Análises compartilhadas/mês | 0 | 20-30 | 100-150 |
| Trials via LinkedIn/mês | 0 | 5-10 | 20-30 |
| Indicações (referral)/mês | 0 | 0-2 | 10-20 |

**Day-3 Activation — o maior preditor de conversão trial→pago:**

> Dados de mercado (2026): usuários que chegam ao "aha moment" nos primeiros 3 dias do trial
> convertem 4× mais que usuários que chegam depois do Day-7. Definir e instrumentar esse evento
> é mais impactante que qualquer outra otimização de funil.

**"Aha moment" do SmartLic:** usuário fez ≥1 busca **E** viu análise de viabilidade de ≥1 edital.
Evento Mixpanel: `first_analysis_viewed` (já rastreado? verificar).

| Métrica | Meta | Ação se abaixo do target |
|---------|------|--------------------------|
| Day-3 activation rate | ≥ 60% | Revisar onboarding + email comportamental Day-3 (disparar quando NÃO voltou — não no dia 3 fixo) |
| Day-7 feature depth | ≥ 3 funcionalidades usadas | Email de dica de feature específica no Day-5 |
| DAU/MAU no trial | ≥ 25% | Alertas de novos editais (push/email) para trazer de volta |

**Checklist de instrumentação:**
- [ ] **Verificar evento `first_analysis_viewed`** existe no Mixpanel (ou criar)
- [ ] **Criar funil no Mixpanel:** `signup → first_search → first_analysis_viewed → trial_converted`
- [ ] **Monitorar Day-3 activation rate** semanalmente
- [ ] **Configurar email comportamental Day-3:** disparar para usuários que SE inscreveram há 2 dias e NÃO geraram evento `first_analysis_viewed`

**O número que mais importa:**
```
trial-to-paid por source (Stripe + Mixpanel UTM)
= Quantos dos trials que vieram de cada canal viraram clientes pagantes?
```

Se um canal tem alto volume de trial e baixo trial-to-paid → problema de qualificação (leads errados).
Se um canal tem baixo volume e alto trial-to-paid → amplificar (leads certos, escassez de topo).

---

## Parte 6 — Off-Page: Backlinks e Autoridade de Domínio

> **Diagnóstico CMO Advisory Board (2026-04-05):** O playbook técnico on-page está no top 5%
> para SaaS early-stage no Brasil — mas opera com uma perna só. A ausência de estratégia
> off-page neutraliza 80% do investimento técnico já feito. Com zero backlinks e DA próximo
> de zero, o Google não tem sinal externo para confiar nas 405 páginas programáticas.
> **Sem DA mínimo de 15-20, essas páginas ficam no limbo por 6-9 meses.**
>
> Esta seção cobre o que estava completamente ausente no playbook original.

### 6.1 — Perfis de Alta Autoridade (1-2h total, zero custo)

> Quick wins imediatos: cada perfil é 1 backlink legítimo de DA 60-98. Total de esforço: ~2h.
> Fazer na **Semana 1**, antes de qualquer outra iniciativa de link building.

| Plataforma | DA | Tipo de link | Tempo | Instrução |
|-----------|-----|-------------|-------|-----------|
| **Product Hunt** | 90 | Dofollow | 2h | Criar página do SmartLic. Agendar lançamento para terça ou quarta (maior engajamento). Categorias: Productivity, SaaS, GovTech |
| **G2** | 80 | Dofollow | 1h | Listagem gratuita. Requer 1 review — pedir a beta user. Categoria: Contract Management / Procurement |
| **Capterra** | 85 | Dofollow | 1h | Listagem gratuita. Categoria: Procurement Software |
| **Crunchbase** | 90 | Dofollow | 30min | Perfil da CONFENGE Avaliações e Inteligência Artificial LTDA + produto SmartLic |
| **LinkedIn Company Page** | 98 | Nofollow (alta autoridade) | 20min | Criar Company Page para SmartLic / CONFENGE se não existe |
| **ABStartups** | 55 | Dofollow | 30min | Diretório de startups brasileiras |
| **Distrito** | 60 | Dofollow | 30min | Diretório do ecossistema de startups |
| **BrazilLAB** | 45 | Dofollow | 30min | Diretório específico de GovTech Brasil |
| **StartupBase** | 50 | Dofollow | 20min | Diretório BR |

#### Checklists

> **Copy pronto para submissão:** `docs/seo/off-page-directories.md` contém taglines, descrições curtas/longas, screenshots necessárias e checklist por plataforma — basta copy-paste no cadastro.

- [ ] **Product Hunt:** criar conta, configurar página do SmartLic com tagline, screenshots, vídeo demo. Agendar para próxima terça ou quarta. _(copy em `docs/seo/off-page-directories.md`)_
- [ ] **G2:** criar listagem, solicitar review para 1 beta user via email, publicar.
- [ ] **Capterra:** criar listagem gratuita.
- [ ] **Crunchbase:** perfil CONFENGE + SmartLic com CNPJ, descrição, fundadores, estágio (seed/pre-seed).
- [ ] **LinkedIn Company Page:** criar se não existe. Completar 100% do perfil (logo, banner, about, website).
- [ ] **ABStartups:** cadastrar em `membros.abstartups.com.br`.
- [ ] **Distrito:** cadastrar em `distrito.me/startups`.
- [ ] **BrazilLAB GovTech:** submeter em `brazillab.org.br`.
- [ ] **Verificar backlinks após 7 dias** usando Ahrefs Webmaster Tools (gratuito — cadastrar `smartlic.tech`).

---

### 6.2 — Testimonial Link Building

> Taxa de sucesso: 40-60% para ferramentas DevTool que mantêm página de cases/testimonials.
> Cada depoimento aceito = backlink de DA 60-92+ com contexto técnico altamente relevante.
> Esforço: ~30min por email. Retorno potencial: 4 backlinks de alta autoridade.

**Template de email (adaptar por ferramenta):**

```
Assunto: Depoimento sobre [ferramenta] — SmartLic (startup GovTech BR)

Olá equipe [ferramenta],

Construímos o SmartLic (smartlic.tech) com [ferramenta] para [resultado específico].
[1-2 linhas sobre o caso de uso técnico concreto]

Seria um prazer escrever um depoimento mais detalhado para vocês, 
se tiverem interesse em cases da comunidade de usuários.

Att,
[Fundador] — SmartLic
```

| Ferramenta | DA | Copy do depoimento |
|-----------|----|--------------------|
| **Supabase** | 85 | "Construímos o SmartLic com Supabase + RLS para processar 40K+ editais públicos do PNCP com segurança multi-tenant. O Auth + Row Level Security reduziu nosso tempo de desenvolvimento de autorização de semanas para dias." |
| **Railway** | 75 | "O SmartLic roda backend FastAPI + worker ARQ no Railway — o deploy monorepo com watch patterns por subdiretório foi exatamente o que precisávamos para separar web e worker. Zero config de infra." |
| **Resend** | 65 | "Usamos o Resend para todos os emails transacionais do SmartLic (trials, onboarding, alertas de edital). A API foi integrada em 30 minutos — nenhuma outra ferramenta que testamos chegou perto disso." |
| **Vercel/Next.js** | 92 | "O SmartLic tem 405 páginas programáticas com ISR e dados ao vivo do PNCP — Next.js App Router + ISR tornou isso viável sem overhead de infra." |

> **Templates prontos:** `docs/seo/testimonial-emails.md` traz 4 emails personalizados (Supabase, Railway, Resend, Vercel) com subject line, corpo, métricas reais do SmartLic, contatos de DevRel e cadência de follow-up.

- [ ] **Email para Supabase** — `partners@supabase.io` ou via formulário de cases no site _(template em `docs/seo/testimonial-emails.md`)_
- [ ] **Email para Railway** — `hello@railway.app` ou via Discord da comunidade Railway
- [ ] **Email para Resend** — `team@resend.com`
- [ ] **Email para Vercel** — via formulário de cases em `vercel.com/enterprise`
- [ ] **Acompanhar respostas em 2 semanas** — se não houver retorno, tentar via Twitter/X ou LinkedIn dos fundadores

---

### 6.3 — Digital PR: Relatório "Panorama Licitações Brasil 2026 T1"

> O SmartLic tem um ativo único: dados reais de 40K+ editais do PNCP processados.
> Isso é pauta de imprensa. Nenhum concorrente tem. Um relatório de dados original
> bem distribuído gera 10-15 backlinks em portais de DA 40-80+ — tudo gratuito.

**Conteúdo do relatório (dados já existem no `pncp_raw_bids`):**

- Top 10 setores por volume de editais publicados (jan-mar 2026)
- UFs com maior crescimento de compras públicas vs mesmo período 2025
- Distribuição de modalidades: impacto da Lei 14.133 (pregão × concorrência × inexigibilidade)
- Valor médio por edital por setor (P25, P50, P75)
- Sazonalidade: quais meses concentram mais editais

**Formato:** PDF de 8-10 páginas com gráficos + landing page gated em `/relatorio-2026-t1` (email para download).

#### Checklist de produção

> **Outline completo:** `docs/seo/panorama-2026-t1-outline.md` traz 8 seções, queries SQL prontas contra `pncp_raw_bids`, design da landing, lista de 20 jornalistas/redações BR e copy de pitch.

- [ ] **Rodar queries no Supabase** para extrair os 5 conjuntos de dados acima _(SQL pronto em `docs/seo/panorama-2026-t1-outline.md`)_
- [ ] **Gerar gráficos** (pode ser com Python/matplotlib ou Google Sheets)
- [ ] **Escrever o relatório** — 8-10 páginas, tom executivo, fontes citadas (PNCP, Lei 14.133)
- [ ] **Criar landing page** `/relatorio-2026-t1` com formulário de download (email obrigatório)
- [ ] **PDF gerado** e hospedado no Supabase Storage

#### Checklist de distribuição

- [ ] **Sebrae Startups** — submeter em `sebraestartups.com.br` (DA 60+, contexto B2B Brasil)
- [ ] **Featured.com** (novo HARO) — cadastrar em `featured.com` como especialista em licitações públicas e compras governamentais. Responder queries de jornalistas buscando dados sobre mercado B2G.
- [ ] **LinkedIn post** do founder com 3-5 dados do relatório no corpo do post (não pedir clique — mostrar valor no próprio post). Link para landing no final.
- [ ] **Email para redações:** Estadão PME, Exame, Valor Econômico, Agência Brasil, Governo Digital. Assunto: "Dados exclusivos: licitações públicas no Brasil em 2026 — relatório SmartLic"
- [ ] **GovTech Brasil** — portais especializados: govtech.com.br, Poder360 (tecnologia pública), Jota (licitações)
- [ ] **Monitorar menções** via Google Alerts: "SmartLic", "panorama licitações 2026"

---

### 6.4 — Diretórios, Fóruns e Comunidade

> Links de fóruns são nofollow, mas geram tráfego qualificado direto e sinais de menção
> de marca — importantes para E-E-A-T. O objetivo aqui não é DA, é presença onde o ICP está.

**Google Meu Negócio:**
- [ ] **Criar perfil** para CONFENGE Avaliações e Inteligência Artificial LTDA com endereço, CNPJ, categoria "Software"
- [ ] **Adicionar SmartLic** como produto/serviço no perfil
- Impacto: aparece em buscas de marca + credibilidade E-E-A-T

**Fóruns de licitação (contribuição útil, não spam):**
- [ ] **LicitaNet** (forum.licitanet.com.br) — responder dúvidas com links contextuais para artigos do blog
- [ ] **Grupos Facebook "Licitações Públicas"** e "Pregão Eletrônico BR" — contribuir com dados do PNCP, linkar para calculadora quando relevante
- [ ] **Reddit r/empreendedorismo** — post sobre análise de licitações com dados exclusivos

**Comunidades B2G:**
- [ ] **Slack da Abstartups** — canal de govtech/b2g
- [ ] **WhatsApp de gestores de licitação** — entrar em grupos como participante ativo (compartilhar artigos relevantes, nunca spam)

**Google Business menções:**
- [ ] **Falar em webinars de licitação** (gratuitos, qualquer formato) — gera autoridade E-E-A-T + menções de marca

---

## Parte 7 — Distribuição: Produto como Canal

> O maior erro de SaaS pré-tração: esperar o SEO orgânico amadurecer (3-6 meses) sem ter
> outros canais ativos. Nos primeiros 60 dias, LinkedIn do founder + produto como distribuição
> devem ser os canais **primários** de aquisição. SEO é o canal de **longo prazo** que
> amortiza o custo. Os dois precisam operar em paralelo, não em sequência.

### 7.1 — Ativação Real do P6: Análise Compartilhável

> O P6 foi implementado (rotas `/analise/[hash]`, botão de compartilhamento, OG metadata),
> mas o mecanismo viral não está **ativado** — não há incentivo claro de compartilhamento,
> nem OG image dinâmica que torna o preview social irresistível.

**O funil viral do P6:**
```
Usuário analisa edital → vê score 78/100 → compartilha link no WhatsApp com o diretor
→ diretor clica → vê análise completa com breakdown dos 4 fatores
→ tenta ver outros editais → precisa criar conta → trial começado
```

**OG image especificado (gerar via `/api/og?hash=[hash]`):**
```
[Logo SmartLic — canto superior direito, 40px]

Score de Viabilidade
[78]/100   [barra de progresso visual]

"Pregão Eletrônico nº 001/2026 — Secretaria de TI..."  [truncado 55 chars]
Ministério da Saúde · SP · R$ 285.000

Modalidade ✅  Prazo ✅  Valor ✅  Geo ⚠️
```

**OG text (meta description da página compartilhada):**
```
"Análise de viabilidade: [título do edital] — Score [N]/100. 
4 fatores avaliados: modalidade, prazo, valor e geografia. 
Gerado pelo SmartLic."
```

#### Checklist de ativação

- [x] **OG image dinâmica** (2026-04-05) — `/api/og?type=analise&score=...&cnpj=...&setor=...&data=...` gera imagem com score colorido (verde/amarelo/vermelho), CNPJ, setor e data. `generateMetadata()` em `app/analise/[hash]/page.tsx` injeta OG + Twitter tags dinâmicas.
- [x] **Botão "Compartilhar no LinkedIn"** (2026-04-05) — novo componente genérico `components/share/ShareButtons.tsx` (LinkedIn + WhatsApp + X/Twitter + copy) integrado em `/analise/[hash]` e `BlogArticleLayout`. Tracking via `trackEvent('share_clicked', { channel, source: 'analise', hash, viability_score })`.
- [x] **Botão "Copiar link"** com toast visual (2026-04-05) — parte do `ShareButtons`, feedback "Copiado!" inline.
- [ ] **Watermark + CTA** no rodapé da página `/analise/[hash]`: "Análise gerada pelo SmartLic · 14 dias grátis para analisar editais do seu setor → [CTA button]"
- [ ] **Email de ativação de compartilhamento** — no Day-3, se usuário não compartilhou nenhuma análise, enviar: "Seu score de viabilidade pode ajudar um colega a decidir mais rápido. Compartilhe uma análise."
- [x] **Verificar analytics** (2026-04-05) — evento `share_clicked` disparado por canal (LinkedIn/WhatsApp/Twitter/copy) via `trackEvent` consent-gated.

**KPI esperado:** 50 análises compartilhadas/mês → 20% de conversão do receptor = 10 trials/mês só por este canal. CAC: zero.

---

### 7.2 — LinkedIn do Founder como Canal Primário (60 primeiros dias)

> LinkedIn é o canal de menor fricção para atingir gestores B2G no Brasil. Um post com dado
> do PNCP atinge exatamente o ICP (compradores de SaaS B2G, consultores de licitação,
> donos de empresas que participam de pregões). Custo: 30-45min por post.

**Cadência: 3 posts/semana**

| Tipo de post | Frequência | Formato | Link |
|-------------|-----------|---------|------|
| Dado do PNCP (números reais) | 1×/semana | "Sabia que X editais de [setor] abriram só em [UF] em [mês]?" + dado + contexto | → `/blog/licitacoes/[setor]/[uf]` |
| Caso de uso prático | 1×/semana | "Como [perfil de empresa] encontrou [resultado] em [tempo]" | → `/casos/[slug]` |
| Reflexão sobre mercado B2G | 1×/semana | Opinião sobre Lei 14.133, tendências, erros comuns | → artigo do blog |

**Regras de formato LinkedIn (para alcance máximo):**
- Primeira linha: hook com número ou pergunta (exibida sem expandir)
- Sem link no corpo do post — link apenas no primeiro comentário (algoritmo do LinkedIn penaliza links no corpo)
- 3-5 linhas com espaçamento duplo (leitura mobile)
- Encerrar com pergunta para engajamento ("Você já analisou quantos editais foram perdidos no seu setor esse mês?")

**Meta de conexões:**
- [ ] **Semana 1:** conectar com 50 gestores B2G (consultores de licitação, diretores comerciais de empresas que participam de pregões)
- [ ] **Mês 1:** 500 novas conexões relevantes
- [ ] **Mês 3:** 5.000 conexões relevantes no nicho B2G

**Checklists por semana:**

> **Calendário editorial 4 semanas pronto:** `docs/seo/linkedin-editorial-4w.md` traz 12 posts completos (3/semana × 4 semanas) com hooks, corpo, CTAs, hashtags e dados do PNCP a validar. Progressão: educação → dados exclusivos → cases/contrarian → soft pitch.

- [ ] **Semana 1:** 3 posts publicados + conexões enviadas _(posts prontos em `docs/seo/linkedin-editorial-4w.md`)_
- [ ] **Semana 2:** 3 posts + engajamento em posts de outros do nicho
- [ ] **Semana 3:** 3 posts + primeiro post sobre resultado de beta user (com permissão)
- [ ] **Mês 1:** avaliar qual tipo de post teve mais engajamento e dobrar esse formato

---

### 7.3 — YouTube Shorts / Reels

> YouTube é o segundo maior mecanismo de busca do mundo. Vídeos sobre "como usar PNCP",
> "encontrar licitações de [setor]", "pregão eletrônico tutorial" têm audiência real e
> competição quase nula. O YouTube indexa vídeos no Google em horas — cada vídeo é mais
> uma URL no grafo de links com âncora para o SmartLic.

**Formato padrão (30-60 segundos):**
```
Título: "Como encontrar editais de [setor] em [UF] em 30 segundos"
Abertura: "Vou te mostrar como achar todos os pregões de [setor] em [UF] agora"
Demonstração: screen recording do SmartLic fazendo a busca (sem narração complexa)
Resultado: mostrar os editais filtrados com score de viabilidade
CTA final: "Link na bio para 14 dias grátis"
```

**Produção:**
- Screen recording: OBS Studio (gratuito) ou Loom
- Edição: DaVinci Resolve (gratuito) ou CapCut
- Tempo total por vídeo: 15-20 minutos

**Checklist:**
- [ ] **Canal YouTube** criado para SmartLic (ou conta pessoal do founder)
- [ ] **2 vídeos/semana** publicados como Shorts (< 60s) ou vídeos normais (2-5min para tutoriais)
- [ ] **Título SEO-first:** incluir "[setor] licitação [UF] 2026" para ranquear nas buscas do YouTube
- [ ] **Descrição com link** para a página programática correspondente (`/blog/licitacoes/[setor]/[uf]`)
- [ ] **Monitorar** quais vídeos geram cliques para o site via UTM `?utm_source=youtube`

---

### 7.4 — Programa de Referral Estruturado

> Dados de mercado (2026): usuários indicados têm CAC 0, LTV 16% maior, e churn 37% menor
> que usuários adquiridos por outros canais. Em B2B de nicho, a indicação entre pares
> (consultor indica para outros consultores) é o canal de maior qualidade.

**Mecânica:**
```
Usuário indica → amigo recebe link com 7 dias extras de trial
Quando amigo converte → quem indicou ganha 1 mês grátis
```

**Implementação:**
- Cada usuário tem código único `/indicar?ref=[user_id_hash]`
- Dashboard de indicações: "Você indicou [N] amigos. [M] converteram. [X] meses grátis acumulados."
- Landing page `/indicar` explicando a mecânica

**Ativação do email de referral:**
- Enviar no **Day-7 do trial** (momento de maior engajamento pré-conversão, não no último dia)
- Subject: "Você ganha 1 mês grátis por cada amigo que converter"
- Copy: mencionar o valor encontrado pelo usuário no trial ("Você encontrou R$[X] em editais compatíveis na última semana. Imagine o que um colega do seu setor poderia fazer com isso.")

**Checklist:**
- [x] **Página `/indicar`** criada com mecânica explicada (2026-04-05) — hero, código único, botão copy de link de share, stats (indicados/convertidos/créditos). Arquivo: `frontend/app/indicar/page.tsx`.
- [x] **Código único por usuário** gerado no backend (2026-04-05) — função SQL `generate_referral_code()` (8 chars alfanumérico), criado on-demand pelo endpoint `GET /v1/referral/code`. Tabela: `supabase/migrations/20260405100000_referrals.sql`.
- [x] **Dashboard de indicações** (2026-04-05) — stats 3-card em `/indicar` via `GET /v1/referral/stats` (total_signups, total_converted, credits_earned_months).
- [ ] **Email Day-7** configurado na sequência de onboarding (Resend + template) — templates criados (`backend/templates/emails/referral_welcome.py` + `referral_converted.py`) mas disparo Day-7 ainda precisa ser plugado na sequência de onboarding existente.
- [x] **Webhook Stripe** para creditar mês grátis automaticamente (2026-04-05) — `customer.subscription.created` roteado para `_handle_subscription_created` → `_credit_referral_conversion`: lê `metadata.referral_code`, marca registro como `converted`, estende `trial_end` do referrer via `stripe.Subscription.modify(..., proration_behavior='none')`, dispara email. Arquivo: `backend/webhooks/handlers/subscription.py`.
- [x] **Fluxo signup com `?ref=CODE`** (2026-04-05) — `app/signup/page.tsx` persiste código em localStorage, chama `/api/referral/redeem` após signup bem-sucedido, limpa storage. Não bloqueia signup em falha.
- [x] **Testes backend** — `backend/tests/test_referral.py` com 8 tests (code generation, stats, redeem, auth mock via `dependency_overrides`), 100% pass.
- [x] **Aplicar migration** (2026-04-05) — aplicada automaticamente pelo `deploy.yml > Apply Pending Migrations` (23s) após push do commit `68bd0a75`. Validação via `supabase db query --linked`: tabela `public.referrals` com 7 colunas, `rls_enabled=true`, 3 policies (`referrals_select_own`, `referrals_insert_own`, `referrals_service_all`), função `generate_referral_code()` retornando código `YLYJGODJ` (8 chars alfanuméricos).
- [ ] **Verificar rastreamento** via Mixpanel: eventos `referral_shared`, `referral_signed_up`, `referral_converted`

---

## Parte 5 — Anti-Patterns

### Anti-patterns de copy (novos nesta versão)

**Copy substituível — rejeitar sempre**
Se o texto faz sentido com qualquer outro nome de produto, foi rejeitado. Testar: substitua "SmartLic" por "Licitabot" ou "EditalFácil" — se ainda fizer sentido, reescrever com dado exclusivo do datalake ou feature específica.

**Conteúdo de uma só função — rejeitar**
Artigo que é útil mas não desejável: não converte.
Artigo que é desejável mas não compartilhável: não amplifica.
Artigo que é compartilhável mas não útil: não fideliza.
Os três ou não publica.

**Número sem fonte — rejeitar**
"3× mais rápido", "clientes satisfeitos" sem fonte = afirmação que o usuário não pode verificar = zero credibilidade. Todo número precisa de: (a) como foi calculado ou (b) fonte pública verificável.

### Anti-patterns técnicos

- **Não criar mais artigos antes de corrigir o sitemap (P0).** Conteúdo não indexado é investimento sem retorno.
- **Não competir em "como participar de licitação"** como keyword primária — KD alto, intenção informacional pura (ainda não compra).
- **Não fazer ads** antes de validar conversão orgânica (unit economics desconhecidos — você pagaria para descobrir que a taxa de conversão é 2%?).
- **Não lançar calculadora sem dados reais** do datalake — calculadora com números genéricos é igual à concorrência e perde toda a vantagem injusta.
- **Não publicar cases sem número de resultado** — "ficou satisfeito" não é case, é depoimento. Sem R$ ou N editais ou horas economizadas → não publicar.
- **Não construir P2/P3 antes de ter P0 e P1 feitos** — fundação antes de conversão.
- **Não otimizar para volume de tráfego.** Um artigo com 200 visitas e 15% de conversão para trial vale mais que 10 artigos com 2.000 visitas cada e 0,3% de conversão.

### Anti-patterns de off-page e distribuição (adicionados 2026-04-05)

> Estes anti-patterns foram identificados pelo Conselho CMO Advisory Board ao diagnosticar
> que o playbook original cobria excelentemente on-page mas ignorava completamente off-page.

- **Não criar mais páginas sem antes conseguir backlinks.** Com zero backlinks e DA ≈ 0, cada nova página vai para o mesmo limbo das 405 existentes. O gargalo é autoridade, não volume de conteúdo. Fazer as 9 ações da seção 6.1 (perfis gratuitos) antes de publicar qualquer novo artigo.

- **Não tratar SEO como único canal de aquisição nos primeiros 60 dias.** SEO B2B SaaS amadurece em 3-6 meses. Nos primeiros 60 dias, LinkedIn do founder + P6 compartilhável + comunidades B2G devem ser os canais primários. SEO complementa, não lidera ainda.

- **Não comprar backlinks PBN (Private Blog Network).** O Google December 2025 Core Update penalizou link schemes com severidade histórica. Um backlink legítimo do Product Hunt (DA 90) vale mais que 100 links de PBN. Risco: penalidade manual que apaga anos de trabalho de SEO.

- **Não focar em keywords KD > 40 com DA < 15.** "Software de licitações" (KD 55+) não ranqueia com domínio novo. Focar em long-tail das páginas programáticas (KD < 10): "editais de engenharia civil Santa Catarina 2026", "pregão TI prefeitura Rio Grande do Sul". É onde o tráfego qualificado de nicho vive.

- **Não fazer A/B test de duração de trial com < 50 signups/mês.** Sem significância estatística, qualquer resultado é ruído. Com 50 signups/mês no mesmo canal, o teste A/B levaria 3-4 meses para ter confiança de 95%. Alternativa: trocar para 7 dias diretamente (dados de mercado de 40.4% vs 30.6% de conversão são suficientemente robustos) e monitorar conversão total.

- **Não confundir DA/DR alto de diretório com link de qualidade editorial.** Links de perfis (Product Hunt, G2, Capterra) têm DA alto mas são nofollow ou de baixo peso editorial. Valem pela tração inicial de autoridade e pelo tráfego qualificado direto. O objetivo de médio prazo são links editoriais (portais de notícias, blogs técnicos de licitação) — que vêm via digital PR (seção 6.3).

- **Não esperar ter "conteúdo perfeito" para começar o LinkedIn.** Posts imperfeitos publicados hoje valem mais que posts perfeitos publicados em 30 dias. O algoritmo do LinkedIn favorece consistência e engajamento, não polimento.

---

## Registro de Operações — Indexação GSC (2026-04-04/05)

### Contexto: por que foi necessário fazer isso manualmente

Em 2026-04-04, ao verificar o status de indexação do smartlic.tech no Google Search Console, foi identificado que **apenas 2 de 524 páginas estavam indexadas**. O GSC reportava "21 páginas encontradas no sitemap" — normal para uma propriedade com 1 dia de existência — mas a fila de indexação orgânica do Googlebot para sites novos sem backlinks pode levar semanas.

**Duas causas raiz identificadas:**

#### Causa 1 — Site novo, sem histórico de autoridade
O domínio `smartlic.tech` foi adicionado ao GSC em 2026-04-04. Sites sem backlinks externos e sem histórico de crawl ficam na fila de baixa prioridade do Googlebot. Sem uma solicitação explícita via URL Inspection, o Google pode levar 2-6 semanas para indexar as primeiras páginas.

A solicitação manual via GSC URL Inspection coloca a URL na **fila prioritária de crawl** (geralmente processada em 24-72h), acelerando o início do processo de indexação.

#### Causa 2 — Cache-Control: private em todas as páginas (impedimento a CDN + crawl eficiente)

O `frontend/app/layout.tsx` (linha 132) contém:
```typescript
const nonce = (await headers()).get("x-nonce") ?? ""
```

Esta chamada a `headers()` — uma API dinâmica do Next.js App Router — força **toda a árvore de renderização** a entrar em modo dinâmico. O Next.js automaticamente define `Cache-Control: private, no-store` em respostas com renderização dinâmica, **sobrescrevendo qualquer header definido no middleware**.

Consequência: mesmo com a correção do middleware (`middleware.ts`, commit `ae013199`) que define `Cache-Control: public, s-maxage=3600` para rotas públicas, o Next.js sobrescreve isso na camada de renderização. O Cloudflare CDN recebe `Cache-Control: private` e registra `cf-cache-status: DYNAMIC` — sem caching, sem TTFB otimizado, sem crawl budget eficiente.

**Trade-off arquitetural documentado:**
- CSP nonce-based (`DEBT-108`) = segurança máxima (elimina `unsafe-inline`/`unsafe-eval`)
- Mas: `headers()` no root layout = dynamic rendering obrigatório = `Cache-Control: private` em toda a árvore
- Solução definitiva futura: separar o nonce em um Server Component isolado que não envolva o layout inteiro, ou migrar para CSP hash-based para scripts estáticos

**Impacto no SEO:** sem CDN caching, cada request do Googlebot bate no Railway diretamente. Crawl budget é consumido mais rapidamente, TTFB é maior (Railway cold start ~800ms vs CDN edge ~50ms), o que pode reduzir a frequência de recrawl.

---

### O que foi feito: solicitação de indexação via GSC URL Inspection

Em 2026-04-05, foram solicitadas manualmente indexações para as 10 URLs de maior valor comercial e de autoridade via a ferramenta de Inspeção de URL do Google Search Console. O processo foi automatizado via Playwright (browser automation).

**Padrão de automação estabelecido:**
1. Navegar para `https://search.google.com/search-console?resource_id=https://smartlic.tech/`
2. Tirar snapshot depth-6 para capturar `combobox [ref=e24]`
3. `browser_type` no combobox com a URL completa + `submit=true`
4. JS evaluate: clicar em `SPAN` com texto `'Solicitar indexação'` (children.length === 0)
5. Aguardar texto `'URL foi adicionado'` na página
6. JS evaluate: clicar no botão `'Dispensar'`
7. Navegar de volta para a visão geral e repetir

**URLs submetidas em 2026-04-05:**

| # | URL | Tipo | Resultado |
|---|-----|------|-----------|
| 1 | `https://smartlic.tech/blog` | Hub de conteúdo | ✅ Indexação solicitada |
| 2 | `https://smartlic.tech/blog/como-aumentar-taxa-vitoria-licitacoes` | Artigo blog P7 | ✅ Indexação solicitada |
| 3 | `https://smartlic.tech/blog/licitacoes-engenharia-2026` | Artigo blog P7 | ✅ Indexação solicitada |
| 4 | `https://smartlic.tech/blog/licitacoes-ti-software-2026` | Artigo blog P7 | ✅ Indexação solicitada |
| 5 | `https://smartlic.tech/blog/pncp-guia-completo-empresas` | Artigo blog P7 | ✅ Indexação solicitada |
| 6 | `https://smartlic.tech/blog/como-participar-primeira-licitacao-2026` | Artigo blog P7 | ✅ Indexação solicitada |
| 7 | `https://smartlic.tech/glossario` | Ferramenta de autoridade | ✅ Indexação solicitada |
| 8 | `https://smartlic.tech/calculadora` | Ferramenta de conversão P2 | ✅ Indexação solicitada |
| 9 | `https://smartlic.tech/licitacoes` | Landing hub setorial | ✅ Indexação solicitada |
| 10 | `https://smartlic.tech/features` | Página de produto | ✅ Indexação solicitada |

**Nota:** O GSC tem limite de ~10-12 solicitações manuais por dia por propriedade. Para as 524 páginas restantes, a indexação ocorrerá via crawl orgânico a partir das páginas indexadas (link graph) + resubmissão do sitemap.

---

### Próximos passos técnicos pós-indexação

**Imediato (24-72h):**
- [ ] Verificar no GSC → Cobertura → Válidas se as 10 URLs aparecem como indexadas
- [ ] Se alguma URL aparecer como "Descoberta — aguardando indexação por mais de 7 dias", reinvestigar (pode ser problema de renderização ou conteúdo fino)

**Curto prazo (1-2 semanas):**
- [ ] Após as 10 URLs indexadas, submeter próximo lote: `/sobre`, `/pricing`, `/ajuda`, `/termos`, `/privacidade`
- [ ] Investigar se `/licitacoes/[setor]` (landing setoriais) estão sendo descobertas via sitemap
- [ ] Monitorar GSC → Desempenho para primeiras impressões orgânicas

**Médio prazo (1 mês):**
- [ ] Resolver `Cache-Control: private` — refatorar nonce para não usar `headers()` no root layout. Opções:
  - Mover nonce para `<head>` via `generateMetadata` (não bloqueia streaming)
  - Usar CSP hash-based para scripts estáticos (elimina necessidade de nonce por request)
  - Criar wrapper Server Component que isola o `headers()` call sem propagar dynamic rendering para o layout inteiro
- [ ] Após fix de cache: verificar Cloudflare Analytics para confirmar `cf-cache-status: HIT` em páginas públicas
- [ ] Construir backlinks iniciais: submeter para Product Hunt, directories B2B SaaS brasileiros, mencionar em fóruns de licitação

**Anti-pattern a evitar:** não submeter todas as 524 URLs de uma vez manualmente. O GSC tem limite diário e URLs programáticas (setor×UF) devem ser descobertas via sitemap + crawl orgânico para demonstrar freshness real ao Google.
- **Não medir sucesso por impressões ou posição de keyword.** A posição não paga o servidor. O trial-to-paid paga.

---

## Registro de Operações — Execução Paralela Multi-Frente (2026-04-05)

Execução simultânea de 5 frentes atacando as ações de maior ROI ainda não executadas, combinando implementação técnica (Frentes 1-4) e geração de artefatos prontos para execução manual (Frente 5). Paralelismo real via subagentes isolados; reconciliação de conflitos em arquivos compartilhados (`SchemaMarkup.tsx`, `sitemap.ts`) feita por delta mínimo aditivo.

### Frente 1 — Viralização P6 (OG dinâmica + ShareButtons)
**Arquivos criados:** `frontend/components/share/ShareButtons.tsx`
**Arquivos modificados:** `frontend/app/api/og/route.tsx`, `frontend/app/analise/[hash]/page.tsx`, `frontend/app/components/BlogArticleLayout.tsx`, `frontend/components/blog/SchemaMarkup.tsx` (+ pageType `analise`)
**Resultado:** OG image dinâmica por análise (score colorido, CNPJ, setor, data), botões de compartilhamento (LinkedIn/WhatsApp/X/copy) com tracking `share_clicked` consent-gated, schema Article. Destrava o funil viral P6 → 7.1.

### Frente 2 — Programa de Referral (7.4)
**Arquivos criados:** `supabase/migrations/20260405100000_referrals.sql`, `backend/routes/referral.py`, `backend/templates/emails/referral_welcome.py`, `backend/templates/emails/referral_converted.py`, `backend/tests/test_referral.py`, `frontend/app/indicar/page.tsx`, `frontend/app/api/referral/{code,stats,redeem}/route.ts`
**Arquivos modificados:** `backend/startup/routes.py`, `backend/webhooks/stripe.py`, `backend/webhooks/handlers/subscription.py`, `frontend/app/signup/page.tsx`
**Resultado:** Tabela `referrals` + RLS, endpoints `GET /v1/referral/code|stats` + `POST /v1/referral/redeem`, roteamento `customer.subscription.created` → crédito automático (`trial_end +30d` via `stripe.Subscription.modify`), signup aceita `?ref=CODE` via localStorage. **Tests 8/8 pass.** Pendências: `supabase db push` (manual), plugar email Day-7 na sequência de onboarding.

### Frente 3 — Gaps técnicos SEO
**Arquivos criados:** `frontend/components/seo/BreadcrumbNav.tsx`, `frontend/lib/seo.ts`, `frontend/app/ajuda/faqData.ts`, `.github/workflows/indexnow.yml`
**Arquivos modificados:** `frontend/app/ajuda/page.tsx` + `AjudaFaqClient.tsx`, `frontend/app/components/ContentPageLayout.tsx`, `frontend/app/components/GoogleAnalytics.tsx`, 4× guias `/como-*/page.tsx`, `frontend/app/planos/page.tsx`, `frontend/app/planos/obrigado/ObrigadoContent.tsx`, `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx`, `frontend/components/blog/SchemaMarkup.tsx` (+ pageType `faq`)
**Resultado:** FAQPage JSON-LD em `/ajuda`, BreadcrumbList centralizado em 4 guias (remove JSON-LD inline duplicado), GA4 ecommerce (`trackViewItem`/`trackBeginCheckout`/`trackPurchase` currency BRL) em `/planos` + `/planos/obrigado`, GitHub Action IndexNow pós-deploy (diff `HEAD~1..HEAD`), freshness label visível em páginas setor×UF.

### Frente 4 — pSEO tier 2 (cidades)
**Arquivos criados:** `frontend/lib/cities.ts` (46 cidades em 15 UFs), `frontend/app/blog/licitacoes/cidade/[cidade]/page.tsx`
**Arquivos modificados:** `frontend/app/sitemap.ts` (+46 URLs), `frontend/components/blog/SchemaMarkup.tsx` (+ pageType `cidade` → LocalBusiness com `areaServed` enriquecido), `frontend/app/blog/licitacoes/[setor]/[uf]/page.tsx` (+ seção "Cidades relevantes em {UF}")
**Resultado:** 46 páginas pSEO ISR 24h consumindo `GET /v1/blog/stats/cidade/{slug}` (hero + stats + órgãos + FAQ + internal linking setor×UF). Rota `/blog/licitacoes/cidade/{slug}` (segmento estático `cidade` para evitar conflito Next.js com `[setor]/[uf]`). **Nota:** 46 em vez de 81 porque `UF_CITIES` no backend atualmente lista 46 cidades; expansão do dicionário backend é trabalho separado.

### Frente 5 — Pack Off-Page e Distribuição (artefatos)
**Arquivos criados em `docs/seo/`:**
- `off-page-directories.md` (277 linhas) — 15 diretórios priorizados P0/P1/P2, copy pronto (tagline/short/long), checklists
- `testimonial-emails.md` (212 linhas) — 4 emails personalizados (Supabase/Railway/Resend/Vercel), cadência de follow-up
- `panorama-2026-t1-outline.md` (431 linhas) — 8 seções, queries SQL contra `pncp_raw_bids`, design landing `/relatorio-2026-t1`, 20 jornalistas BR, copy pitch
- `linkedin-editorial-4w.md` (573 linhas) — 12 posts (3/semana × 4 semanas) com hooks, corpo, hashtags, dados PNCP
- `indexnow-api-key.md` (300 linhas) — geração de key, hosting, GH Secret, validação curl

### Validação de regressão
- `npx tsc --noEmit` (frontend) → **exit 0**
- `pytest backend/tests/test_referral.py` → **8/8 pass**
- `pytest` em tests afetados (webhook/stripe/subscription/billing): **166/166 pass**
- `jest` em suites afetadas (GoogleAnalytics, PlanosPage, AjudaPage, blog-programmatic, blog-infrastructure): **180/180 pass**
- 3 falhas em `test_blog_stats::TestPanoramaStats::*` e `test_openapi_schema_matches_snapshot` confirmadas como **pre-existentes** via `git stash` (reproduziram sem as mudanças). **Zero regressões introduzidas.**

### Pendências manuais
- ~~Aplicar migration: `supabase db push` em `20260405100000_referrals.sql`~~ → **CONCLUÍDO (2026-04-05)** via `deploy.yml > Apply Pending Migrations`; tabela + RLS + função validadas.
- ~~Gerar `INDEXNOW_KEY` + commitar `frontend/public/<key>.txt`~~ → **CONCLUÍDO (2026-04-05)**: key `e9fd5881ff34cea8b67399d910212300`, GH Secret configurado, pipeline validado end-to-end (curl HTTP 200, IndexNow submission HTTP 202).
- Plugar email Day-7 de referral na sequência de onboarding existente (templates prontos em `backend/templates/emails/referral_{welcome,converted}.py`).
- Executar ações off-page (Frente 5) conforme playbooks prontos em `docs/seo/` (Product Hunt, G2, testimonials, LinkedIn, relatório Panorama T1).
