# CRIT-081: Cache Warmup Periódico Ininterrupto — Dados Sempre Disponíveis

**Status:** Done
**Priority:** P1 — HIGH (resiliência contra indisponibilidade de fontes)
**Epic:** Infraestrutura de Cache
**Agent:** @dev + @architect
**Depends on:** CRIT-080 (deploy funcional)

---

## Contexto

O SmartLic depende de 3 fontes externas (PNCP, PCP, ComprasGov) que podem ficar indisponíveis a qualquer momento. O cache é a única garantia de que o usuário sempre receba resultados.

**Estado atual:**
| Mecanismo | Status | Intervalo | Cobertura |
|-----------|--------|-----------|-----------|
| Startup warmup | ✅ Ativo | 120s após startup | 27 UFs × 5 setores = 135 combos |
| Periodic warmup | ✅ Ativo | 3h | Top 10 params populares (INSUFICIENTE) |
| Cache refresh (SWR) | ❌ DESABILITADO | — | HOT/WARM entries (feature-gated OFF) |

**Problema:** Se as fontes caem por >3h, o cache stale expira (24h TTL) e o sistema não tem NADA para servir. O periodic warmup só reaquece 10 params — insuficiente para cobrir todos os setores/UFs ativos.

**Requisito do usuário:** "Cache deve ser aquecido periodicamente para sempre termos o que servir ao usuário em caso de dificuldade de acessar as fontes."

## Acceptance Criteria

### Habilitar Cache Refresh (SWR Background)

- [x] **AC1**: Ativar `CACHE_REFRESH_ENABLED=true` em `config/features.py` (atualmente `false`)
- [x] **AC2**: Reduzir `CACHE_REFRESH_INTERVAL_HOURS` de 12 para 4 horas
- [x] **AC3**: Aumentar `CACHE_REFRESH_BATCH_SIZE` de 25 para 50 entries por ciclo
- [x] **AC4**: Cache refresh deve priorizar HOT entries primeiro, depois WARM, depois COLD

### Expandir Periodic Warmup

- [x] **AC5**: Aumentar `warmup_top_params(limit=10)` para `limit=30` — cobrir os 30 params mais buscados
- [x] **AC6**: Reduzir `WARMUP_PERIODIC_INTERVAL_HOURS` de 3 para 2 horas
- [x] **AC7**: Warmup periódico deve incluir TODOS os setores ativos (não apenas os 5 hardcoded), lendo de `sectors_data.yaml`

### Garantir Dados Sempre Disponíveis

- [x] **AC8**: Implementar `ensure_minimum_cache_coverage()` que roda a cada 1h:
  - Para cada setor ativo × top 5 UFs populares: verificar se cache tem dados < 12h
  - Se não tem: disparar revalidação imediata
  - Métrica: `smartlic_cache_coverage_deficit` gauge (número de combos sem cache)
- [x] **AC9**: Quando TODAS as fontes estão down (3 circuit breakers OPEN):
  - Servir cache stale mesmo se > 24h TTL (com banner "dados de {timestamp}")
  - Novo flag `SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE=true`
- [x] **AC10**: Expor cobertura do cache em `GET /v1/health/cache`:
  ```json
  {
    "warmup_coverage": { "total_combos": 135, "cached": 98, "stale": 22, "missing": 15 },
    "last_warmup": "2026-03-23T10:00:00Z",
    "next_warmup": "2026-03-23T12:00:00Z"
  }
  ```

### Testes

- [x] **AC11**: Teste `test_cache_refresh_enabled.py` — verifica que stale entries são revalidadas dentro de 4h
- [x] **AC12**: Teste `test_ensure_minimum_coverage.py` — verifica que déficits são detectados e preenchidos
- [x] **AC13**: Teste `test_serve_expired_on_outage.py` — verifica que cache expirado é servido quando todas as fontes estão down

## Configuração Final Esperada

```python
# config/features.py
CACHE_REFRESH_ENABLED = True

# config/pipeline.py
WARMUP_PERIODIC_INTERVAL_HOURS = 2
WARMUP_TOP_PARAMS_LIMIT = 30
CACHE_REFRESH_INTERVAL_HOURS = 4
CACHE_REFRESH_BATCH_SIZE = 50
ENSURE_COVERAGE_INTERVAL_HOURS = 1
SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE = True
```

## Arquitetura de Warming (após implementação)

```
Hora 0   → Startup warmup (135 combos)
Hora 1   → ensure_minimum_coverage (preenche gaps)
Hora 2   → Periodic warmup (top 30 + gaps)
Hora 3   → ensure_minimum_coverage
Hora 4   → Periodic warmup + Cache refresh (50 stale entries)
...ciclo contínuo...
```

## Escopo

**IN:** `backend/cache.py` (lógica de warmup e SWR refresh), `backend/config.py` / `backend/config/features.py` (flags de feature), `backend/cron_jobs.py` (periodic warmup scheduler), `backend/routes/health.py` (endpoint `/health/cache` com cobertura)  
**OUT:** Mudanças nas fontes externas (PNCP, PCP, ComprasGov), alterações no TTL do cache L2 (Supabase), modificações no circuito breaker de fontes individuais

## Complexidade

**M** (2–3 dias) — múltiplos mecanismos de warmup + nova função `ensure_minimum_cache_coverage()` + flag de outage total + 3 testes de integração

## Riscos

- **`ensure_minimum_cache_coverage()` + periodic warmup simultâneos:** Dois mecanismos rodando ao mesmo tempo podem disparar revalidações duplicadas — usar lock ou dedup por chave de cache
- **SERVE_EXPIRED_CACHE_ON_TOTAL_OUTAGE:** Servir dados muito antigos (>24h) pode confundir usuários com oportunidades já encerradas — garantir que o banner de "dados de {timestamp}" seja visualmente proeminente

## Critério de Done

- `GET /health/cache` retorna `warmup_coverage` com `missing` ≤ 10% dos combos ativos
- Periodic warmup cobre top 30 parâmetros (confirmado em logs INFO)
- Com todas as 3 fontes simuladas como down: busca retorna resultados stale com banner de data
- Testes AC11, AC12, AC13 passam sem regressões

## Impacto

- **Sem este fix:** Fontes down = usuários sem resultado algum
- **Com este fix:** Cache sempre tem dados < 12h para servir, mesmo durante outage total
