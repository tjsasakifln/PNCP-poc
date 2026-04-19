# STORY-BTS-007 — Integration Tests (real external services) (5 testes)

**Epic:** [EPIC-BTS-2026Q2](EPIC.md)
**Priority:** P2 (último a atacar — integration tests tradicionalmente dependem de infra que pode não estar em CI)
**Effort:** S (2-3h)
**Agents:** @dev + @qa + @devops (se CI service setup for necessário)
**Status:** Ready

---

## Contexto

5 testes em `backend/tests/integration/` que historicamente rodam contra serviços reais (Redis, Supabase, possivelmente OpenAI). Se CI não provisiona esses serviços, tests devem (a) ser movidos para suite `external` separada (não gate), OU (b) usar mocks fortes que simulam semântica completa.

**Decisão necessária antes de implementar:** (a) ou (b). @po/@architect decide.

---

## Arquivos (tests)

- `backend/tests/integration/test_full_pipeline_cascade.py` (3 failures)
- `backend/tests/integration/test_queue_worker_fail_inline.py` (2 failures)

---

## Acceptance Criteria

- [ ] AC1: Decisão documentada: (a) mover para `external` suite, OU (b) mock pesado mantendo o gate. @po aprova em 1 parágrafo.
- [ ] AC2: Se (a): `.github/workflows/backend-tests.yml` exclui `tests/integration/` do gate + criar workflow `backend-tests-external.yml` não-bloqueante que roda as integration.
- [ ] AC2b: Se (b): `pytest backend/tests/integration/test_full_pipeline_cascade.py backend/tests/integration/test_queue_worker_fail_inline.py --timeout=60` retorna exit code 0 com mocks; CI verde.
- [ ] AC3: RCA: (a) ou (b), e por quê.
- [ ] AC4: Cobertura não caiu (se (a), adicionar unit tests equivalentes para preservar coverage).
- [ ] AC5: zero quarantine no path do gate.

---

## Investigation Checklist

- [ ] Rodar cada arquivo com Redis+Supabase mocks — se falha por mock insuficiente, opção (b) é viável
- [ ] Se tests precisam de HTTP real (PNCP, OpenAI), opção (a) é única saída
- [ ] Validar com @devops se CI pode provisionar Redis via GitHub service (já fizemos isso em outras PRs?)

---

## Dependências

- **Bloqueado por:** nenhum (pode rodar em paralelo)
- **Bloqueia:** nenhum

---

## Change Log

- **2026-04-19** — @sm (River): Story criada. Status Ready. @po precisa aprovar direção (a) vs (b) antes de implement.
