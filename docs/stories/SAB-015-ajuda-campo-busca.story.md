# SAB-015: /ajuda — adicionar campo de busca/pesquisa de perguntas

**Status:** Ready
**Origem:** Selenium Quality Audit — test_ajuda_page_has_searchable_content (2026-04-22)
**Prioridade:** P2 — Médio (redução de tickets de suporte)
**Complexidade:** M (Medium)
**Sprint:** SAB-sprint-atual
**Owner:** @dev + @ux-design-expert
**Tipo:** UX / Self-service

---

## Problema

Audit Selenium confirmou que `/ajuda` não tem campo de busca (`input[type='search']` ou `input[placeholder*='buscar']`). Usuários com dúvida específica precisam navegar manualmente pelas categorias.

Impacto estimado:
- Help centers com busca reduzem tickets de suporte em 20–40% (dados Zendesk/Intercom)
- Usuários B2G frequentemente chegam com dúvidas técnicas específicas ("como funciona o pregão eletrônico?", "qual é o limite de buscas?")
- Self-service bem indexado reduz churn early-stage: usuário que acha resposta sozinho tem maior engajamento

---

## Critérios de Aceite

### Campo de Busca (AC1–AC3)

- [ ] **AC1:** Campo `<input type="search">` presente em `/ajuda` com placeholder tipo "Buscar perguntas…" ou "Pesquisar na ajuda"
- [ ] **AC2:** Busca filtra as perguntas visíveis em tempo real (client-side) — sem necessidade de backend para fase 1
- [ ] **AC3:** Campo visível sem scroll em viewport 1280×720 (preferencialmente no topo da seção de conteúdo)

### Comportamento (AC4–AC5)

- [ ] **AC4:** Sem resultados: exibe mensagem "Nenhuma pergunta encontrada para '[termo]'" com link para suporte
- [ ] **AC5:** Campo aceita termos parciais (ex: "plano" filtra "Como funciona o plano Pro?" e "Posso mudar de plano?")

### Regressão (AC6)

- [ ] **AC6:** Audit Selenium passa: `test_ajuda_page_has_searchable_content` sem insight UX de busca

---

## Escopo Fase 1 (esta story)

- Busca client-side nas perguntas já existentes na página
- Sem integração com backend ou banco de dados
- Sem analytics de busca (fase 2)

## Fora de Escopo (fase 2)

- Busca fulltext em toda documentação via API
- Tracking de termos buscados sem resultado (insight para criar novo conteúdo)
- Sugestões de autocomplete

---

## Arquivos prováveis

- `frontend/app/ajuda/page.tsx` — adicionar state de filtro + input
- `frontend/app/ajuda/components/` — verificar se há FAQItem ou componente de pergunta

---

## Riscos

- **R1 (Médio):** Se `/ajuda` carrega conteúdo dinâmico via CMS/API sem estado local, busca client-side simples via `.filter()` não funciona — nesse caso a implementação precisa ser via fetch filtrado ou índice local. Investigar estrutura de dados de `/ajuda` antes de codar.
- **R2 (Baixo):** Campo de busca sem debounce pode travar em páginas com muitas perguntas — adicionar `setTimeout` de 150ms.

## Dependências

- Nenhuma story bloqueante
- Investigação prévia de `frontend/app/ajuda/page.tsx` antes do início

## Notas

- Manter acessibilidade: input com `aria-label="Buscar perguntas"` e role correto
- Não usar `role="search"` sem landmark correto
- Se /ajuda usa conteúdo estático (array de FAQs), busca client-side é trivial via `.filter()`

---

## Change Log

| Data | Agente | Ação |
|------|--------|------|
| 2026-04-22 | @sm | Story criada a partir do Selenium Quality Audit |
| 2026-04-22 | @po | Validação 10-point: **8/10 → GO** — adicionados Riscos e Dependências; escopo fase 1/2 já bem definido |
