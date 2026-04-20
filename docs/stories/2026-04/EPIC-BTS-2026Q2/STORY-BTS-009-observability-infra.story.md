# STORY-BTS-009 — Observability & Infra Drift (20 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P2
**Effort:** S (2-3h) — mostly assertion-drift
**Agents:** @dev + @qa
**Status:** InReview (PR #410 — 25/25 tests green in worktree; blocked on main CI drift unrelated to BTS-009 content — see STORY-BTS-011)

---

## Contexto

20 testes cobrindo infra (GTM-INFRA-001, GTM-INFRA-002, GTM-CRITICAL-SCENARIOS), observabilidade (logs, audit, cron monitoring, prometheus, openapi, schema validation), e error handling. Maioria deve ser assertion-drift sobre valores de config mudados (ex: GUNICORN_TIMEOUT 120→110 já foi fixado parcialmente em PR #392).

---

## Arquivos (tests)

- `backend/tests/test_gtm_infra_001.py` (4 failures) — parciais já fixados em PR #392; remaining 4 são diferentes
- `backend/tests/test_gtm_infra_002.py` (1 failure)
- `backend/tests/test_gtm_critical_scenarios.py` (2 failures)
- `backend/tests/test_gtm_fix_041_042.py` (3 failures)
- `backend/tests/test_gtm_fix_027_track2.py` (1 failure)
- `backend/tests/test_log_volume.py` (6 failures)
- `backend/tests/test_audit.py` (1 failure)
- `backend/tests/test_cron_monitoring.py` (1 failure)
- `backend/tests/test_prometheus_labels.py` (1 failure)
- `backend/tests/test_openapi_schema.py` (1 failure)
- `backend/tests/test_schema_validation.py` (1 failure)
- `backend/tests/test_error_handler.py` (1 failure)

---

## Acceptance Criteria

- [x] AC1: `pytest` nos 12 arquivos retorna exit code 0 (25/25 PASS — 5 extras triaged vs 20 esperados, delta sanitizado em PR body).
- [ ] AC2: CI verde. *(aguarda PR merge)*
- [x] AC3: RCA distinguindo (a) config value drift vs (b) observability output shape drift vs (c) openapi schema drift. Ver PR description para matriz completa.
- [x] AC4: Cobertura não caiu. Suíte vizinha (test_api_buscar + test_pipeline + test_pipeline_cascade_unit) = 55/55 PASS, sem regressões.
- [x] AC5: zero quarantine. Nenhum `@pytest.mark.skip` / `xfail` adicionado.

---

## Investigation Checklist

- [x] Para `test_openapi_schema`: re-gerar schema via `UPDATE_SNAPSHOTS=1 pytest` (38 endpoints novos validados via git log por rota); delete do diff debug artefato.
- [x] Para `test_gtm_infra_001` remainders (4 ainda falham após PR #392): DEBT-204 facade refactor — trocados source-grep checks por `inspect.getsource()` + patch target no submodule correto.
- [x] Para `test_log_volume`: pattern 1 (patch target drift) — todas 6 falhas foram `_supabase_save_cache` removido; re-aliased para `cache.manager.save_to_cache_per_uf`.
- [x] **Novidade descoberta:** pollution global de `startup.state.shutting_down=True` após lifespan test → 5 colateral 503s em test_error_handler. Fixture autouse resetando state + CBs adicionada.

---

## Dependências

- **Bloqueado por:** nenhum (paralelo)
- **Bloqueia:** nenhum

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready.
- **2026-04-19** — @po (Pax): Validação GO — 7/10. Gaps: P4 escopo, P7 valor, P8 riscos. Story confirmada Ready.
- **2026-04-20** — @dev (Dex): Wave 3 initiated. Baseline discovery no worktree `fix/bts-009-observability-infra`: **25 failures** (5 a mais que os 20 triaged — delta documentado em PR body). Status Ready→InProgress.
- **2026-04-20** — @dev (Dex): Wave 3 complete. **25/25 PASS** (zero quarentena, zero prod edits). 8 commits atômicos por categoria. Status InProgress→InReview. Descobertas laterais documentadas:
  - **Não-regressão descoberta (não é prod bug):** pollution de `startup.state.shutting_down` persistente após `async with lifespan(app)` em `test_startup_succeeds_with_valid_schema` fazia todos os HTTP tests subsequentes retornarem 503 via `shutdown_drain_middleware` (DEBT-124). Fixado com autouse fixture que restaura `shutting_down=False` + `Supabase CB.reset()`. Em produção esse estado persiste apenas durante shutdown real — não há regressão.
  - **38 novos endpoints em OpenAPI schema snapshot:** drift legítimo das últimas ~6 weeks de stories públicas (blog, observatório, sitemaps, indice municipal, compliance, fornecedores, notifications, founding). Snapshot regenerado e commitado; sem necessidade de novas stories de API review.
  - **Diff artefato stale** (`openapi_schema.diff.json`) agora é deletado pela própria lógica do teste quando `UPDATE_SNAPSHOTS=1` — commit da deleção evita que ele volte como `dirty tree` em cada CI run.
- **2026-04-20** — @dev (majestic-valiant session): Re-run do CI de main HEAD `2ff704a4` (post #411 + #407 merges) revelou **~150 falhas** em ~8-10 clusters distintos — conjunto **disjunto** do baseline que BTS-009 atacou. Investigação (advisor consultado) confirmou que são drifts **reais** em outras stories, não flakiness pura nem regressão por #407 (diff de #407 é +17 linhas puramente aditivas em `filter/pipeline.py`). Conclusão: BTS-009 code está correto e pronto; PR #410 blocked por main CI que precisa de **STORY-BTS-011** (nova sweep) antes de destravar. PR #424 (`fix(tests): 4 drift clusters`) já liga 15 falhas; BTS-011 ataca os 135 restantes. Status mantido `InReview`.
