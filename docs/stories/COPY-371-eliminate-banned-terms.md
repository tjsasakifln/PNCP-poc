# STORY-COPY-371: Eliminar "faça upgrade", "Assine agora", e "plano" das mensagens voltadas ao usuário

**Prioridade:** P0 (violação de regra)
**Escopo:** `backend/quota.py`, `backend/excel.py`, `frontend/lib/error-messages.ts`, `frontend/app/buscar/types/searchPhase.ts`, `frontend/app/buscar/hooks/useSearch.ts`, `frontend/app/conta/equipe/page.tsx`, `frontend/app/ajuda/page.tsx`
**Estimativa:** M
**Origem:** Conselho de Copymasters — Consenso 8/8 clusters

## Contexto

CLAUDE.md proíbe "plano", "assinatura", "faça upgrade", "Assine agora" em texto visível ao usuário. O codebase tem pelo menos 8 violações em produção.

- **Cluster 3 (SaaS Conversion):** Linguagem transacional ("faça upgrade") cria resistência em compradores B2G brasileiros.
- **Cluster 6 (Copy Brasileira):** Substituições que preservam tom profissional-caloroso.
- **Cluster 1 (Direct Response):** Substituir por copy orientada a resultado, não a transação.

## Critérios de Aceitação

- [ ] AC1: `quota.py:973` — "Limite de {N} buscas mensais atingido. Renovação em {data} ou faça upgrade." → "Você atingiu {N} análises este mês. Seu limite renova em {data}."
- [ ] AC2: `quota.py:930` — mantido (já está bom: "Veja o valor que você analisou e continue tendo vantagem.")
- [ ] AC3: `quota.py:1183` — "Seu acesso expirou. Ative um plano para continuar." → "Seu acesso expirou. Reative para continuar analisando oportunidades."
- [ ] AC4: `excel.py:251` — "Assine agora: https://smartlic.tech/planos" → "Acesse todos os resultados: https://smartlic.tech/planos"
- [ ] AC5: `excel.py:249-250` — Corrigir acentos: "contem" → "contém", "voce" → "você", "tera" → "terá"
- [ ] AC6: `error-messages.ts:298` — "Você atingiu o limite de buscas do seu plano." → "Você atingiu o limite de análises deste mês."
- [ ] AC7: `searchPhase.ts:132` — "Ver planos" → "Ver opções"
- [ ] AC8: `useSearch.ts:901` — "seu plano: {plan_name}" → "seu acesso atual"
- [ ] AC9: `ajuda/page.tsx:91-93` — Remover "plano" das perguntas e respostas da FAQ (reescrever para "Como amplio meu acesso?" / "Acesse a página de Opções e escolha...")
- [ ] AC10: `conta/equipe/page.tsx:189-198` — "disponível no plano Consultoria" → "disponível no SmartLic Consultoria"; "Ver planos" → "Ver opções"
- [ ] AC11: Testes que verificam strings antigas atualizados

## Copy Recomendada

```
// Quota atingida (quota.py)
"Você atingiu {N} análises este mês. Seu limite renova em {data}."

// Acesso expirado (quota.py)
"Seu acesso expirou. Reative para continuar analisando oportunidades."

// Excel upsell (excel.py)
"Este arquivo contém uma prévia com os primeiros 10 resultados."
"Com o SmartLic Pro, você terá acesso a todos os {N} resultados."
"Acesse todos os resultados: https://smartlic.tech/planos"

// Error messages (error-messages.ts)
"Você atingiu o limite de análises deste mês."

// Busca phase action (searchPhase.ts)
"Ver opções"

// useSearch date range (useSearch.ts)
"O período de busca não pode exceder {max} dias (seu acesso atual). Você tentou buscar {N} dias. Reduza o período e tente novamente."
```

## Princípios Aplicados

- **Wiebe (SaaS Conversion):** Copy orientada a resultado converte melhor que copy orientada a transação
- **Cialdini (Psicologia):** Reciprocidade — mostrar o valor antes de pedir pagamento
- **Guanaes (Copy Brasileira):** Pessoalidade > formalismo corporativo

## Evidência

- Atual: 8+ instâncias de "plano", "faça upgrade", "Assine agora" em produção
- Regra CLAUDE.md: "Never use plano, assinatura, tier, pacote, busca in user-visible text"
