# GV-016: Usage Milestone ROI Variant (Extends STORY-312)

**Priority:** P1
**Effort:** XS (3 SP, 1-2 dias)
**Squad:** @dev
**Status:** Ready
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 3
**Pré-requisito:** STORY-312 Done (5 variants de TrialUpsellCTA).

---

## Contexto

STORY-312 (Done) entrega 5 variants de `TrialUpsellCTA`: post-search, post-download, post-pipeline, dashboard, quota. Cada variant tem copy estático template.

Gap: nenhuma variant usa dados reais de uso para copy personalizado. Ex: "Você descobriu R$ 247.500 em oportunidades em 12 análises. 1 licitação ganha paga 6 meses de Pro" seria muito mais convincente que "Veja mais oportunidades no Pro".

Esta story adiciona **nova variant** `usage_milestone_roi` — não novo componente.

---

## Acceptance Criteria

### AC1: Nova variant em `TrialUpsellCTA`

- [ ] `frontend/components/billing/TrialUpsellCTA.tsx` adiciona:
  - Prop `variant = 'usage_milestone_roi'`
  - Prop `contextData = { valor_analisado, analises_count, pipeline_items, roi_multiplier }`
  - Copy dinâmico: "Você descobriu **R$ {valor_analisado_formatado}** em oportunidades em {analises_count} análises. **1 licitação ganha paga {roi_multiplier} meses de Pro.**"
  - CTA → `/planos?source=usage_milestone_roi`

### AC2: Trigger hook

- [ ] `frontend/hooks/useUsageMilestone.ts` novo:
  - Fetch `/v1/user/usage-summary` (estender endpoint existente)
  - Calcula thresholds:
    - 50+ análises OU
    - 10+ pipeline items OU
    - R$500k+ em valor analisado
  - Retorna `{ shouldShow, contextData }`
- [ ] Respeita frequência combinada STORY-312: 1 CTA por sessão max
- [ ] Dismissible 7d (localStorage por variant)

### AC3: Backend endpoint

- [ ] `backend/routes/user.py` estende `/v1/user/usage-summary`:
  ```json
  {
    "valor_analisado_total_brl": 247500,
    "analises_count": 12,
    "pipeline_items": 4,
    "trial_days_remaining": 8,
    "roi_multiplier": 6  // calculado: valor_analisado / plan_monthly_price
  }
  ```
- [ ] Cache 10min Redis

### AC4: Integration pontos

- [ ] `frontend/app/dashboard/page.tsx`: render `<TrialUpsellCTA variant="usage_milestone_roi" />` condicional
- [ ] Condicional via `useUsageMilestone().shouldShow`

### AC5: A/B teste copy

- [ ] Registrar experiment `gv_016_roi_copy` em `frontend/config/experiments.ts`:
  - `control`: "Você descobriu R$ X em oportunidades"
  - `urgency`: "Não perca: R$ X em oportunidades esperando você agir"
  - `social`: "Empresas como a sua descobrem 3x mais oportunidades no Pro"

### AC6: Tracking

- [ ] Mixpanel: reusa `trial_upsell_shown/clicked/dismissed` com `variant=usage_milestone_roi` + props `valor_analisado` etc

### AC7: Testes

- [ ] Unit `useUsageMilestone` — threshold correto
- [ ] Backend test `/v1/user/usage-summary` retorna campos esperados
- [ ] E2E Playwright: user com 52 análises → dashboard mostra variant correta

---

## Scope

**IN:**
- Variant nova em TrialUpsellCTA existente
- Hook trigger
- Endpoint agregado
- A/B copy experiment
- Tracking reuso

**OUT:**
- Novo componente (reusa 312) — intencional
- Variant pós-analise individual (dashboard suficiente)
- Push notification milestone (overkill)

---

## Dependências

- **STORY-312** (Done) — core component
- **GV-001** (A/B framework)

---

## Riscos

- **Copy agressivo ("você está perdendo dinheiro"):** A/B mandatório, fallback control se backfire
- **Endpoint agregado lento:** cache Redis 10min; métrica p95 <200ms

---

## Arquivos Impactados

### Modificados
- `frontend/components/billing/TrialUpsellCTA.tsx` (adiciona variant)
- `backend/routes/user.py` (estende usage-summary)
- `frontend/app/dashboard/page.tsx` (integra variant)
- `frontend/config/experiments.ts` (registra experiment)

### Novos
- `frontend/hooks/useUsageMilestone.ts`
- `frontend/__tests__/hooks/useUsageMilestone.test.ts`

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — extensão STORY-312 com ROI personalizado data-driven |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 9/10 — **GO**. Status Draft → Ready. |
