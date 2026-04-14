# Technical Debt Assessment — DRAFT

## Para Revisão dos Especialistas (Phases 5-7)

**Data:** 2026-04-14
**Autor:** @architect (Aria)
**Workflow:** brownfield-discovery v3.1 — Phase 4

Este DRAFT consolida os débitos técnicos identificados nas Phases 1-3. Está sujeito a revisão dos especialistas (@data-engineer, @ux-design-expert, @qa) antes do FINAL assessment (Phase 8).

---

## Fontes Consolidadas

1. `docs/architecture/system-architecture.md` (Phase 1 — @architect)
2. `supabase/docs/SCHEMA.md` (Phase 2 — @data-engineer)
3. `supabase/docs/DB-AUDIT.md` (Phase 2 — @data-engineer)
4. `docs/frontend/frontend-spec.md` (Phase 3 — @ux-design-expert)

---

## 1. Débitos de Sistema (Fonte: Phase 1)

### CRITICAL

| ID         | Débito                                                                       | Área         | Impacto                                                | File/Path                                    |
|------------|------------------------------------------------------------------------------|--------------|--------------------------------------------------------|----------------------------------------------|
| TD-SYS-001 | CRIT-080 SIGSEGV em POST (jemalloc+Sentry+cryptography)                      | Backend      | POST requests crasham; search broken                   | Dockerfile, requirements.txt, main.py        |
| TD-SYS-002 | PNCP API `tamanhoPagina` max 50 (Feb 2026 breaking)                          | Integration  | 10x mais calls; health canary não detecta              | pncp_client.py                               |
| TD-SYS-003 | Railway hard timeout 120s < Gunicorn 180s                                    | Infra        | Requests >120s killed; incomplete responses            | start.sh, gunicorn_conf.py                   |
| TD-SYS-004 | Migrations não aplicadas bloqueiam features (CRIT-039/045/050) — DEFENDED    | DevOps/DB    | Histórico de incidents; schema mismatch                | .github/workflows/*                          |
| TD-SYS-005 | `search.py` monolítico 1000+ LOC + state distribuído                         | Backend      | Debug difícil; mudanças cascateiam                     | routes/search.py                             |

### HIGH

| ID         | Débito                                                        | Área         | Impacto                                                | File/Path                                    |
|------------|---------------------------------------------------------------|--------------|--------------------------------------------------------|----------------------------------------------|
| TD-SYS-010 | L1 cache não shared entre Gunicorn workers                    | Backend      | Hit ratio baixo multi-worker                           | cache.py, gunicorn_conf.py                   |
| TD-SYS-011 | Feature flags em 3 lugares (env+Redis+código)                 | Backend      | Valores conflitantes; ordem de eval pouco clara        | config.py, feature_flags.py, .env            |
| TD-SYS-012 | Setores duplicados backend YAML + frontend hardcoded          | Backend/FE   | Frontend stale se não sincronizado                     | sectors_data.yaml, buscar/page.tsx           |
| TD-SYS-013 | Session dedup 6-24h eventual consistency                      | Backend      | Duplicatas UI; confusão usuário                        | consolidation.py                             |
| TD-SYS-014 | LLM concurrency bottleneck (ThreadPoolExecutor 10)            | Backend      | Latência 30s+ em alta concorrência                     | llm_arbiter.py                               |
| TD-SYS-015 | FTS não otimizado para Português                              | Backend/DB   | Falsos positivos; menor precisão                       | datalake_query.py                            |
| TD-SYS-016 | `search_results_cache` growth unbounded (sem cron)            | DB           | Table bloat; disk usage                                | migrations/026_*                             |
| TD-SYS-017 | Rate limit ausente endpoints públicos                         | Security     | Scraping; DoS vector                                   | routes/stats_public.py                       |
| TD-SYS-018 | LLM sem cap de custo mensal                                   | Cost         | Runaway spending possível                              | llm_arbiter.py                               |

### MEDIUM

| ID         | Débito                                                        | Área       |
|------------|---------------------------------------------------------------|------------|
| TD-SYS-020 | sectors_data.yaml sem validação startup                       | Backend    |
| TD-SYS-021 | Feature flags docs inconsistentes                             | Backend    |
| TD-SYS-022 | Mock location inconsistente em testes                         | Testes     |
| TD-SYS-023 | Integration tests flaky (shared state)                        | Testes     |
| TD-SYS-024 | `schemas.py` 1500+ LOC monolítico                             | Backend    |
| TD-SYS-025 | Logs JSON-vs-text inconsistentes                              | Observ     |

### LOW

| ID         | Débito                                                        | Área       |
|------------|---------------------------------------------------------------|------------|
| TD-SYS-030 | Python + SQL migrations coexistem sem doc clara               | DevOps     |
| TD-SYS-031 | Dead code em `backend/legacy/`                                | Code       |
| TD-SYS-032 | OTEL spans incompletos (HTTP-only por CRIT-080)               | Observ     |

**Subtotal Sistema: 20 débitos**

---

## 2. Débitos de Database (Fonte: Phase 2)

⚠️ **PENDENTE revisão do @data-engineer (Phase 5)**

### CRITICAL

| ID         | Débito                                                                       | Status      | File/Path                                    |
|------------|------------------------------------------------------------------------------|-------------|----------------------------------------------|
| TD-DB-001  | Service-Role RLS bypass missing em `search_sessions`                         | ✅ FIXED    | 006b_search_sessions_service_role_policy.sql |
| TD-DB-002  | Missing `user_id` indexes on RLS-heavy tables                                | ✅ FIXED    | DEBT-001 migration                           |
| TD-DB-003  | FK conflict: partner_referrals NOT NULL + ON DELETE SET NULL                 | ✅ FIXED    | DEBT-001 migration                           |
| TD-DB-004  | `purge_old_bids()` cron NOT SCHEDULED em prod                                | 🔴 OPEN     | migrations/020260326000000_*                 |

### HIGH

| ID         | Débito                                                                       | File/Path                              |
|------------|------------------------------------------------------------------------------|----------------------------------------|
| TD-DB-010  | Improper RLS em `stripe_webhook_events` (admins sem SELECT)                  | migrations/stripe_webhook_events       |
| TD-DB-011  | No UNIQUE constraint em `profiles.email`                                     | migrations/001_profiles_and_sessions   |
| TD-DB-012  | RLS policy complexa em `messages.INSERT` (triple nested EXISTS)              | migrations/012_create_messages         |
| TD-DB-013  | `search_results_cache` sem pg_cron global cleanup                            | migrations/026_search_results_cache    |
| TD-DB-014  | `search_results_store.expires_at` sem cron cleanup                           | migrations/search_results_store        |
| TD-DB-015  | Alert digest scan index missing                                              | migrations/alert_preferences           |

### MEDIUM

| ID         | Débito                                                                       |
|------------|------------------------------------------------------------------------------|
| TD-DB-020  | `audit_events` sem `is_active` flag (soft-delete)                            |
| TD-DB-021  | `classification_feedback` table status unclear (shipped vs WIP)              |
| TD-DB-022  | `pncp_raw_bids.data_*` nullable — 5-10% bids excluded em filtros             |
| TD-DB-023  | `health_checks` manual cleanup (30-day)                                      |
| TD-DB-024  | `stripe_webhook_events.payload` PII plaintext (LGPD risk)                    |

### LOW

| ID         | Débito                                                                       |
|------------|------------------------------------------------------------------------------|
| TD-DB-030  | Sem `down.sql` rollback templates                                            |
| TD-DB-031  | Duplicate trigger functions (FIXED via DEBT-001)                             |
| TD-DB-032  | Soft FK `pncp_raw_bids.crawl_batch_id` (documented trade-off)                |
| TD-DB-033  | `search_results_store.user_id` NO ACTION vs sister CASCADE (inconsistent)    |

**Subtotal Database: 18 débitos** (4 already fixed; 14 open)

---

## 3. Débitos de Frontend/UX (Fonte: Phase 3)

⚠️ **PENDENTE revisão do @ux-design-expert (Phase 6)**

### CRITICAL

| ID         | Débito                                                         | File/Path (espalhado)                   |
|------------|----------------------------------------------------------------|-----------------------------------------|
| TD-FE-001  | 296 `any` types em TypeScript                                  | frontend/**/*.tsx                       |
| TD-FE-002  | Shepherd.js hardcoded HTML — screen readers broken             | frontend/components/ShepherdTour.tsx    |
| TD-FE-003  | 139 inline `style={{...}}` bypassam Tailwind                   | frontend/**/*.tsx                       |

### HIGH

| ID         | Débito                                                                    |
|------------|---------------------------------------------------------------------------|
| TD-FE-004  | 194 inline hex colors bypassam design tokens                              |
| TD-FE-005  | 62% `<button>` nativo em vez de `<Button>` CVA                            |
| TD-FE-006  | Kanban (@dnd-kit) sem keyboard nav — WCAG 2.1 AA gap                      |
| TD-FE-007  | ~88% "use client" directives — underutiliza RSC                           |
| TD-FE-008  | Sem visual regression testing                                             |

### MEDIUM

| ID         | Débito                                                                    |
|------------|---------------------------------------------------------------------------|
| TD-FE-010  | i18n não implementado (strings hardcoded pt-BR)                           |
| TD-FE-011  | Sem Storybook                                                             |
| TD-FE-012  | Framer Motion/dnd-kit não tree-shaken                                     |
| TD-FE-013  | SSE reconnection não surface para user                                    |
| TD-FE-014  | Image optimization incompleta (`<Image>` nem sempre usado)                |
| TD-FE-015  | Loading state inconsistency (skeleton vs spinner)                         |
| TD-FE-016  | Error messages genéricos ("Erro inesperado")                              |
| TD-FE-017  | Shepherd tour não dismissível persistente                                 |
| TD-FE-018  | Bottom nav mobile não sticky durante scroll                               |
| TD-FE-019  | Cache freshness unclear para user                                         |
| TD-FE-020  | Form validation errors fáceis de perder                                   |
| TD-FE-021  | Blog content não responsivo (images overflow mobile)                      |

### LOW

| ID         | Débito                                                                    |
|------------|---------------------------------------------------------------------------|
| TD-FE-030  | Toast positioning em mobile sub-ótimo                                     |
| TD-FE-031  | Missing JSDoc em components core                                          |
| TD-FE-032  | `Button.examples.tsx` órfão (não em Storybook)                            |

**Subtotal Frontend: 23 débitos**

---

## 4. Matriz Preliminar Consolidada

| ID          | Débito                                               | Área      | Severidade | Esforço Est. | Prioridade Prelim |
|-------------|------------------------------------------------------|-----------|------------|--------------|-------------------|
| TD-SYS-001  | CRIT-080 SIGSEGV                                     | Backend   | CRIT       | 16-40h       | P0                |
| TD-SYS-002  | PNCP page size 50                                    | Integr    | CRIT       | 4h (detect)  | P0                |
| TD-SYS-003  | Railway 120s timeout                                 | Infra     | CRIT       | 8-16h        | P0                |
| TD-SYS-004  | Migration CI                                         | DevOps    | CRIT       | ✅ DONE      | ✅                |
| TD-SYS-005  | search.py monolítico                                 | Backend   | CRIT       | 24-40h       | P1                |
| TD-DB-004   | purge_old_bids cron                                  | DB        | CRIT       | 0.5h         | P0                |
| TD-FE-001   | 296 `any` types                                      | Frontend  | CRIT       | 24-40h       | P1                |
| TD-FE-002   | Shepherd.js a11y                                     | Frontend  | CRIT       | 16-24h       | P1                |
| TD-FE-003   | 139 inline styles                                    | Frontend  | CRIT       | 16-24h       | P2                |
| TD-SYS-010  | L1 cache não shared                                  | Backend   | HIGH       | 8h           | P2                |
| TD-SYS-011  | Feature flags 3 places                               | Backend   | HIGH       | 8-16h        | P2                |
| TD-SYS-012  | Setores duplicados                                   | Backend/FE| HIGH       | 4h           | P1                |
| TD-SYS-013  | Dedup 6-24h window                                   | Backend   | HIGH       | 16h          | P2                |
| TD-SYS-014  | LLM concurrency                                      | Backend   | HIGH       | 16-24h       | P1                |
| TD-SYS-015  | FTS Português                                        | Backend   | HIGH       | 8-16h        | P2                |
| TD-SYS-016  | search_cache growth                                  | DB        | HIGH       | 1h           | P0                |
| TD-SYS-017  | Rate limit público                                   | Security  | HIGH       | 4-8h         | P1                |
| TD-SYS-018  | LLM cost cap                                         | Cost      | HIGH       | 4-8h         | P1                |
| TD-DB-010   | stripe webhook RLS admin                             | DB        | HIGH       | 1h           | P1                |
| TD-DB-011   | profiles.email UNIQUE                                | DB        | HIGH       | 2-4h         | P1                |
| TD-DB-012   | messages RLS complexity                              | DB        | HIGH       | 4-6h         | P2                |
| TD-DB-013   | search_cache cron                                    | DB        | HIGH       | 0.5h         | P0                |
| TD-DB-014   | search_store cron                                    | DB        | HIGH       | 0.5h         | P0                |
| TD-DB-015   | alert digest index                                   | DB        | HIGH       | 1h           | P2                |
| TD-FE-004   | 194 inline hex                                       | Frontend  | HIGH       | 8-16h        | P2                |
| TD-FE-005   | `<button>` → `<Button>`                              | Frontend  | HIGH       | 8h           | P1                |
| TD-FE-006   | Kanban keyboard                                      | Frontend  | HIGH       | 8-16h        | P1                |
| TD-FE-007   | "use client" overuse                                 | Frontend  | HIGH       | 40-56h       | P3                |
| TD-FE-008   | Visual regression                                    | QA        | HIGH       | 8-16h        | P2                |

**Total preliminar de débitos**: 61 (20 sys + 18 db + 23 fe)

---

## 5. Perguntas para Especialistas

### Para @data-engineer (Phase 5)

1. O `purge_old_bids()` cron está configurado em prod? Sem isso, a table excede 500MB FREE tier em 3-4 semanas.
2. Por que `pncp_raw_bids.is_active=false` soft-delete vs hard delete? Audit trail requirement?
3. `partner_referrals` table — feature shipped ou WIP? Pouco referenciada em código.
4. `classification_feedback` table — shipped ou optional? Conditional checks em migrations sugerem optional.
5. Service role bypass wide-open em quase todas tabelas — intencional ou deve ser narrowed?
6. `messages.INSERT` RLS triple nested EXISTS — refactor ou accept?
7. `profiles.email` UNIQUE — adicionar? Duplicate account risk real.
8. PII em `stripe_webhook_events.payload` — mask ou archive após 7 days?
9. `organizations.owner_id` ON DELETE RESTRICT — se owner morre, org orfã. Soft-delete?
10. Avaliar PostgreSQL FTS Portuguese dictionary tuning (TD-SYS-015)?

### Para @ux-design-expert (Phase 6)

1. Server Components strategy — atualmente 88% client-side. Migration plan?
2. TypeScript strict mode — quando habilitar? Blocker para 296 `any` types?
3. Design token enforcement — ESLint (`no-arbitrary-values`) ou code review?
4. i18n roadmap — retrofit agora ou deferir? LATAM roadmap?
5. Storybook — implementar quando?
6. `<Button>` migration — 62% ainda `<button>` nativo. Codemod aprovado?
7. Kanban keyboard nav — prioritize WCAG 2.1 AA compliance?
8. Performance budget targets — LCP/FID/CLS?
9. Mobile-first vs desktop-first — oficial stance?
10. Visual regression tool choice — Percy, Chromatic, Loki?

### Para @qa (Phase 7)

1. Gaps de testing identificados acima são completos? (visual regression, load test, chaos, contract)
2. Riscos cruzados entre TD-SYS-001 (SIGSEGV) e feature flags/rollout — como mitigar?
3. Dependências: TD-SYS-005 (search.py decomposition) precisa ser antes de TD-SYS-014 (LLM async)?
4. Testes necessários pós-resolução de cada CRIT/HIGH?
5. Parecer final: assessment está completo o suficiente para seguir a Planning (Epic + Stories)?

---

## 6. Hotspots Consolidados

### Backend (20 débitos)
- CRITICAL: 5 (SIGSEGV, PNCP 50, Railway 120s, search.py mono, migration CI defended)
- HIGH: 9 (cache, feature flags, dedup, LLM, FTS, rate limit, cost cap)
- Concentração: `backend/routes/search.py`, `llm_arbiter.py`, `cache.py`

### Database (18 débitos, 4 fixed)
- CRITICAL OPEN: 1 (purge_old_bids cron)
- HIGH: 6 (RLS policies, UNIQUE email, messages complexity, cleanup crons)
- Concentração: `supabase/migrations/` RLS + retention

### Frontend (23 débitos)
- CRITICAL: 3 (any types, Shepherd a11y, inline styles)
- HIGH: 5 (hex colors, button migration, kanban keyboard, RSC, visual regression)
- Concentração: type safety + design system adoption

### Cross-Cutting
- **Testing**: 135 FE + 169 BE test files; 0 failures; mas visual regression ausente
- **Observability**: OTEL limitado por CRIT-080; Sentry parcial
- **Docs**: feature flags doc inconsistente; sem down.sql templates

---

## 7. Proposta de Priorização Inicial

**P0 — Storage Quota & Production Critical (~5h total + ongoing):**
- TD-DB-004: Schedule purge_old_bids cron (0.5h)
- TD-DB-013: Schedule search_results_cache cleanup cron (0.5h)
- TD-DB-014: Schedule search_results_store cleanup cron (0.5h)
- TD-SYS-016: search_results_cache growth (overlap com TD-DB-013)
- TD-SYS-001: CRIT-080 SIGSEGV investigation — deep dive (ongoing)
- TD-SYS-003: Railway 120s timeout — time budgets audit (8-16h)

**P1 — Critical Path (1-2 sprints, ~80-120h):**
- TD-SYS-005: search.py decomposition (24-40h)
- TD-FE-001: TypeScript strict + any removal (24-40h)
- TD-FE-002: Shepherd.js a11y replacement (16-24h)
- TD-SYS-012: Setores sync automatizado (4h)
- TD-FE-005: `<button>` → `<Button>` codemod (8h)
- TD-FE-006: Kanban keyboard nav (8-16h)
- TD-SYS-014: LLM async + batching (16-24h)
- TD-SYS-017: Rate limit público (4-8h)
- TD-SYS-018: LLM cost cap (4-8h)
- TD-DB-010: Stripe webhook admin RLS (1h)
- TD-DB-011: profiles.email UNIQUE (2-4h, após cleanup)

**P2 — Maintainability (3-4 sprints, ~60-80h):**
- TD-SYS-010, 011, 013, 015 (backend)
- TD-DB-012, 015 (DB)
- TD-FE-003, 004, 008 (frontend)

**P3 — Strategic (6+ sprints, ~80-120h):**
- TD-FE-007: RSC migration (40-56h)
- TD-FE-010: i18n retrofit (TBD)
- TD-FE-011: Storybook (TBD)

---

## 8. Próximos Passos

1. ✅ **Phase 4 (este DRAFT)** — consolidação inicial
2. ➡️ **Phase 5** — @data-engineer revisa seção 2, estima horas, priorização DB
3. ➡️ **Phase 6** — @ux-design-expert revisa seção 3, estima horas, priorização UX
4. ➡️ **Phase 7** — @qa review geral, gaps, riscos cruzados, parecer APPROVED/NEEDS WORK
5. ➡️ **Phase 8** — @architect finaliza `docs/prd/technical-debt-assessment.md` incorporando todos os inputs
6. ➡️ **Phase 9** — @analyst cria `docs/reports/TECHNICAL-DEBT-REPORT.md` (executivo para stakeholders)
7. ➡️ **Phase 10** — @pm cria Epic + Stories baseadas na priorização final

---

**Document Status**: DRAFT v1 (2026-04-14) — Phase 4 of brownfield-discovery. Aguardando reviews dos especialistas.
