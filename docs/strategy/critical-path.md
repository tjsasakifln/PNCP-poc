# Caminho crítico autoritativo — relançamento público

**Autoridade:** [ADR-STRAT-001](../adr/ADR-STRAT-001-smartlic-confenge-inbound.md) · issue [#1262](https://github.com/tjsasakifln/SmartLic/issues/1262)  
**Atualizado:** 2026-08-13

Nenhuma issue P1/P2 disputa recursos com esta sequência. Trabalho paralelo só é lícito se não cria acoplamento, retrabalho ou violação de ordem.

## Ordem estrita

| # | Issue | Repo | Papel | Pode começar antes? |
|---|-------|------|-------|---------------------|
| 1 | [#1262](https://github.com/tjsasakifln/SmartLic/issues/1262) | SmartLic | Decisão estratégica e freeze | — |
| 2 | [#2111](https://github.com/tjsasakifln/SmartLic/issues/2111) | SmartLic | Congelar/retirar SaaS, Stripe, billing, trial, quotas | Após #1262 |
| 3 | [#2113](https://github.com/tjsasakifln/SmartLic/issues/2113) | SmartLic | Preservar patrimônio SEO; 301/canonical | Inventário pode ser paralelo a #2111; nenhum delete de URL antes |
| 4 | [extra-cli#354](https://github.com/tjsasakifln/extra-cli/issues/354) | extra-cli | `public_read_v1` SELECT-only | Producer; SmartLic não implementa o contrato |
| 5 | [#2108](https://github.com/tjsasakifln/SmartLic/issues/2108) | SmartLic | Consumir `public_read_v1`; aposentar DataLake/crawler | Bloqueado por extra-cli#354 |
| 6 | [#2112](https://github.com/tjsasakifln/SmartLic/issues/2112) | SmartLic | Public intelligence MVP | Bloqueado por #2108 + #2113 |
| 7 | [#2116](https://github.com/tjsasakifln/SmartLic/issues/2116) | SmartLic | Isolamento: tráfego público não degrada extra-cli | Pode desenhar em paralelo; promoção após #2108 |
| 8 | [#2115](https://github.com/tjsasakifln/SmartLic/issues/2115) | SmartLic | Runtime mínimo na Netcup | Após isolamento definido |
| 9 | [#2114](https://github.com/tjsasakifln/SmartLic/issues/2114) | SmartLic | Marca SmartLic ↔ CONFENGE; CTA consultivo | Copy pode rascunhar cedo; rollout após #2112 |
| 10 | [#2117](https://github.com/tjsasakifln/SmartLic/issues/2117) | SmartLic | Attribution + handoff mínimo | Após #2114 |
| 11 | Go-live público | — | Traffic switch | Todos os gates aplicáveis verdes |

## Dependências cross-repo

```text
extra-cli#289 (IDs/eventos canônicos) ─┐
extra-cli#273 (dedup/lineage)         ─┼─► extra-cli#354 (public_read_v1) ─► SmartLic#2108 ─► #2112
                                        │
SmartLic#1262 ─► #2111 ─► #2113 ────────┴─► #2112 ─► #2116 ─► #2115 ─► #2114 ─► #2117 ─► go-live
```

- Producer: `tjsasakifln/extra-cli` (#289, #273, #354).
- Consumer: `tjsasakifln/SmartLic` (#2108, #2112).
- Conversão: #2114, #2117 — CONFENGE é o service plane.
- Warmbly: **não aparece neste grafo**. Consumidor futuro de handoff, nunca gate de go-live.

## Próxima onda (P1, `roadmap:next`)

Só depois dos P0 aplicáveis.

| Issue | Título | Por que não é P0 |
|-------|--------|------------------|
| #2109 | Product-as-content / lead magnets | Expansão de ferramenta; MVP primeiro |
| #2118 | Expandir pSEO só com dado único + intenção | Proibido expandir pSEO antes dos gates P0 |

## Explicitamente later (P2, `roadmap:later`)

| Issue | Título | Por que later |
|-------|--------|---------------|
| #2107 | Assessment privado multi-cliente | Sem evidência de inbound; DEFER |

## Go-live — gates (não negociáveis)

Não declarar GO com base só em testes locais.

- [ ] #1262 merged e documentos canônicos sem tese SaaS.
- [ ] #2111 onda 1 (freeze): checkout/trial/upgrade impossíveis.
- [ ] #2113: baseline SEO + política de redirect para qualquer URL tocada.
- [ ] extra-cli#354: `public_read_v1` com role SELECT-only e contract tests.
- [ ] #2108: SmartLic lê o contrato; crawler/DataLake próprios não são autoridade.
- [ ] #2112: famílias MVP no ar com dado verificável (freshness/provenance).
- [ ] #2116: budgets/kill switch; soak sem degradar writers do extra-cli.
- [ ] #2115: runtime Netcup reversível; Railway não é mais SPOF não documentado.
- [ ] #2114: zero CTA público para signup/trial/upgrade/checkout.
- [ ] #2117: um lead de teste percorre landing → CTA → handoff CONFENGE.
- [ ] Warmbly ausente da lista de blockers.
