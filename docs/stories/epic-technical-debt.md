# EPIC: Resolução de Débitos Técnicos - BidIQ Uniformes

**Epic ID:** TDE-001
**Título:** Resolução de Débitos Técnicos - MVP + Production Ready
**Versão:** 1.0
**Status:** READY TO START ✅
**Data Criada:** January 26, 2026

---

## 1. Objetivo do Epic

Transformar BidIQ Uniformes de um **POC com múltiplos débitos técnicos** em um **produto pronto para produção** com todas as dependências mapeadas, priorizadas e soluções validadas.

**Resultado Final:** Sistema funcional, testado, acessível e pronto para escalar.

---

## 2. Descrição Completa

### Situação Atual

BidIQ é um POC v0.2 com:
- ✅ Arquitetura bem definida (documentada)
- ✅ Design de componentes pronto
- ❌ Implementação incompleta (28 débitos técnicos)
- ❌ Sem testes automatizados
- ❌ Sem UI frontend
- ❌ Sem validação de resilience

### Situação Desejada

BidIQ será um produto v1.0 com:
- ✅ Backend completamente implementado
- ✅ Frontend intuitivo e responsivo
- ✅ 70%+ test coverage
- ✅ WCAG A accessibility
- ✅ PNCP API resilience validada
- ✅ Pronto para deploy em produção

### Transformação

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Funcionalidade** | 0% (não funciona) | 100% (MVP) |
| **Qualidade** | Não testado | 70% coverage |
| **UX** | Sem interface | Clean, intuitive |
| **Performance** | Desconhecido | <1.5s FCP |
| **Acessibilidade** | 0% | WCAG A |
| **Documentação** | Arquitetura apenas | Código + arquitetura + API |

---

## 3. Escopo

### Incluso (MVP + Production)

**Backend:**
- Implementar todos os endpoints FastAPI
- Completo pncp_client com retry logic
- Filter engine com keyword matching
- Excel report generator com styling
- LLM integration com fallback
- 70%+ test coverage
- CI/CD setup

**Frontend:**
- Next.js 14+ app structure
- Core components (UF selector, date picker, results, summary)
- API routes (/api/buscar, /api/download)
- Error handling + loading states
- Form validation + feedback
- Mobile responsiveness
- WCAG A accessibility
- 60%+ test coverage

**Testing:**
- Backend unit + integration tests
- Frontend component + E2E tests
- PNCP API resilience validation
- Excel output validation
- LLM behavior testing
- CI/CD quality gates

### NÃO Incluso (Phase 2 ou Later)

- Database (Supabase) integration
- User authentication
- Advanced filters (value range, semantic search)
- Download history
- Real-time notifications
- Multi-language support
- WCAG AA (can be upgraded later)

---

## 4. Critérios de Sucesso

### Deve-Ter (Non-negotiable)

- [x] Todos 28 débitos técnicos resolvidos
- [x] Backend endpoints funcionando
- [x] Frontend UI completa
- [x] 70%+ backend test coverage
- [x] 60%+ frontend test coverage
- [x] PNCP API resilience validated
- [x] No blocking errors in logs
- [x] End-to-end user flow works
- [x] Documentation complete

### Deve-Ter (Quality)

- [x] Linting passes (eslint + ruff)
- [x] Type checking passes (TypeScript + mypy)
- [x] Bundle size <200KB
- [x] FCP <1.5s
- [x] LCP <2.5s
- [x] WCAG A compliance
- [x] No console errors

### Nice-to-Have (If Time)

- [ ] WCAG AA (upgraded from A)
- [ ] Sentry error tracking setup
- [ ] Google Analytics 4
- [ ] Cypress E2E tests
- [ ] Load testing (1000+ concurrent)

---

## 5. Fases de Entrega

### Fase 1: MVP (Semanas 1-2)

**Deliverables:**
- Backend endpoints + core modules (SYS-001, SYS-002)
- Frontend structure + components (FE-001, FE-002, FE-003)
- Basic tests setup (TEST-001, TEST-002)

**Stories:** TDE-001-1 a TDE-001-6
**Horas:** 55-70
**Status:** Ready to Start

---

### Fase 2: Production Ready (Semana 3)

**Deliverables:**
- Complete test coverage (SYS-003 a SYS-006, TEST-003 a TEST-006)
- Error/loading/validation UX (FE-004 a FE-006)

**Stories:** TDE-001-7 a TDE-001-13
**Horas:** 31-40
**Status:** Dependent on Phase 1

---

### Fase 3: Polish (Semana 4)

**Deliverables:**
- Mobile responsiveness (FE-007)
- Accessibility upgrade (FE-008)
- Help documentation (FE-009)

**Stories:** TDE-001-14 a TDE-001-16
**Horas:** 23-30
**Status:** Dependent on Phases 1-2

---

### Fase 4: Enhancement (Semanas 5-6, Optional)

**Deliverables:**
- Infrastructure (caching, CORS, env validation)
- Advanced features (download history, filters, pagination)

**Stories:** TDE-001-17 a TDE-001-23
**Horas:** 28-35
**Status:** Post-MVP, nice-to-have

---

## 6. Timeline

```
Week 1-2: MVP
├─ Mon-Tue: Backend endpoints (SYS-001, SYS-002)
├─ Wed-Thu: Frontend structure + components (FE-001, FE-002)
└─ Fri: API routes + tests setup (FE-003, TEST-001/002)

Week 3: Testing & QA
├─ Mon-Tue: Complete resilience testing (SYS-003-006)
├─ Wed-Thu: Error handling + loading UI (FE-004-006)
└─ Fri: Bug fixes + validation

Week 4: Polish & Production
├─ Mon-Tue: Mobile responsiveness (FE-007)
├─ Wed-Thu: Accessibility + help (FE-008-009)
└─ Fri: Final QA + deploy staging

Total: 3-4 weeks for production-ready
Optional: Week 5-6 for Phase 4 (scalability)
```

---

## 7. Recursos Necessários

### Equipe

| Papel | FTE | Semanas | Custo |
|-------|-----|---------|-------|
| Backend Developer | 1 | 4 | R$ 24,000 |
| Frontend Developer | 1 | 4 | R$ 19,200 |
| QA Engineer | 1 | 3 | R$ 15,600 |
| **Subtotal** | - | - | **R$ 58,800** |
| Contingency (10%) | - | - | R$ 5,880 |
| **Total** | - | - | **R$ 64,680** |

*Baseado em R$ 150/h backend, R$ 120/h frontend, R$ 130/h QA*

### Ambiente

- GitHub (code hosting)
- GitHub Actions (CI/CD)
- Staging environment (para QA)
- Production environment (railway.app ou similar)

### Dependências Externas

- PNCP API (public, no API key needed)
- OpenAI API (need valid API key + credit)
- GitHub (already have)

---

## 8. Riscos & Mitigações

| Risco | Probability | Impact | Mitigation |
|-------|-------------|--------|-----------|
| PNCP API instability | High | Critical | Robust retry logic (designed) + mocking |
| Scope creep | Medium | High | Strict MVP focus, defer Phase 2 features |
| Test coverage gaps | Medium | High | QA strategy document + CI gates |
| Performance issues | Medium | Medium | Load testing with realistic data |
| LLM API costs | Low | Medium | Token limits + cost monitoring |
| Team availability | Medium | Medium | Cross-training + documentation |

---

## 9. Dependências de Story

```
START (Day 1)
  ├─ TDE-001-1: Backend endpoints (SYS-001)
  │  ├─ BLOCKS: TDE-001-7 (API testing)
  │  └─ Duration: 2-3 days
  │
  ├─ TDE-001-2: Frontend structure (FE-001)
  │  ├─ BLOCKS: TDE-001-3, TDE-001-4, TDE-001-5
  │  └─ Duration: 1 day
  │
  └─ TDE-001-6: Tests setup (TEST-001/002)
     └─ Duration: 2-3 days

(Continues...)
```

---

## 10. Success Metrics (Final)

### Functional

- ✅ User can select UF → pick date range → click search
- ✅ System calls PNCP API → filters results → returns data
- ✅ Results display in table + GPT summary card
- ✅ User can download Excel report
- ✅ All error cases handled gracefully

### Quality

- ✅ Backend test coverage: 70%+
- ✅ Frontend test coverage: 60%+
- ✅ Linting: 0 errors
- ✅ Type checking: 0 errors
- ✅ No console errors on happy path

### Performance

- ✅ FCP <1.5s
- ✅ LCP <2.5s
- ✅ Bundle <200KB gzipped
- ✅ Search response <5s (including API)

### Accessibility

- ✅ WCAG A compliance
- ✅ Keyboard navigation works
- ✅ Color contrast >4.5:1
- ✅ Semantic HTML

### Operations

- ✅ CI/CD pipeline green
- ✅ Can deploy one-click
- ✅ Monitoring setup (logs)
- ✅ Documentation complete

---

## 11. Story Breakdown

### Phase 1: MVP (TDE-001-1 to TDE-001-6)

| Story | Title | Owner | Points | Phase |
|-------|-------|-------|--------|-------|
| TDE-001-1 | Implement FastAPI endpoints | @dev-backend | 13 | 1 |
| TDE-001-2 | Create Next.js app structure | @dev-frontend | 8 | 1 |
| TDE-001-3 | Implement core components | @dev-frontend | 13 | 1 |
| TDE-001-4 | Create API routes (/api/buscar, /api/download) | @dev-frontend | 5 | 1 |
| TDE-001-5 | Complete core modules (pncp, filter, excel, llm) | @dev-backend | 13 | 1 |
| TDE-001-6 | Setup test infrastructure | @qa | 8 | 1 |

---

### Phase 2: Production (TDE-001-7 to TDE-001-13)

| Story | Title | Owner | Points | Phase |
|-------|-------|-------|--------|-------|
| TDE-001-7 | Validate PNCP API resilience | @qa | 8 | 2 |
| TDE-001-8 | Test Excel output thoroughly | @qa | 8 | 2 |
| TDE-001-9 | Test LLM integration | @qa | 5 | 2 |
| TDE-001-10 | Write integration tests | @qa | 10 | 2 |
| TDE-001-11 | Implement error handling UI | @dev-frontend | 8 | 2 |
| TDE-001-12 | Implement loading states | @dev-frontend | 5 | 2 |
| TDE-001-13 | Implement form validation feedback | @dev-frontend | 5 | 2 |

---

### Phase 3: Polish (TDE-001-14 to TDE-001-16)

| Story | Title | Owner | Points | Phase |
|-------|-------|-------|--------|-------|
| TDE-001-14 | Mobile responsiveness testing | @dev-frontend | 10 | 3 |
| TDE-001-15 | WCAG A accessibility implementation | @dev-frontend | 10 | 3 |
| TDE-001-16 | Help/documentation UI | @dev-frontend | 5 | 3 |

---

### Phase 4: Enhancement (Optional, TDE-001-17+)

| Story | Title | Owner | Points | Phase |
|-------|-------|-------|--------|-------|
| TDE-001-17 | Redis caching implementation | @dev-backend | 13 | 4 |
| TDE-001-18 | CORS configuration | @dev-backend | 3 | 4 |
| TDE-001-19 | Environment validation | @dev-backend | 3 | 4 |
| TDE-001-20 | Download history feature | @dev-frontend | 10 | 4 |
| TDE-001-21 | Advanced filters (value range) | @dev-frontend | 13 | 4 |
| TDE-001-22 | Pagination/virtualization | @dev-frontend | 13 | 4 |

---

## 12. Definition of Done (For Each Story)

- [x] Code written and committed
- [x] Code reviewed by peer
- [x] Tests written (unit + integration)
- [x] Tests passing (100% of story tests)
- [x] Linting passes (eslint, ruff)
- [x] Type checking passes (TS, mypy)
- [x] Documentation updated
- [x] Verified against acceptance criteria
- [x] No new console errors
- [x] QA approved

---

## 13. Acceptance Criteria (Epic Level)

### Phase 1 Complete When:

- [x] Backend endpoints respond to requests
- [x] Frontend UI renders without errors
- [x] User can perform full search flow
- [x] Basic tests run and pass
- [x] No blocking issues in QA

### Phase 2 Complete When:

- [x] All unit tests pass (70%+ backend)
- [x] All integration tests pass
- [x] Error handling shows user-friendly messages
- [x] PNCP API failures handled correctly
- [x] Ready for public beta

### Phase 3 Complete When:

- [x] Mobile works (tested on devices)
- [x] Accessibility WCAG A compliant
- [x] All help text in place
- [x] Performance targets met
- [x] Ready for production deployment

---

## 14. Communication Plan

### Stakeholders

- **CTO/VP Tech:** Weekly status (every Fri)
- **Product Owner:** Daily standup (quick)
- **Finance:** Weekly budget check
- **Customers:** Beta kickoff (end Phase 1)

### Updates

| Frequency | Audience | Format |
|-----------|----------|--------|
| Daily | Team | Standup (15min) |
| Weekly | Leadership | Email summary |
| Bi-weekly | Stakeholders | Demo + metrics |
| Monthly | Board | Financial summary |

---

## 15. Glossary & References

**MVP:** Minimum Viable Product (Phase 1, functional)
**Production Ready:** Phases 1-3 combined
**Enterprise Grade:** All phases complete (including Phase 4)

**Related Documents:**
- `docs/architecture/system-architecture.md` (Technical overview)
- `docs/frontend/frontend-spec.md` (Component design)
- `docs/prd/technical-debt-assessment.md` (Debt prioritization)
- `docs/reports/TECHNICAL-DEBT-REPORT.md` (Executive summary)

---

## 16. Approval & Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Architect | @architect | 2026-01-26 | ✅ |
| Product Manager | TBD | TBD | ⏳ |
| Engineering Manager | TBD | TBD | ⏳ |
| CTO | TBD | TBD | ⏳ |

---

## Next Steps

1. **Engineering Manager:** Review & assign stories
2. **Team:** Kick-off meeting (Day 1)
3. **Dev Team:** Begin Phase 1 (Backend + Frontend)
4. **QA:** Begin test infrastructure
5. **Project Manager:** Track progress weekly

---

**Epic Created:** January 26, 2026
**Version:** 1.0
**Status:** ✅ READY FOR KICK-OFF
**Expected Duration:** 3-4 weeks
**Estimated Budget:** R$ 65k

---

*Epic approved by @architect. Awaiting executive approval to proceed.*
