# STORY-CIG-BE-asyncio-run-production-scan — Static scan detecta `asyncio.run()` em 4 arquivos de produção — 2 testes prod-bug candidato

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P1 — Gate
**Effort:** S (1-3h) usando Fix Path recomendado; M (3-8h) se Option A de Phase 2
**Agents:** @dev, @qa, @devops (decisão @architect já fechada)

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

## Architect Decision (AC0 — resolvido 2026-04-18 por @architect / Aria)

**Verdict: (C) MIX.** Dos 4 arquivos listados no triage, **2 são antipatterns reais**, **1 é legítimo** (CLI entry `__main__`), **1 é falso positivo** (arquivo não contém `asyncio.run()`). Além disso, o static scan está capturando **2 CLI scripts legítimos adicionais** que não foram listados no triage mas falham o mesmo teste.

### Tabela de decisão arquivo-por-arquivo

| # | Arquivo:Linha | Contexto real (código lido) | Verdict | Fix |
|---|---------------|-----------------------------|---------|-----|
| 1 | `backend/llm.py:371` | Dentro de `try/except`, fire-and-forget para `track_llm_cost()`. Guard `_loop.is_running()` — se sim `ensure_future`, senão `asyncio.run()`. Invocado por `gerar_resumo()` que roda em ARQ worker (async) E em ThreadPoolExecutor (sync). | **(A) Antipattern** | Ver Fix Path Phase 2 abaixo |
| 2 | `backend/ingestion/contracts_crawler.py:763,765,770` | Dentro de `if __name__ == "__main__":` CLI block. Módulo é importado por `ingestion/scheduler.py` (ARQ) e `routes/admin_trace.py` — o guard `__main__` impede `asyncio.run()` de disparar quando importado. | **(B) Legítimo** | Ver Fix Path Phase 1 |
| 3 | `backend/llm_arbiter/classification.py:217` | Dentro de `try/except RuntimeError`, mesmo padrão de #1. Usa `get_running_loop()` (moderno) vs #1 que usa `get_event_loop()` deprecated. Comment: "Sem loop rodando (thread pool worker) — executa inline". | **(A) Antipattern** | Ver Fix Path Phase 2 |
| 4 | `backend/webhooks/handlers/__init__.py` | **Arquivo não contém `asyncio.run()`** (grep retornou 0 matches). Triage listou por engano ou o fix já foi aplicado antes. | **(N/A) falso positivo** | Nenhuma ação |

### Achados adicionais (não listados no triage mas falham o mesmo static scan)

| Arquivo:Linha | Contexto | Verdict |
|---------------|----------|---------|
| `backend/scripts/gsc_metrics.py:155` | CLI script standalone | **(B) Legítimo** — Phase 1 |
| `backend/scripts/backfill_embeddings.py:242` | CLI script standalone | **(B) Legítimo** — Phase 1 |

### Racional técnico (por que #1 e #3 são antipatterns)

1. **`asyncio.run()` dentro de ThreadPoolExecutor worker cria event loop novo por chamada**. Custo: ~1-3ms por call + alloc de resources + possível GC pressure. Para `track_llm_cost()` disparado a cada summary/classification, isso é desperdício.
2. **Fragilidade com `get_event_loop()` em #1**: em Python 3.12, `asyncio.get_event_loop()` sem loop rodando emite `DeprecationWarning` e cria um novo loop. O código depende desse comportamento deprecated. Python 3.14 removerá.
3. **Isolamento de conexões**: se `track_llm_cost()` usar clientes async (Supabase, Redis) inicializados no main loop, chamá-los de um novo loop via `asyncio.run()` pode corromper connection pools ou causar `Future attached to different loop`.

### Fix Path recomendado

**Phase 1 — low risk, 1 commit, unblocks CI (recomendado começar por aqui):**

Atualizar os 2 static-scan tests para ignorar linhas legítimas:

- **Skip lines dentro de `if __name__ == "__main__":` blocks.** Detecção: rastrear indentation dentro do loop de parsing e pular quando estiver dentro de um bloco cuja primeira linha match `if __name__ == "__main__":`.
- **Skip files sob `backend/scripts/`** (são CLI tools por design — invocados via `python backend/scripts/X.py`, nunca importados).

Alvo dos edits:
- `backend/tests/test_redis_pool.py` linhas 441-475 (`TestNoAsyncioRunInProduction`)
- `backend/tests/test_story_221_async_fixes.py` linhas 197-226 (`test_no_asyncio_run_in_production_code`)

Impacto após Phase 1: ambos testes passam sem tocar em código de produção. `llm.py:371` e `classification.py:217` ainda violam o scan — seguir para Phase 2.

**Phase 2 — medium risk, resolve os 2 antipatterns reais. Escolher UMA das 3 opções:**

- **Option C (recomendada para fix rápido):** Nos arquivos #1 e #3, remover o branch que chama `asyncio.run()` e substituir por: emitir counter `smartlic_llm_budget_track_skipped_total{reason="no_running_loop"}` + retornar silenciosamente. Racional: tracking de custo é fire-and-forget observável — perder alguns ticks em thread pool workers é aceitável, especialmente se instrumentado. Adicionar `TODO(CIG-BE-28 Phase 2 Option A)` no código marcando a dívida técnica. **Effort: S.**

- **Option A (long-term, mais correto):** Capturar a referência ao main loop no FastAPI `lifespan` startup (`app.state.main_loop = asyncio.get_running_loop()`) e propagar para o módulo `llm_budget` via injection ou global. Em #1 e #3, substituir `asyncio.run(_track(...))` por `asyncio.run_coroutine_threadsafe(_track(cost_usd), main_loop)` — agenda no loop principal de forma thread-safe. **Effort: M.** Requer cuidado para que o `main_loop` esteja disponível em ARQ workers também.

- **Option B (sync track):** Reescrever `track_llm_cost()` como função sync que usa cliente sync (redis-py sync, httpx sync) quando chamada de thread pool. Duplica código. **Effort: M.** Não recomendado.

**Recomendação final:** Phase 1 + Phase 2 Option C em 1 commit, escopo S (1-3h). Se @po exigir correção definitiva agora, escolher Option A e re-estimar para M.

---

## Acceptance Criteria

- [x] AC0 (resolvido 2026-04-18 por @architect): verdict MIX (C). Phase 1 + Phase 2 Option C é o fix path recomendado. Detalhes na seção "Architect Decision" acima.
- [ ] AC1 (after implementation): `pytest backend/tests/test_redis_pool.py::TestNoAsyncioRunInProduction backend/tests/test_story_221_async_fixes.py::test_no_asyncio_run_in_production_code -v` retorna exit code 0 localmente (2/2 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra as 2 suítes com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis" referenciando (a) Architect Decision acima, (b) edits Phase 1 em static-scan tests com justificativa inline em comentário, (c) edits Phase 2 em `llm.py:371` e `classification.py:217` com TODO referenciando Phase 2 Option A.
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido. Novo counter `smartlic_llm_budget_track_skipped_total` emitido em Phase 2 Option C para observabilidade do trade-off.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados. Nenhum teste adicionado com `@pytest.mark.skip`.

---

## Investigation Checklist (para @architect — concluído 2026-04-18)

- [x] Ler os 4 arquivos e identificar call-sites de `asyncio.run()`.
- [x] Para cada: classificar como antipattern real (A), legítimo (B), ou requer refactor sutil (C). Resultado: (C) MIX documentado na tabela acima.
- [x] Documentar decisão na seção "Architect Decision" acima.
- [x] Planejar refactor incremental em 2 phases (Phase 1 static-scan update; Phase 2 Option C com TODO para Option A futura).
- [x] Identificar falsos positivos no triage (`webhooks/handlers/__init__.py`) e achados adicionais não listados (`scripts/gsc_metrics.py`, `scripts/backfill_embeddings.py`).

## Investigation Checklist (para @dev, fase Implement)

- [ ] Phase 1: editar `backend/tests/test_redis_pool.py` linhas 441-475 para skipar (a) linhas dentro de `if __name__ == "__main__":` e (b) arquivos sob `backend/scripts/`. Comentário inline referenciando esta story (`# STORY-CIG-BE-asyncio-run-production-scan: ...`).
- [ ] Phase 1: mesma edit em `backend/tests/test_story_221_async_fixes.py` linhas 197-226.
- [ ] Phase 2: em `backend/llm.py:362-373` e `backend/llm_arbiter/classification.py:208-219`, substituir branch `asyncio.run()` por `metrics.smartlic_llm_budget_track_skipped_total.labels(reason="no_running_loop").inc()` + `return`. Adicionar TODO comment referenciando Phase 2 Option A como dívida futura.
- [ ] Adicionar counter `smartlic_llm_budget_track_skipped_total` em `backend/metrics.py` (label `reason`).
- [ ] Rodar `pytest backend/tests/test_redis_pool.py backend/tests/test_story_221_async_fixes.py -v`.
- [ ] Rodar suítes relacionadas a LLM (`pytest backend/tests/test_llm_cost_monitoring.py backend/tests/test_harden001_openai_timeout.py -v`) para garantir não-regressão — overlap com STORY-CIG-BE-llm-arbiter-internals (#14).
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #28/30)
- ~~Bloqueada por: decisão @architect (AC0)~~ — **resolvido 2026-04-18**, story liberada

## Stories relacionadas no epic

- STORY-CIG-BE-llm-arbiter-internals (#14 — mesmo path `llm_arbiter/`)
- STORY-CIG-BE-consolidation-helpers-private (#10 — mesmo padrão private refactor)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #28/30 (handoff PR #383). Status `Blocked` — aguarda decisão @architect.
- **2026-04-18** — @architect (Aria): AC0 resolvido. Decisão (C) MIX: 2 antipatterns reais (`llm.py:371`, `llm_arbiter/classification.py:217`), 1 CLI legítimo (`contracts_crawler.py`), 1 falso positivo (`webhooks/handlers/__init__.py` não contém asyncio.run). Fix Path Phase 1 (static-scan skip `__main__` + `scripts/`) + Phase 2 Option C (skip tracking em thread pool workers, TODO para Option A) documentado. Achados adicionais: `scripts/gsc_metrics.py` e `scripts/backfill_embeddings.py` também são (B) CLI legítimos cobertos pela Phase 1. Effort rebaixado de L → S. Status `Blocked` → `Draft`. Próximo: `@po *validate-story-draft`.
- **2026-04-18** — @po (Pax): *validate-story-draft **GO (9/10)** — Draft → Ready. Story exemplar pós-unblock @architect. AC0 resolvido, Fix Path Phase 1 + Phase 2 Option C documentados; @dev pode iniciar Implement com Effort S.
