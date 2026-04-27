# RES-BE-003: Negative Cache Padrão em 41 Failure Paths

**Priority:** P0
**Effort:** L (5-7 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 2 (2026-05-06 → 2026-05-12)
**Dependências bloqueadoras:** [RES-BE-002](RES-BE-002-budget-top5-routes.md) (rotas top-5 já protegidas com budget; agora protegemos failure path delas)

---

## Contexto

Durante o P0 de 2026-04-27 Stage 2, descobriu-se que rotas como `perfil-b2g/[uf]` e `fornecedor profile` não tinham **negative cache**: quando uma query Supabase falhava (timeout ou erro), o próximo request executava a mesma query novamente, **amplificando cascata** sob a wave Googlebot. O hotfix PR #529 cobriu apenas 2 rotas; restam **41 rotas no failure path** sem proteção, segundo auditoria pós-incidente.

Padrão a instituir: decorator `@with_negative_cache(ttl=60)` que, em caso de falha (timeout, exception, status >=500), grava marker no Redis com TTL curto (60s default). Próximas requests com mesma chave de parâmetros retornam imediatamente HTTP 503 com `Retry-After: 60` — **economizando o pool Supabase** e impedindo cascata.

Memory referência: `feedback_build_hammers_backend_cascade` (2026-04-27) — frontend SSG (4146 pages) saturou backend hobby; AbortSignal.timeout no frontend + negative cache no backend são contramedidas complementares.

Esta story é P0 mas tem effort L porque cobre **41 rotas** + introduz infra reutilizável (decorator + Redis key schema + métrica + Grafana panel).

---

## Acceptance Criteria

### AC1: Decorator `@with_negative_cache`

- [ ] Criar `backend/cache/negative_cache.py`:
  ```python
  from functools import wraps
  from typing import Callable, Awaitable
  import hashlib, json, asyncio
  from redis_client import get_redis

  def with_negative_cache(
      *,
      ttl: int = 60,
      key_fn: Callable[..., str] | None = None,
      catch: tuple[type[Exception], ...] = (asyncio.TimeoutError, Exception),
  ):
      def decorator(func: Callable[..., Awaitable]):
          @wraps(func)
          async def wrapper(*args, **kwargs):
              redis = await get_redis()
              cache_key = _build_key(func, args, kwargs, key_fn)
              # Check negative cache marker
              if await redis.get(cache_key):
                  NEGATIVE_CACHE_HIT_TOTAL.labels(route=func.__name__).inc()
                  raise HTTPException(status_code=503, detail="...", headers={"Retry-After": str(ttl)})
              try:
                  return await func(*args, **kwargs)
              except catch as e:
                  await redis.setex(cache_key, ttl, "1")
                  NEGATIVE_CACHE_SET_TOTAL.labels(route=func.__name__, reason=type(e).__name__).inc()
                  raise
          return wrapper
      return decorator
  ```
- [ ] Redis key pattern: `negcache:{route_name}:{params_hash}` onde `params_hash = sha256(json.dumps(canonical_args, sort_keys=True))[:16]`
- [ ] Default `key_fn` extrai args nomeados da função (skipping self/cls/request); custom `key_fn` permite filtrar (e.g. ignorar header User-Agent)
- [ ] Default `catch` inclui `TimeoutError` + `Exception` genérico; rotas podem narrowdown para `(TimeoutError, SupabaseAPIError)` se quiserem só erros downstream

### AC2: Métricas Prometheus + Sentry

- [ ] Em `backend/metrics.py` (ou seu split RES-BE-006), adicionar:
  ```python
  NEGATIVE_CACHE_HIT_TOTAL = Counter(
      "smartlic_negative_cache_hit_total",
      "Negative cache hits (request short-circuited)",
      ["route"],
  )
  NEGATIVE_CACHE_SET_TOTAL = Counter(
      "smartlic_negative_cache_set_total",
      "Negative cache markers set after failure",
      ["route", "reason"],
  )
  ```
- [ ] Sentry breadcrumb em cada hit (não capture; hit é comportamento esperado)
- [ ] Sentry `capture_message(level="warning")` se taxa de set > 50/min para uma única rota — sinal de downstream problem
- [ ] Grafana panel mock em `docs/runbooks/negative-cache.md` (queries PromQL: `rate(smartlic_negative_cache_set_total[5m]) by (route, reason)`)

### AC3: Rollout — wave 1 (rotas top-5 de RES-BE-002)

- [ ] Aplicar `@with_negative_cache(ttl=60)` em endpoints das rotas:
  - `routes/mfa.py` — 5+ endpoints (excluir mutations: enroll, verify — só read)
  - `routes/referral.py` — 4+ endpoints (read-only)
  - `routes/founding.py` — 2+ endpoints
  - `routes/conta.py` — 3+ endpoints (read-only; NÃO aplicar em update/delete)
  - `routes/sitemap_*.py` — TODOS endpoints (sitemap sempre read)
- [ ] **NUNCA** aplicar em mutations (POST/PUT/PATCH/DELETE) — risco de bloquear retry legítimo após erro transitório
- [ ] Cada endpoint declara `ttl` explícito (60s default; sitemap usa 300s = 5min)
- [ ] Lint clean, testes passing

### AC4: Rollout — wave 2 (outras 30+ rotas read-only)

- [ ] Aplicar decorator em (lista preliminar; ajustar conforme audit):
  - `routes/features.py` (3 endpoints)
  - `routes/user.py` (2 endpoints read)
  - `routes/perfil_b2g.py` (alvo do P0 Stage 2)
  - `routes/fornecedor_profile.py` (alvo do P0 Stage 2)
  - `routes/cnpj.py`, `routes/orgaos.py`, `routes/itens.py`, `routes/observatorio.py`, `routes/fornecedores.py` (rotas SEO programáticas)
  - Outras rotas read-only identificadas via grep `@router.get`
- [ ] Total: 41 rotas (alinhado com audit pós-P0)
- [ ] Cada rota recebe linha "Negative cache: TTL=60s" no docstring

### AC5: Configuração & feature flag

- [ ] `backend/config.py`:
  ```python
  ENABLE_NEGATIVE_CACHE: bool = os.getenv("ENABLE_NEGATIVE_CACHE", "true").lower() == "true"
  NEGATIVE_CACHE_DEFAULT_TTL: int = int(os.getenv("NEGATIVE_CACHE_DEFAULT_TTL", "60"))
  ```
- [ ] Decorator respeita flag — quando `false`, decorator é no-op (passa request direto)
- [ ] Toggle `ENABLE_NEGATIVE_CACHE=false` permite rollback em <30s

### AC6: Edge cases & invalidação

- [ ] Negative cache **NÃO** captura HTTP 4xx (não é falha de servidor — é input ruim)
- [ ] Negative cache **NÃO** captura `HTTPException(status_code<500)` levantadas explicitamente pelo handler
- [ ] Endpoint admin `POST /v1/admin/negative-cache/clear` (auth `is_admin`) limpa todos markers (`SCAN negcache:*` + `DEL`); útil para rollback manual após resolver downstream issue
- [ ] Documentar TTL adequado por categoria:
  - Sitemap: 300s (5min) — Googlebot tolera Retry-After grande
  - User-facing dashboard: 30s (rápida recuperação)
  - SEO programmatic: 60s (default)

### AC7: Testes

- [ ] **Unit tests:** `backend/tests/cache/test_negative_cache.py`
  - Decorator no-op quando flag false
  - Cache hit retorna 503 com Retry-After
  - Cache miss + sucesso → não seta marker
  - Cache miss + falha → seta marker
  - Cache miss + HTTPException(400) → NÃO seta marker
  - Custom `key_fn` é respeitado
  - TTL respeita custom value
  - Cobertura ≥85%
- [ ] **Integration tests:** `backend/tests/integration/test_negative_cache_routes.py`
  - Rota com decorator: simular 1ª chamada com Supabase mock raising → 2ª chamada retorna 503 sem hit Supabase
  - Mock counter assertions
  - 5 rotas amostradas (1 de cada wave)
- [ ] **Load test (informal):** Locust script `backend/load_tests/negative_cache_burst.py` — 100 req/s em rota com Supabase forçado a falhar → confirmar pool Supabase calls cap em 1 (resto serve do negative cache)

---

## Scope

**IN:**
- Decorator `with_negative_cache` em `backend/cache/negative_cache.py`
- Aplicação em 41 rotas read-only
- Métricas Prometheus + Sentry warning
- Endpoint admin clear cache
- Feature flag `ENABLE_NEGATIVE_CACHE`
- Testes unit + integration + load
- Runbook + Grafana panel

**OUT:**
- Negative cache em mutations (escopo separado, requer pattern diferente — DEFER)
- Cache positivo (já existe via `cache/manager.py` — não conflitar)
- Multi-tier negative cache (L1 in-memory + L2 Redis) — over-engineering MVP
- Rate limiting baseado em negative cache hits — escopo RES-BE-010 (bulkheads)

---

## Definition of Done

- [ ] Decorator implementado, testado, lint clean
- [ ] 41 rotas aplicando `@with_negative_cache`
- [ ] Counters Prometheus visíveis em `/metrics`
- [ ] Endpoint admin `/v1/admin/negative-cache/clear` funcional
- [ ] Feature flag `ENABLE_NEGATIVE_CACHE` documentada em CLAUDE.md
- [ ] Cobertura testes ≥85% nas linhas tocadas
- [ ] Sem regressão em testes existentes (5131+ passing, 0 failures)
- [ ] Locust load test confirma proteção sob 100 req/s em rota Supabase-down
- [ ] CodeRabbit review clean (CRITICAL=0, HIGH=0)
- [ ] PR review por @architect (Aria) + @qa (Quinn) com verdict PASS
- [ ] Deploy staging com flag ativa por 24h sem regressão métrica
- [ ] Runbook `docs/runbooks/negative-cache.md` criado e revisado
- [ ] Grafana panel publicado (ou mock documentado se Grafana não está em prod ainda)

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/cache/negative_cache.py` (novo)
- `/mnt/d/pncp-poc/backend/redis_client.py` (existente — usar `get_redis()`)
- `/mnt/d/pncp-poc/backend/metrics.py` (adicionar 2 counters; coordenar com RES-BE-006)
- `/mnt/d/pncp-poc/backend/config.py` (adicionar flag)
- `/mnt/d/pncp-poc/backend/routes/admin.py` (adicionar endpoint clear)
- `/mnt/d/pncp-poc/backend/tests/cache/test_negative_cache.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/integration/test_negative_cache_routes.py` (novo)
- `/mnt/d/pncp-poc/backend/load_tests/negative_cache_burst.py` (novo)
- `/mnt/d/pncp-poc/docs/runbooks/negative-cache.md` (novo)

Lista de rotas alvo (TODO @architect: validar lista exata pre-implementation):
- `/mnt/d/pncp-poc/backend/routes/mfa.py`
- `/mnt/d/pncp-poc/backend/routes/referral.py`
- `/mnt/d/pncp-poc/backend/routes/founding.py`
- `/mnt/d/pncp-poc/backend/routes/conta.py`
- `/mnt/d/pncp-poc/backend/routes/sitemap_*.py` (5+ arquivos)
- `/mnt/d/pncp-poc/backend/routes/features.py`
- `/mnt/d/pncp-poc/backend/routes/user.py`
- `/mnt/d/pncp-poc/backend/routes/perfil_b2g.py`
- `/mnt/d/pncp-poc/backend/routes/fornecedor_profile.py`
- `/mnt/d/pncp-poc/backend/routes/cnpj.py`, `orgaos.py`, `itens.py`, `observatorio.py`, `fornecedores.py`

### Padrão de uso

```python
from cache.negative_cache import with_negative_cache

@router.get("/perfil-b2g/{uf}")
@with_negative_cache(ttl=60)
async def get_perfil(uf: str):
    return await _maybe_wrap(
        asyncio.to_thread(lambda: supabase.from_("...").execute()),
        budget=3.0, phase="route", source="perfil_b2g.get",
    )
```

**Ordem dos decorators é crítica:** `@router.get` deve estar acima de `@with_negative_cache` (FastAPI ordena de fora para dentro; cache executa antes do handler).

### Frameworks de teste

- pytest 8.x + pytest-asyncio + fakeredis (`pip install fakeredis`)
- File location: `backend/tests/cache/test_negative_cache.py`
- Marks: `@pytest.mark.timeout(10)`
- Fixtures: `fake_redis` autouse para isolar testes (não usar Redis real)
- Locust: `from locust import HttpUser, task, between`

### Convenções

- Decorator preserva `__name__`, `__doc__` (via `functools.wraps`)
- Type hints obrigatórios; usar `ParamSpec` se possível para type-safety do decorator
- Cache key NUNCA inclui PII (e.g. email, CPF) — usar hash dos params
- Logger: `logger.info` em hit (visualização de proteção); `logger.warning` em set (sinal de falha downstream)

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| Negative cache hit rate >20% sustained em rota crítica | Investigar downstream (Supabase saúde); `POST /v1/admin/negative-cache/clear` para reset; checar `smartlic_negative_cache_set_total{reason}` para causa |
| User reporta "está sempre dando 503" em rota | Verificar TTL — talvez muito longo; reduzir; ou clear cache via admin endpoint |
| Cascata em rota com mutations (regressão) | Confirmar decorator NÃO está em POST/PUT/DELETE; revert PR específico se sim |
| Prometheus counter não incrementa | Verificar import circular metrics.py ↔ negative_cache.py; usar lazy import dentro do decorator |
| `ENABLE_NEGATIVE_CACHE=false` deixa rotas sem proteção em incidente | Acionar bulkhead (RES-BE-010) como fallback; flag deve ser exceção, não regra |

**Rollback completo:** revert PR. Feature flag `ENABLE_NEGATIVE_CACHE=false` permite rollback em <30s sem revert.

---

## Dependencies

**Entrada:**
- [RES-BE-001](RES-BE-001-audit-execute-without-budget.md) — gate CI ativo
- [RES-BE-002](RES-BE-002-budget-top5-routes.md) — top-5 rotas com budget (negative cache complementa)
- `backend/redis_client.py::get_redis` (existente)

**Saída (esta story bloqueia):**
- [RES-BE-010](RES-BE-010-bulkheads-critical-routes.md) — bulkheads compõem com negative cache
- [RES-BE-012](RES-BE-012-circuit-breaker-supabase.md) — breaker é a camada acima (rede), negative cache é por-rota

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | "Negative Cache Padrão em 41 Failure Paths" — escopo numericamente claro. |
| 2 | Complete description | ✓ | Liga Stage 2 P0 → cascade amplification → padrão decorator + Redis + Retry-After. |
| 3 | Testable acceptance criteria | ✓ | 7 ACs com pseudocódigo do decorator (AC1) + 8 testes unit (AC7) + integration + load. |
| 4 | Well-defined scope | ✓ | IN/OUT detalhados; OUT exclui mutations explicitamente (regra correta de design). |
| 5 | Dependencies mapped | ✓ | Entrada RES-BE-001+002; saída RES-BE-010, 012. |
| 6 | Complexity estimate | ✓ | L (5-7 dias) coerente: decorator + 41 rotas + métricas + admin endpoint + load test. |
| 7 | Business value | ✓ | "Economiza pool Supabase, impede cascata downstream" — valor técnico→operacional explícito. |
| 8 | Risks documented | ✓ | 5 riscos incluindo cascade em mutations (regression watch); rollback via feature flag <30s. |
| 9 | Criteria of Done | ✓ | 12 itens DoD incluindo Locust load 100 req/s validado e Grafana panel documentado. |
| 10 | Alignment with PRD/Epic | ✓ | Métrica #5 EPIC (Sentry events <5/min) e invariant `negative_cache_hit/error >= 0.5` (Validation Framework). |

### Required Fixes

Nenhuma — story pronta para implementação.

### Observations

- AC4 lista preliminar de 41 rotas com nota "TODO @architect: validar lista exata pre-implementation" — aceito; auditoria viva.
- Decoração antes de `@router.get` está correta nos exemplos (FastAPI ordena outside-in, mas Python aplica bottom-up no decorator stack — exemplo correto coloca `@with_negative_cache` ABAIXO de `@router.get`).
- TTL diferenciado por categoria (sitemap 300s vs dashboard 30s vs default 60s) é boa prática — evita cache bloat.
- Memória `feedback_build_hammers_backend_cascade` referenciada — alinhamento com aprendizados pós-incidente.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — proteger 41 failure paths | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). Decorator + 41 rotas + load test; rollback feature-flag <30s. Status: Draft → Ready. | @po (Pax) |
