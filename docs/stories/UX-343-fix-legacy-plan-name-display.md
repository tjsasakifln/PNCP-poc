# UX-343 — Fix: Exibicao de Nome de Plano Legacy ("Sala de Guerra" → "SmartLic Pro")

**Tipo:** Bug / UX
**Prioridade:** Alta
**Criada:** 2026-02-22
**Status:** Concluido
**Origem:** Auditoria UX 2026-02-22 — Menu do usuario mostra "Sala de Guerra" (plano legacy)

---

## Problema

No menu do usuario (dropdown do avatar), o plano exibido e "Sala de Guerra" com badge dourado "S". Este era o nome do plano mais alto no modelo antigo de 3 tiers (Consultor Agil / Maquina de Licitacoes / Sala de Guerra).

Apos GTM-002, o SmartLic migrou para plano unico "SmartLic Pro" com 3 periodos de faturamento. Os planos legados foram mantidos funcionais mas deveriam exibir "(legacy)" no nome conforme documentado.

### Evidencia

- Screenshot `ux-audit-10-user-menu.png` — badge "S Sala de Guerra >" no menu do usuario
- GTM-002 documenta: Legacy plans kept with "(legacy)" suffix in PLAN_NAMES

### Impacto

- Incoerencia: landing page e pricing falam "SmartLic Pro", mas o menu mostra "Sala de Guerra"
- Confusao para usuario: "O que e Sala de Guerra? Nao era SmartLic Pro?"
- Para novos usuarios que verao outros com planos diferentes, gera duvida

---

## Solucao

### 1. Frontend: Mapear nomes legados para exibicao

No componente que renderiza o plano no menu do usuario, mapear:

```typescript
const DISPLAY_PLAN_NAMES: Record<string, string> = {
  'smartlic_pro': 'SmartLic Pro',
  'sala_guerra': 'SmartLic Pro',        // legacy → mostrar como Pro
  'maquina': 'SmartLic Pro',            // legacy → mostrar como Pro
  'consultor_agil': 'SmartLic Pro',     // legacy → mostrar como Pro
  'free_trial': 'Avaliacao',
};
```

Ou, se o backend ja retorna `plan_type` normalizado, garantir que a UI consome o nome correto.

### 2. Backend: Verificar profiles.plan_type

Verificar na tabela `profiles` se o campo `plan_type` do admin e `sala_guerra` e se deveria ter sido migrado para `smartlic_pro` apos GTM-002.

Se nao migrado: criar migration ou script que atualiza planos legados para `smartlic_pro` (se a subscription Stripe foi migrada).

---

## Criterios de Aceitacao

- [x] AC1: Menu do usuario exibe "SmartLic Pro" (nunca "Sala de Guerra", "Maquina" ou "Consultor Agil")
- [x] AC2: Badge usa icone/cor consistente com o branding SmartLic Pro
- [x] AC3: Pagina /conta exibe "SmartLic Pro" na secao de plano
- [x] AC4: Se o backend retorna plano legacy, o frontend mapeia para "SmartLic Pro"
- [x] AC5: Backend authorization.py atualizado: admin/master retorna "SmartLic Pro (Admin/Master)"

### Nao-Regressao

- [x] AC6: Funcionalidades do plano continuam identicas (so nome/exibicao mudou)
- [x] AC7: Nenhum teste novo quebra (9 fail BE / 58 fail FE = pre-existentes)

---

## Arquivos Modificados

### Frontend (7 files)
- `lib/plans.ts` — displayNamePt e badge config de legacy plans → "SmartLic Pro"
- `app/components/PlanBadge.tsx` — badge styling e icon (C/M/S → P) para legacy plans
- `app/components/QuotaBadge.tsx` — sem mudanca (ja usa getPlanDisplayName)
- `app/planos/obrigado/page.tsx` — PLAN_DETAILS legacy → "SmartLic Pro"
- `app/conta/page.tsx` — usa getPlanDisplayName() ao inves de plan_name raw
- `components/subscriptions/AnnualBenefits.tsx` — "Exclusivo Sala de Guerra" → "Exclusivo SmartLic Pro"

### Backend (1 file)
- `authorization.py` — get_master_quota_info(): "Sala de Guerra" → "SmartLic Pro"

### Testes Atualizados (4 files)
- `backend/tests/test_authorization.py` — plan_name assertions
- `backend/tests/test_api_me.py` — admin plan_name assertion
- `frontend/__tests__/PlanBadge.test.tsx` — 21 tests (legacy → SmartLic Pro)
- `frontend/__tests__/components/subscriptions/AnnualBenefits.test.tsx` — 19 tests
- `frontend/e2e-tests/plan-display.spec.ts` — E2E plan name assertions

---

## Estimativa

- **Complexidade:** Baixa
- **Risco:** Baixo (so renomeia exibicao)
