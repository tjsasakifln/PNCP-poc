# STORY-443: Trial-Value Dashboard

**Priority:** P1 — Quantifica valor antes do paywall
**Effort:** M (3 dias)
**Squad:** @dev + @qa
**Status:** Done
**Epic:** [EPIC-CONVERSION-2026-04](EPIC-CONVERSION-2026-04.md)
**Sprint:** Sprint 2 — Semanas 3-4

---

## Contexto

Usuários trial veem o mesmo dashboard genérico dos usuários pagantes. Não há nenhuma superfície que mostre ao usuário trial o valor concreto que ele está extraindo da plataforma durante os 14 dias — o que reduz urgência de conversão.

O endpoint `GET /v1/analytics/trial-value` já existe (implementado em GTM-010) e retorna dados de valor do trial. O único trabalho é surfacear isso de forma proeminente e convincente no topo do dashboard.

**Impacto estimado:** +1-2pp em trial-to-paid conversion.

---

## Acceptance Criteria

### AC1: Card de Trial Value no topo do dashboard
- [x] Para usuários `plan_type === "free_trial"` com trial ativo, renderizar `TrialValueCard` no topo da página `/dashboard` (acima dos outros widgets)
- [x] Card contém (usando campos reais do endpoint `TrialValueResponse`):
  - Título: "Seu progresso no SmartLic"
  - Oportunidades encontradas: "{`total_opportunities`} editais relevantes identificados"
  - Valor total analisado: "R$ {`total_value`} em contratos potenciais" (formatado em BRL)
  - Buscas realizadas: "{`searches_executed`} buscas executadas"
  - Horas economizadas: "~{`total_opportunities` × 45 / 60} horas economizadas vs. busca manual"
  - Progresso do trial: "Dia X de 14" + barra de progresso visual (linear)

### AC2: Dados do endpoint existente
- [x] Dados buscados de `GET /api/analytics?endpoint=trial-value` (proxy existente)
- [x] NÃO criar novo endpoint backend — reutilizar o que existe
- [x] Se endpoint retornar erro: exibir card com apenas "Dia X de 14" + CTA (sem métricas)

### AC3: CTA de conversão no card
- [x] Botão no card: "Continue analisando com SmartLic Pro →" com href="/planos"
- [x] Botão com estilo primário (não secundário/outline)
- [x] Subtext: "A partir de R$397/mês — cancele quando quiser"

### AC4: Progresso visual do trial
- [x] Barra de progresso linear (0-100%) representando dias usados / 14 dias totais
- [x] Cor da barra: verde (dias 1-7), amarelo (8-11), vermelho (12-14)
- [x] Texto de urgência na barra: "X dias restantes" (vermelho nos últimos 3 dias)

### AC5: Não aparece para pagantes
- [x] `TrialValueCard` NÃO renderizado para usuários com plano pago
- [x] `TrialValueCard` NÃO renderizado para trial expirado (eles já estão no hard block)

### AC6: Loading e fallback
- [x] Durante fetch dos dados: skeleton loader no card (não spinner de página inteira)
- [x] Se analytics endpoint lento (>3s): mostrar card com dados parciais (dia do trial) sem bloquear

### AC7: Testes
- [x] Teste: trial user dia 5 → card visível com dados corretos
- [x] Teste: trial user com erro de analytics → card com fallback (apenas dia)
- [x] Teste: paid user → card não renderizado
- [x] Teste: barra de progresso com cor correta por fase

---

## Scope

**IN:**
- Componente `TrialValueCard.tsx`
- Integração no `dashboard/page.tsx`
- Reutilização do endpoint existente `/api/analytics?endpoint=trial-value`
- Skeleton loader
- Tracking implícito (CTA já tem href=/planos — não requer evento separado)

**OUT:**
- Novo endpoint backend
- Gamificação (badges, achievements)
- Comparação com outros usuários
- Gráfico de histórico dentro do card

---

## Dependencies

- Endpoint `GET /v1/analytics/trial-value` (GTM-010) — verificar campos retornados: `total_searches`, `total_results`, `total_value_brl`
- Contexto de auth para verificar `plan_type` e `trial_expires_at`
- STORY-448 (barra de progresso no header) — pode ser implementada em paralelo; coordenar cor/estilo da barra de progresso para consistência visual

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Endpoint trial-value retorna campos com nomes diferentes dos esperados | Média | Verificar contrato da API antes de implementar o card |
| Trial expires_at não acessível no componente de dashboard | Baixa | Verificar hook/context de auth disponível |

---

## File List

- [x] `frontend/app/dashboard/components/TrialValueCard.tsx` — AC1-AC6: novo componente
- [x] `frontend/app/dashboard/page.tsx` — AC1, AC5: integrar card condicionalmente no topo
- [x] `frontend/__tests__/dashboard/TrialValueCard.test.tsx` — AC7: testes unitários

---

## Dev Notes

- Campos confirmados do `TrialValueResponse` (backend/routes/analytics.py linha 329-334):
  - `total_opportunities: int`
  - `total_value: float`
  - `searches_executed: int`
  - `avg_opportunity_value: float`
  - `top_opportunity: TopOpportunity | None`
- Fórmula de horas economizadas: `Math.round(total_opportunities * 45 / 60)` horas (45 min por edital analisado manualmente)
- Formato de valor: `Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)`
- Reutilizar classes Tailwind da barra de progresso da STORY-448 para consistência visual
- Componente deve usar `Suspense` boundary ou loading state próprio para não bloquear dashboard

---

## Change Log
- 2026-04-12: Status → Done (implementado em EPIC-CONVERSION-2026-04, testes corrigidos)

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Story criada — CEO Board Sprint, impacto +1-2pp |
| 2026-04-12 | @po | GO — Correção: campos reais confirmados (`total_opportunities`, `total_value`, `searches_executed`). AC1 atualizado. |
