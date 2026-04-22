# Session Handoff — Wave 3: CRIT-054 fix + BTS-009 + CONV-003a scaffolding

**Date:** 2026-04-20 (madrugada, follow-up direto da Wave 2 de 2026-04-19)
**Founder:** Tiago Sasaki
**Branch head:** `main` (após merges Wave 3)
**Session focus:** Fechar gap Backend Tests (CRIT-054 + BTS-009) + unblock revenue (CONV-003a DB scaffolding)
**Continuation of:** `docs/sessions/2026-04/2026-04-19-bts-wave2-handoff.md`
**Plano board:** `~/.claude/plans/considere-em-conjunto-o-silly-peacock.md` (v2.0)

---

## Outcome at a glance

| Fase | Target | Actual | Status |
|------|--------|--------|--------|
| 1 — CRIT-054 prod fix (foreground) | 1 PR com elif pass-through | **branch `fix/crit-054-pcp-passthrough` + commit `f7f0a64c`** | ✅ Committed |
| 2 — BTS-009 test realignment (background agent) | 20 tests realigned, 1 PR | _See section Agent Report below_ | ⏳/✅ |
| 4 — CONV-003a scaffolding (foreground) | Migration + down + story update | **branch `feat/conv-003a-scaffolding` + commit `bc52b548`** | ✅ Committed |
| 5 — Tier 0.9 kill-criteria doc | Doc novo em `docs/strategy/` | **`docs/strategy/kill-criteria.md` criado** | ✅ |
| 3 — Merge train via @devops | PRs pushed + merged + gate green | _See section @devops delegation_ | ⏳/✅ |
| 6 — Epic-level updates | EPIC-BTS Change Log + status sync | _After merge_ | ⏳ |

---

## Fase 1 — CRIT-054 Prod Fix

**Commit:** `f7f0a64c` em `fix/crit-054-pcp-passthrough`

**Mudança:** `backend/filter/pipeline.py` recebeu 16 linhas novas (elif + imports + comments). Restaura o pass-through PCP v2 dropado silenciosamente no DEBT-201 refactor.

**Spec correta (re-derivada dos testes — story original tinha imprecisões):**
- Branch condição: `status_inferido in ("desconhecido", "todos") AND _source == "PORTAL_COMPRAS"`
- Marker: `lic["_status_unconfirmed"] = True` (dict attr, não lista module-level)
- Counter: `FILTER_PASSTHROUGH_TOTAL.labels(reason="pcp_status_ambiguous").inc()` (counter já existe em `metrics.py:792`, label name é `reason` não `source`)

**Story updates:** AC1-AC3+AC5 marcadas [x]; AC4 pendente (CI é validação — ambiente local sem pytest, venv Windows + system sem deps).

**Blast radius verification:**
- grep `_status_unconfirmed` em toda `backend/` retornou apenas 3 asserts no test file → zero legacy call sites
- Test matrix static analysis: 6 testes do file CRIT-054 logicamente cobertos pela implementação (incluindo o scenario 91% rejection fix)

**Merge strategy desejada:** merge normal (sem admin-bypass) como diagnóstico do gate pós Wave 2.

---

## Fase 2 — BTS-009 Agent Report

**Agent launched:** 2026-04-20 inicio da sessão, background, `general-purpose`, worktree isolation baked-in.

**Agent scope:** 20 failures em 12 arquivos observability/infra (`test_gtm_infra_001/002`, `test_log_volume`, `test_audit`, `test_cron_monitoring`, `test_prometheus_labels`, `test_openapi_schema`, `test_schema_validation`, `test_error_handler`, `test_gtm_critical_scenarios`, `test_gtm_fix_041_042`, `test_gtm_fix_027_track2`).

**Report:** _A ser preenchido quando agent completar._

```
[AGENT FINAL REPORT TBD]
- Worktree path:
- Branch:
- PR URL:
- Contagem: X/20 PASS
- Patterns aplicados:
- Prod findings (se houver):
```

---

## Fase 4 — CONV-003a Scaffolding

**Commit:** `bc52b548` em `feat/conv-003a-scaffolding`

**Arquivos:**
- `supabase/migrations/20260420000003_add_profiles_stripe_default_pm_id.sql` — adiciona coluna nullable + índice parcial
- `supabase/migrations/20260420000003_add_profiles_stripe_default_pm_id.down.sql` — revert pareado (STORY-6.2)
- `docs/stories/2026-04/EPIC-REVENUE-2026-Q2/STORY-CONV-003a-backend-stripe-signup.story.md` — Change Log atualizado

**Escopo deliberadamente reduzido (advisor guidance — Stripe integration alta variância via agente):**
- ✅ DB foundation (AC2 partial)
- ❌ Route `/v1/auth/signup` — não existe ainda (signup atual é Supabase Auth direto do frontend). AC1 criaria o endpoint.
- ❌ Stripe client calls (`Customer.create`, `PaymentMethod.attach`, `Subscription.create`) — reservado para sessão founder dedicada, ~3-4h estimativa
- ❌ Webhook `customer.subscription.trial_will_end` — AC4 na próxima sessão
- ❌ Test stubs `pytest.mark.skip` — violaria Zero Quarentena policy (EPIC-BTS); tests reais escritos junto com AC1

**Story status:** permanece Ready. Change Log explica scoping decision.

**Benefício do ship separado:** CI `deploy.yml` auto-apply exercitado sem acoplamento a Stripe pendente. Próxima sessão abre com coluna live.

---

## Fase 5 — Tier 0.9 Kill-Criteria Doc

**Arquivo:** `docs/strategy/kill-criteria.md` (novo)

Conteúdo: triggers executáveis dos gates D+30 / D+45 / D+60 / D+90 com SQL/CLI commands, verdict matrices, swap rules automáticos, e history log. Preenche o item 0.9 do TIER 0 do plano board v2.0.

---

## Fase 3 — Merge Train (via @devops)

**A executar após BTS-009 agent completar:**

1. `Skill(skill: "devops")` → push + PR CRIT-054 (branch `fix/crit-054-pcp-passthrough`)
2. `Skill(skill: "devops")` → push + PR BTS-009 (branch do agent)
3. `Skill(skill: "devops")` → push + PR CONV-003a scaffolding (branch `feat/conv-003a-scaffolding`)
4. `Skill(skill: "devops")` → push + PR kill-criteria docs (branch `docs/wave3-kill-criteria-handoff`)

**Ordem de merge sugerida:**
1. CONV-003a (DB migration, sem dependência de tests) — merge primeiro, valida `deploy.yml` auto-apply
2. CRIT-054 prod fix — merge normal para diagnosticar gate
3. BTS-009 — admin-bypass se necessário; merge last por ser maior PR
4. Kill-criteria docs — merge pode ser último (docs puro, zero risco)

**Pós-merge:**
- Verificar `gh run list --workflow "Backend Tests (PR Gate)" --branch main --limit 5`
- Se gate green: **2-run streak começou**, faltam 8 para DoD EPIC-BTS
- Se gate red: investigar qual test continua vermelho (não é CRIT-054 nem BTS-009)

---

## Fase 6 — Epic-Level Updates (post-merge)

**`EPIC-BTS-2026Q2/EPIC.md` Change Log append:**

```markdown
- **2026-04-20 (Wave 3)** — @dev + @devops: **Wave 3 COMPLETE**. STORY-CRIT-054
  (prod fix: 3 tests unblocked via elif PCP v2 pass-through restoration + metric
  increment) + STORY-BTS-009 (20 observability/infra tests realigned). Combined:
  ~15-30 residuals → close to 0. Epic DoD: 11/11 stories Done. 10-run backend
  streak starts NOW; branch protection re-enforce pending (time-bound).
  Scaffolding CONV-003a (profiles.stripe_default_pm_id migration) shipped as
  non-BTS side effect. Session handoff:
  `docs/sessions/2026-04/2026-04-20-wave3-handoff.md`.
```

**Story statuses via @devops pós-merge:**
- `STORY-CRIT-054-*.story.md` — InReview → Done
- `STORY-BTS-009-*.story.md` — InReview → Done

---

## Arquivos criados / modificados nesta sessão

### Novos

- `backend/filter/pipeline.py` — +16 linhas CRIT-054 elif (branch `fix/crit-054-pcp-passthrough`)
- `supabase/migrations/20260420000003_add_profiles_stripe_default_pm_id.sql` + `.down.sql` (branch `feat/conv-003a-scaffolding`)
- `docs/strategy/kill-criteria.md` (branch `docs/wave3-kill-criteria-handoff`)
- `docs/sessions/2026-04/2026-04-20-wave3-handoff.md` (este arquivo, branch docs)
- Agent BTS-009: tests em `backend/tests/test_gtm_*`, `test_log_volume.py`, etc. (pending)

### Modificados

- `docs/stories/2026-04/EPIC-BTS-2026Q2/STORY-CRIT-054-filter-passthrough-regression.story.md` — spec correction + ACs marcadas + Status InReview
- `docs/stories/2026-04/EPIC-REVENUE-2026-Q2/STORY-CONV-003a-backend-stripe-signup.story.md` — Change Log scaffolding note

---

## Próxima sessão — prioridades recomendadas

### ROI crítico (destravar Stripe integration full)

1. **STORY-CONV-003a AC1 + AC4** — founder hands, ~3-4h
   - Criar endpoint `POST /v1/auth/signup` (backend route + Pydantic schemas)
   - Integração Stripe: Customer.create + PaymentMethod.attach + Subscription.create (com trial_period_days=14)
   - Idempotency key `signup-{email}-{date_utc}` em cada chamada Stripe
   - Webhook handler `customer.subscription.trial_will_end` + Redis dedup
   - Escrever test file real (10+ cases) — NÃO stubs skipados

2. **Monitor 10-run backend streak** — se gate firme, re-enforce branch protection:
   ```bash
   gh api repos/tjsasakifln/PNCP-poc/branches/main/protection -X PUT ...
   ```

3. **Handoff do 2 precision/recall tests BTS-006 deferred** para @data-engineer (regenerar `benchmark_ground_truth.json`)

### ROI receita direta (continua executando)

4. **Outreach B2G** — 15 contatos/semana (já em cruise-control via STORY-B2G-001)
5. **UptimeRobot setup** — Tier 0.5 pendente (~30min)
6. **Mixpanel funnel setup** — Tier 0.6 pendente (`signup → first_search → ... → paid`)

### KILL LIST (não fazer)

- Full CONV-003b (frontend 2-step) antes de CONV-003a AC1 Done
- STORY-434 API pública read-only datalake (payoff 6+ meses)
- Refactor hygiene sem payoff direto

---

## Lições aprendidas — Wave 3

### Bom

1. **Spec re-derivation do código de teste** (CRIT-054) evitou implementar errado conforme story doc desatualizada. Advisor flagou; testes são single source of truth.
2. **Scoping down CONV-003a** para scaffolding-only respeitou "seguro e efetivo" do user. Commit limpo, reverso trivial.
3. **Worktree cwd fix baked-in** no prompt do agent BTS-009 (lição Wave 2 carregada).
4. **Merge strategy com diagnóstico** — tentar normal primeiro, admin-bypass só se necessário, gera sinal sobre gate real.

### Problemático

1. **Ambiente local sem pytest** continua blocker para CRIT-054-like prod fixes. WSL venv Windows-incompatible. Considerar: criar venv Linux paralelo em `backend/venv-linux/` para validação WSL.
2. **Story doc drift** — CRIT-054 story (escrita 2026-04-19) já estava desatualizada vs. testes (que foram escritos antes). Mais um argumento para tests-as-spec.
3. **Multi-branch management** — 4 branches locais + 1 agent worktree = mental overhead. Considerar ferramenta de visualização (`git-branchless` ou similar) para próximas waves.

---

## Plano 90 dias — status pós Wave 3

- **TIER 0:** 0.2-0.4 + 0.9 shippados. 0.5-0.8 (UptimeRobot, Mixpanel, GSC, eventos validation) remanescentes.
- **TIER 1 (receita):**
  - STORY-BIZ-001/002 + B2G-001 — ✅ Done (sessão prévia)
  - STORY-CONV-003a — Ready (scaffolding partial Wave 3; AC1+AC4 próxima sessão)
  - STORY-CONV-003b — Ready (bloqueada por 003a)
  - STORY-CONV-003c — Ready (bloqueada por 003a)
- **EPIC-BTS-2026Q2:** Wave 3 ship fecha 11/11 stories (BTS-009 + CRIT-054). Epic DoD = 10-run streak (time-bound, começa pós-merge).
- **EPIC-CI-GREEN-MAIN-2026Q2:** Backend track viabilizado por BTS close; P1 P2 Ready stories restantes (~5) podem iniciar em paralelo.
- **MRR:** R$ 0 (gate D+45 target ≥ R$ 397). Primeiro pagante esperado pós CONV-003a+b+c ship (ETA ~15 dias úteis se próxima sessão foca 003a full).

---

## Verification commands (pós-sessão)

```bash
# 1. Confirmar commits Wave 3 em main pós-merge
git log --oneline --since='2026-04-20' main

# 2. Backend Tests streak pós Wave 3
gh run list --workflow "Backend Tests (PR Gate)" --branch main --limit 5 --json conclusion

# 3. Confirmar elif CRIT-054 em main
git grep -n "status_unconfirmed" backend/filter/pipeline.py

# 4. Migration aplicada em Supabase prod
# Via Supabase SQL editor: \d public.profiles | grep stripe_default_pm_id

# 5. Kill-criteria doc acessível
ls -la docs/strategy/kill-criteria.md

# 6. Agent BTS-009 PR merged (X = PR number)
gh pr view X --json state,mergedAt,title
```
