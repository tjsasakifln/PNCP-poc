# Destino de runtime — FastAPI, Redis, ARQ, Supabase, Railway, Warmbly

**Autoridade:** [ADR-STRAT-001](../adr/ADR-STRAT-001-smartlic-confenge-inbound.md)  
**Regra:** ausência de justificativa implica remoção. Não migrar o DataLake legado do SmartLic para a Netcup.

## Mapa

| Componente | Papel legado | Destino | Categoria | Justificativa para existir agora | Quando some / muda |
|------------|--------------|---------|-----------|----------------------------------|--------------------|
| **FastAPI** | API do SaaS + SEO backends + admin | Adapter de apresentação | KEEP + ADAPT | Superfície pública e ISR dependem dos routers; reescrita total viola "não reescrever a arquitetura" | Encolhe com #2108/#2112; runtime mínimo em #2115 |
| **Next.js** | App autenticado + 10k+ ISR | Superfície pública + admin interno | KEEP + PRIORITIZE | Patrimônio SEO | Permanece; login some do conteúdo público (#2111/#2114) |
| **Redis** | Cache L2, SSE, ARQ broker, rate-limit, locks | Cache/rate-limit transitório | KEEP + ADAPT | Isola picos de leitura do truth plane | Reavaliar em #2115/#2116; não é autoridade |
| **ARQ workers** | Ingestão, Excel, LLM, billing cron, trial emails | Jobs de apresentação apenas | SUNSET AFTER DEPENDENCY (ingestão/billing) | Ainda geram exports/resumos | Ingestão → extra-cli (#2108); billing → #2111 onda 3 |
| **Supabase PostgreSQL** | DataLake + Auth + cache + billing rows | Store transicional; **não autoridade** | REPLACE (autoridade) / KEEP + ADAPT (auth/admin até haver substituto) | Cutover sem downtime | Autoridade → extra-cli; Auth admin permanece até #2115 decidir |
| **Supabase Auth** | Login de trial/SaaS | Admin + operadores | KEEP + ADAPT | Admin e PII de leads precisam de porta | Signup público comercial sai (#2111) |
| **Stripe** | Billing | Removido em ondas | SUNSET | Código ainda existe; tese morta | #2111 |
| **Railway** | web + worker + frontend | Substituído | REPLACE | Produção atual | #2115 Netcup; rollback documentado |
| **Upstash/Railway Redis** | Broker | Avaliar no runtime mínimo | KEEP + ADAPT | Ver Redis | #2115 |
| **Sentry / Prometheus / OTel / Mixpanel** | Observabilidade SaaS | Observabilidade inbound | KEEP + ADAPT | Precisamos de freshness, 5xx, CTA, leads | Eventos de checkout saem |
| **Resend** | Trial/billing/founders email | Lead / handoff | KEEP + ADAPT | Canal transacional útil | Sequências trial/dunning saem |
| **OpenAI** | Classificação + resumos | Inteligência de apresentação | KEEP + ADAPT | Não é truth plane; enriquece superfície | Sem paywall |
| **Warmbly** | — | Action plane futuro | DEFER | Não existe no caminho crítico | Consome handoff depois do go-live |
| **extra-cli PostgreSQL (Netcup)** | — | Truth/data plane | KEEP + PRIORITIZE (fora deste repo) | Única autoridade de fatos públicos | `public_read_v1` extra-cli#354 |

## Proibições de destino

- Não criar segundo DataLake no SmartLic.
- Não copiar `pncp_raw_bids` / `pncp_supplier_contracts` para a Netcup como "migração".
- Não manter Supabase e extra-cli como duas autoridades do mesmo fato.
- Não introduzir Kafka, Kubernetes ou microservices para justificar o cutover.
- Não acoplar o processo do SmartLic ao Warmbly.

## Runtime mínimo alvo (#2115)

Superfície pública Next.js + adapter FastAPI enxuto + leitura `public_read_v1` + cache/rate-limit + observabilidade. Sem worker de crawler. Sem Stripe. Sem trial. Rollback: Railway permanece até o canário na Netcup provar disponibilidade e SEO.
