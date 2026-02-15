# STORY-TD-007: Async Fixes e CI Quality Gates

## Epic
Epic: Resolucao de Debito Tecnico v2.0 -- SmartLic/BidIQ (EPIC-TD-v2)

## Sprint
Sprint 1: Seguranca e Correcoes

## Prioridade
P1

## Estimativa
4h

## Descricao

Esta story corrige anti-patterns de blocking em contexto async e adiciona mypy ao CI pipeline, fechando lacunas de qualidade automatizada.

1. **`time.sleep(0.3)` sincrono em contexto async (SYS-07, MEDIUM, 2h)** -- `save_search_session` em `backend/quota.py` linha 910 usa `time.sleep(0.3)` no retry, bloqueando o event loop inteiro. Todas as requests concorrentes pausam 300ms durante retry. Migrar para `asyncio.sleep(0.3)`. **ATENCAO CR-09:** `time.sleep` garante exclusao mutua por bloqueio do event loop; `asyncio.sleep` permite interleaving. Verificar se `save_search_session` tem race conditions potenciais antes de migrar.

2. **mypy nao configurado no CI (SYS-10, MEDIUM, 2h)** -- `ruff check .` ja esta ativo em `backend-ci.yml` linhas 33-36. Apenas mypy falta para completar o pipeline de qualidade estatica. Adicionar step de mypy ao workflow com configuracao basica (`--ignore-missing-imports` inicialmente, restringir gradualmente).

## Itens de Debito Relacionados
- SYS-07 (MEDIUM): `save_search_session` usa `time.sleep(0.3)` sincrono em contexto async
- SYS-10 (MEDIUM): mypy nao configurado no CI (ruff ja ativo)

## Criterios de Aceite

### Async Sleep Fix
- [ ] `grep "time.sleep" backend/quota.py` retorna zero matches
- [ ] `save_search_session` usa `asyncio.sleep(0.3)` no retry
- [ ] Verificacao de race condition documentada: operacao protegida ou safe para interleaving
- [ ] Se race condition detectada: implementar lock (asyncio.Lock) antes de migrar para asyncio.sleep
- [ ] Testes de `save_search_session` atualizados para usar async mock
- [ ] SSE progress funciona corretamente apos mudanca

### mypy no CI
- [ ] `.github/workflows/backend-ci.yml` inclui step de mypy
- [ ] `mypy backend/` executa sem erros CRITICAL (warnings podem ser tolerados inicialmente)
- [ ] `pyproject.toml` ou `mypy.ini` criado com configuracao basica
- [ ] `--ignore-missing-imports` habilitado para libs sem stubs
- [ ] CI pipeline passa com mypy habilitado (nao bloqueia por warnings)

## Testes Requeridos

| ID | Teste | Tipo | Prioridade |
|----|-------|------|-----------|
| REG-T06 | SSE progress funciona apos asyncio.sleep | Integracao | P1 |
| REG-T07 | `save_search_session` retry sem race condition | Unitario | P1 |
| PERF-T04 | Busca 5 UFs sem event loop blocking (nenhum stall > 300ms) | Load test | P2 |

## Dependencias
- **Blocks:** Nenhuma
- **Blocked by:** Nenhuma (independente)

## Riscos
- **CR-09:** `time.sleep` -> `asyncio.sleep` pode expor race condition se `save_search_session` nao for safe para interleaving. Investigar ANTES de implementar.
- mypy pode reportar muitos erros em codebase existente. Usar `--ignore-missing-imports` e gradualmente restringir.

## Rollback Plan
- Se asyncio.sleep causar race condition: reverter para `time.sleep` e documentar como debt a ser resolvido com locking.
- Se mypy bloquear CI: tornar step non-blocking (`continue-on-error: true`) e criar plan de correcao gradual.

## Definition of Done
- [ ] Codigo implementado e revisado
- [ ] Testes passando (unitario + integracao)
- [ ] CI/CD green (incluindo novo step mypy)
- [ ] Documentacao atualizada (analise de race condition)
- [ ] Deploy em staging verificado
