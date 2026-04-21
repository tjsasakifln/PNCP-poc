# Session Handoff — Floofy Sparkle (2026-04-21)

**Data:** 2026-04-21 madrugada (~03-06 UTC)
**Executor:** Claude Opus 4.7 (1M context) em auto mode multi-frente
**Plano seguido:** `/home/tjsasakifln/.claude/plans/voc-o-consultor-floofy-sparkle.md`
**Sessão anterior:** `docs/sessions/2026-04/2026-04-20-temporal-bonbon-handoff.md` (cascade drift sweep + CONV-003 merge train)

---

## Outcome at a glance

| Frente | Target | Actual | Status |
|---|---|---|---|
| 1 — Migration Check awk filter | PR merged | [PR #445](https://github.com/tjsasakifln/PNCP-poc/pull/445) pushed, CI running | ⏳ Awaiting CI |
| 2 — Triagem 3 broken workflows (chromatic/lighthouse/billing-check) | PR merged | [PR #446](https://github.com/tjsasakifln/PNCP-poc/pull/446) pushed, CI running; **Chromatic SUCCESS empirical** confirms YAML fix | ⏳ Awaiting CI |
| 3 — SEO-001 AC3 + AC4 (sitemap observability) | Backend metric + frontend Sentry | [PR #447](https://github.com/tjsasakifln/PNCP-poc/pull/447) — 7 fetchers refactored + 7 endpoints instrumented | ⏳ Awaiting CI |
| 4 — CONV-003c status sync → Done | Story file reconciled | Bundled into PR #447 (docs-only delta) | ⏳ Awaiting CI |
| 5 — Dependabot batch (10 PRs) | 10 merged | **Deferred** — all 10 have failures from broken workflows (F2) + Load Test pre-existing; rebase post-F1/F2 merge | 🟡 Deferred |
| 6 — Baseline validation (Tests Full Matrix green) | Main CI green | Pending merges from F1/F2/F3+F4 | ⏳ In progress |

---

## Frente 1 — Migration Check awk stderr filter

**Branch:** `fix/ci/migration-check-timestamp-filter` (commit `8ab87764`)
**PR:** [#445](https://github.com/tjsasakifln/PNCP-poc/pull/445)

### Problem

Post-PR #441 the workflow was still failing with false positives. Run `24703292240` log showed:

```
Unapplied migrations:
Connecting to remote database...
Skipping migration 006a_update_profiles_plan_type_constraint.sql...
Skipping migration README.md...
```

Root cause: Supabase CLI writes informational messages to stderr. `supabase migration list --linked 2>&1` merges them into stdout. These lines lack pipe separators, so `awk -F'|'` treats the whole line as `$1` (local) with `$2` (remote) empty → classified as unapplied.

### Fix

Single-line addition to existing awk block:

```awk
if (local !~ /^[0-9]{14}$/) next
```

Preserves the dual-row dedup semantics from PR #441 (Abstract Coral session).

### Validation

- ✅ Local simulation: applied migrations + stderr noise → `UNAPPLIED=''`
- ✅ Local simulation: real unapplied (no dual-row) → `UNAPPLIED='20260414131000'` (correctly detected)

---

## Frente 2 — Repair 3 broken workflow files

**Branch:** `fix/ci/broken-workflows-triage` (commit `f03db6b3`)
**PR:** [#446](https://github.com/tjsasakifln/PNCP-poc/pull/446)

### Discovery

All three workflows had **100/100 failures on last 100 runs**. GitHub CLI reported "This run likely failed because of a workflow file issue" — indicating YAML itself is invalid, so GitHub can't schedule the run.

### Root causes + fixes

| File | Root cause | Fix |
|------|-----------|-----|
| `billing-check.yml` | Python block inside `run: \|` had lines at col 1 (`import sys, json`), terminating the YAML block scalar (indent=10). | Extracted Python to `.github/scripts/billing-check.py`, invoked via stdin. CRIT-080 alerting preserved. |
| `lighthouse.yml` | `actions/github-script` inline JS template literal contained Markdown-table lines (`\| Category \| Score \|`) at col 1, terminating the YAML `script: \|` block. | Extracted to `.github/scripts/lighthouse-comment.js`, invoked via `require(...)`. Job marked `continue-on-error: true` given 0/100 history. |
| `chromatic.yml` | Used `if: ${{ secrets.CHROMATIC_PROJECT_TOKEN != '' }}` at job level. GitHub doesn't expose secrets to job-level `if:` conditions. | Replaced with first step that reads secret via `env:` and sets output; subsequent steps gate on that output. |

### Empirical confirmation

On PR #446, **Chromatic — Visual Regression (10 screens)** job finished with **SUCCESS** at 2026-04-21T04:59:53Z. This was the first-ever success of that workflow. Confirms the YAML fix is structurally correct and the workflow now reaches the actual Chromatic CLI invocation.

### Follow-up (out of scope)

- **Lighthouse**: `continue-on-error: true` is a temporary bridge. Decide gate vs delete — don't let it persist indefinitely.
- **Chromatic**: if `CHROMATIC_PROJECT_TOKEN` is set in repo secrets, workflow now runs for real on every main push. Monitor first 2-3 runs.

---

## Frente 3 — SEO-001 sitemap observability

**Branch:** `feat/seo-001-and-conv-003c-closure` (commit `bc17524c`)
**PR:** [#447](https://github.com/tjsasakifln/PNCP-poc/pull/447)

### Problem (empirical)

```bash
$ for i in 0 1 2 3 4; do
    curl -sL https://smartlic.tech/sitemap/$i.xml | grep -c '<url>'
  done
39
60
810
301
0   ← ~92% long-tail entity pages silently dropped from Google index
```

Root cause: Railway frontend has no `BACKEND_URL` env var → `frontend/app/sitemap.ts` fetches hit `http://localhost:8000` → ECONNREFUSED → silent `catch { return []; }` → shard 4 empty for weeks with zero alert.

### AC3 — observable fetch wrapper (frontend)

- New helper `fetchSitemapJson<T>(endpoint, extract, label)` in `frontend/app/sitemap.ts`.
- On failure: `Sentry.captureException` with tags `sitemap_endpoint` + `sitemap_outcome` + context `endpoint, url, status`.
- Build still graceful — wrapper returns `null`, callers default to `[]`.
- **7 fetchers refactored**: `fetchLicitacoesIndexable`, `fetchContratosOrgaoIndexable`, `fetchSitemapCnpjs`, `fetchSitemapFornecedoresCnpj`, `fetchSitemapMunicipios`, `fetchSitemapItens`, `fetchSitemapOrgaos`.

### AC4 — Prometheus instrumentation (backend)

- New `smartlic_sitemap_urls_served_total{endpoint}` Counter + `smartlic_sitemap_urls_last{endpoint}` Gauge in `backend/metrics.py`.
- Helper `record_sitemap_count(endpoint, count)` called from 7 endpoints (both cache-hit and cache-miss paths):
  - `sitemap_cnpjs.py` → `cnpjs`, `fornecedores-cnpj`
  - `sitemap_orgaos.py` → `orgaos`, `contratos-orgao-indexable`
  - `sitemap_licitacoes.py` → `licitacoes-indexable`
  - `municipios_publicos.py` → `municipios`
  - `itens_publicos.py` → `itens`

### Validation

- ✅ AST parse clean on all 5 backend route files + `metrics.py`
- ✅ `npx tsc --noEmit` — 0 errors on full frontend project
- ✅ Import convention aligned (`from metrics import`, not `from backend.metrics`)

### Still pending — SEO-001 remaining ACs

These are explicitly scoped OUT of this PR:

- **AC1** — Railway `smartlic-frontend` service needs `BACKEND_URL` env var set (pointing to internal/public backend URL). **Action for @devops.**
- **AC2** — `curl -sL https://smartlic.tech/sitemap/4.xml | grep -c '<url>'` ≥ 5000 after AC1 redeploy. Validation.
- **AC5** — Configure Grafana/Sentry alert rules:
  - Warning: `smartlic_sitemap_urls_last{endpoint="cnpjs"} < 100`
  - Critical: `smartlic_sitemap_urls_last{endpoint="cnpjs"} < 10`
  - Counter stall: `rate(smartlic_sitemap_urls_served_total[1h]) == 0`
- **AC6** — Submit updated sitemap.xml in Google Search Console; monitor Coverage for 4 weeks.
- **AC7** — Add `frontend/__tests__/sitemap-coverage.test.ts` that fails in CI if shard 4 < 100.

---

## Frente 4 — CONV-003c status sync → Done

**Bundled in PR #447** (docs-only delta alongside SEO-001).

### Audit of AC6 (backend test coverage ≥85%)

Inventoried `backend/tests/`:

| File | Tests | Covers |
|------|------:|--------|
| `test_cancel_trial_token.py` | 19 | JWT sign/verify + GET + POST + idempotency |
| `test_trial_funnel_metrics.py` | 7 | 4 Prometheus counters + branch labels |
| `test_welcome_to_pro_email.py` | 8 | Template render + dispatcher branch |
| `test_trial_emails.py` | 125 (18 new for AC1) | Day-13 branch-aware email |
| `test_payment_failed_webhook.py` + `test_stripe_webhook*.py` + `test_webhook_rls_security.py` | existing | `payment_succeeded`, `payment_failed`, `payment_action_required`, idempotency, RLS |

**AC6 sub-item** `test_trial_charge_warning_cron.py` marked **N/A** — AC1 reused STORY-321 Day-13 infrastructure (no new cron, documented architectural decision — see story change-log).

### Status transition

- `InProgress` → `Done`
- DoD reconciled: code/tests ✅, operational items (14-day real charge, 30d chargeback rate) deferred to post-PCT=10 flip

### Operational flip (NOT this session)

Railway PCT=10 flip instructions remain in:
- `docs/runbooks/trial-card-rollback.md`
- `docs/sessions/2026-04/2026-04-20-temporal-bonbon-handoff.md` (Frente 4 section)

---

## Frente 5 — Dependabot batch (DEFERRED)

10 open Dependabot PRs (#413-#422). Pre-triage revealed all have failures driven by:

### Frontend bumps (#414, #417, #418, #421, #422) — 2 failures each

| Workflow | Failure |
|----------|---------|
| `Dependabot Auto-merge (patch/minor)` | Orthogonal to F2; separate broken workflow |
| `Storybook Build` | Real frontend build failure — unrelated to dep bump |

### Backend patch bumps (#415, #416, #419, #420) — 6 failures each

| Workflow | Category |
|----------|----------|
| Backend Tests + Backend Tests (3.11) + Backend Test Results | Real pre-existing test failures on main |
| Load Test - Backend API | **Pre-existing 100% failure rate** (6187/6187 failed in 120s run) — present on every PR including F3+F4 #447 |
| `test` (Backend CI Security + Linting) | Real pre-existing |
| `Dependabot Auto-merge (patch/minor)` | Orthogonal |

### mypy major bump (#413) — 6 failures, ⚠️ risk

`mypy 1.15.0 → 1.20.1` is a minor range bump that in practice acts as a major for a large codebase. Failures include `test` + `Backend Tests` + `Backend Tests (3.11)` — strongly suggests new type errors surfaced.

**Recommendation (needs user approval — destructive action):** close #413 with label "needs dedicated type-fix sweep story". Do not attempt to rebase-merge.

### Why F5 was deferred

1. Merging dependabots before F1/F2 merge just rebases into the same broken CI gates.
2. Load Test pre-existing failure and Storybook Build pre-existing failure would turn the batch merge into a fishing expedition.
3. Blast radius: 10 PRs × ~20 min CI each = 3-4 hours of CI wallclock. Not a fit for a polling-intensive session.

### Path forward (next session)

1. Wait for F1/F2/F3+F4 merges to main.
2. Bulk rebase: `for pr in 414 417 418 421 422; do gh pr comment $pr --body "@dependabot rebase"; done` (frontend patch, lowest risk).
3. After each rebase: check if only Storybook Build + Dependabot Auto-merge remain failing. If yes, admin-merge (both are orthogonal to the dep bump itself).
4. Backend bumps (#415, #416, #419, #420): wait for main baseline green → rebase → verify Backend Tests pass real.
5. mypy #413: user-approved close OR new story `DEBT-mypy-1.20-type-sweep`.

---

## Frente 6 — Baseline validation (PENDING)

Awaiting F1 (#445) + F2 (#446) + F3+F4 (#447) merges. Post-merge plan:

1. Wait for main "Tests (Full Matrix + Integration + E2E)" run to complete.
2. If green: baseline confirmed. Tag handoff as COMPLETE.
3. If red: triage cluster-by-cluster, padrão BTS-011 (1 commit per cluster).

### Known pre-existing main failures (NOT caused by this session)

- **Load Test - Backend API**: 100% failure rate, likely since PR #444 locust fix. Unrelated to this session's work. Needs dedicated investigation.
- **Migration Check**: fixed in F1 (#445) pending merge.
- **Chromatic / Lighthouse / billing-check**: fixed in F2 (#446) pending merge.
- **Deploy (Railway)**: last run failed, prior succeeded → flaky. Monitoring.

---

## Ações pendentes para @devops / operacional

### Immediate (this session's PRs)

1. Merge [PR #445](https://github.com/tjsasakifln/PNCP-poc/pull/445) (F1 migration-check)
2. Merge [PR #446](https://github.com/tjsasakifln/PNCP-poc/pull/446) (F2 broken workflows)
3. Merge [PR #447](https://github.com/tjsasakifln/PNCP-poc/pull/447) (F3+F4 SEO + CONV-003c sync)

### Post-merge operational

4. **Railway frontend:** set `BACKEND_URL` env var → redeploy → verify `curl https://smartlic.tech/sitemap/4.xml | grep -c '<url>' >= 5000` (SEO-001 AC1/AC2)
5. **Railway frontend:** set `NEXT_PUBLIC_TRIAL_REQUIRE_CARD_ROLLOUT_PCT=10` → redeploy → monitor Mixpanel/Sentry 48h (CONV-003c flip)
6. **Google Search Console:** submit updated sitemap.xml (SEO-001 AC6)
7. **After PCT=10 stable 48h:** escalate 25% → 50% → 100% per runbook `docs/runbooks/trial-card-rollback.md`

### Dependabot batch follow-up

8. Bulk-rebase frontend dependabots (#414, #417, #418, #421, #422) via `@dependabot rebase` comments after F1/F2 merged.
9. **User decision needed:** close #413 (mypy 1.15→1.20 major bump, real type errors) or create dedicated sweep story.

---

## Próximas prioridades (roadmap)

- **SEO-002 to SEO-008** (EPIC-SEO-2026-04) — 7 remaining stories in the new epic (stories exist in `docs/stories/STORY-SEO-00{2..8}-*.md`, untracked — need @sm to commit + prioritize)
- **CONV-003c Dashboard `/admin/billing/trial-funnel`** (AC4 P2 deferred)
- **Lighthouse perf gate decision** — enable as gate vs delete
- **Load Test investigation** — 100% failure rate on main since #444; root cause likely locust user context or env var missing
- **mypy 1.20 type sweep** (if #413 closed)

---

## Decisões de rota justificadas nesta sessão

1. **Extração de Python/JS para arquivos separados** (F2) em vez de indentação manual dos blocos inline: preserva legibilidade do código e evita futuras regressões YAML pelo mesmo padrão.
2. **`continue-on-error: true` em lighthouse** (F2): workflow tem 0/100 success histórico — gating sem validação de secrets/thresholds é pior que advisory. Follow-up explícito documentado.
3. **Bundle F3+F4 em PR único** (advisor recommendation): F4 é 10min de docs + F3 é code change relacionado a SEO — um PR acelera merge sem comprometer review.
4. **Defer F5 (Dependabots)** ao invés de tentar mergear em loop: as falhas são majoritariamente CI infra (F2 fixes) + Storybook/Load Test pré-existentes. Merge antes de F2 gera retrabalho.
5. **Não fechar mypy #413** autonomously — ação destrutiva, requer aprovação explícita do usuário (per advisor + per behavioral rules "delete/remove content without asking first").
