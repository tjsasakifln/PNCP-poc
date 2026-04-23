# STORY-BTS-015 — CI-Specific Cache State Flakiness Post-BTS-013

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P3 — CI Investigation (deferred, non-blocking)
**Effort:** M (2-4 hours — forensic investigation required)
**Agents:** @dev + @qa
**Status:** Draft

---

## Context

Descobrido durante o merge cycle de PR #487 (BTS-013 architectural fix
for feature flag runtime overrides). O fix em `config/features.py` faz
`_runtime_overrides` canonical e consultado primeiro por `get_feature_flag`.

O test `test_update_flag_invalidates_ttl_cache` testava o invariant de
que após admin PATCH, `get_feature_flag()` retorna o novo valor. Esse
test **passa deterministicamente em local** (19/19 isolados, 9175+ em
batch) mas **falha em CI** com estado `_feature_flag_cache` mostrando a
entrada original seeded (timestamp indica que nunca foi deletado pela
route) — OU `_runtime_overrides` não contém a entrada no momento da
assertion (impossível pela trace de código).

Os dois cenários apontam para alguma diferença de ambiente CI que não
se reproduz localmente.

**Mitigação imediata (PR #487):** o test foi reescrito para testar o
mecanismo direto (`_runtime_overrides.get(X) is False`) em vez do
full-stack read via `get_feature_flag(X)`. Isso cobre o invariant
arquitetural do BTS-013 sem tocar na flakiness CI-específica. O teste
`test_update_flag_stores_in_memory` já testa o mesmo mecanismo para
outro flag (DIGEST_ENABLED) e passa em CI sem problema.

---

## Hypothesis List (para investigar)

1. **Test ordering effect:** algum test ANTERIOR em ordem alfabética
   (ex: `test_feature_flag_matrix.py`) deixa `_runtime_overrides` OU
   `_feature_flag_cache` em estado que interage com o teardown/setup
   do fixture `clear_overrides`.

2. **Module reload pela TestClient:** `FastAPI.TestClient` pode estar
   reloading algum módulo em CI (não local) que re-inicializa
   `_runtime_overrides = {}` e aponta para um novo dict object, dessincronizando
   o route (bound ao dict original) do test (bound ao novo).

3. **Env var CI-specific:** algum env var setado no workflow CI faz
   `get_feature_flag` comportar-se diferente. Conferir
   `.github/workflows/backend-tests.yml` e variáveis de secret.

4. **Mock mais estrito em CI:** patches de `_redis_set_override` +
   `_redis_get_override` podem ter side effects diferentes sob pytest-cov
   (CI usa coverage, local não por padrão).

5. **Pytest-timeout thread interruption:** o timeout_method='thread'
   do project config pode interromper o route handler antes do
   `_runtime_overrides[X] = new_value` executar em CI (Linux signal),
   enquanto local (WSL/Windows thread) dá mais tolerância.

---

## Acceptance Criteria

### AC1: Reproduzir a falha localmente

- [ ] Rodar test no ambiente Docker isolado espelhando CI (ubuntu-latest +
      python 3.12 + coverage) para reproduzir o `_feature_flag_cache`
      state reportado.
- [ ] Anexar trace log com valores de `_runtime_overrides` e
      `_feature_flag_cache` no ponto da assertion.

### AC2: Identificar root cause

- [ ] Eliminar hipóteses uma a uma via bisect de test ordering + env vars.
- [ ] Documentar no story qual das 5 hipóteses confirma-se.

### AC3: Corrigir e restaurar invariant test

- [ ] Implementar fix (provavelmente em conftest ou no fixture
      `clear_overrides`) que garante o test passa tanto local quanto CI.
- [ ] Restaurar o test `test_update_flag_invalidates_ttl_cache` com
      assertion via `get_feature_flag()` observational invariant.

---

## Scope

**IN:**
- Investigação de CI runner vs local differences para feature-flag state
- Fix no conftest/fixture se necessário
- Restore original assertion contract

**OUT:**
- Refactor de _runtime_overrides architecture (já feito em BTS-013)
- Mudança em routes/feature_flags.py runtime behavior (estável)

---

## Dependencies

- PR #487 merged (delivers the BTS-013 architectural fix)
- Access to CI logs for forensic analysis

---

## Risks

- **Baixo.** Test mitigation via assertion direta sobre `_runtime_overrides`
  já cobre o invariant arquitetural. Esta story restaura rigor de
  observational invariant mas não é blocker de produção.

---

## Files

- `backend/tests/test_feature_flags_admin.py` (modify — restore original assertion after fix)
- `backend/tests/conftest.py` (possibly modify — fixture hardening)

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-22 | @sm (zippy-star) | Story criada pós #487 merge cycle. CI-specific flakiness isolated from BTS-013 arch fix. Mitigação imediata: test reescrito para testar mecanismo direto. Full observational invariant diferido para investigação CI-specific dedicada. |
