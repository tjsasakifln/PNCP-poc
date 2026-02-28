# STORY-312: Trial Upsell CTAs Contextuais

**Epic:** EPIC-PRE-GTM-2026-02
**Sprint:** Sprint 2 (Launch)
**Priority:** HIGH
**Story Points:** 5 SP
**Estimate:** 3-4 dias
**Owner:** @dev + @ux-design-expert

---

## Problem

CTAs de conversao trial→paid sao genericos e aparecem apenas quando o trial expira (TrialConversionScreen) ou como banner fixo (TrialExpiringBanner). Faltam CTAs contextuais nos momentos de alto valor percebido — quando o usuario acaba de descobrir oportunidades, gerar um relatorio, ou adicionar ao pipeline. Esses "momentos de valor" sao os pontos de maior propensao a conversao.

## Solution

Inserir CTAs contextuais em 5 momentos-chave de valor percebido, com copy personalizado baseado na acao do usuario e metricas de uso. Tracking de conversao por ponto de insercao para otimizacao.

---

## Acceptance Criteria

### Frontend — CTAs Contextuais

- [x] **AC1:** CTA pos-busca bem-sucedida em `SearchResults.tsx`:
  - Trigger: resultado com >= 10 oportunidades filtradas, usuario em trial
  - Copy: "Voce encontrou {N} oportunidades! Com o SmartLic Pro, analise ilimitada."
  - CTA: "Ver planos" → /planos
  - Estilo: card sutil abaixo dos resultados (nao intrusivo), tom celebratorio
- [x] **AC2:** CTA pos-download Excel em `SearchResults.tsx`:
  - Trigger: apos download de relatorio, usuario em trial
  - Copy: "Relatorio exportado! No plano Pro, exporte ate {limit} por mes."
  - CTA: "Assinar SmartLic Pro" → /planos
  - Estilo: toast ou inline card, dismissavel
- [x] **AC3:** CTA pos-adicionar ao pipeline em pipeline page:
  - Trigger: usuario adiciona item ao pipeline, usuario em trial
  - Copy: "Pipeline ativo! Com o Pro, acompanhe ate {limit} oportunidades simultaneas."
  - CTA: "Conhecer plano Pro" → /planos
  - Estilo: tooltip ou card inline no pipeline
- [x] **AC4:** CTA na pagina de dashboard com metricas de uso:
  - Trigger: usuario visita dashboard, tem >= 3 buscas, usuario em trial
  - Copy: "Voce ja analisou R${valor} em oportunidades. Continue sem limites."
  - CTA: "Assinar agora" → /planos
  - Estilo: card destaque no dashboard, com valor em destaque
- [x] **AC5:** CTA em quota approaching (80%):
  - Trigger: `useQuota()` retorna >= 80% usage, usuario em trial
  - Copy: "Voce usou {X}/{Y} buscas. Atualize para continuar sem interrupcao."
  - CTA: "Atualizar plano" → /planos
  - Estilo: banner amarelo no topo (reusar pattern de QuotaCounter)

### Frontend — Componente Reutilizavel

- [x] **AC6:** Criar `frontend/components/billing/TrialUpsellCTA.tsx`:
  - Props: `variant` (post-search | post-download | post-pipeline | dashboard | quota)
  - Props: `contextData` (oportunidades, valor, usage, etc.)
  - Logica interna: so renderiza se `plan_type === 'free_trial'` e trial nao expirado
  - Dismissavel com `localStorage` (nao mostrar mesmo CTA por 24h apos dismiss)
  - Tracking: `trackEvent('trial_upsell_shown', { variant, context })`
  - Tracking: `trackEvent('trial_upsell_clicked', { variant, context })`
  - Tracking: `trackEvent('trial_upsell_dismissed', { variant, context })`
- [x] **AC7:** Frequencia max: 1 CTA por sessao de uso (nao bombardear)
  - `sessionStorage` counter: se ja mostrou 1 CTA nesta sessao, nao mostrar outro
  - Excecao: quota approaching (AC5) sempre mostra (e funcional, nao upsell)

### Frontend — Integracao com TrialConversionScreen Existente

- [x] **AC8:** Manter `TrialConversionScreen.tsx` como modal de expiracao (nao duplicar)
- [x] **AC9:** Manter `TrialExpiringBanner.tsx` como aviso de dias restantes (nao duplicar)
- [x] **AC10:** CTAs contextuais complementam (nao substituem) os componentes existentes

### Analytics — Conversao por Ponto

- [x] **AC11:** Dashboard admin deve mostrar (STORY-308):
  - CTAs mostrados vs clicados por variant (conversion rate)
  - Top variant por conversao
  - Revenue atribuida a cada ponto de CTA

### Testes

- [x] **AC12:** Testes para cada variant do TrialUpsellCTA (5 variants x render + dismiss + click)
- [x] **AC13:** Teste de frequencia max (1 por sessao)
- [x] **AC14:** Teste que CTA nao aparece para usuarios pagos
- [x] **AC15:** Zero regressions

---

## Infraestrutura Existente

| Componente | Arquivo | Status |
|-----------|---------|--------|
| TrialConversionScreen | `frontend/app/components/TrialConversionScreen.tsx` | Existe (expiracao) |
| TrialExpiringBanner | `frontend/app/components/TrialExpiringBanner.tsx` | Existe |
| Trial value API | `backend/routes/analytics.py` GET /trial-value | Existe |
| useQuota hook | `frontend/hooks/useQuota.ts` | Existe |
| useAnalytics hook | `frontend/hooks/useAnalytics.ts` | Existe |
| Mixpanel tracking | Integrado via useAnalytics | Existe |

## Files Esperados (Output)

**Novos:**
- `frontend/components/billing/TrialUpsellCTA.tsx`
- `frontend/__tests__/billing/trial-upsell-cta.test.tsx`

**Modificados:**
- `frontend/app/buscar/components/SearchResults.tsx`
- `frontend/app/pipeline/page.tsx` (ou componente equivalente)
- `frontend/app/dashboard/page.tsx`

## Dependencias

- STORY-308 (dashboard admin para metricas)
- useQuota hook funcional

## Riscos

- CTAs demais = usuario annoyed → frequencia max de 1/sessao e critica
- Copy generico nao converte → personalizar com dados reais do usuario
- A/B testing futuro: considerar infra para variar copy/posicionamento
