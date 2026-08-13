# ROADMAP — SmartLic

**Versao:** 9.0 | **Atualizado:** 2026-08-13 | **Status:** inbound CONFENGE — caminho crítico P0 vigente ([ADR-STRAT-001](docs/adr/ADR-STRAT-001-smartlic-confenge-inbound.md))

> **Direção vigente ([#1262](https://github.com/tjsasakifln/SmartLic/issues/1262)):** SmartLic é o public discovery / intelligence / inbound plane da CONFENGE, alimentado pelo extra-cli. Não há tese de assinatura, trial, Stripe ou DataLake próprio. Documento operacional: [`docs/strategy/critical-path.md`](docs/strategy/critical-path.md).

## Caminho crítico (único backlog que compete por recurso)

Ordem estrita. P1/P2 não furam esta fila.

| Ordem | Issue | Entrega |
|------:|-------|---------|
| 1 | [#1262](https://github.com/tjsasakifln/SmartLic/issues/1262) | Decisão estratégica e freeze |
| 2 | [#2111](https://github.com/tjsasakifln/SmartLic/issues/2111) | Sunset SaaS / Stripe / trial / quotas |
| 3 | [#2113](https://github.com/tjsasakifln/SmartLic/issues/2113) | Preservar patrimônio SEO |
| 4 | [extra-cli#354](https://github.com/tjsasakifln/extra-cli/issues/354) | `public_read_v1` |
| 5 | [#2108](https://github.com/tjsasakifln/SmartLic/issues/2108) | Consumir contrato; aposentar DataLake/crawler SmartLic |
| 6 | [#2112](https://github.com/tjsasakifln/SmartLic/issues/2112) | Public intelligence MVP |
| 7 | [#2116](https://github.com/tjsasakifln/SmartLic/issues/2116) | Isolamento / performance |
| 8 | [#2115](https://github.com/tjsasakifln/SmartLic/issues/2115) | Runtime mínimo Netcup |
| 9 | [#2114](https://github.com/tjsasakifln/SmartLic/issues/2114) | Marca SmartLic ↔ CONFENGE |
| 10 | [#2117](https://github.com/tjsasakifln/SmartLic/issues/2117) | Attribution e handoff |
| 11 | Go-live público | Somente com gates verdes |

**Next (não agora):** #2109 product-as-content · #2118 pSEO só com dado único.  
**Later:** #2107 assessment privado.  
**Fora:** Warmbly, CRM, Kafka, K8s, segundo DataLake, novo billing.

O bloco abaixo (EPIC-GROWTH-VIRAL e fases 2026-04) é **histórico do período SaaS**. Não é o plano vigente.

## 2026-04-24 — EPIC-GROWTH-VIRAL-2026-Q3: On-Page CAC-Zero (HISTÓRICO / SUPERSEDIDO)

21 stories organizadas em 6 waves (142 SP, 4 sprints). Objetivo *na época*: loops virais e CAC. **Supersedido por ADR-STRAT-001** — signup/K-factor não é north star. Mantido apenas como arquivo histórico.

- **Wave 0 Infra (GV-001):** A/B testing framework + funnel auto-tracking (BLOCKER)
- **Wave 1 Viral Loops (GV-002-005):** watermark + pseudonimização, analysis replay, embed widget, propose-to-colleague
- **Wave 2 Scarcity (GV-006-008):** early-access waitlist, trending gallery, live impact ticker
- **Wave 3 Habit (GV-009-012):** daily matching, badges+certificate LinkedIn, weekly wins digest, post-win celebration
- **Wave 4 Collaboration (GV-013-015):** team invites tiered, consultoria→cliente read-only, concorrente alert
- **Wave 5 Monetization (GV-016-018):** usage milestone ROI variant, exit-intent modal, referral tiered+social widget
- **Wave 6 Content (GV-019-021):** sectorial benchmarking, ROI calculator embed, churn winback campaign

Epic master: `docs/stories/2026-04/EPIC-GROWTH-VIRAL-2026-Q3.md`. Estende STORY-289/312/432/449 sem duplicar. Milestone #4 criado. Issues ainda nao criados — status: Draft.

---

## 2026-04 — Cache Warming Deprecation (DataLake é a fonte)

Decisão arquitetural baseada no novo modelo de dados: Supabase agora armazena ~50K licitações abertas (`pncp_raw_bids`) + 2M+ contratos históricos (`supplier_contracts`, estratégia 100% orgânica de inbound via SEO). Consultas vão ao DB com latência <100ms.

- **Layer 3 cache warming proativo removido** — jobs startup/cron/coverage-check deletados (`cron/cache.py` reduzido a cleanup; `jobs/cron/cache_ops.py` deletado; `cache_warming_job` + `cache_refresh_job` removidos).
- **Feature flags deletadas:** `WARMUP_ENABLED`, `CACHE_WARMING_ENABLED`, `CACHE_REFRESH_ENABLED`, `CACHE_WARMING_POST_DEPLOY_ENABLED` + constantes `WARMING_*`, `CACHE_REFRESH_*`, `WARMUP_*`.
- **Funções admin removidas:** `get_stale_entries_for_refresh`, `get_top_popular_params`, `get_popular_ufs_from_sessions` (consumidas apenas pelos jobs).
- **Cache passivo permanece:** `search_results_cache` (Supabase 24h) + Redis L2 + InMemory L1 + SWR por-request em `cache/swr.py::trigger_background_revalidation`.
- **Stories substituídas (Superseded):** GTM-STAB-007, CRIT-081, CRIT-055, GTM-ARCH-002 marcadas como Superseded.
- **STORY-CIG-BE-cache-warming-deprecate** (branch `fix/cig-be-wave2-tier1-plus-tier2`) — deleta 6 arquivos de teste (~40 testes obsoletos), remove código, atualiza docs.
- **Migration `20260308330000_debt009_ban_cache_warmer.sql` mantida** — conta banida permanece (agora por razão ainda mais forte: não existe mais).


---

## Status Atual

```
ESTRATÉGIA (#1262 / ADR-STRAT-001):   [########............] docs + freeze (este ciclo)
SUNSET SaaS (#2111):                  [....................] após #1262
SEO PATRIMÔNIO (#2113):               [....................]
extra-cli public_read_v1 (#354):      [....................] producer
CONSUMER (#2108):                     [....................]
MVP PÚBLICO (#2112):                  [....................]
ISOLAMENTO (#2116) / NETCUP (#2115):  [....................]
MARCA (#2114) / HANDOFF (#2117):      [....................]
GO-LIVE PÚBLICO:                      [....................] gated

— histórico legado (não é o plano vigente) —
POC / GTM / RELIABILITY / FOUNDERS / TD / INTEL / UX / Q2 / SDD: 100% no tracker antigo
```

**Production (transição):** https://smartlic.tech — ainda no runtime legado (Railway/Supabase). Destino: Netcup + extra-cli.

---

## Fases Concluidas

### Fase 1 — POC Core (Jan 2026)
PNCP client, filtering engine, Excel export, LLM summaries, Next.js frontend. Deployed Jan 28.

### Fase 2 — Multi-Sector + GTM Launch (Feb 1-14)
15 sectors, Stripe billing, onboarding wizard, trial conversion, SSE progress, PCP integration, pipeline management. 10 GTM stories + 37 production fixes.

### Fase 3 — GTM Resilience (Feb 17-20)
25 stories across 6 tracks. See `docs/gtm-resilience-summary.md` for details.

| Track | Stories | Key Deliverables |
|-------|---------|------------------|
| A — Never Empty | 5 | Fallback cascade, partial results, coverage bar |
| B — Smart Cache | 6 | Two-level cache, SWR, hot/warm/cold priority, admin dashboard |
| C — Coverage UX | 3 | Confidence indicator, freshness, reliability badges |
| D — Classification | 5 | Zero-match LLM, viability assessment, feedback loop |
| E — Observability | 3 | Structured logging, Prometheus metrics, Sentry |
| F — Infrastructure | 3 | ARQ job queue, OpenTelemetry tracing, schema validation |

### Fase 4 — Reliability Sprint (Feb 22-27)
13 stories across 4 sprints. Architecture hardening for multi-worker production.

| Sprint | Stories | Key Deliverables |
|--------|---------|------------------|
| Sprint 0 — Make It Work | STORY-283, 290, 291, 292, 293 | Event loop unblock, Supabase circuit breaker, async search 202 pattern, CI fix |
| Sprint 1 — Make It Reliable | STORY-294, 295, 296, 297, 298 | Redis state externalization, progressive results, bulkhead per source, SSE resumption, unified error UX |
| Sprint 2 — Make It Observable | STORY-299, 300 | SLOs + alerting dashboard, security hardening (CSP, LGPD) |
| Sprint 3 — Make It Competitive | STORY-301, 302 | Email alert system (CRUD, cron, dedup), documentation cleanup |

### Fase 4.1 — GTM Repricing (Feb 25-26)
Market-validated pricing realignment.

| Story | Title | Status |
|-------|-------|--------|
| STORY-277 | Repricing R$1.999 → R$397/mes | Completed |
| STORY-280 | Boleto + PIX via Stripe | Completed |
| STORY-284 | GTM Quick Wins | Completed |

### Fase 4.2 — Reposicionamento B2G Phase 0 (Mai 2026) — 100% Concluido

23 de 23 issues fechadas (milestone #5 fechado). Reposicionamento completo do produto para B2G, novas páginas e disclaimers legais.

| Série | Entregáveis |
|-------|-------------|
| REPO-001–005 | Labels GitHub, doc copywriting guidelines, audit disclaimers legais, lead_capture estendido, fix CNPJ footer |
| REPO-006–012 | Hero homepage reescrito, REPO-007 disclaimer servidor público, bloco 3 níveis, /consultoria-b2g, /navbar dropdown, footer colunas, componente DiagnosticForm |
| REPO-013–018 | ViabilityVerdict plug pSEO, CTA contextual 4 rotas, REPO-015, title/meta GSC-driven, Mixpanel eventos padronizados, Rename PNCP→nossas fontes |
| REPO-019–022 | Mixpanel funnel, remover copy garantia ganho, Disclaimer recomendação algorítmica, Gate decision doc 14d |

Milestone: `Reposicionamento B2G Phase 0` (#5) — 23/23 fechado. #775 (INDEX) fechado em 2026-05-13.

### Fase 4.3 — pSEO Health Sprint (Mai 2026) — Concluido

10 issues P0 qualidade de sinal Google (#656–#665). BreadcrumbList JSON-LD, DISTINCT queries, og:image dinâmica, sitemap freshness, robots.ts fix, sameAs bug fix. Milestone #2 fechado (12 issues total).

### Fase 4.4 — On-Page CTA & Copy Sprint (Mai 2026) — Concluido

10 issues CTA/copy (#619–#621, #623–#627, #651, #652). CTAs inline programmatic pages, TrialCountdown copy, social proof, meta descriptions GSC. Milestone #3 fechado (12 issues total). Nota: #622 nao existe — range original com gap.

### Fase 4.5 — Conversão + Instrumentação (Mai 2026) — Concluido

CONV-INST-001–005: Mixpanel page-load, signup lifecycle events, email confirmation, CNPJ deep-link onboarding, MS Clarity trial tagging. SEC-HMAC-001: HMAC verify webhook. SEC-SECDEF-001/002: SECURITY DEFINER audit + CI guard. Todas as issues fechadas (#606, #607, #608, #697, #698, #714, #854, #855, #901, #902).

### Fase 5 — Founders Plan (Mai 2026) — Concluido

Plano Fundadores vitalício R$997 one-time. 23 issues implementados em 2 dias.

| Entregável | Issues |
|-----------|--------|
| Backend: pivot checkout one-time, webhook entitlement, session-status endpoint | #782, #783, #785, #861, #862, #863, #865 |
| DB: campos founder em profiles, feature flag FOUNDERS_OFFER_ENABLED | #784, #794 |
| Frontend: /fundadores page, banner global, CTAs pSEO, /pricing comparação, /obrigado dual-state | #786, #787, #788, #789, #792, #864, #870, #872 |
| Tracking: founders_* events Mixpanel | #790 |
| Email: welcome founders template | #791, #868 |
| Legal: /termos/fundadores, founders-policy.md | #793, #795 |
| Copy: headline pain-focused, FAQ objeções reais, features benefit-driven | #867 |

---

## Backlog Ativo

O backlog que compete por recurso está **somente** na tabela do caminho crítico no topo deste arquivo e em [`docs/strategy/backlog-review-1262.md`](docs/strategy/backlog-review-1262.md). As seções abaixo são arquivo histórico (epics 2026-04/05/06). #1262 deixou de ser "Terminal do Operador" e passou a ser a decisão de inbound.

### Intel Reports Epic (100% — todas fechadas · tese de compra avulsa em sunset)

Milestone: `Intel Reports Epic` (#1) — open:0, closed:8.

| Story | Título | Status |
|-------|--------|--------|
| #628 | Migration + RPC cnpj_supplier_intel | Closed |
| #629 | PDF Generator + LLM narrative Raio-X | Closed |
| #630 | Stripe checkout + webhook fulfillment | Closed |
| #631 | ARQ background job + Storage delivery | Closed |
| #632 | Frontend CTA + checkout flow + polling | Closed |
| #826 | RPC sector_uf_intel (INTEL-REPORT-002) | Closed |
| #634 | EPIC: One-Time Data Products — Raio-X + Mapa Setorial | Closed |
| #633 | Mapa de Oportunidade Setorial (R47) | Closed |

### Technical Debt (TD — 100% concluido)

61 TD issues (#178–#238). Todas fechadas. 0 abertas.

| Sprint | Stories | Focus |
|--------|---------|-------|
| Sprint 0 | TD-HP-001 a TD-HP-012 | Hot path (LLM fallback, Excel buffer, PNCP parsing, race conditions) |
| Sprint 1 | TD-GTM-001 a TD-GTM-004 | GTM infra (Supabase singleton, rate limiter, plan capabilities, security) |
| Sprint 2 | TD-UX-001 a TD-UX-004 | Accessibility (ARIA labels, keyboard nav, focus, color contrast) |
| Sprint 3 | TD-CODE-001, TD-TEST-001 a TD-TEST-005 | Test coverage + god component split |
| Sprint 4 | TD-BE-002 a TD-BE-025 | Backend (SQL injection, validation, error handling, health checks) |
| Sprint 5 | TD-FE-002 a TD-FE-031 | Frontend (state mgmt, re-renders, code splitting, form validation, API interceptors) |
| Sprint 6 | TD-OPS-001 a TD-OPS-014 | DevOps (CI coverage, deploy pipeline, health checks, load tests) |
| Sprint 7 | TD-TEST-012 a TD-TEST-028 | Testing (async concurrency, E2E scenarios, accessibility, security, error recovery) |

### UX Premium (UX-301 to UX-335) — 22.9% (12/35 issues criadas)

Source: `docs/stories/EPIC-UX-PREMIUM-2026-02.md` (35 problems from production audit). 12 issues criadas no tracker (#1559–#1573), todas closed.

**Issues Criadas (2026-06-08):**

| Issue | Título | Status |
|-------|--------|--------|
| #1559 | UX-306: Add Header/Navigation na Página de Conta | Closed |
| #1560 | UX-313: Empty State em 'Buscas Salvas' | Closed |
| #1561 | UX-312: Indicador de Quota de Análises visível no header | Closed |
| #1562 | UX-307: Validação de Senha em Tempo Real no Signup/Reset | Closed |
| #1564 | UX-314: Indicador de Estado em 'Personalizar busca' | Closed |
| #1565 | UX-315: Slider de Valor com Tooltip em Drag | Closed |
| #1566 | UX-316: Hover States em Cards de Modalidade | Closed |
| #1567 | UX-308: Confirmação em Cancelamento de Plano | Closed |
| #1570 | UX-309: Fix Estados 'Aguardando...' Indefinidamente | Closed |
| #1571 | UX-310: Mensagens de Erro Acionáveis (Não Genéricas) | Closed |
| #1572 | UX-311: Estimativa de Tempo Realista (Calibração) | Closed |
| #1573 | UX-317: Fix Links Quebrados no Footer | Closed |

**Pendentes de criação (23 issues):** UX-301 a UX-305, UX-318 a UX-335 — backlog.

### Growth Viral Epic Q3 (GV-001 to GV-021) — Draft

Source: `docs/stories/2026-04/EPIC-GROWTH-VIRAL-2026-Q3.md`

| Sprint | Stories | Foco | SP |
|--------|---------|------|----|
| 1 | GV-001, 002, 005, 018 | Infra + viral loops base + referral UI | 26 |
| 2 | GV-003, 006, 009, 012, 013, 017, 021 | Replay + waitlist + daily + winback | 42 |
| 3 | GV-004, 007, 010, 014, 016 | Embed + trending + badges + consultoria | 45 |
| 4 | GV-008, 011, 015, 019, 020 | Ticker + wins digest + concorrente + content | 29 |

Status: todas Draft — Milestone criado (#4), issues a criar.

---

## Q2 2026 — Inteligencia Multi-Camada (em execucao)

5 EPICs lançados 2026-05-16 a 2026-06-02 + CONV + Verticais Premium. ~85 issues (~83 closed, ~2 open). Foco: camada de inteligência B2G profunda além da busca. Progresso real: ~99% concluído (recálculo audit 2026-06-15 — 31 state mismatches corrigidos, 4/5 EPICs fechados, UX Premium + SDD Gaps 100%).

### EPIC-SUBINTEL — Inteligencia de Cadeia de Fornecimento (#1224)

| Issue | Título | Status |
|-------|--------|--------|
| #1224 | EPIC-SUBINTEL — Inteligência de Cadeia de Fornecimento / Subcontratação | Closed |
| #1225 | SUBINTEL-002 — RPC subcontract_regional_dependency | Closed |
| #1226 | SUBINTEL-002 — RPC subcontract_regional_dependency | Closed |
| #1227 | SUBINTEL-003 — RPC supplier_growth_anomaly (Wave 0) | Closed |
| #1228 | SUBINTEL-010 — Radar de Subcontratação: score + página + narrativa LLM | Closed |
| #1229 | SUBINTEL-011 — Score de Oportunidade de Parceria em /fornecedores/[cnpj] | Closed |
| #1230 | SUBINTEL-012 — Índice de Dependência Regional: heatmap visual (Wave 1) | Closed |
| #1231 | SUBINTEL-020 — Rede de fornecedores recorrentes por órgão (Wave 2) | Closed |
| #1232 | SUBINTEL-021 — Matching B2B entre fornecedores opt-in LGPD (Wave 2) | Closed |
| #1233 | SUBINTEL-022 — Potenciais subcontratações por edital aberto: bloco aditivo | Closed |
| #1235 | SUBINTEL-031 — Novo tier premium "SmartLic Insight" (empacotamento) | **Open** (Paused-Revenue-Dependent) |
| #1234 | SUBINTEL-030 — Capability allow_subcontract_intel + feature flag (Wave 3) | Closed |

### EPIC-PREDINT — Inteligencia Preditiva de Demanda Governamental (#1260)

| Issue | Título | Status |
|-------|--------|--------|
| #1260 | EPIC-PREDINT — Inteligência Preditiva de Demanda Governamental | Closed |
| #1264 | PREDINT-001 — RPC predict_opportunity_window | Closed |
| #1265 | PREDINT-002 — RPC predict_budget_cycle | Closed |
| #1266 | PREDINT-003 — RPC predict_seasonal_calendar | Closed |
| #1267 | PREDINT-004 — RPC predict_incumbent_decay | Closed |
| #1268 | PREDINT-005 — RPC predict_expansion_organs | Closed |
| #1269 | PREDINT-010 — Radar de Recorrência Governamental (página flagship) | Closed |
| #1270 | PREDINT-011 — Heatmap Nacional de Oportunidades Futuras | Closed |
| #1271 | PREDINT-012 — Calendário Sazonal Interativo (grid UF × setor × mês) | Closed |
| #1291 | PREDINT-000 — Capability allow_predictive_intel + feature flag | Closed |

### EPIC-COMPINT — Inteligencia Concorrencial Profunda (#1261)

| Issue | Título | Status |
|-------|--------|--------|
| #1261 | EPIC-COMPINT — Inteligência Concorrencial Profunda (OSINT B2G) | Closed |
| #1272 | COMPINT-001 — RPC competitor_territory_map | Closed |
| #1273 | COMPINT-002 — RPC competitor_win_metrics | Closed |
| #1274 | COMPINT-003 — RPC competitor_shadow_network | Closed |
| #1275 | COMPINT-010 — Mapa de Território Competitivo (página flagship) | Closed |
| #1276 | COMPINT-011 — Seção 'Inteligência Concorrencial' em /fornecedores/[cnpj] | Closed |
| #1292 | COMPINT-000 — Capability allow_competitive_intel + feature flag | Closed |

### EPIC-NETINT — Camada de Rede / Inteligencia Coletiva B2G (#1263)

| Issue | Título | Status |
|-------|--------|--------|
| #1263 | EPIC-NETINT — Camada de Rede / Inteligência Coletiva B2G | Closed |
| #1283 | NETINT-001 — Schema network_events_agg + mecanismo de coleta anonimizada | Closed |
| #1284 | NETINT-002 — RPC network_intel_snapshot | Closed |
| #1285 | NETINT-003 — RPC network_orgao_patterns | Closed |
| #1286 | NETINT-004 — RPC network_discount_trends | Closed |
| #1287 | NETINT-010 — Feed de Inteligência Coletiva (bloco aditivo na dashboard) | Closed |
| #1288 | NETINT-011 — Bloco 'Padrões de Mercado' em páginas de setor (pSEO aditivo) | Closed |

### EPIC-B2GOPS — escopo antigo (workspace). #1262 foi reutilizada.

O workspace/war-room (#1277–#1294) está fechado e **não** é caminho crítico (SUNSET/DEFER). A issue #1262 agora é a decisão de inbound CONFENGE.

| Issue | Título | Status |
|-------|--------|--------|
| #1262 | Reposicionar SmartLic como braço público de inbound da CONFENGE | Open (decisão vigente) |
| #1277 | B2GOPS-001 — Schema workspace_watchlists + RPCs | Closed |
| #1278 | B2GOPS-002 — Schema workspace_documents + RPCs de gestão documental | Closed |
| #1279 | B2GOPS-003 — Schema workspace_timeline + RPCs de timeline operacional | Closed |
| #1280 | B2GOPS-010 — Workspace Colaborativo (página flagship /workspace) | Closed |
| #1281 | B2GOPS-011 — Alertas Inteligentes (watchlist + contratos + timeline) | Closed |
| #1282 | B2GOPS-012 — Centro de Guerra de Pregão (/workspace/centro-guerra/[id]) | Closed |
| #1294 | B2GOPS-004 — Schema workspace_war_rooms + RPCs + SSE channel | Closed |
| #1293 | B2GOPS-000 — Capability allow_workspace_basic + feature flag | Closed |

### CONV — Conversao pSEO (45 issues — 12 open, 33 closed)

14 issues originais (#1310–#1323) criados 2026-05-31 + 25 sub-issues expandidos 2026-06-01 a 2026-06-02. Foco: otimizacao de conversao em paginas programaticas.

**Wave 1 — Core (14 issues originais #1310–#1323)**

| Issue | Título | Prioridade | Status |
|-------|--------|-----------|--------|
| #1310 | CONV-001: pSEO — Caixa de valor agressiva acima da dobra | P0 | Closed |
| #1311 | CONV-002: Landing pages transacionais — Fornecedor/CNPJ/Órgão/Contrato | P0 | Closed |
| #1312 | CONV-003: Captura contextual — Blog/Perguntas/Glossário com simulador | P0 | Closed |
| #1313 | CONV-004: 'Aha moment' pré-cadastro — Insight grátis | P0 | Closed |
| #1314 | CONV-005: Monetização de entrada — Microtransações (relatórios avulsos) | P0 | Closed |
| #1315 | CONV-006b: Rollout SERP — Reescrever títulos/metadescriptions 74 páginas | P0 | Closed |
| #1316 | CONV-007: Trilhas por intenção — 4 clusters de busca | P0 | Closed |
| #1317 | CONV-008a: Subcontratação como categoria central — Páginas flagship | P0 | Closed |
| #1318 | CONV-009: Instrumentar conversão — Scroll/CTA/Checkout/Abandono | P0 | Closed |
| #1319 | CONV-010: Landing pages autônomas — Cada página = proposta comercial | P0 | Closed |
| #1320 | CONV-006a: Quick Win SERP — Reescrever 4 piores páginas (deploy 24h) | P0 | Closed |
| #1321 | CONV-008b: Subcontratação — Blocos aditivos em páginas existentes | P1 | Closed |
| #1322 | CONV-011: Sequência de pós-compra — Email transacional + upsell 0h/48h/7d | P0 | Closed (substituída por #1331 CONV-011b) |
| #1323 | CONV-012: Infraestrutura de A/B testing para páginas pSEO | P1 | Closed |

**Wave 1b — Novas issues (2026-06-01 a 2026-06-02)**

| Issue | Título | Prioridade | Status |
|-------|--------|-----------|--------|
| #1324 | CONV-013: Botão WhatsApp direto com founder — captura por canal Brasil | P1 | Closed |
| #1325 | CONV-009b: Wirear instrumentação pSEO nas páginas reais | P0 | Closed |
| #1327 | CONV-002b: Wirear PSEOTemplate + PreviewCTA nas 5 entity pages | P0 | Closed |
| #1328 | CONV-014: Liberar sistema de alertas — remover feature flag | P0 | Closed |
| #1329 | CONV-015: Landing pages de caso de uso — hubs conectando intenção a dados | P1 | Closed |
| #1330 | CONV-016: Sinais de urgência em páginas pSEO | P1 | Closed |
| #1332 | CONV-017: Interlinking journeys programático | P1 | Closed |
| #1333 | CONV-018: Segmento do usuário no primeiro contato | P1 | Closed |

**Wave 2 — Microtransações (CONV-005b, #1326, #1334–#1337)**

| Issue | Título | Status |
|-------|--------|--------|
| #1334 | CONV-005b-1: Schema digital_products + migration + seed | Closed |
| #1335 | CONV-005b-2: Endpoint POST /api/checkout/one-time genérico | Closed |
| #1326 | CONV-005b: Checkout modular para microtransações | Closed |
| #1336 | CONV-005b-3: Preview configurável + componente checkout frontend | Closed |
| #1337 | CONV-005b-4: ARQ job delivery + página obrigado pós-compra | Closed |

**Wave 3 — Pós-compra (CONV-011b, #1331, #1338–#1340)**

| Issue | Título | Status |
|-------|--------|--------|
| #1338 | CONV-011b-1: Schema post_purchase_sequences + webhook | Closed |
| #1331 | CONV-011b: Sequência de pós-compra — email + upsell 0h/48h/7d | Closed (subs #1338-#1340 fechados) |
| #1339 | CONV-011b-2: 3 templates email (delivery, followup, reengagement) | Closed |
| #1340 | CONV-011b-3: ARQ jobs post_purchase_sequence + tracking Mixpanel | Closed |

**CRO-CTA (2026-05-30 a 2026-06-02) — Arquitetura de CTA por intenção**

| Issue | Título | Status |
|-------|--------|--------|
| #1211 | CRO-CTA-005: /blog/subcontratacao-licitacoes-regras-lei-14133 — CTA estratégia de entrada para PME | Closed |
| #1212 | CRO-CTA-006: /perguntas/indice-reajuste-contrato-publico — CTA contratos monitoráveis | Closed |
| #1213 | CRO-CTA-007: /blog/licitacoes/facilities/es — Inverter mensagem para páginas com zero editais | Closed |
| #1214 | CRO-CTA-000: Arquitetura de CTA por intenção de busca — matar "Teste Grátis" como CTA padrão do pSEO | Closed |

**Verticais Premium (2026-06-02)**

| Issue | Título | Status |
|-------|--------|--------|
| #1373 | P0: Ativar 4 feature flags premium — verticais já codificados | Closed |
| #1374 | P0: White-Label — modelo de inexigibilidade + landing page institucional | Closed |
| #1375 | P0: Ativar B2G_OPS_ENABLED — Pipeline Premium add-on R$0/mês | Closed |
| #1376 | P0: Ativar SUBCONTRACT_INTEL_ENABLED — Supplier Intelligence add-on | Closed |
| #1377 | P0: Ativar COMPETITIVE_INTEL_ENABLED — Competitive Intelligence add-on | Closed |
| #1378 | P0: Ativar PREDICTIVE_INTEL_ENABLED — Predictive Intelligence add-on | Closed |
| #1372 | P0: Datalake API Self-Service — monetização imediata via API REST | Closed |

### REPO — Extensoes pos-Phase 0

| Issue | Título | Status |
|-------|--------|--------|
| #1289 | REPO-COMMS — Overhaul de Copy/Homepage (posicionamento 'vantagem competitiva') | Closed |
| #1290 | REPO-TIER-COMMAND — Novo tier premium 'SmartLic Command' (R$970/mês) | Closed |

### Q2 Wave 4 — Core Features (Jun 2026) — 55 issues (100% closed)

Lançados 2026-06-04. 55 de 55 closed (100%) — todos fechados entre Jun 4-8. Foco: retenção, revenue visibility, API self-service, UX repositioning, feedback loop.

**DIGEST — Motor de Retenção Semanal (#1410–#1413, #1421)**

| Issue | Título | Status |
|-------|--------|--------|
| #1410 | DIGEST-001: Migration + config — coluna frequency, cron pg_cron, flag DIGEST_ENABLED | Closed |
| #1411 | DIGEST-002: Lógica de build do digest — query por setor, top N por tier, fallback | Closed |
| #1412 | DIGEST-003: Template HTML + integração Resend — viability badges, CTA, List-Unsubscribe | Closed |
| #1413 | DIGEST-004: Endpoint de preferências — PATCH /conta/preferencias para frequency toggle | Closed |
| #1421 | DIGEST-005: Métricas + Mixpanel — digest_sent/opened/clicked/unsubscribe | Closed |

**FOUNDER — Revenue Dashboard (#1414–#1417, #1422)**

| Issue | Título | Status |
|-------|--------|--------|
| #1414 | FOUNDER-001: SQL queries — MRR, churn 30d, trial-to-paid 30d/90d, D7 retention, ARPA | Closed |
| #1415 | FOUNDER-002: Cron diário + cache Redis — computar métricas, invalidar a cada 1h | Closed |
| #1416 | FOUNDER-003: Endpoint GET /admin/metrics/revenue — JSON, p95 <500ms | Closed |
| #1417 | FOUNDER-004: Frontend /admin/metrics — cards numéricos + gráfico de coortes (Recharts) | Closed |
| #1422 | FOUNDER-005: Mixpanel founder_metrics_viewed + permission check admin-only | Closed |

**API-SELF — Datalake API Self-Service (#1418–#1425, estende #1372)**

| Issue | Título | Status |
|-------|--------|--------|
| #1372 | P0: Datalake API Self-Service — monetização imediata via API REST | Closed |
| #1418 | API-SELF-001: Migration api_keys + modelo Pydantic + rotas CRUD | Closed |
| #1419 | API-SELF-002: Middleware require_api_key + rota GET /v1/api/search | Closed |
| #1420 | API-SELF-003: Rate limiting por API key via Redis token bucket (respeita tier) | Closed |
| #1423 | API-SELF-004: Stripe — 3 products/prices + webhook + metered billing cron | Closed |
| #1424 | API-SELF-005: Landing page /api + Swagger UI público + pricing cards | Closed |
| #1425 | API-SELF-006: Dashboard de uso no /conta — consumo/mês, gráfico, checkout | Closed |

**LIFECYCLE — User Lifecycle State Machine (#1426–#1429, estende #1408)**

| Issue | Título | Status |
|-------|--------|--------|
| #1408 | feat: Implement User Lifecycle State Machine + Login Tracking | Closed |
| #1426 | LIFECYCLE-001: Migration — profiles.last_login_at, login_count, tabela login_activity | Closed |
| #1427 | LIFECYCLE-002: Auth middleware — atualizar last_login_at + login_activity (Redis write-behind) | Closed |
| #1428 | LIFECYCLE-003: SQL function compute_user_lifecycle() + endpoint GET /admin/users/segments | Closed |
| #1429 | LIFECYCLE-004: Admin dashboard — lifecycle states, transições/semana, power users, Mixpanel | Closed |

**VIAB-UX — Viability Score UX Repositioning (#1430–#1434, #1452–#1453, estende #1405)**

| Issue | Título | Status |
|-------|--------|--------|
| #1405 | feat: Reposition Viability Score as Central UX Element | Closed |
| #1430 | VIAB-UX-001: Mudar default sort para confianca — backend schema + frontend SearchForm | Closed |
| #1431 | VIAB-UX-002: ViabilityBadge inline em cada linha da listagem principal | Closed |
| #1432 | VIAB-UX-003: Tooltip com breakdown dos 4 fatores — Modalidade, Prazo, Valor, Geografia | Closed |
| #1433 | VIAB-UX-004: Seção 'Por que esta oportunidade?' — expandable section no card | Closed |
| #1434 | VIAB-UX-005: A/B test — feature flag VIABILITY_DEFAULT_SORT + métricas de comparação | Closed (substituída por #1452+#1453) |
| #1452 | VIAB-UX-005a: Feature flag VIABILITY_DEFAULT_SORT + split 50/50 via hash user_id | Closed |
| #1453 | VIAB-UX-005b: Admin dashboard de A/B test — metricas comparativas + significancia estatistica | Closed |

**FEEDBACK — Feedback Loop + Sector Affinity (#1435–#1439, estende #1406)**

| Issue | Título | Status |
|-------|--------|--------|
| #1406 | feat: Close the Feedback Loop — Learn from User Behavior | Closed |
| #1435 | FEEDBACK-001: Migration user_sector_affinity — tabela + RLS + seed inicial | Closed |
| #1436 | FEEDBACK-002: Atualizar affinity no feedback — correct +0.1, false_positive -0.2 por setor | Closed |
| #1437 | FEEDBACK-003: Combined score adjustment — fator de afinidade no enrich pipeline | Closed |
| #1438 | FEEDBACK-004: Endpoint GET /profile/sector-affinity — transparência de afinidades | Closed |
| #1439 | FEEDBACK-005: Frontend — 'Setores que não me interessam' + mute/unmute na /conta/preferencias | Closed |

**NO-JARGON — Replace Technical Jargon (#1440–#1443, estende #1407)**

| Issue | Título | Status |
|-------|--------|--------|
| #1407 | fix: Replace Technical Jargon in Customer-Facing UX | Closed |
| #1440 | NO-JARGON-001: Substituir 'Cache' → 'Dados recentes' nos 6 componentes de busca | Closed |
| #1441 | NO-JARGON-002: Substituir 'GPT-4', 'LLM', 'quota' em componentes visíveis | Closed |
| #1442 | NO-JARGON-003: Blog — substituir 'datalake' por 'base de dados' em 15+ artigos | Closed |
| #1443 | NO-JARGON-004: Atualizar BANNED_PHRASES + extender validação para blog e search components | Closed |

**ENTITY — Entity Tracking (#1444–#1447, estende #1409)**

| Issue | Título | Status |
|-------|--------|--------|
| #1409 | feat: Enable "Follow Organ/Competitor" Entity Tracking | Closed (subs #1444-#1447 fechados) |
| #1444 | ENTITY-001: Migration — adicionar tracked_orgaos e tracked_fornecedores ao schema de alertas | Closed |
| #1445 | ENTITY-002: Alert matcher — cruzar novos bids com CNPJ dos órgãos/fornecedores trackeados | Closed |
| #1446 | ENTITY-003: Frontend — botão 'Seguir' nas páginas de órgão e CNPJ | Closed |
| #1447 | ENTITY-004: Limite de entidades por plano + upgrade prompt | Closed |

**TIER-COMMAND — SmartLic Command Tier (#1448–#1451, estende #1290)**

| Issue | Título | Status |
|-------|--------|--------|
| #1448 | TIER-COMMAND-001: PlanCapabilities + TierConfig — novo tier 'command' no quota_core.py | Closed |
| #1449 | TIER-COMMAND-002: Stripe — novo product/price + webhook handlers | Closed |
| #1450 | TIER-COMMAND-003: Feature flags por capability — gate de acesso às funcionalidades Command | Closed |
| #1451 | TIER-COMMAND-004: Página de checkout + landing page do tier Command | Closed |

**CONV-SUB — CONV Sub-Issues (#1400–#1402)**

| Issue | Título | Status |
|-------|--------|--------|
| #1400 | CONV-003-1: Simulador de Oportunidades — widget interativo para Blog/SEO | Closed |
| #1401 | CONV-007-1: 4 landing pages de intenção (comercial/investigativa/jurídica/subcontratação) | Closed |
| #1402 | CONV-010-1: Template "Proposta Comercial" — bloco aditivo em entity pages | Closed |

**CORE-FEAT — Core Features Avulsas (#1403, #1404) — Concluído**

| Issue | Título | Status |
|-------|--------|--------|
| #1403 | feat: Founder Revenue Dashboard — MRR, Churn, Activation, Retention | Closed (subs #1414-#1417,#1422 fechados) |
| #1404 | feat: Activate Daily/Weekly Digest Email — Motor de Retenção Semanal | Closed (subs #1410-#1413,#1421 fechados) |


### Q2 Wave Extensions — 2026-06-07 (24 novas issues)

Extensões dos 5 EPICs Q2 + CONV. Issues criadas em 2026-06-07.

**CONV — Wave 3+ Extensions (#1509–#1515)**

| Issue | Título | Status |
|-------|--------|--------|
| #1509 | CONV-010-2: AutonomousLandingShell + integração de templates em entity pages | Closed |
| #1510 | CONV-010-3: Homepage refatorada como terminal de inteligência | Closed |
| #1511 | CONV-007-2: IntentRouter + IntentTrail — detecção de intenção e roteamento dinâmico | Closed |
| #1512 | CONV-007-3: Analytics Mixpanel + dashboard por cluster de intenção | Closed |
| #1513 | CONV-003-2: ContextualCapture em páginas de Perguntas jurídicas | Closed |
| #1514 | CONV-003-3: ContextualCapture em páginas de Glossário | Closed |
| #1515 | CONV-003-4: PartialReportPreview + integração LeadCaptureIntermediate | Closed |

**NETINT — Wave 2 Extensions (#1516–#1519)**

| Issue | Título | Status |
|-------|--------|--------|
| #1516 | NETINT-011 — Sinais de Mercado: Trending Sectors & UFs (bloco aditivo na dashboard) | Closed |
| #1517 | NETINT-012 — Network Graph: Visualização de co-ocorrência de fornecedores por órgão | Closed |
| #1518 | NETINT-013 — API de Sinais Coletivos: endpoint público para dados agregados anonimizados | Closed |
| #1519 | NETINT-014 — Widget embedável de Inteligência Coletiva para SEO pages | Closed |

**B2GOPS — Wave 2 Extensions (#1520–#1523)**

| Issue | Título | Status |
|-------|--------|--------|
| #1520 | B2GOPS-013 — Documentos Colaborativos: editor + templates de documentos de licitação | Closed |
| #1521 | B2GOPS-014 — Timeline Intelligence: feed cronológico de eventos do edital | Closed |
| #1522 | B2GOPS-015 — API Integrations: webhooks para Slack, Teams e Email | Closed |
| #1523 | B2GOPS-016 — Mobile Command Center: PWA otimizado para operadores em campo | Closed |

**COMPINT — Wave 2 Extensions (#1524–#1526)**

| Issue | Título | Status |
|-------|--------|--------|
| #1524 | COMPINT-012 — Alertas Competitivos: 'Seu concorrente acaba de vencer' (notificações + email) | Closed |
| #1525 | COMPINT-013 — Benchmarks Setoriais: comparativos de performance por setor (bloco aditivo em /intel-concorrente) | Closed |
| #1526 | COMPINT-014 — Dossiê Competitivo PDF: relatório executivo de concorrente (download) | Closed |

**PREDINT — Wave 2 Extensions (#1527–#1529)**

| Issue | Título | Status |
|-------|--------|--------|
| #1527 | PREDINT-013 — Pipeline Preditivo: 'O que vem aí nos próximos 90 dias' (bloco aditivo na dashboard) | Closed |
| #1528 | PREDINT-014 — Alertas Preditivos: notificações de oportunidades futuras (in-app + email) | Closed |
| #1529 | PREDINT-015 — API de Inteligência Preditiva: endpoints para dados de previsão (Wave 2) | Closed |

**SUBINTEL — Wave 3 Extensions (#1530–#1532)**

| Issue | Título | Status |
|-------|--------|--------|
| #1530 | SUBINTEL-032 — Onboarding + trial específico para vertical de subcontratação (Wave 3) | Closed |
| #1531 | SUBINTEL-033 — Relatórios de Subcontratação: PDF executivo para parceiros (Wave 3) | Closed |
| #1532 | SUBINTEL-034 — API de Subcontratação: endpoints para integração externa (Wave 3) | Closed |

---

### Reversa SDD Confidence Gaps — 100% (21 issues, todas closed)

Issues de engenharia reversa e confidence tracking criadas em 2026-06-08 via Reversa SDD. Lacunas de documentação, resiliência e core-logic identificadas no codebase. Todas as 21 issues fechadas em 2026-06-15.

**🔴 CRITICAL (P0) — 3 issues:**

| Issue | Título | Status |
|-------|--------|--------|
| #1579 | GAP-002: Provisionamento do plano Command — fluxo de ativação enterprise | Closed |
| #1580 | GAP-003: Estratégia de limpeza de cache stale — L1 Redis + L2 Supabase | Closed |
| #1581 | GAP-004: Estratégia de retry ARQ — exponential backoff configurável por job | Closed |

**🟡 MODERATE (P1) — 12 issues:**

| Issue | Título | Status |
|-------|--------|--------|
| #1582 | GAP-001: Atualizar spec billing — sincronização Stripe → plan_billing_periods | Closed |
| #1583 | GAP-005: Fallback SSE quando Redis pub/sub falha — heartbeat + polling | Closed |
| #1584 | GAP-006: Limite de concorrência de buscas por usuário — 3 simultâneas | Closed |
| #1585 | GAP-007: Limpeza de checkpoints órfãos — pg_cron semanal | Closed |
| #1586 | GAP-008: RPC dedicada upsert_supplier_contracts — schema independente de bids | Closed |
| #1587 | GAP-009: Threshold fuzzy dedup configurável — DEDUP_FUZZY_THRESHOLD via env | Closed |
| #1588 | GAP-010: Lista de stopwords PT-BR para dedup — NLTK + termos de licitação | Closed |
| #1589 | GAP-011: Pesos de viabilidade configuráveis por setor — override em sectors_data.yaml | Closed |
| #1590 | GAP-012: Fallback de quota com Supabase offline — fail open com limite conservador | Closed |
| #1591 | GAP-013: Retry com exponential backoff + jitter para OpenAI — 3 tentativas | Closed |
| #1592 | GAP-014: Documentar mecanismo de isenção de auth — FastAPI Depends nativo | Closed |
| #1593 | DEC-BIL-GAP-02: Estratégia se Stripe offline — grace period + notificação founder | Closed |

**🟢 COSMETIC (P2) — 4 issues:**

| Issue | Título | Status |
|-------|--------|--------|
| #1596 | GAP-016: Definir modelo fallback se GPT-4.1-nano for deprecated | Closed |
| #1597 | GAP-017: Documentar ordem dos 65 routers em startup/routes.py | Closed |
| #1598 | GAP-018: Expandir code-spec-matrix com cobertura frontend completa | Closed |
| #1599 | GAP-019: Mapear módulos cross-cutting (utils, config, templates) no code-spec-matrix | Closed |

**✅ Closed — 21 issues (todas):**

| Issue | Título | Status |
|-------|--------|--------|
| #1594 | DEC-SRC-GAP-01: Documentar mecanismo específico de TTL de cache | Closed |
| #1595 | GAP-015: Confirmar e documentar mecanismo de TTL de cache L1/L2 | Closed |

---

### Reversa Code Analysis (F-01 a F-14) — #1772–#1785 (14 issues)

Issues de engenharia reversa e análise de código criadas ~2026-06-14. 14 findings do ecossistema de código — segurança, testes, documentação, complexidade.

**🔴 P0 (2 issues):**

| Issue | Título | Status |
|-------|--------|--------|
| #1772 | F-01: Uvicorn max_requests=10000 causa shutdown do backend em produção | Open |
| #1773 | F-02: Sem HMAC verify no webhook /trial-emails/webhook | Open |

**🟡 P1 (7 issues):**

| Issue | Título | Status |
|-------|--------|--------|
| #1774 | F-03: jobs-cron — baixa cobertura de testes em 19 lifespan loops + 9 cron schedules | Open |
| #1775 | F-04: ingestion-datalake — testes de integração real com 27 UFs | Open |
| #1776 | F-05: Validar algoritmo de dedup de 5 camadas com engenharia | Open |
| #1777 | F-06: Análise de código do frontend (~72 componentes, ~25 páginas) | Open |
| #1778 | F-07: Admin role booleano sem granularidade (risco LGPD) | Open |
| #1781 | F-10: Reduzir complexidade em 6 módulos críticos do backend | Open |
| #1785 | F-14: Completar cobertura de análise das routes públicas (~8300 LOC) | Open |

**🟢 P2 (5 issues):**

| Issue | Título | Status |
|-------|--------|--------|
| #1779 | F-08: Criar ADR-RUNNER-001 — decisão Uvicorn vs Gunicorn pós-SIGSEGV | Open |
| #1780 | F-09: Documentar estratégia de fallback quando todas as fontes falham | Open |
| #1782 | F-11: Documentar mapeamento setor-CNAE | Open |
| #1783 | F-12: Documentar política de rate limiting (Redis token bucket) | Open |
| #1784 | F-13: Documentar fórmulas e estilos do Excel export | Open |

### Infrastructure & Security Hardening — #1786–#1817 (32 issues)

Bloco de infraestrutura, segurança e operações criado ~2026-06-14/15. 32 issues abertas — 7 P0, 13 P1, 12 P2.

**🔴 P0 (7 issues):**

| Issue | Título | Status |
|-------|--------|--------|
| #1786 | Sem monitoramento/alerting de downtime — backend ficou DOWN ~6h sem notificação | Open |
| #1787 | Estratégia de Backup e Disaster Recovery — sem RPO/RTO definido | Open |
| #1788 | Dependency vulnerability scanning — sem CVE detection em dependências | Open |
| #1789 | Secret scanning no CI — sem detecção de credenciais expostas | Open |
| #1790 | Health check robusto — GET /api/health deve refletir estado real e responder <100ms | Open |
| #1791 | Frontend graceful degradation — modo read-only com backend DOWN | Open |
| #1792 | RLS audit completo — verificar se TODAS as tabelas têm Row Level Security | Open |
| #1793 | Stripe webhook idempotency — verificar 12 eventos e prevenir duplicação | Open |

**🟡 P1 (13 issues):**

| Issue | Título | Status |
|-------|--------|--------|
| #1794 | Smoke tests pós-deploy — verificar endpoints críticos automaticamente | Open |
| #1795 | SAST no pipeline — análise estática de segurança no CI | Open |
| #1796 | Load e stress testing — benchmark de endpoints críticos sob carga | Open |
| #1797 | Canary/blue-green deploy — mitigação de risco em produção | Open |
| #1798 | CSP unsafe-inline — migrar para nonce/hash-based Content Security Policy | Open |
| #1799 | Runbook de incidentes — procedimentos documentados de resposta | Open |
| #1800 | Circuit breaker testing — validar resiliência contra falhas de APIs externas | Open |
| #1801 | Redis failure mode — graceful degradation quando Redis offline | Open |
| #1802 | Error budget e SLO — definir objetivos de serviço mensuráveis | Open |
| #1803 | Database migration rollback testado — validar .down.sql migrations | Open |
| #1812 | Environment parity — staging idêntico a produção | Open |
| #1813 | ARQ job Dead Letter Queue — jobs falhos não devem ser descartados silenciosamente | Open |
| #1817 | Database connection pool monitoring — prevenir CRIT-046 recorrência | Open |

**🟢 P2 (12 issues):**

| Issue | Título | Status |
|-------|--------|--------|
| #1804 | LGPD — fluxo de deleção de dados do usuário | Open |
| #1805 | LGPD — Registro de Operações de Tratamento de Dados Pessoais (ROPA) | Open |
| #1806 | OpenAPI schema acessível publicamente — GET /api/openapi.json retorna 404 | Open |
| #1807 | Documentação de onboarding para desenvolvedores | Open |
| #1808 | API versioning strategy — política formal de versionamento | Open |
| #1809 | Feature flag cleanup — remover flags não utilizadas | Open |
| #1810 | Procedimento de rotação de secrets/credenciais | Open |
| #1811 | Admin session revocation — revogar sessões de usuários | Open |
| #1814 | Log level runtime — alterar nível de log sem redeploy | Open |
| #1815 | Accessibility audit — validar WCAG AA em todas as páginas | Open |
| #1816 | Penetration test — auditoria de segurança externa antes do v1.0 | Open |

### Q2 Pendentes (supersedidos)

| Issue | Título | Status |
|-------|--------|--------|
| #1262 | Inbound CONFENGE (não é mais B2GOPS) | Aberta no caminho crítico; ver topo deste arquivo |
| #1235 | SUBINTEL-031 — tier premium "SmartLic Insight" | Premissa SaaS morta — não reabrir; SUNSET |

---

## Archived Documentation

Obsolete stories and docs moved to `docs/archive/` (Feb 20, 2026):
- `completed/gtm-resilience/` — 25 GTM-RESILIENCE stories
- `completed/gtm-fixes/` — GTM-FIX production fixes
- `completed/gtm-core/` — GTM-003 to GTM-010
- `completed/features/` — STORY-165 to STORY-185
- `completed/ux/` — UX-303, UX-336
- `superseded/` — STORY-156-164, STORY-200-229 (replaced by TD series)
- Sprint, session, review, ceremony, and investigation artifacts

---

## Historico

| Data | Evento |
|------|--------|
| 2026-01-24 | Project initialized |
| 2026-01-25 | MVP v0.1 complete |
| 2026-01-28 | Production deployment v0.2 |
| 2026-02-03 | Multi-sector expansion v0.3 |
| 2026-02-14 | GTM launch phase v0.4 |
| 2026-02-17 | GTM production fixes (37 fixes) |
| 2026-02-20 | GTM Resilience complete v0.5 (25 stories) |
| 2026-02-20 | Documentation cleanup (180+ files archived) |
| 2026-02-22 | Reliability Sprint started (13 stories, 4 sprints) |
| 2026-02-25 | GTM Repricing — R$1.999 → R$397 (STORY-277) |
| 2026-02-26 | Boleto + PIX payment methods (STORY-280) |
| 2026-02-27 | Reliability Sprint complete v0.5.2 (13/13 stories) |
| 2026-05-03 | pSEO Health Sprint complete (10/10 issues, milestone fechado) |
| 2026-05-04 | On-Page CTA & Copy Sprint complete (10/10 issues, milestone fechado) |
| 2026-05-05 | Conversão + Instrumentação completo (CONV-INST, SEC-HMAC, SEC-SECDEF) |
| 2026-05-07 | Reposicionamento B2G Phase 0 — 96% (22/23 REPO issues) |
| 2026-05-08 | Founders Plan live — R$997 one-time, 23 issues shipped em 2 dias |
| 2026-05-08 | ROADMAP v5.1 — sync com tracker (397 issues, velocity ~25/dia) |
| 2026-05-13 | Reposicionamento B2G Phase 0 — 100% (#775 INDEX fechado, milestone completo) |
| 2026-05-16 | EPIC-SUBINTEL lancado — Inteligencia de Cadeia de Fornecimento (12 issues) |
| 2026-05-30 | EPICs PREDINT, COMPINT, B2GOPS, NETINT lancados (~35 issues) |
| 2026-05-31 | CONV-001 a CONV-012 lancados — Conversao pSEO (14 issues) |
| 2026-05-31 | ROADMAP v6.0 — sync completo com tracker (577 issues, 50 open, 527 closed) |
| 2026-06-01 | Q2 Multi-Camada: +13 RPCs closed (PREDINT, COMPINT, NETINT, B2GOPS) |
| 2026-06-02 | Q2 Multi-Camada: +6 RPCs closed + 4 feature flags premium ativados |
| 2026-06-02 | CONV Wave 2-3 expandido: Microtransações + Pós-compra (11 novas issues) |
| 2026-06-02 | Verticais Premium: 6 feature flags ativados + Datalake API Self-Service |
| 2026-06-03 | ROADMAP v6.1 — audit sync: 601 issues (565 closed, 36 open), Q2 69.1% |
| 2026-06-04 | ROADMAP v6.2 — audit sync: 655 issues (567 closed, 88 open). Fix #1339/#1340 states, +4 capabilities, +54 Wave 4 issues. Q2 recalculado: 61.2% (85 issues, não 110) |
| 2026-06-06 | ROADMAP v6.4 — audit sync: 655 issues (618 closed, 37 open). 19 state mismatches corrigidos, 6 EPIC TRACKERs fechados. Q2 Multi-Camada ~78%, Wave 4 87.0% (47/54). Velocity ~12/dia. |
| 2026-06-07 | ROADMAP v6.5 — audit sync: 679 issues (619 closed, 60 open). 24 novas issues #1509–#1532 (Q2 Wave Extensions). Fix #1439 state. Q2 Multi-Camada ~68% (89 core, 60 closed). Wave 4 89.3% (50/56). Velocity ~13/dia. |
| 2026-06-07 | ROADMAP v6.6 — audit sync: 679 issues (647 closed, 32 open). 28 state mismatches corrigidos (flagships + Wave 2/3 fechados em massa ~19:44 UTC). Q2 Multi-Camada ~90% (~128 closed). Wave 4 92.9% (52/56). Velocity ~19/dia. |
| 2026-06-08 | ROADMAP v7.0 — audit sync: 712 issues (684 closed, 28 open). 27 state mismatches corrigidos (Wave 4 + CONV + Wave Extensions 100% fechados). Intel Reports 100% (#633 closed). +UX Premium (12 issues) + SDD Gaps (21 issues). Velocity ~20/dia. |
| 2026-06-15 | ROADMAP v8.0 — audit sync: 811 issues (763 closed, 48 open). 31 state mismatches corrigidos (4/5 EPICs Q2 fechados, UX Premium 100%, SDD Gaps 100%). +46 issues abertas (Reversa Code Analysis F-01–F-14 + InfraSec Hardening P0/P1/P2). Velocity ~16/dia (113 closed em 7 dias). |

---

*Ultima atualizacao: 2026-06-15 (v8.0)*
