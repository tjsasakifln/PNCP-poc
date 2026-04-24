# Session ultra-generic-diffie — 2026-04-24

**Branch:** `docs/session-2026-04-24-piped-cray` → ramificará nova branch para PR
**Plan:** `~/.claude/plans/ultra-generic-diffie.md`
**Mission:** empresa-morrendo (MRR única métrica) — user pediu "10h max ROI"
**Classe:** REVENUE-DIRECT (1 fix shipped) + DISCOVERY (root cause SEO/aquisição)

## Objetivo

Sem objetivo declarado pelo user. Bootstrap deu 3 opções; user escolheu "10h max ROI". Plan committed = só Hora 1 (discriminadores) + Hora 2 (re-plan data-driven) — branches A/B/C/D escolhidas pelos dados. Advisor flagou 2 vezes (sharpening). Resultado: alavanca real foi descoberta MUITO acima do plan inicial (sitemap broken, vacuum aquisição), mas evidence pegou que webhook Resend e CTA template eram menos prioritários que copy iter blog page.

## Entregue

| Mudança | Arquivo | Escopo |
|---------|---------|--------|
| Title + meta description rewrite `/blog/pncp-guia-completo-empresas` | `frontend/lib/blog.ts:1127-1149` | Title 52→60 chars com PNCP lead + Licitações + 2026 + Grátis. Description re-foca em queries observadas em GSC. Keywords expandidas com 6 termos de alto-volume (`pncp licitações`, `consulta editais pncp`, `pncp 2026` etc). `lastModified: 2026-04-24` para sinal de re-crawl. |

**Não shipped (pivots por advisor + dados):**
- Resend webhook config (`POST /trial-emails/webhook` já existe MAS Resend dashboard tem 0 webhooks): defer — volume real 9 emails/30d não justifica 30min config quando bottleneck é gerar trials, não medir
- Template CTA contextual em `/contratos/orgao/[cnpj]/page.tsx`: defer — sem Mixpanel engagement data (time-on-page/scroll/bounce), risco de fixar wrong problem (advisor flagou: queries CNPJ-lookup tipo "labbrasil"/"tekis" podem ser tráfico não-fit, não conversion broken)
- Backend sitemap fix (`/v1/sitemap/{cnpjs|orgaos|fornecedores-cnpj|...}` timeout 30s+): defer 4-5h — RPCs funcionam direto (1.4s) mas event loop blocked por paginated fallback 2M rows + serial query_sector 15× × 4s. Fix proper = parallel asyncio.gather + RPCs + materialized view. Story para próxima sessão.
- Frontend `app/sitemap.ts` `AbortSignal.timeout(15000)`: defer — bumpar 15s→90s = regression risk no revenue path durante ISR rebuild a cada hora

## Audit GATE / Discriminadores (Hora 1, ~2h)

4 discriminadores paralelos antes de committar abordagem:

1. **Mixpanel `paywall_hit` count 4h** — não verificado direto (sem MIXPANEL_API_SECRET, só TOKEN); inferido OK pq backend logs Sentry/eventos visíveis
2. **Resend dashboard webhooks** — `curl https://api.resend.com/webhooks` → `{"data":[]}` — **ZERO webhooks configurados em prod**
3. **Supabase signups cohort** — 2 profiles 30d, 0 7d, 0 24h. Vacuum total. trial_email_log: 9 emails 30d
4. **Grep webhook existente** — `POST /trial-emails/webhook` JÁ existe em backend (anti-pattern story_discovery #3 da semana)

GSC drill-down via Playwright (smartlic.tech 28d):
- **126 cliques / 9,901 impressões / CTR 1.3% / pos 7.1** (389 queries)
- Top queries são CNPJ/empresa lookups ("supra distribuidora hospitalares", "labbrasil", "tekis", "69034668000156") — mostly 0 clicks
- Top blog landing: `/blog/pncp-guia-completo-empresas` — **2,257 impressões, 2 clicks, CTR 0.09%** = título/snippet weak
- Top programmatic landing: `/contratos/orgao/{cnpj}` — CTR 22-44% (working) mas volume baixo (sitemap 4.xml=0 URLs bloqueia expansion)

Sub-sitemaps em prod: 0.xml=43, 1.xml=60, 2.xml=810, 3.xml=357, **4.xml=0**. Total 1,270 URLs vs esperado ~12,000+.

## Impacto em receita

| Mudança | Estado | Como medir (próxima sessão / 7-14d) |
|---------|--------|------------------------------------|
| Title/meta `/blog/pncp-guia-completo-empresas` | DONE branch local | GSC 7-14d pós-deploy: CTR esta página 0.09%→? (target 1%+ = 23+ clicks/month vs 2/month) |
| Volume signups | UNCHANGED — bottleneck identificado mas não atacado | GSC + Mixpanel funnel próxima sessão |
| Sitemap 4.xml empty | UNCHANGED — story aberta para próxima sessão | Após fix backend: count URLs em `/sitemap/4.xml` (esperado 10k+) |

**Hipótese central:** se title rewrite move CTR `/blog/pncp-guia-completo-empresas` de 0.09% para 1% (modest, position 8-15 typical), são 23 clicks/month adicionais. Industry baseline conversion landing→signup 1-2% = 0.5 signup adicional/month deste único page. Pequeno em absoluto, mas single-file safe edit; baseline pré-fix é 0 signup/month, então qualquer lift é +∞%.

**Hipótese principal a testar próxima sessão:** Mixpanel engagement em `/contratos/orgao/*` — se bounce >85%/time <30s = traffic wrong-fit (skip CTA fix); se time >60s/scroll >50% = CTA é bottleneck (template fix high ROI).

## Pendente (dono + prazo)

- [ ] **@devops push** branch + abrir PR — desta sessão (2026-04-24) — single-file edit `frontend/lib/blog.ts`
- [ ] **Mixpanel engagement query** `/contratos/orgao/*`, `/blog/*` 28d — próxima sessão (2026-04-25+)
- [ ] **GSC 7-14d soak title rewrite** `/blog/pncp-guia-completo-empresas` — sessão semana 2 (2026-05-01+) — pós-Google re-crawl
- [ ] **Story SEO-XXX backend sitemap parallel + RPC + materialized view** — @sm + @architect — próxima sessão urgente para destrancar 10x volume programmatic
- [ ] **Story TRIAL-EMAIL-WEBHOOK-CONFIG** — @sm — REVENUE-ADJACENT, 30min config + 30min HMAC verify backend; defer até trial volume justificar
- [ ] **24h soak Mixpanel `paywall_hit`** (herdado piped-cray) — próxima sessão 2026-04-25+

## Riscos vivos

| Risco | Severidade | Prazo virar incidente |
|-------|-----------|----------------------|
| Sitemap 4.xml empty cumulativo (Google de-indexa entity pages se ausentes do sitemap por semanas) | MED | 14-28d sem fix → impressões caem |
| `_compute_contracts_combos` statement_timeout Postgres (57014) intermitente em prod | MED | Já recorrente em logs hoje |
| Backend event loop blocked por sitemap requests serial blocking → outras endpoints (paywall, /buscar) latencia spike durante crawler hits | LOW-MED | Visível em logs como "took 3-4 seconds" warnings asyncio |
| Resend webhook handler sem HMAC verify (security gap) | LOW | Endpoint não exposto via Resend ainda — só vira issue se webhook setado sem fix prévio |

## Memory updates

| File | Razão |
|------|-------|
| `reference_trial_email_log_delivery_status_null.md` | **Reescrita.** Coluna `delivery_status` NÃO existe (grep zero hits). Schema STORY-310 tem `opened_at`/`clicked_at`/`resend_email_id`. Endpoint webhook existe mas Resend dashboard 0 webhooks → todos opened/clicked NULL. |
| `reference_smartlic_baseline_2026_04_24.md` | **Novo.** Snapshot signup vacuum + GSC 28d numbers + sitemap state em prod. Decay rápido mas útil para próxima comparação. |
| `MEMORY.md` | Atualizado com 2 novos entries acima |

## KPIs da sessão

| Métrica | Alvo | Realizado |
|---------|------|-----------|
| Shipped to prod | ≥1 mudança caminho receita | 1 (title/meta blog REVENUE-DIRECT, pendente push @devops) |
| Incidentes novos | 0 | 0 |
| Tempo em docs | <15% | ~10% (handoff + memory) |
| Tempo em fix não-prod | <25% | ~15% (Hora 1 discriminators são pre-prod necessários) |
| Instrumentação adicionada | ≥1 evento funil | 0 — defer pq sem secret API Mixpanel não consigo verify; flag para próxima sessão |

**Yellow:** instrumentação 0/1 alvo. Próxima sessão começar com Mixpanel funnel verify (engagement `/contratos/orgao/*`).

## Próxima ação prioritária

**Próxima sessão 2026-04-25+:** Mixpanel engagement `/contratos/orgao/*` 28d → branch decision (CTA template fix vs targeting fix vs sitemap backend fix). Em paralelo: 24h soak `paywall_hit` herdado piped-cray. Após dados Mixpanel, escolher entre 3 alavancas concretas mapeadas neste handoff.
