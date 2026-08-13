# Campanha SmartLic → inbound CONFENGE (2026-08-13)

Branch: `feat/confenge-inbound-campaign`  
Base: freeze #2111 (`fix/2111-saas-commerce-freeze` / PR #2120)

## Dependency graph

```text
#1262 (merged)
  → #2111 freeze (PR #2120, reuse)
      → #2114 brand/journey
      → #2117 lead outbox
      → #2113 URL registry + 301
  → extra-cli#354 / PR #358 (OPEN, not production)
      → #2108 consumer boundary (flag off)
      → #2116 isolation
  → #2112 six public families
  → #2118 eligibility
  → #2109 calculadora/comparador
  → #2115 Netcup runbook
  → #2121 Railway fallback 404 (infra, not this SHA)
```

## Classification leftovers

Stripe SDK, webhooks, secrets: SUNSET AFTER ZERO-USE. Não removidos neste ciclo porque Railway está morto e não há prova de zero evento residual.
