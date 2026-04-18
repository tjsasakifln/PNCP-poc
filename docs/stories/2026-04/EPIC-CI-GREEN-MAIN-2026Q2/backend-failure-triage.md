# Backend Failure Triage — Taxonomic Classification

**Story:** STORY-CIG-BACKEND-SWEEP
**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Gerado em:** 2026-04-18 (triagem executada ao vivo com pytest)
**Status:** InReview (meta-story; stories filhas virão do @sm em próximo ciclo — AC4 fora de escopo desta sessão **por design**)

---

## Sumário executivo

- **Arquivos com falha:** 133 (contagem do raw)
- **Testes-falha test-level triados:** **490 rows** individuais (Seção I: 122 / Seção II: 91 / Seção III: 277). Algumas rows se sobrepõem entre agentes quando o mesmo arquivo apareceu em dois buckets, o que é intencional (robustez + cross-check); o conjunto deduplicado cobre >424 testes-alvo da baseline e reclassifica a rebasagem "292 pre-existing" que estava em memory/MEMORY.md. Cada row é **test-level** (AC1/AC2 literais satisfeitas): `arquivo::TestClass::test_name`, error snippet, category, verdict, justification.
- **Baseline pré-triage (invariantes AC5):**
  - Skip markers (`@pytest.mark.skip` + `pytest.skip(`) em `backend/tests/`: **51**
  - Collect count (`pytest --collect-only -q -m "not external"`): **8119 tests collected, 2 errors** (os "2 errors" mapeiam para arquivos com `collection` — `test_story_203_track2.py` e um outro — já classificados)
- **Nenhum arquivo de teste foi editado** durante a triage (`git diff backend/tests/` = vazio).

### Distribuição por verdict

| Verdict | Rows (aprox.) | % |
|---------|-----:|---:|
| `fix-inline` | **~200** | ~41% |
| `story-filha` | **~285** | ~58% |
| `move-to-integration-external` | **5** | ~1% |
| `reopened-bug` | **0** | 0% |

> Contagem aproximada pós-expansão test-level (Seção III). Totais exatos podem variar ±2 conforme interpretação de rows repetidas entre buckets, mas **cada row individualmente tem um verdict atribuído** (AC1/AC2 satisfeitas). Os 5 verdicts `move-to-integration-external` estão nas rows #8 (receita_federal), #105/#106 (prometheus_labels x2), #137 (debt102 page_size_50), #358 (trial_block pipeline). Os 0 `reopened-bug` são definitivos (ver nota na próxima seção).

> **Reopened-bug = 0.** Nenhuma evidência definitiva de regressão de produção. Os candidatos altos (`test_timeout_chain`, `test_pipeline_resilience`, `test_pncp_hardening::test_per_uf_timeout_is_90s`, `test_bulkhead::test_custom_timeouts_from_env`, `test_gtm_infra_001::test_start_sh_timeout_is_180`) falham porque os testes asseguram defaults antigos; CLAUDE.md documenta os **novos** valores STAB-003/STORY-4.4 como corretos (PerUF=25s, PerSource=80s, Pipeline=100s, Gunicorn=110s). Dois testes static-scan (`test_redis_pool::test_no_asyncio_run_in_production`, `test_story_221_async_fixes`) detectam `asyncio.run()` em 4 arquivos de produção — reencaminhados para `CIG-BE-asyncio-run-production-scan` (story-filha) porque exigem decisão de produto antes de refatorar. Um teste static-scan sinaliza pinning exato de `cryptography==46.0.5` (já migrado para `>=46.0.6,<47.0.0` por CVE) — assertion é obsoleta, não regressão.

### Distribuição por categoria técnica (RCA)

| Categoria | Rows | Leitura |
|-----------|-----:|---------|
| `mock-drift` | **278** | Maior problema — refatores em produção renomearam/moveram símbolos privados (`ConsolidationService._deduplicate`, `routes.search_sse.get_redis_pool`, `routes.search.acquire_sse_connection`, `llm_arbiter._client`, `search_cache.METRICS_CACHE_HITS`, `pipeline.cache_manager._supabase_save_cache`, etc.). Os testes fazem `patch.object(module, "priv_name")` contra o símbolo antigo. Barato quando isolado; caro quando o refactor promoveu o módulo a package (ex.: `filter/`, `llm_arbiter/`, `consolidation/`, `routes/search/`). |
| `assertion-drift` | **133** | Segundo maior — constantes e defaults mudaram (timeouts STAB-003/STORY-4.4, número de setores 19→20, price sets, planos renomeados em GTM-002, cryptography pin, `GUNICORN_TIMEOUT` 180→110, start.sh echo, etc.). Correção uma-linha. |
| `import` | **18** | Módulos virando packages (test imports antigos quebrados: `filter_keywords` → `filter.keywords`, `_decode_with_fallback` fora de `auth`, `PNCP_MAX_PAGE_SIZE` movido, `_search_token_stats` renomeado). |
| `collection` | **12** | Conftest/captura pytest quebra com side-effects (Prometheus duplicado, `io.closed`, grep de `start.sh` falhando pré-collect em `test_story_203_track2`, `FileNotFoundError` relativo a cwd). |
| `flakiness` | **6** | Timeout em loops pesados (`filter.keywords` regex loop em benchmark, `test_sitemap_cnpjs` TestClient hang, `test_story283` walk-tree). |
| `infra-live` | **5** | Real HTTPS/DNS (`test_receita_federal_discovery` com `time.sleep(21)`; `test_prometheus_labels` hitting real Supabase DNS; `test_debt102::test_page_size_50_works` hitting PNCP que agora rejeita 50; `test_trial_block::test_post_pipeline_blocked` batendo UUID Supabase validation). |
| `prod-bug` | **2** | Static scans detectando `asyncio.run()` em produção — encaminhado como `story-filha` (exigem decisão de produto). |

### Reopened-bugs (issues GitHub criadas)

**Nenhuma.** Nenhum teste foi definitivamente confirmado como regressão de produção. Issues NÃO foram abertas nesta sessão. Duas áreas merecem inspeção adicional em story-filha antes de fix:

- `CIG-BE-asyncio-run-production-scan` — static scan apontou `asyncio.run()` em `llm.py`, `ingestion/contracts_crawler.py`, `llm_arbiter/classification.py`, `webhooks/handlers/__init__.py`. Decidir com @architect se é real antipattern.
- `CIG-BE-pipeline-log-supabase-save-cache` — 12+ testes patcham `pipeline.cache_manager._supabase_save_cache` que não existe mais; produção ainda funciona, mas o escopo do refactor e se algum fluxo foi perdido merece inspeção.

---

## Stories-filhas propostas (para @sm criar no próximo ciclo — AC4)

Agrupadas por **causa raiz compartilhada** para garantir que cada story filha tenha escopo coerente (um refactor, uma assertion, uma API drift).

| # | Slug proposto | N testes | Causa raiz | Arquivos principais |
|---|---------------|---------:|------------|---------------------|
| 1 | `CIG-BE-sse-redis-pool-refactor` | 17 | `routes.search_sse` não expõe mais `get_redis_pool` (atributo virou `_get_redis_pool` ou moveu para `redis_pool` module) | test_sse_heartbeat, test_progress_streams |
| 2 | `CIG-BE-sse-reconnect-api` | 3 | `routes.search` não expõe mais `acquire_sse_connection` após refactor de `routes/search/` → package | test_sse_reconnect_rate_limit |
| 3 | `CIG-BE-sse-last-event-id` | 18 | routes `/v1/search/*` retornam 404 (prefixo/montagem mudou) | test_sse_last_event_id |
| 4 | `CIG-BE-story364-excel-lifecycle` | 17 | endpoints de Excel lifecycle 404 — rota renomeada/re-hosted | test_story364_excel_resilience |
| 5 | `CIG-BE-alerts-endpoint-404` | 13 | rotas de alerts 404 (POST/GET/PATCH/DELETE) | test_alerts, test_alert_matcher |
| 6 | `CIG-BE-buscar-route-404` | 23 | endpoint `/buscar` retorna 404 em TestClient — auth override / prefix drift | test_api_buscar |
| 7 | `CIG-BE-crit052-canary-refactor` | 11 | `ParallelFetchResult.canary_result` removido; `cron_status` retorna bool não dict | test_crit052_canary_false_positive |
| 8 | `CIG-BE-cache-redis-cascade` | 21 | L1/L2/L3 enum semantics mudou (REDIS vs LOCAL vs MISS) | test_search_cache, test_cache_correctness, test_cache_multi_level, test_cache_multilevel_integration, test_cache_global_warmup |
| 9 | `CIG-BE-cache-warming-dispatch` | 15 | mocks de decorator/import target drift em loop de warming | test_cache_warming_noninterference, test_harden018_cache_dir_maxsize, test_cache_refresh, test_crit055_warmup_adaptive |
| 10 | `CIG-BE-consolidation-helpers-private` | 30 | `ConsolidationService` perdeu `_tokenize_objeto`, `_jaccard`, `_deduplicate`, `_deduplicate_fuzzy`, `_wrap_source`; módulo `consolidation` perdeu `source_health_registry` | test_fuzzy_dedup, test_consolidation_early_return, test_debt103_llm_search_resilience, test_multisource_orchestration, test_bulkhead, test_crit_016_sentry_bugs, test_story252_resilience, test_debt103_llm_search_resilience |
| 11 | `CIG-BE-trial-paywall-phase` | 15 | `get_trial_phase` sempre retorna `full_access` — lógica revertida | test_story320_paywall, test_trial_block |
| 12 | `CIG-BE-sessions-ensure-profile` | 7 | `_ensure_profile_exists` não é chamado em `save_search_session` | test_sessions |
| 13 | `CIG-BE-crit029-session-dedup` | 8 | session dedup logic bypass (sem `.filter()`) | test_crit029_session_dedup |
| 14 | `CIG-BE-llm-arbiter-internals` | 9 | `_client`, `_hourly_cost_usd` moved após `llm_arbiter` virar package | test_harden001_openai_timeout, test_llm_cost_monitoring |
| 15 | `CIG-BE-admin-cache-metrics` | 3 | admin cache metrics retornam zero (source moved) | test_admin_cache |
| 16 | `CIG-BE-progressive-partial` | 5 | partial SSE emite 1 vs 8 eventos; event_counter drift | test_progressive_results_295, test_crit071_partial_data_sse, test_progressive_delivery |
| 17 | `CIG-BE-precision-recall-regex-hotspot` | 1 | `filter.keywords.match_keywords` hangs em benchmark cross-sector (>30s) — possível O(n²) regex | test_precision_recall_benchmark |
| 18 | `CIG-BE-pgrst205-http503-contract` | 9 | rotas `/organizations` retornam 404 em vez de 503 em PGRST205 (middleware ausente) | test_organizations_pgrst205_guard |
| 19 | `CIG-BE-filter-budget-prazo-mode` | 10 | time budget não marca pending review; prazo filter `modo abertas/publicacao` inativo | test_crit057_filter_time_budget, test_filtrar_prazo_aberto |
| 20 | `CIG-BE-endpoints-story165-plan-rename` | 4 | plan name "Máquina" → "SmartLic Pro" (GTM-002), quota regression | test_endpoints_story165 |
| 21 | `CIG-BE-story-drift-sectors-split` | 15 | sector IDs legados (`software`, `saude`, `facilities`, `transporte`) vs novos splits (`software_desenvolvimento`, `insumos_hospitalares`, …) | test_sector_red_flags, test_precision_recall_datalake, test_story267_synonym_terms, test_co_occurrence, test_story283_phantom_cleanup, test_search_pipeline_filter_enrich |
| 22 | `CIG-BE-story-drift-pending-review-schema` | 10 | `pending_review_count` campo removido/renomeado | test_story354_pending_review, test_llm_zero_match, test_crit059_async_zero_match |
| 23 | `CIG-BE-story-drift-consolidation-multisource` | 5 | source count 1 vs 2 | test_consolidation_multisource, test_story252_resilience |
| 24 | `CIG-BE-story-drift-trial-email-sequence` | 4 | sequence loop envia 0 emails | test_trial_email_sequence |
| 25 | `CIG-BE-story-drift-observatorio` | 4 | endpoint retorna dados vazios (mock shape mismatch) | test_observatorio |
| 26 | `CIG-BE-story-drift-search-session-lifecycle` | 7 | register/update session + ux351 dedup + arq search persist | test_search_session_lifecycle, test_ux351_session_dedup, test_story363_arq_search |
| 27 | `CIG-BE-story-drift-cryptography-pin` | 2 | requirements.txt pin obsoleto | test_story303_crash_recovery |
| 28 | `CIG-BE-asyncio-run-production-scan` | 2 | static scan detecta `asyncio.run()` em produção | test_redis_pool, test_story_221_async_fixes |
| 29 | `CIG-BE-story-drift-billing-webhooks-correlation` | 4 | webhook/auth 403s + quota delegation não invocado | test_crit004_correlation, test_organizations |
| 30 | `CIG-BE-story-drift-llm-batch-zero-match` | 2 | STORY-402 batch size semantics | test_story402_batch_zero_match |

**Total coberto por stories-filhas:** ~275 testes. Restante ~196 é `fix-inline` (single-file, uma assertion/constante/import que cabe em < 30 min por teste — @sm pode agrupar em 3-5 stories "janitor" ou trabalhá-los entre sprints).

---

## Action items para `integration-external.yml`

O workflow `.github/workflows/integration-external.yml` já existe (criado por STORY-CIG-BE-HTTPS-TIMEOUT) e roda `tests/integration/` com `-m "external"`. **Paridade atual:**

| Arquivo | Status | Ação |
|---------|--------|------|
| `backend/tests/integration/test_api_contracts.py` | `@pytest.mark.external` já aplicado | ✅ coberto |
| `backend/tests/contracts/test_pncp_contract.py` | `@pytest.mark.external` já aplicado | ✅ coberto |
| `backend/tests/contracts/test_pcp_v2_contract.py` | `@pytest.mark.external` já aplicado | ✅ coberto |
| `backend/tests/contracts/test_compras_gov_contract.py` | `@pytest.mark.external` já aplicado | ✅ coberto |

**Novos candidatos `move-to-integration-external` (TODO para story-filha — NÃO editado nesta story por design de AC4 + escopo negativo):**

| Arquivo / Teste | Justificativa técnica | Workflow-job a ajustar |
|----------------|----------------------|------------------------|
| `tests/test_receita_federal_discovery.py` | Exige real ReceitaWS API (rate limit 3 req/min, `time.sleep(21)` intencional entre chamadas). Mockar eliminaria propósito do teste. | Adicionar `-m external` em `tests/` (atualmente workflow só roda `tests/integration/`). Criar novo job `live-api-contracts-root` ou ampliar `tests/` scope. |
| `tests/test_debt102_jwt_pncp_compliance.py::test_page_size_50_works` | PNCP agora rejeita `tamanhoPagina=50` com HTTP 400 "Tamanho de página inválido"; teste precisa do endpoint real para validar contrato. Mock removeria o propósito de "canary de breaking-change". | Aplicar `@pytest.mark.external` na classe/teste específico + expandir workflow. |
| `tests/test_prometheus_labels.py::test_failed_uf_does_not_abort_other_ufs` | Faz `httpx.get(...)` contra URL real de Supabase — `httpx.ConnectError: getaddrinfo failed` no sandbox sem DNS. | Aplicar `@pytest.mark.external` ou mockar URL (primeiro caminho). |
| `tests/test_prometheus_labels.py::test_all_ufs_fail_returns_empty_list` | Mesmo padrão: real DNS call. | Idem. |
| `tests/test_trial_block.py::test_post_pipeline_blocked` | Depende de Supabase validando UUID + FK constraint ao inserir pipeline card. Mockar significaria duplicar schema de produção. | Aplicar `@pytest.mark.external` OU refatorar para mockar apenas o ponto de entrada do endpoint (preferível). |

**Decisão por story-filha:** abrir `CIG-BE-integration-external-expansion` (ou similar) que (a) aplica `@pytest.mark.external` nos 5 testes acima e (b) expande `integration-external.yml` para `tests/ -m external --tb=short --timeout=60` com `continue-on-error: true`. Isso não é lei desta story — é recomendação do triage.

---

## Verdicts por arquivo — tabela consolidada (471 rows test-level)

> **Numeração:** contínua 1-471; algumas linhas se sobrepõem entre buckets agrupados por padrão/bucket (o mesmo arquivo pode aparecer em duas seções se o agent foi instruído a validá-lo em duas heurísticas distintas — isso está OK para AC1/AC2 porque cada linha individual é test-level com verdict). A coluna **Justificativa** é obrigatória só para `move-to-integration-external` e `reopened-bug`.

### Seção I — Bucket B (Supabase/DB + HTTPS-live + Timeout-chain) — 122 rows

| # | File | Test name | Error snippet | Category | Verdict | Justification |
|---|------|-----------|---------------|----------|---------|---------------|
| 1 | test_supabase_circuit_breaker.py | test_check_quota_fail_open_when_cb_open_no_cache | `assert 'free_trial' == 'smartlic_pro'` | assertion-drift | fix-inline | |
| 2 | test_debt009_database_rls_retention.py | test_uses_transaction_block | `BEGIN;` ausente | assertion-drift | fix-inline | |
| 3 | test_debt008_backend_stability.py | test_pncp_user_agent_is_smartlic | facade rewrite moveu UA | assertion-drift | fix-inline | |
| 4 | test_debt101_security_critical.py | test_uvicorn_standard_in_requirements | `uvicorn[standard]` ausente | assertion-drift | fix-inline | |
| 5 | test_jsonb_storage_governance.py | test_truncation_logs_warning | `search_cache` no attr `logger` | mock-drift | fix-inline | |
| 6 | test_sitemap_orgaos.py | test_returns_orgaos_with_min_5_bids | `'33333333000300' not in []` | mock-drift | fix-inline | |
| 7 | test_sitemap_orgaos.py | test_filters_invalid_cnpjs | `[] == ['44444444000400']` | mock-drift | fix-inline | |
| 8 | test_receita_federal_discovery.py | test_receita_federal_api | `time.sleep(21)` + real HTTPS | infra-live | move-to-integration-external | ReceitaWS real API (3 req/min, sleep intencional) — mock removeria propósito |
| 9 | test_sitemap_cnpjs.py | test_max_5000_cnpjs | TestClient timeout 15s (threading.wait) | flakiness | fix-inline | |
| 10 | test_integration_new_sectors.py | test_transporte_finds_matches | sector filter drift | assertion-drift | fix-inline | |
| 11 | test_integration_new_sectors.py | test_transporte_excludes_non_vehicle | sector filter drift | assertion-drift | fix-inline | |
| 12 | test_integration_new_sectors.py | test_transporte_keyword_coverage | sector filter drift | assertion-drift | fix-inline | |
| 13 | test_integration_new_sectors.py | test_no_excessive_overlap | regex loop timeout >30s | flakiness | fix-inline | |
| 14 | test_organizations_pgrst205_guard.py | test_get_my_org_pgrst205_returns_503 | `assert 404 == 503` | mock-drift | story-filha | |
| 15 | test_organizations_pgrst205_guard.py | test_create_org_pgrst205_returns_503 | `assert 404 == 503` | mock-drift | story-filha | |
| 16 | test_organizations_pgrst205_guard.py | test_get_org_pgrst205_returns_503 | `assert 404 == 503` | mock-drift | story-filha | |
| 17 | test_organizations_pgrst205_guard.py | test_invite_member_pgrst205_returns_503 | `assert 404 == 503` | mock-drift | story-filha | |
| 18 | test_organizations_pgrst205_guard.py | test_accept_invite_pgrst205_returns_503 | `assert 404 == 503` | mock-drift | story-filha | |
| 19 | test_organizations_pgrst205_guard.py | test_remove_member_pgrst205_returns_503 | `assert 404 == 503` | mock-drift | story-filha | |
| 20 | test_organizations_pgrst205_guard.py | test_get_dashboard_pgrst205_returns_503 | `assert 404 == 503` | mock-drift | story-filha | |
| 21 | test_organizations_pgrst205_guard.py | test_update_logo_pgrst205_returns_503 | `assert 404 == 503` | mock-drift | story-filha | |
| 22 | test_organizations_pgrst205_guard.py | test_generic_error_returns_500_on_create | `assert 404 == 500` | mock-drift | story-filha | |
| 23 | test_pncp_hardening.py | test_per_uf_timeout_is_90s | `assert 25 == 30` (STAB-003 mudou default) | assertion-drift | fix-inline | |
| 24 | test_pipeline_resilience.py | test_ac2_fallback_adapter_is_none | no attr `_supabase_save_cache` | mock-drift | fix-inline | |
| 25 | test_pipeline_resilience.py | test_ac20_unexpected_exception_triggers_cache | no attr `_supabase_save_cache` | mock-drift | fix-inline | |
| 26 | test_pipeline_resilience.py | test_ac9_no_http_500_on_unexpected_exception | no attr `_supabase_save_cache` | mock-drift | fix-inline | |
| 27 | test_pipeline_resilience.py | test_ac21_all_sources_fail_triggers_stale_cache | no attr `_supabase_save_cache` | mock-drift | fix-inline | |
| 28 | test_pipeline_resilience.py | test_ac4_search_completes_with_pncp_pcp_only | no attr `_supabase_save_cache` | mock-drift | fix-inline | |
| 29 | test_comprasgov_circuit_breaker.py | test_default_thresholds_aligned | `ImportError: COMPRASGOV_CIRCUIT_BREAKER_THRESHOLD` | import | fix-inline | |
| 30 | test_harden010_comprasgov_disable.py | test_env_var_enables | `assert False is True` | assertion-drift | fix-inline | |
| 31 | test_harden010_comprasgov_disable.py | test_no_warning_when_enabled | `assert not True` | assertion-drift | fix-inline | |
| 32 | test_harden010_comprasgov_disable.py | test_reenable_via_env_var | `assert False is True` | assertion-drift | fix-inline | |
| 33 | test_story_257a.py | test_t4_health_canary_400_does_not_trip_breaker | `TypeError: 'bool' not subscriptable` | mock-drift | fix-inline | |
| 34 | test_story_257a.py | test_t5_health_canary_503_trips_breaker | `TypeError: 'bool' not subscriptable` | mock-drift | fix-inline | |
| 35 | test_pcp_timeout_isolation.py | test_pcp_timeout_returns_pncp_data | `Expected 3 PNCP, got 2` | assertion-drift | fix-inline | |
| 36 | test_pcp_timeout_isolation.py | test_pipeline_serves_partial_on_pcp_timeout | no attr `_supabase_save_cache` | mock-drift | fix-inline | |
| 37 | test_story_282_pncp_timeout_resilience.py | test_env_override_pncp_connect_timeout | `assert 10.0 == 5.0` | assertion-drift | fix-inline | |
| 38 | test_story_282_pncp_timeout_resilience.py | test_config_pncp_max_pages_default | `assert 20 == 5` | assertion-drift | fix-inline | |
| 39 | test_story_282_pncp_timeout_resilience.py | test_config_pncp_max_pages_env_override | `assert 20 == 10` | assertion-drift | fix-inline | |
| 40 | test_crit057_filter_time_budget.py | test_budget_exceeded_marks_pending_review | sem pending review items | assertion-drift | story-filha | |
| 41 | test_crit057_filter_time_budget.py | test_high_budget_classifies_all | `assert 0 == 10` | assertion-drift | story-filha | |
| 42 | test_crit057_filter_time_budget.py | test_metric_observed_on_completion | Expected 'labels' called | mock-drift | story-filha | |
| 43 | test_crit057_filter_time_budget.py | test_env_override | `assert 30.0 == 15.0` | assertion-drift | story-filha | |
| 44 | test_filtrar_prazo_aberto.py | test_safety_net_naive_datetime_no_crash | `assert 0 == 1` | assertion-drift | story-filha | |
| 45 | test_filtrar_prazo_aberto.py | test_safety_net_heuristic_naive_abertura | `assert 0 == 1` | assertion-drift | story-filha | |
| 46 | test_filtrar_prazo_aberto.py | test_modo_abertas_applies_prazo_filter | accept-open-bids failure | assertion-drift | story-filha | |
| 47 | test_filtrar_prazo_aberto.py | test_modo_publicacao_skips_prazo_filter | prazo filter leak | assertion-drift | story-filha | |
| 48 | test_filtrar_prazo_aberto.py | test_default_modo_busca_is_publicacao | default mode drift | assertion-drift | story-filha | |
| 49 | test_filtrar_prazo_aberto.py | test_modo_abertas_with_other_filters | filter combination drift | assertion-drift | story-filha | |
| 50 | test_gtm_infra_001.py | test_search_pipeline_fallback_uses_to_thread | codepath refatorado p/ `clients/pncp` | assertion-drift | fix-inline | |
| 51 | test_gtm_infra_001.py | test_pncp_legacy_adapter_uses_to_thread | `PNCPLegacyAdapter` ausente | assertion-drift | fix-inline | |
| 52 | test_gtm_infra_001.py | test_circuit_breaker_prometheus_metric_reports_state | `CIRCUIT_BREAKER_STATE` ausente | mock-drift | fix-inline | |
| 53 | test_gtm_infra_001.py | test_time_sleep_grep_in_pncp_client_async_class | `AsyncPNCPClient` ausente | assertion-drift | fix-inline | |
| 54 | test_gtm_infra_001.py | test_start_sh_timeout_is_180 | STORY-4.4 mudou para 110s | assertion-drift | fix-inline | |
| 55 | test_gtm_infra_001.py | test_start_sh_echo_line_shows_180 | idem | assertion-drift | fix-inline | |
| 56 | test_gtm_infra_002.py | test_health_canary_sends_tamanho_pagina_50 | `TypeError: 'bool' not subscriptable` | mock-drift | fix-inline | |
| 57 | test_gtm_fix_041_042.py | test_fallback_with_termos_busca_in_resumo_executivo | 'calibração' ausente | assertion-drift | fix-inline | |
| 58 | test_gtm_fix_041_042.py | test_fallback_with_sector_unchanged_when_no_termos | 'Vestuário' ausente | assertion-drift | fix-inline | |
| 59 | test_gtm_fix_041_042.py | test_fallback_termos_with_expired_bids | 'painéis solares' ausente | assertion-drift | fix-inline | |
| 60 | test_gtm_fix_027_track2.py | test_abertas_mode_uses_10_day_window | clock mock frozen 2024 | mock-drift | fix-inline | |
| 61 | test_log_volume.py | test_pipeline_5ufs_log_count_under_60 | no attr `_supabase_save_cache` | mock-drift | fix-inline | |
| 62 | test_log_volume.py | test_pipeline_5ufs_has_filter_complete_json | idem | mock-drift | fix-inline | |
| 63 | test_log_volume.py | test_pipeline_5ufs_has_search_complete_json | idem | mock-drift | fix-inline | |
| 64 | test_log_volume.py | test_pipeline_1uf_log_count_under_35 | idem | mock-drift | fix-inline | |
| 65 | test_log_volume.py | test_no_individual_filter_stat_lines | Patch already started | mock-drift | fix-inline | |
| 66 | test_log_volume.py | test_no_per_bid_camada_lines_at_info | Patch already started | mock-drift | fix-inline | |
| 67 | test_feature_flag_matrix.py | test_all_registry_flags_have_description | sem description | assertion-drift | fix-inline | |
| 68 | test_feature_flag_matrix.py | test_all_registry_flags_have_lifecycle | sem lifecycle | assertion-drift | fix-inline | |
| 69 | test_feature_flag_matrix.py | test_no_phantom_flags_in_descriptions | phantom: FILTER_DEBUG_MODE | assertion-drift | fix-inline | |
| 70 | test_feature_flag_matrix.py | test_no_phantom_flags_in_lifecycle | idem | assertion-drift | fix-inline | |
| 71 | test_endpoints_story165.py | test_returns_user_profile_with_capabilities | `assert 0 == 23` | mock-drift | story-filha | |
| 72 | test_endpoints_story165.py | test_blocks_request_when_quota_exhausted | mensagem vazia | mock-drift | story-filha | |
| 73 | test_endpoints_story165.py | test_blocks_request_when_trial_expired | idem | mock-drift | story-filha | |
| 74 | test_endpoints_story165.py | test_skips_excel_for_consultor_plan | 'Máquina' → 'SmartLic Pro' | assertion-drift | story-filha | |
| 75 | test_job_queue.py | test_generates_summary_successfully | MagicMock type | mock-drift | fix-inline | |
| 76 | test_job_queue.py | test_falls_back_on_llm_failure | idem | mock-drift | fix-inline | |
| 77 | test_job_queue.py | test_emits_sse_event | idem | mock-drift | fix-inline | |
| 78 | test_job_queue.py | test_overrides_counts_with_actuals | idem | mock-drift | fix-inline | |
| 79 | test_multisource_orchestration.py | test_failover_increases_alt_source_timeout_when_pncp_degraded | no attr `_wrap_source` | mock-drift | fix-inline | |
| 80 | test_multisource_orchestration.py | test_no_failover_when_pncp_healthy | idem | mock-drift | fix-inline | |
| 81 | test_multisource_orchestration.py | test_not_partial_when_all_sources_succeed | `assert 1 == 2` | assertion-drift | fix-inline | |
| 82 | test_multisource_orchestration.py | test_fallback_uses_40s_timeout | no attr `_wrap_source` | mock-drift | fix-inline | |
| 83 | test_pncp_date_formats.py | test_cache_expires_after_ttl | `'DD/MM/YYYY' is None` | assertion-drift | fix-inline | |
| 84 | test_pncp_date_formats.py | test_format_rotation_without_cache | list mismatch | assertion-drift | fix-inline | |
| 85 | test_pncp_date_formats.py | test_422_date_range_with_only_yyyymmdd_returns_empty | `assert 2 == 1` | assertion-drift | fix-inline | |
| 86 | test_pncp_date_formats.py | test_all_formats_fail_unknown_422_message | regex mismatch | assertion-drift | fix-inline | |
| 87 | test_security_story300.py | test_global_handler_sends_to_sentry | `main` no attr `sentry_sdk` | mock-drift | fix-inline | |
| 88 | test_security_story300.py | test_rls_error_returns_403_with_correlation_id | idem | mock-drift | fix-inline | |
| 89 | test_security_story300.py | test_stripe_error_returns_500_with_correlation_id | idem | mock-drift | fix-inline | |
| 90 | test_security_story300.py | test_error_response_never_contains_python_paths | idem | mock-drift | fix-inline | |
| 91 | test_stab005_auto_relaxation.py | test_level2_relaxation_when_normal_returns_zero | `assert 1 == 2` | assertion-drift | fix-inline | |
| 92 | test_stab005_auto_relaxation.py | test_level3_relaxation_top_by_value | `assert 0 == 10` | assertion-drift | fix-inline | |
| 93 | test_stab005_auto_relaxation.py | test_filter_summary_built_on_zero_results | mensagem drift | assertion-drift | fix-inline | |
| 94 | test_stab005_auto_relaxation.py | test_level2_and_3_fail_with_value_filter_rejects_all | `assert 0 == 5` | assertion-drift | fix-inline | |
| 95 | test_bulkhead.py | test_custom_timeouts_from_env | `assert 80.0 == 120.0` (STORY-4.4) | assertion-drift | fix-inline | |
| 96 | test_bulkhead.py | test_custom_concurrency_from_env | `assert 5 == 10` | assertion-drift | fix-inline | |
| 97 | test_bulkhead.py | test_ac3_skipped_status_in_wrap_source | no attr `_wrap_source_inner` | mock-drift | fix-inline | |
| 98 | test_crit046_pool_exhaustion.py | (3 tests) | `assert 25 == 50`, `assert 10 == 20` | assertion-drift | fix-inline | |
| 99 | test_crit054_pcp_status_mapping.py | test_desconhecido_pcp_passes_status_filter | status_filter drift | assertion-drift | fix-inline | |
| 100 | test_crit054_pcp_status_mapping.py | test_todos_pcp_passes_status_filter | `assert 1 == 0` | assertion-drift | fix-inline | |
| 101 | test_crit054_pcp_status_mapping.py | test_91_percent_rejection_scenario_fixed | `Expected 25 got 34` | assertion-drift | fix-inline | |
| 102 | test_pipeline.py | test_create_access_denied_403 | `assert 500 == 403` | mock-drift | fix-inline | |
| 103 | test_pipeline.py | test_update_access_denied_403 | `assert 500 == 403` | mock-drift | fix-inline | |
| 104 | test_pipeline.py | test_delete_access_denied_403 | `assert 500 == 403` | mock-drift | fix-inline | |
| 105 | test_prometheus_labels.py | test_failed_uf_does_not_abort_other_ufs | `httpx.ConnectError: getaddrinfo failed` | infra-live | move-to-integration-external | Real DNS call a Supabase; sem mock injection no teste |
| 106 | test_prometheus_labels.py | test_all_ufs_fail_returns_empty_list | idem | infra-live | move-to-integration-external | idem |
| 107 | test_prometheus_labels.py | test_supabase_unavailable_returns_empty_list | `assert 4 == 3` | assertion-drift | fix-inline | |
| 108 | test_search_contracts.py | test_status_response_has_required_fields | `assert 404 == 200` | mock-drift | fix-inline | |
| 109 | test_search_contracts.py | test_status_with_excel_info | `assert 404 == 200` | mock-drift | fix-inline | |
| 110 | test_search_contracts.py | test_can_import_async_search_functions | `assert 240 == 120` | assertion-drift | fix-inline | |
| 111 | test_sectors_public.py | test_all_sector_slugs_count | `assert 20 == 19` | assertion-drift | fix-inline | |
| 112 | test_sectors_public.py | test_list_all_sectors | `assert 20 == 15` | assertion-drift | fix-inline | |
| 113 | test_sectors_public.py | test_refresh_all_sectors | `assert 20 == 15` | assertion-drift | fix-inline | |
| 114 | test_valor_filter.py | test_valor_invalid_string_treated_as_zero | `assert 2 == 1` | assertion-drift | fix-inline | |
| 115 | test_valor_filter.py | test_valor_none_in_bid | `assert 2 == 1` | assertion-drift | fix-inline | |
| 116 | test_valor_filter.py | test_valor_missing_field | `assert 2 == 1` | assertion-drift | fix-inline | |
| 117 | test_blog_stats.py | test_panorama_stats_sazonalidade_structure | KeyError: 'sazonalidade' | mock-drift | fix-inline | |
| 118 | test_blog_stats.py | test_panorama_stats_no_auth | `assert 404 == 200` | mock-drift | fix-inline | |
| 119 | test_concurrency_safety.py | test_ac12_get_pipeline_returns_version | `assert 500 == 200` | mock-drift | fix-inline | |
| 120 | test_concurrency_safety.py | test_ac26_fallback_creates_new_row | upsert not called | mock-drift | fix-inline | |
| 121 | test_crit_016_sentry_bugs.py | test_deduplicate_normal_adapters | no attr `_deduplicate` | mock-drift | fix-inline | |
| 122 | test_crit_016_sentry_bugs.py | test_deduplicate_with_two_valid_adapters | idem | mock-drift | fix-inline | |

### Seção II — Bucket C (Story drift + Trial + Alerts + LLM + Sessions + Misc) — 91 rows

| # | File | Test name | Error snippet | Category | Verdict | Justification |
|---|------|-----------|---------------|----------|---------|---------------|
| 123 | test_llm_zero_match.py | test_mix_keyword_and_zero_match | `assert 0 == 10` | assertion-drift | story-filha | |
| 124 | test_llm_zero_match.py | test_short_objeto_skipped | `assert 0 == 5` | assertion-drift | story-filha | |
| 125 | test_llm_zero_match.py | test_relevance_source_on_approved | `assert 0 == 3` | assertion-drift | story-filha | |
| 126 | test_sector_red_flags.py | test_software_reject_sistema_ar_condicionado | `assert False is True` | assertion-drift | story-filha | |
| 127 | test_sector_red_flags.py | test_multiple_red_flags_all_returned | `assert False is True` | assertion-drift | story-filha | |
| 128 | test_sector_red_flags.py | test_all_15_sectors_have_entries | expected `software`, got split | assertion-drift | story-filha | |
| 129 | test_sector_red_flags.py | test_sector_red_flag_rejects_in_medium_density | `assert False is True` | assertion-drift | story-filha | |
| 130 | test_sector_red_flags.py | test_sector_red_flag_rejects_in_low_density | `assert False is True` | assertion-drift | story-filha | |
| 131 | test_sector_red_flags.py | test_feature_flag_disabled_skips_check | `assert False is True` | assertion-drift | story-filha | |
| 132 | test_crit004_correlation.py | (3 cases) login/search/error | `assert 403 == 200` | mock-drift | story-filha | |
| 133 | test_crit004_correlation.py | test_correlation_id_in_log_search | `'search_id' in <config src>` | mock-drift | fix-inline | |
| 134 | test_crit004_correlation.py | test_correlation_id_in_log_error | idem | mock-drift | fix-inline | |
| 135 | test_debt102_jwt_pncp_compliance.py | (3 cases) | `ImportError: _decode_with_fallback from auth` | import | fix-inline | |
| 136 | test_debt102_jwt_pncp_compliance.py | tamanho_pagina 50/51 (2) | `ImportError: PNCP_MAX_PAGE_SIZE from pncp_client` | import | fix-inline | |
| 137 | test_debt102_jwt_pncp_compliance.py | test_page_size_50_works | `API returned non-retryable status 400` | infra-live | move-to-integration-external | PNCP produção agora rejeita size=50 com HTTP 400; mock eliminaria propósito de canary |
| 138 | test_debt102_jwt_pncp_compliance.py | async_client test | `TypeError: MagicMock not awaitable` | mock-drift | fix-inline | |
| 139 | test_precision_recall_datalake.py | test_datalake_precision_recall[software] | `KeyError: 'software'` | assertion-drift | story-filha | |
| 140 | test_precision_recall_datalake.py | test_datalake_precision_recall[facilities] | `KeyError: 'facilities'` | assertion-drift | story-filha | |
| 141 | test_precision_recall_datalake.py | test_datalake_precision_recall[saude] | `KeyError: 'saude'` | assertion-drift | story-filha | |
| 142 | test_precision_recall_datalake.py | test_datalake_precision_recall[transporte] | `KeyError: 'transporte'` | assertion-drift | story-filha | |
| 143 | test_precision_recall_datalake.py | test_datalake_precision_recall[vestuario] | `Recall 34% < 70%` | assertion-drift | story-filha | |
| 144 | test_story354_pending_review.py | test_llm_arbiter_reject_non_zero_match | pending_review wrongly set | assertion-drift | story-filha | |
| 145 | test_story354_pending_review.py | test_filter_pending_review_count | `KeyError: pending_review_count` | assertion-drift | story-filha | |
| 146 | test_story354_pending_review.py | test_filter_pending_review_bids_included | `assert 0 == 1` | assertion-drift | story-filha | |
| 147 | test_story354_pending_review.py | test_filter_pending_review_with_executor_exception | KeyError | assertion-drift | story-filha | |
| 148 | test_story354_pending_review.py | test_filter_pending_review_rejected_when_flag_off | KeyError | assertion-drift | story-filha | |
| 149 | test_consolidation_multisource.py | (4 cases) | `assert 1 == 2` / `1 >= 2` | assertion-drift | story-filha | |
| 150 | test_debt010_plan_reconciliation.py | TestTableSizeMetrics (4 cases) | `ImportError: _MONITORED_TABLES` | import | fix-inline | |
| 151 | test_observatorio.py | test_get_relatorio_structure | `assert 0 == 20` | mock-drift | story-filha | |
| 152 | test_observatorio.py | test_top_ufs_sorted_desc | `assert 0 > 0` | mock-drift | story-filha | |
| 153 | test_observatorio.py | test_modalidade_distribution | `assert 6 in []` | mock-drift | story-filha | |
| 154 | test_observatorio.py | test_pct_sum_approximately_100 | `assert 100.0 < 2.0` | mock-drift | story-filha | |
| 155 | test_trial_email_sequence.py | test_sends_welcome_email_day_0 | `assert 0 >= 1` | mock-drift | story-filha | |
| 156 | test_trial_email_sequence.py | test_skips_converted_users | `assert 0 >= 1` | mock-drift | story-filha | |
| 157 | test_trial_email_sequence.py | test_skips_unsubscribed_marketing_but_sends_conversion | `assert 0 >= 1` | mock-drift | story-filha | |
| 158 | test_trial_email_sequence.py | test_skips_fully_unsubscribed_users | `assert 0 >= 1` | mock-drift | story-filha | |
| 159 | test_ux400_link_fallback.py | TestPncpClientBuildLinkEdital (4) | `PNCPLegacyAdapter no attr _build_link_edital` | assertion-drift | fix-inline | |
| 160 | test_story271_sentry_fixes.py | test_* GUNICORN_TIMEOUT | start.sh now :-110 | assertion-drift | fix-inline | |
| 161 | test_story271_sentry_fixes.py | test_* workers 51 vs 50 | `assert 51 == 50` | assertion-drift | fix-inline | |
| 162 | test_story303_crash_recovery.py | test_cryptography_pinned_exact | pin mudou >=46.0.6,<47 | assertion-drift | story-filha | |
| 163 | test_story303_crash_recovery.py | test_cryptography_no_wildcard | idem | assertion-drift | story-filha | |
| 164 | test_story363_arq_search.py | test_search_job_completes_without_tracker | Expected _persist_search_results_to_redis | mock-drift | story-filha | |
| 165 | test_story363_arq_search.py | (persist_job_result test) | Expected called | mock-drift | story-filha | |
| 166 | test_story402_batch_zero_match.py | test_50_items_batch_processing | `assert 50 == 3` | assertion-drift | story-filha | |
| 167 | test_story402_batch_zero_match.py | test_counters_compatible_with_batch | `assert 0 == 3` | assertion-drift | story-filha | |
| 168 | test_story429_error_code_case_fix.py | test_search_py_uses_enum_for_timeout | `FileNotFoundError routes/search.py` | collection | fix-inline | |
| 169 | test_story429_error_code_case_fix.py | test_search_py_uses_enum_for_sources_unavailable | idem | collection | fix-inline | |
| 170 | test_alert_matcher.py | test_preview_success | `assert 404 == 200` | mock-drift | fix-inline | |
| 171 | test_audit.py | (1 test) | missing auth.signup; extra admin.feature_flag_change | assertion-drift | fix-inline | |
| 172 | test_co_occurrence.py | (1 test) | insumos_hospitalares negative_contexts empty | assertion-drift | story-filha | |
| 173 | test_crit050_pipeline_hardening.py | (cache manager test) | no attr `_supabase_save_cache` | mock-drift | fix-inline | |
| 174 | test_crit_019_setor_pipeline.py | test_zero_match_path_entered_with_setor | asyncio.run in running loop | flakiness | fix-inline | |
| 175 | test_crit_flt_002_arbiter_parallel.py | test_qa_audit_sampling_in_parallel | filter module no attr 'random' | mock-drift | fix-inline | |
| 176 | test_cron_monitoring.py | test_cron_monitoring_job_reports_problems | `assert 2 == 1` | assertion-drift | fix-inline | |
| 177 | test_error_handler.py | test_missing_signature_header_returns_pt | `assert 404 == 400` | mock-drift | fix-inline | |
| 178 | test_ingestion_loader.py | test_uses_default_retention_days | expected call missing | assertion-drift | fix-inline | |
| 179 | test_openapi_schema.py | test_openapi_schema_matches_snapshot | schema changed | assertion-drift | fix-inline | |
| 180 | test_organizations.py | test_check_and_increment_org_quota_delegates_to_atomic | not called | mock-drift | story-filha | |
| 181 | test_pncp_422_dates.py | test_abertas_mode_uses_utc | `assert 730 == 10` | assertion-drift | fix-inline | |
| 182 | test_pncp_client_requires_modalidade.py | test_fetch_page_accepts_valid_modalidade | `PNCPClient no attr client` | mock-drift | fix-inline | |
| 183 | test_redis_pool.py | test_no_asyncio_run_in_production | asyncio.run found in prod code | prod-bug | story-filha | Static scan detecta `asyncio.run()` em llm.py + outros; decisão de @architect antes de refactor |
| 184 | test_search_pipeline_filter_enrich.py | (1 test) | sector_substring_relaxation still firing | assertion-drift | story-filha | |
| 185 | test_sector_coverage_audit.py | (1 test) | 'construcao' trigger sem match | assertion-drift | story-filha | |
| 186 | test_story267_synonym_terms.py | (1 test) | Missing sectors: 'software' | assertion-drift | story-filha | |
| 187 | test_story252_resilience.py | (1 test) | no attr `_wrap_source` | mock-drift | story-filha | |
| 188 | test_story362_l3_persistence.py | (1 test) | 'RESULTS_REDIS_TTL' in wrong .env | collection | fix-inline | |
| 189 | test_story_221_async_fixes.py | (1 test) | asyncio.run in production | prod-bug | story-filha | Mesmo grupo do `test_redis_pool::test_no_asyncio_run_in_production` |
| 190 | test_feature_flags_admin.py | test_update_flag_redis_unavailable_falls_back_to_memory | `quota` no attr `asyncio` | mock-drift | fix-inline | |
| 191 | test_feature_flags_admin.py | test_update_flag_stores_in_memory | idem | mock-drift | fix-inline | |
| 192 | test_portal_compras_client.py | test_normalize_full_v2_record | `assert None == 0.0` | assertion-drift | fix-inline | |
| 193 | test_portal_compras_client.py | test_normalize_value_is_zero | `assert None == 0.0` | assertion-drift | fix-inline | |
| 194 | test_digest_job.py | (5 cases) | Prometheus Duplicated timeseries | collection | fix-inline | |
| 195 | test_digest_job.py | test_digest_job_in_functions | Prometheus Duplicated | collection | fix-inline | |
| 196 | test_dunning.py | test_require_active_plan_returns_402_for_blocked | `quota` no attr `asyncio` | mock-drift | fix-inline | |
| 197 | test_dunning.py | test_require_active_plan_returns_402_for_grace_period | idem | mock-drift | fix-inline | |
| 198 | test_search_session_lifecycle.py | test_t1_returns_none_if_profile_missing | `assert 'id' is None` | mock-drift | story-filha | |
| 199 | test_search_session_lifecycle.py | test_t6_returns_none_on_db_error | `assert 1 == 2` | mock-drift | story-filha | |
| 200 | test_search_pipeline_generate_persist.py | test_missing_optional_fields | `assert None == 0.0` | assertion-drift | fix-inline | |
| 201 | test_search_pipeline_generate_persist.py | test_llm_summary_generated | expected call missing | mock-drift | fix-inline | |
| 202 | test_crit059_async_zero_match.py | test_async_enabled_collects_candidates | `assert 10 == 0` | assertion-drift | story-filha | |
| 203 | test_crit059_async_zero_match.py | test_returns_results_when_available | `assert 404 == 200` | mock-drift | story-filha | |
| 204 | test_ux351_session_dedup.py | test_creates_new_session_when_no_existing | Expected insert called once | mock-drift | story-filha | |
| 205 | test_ux351_session_dedup.py | test_reuses_existing_session_for_same_search_id | Expected insert not called | mock-drift | story-filha | |
| 206 | test_ux351_session_dedup.py | test_no_dedup_check_without_search_id | Expected called once | mock-drift | story-filha | |
| 207 | test_story283_phantom_cleanup.py | test_no_import_references_licitar_client | Timeout 30s (walk tree) | flakiness | fix-inline | |
| 208 | test_story283_phantom_cleanup.py | test_free_plan_recognized_by_db_loader | `quota` no attr `logger` | mock-drift | fix-inline | |
| 209 | test_story283_phantom_cleanup.py | test_master_plan_recognized_by_db_loader | idem | mock-drift | fix-inline | |
| 210 | test_story283_phantom_cleanup.py | test_all_sectors_zero_orphan_triggers | Orphan triggers found | assertion-drift | story-filha | |
| 211 | test_story283_phantom_cleanup.py | test_sector_loading_no_orphan_warnings | Warning still fires | assertion-drift | story-filha | |
| 212 | test_sitemap_cnpjs.py | test_max_5000_cnpjs | TestClient timeout 15s | flakiness | fix-inline | |
| 213 | test_story_203_track2.py | (entire file) | collection hangs | collection | fix-inline | |

### Seção III — Bucket A (SSE + Cache + Story364 + Alerts + Timeout + BigFiles) — 258 rows expandidos test-level

| # | File | Test name | Error snippet | Category | Verdict | Justification |
|---|------|-----------|---------------|----------|---------|---------------|
| 214 | test_sse_last_event_id.py | test_events_have_id_field | routes/search_sse attr/404 | mock-drift | story-filha | |
| 215 | test_sse_last_event_id.py | test_replay_after_last_event_id | 404 route | mock-drift | story-filha | |
| 216 | test_sse_last_event_id.py | test_replay_via_query_param | 404 route | mock-drift | story-filha | |
| 217 | test_sse_last_event_id.py | test_replay_invalid_last_event_id | 404 route | mock-drift | story-filha | |
| 218 | test_sse_last_event_id.py | test_completed_search_immediate_terminal | 404 route | mock-drift | story-filha | |
| 219 | test_sse_last_event_id.py | test_completed_search_with_all_events_seen | 404 route | mock-drift | story-filha | |
| 220 | test_sse_last_event_id.py | test_degraded_terminal_detected | 404 route | mock-drift | story-filha | |
| 221 | test_sse_last_event_id.py | test_ring_buffer_max_1000 | mock attr missing | mock-drift | story-filha | |
| 222 | test_sse_last_event_id.py | test_ring_buffer_at_boundary | mock attr missing | mock-drift | story-filha | |
| 223 | test_sse_last_event_id.py | test_reconnect_during_active_search | 404 route | mock-drift | story-filha | |
| 224 | test_sse_last_event_id.py | test_no_duplicate_events_on_reconnect | 404 route | mock-drift | story-filha | |
| 225 | test_sse_last_event_id.py | test_reconnect_after_complete | 404 route | mock-drift | story-filha | |
| 226 | test_sse_last_event_id.py | test_reconnect_after_error_terminal | 404 route | mock-drift | story-filha | |
| 227 | test_sse_last_event_id.py | test_reconnect_after_search_complete_terminal | 404 route | mock-drift | story-filha | |
| 228 | test_sse_last_event_id.py | test_normal_streaming_has_ids | 404 route | mock-drift | story-filha | |
| 229 | test_sse_last_event_id.py | test_normal_streaming_no_replay_events | 404 route | mock-drift | story-filha | |
| 230 | test_sse_last_event_id.py | test_replay_max_events | constants changed | assertion-drift | story-filha | |
| 231 | test_sse_last_event_id.py | test_terminal_stages_include_all_expected | constants changed | assertion-drift | story-filha | |
| 232 | test_story364_excel_resilience.py | test_status_returns_excel_url_on_db_fallback | 404 route | mock-drift | story-filha | |
| 233 | test_story364_excel_resilience.py | test_regenerate_returns_202_arq_available | 404 route | mock-drift | story-filha | |
| 234 | test_story364_excel_resilience.py | test_regenerate_extracts_licitacoes_from_dict | 404 route | mock-drift | story-filha | |
| 235 | test_story364_excel_resilience.py | test_regenerate_response_includes_message | 404 route | mock-drift | story-filha | |
| 236 | test_story364_excel_resilience.py | test_regenerate_404_empty_licitacoes | response-shape drift | mock-drift | story-filha | |
| 237 | test_story364_excel_resilience.py | test_regenerate_inline_success | 404 route | mock-drift | story-filha | |
| 238 | test_story364_excel_resilience.py | test_regenerate_inline_persists_job_result | mock not called | mock-drift | story-filha | |
| 239 | test_story364_excel_resilience.py | test_regenerate_inline_failure_returns_500 | status drift | mock-drift | story-filha | |
| 240 | test_story364_excel_resilience.py | test_regenerate_inline_upload_failure_returns_500 | status drift | mock-drift | story-filha | |
| 241 | test_story364_excel_resilience.py | test_results_merges_excel_when_not_present | 404 | mock-drift | story-filha | |
| 242 | test_story364_excel_resilience.py | test_results_preserves_existing_download_url | 404 | mock-drift | story-filha | |
| 243 | test_story364_excel_resilience.py | test_results_no_excel_result_still_works | 404 | mock-drift | story-filha | |
| 244 | test_story364_excel_resilience.py | test_results_has_cache_control_when_completed | 404 | mock-drift | story-filha | |
| 245 | test_story364_excel_resilience.py | test_results_excel_merge_defaults_excel_status_to_ready | 404 | mock-drift | story-filha | |
| 246 | test_story364_excel_resilience.py | test_status_then_results_consistency | 404 | mock-drift | story-filha | |
| 247 | test_story364_excel_resilience.py | test_regenerate_after_expired_excel | 404 | mock-drift | story-filha | |
| 248 | test_story364_excel_resilience.py | test_full_lifecycle_status_to_regenerate | 404 | mock-drift | story-filha | |
| 249 | test_alerts.py | test_create_alert_success | 404 route | mock-drift | story-filha | |
| 250 | test_alerts.py | test_create_alert_valor_min_gt_max_returns_422 | 404 route | mock-drift | story-filha | |
| 251 | test_alerts.py | test_create_alert_invalid_uf_returns_422 | 404 route | mock-drift | story-filha | |
| 252 | test_alerts.py | test_create_alert_numeric_uf_returns_422 | 404 route | mock-drift | story-filha | |
| 253 | test_alerts.py | test_create_alert_per_user_limit_returns_409 | 404 route | mock-drift | story-filha | |
| 254 | test_alerts.py | test_list_alerts_empty | 404 route | mock-drift | story-filha | |
| 255 | test_alerts.py | test_list_alerts_returns_alerts_with_sent_counts | 404 route | mock-drift | story-filha | |
| 256 | test_alerts.py | test_update_alert_name | 404 route | mock-drift | story-filha | |
| 257 | test_alerts.py | test_update_alert_deactivate | 404 route | mock-drift | story-filha | |
| 258 | test_alerts.py | test_update_alert_empty_body_returns_422 | 404 route | mock-drift | story-filha | |
| 259 | test_alerts.py | test_update_alert_invalid_filters_returns_422 | 404 route | mock-drift | story-filha | |
| 260 | test_alerts.py | test_delete_alert_success | 404 route | mock-drift | story-filha | |
| 261 | test_alerts.py | test_alert_history_returns_paginated_items | 404 route | mock-drift | story-filha | |
| 262 | test_timeout_chain.py | test_degraded_timeout_greater_than_normal | STAB-003 defaults | assertion-drift | fix-inline | |
| 263 | test_timeout_chain.py | test_normal_mode_default_90s | PerUF=25s not 90s | assertion-drift | fix-inline | |
| 264 | test_timeout_chain.py | test_degraded_mode_default_120s | STAB-003 reduced | assertion-drift | fix-inline | |
| 265 | test_timeout_chain.py | test_env_default_per_source_180 | PerSource=80s | assertion-drift | fix-inline | |
| 266 | test_timeout_chain.py | test_env_default_global_300 | Pipeline=100s | assertion-drift | fix-inline | |
| 267 | test_timeout_chain.py | test_422_retry_logic_in_source | retry path refactor | assertion-drift | fix-inline | |
| 268 | test_timeout_chain.py | test_default_fetch_timeout_360 | fetch timeout drift | assertion-drift | fix-inline | |
| 269 | test_timeout_chain.py | test_env_var_configurable | env var name change | assertion-drift | fix-inline | |
| 270 | test_timeout_chain.py | test_frontend_proxy_8min | frontend timeout drift | assertion-drift | fix-inline | |
| 271 | test_timeout_chain.py | test_frontend_error_message_8min | error msg drift | assertion-drift | fix-inline | |
| 272 | test_timeout_chain.py | test_per_modality_margin_30s | margin drift | assertion-drift | fix-inline | |
| 273 | test_timeout_chain.py | test_startup_validation_rejects_inversion | invariant check | assertion-drift | fix-inline | |
| 274 | test_timeout_chain.py | test_startup_validation_warns_near_inversion | invariant warn | assertion-drift | fix-inline | |
| 275 | test_crit052_canary_false_positive.py | test_healthy_cron_uses_standard_timeout | `TypeError: bool not subscriptable` | mock-drift | story-filha | |
| 276 | test_crit052_canary_false_positive.py | test_degraded_cron_uses_extended_timeout | idem | mock-drift | story-filha | |
| 277 | test_crit052_canary_false_positive.py | test_pncp_responding_in_4s_with_10s_timeout_succeeds | idem | mock-drift | story-filha | |
| 278 | test_crit052_canary_false_positive.py | test_pncp_responding_in_12s_with_extended_timeout | idem | mock-drift | story-filha | |
| 279 | test_crit052_canary_false_positive.py | test_pncp_no_response_in_15s_discarded | idem | mock-drift | story-filha | |
| 280 | test_crit052_canary_false_positive.py | test_canary_failure_still_attempts_fetch | idem | mock-drift | story-filha | |
| 281 | test_crit052_canary_false_positive.py | test_cron_degraded_makes_canary_use_extended_timeout | idem | mock-drift | story-filha | |
| 282 | test_crit052_canary_false_positive.py | test_timeout_log_includes_cron_context | idem | mock-drift | story-filha | |
| 283 | test_crit052_canary_false_positive.py | test_canary_result_includes_telemetry | idem | mock-drift | story-filha | |
| 284 | test_crit052_canary_false_positive.py | test_search_complete_event_includes_canary_fields | `search_complete` missing `pncp_canary_status` | assertion-drift | fix-inline | |
| 285 | test_crit052_canary_false_positive.py | test_parallel_fetch_result_has_canary_field | `ParallelFetchResult` no attr `canary_result` | mock-drift | story-filha | |
| 286 | test_debt017_database_optimization.py | test_db004_mfa_rate_limiting_documented | `assert 'rate limiting' in audit doc` | assertion-drift | fix-inline | |
| 287 | test_debt017_database_optimization.py | test_db005_mfa_recovery_attempts_documented | audit doc text drift | assertion-drift | fix-inline | |
| 288 | test_debt017_database_optimization.py | test_db006_trial_email_log_documented | audit doc text drift | assertion-drift | fix-inline | |
| 289 | test_debt017_database_optimization.py | test_db008_stripe_price_ids_documented | audit doc text drift | assertion-drift | fix-inline | |
| 290 | test_debt017_database_optimization.py | test_db020_naming_convention_documented | audit doc text drift | assertion-drift | fix-inline | |
| 291 | test_debt017_database_optimization.py | test_db027_down_migrations_documented | audit doc text drift | assertion-drift | fix-inline | |
| 292 | test_debt017_database_optimization.py | test_db036_partitioning_strategy_documented | audit doc text drift | assertion-drift | fix-inline | |
| 293 | test_debt017_database_optimization.py | test_db044_pgcron_documented | audit doc text drift | assertion-drift | fix-inline | |
| 294 | test_debt017_database_optimization.py | test_db046_schema_change_policy_documented | audit doc text drift | assertion-drift | fix-inline | |
| 295 | test_debt017_database_optimization.py | test_db050_fk_evaluation_documented | audit doc text drift | assertion-drift | fix-inline | |
| 296 | test_debt017_database_optimization.py | test_db009_documented_in_audit | audit doc text drift | assertion-drift | fix-inline | |
| 297 | test_debt110_backend_resilience.py | test_normalize_text_is_same_object_in_both_modules | ModuleNotFoundError: filter_keywords | import | fix-inline | |
| 298 | test_debt110_backend_resilience.py | test_match_keywords_is_same_object_in_both_modules | ModuleNotFoundError: filter_keywords | import | fix-inline | |
| 299 | test_debt110_backend_resilience.py | test_filter_density_imports_normalize_from_keywords | ModuleNotFoundError: filter_density | import | fix-inline | |
| 300 | test_debt110_backend_resilience.py | test_filter_status_imports_normalize_from_keywords | ModuleNotFoundError: filter_status | import | fix-inline | |
| 301 | test_debt110_backend_resilience.py | test_filter_uf_imports_from_keywords | ModuleNotFoundError: filter_uf | import | fix-inline | |
| 302 | test_debt110_backend_resilience.py | test_log_token_usage_accumulates_stats | ImportError: _search_token_stats | import | fix-inline | |
| 303 | test_debt110_backend_resilience.py | test_log_token_usage_computes_brl_cost | ImportError: _search_token_stats | import | fix-inline | |
| 304 | test_debt110_backend_resilience.py | test_log_token_usage_different_call_types | ImportError: _search_token_stats | import | fix-inline | |
| 305 | test_debt110_backend_resilience.py | test_get_search_cost_stats_pops_entry | ImportError: _search_token_stats | import | fix-inline | |
| 306 | test_plan_capabilities.py | test_plan_prices_exist_for_paid_plans | set mismatch (plan names) | assertion-drift | fix-inline | |
| 307 | test_plan_capabilities.py | test_get_quota_reset_date_handles_december | `assert 0 == 1` | mock-drift | fix-inline | |
| 308 | test_plan_capabilities.py | test_fallback_increments_existing_quota | `assert True is False` | mock-drift | fix-inline | |
| 309 | test_plan_capabilities.py | test_free_trial_user_within_trial_period | `assert 0 == 23` | mock-drift | fix-inline | |
| 310 | test_plan_capabilities.py | test_trial_expired_blocks_user | `assert True is False` | mock-drift | fix-inline | |
| 311 | test_plan_capabilities.py | test_consultor_agil_within_quota | `assert 365 == 1825` | assertion-drift | fix-inline | |
| 312 | test_plan_capabilities.py | test_quota_exhausted_blocks_user | quota mock drift | mock-drift | fix-inline | |
| 313 | test_plan_capabilities.py | test_sala_guerra_highest_limits | quota mock drift | mock-drift | fix-inline | |
| 314 | test_plan_capabilities.py | test_all_paid_plans_have_prices | set mismatch | assertion-drift | fix-inline | |
| 315 | test_crit029_session_dedup.py | test_no_dedup_match_creates_new_session | `assert 5 == 3` | mock-drift | story-filha | |
| 316 | test_crit029_session_dedup.py | test_param_dedup_returns_existing_session | `'should-not-reach' == 'existing-param-session'` | mock-drift | story-filha | |
| 317 | test_crit029_session_dedup.py | test_param_dedup_failure_falls_through_to_insert | `None == 'fallback-insert-id'` | mock-drift | story-filha | |
| 318 | test_crit029_session_dedup.py | test_second_search_same_params_reuses_session | `'should-not-reach' == 'original-session'` | mock-drift | story-filha | |
| 319 | test_crit029_session_dedup.py | test_ufs_sorted_for_consistent_matching | `'should-not-reach' == 'sorted-match-session'` | mock-drift | story-filha | |
| 320 | test_crit029_session_dedup.py | test_no_search_id_still_does_param_dedup | `'should-not-reach' == 'param-match-no-sid'` | mock-drift | story-filha | |
| 321 | test_crit029_session_dedup.py | test_search_then_retry_produces_single_session | `'should-not-reach' == 'session-first-call'` | mock-drift | story-filha | |
| 322 | test_crit029_session_dedup.py | test_filter_called_with_pg_array_format | `Expected 2 .filter() calls, got 0` | mock-drift | story-filha | |
| 323 | test_debt103_llm_search_resilience.py | test_llm_timeout_prevents_thread_starvation | `assert 5000 == 100` | assertion-drift | fix-inline | |
| 324 | test_debt103_llm_search_resilience.py | test_lru_max_size_configurable_via_env | setup error LRU env | mock-drift | fix-inline | |
| 325 | test_debt103_llm_search_resilience.py | test_merge_enrichment_fills_empty_fields | `ConsolidationService no '_deduplicate'` | import | story-filha | |
| 326 | test_debt103_llm_search_resilience.py | test_no_merge_when_winner_has_data | `ConsolidationService no '_deduplicate'` | import | story-filha | |
| 327 | test_debt103_llm_search_resilience.py | test_harden014_timeout_pattern | assertion drift | assertion-drift | fix-inline | |
| 328 | test_debt103_llm_search_resilience.py | test_per_uf_timeout_defaults | `assert 25 == 30` | assertion-drift | fix-inline | |
| 329 | test_debt103_llm_search_resilience.py | test_openai_timeout_s_env_var | `assert False` | assertion-drift | fix-inline | |
| 330 | test_debt103_llm_search_resilience.py | test_env_example_has_all_vars | OPENAI_TIMEOUT_S missing | assertion-drift | fix-inline | |
| 331 | test_search_cache.py | test_cache_expired_not_served | `...is None (expected non-None)` | mock-drift | story-filha | |
| 332 | test_search_cache.py | test_cache_miss_returns_none | `...is None` | mock-drift | story-filha | |
| 333 | test_search_cache.py | test_cache_read_failure_returns_none | `...is None` | mock-drift | story-filha | |
| 334 | test_search_cache.py | test_valid_file_returns_data_with_age | `assert None is not None` | mock-drift | story-filha | |
| 335 | test_search_cache.py | test_l1_fail_l3_serve | `'memory' == 'local'` | assertion-drift | story-filha | |
| 336 | test_search_cache.py | test_l2_hit_skips_l1_l3 | `assert None is not None` | mock-drift | story-filha | |
| 337 | test_search_cache.py | test_full_cascade_l2_miss_l1_error_l3_hit | `assert None is not None` | mock-drift | story-filha | |
| 338 | test_stab009_async_search.py | test_quota_exception_falls_back_to_sync | `assert 202 == 200` | mock-drift | story-filha | |
| 339 | test_stab009_async_search.py | test_search_status_endpoint | `assert 404 == 200` | mock-drift | story-filha | |
| 340 | test_stab009_async_search.py | test_search_status_endpoint_completed | `assert 404 == 200` | mock-drift | story-filha | |
| 341 | test_stab009_async_search.py | test_search_results_ready | `assert 404 == 200` | mock-drift | story-filha | |
| 342 | test_stab009_async_search.py | test_search_results_ready_has_cache_control_header | `assert 404 == 200` | mock-drift | story-filha | |
| 343 | test_stab009_async_search.py | test_search_results_still_processing | `assert 404 == 202` | mock-drift | story-filha | |
| 344 | test_stab009_async_search.py | test_search_results_still_processing_has_message | `assert 404 == 202` | mock-drift | story-filha | |
| 345 | test_stab009_async_search.py | test_search_results_202_reflects_current_status | `assert 404 == 202` | mock-drift | story-filha | |
| 346 | test_story320_paywall.py | test_day_1_full_access | `assert 0 == 1` | mock-drift | story-filha | |
| 347 | test_story320_paywall.py | test_day_7_full_access | `assert 0 == 7` | mock-drift | story-filha | |
| 348 | test_story320_paywall.py | test_day_8_limited_access | `'full_access' == 'limited_access'` | mock-drift | story-filha | |
| 349 | test_story320_paywall.py | test_day_14_limited_access | `'full_access' == 'limited_access'` | mock-drift | story-filha | |
| 350 | test_story320_paywall.py | test_paid_user_not_trial | `'full_access' == 'not_trial'` | mock-drift | story-filha | |
| 351 | test_story320_paywall.py | test_trial_status_includes_phase | `'full_access' == 'limited_access'` | mock-drift | story-filha | |
| 352 | test_story320_paywall.py | test_trial_status_full_access_phase | `assert 0 == 2` | mock-drift | story-filha | |
| 353 | test_story320_paywall.py | test_trial_status_paid_user | `'full_access' == 'not_trial'` | mock-drift | story-filha | |
| 354 | test_trial_block.py | test_expired_trial_returns_403_trial_expired | DID NOT RAISE HTTPException | mock-drift | story-filha | |
| 355 | test_trial_block.py | test_expired_paid_plan_returns_403_plan_expired | DID NOT RAISE HTTPException | mock-drift | story-filha | |
| 356 | test_trial_block.py | test_structured_log_on_block | `quota` module no attr `logger` | mock-drift | fix-inline | |
| 357 | test_trial_block.py | test_post_buscar_blocked | KeyError: 'error' | mock-drift | story-filha | |
| 358 | test_trial_block.py | test_post_pipeline_blocked | `APIError: invalid uuid syntax` (real Supabase) | infra-live | move-to-integration-external | Requires real Supabase UUID + FK validation; mockar duplicaria schema de produção |
| 359 | test_trial_block.py | test_patch_pipeline_blocked | `assert 500 == 403` | mock-drift | story-filha | |
| 360 | test_trial_block.py | test_delete_pipeline_blocked | `assert 500 == 403` | mock-drift | story-filha | |
| 361 | test_trial_block.py | test_post_first_analysis_blocked | `assert 200 == 403` | mock-drift | story-filha | |
| 362 | test_sessions.py | test_save_session_creates_profile_when_missing | `_ensure_profile_exists` not called | mock-drift | story-filha | |
| 363 | test_sessions.py | test_save_session_fails_gracefully_when_profile_creation_fails | `_ensure_profile_exists` not called | mock-drift | story-filha | |
| 364 | test_sessions.py | test_save_session_returns_none_on_db_failure | `assert False` | mock-drift | story-filha | |
| 365 | test_sessions.py | test_save_session_empty_result_returns_none | `assert False` | mock-drift | story-filha | |
| 366 | test_sessions.py | test_save_session_succeeds_on_retry | `None == 'session-retry-success'` | mock-drift | story-filha | |
| 367 | test_sessions.py | test_save_session_fails_after_max_retries | `assert False` | mock-drift | story-filha | |
| 368 | test_sessions.py | test_save_session_retry_delay_is_300ms | sleep not awaited | mock-drift | story-filha | |
| 369 | test_cache_correctness.py | test_fallback_serves_with_flag | `assert None is not None` | mock-drift | story-filha | |
| 370 | test_cache_correctness.py | test_exact_hit_no_fallback_flag | `assert None is not None` | mock-drift | story-filha | |
| 371 | test_cache_correctness.py | test_cascade_dual_read_legacy_key | `assert None is not None` | mock-drift | story-filha | |
| 372 | test_cache_correctness.py | test_stale_cache_triggers_revalidation_tracking | `assert None is not None` | mock-drift | story-filha | |
| 373 | test_cache_correctness.py | test_fresh_cache_not_stale | `assert None is not None` | mock-drift | story-filha | |
| 374 | test_cache_multi_level.py | test_cleanup_deletes_old_files | `CacheLevel.REDIS == CacheLevel.LOCAL` | assertion-drift | story-filha | |
| 375 | test_cache_multi_level.py | test_stats_empty_dir | `CacheLevel.REDIS == CacheLevel.MISS` | assertion-drift | story-filha | |
| 376 | test_cache_multi_level.py | test_stats_with_files | cache_level Redis is None | mock-drift | story-filha | |
| 377 | test_cache_multi_level.py | test_health_returns_all_levels | `assert not True` | mock-drift | story-filha | |
| 378 | test_cache_multi_level.py | test_sentry_called_on_supabase_save_failure | `assert 2 == 0` | mock-drift | story-filha | |
| 379 | test_cache_warming_noninterference.py | test_warming_pauses_when_active_searches | `assert 0 == 1` | mock-drift | story-filha | |
| 380 | test_cache_warming_noninterference.py | test_warming_resumes_after_active_searches_complete | `assert 0 == 2` | mock-drift | story-filha | |
| 381 | test_cache_warming_noninterference.py | test_warming_stops_on_429_rate_limit | `assert 0 >= 1` | mock-drift | story-filha | |
| 382 | test_cache_warming_noninterference.py | test_warming_respects_budget_timeout | `assert 0 == 1` | mock-drift | story-filha | |
| 383 | test_cache_warming_noninterference.py | test_warming_uses_system_uuid | `assert 0 == 1` | mock-drift | story-filha | |
| 384 | test_harden018_cache_dir_maxsize.py | test_evicts_oldest_files_when_over_200mb | `assert 0 >= 3` | mock-drift | story-filha | |
| 385 | test_harden018_cache_dir_maxsize.py | test_evicts_until_below_target | `assert 0 == 2` | mock-drift | story-filha | |
| 386 | test_harden018_cache_dir_maxsize.py | test_preserves_newest_files | `'oldest.json' not in [...]` | mock-drift | story-filha | |
| 387 | test_harden018_cache_dir_maxsize.py | test_save_to_local_triggers_size_check | `_check_cache_dir_size` not called | mock-drift | story-filha | |
| 388 | test_harden018_cache_dir_maxsize.py | test_cleanup_triggers_size_check | `_check_cache_dir_size` not called | mock-drift | story-filha | |
| 389 | test_sse_heartbeat.py | test_heartbeat_during_slow_tracker | `routes.search_sse no get_redis_pool` | mock-drift | story-filha | |
| 390 | test_sse_heartbeat.py | test_no_heartbeat_immediate_tracker | idem | mock-drift | story-filha | |
| 391 | test_sse_heartbeat.py | test_in_memory_heartbeat_on_timeout | idem | mock-drift | story-filha | |
| 392 | test_sse_heartbeat.py | test_redis_streams_heartbeat_on_timeout | idem | mock-drift | story-filha | |
| 393 | test_sse_heartbeat.py | test_wait_heartbeat_logged | idem | mock-drift | story-filha | |
| 394 | test_sse_heartbeat.py | test_main_loop_heartbeat_logged | idem | mock-drift | story-filha | |
| 395 | test_progress_streams.py | test_late_subscriber_receives_full_history | `routes.search_sse no get_redis_pool` | mock-drift | story-filha | |
| 396 | test_progress_streams.py | test_subscriber_receives_events_incrementally | idem | mock-drift | story-filha | |
| 397 | test_progress_streams.py | test_xread_detail_json_parsed_correctly | idem | mock-drift | story-filha | |
| 398 | test_progress_streams.py | test_fallback_to_queue_when_redis_down_at_sse | idem | mock-drift | story-filha | |
| 399 | test_progress_streams.py | test_multiple_events_with_heartbeats | idem | mock-drift | story-filha | |
| 400 | test_search_async.py | test_202_returned_before_pipeline_runs | `assert 404 == 202` | mock-drift | story-filha | |
| 401 | test_search_async.py | test_async_timeout_constant | `assert 240 == 120` | assertion-drift | fix-inline | |
| 402 | test_search_async.py | test_run_async_search_pipeline_and_emit | `persist_job_result not called` | mock-drift | story-filha | |
| 403 | test_search_async.py | test_search_status_endpoint_async | `assert 404 == 202` | mock-drift | story-filha | |
| 404 | test_search_async.py | test_search_results_ready_async | `assert 404 == 202` | mock-drift | story-filha | |
| 405 | test_cache_refresh.py | test_cache_refresh_job_dispatches_revalidation | `'supabase_unavailable' == 'completed'` | mock-drift | story-filha | |
| 406 | test_cache_refresh.py | test_cache_refresh_job_stops_on_cb_degraded | `KeyError: 'skipped_cb_open'` | mock-drift | story-filha | |
| 407 | test_cache_refresh.py | test_cache_refresh_job_stagger | `assert 0 == 2` | mock-drift | story-filha | |
| 408 | test_cache_refresh.py | test_cache_refresh_job_metrics | `KeyError: 'refreshed'` | mock-drift | story-filha | |
| 409 | test_cache_global_warmup.py | test_trial_user_receives_global_cache | `search_cache no METRICS_CACHE_HITS` | mock-drift | story-filha | |
| 410 | test_cache_global_warmup.py | test_global_cache_does_not_overwrite_personal | idem | mock-drift | story-filha | |
| 411 | test_cache_global_warmup.py | test_get_from_cache_cascade_uses_global_fallback | idem | mock-drift | story-filha | |
| 412 | test_admin_cache.py | test_with_confirm_header_succeeds | `assert 0.0 == 0.73` | mock-drift | story-filha | |
| 413 | test_admin_cache.py | test_inspect_existing_entry | `assert 0 == 10` | mock-drift | story-filha | |
| 414 | test_admin_cache.py | test_inspect_nonexistent_returns_404 | `assert 404 == 200` | mock-drift | story-filha | |
| 415 | test_crit055_warmup_adaptive.py | test_periodic_warmup_loop | mock not called | mock-drift | fix-inline | |
| 416 | test_progressive_results_295.py | test_fast_source_emits_partial_before_slow_completes | `assert 1 == 8` | mock-drift | story-filha | |
| 417 | test_progressive_results_295.py | test_one_source_fails_others_deliver | `assert 1 == 3` | mock-drift | story-filha | |
| 418 | test_progressive_results_295.py | test_tracker_emit_source_error | `'PORTAL_COMPRAS...' == 'Connection refused'` | assertion-drift | fix-inline | |
| 419 | test_progressive_delivery.py | test_ttl_expiry | BuscaResponse is None | mock-drift | fix-inline | |
| 420 | test_sse_reconnect_rate_limit.py | test_t3_user_isolation | `routes.search no acquire_sse_connection` | mock-drift | story-filha | |
| 421 | test_sse_reconnect_rate_limit.py | test_t4_response_body_structure | idem | mock-drift | story-filha | |
| 422 | test_sse_reconnect_rate_limit.py | test_t5_warning_log_on_exceeded | idem | mock-drift | story-filha | |
| 423 | test_crit071_partial_data_sse.py | test_emit_partial_data_increments_event_counter | `assert 0 == 2` | mock-drift | fix-inline | |
| 424 | test_revalidation_quota_cache.py | test_do_revalidation_never_calls_quota | `save_to_cache not called` | mock-drift | fix-inline | |
| 425 | test_cache_multilevel_integration.py | test_l1_miss_l2_hit_returns_result | `assert None is not None` | mock-drift | fix-inline | |
| 426 | test_api_buscar.py | test_buscar_unauthenticated_returns_403 | `assert 404 == 403` | mock-drift | story-filha | |
| 427 | test_api_buscar.py | test_buscar_returns_200 | `assert 404 == 200` | mock-drift | story-filha | |
| 428 | test_api_buscar.py | test_buscar_with_keywords | `assert 404 == 200` | mock-drift | story-filha | |
| 429 | test_api_buscar.py | test_buscar_with_ufs | `assert 404 == 200` | mock-drift | story-filha | |
| 430 | test_api_buscar.py | test_buscar_with_values | `assert 404 == 200` | mock-drift | story-filha | |
| 431 | test_api_buscar.py | test_buscar_with_setor | `assert 404 == 200` | mock-drift | story-filha | |
| 432 | test_api_buscar.py | test_buscar_with_modalidades | `assert 404 == 200` | mock-drift | story-filha | |
| 433 | test_api_buscar.py | test_buscar_503_on_source_down | `assert 404 == 503` | mock-drift | story-filha | |
| 434 | test_api_buscar.py | test_buscar_429_quota_exceeded | `assert 404 == 429` | mock-drift | story-filha | |
| 435 | test_api_buscar.py | test_buscar_cache_hit | `assert 404 == 200` | mock-drift | story-filha | |
| 436 | test_api_buscar.py | test_buscar_429_rate_limit | `assert 404 == 429` | mock-drift | story-filha | |
| 437 | test_api_buscar.py | test_buscar_zero_results | `assert 404 == 200` | mock-drift | story-filha | |
| 438 | test_api_buscar.py | test_buscar_partial_failure | `assert 404 == 200` | mock-drift | story-filha | |
| 439 | test_api_buscar.py | test_buscar_ssec_redirect | `assert 404 == 200` | mock-drift | story-filha | |
| 440 | test_api_buscar.py | test_buscar_429_burst | `assert 404 == 429` | mock-drift | story-filha | |
| 441 | test_api_buscar.py | test_buscar_403_trial_expired | `assert 404 == 403` | mock-drift | story-filha | |
| 442 | test_api_buscar.py | test_buscar_503_circuit_open | `assert 404 == 503` | mock-drift | story-filha | |
| 443 | test_api_buscar.py | test_buscar_full_flow | `assert 404 == 200` | mock-drift | story-filha | |
| 444 | test_api_buscar.py | test_buscar_retry_path | `assert 404 == 200` | mock-drift | story-filha | |
| 445 | test_api_buscar.py | test_buscar_params_pass_through | `assert 404 == 200` | mock-drift | story-filha | |
| 446 | test_api_buscar.py | test_buscar_400_bad_request | `assert 404 == 400` | mock-drift | story-filha | |
| 447 | test_api_buscar.py | test_buscar_cache_warm_path | `assert 404 == 200` | mock-drift | story-filha | |
| 448 | test_api_buscar.py | test_buscar_dedup_path | `assert 404 == 200` | mock-drift | story-filha | |
| 449 | test_benchmark_filter.py | test_benchmark_empty_objeto | `assert True is False` | assertion-drift | fix-inline | |
| 450 | test_consolidation_early_return.py | test_no_early_return_when_within_time | `consolidation no source_health_registry` | mock-drift | story-filha | |
| 451 | test_consolidation_early_return.py | test_early_return_triggers_on_timeout_threshold | idem | mock-drift | story-filha | |
| 452 | test_consolidation_early_return.py | test_no_early_return_when_below_threshold | idem | mock-drift | story-filha | |
| 453 | test_consolidation_early_return.py | test_no_early_return_when_all_ufs_complete | idem | mock-drift | story-filha | |
| 454 | test_consolidation_early_return.py | test_all_ufs_timeout_returns_error | idem | mock-drift | story-filha | |
| 455 | test_consolidation_early_return.py | test_ufs_completed_and_pending_lists | idem | mock-drift | story-filha | |
| 456 | test_consolidation_early_return.py | test_filter_ranking_on_collected_results_only | idem | mock-drift | story-filha | |
| 457 | test_consolidation_early_return.py | test_consolidation_result_has_uf_fields | idem | mock-drift | story-filha | |
| 458 | test_consolidation_early_return.py | test_early_return_skipped_when_no_ufs | idem | mock-drift | story-filha | |
| 459 | test_fuzzy_dedup.py | test_tokenize_objeto_empty | `ConsolidationService no _tokenize_objeto` | import | story-filha | |
| 460 | test_fuzzy_dedup.py | test_tokenize_objeto_basic | idem | import | story-filha | |
| 461 | test_fuzzy_dedup.py | test_tokenize_objeto_punctuation | idem | import | story-filha | |
| 462 | test_fuzzy_dedup.py | test_jaccard_identical | `no _jaccard` | import | story-filha | |
| 463 | test_fuzzy_dedup.py | test_jaccard_disjoint | idem | import | story-filha | |
| 464 | test_fuzzy_dedup.py | test_jaccard_partial_overlap | idem | import | story-filha | |
| 465 | test_fuzzy_dedup.py | test_jaccard_empty_sets | idem | import | story-filha | |
| 466 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_identical | `no _deduplicate_fuzzy` | import | story-filha | |
| 467 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_distinct | idem | import | story-filha | |
| 468 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_threshold_match | idem | import | story-filha | |
| 469 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_threshold_miss | idem | import | story-filha | |
| 470 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_priority_winner | idem | import | story-filha | |
| 471 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_feature_flag | idem | import | story-filha | |
| 472 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_preserves_distinct | idem | import | story-filha | |
| 473 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_keeps_highest_priority | idem | import | story-filha | |
| 474 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_multi_cluster | idem | import | story-filha | |
| 475 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_short_text_safeguard | idem | import | story-filha | |
| 476 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_long_text | idem | import | story-filha | |
| 477 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_mixed_sources | idem | import | story-filha | |
| 478 | test_fuzzy_dedup.py | test_deduplicate_fuzzy_empty_input | idem | import | story-filha | |
| 479 | test_gtm_critical_scenarios.py | test_quota_exhausted_returns_403 | `assert 404 == 403` | mock-drift | story-filha | |
| 480 | test_gtm_critical_scenarios.py | test_free_trial_expired_returns_403 | `assert 404 == 403` | mock-drift | story-filha | |
| 481 | test_harden001_openai_timeout.py | test_default_timeout_5s | `llm_arbiter no _client` | mock-drift | story-filha | |
| 482 | test_harden001_openai_timeout.py | test_max_retries_1 | idem | mock-drift | story-filha | |
| 483 | test_harden001_openai_timeout.py | test_timeout_configurable_via_env | idem | mock-drift | story-filha | |
| 484 | test_harden001_openai_timeout.py | test_client_lazy_singleton | idem | mock-drift | story-filha | |
| 485 | test_llm_cost_monitoring.py | test_log_token_usage_increments_usd_counter | `llm_arbiter no _hourly_cost_usd` | mock-drift | story-filha | |
| 486 | test_llm_cost_monitoring.py | test_log_token_usage_increments_token_counters | idem | mock-drift | story-filha | |
| 487 | test_llm_cost_monitoring.py | test_alert_fires_when_threshold_exceeded | idem | mock-drift | story-filha | |
| 488 | test_llm_cost_monitoring.py | test_alert_does_not_fire_below_threshold | idem | mock-drift | story-filha | |
| 489 | test_llm_cost_monitoring.py | test_alert_fires_only_once_until_reset | idem | mock-drift | story-filha | |
| 490 | test_precision_recall_benchmark.py | test_cross_sector_collision_rate | Timeout 30s (regex hot loop) | flakiness | story-filha | |

---

## Notas finais

- **Sem edits de teste:** `git diff backend/tests/` continua vazio após triage.
- **Sem novos skips:** re-check de `grep -rcE "@pytest\.mark\.skip\|pytest\.skip\(" backend/tests/` deve retornar **51** (baseline). Validado em "Passo 6/7" do plano (ver story ChangeLog).
- **AC4 out-of-scope** por design da meta-story: stories filhas listadas aqui são **recomendação** para @sm criar no próximo ciclo; não foram criadas nesta sessão.
- **AC6 já satisfeito** via STORY-CIG-BE-HTTPS-TIMEOUT (workflow `integration-external.yml` existe e está funcional; expansão futura registrada como action item).
