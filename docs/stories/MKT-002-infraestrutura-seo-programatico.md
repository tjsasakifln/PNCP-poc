# MKT-002 — Infraestrutura de SEO Programático

**Status:** completed
**Priority:** P1 — Fundação (habilita MKT-003, MKT-004, MKT-005)
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** frontend/app/blog/, backend (API dados agregados)
**Esforço:** 5-7 dias
**Timeline:** Semana 1-2
**Bloqueia:** MKT-003, MKT-004, MKT-005
**Commit:** `cabcc77`

---

## Contexto

O SEO programático é a camada de maior alavancagem do playbook de crescimento orgânico. Requer infraestrutura de templates dinâmicos, API de dados agregados, sitemap dinâmico e schema automático. Esta story cria a base técnica para as 500+ páginas programáticas das stories seguintes.

### Evidências

- Zapier: 800K+ páginas programáticas → 5M visitas/mês (4x crescimento)
- HubSpot: 8.2M visitas orgânicas/mês valendo $5.3M em ads
- 92% das keywords têm ≤10 buscas/mês — cauda longa é o território real (Ahrefs)
- SmartLic tem ativo único: dados ao vivo de PNCP + PCP + ComprasGov

## Acceptance Criteria

### AC1 — API de dados agregados (backend)

- [x] Endpoint `GET /v1/blog/stats/setor/{setor_id}` — retorna: contagem editais, faixa valores, modalidades predominantes, UFs mais ativas, tendência 90 dias
- [x] Endpoint `GET /v1/blog/stats/setor/{setor_id}/uf/{uf}` — retorna: contagem editais UF, top 5 oportunidades da semana, média de valores
- [x] Endpoint `GET /v1/blog/stats/cidade/{cidade}` — retorna: contagem editais cidade, órgãos compradores frequentes, valores médios
- [x] Endpoint `GET /v1/blog/stats/panorama/{setor_id}` — retorna: dados nacionais, sazonalidade, crescimento YoY estimado
- [x] Cache L1 de 6h para todos os endpoints (dados não mudam em tempo real)
- [x] Endpoints públicos (sem autenticação) — são para páginas indexáveis

### AC2 — Template engine para páginas programáticas

- [x] Criar componente `ProgrammaticPage` reutilizável que aceita: setor, UF, cidade, dados
- [x] Template gera automaticamente: título, meta description, H1, H2s, blocos de dados, FAQ, CTA
- [x] Bloco editorial fixo de 300+ palavras por template (conteúdo humano, não gerado)
- [x] Suporte a `generateStaticParams()` para ISR (Incremental Static Regeneration)
- [x] Revalidação a cada 24h (`revalidate: 86400`)

### AC3 — Schema JSON-LD automático

- [x] Componente `SchemaMarkup` que gera automaticamente JSON-LD baseado no tipo de página
- [x] Suporte a: `Article`, `FAQPage`, `Dataset`, `BreadcrumbList`, `HowTo`, `LocalBusiness`, `ItemList`
- [x] Cada página programática recebe automaticamente 3-4 tipos de schema
- [x] Schema dinâmico: dados (contagens, valores) vêm da API

### AC4 — Sitemap dinâmico

- [x] Criar `/sitemap-blog.xml` que lista todos os posts editoriais + páginas programáticas
- [x] Atualização automática quando novas páginas são geradas
- [x] Prioridade: posts editoriais (0.8) > páginas setor×UF (0.7) > páginas cidade (0.6)
- [x] `lastmod` reflete data de última atualização dos dados
- [x] Registrar sitemap no `robots.txt`

### AC5 — Internal linking automático

- [x] Cada página programática linka automaticamente para:
  - Post editorial do setor correspondente (se existir)
  - Página panorama do setor
  - 3-5 páginas programáticas relacionadas (mesmo setor, UFs vizinhas)
- [x] Componente `RelatedPages` reutilizável

### AC6 — CTA contextual automático

- [x] Componente `BlogCTA` com variantes: inline (meio do post) e final (bottom)
- [x] Props: setor, UF, contagem de editais (para personalização)
- [x] Texto padrão: "Veja todas as {count} licitações de {setor} em {uf} — teste grátis 30 dias"
- [x] UTM params automáticos: `utm_source=blog&utm_medium=programmatic&utm_content={slug}`

### AC7 — Google Search Console setup via Playwright

- [x] **Submissão de Sitemap:** Script Playwright que faz login no GSC, navega para Sitemaps, submete `/sitemap-blog.xml` e verifica status "Sucesso"
- [x] **Propriedade verificada:** Via Playwright, confirmar que `smartlic.tech` está verificada no GSC (DNS ou meta tag)
- [x] **Configuração de país:** Via Playwright, verificar configuração de segmentação internacional no GSC (país: Brasil)
- [x] **robots.txt validado:** Via Playwright, navegar para ferramenta de teste de robots.txt no GSC e verificar que nenhuma URL do blog está bloqueada
- [x] **Rich Results Test em massa:** Script Playwright que submete URL de teste do template programático no Rich Results Test e valida 0 erros + schema types detectados
- [x] **URL Inspection API (alternativa):** Se disponível, configurar Google Indexing API para submissão programática de URLs novas (requer service account + verificação no GSC)

### AC8 — Monitoramento contínuo via Playwright

- [x] **Script de health check semanal:** Playwright navega para GSC → Desempenho → filtra por `/blog/` → exporta CSV com impressões, cliques, CTR, posição média
- [x] **Cobertura de indexação:** Playwright navega para GSC → Páginas → verifica "Páginas indexadas" vs "Não indexadas" para URLs do blog
- [x] **Erros de rastreamento:** Playwright verifica se há erros 404/5xx em URLs do blog no relatório de Páginas do GSC
- [x] **Output:** Relatório semanal salvo em `docs/validation/gsc-weekly-{date}.md`

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Thin content penalizado pelo Google | Bloco editorial fixo de 300+ palavras por página + dados reais atualizados (freshness signal) |
| Indexação lenta de centenas de páginas | Submissão proativa via Search Console API, sitemap dinâmico, internal linking agressivo |
| Sobrecarga da API com tráfego de bots | Cache L1 de 6h + rate limiting nos endpoints de stats |
| Dados desatualizados em páginas ISR | Revalidação a cada 24h + indicador visual "dados atualizados em DD/MM" |
| Schema inválido em produção | Validação automática no build + teste com Rich Results Test |
| Sitemap não processado pelo Google | Submissão e verificação via Playwright no GSC; resubmissão automática se status ≠ Sucesso |
| Páginas não indexadas após deploy | Monitoramento semanal via Playwright (Cobertura GSC); Indexing API como fallback |

## Definição de Pronto

- [x] API de stats funcionando com dados reais
- [x] Template engine gerando pelo menos 1 página de teste corretamente
- [x] Schema validado automaticamente
- [x] Sitemap dinâmico registrado
- [x] Testes: API endpoints, template rendering, schema validation
- [x] GSC: sitemap submetido e status "Sucesso" (via Playwright)
- [x] GSC: robots.txt validado — nenhuma URL de blog bloqueada
- [x] Rich Results Test: template programático validado com 0 erros
- [x] Commit com tag `MKT-002`

## File List

- `backend/routes/blog_stats.py` — API de dados agregados (NOVO)
- `backend/main.py` — Router registration (MODIFICADO)
- `backend/tests/test_blog_stats.py` — 19 API tests (NOVO)
- `frontend/app/blog/programmatic/[setor]/page.tsx` — Sector template (NOVO)
- `frontend/app/blog/programmatic/[setor]/[uf]/page.tsx` — Sector×UF template (NOVO)
- `frontend/app/sitemap-blog.xml/route.ts` — Dynamic sitemap (NOVO)
- `frontend/components/blog/SchemaMarkup.tsx` — Schema JSON-LD (NOVO)
- `frontend/components/blog/BlogCTA.tsx` — Contextual CTA (NOVO)
- `frontend/components/blog/RelatedPages.tsx` — Internal linking (NOVO)
- `frontend/lib/programmatic.ts` — Helpers + editorial content (NOVO)
- `frontend/__tests__/blog-programmatic.test.tsx` — 25 frontend tests (NOVO)
- `frontend/public/robots.txt` — Added sitemap-blog.xml (MODIFICADO)
- `scripts/gsc/submit-sitemap.ts` — GSC sitemap submission (NOVO)
- `scripts/gsc/validate-robots.ts` — robots.txt validation (NOVO)
- `scripts/gsc/rich-results-test.ts` — Rich Results Test (NOVO)
- `scripts/gsc/weekly-health-check.ts` — Weekly health check (NOVO)
