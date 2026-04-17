# Backend Failure Triage — Raw Enumeration

**Gerado automaticamente em 2026-04-16** a partir de `python scripts/run_tests_safe.py --parallel 4` (exit 1).

**Insumo da STORY-CIG-BACKEND-SWEEP.** Esta é a enumeração bruta; a triage taxonômica (infra-dependent / drift / flakiness / bug real) + as stories filhas são trabalho do @dev em Implement.

---

## Sumário agregado

- **435** arquivos de teste executados
- **133** arquivos com pelo menos 1 falha
- **424** falhas individuais contadas nos arquivos cujo sumário reporta N failures (arquivos com "(0 failures)" no sumário tiveram falha de collection/suite — contam como 1 conceitualmente)
- Baseline histórica de memory/MEMORY.md (2026-03-22): 292 pre-existing — drift de **+132** testes adicionais desde então (baseline defasada).

**Regra para stories filhas (SWEEP AC2):** cada teste individual (não arquivo) recebe verdict. Use este doc como índice e expanda cada arquivo via `pytest backend/tests/<arquivo> -v` para obter nome de teste granular no momento da triagem.

---

## Enumeração por arquivo (ordenada por N failures decrescente)

| # | Arquivo | N failures | Tempo (s) | Verdict inicial (a confirmar) |
|---|---------|------------|-----------|-------------------------------|
| 1 | `test_sse_last_event_id.py` | 18 | 9.4 | _(triage em Implement)_ |
| 2 | `test_story364_excel_resilience.py` | 17 | 17.5 | _(triage em Implement)_ |
| 3 | `test_alerts.py` | 13 | 10.9 | _(triage em Implement)_ |
| 4 | `test_timeout_chain.py` | 13 | 6.0 | _(triage em Implement)_ |
| 5 | `test_crit052_canary_false_positive.py` | 11 | 15.9 | _(triage em Implement)_ |
| 6 | `test_debt017_database_optimization.py` | 11 | 2.6 | _(triage em Implement)_ |
| 7 | `test_debt110_backend_resilience.py` | 9 | 3.1 | _(triage em Implement)_ |
| 8 | `test_plan_capabilities.py` | 9 | 3.0 | _(triage em Implement)_ |
| 9 | `test_crit029_session_dedup.py` | 8 | 3.0 | _(triage em Implement)_ |
| 10 | `test_debt103_llm_search_resilience.py` | 8 | 13.7 | _(triage em Implement)_ |
| 11 | `test_search_cache.py` | 8 | 6.7 | _(triage em Implement)_ |
| 12 | `test_stab009_async_search.py` | 8 | 61.0 | _(triage em Implement)_ |
| 13 | `test_story320_paywall.py` | 8 | 24.6 | _(triage em Implement)_ |
| 14 | `test_trial_block.py` | 8 | 30.0 | _(triage em Implement)_ |
| 15 | `test_sessions.py` | 7 | 2.7 | _(triage em Implement)_ |
| 16 | `test_crit004_correlation.py` | 6 | 23.3 | _(triage em Implement)_ |
| 17 | `test_digest_job.py` | 6 | 3.4 | _(triage em Implement)_ |
| 18 | `test_filtrar_prazo_aberto.py` | 6 | 2.5 | _(triage em Implement)_ |
| 19 | `test_gtm_infra_001.py` | 6 | 4.6 | _(triage em Implement)_ |
| 20 | `test_llm_zero_match.py` | 6 | 3.6 | _(triage em Implement)_ |
| 21 | `test_log_volume.py` | 6 | 4.2 | _(triage em Implement)_ |
| 22 | `test_sector_red_flags.py` | 6 | 2.5 | _(triage em Implement)_ |
| 23 | `test_sse_heartbeat.py` | 6 | 9.8 | _(triage em Implement)_ |
| 24 | `test_cache_correctness.py` | 5 | 5.1 | _(triage em Implement)_ |
| 25 | `test_cache_multi_level.py` | 5 | 5.9 | _(triage em Implement)_ |
| 26 | `test_cache_warming_noninterference.py` | 5 | 3.4 | _(triage em Implement)_ |
| 27 | `test_debt102_jwt_pncp_compliance.py` | 5 | 3.2 | _(triage em Implement)_ |
| 28 | `test_harden018_cache_dir_maxsize.py` | 5 | 3.5 | _(triage em Implement)_ |
| 29 | `test_pipeline_resilience.py` | 5 | 5.2 | _(triage em Implement)_ |
| 30 | `test_precision_recall_datalake.py` | 5 | 5.7 | _(triage em Implement)_ |
| 31 | `test_progress_streams.py` | 5 | 8.9 | _(triage em Implement)_ |
| 32 | `test_search_async.py` | 5 | 9.2 | _(triage em Implement)_ |
| 33 | `test_story354_pending_review.py` | 5 | 3.9 | _(triage em Implement)_ |
| 34 | `test_cache_refresh.py` | 4 | 5.2 | _(triage em Implement)_ |
| 35 | `test_consolidation_multisource.py` | 4 | 4.0 | _(triage em Implement)_ |
| 36 | `test_crit057_filter_time_budget.py` | 4 | 3.9 | _(triage em Implement)_ |
| 37 | `test_debt010_plan_reconciliation.py` | 4 | 2.7 | _(triage em Implement)_ |
| 38 | `test_feature_flag_matrix.py` | 4 | 8.9 | _(triage em Implement)_ |
| 39 | `test_endpoints_story165.py` | 4 | 91.2 | _(triage em Implement)_ |
| 40 | `test_job_queue.py` | 4 | 30.4 | _(triage em Implement)_ |
| 41 | `test_multisource_orchestration.py` | 4 | 3.0 | _(triage em Implement)_ |
| 42 | `test_observatorio.py` | 4 | 8.6 | _(triage em Implement)_ |
| 43 | `test_pncp_date_formats.py` | 4 | 2.8 | _(triage em Implement)_ |
| 44 | `test_security_story300.py` | 4 | 21.7 | _(triage em Implement)_ |
| 45 | `test_stab005_auto_relaxation.py` | 4 | 4.8 | _(triage em Implement)_ |
| 46 | `test_trial_email_sequence.py` | 4 | 4.8 | _(triage em Implement)_ |
| 47 | `test_ux400_link_fallback.py` | 4 | 4.9 | _(triage em Implement)_ |
| 48 | `test_admin_cache.py` | 3 | 12.2 | _(triage em Implement)_ |
| 49 | `test_bulkhead.py` | 3 | 5.1 | _(triage em Implement)_ |
| 50 | `test_cache_global_warmup.py` | 3 | 6.5 | _(triage em Implement)_ |
| 51 | `test_crit046_pool_exhaustion.py` | 3 | 5.9 | _(triage em Implement)_ |
| 52 | `test_crit054_pcp_status_mapping.py` | 3 | 2.6 | _(triage em Implement)_ |
| 53 | `test_gtm_fix_041_042.py` | 3 | 3.3 | _(triage em Implement)_ |
| 54 | `test_harden010_comprasgov_disable.py` | 3 | 2.4 | _(triage em Implement)_ |
| 55 | `test_pipeline.py` | 3 | 5.3 | _(triage em Implement)_ |
| 56 | `test_prometheus_labels.py` | 3 | 6.3 | _(triage em Implement)_ |
| 57 | `test_progressive_results_295.py` | 3 | 10.9 | _(triage em Implement)_ |
| 58 | `test_search_contracts.py` | 3 | 7.4 | _(triage em Implement)_ |
| 59 | `test_sectors_public.py` | 3 | 2.8 | _(triage em Implement)_ |
| 60 | `test_story_282_pncp_timeout_resilience.py` | 3 | 3.1 | _(triage em Implement)_ |
| 61 | `test_ux351_session_dedup.py` | 3 | 2.8 | _(triage em Implement)_ |
| 62 | `test_valor_filter.py` | 3 | 3.0 | _(triage em Implement)_ |
| 63 | `test_blog_stats.py` | 2 | 10.0 | _(triage em Implement)_ |
| 64 | `test_concurrency_safety.py` | 2 | 6.6 | _(triage em Implement)_ |
| 65 | `test_crit_016_sentry_bugs.py` | 2 | 2.8 | _(triage em Implement)_ |
| 66 | `test_crit059_async_zero_match.py` | 2 | 9.8 | _(triage em Implement)_ |
| 67 | `test_dunning.py` | 2 | 4.1 | _(triage em Implement)_ |
| 68 | `test_feature_flags_admin.py` | 2 | 6.1 | _(triage em Implement)_ |
| 69 | `test_pcp_timeout_isolation.py` | 2 | 6.8 | _(triage em Implement)_ |
| 70 | `test_portal_compras_client.py` | 2 | 2.5 | _(triage em Implement)_ |
| 71 | `test_search_session_lifecycle.py` | 2 | 8.1 | _(triage em Implement)_ |
| 72 | `test_search_pipeline_generate_persist.py` | 2 | 23.0 | _(triage em Implement)_ |
| 73 | `test_sitemap_orgaos.py` | 2 | 9.9 | _(triage em Implement)_ |
| 74 | `test_story271_sentry_fixes.py` | 2 | 2.7 | _(triage em Implement)_ |
| 75 | `test_story303_crash_recovery.py` | 2 | 2.6 | _(triage em Implement)_ |
| 76 | `test_story363_arq_search.py` | 2 | 9.7 | _(triage em Implement)_ |
| 77 | `test_story402_batch_zero_match.py` | 2 | 3.6 | _(triage em Implement)_ |
| 78 | `test_story429_error_code_case_fix.py` | 2 | 2.5 | _(triage em Implement)_ |
| 79 | `test_story_257a.py` | 2 | 30.0 | _(triage em Implement)_ |
| 80 | `test_alert_matcher.py` | 1 | 10.6 | _(triage em Implement)_ |
| 81 | `test_audit.py` | 1 | 2.8 | _(triage em Implement)_ |
| 82 | `test_cache_multilevel_integration.py` | 1 | 5.0 | _(triage em Implement)_ |
| 83 | `test_co_occurrence.py` | 1 | 3.3 | _(triage em Implement)_ |
| 84 | `test_comprasgov_circuit_breaker.py` | 1 | 3.2 | _(triage em Implement)_ |
| 85 | `test_crit050_pipeline_hardening.py` | 1 | 5.5 | _(triage em Implement)_ |
| 86 | `test_crit055_warmup_adaptive.py` | 1 | 5.3 | _(triage em Implement)_ |
| 87 | `test_crit071_partial_data_sse.py` | 1 | 2.7 | _(triage em Implement)_ |
| 88 | `test_crit_019_setor_pipeline.py` | 1 | 5.2 | _(triage em Implement)_ |
| 89 | `test_crit_flt_002_arbiter_parallel.py` | 1 | 4.2 | _(triage em Implement)_ |
| 90 | `test_cron_monitoring.py` | 1 | 2.5 | _(triage em Implement)_ |
| 91 | `test_debt009_database_rls_retention.py` | 1 | 3.0 | _(triage em Implement)_ |
| 92 | `test_debt008_backend_stability.py` | 1 | 4.7 | _(triage em Implement)_ |
| 93 | `test_debt101_security_critical.py` | 1 | 3.2 | _(triage em Implement)_ |
| 94 | `test_error_handler.py` | 1 | 9.0 | _(triage em Implement)_ |
| 95 | `test_gtm_fix_027_track2.py` | 1 | 5.7 | _(triage em Implement)_ |
| 96 | `test_gtm_infra_002.py` | 1 | 2.5 | _(triage em Implement)_ |
| 97 | `test_ingestion_loader.py` | 1 | 4.2 | _(triage em Implement)_ |
| 98 | `test_jsonb_storage_governance.py` | 1 | 3.1 | _(triage em Implement)_ |
| 99 | `test_openapi_schema.py` | 1 | 13.7 | _(triage em Implement)_ |
| 100 | `test_organizations.py` | 1 | 11.0 | _(triage em Implement)_ |
| 101 | `test_pncp_422_dates.py` | 1 | 6.9 | _(triage em Implement)_ |
| 102 | `test_pncp_client_requires_modalidade.py` | 1 | 8.0 | _(triage em Implement)_ |
| 103 | `test_pncp_hardening.py` | 1 | 17.5 | _(triage em Implement)_ |
| 104 | `test_progressive_delivery.py` | 1 | 5.1 | _(triage em Implement)_ |
| 105 | `test_quota.py` | 1 | 2.6 | _(triage em Implement)_ |
| 106 | `test_redis_pool.py` | 1 | 3.7 | _(triage em Implement)_ |
| 107 | `test_revalidation_quota_cache.py` | 1 | 23.6 | _(triage em Implement)_ |
| 108 | `test_search_pipeline_filter_enrich.py` | 1 | 4.8 | _(triage em Implement)_ |
| 109 | `test_sector_coverage_audit.py` | 1 | 6.6 | _(triage em Implement)_ |
| 110 | `test_story267_synonym_terms.py` | 1 | 3.2 | _(triage em Implement)_ |
| 111 | `test_story252_resilience.py` | 1 | 17.9 | _(triage em Implement)_ |
| 112 | `test_story362_l3_persistence.py` | 1 | 6.8 | _(triage em Implement)_ |
| 113 | `test_story_221_async_fixes.py` | 1 | 9.6 | _(triage em Implement)_ |
| 114 | `test_supabase_circuit_breaker.py` | 1 | 14.3 | _(triage em Implement)_ |
| 115 | `test_api_buscar.py` | 0 | 11.9 | _(triage em Implement)_ |
| 116 | `test_benchmark_filter.py` | 0 | 2.7 | _(triage em Implement)_ |
| 117 | `test_benchmark_pncp_client.py` | 0 | 2.8 | _(triage em Implement)_ |
| 118 | `test_consolidation_early_return.py` | 0 | 3.0 | _(triage em Implement)_ |
| 119 | `test_fuzzy_dedup.py` | 0 | 2.7 | _(triage em Implement)_ |
| 120 | `test_gtm_critical_scenarios.py` | 0 | 8.8 | _(triage em Implement)_ |
| 121 | `test_harden001_openai_timeout.py` | 0 | 2.9 | _(triage em Implement)_ |
| 122 | `test_llm_cost_monitoring.py` | 0 | 2.9 | _(triage em Implement)_ |
| 123 | `test_integration_new_sectors.py` | 0 | 59.4 | _(triage em Implement)_ |
| 124 | `test_organizations_pgrst205_guard.py` | 0 | 9.8 | _(triage em Implement)_ |
| 125 | `test_pncp_homologados_discovery.py` | 0 | 31.5 | _(triage em Implement)_ |
| 126 | `test_precision_recall_benchmark.py` | 0 | 35.6 | _(triage em Implement)_ |
| 127 | `test_receita_federal_discovery.py` | 0 | 31.6 | _(triage em Implement)_ |
| 128 | `test_sse_reconnect_rate_limit.py` | 0 | 9.2 | _(triage em Implement)_ |
| 129 | `test_sitemap_cnpjs.py` | 0 | 42.1 | _(triage em Implement)_ |
| 130 | `test_story283_phantom_cleanup.py` | 0 | 32.2 | _(triage em Implement)_ |
| 131 | `test_story_203_track2.py` | 0 | 1.6 | _(triage em Implement)_ |
| 132 | `test_full_pipeline_cascade.py` | ? | 10.3 | _(triage em Implement)_ |
| 133 | `test_queue_worker_fail_inline.py` | ? | 10.8 | _(triage em Implement)_ |

---

## Heurísticas para verdict inicial (guia para @dev)

- **test_sse_***, **test_stab009_async_search**, **test_trial_block**: alto tempo + alta contagem de failures → likely timeout/flaky → **flakiness** ou **infra-dependent**.
- **test_supabase_***, **test_datalake_***: provável **infra-dependent** (requer Supabase live / pg_cron / RLS).
- **test_story_***, **test_storyNNN_***: provável **drift** após refactor do código de produção que a story testou.
- **test_api_buscar**, **test_timeout_chain**, **test_full_pipeline_cascade**: críticos → investigar primeiro, podem revelar **bugs reais** em hot path.
- **test_sse_reconnect_rate_limit.py (0 failures)**: "0 failures" no sumário = coleção/import error → **drift de módulo** (fix barato).

## Contrato de saída do triage

Ao fim da triage, @dev produz:
1. `backend-failure-triage.md` com cada teste individual classificado em `fix-inline` / `story-filha` / `move-to-integration-external` / `reopened-bug`.
2. N stories filhas `STORY-CIG-BE-NN-<slug>.story.md` criadas no próximo ciclo de @sm.
3. `integration-external.yml` (novo workflow) se algum teste receber `move-to-integration-external`.
4. Confirmação via `pytest --collect-only | wc -l` que o total de testes do workflow principal diminuiu **apenas** pelo conjunto movido — nada de skip oculto.
