# Handoff — campanha inbound CONFENGE

**Data:** 2026-08-13  
**Branch:** `feat/confenge-inbound-campaign`  
**Base:** `a0243e95` (PR #2120 freeze)

## Feito

Consumer `public_read_v1`, jornada/marca, 301 SaaS, outbox de lead, 6 famílias com provenance/CTA, eligibility, Netcup runbook, smoke classifica Railway fallback.

## Não feito / bloqueado

- Cutover real: extra-cli PR #358 aberto, DSN de produção indisponível.
- Railway produção: `x-railway-fallback: true` em smartlic.tech e no backend (#2121).
- Remoção física Stripe/secrets: sem prova de zero evento.
- Merge/close dos PRs pSEO 2078–2082: disposição documentada, não fechados (precisa @devops).
