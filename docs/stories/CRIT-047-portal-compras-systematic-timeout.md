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

- [ ] **AC1:** Testar manualmente a API do PCP v2 com curl — verificar latência atual
  ```bash
  curl -w '%{time_total}s' 'https://compras.api.portaldecompraspublicas.com.br/v2/licitacao/processos?pagina=1'
  ```
- [ ] **AC2:** Verificar se o IP do Railway está sendo rate-limited (testar de IP diferente)
- [ ] **AC3:** Adicionar logging de latência per-page no PCP v2 client para diagnosticar onde o timeout ocorre

### Fix (baseado no diagnóstico)

- [ ] **AC4:** Se API lenta: aumentar timeout PCP para 90s OU implementar early-return com records parciais
- [ ] **AC5:** Se rate-limited: implementar rate limiting client-side (max 2 req/s) com backoff
- [ ] **AC6:** Se API fora do ar: desabilitar temporariamente via feature flag `PCP_V2_ENABLED=false` e remover da consolidation

### Resiliência

- [ ] **AC7:** Quando fonte está DOWN, SWR revalidation deve pular a fonte (não desperdiçar 60s esperando timeout conhecido)
- [ ] **AC8:** Adicionar healthcheck dedicado para PCP v2 no `/v1/health` — probar com 1 request antes de incluir na consolidation

### Validação

- [ ] **AC9:** Monitorar logs Railway por 2h — PORTAL_COMPRAS retorna SUCCESS ou está corretamente desabilitada
- [ ] **AC10:** Testes existentes passam sem regressão

---

## Notas

- PCP v2 é fonte secundária (priority 2) — PNCP cobre ~90% dos editais
- A degradação funciona: resultados são entregues via PNCP mesmo com PCP DOWN
- "salvaged N partial records" indica que ALGUMAS páginas retornam antes do timeout
- Considerar se PCP v2 vale o custo de 60s timeout em cada revalidation
