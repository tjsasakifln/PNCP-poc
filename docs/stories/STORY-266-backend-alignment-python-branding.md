# STORY-266: Backend Alignment — Python Version & Branding

## Metadata
- **Epic:** Enterprise Readiness (EPIC-ENT-001)
- **Priority:** P1 (Stability)
- **Effort:** 0.75 hours
- **Area:** Backend
- **Depends on:** None
- **Risk:** Low
- **Assessment IDs:** T2-13, T2-14

## Context

O Dockerfile usa `python:3.11-slim` mas `pyproject.toml` targeta Python 3.12, criando incompatibilidades sutis com type hints e stdlib. O User-Agent das requests HTTP para APIs publicas (PNCP, PCP) ainda diz "BidIQ" em vez de "SmartLic", o que e misleading para provedores e inconsistente com o branding atual.

## Acceptance Criteria

- [x] AC1: Dockerfile e pyproject.toml concordam na versao Python (ambos 3.12 ou ambos 3.11)
- [x] AC2: Build Docker funciona sem erros com a versao alinhada
- [x] AC3: Full backend test suite passa com a versao alinhada
- [x] AC4: User-Agent em todas as requests HTTP externas diz "SmartLic" (nao "BidIQ")
- [x] AC5: `grep -r "BidIQ" backend/` retorna zero resultados em arquivos de producao (testes podem manter referencias historicas)

## Tasks

- [x] Task 1: Alinhar `backend/Dockerfile` para `python:3.12-slim` (ou atualizar pyproject.toml para target 3.11)
- [x] Task 2: Rebuild Docker image e verificar que compila sem erros
- [x] Task 3: Em `backend/pncp_client.py`: substituir User-Agent "BidIQ" por "SmartLic"
- [x] Task 4: Grep por "BidIQ" em todo o backend — corrigir qualquer referencia em codigo de producao
- [x] Task 5: Rodar full `pytest`

## Test Plan

1. Docker build com versao alinhada — sem erros
2. `pytest` full suite — 0 regressions
3. `grep -ri "bidiq" backend/ --include="*.py"` — zero em arquivos de producao (exceto testes/configs historicos)
4. Verificar User-Agent em logs de request PNCP

## Regression Risks

- **Baixo (T2-13):** Mudar de 3.11 para 3.12 pode expor warnings de deprecation. Rodar full test suite e suficiente.
- **Baixo (T2-14):** Mudanca de string. Nenhum provedor de API depende do User-Agent para autenticacao.

## Files Changed

- `backend/Dockerfile` (EDIT — python:3.11→3.12, BidIQ→SmartLic)
- `backend/pyproject.toml` (EDIT — name, description, requires-python)
- `backend/config.py` (EDIT — CORS origins updated to smartlic hostnames)
- `backend/job_queue.py` (EDIT — Redis key prefix bidiq:→smartlic:)
- `backend/progress.py` (EDIT — Redis key prefix bidiq:→smartlic:)
- `backend/routes/bid_analysis.py` (EDIT — Redis cache key prefix)
- `backend/routes/emails.py` (EDIT — default backend URL)
- `backend/railway.toml` (EDIT — comments BidIQ→SmartLic)
- `backend/railway-worker.toml` (EDIT — comments BidIQ→SmartLic)
- `backend/README.md` (EDIT — title BidIQ→SmartLic)
- `backend/tests/test_job_queue.py` (EDIT — Redis key assertion)
- `backend/tests/test_progress.py` (EDIT — Redis key assertions)

## Definition of Done

- [x] Versao Python alinhada entre Dockerfile e pyproject.toml
- [x] Docker build funcional
- [x] Zero "BidIQ" em codigo de producao
- [x] Full pytest suite passing
