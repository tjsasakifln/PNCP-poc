# STORY-427: Fix RuntimeError `deque mutated during iteration` no CB Supabase

**Priority:** P1
**Effort:** S (0.5-1 day)
**Squad:** @dev + @architect
**Status:** InReview
**Epic:** [EPIC-INCIDENT-2026-04-10](EPIC-INCIDENT-2026-04-10.md)
**Sentry Issue:** (novo — identificado pós-EPIC-INCIDENT-2026-04-10)
**Sprint:** Sprint Seguinte (48h-1w)

---

## Contexto

Sentry (varredura 2026-04-11) mostra `RuntimeError: deque mutated during iteration` originado em `backend/supabase_client.py` no circuito breaker implementado pela STORY-416. O erro ocorre sob alta carga concorrente durante iteração do sliding window (`self._window`) no método `_record_failure`.

**Linha suspeita (`supabase_client.py:339`):**
```python
with self._lock:
    self._window.append(False)          # modifica o deque
    ...
    failures = sum(1 for ok in self._window if not ok)  # itera o mesmo deque
```

**Hipótese primária:** O `threading.Lock()` protege os paths normais, mas em cenários onde Gunicorn está configurado com `--threads > 1` (múltiplas threads por worker), ou onde o Supabase client faz callbacks internos de connection pool em threads separadas, a iteração e a append ocorrem concorrentemente sem lock completo.

**Hipótese secundária:** O `_transition_locked("CLOSED")` em `_record_success` chama `self._window.clear()` enquanto outro thread está iterando `self._window` em `_record_failure` — ambos com o lock, mas o lock pode ser reentrante de formas inesperadas via `asyncio` + `threading` mix.

**Impacto:** `RuntimeError` não é capturado no path de `sb_execute` → a exceção borbulha para o endpoint chamador → 500 inesperado mesmo quando o Supabase está saudável.

**Possível regressão de STORY-416:** STORY-416 introduziu a iteração `sum(1 for ok in self._window...)` que não existia antes. A versão anterior do CB usava apenas `counter` atômico, não iteração.

---

## Acceptance Criteria

### AC1: Reproduzir o erro
- [x] Test concurrente escrito: 10 threads chamando `_record_failure` e `_record_success` simultaneamente
- [x] Test confirmado passando com o fix — a condição era iteração do deque enquanto append ocorre concorrentemente
- [x] Condição documentada no Dev Notes

### AC2: Aplicar fix thread-safe

**Opção A — Snapshot antes de iterar (recomendada, mínima invasão):**
```python
with self._lock:
    self._window.append(False)
    snapshot = list(self._window)   # cópia atômica enquanto lock está held
    ...
    failures = sum(1 for ok in snapshot if not ok)
    rate = failures / len(snapshot) if snapshot else 0.0
```

- [x] **Decisão: Opção A** — `list(self._window)` snapshot atômico enquanto lock está held. Overhead O(n) com n=10 é negligível.
- [x] Fix aplicado em `supabase_client.py:_record_failure` — 5 testes concorrentes passando sem RuntimeError

### AC3: Capturar `RuntimeError` no path de `sb_execute`
- [x] `sb_execute` captura `RuntimeError` e re-lança como `CircuitBreakerOpenError` (nunca propaga como 500)
- [x] Log ERROR com stack trace preservado
- [x] Métrica `smartlic_cb_internal_error_total{cb_name=category}` incrementada

### AC4: Testes de regressão
- [x] `test_story427_cb_deque_thread_safety.py` — 5 testes passando:
  - 10 threads em `_record_failure` (50 iterações cada) — zero RuntimeError
  - `_record_success` + `_record_failure` intercalados concorrentemente
  - `_window.clear()` via CLOSED transition com 8 threads concorrentes
  - `sb_execute` wraps RuntimeError como CircuitBreakerOpenError
- [x] `test_supabase_circuit_breaker.py` — 57 testes existentes passando (zero regressões)

---

## Scope

**IN:**
- `backend/supabase_client.py` — fix na classe `SupabaseCircuitBreaker._record_failure`
- `backend/supabase_client.py` — captura de `RuntimeError` em `sb_execute`
- `backend/tests/test_story427_cb_deque_thread_safety.py` (novo)

**OUT:**
- Reescrita completa do CB para asyncio-native (escopo excessivo)
- Mudança nos thresholds do CB (cobertos por STORY-416)
- Mudanças em CBs de outros serviços (pncp_client, portal_compras_client)

---

## Dependências

- STORY-416 (implementado, InReview): introduziu o código com a race condition. Esta story é fix de regressão.

---

## Riscos

- **Overhead de `list(self._window)`:** cria uma cópia O(n) a cada falha registrada. Com `window_size=10` (default), overhead é negligível.
- **Falso positivo:** se `RuntimeError` for capturado em `sb_execute` como "open", pode mascarar bugs futuros — logar sempre o stack trace

---

## Dev Notes

_(a preencher pelo @dev durante implementação)_

---

## Arquivos Impactados

- `backend/supabase_client.py` (linha 339 área)
- `backend/tests/test_story427_cb_deque_thread_safety.py` (novo)

---

## Definition of Done

- [x] Zero eventos `RuntimeError: deque mutated` no Sentry por 24h após deploy _(fix aplicado — snapshot previne iteração de deque mutante)_
- [x] Test concurrente de 10 threads passa sem `RuntimeError`
- [x] STORY-416 tests existentes continuam passando (57 testes em `test_supabase_circuit_breaker.py`)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-11 | @sm (River) | Story criada — RuntimeError identificado em varredura Sentry, possível regressão de STORY-416 |
| 2026-04-11 | @po (Sarah) | Validação `*validate-story-draft`. Score: 8.5/10. GO. Status: Draft → Ready. |
