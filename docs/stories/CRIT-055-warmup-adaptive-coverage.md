# CRIT-055: Warmup Adaptativo Baseado em Buscas Reais

**Prioridade:** HIGH
**Componente:** Backend — cron_jobs.py, search_cache.py
**Origem:** Incidente 2026-03-05 — Warmup cacheia 5 UFs hardcoded, usuario busca 7-27 UFs

## Problema

O warmup startup (`start_warmup_task`) usa setores e UFs hardcoded:
```python
sectors=['software', 'informatica', 'engenharia', 'saude', 'facilities']
ufs=['SP', 'RJ', 'MG', 'BA', 'PR']
```

O usuario buscou com 7 UFs (SP,ES,MG,RJ,PR,RS,SC) e depois 27 UFs. O warmup nao cobriu ES, RS, SC e todas as outras UFs. Cache miss total.

**Nota:** Se CRIT-051 (cache composable por UF) for implementado, este problema se resolve parcialmente — o warmup por UF individual alimentaria buscas multi-UF. Mas o warmup ainda precisa cobrir TODAS as UFs que usuarios realmente buscam.

## Acceptance Criteria

### AC1: Warmup cobre todas as 27 UFs
- [x] `start_warmup_task` itera sobre TODAS as UFs brasileiras (27), nao subset hardcoded
- [x] Batching: grupos de 5 UFs com delay de `WARMUP_BATCH_DELAY_SECONDS` entre grupos
- [x] Total: 5 setores x 27 UFs = 135 combinacoes (com delay ~5min total)

### AC2: Prioridade de UFs baseada em historico
- [x] Query `search_sessions` para UFs mais buscadas nos ultimos 7 dias
- [x] Warm UFs populares primeiro, depois o resto
- [x] Se nao ha historico, usar ordem default: SP, RJ, MG, BA, PR, RS, SC, PE, CE, GO, DF, ...

### AC3: Warmup periodico (nao so startup)
- [x] Cron job a cada 3h re-aquece top 10 combinacoes mais buscadas
- [x] Usa `warmup_top_params()` que ja existe — garantir que funciona com cache composable

### AC4: Warmup nao sobrecarrega PNCP
- [x] Rate limiting: max 2 requests/segundo ao PNCP durante warmup
- [x] Se PNCP cron canary reporta degraded, pausar warmup por 5 minutos
- [x] Total de requests warmup: ~135 * 4 modalidades = ~540 requests (com rate limit ~5min)

### AC5: Observabilidade
- [x] Log summary ao final: `"Warmup complete: 135/135 dispatched, 0 failed, coverage: 27/27 UFs"`
- [x] Metrica: `smartlic_warmup_coverage_ratio` gauge (UFs cacheadas / total UFs)

### AC6: Testes
- [x] Test: warmup itera 27 UFs x 5 setores
- [x] Test: UFs priorizadas por historico
- [x] Test: PNCP degraded → warmup pausa

## Arquivos Afetados

- `backend/cron_jobs.py` — `start_warmup_task()`, nova logica de cobertura
- `backend/config.py` — `WARMUP_ALL_UFS`, `WARMUP_RATE_LIMIT_RPS`
- `backend/search_cache.py` — query de UFs populares
