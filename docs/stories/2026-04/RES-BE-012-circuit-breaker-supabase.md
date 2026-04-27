# RES-BE-012: Circuit Breaker Supabase Client (Open/Half-Open/Closed)

**Priority:** P2
**Effort:** M (3-4 dias)
**Squad:** @dev + @architect
**Status:** Ready
**Epic:** [EPIC-RES-BE-2026-Q2](EPIC-RES-BE-2026-Q2.md)
**Sprint:** Sprint 6 (2026-06-17 → 2026-06-23) — backlog P2
**Dependências bloqueadoras:** [RES-BE-002](RES-BE-002-budget-top5-routes.md), [RES-BE-003](RES-BE-003-negative-cache-failure-paths.md)

---

## Contexto

Após Sprint 1-3, o backend tem 3 camadas de proteção: budget temporal (RES-BE-002), negative cache (RES-BE-003), bulkhead (RES-BE-010). Falta a **4ª camada: circuit breaker no client Supabase global** — corte rápido quando Supabase está degradado.

Cenário: Supabase API retorna 503 sustentado por 30s. Sem breaker:
- Cada request tenta query → timeout 3s → negative cache marca → próximo request 503
- Mas request COM cache miss continua tentando — slow drain
- Pool fica idle (queries timed out) mas timeout custou 3s × N requests

Com breaker em estado **open**:
- 1ª falha incrementa contador
- 5 falhas em 30s → estado vira `open` por 60s
- Durante `open`, **toda** chamada Supabase falha imediatamente sem hit DB (sem 3s timeout)
- Após 60s → `half-open`: 1 request de teste; se sucesso → `closed`; se falha → `open` por 60s mais

Padrão ortogonal a negative cache: negative cache é por-rota+params; breaker é global por-cliente. Um pode evitar saturação local; outro evita "death spiral" do client.

P2 porque RES-BE-002+003+010 já cobrem 80% do risco; breaker é diminishing returns. Sprint 6.

---

## Acceptance Criteria

### AC1: Avaliar `pybreaker` vs custom

- [ ] @architect decide entre:
  - **Opção A:** `pip install pybreaker` (https://pypi.org/project/pybreaker/) — battle-tested, 2.5k stars
  - **Opção B:** Custom `backend/circuit_breaker.py` (~150L) — zero deps, customizado para Supabase
- [ ] Decisão registrada via `decision-recorder.js`:
  ```
  node .aios-core/development/scripts/decision-recorder.js \
    --type architecture \
    --title "Circuit breaker Supabase: pybreaker vs custom" \
    --rationale "..."
  ```
- [ ] Recomendação SM (não bloqueante): custom para visibility/control + integração metrics nativas

### AC2: Implementação core

- [ ] Criar `backend/circuit_breaker.py`:
  ```python
  from enum import Enum
  from time import monotonic
  import asyncio

  class CircuitState(Enum):
      CLOSED = "closed"
      OPEN = "open"
      HALF_OPEN = "half_open"

  class CircuitBreaker:
      def __init__(
          self,
          *,
          name: str,
          failure_threshold: int = 5,
          window_seconds: float = 30,
          cooldown_seconds: float = 60,
      ):
          self.name = name
          self._failure_threshold = failure_threshold
          self._window = window_seconds
          self._cooldown = cooldown_seconds
          self._state = CircuitState.CLOSED
          self._failures: list[float] = []
          self._opened_at: float | None = None
          self._lock = asyncio.Lock()

      async def call(self, coro):
          async with self._lock:
              now = monotonic()
              # Cleanup old failures outside window
              self._failures = [t for t in self._failures if now - t < self._window]
              # State transitions
              if self._state == CircuitState.OPEN:
                  if now - self._opened_at >= self._cooldown:
                      self._state = CircuitState.HALF_OPEN
                  else:
                      _record_state(self.name, self._state)
                      raise CircuitBreakerOpenError(self.name)
              # Allow call (closed or half-open)
          try:
              result = await coro
              async with self._lock:
                  if self._state == CircuitState.HALF_OPEN:
                      self._state = CircuitState.CLOSED
                      self._failures.clear()
                  _record_state(self.name, self._state)
              return result
          except Exception:
              async with self._lock:
                  self._failures.append(monotonic())
                  if len(self._failures) >= self._failure_threshold or self._state == CircuitState.HALF_OPEN:
                      self._state = CircuitState.OPEN
                      self._opened_at = monotonic()
                  _record_state(self.name, self._state)
              raise
  ```
- [ ] `CircuitBreakerOpenError` extends Exception
- [ ] Logger emite warning em transição estado

### AC3: Integração com Supabase client

- [ ] Em `backend/database.py` (ou `supabase_client.py`):
  ```python
  from circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

  _supabase_breaker = CircuitBreaker(
      name="supabase",
      failure_threshold=5,
      window_seconds=30,
      cooldown_seconds=60,
  )

  async def execute_with_breaker(coro):
      try:
          return await _supabase_breaker.call(coro)
      except CircuitBreakerOpenError:
          raise HTTPException(status_code=503, detail="Database temporarily unavailable",
                              headers={"Retry-After": "60"})
  ```
- [ ] **NÃO** wrappear cada `.execute()` automaticamente — opt-in por rota crítica
- [ ] Aplicar em `_run_with_budget` opcionalmente: se `use_breaker=True` flag, chama `execute_with_breaker`

### AC4: Métricas Prometheus

- [ ] Em `backend/metrics.py`:
  ```python
  CIRCUIT_BREAKER_STATE = Gauge(
      "smartlic_circuit_breaker_state",
      "Circuit breaker state: 0=closed, 1=half_open, 2=open",
      ["component"],
  )
  CIRCUIT_BREAKER_TRANSITIONS_TOTAL = Counter(
      "smartlic_circuit_breaker_transitions_total",
      "State transitions of circuit breaker",
      ["component", "from_state", "to_state"],
  )
  CIRCUIT_BREAKER_REJECTED_TOTAL = Counter(
      "smartlic_circuit_breaker_rejected_total",
      "Requests rejected because breaker is open",
      ["component"],
  )
  ```
- [ ] Helper `_record_state(name, state)` atualiza gauge + counter
- [ ] Sentry alerta em transição CLOSED→OPEN (sinal crítico)

### AC5: Feature flag

- [ ] `backend/config.py`:
  ```python
  ENABLE_CIRCUIT_BREAKER: bool = os.getenv("ENABLE_CIRCUIT_BREAKER", "true").lower() == "true"
  CB_FAILURE_THRESHOLD: int = int(os.getenv("CB_FAILURE_THRESHOLD", "5"))
  CB_COOLDOWN_SECONDS: int = int(os.getenv("CB_COOLDOWN_SECONDS", "60"))
  ```
- [ ] Quando flag false, `execute_with_breaker` é no-op (passa direto)

### AC6: Configuração rotas críticas

- [ ] Aplicar `use_breaker=True` em rotas de alto tráfego/baixa tolerância:
  - top-5 RES-BE-002 (mfa, referral, founding, conta, sitemap)
  - top-5 SEO programmatic (cnpj, orgaos, itens, observatorio, fornecedores)
- [ ] Endpoint admin `GET /v1/admin/ops/circuit-breaker/status` retorna estado atual
- [ ] Endpoint admin `POST /v1/admin/ops/circuit-breaker/reset` força reset CLOSED (auth master)

### AC7: Testes

- [ ] **Unit tests:** `backend/tests/test_circuit_breaker.py`
  - Estado CLOSED → 5 falhas em 30s → OPEN
  - Estado OPEN → request rejeitado imediatamente sem chamar coro
  - Estado OPEN → após cooldown → HALF_OPEN
  - HALF_OPEN + sucesso → CLOSED
  - HALF_OPEN + falha → OPEN
  - Failures fora da window não contam
  - Concurrent calls thread-safe (asyncio.Lock)
  - Cobertura ≥85%
- [ ] **Integration tests:** `backend/tests/integration/test_circuit_breaker_supabase.py`
  - Mock Supabase com 5 erros consecutivos → 6º request retorna 503 em <50ms (sem hit DB)
  - Cooldown 60s → 7º request (após sleep) testa half-open
- [ ] **Load test:** Locust simulando Supabase down — confirmar pool não satura, breaker fica open

---

## Scope

**IN:**
- Circuit breaker custom em `backend/circuit_breaker.py`
- Integração com Supabase client
- Métricas Prometheus + Sentry
- Feature flag + tunables via env
- Endpoints admin status + reset
- Testes unit + integration + load
- Aplicar em 10 rotas críticas (mesmas de RES-BE-010)

**OUT:**
- Breaker para outros downstreams (OpenAI, Stripe, Resend) — escopo separado se valor justifica
- Adaptive thresholds (auto-tune) — over-engineering
- Multi-region failover trigger — fora de escopo
- Webhook quando breaker abre (Slack/PagerDuty) — escopo ops

---

## Definition of Done

- [ ] `circuit_breaker.py` implementado, testado, lint clean
- [ ] Integração Supabase via `execute_with_breaker`
- [ ] Métricas Prometheus + Sentry alerting em transição CLOSED→OPEN
- [ ] Feature flag documentada
- [ ] Endpoints admin status + reset funcionais
- [ ] 10 rotas críticas usando breaker
- [ ] Cobertura ≥85%
- [ ] Sem regressão
- [ ] Locust valida proteção sob falha
- [ ] CodeRabbit clean
- [ ] PR review por @architect (Aria) e @qa (Quinn) com verdict PASS
- [ ] Runbook `docs/runbooks/circuit-breaker.md` criado
- [ ] CLAUDE.md atualizado
- [ ] Decision recorded via `decision-recorder.js`

---

## Dev Notes

### Paths absolutos

- `/mnt/d/pncp-poc/backend/circuit_breaker.py` (novo)
- `/mnt/d/pncp-poc/backend/database.py` ou `backend/supabase_client.py` (modificar — wrapper)
- `/mnt/d/pncp-poc/backend/metrics.py` (adicionar 3 métricas)
- `/mnt/d/pncp-poc/backend/config.py` (adicionar flags)
- `/mnt/d/pncp-poc/backend/routes/admin.py` (após RES-BE-008: `routes/admin/ops.py`) — endpoints status/reset
- `/mnt/d/pncp-poc/backend/tests/test_circuit_breaker.py` (novo)
- `/mnt/d/pncp-poc/backend/tests/integration/test_circuit_breaker_supabase.py` (novo)
- `/mnt/d/pncp-poc/backend/load_tests/circuit_breaker_failure.py` (novo)
- `/mnt/d/pncp-poc/docs/runbooks/circuit-breaker.md` (novo)

### Padrão referência

- Hystrix circuit breaker: https://github.com/Netflix/Hystrix/wiki/How-it-Works#circuit-breaker
- Martin Fowler "Circuit Breaker": https://martinfowler.com/bliki/CircuitBreaker.html
- pybreaker repo: https://github.com/danielfm/pybreaker
- Padrão decoder bulkhead RES-BE-010 — reuse pattern de feature flag + counter

### Frameworks de teste

- pytest 8.x + pytest-asyncio
- File location: `backend/tests/test_circuit_breaker.py`, `backend/tests/integration/test_circuit_breaker_supabase.py`
- Marks: `@pytest.mark.timeout(30)` para integration; `@pytest.mark.timeout(10)` para unit
- Fixtures: `freezegun` para fast-forward time em testes de cooldown (`pip install freezegun` se ainda não instalado)
- Locust simulando Supabase 503 sustained

### Convenções

- `asyncio.Lock` para state transitions (thread-safe)
- Type hints obrigatórios; usar `enum.Enum` para CircuitState
- Logger emite warning em CLOSED→OPEN, info em outras transições
- HTTPException 503 com `Retry-After: <cooldown>`

---

## Risk & Rollback

| Trigger | Ação |
|---|---|
| Breaker abre falsamente (5 falhas legítimas mas DB OK) | Investigar via Sentry; ajustar `failure_threshold=10` ou `window_seconds=60` via env |
| Half-open flaky (oscila entre OPEN e CLOSED) | Aumentar cooldown; investigar root cause downstream |
| Endpoint admin reset abusado (oculta problema real) | Auditoria via log; só master pode chamar |
| `asyncio.Lock` causa contention sob alta concorrência | Profile; considerar lock-free com atomic counter (mais complexo) |
| Rotas SEO programmatic ficam 503 quando Supabase blip → Googlebot trust degrada | Aceitar — sinal real; alternativa é wedge total que é pior |

**Rollback completo:** `railway variables --service bidiq-backend --set ENABLE_CIRCUIT_BREAKER=false` em <30s. PR revert se necessário.

---

## Dependencies

**Entrada:**
- [RES-BE-002](RES-BE-002-budget-top5-routes.md) — top-5 com budget
- [RES-BE-003](RES-BE-003-negative-cache-failure-paths.md) — negative cache complementar
- (Soft) [RES-BE-006](RES-BE-006-godmodule-split-metrics.md) — métricas em `metrics/gauges.py`
- (Soft) [RES-BE-008](RES-BE-008-godmodule-split-admin.md) — endpoint admin em `routes/admin/ops.py`

**Saída:** 4ª camada de proteção completa — habilita declarar epic Done.

---

## PO Validation

**Validated by:** @po (Pax)
**Date:** 2026-04-27
**Verdict:** GO
**Score:** 9/10

### 10-Point Checklist

| # | Criterion | ✓/✗ | Notes |
|---|---|---|---|
| 1 | Clear and objective title | ✓ | "Circuit Breaker Supabase Client (Open/Half-Open/Closed)" — pattern + estado nomeados. |
| 2 | Complete description | ✓ | 4ª camada de proteção (após budget+negative cache+bulkhead) com cenário ilustrado. |
| 3 | Testable acceptance criteria | ✓ | 7 ACs incluindo state transitions, concurrent thread-safety, integration mock 5 erros + cooldown. |
| 4 | Well-defined scope | ✓ | IN/OUT explicitos; OUT exclui breaker para outros downstreams (OpenAI, Stripe). |
| 5 | Dependencies mapped | ✓ | Entrada RES-BE-002+003; soft RES-BE-006+008. |
| 6 | Complexity estimate | ✓ | M (3-4 dias) coerente — circuit breaker custom (~150L) + integração + métricas + 10 rotas + tests. |
| 7 | Business value | ✗ | P2 backlog: "diminishing returns após RES-BE-002+003+010 cobrem 80%" — story reconhece isso. Aceitável para Sprint 6, mas valor incremental modesto. |
| 8 | Risks documented | ✓ | 5 riscos incluindo "rotas SEO 503 quando Supabase blip" com decisão explícita ("aceitar — alternativa wedge é pior"). |
| 9 | Criteria of Done | ✓ | 14 itens DoD incluindo decision-recorder.js mandatório e Locust validation. |
| 10 | Alignment with PRD/Epic | ✓ | "4ª camada de proteção completa — habilita declarar epic Done" — saída explícita. |

### Required Fixes

Nenhuma.

### Observations

- AC1 oferece duas opções (pybreaker vs custom) com SM recommendation não-bloqueante para custom — boa prática de @architect autonomy.
- Opt-in via `use_breaker=True` (não wrap automático em todo `.execute()`) — design escolha que reduz blast radius.
- `freezegun` para testes de cooldown sem time.sleep real — boa prática pytest.
- Critério #7 minorado por reconhecimento explícito de diminishing returns (P2 racional), mas story não é gold-plating.

## Change Log

| Data | Versão | Descrição | Autor |
|---|---|---|---|
| 2026-04-27 | 1.0 | Story criada — circuit breaker Supabase global | @sm (River) |
| 2026-04-27 | 1.1 | PO validation: GO (9/10). 4ª camada de proteção, P2 Sprint 6. Status: Draft → Ready. | @po (Pax) |
