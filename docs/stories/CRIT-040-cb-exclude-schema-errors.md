# CRIT-040: Circuit Breaker Deve Ignorar Erros de Schema (PGRST205)

**Epic:** Production Stability
**Sprint:** Hotfix
**Priority:** P0 — CRITICAL
**Story Points:** 5 SP
**Estimate:** 3-4 horas
**Owner:** @dev

---

## Problem

O `SupabaseCircuitBreaker` (supabase_client.py) conta erros PGRST205 ("Could not find the table in the schema cache") como falhas reais. PGRST205 indica tabela/coluna ausente no cache do PostgREST — NÃO indica que o Supabase está down.

**Cadeia de falha observada em produção (28/02/2026):**

1. Health canary tenta escrever em `health_checks` → PGRST205 (tabela ausente)
2. CB registra falha → após 5 erros (10 window × 50% threshold), CB abre
3. CB OPEN → `cache_refresh`, `trial_reminders`, `trial_email_sequence` TODOS falham com `CircuitBreakerOpenError`
4. Sentry recebe 86 eventos de erro em 24h — todos falsos positivos

**Mesmo após aplicar CRIT-039**, este padrão pode se repetir se qualquer migração futura não for aplicada a tempo.

---

## Solution

Implementar **error discrimination** no `SupabaseCircuitBreaker`:
- Erros de schema (PGRST204, PGRST205) = **excluídos** do CB (não contam como falha)
- Erros de conexão, timeout, 5xx = **contados** como falha (comportamento atual)

Padrão baseado em: [Microsoft Azure Circuit Breaker Pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) — "distinguish between transient failures and determinate failures."

---

## Acceptance Criteria

### Backend — CB Error Exclusion

- [x] **AC1:** Adicionar parâmetro `exclude_predicates: list[Callable[[Exception], bool]]` ao `SupabaseCircuitBreaker.__init__()` (supabase_client.py)
- [x] **AC2:** No método `_record_failure()`, iterar `exclude_predicates` antes de registrar a falha:
  ```python
  def _record_failure(self, exc: Exception) -> None:
      for pred in self.exclude_predicates:
          if pred(exc):
              logger.debug(f"CB: excluded error from failure count: {exc}")
              return  # don't count
      # ... existing failure logic
  ```
- [x] **AC3:** Configurar o singleton `supabase_cb` com predicados padrão:
  - Excluir erros contendo `PGRST205` (schema cache miss — tabela ausente)
  - Excluir erros contendo `PGRST204` (schema cache miss — coluna ausente)
  - Excluir erros contendo código `42703` (PostgreSQL: undefined column)
  - Excluir erros contendo código `42P01` (PostgreSQL: undefined table)
- [x] **AC4:** Log em nível WARNING quando um erro é excluído do CB (para visibilidade sem poluir ERROR)

### Backend — Sentry Noise Reduction

- [x] **AC5:** No `sentry_sdk.init()` (main.py), adicionar `before_send` filter:
  - Dropar eventos com `CircuitBreakerOpenError` (já rastreado via Prometheus `smartlic_supabase_cb_state`)
  - Dropar eventos com `PGRST205` no message (schema cache, não runtime error)
  - Manter TODOS os outros erros intactos
- [x] **AC6:** Adicionar `CircuitBreakerOpenError` ao `ignore_errors` do Sentry SDK como fallback

### Health Canary — Graceful Handling

- [x] **AC7:** Em `health.py:save_health_check()` (line ~646): capturar PGRST205 separadamente e logar como WARNING, não ERROR
- [x] **AC8:** Em `health.py:detect_incident()` (line ~757): capturar PGRST205 e logar como WARNING, não ERROR
- [x] **AC9:** Em `health.py:cleanup_old_health_checks()` (line ~777): capturar PGRST205 e logar como WARNING, não ERROR

### Testes

- [x] **AC10:** Testes unitários para `SupabaseCircuitBreaker` com `exclude_predicates`:
  - Erro PGRST205 NÃO incrementa failure count
  - Erro de conexão SIM incrementa failure count
  - CB NÃO abre após 10 erros PGRST205 consecutivos
  - CB SIM abre após 5 erros de conexão em window de 10
- [x] **AC11:** Teste de integração: health canary com tabela ausente → CB permanece CLOSED

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/supabase_client.py` | `exclude_predicates` no CB + configuração do singleton |
| `backend/health.py` | Log level PGRST205: ERROR → WARNING |
| `backend/main.py` | `before_send` filter no Sentry SDK |
| `backend/tests/test_supabase_circuit_breaker.py` | Novos testes para exclusion |

---

## Referências

- [Microsoft Azure Circuit Breaker Pattern — error discrimination](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- [PyBreaker `exclude` parameter](https://github.com/danielfm/pybreaker)
- [Sentry Python `before_send` filtering](https://docs.sentry.io/platforms/python/configuration/filtering/)
- [Supabase PGRST205 bug #39446](https://github.com/supabase/supabase/issues/39446)
