# STORY-CIG-BE-HTTPS-TIMEOUT — Backend Tests (3.11) — timeout em teste HTTPS real bloqueia matrix job

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** Ready
**Priority:** P0 — Matrix Blocker (causa fail-fast em 3.12 também)
**Effort:** M (3-6h — reproduzir + decidir estratégia)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `backend/tests/(a identificar — teste que usa requests/urllib3 contra HTTPS real)` roda em `tests.yml (Backend Tests 3.11)` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
[CI run 24512013523 (main pós STORY-CI-1) e 24539387474 (PR #372):
  Backend Tests (3.11) falha com single timeout em teste HTTPS real;
  pytest-timeout está instalado (STORY-CI-1 done) — timeout é acionado corretamente,
  mas o teste atinge 30s porque tenta fazer HTTPS contra host real.]

Evidência no log do matrix run: "+++ Timeout +++" do plugin pytest-timeout
(prova que o plugin funciona; o teste é que faz rede real).
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Algum teste em `backend/tests/` usa `requests.get(https://...)` ou `httpx.AsyncClient().get(https://...)` contra URL real de produção (ex.: PNCP, ComprasGov, BrasilAPI), sem mock. Em CI matrix 3.11 o handshake TLS demora > 30s (timeout do pyproject). Identificação: rodar `pytest --collect-only` + grep por `https://` em tests/ para localizar. Fix: (a) mockar com `responses` ou `respx`, (b) se é integration test legítimo, mover para `integration-external.yml` separado. **Sem skip.**

---

## Acceptance Criteria

- [ ] AC1: Teste específico identificado (grep por URLs HTTPS reais em `backend/tests/`); nome + path registrado em "Root Cause Analysis".
- [ ] AC2: Run do matrix `Backend Tests (3.11)` no PR desta story completa em < 10min sem single timeout em HTTPS real; job `Backend Tests (3.12)` deixa de ser `CANCELLED` e executa até o fim. Link para run ID registrado no Change Log.
- [ ] AC3: Causa raiz descrita (qual teste, qual URL, por que não estava mockado). Fix aplicado: (a) mock com `responses`/`respx`, OU (b) teste movido para novo workflow `integration-external.yml` não-gateado de PR, com justificativa técnica documentada.
- [ ] AC4: Cobertura backend não caiu vs. baseline memory/MEMORY.md (7656 pass / 292 pre-existing fail); se teste foi movido para external, `pytest --collect-only | wc -l` no workflow principal diminui apenas pelo conjunto movido (contagem documentada).
- [ ] AC5 (NEGATIVO): Nenhum `@pytest.mark.skip` ou `pytest.skip()` introduzido. `grep -rn "@pytest.mark.skip\|pytest.skip()" backend/tests/ | wc -l` igual à baseline pré-story (documentar contagem).

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- backend/tests/(a identificar — teste que usa requests/urllib3 contra HTTPS real)` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" backend/tests/(a identificar — teste que usa requests/urllib3 contra HTTPS real)` — deve voltar vazio.

---

## Root Cause Analysis

_(preenchido por @dev em Implement após confirmar causa)_

## File List (preditiva, a confirmar em Implement)

- `backend/tests/ (identificar teste específico)`
- `pyproject.toml (timeout config)`
- `.github/workflows/tests.yml (se separar em integration-external.yml)`

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)



## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (8/10) — Draft → Ready. P0 — Matrix Blocker. Execução prioritária na fase 0 do epic, antes das stories frontend. AC testáveis, escopo claro.
