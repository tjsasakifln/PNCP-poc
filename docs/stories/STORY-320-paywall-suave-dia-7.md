# STORY-320: Paywall Suave Dia 7 — Preview de Features Pro Bloqueadas

**Epic:** EPIC-TURBOCASH-2026-03
**Sprint:** Sprint 1 (Quick Wins)
**Priority:** P0 — HIGH
**Story Points:** 8 SP
**Estimate:** 4-6 dias
**Owner:** @dev + @ux-design-expert
**Origem:** TurboCash Playbook — Acao 5 (Otimizar Trial Funnel)

---

## Problem

O trial atual oferece acesso total a todas as features durante o periodo inteiro. Isso reduz a urgencia de conversao pois o usuario nao percebe o valor diferenciado do plano pago. Nao ha "preview" que crie desejo pelo upgrade. STORY-312 (CTAs contextuais) mostra CTAs de upsell, mas nao bloqueia ou limita features.

## Solution

Implementar paywall suave a partir do dia 7 do trial (metade do novo trial de 14 dias). A partir do dia 7:
- Resultados de busca alem do top 10 ficam "blurred" (desfocados)
- Export Excel limitado a 10 resultados (preview dos primeiros)
- Resumo IA mostra preview truncado (primeiros 2 paragrafos)
- Pipeline limitado a 5 items
- Banner persistente "Desbloqueie acesso completo"

**Evidencia:** Paywall no meio do trial cria "loss aversion" — usuario ja investiu 7 dias e nao quer perder o progresso.

---

## Acceptance Criteria

### Backend — Feature Gating

- [ ] **AC1:** Criar funcao `get_trial_phase(user)` em `quota.py`:
  - `full_access` (dias 1-7): todas as features sem restricao
  - `limited_access` (dias 8-14): features com paywall suave
  - Retorna: `{ phase: "full_access" | "limited_access", day: int, days_remaining: int }`
- [ ] **AC2:** Endpoint `GET /v1/trial-status` inclui campo `trial_phase` no response
- [ ] **AC3:** `POST /buscar` retorna campo `paywall_applied: bool` quando resultados sao truncados
  - Se `limited_access`: retorna max 10 resultados completos + count total
  - Header `X-Total-Results` com total real (para mostrar "Veja todos os {N} resultados")
- [ ] **AC4:** `GET /v1/export/excel` em `limited_access`: gera Excel com 10 resultados + sheet extra "Desbloqueie {N-10} resultados adicionais com SmartLic Pro"
- [ ] **AC5:** Feature flag `TRIAL_PAYWALL_ENABLED` (default: true) para desativar rapidamente

### Frontend — UI de Paywall

- [ ] **AC6:** Criar `frontend/components/billing/TrialPaywall.tsx`:
  - Componente overlay semi-transparente com blur
  - Copy: "Desbloqueie {N} resultados adicionais"
  - CTA principal: "Assinar SmartLic Pro" → /planos
  - CTA secundario: "Continuar com preview" (dismiss por 1h)
  - Tracking: `trial_paywall_shown`, `trial_paywall_clicked`, `trial_paywall_dismissed`
- [ ] **AC7:** Em `SearchResults.tsx`:
  - Dias 1-7: renderiza todos os resultados normalmente
  - Dias 8-14: renderiza top 10 normalmente + demais com blur overlay + TrialPaywall
  - Mostrar badge "Preview" nos resultados blurred
- [ ] **AC8:** Em `SearchResults.tsx` — download Excel:
  - Dias 8-14: botao muda para "Baixar Preview (10 resultados)" com icone de cadeado
  - Tooltip: "Assine o SmartLic Pro para exportar todos os {N} resultados"
- [ ] **AC9:** Resumo IA (LLM summary):
  - Dias 8-14: mostrar primeiros 2 paragrafos + "..." + paywall overlay
  - CTA: "Ver analise completa com SmartLic Pro"
- [ ] **AC10:** Pipeline page:
  - Dias 8-14: permitir max 5 items no pipeline
  - Ao tentar adicionar o 6o: modal "Limite do trial — assine para pipeline ilimitado"
- [ ] **AC11:** Usar `useTrialPhase()` hook que consulta `/v1/trial-status` e cacheia em sessionStorage

### Frontend — Banner Persistente

- [ ] **AC12:** Banner no topo da area logada (dias 8-14):
  - Copy: "Voce esta no modo preview. Desbloqueie acesso completo ao SmartLic."
  - CTA: "Ver planos" → /planos
  - Nao dismissavel (diferente dos CTAs contextuais da STORY-312)
  - Cor: gradiente azul→roxo (diferenciar dos banners amarelos de warning)

### Testes

- [ ] **AC13:** Testes backend: `get_trial_phase()` retorna fase correta por dia
- [ ] **AC14:** Testes backend: busca trunca resultados em `limited_access`
- [ ] **AC15:** Testes frontend: TrialPaywall renderiza blur em dia 8+
- [ ] **AC16:** Testes frontend: nao renderiza paywall em dias 1-7
- [ ] **AC17:** Testes frontend: nao renderiza paywall para usuarios pagos
- [ ] **AC18:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Trial status endpoint | `backend/routes/user.py` → GET /trial-status | Existe |
| Quota system | `backend/quota.py` | Existe |
| TrialUpsellCTA | `frontend/components/billing/TrialUpsellCTA.tsx` | Existe (STORY-312) |
| Search results | `frontend/app/buscar/components/SearchResults.tsx` | Existe |
| Excel export | `backend/excel.py` | Existe |
| LLM summary | `backend/llm.py` | Existe |
| Pipeline | `frontend/app/pipeline/page.tsx` | Existe |

## Files Esperados (Output)

**Novos:**
- `frontend/components/billing/TrialPaywall.tsx`
- `frontend/hooks/useTrialPhase.ts`
- `frontend/__tests__/billing/trial-paywall.test.tsx`
- `backend/tests/test_trial_paywall.py`

**Modificados:**
- `backend/quota.py` (get_trial_phase)
- `backend/routes/user.py` (trial_phase no response)
- `backend/routes/search.py` (truncar resultados)
- `backend/excel.py` (preview sheet)
- `backend/config.py` (feature flag)
- `frontend/app/buscar/components/SearchResults.tsx`
- `frontend/app/pipeline/page.tsx`

## Dependencias

- STORY-319 (trial 14 dias) — precisa do novo trial duration para calcular dia 7
- STORY-312 (CTAs contextuais) — complementa, nao substitui

## Riscos

- Paywall muito agressivo = usuarios abandonam trial antes de converter
- Paywall muito suave = nao cria urgencia suficiente
- Monitorar: taxa de conversao dias 7-14 vs baseline
- Fallback: feature flag para desativar se metricas piorarem
