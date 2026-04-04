# SmartLic — Playbook de Crescimento Orgânico: CAC Mínimo via Conversão Máxima
## Versão 2.0 · Atualizado: 2026-04-04

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
- [ ] **Adicionar `dateModified`** no JSON-LD de cada página com ISR igual ao `revalidate` timestamp

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
- [ ] **Não indexar** `/analise/[hash]` (conteúdo gerado por usuário, não editorial) — adicionar `<meta name="robots" content="noindex">` na página de análise compartilhada

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

- [ ] **Verificar que a homepage** tem links explícitos para `/calculadora` e `/cnpj`
- [ ] **Verificar que cada artigo de blog** tem link para `/licitacoes/[setor]` correspondente
- [ ] **Verificar que cada landing setorial** tem links para as 5 UFs principais (`/blog/licitacoes/[setor]/sp`, `/mg`, `/rs`, `/pr`, `/sc`)

### 6. Indexabilidade e Canonical

Erros silenciosos de canonical ou `noindex` matam meses de trabalho sem aviso.

- [ ] **Auditar mensalmente no GSC** (Cobertura → Excluídas) para detectar páginas `noindex` acidentais
- [ ] **Garantir canonical correto** nas 405 páginas setor×UF — cada uma com sua própria URL canonical (não apontar para a landing setorial)
- [ ] **Verificar que ISR não quebra canonical** — Next.js ISR pode servir versões stale com canonical incorreto se o `generateMetadata` não for async corretamente
- [x] **Robots.txt** — confirmar que `/api/`, `/admin/`, `/auth/` estão bloqueados; que `/licitacoes/`, `/blog/`, `/calculadora/`, `/cnpj/`, `/casos/`, `/analise/` **não** estão bloqueados. Adicionadas rotas protegidas: `/dashboard`, `/conta`, `/buscar`, `/pipeline`, `/historico`, `/mensagens`, `/alertas`, `/onboarding`

```
# Verificação rápida:
curl https://smartlic.tech/robots.txt
curl https://smartlic.tech/sitemap.xml | grep -c "<url>" # deve retornar 450+
```

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
- [ ] **Verificar `getRegionalEditorial(uf, sector)`** cobre todas as 27 UFs
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

- [ ] **Criar endpoint público** `GET /v1/calculadora/dados?setor={id}&uf={uf}`
  - Retorna: `{ total_editais_mes, avg_value, p25_value, p75_value, setor_name, uf }`
  - Query em `pncp_raw_bids` agrupada por setor/UF — últimos 30 dias
  - **Sem autenticação** (público — é marketing)
  - Cache: Redis 1h
  - Rate limit: 60 req/min por IP
- [ ] **Adicionar rota** em `backend/routes/calculadora.py`
- [ ] **Testar endpoint:**
  ```bash
  curl "http://localhost:8000/v1/calculadora/dados?setor=saude&uf=SP"
  # Esperado: { "total_editais_mes": 847, "avg_value": 285000, ... }
  ```

#### Checklist de implementação — Frontend

- [ ] **Criar `frontend/app/calculadora/page.tsx`**
- [ ] **Metadata SEO:**
  ```ts
  title: 'Calculadora de Oportunidades B2G — Quanto você está perdendo em licitações?'
  description: 'Descubra quantas licitações do seu setor sua equipe está perdendo por falta de automação. Dados reais do PNCP, por setor e UF.'
  canonical: 'https://smartlic.tech/calculadora'
  ```
- [ ] **Schema markup:** `HowTo` + `FAQPage`
- [ ] **Formulário de 3 etapas** com validação client-side
- [ ] **Buscar dados reais** via `GET /api/calculadora/dados?setor=X&uf=Y` (proxy sem auth)
  - Criar `frontend/app/api/calculadora/dados/route.ts`
- [ ] **Resultado visual** com card de choque R$, gauge de cobertura, comparativo lado-a-lado
- [ ] **CTA contextual:** "Analisar as X oportunidades abertas agora no seu setor" → `/signup?ref=calculadora&setor={setor}&uf={uf}`
- [ ] **Adicionar `/calculadora`** ao sitemap.ts (priority 0.9, changeFrequency: 'weekly')
- [ ] **Adicionar link** na landing page, footer, e ao final de cada artigo setorial
- [ ] **Testar mobile** (formulário de 3 passos funciona em 375px?)
- [ ] **Analytics:** evento `calculadora_completed` no Mixpanel com `{ setor, uf, resultado_valor, clicked_cta }`
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

- [ ] **Criar endpoint público** `GET /v1/empresa/{cnpj}/perfil-b2g`
  - Agrega: BrasilAPI + Portal da Transparência (contratos)
  - Cache Redis 24h (dados mudam pouco)
  - **Sem autenticação** (público)
  - Rate limit: 30 req/min por IP
  - CNPJ inválido → 400 + mensagem clara
  - Empresa não encontrada → 404 + sugestão de trial
- [ ] **Criar `backend/routes/empresa_publica.py`**
- [ ] **Testar:** CNPJ `09225035000101` (GJS Construções — dados reais disponíveis)
- [ ] **Aviso legal** na resposta: fontes públicas (CNPJ aberto + Portal da Transparência)

#### Checklist de implementação — Frontend

- [ ] **Criar `frontend/app/cnpj/[cnpj]/page.tsx`** com ISR de 24h
  - `generateStaticParams()` vazio (SSR on-demand)
  - `revalidate = 86400`
- [ ] **Criar `frontend/app/cnpj/page.tsx`** — landing com formulário de busca
- [ ] **Metadata dinâmica:**
  ```ts
  title: `${razaoSocial} — Histórico de Contratos Públicos | SmartLic`
  description: `${razaoSocial} tem ${totalContratos} contratos com o governo nos últimos 24 meses. 
                Total: R$ ${valorTotal}. Score B2G: ${score}. Ver histórico completo.`
  canonical: `https://smartlic.tech/cnpj/${cnpj}`
  ```
- [ ] **Schema markup:** `Organization` + `Dataset`
- [ ] **OG image dinâmico** com razão social + score + total de contratos
- [ ] **Score visual** (badge: Verde=Ativa, Amarelo=Iniciante, Cinza=Sem histórico)
- [ ] **Tabela de contratos** paginada (max 10, lazy load)
- [ ] **Contador de editais ao vivo** do setor detectado (dado do datalake)
- [ ] **CTA contextual** por cenário A/B/C (copy acima)
- [ ] **Adicionar `/cnpj`** ao sitemap.ts (priority 0.8)
- [ ] **Link** no footer e menu "Ferramentas gratuitas"
- [ ] **Aviso legal** visível: dados de fontes públicas
- [ ] **Analytics:** `cnpj_lookup` no Mixpanel com `{ setor_detectado, uf, total_contratos, score, clicked_cta }`
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

- [ ] **Selecionar 5 cases** dos `docs/reports/`:
  - 1 Engenharia, 1 Construção, 1 Facilities, 1 Saúde ou TI, 1 anonimizado de destaque
- [ ] **Extrair por case:** porte, setor, UF, N editais analisados, valor oportunidades, score médio, insight chave
- [ ] **Obter aprovação** dos betas (email simples):
  - Opção A: nome real + logo (máxima credibilidade)
  - Opção B: perfil anonimizado "Construtora de médio porte em SC" (zero risco)

#### Checklist de implementação — Frontend

- [ ] **Criar `frontend/app/casos/page.tsx`** — listagem de cases
- [ ] **Criar `frontend/app/casos/[slug]/page.tsx`** — case individual
- [ ] **Metadata SEO por case:**
  ```ts
  title: `Como ${empresa} identificou R$ ${valor} em contratos de licitação em ${tempo} | SmartLic`
  description: `Case real: ${empresa} analisou ${totalEditais} editais com o SmartLic e encontrou 
                R$ ${valor} em contratos compatíveis. Score médio de viabilidade: ${score}/100.`
  ```
- [ ] **Schema markup:** `Article` + `Review`
- [ ] **Adicionar `/casos`** ao sitemap.ts (priority 0.8)
- [ ] **Link "Casos de sucesso"** no menu de navegação principal e footer
- [ ] **CTA em cada case:** "Rode uma análise para o seu setor" → `/signup?ref=case-{slug}`
- [ ] **Link cruzado** nos artigos de blog do setor correspondente
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

- [ ] **Criar tabela** `shared_analyses` no Supabase:
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
- [ ] **Endpoint** `POST /v1/share/analise` (requer auth) → retorna `{ url }`
- [ ] **Endpoint** `GET /v1/share/analise/{hash}` (público) → incrementa view_count, 404 se expirado

#### Checklist de implementação — Frontend

- [ ] **Botão "Compartilhar análise"** em cada card de resultado no `/buscar`
  - Click → POST → copia URL para clipboard com toast "Link copiado!"
  - Mobile: Web Share API nativo se disponível
- [ ] **Criar `frontend/app/analise/[hash]/page.tsx`** (ISR 1h)
  - Score de viabilidade com breakdown dos 4 fatores
  - OG image dinâmico com score e título
  - Watermark + CTA contextual (copy acima)
- [ ] **Metadata dinâmica:**
  ```ts
  title: `Análise: ${bidTitle} — Score ${score}/100 | SmartLic`
  description: `Viabilidade ${score}/100 para "${bidTitle}" (${organ}). 
                4 fatores: modalidade, prazo, valor e geografia.`
  ```
- [ ] **Schema markup:** `Review` com `ratingValue = score`
- [ ] **Analytics:** `analysis_shared`, `analysis_viewed` no Mixpanel
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

- [ ] "Checklist completo de habilitação para licitação em 2026 (Lei 14.133)"
- [ ] "Pregão eletrônico: guia passo a passo para primeira participação"
- [ ] "Como calcular o preço de proposta para não perder dinheiro em licitação"
- [ ] "MEI e Microempresa: vantagens e limites para participar de licitações"
- [ ] "SICAF: como se cadastrar e manter ativo em 2026"
- [ ] "Principais erros que desclassificam propostas — e como evitá-los"
- [ ] "Impugnação de edital: quando e como contestar"
- [ ] "Ata de Registro de Preços: estratégia de licitação sem comprar"

#### Distribuição de cada artigo

- [ ] LinkedIn do fundador (post nativo, não link — dados do artigo adaptados para o formato)
- [ ] WhatsApp de grupos de licitações (com permissão dos admins)
- [ ] Resposta em fóruns: Licitações-e community, grupos Facebook "licitações públicas"

#### Infraestrutura de blog (melhorias independentes)

- [ ] **RSS feed** — verificar se `/blog/rss.xml` está no sitemap
- [ ] **Canonical tags** — confirmar que todas as 40 páginas têm `alternates.canonical`
- [ ] **Internal linking audit** — cada artigo linka para pelo menos 2 outros + `/calculadora`
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

**Métricas de CAC (prioridade 1):**

| Métrica | Baseline | Meta 30 dias | Meta 90 dias |
|---------|----------|-------------|-------------|
| CAC orgânico geral (R$) | — | < R$150 | < R$80 |
| Trials via orgânico/mês | — | 30 | 120 |
| Trial-to-paid por canal (%) | — | > 30% | > 35% |
| Pagantes via orgânico/mês | — | 10 | 42 |
| MRR orgânico incremental | R$0 | R$3.970 | R$16.674 |

**Métricas de funil (prioridade 2):**

| Métrica | Baseline | Meta 30 dias | Meta 90 dias |
|---------|----------|-------------|-------------|
| Páginas indexadas (GSC) | ~50 est. | 130+ (pós P0+P1) | 450+ |
| Impressões orgânicas/mês | — | 5.000 | 50.000 |
| Cliques orgânicos/mês | — | 200 | 2.000 |
| Cálculos na calculadora/mês | 0 | 100 | 500 |
| Consultas CNPJ/mês | 0 | 200 | 2.000 |
| Análises compartilhadas/mês | 0 | 30 | 150 |

**O número que mais importa:**
```
trial-to-paid por source (Stripe + Mixpanel UTM)
= Quantos dos trials que vieram de cada canal viraram clientes pagantes?
```

Se um canal tem alto volume de trial e baixo trial-to-paid → problema de qualificação (leads errados).
Se um canal tem baixo volume e alto trial-to-paid → amplificar (leads certos, escassez de topo).

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
- **Não medir sucesso por impressões ou posição de keyword.** A posição não paga o servidor. O trial-to-paid paga.
