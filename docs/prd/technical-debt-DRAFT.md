# Technical Debt Assessment - DRAFT
**BidIQ Uniformes POC v0.2**

**Gerado em:** January 26, 2026
**Status:** PENDING REVIEW
**Para Revisão de:** @data-engineer (skipped - no DB), @ux-design-expert, @qa

---

## 1. Débitos de Sistema (Sistema FastAPI)

Extraído de: `docs/architecture/system-architecture.md`

| ID | Débito | Área | Severidade | Impacto | Esforço (h) | Prioridade |
|----|--------|------|-----------|---------|-----------|-----------|
| SYS-001 | Backend endpoints não implementados | FastAPI | CRÍTICO | Produto não funciona | 8-12 | P0 |
| SYS-002 | Core modules incomplete (pncp_client, filter, excel, llm) | Backend | CRÍTICO | API não funciona | 8-12 | P0 |
| SYS-003 | PNCP API resilience untested | Resilience | ALTO | Pode falhar sob rate limiting | 3-4 | P1 |
| SYS-004 | Excel export module integrated but untested | Excel | ALTO | Formato pode estar errado | 3-4 | P1 |
| SYS-005 | LLM integration designed but untested | LLM | ALTO | Fallback behavior unknown | 2-3 | P1 |
| SYS-006 | Rate limiting not validated against real PNCP | Resilience | ALTO | Desempenho desconhecido | 3-4 | P1 |
| SYS-007 | Download cache strategy not scalable | Caching | MÉDIO | Não funciona com múltiplas instâncias | 4-6 | P2 |
| SYS-008 | Environment variables not validated at startup | Config | MÉDIO | Erros crípticos se faltarem vars | 1-2 | P2 |
| SYS-009 | CORS not configured for production | Security | MÉDIO | Não é production-safe | 1 | P2 |
| SYS-010 | No database integration (yet) | Architecture | BAIXO | Planejado para fase 2 | 0 | P3 |

**Subtotal Sistema:** 9 débitos, Esforço: 33-48 horas

---

## 2. Débitos de Frontend/UX

Extraído de: `docs/frontend/frontend-spec.md`

| ID | Débito | Área | Severidade | Impacto | Esforço (h) | Prioridade |
|----|--------|------|-----------|---------|-----------|-----------|
| FE-001 | Frontend structure not created | Structure | CRÍTICO | Não pode desenvolver UI | 4-6 | P0 |
| FE-002 | Core components not implemented | Components | CRÍTICO | Não há interface | 8-10 | P0 |
| FE-003 | API routes (/api/buscar, /api/download) not implemented | API | CRÍTICO | Sem comunicação com backend | 2-3 | P0 |
| FE-004 | Error handling UI missing | UX | ALTO | Experiência ruim em erros | 3-4 | P1 |
| FE-005 | Loading states not implemented | UX | ALTO | Usuário sem feedback | 2-3 | P1 |
| FE-006 | Form validation feedback missing | UX | ALTO | Validação silenciosa | 2-3 | P1 |
| FE-007 | Mobile responsiveness untested | Responsive | ALTO | Pobre experiência mobile | 4-5 | P1 |
| FE-008 | WCAG 2.1 AA accessibility not implemented | A11y | ALTO | Não é acessível | 4-5 | P1 |
| FE-009 | Help/documentation UI missing | UX | MÉDIO | Usuários não sabem usar | 2-3 | P2 |
| FE-010 | Download management limited to single download | UX | MÉDIO | Não há histórico | 4-5 | P2 |
| FE-011 | Advanced filters not available | Features | MÉDIO | Apenas UF + data | 6-8 | P2 |
| FE-012 | Pagination/virtualization missing for large results | Performance | MÉDIO | Performance degrada com 100+ resultados | 4-6 | P2 |

**Subtotal Frontend:** 12 débitos, Esforço: 42-60 horas

---

## 3. Débitos de Testing (Não há Database neste POC)

Extraído de: `CLAUDE.md` (testing strategy)

| ID | Débito | Área | Severidade | Impacto | Esforço (h) | Prioridade |
|----|--------|------|-----------|---------|-----------|-----------|
| TEST-001 | Backend test infrastructure incomplete | Testing | CRÍTICO | Sem cobertura de testes | 6-8 | P0 |
| TEST-002 | Frontend tests not written | Testing | CRÍTICO | 0% cobertura | 6-8 | P0 |
| TEST-003 | Integration tests missing | Testing | ALTO | Fluxo end-to-end não testado | 4-6 | P1 |
| TEST-004 | PNCP API resilience tests incomplete | Testing | ALTO | Rate limiting não validado | 3-4 | P1 |
| TEST-005 | Excel output not thoroughly tested | Testing | ALTO | Formatação pode estar errada | 3-4 | P1 |
| TEST-006 | LLM fallback behavior not tested | Testing | ALTO | Comportamento em falha desconhecido | 2-3 | P1 |

**Subtotal Testing:** 6 débitos, Esforço: 24-33 horas

---

## 4. Matriz Preliminar de Débitos

```
CRÍTICOS (Deve fixar antes de produção):
├─ SYS-001: Backend endpoints
├─ SYS-002: Core modules
├─ FE-001: Frontend structure
├─ FE-002: Components
├─ FE-003: API routes
├─ TEST-001: Backend tests
└─ TEST-002: Frontend tests

ALTOS (Deve fixar para MVP):
├─ SYS-003: PNCP resilience testing
├─ SYS-004: Excel testing
├─ SYS-005: LLM testing
├─ SYS-006: Rate limiting validation
├─ FE-004 to FE-008: UX/A11y
└─ TEST-003 to TEST-006: Integration/specific tests

MÉDIOS (Pode fixar após MVP):
├─ SYS-007 to SYS-009: Caching, config, CORS
└─ FE-009 to FE-012: Help, downloads, advanced filters
```

---

## 5. Resumo de Débitos por Categoria

| Categoria | Críticos | Altos | Médios | Baixos | Total |
|-----------|----------|-------|--------|--------|-------|
| Sistema/Backend | 2 | 4 | 3 | 1 | 10 |
| Frontend/UX | 3 | 5 | 4 | 0 | 12 |
| Testing | 2 | 4 | 0 | 0 | 6 |
| **TOTAIS** | **7** | **13** | **7** | **1** | **28** |

**Esforço Total Estimado: 99-141 horas**

---

## 6. Perguntas para Especialistas

### Para @ux-design-expert (Frontend):

1. **Componentes:** Os componentes propostos (UFSelector, DateRangePicker, ResultsTable, SummaryCard) cobrem bem o caso de uso, ou faltam elementos?

2. **UX Flow:** O fluxo de search → filter → display results → download é simples demais ou está OK para POC?

3. **Mobile-First:** Deveríamos começar com mobile-first ou desktop-first? Qual é a prioridade?

4. **Accessibility:** Que nível de WCAG (A, AA, AAA) devemos visar no MVP?

5. **Advanced Filters:** Quando incluir filtros avançados (value range slider, keywords)? MVP ou Phase 2?

6. **Design System:** Usar Tailwind puro ou criar componentes customizados? (Tailwind parece mais rápido)

7. **Loading/Error States:** Qual é a melhor UX para comunicar:
   - Buscando (quanto tempo?
   - Erro de conectividade
   - Nenhum resultado

8. **Download Management:** Single download vs multiple simultaneous? Mostrar histórico?

### Para @qa (Quality Assurance):

1. **Test Approach:** Qual abordagem recomenda?
   - Unit tests (componentes, funções)
   - Integration tests (API calls)
   - E2E tests (user flows)
   - Todos os três?

2. **Coverage Threshold:** 60% (frontend) e 70% (backend) é suficiente ou muito baixo?

3. **Critical Test Scenarios:**
   - O que deve ser testado PRIMEIRO (highest risk)?
   - PNCP API resilience?
   - Excel generation?
   - Frontend validation?

4. **CI/CD Gates:** Quais critérios devem bloquear um merge?
   - Coverage threshold
   - All tests passing
   - Linting
   - Type checking

5. **Performance Testing:** Devemos testar com dados realistas (1000+ bids)?

6. **Accessibility Testing:** Como testar WCAG compliance?
   - Automated tools (axe, jest-axe)
   - Manual screen reader testing
   - Keyboard navigation testing

---

## 7. Sequência Recomendada de Resolução

### Fase 1: Core Implementation (1-2 semanas)

**Objetivo:** Produto mínimo funcional

1. SYS-001: Implement FastAPI endpoints (8h)
2. SYS-002: Complete core modules (12h)
3. FE-001: Create Next.js app structure (6h)
4. FE-002: Implement core components (10h)
5. FE-003: Create API routes (3h)
6. TEST-001: Setup backend tests (8h)
7. TEST-002: Setup frontend tests (8h)

**Subtotal:** 55 horas
**Bloqueadores:** Nenhum
**Dependências:** SYS-001/002 → FE-003, TEST-001

### Fase 2: Testing & Validation (1 semana)

**Objetivo:** Cobertura de testes adequada

1. SYS-003: Test PNCP API resilience (4h)
2. SYS-004: Test Excel export (4h)
3. SYS-005: Test LLM fallback (3h)
4. SYS-006: Validate rate limiting (4h)
5. TEST-003: Write integration tests (6h)
6. TEST-004-006: Write specific tests (10h)

**Subtotal:** 31 horas
**Bloqueadores:** Fase 1 must complete
**Dependências:** All Phase 1 items

### Fase 3: UX Polish (1 semana)

**Objetivo:** User experience and accessibility

1. FE-004: Error handling UI (4h)
2. FE-005: Loading states (3h)
3. FE-006: Form validation (3h)
4. FE-007: Mobile responsiveness (5h)
5. FE-008: WCAG accessibility (5h)
6. FE-009: Help/documentation (3h)

**Subtotal:** 23 horas
**Bloqueadores:** Fase 1 must complete
**Dependências:** All Phase 1 items

### Fase 4: Infrastructure & Scalability (Post-MVP)

**Objetivo:** Production readiness

1. SYS-007: Redis caching (6h)
2. SYS-008: Env validation (2h)
3. SYS-009: CORS configuration (1h)
4. FE-010: Download history (5h)
5. FE-011: Advanced filters (8h)
6. FE-012: Pagination (6h)

**Subtotal:** 28 horas
**Bloqueadores:** Nenhum (nice-to-have)
**Timeline:** After Phases 1-3

---

## 8. Estimativa de Timeline

```
PROJETO TOTAL: ~130-160 horas

FASE 1 (MVP)        55 horas   → 1-2 semanas (1 dev + 1 frontend dev)
FASE 2 (Testing)    31 horas   → 1 semana (@qa + devs)
FASE 3 (UX)         23 horas   → 1 semana (frontend dev)
FASE 4 (Post-MVP)   28 horas   → 1-2 semanas (optional, post-launch)

PARALLELIZABLE:
- Fases 1 backend (SYS-001/002) e frontend (FE-001/002/003) podem ser paralelas
- Fase 2 testing pode começar quando Fase 1 termina
- Fase 3 UX pode começar quando Fase 1 termina

TIMELINE REALISTA:
- MVP (Fases 1-3): 3-4 semanas com 2-3 devs
- MVP + Infrastructure: 4-5 semanas
```

---

## 9. Riscos & Mitigações

| Risco | Prob | Impacto | Mitigação |
|-------|------|---------|-----------|
| PNCP API instability | Alta | CRÍTICO | Robust retry logic (já designed) |
| Test coverage gaps | Alta | ALTO | Estabelecer coverage gates cedo |
| Scope creep | Média | ALTO | Focus on MVP first, Phase 2 depois |
| LLM cost overrun | Baixa | MÉDIO | Token limits, fallback without LLM |
| Frontend complexity | Média | MÉDIO | Start simple, add features gradually |
| Performance issues | Média | MÉDIO | Test com dados realistas |

---

## 10. Status do DRAFT

**Completude:** 85%

✅ Documentado: Architecture + Frontend analysis
✅ Débitos identificados: 28 items
✅ Estimativas: Effort + timeline
✅ Sequência: Fases de resolução propostas

⚠️ PENDENTE REVISÃO: @ux-design-expert
⚠️ PENDENTE REVISÃO: @qa
⚠️ DATABASE SKIPPED: Projeto não tem DB configurada

---

## 11. Perguntas Críticas para Validação

### Escopo MVP

1. MVP = funcionalidades de search + filter + export (atual)?
2. Ou MVP precisa de user accounts + saved searches?
3. Database deve estar no MVP ou é post-launch?

### Timeline & Equipe

1. Quantos devs disponíveis?
2. Timeline alvo: 3 semanas? 6 semanas? 3 meses?
3. Backend + Frontend separado ou mesmo dev?

### Prioridades

1. Qual é mais importante:
   - Funcionalidade (Fase 1)
   - Qualidade/Testing (Fase 2)
   - UX Polish (Fase 3)

### Trade-offs

1. Accessibility (WCAG AA) deve estar no MVP ou pode ser Phase 2?
2. Mobile responsiveness crítica no Day 1 ou pode esperar?
3. Advanced filtering (value range, keywords) MVP ou Phase 2?

---

**Próximo Passo:** @ux-design-expert e @qa revisam este DRAFT e fornecem feedback.

Então @architect consolida todas as revisões em assessment final.

