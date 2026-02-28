# STORY-324: Landing Pages Programaticas por Setor (SEO)

**Epic:** EPIC-TURBOCASH-2026-03
**Sprint:** Sprint 3 (Scalable Revenue)
**Priority:** P2 — MEDIUM
**Story Points:** 13 SP
**Estimate:** 6-8 dias
**Owner:** @dev + @ux-design-expert
**Origem:** TurboCash Playbook — Acao 8 (Content-Led Acquisition, dia 90+)

---

## Problem

O SmartLic nao tem presenca organica em buscas como "oportunidades de licitacao [setor]" ou "licitacoes abertas [setor]". Todo o trafego depende de outreach direto. Para atingir 50-100 trials organicos/mes, precisamos de 15 landing pages otimizadas para SEO — uma por setor.

## Solution

Criar 15 paginas programaticas em `/licitacoes/[setor-slug]` com conteudo dinamico:
- Dados reais de licitacoes abertas (atualizados diariamente via cache)
- Estatisticas do setor (volume, valor medio, UFs com mais oportunidades)
- CTA para trial do SmartLic
- Schema markup (JSON-LD) para rich snippets no Google

**Evidencia:** ConLicitacao tem 16K clientes — boa parte via SEO organico.

---

## Acceptance Criteria

### Backend — API de Dados por Setor

- [x] **AC1:** Endpoint publico `GET /v1/sectors/{slug}/stats` (sem auth):
  - `total_open` — licitacoes abertas no setor (ultimos 10 dias)
  - `total_value` — valor estimado total
  - `avg_value` — valor medio
  - `top_ufs` — top 5 UFs por volume (array)
  - `top_modalidades` — top 3 modalidades (array)
  - `sample_items` — 5 licitacoes reais (titulo, orgao, valor, UF, data) como preview
  - `last_updated` — timestamp
- [x] **AC2:** Cache de 6h (L1 InMemory) para o endpoint — dados nao precisam ser real-time
- [x] **AC3:** Cron job diario: atualiza stats de todos os 15 setores (06:00 UTC)
- [x] **AC4:** `sample_items` nao expoe dados sensiveis (sem IDs internos, sem links diretos)

### Frontend — Paginas Programaticas

- [x] **AC5:** Rota `frontend/app/licitacoes/[setor]/page.tsx` (SSG com ISR 6h):
  - Renderiza no servidor para SEO (Next.js generateStaticParams)
  - Revalida a cada 6h (ISR)
- [x] **AC6:** Layout da pagina:
  - Hero: "Licitacoes de {Setor} — {N} oportunidades abertas"
  - Stats cards: total aberto, valor total, valor medio, top UFs
  - Tabela preview: 5 licitacoes (titulo truncado, orgao, valor, UF, prazo)
  - CTA: "Veja todas as {N} oportunidades — 14 dias gratis"
  - Secao "Como funciona": 3 passos (buscar → filtrar → analisar)
  - FAQ: 4-5 perguntas sobre licitacoes no setor
  - Footer: links para outros setores
- [x] **AC7:** Cada pagina usa dados de `sectors_data.yaml` (nome, descricao, keywords)
- [x] **AC8:** Slug mapping: `backend/sectors_data.yaml` → slug (ex: "manutencao_predial" → "manutencao-predial")

### Frontend — SEO

- [x] **AC9:** Meta tags por pagina:
  - `<title>`: "Licitacoes de {Setor} — {N} Oportunidades Abertas | SmartLic"
  - `<meta description>`: "Encontre {N} licitacoes abertas de {Setor} em {top UFs}. Analise com IA e score de viabilidade. 14 dias gratis."
  - `<link rel="canonical">`: URL canonica
- [x] **AC10:** JSON-LD Schema markup (WebPage + ItemList para sample_items + FAQPage)
- [x] **AC11:** Open Graph tags para compartilhamento social
- [x] **AC12:** Sitemap automatico: `frontend/app/sitemap.ts` inclui todas as 15 paginas
- [x] **AC13:** `robots.txt` permite crawling das paginas

### Frontend — Navegacao

- [x] **AC14:** Pagina index `/licitacoes` com grid de 15 setores (card por setor com stats resumidos)
- [x] **AC15:** Footer do site inclui links para as 15 paginas de setor
- [x] **AC16:** Links internos entre paginas de setor ("Setores relacionados")

### Conteudo — FAQ por Setor

- [x] **AC17:** Criar `frontend/data/sector-faqs.ts` com 4-5 FAQs por setor:
  - "Quais tipos de licitacao existem em {Setor}?"
  - "Como encontrar licitacoes de {Setor} no PNCP?"
  - "Qual o valor medio das licitacoes de {Setor}?"
  - "Como o SmartLic ajuda empresas de {Setor}?"
  - FAQ especifica do setor

### Testes

- [x] **AC18:** Testes backend: endpoint retorna stats corretos (24 tests, all pass)
- [x] **AC19:** Testes frontend: pagina renderiza com dados (35 tests, all pass)
- [x] **AC20:** Testes SEO: meta tags, JSON-LD, sitemap incluem paginas
- [x] **AC21:** Zero regressions (pending full suite confirmation)

---

## Files Changed

**New:**
- `backend/routes/sectors_public.py` — Public sector stats endpoint + cron helper
- `backend/tests/test_sectors_public.py` — 24 backend tests
- `frontend/lib/sectors.ts` — Sector metadata, API helpers, formatBRL
- `frontend/data/sector-faqs.ts` — 4-5 FAQs per sector (15 sectors)
- `frontend/app/licitacoes/page.tsx` — Sector index page (grid of 15)
- `frontend/app/licitacoes/[setor]/page.tsx` — Sector detail page (SSG + ISR 6h)
- `frontend/__tests__/licitacoes/sector-pages.test.tsx` — 35 frontend tests

**Modified:**
- `backend/main.py` — Register sectors_public router + start cron job
- `backend/cron_jobs.py` — Daily sector stats refresh at 06:00 UTC
- `frontend/app/sitemap.ts` — Added 15 sector pages + index
- `frontend/app/components/Footer.tsx` — Added "Setores" column with links
- `frontend/public/robots.txt` — Added Allow: /licitacoes
- `frontend/jest.config.js` — Added @/data/ path mapping

## Dependencias

- STORY-319 (trial 14 dias) — CTA referencia "14 dias gratis"
- `sectors_data.yaml` — fonte de verdade para os 15 setores
