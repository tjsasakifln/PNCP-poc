# MON-SEO-04: Sitemaps Dinâmicos Escaláveis + Fix Bug `sitemap/4.xml`

**Priority:** P0
**Effort:** M (3 dias)
**Squad:** @dev + @devops
**Status:** Draft
**Epic:** [EPIC-MON-SEO-2026-04](EPIC-MON-SEO-2026-04.md)
**Sprint:** Wave 3 (standalone, fix urgente)

---

## Contexto

**Bug crítico:** `sitemap/4.xml` está retornando vazio em produção. Causa provável (memoria do Explore agent): `BACKEND_URL` env var missing em build Railway frontend → fetch para backend falha silenciosamente → sitemap fallback vazio.

**Além do bug:** precisamos escalar sitemap para **2M+ URLs de fornecedor + 5k de categoria + 15k de órgão**. Google enforce 50k URLs/sitemap. Solução: `sitemap_index.xml` apontando para shards.

---

## Acceptance Criteria

### AC1: Diagnóstico + fix sitemap/4.xml

- [ ] Investigar em `frontend/app/sitemap.ts` linhas 43-56 (fetch do backend)
- [ ] Validar `BACKEND_URL` no build Railway: via `railway variables --service bidiq-frontend | grep BACKEND_URL`
- [ ] Se missing: adicionar no Railway service
- [ ] Fallback defensivo: se fetch falha, log Sentry error + não retornar vazio (emitir sitemap parcial com alertas)

### AC2: Sitemap index com shards

- [ ] `frontend/app/sitemap_index.xml/route.ts` gera índice:
```xml
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://smartlic.tech/sitemap-static.xml</loc></sitemap>
  <sitemap><loc>https://smartlic.tech/sitemap-blog.xml</loc></sitemap>
  <sitemap><loc>https://smartlic.tech/sitemap-fornecedores-0.xml</loc></sitemap>
  ...
  <sitemap><loc>https://smartlic.tech/sitemap-fornecedores-99.xml</loc></sitemap>
  <sitemap><loc>https://smartlic.tech/sitemap-categorias-a.xml</loc></sitemap>
  ...
  <sitemap><loc>https://smartlic.tech/sitemap-orgaos.xml</loc></sitemap>
</sitemapindex>
```

### AC3: Shards de fornecedores

- [ ] `frontend/app/sitemap-fornecedores-[shard]/route.ts`:
  - Shard por 2 primeiros dígitos de CNPJ (00-99, máximo 100 shards)
  - Cada shard consulta backend para CNPJs únicos + `lastmod` do último contrato
  - Priority: 0.8 se `total_valor > R$ 1M`, 0.5 default
  - Caching: Cache-Control `public, max-age=3600` (1h)

### AC4: Shards de categorias

- [ ] `frontend/app/sitemap-categorias-[letter]/route.ts`:
  - Shard por primeira letra do slug (26 shards máximo)
  - Apenas slugs com `sample_size >= 10` (thin content gate)

### AC5: Single sitemap órgãos

- [ ] `frontend/app/sitemap-orgaos/route.ts` — único (15k URLs cabem em 1 sitemap)

### AC6: Atualização robots.txt

- [ ] `frontend/app/robots.ts` referencia `sitemap_index.xml`
- [ ] Disallow endpoints privados (`/conta`, `/admin`)

### AC7: Monitoring

- [ ] Cron diário `audit_sitemap_health_job`: verifica todos os shards retornam >0 URLs, log Sentry se qualquer falha
- [ ] Prometheus: `smartlic_sitemap_urls_total{shard}`

### AC8: Google Search Console re-submit

- [ ] Após deploy: resubmit `sitemap_index.xml` no GSC
- [ ] Monitorar indexação semanalmente por 4 semanas

### AC9: Testes

- [ ] Integration: todos os shards retornam XML válido (schema W3C)
- [ ] Performance: shard fornecedores com 20k URLs gera em <5s (SSR)

---

## Scope

**IN:**
- Fix bug sitemap/4.xml
- Sitemap index + shards
- Monitoring cron
- Robots.txt update
- Testes

**OUT:**
- hreflang (v2 se lançar internacional)
- Image/Video sitemaps (não aplicável)

---

## Dependências

- Backend endpoints expostos (pncp_supplier_contracts, catmat_catser_catalog, orgaos)
- Railway env vars acessíveis

---

## Riscos

- **Googlebot crawl budget runaway:** 2M URLs alta carga; priorizar top via `<priority>` + monitorar no GSC
- **Shard overflow:** se 1 shard exceder 50k URLs, Google ignora; validar com query `SELECT count(DISTINCT ni_fornecedor) WHERE LEFT(ni_fornecedor, 2) = '00' ...` — se >50k, sub-shardar

---

## Dev Notes

_(a preencher pelo @dev)_

---

## Arquivos Impactados

- `frontend/app/sitemap_index.xml/route.ts` (novo)
- `frontend/app/sitemap-fornecedores-[shard]/route.ts` (novo)
- `frontend/app/sitemap-categorias-[letter]/route.ts` (novo)
- `frontend/app/sitemap-orgaos/route.ts` (novo)
- `frontend/app/sitemap-static.xml/route.ts` (novo — URLs estáticas)
- `frontend/app/sitemap-blog.xml/route.ts` (estender se existe)
- `frontend/app/sitemap.ts` (remover/substituir pelo index)
- `frontend/app/robots.ts` (estender)
- `backend/routes/sitemap_fornecedores.py` (novo — data fetcher)
- `backend/routes/sitemap_categorias.py` (novo)
- `backend/jobs/cron/sitemap_health.py` (novo)

---

## Definition of Done

- [ ] sitemap_index.xml retorna 200 com todos shards listados
- [ ] Sitemap/4.xml original bug resolvido
- [ ] 100+ shards de fornecedores renderizam
- [ ] 26 shards de categorias renderizam
- [ ] GSC re-submit feito
- [ ] Cron de monitoring ativo
- [ ] Testes passando

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Story criada — fix de bug crítico + infra escalável de sitemap |
