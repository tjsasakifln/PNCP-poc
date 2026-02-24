# GTM-STAB-005 — Fix "0 Oportunidades" com Check Verde + UX de Resultados Vazios

**Status:** To Do
**Priority:** P1 — High (UX medíocre → percepção de produto quebrado)
**Severity:** Frontend + Backend — filtro rejeita tudo, UX não comunica adequadamente
**Created:** 2026-02-24
**Sprint:** GTM Stabilization
**Relates to:** GTM-STAB-004 (partial results), UX-341 (empty states educativos), STORY-267 (term search parity)

---

## Problema

### 1. Check verde com 0 resultados = confusão

O screenshot mostra ES e SP com **✓ verde** e "0 oportunidades". Para o usuário, verde = sucesso. Mas 0 oportunidades = fracasso. Essa contradição visual gera frustração:

- "O sistema buscou e não encontrou nada?" → Desconfiança
- "Os dados estão corretos?" → Perda de credibilidade
- "Por que eu esperei 100s para isso?" → Abandono

### 2. Filtro muito agressivo para termos livres

O pipeline de filtro (filter.py, 3500+ linhas) foi otimizado para buscas por **setor** (15 setores com keywords calibradas). Quando o usuário faz busca por **termos livres** (custom_terms), o mesmo filtro se aplica e frequentemente rejeita TUDO:

- Keyword density mínima rejeita bids que mencionam o termo de forma diferente
- Sector exclusions podem excluir termos legítimos
- Min-match floor pode ser alto demais para termos genéricos
- Proximity/co-occurrence rules rejeitam falsos positivos que são verdadeiros positivos

### 3. Nenhuma orientação quando 0 resultados

Não há empty state educativo. O usuário vê "0 oportunidades" e não sabe:
- Se é porque não existem licitações no período
- Se é porque o filtro está muito restritivo
- O que fazer para melhorar os resultados

---

## Acceptance Criteria

### AC1: Semântica visual de UF status
- [ ] UfProgressGrid.tsx — 4 estados visuais distintos:
  | Estado | Visual | Significado |
  |--------|--------|-------------|
  | success + N>0 | ✓ verde, "N oportunidades" | Normal |
  | success + N=0 | — amarelo, "Sem oportunidades" | API respondeu, filtro zerou |
  | failed | ✗ vermelho, "Indisponível" | API timeout/error |
  | retrying | ↻ azul, "Retentando..." | Em retry |
- [ ] "0 oportunidades" com check verde NÃO deve mais existir
- [ ] Quando N=0, o card deve ser visivelmente diferente de sucesso (amarelo/cinza, não verde)

### AC2: Empty state educativo
- [ ] Quando total de resultados = 0 após processamento completo:
  ```
  ┌─────────────────────────────────────────┐
  │  🔍 Nenhuma oportunidade encontrada     │
  │                                         │
  │  Possíveis motivos:                     │
  │  • Período muito curto (10 dias)        │
  │  • Termos de busca muito específicos    │
  │  • Poucos editais abertos neste momento │
  │                                         │
  │  Sugestões:                             │
  │  [Ampliar período para 30 dias]         │
  │  [Incluir mais estados]                 │
  │  [Buscar por setor em vez de termos]    │
  │                                         │
  │  💡 Dica: Buscas por setor encontram    │
  │  mais oportunidades que buscas por      │
  │  termos específicos                     │
  └─────────────────────────────────────────┘
  ```
- [ ] Botões de sugestão devem ser funcionais (alteram parâmetros e rebuscam)
- [ ] Se modo setor com 0 resultados: sugerir ampliar período e estados
- [ ] Se modo termos com 0 resultados: sugerir setor mais próximo ou ampliar termos

### AC3: Filter stats transparente
- [ ] Quando resultados = 0, exibir motivo do filtro no response:
  ```json
  {
    "total_bruto": 47,
    "filtrado": 0,
    "filter_stats": {
      "valor_rejeitadas": 5,
      "keyword_rejeitadas": 38,
      "llm_rejeitadas": 4,
      "status_rejeitadas": 0
    },
    "filter_summary": "47 licitações encontradas, nenhuma aprovada pelos filtros de relevância"
  }
  ```
- [ ] Frontend exibe: "47 licitações encontradas nas fontes oficiais, mas nenhuma corresponde aos seus critérios"
- [ ] Isso dá confiança: o sistema BUSCOU, os dados EXISTEM, mas não são relevantes

### AC4: Auto-relaxation para termos livres
- [ ] Quando custom_terms + 0 resultados após filtro normal:
  1. **Retry 1:** Desabilitar min_match_floor → rodar filtro com floor=0
  2. **Retry 2:** Desabilitar keyword density threshold → aceitar qualquer menção
  3. **Retry 3:** Mostrar top-10 por valor (sem filtro keyword) com badge "Resultado ampliado"
- [ ] Cada retry deve ser automático (não pedir ação do usuário)
- [ ] Response deve indicar `filter_relaxed: true` e `relaxation_level: N`
- [ ] Frontend exibe banner: "Resultados com filtro ampliado — seus termos podem não aparecer diretamente"

### AC5: "Indisponível" com contexto
- [ ] Quando UF=failed, mostrar motivo:
  - "PNCP não respondeu para MG (timeout)" → user entende que é temporário
  - "Taxa limite atingida para RJ" → user entende rate limit
  - "Fonte offline para ES" → circuit breaker
- [ ] Sugerir: "Tente novamente em alguns minutos" ou auto-retry button

### AC6: Testes
- [ ] Frontend: test empty state com 0 resultados → sugestões visíveis
- [ ] Frontend: test UF status amarelo para success+0
- [ ] Backend: test auto-relaxation retorna resultados quando normal retorna 0
- [ ] Backend: test filter_stats incluso no response quando filtrado=0
- [ ] E2E: busca com termos específicos que resultam 0 → empty state educativo aparece

---

## Arquivos Envolvidos

| Arquivo | Ação |
|---------|------|
| `frontend/app/buscar/components/UfProgressGrid.tsx` | AC1: 4 estados visuais |
| `frontend/app/buscar/components/SearchResults.tsx` | AC2: empty state educativo |
| `frontend/app/buscar/page.tsx` | AC2+AC4: sugestões + auto-retry |
| `backend/search_pipeline.py` | AC4: auto-relaxation logic |
| `backend/filter.py` | AC3: filter_stats no return + AC4: relaxation retries |
| `backend/schemas.py` | AC3: filter_summary field + relaxation_level |
| `backend/routes/search.py` | AC3: include filter_stats when 0 results |

---

## Decisões Técnicas

- **Amarelo para 0 results** — Padrão UX: verde=sucesso, vermelho=erro, amarelo=atenção. "Sem oportunidades" é atenção, não sucesso.
- **Filter stats** — Transparência gera confiança. "O sistema buscou mas não encontrou" é muito melhor que "0 oportunidades" sem contexto.
- **Auto-relaxation** — Google Search faz isso: "Did you mean..." + resultados ampliados. Nunca retorne vazio se há dados.
- **3 níveis de relaxation** — Gradual, do mais preciso ao mais amplo. Cada nível é logged para analytics.

## Estimativa
- **Esforço:** 6-8h
- **Risco:** Baixo-Médio (UX changes + filter relaxation)
- **Squad:** @ux-design-expert (AC1+AC2+AC5) + @dev (AC3+AC4) + @qa (AC6)
