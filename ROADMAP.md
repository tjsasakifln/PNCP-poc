# ROADMAP — Smart PNCP POC

**Versao:** 2.0 | **Atualizado:** 2026-02-04 | **Status:** POC DEPLOYED + Technical Debt Phase

---

## Status Atual

```
POC CORE:        [####################] 100% (34/34) DEPLOYED
CLOSED TOTAL:    95 issues
OPEN TOTAL:      157 issues (technical debt backlog)
```

**Production URLs:**
- Frontend: https://bidiq-frontend-production.up.railway.app
- Backend: https://bidiq-uniformes-production.up.railway.app
- API Docs: https://bidiq-uniformes-production.up.railway.app/docs

---

## Epics Concluidos (POC Core)

| EPIC | Issues | Status |
|------|--------|--------|
| EPIC 1: Setup e Infraestrutura | #2, #3, #4, #5, #32 | CLOSED |
| EPIC 2: Cliente PNCP | #6, #7, #8, #28 | CLOSED |
| EPIC 3: Motor de Filtragem | #9, #10, #11, #30 | CLOSED |
| EPIC 4: Geracao de Saidas | #12, #13, #14, #15 | CLOSED |
| EPIC 5: API Backend | #16, #17, #18, #19, #29 | CLOSED |
| EPIC 6: Frontend | #20, #21, #22, #23, #24, #56, #57 | CLOSED |
| EPIC 7: Deploy | #25, #26, #27, #31, #61, #65, #66, #71, #73, #74, #75 | CLOSED |
| EPIC 8: Design System | #83-#94 (exceto #89) | CLOSED |

---

## Backlog Priorizado (157 Open Issues)

### P0 - CRITICO (Seguranca/Estabilidade)

| # | Issue | Categoria |
|---|-------|-----------|
| 156 | CORS allows all origins - CRITICAL for GTM | SEC |
| 205 | SQL Injection Risk in Quota Upsert | SEC |
| 168 | Sensitive data in logs (potential PII exposure) | SEC |
| 203 | Unsafe Admin User ID Parsing | SEC |
| 240 | Race Condition in Quota Increment | BE |
| 189 | Race Condition in Quota Check/Increment | HP |

### P1 - ALTA (Funcionalidade Core)

| # | Issue | Categoria |
|---|-------|-----------|
| 150 | Configure Stripe products and webhook | SETUP |
| 199 | Jest Coverage Below 60% Target (44%) | TEST |
| 300 | Jest Coverage Below Target (44% vs 60%) | TEST |
| 164 | Frontend test coverage at 49% | TEST |
| 283 | Frontend Coverage Below Minimum Standard | OPS |
| 163 | Main page component too large (1467 lines) | FE |
| 198 | Monolithic Page Component (1467 lines) | CODE |
| 256 | Monolithic Page Component | FE |
| 178 | LLM Fallback Chain May Still Fail Silently | HP |
| 239 | Missing Error Handling in LLM Fallback Chain | BE |

### P2 - MEDIA (Qualidade/UX)

| # | Issue | Categoria |
|---|-------|-----------|
| 194 | Missing ARIA Labels on Interactive Elements | UX |
| 268 | Missing ARIA Labels on Interactive Elements | FE |
| 195 | Keyboard Navigation Incomplete | UX |
| 269 | Keyboard Navigation Not Complete | FE |
| 197 | Color Contrast Issues May Fail WCAG AA | UX |
| 271 | Color Contrast Issues | FE |
| 179 | Excel Generation Buffer Resource Leak | HP |
| 241 | Excel Generation Buffer Not Explicitly Closed | BE |
| 171 | No error boundaries in React components | FE |
| 185 | Missing Error Boundary for Component Errors | HP |
| 277 | Missing Error Boundary for Component Errors | FE |

### P3 - BAIXA (Escalabilidade/Nice-to-Have)

| # | Issue | Categoria |
|---|-------|-----------|
| 157-162 | TD-SCALE-001 to 006 | SCALE |
| 165-167 | TD-SCALE-007 to 009 | SCALE |
| 172, 177 | TD-SCALE-010, 011 | SCALE |
| 220 | No Canary or Blue-Green Deployment | OPS |
| 222 | No Observability/Monitoring | OPS |
| 166 | No observability (APM, metrics, tracing) | SCALE |

---

## Technical Debt Summary

```
CATEGORIA          OPEN   EXEMPLOS
----------------- ------ ----------------------------------
TD-SEC (Security)     4   #156, #168, #205, #203
TD-BE (Backend)      23   #239-#255
TD-FE (Frontend)     51   #163-#282 (FE range)
TD-TEST (Testing)    26   #199-#311 (TEST range)
TD-OPS (DevOps)      15   #215-#289 (OPS range)
TD-HP (Happy Path)   12   #178-#189
TD-GTM (Go-to-Mkt)    4   #190-#193
TD-UX (User Exp)      4   #194-#197
TD-SCALE              11  #157-#177
TD-PERF               2   #169, #176
TD-DX                 1   #175
TD-INFRA              1   #173
OUTROS               3   #89, #150
```

---

## Proximas Acoes Recomendadas

### Sprint 1: Seguranca (P0)
1. [ ] #156 - Fix CORS configuration
2. [ ] #205 - Fix SQL injection risk
3. [ ] #168 - Remove PII from logs
4. [ ] #203 - Fix admin ID parsing
5. [ ] #240 - Fix race condition in quota

### Sprint 2: Cobertura de Testes (P1)
1. [ ] #199/#300 - Aumentar Jest coverage para 60%
2. [ ] #164/#283 - Frontend coverage enforcement
3. [ ] Consolidar issues duplicadas

### Sprint 3: Refactoring (P1)
1. [ ] #163/#198/#256 - Quebrar page.tsx monolitico
2. [ ] #178/#239 - Melhorar error handling LLM

### Futuro: Escalabilidade (P3)
- Circuit breaker, caching, observability
- Blue-green deployment
- Horizontal scaling

---

## Notas da Auditoria (2026-02-04)

**Drift Detectado:**
- ROADMAP anterior: 132 issues documentadas
- Realidade tracker: 252 issues
- Drift: +120 issues (90.9%)

**Issues Duplicadas Identificadas:**
- Coverage: #199, #300, #164, #283 (mesmo tema)
- Monolithic: #163, #198, #256 (mesmo tema)
- Error Boundary: #171, #185, #277 (mesmo tema)
- ARIA: #194, #268 (mesmo tema)
- Race Condition: #189, #240 (mesmo tema)

**Recomendacao:** Consolidar issues duplicadas antes de priorizar trabalho.

---

## Historico

| Data | Evento |
|------|--------|
| 2026-01-28 | POC deployed to production |
| 2026-01-31 | Design System EPIC 8 91.7% complete |
| 2026-02-04 | Technical debt audit: 157 open issues |

---

*Ultima auditoria: 2026-02-04 | Proximo review: Sprint planning*
