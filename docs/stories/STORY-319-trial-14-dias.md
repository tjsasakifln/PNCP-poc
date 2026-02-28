# STORY-319: Reduzir Trial de 30 para 14 Dias

**Epic:** EPIC-TURBOCASH-2026-03
**Sprint:** Sprint 1 (Quick Wins)
**Priority:** P0 — BLOCKER
**Story Points:** 5 SP
**Estimate:** 3-4 dias
**Owner:** @dev
**Origem:** TurboCash Playbook — Acao 5 (Otimizar Trial Funnel)

---

## Problem

O trial atual de 30 dias e longo demais. Benchmark de mercado (Chargebee/ProfitWell) mostra que trials de 14 dias convertem 40-60% mais que trials de 30 dias. Licita Ja (concorrente direto) usa trial de 14 dias. O periodo estendido reduz urgencia e permite que usuarios "esqueçam" a plataforma antes de converter.

## Solution

Reduzir o trial de 30 para 14 dias com migração adequada para usuarios existentes e ajuste de toda a copy/UX que referencia "30 dias".

**Evidencia:** Trial conversion (14d vs 30d): +40-60% lift — Chargebee/ProfitWell

---

## Acceptance Criteria

### Backend — Configuracao

- [ ] **AC1:** Alterar `config.py` → `TRIAL_DURATION_DAYS` default de `30` para `14`
- [ ] **AC2:** Alterar `quota.py` → qualquer referencia hardcoded a 30 dias de trial
- [ ] **AC3:** Alterar email templates em `backend/templates/emails/trial.py`:
  - `render_trial_midpoint_email()` — ajustar copy de "15 dias" para "7 dias"
  - `render_trial_expiring_email()` — ajustar copy de "5 dias" para "3 dias"
  - `render_trial_last_day_email()` — manter (dia 13/14)
  - `render_trial_expired_email()` — manter
- [ ] **AC4:** Endpoint `GET /v1/trial-status` retorna `days_remaining` correto (baseado em 14d)

### Backend — Migracao de Usuarios Existentes

- [ ] **AC5:** Criar migration SQL que:
  - Usuarios com trial ativo e `created_at` ha mais de 14 dias → manter trial ate completar 30d (grandfather clause)
  - Usuarios com trial ativo e `created_at` ha 14 dias ou menos → aplicar novo limite de 14d
  - Novos usuarios a partir da data da migration → 14 dias
  - Log: registrar quantos usuarios foram afetados em cada grupo
- [ ] **AC6:** Feature flag `TRIAL_14_DAYS_ENABLED` para rollout gradual (default: true)

### Frontend — Copy e UX

- [ ] **AC7:** Atualizar `TrialCountdown.tsx` — qualquer referencia a "30 dias"
- [ ] **AC8:** Atualizar `TrialExpiringBanner.tsx` — threshold de exibicao (mostrar a partir do dia 8, nao dia 24)
- [ ] **AC9:** Atualizar `TrialConversionScreen.tsx` — copy "30 dias" → "14 dias"
- [ ] **AC10:** Atualizar pagina `/planos` — copy de trial
- [ ] **AC11:** Atualizar pagina `/signup` — copy de trial ("14 dias gratis")
- [ ] **AC12:** Atualizar landing page (`/`) — qualquer referencia a "30 dias gratis"
- [ ] **AC13:** Atualizar onboarding — copy de trial

### Testes

- [ ] **AC14:** Testes backend: trial expira em 14d (nao 30d)
- [ ] **AC15:** Testes backend: grandfather clause para usuarios existentes
- [ ] **AC16:** Testes frontend: componentes exibem "14 dias"
- [ ] **AC17:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| Trial duration config | `backend/config.py:381` | Existe (30d) |
| Trial status endpoint | `backend/routes/user.py` → GET /trial-status | Existe |
| Trial countdown | `frontend/app/components/TrialCountdown.tsx` | Existe |
| Trial expiring banner | `frontend/app/components/TrialExpiringBanner.tsx` | Existe |
| Trial conversion screen | `frontend/app/components/TrialConversionScreen.tsx` | Existe |
| Plan capabilities | `backend/quota.py:93-102` | Existe |
| Email templates | `backend/templates/emails/trial.py` | Existe |

## Files Esperados (Output)

**Modificados:**
- `backend/config.py` (TRIAL_DURATION_DAYS 30→14)
- `backend/quota.py` (referências a 30d)
- `backend/templates/emails/trial.py` (copy ajustado)
- `frontend/app/components/TrialCountdown.tsx`
- `frontend/app/components/TrialExpiringBanner.tsx`
- `frontend/app/components/TrialConversionScreen.tsx`
- `frontend/app/planos/page.tsx`
- `frontend/app/signup/page.tsx` (ou equivalente)
- `frontend/app/page.tsx` (landing)

**Novos:**
- `supabase/migrations/XXXXXXXX_trial_14_days.sql`
- Testes atualizados

## Dependencias

- Nenhuma bloqueadora
- STORY-321 (email sequence) depende desta story

## Riscos

- Usuarios existentes com trial de 30d podem reclamar se cortarmos → grandfather clause (AC5)
- Copy hardcoded em locais inesperados → search completo por "30 dias", "30 days", "30d"
- A/B testing futuro: manter feature flag para reverter se conversao cair
