# GV-020: ROI Calculator Embed + Lead Capture Flow

**Priority:** P2
**Effort:** S (5 SP, 2-3 dias)
**Squad:** @dev + @ux-design-expert
**Status:** Ready (blocked by STORY-432)
**Epic:** [EPIC-GROWTH-VIRAL-2026-Q3](EPIC-GROWTH-VIRAL-2026-Q3.md)
**Sprint:** 4
**Pré-requisito:** STORY-432 (EPIC-SEO-ORGANIC) InProgress — calculadora embeddable básica.

---

## Contexto

STORY-432 entrega calculadora embeddable como link bait. Esta story **estende** com lead capture flow completo (email gate para ver resultado detalhado + drip nurture).

ROI Calculator classic marketing tool B2B — user estima economia antes de converter, supercomputer de intent signal.

---

## Acceptance Criteria

### AC1: Página calculator standalone

- [ ] `frontend/app/roi-calculator/page.tsx`:
  - Form inputs:
    - Ticket médio licitação (R$)
    - Taxa conversão atual estimada (%)
    - Horas/semana analisando licitações manualmente
    - Salário médio analista (R$/h)
  - Submit → calcula output:
    - Economia de horas analista com SmartLic
    - Conversão adicional estimada (+X pp)
    - ROI anual (R$ ganhos extras - custo plan)
    - Payback period em meses
  - Output visual: barras comparando "Com SmartLic" vs "Atual"

### AC2: Página embed `/roi-calculator/embed`

- [ ] `frontend/app/roi-calculator/embed/page.tsx`:
  - Mesmo calculator mas layout compacto iframe-friendly
  - Query params customização: `?color=hex&logo=url`
  - CSP `frame-ancestors *` (igual GV-004 pattern)

### AC3: Lead capture flow

- [ ] Após cálculo, CTA:
  - "Envie o cálculo completo por email (com PDF anexo)" → form email capture
  - Ou "Tenha análise real grátis 14 dias" → direct signup link
- [ ] Endpoint `POST /v1/roi-calculator/save`:
  - Persiste inputs + outputs em tabela `roi_calculations`
  - Envia email com PDF (copy branded + CTA signup)

### AC4: Email nurture

- [ ] D+0: "Seu ROI estimado — veja como atingi-lo"
- [ ] D+3: "Como empresa X atingiu ROI parecido com SmartLic"
- [ ] D+7: "Teste grátis 14 dias — comprove seu ROI na prática"

### AC5: Snippet generator

- [ ] Settings (opcional futuro — por ora só landing)
- [ ] Embed code copy: `<iframe src="https://smartlic.tech/roi-calculator/embed?color=0066cc" width="100%" height="500"></iframe>`

### AC6: Tracking

- [ ] Mixpanel:
  - `roi_calculator_input_submitted` com inputs
  - `roi_calculator_email_captured`
  - `roi_calculator_pdf_downloaded`

### AC7: Testes

- [ ] Unit ROI formula (edge: inputs zero, extremos)
- [ ] E2E: inputs → calculate → email capture → PDF received (mock)

---

## Scope

**IN:**
- Calculator standalone + embed
- Lead capture + drip
- PDF report
- Tracking

**OUT:**
- ROI por setor customizado (v2, LLM)
- Live chat support durante cálculo (v2)

---

## Dependências

- **STORY-432** (EPIC-SEO-ORGANIC) — calculator base deve existir
- `frontend/middleware.ts` CSP rota-específica (pattern GV-004)

---

## Riscos

- **Cálculos irrealísticos user inflate ROI:** outputs com caveat "estimativa; resultado real varia"
- **CSP clickjacking:** mesma mitigação GV-004
- **Embed sem atribuição:** UTMs fixos em CTA

---

## Arquivos Impactados

### Novos
- `frontend/app/roi-calculator/page.tsx`
- `frontend/app/roi-calculator/embed/page.tsx`
- `backend/routes/roi_calculator.py`
- `backend/templates/emails/roi_d0.html`, `roi_d3.html`, `roi_d7.html`
- `supabase/migrations/YYYYMMDDHHMMSS_roi_calculations.sql` (+ down)

### Modificados
- `frontend/middleware.ts` (CSP /roi-calculator/embed)
- `frontend/app/sitemap.ts` (incluir /roi-calculator)

---

## Change Log

| Data | Autor | Mudança |
|------|-------|---------|
| 2026-04-24 | @sm | Story criada — extensão STORY-432 com lead capture completo |
| 2026-04-24 | @po (Pax) | Validated — 10-point checklist 8/10 — **GO blocked**. Pré-requisito STORY-432 deve estar Done antes de iniciar. Status Draft → Ready (blocked). |
