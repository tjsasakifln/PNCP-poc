# GTM-OK Remediation Stories

11 stories identificadas no GTM-OK assessment (2026-02-16). Revisadas por squad de 5 agentes (architect, dev, QA, UX, data-engineer).

## Ordem de Execução

### Sprint 1 — P0 Critical Fixes

1. **GTM-FIX-002** — Enable Production Observability — XS (30min) — GO
2. **GTM-FIX-005** — Circuit Breaker per-source — XS (30min) — GO c/ revisoes
3. **GTM-FIX-001** — Fix Stripe Checkout→Activation — S (4-8h) — GO
4. **GTM-FIX-004** — Truncation per-source — S (5h) — GO c/ revisoes
5. **GTM-FIX-003** — Copy Rewrite (36 claims) — M (2-3d) — GO (paralelizavel)

### Sprint 2 — P1 UX + Integracao

6. **GTM-FIX-008** — Mobile Navigation — S (4h) — GO
7. **GTM-FIX-009** — Email Confirmation — S (6-8h) — REVISE (seguranca: polling via POST)
8. **GTM-FIX-006** — Subscription Cancellation — S (8h) — GO
9. **GTM-FIX-007** — Payment Dunning — S (8-10h) — GO
10. **GTM-FIX-011** — PCP API Integration — S (1-2d) — REVISE (usar PortalComprasAdapter existente)
11. **GTM-FIX-010** — SWR Cache dual-source — M (4-5d) — GO c/ revisoes

## Acoes Criticas Pre-Execucao

- **GTM-FIX-011**: NAO criar `pcp_client.py` nem `data_source_aggregator.py`. Completar `PortalComprasAdapter` existente (609 linhas) + usar `ConsolidationService`
- **GTM-FIX-009**: Mudar polling de GET com email na URL para POST (vulnerability LGPD)
- **Banner Priority System**: Max 2 banners simultaneos (5 possiveis atualmente)
- **Test infra**: Criar `helpers/stripe_webhook_mock.py`, `helpers/dual_source_mock.py`

## Dependencias

```
GTM-FIX-002 (primeiro, observabilidade)
    └→ GTM-FIX-005 (circuit breaker per-source)
        └→ GTM-FIX-011 (completar PortalComprasAdapter)
            ├→ GTM-FIX-010 (cache dual-source, soft dep)
            ├→ GTM-FIX-004 (truncation per-source, soft dep)
            └→ GTM-FIX-003 (copy claims accuracy, soft dep)
```

## Effort Summary

- **XS (<=1h):** GTM-FIX-002, GTM-FIX-005
- **S (4-10h):** GTM-FIX-001, 004, 006, 007, 008, 009, **011**
- **M (2-5d):** GTM-FIX-003, GTM-FIX-010

**Total:** 11-15 days (1 dev) ou 6-8 days (2 devs paralelo)

## Score Projetado

**Antes:** 5.42/10 (NO GO) → **Depois:** 7.5+/10 (GO)

## Squad Review Findings (2026-02-16)

### Descoberta Critica
O codebase ja possui infraestrutura multi-source: `PortalComprasAdapter` (609 linhas), `ConsolidationService`, `SourceAdapter` ABC, `SourceHealthRegistry`. GTM-FIX-011 reescrita para completar o existente.

### Por Story

| Story | Veredicto | Revisoes Necessarias |
|-------|-----------|---------------------|
| GTM-FIX-001 | GO | Corrigir path refs (routes/billing.py) |
| GTM-FIX-002 | GO | Sem revisoes |
| GTM-FIX-003 | GO | Snapshot tests ANTES das mudancas |
| GTM-FIX-004 | GO c/ revisoes | Pydantic `TruncationDetails`, remover "250.000" hardcoded |
| GTM-FIX-005 | GO c/ revisoes | Renomear `PNCPCircuitBreaker` → `SourceCircuitBreaker` |
| GTM-FIX-006 | GO | Clarificar `canceling` status (DB vs Stripe-derived) |
| GTM-FIX-007 | GO | Adicionar `routes/user.py` nos files-to-modify |
| GTM-FIX-008 | GO | Trap focus no menu mobile |
| GTM-FIX-009 | REVISE | Polling via POST (nao GET), Supabase Admin API correto, effort 6-8h |
| GTM-FIX-010 | GO c/ revisoes | Reconciliar com migration 026, fix datetime.utcnow(), hash determinism |
| GTM-FIX-011 | REVISE (reescrita) | Usar infra existente. Effort: S(1-2d), nao M(3-5d) |

### Cross-Story Concerns
- **Banner Overload**: 5 banners possiveis simultaneos → implementar priority system (max 2)
- **GTM-FIX-005 quebra testes existentes**: constructor signature change em CircuitBreaker
- **GTM-FIX-010 schema mismatch**: migration 026 ja deployed usa field names diferentes do story

## PCP API Reference

| Item | Value |
|------|-------|
| Base URL | `https://apipcp.portaldecompraspublicas.com.br` |
| Test URL | `https://apipcp.wcompras.com.br` |
| Auth | `publicKey` param (env var `PCP_PUBLIC_KEY`) |
| Key endpoints | processos abertos, recebendo propostas, lista com status |
| Date format | DD/MM/AAAA (Brazilian) |
| Value | Per-item (`VL_UNITARIO_ESTIMADO * QT_ITENS`), needs summation |
| Unique feature | CNAE classification data available |
| Full docs | See [GTM-FIX-011](./GTM-FIX-011.md) |

---

**Last updated:** 2026-02-16 (post squad review)
**Status:** Ready for implementation (11 stories, reviewed by 5-agent squad)
