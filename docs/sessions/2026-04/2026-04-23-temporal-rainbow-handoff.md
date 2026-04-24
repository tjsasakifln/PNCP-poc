# Session Handoff — Temporal-Rainbow (Day 3 zippy-star continuation, max-ROI)

**Date:** 2026-04-23/24 BRT
**Codename:** temporal-rainbow
**Plan file:** `~/.claude/plans/mission-maximizar-roi-temporal-rainbow.md`
**Branch base:** `docs/session-2026-04-22-zippy-star`
**Predecessor:** temporal-dongarra (encerrada 2026-04-23 13:20Z com admin merge #495 revert #470)
**Modelo:** Claude Opus 4.7 (1M context)
**Modo:** Plan Mode → ExitPlanMode → Opção 1 (Unblock Ship)

---

## TL;DR

Sessão executou Opção 1 do plano (Unblock Ship). Detectou falha raiz em main (1 test regex desatualizada após refactor STORY-413) bloqueando merge train inteiro. Fix shipado em PR #496 + merge train avançou 3 stories Selenium. **4 PRs mergeados em main** (#496, #494, #491, #493) + **3 PRs ainda em CI** (#490, #483, #492) ao encerrar. Prod restaurada ("compute limits" resolvido pelo user durante sessão). `api.smartlic.tech/health` = 200.

| Frente | Status | Output |
|--------|--------|--------|
| PR #496 fix CI regex test_task_registry_story413 | ✅ MERGED `e36864f1` | Desbloqueia Backend Tests gate após STORY-413 refactor |
| PR #494 SAB-015 /ajuda search | ✅ MERGED `a0390b95` | input type=search + termo empty state |
| PR #491 SEO-479 metadata overlong | ✅ MERGED `41058fd7` | Title/desc ≤60/≤160 em /sobre, /fornecedores, /planos, /features + test sync |
| PR #493 SEO-480 blog JSON-LD | ✅ MERGED `36f796e4` | Blog schema + `<article>` wrappers |
| PR #492 SAB-014 trial badge | 🔴 OPEN — BT flaky | Test sync pushado; flaky `test_decrypt_tampered_ciphertext` oauth base64 6.25% false-pass |
| PR #490 session docs zippy-star Day 1 | 🟡 OPEN — CI rodando | Update-branch cycle depois de cada merge |
| PR #483 BTS Wave G drift sweep | 🟡 OPEN — CI rodando | Rebase já feito ontem; reruns update-branch |
| PR #478, #476, #420, #418 | ⏸ OPEN | Não tocados nesta sessão |
| Prod api.smartlic.tech | ✅ UP | User resolveu compute limits; `/health` 200 |

---

## 1. Entregáveis durables

### Merges em main (4)
- `e36864f1` **#496** `fix(tests): update regex to match refactored TaskRegistrationError message`
- `a0390b95` **#494** `feat(sab-015): input type=search + termo em empty state /ajuda`
- `41058fd7` **#491** `fix(seo-479): meta title/description ≤60/≤160 chars em 4 páginas` + `test(sobre): update metadata title assertion to new SEO-479 value`
- `36f796e4` **#493** `feat(seo-480): Blog JSON-LD + article wrappers em /blog`

### Commits nas branches PR (test sync drift)
- `89a47894` (fix/seo-479-metadata-overlong) — regex `toContain('Sobre o SmartLic')` → `toContain('Metodologia')`
- `a28ff756` (feat/sab-014-planos-trial-badge) — CTA `/Começar a filtrar oportunidades/` → `/Começar trial grátis/` em 2 suites

### Branch nova
- `fix/ci-main-task-registry-regex` (deletada pós-merge) — 1 commit `15e971df`

---

## 2. Descobertas empíricas críticas

### 2.1 Backend Tests bloqueando main há 6h — refactor STORY-413 sem test sync

CI Backend Tests (PR Gate) falhando em main desde `74a909fd` (2026-04-23 15:22Z). 1 teste:

```
FAILED tests/test_task_registry_story413.py::test_register_rejects_sync_function_when_is_coroutine_true
AssertionError: Regex pattern did not match.
  Expected regex: 'not an async function'
  Actual message: "is_coroutine=True but start_fn is not a coroutine function"
```

**Root cause:** commit `1900e6ff` (STORY-413 fail-fast, 2026-04-15) refatorou `task_registry.py:register()` — moveu check `iscoroutinefunction` pro topo + renomeou "async function" → "coroutine function". **Test regex não foi atualizado no mesmo PR.** Test passou 9 dias em CI porque `docs/session-2026-04-22-zippy-star` branch tinha versão antiga do registry; quando main mergeou Day 2 session branch (f8955dcd), carregou o refactor de `task_registry.py` mas manteve test regex antigo.

**Fix shipado (#496):** regex → `match="is_coroutine=True"` — invariante semântico do path testado. Resistente a futuros renames cosméticos.

### 2.2 Test-code drift nos PRs abertos — 2 fixes adicionais ✅

Ambos PRs da Selenium audit anterior falhavam FT **nos próprios testes** porque stories mudaram strings visíveis mas test assertions não foram sincronizadas:

- **#491 SEO-479** — `metadata.title` em `/sobre` mudou para "Metodologia e Critérios de Avaliação" mas `sobre-page.test.tsx:174` esperava "Sobre o SmartLic"
- **#492 SAB-014** — CTA anonymous em `/planos` mudou para "Começar trial grátis de 14 dias" mas `PlanosPage.test.tsx:290,305` e `planos-page.test.tsx:464` esperavam "Começar a filtrar oportunidades"

Ambos fixados com regex match invariante ao sufixo de frase — robustos a ajustes futuros dentro do padrão.

**Lição (nova memory):** Selenium audit + story handoff sem dev owner resultaram em code changes sem test updates pareados. Story template deveria exigir `test plan` section + validation local pre-push.

### 2.3 Flaky test_decrypt_tampered_ciphertext (oauth base64)

CI #492 retornou BT FAILURE pós-fix do test sync: `test_oauth_story224.py::TestAC13TokenDecryption::test_decrypt_raises_error_on_tampered_ciphertext — DID NOT RAISE`.

Memória `feedback_jwt_base64url_flaky_test` diz: **signature tamper via single-char flip tem 6.25% false-pass** (base64 alphabet has 64 chars; random last char flip pode resultar em valid decrypt ~1/16 dos casos).

Este teste **não foi alterado por #492** — é flaky pré-existente. Rerun CI é estratégia padrão. `gh run rerun --failed` bloqueou ("workflow file may be broken"); novo BT run triggerou via update-branch.

### 2.4 Railway prod "down" era compute limit, não routing

Bootstrap inicial viu `api.smartlic.tech/health` = 404. User esclareceu durante sessão: **"era compute limits, ja removi"**. Account cap atingido → Railway suspended deploy. Resolução: user ajustou limits no dashboard.

Distinção importante (nova memory): Railway retorna idêntico 404 "Application not found" para (a) rootDir bug, (b) deploy crash loop, (c) **compute/billing limit atingido**, (d) domain unassigned. Bootstrap diagnostic não distingue — exige user confirmação dashboard.

### 2.5 Strict protection + merge train pattern confirmado

Main branch `strict:true` per memory `reference_branch_protection_strict` — cada merge força subsequentes PRs a `update-branch` cycle. Confirmado empiricamente:

- #491 required checks verde em commit ancestor de main → mss=BEHIND pós-#494 merge
- Preciso trigger `gh api -X PUT /repos/:owner/:repo/pulls/:n/update-branch` + aguardar novo CI (~12min)
- Cada merge subsequente repete ciclo para PRs ainda abertos

Batches 2-3 per memory `feedback_concurrent_jobs_cap` evita saturar GH Actions concurrency cap (20 simultâneos).

### 2.6 Investigação custo Railway self-hosted runners

User questionou custo self-hosted em Railway Abril 2026 (gargalo = wait runners GH Hosted).

**Conclusão:** Não vale.
- Repo é público → GH Hosted **grátis** atualmente
- Railway self-host 2vCPU+4GB always-on: **$80/mês compute + $55/mês GH platform fee (Mar 2026+) = $135/mês per runner**
- Burst 3 runners: **~$405/mês**
- BuildJet alternativa 4-core: ~$36/mês (2-4× speed)
- **Gargalo real é queue wait, não custo.** Otimização workflow (cache `actions/setup-node`, `actions/cache` pip, skip CodeQL em docs-only, fail-fast matrix) = 30-40% speedup grátis.

Deferred para story dedicada (STORY-CI-OPTIMIZATION-001 ou similar).

---

## 3. Decisões técnicas importantes

### 3.1 Regex test `is_coroutine=True` (invariante semântico vs frase exata)

Opções consideradas:
1. `match="not a coroutine function"` (nova mensagem exata — frágil se renomearem de novo)
2. `match="is_coroutine=True"` (semântico, captura intent do path)
3. `match="coroutine"` (loose demais — false-match em outras error messages)

Escolhi **(2)** — resistente a renomeações cosméticas futuras async↔coroutine.

### 3.2 Flaky oauth test — NÃO escalar fix agora

Test flaky `test_decrypt_tampered_ciphertext` é **fora escopo #492**. Fix verdadeiro exige re-sign ciphertext ou full-char replacement (ver memory). Adiar para story dedicada evita scope creep em PR de feature.

### 3.3 Railway self-host — "não" baseado em dados

Análise rigorosa com pricing verificado (WebSearch Abr/2026). Recomendação: optimize workflows primeiro, considerar BuildJet se gargalo persiste. Railway self-host reservar para workload >100k min/mês OU hardware custom.

### 3.4 EXT-001..007 + epic + research (untracked) — NÃO commitar nesta sessão

Opção 2 do plano foi deferida a pedido implícito do user (escolheu Opção 1). 10 untracked files permanecem no working tree do session branch para sessão dedicada:
- `docs/research/2026-04-23-crawling-licitacoes-arquitetura.md`
- `docs/research/2026-04-23-fontes-externas-licitacoes.md`
- `docs/stories/epic-ext-001-fontes-externas.md`
- `docs/stories/EXT-001..007*.story.md` (7 files)

Também `.claude/hooks/squads-briefing.cjs` modified (WIP anterior).

**Próxima sessão deve decidir:** commit untracked + abrir epic EXECUTION yaml, OU separar em branch dedicada `docs/epic-ext-001`.

---

## 4. Estado final dos PRs

| PR | Head | Estado | CI | Merge state | Próxima ação |
|----|------|--------|-----|-----|-------------|
| #496 | fix/ci-main-task-registry-regex | ✅ MERGED | green | — | — |
| #494 | feat/sab-015-ajuda-search | ✅ MERGED | green | — | — |
| #491 | fix/seo-479-metadata-overlong | ✅ MERGED | green | — | — |
| #493 | feat/seo-480-blog-structured-data | ✅ MERGED | green | — | — |
| #490 | docs/session-2026-04-22-zippy-star | 🟡 OPEN | BT in_progress | BLOCKED | Aguardar CI + merge |
| #483 | fix/wave-g-drift-cluster-sweep | 🟡 OPEN | BT in_progress | BLOCKED | Aguardar CI + merge |
| #492 | feat/sab-014-planos-trial-badge | 🔴 OPEN | BT flaky oauth | BLOCKED | Rerun CI — flaky base64 |
| #478 | feat/seo-005-gsc-dashboard | ⏸ OPEN | não tocado | — | — |
| #476 | docs/session-2026-04-22-ocean-compass-research | ⏸ OPEN | não tocado | — | — |
| #420, #418 | Dependabot | ⏸ OPEN | não tocado | — | — |

---

## 5. Próximas ações recomendadas (ordem ROI)

### P0 — Completar merge train (próxima sessão primeiro passo)

1. **#490 + #483 + #492** — aguardar CI pós update-branch; merger em cadeia
2. **#492 rerun flaky** — se BT failure persistir, 1x rerun normalmente resolve
3. Update-branch entre merges (strict protection)

### P1 — SEO/CRO shipping

4. **#478 SEO-005 GSC dashboard** — shippar se CI green (SEO analytics inbound)
5. **#476 ocean-compass research** — docs merge trivial
6. **#420, #418 Dependabot** — auto-merge patches (ver workflow `Dependabot Auto-merge`)

### P1 — Débito estrutural identificado

7. **STORY: test drift prevention** — Selenium audit produziu 2 PRs com test-code drift (#491, #492). Adicionar ACs "atualizar testes de assertion na mesma PR" em story template ou CI gate.
8. **STORY: CI optimization** — cache setup-node/pip, skip CodeQL em docs-only, fail-fast matrix, avaliar BuildJet se gargalo persistir.
9. **STORY: flaky test_decrypt_tampered_ciphertext** — fix via re-sign ou full-char replacement (EPIC-TD-2026Q2 quality)
10. **STORY-DEBT-CI-migration-dessync** — ainda aberto; `@data-engineer` audit por migration (herdado de temporal-dongarra)

### P2 — Escopo novo diferido

11. **EPIC-EXT-001 fontes externas** — 10 files untracked no session branch. Decisão: commit + primeira story implement OU branch dedicada. Sprint 1 = EXT-001 schema.

### P2 — Plan zippy-star 15-day continuation

12. **STORY-OPS-001 trial cohort interviews** (founder-execution)
13. **Phase 4 funnel baseline doc** (deferred day 2)
14. **STORY-5.14 bundle reduction 200-300KB** (backlog)
15. **Web Vitals RUM analysis**

---

## 6. Métricas desta sessão

| Métrica | Valor |
|---------|------:|
| PRs mergeados em main | **4** (#496, #494, #491, #493) |
| PRs com fix test drift durante merge train | **2** (#491 sobre-page, #492 planos CTA) |
| Commits diretos em session branch | **0** (session branch apenas checkout/stash) |
| Commits em branches PR (test sync) | **3** (15e971df, 89a47894, a28ff756) |
| Linhas de código alteradas | **~7** (3 test regex updates) |
| Incidents P0 resolvidos pelo user | **1** (prod compute limit) |
| Descobertas empíricas novas | **3** (STORY-413 refactor gap, test drift pattern, Railway cost analysis) |
| Memories candidates para salvar | **3** (ver seção 7) |
| Workflows CI investigados | Backend Tests, Frontend Tests, Deploy to Production |
| Branches criadas | 1 (fix/ci-main-task-registry-regex — deletada pós-merge) |

---

## 7. Memórias candidatas para salvar

1. **`reference_railway_404_triage_2026_04_24`** — `api.smartlic.tech` 404 externo tem 4 causas distintas não discrimináveis via curl: rootDir bug, compute limit, deploy crash, domain unassigned. Sempre perguntar user antes de escalar.

2. **`feedback_test_regex_invariant_semantic`** — Quando test regex para error message, prefira match do path semântico (flag name, invariant do contexto) sobre frase exata. Ex: `"is_coroutine=True"` > `"not an async function"`. Resistente a renames cosméticos.

3. **`project_railway_runners_cost_2026_04`** — Railway self-hosted runners custam $135/mês vs $0 GH Hosted em repo público. GH platform fee $0.002/min (Mar/2026+) aplica em ALL self-hosted. Gargalo real = queue, não custo. Optimize first: cache, skip CodeQL docs-only, BuildJet alternative.

---

## 8. Notas para próximo operador

1. **PRIMEIRO:** verificar merge train pending:
   ```bash
   for pr in 490 483 492; do gh pr view $pr --json mergeStateStatus,statusCheckRollup; done
   ```
   Se CLEAN/UNSTABLE: `gh pr merge $pr --merge --delete-branch`. Após cada: `gh api -X PUT "/repos/:o/:r/pulls/$next/update-branch"` para próximo BEHIND.

2. **#492 BT flaky** — rerun primeiro antes de debug. `test_decrypt_tampered_ciphertext` é pré-existente, não causado pelo PR.

3. **10 files untracked EXT-001 epic** — preservados no working tree session branch. Sessão dedicada decidir: commit inline OU branch separada. Não perder research.

4. **Prod UP** — `curl -sf https://api.smartlic.tech/health` confirmar 200 antes de mais merges. Compute limit pode reaparecer se carga subir.

5. **Deploy workflow** — `74a909fd fix(deploy): remove working-directory` foi committed direto em main pelo user com Sonnet 4.6. Verificar Backend Tests pós-deploy — não vimos ainda se o fix é robusto.

6. **DEBT-CI-migration-dessync** (temporal-dongarra legacy) — continua P1. `@data-engineer` audit migration-by-migration. Blocks qualquer re-ship #470.

7. **Chain merges dispara deploys** — monitor Railway billing/logs pós cada merge. Memory `reference_railway_404_triage_2026_04_24` útil se reaparecer 404.

---

## 9. Encerramento

**Decisão do user (explícita):** "atualize o handoff e encerre."

Sessão temporal-rainbow executou Opção 1 (Unblock Ship) do plano. 4 merges em main = SEO-479, SEO-480, SAB-015 + fix CI raiz. 3 PRs ainda aguardando CI pós update-branch cycles (#490, #483, #492). Prod UP após user resolver compute limits. 10 files untracked EXT-001 epic preservados no session branch para sessão dedicada.

**Baseline para próxima sessão:**
- CI gate main desbloqueado
- Merge train pattern consolidado (update-branch cycle + batches 2-3)
- Prod stable
- 3 lições novas para memory

---

**Sessão temporal-rainbow encerrada.** 4 merges shippados, 3 PRs em CI trail, 0 incidents novos, 3 débitos técnicos mapeados, memories prontas.
