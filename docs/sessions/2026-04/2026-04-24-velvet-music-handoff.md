# Session velvet-music — 2026-04-24

**Branch:** `docs/session-2026-04-24-snappy-treehouse` (5ª sessão herdada)
**Plan:** `~/.claude/plans/mission-empresa-morrendo-velvet-music.md`
**Mission:** empresa-morrendo (MRR única métrica)
**Budget:** 10h confirmadas

## Objetivo

Bootstrap revelou PR #499 BEHIND main (5 commits REVENUE-DIRECT). Sessão descobriu bug sistêmico em signup (trial_expires_at=NULL) via diagnóstico Supabase pós-advisor check, corrigiu, shippou, e aplicou backfill em prod.

## Entregue

| PR | Commit squashed | Scope | Classe |
|----|----|-----|--------|
| **#499 MERGED** `0fcd733e` | 7 commits bundled | Mixpanel cohort (trial_email_sent, subscription_canceled) + UF_CITIES 27 UFs + CI fix Migration/Data Parity + docs epic + **fix signup trigger trial_expires_at** | REVENUE-DIRECT |
| **#500 OPEN** `2de7f221` | 1 commit | `fix(deploy): exclude .down.sql from supabase db push` — destrava apply futuro migrations pareadas | ENG-DEBT (blocker futuro ship) |

**Migration produção aplicada manualmente via WSL** (`.down.sql` stashed): `20260424123244_fix_handle_new_user_trial_expires_at` + backfill:

| Email | created_at | trial_exp pós-backfill |
|-------|------------|------------------------|
| dsl\*@gmail.com | 2026-04-08 | 2026-04-22 (expirado 2d) |
| pau\*@adeque-t.com.br | 2026-04-10 | 2026-04-24 (expirado hoje) |
| sys\*@internal (irrelevante) | 2026-02-26 | 2026-03-12 |
| tia\*@gmail.com (admin — bypass) | 2026-02-03 | 2026-02-17 |

Smoke 12/12 capitais SEO: `200`. Prod healthy.

## Impacto em receita

| Mudança | Estado | Como medir |
|---------|--------|-----------|
| `trial_email_sent` Mixpanel emit | LIVE | Próximo trial email batch → evento Mixpanel |
| `subscription_canceled` Mixpanel emit | LIVE | Próximo `customer.subscription.deleted` webhook |
| 12 capitais SEO indexáveis | LIVE (200/200) | Google indexing 2-14d |
| **Paywall trigger funcional (velvet-music)** | LIVE via migration manual | dsl+pau vão hit paywall na próxima busca (pau após grace 48h) |
| Future signups → trial_expires_at populated | LIVE | Novo signup → profile row com `trial_expires_at = created_at + 14d` |
| Future migrations paired — deploy não trava | Aguarda #500 merge | Próxima migration pareada valida |

**Hipóteses a testar próximas 7 dias:**
1. dsl (expirado 2026-04-22) próxima busca → paywall → `paywall_hit` Mixpanel evento.
2. pau (expirado 2026-04-24, +48h grace até 2026-04-26) próxima busca depois 2026-04-26 → paywall.
3. Novo signup real próximos 14d → trial_expires_at populado corretamente no trigger.

## Pendente

| # | Ação | Dono | Prazo |
|---|------|------|-------|
| 1 | Review + merge PR #500 (workflow fix) | `@devops` | nesta sessão |
| 2 | `/schedule` +48h → verificar dsl/pau hit paywall e `paywall_hit` Mixpanel event disparou | `@dev` | 2026-04-26 |
| 3 | Fix workflow `handle-new-user-guard.yml` bug multi-line GITHUB_OUTPUT | `@devops` | backlog |
| 4 | Investigar signup SDK direto — se `signUpWithEmail` ainda dispara trigger corretamente | `@architect` | baixa prioridade (trigger cobre ambos paths) |
| 5 | Validar próximo signup real popula `trial_expires_at` | `@qa` | proativo, próximos 7d |

## Riscos vivos

| Risco | Sev | Prazo p/ virar incidente |
|-------|-----|--------------------------|
| PR #500 não mergeado até próxima migration pareada → próximo Deploy falha schema_migrations_pkey again | Média | Qualquer novo migration com `.down.sql` pareado |
| dsl/pau impactados UX (paywall rudo) pode gerar abandono | Baixa (N=2) | 48h pós-retomada uso |
| Deploy #499 marcou como SUCCESS apesar de migration ter falhado (`continue-on-error: true`) — observabilidade vai mostrar Migration Check FAIL post-merge | Baixa | Já visível em `Migration Check (Post-Merge Alert)` workflow |

## Memory updates

Candidatos a salvar (ainda não persistidos):

- `project_empresa_morrendo_baseline_2026_04_24` — snapshot: 4 profiles, 2 externos reais, 0 paid 30d, 0 trials 7d. Historical, útil para futura sessão de crescimento.
- `reference_supabase_down_sql_schema_migrations_conflict` — CLI 2.x `db push --include-all` causa `schema_migrations_pkey` duplicate quando `.sql` + `.down.sql` pareados compartilham timestamp. Workaround: stash `.down.sql` antes do push. Fix no deploy.yml em PR #500.
- `reference_admin_bypass_paywall_policy` — admin=True em `profiles` bypassa paywall independente de `trial_expires_at`. Relevante para QA e diagnose.

Aplicadas:

- `feedback_advisor_critical_discernment` — advisor orientou 2 verificações barato antes de pivotar Fase 5. Desambiguou: bug UPTIME-CRITICAL real escondido sob aparente "baixa conversão".
- `reference_pr_body_edit_persistence` — body atualizado via `gh api PATCH`.
- `feedback_story_discovery_grep_before_implement` — investigação 15min signup code revelou bug sistêmico antes de implementar quick-win que não moveria N=4.

## KPI da sessão

| Métrica | Alvo | Real |
|---------|------|------|
| Shipped to prod | ≥1 | **2** (PR #499 merged + migration manual apply) |
| Incidentes novos | 0 | 0 |
| Tempo em docs | <15% | ~10% |
| Tempo em fix não-prod | <25% | ~15% (workflow deploy.yml fix) |
| Instrumentação adicionada | ≥1 | 2 (Mixpanel events herdados em #499 + signup trigger field) |
| Bug REVENUE-DIRECT descoberto via diagnóstico | N/A | 1 (trial_expires_at=NULL sistêmico) + 1 (deploy workflow `.down.sql` apply bug) |

## Para retomar

```bash
# 1. PR #500 merged?
gh pr view 500 --json state,mergedAt

# 2. Verificar dsl/pau paywall hit
# Mixpanel dashboard: evento paywall_hit com user_id=39b32b6f* ou 285edd6e*

# 3. Novo signup testou (se houver): trial_expires_at populated?
python3 /tmp/auth_check.py  # ou equivalente query profiles

# 4. Backlog: fix handle-new-user-guard.yml multi-line GITHUB_OUTPUT
```

**Status final: velvet-music executou Fases 1-5 completas. Fase 6 skipped (escopo tomado por Fase 5 + workflow fix). Fase 7 este handoff. Mission advance: bug REVENUE-DIRECT sistêmico em signup fixo + instrumentação live + SEO destravado.**
