# CRIT-056: Cache Poisoning — Salvar Resultados Degradados Contamina Cache

**Prioridade:** HIGH
**Componente:** Backend — search_pipeline.py, pipeline/cache_manager.py, search_cache.py
**Origem:** Incidente 2026-03-05 — Pipeline salva 104 resultados PCP-only no cache (sem PNCP)

## Problema

Quando PNCP esta degraded e so PCP v2 retorna dados, o pipeline salva esses resultados parciais no cache:

```
Cache SAVE L1/supabase: 104 results for hash e0904da5fb9a... (sources: ['PORTAL_COMPRAS'])
```

Esses 104 resultados sao todos do PCP v2 e 95% sao rejeitados pelo filtro de status.
Agora o cache esta "envenenado" — proximas buscas com os mesmos parametros vao servir esses mesmos dados inuteis do cache por 4-24 horas.

Quando o PNCP voltar ao normal, o usuario ainda recebera dados degradados do cache ate o TTL expirar.

## Acceptance Criteria

### AC1: Nao cachear quando fonte primaria falhou
- [ ] Se PNCP (prioridade 1) esta em `sources_degraded` ou `sources_failed`:
  - NAO salvar no cache L1 (InMemory) nem L2 (Supabase)
  - Log: `"Cache SKIP: primary source degraded, not caching partial results"`
- [ ] Se todas as fontes succeeded: salvar normalmente

### AC2: Cache com metadata de qualidade
- [ ] Cada entrada de cache inclui `sources_available` e `quality_score`
- [ ] `quality_score`: 1.0 (todas fontes), 0.5 (sem PNCP), 0.0 (sem fontes)
- [ ] Na leitura, se `quality_score < 0.5` e fonte esta healthy agora → forcar refresh

### AC3: Cache stale preferido sobre cache degradado
- [ ] Se existe cache anterior (pre-degradacao) com quality_score 1.0:
  - Servir o cache antigo (stale) em vez do novo (degradado/parcial)
  - Banner: "Exibindo resultados de Xh atras (dados mais recentes indisponiveis)"
- [ ] Se nao existe cache anterior: servir parcial com banner de degradacao (CRIT-053)

### AC4: Auto-invalidacao quando fonte volta
- [ ] Cron canary detecta PNCP voltou para healthy
- [ ] Marcar entradas de cache com `quality_score < 1.0` como stale (forcar revalidacao)
- [ ] Log: `"PNCP recovered — invalidating {N} degraded cache entries"`

### AC5: Testes
- [ ] Test: PNCP degraded → resultados NAO salvos no cache
- [ ] Test: cache anterior com quality 1.0 preferido sobre novo com quality 0.5
- [ ] Test: PNCP volta healthy → cache degradado invalidado
- [ ] Test: todas fontes ok → cache salvo normalmente

## Arquivos Afetados

- `backend/search_pipeline.py` — condicional de save baseado em source status
- `backend/pipeline/cache_manager.py` — `_write_cache` com quality check
- `backend/search_cache.py` — `save_to_cache` com quality_score, auto-invalidacao
- `backend/cron_jobs.py` — invalidacao quando PNCP volta
