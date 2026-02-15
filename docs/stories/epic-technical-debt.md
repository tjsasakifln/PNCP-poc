# Epic: Resolucao de Debito Tecnico v2.0

## SmartLic/BidIQ -- Remediacao Brownfield

**Epic ID:** EPIC-TD-v2
**Criado:** 2026-02-15
**Atualizado:** 2026-02-15
**Substitui:** EPIC-TD v1.0 (2026-02-11, commit `808cd05`, stories STORY-200 a STORY-203)
**Owner:** @pm
**Fonte Tecnica:** [`docs/prd/technical-debt-assessment.md`](../prd/technical-debt-assessment.md) (FINAL v2.0, 87 itens)
**Fonte Executiva:** [`docs/reports/TECHNICAL-DEBT-REPORT.md`](../reports/TECHNICAL-DEBT-REPORT.md) (v2.0)
**Commit Baseline:** `b80e64a` (branch `main`)
**Aprovado Por:** @architect (Helix), @data-engineer (Datum), @ux-design-expert (Pixel), @qa (Quinn)

---

## Objetivo

Resolver sistematicamente os 87 itens de debito tecnico identificados durante a auditoria brownfield v2.0 do SmartLic/BidIQ, priorizando seguranca de dados, integridade funcional, confianca do usuario e sustentabilidade do codigo. A resolucao esta organizada em 4 sprints ao longo de 8-10 semanas, com investimento estimado de R$ 54.000 (base) a R$ 70.200 (com margem 1.3x).

---

## Escopo

### Numeros Consolidados

| Metrica | Valor |
|---------|-------|
| Total de debitos | **87** |
| Criticos (CRITICAL) | **3** |
| Altos (HIGH) | **14** |
| Medios (MEDIUM) | **36** |
| Baixos (LOW) | **34** |
| Esforco total estimado | **~360h** |
| Custo base (R$150/h) | **R$ 54.000** |
| Custo com margem 1.3x | **R$ 70.200** |
| Prazo estimado | **8-10 semanas (4 sprints)** |

### Distribuicao por Area

| Area | Debitos | Horas | Custo |
|------|---------|-------|-------|
| Sistema/Backend (infraestrutura, APIs, processamento) | 24 | 143h | R$ 21.450 |
| Banco de Dados (seguranca, integridade, performance) | 17 | 23h | R$ 3.450 |
| Frontend/UX (componentes, acessibilidade, consistencia) | 46 | 194h | R$ 29.100 |
| **Total** | **87** | **360h** | **R$ 54.000** |

### Distribuicao por Urgencia

| Prioridade | Itens | Horas | Custo |
|------------|-------|-------|-------|
| P0 -- Imediato | 8 (+verificacao) | 11,5h | R$ 1.725 |
| P1 -- Proximo sprint | 10 | 35,5h | R$ 5.325 |
| P2 -- 4-6 semanas | 18 | 153h | R$ 22.950 |
| P3 -- Backlog | 51 | 157h | R$ 23.550 |

---

## Orcamento e ROI

**Fonte:** [Relatorio Executivo v2.0](../reports/TECHNICAL-DEBT-REPORT.md)

| Sprint | Investimento | Riscos Eliminados | ROI |
|--------|-------------|-------------------|-----|
| Sprint 0 (1 semana) | R$ 2.250 | R$ 150.000+ (seguranca + cadastro) | **67:1** |
| Sprint 1 (2 semanas) | R$ 3.600 | R$ 80.000+ (confianca + compliance) | **22:1** |
| Sprint 2 (3 semanas) | R$ 10.800 | R$ 60.000+ (velocidade + qualidade) | **6:1** |
| Sprint 3 (2 semanas) | R$ 8.400 | R$ 40.000+ (cobertura de testes) | **5:1** |
| **Total Sprints 0-3** | **R$ 25.050** | **R$ 330.000+** | **13:1** |
| Backlog (ongoing) | R$ 23.550 | Polimento e otimizacoes | -- |

**Custo potencial de NAO resolver:** R$ 350.000 - R$ 650.000

**Para cada R$ 1 investido, evitamos entre R$ 6 e R$ 12 em riscos.**

---

## Criterios de Sucesso

1. **Todos os 3 itens CRITICAL resolvidos** -- verificado por testes automatizados e revisao de codigo
2. **Todos os 14 itens HIGH resolvidos** -- verificado por testes automatizados e revisao de codigo
3. **Zero vulnerabilidades RLS** -- testes de seguranca SEC-T01 a SEC-T08 passando
4. **Cadastro de novos usuarios funcional** -- signup cria `plan_type = 'free_trial'` sem erros
5. **Pagina de precos clara e confiavel** -- sem "9.6x", valores consistentes entre paginas
6. **Frontend test coverage >= 60%** -- enforced por Jest threshold (pos-Sprint 3)
7. **Backend test coverage >= 70%** -- enforced por pytest-cov threshold (mantido)
8. **CI pipeline green** -- backend (pytest + ruff + mypy) e frontend (jest) passando
9. **Nenhum arquivo > 500 linhas no backend critico** -- search_pipeline.py decomposto
10. **Prop drilling eliminado na busca** -- SearchForm/SearchResults com 0 props via Context
11. **22 testes de quarentena reativados** -- diretorio `quarantine/` vazio
12. **34 pontos positivos preservados** -- strengths listados na Secao 9 do assessment verificados intactos

---

## Timeline

```
Semana 1        Semana 2-3         Semana 4-6          Semana 7-8+
Sprint 0        Sprint 1           Sprint 2            Sprint 3
~15h            ~24h               ~72h                ~56h
P0 Criticos     P1 Seguranca       P2 Refatoracao      P2-P3 Testes
                + Confianca        + Consolidacao       + Polimento
```

---

## Stories

| Story ID | Titulo | Sprint | Prioridade | Esforco | Dependencias |
|----------|--------|--------|------------|---------|--------------|
| **Sprint 0: Verificacao e Quick Wins (1 semana, ~15h)** | | | | | |
| STORY-TD-001 | Verificacao de producao e migration 027 | Sprint 0 | P0 | 8h | Nenhuma |
| STORY-TD-002 | Fix precos divergentes e UX trust | Sprint 0 | P0 | 4h | Nenhuma |
| STORY-TD-003 | Split requirements + cleanup | Sprint 0 | P0 | 3h | Nenhuma |
| **Sprint 1: Seguranca e Correcoes (2 semanas, ~24h)** | | | | | |
| STORY-TD-004 | Seguranca restante e documentacao DB | Sprint 1 | P1 | 4h | TD-001 |
| STORY-TD-005 | Dialog primitive e acessibilidade | Sprint 1 | P1 | 4h | Nenhuma |
| STORY-TD-006 | Mensagens de erro e UX de navegacao | Sprint 1 | P1 | 8h | Nenhuma |
| STORY-TD-007 | Async fixes e CI quality gates | Sprint 1 | P1 | 4h | Nenhuma |
| STORY-TD-008 | PNCP client consolidation (inicio) | Sprint 1 | P1 | 5h | Nenhuma |
| **Sprint 2: Consolidacao e Refatoracao (3 semanas, ~72h)** | | | | | |
| STORY-TD-009 | PNCP client consolidation (conclusao) | Sprint 2 | P1 | 11h | TD-008 |
| STORY-TD-010 | Decomposicao de search_pipeline.py | Sprint 2 | P2 | 16h | Nenhuma |
| STORY-TD-011 | Unquarantine testes + E2E safety net | Sprint 2 | P2 | 16h | Nenhuma |
| STORY-TD-012 | Search state refactor: Context + useReducer | Sprint 2 | P2 | 32h | TD-011 (parcial) |
| **Sprint 3: Qualidade e Cobertura (2 semanas, ~56h)** | | | | | |
| STORY-TD-013 | Testes unitarios para nova arquitetura de busca | Sprint 3 | P2 | 16h | TD-012 |
| STORY-TD-014 | Dynamic imports + consolidacao de planos + icones | Sprint 3 | P2 | 16h | Nenhuma |
| STORY-TD-015 | Testes de pipeline, onboarding e middleware | Sprint 3 | P2-P3 | 24h | Nenhuma |
| **Sprint 2-3: Items P2 de DB e Backend** | | | | | |
| STORY-TD-016 | DB improvements: FK, analytics, triggers | Sprint 2 | P2 | 16h | TD-001 |
| STORY-TD-017 | Backend scalability: Redis, storage, routes | Sprint 2-3 | P2 | 24h | Nenhuma |
| STORY-TD-018 | Consolidacao plan data + search button sticky | Sprint 2 | P2 | 8h | Nenhuma |
| **Backlog** | | | | | |
| STORY-TD-019 | Backlog -- Polimento e Otimizacao | Sprint 3+ | P3 | ~157h | TD-001 a TD-018 (parciais) |

**Total das stories TD-001 a TD-018:** ~206h (Sprint 0-3)
**Total do backlog TD-019:** ~157h (ongoing)
**Total geral:** ~363h (alinhado com assessment ~360h)

---

## Grafo de Dependencias

```
[PREREQUISITO: Queries V1-V5 de verificacao em producao]
        |
        v
TD-001 (Sprint 0: DB P0) -------> TD-004 (Sprint 1: DB P1)
  |                                   |
  +-----> TD-016 (Sprint 2: DB P2)    +-----> TD-019 (backlog DB)
  |
  +-----> TD-003 (Sprint 0: cleanup, paralelo)
  |
  +-----> TD-002 (Sprint 0: UX trust, paralelo)

TD-005 (Sprint 1: A11Y) ---------> TD-019 (backlog: UX-NEW-03 usa Dialog)

TD-008 (Sprint 1: SYS-02 inicio) -> TD-009 (Sprint 2: SYS-02 conclusao)

TD-011 (Sprint 2: unquarantine) --> TD-012 (Sprint 2: search refactor)
                                        |
                                        +----> TD-013 (Sprint 3: testes novos)

TD-012 (search refactor) ----------> TD-013 (testes unitarios)
                                        |
                                        +----> TD-015 (testes adicionais, parcial)

TD-010 (pipeline decomposition) --- independente
TD-014 (dynamic imports) ---------- independente
TD-006 (mensagens erro) ----------- independente
TD-007 (async + CI) --------------- independente
TD-017 (scalability) -------------- independente
TD-018 (plan data + sticky) ------- independente
```

---

## Riscos Cruzados (do Assessment v2.0)

| # | Risco | Probabilidade | Impacto | Mitigacao |
|---|-------|---------------|---------|-----------|
| CR-01 | Migration 027 falha em producao | Media | CRITICAL | Queries V1-V5 antes. Script de rollback. Staging se disponivel. |
| CR-02 | Refactor prop drilling quebra testes e E2E | Alta | HIGH | E2E como safety net. Unquarantine ANTES do refactor. |
| CR-03 | Correcao de RLS bloqueia funcionalidade | Baixa | HIGH | Auditar uso de service_role key antes. |
| CR-04 | Remocao sync client quebra fallback single-UF | Media | HIGH | Verificar PNCPLegacyAdapter.fetch() antes de remover. |
| CR-05 | Atualizacao parcial de plan_type cria inconsistencia | Media | CRITICAL | 4 code paths corrigidos atomicamente no Sprint 0. |
| CR-09 | time.sleep -> asyncio.sleep expoe race condition | Baixa | MEDIUM | Verificar save_search_session. |
| CR-10 | search_pipeline.py dificulta correcoes backend | Alta | MEDIUM | Decomposicao no Sprint 2. |

---

## Pontos Positivos a Preservar

Durante a resolucao de debitos, os **34 pontos positivos** listados na Secao 9 do assessment DEVEM ser preservados. PRs que degradem estes itens requerem justificativa explicita. Os mais criticos:

**Backend:** Retry com exponential backoff + jitter, fetch paralelo de UFs com Semaphore, circuit breaker, filtragem fail-fast, LLM Arbiter pattern, fallback multi-camada de subscription, mascaramento PII, idempotencia Stripe, correlation ID, structured JSON logging.

**Database:** Funcoes atomicas de quota com FOR UPDATE, 100% RLS coverage, 26 migrations documentadas, partial indexes, GIN trigram index, pg_cron retention, audit logging privacy-first.

**Frontend:** Design system CSS custom properties, dark/light mode FOUC-free, skip navigation WCAG 2.4.1, prefers-reduced-motion, SSE progress real-time, keyboard shortcuts, LGPD compliance, resiliencia UX (CacheBanner, DegradationBanner).

---

## Mudancas vs Epic v1.0 (2026-02-11)

| Aspecto | v1.0 (Feb 11) | v2.0 (Feb 15) |
|---------|---------------|---------------|
| Commit baseline | `808cd05` | `b80e64a` |
| Total de debitos | 90 | 87 (resolucoes + novos + deduplicacoes) |
| Esforco estimado | ~320-456h | ~360h (mais preciso) |
| Custo estimado | R$ 45.000 | R$ 54.000 |
| Risco de nao resolver | R$ 100-250K | R$ 350-650K (refinado) |
| Stories | STORY-200 a STORY-203 (4 stories amplas) | STORY-TD-001 a STORY-TD-019 (19 stories granulares) |
| Sprints | 4 sprints genericos | Sprint 0 (P0) + Sprint 1-3 com items especificos |
| CRITICALs | 13 | 3 (muitos resolvidos desde v1.0) |
| HIGHs | 19 | 14 |

**Stories STORY-200 a STORY-203 sao consideradas obsoletas** e substituidas pelas STORY-TD-001 a STORY-TD-019.

---

## Documentos Relacionados

- [`docs/prd/technical-debt-assessment.md`](../prd/technical-debt-assessment.md) -- Assessment tecnico completo v2.0 (87 itens)
- [`docs/reports/TECHNICAL-DEBT-REPORT.md`](../reports/TECHNICAL-DEBT-REPORT.md) -- Relatorio executivo v2.0 (custos, ROI, timeline)
- [`docs/architecture/system-architecture.md`](../architecture/system-architecture.md) -- Arquitetura do sistema
- [`supabase/docs/SCHEMA.md`](../../supabase/docs/SCHEMA.md) -- Documentacao do schema
- [`supabase/docs/DB-AUDIT.md`](../../supabase/docs/DB-AUDIT.md) -- Auditoria de banco de dados
- [`docs/frontend/frontend-spec.md`](../frontend/frontend-spec.md) -- Especificacao frontend
- [`docs/reviews/db-specialist-review.md`](../reviews/db-specialist-review.md) -- Review @data-engineer
- [`docs/reviews/ux-specialist-review.md`](../reviews/ux-specialist-review.md) -- Review @ux-design-expert
- [`docs/reviews/qa-review.md`](../reviews/qa-review.md) -- Review @qa

---

*Epic criado por @pm em 2026-02-15 baseado no assessment tecnico FINAL v2.0.*
*Aprovado por @architect (Helix), @data-engineer (Datum), @ux-design-expert (Pixel), @qa (Quinn).*
*Commit de referencia: `b80e64a` (branch `main`).*
