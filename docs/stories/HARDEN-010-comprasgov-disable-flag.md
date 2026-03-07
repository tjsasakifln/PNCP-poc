# HARDEN-010: ComprasGov v3 Feature Flag Disable

**Severidade:** ALTA
**Esforço:** 5 min
**Quick Win:** Sim
**Origem:** Conselho CTO — Auditoria de Fragilidades (2026-03-06)

## Contexto

ComprasGov v3 está completamente fora do ar (confirmado 2026-03-03). API retorna 404 na homepage. Circuit breaker trata como transient e tenta recovery a cada 60s — desperdício de recursos.

## Critérios de Aceitação

- [x] AC1: Feature flag `COMPRASGOV_ENABLED` em config.py (default=false)
- [x] AC2: Consolidation skip source quando disabled
- [x] AC3: Log warning na startup se disabled
- [x] AC4: Fácil reativar via env var quando API voltar
- [x] AC5: Teste unitário valida skip

## Arquivos Afetados

- `backend/config.py` — COMPRASGOV_ENABLED flag + feature flag registry + startup warning
- `backend/source_config/sources.py` — from_env() reads COMPRASGOV_ENABLED from config.py
- `backend/search_pipeline.py` — early skip when COMPRASGOV_ENABLED=false
- `backend/main.py` — health check respects flag
- `backend/tests/test_harden010_comprasgov_disable.py` — 9 tests (AC1-AC5)
- `backend/tests/test_compras_gov_v3.py` — updated mock to use config.COMPRASGOV_ENABLED
- `backend/tests/test_pipeline_resilience.py` — updated mock to use config.COMPRASGOV_ENABLED
