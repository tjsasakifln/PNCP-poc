# SmartLic — Checklist de Verificacao em Producao: SEO & Crescimento Organico
## Documento Espelho do SEO-ORGANIC-PLAYBOOK.md · v1.0 · 2026-04-08

> **Objetivo:** Verificar que TODAS as implementacoes descritas no playbook estao funcionando corretamente em producao (`https://smartlic.tech`). Cada item e acionavel — com URL, comando ou criterio de sucesso mensuravel.

---

## Como Usar Este Checklist

**Legenda de frequencia:**
- `[UNICA]` — Verificar uma vez apos deploy
- `[SEMANAL]` — Verificar semanalmente
- `[MENSAL]` — Verificar mensalmente
- `[DIARIA]` — Verificar diariamente (automatizavel via S14)

**Legenda de status:**
- `[ ]` — Nao verificado
- `[x]` — Verificado e OK
- `[!]` — Verificado com problema (anotar abaixo)

**Procedimento:** Percorrer secao por secao. Marcar `[x]` quando o criterio de sucesso for atendido. Itens `[!]` devem ter issue criada no GitHub.

---

## F. Fundacao Tecnica

### F.1 Core Web Vitals `[MENSAL]`

**Ferramenta:** PageSpeed Insights — `https://pagespeed.web.dev/`

| # | Verificacao | URL de Teste | Criterio de Sucesso |
|---|------------|-------------|---------------------|
| F.1.1 | [ ] Landing setorial — mobile | `https://smartlic.tech/licitacoes/engenharia` | LCP < 2.0s, CLS < 0.1, perf >= 95 |
| F.1.2 | [ ] Landing setorial — desktop | `https://smartlic.tech/licitacoes/engenharia` | LCP < 1.0s, CLS < 0.1, perf >= 95 |
| F.1.3 | [ ] Pagina setor×UF — mobile | `https://smartlic.tech/blog/licitacoes/engenharia/sp` | LCP < 2.0s, CLS < 0.1, perf >= 90 |
| F.1.4 | [ ] Calculadora — mobile | `https://smartlic.tech/calculadora` | LCP < 2.5s, TBT < 200ms (proxy INP), perf >= 95 |
| F.1.5 | [ ] Cases — mobile | `https://smartlic.tech/casos` | LCP < 2.5s, CLS < 0.1, perf >= 90 |
| F.1.6 | [ ] Homepage — mobile | `https://smartlic.tech` | LCP < 2.5s, CLS < 0.1, perf >= 90 |
| F.1.7 | [ ] GSC Core Web Vitals report | GSC > Experiencia > Core Web Vitals | Zero URLs "Poor", < 10% "Needs Improvement" |

**Spot check adicional (5 paginas aleatorias setor×UF):**

| # | URL | LCP | CLS | Perf |
|---|-----|-----|-----|------|
| F.1.8 | [ ] `/blog/licitacoes/vestuario/ba` | ___ | ___ | ___ |
| F.1.9 | [ ] `/blog/licitacoes/informatica/rs` | ___ | ___ | ___ |
| F.1.10 | [ ] `/blog/licitacoes/saude/am` | ___ | ___ | ___ |
| F.1.11 | [ ] `/blog/licitacoes/alimentos/ce` | ___ | ___ | ___ |
| F.1.12 | [ ] `/blog/licitacoes/engenharia-rodoviaria/go` | ___ | ___ | ___ |

### F.2 E-E-A-T `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| F.2.1 | [ ] Autor identificado nos artigos | Abrir 3 artigos aleatorios do blog | `authorName` e `authorRole` visiveis |
| F.2.2 | [ ] Data de atualizacao visivel | Abrir pagina com dados ao vivo | Timestamp "Dados atualizados X horas atras" presente |
| F.2.3 | [ ] `dateModified` no JSON-LD | `curl -s https://smartlic.tech/blog/licitacoes/engenharia/sp \| grep dateModified` | Campo presente no JSON-LD |
| F.2.4 | [ ] CNPJ CONFENGE no footer | Abrir qualquer pagina, scroll ate o footer | CNPJ visivel |
| F.2.5 | [ ] Link para `/sobre` no footer | Inspecionar footer | Link presente e funcional |
| F.2.6 | [ ] Fontes primarias nos artigos | Abrir 3 artigos, verificar links | Min 2 links para PNCP/Portal Transparencia/DO por artigo |
| F.2.7 | [ ] Freshness label em paginas ISR | `https://smartlic.tech/licitacoes/engenharia` | Label "Dados atualizados..." abaixo do StatsCards |

### F.3 AI Overviews `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| F.3.1 | [ ] FAQPage JSON-LD nos artigos | Rich Results Test em 3 artigos | FAQPage detectado, sem erros |
| F.3.2 | [ ] Respostas diretas nas FAQs | Abrir 3 artigos, verificar FAQ | Primeiro token da resposta e a resposta direta (nao contexto) |
| F.3.3 | [ ] HowTo schema nas landing setoriais | Rich Results Test: `/licitacoes/engenharia` | HowTo detectado |
| F.3.4 | [ ] Dataset schema nas landing setoriais | Rich Results Test: `/licitacoes/engenharia` | Dataset detectado |

**Ferramenta:** `https://search.google.com/test/rich-results`

### F.4 Freshness & Crawl Budget `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| F.4.1 | [ ] Sitemap total de URLs | `curl -s https://smartlic.tech/sitemap.xml \| grep -c "<url>"` | >= 600 URLs |
| F.4.2 | [ ] Paginas setor×UF no sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep "blog/licitacoes" \| head -5` | 405 URLs com `changefreq: daily` |
| F.4.3 | [ ] `/analise/` nao indexada | `curl -s https://smartlic.tech/analise/test123 \| grep "noindex"` | `robots: { index: false }` presente |
| F.4.4 | [ ] ISR funcionando (cache HIT) | `curl -sI https://smartlic.tech/blog/licitacoes/engenharia/sp \| grep x-nextjs-cache` | `x-nextjs-cache: HIT` |
| F.4.5 | [ ] Cache-Control publico | `curl -sI https://smartlic.tech/licitacoes/engenharia \| grep cache-control` | `public, s-maxage=3600, stale-while-revalidate=86400` |

### F.5 Internal Linking `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| F.5.1 | [ ] Homepage linka `/calculadora` | Inspecionar homepage | Link presente (navbar ou corpo) |
| F.5.2 | [ ] Homepage linka `/cnpj` | Inspecionar homepage | Link presente (navbar ou footer) |
| F.5.3 | [ ] Artigos linkam para landing setorial | Abrir 3 artigos, verificar sidebar/RelatedPages | Link para `/licitacoes/[setor]` correspondente |
| F.5.4 | [ ] Landing setorial linka 27 UFs | `https://smartlic.tech/licitacoes/engenharia` | Links para todas 27 UFs (nao so 5) |
| F.5.5 | [ ] Landing setorial linka calculadora | `https://smartlic.tech/licitacoes/informatica` | Link para `/calculadora?setor=...` |
| F.5.6 | [ ] Blog listing linka ferramentas | `https://smartlic.tech/blog` | Secao "Ferramentas Gratuitas" com calculadora, CNPJ, glossario |
| F.5.7 | [ ] Breadcrumbs corretos setor×UF | `https://smartlic.tech/blog/licitacoes/engenharia/sp` | Breadcrumb aponta para `/licitacoes/engenharia` (hub), NAO `/blog/programmatic/engenharia` |

### F.6 Indexabilidade & Canonical `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| F.6.1 | [ ] robots.txt correto | `curl https://smartlic.tech/robots.txt` | `/api/`, `/admin/`, `/auth/`, `/dashboard/`, `/conta/`, `/buscar/`, `/pipeline/`, `/historico/`, `/mensagens/`, `/alertas/`, `/onboarding/` bloqueados; `/licitacoes/`, `/blog/`, `/calculadora/`, `/cnpj/`, `/casos/`, `/glossario/` permitidos |
| F.6.2 | [ ] Canonical self-referencing setor×UF | `curl -s https://smartlic.tech/blog/licitacoes/engenharia/sp \| grep canonical` | Canonical aponta para propria URL |
| F.6.3 | [ ] Trailing slash redirect | `curl -sI https://smartlic.tech/calculadora/` | HTTP 308 redirect para `/calculadora` (sem trailing slash) |
| F.6.4 | [ ] PWA manifest | `curl -s https://smartlic.tech/manifest.json` | JSON valido com name, icons, theme_color, lang pt-BR |
| F.6.5 | [ ] Preconnect hints | View source de qualquer pagina | `<link rel="preconnect">` para Supabase |
| F.6.6 | [ ] JSON-LD inline (nao async) | View source de qualquer pagina | `<script type="application/ld+json">` (nao `<Script>` async) |
| F.6.7 | [ ] `trailingSlash: false` ativo | Verificar `next.config.js` ou testar redirect acima | Config ativa |

### F.7 IndexNow & Google Ping `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| F.7.1 | [ ] IndexNow key acessivel | `curl -s https://smartlic.tech/e9fd5881ff34cea8b67399d910212300.txt` | HTTP 200, retorna a key |
| F.7.2 | [ ] GitHub Action IndexNow | `gh run list --workflow=indexnow.yml --limit=3` | Ultimas 3 execucoes com status "success" |
| F.7.3 | [ ] Secret INDEXNOW_KEY configurado | `gh secret list \| grep INDEXNOW_KEY` | Secret presente |
| F.7.4 | [ ] Google Ping no workflow | Inspecionar `.github/workflows/indexnow.yml` | Step "Ping Google & Bing" presente com `if: always()` |
| F.7.5 | [ ] Google Ping funcional | `curl -s "https://www.google.com/ping?sitemap=https://smartlic.tech/sitemap.xml"` | HTTP 200 |

---

## P. Iniciativas Tecnicas (P0-P7)

### P0 — Sitemap `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| P0.1 | [ ] Sitemap acessivel | `curl -sI https://smartlic.tech/sitemap.xml` | HTTP 200, content-type XML |
| P0.2 | [ ] Rotas `/blog/programmatic/[setor]` | `curl -s https://smartlic.tech/sitemap.xml \| grep "blog/programmatic"` | 15 URLs (1 por setor) |
| P0.3 | [ ] Rotas `/blog/licitacoes/[setor]/[uf]` | `curl -s https://smartlic.tech/sitemap.xml \| grep "blog/licitacoes" \| grep -v "cidade" \| wc -l` | 405 URLs |
| P0.4 | [ ] Rotas `/blog/panorama/[setor]` | `curl -s https://smartlic.tech/sitemap.xml \| grep "blog/panorama"` | 15 URLs |
| P0.5 | [ ] Sitemap submetido ao GSC | GSC > Sitemaps | Status "Processado", sem erros |
| P0.6 | [ ] Total de URLs | `curl -s https://smartlic.tech/sitemap.xml \| grep -c "<url>"` | >= 2.550 (com expansao programatica) |

### P1 — Paginas Setor×UF (405) `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| P1.1 | [ ] Pagina responde HTTP 200 | `curl -sI https://smartlic.tech/blog/licitacoes/engenharia/sp` | HTTP 200 |
| P1.2 | [ ] ISR cache ativo | Header `x-nextjs-cache` na resposta | `HIT` ou `STALE` |
| P1.3 | [ ] Dados ao vivo no hero | Abrir pagina no browser | H1 com contagem de editais + valor medio + timestamp |
| P1.4 | [ ] CTA contextual | Abrir pagina no browser | CTA com setor e UF pre-preenchidos no link `/signup?ref=...` |
| P1.5 | [ ] Spot check — 5 combinacoes | Testar: `vestuario/ba`, `informatica/rs`, `saude/am`, `alimentos/ce`, `engenharia-rodoviaria/go` | Todos HTTP 200 |
| P1.6 | [ ] Slug TI correto | `curl -sI https://smartlic.tech/blog/licitacoes/informatica/sp` | HTTP 200 (slug = `informatica`, NAO `tecnologia-informacao`) |
| P1.7 | [ ] Title com mes corrente | View source de qualquer setor×UF | `<title>` contem mes/ano atual |

### P2 — Calculadora `/calculadora` `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| P2.1 | [ ] Pagina acessivel | `curl -sI https://smartlic.tech/calculadora` | HTTP 200 |
| P2.2 | [ ] Endpoint backend funcional | `curl -s "https://api.smartlic.tech/v1/calculadora/dados?setor=1&uf=SP"` | JSON com `total_editais_mes`, `avg_value` |
| P2.3 | [ ] Schema HowTo + FAQPage | Rich Results Test: `/calculadora` | Ambos detectados |
| P2.4 | [ ] Formulario 3 etapas funcional | Testar no browser: selecionar setor, UF, preencher valores | Resultado com card R$ + breakdown + comparativo |
| P2.5 | [ ] CTA contextual no resultado | Completar calculo | Botao "Analisar as X oportunidades..." com `?ref=calculadora&setor=...&uf=...` |
| P2.6 | [ ] Link no navbar | Inspecionar navegacao principal | "Calculadora" presente |
| P2.7 | [ ] Link no footer | Inspecionar footer | Secao "Ferramentas" com calculadora |
| P2.8 | [ ] Mobile responsive | Testar em 375px viewport | Sem overflow, steps centralizados |
| P2.9 | [ ] No sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep calculadora` | Presente com priority >= 0.8 |

### P3 — Ferramenta CNPJ `/cnpj` `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| P3.1 | [ ] Landing page acessivel | `curl -sI https://smartlic.tech/cnpj` | HTTP 200 |
| P3.2 | [ ] Formulario de busca funcional | Abrir `/cnpj`, digitar CNPJ valido | Redirect para `/cnpj/[cnpj]` |
| P3.3 | [ ] Endpoint backend funcional | `curl -s "https://api.smartlic.tech/v1/empresa/00000000000191/perfil-b2g"` | JSON com perfil, score, contratos |
| P3.4 | [ ] Schema Organization + Dataset | Rich Results Test em `/cnpj/[cnpj]` | Ambos detectados |
| P3.5 | [ ] Score visual (badge colorido) | Abrir perfil de CNPJ ativo | Badge verde/amarelo/cinza conforme score |
| P3.6 | [ ] CTA por cenario (A/B/C) | Testar com CNPJ ativo, iniciante e sem historico | Copy diferente por cenario |
| P3.7 | [ ] Aviso legal visivel | Abrir qualquer perfil CNPJ | "Dados de fontes publicas" visivel |
| P3.8 | [ ] No sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep "/cnpj"` | Presente com priority >= 0.8 |
| P3.9 | [ ] Link no footer | Inspecionar footer | Secao "Ferramentas" com CNPJ |

### P4 — Schema Markup `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| P4.1 | [ ] Dataset schema em landing setorial | Rich Results Test: `/licitacoes/engenharia` | Dataset com `variableMeasured`, `spatialCoverage`, `distribution` |
| P4.2 | [ ] HowTo schema em landing setorial | Rich Results Test: `/licitacoes/engenharia` | 3 steps HowTo detectados |
| P4.3 | [ ] Spot check 3 setores | Rich Results Test: `/licitacoes/informatica`, `/licitacoes/saude`, `/licitacoes/alimentos` | Dataset + HowTo em todos |
| P4.4 | [ ] FAQPage no blog | Rich Results Test em 3 artigos | FAQPage detectado, sem erros |

### P5 — Cases `/casos` `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| P5.1 | [ ] Listagem acessivel | `curl -sI https://smartlic.tech/casos` | HTTP 200 |
| P5.2 | [ ] Case individual acessivel | `curl -sI https://smartlic.tech/casos/[slug]` | HTTP 200 (testar 2 slugs) |
| P5.3 | [ ] Schema Article + Review | Rich Results Test em 1 case | Ambos detectados |
| P5.4 | [ ] CTA em cada case | Abrir 1 case | "Rode uma analise para o seu setor" com `?ref=case-[slug]` |
| P5.5 | [ ] No menu de navegacao | Inspecionar navbar | "Casos de sucesso" presente |
| P5.6 | [ ] No sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep "/casos"` | Presente |
| P5.7 | [ ] Numero de resultado concreto | Abrir cada case | Valor em R$ ou N editais ou horas (NUNCA so "ficou satisfeito") |

### P6 — Compartilhamento Viral `/analise/[hash]` `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| P6.1 | [ ] Tabela `shared_analyses` existe | Query Supabase | Tabela com colunas hash, viability_score, viability_breakdown |
| P6.2 | [ ] Endpoint POST funcional | Testar via busca autenticada + compartilhar | Retorna URL com hash |
| P6.3 | [ ] Endpoint GET publico funcional | `curl -s https://api.smartlic.tech/v1/share/analise/[hash]` | JSON com score + breakdown |
| P6.4 | [ ] OG image dinamica | Compartilhar link no WhatsApp/Telegram | Preview mostra score colorido + titulo do edital |
| P6.5 | [ ] ShareButtons presentes | Abrir `/analise/[hash]` no browser | Botoes LinkedIn, WhatsApp, X/Twitter, Copiar |
| P6.6 | [ ] Watermark + CTA no rodape | Scroll ate o fim da pagina `/analise/[hash]` | "Analise gerada pelo SmartLic" + CTA 14 dias gratis |
| P6.7 | [ ] Schema Review | Rich Results Test em `/analise/[hash]` | Review com ratingValue |
| P6.8 | [ ] `noindex` na pagina | View source | `robots: { index: false, follow: true }` |

### P7 — Blog & Conteudo `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| P7.1 | [ ] RSS feed acessivel | `curl -sI https://smartlic.tech/blog/rss.xml` | HTTP 200, XML valido |
| P7.2 | [ ] RSS no sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep rss` | Presente |
| P7.3 | [ ] Canonical tags corretas | `curl -s https://smartlic.tech/blog/[slug] \| grep canonical` em 3 artigos | Self-referencing correto |
| P7.4 | [ ] BlogInlineCTA contextual | Abrir artigo, verificar CTA ~40% do texto | Copy contextual (nao generico "teste gratis") |
| P7.5 | [ ] 8 artigos P7 acessiveis | Testar 3 dos 8 temas prioritarios | HTTP 200 |
| P7.6 | [ ] Artigos BOFU acessiveis | `curl -sI https://smartlic.tech/blog/smartlic-vs-effecti-comparacao-2026` | HTTP 200 |
| P7.7 | [ ] Georgia font removida de H1s | View source de pagina setor×UF | Sem `style={{ fontFamily: "Georgia..." }}` no H1 |

---

## S. Substituicoes On-Page (S1-S14)

### S1 — Glossario `/glossario` `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S1.1 | [ ] Hub acessivel | `curl -sI https://smartlic.tech/glossario` | HTTP 200 |
| S1.2 | [ ] Termo individual acessivel | `curl -sI https://smartlic.tech/glossario/pregao-eletronico` | HTTP 200 |
| S1.3 | [ ] Schema DefinedTerm + FAQPage | Rich Results Test em 1 termo | Ambos detectados |
| S1.4 | [ ] 50+ termos no sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep glossario \| wc -l` | >= 50 |
| S1.5 | [ ] Sidebar com termos relacionados | Abrir 1 termo | Lista de termos relacionados visivel |
| S1.6 | [ ] Links para paginas setoriais | Abrir 1 termo | Links para `/licitacoes/[setor]` relevantes |
| S1.7 | [ ] Canonical sem acento | View source de termo com acento | URL canonica sem caracteres acentuados |

### S2 — Data Hub `/dados` `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S2.1 | [ ] Pagina acessivel | `curl -sI https://smartlic.tech/dados` | HTTP 200 |
| S2.2 | [ ] Endpoint backend funcional | `curl -s https://api.smartlic.tech/v1/dados/agregados` | JSON com dados por setor/UF/modalidade/tendencia |
| S2.3 | [ ] Schema Dataset + DataCatalog | Rich Results Test: `/dados` | Ambos detectados |
| S2.4 | [ ] Graficos Recharts renderizam | Abrir no browser | Bar charts setor/UF, pie modalidade, line tendencia visiveis |
| S2.5 | [ ] Download CSV email-gated | Clicar "Baixar CSV" | Formulario de email aparece antes do download |

### S3 — Comparador + Alertas `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S3.1 | [ ] Comparador acessivel | `curl -sI https://smartlic.tech/comparador` | HTTP 200 |
| S3.2 | [ ] Busca no comparador funcional | Testar busca com termo generico | Retorna ate 10 resultados |
| S3.3 | [ ] Comparacao lado a lado | Selecionar 2-3 bids, comparar | Grid comparativo renderiza |
| S3.4 | [ ] URL compartilhavel comparador | Comparar bids, copiar URL | URL com `?ids=` funciona ao recarregar |
| S3.5 | [ ] Hub alertas acessivel | `curl -sI https://smartlic.tech/alertas-publicos` | HTTP 200 |
| S3.6 | [ ] Alerta setor×UF acessivel | `curl -sI https://smartlic.tech/alertas-publicos/engenharia/sp` | HTTP 200 |
| S3.7 | [ ] RSS feed por setor×UF | `curl -sI https://smartlic.tech/alertas-publicos/engenharia/sp/rss.xml` | HTTP 200, XML valido |
| S3.8 | [ ] Schema DataFeed nos alertas | Rich Results Test: `/alertas-publicos/engenharia/sp` | DataFeed detectado |
| S3.9 | [ ] 405+ alertas no sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep alertas-publicos \| wc -l` | >= 405 |
| S3.10 | [ ] CTA contextual nos alertas | Abrir 1 alerta | CTA com setor + UF |

### S4 — Weekly Digest `/blog/weekly` `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S4.1 | [ ] Indice de semanas acessivel | `curl -sI https://smartlic.tech/blog/weekly` | HTTP 200 |
| S4.2 | [ ] Ultimo digest acessivel | Abrir primeiro link do indice | HTTP 200, dados da semana atual |
| S4.3 | [ ] Endpoint backend funcional | `curl -s https://api.smartlic.tech/v1/blog/weekly/latest` | JSON com stats semanais |
| S4.4 | [ ] Schema NewsArticle + Dataset | Rich Results Test no ultimo digest | Ambos detectados |
| S4.5 | [ ] Tabelas com trend arrows | Abrir digest no browser | Tabelas setor/UF com setas de tendencia |
| S4.6 | [ ] No sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep "blog/weekly"` | >= 1 URL |

### S5 — Demo Interativo `/demo` `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S5.1 | [ ] Pagina acessivel | `curl -sI https://smartlic.tech/demo` | HTTP 200 |
| S5.2 | [ ] Tour Shepherd.js funcional | Abrir no browser, iniciar tour | 4 passos: setor > busca > resultados > analise |
| S5.3 | [ ] Schema HowTo + WebApplication | Rich Results Test: `/demo` | Ambos detectados |
| S5.4 | [ ] CTA ao final | Completar tour | "Criar conta gratis" com `?ref=demo` |
| S5.5 | [ ] No sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep "/demo"` | Presente |

### S6 — Estatisticas Citaveis `/estatisticas` `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S6.1 | [ ] Pagina acessivel | `curl -sI https://smartlic.tech/estatisticas` | HTTP 200 |
| S6.2 | [ ] Endpoint backend funcional | `curl -s https://api.smartlic.tech/v1/stats/public` | JSON com 15-20 stats agregadas |
| S6.3 | [ ] Schema Dataset + StatisticalPopulation | Rich Results Test: `/estatisticas` | Ambos detectados |
| S6.4 | [ ] Botao "Citar estatistica" | Clicar em 1 stat | HTML blockquote com backlink para smartlic.tech copiado |
| S6.5 | [ ] Botao "Copiar citacao" | Clicar em 1 stat | Formato ABNT copiado |
| S6.6 | [ ] No sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep estatisticas` | Presente |

### S7 — Entity SEO `/sobre` + Author Pages `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S7.1 | [ ] `/sobre` acessivel | `curl -sI https://smartlic.tech/sobre` | HTTP 200 |
| S7.2 | [ ] Organization schema | Rich Results Test: `/sobre` | Organization com name, brand, founder, taxID |
| S7.3 | [ ] LocalBusiness schema | Rich Results Test: `/sobre` | LocalBusiness com address |
| S7.4 | [ ] Author page acessivel | `curl -sI https://smartlic.tech/blog/author/tiago` | HTTP 200 |
| S7.5 | [ ] Person schema no author | Rich Results Test: `/blog/author/tiago` | Person com name, jobTitle, sameAs |
| S7.6 | [ ] Lista de artigos no author | Abrir author page | Lista de artigos publicados |
| S7.7 | [ ] CNPJ no footer | Qualquer pagina, scroll ao footer | CNPJ CONFENGE visivel |
| S7.8 | [ ] `sameAs` com GitHub/LinkedIn | Inspecionar JSON-LD em `/sobre` | Links sociais presentes |

### S8 — Tech Stack `/stack` `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S8.1 | [ ] Pagina acessivel | `curl -sI https://smartlic.tech/stack` | HTTP 200 |
| S8.2 | [ ] Cards por ferramenta | Abrir no browser | Cards com Supabase, Railway, Next.js, FastAPI, Resend, OpenAI, Redis, Stripe |
| S8.3 | [ ] Metricas reais por ferramenta | Verificar dados nos cards | Numeros especificos (40K+ rows, 49 endpoints, etc) |
| S8.4 | [ ] Schema SoftwareApplication + HowTo | Rich Results Test: `/stack` | Ambos detectados |
| S8.5 | [ ] No sitemap + footer | Verificar | Presente em ambos |

### S9 — API Publica + Embed `/estatisticas/embed` `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S9.1 | [ ] Endpoint JSON publico | `curl -s "https://api.smartlic.tech/v1/public/stats?format=json"` | JSON com stats agregadas |
| S9.2 | [ ] Formato embed | `curl -s "https://api.smartlic.tech/v1/public/stats?format=embed"` | HTML snippet com backlink |
| S9.3 | [ ] Pagina de instrucoes | `curl -sI https://smartlic.tech/estatisticas/embed` | HTTP 200 |
| S9.4 | [ ] Preview do embed funcional | Abrir `/estatisticas/embed` no browser | Preview ao vivo do widget |
| S9.5 | [ ] Badge SVG com link | Inspecionar badge | Link para `/estatisticas` |
| S9.6 | [ ] DataDownload schema | Rich Results Test: `/estatisticas` | DataDownload com encodingFormat application/json |

### S10 — Q&A Publico `/perguntas` `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S10.1 | [ ] Hub acessivel | `curl -sI https://smartlic.tech/perguntas` | HTTP 200 |
| S10.2 | [ ] Pergunta individual acessivel | `curl -sI https://smartlic.tech/perguntas/[slug]` | HTTP 200 (testar 2 slugs) |
| S10.3 | [ ] Schema QAPage + FAQPage | Rich Results Test em 1 pergunta | Ambos detectados |
| S10.4 | [ ] 50+ perguntas no sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep perguntas \| wc -l` | >= 50 |
| S10.5 | [ ] Internal linking com glossario | Abrir 1 pergunta | Links para termos do glossario |
| S10.6 | [ ] Categorias organizadas | Abrir hub | 6 categorias visiveis (modalidades, prazos, documentacao, precos, setores, geral) |
| S10.7 | [ ] Dados PNCP nas respostas | Abrir 3 perguntas | Numeros verificaveis com fonte PNCP |

### S11 — Blog Founder `/blog/author/tiago` `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S11.1 | [ ] Author page acessivel | `curl -sI https://smartlic.tech/blog/author/tiago` | HTTP 200 |
| S11.2 | [ ] Person schema | Rich Results Test: `/blog/author/tiago` | Person detectado com sameAs |
| S11.3 | [ ] RSS feed do autor | `curl -sI https://smartlic.tech/blog/author/tiago/rss.xml` | HTTP 200, XML valido |
| S11.4 | [ ] Weekly digests vinculados ao author | Abrir ultimo weekly digest | Byline com link para `/blog/author/tiago` |

### S12 — Micro-Demos Animadas `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S12.1 | [ ] MicroDemo em landing setorial | Abrir `/licitacoes/engenharia` | Animacao visivel (busca, resultado ou viabilidade) |
| S12.2 | [ ] VideoObject schema | Rich Results Test: `/licitacoes/engenharia` | VideoObject detectado com thumbnailUrl, duration |
| S12.3 | [ ] 3 variantes de animacao | Verificar `MicroDemo.tsx` no codigo | busca, resultado, viabilidade |

### S13 — Masterclass `/masterclass` `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S13.1 | [ ] Pagina acessivel (tema 1) | `curl -sI https://smartlic.tech/masterclass/primeiro-edital` | HTTP 200 |
| S13.2 | [ ] Pagina acessivel (tema 2) | `curl -sI https://smartlic.tech/masterclass/analise-viabilidade` | HTTP 200 |
| S13.3 | [ ] Pagina acessivel (tema 3) | `curl -sI https://smartlic.tech/masterclass/inteligencia-setorial` | HTTP 200 |
| S13.4 | [ ] Schema Event + VideoObject + Course | Rich Results Test em 1 tema | @graph com 4 schemas |
| S13.5 | [ ] Email-gate via LeadCapture | Abrir masterclass | Formulario de email antes do conteudo |
| S13.6 | [ ] Videos gravados presentes | Reproduzir video | **PENDENTE:** 3 screencasts precisam ser gravados (OBS Studio, 15-20min cada) |

### S14 — Dashboard SEO Admin `/admin/seo` `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| S14.1 | [ ] Dashboard acessivel (auth admin) | Login como admin, navegar para `/admin/seo` | HTTP 200, dashboard renderiza |
| S14.2 | [ ] Tabela `seo_metrics` existe | Query Supabase | Tabela com date, impressions, clicks, position, pages_indexed |
| S14.3 | [ ] Graficos Recharts renderizam | Abrir dashboard | Graficos de tendencia visiveis |
| S14.4 | [ ] Cron semanal ativo | Verificar `jobs/cron/seo_snapshot.py` | Script funcional, graceful skip sem credentials GSC |
| S14.5 | [ ] Migration aplicada | `supabase migration list --linked` | `20260407400000_seo_metrics.sql` presente |

---

## E. Expansao Programatica (Parte 11)

### E.1 — CNPJ Pages no Sitemap (Onda 1) `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| E1.1 | [ ] Endpoint sitemap CNPJs funcional | `curl -s https://api.smartlic.tech/v1/sitemap/cnpjs \| python -c "import sys,json; d=json.load(sys.stdin); print(len(d))"` | >= 1.000 CNPJs (threshold >= 3 bids) |
| E1.2 | [ ] URLs no sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep "/cnpj/" \| wc -l` | >= 1.000 URLs |
| E1.3 | [ ] Priority e changefreq | Inspecionar sitemap | priority 0.5, changefreq weekly |
| E1.4 | [ ] Pagina CNPJ individual funcional | Pegar 1 CNPJ do sitemap, acessar no browser | HTTP 200, perfil B2G renderiza |
| E1.5 | [ ] Threshold thin content | Verificar endpoint | Apenas CNPJs com >= 3 licitacoes incluidos |
| E1.6 | [ ] Cache 24h no endpoint | `curl -sI https://api.smartlic.tech/v1/sitemap/cnpjs \| grep cache` | Cache ativo |

### E.2 — Orgaos Compradores (Onda 2) `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| E2.1 | [ ] Endpoint sitemap orgaos | `curl -s https://api.smartlic.tech/v1/sitemap/orgaos` | JSON com >= 500 orgaos |
| E2.2 | [ ] Landing page orgaos | `curl -sI https://smartlic.tech/orgaos` | HTTP 200 |
| E2.3 | [ ] Orgao individual funcional | Navegar para 1 orgao do indice | HTTP 200, dados do datalake |
| E2.4 | [ ] Endpoint stats por orgao | `curl -s "https://api.smartlic.tech/v1/orgao/[cnpj]/stats"` | JSON com contagens 30/90/365d, valor, modalidades, setores |
| E2.5 | [ ] Schema GovernmentOrganization + Dataset | Rich Results Test em 1 orgao | Ambos detectados |
| E2.6 | [ ] URLs no sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep "/orgaos/" \| wc -l` | >= 500 |
| E2.7 | [ ] Threshold thin content | Verificar endpoint | Apenas orgaos com >= 5 licitacoes |
| E2.8 | [ ] FAQ na landing | Abrir `/orgaos` | Secao FAQ com QAPage schema |

### E.3 — Cidade × Setor (Onda 3) `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| E3.1 | [ ] Endpoint backend funcional | `curl -s "https://api.smartlic.tech/v1/blog/stats/cidade/sao-paulo/setor/1"` | JSON com CidadeSectorStats |
| E3.2 | [ ] Pagina individual funcional | `curl -sI https://smartlic.tech/blog/licitacoes/cidade/sao-paulo/engenharia` | HTTP 200 |
| E3.3 | [ ] Schema 5-stack | Rich Results Test em 1 cidade×setor | LocalBusiness + Dataset + BreadcrumbList + Article + ItemList |
| E3.4 | [ ] 1.215 URLs no sitemap | `curl -s https://smartlic.tech/sitemap.xml \| grep "cidade" \| wc -l` | >= 1.200 |
| E3.5 | [ ] Thin content fallback | Acessar cidade×setor com poucos dados | Box amarelo informativo com links para escopo mais amplo |
| E3.6 | [ ] Acentuacao portuguesa correta | Abrir 3 paginas | Sem caracteres errados, formato R$ X.XXX,XX, zero markdown |
| E3.7 | [ ] Internal linking | Abrir pagina setor×UF | Links para cidade×setor correspondentes |
| E3.8 | [ ] Spot check 5 cidades | Testar: sao-paulo, rio-de-janeiro, curitiba, belo-horizonte, recife | Todos HTTP 200 |

---

## M. Metricas & Monitoramento (Parte 4/10)

### M.1 — CAC & Funil `[MENSAL]`

| # | Verificacao | Fonte | Meta |
|---|------------|-------|------|
| M1.1 | [ ] Paginas indexadas no GSC | GSC > Paginas > Validas | >= 200 (M2), >= 500 (M3) |
| M1.2 | [ ] Impressoes organicas/mes | GSC > Desempenho | >= 5.000 (M1), >= 20.000 (M3) |
| M1.3 | [ ] Cliques organicos/mes | GSC > Desempenho | >= 500 (M1), >= 2.000 (M3) |
| M1.4 | [ ] Trials organicos/mes | Mixpanel: signup com UTM organico | >= 5-12 (M1), >= 30-40 (M3) |
| M1.5 | [ ] Trial-to-paid por canal | Stripe + Mixpanel UTM | >= 25% |
| M1.6 | [ ] CAC organico | (Horas producao × custo/hora) / pagantes organicos | < R$200 |
| M1.7 | [ ] Calculos na calculadora/mes | Mixpanel: `calculadora_completed` | >= 50 (M1) |
| M1.8 | [ ] Consultas CNPJ/mes | Mixpanel: `cnpj_lookup` | >= 100 (M1) |

### M.2 — Milestones MRR `[MENSAL]`

| Mes | Paginas Indexadas | Visitas Org | Trials | Pagantes Ativos | MRR | Red Flag Se Abaixo |
|-----|-------------------|-------------|--------|-----------------|-----|---------------------|
| M1 (Abr) | 80-200 | 500-800 | 8-14 | 2-4 | R$1-2K | < 50 indexadas |
| M2 (Mai) | 200-500 | 1.000-2.000 | 17-34 | 8-12 | R$3-5K | < 150 indexadas |
| M3 (Jun) | 500-1.500 | 2.000-5.000 | 34-85 | 20-30 | R$9-13K | < 500 visitas |
| M4 (Jul) | 1.500-3.000 | 5.000-12.000 | 85-204 | 50-70 | R$22-30K | Trial→pago < 20% |
| M5 (Ago) | 3.000-5.000 | 12.000-25.000 | 204-425 | 110-145 | R$47-62K | < 8.000 visitas |
| M6 (Set) | 5.000-8.000 | 25.000-50.000 | 425-850 | 230-294 | R$99-126K | < 20.000 visitas |

### M.3 — Red Flags & Acoes Corretivas `[SEMANAL]`

| # | Red Flag | Diagnostico Provavel | Acao Imediata |
|---|----------|---------------------|---------------|
| M3.1 | < 50 indexadas no M1 | Crawling bloqueado ou sitemap nao processado | Verificar GSC Coverage; submeter URLs manualmente; verificar robots.txt |
| M3.2 | < 150 indexadas no M2 | Authority insuficiente | **Executar seed authority (Product Hunt/G2/Capterra)** — urgente |
| M3.3 | < 500 visitas no M3 | Indexadas mas nao rankeando | Verificar posicoes GSC; long-tail deveria rankear pos 1-5 |
| M3.4 | Trial→pago < 20% no M4 | Problema de ativacao | Pausar growth; focar Day-3 activation; card capture Day 7 |
| M3.5 | < 8.000 visitas no M5 | DR estagnado | Reavaliar timeline; canais complementares |
| M3.6 | < 20.000 visitas no M6 | SEO-only insuficiente | Ativar Google Ads como bridge (R$3-5K/mes) |

---

## I. Infraestrutura de Indexacao

### I.1 — Google Search Console `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| I1.1 | [ ] Propriedade verificada | GSC > Configuracoes | smartlic.tech verificada |
| I1.2 | [ ] Sitemap submetido e processado | GSC > Sitemaps | "Processado" sem erros |
| I1.3 | [ ] Zero erros de cobertura criticos | GSC > Paginas | Sem erros "Servidor (5xx)", "Nao encontrada (404)" em paginas importantes |
| I1.4 | [ ] Core Web Vitals sem "Poor" | GSC > Experiencia > Core Web Vitals | Zero URLs classificadas "Poor" |
| I1.5 | [ ] Enhancements sem erros | GSC > Melhorias > FAQ, How-to, etc. | Sem erros de schema |

### I.2 — IndexNow Pipeline `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| I2.1 | [ ] GH Action executa pos-deploy | `gh run list --workflow=indexnow.yml --limit=1` | Sucesso na ultima execucao |
| I2.2 | [ ] URLs mapeadas corretamente | Inspecionar output da Action | `page.tsx` → URLs de producao |
| I2.3 | [ ] Resposta 202 do IndexNow | Output da Action | HTTP 202 Accepted |
| I2.4 | [ ] Google Ping dispara | Output da Action | HTTP 200 de google.com/ping |

### I.3 — Sitemap Completo `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| I3.1 | [ ] Total de URLs consistente | Contar URLs no sitemap | >= 2.550 (base) + CNPJ + orgaos + cidade×setor |
| I3.2 | [ ] Sem URLs duplicadas | Verificar uniqueness | Zero duplicatas |
| I3.3 | [ ] Priorities corretas | Spot check | Landing setorial 0.8-0.9, ferramentas 0.8, glossario 0.7, CNPJs 0.5 |
| I3.4 | [ ] lastModified recente | Spot check 5 URLs | Data recente (nao de meses atras) |

---

## D. Distribuicao & Conversao (Parte 7)

### D.1 — Programa de Referral `/indicar` `[SEMANAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| D1.1 | [ ] Pagina `/indicar` acessivel | `curl -sI https://smartlic.tech/indicar` | HTTP 200 |
| D1.2 | [ ] Codigo unico gerado | Login, acessar `/indicar` | Codigo de 8 chars visivel |
| D1.3 | [ ] Botao copiar funcional | Clicar "Copiar link" | Link copiado com `?ref=CODE` |
| D1.4 | [ ] Dashboard stats funcional | Verificar cards (indicados/convertidos/creditos) | 3 cards com dados |
| D1.5 | [ ] Tabela `referrals` existe | Query Supabase | Tabela com 7 colunas, RLS ativo, 3 policies |
| D1.6 | [ ] Signup com `?ref=CODE` funciona | Testar signup com codigo | Referral redimido, localStorage limpo |
| D1.7 | [ ] Webhook Stripe credita mes gratis | Simular conversao | `trial_end` do referrer estendido |
| D1.8 | [ ] Migration aplicada | `supabase migration list --linked` | `20260405100000_referrals.sql` presente |

### D.2 — Trial Email Sequence `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| D2.1 | [ ] Email Day-2 `activation_nudge` | Verificar template + flag `DAY3_ACTIVATION_EMAIL_ENABLED` | Template existe, flag = true em prod |
| D2.2 | [ ] Email Day-8 `referral_invitation` | Verificar flag `REFERRAL_EMAIL_ENABLED` | Template existe, flag conforme desejado |
| D2.3 | [ ] Email `share_activation` (Day 3) | Verificar flag `SHARE_ACTIVATION_EMAIL_ENABLED` | Template existe, flag conforme desejado |
| D2.4 | [ ] Skip conditions funcionais | Verificar logica | Skip se 0 oportunidades encontradas; skip se ja compartilhou |
| D2.5 | [ ] Email Day-16 win-back | Verificar template `TRIAL_COMEBACK_20` | Template existe, cupom valido |

### D.3 — Analytics Events `[MENSAL]`

| # | Verificacao | Como Verificar | Criterio de Sucesso |
|---|------------|---------------|---------------------|
| D3.1 | [ ] `calculadora_completed` | Mixpanel > Events | Evento disparado com setor, uf, resultado_valor |
| D3.2 | [ ] `cnpj_lookup` | Mixpanel > Events | Evento com setor_detectado, uf, total_contratos, score |
| D3.3 | [ ] `share_clicked` | Mixpanel > Events | Evento com channel (LinkedIn/WhatsApp/Twitter/copy) |
| D3.4 | [ ] `analysis_shared` | Mixpanel > Events | Evento ao compartilhar analise |
| D3.5 | [ ] `analysis_viewed` | Mixpanel > Events | Evento ao visualizar `/analise/[hash]` |
| D3.6 | [ ] `first_search` | Mixpanel > Events | Evento single-fire (localStorage) apos primeira busca |
| D3.7 | [ ] `first_analysis_viewed` | Mixpanel > Events | Evento single-fire apos primeira analise |
| D3.8 | [ ] `trial_converted` | Mixpanel > Events | Evento single-fire apos subscription ativada |
| D3.9 | [ ] `referral_shared` | Mixpanel > Events | Evento ao compartilhar link de indicacao |
| D3.10 | [ ] `referral_signed_up` | Mixpanel > Events | Evento ao signup via referral |
| D3.11 | [ ] `referral_converted` | Mixpanel > Events | Evento ao referral converter para pagante |
| D3.12 | [ ] Funil Mixpanel completo | Mixpanel > Funnels | `signup → first_search → first_analysis_viewed → trial_converted` configurado |

### D.4 — Day-3 Activation `[SEMANAL]`

| # | Verificacao | Fonte | Meta |
|---|------------|-------|------|
| D4.1 | [ ] Day-3 activation rate | Mixpanel: % de users com `first_analysis_viewed` ate dia 3 | >= 60% |
| D4.2 | [ ] Day-7 feature depth | Mixpanel: features usadas por usuario no dia 7 | >= 3 features |
| D4.3 | [ ] DAU/MAU no trial | Mixpanel: ratio diario/mensal | >= 25% |

---

## AP. Anti-Patterns (Verificacao Negativa)

> Confirmar que NENHUM destes anti-patterns esta presente.

| # | Anti-Pattern | Como Verificar | Criterio |
|---|-------------|---------------|----------|
| AP.1 | [ ] Copy substituivel | Trocar "SmartLic" por "Licitabot" em headlines | Se fizer sentido → reescrever |
| AP.2 | [ ] Numero sem fonte | Buscar afirmacoes de beneficio nos CTAs | Todo numero precisa de fonte |
| AP.3 | [ ] Artigo de 1 funcao so | Verificar ultimos 3 artigos contra checklist 3-em-1 | Util + Desejavel + Compartilhavel |
| AP.4 | [ ] Conteudo sem dado PNCP | Verificar ultimos artigos | Min 1 dado exclusivo do datalake |
| AP.5 | [ ] Case sem numero | Verificar `/casos` | Todo case tem R$ ou N editais ou horas |
| AP.6 | [ ] Keyword KD > 40 como primaria | Verificar keywords dos ultimos artigos | Evitar KD > 40 com DA < 15 |
| AP.7 | [ ] Calculadora com dados genericos | Testar calculadora | Dados devem vir do datalake PNCP, nao hardcoded |

---

## Pendencias Conhecidas

| # | Item | Status | Referencia Playbook |
|---|------|--------|---------------------|
| PK.1 | Gravar 3 screencasts para masterclass (S13) | PENDENTE | S13, line ~1915 |
| PK.2 | Obter aprovacao de betas para cases P5 (nome real vs anonimizado) | PENDENTE | P5.8, line ~793 |
| PK.3 | Seed authority: Product Hunt, G2, Capterra, Crunchbase (Alavanca 6) | PENDENTE | 10.4, line ~2142 |
| PK.4 | Cloudflare Cache Rules para HTML (cf-cache-status: DYNAMIC) | FOLLOW-UP | Registro Ops, line ~2360 |
| PK.5 | Dashboard Mixpanel manual (funil signup→converted) | PENDENTE | Parte 4, line ~1101 |
| PK.6 | Lead magnet email capture na calculadora/CNPJ (5-10% capture) | IMPLEMENTADO | A2, line ~1069 |
| PK.7 | Win-back sequence pos-expiracao (3 emails adicionais) | PENDENTE | Alavanca 2, line ~2055 |
| PK.8 | Card capture Day 7 (Stripe `trial_end`) | PENDENTE | Alavanca 1, line ~2039 |

---

## Historico de Verificacoes

| Data | Verificador | Secoes | Resultado | Notas |
|------|-------------|--------|-----------|-------|
| _____| _____ | _____ | ___/___OK | _____ |

---

> **Documento espelho de:** `docs/SEO-ORGANIC-PLAYBOOK.md` v3.2 (2026-04-07)
> **Criado em:** 2026-04-08
> **Proxima revisao completa:** quando o playbook original for atualizado
