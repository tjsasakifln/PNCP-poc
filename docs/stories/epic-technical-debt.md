# EPIC: Resolucao de Debitos Tecnicos -- SmartLic

**ID:** EPIC-DEBT-2026
**Data:** 2026-03-23
**Owner:** @pm (Morgan)
**Status:** Draft
**Source:** `docs/prd/technical-debt-assessment.md` (FINAL v1.0, 54 items, ~196h, 6 batches)
**Supersedes:** Previous epic (76 items / 5 waves / ~259h) -- assessment was re-reviewed by specialists (Phases 5-7), 18% error rate corrected, 6 items removed as already resolved.

---

## Objetivo

Resolver 54 debitos tecnicos identificados na avaliacao formal de divida tecnica (Brownfield Discovery Phase 10), eliminando riscos de seguranca, memory leaks em producao, gaps de acessibilidade, e monolitos de codigo que impedem onboarding de desenvolvedores e aumentam risco de regressao.

**Justificativa de negocio:**
- **Seguranca:** Dual Stripe webhook router pode causar double-processing de pagamentos (DEBT-324)
- **Estabilidade:** `_plan_status_cache` sem limite cresce indefinidamente em producao (DEBT-323, CRITICAL)
- **Aquisicao:** Landing page renderiza 13 componentes client-side, prejudicando LCP e SEO (TD-M07)
- **Compliance:** Gaps de acessibilidade (WCAG 2.1) bloqueiam expansao para clientes governamentais (XC-06)
- **Velocidade de desenvolvimento:** 6 arquivos backend >1500 LOC dificultam manutencao e code review

## Escopo

### Incluido
- Todos os 54 debitos catalogados no assessment FINAL
- 6 batches de resolucao (0-5), ordenados por risco e ROI
- Migrations de banco (NOT NULL, CHECK constraints, cache eviction fix)
- Decomposicao de monolitos backend (filter, schemas, webhooks, jobs, quota, cache)
- Conversao RSC da landing page (islands pattern)
- Fixes de acessibilidade (screen reader, viability badges, duplicate IDs)
- Cleanup de dead code (ComprasGov, feature flags, compat shims)

### Excluido
- Rewrite completo de arquitetura (apenas decomposicao incremental com facade pattern)
- Mudancas de stack (permanece FastAPI + Next.js)
- DEBT-311 (test LOC ratio 1.87x -- aceito como normal pelo QA)
- DEBT-321 (blog.ts hardcoded -- decisao intencional de design)
- Novas features -- este epic e puramente de debt reduction

## Criterios de Sucesso

| Metrica | Antes | Depois (target) |
|---------|-------|-----------------|
| Backend monolith files >1500 LOC | 6 | 0 |
| Frontend HIGH debt items | 2 | 0 |
| CRITICAL items abertos | 1 | 0 |
| WCAG a11y violations (axe-core) | Desconhecido | 0 (paginas primarias) |
| Landing page LCP | >3s (estimado) | <2.5s |
| Client JS bundle (landing) | Baseline | -40KB+ gzipped |
| Open DB integrity items | 4 | 0 |
| Backend tests pass | 7656 | 7656 (zero regressions) |
| Frontend tests pass | 5733 | 5733 (zero regressions) |
| OpenAPI schema | Baseline | Unchanged after decomposition |

## Timeline

Assumindo 1 desenvolvedor full-time (~6h/dia produtivas):

| Batch | Story | Horas | Duracao | Inicio (relativo) | Dependencias |
|-------|-------|-------|---------|-------------------|--------------|
| 0 | STORY-DEBT-0: Stripe Webhook Audit | 3h | 0.5 dia | Dia 1 | Nenhuma |
| 1 | STORY-DEBT-1: Quick Wins (DB + Backend) | 5h | 1 dia | Dia 2 | Nenhuma |
| 2 | STORY-DEBT-2: Landing Performance | 10h | 2 dias | Dia 3 | Independente |
| 3 | STORY-DEBT-3: Security + A11y | 17h | 3 dias | Dia 5 | Batch 0 (DEBT-324 -> DEBT-307) |
| 4 | STORY-DEBT-4: Architecture Decomposition | 32h | 5.5 dias | Dia 8 | Pode paralelizar com Batch 3 |
| 5 | STORY-DEBT-5: Polish + Cleanup | 73h | 12 dias | Dia 14 | Batches 1-4 concluidos |
| | **Total** | **~140h core** | **~25 dias** | | |

**Nota:** Batch 5 inclui ~27h de items LOW/backlog que podem ser priorizados oportunisticamente durante feature work ao inves de blocos dedicados.

## Budget

| Item | Valor |
|------|-------|
| Esforco total estimado | ~196h (140h core batches 0-4 + 56h backlog batch 5) |
| Custo estimado (R$150/h dev) | R$29.400 |
| Custo minimo (Batches 0-4 only) | R$10.050 (67h) |
| Timeline minima (Batches 0-4) | ~12 dias uteis |

## Stories

| ID | Titulo | Batch | Prioridade | Horas | Arquivo |
|----|--------|-------|------------|-------|---------|
| STORY-DEBT-0 | Stripe Webhook Audit + Fix | 0 | P0 | 3h | [story-debt-0-webhook-audit.md](story-debt-0-webhook-audit.md) |
| STORY-DEBT-1 | Quick Wins (DB Integrity + Backend Fixes) | 1 | P0 | 5h | [story-debt-1-quick-wins.md](story-debt-1-quick-wins.md) |
| STORY-DEBT-2 | Landing Page RSC + Performance | 2 | P1 | 10h | [story-debt-2-landing-performance.md](story-debt-2-landing-performance.md) |
| STORY-DEBT-3 | Security Decomposition + Accessibility | 3 | P1 | 17h | [story-debt-3-security-a11y.md](story-debt-3-security-a11y.md) |
| STORY-DEBT-4 | Backend Module Decomposition | 4 | P2 | 32h | [story-debt-4-architecture.md](story-debt-4-architecture.md) |
| STORY-DEBT-5 | Polish, Cleanup + DX Improvements | 5 | P3 | 73h | [story-debt-5-polish.md](story-debt-5-polish.md) |

## Riscos

| Risco | Severidade | Mitigacao |
|-------|------------|-----------|
| Monolith decomposition quebra imports de teste | HIGH | Decomposicao incremental (1 arquivo por vez). Full test suite (7656 tests) apos cada move. Facade `__init__.py` preserva imports existentes. |
| Double-processing de webhooks corrompeu dados de billing | HIGH | Batch 0 audit primeiro. Verificar logs de producao, Stripe Dashboard URL, idempotency keys. |
| filter/core.py decomposition regressao | HIGH | Maior risco: 3871 LOC + 14 test files (3704 LOC). Preservar `from filter import X`. Coverage >80% antes de iniciar. |
| Landing RSC migration quebra Framer Motion animations | MEDIUM | Islands pattern: RSC wrapper + client animation children. Build-time error detection (`npm run build` fails on RSC import errors). Visual regression tests com Playwright screenshots. |
| Feature flag cleanup remove flag ativa em producao | MEDIUM | Grep usage em FE + BE antes de remover qualquer flag. Cross-reference ambos codebases. |
| Redis failure modes nao avaliadas neste assessment | MEDIUM | Gap reconhecido. Avaliar durante proximo incident review (CB fail open/closed, rate limit behavior, reconnection). |

## Dependencias

| Dependencia | Tipo | Impacto |
|-------------|------|---------|
| DEBT-324 audit -> DEBT-307 decomp | Interna (Batch 0 -> Batch 3) | Nao decompor webhooks antes de auditar duplicacao |
| jest-axe setup (TD-L01) -> a11y fixes | Interna (Batch 5 -> Batch 3) | Recomendacao: iniciar Batch 3 com setup jest-axe para prevenir regressao |
| DEBT-301/302/305 decomp -> DEBT-304 packaging | Interna (Batch 4) | Decompor modulos individuais antes de reorganizar packages |
| TD-H02 (auth unification) -> TD-NEW-01 (duplicate IDs) | Interna (Batch 3) | Resolver duplicate IDs durante unificacao de auth |
| Stripe Dashboard access | Externa | Necessario para Batch 0 webhook URL audit |
| Railway production logs | Externa | Necessario para Batch 0 log analysis |
| Supabase migration pipeline | Externa | Batches 1, 4 requerem `supabase db push` |

---

*Gerado 2026-03-23 por @pm (Morgan) durante Brownfield Discovery Phase 10.*
*Baseado no Technical Debt Assessment FINAL v1.0 (54 items, ~196h, 6 batches).*
*Supersedes previous epic (76 items / 5 waves / ~259h) based on specialist-reviewed assessment with 18% error correction.*
