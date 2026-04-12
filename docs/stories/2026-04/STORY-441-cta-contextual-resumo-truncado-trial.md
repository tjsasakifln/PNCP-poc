# STORY-441: CTA Contextual no Resumo Truncado (Trial Unlock)

**Priority:** P0 — Captura no momento de maior engajamento
**Effort:** S (1 dia)
**Squad:** @dev + @qa
**Status:** Ready
**Epic:** [EPIC-CONVERSION-2026-04](EPIC-CONVERSION-2026-04.md)
**Sprint:** Sprint 1 — Semanas 1-2

---

## Contexto

O resumo executivo de editais é truncado em 2 frases para usuários trial (`trialPhase === "limited_access"`) em `ResultCard.tsx` (~linha 37). O texto termina abruptamente com "..." mas não há nenhum CTA de unlock in-context — o usuário não sabe o que fazer.

O momento em que o usuário lê o início do resumo e quer ver mais é o pico de engajamento e intenção. Esse momento é desperdiçado atualmente. Um CTA inline "Desbloqueie o resumo completo" transforma frustração em oportunidade de conversão.

**Impacto estimado:** +2-3pp em trial-to-paid conversion.

---

## Acceptance Criteria

### AC1: CTA inline após texto truncado
- [x] Imediatamente após o texto truncado (após o "..."), exibir CTA inline na mesma linha/bloco
- [x] Texto do CTA: "Desbloqueie o resumo completo + recomendação de participação →"
- [x] CTA é um link (não botão) com `href="/planos"`

### AC2: Condicional por plano
- [x] CTA aparece APENAS para `trialPhase === "limited_access"` OU `isTrialExpired`
- [x] CTA NÃO aparece para usuários pagantes (plano ativo)
- [x] CTA NÃO aparece se `trialPhase === "full_access"` (trial com acesso completo, se existir)

### AC3: Navegação interna
- [x] Link usa `router.push('/planos')` ou `<Link href="/planos">` (não `target="_blank"`)
- [x] Não abre nova aba

### AC4: Tracking Mixpanel
- [x] Ao clicar no CTA, disparar evento Mixpanel: `trial_cta_clicked` com propriedades:
  - `source: "result_card_summary"`
  - `edital_id: string`
  - `setor: string`

### AC5: Estilo visual
- [x] CTA visualmente distinto: cor de destaque (usar `text-accent` ou `text-primary` do design system existente)
- [x] NÃO usar modal, popup, ou overlay — apenas texto inline com link
- [x] Fonte levemente menor que o resumo (texto secundário)

### AC6: Testes
- [x] Teste: trial user com `limited_access` → CTA visível
- [x] Teste: paid user → CTA não visível
- [x] Teste: trial expirado → CTA visível
- [x] Teste: click no CTA dispara evento Mixpanel correto

---

## Scope

**IN:**
- Modificação do bloco de resumo em `ResultCard.tsx`
- Condicional de exibição baseada em `trialPhase`
- Tracking Mixpanel no click

**OUT:**
- Modal de upgrade (fora do escopo)
- Alteração da lógica de truncamento (manter 2 frases)
- A/B test (futuro)
- Mudança na página /planos

---

## Dependencies

- STORY-440 (pode ser implementada em paralelo — não há conflito de arquivos exceto `ResultCard.tsx`)
- Se implementadas em paralelo: coordenar alterações em `ResultCard.tsx` para evitar conflito de merge

---

## Risks

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Conflito de merge com STORY-440 em ResultCard.tsx | Alta (se paralelo) | Implementar sequencialmente ou usar branches separadas |
| Tracking Mixpanel não inicializado no contexto do card | Baixa | Verificar que `useAnalytics()` ou `mixpanel.track()` está disponível no componente |

---

## File List

- [x] `frontend/app/buscar/components/search-results/ResultCard.tsx` — AC1, AC2, AC5: adicionar CTA condicional
- [x] `frontend/__tests__/buscar/ResultCard.test.tsx` — AC6: adicionar casos de teste para CTA

---

## Dev Notes

- O trecho de truncamento atual em `ResultCard.tsx`:
  ```tsx
  {trialPhase === "limited_access"
    ? result.resumo.resumo_executivo.split('. ').slice(0, 2).join('. ') + '...'
    : result.resumo.resumo_executivo}
  ```
- Após o `+ '...'`, adicionar condicionalmente o CTA
- Verificar como `trialPhase` é obtido no componente (prop drilling ou hook)
- Mixpanel: usar o mesmo padrão dos outros eventos no projeto (verificar `useAnalytics.ts` ou imports existentes)

---

## Change Log

| Data | Agente | Mudança |
|------|--------|---------|
| 2026-04-12 | @sm | Story criada — CEO Board Sprint, impacto +2-3pp |
