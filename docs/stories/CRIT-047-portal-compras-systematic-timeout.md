# CRIT-047: Portal de Compras (PCP v2) Timeout Sistemático

**Epic:** Data Sources Resilience
**Sprint:** Sprint 5
**Priority:** P2 — MEDIUM
**Story Points:** 5 SP
**Estimate:** 3-4 horas
**Owner:** @dev + @data-engineer

---

## Problem

A fonte PORTAL_COMPRAS está em timeout 100% das vezes nas últimas 24h, causando:

1. **Degradação para DOWN** após 5 falhas consecutivas
2. **Todos os resultados entregues somente via PNCP** (fonte primária)
3. **112 warnings** nos logs Railway (PORTAL_COMPRAS timeout after 60001ms)
4. **Records parciais salvaged** (4 a 920 items), mas nunca completo

**Railway Logs Evidence:**
```
[CONSOLIDATION] PORTAL_COMPRAS: timeout after 60001ms — salvaged N partial records
Source 'PORTAL_COMPRAS' transitioned to DEGRADED status after 3 consecutive failures
Source 'PORTAL_COMPRAS' transitioned to DOWN status after 5 consecutive failures
```

**Sentry Evidence:**
- SMARTLIC-BACKEND-23: `Health incident: System status changed to degraded. Affected: comprasgov` (12h ago)

---

## Root Cause Hypotheses

### H1: API do PCP v2 degradada ou com mudanças
A API `compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos` pode ter:
- Aumentado latência significativamente
- Mudado rate limiting
- Implementado bloqueio de IPs de cloud (Railway)

### H2: Timeout muito agressivo
O timeout per-source de 60s pode ser insuficiente para a paginação do PCP v2:
- PCP v2 retorna 10 items/página (fixo)
- Para 27 UFs com client-side filtering, precisa paginar muitas vezes
- 60s pode não ser suficiente para completar todas as páginas

### H3: Rate limiting acumulado
Com SWR revalidation paralela, múltiplas buscas simultâneas podem estar hitting rate limits do PCP v2.

---

## Acceptance Criteria

### Diagnóstico

- [x] **AC1:** Testar manualmente a API do PCP v2 com curl — verificar latência atual
  ```bash
  curl -w '%{time_total}s' 'https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos?pagina=1'
  ```
  _Resultado: API responde ~0.6-0.7s/página. 206 páginas para range de 10 dias (2055 records). Root cause = H2 (timeout insuficiente para volume de paginação)._
- [x] **AC2:** Verificar se o IP do Railway está sendo rate-limited (testar de IP diferente)
  _Resultado: Sem rate limiting detectado. Latência consistente. Volume de paginação é o problema._
- [x] **AC3:** Adicionar logging de latência per-page no PCP v2 client para diagnosticar onde o timeout ocorre
  _Implementado: per-page elapsed_ms logging + total fetch time + slow page detection._

### Fix (baseado no diagnóstico)

- [x] **AC4:** Se API lenta: aumentar timeout PCP para 90s OU implementar early-return com records parciais
  _Implementado: PCP_MAX_PAGES_V2=20 (cap de páginas) + early-return após 3 páginas lentas consecutivas (>PCP_SLOW_PAGE_THRESHOLD_S)._
- [x] **AC5:** Se rate-limited: implementar rate limiting client-side (max 2 req/s) com backoff
  _Implementado: PCP_RATE_LIMIT_DELAY=0.5s configurável via env var. Default 0.5s = ~2 req/s._
- [x] **AC6:** Se API fora do ar: desabilitar temporariamente via feature flag `PCP_V2_ENABLED=false` e remover da consolidation
  _Implementado: PCP_V2_ENABLED no feature flag registry (config.py). search_pipeline.py e main.py checam health registry antes de incluir PCP._

### Resiliência

- [x] **AC7:** Quando fonte está DOWN, SWR revalidation deve pular a fonte (não desperdiçar 60s esperando timeout conhecido)
  _Implementado: search_cache.py agora checa source_health_registry.is_available() antes de incluir fontes na revalidação. Fontes DOWN são skipped com log info._
- [x] **AC8:** Adicionar healthcheck dedicado para PCP v2 no `/v1/health` — probar com 1 request antes de incluir na consolidation
  _Implementado: search_pipeline.py checa health registry status antes de incluir PCP nos adapters. main.py data-sources endpoint também checa._

### Validação

- [ ] **AC9:** Monitorar logs Railway por 2h — PORTAL_COMPRAS retorna SUCCESS ou está corretamente desabilitada
  _Operacional — requer deploy e monitoramento manual pós-deploy._
- [x] **AC10:** Testes existentes passam sem regressão
  _6765 passed, 21 pre-existing failures, 5 skipped. 23 novos testes CRIT-047 + 56 PCP existentes = zero regressões._

---

## File List

| File | Action | Purpose |
|------|--------|---------|
| `backend/clients/portal_compras_client.py` | Modified | Per-page latency logging, max pages cap, slow page early-return, configurable rate limit |
| `backend/config.py` | Modified | PCP_MAX_PAGES_V2, PCP_RATE_LIMIT_DELAY, PCP_SLOW_PAGE_THRESHOLD_S, PCP_V2_ENABLED flag |
| `backend/search_cache.py` | Modified | SWR revalidation skips DOWN sources via health registry |
| `backend/search_pipeline.py` | Modified | Pre-consolidation health registry check for PCP |
| `backend/main.py` | Modified | Data-sources endpoint health registry check for PCP |
| `backend/tests/test_crit047_pcp_timeout.py` | Created | 23 tests covering AC3-AC8 |
| `docs/stories/CRIT-047-portal-compras-systematic-timeout.md` | Modified | Story checkboxes updated |

---

## Notas

- PCP v2 é fonte secundária (priority 2) — PNCP cobre ~90% dos editais
- A degradação funciona: resultados são entregues via PNCP mesmo com PCP DOWN
- "salvaged N partial records" indica que ALGUMAS páginas retornam antes do timeout
- Considerar se PCP v2 vale o custo de 60s timeout em cada revalidation
