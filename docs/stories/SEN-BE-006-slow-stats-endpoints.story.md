# SEN-BE-006: Slow-request warnings saturando endpoints de stats (blog/contratos/fornecedores)

**Status:** Ready
**Origem:** Sentry unresolved — ~70 issues slow_request em rotas `/v1/contratos/*/stats`, `/v1/fornecedores/*/stats`, `/v1/blog/stats/setor/*`, `/v1/blog/stats/contratos/*`
**Prioridade:** P1 — Alto (timeouts repetidos em 1069s — muito acima do limite Railway 120s)
**Complexidade:** L (Large)
**Owner:** @data-engineer + @dev
**Tipo:** Performance

---

## Problema

Cerca de 70 issues warning do tipo `slow_request` registram latências entre **1069s e 1682s** em endpoints de estatísticas públicas usados pelo SEO orgânico e perfis B2G:

Padrões de URL afetados (samples):
- `GET /v1/contratos/{setor}/{uf}/stats` — ex.: `/v1/contratos/transporte/go/stats` (1069.2s)
- `GET /v1/fornecedores/{setor}/{uf}/stats` — ex.: `/v1/fornecedores/software/rn/stats` (1069.6s)
- `GET /v1/blog/stats/setor/{setor}/uf/{uf}` — ex.: `/v1/blog/stats/setor/vigilancia/uf/RR` (1069.3s)
- `GET /v1/blog/stats/contratos/{setor}/uf/{uf}` — ex.: `/v1/blog/stats/contratos/medicamentos/uf/ES` (148.2s)

Observações:
- Latências de 1069-1682s indicam que o processo é morto só pelo `GUNICORN_TIMEOUT=180s` após vários kill/restart
- Railway proxy já devolveu 502 ao cliente em ~120s — usuário nunca vê resposta
- Combinação `setor × UF × 27 UFs × 15 setores` → crawler pode estar tentando matrix completa simultânea

---

## Critérios de Aceite

- [ ] **AC1:** Medir baseline de p95 em cada família de rota (contratos/fornecedores/blog-stats) via `smartlic_request_duration_seconds_bucket`
- [ ] **AC2:** EXPLAIN ANALYZE das 3 queries representativas (uma por família) documentado em `docs/explain-plans/SEN-BE-006.md`
- [ ] **AC3:** Índices novos criados via migration `supabase/migrations/YYYYMMDDHHMMSS_sen_be_006_stats_indexes.sql` + `.down.sql` — esperada queda >10x na query de pior caso
- [ ] **AC4:** Cache L2 (Supabase ou Redis) com TTL 1h para estas rotas (dados são agregados diários/semanais, 1h staleness tolerável)
- [ ] **AC5:** Rate limit por IP nas rotas de stats (ex.: 10 req/min) para evitar crawler bater todas as combinações simultâneas
- [ ] **AC6:** Após deploy, nenhum novo warning slow_request com >60s nessas rotas por 7 dias consecutivos
- [ ] **AC7:** Sitemap/CDN-friendly: adicionar `Cache-Control: public, max-age=3600, stale-while-revalidate=86400` nas responses

### Anti-requisitos

- NÃO remover os endpoints — são usados por SEO orgânico (ver `supplier_contracts` ~2M rows feeding SEO inbound)
- NÃO pré-gerar 27×15=405 combinações em cron job — volume grande demais para Supabase schedule

---

## Referência de implementação

Arquivos prováveis:
- `backend/routes/contratos_publicos.py`
- `backend/routes/fornecedores_publicos.py`
- `backend/routes/blog_stats.py` ou similar
- `backend/cache/` — estender para `stats_cache.py`

Padrão existente: `search_results_cache` (Supabase) 24h TTL. Aplicar padrão similar.

---

## Riscos

- **R1 (Alto):** Crawlers externos (Google, Bing) podem estar causando o traffic spike — verificar `User-Agent` nos eventos; rate limit com allowlist para bots legítimos
- **R2 (Médio):** Cache 1h pode servir stat desatualizado se `supplier_contracts` receber ingestão intraday — aceitar staleness, confirmar com @po
- **R3 (Baixo):** Índices novos em `supplier_contracts` (~2M rows) precisam `CREATE INDEX CONCURRENTLY`

## Dependências

- SEN-BE-001 (statement_timeout) — compartilha causa raiz em queries de supplier_contracts
- SEN-BE-005 (sitemap 502) — provavelmente mesma causa estrutural

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — ~70 issues clustered, centenas de eventos |
| 2026-04-23 | @po | Validação 10/10 → **GO**. LIVE (lastSeen 2026-04-22). Promovida Draft → Ready |
