# STORY-CIG-BE-buscar-route-404 — `/buscar` retorna 404 em TestClient (auth override / prefix drift)

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate Blocker
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_api_buscar.py` roda em `backend-tests.yml` e falha em **23 testes** do triage row #6/30 (ver `docs/stories/2026-04/EPIC-CI-GREEN-MAIN-2026Q2/backend-failure-triage.md`). Causa raiz classificada pelo triage como **mock-drift / import / route-prefix drift**.

O endpoint `/buscar` — rota central do produto (POST assincrono, SSE progress chain) — retorna HTTP 404 quando chamado via `TestClient` nos testes. Produção não foi validada pelo triage; o sintoma observado é exclusivo de ambiente de teste, sugerindo (a) `app.dependency_overrides[require_auth]` não está mais batendo com a assinatura atual do `require_auth`, (b) o prefix foi movido de `/buscar` para `/v1/search` (ou similar) em algum refactor recente, ou (c) o router de `routes/search/` virou package e perdeu o endpoint raiz.

Essa story é **gate blocker**: 23 testes da suíte mais importante do backend estão vermelhos e bloqueiam a meta agregada do EPIC (0 failed por 10 runs consecutivos).

**Arquivos principais afetados:**
- `backend/tests/test_api_buscar.py` (23 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Ver opções (a)/(b)/(c) acima. Validar com `pytest --collect-only` e `grep -rn "/buscar\\|@router.post" backend/routes/` antes de propor fix.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_api_buscar.py -v` retorna exit code 0 localmente (23/23 PASS, 0 skipped introduzidos nesta story).
- [ ] AC2: Última run do workflow `backend-tests.yml` no PR desta story mostra `test_api_buscar.py` com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" (categoria mock-drift / assertion-drift / import / collection / flakiness / infra-live / prod-bug conforme triage). Sintoma isolado **não é suficiente**.
- [ ] AC4: Cobertura backend **não caiu** vs. último run verde conhecido (diff `coverage-summary.json` no Change Log). Threshold 70% mantido.
- [ ] AC5 (NEGATIVO — política Zero quarentena do EPIC): `grep -nE "@pytest\\.mark\\.skip|pytest\\.skip\\(|@pytest\\.mark\\.xfail|\\.only\\("` vazio em todos os arquivos tocados nesta story. Nenhum teste movido para workflow não-gateado sem justificativa aprovada por @devops.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_api_buscar.py -v` isolado e confirmar reprodução local dos erros 404.
- [ ] Classificar causa real entre: (a) auth override drift, (b) route prefix changed, (c) router package refactor sem backward-compat, (d) mock incompleto.
- [ ] `grep -rn "@router.post.*buscar\\|@app.post.*buscar" backend/routes/ backend/main.py` — confirmar caminho real do endpoint em produção.
- [ ] Se bug real: rota foi removida / quebrou produção — abrir issue separada, marcar story `Status: Blocked` até decisão @po.
- [ ] Verificar se story vizinha (ex: CIG-BE-sse-reconnect-api) resolveu um subset — evitar duplicação.
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar grep de skip markers — deve voltar vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #6/30)
- **PR #383** (meta-story de triage) — merged/InReview

## Stories relacionadas no epic

- STORY-CIG-BE-sse-reconnect-api (mesmo módulo `routes/search/` refactor)
- STORY-CIG-BE-sse-last-event-id (mesmo módulo `routes/search/` refactor)
- STORY-CIG-BE-sse-redis-pool-refactor (mesmo módulo `routes.search_sse` refactor)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #6/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
