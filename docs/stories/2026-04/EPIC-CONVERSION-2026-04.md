# EPIC-CONVERSION-2026-04: On-Page Conversion Sprint

**Priority:** P0
**Owner:** @sm + @po
**Status:** Done
**Sprint:** Conversion Sprint Q2 2026

---

## Contexto

O CEO Board (53 CEOs, 8 clusters) identificou em deliberação de Abril/2026 que o SmartLic v0.5.3 possui inteligência significativa no backend que permanece invisível no frontend. O gap trial-to-paid está estimado em ~3% contra benchmark de mercado de 18-25% para SaaS B2B sem cartão.

**Diagnóstico central:** O produto já resolve o problema, mas esconde do usuário as provas de que resolve.

**Impacto cumulativo estimado:** +12-18pp em trial conversion (de ~3% → 15-21%).

---

## Stories deste Epic

| Story | Título | Priority | Effort | Sprint | Impacto | Status |
|-------|--------|----------|--------|--------|---------|--------|
| [STORY-440](STORY-440-score-viabilidade-visivel-cards-resultado.md) | Score de Viabilidade Visível nos Cards | P0 | S | 1 | +3-4pp | Draft |
| [STORY-441](STORY-441-cta-contextual-resumo-truncado-trial.md) | CTA Contextual no Resumo Truncado | P0 | S | 1 | +2-3pp | Draft |
| [STORY-448](STORY-448-barra-progresso-trial-header.md) | Barra de Progresso do Trial no Header | P1 | S | 1 | +0.5pp | Draft |
| [STORY-442](STORY-442-guided-tour-interativo-shepherd-js.md) | Guided Tour Interativo (Shepherd.js) | P1 | M | 2 | +2pp | Draft |
| [STORY-443](STORY-443-trial-value-dashboard.md) | Trial-Value Dashboard | P1 | M | 2 | +1-2pp | Draft |
| [STORY-444](STORY-444-email-sequence-nurturing-trial.md) | Email Sequence de Nurturing (5 emails) | P1 | M | 2 | +1-2pp | Draft |
| [STORY-446](STORY-446-upgrade-gate-pipeline-kanban-trial.md) | Upgrade Gate no Pipeline (Limite Trial) | P1 | S | 2 | +1pp | Draft |
| [STORY-445](STORY-445-notificacao-inapp-novas-oportunidades.md) | Notificação In-App de Novas Oportunidades | P1 | M | 3 | +1pp | Draft |
| [STORY-449](STORY-449-referral-incontext-pos-busca.md) | Referral In-Context Pós-Busca | P2 | S | 3 | +0.5pp | Draft |
| [STORY-447](STORY-447-pdf-executivo-por-edital.md) | PDF Executivo por Edital | P2 | L | 3 | +0.5-1pp | Draft |

---

## Sprints de Execução

### Sprint 1 — Semanas 1-2 (Valor Visível) — ~5 dias
**Meta:** Tornar a inteligência do backend visível no frontend. Impacto esperado: +5-7pp.

- STORY-440: Badge de viabilidade nos cards (S — 1-2 dias)
- STORY-441: CTA contextual no resumo truncado (S — 1 dia)
- STORY-448: Barra de progresso do trial no header (S — 1-2 dias)

### Sprint 2 — Semanas 3-4 (Ativação & Conversão) — ~10 dias
**Meta:** Instrumentar o momento-aha e criar mecanismos de conversão ativa. Impacto esperado: +4-6pp.

- STORY-442: Guided tour com Shepherd.js (M — 3-4 dias)
- STORY-443: Trial-value dashboard (M — 3 dias)
- STORY-444: Email sequence de nurturing Day 1/3/5/10/12 (M — 3-4 dias)
- STORY-446: Upgrade gate no pipeline — limite de 5 cards para trial (S — 2 dias)

### Sprint 3 — Semanas 5-8 (Retenção & Aquisição Viral) — ~10 dias
**Meta:** Criar mecanismos de retenção diária e canais de aquisição viral. Impacto esperado: +3-5pp.

- STORY-445: Notificação in-app de novas oportunidades (M — 4 dias)
- STORY-449: Referral in-context pós-busca bem-sucedida (S — 1-2 dias)
- STORY-447: PDF executivo por edital (L — 5-7 dias)

---

## KPIs de Sucesso

| Métrica | Baseline Atual | Meta Sprint 1 | Meta Sprint 2 | Meta Final (Sprint 3) |
|---------|---------------|---------------|---------------|----------------------|
| Trial-to-paid conversion | ~3% | 8% | 12% | 15-21% |
| Trial users com ≥1 busca bem-sucedida | n/a | n/a | instrumentar | >60% |
| Tempo para primeiro "resultado relevante" | n/a | n/a | instrumentar | <5 min |
| Email open rate (nurturing) | n/a | n/a | >25% | >30% |
| Pipeline utilization (trial) | 100% free | 5-card gate | — | — |

---

## Dependências do Epic

- Mixpanel já integrado (eventos necessários para instrumentação do funil)
- Endpoint `/v1/analytics/trial-value` já existe (STORY-443 reutiliza)
- `viability.py` já calcula score e retorna na resposta (STORY-440 só precisa exibir)
- `Shepherd.js` já está em `package.json` (STORY-442 só precisa implementar)
- Sistema de referral `/indicar` já existe (STORY-449 só precisa trigger contextual)
- `backend/jobs/cron/notifications.py` já existe (STORY-444 estende)

---

## Change Log
- 2026-04-12: Status → Done (implementado em EPIC-CONVERSION-2026-04, testes corrigidos)

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Epic criado com base em deliberação do CEO Board (53 CEOs, 8 clusters) |
