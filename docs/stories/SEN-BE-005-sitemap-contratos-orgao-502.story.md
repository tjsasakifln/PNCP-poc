# SEN-BE-005: sitemap_contratos_orgao_indexable retorna 502 "JSON could not be generated"

**Status:** Ready
**Origem:** Sentry unresolved — issue 7408168565 (17 evt em 14d)
**Prioridade:** P1 — Alto (SEO orgânico depende de sitemap indexável)
**Complexidade:** S (Small)
**Owner:** @dev + @data-engineer
**Tipo:** SEO / Performance

---

## Problema

`routes.sitemap_orgaos.sitemap_contratos_orgao_indexable` falha com:

```
{'message': 'JSON could not be generated', 'code': 502, 'hint': 'Refer to full message for details', 'details': '<html>\r\n<head><title>502 Bad Gateway</t...'}
```

PostgREST retorna 502 Bad Gateway — o upstream (PgBouncer/Supavisor) ou a query subjacente está falhando/travando. O HTML entrega pista de que é erro de proxy/gateway, não de PostgREST si.

Impacto:
- Sitemap de contratos por órgão (inbound SEO) fica vazio/desatualizado
- 17 eventos/14d = ~1.2/dia — sitemap crawler do Google pode rebaixar ranking
- Relacionado a SEN-BE-007 (slow_request /v1/sitemap/*) — possivelmente mesma causa raiz

---

## Critérios de Aceite

- [ ] **AC1:** Identificar query SQL subjacente (RPC ou raw query) em `backend/routes/sitemap_orgaos.py`
- [ ] **AC2:** Executar query direta em Supabase SQL Editor — medir tempo e confirmar erro PgBouncer
- [ ] **AC3:** Se query >30s: paginar por `orgao_id` em batches (ex.: 1000/batch) — atualmente provavelmente full-scan
- [ ] **AC4:** Cache layer: resposta de sitemap indexable tem TTL 6h (sitemaps não mudam com frequência) — `backend/cache/sitemap_cache.py`
- [ ] **AC5:** Fallback: se RPC falha, retornar último sitemap cacheado em S3/Redis com header `Cache-Control: stale-while-revalidate`
- [ ] **AC6:** Sentry issue `7408168565` não recebe eventos por 48h após fix
- [ ] **AC7:** Validação manual: `curl https://api.smartlic.tech/v1/sitemap/contratos-orgao-indexable` retorna 200 em <10s com payload válido

### Anti-requisitos

- NÃO trocar sitemap-indexable para resposta vazia como fallback — rompe SEO

---

## Referência de implementação

- `backend/routes/sitemap_orgaos.py::sitemap_contratos_orgao_indexable`
- RPC provável em `supabase/migrations/` — buscar `sitemap_contratos_orgao` function
- Padrão de ISR existente em `frontend/` — `export const revalidate = 3600` (ver memory `project_sitemap_serialize_isr_pattern`)

---

## Riscos

- **R1 (Médio):** Cache stale pode servir URL de órgão removido — mitigar com TTL 6h (não 24h)
- **R2 (Baixo):** Paginação aumenta latência total — mas cada batch fica abaixo de statement_timeout

## Dependências

- SEN-BE-007 (slow sitemap endpoints) — coordenar fix

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-23 | @sm | Story criada — issue único, 17 eventos |
| 2026-04-23 | @po | Validação 10/10 → **GO**. LIVE (lastSeen 2026-04-22). Promovida Draft → Ready |
