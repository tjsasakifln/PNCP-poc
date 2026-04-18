# STORY-CIG-BE-admin-cache-metrics — Admin cache metrics retornam zero (source moved) — 3 testes mock-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
**Priority:** P2 — Gate
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_admin_cache.py` roda em `backend-tests.yml` e falha em **3 testes** do triage row #15/30. Causa raiz classificada como **mock-drift**: a fonte dos metrics do endpoint `/admin/cache` moveu (provavelmente de `search_cache.METRICS_CACHE_HITS` para outro módulo), fazendo a view retornar zero.

**Arquivos principais afetados:**
- `backend/tests/test_admin_cache.py` (3 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Métricas Prometheus foram centralizadas em `backend/metrics.py`; admin endpoint continua lendo de `search_cache.*` que está vazio. Validar com `grep -rn "METRICS_CACHE\\|cache_hits\\|cache_metrics" backend/`.

---

## Acceptance Criteria

- [x] AC1: `pytest backend/tests/test_admin_cache.py -v` retorna exit code 0 localmente (15 passed, 3 previamente-failing agora PASS). Evidência: seção "Root Cause Analysis" abaixo.
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log. (aguarda push/CI — @devops)
- [x] AC3: Causa raiz descrita em "Root Cause Analysis" (mock-drift). Path antes→depois das métricas documentado.
- [x] AC4: Cobertura backend **não caiu** — apenas caminhos de patch em teste foram alterados; nenhum código de produção modificado. Threshold 70% mantido por construção.
- [x] AC5 (NEGATIVO): grep por skip markers vazio. Verificado: `grep -nE "@pytest\.mark\.skip|pytest\.skip\(|@pytest\.mark\.xfail|\.only\(" backend/tests/test_admin_cache.py` → 0 matches.

---

## Investigation Checklist (para @dev, fase Implement)

- [x] Rodar `pytest backend/tests/test_admin_cache.py -v` isolado. Baseline: 3 failed / 12 passed. Pós-fix: 15 passed / 0 failed.
- [x] Mapear onde os métricos vivem agora. `backend/cache.py` foi refatorado em pacote `backend/cache/` com submódulos. `search_cache.py` agora é fachada que reexporta de `cache.admin`, `cache.manager`, etc.
- [x] Decidir: atualizar testes/mocks. Endpoint admin em `backend/admin.py` faz `from cache.admin import ...` dentro da função — patch em `search_cache.X` não tem efeito (facade vs fonte real). Correção isolada ao arquivo de teste.
- [x] Preferir corrigir endpoint se produção realmente retornar zero (prod-bug). **NÃO é prod-bug**: endpoint importa de `cache.admin` corretamente; apenas os mocks de teste usavam o módulo fachada (`search_cache.X`), que é re-export e não altera o símbolo importado localmente em `admin.py`. Produção funciona normalmente.
- [x] Validar cobertura não regrediu — nenhum código de produção modificado.
- [x] Grep de skip markers vazio — verificado (0 matches).

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #15/30)

## Stories relacionadas no epic

- STORY-CIG-BE-cache-redis-cascade (#8 — mesma área cache)
- STORY-CIG-BE-cache-warming-dispatch (#9 — mesma área cache)

---

## Root Cause Analysis

**Classificação:** mock-drift (não prod-bug).

**Contexto da refatoração:** O módulo `backend/cache.py` foi convertido em um pacote `backend/cache/` com submódulos especializados (`admin.py`, `cascade.py`, `manager.py`, `_ops.py`, `swr.py`, `local_file.py`, `redis.py`, `supabase.py`, `memory.py`, `enums.py`). O antigo `backend/search_cache.py` foi mantido como **fachada de compatibilidade** que re-exporta símbolos dos novos submódulos.

**Path antes → depois:**

| Símbolo | Antes (fachada) | Depois (fonte real) |
|---------|-----------------|---------------------|
| `get_cache_metrics` | `search_cache.get_cache_metrics` | `cache.admin.get_cache_metrics` |
| `inspect_cache_entry` | `search_cache.inspect_cache_entry` | `cache.admin.inspect_cache_entry` |
| `invalidate_cache_entry` | `search_cache.invalidate_cache_entry` | `cache.admin.invalidate_cache_entry` |
| `invalidate_all_cache` | `search_cache.invalidate_all_cache` | `cache.admin.invalidate_all_cache` |

**Por que os testes falharam (3 rows):** Os endpoints em `backend/admin.py` (linhas 687, 713, 744, 772) fazem `from cache.admin import <fn>` **dentro do corpo da função** — um import local. Quando o teste chama `patch("search_cache.get_cache_metrics", ...)`, o símbolo no namespace `search_cache` é substituído, mas o endpoint re-resolve a função a partir de `cache.admin` a cada requisição, ignorando o mock. Resultado: a função real executa, acessa Redis/Supabase vazios em ambiente de teste e retorna zeros — daí as asserts `0.0 == 0.73`, `0 == 10`, `404 == 200`.

**Correção:** Redirecionar todos os `patch(...)` de `search_cache.X` para `cache.admin.X` (fonte real que o endpoint consome). Nenhum código de produção precisou ser alterado — o bug era exclusivamente no binding de mock.

**5 patches atualizados** em `backend/tests/test_admin_cache.py`:
1. `TestCacheMetricsEndpoint::test_returns_all_metric_fields` (falhava)
2. `TestCacheInvalidation::test_invalidate_specific_entry` (passava por coincidência — mock nunca era invocado, mas retorno padrão continha os levels esperados; corrigido por consistência)
3. `TestCacheBulkInvalidation::test_with_confirm_header_succeeds` (falhava)
4. `TestCacheInspection::test_inspect_existing_entry` (falhava)
5. `TestCacheInspection::test_inspect_nonexistent_returns_404` (passava por coincidência — endpoint retornava 404 real; corrigido por consistência)

**Invariante preservada:** nenhum `@pytest.mark.skip`, `pytest.skip(...)`, `@pytest.mark.xfail` ou `.only(...)` introduzido.

---

## File List

**Modified:**
- `backend/tests/test_admin_cache.py` — 5 patches redirecionados de `search_cache.*` para `cache.admin.*`

**Not modified (preservados):**
- `backend/admin.py` (endpoints corretos)
- `backend/cache/admin.py` (implementação)
- `backend/search_cache.py` (fachada — re-exports mantidos para compatibilidade)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #15/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (7/10)** — Draft → Ready. Template FE-07 aplicado consistentemente; mock-drift claro; Investigation Checklist acionável.
- **2026-04-18** — @dev: mock-drift corrigido — 5 `patch("search_cache.X")` → `patch("cache.admin.X")` em `backend/tests/test_admin_cache.py`. Causa raiz: endpoints em `admin.py` fazem `from cache.admin import ...` local; patch na fachada `search_cache` não afetava o símbolo resolvido no endpoint. Resultado: **15 passed / 0 failed** (baseline: 3 failed / 12 passed). Nenhuma alteração em código de produção. Status Ready → InReview.
