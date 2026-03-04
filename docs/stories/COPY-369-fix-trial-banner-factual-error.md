# STORY-COPY-369: Corrigir banner de trial que mostra "termina amanhã" independente dos dias restantes

**Prioridade:** P0 (bug factual)
**Escopo:** `frontend/app/components/TrialExpiringBanner.tsx`, `frontend/__tests__/trial-components.test.tsx`
**Estimativa:** XS
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

O banner `TrialExpiringBanner` exibe fixamente "Seu acesso completo ao SmartLic termina amanhã." para qualquer valor de `daysRemaining` de 0 a 6. Quando `daysRemaining=6`, faltam 6 dias — dizer "termina amanhã" é factualmente incorreto. Isso destrói confiança imediatamente.

- **Cluster 2 (UX Writing):** Credibilidade é pré-requisito para qualquer conversão.
- **Cluster 5 (Psicologia):** Inconsistência factual ativa ceticismo e invalida toda mensagem subsequente.
- **Cluster 5 (Ariely):** Reframe diário reduz dor do pagamento (R$9,90/dia vs R$297/mês).

## Critérios de Aceitação

- [ ] AC1: Copy do banner usa `daysRemaining` dinamicamente:
  - `daysRemaining === 0`: "Seu acesso completo ao SmartLic termina hoje."
  - `daysRemaining === 1`: "Seu acesso completo ao SmartLic termina amanhã."
  - `daysRemaining >= 2`: "Seu acesso completo ao SmartLic termina em {N} dias."
- [ ] AC2: Subtexto ajustado: "Continue com acesso a todas as funcionalidades a partir de R$ 9,90/dia."
- [ ] AC3: Testes atualizados para validar copy dinâmica para `daysRemaining` = 0, 1, 3, 6
- [ ] AC4: CTA permanece "Continuar tendo vantagem" (já está bom)

## Copy Recomendada

```
// daysRemaining === 0
"Seu acesso completo ao SmartLic termina hoje."

// daysRemaining === 1
"Seu acesso completo ao SmartLic termina amanhã."

// daysRemaining >= 2
"Seu acesso completo ao SmartLic termina em {N} dias."

// Subtexto (todos os casos)
"Continue com acesso a todas as funcionalidades a partir de R$ 9,90/dia."
```

## Princípios Aplicados

- **Yifrah (UX Writing):** Precisão factual é pré-condição para confiança em microcopy
- **Ariely (Psicologia):** Reframe diário reduz dor do pagamento (R$9,90/dia vs R$297/mês)

## Evidência

- Atual: `TrialExpiringBanner.tsx:49` — "termina amanhã" hardcoded com prop `daysRemaining` ignorada
- Best practice 2026: Trial banners devem ser contextualmente precisos; erros factuais destroem confiança 3x mais rápido que copy fraca
