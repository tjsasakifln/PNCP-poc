# Disposition de capabilities — #1262

**Status:** vigente a partir de 2026-08-13  
**Autoridade:** [ADR-STRAT-001](../adr/ADR-STRAT-001-smartlic-confenge-inbound.md)  
**Regra:** nenhuma capability estrategicamente ambígua. Toda linha tem exatamente uma categoria.

Categorias: `KEEP + PRIORITIZE` · `KEEP + ADAPT` · `SUNSET` · `REPLACE` · `DEFER`

## KEEP + PRIORITIZE

Ativos que encurtam o tempo até demanda qualificada para a CONFENGE, ou que já existem e não podem ser perdidos.

| Capability | Evidência | Por quê |
|------------|-----------|---------|
| Páginas pSEO de entidade (CNPJ, fornecedor, órgão, município, contrato, licitação) | `frontend/app/{cnpj,fornecedores,orgaos,municipios,contratos,licitacoes}` | Patrimônio indexável; intenção comercial |
| Observatório e recortes `raio-x-*` | `frontend/app/observatorio` | Descoberta + autoridade |
| Sitemaps, canonical, robots, ADR-SEO-001 | `.github/workflows/audit-seo-notfound.yml`, `docs/adr/ADR-SEO-001-*.md` | Preservar indexação (#2113) |
| Ferramentas públicas com dado (calculadora, comparador, glossário, perguntas, blog) | rotas públicas Next.js | Utilidade antes do CTA |
| Classificação setorial e viabilidade como inteligência pública | `backend/filter/`, `backend/viability.py`, `backend/sectors_data.yaml` | Diferencial verificável, sem paywall |
| Captura de lead / CTA consultivo | `LeadCapture`, `/consultoria-b2g` | Ponte para CONFENGE (#2114, #2117) |
| Health público e observabilidade da superfície | `/health/*`, Sentry | Confiabilidade do inbound |

## KEEP + ADAPT

Permanece porque o cutover precisa dela, mas a semântica muda (público/consultivo, não SaaS).

| Capability | Adaptação | Issue |
|------------|-----------|-------|
| FastAPI | Vira adapter de apresentação sobre `public_read_v1`; sem autoridade de dados | #2108, #2115 |
| Next.js autenticado (shell, admin) | Admin interno permanece; conteúdo público não exige login | #2111, #2114 |
| Redis | Cache/rate-limit/locks na transição; reavaliar no runtime mínimo | #2115, #2116 |
| Auth / RLS / MFA | Apenas admin, operações internas e proteção de PII de leads | #2111 |
| Resend | E-mails de lead/handoff; sequências de trial saem | #2111 |
| Mixpanel / Sentry | Eventos de inbound (landing → CTA → lead), não funnel de signup | #2117 |
| Busca / pipeline de classificação | Discovery público sem quota/paywall | #2112 |
| Export Excel/PDF | Lead magnet ou ferramenta pública; sem checkout | #2109 |
| Feature flags | Kill switches de sunset/freeze, não rollout de planos | #2111 |

## SUNSET

Premissa comercial morta. Remoção em ondas (#2111). Não expandir.

| Capability | Onda | Notas |
|------------|------|-------|
| Stripe SDK, Checkout, Customer Portal, webhooks de billing | 1 freeze → 3 desativar → 4 remover | Zero novas assinaturas imediatamente |
| Plans, prices, products, founding offer, partner billing | 1–4 | Sem plano substituto |
| Trial, trial emails, trial paywall, quota, entitlement | 1–4 | Sem trial indireto |
| `/pricing`, `/planos`, `/signup` comercial, `/fundadores`, upgrade CTAs | 2 desvio (redirect #2113/#2114) | Não apagar URL indexada sem 301 |
| Intel Reports / microtransações / checkout one-time | 2–4 | Não recriar billing avulso |
| Workers/jobs de billing, dunning, founders welcome | 3 | Após zero uso |
| Gates CI específicos de billing | 4 | Após prova de zero chamada |
| Workspace privado multi-tenant como produto | 2–4 | Sem evidência comercial; código histórico permanece até decisão de delete |
| Viral loops cujo KPI é signup/K-factor | 2 | `docs/strategy/kill-criteria.md` (MRR) está supersedido |

## REPLACE

Autoridade ou runtime que será substituído, não evoluído no lugar.

| Capability atual | Substituta | Proibido |
|------------------|------------|----------|
| DataLake SmartLic (`pncp_raw_bids`, `pncp_supplier_contracts` como autoridade) | extra-cli `public_read_v1` | Migrar o DataLake legado para a Netcup; segundo DataLake |
| Crawling / ingestion SmartLic (`backend/ingestion/`) | extra-cli acquisition | Novo crawler no SmartLic |
| Supabase como fonte da verdade | PostgreSQL extra-cli + role SELECT-only | Manter Supabase como 2ª autoridade |
| Fallback live PNCP/PCP/ComprasGov como caminho primário | Freshness/completeness do extra-cli | Recriar ETL no SmartLic |
| Railway como casa permanente | Runtime mínimo Netcup (#2115) | Kubernetes, microservices |

## DEFER

Trabalho válido só depois do go-live público, ou explicitamente fora do caminho crítico.

| Capability | Motivo | Issue |
|------------|--------|-------|
| Warmbly / outreach / action plane | Não bloqueia go-live; consome handoff depois | — |
| Assessment privado multi-cliente | Sem evidência de inbound funcionando | #2107 |
| Expansão pSEO de clusters novos | Só após gates P0 e dado único + intenção | #2118 |
| Product-as-content adicional | Próxima onda, não P0 | #2109 |
| Intel preditiva / network / competitive expansion | Não gera demanda imediata | epics históricos fechados |
| CRM próprio | CONFENGE é o service plane | — |
| Kafka, event bus, CDC | Sem restrição concreta | extra-cli#354 fora de escopo |

## Ambiguidade residual (zero)

Qualquer capability nova deve ser classificada neste arquivo no mesmo PR que a introduz. P0/P1 que proponham billing, SaaS, DataLake ou crawler próprio são inválidas por este documento.
