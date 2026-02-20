# Integration Tests -- CRIT-007

End-to-end failure testing for the SearchPipeline and supporting infrastructure.

## Running

```bash
# All integration tests
pytest backend/tests/integration/ -v

# Specific test file
pytest backend/tests/integration/test_full_pipeline_cascade.py -v

# Only integration-marked tests
pytest -m integration -v
```

## Architecture

Tests use FastAPI's `TestClient` with mocked external dependencies:

| Dependency | Mock Strategy |
|-----------|--------------|
| Supabase | `MockSupabaseClient` (configurable failure modes) |
| PNCP API | `patch("routes.search.buscar_todas_ufs_paralelo")` |
| Redis | `MockRedis` (in-memory) |
| LLM (OpenAI) | `patch("llm.gerar_resumo")` |
| Storage | `patch("storage.upload_excel")` |
| Metrics | All Prometheus counters mocked |

## Test Files

| File | AC | Scenario |
|------|-----|----------|
| test_full_pipeline_cascade.py | AC6 | PNCP fail -> cache fallback -> empty_failure |
| test_queue_inline_fallback.py | AC7 | Queue unavailable -> inline LLM/Excel |
| test_supabase_total_outage.py | AC8 | All DB ops fail -> degraded search |
| test_absolute_worst_case.py | AC9 | All sources + caches fail |
| test_post_independent_of_sse.py | AC10 | POST works without SSE |
| test_frontend_504_timeout.py | AC11 | Timeout -> user-friendly error |
| test_queue_worker_fail_inline.py | AC12 | Queue dispatch OK, worker fails |
| test_schema_canary.py | AC13 | Schema drift detection |
| test_pncp_api_canary.py | AC14 | PNCP API contract validation |
| test_concurrent_searches.py | AC15 | Concurrent search isolation |

## Adding Tests

1. Use `@pytest.mark.integration` marker
2. Use `integration_app` fixture for TestClient access
3. Mock external boundaries, let internal pipeline run
4. Include production-scenario docstring
