# Session keen-sutton — 2026-04-26

## Objetivo

Fechar incident SSG-hammers-backend (humble-dolphin), ship FAQ rich result, validar trial email pipeline antes de n crescer — para próxima sessão de receita não descobrir débito operacional latente.

## Entregue

- **PR #515 mergeado** — hotfix incident: negative cache em `_compute_contratos_stats` + `AbortSignal.timeout(8000)` em fetches build-time. Commit `053eb785`.
- **PR #516 mergeado** — handoff humble-dolphin (docs sessão prior). Commit `7419f46a`.
- **PR #514 mergeado** — FAQPage JSON-LD em landing (`HomeFaqStructuredData.tsx`). Commit `3a579252`.
- **Migration `20260427015000_incident_municipio_trigram_index`** aplicada em prod via Supabase Management API:
  - GIN trigram index `idx_psc_municipio_trgm` (60 MB) em `pncp_supplier_contracts.municipio` WHERE `is_active=true`. Espelha `idx_psc_objeto_trgm`.
  - ANALYZE rodado. Schema_migrations registrado.
  - **Caveat empírico**: planner picks parallel seq scan no padrão exato do incident (UF=SP + ILIKE %x% + ORDER+LIMIT). Hotfix negative cache continua proteção real; index é additive para queries onde planner achar útil. Query rewrite/hint = story futura.
- **`docs/qa/trial-email-coverage.md`** — TRIAL-001 audit slice (AC1+AC2 mensurados; AC5+AC6 deferidos).
- **11 stories Approved** commitadas (CONV-001..007, GROW-001, SEO-023, SEO-024, TRIAL-001) — backlog visível.

## Impacto em receita

- **FAQ JSON-LD live** em `/`. 4º schema (Organization + WebSite + SoftwareApplication + FAQPage). Hipótese: rich snippet → +CTR ~5-15% nas keywords cobertas. Mensurar GSC em 14-21d.
- **Hotfix completou loop**: prod resiliente a build SSG hammering (negative cache + AbortSignal). Backend hobby plan + WEB_CONCURRENCY=2 absorve traffic spike sem wedge.
- **Trial pipeline visibilidade**: bug sistemático identificado — email_number=1 (welcome day-0) **0% cobertura em 3/3 trials**. Root cause em `process_trial_emails:306-307` (target_start `now-12h` corta usuários >12h antes do próximo 8-11am cron window). Story de fix abrir antes de n≥30.

## Pendente (dono + prazo)

- [ ] **Fix window calc `process_trial_emails`** — @dev — antes de campanha drive trials. Trocar `target_start = now - timedelta(days=day, hours=12)` para janela maior; corrigir `target_end` de `day-1` para `day`.
- [ ] **Composite index query rewrite** — @data-engineer — investigar por que planner não pick `idx_psc_municipio_trgm` no padrão prod (UF first + LIMIT/ORDER). Possíveis hints: re-ordenar WHERE, materializar UF subquery, ou index com expressão. Não bloqueia receita (hotfix protege).
- [ ] **Other pg_cron failures** — @data-engineer — `bloat-check-pncp-raw-bids` (column relpages errado), `cleanup-cold-cache-entries` (syntax INTERVAL 7 days), `cleanup-reconciliation-log`, `retention-search-sessions`. Backlog low-priority — não impactam receita.
- [ ] **TRIAL-001 AC3+AC4+AC5+AC6+AC7+AC8** — @qa/@dev — sessão futura. Story fica `InProgress`.
- [ ] **GSC sitemap resubmit** — @devops — após frontend rebuild #514 confirmar populado, resubmit `/sitemap/4.xml` para indexação. Memória `reference_gsc_playwright_resubmit.md` aplicável.
- [ ] **`feedback_smartlic_baseline_2026_04_24.md` update** — atualizar baseline n=3 trials (de 2) e GSC métricas pós-FAQ.

## Riscos vivos

- **Sev3 (próximas 24-48h)**: frontend Railway build #514 ainda BUILDING ao escrever este handoff. Hotfix em prod deve evitar repetição do incident, mas validar `/sitemap/4.xml` populado + FAQ smoke pós-deploy. Se /4.xml continuar 0 URLs após deploy success, escalar como follow-up story.
- **Sev3 (CI)**: próximo deploy auto-apply pode hit duplicate-key em `schema_migrations` na migration 20260427015000 (já registrada manualmente). Alternativa: monitorar deploy.yml; se falhar, executar `supabase migration repair --status applied 20260427015000` ou ajustar workflow.
- **Sev1 (lifecycle)**: welcome day-0 missing 100%. Quando aquisição crescer (e onboarding email é primeiro touchpoint), gap dói rapidamente. Fix antes de campanha de trial.

## Memory updates

- `reference_smartlic_baseline_2026_04_24.md` — atualizar n=3 trials (não 2). Adicionar gap welcome day-0.
- Novo: `feedback_supabase_migration_via_management_api.md` — quando CLI `db push` falha por OOO/duplicate key, fallback é Supabase Management API endpoint `/database/query`. Pattern: `SET statement_timeout TO 0; CREATE INDEX ...` em single multi-statement call. Manualmente inserir em `supabase_migrations.schema_migrations`.
- Novo: `feedback_planner_no_pick_gin_trgm_with_limit_order.md` — `idx_psc_municipio_trgm` GIN trigram criado mas planner ignora em query com `WHERE uf=X AND ILIKE %y% ORDER BY z LIMIT N`. Causa não-determinada — possível interação com (uf, data_assinatura) idx existente + LIMIT 5000 cost estimate. Story de query rewrite na backlog.
- Atualizar `project_smartlic_onpage_pivot_2026_04_26.md` — TRIAL-001 slice mostrou day-0 gap como bug, não diretriz pivot.

## KPI da sessão

| Métrica | Alvo | Real |
|---------|------|------|
| Shipped to prod (caminho receita) | ≥1 | **3** (#515 hotfix, #514 FAQ, idx_psc_municipio_trgm) |
| Incidents novos | 0 | 0 |
| Tempo em docs | <15% | ~10% (1 audit doc + 1 handoff) |
| Tempo em fix não-prod | <25% | ~15% (composite index ANALYZE failed-pick) |
| Instrumentação adicionada | ≥1 | 1 (TRIAL-001 cobertura measurement) |
| Composite index DEBT | Zerado | Index existente; query rewrite open |
| TRIAL pipeline visibility | AC1+2+5+6 | AC1+2 done; AC5+6 deferred |

KPI session: **green** (3 ships, 0 incidents, instrumentação ≥1, doc <15%).

## Próxima ação prioritária de receita

Fix `process_trial_emails` window calc (welcome day-0). Sem isso, qualquer campanha de aquisição perde primeiro touchpoint do funil de email lifecycle.
