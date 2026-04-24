# GV-007: Public `/trending/analises` Gallery — Top 20 da Semana

**Priority:** P1
**Effort:** M (8 SP, 4 dias)
**Squad:** @dev + @data-engineer + @ux-design-expert
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 3

---

## Contexto

Lovable fez "Launched" gallery gamificada com upvotes semanais — top apps ganham créditos + geram backlinks. SmartLic pode fazer equivalente mostrando **editais mais analisados** (proxy de demanda de mercado).

Adaptação B2G:
- Público vê "licitações quentes" (sinal de oportunidade)
- Empresa buscante permanece anonimizada (via GV-002)
- Orgão + edital permanecem (dados públicos do PNCP)
- Gera página SEO-friendly + backlink bait jornalístico ("observatório" da semana)

---

## Acceptance Criteria

### AC1: Materialized view trending

- [ ] Migration `supabase/migrations/YYYYMMDDHHMMSS_trending_analyses_mv.sql`:
  ```sql
  CREATE MATERIALIZED VIEW trending_analyses_weekly AS
  SELECT
    licitacao_id,
    COUNT(DISTINCT user_id) AS unique_analyses,
    COUNT(*) AS total_analyses,
    AVG(viability_score) AS avg_viability,
    MAX(created_at) AS last_analysis_at
  FROM search_decision_traces
  WHERE created_at > NOW() - INTERVAL '7 days'
  GROUP BY licitacao_id
  ORDER BY unique_analyses DESC, total_analyses DESC
  LIMIT 100;
  CREATE UNIQUE INDEX ON trending_analyses_weekly(licitacao_id);
  ```
- [ ] Refresh diário 3am BRT via `cron.schedule('refresh-trending', '0 6 * * *', 'REFRESH MATERIALIZED VIEW trending_analyses_weekly')`
- [ ] Include em `cron_job_health` monitoring (CLAUDE.md pattern)

### AC2: Página `/trending/analises`

- [ ] `frontend/app/trending/analises/page.tsx`:
  - SSG + ISR 6h
  - Lista top 20 editais com cards:
    - Título edital (pseudonimizado se sensível)
    - Órgão comprador (dado público, não pseudonimizar)
    - Valor estimado (bucket se opt-in; senão exato)
    - UF + modalidade
    - Badge "Analisado por N empresas esta semana"
    - Viability médio (badge verde/amarelo/vermelho)
    - CTA "Analise você também" → `/buscar?preselect_id={id}`
  - Filtros: setor, UF, valor range (client-side)
  - Paginação (20/página)

### AC3: SEO + Schema.org

- [ ] Meta tags:
  - Title: "Editais Mais Analisados — Semana {YYYY-MM-DD} | SmartLic"
  - Description: "Top 20 licitações que mais empresas analisaram esta semana. Veja oportunidades quentes antes dos concorrentes."
- [ ] JSON-LD `schema.org/ItemList`:
  ```json
  {
    "@type": "ItemList",
    "itemListElement": [
      {"@type": "ListItem", "position": 1, "item": {"@type": "Thing", "name": "Licitação X", "url": "..."}},
      ...
    ]
  }
  ```
- [ ] Include em `frontend/app/sitemap.ts` (ID 3 content/blog)

### AC4: Opt-out empresas

- [ ] Toggle em `frontend/app/settings/privacidade/page.tsx` (já criada em GV-002):
  - "Excluir minhas análises do ranking público /trending"
  - Default OFF (aparecer, mas pseudonimizado como todos)
  - Aplicado em filter do materialized view via JOIN com `profiles`

### AC5: Backlink bait — "Observatório Semanal"

- [ ] `frontend/app/observatorio/semana/[weekSlug]/page.tsx`:
  - Snapshot histórico (semana passada, 2 semanas atrás, etc)
  - Análise jornalística: "R$ X em oportunidades abertas no setor Y"
  - Top 3 insights gerados via LLM
  - Copy-friendly para imprensa ("Dados disponíveis via SmartLic")
- [ ] Sitemap dinâmico inclui últimas 12 semanas

### AC6: Tracking

- [ ] Mixpanel:
  - `trending_gallery_viewed`
  - `trending_licitacao_clicked` (com licitacao_id + position)
  - `trending_cta_analise_clicked`

### AC7: Testes

- [ ] Unit backend aggregation logic
- [ ] Snapshot page component
- [ ] E2E Playwright: user não-logado abre `/trending/analises` → vê ranking → clica → signup
- [ ] Lighthouse ≥90 SEO

---

## Scope

**IN:**
- Materialized view + cron refresh
- Página trending
- Observatório weekly snapshots
- SEO + schema.org
- Opt-out user

**OUT:**
- Upvotes user (complica abuse) — v2
- Gallery de análises individuais por user (privacy B2G) — v3
- Real-time ticker (só refresh diário) — considerado em GV-008

---

## Dependências

- **GV-002** (watermark + pseudonimização) — cards herdam mask
- **GV-003** (trace capturada) — `search_decision_traces` tabela
- `frontend/app/sitemap.ts` existente

---

## Riscos

- **Ranking manipulável:** user spam análises mesmo edital → inflates count. Mitigação: `unique_analyses` count only distinct user_ids + rate limit per (user, licitacao) 5/dia
- **Privacy leak via pattern:** se só 2 empresas analisaram X edital, próximo análise pode ser identificada. Mitigação: floor mínimo de 3 análises para aparecer em trending
- **Cache CDN servindo stale:** `Cache-Control: public, max-age=21600` (6h), respeita ISR Next

---

## Arquivos Impactados

### Novos
- `frontend/app/trending/analises/page.tsx`
- `frontend/app/observatorio/semana/[weekSlug]/page.tsx`
- `supabase/migrations/YYYYMMDDHHMMSS_trending_analyses_mv.sql` (+ down)
- `backend/jobs/cron/refresh_trending.py` (opcional — pg_cron já cobre)
- `backend/tests/test_trending_query.py`

### Modificados
- `frontend/app/sitemap.ts` (incluir /trending/* + /observatorio/*)
- `frontend/app/settings/privacidade/page.tsx` (toggle opt-out, se criado em GV-002)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — Lovable-inspired public gallery adaptado B2G com floor 3 analyses para privacy |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
