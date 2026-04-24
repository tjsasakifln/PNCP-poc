# SEN-BE-007: Slow-request em `/v1/sitemap/*` (1428s–1682s)

**Status:** Ready
**Origem:** Sentry unresolved — issues 7409549200 (sitemap/orgaos 1682s 40evt), 7409549180 (sitemap/itens 1682s 39evt), 7409548146 (sitemap/fornecedores-cnpj 1682s 39evt), 7409501067 (sitemap/cnpjs 1680s 39evt), 7409535162 (sitemap/municipios 1427s 37evt), 7405051391 (sitemap/licitacoes-indexable 104s 30evt), 7406847188 (sitemap/contratos-orgao-indexable 318s 47evt)
**Prioridade:** P1 — Alto (sitemap é base do SEO programmatic)
**Complexidade:** M (Medium)
**Owner:** @data-engineer + @dev
**Tipo:** SEO / Performance

---

## Problema

Endpoints de sitemap em `/v1/sitemap/*` estão demorando entre **104s e 1682s** (i.e., 1.7s a 28min). Railway proxy mata em 120s — crawler do Google recebe 502.

Rotas afetadas (7 issues):
- `/v1/sitemap/orgaos` (1682s, 40 evt)
- `/v1/sitemap/itens` (1682s, 39 evt)
- `/v1/sitemap/fornecedores-cnpj` (1682s, 39 evt)
- `/v1/sitemap/cnpjs` (1680s, 39 evt)
- `/v1/sitemap/municipios` (1427s, 37 evt)
- `/v1/sitemap/contratos-orgao-indexable` (318s, 47 evt)
- `/v1/sitemap/licitacoes-indexable` (104s, 30 evt)

Impacto:
- Google Search Console reporta sitemap error → páginas caem do índice
- Frontend `sitemap.ts` (Next.js) pode estar fazendo fetch sequencial deste backend (ver memory `project_sitemap_serialize_isr_pattern`)

---

## Critérios de Aceite

- [ ] **AC1:** Cada rota de sitemap tem query paginada em LIMIT 5000/página — evita full-scan de tabelas 2M rows
- [ ] **AC2:** Resposta cacheada em L2 (Supabase ou Redis) com TTL **6h** — sitemap não muda com frequência
- [ ] **AC3:** Fallback: endpoint retorna último sitemap válido cacheado (stale-while-revalidate) se query live falhar
- [ ] **AC4:** Migration de índices em supplier_contracts/pncp_raw_bids para suportar sitemap (confirmar via EXPLAIN)
- [ ] **AC5:** Header `Cache-Control: public, max-age=21600, stale-while-revalidate=86400` nas responses
- [ ] **AC6:** p95 de cada rota cai abaixo de 30s (medido via Prometheus 7 dias pós-fix)
- [ ] **AC7:** Issues Sentry listadas acima param de receber novos eventos por 72h
- [ ] **AC8:** Sitemap submetido ao GSC (via `gh` ou dashboard) retorna "Success" em `curl -I`

### Anti-requisitos

- NÃO truncar sitemaps a <5000 URLs — perderia cobertura
- NÃO pré-gerar sitemap em cron se payload for compressível via cache L2

---

## Referência de implementação

Arquivos prováveis:
- `backend/routes/sitemap_*.py` (orgaos, itens, fornecedores, cnpjs, municipios, licitacoes)
- `backend/cache/sitemap_cache.py` (criar se não existir)
- `frontend/app/sitemap.ts` + sitemaps namespaced em `frontend/app/sitemaps/*`

Pattern sitemap serializado (memory `project_sitemap_serialize_isr_pattern` 2026-04-21): substituir `Promise.all` por `await` sequencial no frontend caller também.

---

## Riscos

- **R1 (Alto):** 5000 URLs/sitemap respeita limite Google (50k max) mas gera múltiplos arquivos — precisa sitemap index
- **R2 (Médio):** Cache 6h pode servir sitemap sem URL nova criada hoje — aceitar, Google recrawl em 24h

## Dependências

- SEN-BE-005 (contratos-orgao-indexable 502) — mesma causa
- SEN-BE-006 (slow stats) — compartilha índices de `supplier_contracts`

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — 7 issues sitemap, 270+ eventos combinados |
| 2026-04-23 | @po | Validação 10/10 → **GO**. LIVE (lastSeen 2026-04-22). Promovida Draft → Ready |
