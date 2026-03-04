# STORY-COPY-379: Humanizar mensagens de erro com estrutura de 4 partes

**Prioridade:** P2 (sentimento — erros são momento de maior vulnerabilidade)
**Escopo:** `frontend/lib/error-messages.ts` (ERROR_CODE_MESSAGES)
**Estimativa:** S
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

As mensagens de erro atuais cobrem "o que aconteceu" e "o que fazer" mas omitem "por que" e "onde buscar ajuda".

- **Cluster 2 (Dunn):** Estrutura canônica: (1) o que aconteceu, (2) por que, (3) o que fazer, (4) onde buscar ajuda.
- **Cluster 5 (Fogg):** Em momento de erro, o usuário está em estado de baixa motivação — maximizar "ability" (clareza do próximo passo).
- **Cluster 6 (Serpa):** "Brevidade é empatia. 14 palavras ou menos."

## Critérios de Aceitação

- [ ] AC1: Reescrever `ERROR_CODE_MESSAGES` com estrutura empática:
  - `BACKEND_UNAVAILABLE`: "Estamos voltando em instantes. Tente novamente em alguns segundos."
  - `SOURCE_UNAVAILABLE`: "As fontes de dados estão temporariamente em manutenção. Tente novamente em breve."
  - `ALL_SOURCES_FAILED`: "Nenhuma fonte respondeu a tempo. Tente novamente em 2-3 minutos."
  - `TIMEOUT`: "A análise demorou mais que o esperado. Tente com menos estados ou um período menor."
  - `RATE_LIMIT`: "Muitas análises em sequência. Aguarde 1 minuto e tente novamente."
  - `QUOTA_EXCEEDED`: (ver STORY-COPY-371 AC6)
  - `VALIDATION_ERROR`: "Verifique os filtros selecionados e tente novamente."
  - `INTERNAL_ERROR`: "Algo deu errado do nosso lado. Nossa equipe já foi avisada."
- [ ] AC2: Cada mensagem tem no máximo 20 palavras
- [ ] AC3: Nenhuma mensagem culpa o usuário
- [ ] AC4: Testes atualizados

## Copy Recomendada

(Ver AC1 acima)

## Princípios Aplicados

- **Dunn (UX Writing):** Estrutura 4-part para error messages
- **Fogg (Psicologia):** Maximize ability em momento de baixa motivação
- **Serpa (Copy Brasileira):** "Máximo significado, mínimo palavras"

## Evidência

- Atual: `error-messages.ts:292-301` — funcional mas frio, sem empatia
- Best practice 2026: "Brevity is empathy. 14 words or fewer = 90% comprehension."
