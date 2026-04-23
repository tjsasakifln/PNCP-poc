# SAB-014: /planos — destacar trial 14 dias "sem cartão" acima do fold

**Status:** Ready
**Origem:** Selenium Quality Audit — test_planos_page_shows_prices (2026-04-22)
**Prioridade:** P1 — Alto (conversão direta de visitante orgânico)
**Complexidade:** S (Small)
**Sprint:** SAB-sprint-atual
**Owner:** @dev + @po
**Tipo:** UX / Conversão

---

## Problema

Audit Selenium detectou que `/planos` não destaca o período de trial de 14 dias de forma visível. O teste verificou a presença de "14", "trial" ou "grátis" no conteúdo — e identificou ausência de destaque claro acima do fold.

Contexto de conversão B2G:
- Compradores B2G têm ciclo de decisão longo — trial sem fricção é o principal gatilho de ativação
- "Sem cartão de crédito" reduz medo de cobrança acidental (principal objeção em B2B SaaS no Brasil)
- Pesquisas de CRO: badges de "14 dias grátis" acima do fold aumentam conversão de pricing page em 15–30%

---

## Critérios de Aceite

- [ ] **AC1:** Badge ou destaque visual "14 dias grátis" visível sem scroll em viewport 1280×720 em `/planos`
- [ ] **AC2:** Texto "sem cartão de crédito" ou "sem precisar de cartão" presente próximo ao CTA principal
- [ ] **AC3:** CTA do plano Pro inclui microcopy de trial (ex: "Começar trial grátis" em vez de só "Assinar")
- [ ] **AC4:** Viewport mobile 390px: badge/destaque de trial visível sem scroll
- [ ] **AC5:** Audit Selenium passa: `test_planos_page_shows_prices` sem insight UX de trial

### Anti-requisitos

- Não remover preços — transparência de billing é mantida
- Não adicionar pop-up ou modal de trial — apenas destaque na página existente

---

## Referência de implementação

Verificar `frontend/app/planos/page.tsx` e componentes de `PlanCard`. O destaque pode ser:
- Badge "14 dias grátis" no header da seção de planos
- Sublabel no botão de CTA de cada card
- Banner acima dos cards: "Todos os planos incluem 14 dias grátis • Sem cartão"

---

## Riscos

- **R1 (Alto):** Wording de trial deve refletir condições reais — se `TRIAL_DAYS` em produção não for 14, texto "14 dias" é enganoso (CDC). **Bloqueia início**: confirmar `TRIAL_DAYS` antes de implementar.
- **R2 (Baixo):** Badge "grátis" pode gerar expectativa de plano permanentemente gratuito — usar "trial grátis" ou "14 dias sem custo" para clareza.

## Dependências

- `backend/config.py` → `TRIAL_DAYS` deve ser verificado em produção antes do início
- Aprovação de wording pelo @po antes do merge

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-22 | @sm | Story criada a partir do Selenium Quality Audit |
| 2026-04-22 | @po | Validação 10-point: **7/10 → GO condicional** — R1 bloqueia início até confirmar TRIAL_DAYS em produção |
