# STORY-434: API Pública Read-Only do Datalake — Backlinks Acadêmicos e de Developers

**Priority:** P2
**Effort:** L (3-5 dias)
**Squad:** @dev + @devops
**Status:** Draft
**Epic:** [EPIC-SEO-ORGANIC-2026-04](EPIC-SEO-ORGANIC-2026-04.md)
**Sprint:** Sprint 3

---

## Contexto

O maior gerador de backlinks orgânicos de alta qualidade para SaaS de dados é **disponibilizar os dados publicamente**. Desenvolvedores citam APIs em projetos GitHub. Acadêmicos citam fontes de dados em papers. Jornalistas de dados embutem visualizações que chamam a API. Cada citação = backlink.

**O que o SmartLic tem:** 40K+ licitações ativas no datalake `pncp_raw_bids`, processadas por IA (classificação setorial + score de viabilidade), atualizadas 4x/dia. Nenhum concorrente tem esse dado estruturado publicamente disponível via API.

**A API pública não rivaliza com o produto:** O produto pago oferece busca personalizada, pipeline, IA profunda, relatórios Excel, histórico de sessões. A API pública oferece dados brutos agregados — complementa, não substitui.

**Benchmarks de impacto:**
- APIs públicas de dados geram em média **3-8x mais backlinks** que páginas de conteúdo equivalentes (Ahrefs Content Study 2024)
- Uma API de dados citada em 1 paper acadêmico pode gerar 5-20 backlinks secundários (outros papers que citam o paper)
- Desenvolvedores que usam uma API de dados em projeto aberto linkam no README do GitHub (`github.com` = DA 96)

**Rate limits e segurança:**
- `GET` apenas — sem write, sem mutation
- Rate limit por IP: 60 req/min (sem token), 300 req/min (com API key gratuita)
- Dados públicos do PNCP — nenhuma dado proprietário exposto além de classificação IA e score de viabilidade que são gerados pelo SmartLic

---

## Acceptance Criteria

### AC1: Endpoints da API pública (versão v1)

Criar `backend/routes/public_api.py` com os seguintes endpoints:

- [ ] `GET /api/public/v1/licitacoes` — lista paginada de licitações ativas
  - Query params: `setor`, `uf`, `modalidade`, `valor_min`, `valor_max`, `limit` (max 100), `offset`
  - Response: `{ total: int, items: [...], next_page: str | null, fonte: "PNCP via SmartLic" }`
  - Cada item: `{ id, setor, uf, modalidade, valor_estimado, data_publicacao, data_abertura, orgao_nome, score_viabilidade, classificacao_ia_fonte }`
  
- [ ] `GET /api/public/v1/licitacoes/{id}` — detalhe de 1 licitação por ID
  - Response: todos os campos do item acima + `objeto_descricao` (texto do edital)
  
- [ ] `GET /api/public/v1/stats` — estatísticas agregadas (sem paginação)
  - Query params: `setor`, `uf`, `periodo` (7d, 30d, 90d)
  - Response: `{ total_ativas: int, valor_medio: float, valor_mediano: float, por_modalidade: [...], por_setor: [...], por_uf: [...] }`
  
- [ ] `GET /api/public/v1/setores` — lista dos 20 setores com metadados
  - Response: `{ setores: [{ id, nome, keywords_exemplo: [...], viability_value_range: { min, max } }] }`
  
- [ ] `GET /api/public/v1/health` — health check público da API

### AC2: Rate limiting e autenticação opcional

- [ ] Rate limit sem API key: **60 req/min por IP** — generoso o suficiente para uso legítimo e embeddings
- [ ] API key opcional (gratuita, cadastro simples via email):
  - Endpoint de geração: `POST /api/public/v1/apikey` com `{ email: str }` — envia key por email
  - Com API key: **300 req/min** + acesso ao campo `objeto_descricao` (texto completo)
  - Sem API key: campos básicos apenas, sem `objeto_descricao`
- [ ] Rate limit implementado via Redis (já existe no projeto): `ratelimit:public:{ip}` com TTL 60s
- [ ] Response 429 inclui header `Retry-After: {seconds}` e body `{ error: "Rate limit exceeded. Get a free API key at smartlic.tech/api" }`

### AC3: Documentação da API (OpenAPI / Swagger UI)

- [ ] Swagger UI disponível em `/api/public/docs` — gerado automaticamente pelo FastAPI
- [ ] Cada endpoint tem:
  - `description` completa em português e inglês
  - Exemplo de request e response
  - Descrição dos campos de response
  - Exemplo de código em Python e cURL no description
- [ ] Adicionar header em todos os responses: `X-Data-Source: PNCP via SmartLic Observatório (smartlic.tech)` — branding em cada resposta
- [ ] README da API publicado em `smartlic.tech/api` (página pública)

### AC4: Página de landing da API (`/api`)

- [ ] Criar `frontend/app/api/public/page.tsx` (ou renomear para evitar conflito com API routes do Next.js — verificar)
- [ ] Conteúdo da página:
  - Headline: "API Pública de Dados de Licitações — Gratuita"
  - Descrição: "Acesse dados estruturados do PNCP, processados por IA. 40K+ licitações ativas. Atualização 4x/dia."
  - Exemplos de código embeddáveis (tabs: cURL, Python, JavaScript)
  - Link para `/api/public/docs` (Swagger UI)
  - Formulário de geração de API key (email → recebe key por email via Resend)
  - Seção "Quem usa": espaço para logos de parceiros/usuários (inicialmente vazio, preencher à medida que chegam)
  
- [ ] SEO da página:
  - title: `"API de Licitações Públicas Gratuita — Dados do PNCP | SmartLic"` (58 chars ✓)
  - description: `"API REST gratuita com dados de 40K+ licitações públicas do Brasil. Filtros por setor, UF e modalidade. Processado por IA. Documentação completa."` (146 chars ✓)
  - `robots: { index: true }`

### AC5: CORS e headers de branding

- [ ] CORS: `Access-Control-Allow-Origin: *` para todos os endpoints `/api/public/v1/*`
- [ ] Header `X-Data-Source: PNCP via SmartLic Observatório` em cada response
- [ ] Header `X-Rate-Limit-Remaining: {n}` em cada response
- [ ] Link para documentação no header: `Link: <https://smartlic.tech/api>; rel="documentation"`

### AC6: Distribuição da API (aumentar descoberta)

- [ ] Submeter a `rapidapi.com` — marketplace de APIs com DA 91. Listing gratuito gera backlink + descoberta
- [ ] Submeter a `public-apis.io` (repositório GitHub de APIs públicas, DA 62+) — criar PR adicionando SmartLic à lista
  - Categoria: `Government`
  - Entry format: `| SmartLic Licitações | API de dados de licitações públicas do Brasil (PNCP) | No | Yes | Yes |`
- [ ] Submeter a `apilist.fun` e `apis.guru`
- [ ] Post em `r/datasets` e `r/Brazil` no Reddit: "Free API: Brazilian Public Procurement Data (PNCP processed by AI)"

### AC7: Testes

- [ ] `pytest tests/test_public_api.py` — suite completa:
  - `GET /api/public/v1/licitacoes` com e sem filtros retorna 200
  - Paginação: `limit=100` funciona, `limit=101` retorna 400
  - Rate limit: 61ª request sem API key retorna 429 com `Retry-After`
  - `GET /api/public/v1/stats?setor=informatica&uf=SP` retorna dados corretos
  - CORS: response inclui `Access-Control-Allow-Origin: *`
  - Health: `GET /api/public/v1/health` retorna 200
- [ ] `npm test` passa sem regressões

---

## Scope

**IN:**
- `backend/routes/public_api.py` (novo)
- `frontend/app/[rota-api-landing]/page.tsx` (novo — verificar nome para não conflitar com `/app/api/`)
- Swagger UI via FastAPI (`/api/public/docs`)
- Rate limiting Redis
- API key system simples (email → key)
- Testes

**OUT:**
- Webhooks (eventos em tempo real)
- GraphQL (REST é suficiente para v1)
- SDK em múltiplas linguagens (documentação cURL/Python é suficiente)
- Billing por uso da API (freemium — sempre gratuita no tier básico)

---

## Dependências

- Redis operacional (já está no projeto)
- Resend configurado para enviar API key por email (já está no projeto)
- `pncp_raw_bids` com dados (confirmado)

---

## Riscos

- **Conflito de rota:** `frontend/app/api/` já é usado para API routes do Next.js. A landing page da API pública precisa de um path diferente — sugestão: `/dados-publicos` ou `/dev` para não conflitar
- **Scraping agressivo:** API pública pode atrair bots. Rate limit de 60 req/min por IP mitiga. Adicionar `robots.txt` com `Disallow: /api/public/v1/` para limitar crawlers (não ajuda com bots não-Google, mas é uma camada)
- **Exposição de dados sensíveis:** Verificar que `cnpj_vencedor` e dados de empresas privadas não estão expostos. Expor apenas dados de órgãos públicos (contratante) e texto do edital (público no PNCP)

---

## Dev Notes

_(a preencher pelo @dev durante implementação)_

---

## Arquivos Impactados

- `backend/routes/public_api.py` (novo)
- `backend/main.py` (registrar router)
- `frontend/app/dados-publicos/page.tsx` ou similar (novo)
- `backend/tests/test_public_api.py` (novo)

---

## Definition of Done

- [ ] Todos os 5 endpoints de AC1 retornam dados reais do datalake
- [ ] Rate limit testado: 60 req sem throttle, 61ª retorna 429
- [ ] Swagger UI acessível em `/api/public/docs` com todos os endpoints documentados
- [ ] CORS verificado: embed em página HTML externa funciona
- [ ] Landing `/dados-publicos` (ou similar) publicada em produção
- [ ] Submissão em RapidAPI + `public-apis` GitHub PR criado
- [ ] `pytest tests/test_public_api.py` + `npm test` passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — API pública é o maior gerador de backlinks acadêmicos e de developers. "github.com" (DA 96) aparece quando devs citam a API em READMEs. |
