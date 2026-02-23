# GTM Root Cause Analysis — Index

> **Origem:** Squad investigation com 4 agentes (architect, qa, ux, data-engineer) — 101 findings, 193 tool calls, ~564k tokens.
>
> **Data:** 2026-02-23
>
> **Causa raiz fundamental:** O sistema foi arquitetado como request-response sincrono (POST /buscar retorna apos 360s), mas roda em infraestrutura com hard timeout de ~120s (Railway proxy). Todo codigo acima de 120s e dead code em producao. O cache per-user nao protege novos usuarios. Erros chegam crus ao usuario em ingles.

---

## Matriz de Priorizacao

| Story | Severity | Impacto GTM | Complexidade | Prioridade | Estimativa |
|-------|----------|-------------|--------------|------------|------------|
| **GTM-ARCH-001** | 🔴 CRITICAL | Buscas nao funcionam >120s | Alta | **P0** | 32h |
| **GTM-ARCH-002** | 🔴 CRITICAL | Trial users sem protecao | Media | **P0** | 16h |
| **GTM-PROXY-001** | 🔴 HIGH | Erros ingles na cara do usuario | Media | **P0** | 12h |
| **GTM-QUAL-001** | 🟠 HIGH | Validacao E2E pos-mudancas | Baixa | **P1** | 4h |
| **GTM-UX-001** | 🟠 HIGH | Muro de 8 banners | Media | **P1** | 12h |
| **GTM-UX-002** | 🟠 HIGH | Dashboard/Historico falso + zero results | Baixa | **P1** | 10h |
| **GTM-UX-003** | 🟡 MEDIUM | Retry confuso | Baixa | **P1** | 6h |
| **GTM-UX-004** | 🟠 HIGH | Pos-pagamento quebrado | Baixa | **P1** | 6h |
| **GTM-INFRA-001** | 🟠 HIGH | Workers bloqueados | Media | **P2** | 8h |
| **GTM-INFRA-002** | 🟡 MEDIUM | CB nao tripa, deploys matam buscas | Baixa | **P2** | 4h |
| **GTM-INFRA-003** | 🟡 MEDIUM | Cache ineficiente | Media | **P2** | 8h |
| **GTM-POLISH-001** | 🟢 LOW | Loading inconsistente | Baixa | **P3** | 6h |
| **GTM-POLISH-002** | 🟢 LOW | Mobile quebrado | Media | **P3** | 8h |

**Total:** 13 stories | ~132h

---

## Stories por Tier

### Tier 1 — Bloqueadores de GTM (P0) — 60h

Sem estas stories, o produto nao funciona para o publico GTM.

| # | Story | Link | Resumo |
|---|-------|------|--------|
| 1 | GTM-ARCH-001 | [async-job-pattern](GTM-ARCH-001-async-job-pattern.md) | Railway 120s mata pipeline 360s. Async job + feature flag + rollback. |
| 2 | GTM-ARCH-002 | [cache-global-cross-user](GTM-ARCH-002-cache-global-cross-user.md) | Cache per-user deixa trial users expostos. Cache global + warmup. |
| 3 | GTM-PROXY-001 | [sanitizar-proxies](GTM-PROXY-001-sanitizar-proxies-erro-ingles.md) | 7+ proxies sem sanitizacao. Erros em ingles. Localhost fallback. |

### Quality Gate — Executar apos Tier 1

| # | Story | Link | Resumo |
|---|-------|------|--------|
| — | GTM-QUAL-001 | [smoke-test-e2e](GTM-QUAL-001-smoke-test-e2e-pos-root-cause.md) | Validacao E2E: signup→busca→resultado. Zero ingles. Max 1 banner. |

### Tier 2 — Experiencia Precaria (P1) — 34h

Sem estas, churn garantido nos primeiros 5 minutos.

| # | Story | Link | Resumo |
|---|-------|------|--------|
| 4 | GTM-UX-001 | [banner-unico](GTM-UX-001-data-quality-banner-unico.md) | 8 banners empilham. Consolidar em 1 DataQualityBanner. |
| 5 | GTM-UX-002 | [erros-explicitos](GTM-UX-002-erros-silenciosos-estados-explicitos.md) | Dashboard zerado em outage. Zero results com sugestoes acionaveis. |
| 6 | GTM-UX-003 | [retry-unificado](GTM-UX-003-retry-unificado.md) | 2 mecanismos de retry competem. Cooldown 30s excessivo. |
| 7 | GTM-UX-004 | [subscription-dead-buttons](GTM-UX-004-subscription-status-dead-buttons.md) | Status "pending" falso. Botao "Ver ultima busca" morto. |

### Tier 3 — Infraestrutura de Resiliencia (P2) — 20h

Protecao contra falhas em cascata.

| # | Story | Link | Resumo |
|---|-------|------|--------|
| 8 | GTM-INFRA-001 | [sync-fallback-cb](GTM-INFRA-001-eliminar-sync-fallback-circuit-breaker.md) | Sync PNCPClient bloqueia event loop. CB threshold 50 lento. |
| 9 | GTM-INFRA-002 | [canary-railway](GTM-INFRA-002-health-canary-railway-config.md) | Canary testa 10 (prod usa 50). drainingSeconds=15 mata buscas. |
| 10 | GTM-INFRA-003 | [revalidation-quota](GTM-INFRA-003-revalidation-multisource-skip-quota.md) | Revalidation PNCP-only. Quota consumida em cache stale. |

### Tier 4 — Polimento (P3) — 14h

Pos-launch, melhoria continua.

| # | Story | Link | Resumo |
|---|-------|------|--------|
| 11 | GTM-POLISH-001 | [loading-consistency](GTM-POLISH-001-consistencia-ux-loading.md) | 5 padroes de auth loading. Pipeline sem skeleton. |
| 12 | GTM-POLISH-002 | [mobile-error-tabs](GTM-POLISH-002-mobile-error-pipeline-tabs.md) | Retry card overflow 375px. Pipeline kanban inutilizavel mobile. |

---

## Grafo de Dependencias

```
GTM-ARCH-001 (async job) ──→ GTM-ARCH-002 (cache global)
                         ──→ GTM-INFRA-001 (sync fallback, less critical)

GTM-PROXY-001 (sanitizar) ──→ GTM-UX-004 (subscription status)

Tier 1 completo ──→ GTM-QUAL-001 (smoke test) ──→ Tier 2

GTM-UX-001 (banner unico)  ┐
GTM-UX-002 (erros explicitos)├── Paralelas entre si
GTM-UX-003 (retry unificado)┘

Tier 2 completo ──→ GTM-QUAL-001 (re-run) ──→ Tier 3

GTM-INFRA-001 ┐
GTM-INFRA-002 ├── Paralelas entre si
GTM-INFRA-003 ┘

Tier 3 completo ──→ GTM-QUAL-001 (re-run) ──→ Tier 4

GTM-POLISH-001 ┐
GTM-POLISH-002 ├── Paralelas, apos Tier 1-3
               ┘

Todas completas ──→ GTM-QUAL-001 (final) ──→ GTM Launch
```

---

## Ordem de Execucao Recomendada

### Sprint 6 (Tier 1 — P0): ~60h

```
[Paralelo]
├── GTM-ARCH-001 (32h) — async job pattern + feature flag + rollback
└── GTM-PROXY-001 (12h) — sanitizar proxies

[Sequencial apos ARCH-001]
└── GTM-ARCH-002 (16h) — cache global

[Quality Gate]
└── GTM-QUAL-001 (4h) — smoke test E2E validacao Tier 1
```

### Sprint 7 (Tier 2 — P1): ~34h

```
[Paralelo]
├── GTM-UX-001 (12h) — banner unico
├── GTM-UX-002 (10h) — erros explicitos + zero results
├── GTM-UX-003 (6h) — retry unificado
└── GTM-UX-004 (6h) — subscription + dead buttons

[Quality Gate]
└── GTM-QUAL-001 re-run — validacao Tier 2
```

### Sprint 8 (Tier 3 — P2): ~20h

```
[Paralelo]
├── GTM-INFRA-001 (8h) — sync fallback + CB
├── GTM-INFRA-002 (4h) — canary + railway
└── GTM-INFRA-003 (8h) — revalidation + quota

[Quality Gate]
└── GTM-QUAL-001 re-run — validacao Tier 3
```

### Sprint 9 (Tier 4 — P3): ~14h

```
[Paralelo]
├── GTM-POLISH-001 (6h) — loading consistency
└── GTM-POLISH-002 (8h) — mobile + pipeline tabs

[Quality Gate Final]
└── GTM-QUAL-001 final — validacao pre-GTM launch
```

---

## Numeros do Squad

| Metrica | Valor |
|---------|-------|
| **Agentes** | 4 (architect, qa, ux, data-engineer) |
| **Tempo total** | ~16 min (paralelo) |
| **Tools usados** | 193 |
| **Tokens consumidos** | ~564k |
| **Findings unicos** | 101 |
| **Stories geradas** | 13 (3 P0, 5 P1, 3 P2, 2 P3) |

---

*Documento gerado em 2026-02-23 com base em root cause analysis de 4 dominios: arquitetura, QA, UX, data engineering.*
