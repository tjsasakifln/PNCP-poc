# CRIT-036 — Backend: Zero Test Failures (25 → 0)

**Status:** Done
**Priority:** P0 — Blocker
**Severity:** Infraestrutura de qualidade
**Created:** 2026-02-23
**Blocks:** GTM launch (sem baseline limpo, regressões são invisíveis)

---

## Problema

25 testes backend falhando. Parecem "pre-existing" mas na verdade são **test rot** — código mudou, testes não acompanharam. Resultado: qualquer regressão real se esconde no ruído.

### Causa-Raiz por Grupo

| Grupo | Tests | Causa | Módulos |
|-------|-------|-------|---------|
| G1: Revalidation path | 10 | `get_source_config` movido para `source_config.sources`, mas testes patcheiam `search_cache` | test_background_revalidation (5), test_revalidation_quota_cache (4), test_cache_global_warmup (1) |
| G2: Consolidation path | 1 | `compute_search_hash` patched em `search_pipeline`, mas vive em `search_cache` | test_consolidation |
| G3: Profile context | 4 | Endpoint retorna 500 — mock incompleto (falta `.data` no retorno) | test_profile_context |
| G4: Strings i18n | 2 | Código traduzido para PT-BR, assertions ainda em inglês | test_search_state |
| G5: Quota tests | 4 | Quota assertions desatualizadas (limites mudaram de 50→3 buscas, strings PT-BR com encoding) | test_quota |
| G6: Individuais | 8 | Ver detalhes abaixo | 8 arquivos |

---

## Acceptance Criteria

### G1 — Revalidation Module Paths (10 tests)

- [x] **AC1:** `test_background_revalidation.py` — Changed mock from `pncp_client.buscar_todas_ufs_paralelo` to `search_cache._fetch_multi_source_for_revalidation`
- [x] **AC2:** `test_revalidation_quota_cache.py` — Same fix applied to 4 tests
- [x] **AC3:** `test_cache_global_warmup.py::test_revalidation_falls_back_to_pncp_only` — Corrected patch path

### G2 — Consolidation Hash Path (1 test)

- [x] **AC4:** `test_consolidation.py::test_one_source_timeout_partial_results` — Fixed patch path to `search_cache.compute_search_hash`

### G3 — Profile Context Endpoint (4 tests)

- [x] **AC5:** `test_profile_context.py` — Root cause: test pollution from other files' importlib.reload. Fixed with belt-and-suspenders: dependency_overrides + patch("database.get_supabase")

### G4 — Strings PT-BR (2 tests)

- [x] **AC6:** `test_search_state.py::test_old_searches_marked_timed_out` — Updated assertion from English to PT-BR strings
- [x] **AC7:** `test_search_state.py::test_recent_searches_marked_failed` — Updated assertion from English to PT-BR strings

### G5 — Quota Tests (4 tests)

- [x] **AC8a:** `test_quota.py` — Already passing (quota limits match current smartlic_pro plan)
- [x] **AC8b:** `test_quota.py` — Already passing (no encoding issues detected)

### G6 — Individuais (8 tests)

- [x] **AC8:** `test_oauth_story224.py:408` — Test pollution from importlib.reload(oauth) in TestAC12. Passes now after arq fix resolved ordering.
- [x] **AC9:** `test_openapi_schema.py` — Already passing (schema snapshot current)
- [x] **AC10:** `test_sectors.py:129::test_excludes_nebulizacao` — Added nebulização/fumigação to facilities exclusions in `sectors_data.yaml`
- [x] **AC11:** `test_job_queue.py` — Created `_FakeRedisSettings` class + wrapped tests with `patch("arq.connections.RedisSettings")` to avoid sys.modules pollution
- [x] **AC12:** `test_search_session_lifecycle.py:93` — Changed UFs assertion to use `sorted()` comparison
- [x] **AC13:** `test_api_buscar.py` — Fixed autouse fixture: changed ConsolidationResult mock from MagicMock to SimpleNamespace (MagicMock child attributes leaked into Pydantic validation)
- [x] **AC14:** `test_crit001_schema_alignment.py` — Updated column count from 18→19, added `params_hash_global` assertion

### Gate Final

- [x] **AC15:** `pytest` roda com **0 failures** (5127 passed, 0 failed, 5 skipped)
- [x] **AC16:** Coverage ≥ 70% mantida (no production code deleted)
- [x] **AC17:** Nenhum teste foi deletado — apenas corrigido

---

## Estimativa

**Esforço:** ~3-4 horas (maioria é atualização de patch paths e assertions)
**Risco:** Baixo — são fixes de testes, não de código de produção (exceto AC10 sectors exclusion)

## Files

- `backend/tests/test_background_revalidation.py`
- `backend/tests/test_revalidation_quota_cache.py`
- `backend/tests/test_cache_global_warmup.py`
- `backend/tests/test_consolidation.py`
- `backend/tests/test_profile_context.py`
- `backend/tests/test_search_state.py`
- `backend/tests/test_oauth_story224.py`
- `backend/tests/test_openapi_schema.py`
- `backend/tests/test_sectors.py`
- `backend/tests/test_job_queue.py`
- `backend/tests/test_search_session_lifecycle.py`
- `backend/tests/test_api_buscar.py`
- `backend/tests/test_crit001_schema_alignment.py`
- `backend/tests/snapshots/openapi_schema.json`
- `backend/sectors_data.yaml` (se AC10 necessitar)
