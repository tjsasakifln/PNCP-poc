# SAB-011: Planos — remover badge BETA e melhorar heading

**Origem:** UX Premium Audit P2-03, P2-04
**Prioridade:** P2 — Médio
**Complexidade:** S (Small)
**Sprint:** SAB-P2
**Owner:** @dev + @po
**Screenshots:** `ux-audit/28-planos.png`, `ux-audit/29-planos-bottom.png`

---

## Problema

### P2-03: Badge "BETA" no produto pago
Card de pricing mostra "SmartLic Pro **BETA**" com badge azul. Cobrar R$397/mês por um produto em "BETA" gera desconfiança.

### P2-04: Heading questionável
Título "Escolha Seu Nível de Compromisso" — "Compromisso" tem conotação negativa em português ("obrigação").

---

## Critérios de Aceite

### Badge BETA (P2-03)

- [x] **AC1:** Opção A escolhida: Badge "BETA" removido completamente do card de pricing.
- [x] **AC2:** N/A (opção A escolhida — sem tooltip necessário).
- [x] **AC3:** Grep global realizado. Removido "(Beta)" de: ajuda FAQ (2x), FaqStructuredData (2x), termos, signup layout meta, planos layout meta, InstitutionalSidebar, valueProps, TrialConversionScreen. Total: 10 ocorrências limpas.

### Heading (P2-04)

- [x] **AC4:** Heading alterado para "Comece a Vencer Licitações". Também atualizado: PlanToggle aria-label, FAQ answer, trial/expired banners, TrialCountdown title, pricing page — todos "compromisso" → "período de acesso".

---

## Arquivos Prováveis

- `frontend/app/planos/page.tsx` — página de planos/pricing
- `frontend/components/PlanCard.tsx` — card de plano

## Notas

- Decisão de copy precisa de aprovação do PO/Marketing antes de implementar.
- Não alterar preços ou estrutura de planos — apenas visual e copy.
