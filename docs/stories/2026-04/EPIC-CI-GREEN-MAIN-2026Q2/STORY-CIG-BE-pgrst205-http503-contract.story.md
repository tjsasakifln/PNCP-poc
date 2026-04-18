# STORY-CIG-BE-pgrst205-http503-contract — Rotas `/organizations` retornam 404 em vez de 503 em PGRST205 — 9 testes assertion-drift

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Draft
**Priority:** P1 — Gate (regressão do contrato PGRST205/503)
**Effort:** M (3-8h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/test_organizations_pgrst205_guard.py` roda em `backend-tests.yml` e falha em **9 testes** do triage row #18/30. Causa raiz classificada como **assertion-drift / mock-drift**: as rotas `/organizations` retornam HTTP 404 em vez do esperado HTTP 503 quando o backend encontra erro PGRST205 (schema not reloaded). O middleware guard existe mas pode ter sido removido ou o router mudou de prefix.

CLAUDE.md CRIT-050 documenta o fluxo PGRST205: ao deploy de nova migration, backend deve enviar `NOTIFY pgrst, 'reload schema'` e smoke test verifica ausência de erros. Se PGRST205 ocorrer em runtime, o contrato definido é HTTP 503 (Service Unavailable) com retry-after, não 404.

**Arquivos principais afetados:**
- `backend/tests/test_organizations_pgrst205_guard.py` (9 testes)

**Hipótese inicial de causa raiz (a confirmar em Implement):** Middleware `pgrst205_guard` removido ou movido, OU prefix de `/organizations` mudou (possível mesmo padrão de STORY-CIG-BE-buscar-route-404 #6). Validar com `grep -rn "PGRST205\\|pgrst205_guard\\|503.*PGRST\\|@router.*organizations" backend/`.

---

## Acceptance Criteria

- [ ] AC1: `pytest backend/tests/test_organizations_pgrst205_guard.py -v` retorna exit code 0 localmente (9/9 PASS).
- [ ] AC2: Última run de `backend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link no Change Log.
- [ ] AC3: Causa raiz descrita em "Root Cause Analysis". Distinguir (a) route-drift puro vs (b) middleware guard removido (prod-bug).
- [ ] AC4: Cobertura backend **não caiu**. Threshold 70% mantido.
- [ ] AC5 (NEGATIVO): grep por skip markers vazio nos arquivos tocados.

---

## Investigation Checklist (para @dev, fase Implement)

- [ ] Rodar `pytest backend/tests/test_organizations_pgrst205_guard.py -v` isolado.
- [ ] `grep -rn "PGRST205\\|pgrst205_guard\\|@router.*organizations" backend/`.
- [ ] Verificar se migration CI auto-apply (CRIT-050) continua enviando `NOTIFY pgrst, 'reload schema'` — se sim, PGRST205 em runtime é raro mas o contrato 503 deve continuar válido.
- [ ] Se middleware removido: restaurar ou reimplementar.
- [ ] Validar cobertura não regrediu.
- [ ] Grep de skip markers vazio.

---

## Dependências

- **Epic pai:** EPIC-CI-GREEN-MAIN-2026Q2
- **Meta-story pai:** STORY-CIG-BACKEND-SWEEP (PR #383, triage row #18/30)

## Stories relacionadas no epic

- STORY-CIG-BE-buscar-route-404 (#6 — mesmo padrão de route drift)
- STORY-CIG-BE-story-drift-billing-webhooks-correlation (#29 — também toca `test_organizations`)

---

## Change Log

- **2026-04-18** — @sm: story criada a partir da triage row #18/30 (handoff PR #383). Status Draft, aguarda `@po *validate-story-draft`.
