# ROADMAP — SmartLic

**Versao:** 3.0 | **Atualizado:** 2026-02-20 | **Status:** GTM Resilience Complete, Active Backlog

---

## Status Atual

```
POC CORE:            [####################] 100% DEPLOYED
GTM LAUNCH:          [####################] 100% (10/10 stories)
GTM FIXES:           [####################] 100% (37 fixes)
GTM RESILIENCE:      [####################] 100% (25/25 stories)
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

---

*Ultima atualizacao: 2026-02-20*
