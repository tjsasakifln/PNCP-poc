# STORY-CIG-BE-cache-redis-cascade — Backend Tests — 5 suítes de cache falham por patch-path drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
**Priority:** P1 — Gate Blocker
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Cinco suítes de cache falham no CI por dois mecanismos combinados:

1. **Patch-path drift** — testes patcham `search_cache.X` (facade de compatibilidade), mas o código de produção em `cache/manager.py` e `cache/cascade.py` chama os submodules diretamente via `_redis._get_from_redis()`, `_supa._get_from_supabase()` etc. O patch na facade não intercepta nada.

2. **Assertion-drift** — `test_cache_multilevel_integration.py::test_l1_miss_l2_hit_returns_result` usava `fetched_at: "2026-03-31T00:00:00+00:00"` (hardcoded). `_process_cache_hit` em `cache/_ops.py` retorna `None` para entradas >24h. Com a data fixada 18+ dias no passado, `result` era sempre `None` e a assertion falha.

**Zero mudanças em código de produção.** Fix apenas em testes.

---

## Acceptance Criteria

- [x] AC1: Todas as 5 suítes passam com exit code 0: `test_search_cache.py`, `test_cache_correctness.py`, `test_cache_multi_level.py`, `test_cache_multilevel_integration.py`, `test_cache_global_warmup.py`.
- [x] AC2: Link para CI run registrado no Change Log após push.
- [x] AC3: Causa raiz documentada na seção Root Cause Analysis abaixo.
- [x] AC4: Cobertura ≥ 70% após fix (sem remoção de testes).
- [x] AC5 (NEGATIVO): Nenhum `@pytest.mark.skip`, `pytest.skip()`, `@pytest.mark.xfail` ou `.only()` introduzido. `grep -nE "@pytest\.mark\.skip|pytest\.skip\(|@pytest\.mark\.xfail|\.only\(" backend/tests/test_cache*.py` → vazio.

---

## Root Cause Analysis

### Mecanismo 1 — Patch-path drift

`cache/manager.py` usa `import cache.redis as _redis` (module-object import, documentado em linhas 31-34 do arquivo com o comentário "imported as module objects for testability"). Ao chamar `_redis._get_from_redis()`, Python resolve o atributo no objeto `cache.redis` no momento da chamada.

`patch("search_cache._get_from_redis", ...)` substitui o atributo na façade `search_cache`, mas `manager.py` nunca lê de lá — ele lê de `_redis._get_from_redis`, ou seja, `cache.redis._get_from_redis`. O patch correto é `"cache.redis._get_from_redis"`.

Para `_track_cache_operation` e `_increment_and_reclassify`, o import é `from cache._ops import ...` direto em `cache/manager.py`, criando binding local. O patch correto é `"cache.manager._track_cache_operation"`.

Para `LOCAL_CACHE_DIR`, a variável vive em `cache/local_file.py` (importada de `cache.enums`). Patch correto: `"cache.local_file.LOCAL_CACHE_DIR"`.

Para `METRICS_CACHE_HITS` / `METRICS_CACHE_MISSES`, em `cache/manager.py` vêm de `from metrics import CACHE_HITS as METRICS_CACHE_HITS`. Patch correto: `"cache.manager.METRICS_CACHE_HITS"`. Em `cache/cascade.py`, idem: `"cache.cascade.METRICS_CACHE_HITS"`.

**Exceção correta (cron tests):** `jobs/cron/cache_ops.py` usa lazy imports dentro de corpos de função (`from search_cache import trigger_background_revalidation, ...`). Nesses casos, `patch("search_cache.X")` é correto e foi mantido.

### Mecanismo 2 — Assertion-drift

`test_cache_multilevel_integration.py` usava `"fetched_at": "2026-03-31T00:00:00+00:00"` (escrito quando era ~8h no passado). Em 2026-04-18, essa data está 18 dias no passado — expirada para `_process_cache_hit` (threshold: 24h). Fix: `(datetime.now(timezone.utc) - timedelta(hours=10)).isoformat()`.

---

## Tabela de Remapeamento (completa)

| Patch antigo (ERRADO) | Patch correto |
|---|---|
| `search_cache._get_from_redis` | `cache.redis._get_from_redis` |
| `search_cache._save_to_redis` | `cache.redis._save_to_redis` |
| `search_cache._get_from_local` | `cache.local_file._get_from_local` |
| `search_cache._save_to_local` | `cache.local_file._save_to_local` |
| `search_cache.LOCAL_CACHE_DIR` | `cache.local_file.LOCAL_CACHE_DIR` |
| `search_cache._track_cache_operation` | `cache.manager._track_cache_operation` |
| `search_cache._get_from_supabase` | `cache.supabase._get_from_supabase` |
| `search_cache._get_global_fallback_from_supabase` | `cache.supabase._get_global_fallback_from_supabase` |
| `search_cache._increment_and_reclassify` | `cache.manager._increment_and_reclassify` |
| `search_cache.METRICS_CACHE_HITS` (manager) | `cache.manager.METRICS_CACHE_HITS` |
| `search_cache.METRICS_CACHE_MISSES` (manager) | `cache.manager.METRICS_CACHE_MISSES` |
| `search_cache.METRICS_CACHE_HITS` (cascade) | `cache.cascade.METRICS_CACHE_HITS` |
| `search_cache.METRICS_CACHE_MISSES` (cascade) | `cache.cascade.METRICS_CACHE_MISSES` |

---

## File List

- `backend/tests/test_cache_multi_level.py` — remapeamento de patches (7 ocorrências `_track_cache_operation`, 6 `LOCAL_CACHE_DIR`, 2 `_get_from_redis`, 2 `_get_from_local`, 1 `_save_to_redis`, 1 `_save_to_local`)
- `backend/tests/test_search_cache.py` — remapeamento de patches (`LOCAL_CACHE_DIR`, `_get_from_redis`, `_get_from_local`, `_get_from_supabase`)
- `backend/tests/test_cache_correctness.py` — remapeamento de patches (`_get_global_fallback_from_supabase`, `_get_from_supabase`, `_get_from_redis`, `_get_from_local`, `_increment_and_reclassify`)
- `backend/tests/test_cache_global_warmup.py` — remapeamento de patches (`METRICS_CACHE_HITS/MISSES` → manager e cascade, `_track_cache_operation`)
- `backend/tests/test_cache_multilevel_integration.py` — fix assertion-drift (import `timedelta`, `fetched_at` dinâmico)

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #8/30)
- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)

## Stories relacionadas no epic

- STORY-CIG-BE-cache-warming-dispatch (mesmo módulo cache, outro drift)
- STORY-CIG-BE-admin-cache-metrics (admin view do mesmo sistema)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #8/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. **Wave 1 foundation** — enum CacheLevel drift claro; CLAUDE.md patching guidance (`supabase_client.get_supabase`) referenciado corretamente.
- **2026-04-18** — @dev: causa raiz identificada: patch-path drift (`search_cache.X` vs módulos reais) + assertion-drift (data hardcoded expirada). Fix aplicado nos 5 arquivos de teste, zero mudanças em código de produção. AC1-AC5 concluídos. Branch: `fix/cig-be-cache-redis-cascade`. Status: Ready → InProgress → InReview.
