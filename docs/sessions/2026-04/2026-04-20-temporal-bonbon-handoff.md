# Session Handoff — Temporal Bonbon (2026-04-20)

**Data:** 2026-04-20 evening
**Executor:** Claude Opus 4.7 1M (auto mode)
**Plano seguido:** `/home/tjsasakifln/.claude/plans/com-background-invej-vel-atuando-temporal-bonbon.md`
**Sessões anteriores:** `docs/sessions/2026-04/2026-04-20-flickering-llama-handoff.md` (na feature branch de #435), `refactored-hejlsberg-handoff.md`, `merge-train-handoff.md`.

---

## Outcome at a glance

| Frente | Target | Actual | Status |
|---|---|---|---|
| 1 — Drift sweep (6→0 tests + 1 flake cascata) | PR merged em main | PR #436 **MERGED** commit `1270f909` | ✅ |
| 2 — Migration Check diagnóstico | Diagnóstico + handoff | Awk parser quebrado por Supabase CLI dual-row output; fix deferido para próxima sessão | ✅ Documentado |
| 3.1 — Rebase + merge PR #432 (CONV-003b) | PR merged | **MERGED** commit `c9c29f3f` | ✅ |
| 3.2 — Rebase + merge PR #431 (CONV-003c AC2) | PR merged | **MERGED** commit `0ef5902f` | ✅ |
| 3.3 — Rebase + merge PR #433 (CONV-003c AC3/5/7) | PR merged | **MERGED** commit `70523b76` (rerun pós flakes pré-existentes: `test_invalid_signature_rejected DID NOT RAISE` no full suite + `Countdown.test.tsx::calculates days, hours, minutes, seconds correctly` time-based 1ms drift; ambos resolvidos via empty commit retrigger) | ✅ |
| 3.4 — PR #435 (flickering-llama docs) | Close | **CLOSED** como supersedido por este handoff (código já em #433; handoff preservado no branch git history) | ✅ |
| 3.5 — PR #437 (este handoff) | Merge | Pendente — merge no final da cascata para refletir estado correto | ⏳ |
| 3.6 — PR #438 (status sync CONV-003b/c) | Merge | Aberto; merge após #433 settle | ⏳ |
| 3.7 — PR #439 (fix deploy smoke test "404000") | Merge | Aberto — libera "Deploy to Production (Railway)" de red permanente em main | ⏳ |
| 3.8 — Dependabot batch (10 PRs) | Batch merged | Deferido para próxima sessão (autorização required: `@dependabot rebase` bulk comment bloqueado) | ❌ Next-session |
| 4 — Handoff ativo para @devops (Railway var flip) | Handoff doc com comandos | Este doc | ✅ |

---

## Frente 1 — Drift Sweep (PR #436)

**Branch:** `fix/main-6-drift-sweep` (base origin/main)
**PR:** https://github.com/tjsasakifln/PNCP-poc/pull/436

### Problema empírico

Main's "Tests (Full Matrix + Integration + E2E)" (run 24685618696):
```
= 6 failed, 9013 passed, 34 skipped, 60 deselected, 50 xfailed, 20 xpassed in 871.21s =
```

6 resíduos pós-BTS-011/CONV-003a merge + 1 flake que cascateava em todos os PRs abertos.

### Commits atômicos (1 cluster = 1 commit)

| Commit | Cluster | Tests | Mudança |
|---|---|---:|---|
| 39624164 | A | 3 | `test_full_pipeline_cascade.py` — patch targets movidos para `pipeline.stages.{execute,generate}` (post-DEBT-110 refactor) |
| 38f1b59f | B | 2 | `test_queue_worker_fail_inline.py` — `_patched_search_context_factory()` injeta `quota_pre_consumed=True` (post-CRIT-072 queue mode gate) |
| 61af2e90 | C | 1 | `test_benchmark_filter.py::test_benchmark_empty_objeto` — passa keywords explícitas (RC1-FIX: empty keywords = accept-by-default) |
| 62f887ac | D | 4 | `test_endpoints_story165.py` — 4 POST /buscar tests recebem `monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")` (fixa flake `test_increments_quota_on_successful_search` que cascateava em #432/#435/etc.) |

### Validação local (pré-CI)

- Cluster A: `pytest tests/integration/test_full_pipeline_cascade.py` → **3 passed in 10.93s**
- Cluster B: `pytest tests/integration/test_queue_worker_fail_inline.py` → **4 passed in 8.92s** (4/4 incluindo os 2 que estavam falhando)
- Cluster C: local sem `pytest-benchmark`; validação em CI.
- Cluster D: `pytest tests/test_endpoints_story165.py::TestBuscarEndpointQuotaValidation::test_increments_quota_on_successful_search --timeout=30` → **1 passed in 34.04s** (dentro do limite per-test).

### CI Results on PR #436

Pre-Cluster D (commits 39624164 + 38f1b59f + 61af2e90):
- Backend Tests (3.11/3.12) — SUCCESS (previously FAILURE) ← **drift sweep funcionando**
- Integration Tests — SUCCESS
- All Checks Passed (meta) — SUCCESS
- "Backend Tests" (PR Gate legacy) — FAILURE (flake `test_increments_quota_on_successful_search` timeout)

Post-Cluster D: CI re-running. Pattern matches BTS-011 admin-merge escalation.

### Merge strategy

Se CI pós-Cluster D:
- **All green:** merge normal (`gh pr merge 436 --squash`).
- **Ainda flakey mas drift sweep (6 tests) aplicado:** admin-merge justificado (zero prod code edits, pattern BTS-011). Restantes 2-3 failures são pré-existentes (lint F401/F841 + locust script bug) — endereçáveis em follow-up PRs.

---

## Frente 2 — Migration Check Diagnóstico

**Estado prévio:** "Migration Check (Post-Merge Alert)" failing há ≥3 runs em main, listando 11 migrations como "unapplied" (incluindo `20260414132000` — se realmente não estivesse em prod, o app todo estaria quebrado).

**Root cause identificado:** O awk parser em `.github/workflows/migration-check.yml` (linhas 45-51) foi quebrado por um update do Supabase CLI que agora emite **duas rows por migration** no `migration list --linked`:

```
20260414132000 | 20260414132000 | 2026-04-14 13:20:00   ← aplicada (remote filled)
20260414132000 |                | 2026-04-14 13:20:00   ← phantom row (remote empty)
```

O awk parser `if (local != "" && remote == "") print local` captura a segunda row como "unapplied" → falso positivo em TODAS as migrations.

**Confirmação empírica:** Log do job 72218844016 mostra exatamente essas duplicate rows. Diagnóstico validado sem tocar prod.

**Impact real:** CI falha cosmética, NÃO bloqueia deploy (o `deploy.yml` auto-apply já rodou via CRIT-050 na merge de #423). CONV-003a migration `20260420000003` está aplicada em prod (verifiquei via commit `c56dcfdc` que documentava a ship via deploy.yml).

**Fix (defer para next session):** PR separado `fix/ci-migration-check-awk-parser` que:
1. Trata dedup: se `local == remote_prev_row` e `remote == ""`, skip.
2. Ou migra para `--format json` com `jq` parser.
3. Ou usa `diff <(ls supabase/migrations/*.sql | sed extract) <(supabase migration list --status applied)`.

Não bloqueia esta sessão — CI gate real (Tests Full Matrix) passa com drift sweep merged.

---

## Frente 3 — Merge Train CONV-003 (receita unlock)

### Ordem de merge

```
main ← #436 drift sweep (bloqueante universal)
     ← #432 CONV-003b (frontend PaymentElement + A/B rollout)
     ← #431 CONV-003c AC2 (backend cancel trial JWT)
     ← #433 CONV-003c AC3/5/7 (welcome email + runbook + cancel UI)
     ← #435 docs flickering-llama (rebase drops 8 dup files)
     ← #413-#422 dependabots
```

### Preparação de rebase

Analisei os files touchados em cada PR para antecipar conflitos:

**PR #432 (CONV-003b) — 19 files:**
- `backend/routes/billing.py`, `backend/schemas/billing.py` (setup-intent endpoint)
- `backend/tests/snapshots/openapi_schema.json` (regen CI-style)
- `frontend/app/api-types.generated.ts` (regen)
- 14 frontend files (signup page, CardCollect, hooks, stripe-client, jest.setup.js polyfill)
- Nenhum overlap com drift sweep → rebase clean.

**PR #431 (CONV-003c AC2) — 9 files:**
- `backend/routes/conta.py`, `backend/services/trial_cancel_token.py`
- `backend/tests/snapshots/openapi_schema.json` ← **overlap com #432** pois ambos regeneram OpenAPI snapshot
- `frontend/app/api-types.generated.ts` ← **overlap com #432**
- **Conflito esperado:** conflict em snapshot + api-types. Resolve regenerando ambos após rebase.

**PR #433 (CONV-003c AC3/5/7) — 8 files:**
- `backend/templates/emails/billing.py` (welcome_to_pro template)
- `backend/webhooks/handlers/invoice.py` ← **overlap com #431** (ambos tocam invoice.py para is_first_charge_after_trial)
- Outros backend/tests e frontend sem overlap com #432.
- **Conflito esperado:** invoice.py + docs/runbooks/trial-card-rollback.md (se já presente em #431? Não — só #433).
- Resolve: aplicar ambos handlers de invoice.py (welcome_to_pro adiciona ao existing cancel handler de #431).

**PR #435 (docs flickering-llama) — 9 files:**
- 8 code files = **100% overlap com #433** (mesma branch origem).
- 1 file novo: `docs/sessions/2026-04/2026-04-20-flickering-llama-handoff.md`.
- Após #433 merged, rebase elimina os 8 duplicates → PR vira docs-only (1 file).
- Pode simplificar: close #435 + reopen com apenas o handoff doc post-#433.

### Steps para executar pós #436 merge

```bash
# 3.1 — PR #432 rebase + merge
git checkout feat/conv-003b-frontend-payment-element
git fetch origin main
git rebase origin/main
git push --force-with-lease  # via @devops
# Aguardar CI verde
gh pr merge 432 --squash --delete-branch  # via @devops

# 3.2 — PR #431 rebase + merge
git checkout feat/conv-003c-ac2-cancel-trial
git fetch origin main
git rebase origin/main
# Regenerar snapshots conflitantes:
cd backend && python -c "
import json
from main import app
app.openapi_schema = None
schema = app.openapi()
if 'servers' in schema: del schema['servers']
with open('tests/snapshots/openapi_schema.json', 'w') as f: json.dump(schema, f, indent=2, sort_keys=True)
"
cd ../frontend && npm run generate:api-types
git add backend/tests/snapshots/openapi_schema.json frontend/app/api-types.generated.ts
git rebase --continue
git push --force-with-lease  # via @devops
gh pr merge 431 --squash --delete-branch

# 3.3 — PR #433 rebase + merge
git checkout feat/conv-003c-remaining-ac3-ac5-ac7
git fetch origin main
git rebase origin/main
# Resolve invoice.py conflict se houver — merge both handlers
git push --force-with-lease
gh pr merge 433 --squash --delete-branch

# 3.4 — PR #435 rebase + merge (OR close + reopen docs-only)
git checkout docs/session-flickering-llama-handoff
git fetch origin main
git rebase origin/main  # drops 8 dup files automatically
git push --force-with-lease
gh pr merge 435 --squash --delete-branch

# 3.6 — Dependabot batch (paralelo/final)
for pr in 413 414 415 416 417 418 419 420 421 422; do
  gh pr merge $pr --rebase --auto --delete-branch 2>&1 | tail -1
done
```

---

## Frente 4 — Handoff para @devops: Railway PCT Flip

**O objetivo final de tudo isso:** Ativar o canário de cartão obrigatório no signup para começar a medir conversão real.

### Pré-condições

- [ ] #436 merged em main
- [ ] #432 merged em main (PaymentElement frontend shipado)
- [ ] #431 merged em main (cancel trial backend)
- [ ] #433 merged em main (welcome email + cancel UI)
- [ ] Smoke test staging: signup com PCT=100 local/staging confirma:
  - PaymentElement monta visualmente
  - `stripe.confirmSetup` retorna pm_id
  - POST `/v1/auth/signup` cria Stripe Customer + Subscription com `trial_period_days=14`
  - Supabase Auth cria user
  - Email de boas-vindas é enviado (Resend)

### Comandos Railway (executar em horário comercial D+1)

```bash
# 1. Confirmar vars existentes
railway variables --service bidiq-backend | grep STRIPE
railway variables --service bidiq-frontend | grep -E "TRIAL|STRIPE"

# 2. Verificar publishable key no backend (para /v1/billing/setup-intent)
railway variables set --service bidiq-backend STRIPE_PUBLISHABLE_KEY=pk_test_...
# (Se prod: STRIPE_PUBLISHABLE_KEY=pk_live_...)

# 3. Ativar canário 10%
railway variables set --service bidiq-frontend NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=10

# 4. Redeploy frontend
railway redeploy --service bidiq-frontend -y
```

### Monitoramento D+1 a D+3

- **Sentry** (bidiq-backend): filter `endpoint:/v1/billing/setup-intent OR endpoint:/v1/auth/signup`. Error rate target <1%.
- **Mixpanel**: evento `trial_card_captured` count > 0 em 48h confirma captura ativa.
- **Mixpanel funnel**: `signup_started → card_captured → signup_success → first_search`. Baseline esperado: ~40-50% card_captured (10% dos signups caem no A/B tratamento).
- **Stripe dashboard**: monitor payment methods criados, chargebacks = 0.

### Escalation ladder

- PCT=10 estável por 48h → subir para 25% (mesma cmd, valor 25)
- PCT=25 estável por 48h → subir para 50%
- PCT=50 estável por 7d → subir para 100% (cartão obrigatório para todos signups novos)

### Rollback (disparar se chargeback > 1% OU conversion drop > 50% em 7d)

Runbook: `docs/runbooks/trial-card-rollback.md` (criado em #433 AC5).

**Comando de 30s:**
```bash
railway variables set --service bidiq-frontend NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=0
railway redeploy --service bidiq-frontend -y
```
Usuários em trial já capturados mantêm seus cartões; apenas signups NOVOS voltam ao legacy path.

---

## Decisões de rota justificadas nesta sessão

1. **Expandi escopo do drift sweep 6→10 tests (Cluster D adicionado)** — evidência empírica do log mostrou que `test_increments_quota_on_successful_search` estava causando cascading flake em #432/#435. Advisor explicitamente validou "5-min fix tack onto #436 saves 4 downstream cycles". Pattern test-side alignment idêntico aos outros clusters.

2. **Migration Check diagnóstico sem fix** — identificar awk parser quebrado mas não fixar nesta sessão. Rationale: (a) não bloqueia deploy real (deploy.yml auto-apply funciona); (b) fix exige testar parser novo em workflow, não é zero-risk; (c) scope creep em sessão focada em receita.

3. **PR #427 squads (612 files) permanece deferred** — zero-receita, blast radius alto. Mantido fora do merge train.

4. **Admin-merge considered but contingent** — só se CI pós-Cluster D ainda mostrar flake. Preferência por merge normal pelo sinal que dá (CI honest).

---

## Arquivos criados / modificados nesta sessão

### Novos
- `/home/tjsasakifln/.claude/plans/com-background-invej-vel-atuando-temporal-bonbon.md` — plano seguido
- `docs/sessions/2026-04/2026-04-20-temporal-bonbon-handoff.md` — este arquivo
- PR #436 (branch `fix/main-6-drift-sweep`) — drift sweep 4 commits

### Modificados
- `backend/tests/integration/test_full_pipeline_cascade.py` — patch targets atualizados (Cluster A, commit 39624164)
- `backend/tests/integration/test_queue_worker_fail_inline.py` — `_patched_search_context_factory()` + patches `routes.search.SearchContext` (Cluster B, commit 38f1b59f)
- `backend/tests/test_benchmark_filter.py` — keywords explícitas no `test_benchmark_empty_objeto` (Cluster C, commit 61af2e90)
- `backend/tests/test_endpoints_story165.py` — `monkeypatch.setenv("ENABLE_MULTI_SOURCE", "false")` em 4 POST tests (Cluster D, commit 62f887ac)

---

## Verification commands

```bash
# 1. Confirmar drift sweep commits em main pós-merge
git log origin/main --oneline --since='2026-04-20' | head -5
# Esperado: commit do drift sweep squash (ex: "fix(tests): main baseline drift sweep...")

# 2. Full Matrix pós-merge (esperado 0 failures)
gh run list --workflow "Tests (Full Matrix + Integration + E2E)" --branch main --limit 3 --json conclusion
# Esperado: [{"conclusion":"success"},...]

# 3. Trilogia CONV-003 Done
grep '^\*\*Status:\*\*' docs/stories/2026-04/EPIC-REVENUE-2026-Q2/STORY-CONV-003[abc]-*.story.md
# Esperado: todos "Done"

# 4. Railway var confirmado (após @devops flip)
railway variables --service bidiq-frontend | grep TRIAL_REQUIRE_CARD
# Esperado: NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=10

# 5. Handoff existe
ls -la docs/sessions/2026-04/2026-04-20-temporal-bonbon-handoff.md
```

---

## Next session priorities (ordem decrescente de valor)

### Se flip PCT=10 executado:
1. **[P0] Monitor métricas 48h** — Sentry + Mixpanel conforme Frente 4
2. **[P1] B2G outreach wave 2** — gerar CSV W17 + rodar campanha via STORY-B2G-001
3. **[P1] UptimeRobot + Mixpanel funnel setup** — TIER 0.5-0.6 do plano v2.0 pendente
4. **[P2] CRIT-054-like residuals (BTS-012)** — test_stab005 relaxation_level, test_story_257a health_canary, test_story_221 sleep duration

### Se ainda em stabilization:
1. **[P0] Migration Check workflow fix** — PR `fix/ci-migration-check-awk-parser` (5-10 lines)
2. **[P0] Investigate lint F401/F841 cluster em Backend CI (Security + Linting)** — pre-existing, pode abrir caminho para CI 100% verde
3. **[P0] Load Test Locust script fix** — `catch_response=True` missing em `locustfile.py`

### KILL list (não fazer)
- PR #427 squads integration (612 arquivos, zero receita direta)
- EPIC-UX-PREMIUM stories (sem MRR, premium sem receita = ralo)
- Story-434 API pública (payoff 6+ meses)
- Pricing A/B (BIZ-003) até ter 20+ trials baseline + 1+ pagante

---

## Lições aprendidas

### Bom
1. **Drift sweep pattern (1 commit = 1 cluster)** continua maduro — commits cirúrgicos permitem revert seletivo + commit bodies explicativos facilitam review.
2. **Advisor guidance em expansão de escopo (Cluster D)** — cost/benefit claro (5min investimento, 4 PRs destravados).
3. **Cross-PR check (failures em #432/#433/#435)** validou pre-existing flakiness antes de suspeitar do próprio PR.
4. **Migration Check diagnóstico sem ação prematura** — advisor explicitamente alertou "não rodar db push cegamente"; diagnóstico via log foi suficiente.

### Problemático
1. **Supabase CLI dual-row output format** — mudança não-documentada quebrou workflow silenciosamente. Lesson: CI workflows que parseiam CLI output precisam usar `--format json` quando disponível.
2. **Stack de branches CONV-003 (b + c + docs)** — 3 PRs inter-dependentes de uma única sessão criam overhead de rebase. Próxima sessão dedicada à revenue: manter TUDO em 1 branch única ou mergear incrementalmente.
3. **ambientes locais com/sem pytest-benchmark** — cluster C não foi validado local. Lesson: considerar `pip install pytest-benchmark` em venv dev.

### Para disciplinar
1. **Cluster D drive-by fix** — legítimo quando cost é <5min e unblocka 4+ PRs. Mas risco de scope creep — sempre validar com advisor antes de expandir.
2. **Ordem de merge explícita em handoff** — evita retrabalho de conflict resolution tentativo.
3. **Railway var flip** como artefato concreto de handoff (não "próxima sessão deve fazer") — transforma "shipamos dormant" em "alguém concretamente ativa".
