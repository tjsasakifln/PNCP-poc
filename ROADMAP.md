# ROADMAP — Smart PNCP POC

**Versao:** 2.0 | **Atualizado:** 2026-02-04 | **Status:** POC DEPLOYED + Technical Debt Phase

---

## Status Atual

```
POC CORE:        [####################] 100% (34/34) DEPLOYED
CLOSED TOTAL:    119 issues (incl. 24 duplicates)
OPEN TOTAL:      133 issues (technical debt backlog)
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

## Backlog Priorizado (133 Open Issues)

### P0 - CRITICO (Seguranca/Estabilidade)

| # | Issue | Categoria |
|---|-------|-----------|
| 156 | CORS allows all origins - CRITICAL for GTM | SEC |
| 205 | SQL Injection Risk in Quota Upsert | SEC |
| 168 | Sensitive data in logs (potential PII exposure) | SEC |
| 203 | Unsafe Admin User ID Parsing | SEC |
| 189 | Race Condition in Quota Check/Increment | HP |

### P1 - ALTA (Funcionalidade Core)

| # | Issue | Categoria |
|---|-------|-----------|
| 150 | Configure Stripe products and webhook | SETUP |
| 199 | Jest Coverage Below 60% Target (44%) | TEST |
| 164 | Frontend test coverage at 49% | TEST |
| 163 | Main page component too large (1467 lines) | FE |
| 178 | LLM Fallback Chain May Still Fail Silently | HP |

### P2 - MEDIA (Qualidade/UX)

| # | Issue | Categoria |
|---|-------|-----------|
| 194 | Missing ARIA Labels on Interactive Elements | UX |
| 195 | Keyboard Navigation Incomplete | UX |
| 197 | Color Contrast Issues May Fail WCAG AA | UX |
| 179 | Excel Generation Buffer Resource Leak | HP |
| 171 | No error boundaries in React components | FE |

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
TD-BE (Backend)      18   #243-#255 (after duplicates removed)
TD-FE (Frontend)     40   #163-#282 (after duplicates removed)
TD-TEST (Testing)    22   #199-#311 (after duplicates removed)
TD-OPS (DevOps)      12   #215-#289 (after duplicates removed)
TD-HP (Happy Path)    9   #178-#189 (after duplicates removed)
TD-GTM (Go-to-Mkt)    3   #190-#193 (after duplicates removed)
TD-UX (User Exp)      4   #194-#197
TD-SCALE             11   #157-#177
TD-PERF               2   #169, #176
TD-DX                 1   #175
TD-INFRA              1   #173
OUTROS               2   #89, #150
DUPLICATES CLOSED   24   (consolidated into main issues)
```

---

## Proximas Acoes Recomendadas

### Sprint 1: Seguranca (P0)
1. [ ] #156 - Fix CORS configuration
2. [ ] #205 - Fix SQL injection risk
3. [ ] #168 - Remove PII from logs
4. [ ] #203 - Fix admin ID parsing
5. [ ] #189 - Fix race condition in quota

### Sprint 2: Cobertura de Testes (P1)
1. [ ] #199 - Aumentar Jest coverage para 60%
2. [ ] #164 - Frontend coverage enforcement

### Sprint 3: Refactoring (P1)
1. [ ] #163 - Quebrar page.tsx monolitico
2. [ ] #178 - Melhorar error handling LLM

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

**Issues Duplicadas Fechadas (24 total):**
- #300, #283 (duplicates de coverage)
- #198, #256 (duplicates de monolithic)
- #185, #277 (duplicates de error boundary)
- #268, #269, #271 (duplicates de UX/accessibility)
- #240, #241, #239, #245, #244 (duplicates de backend)
- #208, #274, #273, #275, #262, #281, #280, #224, #279, #237

**Resultado:** Backlog reduzido de 157 para 133 issues abertas.

---

## Historico

| Data | Evento |
|------|--------|
| 2026-01-28 | POC deployed to production |
| 2026-01-31 | Design System EPIC 8 91.7% complete |
| 2026-02-04 | Roadmap audit: 24 duplicates closed, 133 open issues |

---

*Ultima auditoria: 2026-02-04 | Proximo review: Sprint planning*
