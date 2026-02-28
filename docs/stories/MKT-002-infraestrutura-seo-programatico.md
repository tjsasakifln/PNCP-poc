# MKT-002 — Infraestrutura de SEO Programático

**Status:** pending
**Priority:** P1 — Fundação (habilita MKT-003, MKT-004, MKT-005)
**Origem:** Conselho CMO Advisory Board (2026-02-27)
**Componentes:** frontend/app/blog/, backend (API dados agregados)
**Esforço:** 5-7 dias
**Timeline:** Semana 1-2
**Bloqueia:** MKT-003, MKT-004, MKT-005

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

- [ ] Endpoint `GET /v1/blog/stats/setor/{setor_id}` — retorna: contagem editais, faixa valores, modalidades predominantes, UFs mais ativas, tendência 90 dias
- [ ] Endpoint `GET /v1/blog/stats/setor/{setor_id}/uf/{uf}` — retorna: contagem editais UF, top 5 oportunidades da semana, média de valores
- [ ] Endpoint `GET /v1/blog/stats/cidade/{cidade}` — retorna: contagem editais cidade, órgãos compradores frequentes, valores médios
- [ ] Endpoint `GET /v1/blog/stats/panorama/{setor_id}` — retorna: dados nacionais, sazonalidade, crescimento YoY estimado
- [ ] Cache L1 de 6h para todos os endpoints (dados não mudam em tempo real)
- [ ] Endpoints públicos (sem autenticação) — são para páginas indexáveis

### AC2 — Template engine para páginas programáticas

- [ ] Criar componente `ProgrammaticPage` reutilizável que aceita: setor, UF, cidade, dados
- [ ] Template gera automaticamente: título, meta description, H1, H2s, blocos de dados, FAQ, CTA
- [ ] Bloco editorial fixo de 300+ palavras por template (conteúdo humano, não gerado)
- [ ] Suporte a `generateStaticParams()` para ISR (Incremental Static Regeneration)
- [ ] Revalidação a cada 24h (`revalidate: 86400`)

### AC3 — Schema JSON-LD automático

- [ ] Componente `SchemaMarkup` que gera automaticamente JSON-LD baseado no tipo de página
- [ ] Suporte a: `Article`, `FAQPage`, `Dataset`, `BreadcrumbList`, `HowTo`, `LocalBusiness`, `ItemList`
- [ ] Cada página programática recebe automaticamente 3-4 tipos de schema
- [ ] Schema dinâmico: dados (contagens, valores) vêm da API

### AC4 — Sitemap dinâmico

- [ ] Criar `/sitemap-blog.xml` que lista todos os posts editoriais + páginas programáticas
- [ ] Atualização automática quando novas páginas são geradas
- [ ] Prioridade: posts editoriais (0.8) > páginas setor×UF (0.7) > páginas cidade (0.6)
- [ ] `lastmod` reflete data de última atualização dos dados
- [ ] Registrar sitemap no `robots.txt`

### AC5 — Internal linking automático

- [ ] Cada página programática linka automaticamente para:
  - Post editorial do setor correspondente (se existir)
  - Página panorama do setor
  - 3-5 páginas programáticas relacionadas (mesmo setor, UFs vizinhas)
- [ ] Componente `RelatedPages` reutilizável

### AC6 — CTA contextual automático

- [ ] Componente `BlogCTA` com variantes: inline (meio do post) e final (bottom)
- [ ] Props: setor, UF, contagem de editais (para personalização)
- [ ] Texto padrão: "Veja todas as {count} licitações de {setor} em {uf} — teste grátis 30 dias"
- [ ] UTM params automáticos: `utm_source=blog&utm_medium=programmatic&utm_content={slug}`

## Mitigações

| Risco | Mitigação |
|-------|-----------|
| Thin content penalizado pelo Google | Bloco editorial fixo de 300+ palavras por página + dados reais atualizados (freshness signal) |
| Indexação lenta de centenas de páginas | Submissão proativa via Search Console API, sitemap dinâmico, internal linking agressivo |
| Sobrecarga da API com tráfego de bots | Cache L1 de 6h + rate limiting nos endpoints de stats |
| Dados desatualizados em páginas ISR | Revalidação a cada 24h + indicador visual "dados atualizados em DD/MM" |
| Schema inválido em produção | Validação automática no build + teste com Rich Results Test |

## Definição de Pronto

- [ ] API de stats funcionando com dados reais
- [ ] Template engine gerando pelo menos 1 página de teste corretamente
- [ ] Schema validado automaticamente
- [ ] Sitemap dinâmico registrado
- [ ] Testes: API endpoints, template rendering, schema validation
- [ ] Commit com tag `MKT-002`

## File List

- `backend/routes/blog_stats.py` — API de dados agregados (NOVO)
- `frontend/app/blog/programmatic/` — templates programáticos (NOVO)
- `frontend/components/blog/SchemaMarkup.tsx` — schema automático (NOVO)
- `frontend/components/blog/BlogCTA.tsx` — CTAs (NOVO)
- `frontend/components/blog/RelatedPages.tsx` — internal linking (NOVO)
- `frontend/app/sitemap-blog.xml/route.ts` — sitemap dinâmico (NOVO)
