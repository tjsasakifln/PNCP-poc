# Database Specialist Review

**Reviewer:** @data-engineer (Dara)
**Date:** 2026-04-14
**Workflow:** brownfield-discovery v3.1 — Phase 5
**Input:** `docs/prd/technical-debt-DRAFT.md` (Phase 4)

---

## Resumo Executivo

- ✅ Validei os 18 débitos de Database identificados na Phase 4
- 🆕 Adicionei 3 débitos não cobertos
- ⚠️ Ajustei severidade de 2 itens
- 💡 Recomendo ordem priorizando **storage quota** > **RLS gaps** > **performance**

---

## Débitos Validados

| ID         | Débito                                   | Sev. Original     | Sev. Ajustada | Horas | Prioridade DB | Notas |
|------------|------------------------------------------|-------------------|---------------|-------|---------------|-------|
| TD-DB-001  | RLS bypass `search_sessions`             | CRITICAL ✅ FIXED | -             | -     | -             | Confirmado historical fix em 006b_*. Manter como referência. |
| TD-DB-002  | Missing user_id indexes                  | CRITICAL ✅ FIXED | -             | -     | -             | Confirmado fix em DEBT-001. Re-rodar `pg_stat_user_indexes` para confirmar uso. |
| TD-DB-003  | partner_referrals NOT NULL conflict      | CRITICAL ✅ FIXED | -             | -     | -             | Confirmado fix em DEBT-001. |
| TD-DB-004  | purge_old_bids cron NOT SCHEDULED        | CRITICAL 🔴       | CRITICAL ✅   | 0.5h  | **P0**        | **CONFIRMO**: pg_cron NÃO listado em produção. Storage explosivo em 3-4 semanas. |
| TD-DB-010  | stripe_webhook_events RLS admin          | HIGH              | HIGH ✅       | 1h    | P1            | Confirma. Admin debug é UX critical. |
| TD-DB-011  | profiles.email UNIQUE                    | HIGH              | HIGH ✅       | 2-4h  | P1            | **Cautela**: precisa script de dedup ANTES de adicionar constraint. |
| TD-DB-012  | messages.INSERT triple nested EXISTS     | HIGH              | **MEDIUM** ↓  | 4-6h  | P2            | **Ajusto**: query planner Postgres 17 otimiza bem; perf observada não é gargalo. |
| TD-DB-013  | search_results_cache cron cleanup        | HIGH              | HIGH ✅       | 0.5h  | P0            | Confirma — overlap com TD-SYS-016. |
| TD-DB-014  | search_results_store cron cleanup        | HIGH              | HIGH ✅       | 0.5h  | P0            | Confirma — overlap com TD-DB-013. |
| TD-DB-015  | alert digest scan index                  | HIGH              | **MEDIUM** ↓  | 1h    | P2            | **Ajusto**: cron job atual <100ms; not actually slow. |
| TD-DB-020  | audit_events sem is_active               | MEDIUM            | MEDIUM ✅     | 1h    | P2            | Confirma — LGPD compliance defer. |
| TD-DB-021  | classification_feedback status unclear   | MEDIUM            | MEDIUM ✅     | 2-4h  | P2            | **Resposta**: Tabela em uso (feedback bi-gram). Conditional checks são defensive. |
| TD-DB-022  | pncp_raw_bids.data_* nullable            | MEDIUM            | **HIGH** ↑    | 4-8h  | P1            | **Ajusto**: 5-10% exclusão silenciosa = UX issue. Audit ingestion + COALESCE em filtros. |
| TD-DB-023  | health_checks manual cleanup             | MEDIUM            | LOW ↓         | 0.5h  | P3            | Apenas ~5K rows/30d. Schedule cron mas baixa prioridade. |
| TD-DB-024  | stripe_webhook_events PII                | MEDIUM            | MEDIUM ✅     | 4-8h  | P2            | LGPD risk; archive S3 após 7 days. |
| TD-DB-030  | Sem down.sql templates                   | LOW               | LOW ✅        | 4-8h  | P3            | DX gap; não bloqueia. |
| TD-DB-031  | Duplicate trigger functions              | LOW ✅ FIXED      | -             | -     | -             | Confirmado fix. |
| TD-DB-032  | Soft FK pncp_raw_bids                    | LOW               | LOW ✅        | 0.5h  | P3            | Apenas adicionar COMMENT. |
| TD-DB-033  | search_results_store CASCADE inconsistency | LOW             | LOW ✅        | 1h    | P3            | Inconsistência cosmética. |

---

## Débitos Adicionados

### TD-DB-040 (NEW): pg_cron jobs sem monitoring/alertas

- **Severity:** HIGH
- **Finding:** Cron jobs sem alertas se falham. `cron.job_run_details` tem registros mas ninguém monitora.
- **Impact:** Cron silently falha → retention ignorada → storage/compliance issues.
- **Fix:** Sentry alert se `cron.job_run_details` mostra failures recentes; Prometheus exporter de pg_cron status.
- **Effort:** 4-8h
- **Priority:** P1

### TD-DB-041 (NEW): Sem backup automatizado off-Supabase

- **Severity:** HIGH
- **Finding:** Supabase Cloud faz daily backup, mas sem cópia off-site (S3, GH Actions weekly dump).
- **Impact:** Vendor lock-in; recovery dependente do Supabase estar disponível.
- **Fix:** Weekly `pg_dump` → S3 com encryption.
- **Effort:** 4-8h
- **Priority:** P2

### TD-DB-042 (NEW): Connection pooler config não tunada

- **Severity:** MEDIUM
- **Finding:** Supavisor usa defaults. Backend faz ~10 connections/worker; em pico, pode esgotar pool.
- **Impact:** "remaining connection slots reserved" errors em alta concorrência.
- **Fix:** Audit `default_pool_size` + `max_client_conn`; aumentar conforme worker count.
- **Effort:** 2-4h
- **Priority:** P2

---

## Respostas ao @architect (perguntas Phase 4 §5)

1. **`purge_old_bids()` cron**: ❌ NÃO está configurado em prod. **AÇÃO IMEDIATA**: schedule `cron.schedule('purge-old-bids', '0 3 * * *', 'SELECT public.purge_old_bids(12)')`.
2. **Soft-delete `is_active=false`**: ✅ Intencional — análise post-mortem (debugging classificação errada). Pode evoluir para hard-delete após 30 days (2 stages).
3. **`partner_referrals`**: 🟡 Feature WIP — tabela existe mas código de geração de codes não merged. Decisão: manter tabela vazia até produto decidir.
4. **`classification_feedback`**: ✅ Em uso. Bi-gram analysis em `feedback_analyzer.py` consome essa tabela.
5. **Service role bypass wide-open**: ⚠️ Necessário para backend mas deve ser narrowed. Recomendo `service_role_audit` view + revisão trimestral.
6. **`messages.INSERT` complexity**: ✅ Aceitar (Postgres 17 otimiza). Apenas adicionar comment explicando o pattern.
7. **`profiles.email` UNIQUE**: ✅ Adicionar APÓS script de dedup. Não pode rodar `ALTER ADD UNIQUE` em prod sem cleanup primeiro.
8. **PII em `stripe_webhook_events.payload`**: ✅ Archive S3 após 7 days com encryption. Atual 90-day plaintext é LGPD risk.
9. **`organizations.owner_id` RESTRICT**: ⚠️ Trade-off. Soft-delete (`owner_id → NULL`) requer redesign. Manter RESTRICT + UI alert ao admin.
10. **PostgreSQL FTS Portuguese tuning**: ✅ Vale 8-16h. Criar dicionário `public.portuguese_smartlic` com termos legais BR.

---

## Recomendações de Ordem de Resolução (perspectiva DB)

### Tier 1 — IMEDIATO (P0, < 5h total)

1. **TD-DB-004** — Schedule purge_old_bids cron (0.5h) ⚠️ **STORAGE BLOCKING**
2. **TD-DB-013** — Schedule search_results_cache cleanup (0.5h)
3. **TD-DB-014** — Schedule search_results_store cleanup (0.5h)

### Tier 2 — Próxima Sprint (P1, ~10-20h)

5. **TD-DB-010** — Stripe webhook admin RLS (1h)
6. **TD-DB-011** — profiles.email UNIQUE + dedup (2-4h)
7. **TD-DB-022** — pncp_raw_bids.data_* nullability fix (4-8h)
8. **TD-DB-040** — pg_cron monitoring (4-8h)

### Tier 3 — Próxima 2 sprints (P2, ~10-20h)

9. **TD-DB-012** — messages RLS comment/refactor (4-6h)
10. **TD-DB-015** — alert digest index (1h)
11. **TD-DB-020** — audit_events soft-delete (1h)
12. **TD-DB-021** — classification_feedback documentation (2-4h)
13. **TD-DB-024** — stripe webhook PII archive (4-8h)
14. **TD-DB-041** — Off-site backup (4-8h)
15. **TD-DB-042** — Connection pooler tune (2-4h)

### Tier 4 — Strategic (P3, ~6-12h)

16. **TD-DB-023** — health_checks cron (0.5h)
17. **TD-DB-030** — down.sql templates (4-8h)
18. **TD-DB-032** — Soft FK comment (0.5h)
19. **TD-DB-033** — search_results_store CASCADE (1h)

---

## Effort Total

- **Database tier 1 (P0)**: ~2h (most-critical, immediate)
- **Database tier 2 (P1)**: 16-28h
- **Database tier 3 (P2)**: 18-30h
- **Database tier 4 (P3)**: 6-10h
- **Total DB**: ~42-70h (1-2 sprints solo dev)

---

**Status**: ✅ Review completo. Handoff para Phase 7 (@qa).
