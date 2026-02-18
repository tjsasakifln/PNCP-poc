# GTM-RESILIENCE-A01 — Timeout Tenta Cache Antes de 504

**Track:** A — "Nunca Resposta Vazia" (P0)
**Prioridade:** P0 — Bloqueio de percepao de valor
**Sprint:** 1
**Estimativa:** 4-6 horas
**Gaps cobertos:** P-01 (Timeout nao tenta cache), P-02 (Resposta vazia tratada como sucesso)
**Autor:** @pm
**Data:** 2026-02-18

---

## Contexto

A investigacao estrategica (FRENTE 1 — Pipeline de Busca & Resiliencia) identificou dois gaps criticos no fluxo de falha do pipeline:

- **P-01**: Quando `_execute_multi_source()` estoura o `FETCH_TIMEOUT` (360s), o handler de `asyncio.TimeoutError` em `search_pipeline.py:L805-817` levanta imediatamente um `HTTPException(504)` sem consultar nenhum nivel de cache. O usuario ve uma tela de erro puro, mesmo quando existe cache de busca identica com 2 horas de idade.

- **P-02**: Quando todas as fontes falham mas nao ha timeout (ex: PNCP 502 + PCP 503 simultaneos), o pipeline retorna HTTP 200 com `licitacoes: []`. O frontend renderiza "Nenhuma oportunidade encontrada" — indistinguivel de uma busca legitimamente vazia. O usuario nao tem como saber se o resultado e real ou se o sistema falhou silenciosamente.

### Principio violado

> "Em caso de falha parcial ou total das dependencias, o sistema ainda entrega algo util e compreensivel para o usuario?"

Ambos os cenarios violam este principio: o usuario recebe nada (504) ou recebe nada disfarado de sucesso (200 com array vazio).

---

## Problema

1. **Timeout = morte imediata**: O `except asyncio.TimeoutError` em `search_pipeline.py` e o unico handler de erro que NAO tenta cache stale antes de retornar. O handler generico de `Exception` (L818-869) ja implementa fallback para `_supabase_get_cache()`, mas o timeout — que e o cenario MAIS comum de falha em producao — nao.

2. **HTTP 200 + array vazio = mentira semantica**: Quando `ctx.licitacoes_raw = []` e definido apos falha total das fontes (L865, L996), o pipeline continua normalmente e retorna HTTP 200. O frontend nao tem metadata para distinguir "busca executada com sucesso, zero resultados" de "busca falhou, zero dados recuperados".

3. **L3 cache ignorado**: Mesmo nos handlers que tentam cache, apenas Supabase (L1) e consultado. O cache local (L3) — que ja tem `_get_from_local()` implementado em `search_cache.py:L203-212` — nunca e chamado como fallback adicional. (Este gap e tratado em profundidade na story A-03, mas a integracao inicial do fallback cascade pertence a esta story.)

---

## Solucao Proposta

### 1. Timeout → Fallback cascade antes de 504

Refatorar o `except asyncio.TimeoutError` para seguir o mesmo padrao do `except Exception`:
- Tentar `_supabase_get_cache()` (L1)
- Se falhar, tentar `InMemoryCache` (L2)
- Se falhar, tentar `_get_from_local()` (L3) — integracao basica, detalhada em A-03
- Somente se TODOS os niveis falharem, levantar HTTPException 504

Quando cache e servido apos timeout, marcar `ctx.is_partial = True` e `ctx.cached = True` com metadata de freshness.

### 2. Resposta vazia → estado degradado explicito

Quando `ctx.licitacoes_raw` permanece vazio apos falha (nao por filtros, mas por falha de fontes):
- Adicionar campo `response_state` ao `BuscaResponse`: `"live"` | `"cached"` | `"degraded"` | `"empty_failure"`
- Para `empty_failure`: incluir `degradation_guidance` com mensagem orientativa ("Fontes temporariamente indisponiveis. Tente novamente em alguns minutos ou reduza o numero de estados.")
- Frontend usa `response_state` para renderizar UI diferenciada (nao e mais "Nenhuma oportunidade encontrada")

### 3. Semantica HTTP correta

- Cache servido apos timeout: HTTP 200 (dados validos, mesmo que stale)
- Nenhum cache disponivel + timeout: HTTP 504 (mantido, mas com body informativo)
- Fontes falharam + nenhum cache: HTTP 200 com `response_state: "empty_failure"` (nao e erro HTTP, e degradacao)

---

## Acceptance Criteria

### AC1 — Timeout tenta Supabase cache antes de 504
Quando `_execute_multi_source()` estoura `FETCH_TIMEOUT`, o handler de `asyncio.TimeoutError` DEVE chamar `_supabase_get_cache()` com os mesmos parametros da busca corrente antes de levantar HTTPException.

### AC2 — Timeout com cache disponivel retorna HTTP 200
Se o fallback de cache (AC1) encontrar dados, o pipeline DEVE continuar normalmente retornando HTTP 200 com `cached=True`, `cache_status="stale"`, e `is_partial=True`.

### AC3 — Timeout sem cache retorna 504 com body informativo
Se nenhum nivel de cache retornar dados apos timeout, HTTPException 504 DEVE incluir no `detail` uma mensagem orientativa com sugestoes (reduzir UFs, tentar novamente).

### AC4 — BuscaResponse inclui campo `response_state`
O schema `BuscaResponse` DEVE incluir `response_state: Literal["live", "cached", "degraded", "empty_failure"]` com default `"live"`.

### AC5 — Fontes falharam + sem cache → `response_state = "empty_failure"`
Quando `ctx.licitacoes_raw == []` e a causa e falha de fontes (nao filtros), `response_state` DEVE ser `"empty_failure"` e `degradation_guidance` DEVE conter mensagem orientativa em portugues.

### AC6 — Cache servido apos timeout → `response_state = "cached"`
Quando cache stale e servido apos timeout ou falha total, `response_state` DEVE ser `"cached"`.

### AC7 — Frontend distingue `empty_failure` de resultado vazio genuino
O componente `EmptyState` (ou equivalente) DEVE renderizar UI diferente quando `response_state === "empty_failure"`:
- Titulo: "Fontes temporariamente indisponiveis"
- Mensagem: orientacao especifica (nao "Nenhuma oportunidade encontrada")
- Acao: botao "Tentar novamente" com cooldown de 30s

### AC8 — Log estruturado para timeout com fallback
Quando timeout aciona fallback de cache, DEVE logar exatamente 1 entrada JSON com: `event: "timeout_cache_fallback"`, `cache_level` (supabase/memory/local), `cache_age_hours`, `results_count`.

### AC9 — Teste: timeout com cache disponivel
Teste unitario que simula `asyncio.TimeoutError` em `_execute_multi_source()` com mock de `_supabase_get_cache()` retornando dados → pipeline retorna HTTP 200 com `cached=True`.

### AC10 — Teste: timeout sem cache
Teste unitario que simula `asyncio.TimeoutError` com `_supabase_get_cache()` retornando None → pipeline levanta HTTPException 504.

### AC11 — Teste: fontes falharam → `response_state = "empty_failure"`
Teste que simula todas as fontes retornando erro + cache vazio → resposta tem `response_state = "empty_failure"` e `degradation_guidance` nao-vazio.

### AC12 — Teste frontend: renderizacao de `empty_failure`
Teste de componente que verifica que `response_state === "empty_failure"` renderiza "Fontes temporariamente indisponiveis" (nao "Nenhuma oportunidade encontrada").

---

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/search_pipeline.py` | Refatorar `except asyncio.TimeoutError` (L805-817); adicionar cache fallback; set `response_state` |
| `backend/schemas.py` | Adicionar `response_state` e `degradation_guidance` ao `BuscaResponse` |
| `backend/search_cache.py` | Nenhuma mudanca (ja tem `_get_from_local` — integracao completa em A-03) |
| `frontend/app/buscar/components/SearchResults.tsx` | Consumir `response_state`; renderizar UI diferenciada |
| `frontend/app/buscar/components/EmptyState.tsx` | Novo state para `empty_failure` |
| `frontend/types/index.ts` (ou equivalente) | Adicionar `response_state` ao tipo de resposta |
| `backend/tests/test_search_pipeline.py` | AC9, AC10, AC11 |
| `frontend/__tests__/buscar/empty-failure.test.tsx` | AC12 |

---

## Dependencias

| Story | Relacao |
|-------|---------|
| **A-03** (L3 Cache Read) | A-01 prepara o fallback cascade; A-03 completa com L3. A-01 pode ser entregue sem A-03 (usando apenas Supabase). |
| **A-02** (SSE Degraded) | A-01 define `response_state`; A-02 usa esse campo para emitir SSE "degraded". Independentes na implementacao. |
| **A-05** (Indicadores de Cobertura) | A-05 consome `response_state` para decidir visual. Pode ser feita em paralelo. |

---

## Definition of Done

- [ ] Todos os 12 ACs verificados e passing
- [ ] Testes unitarios backend: 4 novos, zero regressoes
- [ ] Testes frontend: 1 novo, zero regressoes
- [ ] TypeScript check (`npx tsc --noEmit`) passing
- [ ] Pipeline de busca executado em producao com 5 UFs — verificar que timeout NAO retorna 504 quando cache existe
- [ ] Log de timeout_cache_fallback visivel no Railway
- [ ] Code review aprovado
- [ ] Commit convencional: `feat(backend+frontend): GTM-RESILIENCE-A01 — timeout cache fallback + empty_failure state`
