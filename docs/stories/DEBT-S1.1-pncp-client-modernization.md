# DEBT-S1.1: PNCP Client Modernization -- Sync to Async
**Epic:** EPIC-DEBT
**Sprint:** 1
**Priority:** P1
**Estimated Hours:** 16h
**Assignee:** TBD

## Objetivo

Migrar `pncp_client.py` de `requests` (sincrona) para `httpx` (async nativo). Atualmente mitigado por `asyncio.to_thread()` que e adequado para 2 workers, mas limita escala futura e adiciona overhead de thread pool. Migracao incremental por metodo para minimizar risco de regressao.

## Debitos Incluidos

| ID | Debito | Severidade | Horas |
|----|--------|------------|-------|
| SYS-02 | PNCP client usa `requests` sincrona. `pncp_client.py` linha 8 tem `import requests`. Mitigado por `asyncio.to_thread()`. Adequado para escala atual (2 workers). | HIGH | 16h |

## Acceptance Criteria

- [ ] AC1: `pncp_client.py` usa `httpx.AsyncClient` em vez de `requests.Session`
- [ ] AC2: `import requests` removido de `pncp_client.py`
- [ ] AC3: `asyncio.to_thread()` wrapper removido dos callers
- [ ] AC4: Todos os metodos publicos sao `async def`
- [ ] AC5: Connection pooling via `httpx.AsyncClient` com limits configurados
- [ ] AC6: Retry logic preservada (exponential backoff, HTTP 422 retryable)
- [ ] AC7: Circuit breaker funciona com async client
- [ ] AC8: Timeout configuravel por request (default 30s por UF)
- [ ] AC9: Todos os 7332+ testes passam (mocks atualizados de `requests.Session` para `httpx.AsyncClient`)

## Tasks

- [ ] T1: Criar feature branch `feat/pncp-async`
- [ ] T2: Adicionar `httpx` a requirements.txt (se nao presente)
- [ ] T3: Migrar primeiro metodo simples (ex: health check) como proof of concept
- [ ] T4: Atualizar mocks correspondentes e rodar testes
- [ ] T5: Migrar `buscar_contratacoes()` (metodo principal)
- [ ] T6: Migrar `buscar_todas_ufs_paralelo()` (metodo de orquestracao)
- [ ] T7: Migrar metodos restantes
- [ ] T8: Remover `asyncio.to_thread()` wrappers em callers (search_pipeline.py, etc.)
- [ ] T9: Atualizar TODOS os `@patch("pncp_client.requests.Session")` mocks
- [ ] T10: Rodar full suite para validar zero regressoes
- [ ] T11: Load test comparativo (antes vs depois) para medir ganho de performance

## Testes Requeridos

- [ ] Todos os testes existentes de `pncp_client` passam com novos mocks
- [ ] Novo teste: `httpx.AsyncClient` connection pool limits respeitados
- [ ] Novo teste: timeout por request funciona
- [ ] Novo teste: retry com backoff funciona em modo async
- [ ] Integration test: busca real com PNCP API (staging)
- [ ] Backend test count >= 7332

## Definition of Done

- [ ] All ACs met
- [ ] Tests passing (backend + frontend)
- [ ] No new debt introduced
- [ ] Code reviewed
- [ ] Deployed to staging

## Notas

- **Migracao incremental obrigatoria.** 1 metodo por vez em feature branch. NAO fazer big-bang.
- **Risco principal:** Todos `@patch("pncp_client.requests.Session")` mocks quebram. Sao muitos testes.
- `httpx` ja pode estar em requirements.txt (usado por outros clients). Verificar.
- Este debt habilita SYS-12 (cache unification) no Sprint 2 que se beneficia do mesmo async pattern.

## Referencias

- Assessment: `docs/prd/technical-debt-assessment.md` secao "Sistema" (SYS-02)
- Client: `backend/pncp_client.py`
- Pipeline: `backend/search_pipeline.py`
- Consolidation: `backend/consolidation.py`
