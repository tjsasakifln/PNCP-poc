# ROADMAP — SmartLic

**Versao:** 4.1 | **Atualizado:** 2026-04-18 | **Status:** Reliability Sprint Complete, Cache Warming Deprecated, Active Backlog

## 2026-04 — Cache Warming Deprecation (DataLake é a fonte)

Decisão arquitetural baseada no novo modelo de dados: Supabase agora armazena ~50K licitações abertas (`pncp_raw_bids`) + 2M+ contratos históricos (`supplier_contracts`, estratégia 100% orgânica de inbound via SEO). Consultas vão ao DB com latência <100ms.

- **Layer 3 cache warming proativo removido** — jobs startup/cron/coverage-check deletados (`cron/cache.py` reduzido a cleanup; `jobs/cron/cache_ops.py` deletado; `cache_warming_job` + `cache_refresh_job` removidos).
- **Feature flags deletadas:** `WARMUP_ENABLED`, `CACHE_WARMING_ENABLED`, `CACHE_REFRESH_ENABLED`, `CACHE_WARMING_POST_DEPLOY_ENABLED` + constantes `WARMING_*`, `CACHE_REFRESH_*`, `WARMUP_*`.
- **Funções admin removidas:** `get_stale_entries_for_refresh`, `get_top_popular_params`, `get_popular_ufs_from_sessions` (consumidas apenas pelos jobs).
- **Cache passivo permanece:** `search_results_cache` (Supabase 24h) + Redis L2 + InMemory L1 + SWR por-request em `cache/swr.py::trigger_background_revalidation`.
- **Stories substituídas (Superseded):** GTM-STAB-007, CRIT-081, CRIT-055, GTM-ARCH-002 marcadas como Superseded.
- **STORY-CIG-BE-cache-warming-deprecate** (branch `fix/cig-be-wave2-tier1-plus-tier2`) — deleta 6 arquivos de teste (~40 testes obsoletos), remove código, atualiza docs.
- **Migration `20260308330000_debt009_ban_cache_warmer.sql` mantida** — conta banida permanece (agora por razão ainda mais forte: não existe mais).


---

## Status Atual

```
POC CORE:            [####################] 100% DEPLOYED
GTM LAUNCH:          [####################] 100% (10/10 stories)
GTM FIXES:           [####################] 100% (37 fixes)
GTM RESILIENCE:      [####################] 100% (25/25 stories)
RELIABILITY SPRINT:  [####################] 100% (13/13 stories, 4 sprints)
TECH DEBT (TD):      [####................] ~20% (19 stories)
UX PREMIUM:          [##..................] ~6% (2/36 stories)
```

**Production:** https://smartlic.tech

---

## Fases Concluidas

### Fase 1 — POC Core (Jan 2026)
PNCP client, filtering engine, Excel export, LLM summaries, Next.js frontend. Deployed Jan 28.

### Fase 2 — Multi-Sector + GTM Launch (Feb 1-14)
15 sectors, Stripe billing, onboarding wizard, trial conversion, SSE progress, PCP integration, pipeline management. 10 GTM stories + 37 production fixes.

### Fase 3 — GTM Resilience (Feb 17-20)
25 stories across 6 tracks. See `docs/gtm-resilience-summary.md` for details.

| Track | Stories | Key Deliverables |
|-------|---------|------------------|
| A — Never Empty | 5 | Fallback cascade, partial results, coverage bar |
| B — Smart Cache | 6 | Two-level cache, SWR, hot/warm/cold priority, admin dashboard |
| C — Coverage UX | 3 | Confidence indicator, freshness, reliability badges |
| D — Classification | 5 | Zero-match LLM, viability assessment, feedback loop |
| E — Observability | 3 | Structured logging, Prometheus metrics, Sentry |
| F — Infrastructure | 3 | ARQ job queue, OpenTelemetry tracing, schema validation |

### Fase 4 — Reliability Sprint (Feb 22-27)
13 stories across 4 sprints. Architecture hardening for multi-worker production.

| Sprint | Stories | Key Deliverables |
|--------|---------|------------------|
| Sprint 0 — Make It Work | STORY-283, 290, 291, 292, 293 | Event loop unblock, Supabase circuit breaker, async search 202 pattern, CI fix |
| Sprint 1 — Make It Reliable | STORY-294, 295, 296, 297, 298 | Redis state externalization, progressive results, bulkhead per source, SSE resumption, unified error UX |
| Sprint 2 — Make It Observable | STORY-299, 300 | SLOs + alerting dashboard, security hardening (CSP, LGPD) |
| Sprint 3 — Make It Competitive | STORY-301, 302 | Email alert system (CRUD, cron, dedup), documentation cleanup |

### Fase 4.1 — GTM Repricing (Feb 25-26)
Market-validated pricing realignment.

| Story | Title | Status |
|-------|-------|--------|
| STORY-277 | Repricing R$1.999 → R$397/mes | Completed |
| STORY-280 | Boleto + PIX via Stripe | Completed |
| STORY-284 | GTM Quick Wins | Completed |

---

## Backlog Ativo

### Technical Debt (TD-001 to TD-019)

Source: `docs/stories/epic-technical-debt.md`

| Sprint | Stories | Focus |
|--------|---------|-------|
| Sprint 0 | TD-001, TD-002, TD-003 | Security (CORS, SQL injection, PII) |
| Sprint 1 | TD-006, TD-007, TD-008 | Architecture (god function, Redis, frontend CI) |
| Sprint 2 | TD-009 to TD-014 | Testing, logging, analytics |
| Sprint 3 | TD-015 to TD-019 | Email, API contracts, polish |

### UX Premium (UX-301 to UX-335)

Source: `docs/stories/EPIC-UX-PREMIUM-2026-02.md` (35 problems from production audit)

| Priority | Stories | Examples |
|----------|---------|----------|
| P0 Critical | UX-301, UX-302, UX-304 | Timeout, progress, filter issues |
| P1 High | UX-305 to UX-318 | Landing, navigation, validation, confirmations |
| P2 Medium | UX-319 to UX-331 | Heartbeat, dark mode, skeletons, keyboard nav |
| P3 Low | UX-332 to UX-335 | Sound feedback, SEO, accessibility |

### Active Feature Stories (STORY-240+)

| Story | Title |
|-------|-------|
| STORY-240 | Buscar licitacoes abertas |
| STORY-241 | Excluir inexigibilidade, ampliar modalidades |
| STORY-242 | Novos setores (rodoviaria, eletricos, hidraulicos) |
| STORY-243 | Renomear setores inclusividade |
| STORY-244 | Copy estrategica landing page |
| STORY-245 | Curadoria acionavel LLM consultor |
| STORY-246 | Experiencia one-click |
| STORY-247 | Onboarding profundo perfil contextualizacao |
| STORY-248 | Precisao absoluta filtros |
| STORY-249 | Sync setores backend/frontend/signup |
| STORY-250 | Gestao pipeline oportunidades |
| STORY-251 | LLM arbiter sector-aware prompts |
| STORY-252 | PNCP API mass timeout/zero results |
| STORY-253 | JWT token refresh fix |
| STORY-254 | Portal transparencia adapter |
| STORY-255 | Querido diario adapter |
| STORY-256 | Sanctions check integration |
| STORY-257A | Backend busca inquebravel |
| STORY-257B | Frontend UX transparente |

### GTM Remaining (GTM-001, GTM-002)

| Story | Title | Status |
|-------|-------|--------|
| GTM-001 | Reescrita copy landing | In progress |
| GTM-002 | Modelo assinatura unico | In progress |

---

## Archived Documentation

Obsolete stories and docs moved to `docs/archive/` (Feb 20, 2026):
- `completed/gtm-resilience/` — 25 GTM-RESILIENCE stories
- `completed/gtm-fixes/` — GTM-FIX production fixes
- `completed/gtm-core/` — GTM-003 to GTM-010
- `completed/features/` — STORY-165 to STORY-185
- `completed/ux/` — UX-303, UX-336
- `superseded/` — STORY-156-164, STORY-200-229 (replaced by TD series)
- Sprint, session, review, ceremony, and investigation artifacts

---

## Historico

| Data | Evento |
|------|--------|
| 2026-01-24 | Project initialized |
| 2026-01-25 | MVP v0.1 complete |
| 2026-01-28 | Production deployment v0.2 |
| 2026-02-03 | Multi-sector expansion v0.3 |
| 2026-02-14 | GTM launch phase v0.4 |
| 2026-02-17 | GTM production fixes (37 fixes) |
| 2026-02-20 | GTM Resilience complete v0.5 (25 stories) |
| 2026-02-20 | Documentation cleanup (180+ files archived) |
| 2026-02-22 | Reliability Sprint started (13 stories, 4 sprints) |
| 2026-02-25 | GTM Repricing — R$1.999 → R$397 (STORY-277) |
| 2026-02-26 | Boleto + PIX payment methods (STORY-280) |
| 2026-02-27 | Reliability Sprint complete v0.5.2 (13/13 stories) |

---

*Ultima atualizacao: 2026-02-27*
