# STORY-5.3: Session Dedup Eventual Consistency Mitigation (TD-SYS-013)

**Priority:** P2 | **Effort:** M (16h → actual ~2h — pre-existing engine)
**Squad:** @dev + @architect | **Status:** InReview
**Epic:** EPIC-TD-2026Q2 | **Sprint:** 4-6

## Story
**As a** usuário SmartLic, **I want** menos duplicatas em busca consolidada, **so that** confiança nos resultados aumente.

## Discovery Note (2026-04-15)

A descoberta durante implementation: `backend/consolidation/dedup.py` (TD-008 refactor) já
implementa 3 camadas de fuzzy dedup sobre `UnifiedProcurement`:

1. `_deduplicate_fuzzy` — blocking por cnpj + Jaccard 0.85 em objeto (com adjacency de
   edital numbers como backstop).
2. `_deduplicate_by_process_number` — blocking por (cnpj, year) + Jaccard 0.80.
3. `_deduplicate_by_title_prefix` — blocking por 60-char prefix + Jaccard 0.85 (cross-org).

A story entrou como "adicionar dedup fuzzy", mas na prática o trabalho correto é
**parametrizar** (threshold via env), **instrumentar** (métrica Prometheus por camada) e
**permitir desligar** (feature flag), sem romper o comportamento default.

## Acceptance Criteria
- [x] AC1: `consolidation.py` adiciona dedup adicional via fuzzy match (orgao_cnpj + objeto_compra similarity) — já existia em `consolidation/dedup.py` (3 layers); preservado + agora instrumentado
- [x] AC2: Threshold configurável via env `DEDUP_FUZZY_THRESHOLD` (default 0.85) — aplicado em `_deduplicate_fuzzy` e `_deduplicate_by_title_prefix`
- [x] AC3: Métrica `smartlic_dedup_fuzzy_hits_total{layer}` — criada em `metrics.py`, incrementada em cada `to_remove.add` das 3 camadas
- [ ] AC4: User feedback negativo de duplicate < 1% (medir 30d post-deploy) — **monitoring task** pós-deploy, não é gate de código

## Tasks
- [x] Audit dedup atual — confirmed 4 layers já implementadas
- [x] Parametrizar threshold — `DEDUP_FUZZY_THRESHOLD` (default 0.85)
- [x] Instrumentar métrica — `DEDUP_FUZZY_HITS{layer}` em 4 call sites (fuzzy x2, process_number x2, title_prefix x1)
- [x] Feature flag — `DEDUP_FUZZY_ENABLED` (default true) permite desligar as 3 camadas fuzzy
- [x] Testes novos — `tests/test_consolidation_fuzzy_dedup.py` (6 tests, todos passing)
- [ ] A/B test em staging — monitoring task (não bloqueia merge)

## Implementation Summary

**Configuração (`backend/config/features.py`):**
```python
DEDUP_FUZZY_ENABLED: bool = str_to_bool(os.getenv("DEDUP_FUZZY_ENABLED", "true"))
DEDUP_FUZZY_THRESHOLD: float = float(os.getenv("DEDUP_FUZZY_THRESHOLD", "0.85"))
```

**Metric (`backend/metrics.py`):**
```python
DEDUP_FUZZY_HITS = _create_counter(
    "smartlic_dedup_fuzzy_hits_total",
    "STORY-5.3: Fuzzy dedup hits by layer",
    labelnames=["layer"],  # fuzzy | process_number | title_prefix
)
```

**Engine (`backend/consolidation/dedup.py`):**
- `DeduplicationEngine.__init__` aceita `fuzzy_enabled` e `fuzzy_threshold` (defaults do env).
- `run()` respeita `_fuzzy_enabled`: quando False pula as 3 camadas fuzzy (mas mantém
  `_deduplicate_by_source_id` + `_deduplicate`, que são dedup exato).
- Linhas 332, 367, 541: threshold hardcoded `0.85` → `self._fuzzy_threshold`.
- Linha 363: `value_threshold = 0.20 if sim >= self._fuzzy_threshold else 0.05`
- 4 call sites `to_remove.add(...)` agora emitem `DEDUP_FUZZY_HITS.labels(layer=...).inc()`.

## Rollback

| Variable | Effect |
|----------|--------|
| `DEDUP_FUZZY_ENABLED=false` | Desliga 3 camadas fuzzy; mantém exact dedup. |
| `DEDUP_FUZZY_THRESHOLD=1.0` | Threshold impossível → efetivamente desliga fuzzy+title_prefix, mas process_number (usa 0.80 fixo) segue rodando. |

## Dev Notes
- TD-SYS-013 ref
- Atual (pré-STORY-5.3): dedup por `numeroControlePNCP` + hash exato + 3 camadas fuzzy (não
  instrumentadas, threshold hardcoded)
- Pós-STORY-5.3: mesmas camadas + threshold parametrizado + flag + métricas Prometheus

## File List

**Modified:**
- `backend/config/features.py` — added DEDUP_FUZZY_ENABLED, DEDUP_FUZZY_THRESHOLD
- `backend/config/__init__.py` — re-export
- `backend/metrics.py` — added DEDUP_FUZZY_HITS counter
- `backend/consolidation/dedup.py` — parametrize threshold + emit metric + flag gate

**Added:**
- `backend/tests/test_consolidation_fuzzy_dedup.py` — 6 tests covering threshold, flag, metric

## Definition of Done
- [x] Flag + threshold + metric implemented
- [x] Tests green (6/6 new, zero regressions: baseline 24 fail / 37 pass / 9 error = identical)
- [ ] Post-deploy monitoring (AC4) — 30d observation window

## Risks
- R1: Falso positivo → bid legítimo escondido. **Mitigation:** threshold conservador (0.85
  default) + flag permite desligar em segundos via env var. Rollback custa zero.

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-04-14 | 1.0 | Initial draft | @sm |
| 2026-04-15 | 1.1 | Scope corrected post-discovery: engine já existia; trabalho real é instrumentation + parametrization | @dev |
| 2026-04-15 | 1.2 | Implementation complete: flag + threshold + metric + tests (6/6) + zero regression | @dev |
