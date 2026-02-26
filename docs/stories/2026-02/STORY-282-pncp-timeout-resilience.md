# STORY-282: PNCP Timeout Resilience — Cache-First + Aggressive Timeout

**Priority:** P0 BLOCKER
**Effort:** 2 days
**Squad:** @dev + @qa
**Fundamentacao:** Logs de producao 2026-02-26 (PNCP 180s timeout, 0 records)

## Problema Observado em Producao

```
PNCP SP modalidade=4: 30s timeout × 3 retries = 90s → primeiro success
PNCP SP modalidade=5: 30s timeout × 2 retries = 60s → success (21 items)
PNCP SP modalidade=6: 30s timeout × 3 retries = 90s → 1463 items (30 pages!)
PNCP SP modalidade=7: timeout total

Consolidation total: 180s → TIMEOUT → 0 records from PNCP
PCP sozinho: 53 records brutos → 0 apos filtro vestuario
Resultado final: 0 oportunidades para o usuario
```

**PNCP modalidade 6 (Pregao) para SP tem 1463 records / 30 pages.** A 3s por pagina = 90s so para paginar. Com retries, impossivel caber no timeout.

## Evidencia: Cache Warming tambem falha

```
[CONSOLIDATION] PNCP: timeout after 60003ms — no records
[CONSOLIDATION] PNCP: timeout after 60000ms — no records
Source 'PNCP' transitioned to DEGRADED status after 3 consecutive failures
revalidation_complete: duration_ms=60007, result=empty, new_results_count=0
```

Cache warming roda 25 combinacoes (5 sectors × 5 UFs) e TODAS falham quando PNCP esta lento. Zero cache populado = zero resultados para usuarios.

## Root Causes (3 camadas)

1. **PNCP read timeout = 30s** muito generoso — multiplica com retries (3) e modalidades (4)
2. **Sem page limit** — modalidade 6/SP tem 30 pages, tenta todas
3. **Cache warming concorre com busca real** — 3 revalidations + 25 warmups competem pelas mesmas conexoes

## Acceptance Criteria

### AC1: Reducao agressiva de timeout PNCP
- [x] `pncp_client.py`: `_CONNECT_TIMEOUT = 10` (era 30) — via `RetryConfig.connect_timeout`
- [x] `pncp_client.py`: `_READ_TIMEOUT = 15` (era 30) — via `RetryConfig.read_timeout`
- [x] Max retries: 1 (era 3) — fail fast, nao adianta retry se API esta lenta
- [x] Configurable via env: `PNCP_CONNECT_TIMEOUT`, `PNCP_READ_TIMEOUT`, `PNCP_MAX_RETRIES`
- [x] AsyncPNCPClient uses split connect/read timeouts in httpx.Timeout

### AC2: Page limit por modalidade
- [x] `pncp_client.py`: `PNCP_MAX_PAGES = 5` (250 items max) — from config.py
- [x] Se total_records > 250, log warning e truncar (nao buscar 30 pages)
- [x] Configurable via env: `PNCP_MAX_PAGES`
- [x] Applied to: `_fetch_single_modality`, `_fetch_modality_with_timeout`, `_fetch_uf_all_pages`, `buscar_todas_ufs_paralelo`, `_fetch_by_uf` (sync)

### AC3: Cache-first para buscas de usuario
- [x] Se cache existe (mesmo stale), retornar IMEDIATAMENTE ao usuario
- [x] Disparar revalidation em background via `trigger_background_revalidation()`
- [x] Frontend: CacheBanner already shows "dados de Xh atras" for stale cache
- [x] `CACHE_FIRST_FRESH_TIMEOUT = 60` configurable via env

### AC4: Priorizar busca real sobre warming
- [x] Se ha busca de usuario em andamento, pausar cache warming — via `ACTIVE_SEARCHES` gauge
- [x] Semaphore: `_warming_wait_for_idle()` in job_queue.py checks gauge before each warming request
- [x] Log: `{"event": "warming_paused", "reason": "active_user_search"}` — already implemented in STAB-007

### AC5: Fallback PCP com filtro UF corrigido
- [x] PCP v2 nao filtra por UF server-side. Client filter corrigido para case-insensitive match.
- [x] Records com UF vazio agora sao SKIPPED quando filtro UF ativo (eram passados silenciosamente)
- [x] Investigacao: 53 records PCP → 0 apos filtro vestuario = esperado (PCP records nao contem keywords vestuario no `resumo`). O problema real era UF vazio passando pelo filtro.

## Files to Modify

| File | Change |
|------|--------|
| `backend/pncp_client.py` | Timeout + page limit |
| `backend/config.py` | PNCP_CONNECT_TIMEOUT, PNCP_READ_TIMEOUT, PNCP_MAX_PAGES |
| `backend/search_cache.py` | Cache-first logic for user searches |
| `backend/cron_jobs.py` | Warming priority/pause logic |
| `backend/portal_compras_client.py` | Investigate UF filter behavior |

## Metricas Esperadas

| Antes | Depois |
|-------|--------|
| PNCP timeout 180s → 0 results | PNCP fail fast 15s → cache served |
| Cache warming: 0/25 populados | Warming com backoff inteligente |
| SP/mod6: 30 pages × 3s = 90s | SP/mod6: 5 pages × 3s = 15s |
| User wait: 185s (timeout) | User wait: <5s (cached) ou <60s (fresh) |
