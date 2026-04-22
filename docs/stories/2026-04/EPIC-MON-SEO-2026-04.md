# EPIC-MON-SEO-2026-04: Camada 1 — SEO de Entidade (Funil Orgânico)

**Priority:** P2 — Wave 3 (MOAT orgânico; leva 6-12 meses para maturar)
**Status:** Draft
**Owner:** @ux-design-expert + @dev + @devops + squad aiox-seo
**Sprint:** Wave 3 (após Waves 1+2 em produção)
**Meta:** Funil orgânico gratuito de alta intenção; CTAs convertendo para camadas pagas 2-4.

---

## Contexto Estratégico

O SmartLic já tem páginas dinâmicas **básicas**:
- `/fornecedores/[cnpj]` (ISR 24h)
- `/cnpj/[cnpj]` (variante)
- `/orgaos/[slug]`

Falta:
- **Enriquecimento** dessas páginas com dados novos (score de risco MON-SCH-01, aditivos, benchmark MON-SCH-02) e CTAs para camadas pagas
- **Páginas `/categoria/[slug]`** — programáticas sobre "quanto o governo paga por X" (milhares de slugs via CATMAT/CATSER)
- **Sitemaps escaláveis** — hoje `sitemap/4.xml` está vazio em produção (bug `BACKEND_URL` no build Railway)
- **Schema.org JSON-LD completo** para rich results

**Conversão esperada:** páginas de alta intenção → CTA para relatório pago (R$47+) ou monitor (R$147+) ou API (pay-per-call).

---

## Stories do Epic

| Story | Priority | Effort | Squad | Status | Objetivo |
|-------|:--------:|:------:|-------|:------:|----------|
| MON-SEO-01 | P1 | M | @dev + @ux | Draft | Enriquecer `/fornecedores/[cnpj]` (score + aditivos + CTAs) |
| MON-SEO-02 | P1 | L | @dev | Draft | Criar `/categoria/[slug]` programático (5k+ páginas) |
| MON-SEO-03 | P1 | M | @dev | Draft | Enriquecer `/orgaos/[slug]` (perfil compras + CTAs) |
| MON-SEO-04 | P0 | M | @dev + @devops | Draft | Sitemaps dinâmicos escaláveis + fix bug sitemap/4.xml |
| MON-SEO-05 | P2 | S | @dev | Draft | Schema.org JSON-LD completo |

---

## Ordem de Execução

1. **MON-SEO-04** primeiro (bug fix crítico de infra, desbloqueia todo indexamento)
2. **MON-SEO-01 + MON-SEO-03** paralelo (depende de MON-SCH-01 aditivos)
3. **MON-SEO-02** (depende de MON-SCH-02 CATMAT + MON-REP-04 para CTA)
4. **MON-SEO-05** último (cobre todas as páginas criadas antes)

---

## KPIs do Epic

| KPI | Baseline (2026-04) | Meta 90 dias | Meta 180 dias |
|-----|-------------------|--------------|---------------|
| Páginas indexadas Google | ~30% das entidades | 60% | 85% |
| Cliques orgânicos/mês nas páginas de entidade | <5 | 500 | 5.000 |
| CTR orgânico | ~0,8% | 2% | 4% |
| Conversão SEO → purchase (relatório) | 0% | 0,5% | 1,5% |
| Backlinks referenciando páginas de entidade | 0 | 5 | 30 |

---

## Dependências

- **Bloqueado por:**
  - MON-SCH-01 (aditivos) → MON-SEO-01, MON-SEO-03
  - MON-SCH-02 (CATMAT) → MON-SEO-02
  - MON-REP-03/04 (relatórios) → CTAs nas páginas
  - MON-SUB-03/04 (monitores) → CTAs nas páginas
- **Complementa:** EPIC-SEO-ORGANIC-2026-04 (stories já existentes para Observatório)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-22 | @sm (River) | Epic criado — Camada 1 da estratégia de monetização; MOAT orgânico de longo prazo |
