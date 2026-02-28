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

- [ ] **AC1:** Endpoint publico `GET /v1/sectors/{slug}/stats` (sem auth):
  - `total_open` — licitacoes abertas no setor (ultimos 10 dias)
  - `total_value` — valor estimado total
  - `avg_value` — valor medio
  - `top_ufs` — top 5 UFs por volume (array)
  - `top_modalidades` — top 3 modalidades (array)
  - `sample_items` — 5 licitacoes reais (titulo, orgao, valor, UF, data) como preview
  - `last_updated` — timestamp
- [ ] **AC2:** Cache de 6h (L1 InMemory) para o endpoint — dados nao precisam ser real-time
- [ ] **AC3:** Cron job diario: atualiza stats de todos os 15 setores (06:00 UTC)
- [ ] **AC4:** `sample_items` nao expoe dados sensiveis (sem IDs internos, sem links diretos)

### Frontend — Paginas Programaticas

- [ ] **AC5:** Rota `frontend/app/licitacoes/[setor]/page.tsx` (SSG com ISR 6h):
  - Renderiza no servidor para SEO (Next.js generateStaticParams)
  - Revalida a cada 6h (ISR)
- [ ] **AC6:** Layout da pagina:
  - Hero: "Licitacoes de {Setor} — {N} oportunidades abertas"
  - Stats cards: total aberto, valor total, valor medio, top UFs
  - Tabela preview: 5 licitacoes (titulo truncado, orgao, valor, UF, prazo)
  - CTA: "Veja todas as {N} oportunidades — 14 dias gratis"
  - Secao "Como funciona": 3 passos (buscar → filtrar → analisar)
  - FAQ: 4-5 perguntas sobre licitacoes no setor
  - Footer: links para outros setores
- [ ] **AC7:** Cada pagina usa dados de `sectors_data.yaml` (nome, descricao, keywords)
- [ ] **AC8:** Slug mapping: `backend/sectors_data.yaml` → slug (ex: "Construcao Civil" → "construcao-civil")

### Frontend — SEO

- [ ] **AC9:** Meta tags por pagina:
  - `<title>`: "Licitacoes de {Setor} — {N} Oportunidades Abertas | SmartLic"
  - `<meta description>`: "Encontre {N} licitacoes abertas de {Setor} em {top UFs}. Analise com IA e score de viabilidade. 14 dias gratis."
  - `<link rel="canonical">`: URL canonica
- [ ] **AC10:** JSON-LD Schema markup (WebPage + ItemList para sample_items)
- [ ] **AC11:** Open Graph tags para compartilhamento social
- [ ] **AC12:** Sitemap automatico: `frontend/app/sitemap.ts` inclui todas as 15 paginas
- [ ] **AC13:** `robots.txt` permite crawling das paginas

### Frontend — Navegacao

- [ ] **AC14:** Pagina index `/licitacoes` com grid de 15 setores (card por setor com stats resumidos)
- [ ] **AC15:** Footer do site inclui links para as 15 paginas de setor
- [ ] **AC16:** Links internos entre paginas de setor ("Setores relacionados")

### Conteudo — FAQ por Setor

- [ ] **AC17:** Criar `frontend/data/sector-faqs.ts` com 4-5 FAQs por setor:
  - "Quais tipos de licitacao existem em {Setor}?"
  - "Como encontrar licitacoes de {Setor} no PNCP?"
  - "Qual o valor medio das licitacoes de {Setor}?"
  - "Como o SmartLic ajuda empresas de {Setor}?"
  - FAQ especifica do setor (ex: TI tem "Pregao eletronico para TI?")

### Testes

- [ ] **AC18:** Testes backend: endpoint retorna stats corretos
- [ ] **AC19:** Testes frontend: pagina renderiza com dados
- [ ] **AC20:** Testes SEO: meta tags, JSON-LD, sitemap incluem paginas
- [ ] **AC21:** Zero regressions

---

## Os 15 Setores (de sectors_data.yaml)

| # | Setor | Slug |
|---|-------|------|
| 1 | Construcao Civil | construcao-civil |
| 2 | Tecnologia da Informacao | tecnologia-da-informacao |
| 3 | Saude | saude |
| 4 | Alimentacao | alimentacao |
| 5 | Seguranca | seguranca |
| 6 | Limpeza e Conservacao | limpeza-e-conservacao |
| 7 | Educacao | educacao |
| 8 | Transporte e Logistica | transporte-e-logistica |
| 9 | Engenharia Ambiental | engenharia-ambiental |
| 10 | Comunicacao e Marketing | comunicacao-e-marketing |
| 11 | Consultoria e Assessoria | consultoria-e-assessoria |
| 12 | Energia | energia |
| 13 | Agropecuaria | agropecuaria |
| 14 | Mobiliario e Equipamentos | mobiliario-e-equipamentos |
| 15 | Vestuario e Textil | vestuario-e-textil |

## Files Esperados (Output)

**Novos:**
- `backend/routes/sectors_public.py`
- `backend/tests/test_sectors_public.py`
- `frontend/app/licitacoes/page.tsx` (index)
- `frontend/app/licitacoes/[setor]/page.tsx` (pagina por setor)
- `frontend/data/sector-faqs.ts`
- `frontend/__tests__/licitacoes/sector-page.test.tsx`

**Modificados:**
- `backend/main.py` (registrar router)
- `backend/cron_jobs.py` (cron de stats)
- `frontend/app/sitemap.ts`
- `frontend/app/layout.tsx` (footer links)

## Dependencias

- STORY-319 (trial 14 dias) — CTA referencia "14 dias gratis"
- `sectors_data.yaml` — fonte de verdade para os 15 setores
- Relacionada: MKT-005 (landing pages por cidade — complementar, nao sobrepor)

## Riscos

- Dados desatualizados se cron falhar → fallback para "Veja oportunidades atualizadas"
- Google pode demorar 2-4 semanas para indexar → submeter via Google Search Console
- Conteudo gerado pode parecer "thin" para Google → FAQs e copy manual ajudam
