# STORY-COPY-375: Upgrade do social proof de "10 empresas" para prova por setor

**Prioridade:** P1 (conversão — FinalCTA é última impressão antes do signup)
**Escopo:** `frontend/app/components/landing/FinalCTA.tsx`, `frontend/__tests__/story-273-social-proof.test.tsx`
**Estimativa:** S
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

"Mais de 10 empresas já testaram" é social proof fraco demais para converter compradores B2G.

- **Cluster 5 (Cialdini):** Social proof funciona por similaridade, não por volume. Para B2G, o que convence é "empresas do meu setor já usam".
- **Cluster 1 (Schwartz):** Especificidade vence volume.
- **Cluster 3 (Klettke):** Voice-of-customer framing.

## Critérios de Aceitação

- [ ] AC1: Substituir "Mais de 10 empresas já testaram — uniformes, TI, engenharia, saúde e facilities" por "Empresas de engenharia, TI, saúde, uniformes e facilities já analisam oportunidades com SmartLic"
- [ ] AC2: Remover o número "10" (muito baixo para social proof efetivo; o formato "empresas de [setores] já..." implica volume sem comprometer com número)
- [ ] AC3: Teste atualizado

## Copy Recomendada

```
"Empresas de engenharia, TI, saúde, uniformes e facilities já analisam oportunidades com SmartLic"
```

Racional: "já analisam" (presente contínuo) é mais forte que "já testaram" (passado, implica que pararam). A menção de setores ativa similaridade ("meu setor está lá").

## Princípios Aplicados

- **Cialdini (Psicologia):** Social proof por similaridade > social proof por volume
- **Schwartz (Direct Response):** Especificidade é a alma da credibilidade
- **Klettke (SaaS Conversion):** VOC framing — use a linguagem do cliente

## Evidência

- Atual: `FinalCTA.tsx:44` — "Mais de 10 empresas"
- Best practice 2026: Social proof deve enfatizar similarity, not scale, para mercados de nicho
