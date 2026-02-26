# Backlog: Reliability Sprint — SmartLic

**Criado:** 2026-02-26
**Origem:** GTM Validation Final (squad-gtm-validation-final.yaml) + Failure Mode Analysis + Industry Standards Research
**Meta:** Sistema funcional, confiável, previsível — e competitivo o suficiente para incomodar players estabelecidos.

---

## Execution Order (13 stories, 4 sprints, ~14 dias)

| # | Story | Sprint | Root Cause | Padrão Indústria | Dep |
|---|-------|--------|-----------|-----------------|-----|
| 1 | STORY-290: Unblock Event Loop | S0 | RC-2 | FastAPI async rules | — |
| 2 | STORY-291: Circuit Breaker Supabase | S0 | RC-1 | Microsoft CB Pattern | — |
| 3 | STORY-292: Async Search 202 Accepted | S0 | RC-4 | Microsoft Async Request-Reply | 290, 291 |
| 4 | STORY-293: Fix CI/CD Pipeline | S0 | Track D | — | — |
| 5 | STORY-294: Externalize State Redis | S1 | RC-3 | State Externalization | 292 |
| 6 | STORY-295: Progressive Results | S1 | RC-5 | Meta-Search Pattern | 292 |
| 7 | STORY-296: Bulkhead Per Source | S1 | RC-5 | Microsoft Bulkhead | 295 |
| 8 | STORY-297: SSE Last-Event-ID | S1 | Track B | WHATWG SSE Spec | 294 |
| 9 | STORY-298: Unified Error UX | S1 | Track B | — | 292, 295 |
| 10 | STORY-299: SLOs + Alerting | S2 | Track D | Google SRE | 290-298 |
| 11 | STORY-300: Security Hardening | S2 | Track F | OWASP + LGPD | — |
| 12 | STORY-301: Email Alert System | S3 | Track A/E | Table Stakes | 292, 295 |
| 13 | STORY-302: Documentation + Stale Cleanup | S3 | Track E | — | — |

---

## Sprint 0: "Make It Work" (3 dias)

**Gate:** Busca de 1 UF funciona 100/100 vezes. Zero worker timeouts. CI verde.

| Story | Effort | Owner |
|-------|--------|-------|
| STORY-290: Unblock Event Loop | L | @dev |
| STORY-291: Circuit Breaker Supabase | M | @dev |
| STORY-292: Async Search 202 Accepted | XL | @dev + @qa |
| STORY-293: Fix CI/CD Pipeline | S | @devops |

## Sprint 1: "Make It Reliable" (4 dias)

**Gate:** Busca 27 UFs funciona 95/100 vezes. Resultados parciais em <15s. SSE resiliente.

| Story | Effort | Owner |
|-------|--------|-------|
| STORY-294: Externalize State Redis | L | @dev |
| STORY-295: Progressive Results | XL | @dev + @qa |
| STORY-296: Bulkhead Per Source | M | @dev |
| STORY-297: SSE Last-Event-ID | M | @dev |
| STORY-298: Unified Error UX | M | @dev (FE) |

## Sprint 2: "Make It Observable" (2 dias)

**Gate:** SLOs definidos. Alertas configurados. CI/CD verde completo.

| Story | Effort | Owner |
|-------|--------|-------|
| STORY-299: SLOs + Alerting | M | @devops |
| STORY-300: Security Hardening | M | @dev |

## Sprint 3: "Make It Competitive" (5 dias)

**Gate:** Alertas de email funcionando. Documentação atualizada. Feature parity com table stakes.

| Story | Effort | Owner |
|-------|--------|-------|
| STORY-301: Email Alert System | XL | @dev + @qa |
| STORY-302: Documentation Cleanup | S | @dev |

---

## Sizing Legend

| Size | Hours | Description |
|------|-------|-------------|
| S | 2-4h | Single file fix, config change |
| M | 4-8h | Single module refactor, new component |
| L | 8-16h | Multi-file change, new pattern introduction |
| XL | 16-24h | Architectural change, multi-module rewrite |
