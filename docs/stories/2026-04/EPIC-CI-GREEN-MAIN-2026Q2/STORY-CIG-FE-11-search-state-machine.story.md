# STORY-CIG-FE-11 — search-state-machine — banner "Atualizando dados em tempo real" removido sem atualizar teste

**Epic:** EPIC-CI-GREEN-MAIN-2026Q2
**Sprint:** 2026-Q2-S4
**Status:** InReview
**Priority:** P1 — Gate Blocker
**Effort:** S (1-3h)
**Agents:** @dev, @qa, @devops

---

## Contexto

Suíte `__tests__/search-state-machine.test.tsx` roda em `frontend-tests.yml` e falha com os erros abaixo, capturados localmente em 2026-04-16 com `.npmrc` legacy-peer-deps aplicado (cherry-pick de PR #372):

```
● CRIT-027 AC7: Live fetch banner lifecycle › SearchResults source guards live fetch banner with loading check

expect(received).toBeGreaterThan(expected)
Expected: > -1
Received: -1

  const bannerIndex = combined.indexOf("Atualizando dados em tempo real");
  expect(bannerIndex).toBeGreaterThan(-1);
  // __tests__/search-state-machine.test.tsx:165
```

**Hipótese inicial de causa raiz (a confirmar em Implement):** Banner "Atualizando dados em tempo real" foi removido ou texto alterado em SearchResults (CRIT-027 rollback?). Teste lê fonte do componente via fs — portanto mudança textual quebra. Verificar se remoção foi intencional (STORY-???) ou se é regressão de banner de live fetch. Se intencional, teste vira obsoleto (remove ou reescreve para novo banner).

---

## Acceptance Criteria

- [x] AC1: `npm test -- __tests__/search-state-machine.test.tsx` retorna exit code 0 localmente com `.npmrc` legacy-peer-deps aplicado. ✅ 6/6 pass em 2026-04-17.
- [ ] AC2: Última run do workflow `frontend-tests.yml` no PR desta story mostra a suíte com **0 failed / 0 errored**. Link para run ID registrado no Change Log.
- [x] AC3: Causa raiz descrita e corrigida em "Root Cause Analysis" — categoria (d) drift de assertion vs implementação: copy do banner mudou no redesign DEBT-FE-004 sem atualizar o teste.
- [x] AC4: Cobertura da suíte **não caiu** vs. último run verde conhecido. 6/6 tests mantidos — o teste continua validando o mesmo invariante (banner de live-fetch guardado por `!loading`).
- [x] AC5 (NEGATIVO — política conserto real): `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/search-state-machine.test.tsx` vazio ✅.

---

## Investigation Checklist (para @dev, Fase Implement)

- [ ] Rodar `npm test -- __tests__/search-state-machine.test.tsx` isolado e confirmar reprodução local do erro.
- [ ] Classificar causa real em uma das categorias: (a) import / module resolution, (b) mock incompleto, (c) snapshot, (d) drift de assertion vs implementação, (e) bug real de produção.
- [ ] Se (e) bug real: abrir issue separada, marcar story `Status: Blocked` até decisão de @po sobre prioridade do bugfix.
- [ ] Se (c) snapshot: executar diff-by-diff **antes** de `-u`; documentar diff em "Snapshot Diff Analysis".
- [ ] Checar se fix em suíte vizinha já resolveu esta (evitar trabalho duplicado).
- [ ] Validar que `coverage-summary.json` não regrediu.
- [ ] Rodar `grep -nE "\.(skip|only)\(|xit\b|xdescribe\b" __tests__/search-state-machine.test.tsx` — deve voltar vazio.

---

## Root Cause Analysis

**Categoria:** (d) drift de assertion vs implementação.

O banner de "live-fetch" foi consolidado no componente `SearchResultsBanners.tsx` pela DEBT-FE-004 (BannerStack). Nesse refactor, o copy mudou de "Atualizando dados em tempo real" para **"Buscando atualizações em segundo plano..."** — mais consistente com o tom de voz dos demais banners (info/warning) e menos alarmista. O componente **preservou** o guard `!loading && liveFetchInProgress && !liveFetchTimedOut` (linha 151 de `SearchResultsBanners.tsx`), que é o invariante real que o teste quer validar. O teste, porém, ainda lia a string antiga via fs e falhava com `bannerIndex === -1`.

Fix: atualizado o teste para buscar a nova copy "Buscando atualizações em segundo plano". O invariante de loading guard (`expect(nearbySource).toMatch(/loading/)`) permanece intacto. Nenhuma mudança de produção — implementação estava correta.

## File List (confirmada em Implement)

- `frontend/__tests__/search-state-machine.test.tsx` — linha 164: string atualizada para "Buscando atualizações em segundo plano", comentário DEBT-FE-004 adicionado.

---

## Dependências

- PR #372 merged em `main` (pré-requisito de TODAS as stories do epic)



## Change Log

- **2026-04-16** — @sm: story criada em `docs/epic-ci-green-stories` com erro real capturado via `npm test` local (jest-results.json). Hipótese inicial atribuída; causa raiz a validar em Implement.
- **2026-04-16** — @po: *validate-story-draft GO (8/10) — Draft → Ready. AC testáveis, escopo claro, dependências mapeadas. Causa raiz a confirmar em Implement conforme política zero-quarentena do epic.
- **2026-04-17** — @dev: fix aplicado — test atualizado para nova copy "Buscando atualizações em segundo plano" (DEBT-FE-004 BannerStack redesign). Loading guard invariante preservado. Suíte isolada: 6/6 pass. Full suite: zero regressão. TSC limpo. AC1/AC3/AC4/AC5 atendidos; AC2 aguarda CI do PR. Status Ready → InReview.
