# STORY-CIG-BE-asyncio-run-production-scan — Static scan detecta `asyncio.run()` em 4 arquivos de produção — 2 testes prod-bug candidato

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Blocked (aguarda decisão @architect)
**Priority:** P1 — Gate (potencial antipattern em produção)
**Effort:** L (8h+, possivelmente maior se refactor)
**Agents:** @architect (decisão primária), @dev, @qa, @devops

---

## Contexto

Duas suítes static-scan rodam em `backend-tests.yml` e falham em **2 testes** do triage row #28/30 — porém por motivo **estrutural**, não por mock drift ou assertion drift simples. Causa raiz classificada como **prod-bug candidato**.

Os testes fazem grep em código de produção procurando `asyncio.run()` e falham com o aviso:

> `asyncio.run()` em código de produção é antipattern quando chamado dentro de contexto async (FastAPI request handler, ARQ worker). Pode causar `RuntimeError: This event loop is already running` ou deadlock.

**4 arquivos de produção apontados pelo static scan:**
- `backend/llm.py`
- `backend/ingestion/contracts_crawler.py`
- `backend/llm_arbiter/classification.py`
- `backend/webhooks/handlers/__init__.py`

**Esta story está BLOCKED** até @architect decidir entre:

- **(A) São antipatterns reais** — refatorar para usar `asyncio.create_task()` ou `await`. Story fica grande e exige validação de não-regressão em produção.
- **(B) São sync entry points legítimos** — scripts CLI, worker boot, webhook dispatch em sync context. Atualizar os testes static-scan para ignorar os 4 paths específicos com justificativa em comentário.
- **(C) Mix** — alguns antipatterns, alguns legítimos. Resolver caso a caso.

**Arquivos principais afetados:**
- `backend/tests/test_redis_pool.py::test_no_asyncio_run_in_production`
- `backend/tests/test_story_221_async_fixes.py`

**Hipótese inicial de causa raiz (a confirmar por @architect):** Provável mix (C). `llm_arbiter/classification.py` e `webhooks/handlers/__init__.py` provavelmente são contextos sync legítimos; `llm.py` e `ingestion/contracts_crawler.py` precisam análise.

---

## Acceptance Criteria

- [ ] AC0 (NOVO — blocker): @architect decide (A)/(B)/(C) arquivo-por-arquivo e documenta decisão em RCA desta story antes de @po validar.
- [ ] AC1: `pytest backend/tests/test_redis_pool.py::test_no_asyncio_run_in_production backend/tests/test_story_221_async_fixes.py -v` retorna exit code 0 localmente (2/2 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" incluindo (a) decisão de @architect por arquivo, (b) commits de refactor (se A), (c) alteração de static-scan com justificativa (se B).
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido. Se refactor (A): testes de integração async cobrindo não-regressão.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados. Se `@pytest.mark.skip` for adicionado em algum teste durante refactor, justificativa documentada + aprovação @devops.

---

## Investigation Checklist (para @architect, fase Pre-Implement)

- [ ] Ler os 4 arquivos e identificar call-sites de `asyncio.run()`.
- [ ] Para cada: classificar como antipattern real (A), legítimo (B), ou requer refactor sutil (C).
- [ ] Documentar decisão em RCA antes de Status passar de Blocked → Draft.
- [ ] Se (A): planejar refactor incremental, não big-bang.
- [ ] Se (B): atualizar static-scan para permitir com justificativa inline.

## Investigation Checklist (para @dev, fase Implement — só após @architect)

- [ ] Implementar decisão de @architect arquivo-por-arquivo.
- [ ] Rodar testes das suítes impactadas (não só os 2 scans).
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #28/30)
- **Bloqueada por:** decisão @architect (AC0)

## Stories relacionadas no epic

- STORY-CIG-BE-llm-arbiter-internals (#14 — mesmo path `llm_arbiter/`)
- STORY-CIG-BE-consolidation-helpers-private (#10 — mesmo padrão private refactor)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #28/30 (handoff PR #383). Status `Blocked` — **aguarda decisão @architect antes de @po validar**. Triage anotou explicitamente: *"exigem decisão de produto antes de refatorar"*.
