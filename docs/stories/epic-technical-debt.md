# EPIC: Resolução de Débitos Técnicos — SmartLic

**Epic ID:** EPIC-TD-2026Q2
**Status:** Approved (aguardando kickoff)
**Owner:** @pm (Morgan)
**Workflow:** brownfield-discovery v3.1 — Phase 10
**Date Created:** 2026-04-14
**Target Completion:** 2026-07-21 (13-14 semanas)

---

## Objetivo do Epic

Eliminar os 69 débitos técnicos abertos identificados na auditoria brownfield (Phases 1-7), priorizando **bloqueios de produção** (P0), **risk reduction** (P1), e **maintainability** (P2). Entregar SmartLic em estado estruturalmente sustentável, compliance WCAG 2.1 AA / LGPD, e elegível para vendas B2G enterprise.

---

## Escopo

### IN

- Todos os 69 débitos abertos catalogados em `docs/prd/technical-debt-assessment.md`
- 5 débitos QA novos (TD-QA-060 a 064)
- Métricas mensuráveis pré/pós (test coverage, `any` count, Lighthouse, axe-core, Sentry rates)
- Documentação de mudanças (changelog, ADRs)

### OUT

- Novas features de produto (toda capacity vai para débito)
- i18n implementation (TD-FE-010 deferred — depende de decisão LATAM)
- Migração big-bang RSC (TD-FE-007 — opportunistic only)

---

## Critérios de Sucesso

| Métrica                       | Atual               | Meta                | Aceite                       |
|-------------------------------|---------------------|---------------------|------------------------------|
| Backend test coverage         | ~70%                | 80%                 | CI gate                      |
| Frontend test coverage        | ~60%                | 75%                 | CI gate                      |
| TypeScript `any` count        | 296                 | <50                 | `tsc --noEmit` strict        |
| ARIA violations (axe-core)    | desconhecido        | 0 críticas          | Playwright @axe-core         |
| Lighthouse Performance        | desconhecido        | >85                 | Lighthouse CI                |
| Lighthouse Accessibility      | desconhecido        | >95                 | Lighthouse CI                |
| Visual regression diff        | n/a                 | <1%                 | Percy                        |
| pg_cron job success rate      | desconhecido        | >99%                | Sentry alerts                |
| Sentry POST error rate        | alto (CRIT-080)     | <0.1% requests      | Sentry dashboard             |
| `pncp_raw_bids` storage       | unbounded risk      | <300MB sustained    | Supabase metrics             |
| LLM monthly cost              | uncapped            | budget definido     | Prometheus + budget alert    |

---

## Timeline e Budget

- **Esforço estimado**: 282-520h (target 400h)
- **Custo estimado (R$150/h)**: R$ 42.300 — R$ 78.000 (target R$ 60.000)
- **Timeline**: 13-14 semanas (1 dev) ou 8-10 semanas (2 devs)
- **Budget aprovado**: [ ] PENDING — sponsor sign-off

---

## Estrutura de Stories

### Sprint 0 — P0 Critical (Semana 1, ~12-30h)

| Story ID  | Título                                                          | Área | Esforço | Owner            |
|-----------|-----------------------------------------------------------------|------|---------|------------------|
| STORY-1.1 | Implementar pg_cron monitoring + alerts Sentry (TD-DB-040)      | DB   | 4-8h    | @data-engineer   |
| STORY-1.2 | Schedule purge_old_bids cron + smoke test (TD-DB-004)           | DB   | 0.5h    | @data-engineer   |
| STORY-1.3 | Schedule search_results_cache cleanup cron (TD-DB-013)          | DB   | 0.5h    | @data-engineer   |
| STORY-1.4 | Schedule search_results_store cleanup cron (TD-DB-014)          | DB   | 0.5h    | @data-engineer   |
| STORY-1.5 | Implementar Kanban keyboard navigation WCAG (TD-FE-006)         | FE   | 8-16h   | @ux + @dev       |
| STORY-1.6 | CRIT-080 SIGSEGV deep-dive investigation (TD-SYS-001 kickoff)   | BE   | (kickoff) | @architect + @dev |

### Sprint 1 — P1 Foundations (Semanas 2-3, ~40-60h)

| Story ID  | Título                                                          | Área   | Esforço |
|-----------|-----------------------------------------------------------------|--------|---------|
| STORY-2.1 | Implementar Pydantic→TypeScript type generation (TD-QA-064)     | QA     | 4-8h    |
| STORY-2.2 | Codemod `<button>` → `<Button>` (TD-FE-005)                     | FE     | 8h      |
| STORY-2.3 | Humanizar error messages com Sentry trace IDs (TD-FE-016)       | FE     | 4-8h    |
| STORY-2.4 | SSE reconnection feedback banner (TD-FE-013)                    | FE     | 4-8h    |
| STORY-2.5 | Disabled state contrast WCAG fix (TD-FE-050)                    | FE     | 2-4h    |
| STORY-2.6 | Modal ARIA padronization (TD-FE-051)                            | FE     | 4-8h    |
| STORY-2.7 | Stripe webhook RLS admin policy fix (TD-DB-010)                 | DB     | 1h      |
| STORY-2.8 | profiles.email UNIQUE constraint + dedup script (TD-DB-011)     | DB     | 2-4h    |
| STORY-2.9 | Setores backend↔frontend sync automatizado (TD-SYS-012)         | BE/FE  | 4h      |
| STORY-2.10| Rate limit em endpoints públicos (TD-SYS-017)                   | BE     | 4-8h    |
| STORY-2.11| LLM monthly cost cap + Prometheus alerts (TD-SYS-018)           | BE     | 4-8h    |
| STORY-2.12| pncp_raw_bids data_* nullability fix (TD-DB-022)                | DB     | 4-8h    |

### Sprint 2 — P1 Refactor + Test Infra (Semanas 4-5, ~40-70h)

| Story ID  | Título                                                          | Área   | Esforço |
|-----------|-----------------------------------------------------------------|--------|---------|
| STORY-3.1 | search.py decomposition (TD-SYS-005)                            | BE     | 24-40h  |
| STORY-3.2 | TypeScript strict + progressive any removal (TD-FE-001)         | FE     | 24-40h  |
| STORY-3.3 | Load test baseline k6/Grafana (TD-QA-060)                       | QA     | 8-16h   |
| STORY-3.4 | Contract tests PNCP/Stripe Pact ou snapshot (TD-QA-062)         | QA     | 8-12h   |
| STORY-3.5 | E2E billing/subscription flow Playwright (TD-QA-063)            | QA     | 8-16h   |

### Sprint 3 — P1 Perf + A11y (Semanas 6-7, ~30-70h)

| Story ID  | Título                                                          | Área | Esforço |
|-----------|-----------------------------------------------------------------|------|---------|
| STORY-4.1 | LLM async + Batch API integration (TD-SYS-014)                  | BE   | 16-24h  |
| STORY-4.2 | Shepherd.js a11y replacement (TD-FE-002)                        | FE   | 16-24h  |
| STORY-4.3 | ESLint no-arbitrary-values + hex cleanup (TD-FE-004)            | FE   | 8-16h   |
| STORY-4.4 | Railway 120s time budgets audit + tuning (TD-SYS-003)           | BE   | 8-16h   |
| STORY-4.5 | PNCP API breaking change detection alert (TD-SYS-002)           | BE   | 4h      |

### Sprint 4-6 — P2 Maintainability (Semanas 8-13, ~80-140h)

| Story ID  | Título                                                          | Área   | Esforço |
|-----------|-----------------------------------------------------------------|--------|---------|
| STORY-5.1 | L1 cache shared via Redis (TD-SYS-010)                          | BE     | 8h      |
| STORY-5.2 | Feature flags single source of truth (TD-SYS-011)               | BE     | 8-16h   |
| STORY-5.3 | Session dedup eventual consistency mitigation (TD-SYS-013)      | BE     | 16h     |
| STORY-5.4 | PostgreSQL FTS Portuguese custom dictionary (TD-SYS-015)        | BE/DB  | 8-16h   |
| STORY-5.5 | Backend medium cleanup (TD-SYS-020 a 025)                       | BE     | 30-50h  |
| STORY-5.6 | DB medium fixes (TD-DB-012, 015, 020, 021, 024)                 | DB     | 13-23h  |
| STORY-5.7 | DB infrastructure (TD-DB-040, 041, 042 monitoring/backup/pool)  | DB     | 10-20h  |
| STORY-5.8 | Visual regression Percy setup (TD-FE-008)                       | FE/QA  | 8-16h   |
| STORY-5.9 | Storybook setup + canonical components (TD-FE-011)              | FE     | 16-24h  |
| STORY-5.10| Bundle tree-shaking Framer/dnd-kit (TD-FE-012)                  | FE     | 4-8h    |
| STORY-5.11| Image optimization Next.js Image (TD-FE-014)                    | FE     | 4-8h    |
| STORY-5.12| Loading state skeleton padronizar (TD-FE-015)                   | FE     | 4-8h    |
| STORY-5.13| UX micro-fixes bundle (TD-FE-017, 018, 019, 020, 021, 052, 053)| FE     | 25-40h  |
| STORY-5.14| Inline style cleanup ESLint (TD-FE-003)                         | FE     | 16-24h  |
| STORY-5.15| Chaos/failure injection toxiproxy (TD-QA-061)                   | QA     | 16-24h  |
| STORY-5.16| Lighthouse CI + axe-core E2E (G-010, G-011)                     | QA     | 6-12h   |

### Sprint 7+ — P3 Strategic (Semanas 14+, ~80-150h)

| Story ID  | Título                                                          | Área | Esforço |
|-----------|-----------------------------------------------------------------|------|---------|
| STORY-6.1 | RSC opportunistic migration plan + first wave (TD-FE-007)       | FE   | 40-56h  |
| STORY-6.2 | down.sql migration rollback templates (TD-DB-030)               | DB   | 4-8h    |
| STORY-6.3 | Backend low cleanup (TD-SYS-030, 031, 032)                      | BE   | 8-12h   |
| STORY-6.4 | DB low fixes (TD-DB-023, 032, 033)                              | DB   | 2-4h    |
| STORY-6.5 | Frontend polish (TD-FE-030, 031, 032)                           | FE   | 6-13h   |
| STORY-6.6 | Mutation testing Stryker (G-012)                                | QA   | 8-16h   |
| STORY-6.7 | Fuzz testing search filter parser (G-013)                       | QA   | 4-8h    |
| STORY-6.8 | i18n preparation (TD-FE-010) — IF LATAM approved                | FE   | 40h+    |

---

## Dependências Críticas

```
Sprint 0 → Sprint 1:
  STORY-1.1 (cron monitoring) PRECEDE STORY-1.2/1.3/1.4

Sprint 1 → Sprint 2:
  STORY-2.1 (Pydantic→TS) PRECEDE STORY-3.2 (TS strict)

Sprint 2 → Sprint 3:
  STORY-3.1 (search.py decompose) PRECEDE STORY-4.1 (LLM async)
```

---

## Gestão e Cadência

### Cerimônias

- **Daily standup**: 15min, foco em blockers
- **Weekly review** (cada sexta): metrics dashboard + débitos resolvidos vs roadmap
- **Bi-weekly sprint demo**: stakeholders + mostra de improvements quantificados
- **Sprint retro**: ajustes de processo a cada 2 semanas

### Métricas de Acompanhamento

- **Velocity**: stories completed vs planned per sprint
- **Burndown**: hours remaining no epic
- **Quality**: test coverage delta, axe violations delta, Sentry error rate delta
- **Risk**: P0/P1 ainda abertos (target: P0 zerado em sprint 0; P1 <30% em sprint 3)

---

## Riscos e Contingências

### Riscos do Epic

- **R-001**: Sponsor não aprova budget completo → priorizar P0 + P1 only (R$ 25K-45K)
- **R-002**: Dev contratado não disponível → considerar 2 freelancers paralelos para P1
- **R-003**: Compliance B2G urgente → STORY-1.5 deve ser semana 1 sem fail
- **R-004**: CRIT-080 SIGSEGV requer mais que 40h → escalate sponsor + considerar consultoria especializada
- **R-005**: Discoveries adicionais durante execução (>10% scope creep) → buffer de 15% incluído

### Contingências

- Se sprint atrasa >20% → re-baseline timeline em sprint review
- Se P1 não conclui em 4 sprints → diferir P3 strategic; manter P2
- Se métricas pós não atingem meta → criar follow-up epic com gaps remanescentes

---

## Stakeholders

- **Sponsor**: Tiago Sasaki (CEO CONFENGE)
- **Product Owner**: @po (Pax)
- **Tech Lead**: @architect (Aria)
- **Implementing**: @dev (Dex), @data-engineer (Dara), @ux-design-expert (Uma)
- **QA**: @qa (Quinn)
- **DevOps**: @devops (Gage)

---

## Lista de Stories Detalhadas

Cada story acima deve ser detalhada em arquivo individual em `docs/stories/`:

```
docs/stories/
├── epic-technical-debt.md (este arquivo)
├── story-1.1-pg-cron-monitoring.md
├── story-1.2-purge-old-bids-cron.md
├── story-1.3-search-cache-cleanup-cron.md
├── story-1.4-search-store-cleanup-cron.md
├── story-1.5-kanban-keyboard-nav.md
├── story-1.6-sigsegv-investigation.md
├── story-2.1-pydantic-typescript-gen.md
├── story-2.2-button-codemod.md
├── ... (uma story por linha das tabelas Sprint 0-7)
```

**Próximo passo @sm**: Para cada Sprint 0-7 entry, criar arquivo individual seguindo template em `.aios-core/development/templates/story-tmpl.yaml`.

**Comando sugerido**:
```bash
node .aios-core/development/scripts/story-manager.js create \
  --title "STORY-1.2 — Schedule purge_old_bids cron" \
  --epic EPIC-TD-2026Q2 \
  --priority P0 \
  --owner @data-engineer
```

---

**Status**: ✅ Epic approved; aguardando @sm para criar stories individuais e @po para validar drafts.
