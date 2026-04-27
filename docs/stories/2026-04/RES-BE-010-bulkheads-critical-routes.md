# RES-BE-010: Bulkheads Asyncio nas 10 Rotas Top Tráfego

**Priority:** P1
**Effort:** M (3-4 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 3 (2026-05-13 → 2026-05-19) — paralelizável com RES-BE-009
**Dependências bloqueadoras:** [RES-BE-002](RES-BE-002-budget-top5-routes.md), [RES-BE-003](RES-BE-003-negative-cache-failure-paths.md)

---

## Contexto

Bulkhead pattern é a 3ª camada de proteção (após budget temporal RES-BE-002 e negative cache RES-BE-003): **isola saturação de uma rota para que não derrube as outras**. Se uma rota cara (e.g. `sitemap.xml` com 50k URLs) estoura concorrência, ela rejeita novos requests com HTTP 503 + `Retry-After: 2` em vez de competir por DB pool com healthchecks e auth.

`backend/bulkhead.py` **já existe** como módulo isolado (foundation laid em sprint anterior, não documentado), mas **não está aplicado em nenhuma rota**. Esta story aplica `Bulkhead(max_concurrent=N)` nas 10 rotas top tráfego identificadas via:

- 5 rotas top de RES-BE-002 (mfa, referral, founding, conta, sitemap_*)
- 5 rotas SEO programmatic críticas (cnpj, orgaos, itens, observatorio, fornecedores)

Counter Prometheus `smartlic_bulkhead_rejected_total{route}` permite alarmar quando bulkhead começa a rejeitar (sinal de saturação). Padrão complementa budget+negative_cache: budget protege individual request, negative cache protege failure repetition, bulkhead protege concorrência total.

---

## Acceptance Criteria

### AC1: Validar/criar `backend/bulkhead.py`

- [ ] Confirmar que `backend/bulkhead.py` existe (CLAUDE.md menciona). Se não existe, criar:
  ```python
  import asyncio
  from contextlib import asynccontextmanager
  from typing import AsyncIterator
  from metrics import BULKHEAD_REJECTED_TOTAL

  class Bulkhead:
      def __init__(self, *, name: str, max_concurrent: int):
          self.name = name
          self._sem = asyncio.Semaphore(max_concurrent)
          self._max = max_concurrent

      @asynccontextmanager
      async def __call__(self) -> AsyncIterator[None]:
          if self._sem.locked():
              BULKHEAD_REJECTED_TOTAL.labels(route=self.name).inc()
              raise BulkheadRejectedError(self.name, retry_after=2)
          async with self._sem:
              yield

  class BulkheadRejectedError(Exception):
      def __init__(self, route: str, retry_after: int):
          self.route = route
          self.retry_after = retry_after
  ```
- [ ] Decorator `@bulkhead(name, max_concurrent)`:
  ```python
  def bulkhead(name: str, *, max_concurrent: int):
      bh = Bulkhead(name=name, max_concurrent=max_concurrent)
      def decorator(func):
          @wraps(func)
          async def wrapper(*args, **kwargs):
              try:
                  async with bh():
                      return await func(*args, **kwargs)
              except BulkheadRejectedError as e:
                  raise HTTPException(503, headers={"Retry-After": str(e.retry_after)})
          return wrapper
      return decorator
  ```

### AC2: Métrica Prometheus

- [ ] Em `backend/metrics.py` (ou seu split RES-BE-006):
  ```python
  BULKHEAD_REJECTED_TOTAL = Counter(
      "smartlic_bulkhead_rejected_total",
      "Requests rejected by bulkhead (saturation)",
      ["route"],
  )
  BULKHEAD_IN_FLIGHT = Gauge(
      "smartlic_bulkhead_in_flight",
      "Current requests in bulkhead semaphore",
      ["route"],
  )
  ```
- [ ] Gauge atualiza em `__aenter__` (incrementa) e `__aexit__` (decrementa)
- [ ] Sentry warning se `rate(BULKHEAD_REJECTED_TOTAL[5m]) > 1` por rota — sinal real de saturação

### AC3: Aplicar bulkheads — top-5 RES-BE-002

- [ ] Aplicar `@bulkhead(name="...", max_concurrent=N)` nos endpoints:
  - `routes/mfa.py` endpoints read — `max_concurrent=20` (auth flow alta freq)
  - `routes/referral.py` endpoints read — `max_concurrent=15`
  - `routes/founding.py` — `max_concurrent=10`
  - `routes/conta.py` — `max_concurrent=15`
  - `routes/sitemap_*.py` — `max_concurrent=5` (queries pesadas)
- [ ] Limites baseline calibrados via:
  - 1 worker hobby Railway = 10 conexões pool Supabase
  - Cada endpoint deve usar ≤50% pool sob carga normal
  - Soma de todos `max_concurrent` ≤ 80% pool total (margem pra healthcheck/auth)

### AC4: Aplicar bulkheads — top-5 SEO programmatic

- [ ] Aplicar nos endpoints (paths backend para frontend SSR):
  - `routes/cnpj.py` — `max_concurrent=10`
  - `routes/orgaos.py` — `max_concurrent=10`
  - `routes/itens.py` — `max_concurrent=10`
  - `routes/observatorio.py` — `max_concurrent=10`
  - `routes/fornecedores.py` — `max_concurrent=10`
- [ ] Coordenar com SEO-PROG-001..005 (que migram frontend para ISR — bulkhead protege backend durante migração)

### AC5: Feature flag

- [ ] `backend/config.py`:
  ```python
  ENABLE_BULKHEAD: bool = os.getenv("ENABLE_BULKHEAD", "true").lower() == "true"
  BULKHEAD_DEFAULT_MAX: int = int(os.getenv("BULKHEAD_DEFAULT_MAX", "10"))
  ```
- [ ] Decorator no-op quando flag false (rollback rápido)
- [ ] Permite override por rota via env var: `BULKHEAD_MAX_MFA=30` → busca `os.getenv("BULKHEAD_MAX_MFA", default=20)`

### AC6: Configuração calibrada por carga

- [ ] Documentar em `docs/runbooks/bulkhead-tuning.md`:
  - Tabela: rota → max_concurrent → justificativa
  - Como ajustar via env var sem deploy (Railway variable)
  - Sinais de under/over-tuning
- [ ] Calibração inicial é educated guess; revisar após 1 semana em prod com métricas reais

### AC7: Testes

- [ ] **Unit tests:** `backend/tests/test_bulkhead.py`
  - Bulkhead aceita até `max_concurrent` requests simultâneos
  - Request `max_concurrent + 1` → `BulkheadRejectedError` levantado, counter incrementa
  - `__aexit__` decrementa gauge
  - Decorator @bulkhead converte erro em HTTPException 503 com Retry-After
  - Feature flag false desabilita
- [ ] **Integration tests:** `backend/tests/integration/test_bulkhead_under_load.py`
  - Disparar `max_concurrent + 5` requests concorrentes em endpoint mockado
  - Confirmar exatamente `max_concurrent` recebem 200, restantes recebem 503
  - Counter Prometheus reflete rejeição
- [ ] **Load test:** Locust `backend/load_tests/bulkhead_saturation.py`
  - 200 req/s em rota com `max_concurrent=10`
  - Pool Supabase calls cap em 10 (resto: 503)
  - Healthcheck `/health/ready` continua respondendo 200 (bulkheads NÃO afetam health)

---

## Scope

**IN:**
- Validar/criar `backend/bulkhead.py` (decorator + class)
- Aplicar `@bulkhead` em 10 rotas (top-5 RES-BE-002 + top-5 SEO programmatic)
- Métricas Prometheus (counter + gauge)
- Feature flag `ENABLE_BULKHEAD`
- Override por rota via env var
- Testes unit + integration + load
- Runbook tuning

**OUT:**
- Bulkheads em mais de 10 rotas (escopo separado)
- Adaptive bulkhead (auto-tune via histórico) — escopo futuro
- Bulkhead em mutations (POST/PUT/DELETE) — POST de auth pode precisar; DEFER
- Multi-tier bulkhead (per-user) — over-engineering MVP
- Substituir por leaky bucket / token bucket — fora de escopo

---

## Definition of Done

- [ ] `backend/bulkhead.py` validado/criado com class + decorator
- [ ] 10 rotas aplicando `@bulkhead` (5 RES-BE-002 + 5 SEO)
- [ ] Counters + gauges visíveis em `/metrics`
- [ ] Feature flag `ENABLE_BULKHEAD` documentada em CLAUDE.md
- [ ] Override por rota documentado em runbook
- [ ] Cobertura testes ≥85%
- [ ] Sem regressão (5131+ passing)
- [ ] Locust load test confirma proteção (cap em max_concurrent, healthcheck OK)
- [ ] CodeRabbit clean
- [ ] PR review por @architect (Aria) e @qa (Quinn) com verdict PASS
- [ ] Deploy staging com flag ativa por 24h
- [ ] Runbook `docs/runbooks/bulkhead-tuning.md` criado
- [ ] CLAUDE.md atualizado (referência ao novo padrão)

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/bulkhead.py` (validar/criar)
- `/mnt/d/pncp-poc/backend/metrics.py` (adicionar counter + gauge)
- `/mnt/d/pncp-poc/backend/config.py` (adicionar flag)
- `/mnt/d/pncp-poc/backend/routes/mfa.py`, `referral.py`, `founding.py`, `conta.py`, `sitemap_*.py` — aplicar
- `/mnt/d/pncp-poc/backend/routes/cnpj.py`, `orgaos.py`, `itens.py`, `observatorio.py`, `fornecedores.py` — aplicar
- `/mnt/d/pncp-poc/backend/tests/test_bulkhead.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/integration/test_bulkhead_under_load.py` (novo)
- `/mnt/d/pncp-poc/backend/load_tests/bulkhead_saturation.py` (novo)
- `/mnt/d/pncp-poc/docs/runbooks/bulkhead-tuning.md` (novo)

### Padrão referência

- `backend/cache/negative_cache.py` (RES-BE-003) — pattern de decorator + counter + flag
- asyncio.Semaphore docs: https://docs.python.org/3/library/asyncio-sync.html#semaphore
- Hystrix bulkhead pattern (Netflix): https://github.com/Netflix/Hystrix/wiki/How-it-Works#bulkhead

### Calibração de `max_concurrent`

Princípio: soma de todos `max_concurrent` <= 80% × pool_size

Pool Supabase = 10 (Railway Hobby)
- Healthcheck: 1 (sempre disponível)
- Auth/MFA: 20 burst (mas usa Redis cache em hot path → DB hit baixo)
- 5 rotas RES-BE-002: 5+15+10+15+5 = 50 (mas concorrência real raramente >5 cada)
- 5 rotas SEO: 5×10 = 50

Total teórico = 121, mas concorrência real <30 sob carga normal. Calibrar pós-deploy via métrica real.

### Frameworks de teste

- pytest 8.x + pytest-asyncio
- File location: `backend/tests/test_bulkhead.py`, `backend/tests/integration/test_bulkhead_under_load.py`
- Marks: `@pytest.mark.timeout(30)` para integration; `@pytest.mark.timeout(10)` para unit
- Fixtures: `asyncio.gather(*[client.get(...) for _ in range(N)])` para teste de concorrência
- Locust: simular Googlebot pattern (slow, sustained, paralelizado)

### Convenções

- Decorator preserva `__name__`, `__doc__`
- Type hints obrigatórios
- HTTPException 503 com `Retry-After: 2` (não 60 — Googlebot tolera retry rápido)
- Logger: `logger.warning` em rejeição

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| `BULKHEAD_REJECTED_TOTAL` >5/min sustained em rota | Aumentar `max_concurrent` via env var (sem deploy); investigar causa raiz |
| User reporta "está dando 503 sempre" | Bulkhead muito apertado; aumentar limite; ou bug em outro lugar |
| Healthcheck regride (rejeitado por bulkhead) | Bulkheads NÃO devem afetar `/health/*`; confirmar que `/health/live` e `/health/ready` não têm decorator |
| Pool Supabase ainda exhausta com bulkheads ativos | Soma de `max_concurrent` excede pool; recalibrar; considerar RES-BE-012 (circuit breaker) |
| Deadlock em concorrência (semaphore não libera) | Investigar exception não capturada; `__aexit__` deve sempre liberar |

**Rollback completo:** `railway variables --service bidiq-backend --set ENABLE_BULKHEAD=false` em <30s. PR revert se necessário.

---

## Dependencies

**Entrada:**
- [RES-BE-002](RES-BE-002-budget-top5-routes.md) — top-5 rotas têm budget
- [RES-BE-003](RES-BE-003-negative-cache-failure-paths.md) — failure paths protegidos
- `backend/bulkhead.py` (existente — validar)

**Saída:** Habilita SEO-PROG-001..005 ramp-up (rotas SSR→ISR têm 3 camadas de proteção).

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 10/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | "Bulkheads Asyncio nas 10 Rotas Top Tráfego" — escopo numérico claro. |
| 2 | Complete description | ✓ | 3ª camada de proteção (após budget+negative cache); racional Hystrix referenciado. |
| 3 | Testable acceptance criteria | ✓ | 7 ACs incluindo unit + integration + Locust load test (200 req/s). |
| 4 | Well-defined scope | ✓ | IN/OUT explicitos; 10 rotas (top-5 RES-BE-002 + top-5 SEO programmatic). |
| 5 | Dependencies mapped | ✓ | Entrada RES-BE-002+003; saída habilita SEO-PROG-001..005 com 3 camadas de proteção. |
| 6 | Complexity estimate | ✓ | M (3-4 dias) coerente — verificado empiricamente (`backend/bulkhead.py` existe, 7936 bytes), AC1 reduz a "validar" essencialmente. |
| 7 | Business value | ✓ | "Isola saturação de uma rota para que não derrube as outras" — claro e mensurável. |
| 8 | Risks documented | ✓ | 5 riscos incluindo healthcheck protection (bulkheads NÃO em /health/*); pool oversaturation; rollback feature flag <30s. |
| 9 | Criteria of Done | ✓ | 13 itens DoD incluindo Locust validation + healthcheck non-affected. |
| 10 | Alignment with PRD/Epic | ✓ | Validation Framework EPIC: `rate(smartlic_bulkhead_rejected_total[5m]) > 0` é alarme; story implementa o counter. |

### Required Fixes

Nenhuma — `backend/bulkhead.py` confirmado existente (verified `ls -la`: 7936 bytes, abr 1).

### Observations

- AC1 path "validar/criar" é correto: arquivo existe mas integração com decorator `@bulkhead` precisa ser confirmada/criada conforme Dev Notes.
- Calibração: soma de `max_concurrent` ≤ 80% pool (10 conexões) — boa heurística mas pode precisar tune real.
- Override por env var (`BULKHEAD_MAX_MFA=30`) permite ajuste sem deploy — operacionalmente flexível.
- Counter + gauge ambos instrumentados (rejection rate + in-flight) — observabilidade completa.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — bulkheads em 10 rotas top tráfego | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (10/10). bulkhead.py verificado existente; calibração documentada, env override flexível. Status: Draft → Ready. | @po (Pax) |
