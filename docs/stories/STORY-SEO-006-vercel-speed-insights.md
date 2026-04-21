# Story SEO-006: Vercel Speed Insights (ou web-vitals + GA4) para CWV Real

**Epic:** EPIC-SEO-2026-04
**Priority:** 🟠 P1
**Story Points:** 2 SP
**Owner:** @dev
**Status:** Ready
**Audit Ref:** Audit 5.1 + 5.4

---

## Problem

SmartLic não coleta Core Web Vitals reais (LCP / INP / CLS com percentis p75). O audit não conseguiu medir porque:

- Google Analytics 4 ✓ (instalado, mas não reporta Web Vitals por default)
- Microsoft Clarity ✓ (heatmaps + session recordings — não é CWV)
- Vercel Speed Insights ✗ (não instalado)
- web-vitals npm package ✗ (não instrumentado)
- Sentry Performance: não confirmado (`sentry.client.config.ts` precisa review)

**Impacto:**
- Performance category (peso 10% no score) **não mensurável**
- Lighthouse CI só roda em build, não RUM (Real User Monitoring)
- Cada deploy é um chute — não sabemos se LCP p75 regrediu
- STORY-SEO-005 (GSC dashboard) terá buraco de dados sem CWV

---

## Acceptance Criteria

- [ ] **AC1** — Decidir entre duas opções (documentar trade-off):
  - **Opção A (recomendada se hospedado em Vercel)**: Vercel Speed Insights — 1 linha de código, UI plug-and-play
  - **Opção B (agnóstica)**: `web-vitals` package → custom events para GA4 `event: 'web_vitals'`
  - Railway deploy ≠ Vercel host → verificar se Speed Insights funciona fora do Vercel; caso contrário usar Opção B

- [ ] **AC2** — Se Opção A:
  ```bash
  npm install @vercel/speed-insights
  ```
  ```tsx
  // frontend/app/layout.tsx
  import { SpeedInsights } from '@vercel/speed-insights/next';
  // ...
  <SpeedInsights />
  ```

- [ ] **AC3** — Se Opção B:
  ```bash
  npm install web-vitals
  ```
  ```tsx
  // frontend/app/components/WebVitalsReporter.tsx
  'use client';
  import { onCLS, onINP, onLCP, onTTFB, onFCP } from 'web-vitals';
  import { useEffect } from 'react';

  export function WebVitalsReporter() {
    useEffect(() => {
      const report = (metric) => {
        if (window.gtag) {
          window.gtag('event', 'web_vitals', {
            event_category: 'Web Vitals',
            event_label: metric.name,
            value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
            non_interaction: true,
            metric_id: metric.id,
            metric_value: metric.value,
            metric_delta: metric.delta,
          });
        }
      };
      onCLS(report); onINP(report); onLCP(report); onTTFB(report); onFCP(report);
    }, []);
    return null;
  }
  ```

- [ ] **AC4** — Após 7 dias de coleta, dashboard mostra (agregado top 10 URLs):
  - LCP p75
  - INP p75
  - CLS p75
  - TTFB p75 (bônus)
  - FCP p75 (bônus)

- [ ] **AC5** — CI check: se LCP p75 > 3s em URL crítica (home, `/planos`, `/buscar`) → falhar build. Lighthouse CI complementa RUM.

- [ ] **AC6** — Dashboard visível em `/admin/seo` (integração com STORY-SEO-005) OU painel Vercel standalone (Opção A)

- [ ] **AC7** — Documentação em `docs/observability/web-vitals.md` explicando:
  - Onde ver os dados
  - Como interpretar (thresholds Google: LCP ≤2.5s, INP ≤200ms, CLS ≤0.1)
  - Como reagir a regressão

---

## Dev Notes

> **Decisão pré-implementação (2026-04-21):** SmartLic está hospedado no **Railway**, não no Vercel. Vercel Speed Insights exige hosting Vercel — **Opção A descartada**. Implementar **Opção B**: `web-vitals` npm package → custom events GA4 (`event: 'web_vitals'`). Dashboard em `/admin/seo` via integração STORY-SEO-005.

---

## Scope IN

- Instalar e configurar Speed Insights OU web-vitals+GA4
- Dashboard (standalone ou integrado)
- Doc de observability
- Lighthouse CI threshold update

## Scope OUT

- Otimização específica de CWV (será consequência, não desta story)
- Bundle size reduction (STORY-5.14 existente, memória `project_bundle_size_budget`)
- Sentry Performance setup (pode ser complemento futuro)

---

## Implementation Decision Matrix

| Critério | Vercel Speed Insights | web-vitals + GA4 |
|----------|----------------------|------------------|
| Setup | 1 linha | ~30 linhas |
| Custo | Grátis no plano Vercel Pro (já hospedado no Railway — verificar) | Grátis |
| Dashboard | UI pronta | Usar GA4 Explorations (manual) |
| Retenção | 30 dias (Vercel) | 14 meses (GA4) |
| Agnóstico de host | Não | Sim |

**Recomendação prévia**: Como SmartLic está no Railway (não Vercel), **Opção B** é mais robusta. Dashboard em `/admin/seo` via STORY-SEO-005.

---

## Files

- `frontend/package.json` (add `web-vitals`)
- `frontend/app/components/WebVitalsReporter.tsx` (new)
- `frontend/app/layout.tsx` (import WebVitalsReporter)
- `docs/observability/web-vitals.md` (new)
- `.github/workflows/lighthouse-ci.yml` (modify — se já existir, bump thresholds)

---

## Success Metrics

- Após 7 dias: ≥1.000 samples p75 em GA4 ou Speed Insights
- LCP p75 das top 10 URLs ≤2.5s em 80% das URLs
- CLS p75 ≤0.1 em 100% das URLs
- Regressão em CWV detectada e reportada antes do feedback em GSC (2-3 semanas)

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-04-21 | @sm (River) | Story criada a partir do audit SEO 2026-04-21 |
| 2026-04-21 | @po (Pax) | Validação 7/10 — GO condicional. Dev DEVE fechar Opção A/B (Recmd: B) antes de codificar. Sem Risks. Status Draft → Ready |
| 2026-04-21 | @po (Pax) | Decisão fechada: Railway ≠ Vercel → Opção B (web-vitals + GA4) registrada em Dev Notes |
