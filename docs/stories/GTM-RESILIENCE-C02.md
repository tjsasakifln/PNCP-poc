# GTM-RESILIENCE-C02 -- Indicador de Confiabilidade por Resultado

| Campo | Valor |
|-------|-------|
| **Track** | C: Valorizacao de Percepcao |
| **Prioridade** | P1 |
| **Sprint** | 3 |
| **Estimativa** | 8-12 horas (backend schema + frontend UI) |
| **Gaps Cobertos** | UX-06 |
| **Dependencias** | GTM-RESILIENCE-C01 (copy baseline), GTM-FIX-028 (relevance_source infra) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

A investigacao (Frente 3, Gap UX-06) identificou que o sistema ja comunica a **origem da relevancia** de cada resultado via badges "Palavra-chave" (verde) e "Validado por IA" (azul) (GTM-FIX-028). Porem, o usuario nao consegue distinguir a **confianca** da classificacao: um resultado com 8% de term density (altissima relevancia keyword) recebe o mesmo badge verde que um com 5.1% (limiar minimo de auto-accept).

Da mesma forma, resultados classificados por LLM nao comunicam se a decisao foi "95% certeza" ou "55% talvez relevante". O pipeline ja calcula internamente a zona de term density (Camada 2 da classificacao, ver Frente 4 do report), mas essa informacao nao chega ao frontend.

### Estado Atual do Pipeline de Classificacao

```
Camada 2: Term Density Zoning
  >5%: AUTO-ACCEPT (relevance_source = "keyword")
  2-5%: LLM standard prompt (relevance_source = "llm_standard")
  1-2%: LLM conservative prompt (relevance_source = "llm_conservative")
  <1%: AUTO-REJECT
Camada 4: Zero-Match LLM (relevance_source = "llm_zero_match")
```

O frontend so recebe `relevance_source` como string enum. Nao recebe term density, confidence score, ou zona de classificacao.

## Problema

1. **Sem nivel de confianca** -- usuario nao sabe se pode confiar no resultado
2. **Badge binario** -- verde (keyword) ou azul (IA) e insuficiente para decisao
3. **Sem diferenciacao dentro da mesma zona** -- 8% density = 5.1% density para o usuario
4. **Zero match LLM indistinguivel** -- resultado que passou por zero-match (mais incerto) recebe mesmo badge "Validado por IA" que llm_standard (mais confiante)
5. **Impossivel ordenar por confianca** -- usuario nao pode priorizar resultados mais confiaveis

## Solucao

### Backend: Adicionar campo `confidence` ao schema

O backend ja calcula term density internamente em `filter.py`. O objetivo e expor um campo `confidence` normalizado na resposta:

| Zona | Term Density | relevance_source | confidence | Label |
|------|-------------|-------------------|------------|-------|
| Auto-accept | >5% | keyword | "high" | Alta confianca |
| LLM Standard | 2-5% | llm_standard | "medium" | Confianca media |
| LLM Conservative | 1-2% | llm_conservative | "low" | Confianca baixa |
| Zero-match | 0% | llm_zero_match | "low" | Avaliado por IA |

### Frontend: Badge de confianca com 3 niveis visuais

Adicionar um indicador visual ao lado do badge de relevance_source existente:

- **Alta** (verde forte): icone de escudo + "Alta confianca" -- tooltip "Este resultado tem alta densidade de termos relevantes para o setor"
- **Media** (amarelo): icone de escudo parcial + "Confianca media" -- tooltip "Relevancia confirmada por avaliacao de IA"
- **Baixa** (cinza): icone de interrogacao + "Avaliado por IA" -- tooltip "Resultado com relevancia possivel, verificado por inteligencia artificial"

### Ordenacao por confianca

Permitir que o usuario ordene resultados por confidence (high > medium > low) como opcao no seletor de ordenacao existente.

---

## Criterios de Aceitacao

### Backend

### AC1: Campo confidence no schema LicitacaoItem
- [ ] `LicitacaoItem` (backend schemas.py ou equivalente) inclui campo `confidence: Optional[Literal["high", "medium", "low"]] = None`
- [ ] Campo e do tipo `Optional` para backward compatibility (resultados antigos sem confidence)
- [ ] OpenAPI schema atualizado automaticamente via Pydantic

### AC2: filter.py popula confidence baseado em term density zone
- [ ] Resultados com `relevance_source == "keyword"` recebem `confidence = "high"`
- [ ] Resultados com `relevance_source == "llm_standard"` recebem `confidence = "medium"`
- [ ] Resultados com `relevance_source == "llm_conservative"` recebem `confidence = "low"`
- [ ] Resultados com `relevance_source == "llm_zero_match"` recebem `confidence = "low"`
- [ ] Resultados sem relevance_source (legacy) recebem `confidence = None`

### AC3: Testes backend para mapeamento confidence
- [ ] Teste unitario: keyword -> high
- [ ] Teste unitario: llm_standard -> medium
- [ ] Teste unitario: llm_conservative -> low
- [ ] Teste unitario: llm_zero_match -> low
- [ ] Teste unitario: None -> None (backward compat)
- [ ] Todos os testes passam sem regressao vs baseline (~45 pre-existentes)

### Frontend

### AC4: Tipo LicitacaoItem atualizado
- [ ] `frontend/app/types.ts` LicitacaoItem inclui `confidence?: "high" | "medium" | "low" | null`
- [ ] `npx tsc --noEmit --pretty` passa limpo

### AC5: Badge de confianca por resultado
- [ ] Cada resultado exibe badge de confianca ao lado dos badges existentes (relevance_source + data source)
- [ ] **Alta confianca**: badge verde com icone de escudo, texto "Alta confianca"
- [ ] **Confianca media**: badge amarelo/amber com icone de escudo parcial, texto "Confianca media"
- [ ] **Confianca baixa**: badge cinza com icone de interrogacao, texto "Avaliado por IA"
- [ ] Quando `confidence == null` (legacy), nenhum badge de confianca e exibido (graceful degradation)

### AC6: Tooltip explicativo por nivel
- [ ] Badge de confianca tem `title` (tooltip nativo) com explicacao:
  - High: "Alta densidade de termos relevantes para o setor selecionado"
  - Medium: "Relevancia confirmada por avaliacao de inteligencia artificial"
  - Low: "Resultado com relevancia possivel, verificado por IA. Recomendamos revisar manualmente"

### AC7: Diferenciacao visual clara entre 3 niveis
- [ ] Os 3 niveis sao visualmente distinguiveis por cor E icone (nao depender apenas de cor para acessibilidade)
- [ ] Contraste adequado em light mode e dark mode
- [ ] Badge de confianca nao conflita visualmente com badges existentes (relevance_source, data source, UF)

### AC8: Ordenacao por confianca
- [ ] Seletor de ordenacao de resultados inclui opcao "Confianca" (ou "Mais confiaveis primeiro")
- [ ] Ordenacao: high > medium > low > null
- [ ] Dentro do mesmo nivel de confianca, manter ordenacao anterior (por valor ou relevance_score)

### AC9: Contagem por nivel no header
- [ ] Header de resultados mostra contagem por nivel: ex. "42 resultados: 28 alta, 10 media, 4 baixa"
- [ ] Contagem so aparece quando ha pelo menos 1 resultado com confidence != null
- [ ] Quando todos sao null (backend antigo), contagem nao aparece (backward compat)

### AC10: Testes frontend
- [ ] Teste: badge "Alta confianca" renderizado quando confidence="high"
- [ ] Teste: badge "Confianca media" renderizado quando confidence="medium"
- [ ] Teste: badge "Avaliado por IA" renderizado quando confidence="low"
- [ ] Teste: nenhum badge quando confidence=null
- [ ] Teste: tooltip correto por nivel
- [ ] Teste: ordenacao por confianca funciona corretamente
- [ ] Teste: contagem no header reflete distribuicao real
- [ ] Nenhum novo teste failure vs baseline (33 frontend pre-existentes)

### AC11: Acessibilidade
- [ ] Badges tem `aria-label` descritivo (ex: "Confianca alta na relevancia deste resultado")
- [ ] Tooltips acessiveis via teclado (focusable)
- [ ] Cores nao sao unico diferenciador (icones distintos por nivel)

---

## Arquivos Afetados

### Backend

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `backend/schemas.py` ou modelo equivalente | Adicionar campo `confidence` ao LicitacaoItem |
| `backend/filter.py` | Mapear relevance_source -> confidence ao final da classificacao |
| `backend/tests/test_filter.py` | 5+ novos testes de mapeamento |

### Frontend

| Arquivo | Tipo de Mudanca |
|---------|----------------|
| `frontend/app/types.ts` | Adicionar `confidence` ao LicitacaoItem |
| `frontend/app/buscar/components/SearchResults.tsx` | Badge de confianca, contagem header, opcao de sort |
| `frontend/app/components/LicitacoesPreview.tsx` | Badge de confianca (se usado neste componente) |
| `frontend/__tests__/llm-zero-match.test.tsx` | Atualizar/expandir testes |
| `frontend/__tests__/buscar/search-results-confidence.test.tsx` | Novo arquivo de testes |

---

## Dependencias

| Dependencia | Tipo | Motivo |
|-------------|------|--------|
| **GTM-RESILIENCE-C01** | Soft | Copy de confianca deve seguir tom estabelecido em C-01 (sem contagem de fontes) |
| **GTM-FIX-028** | Hard (ja completo) | Infra de `relevance_source` ja existe -- esta story adiciona `confidence` como camada acima |
| **Frente 4 (CL-02)** futura | Soft | Quando LLM output estruturado vier (Track D), confidence pode ser refinado com score numerico real |

---

## Riscos e Mitigacoes

| Risco | Probabilidade | Mitigacao |
|-------|---------------|-----------|
| Backend nao expoe term density diretamente | Media | Usar mapeamento via relevance_source (proxy suficiente para v1) |
| LLM confidence real != zone-based proxy | Alta | Documentar como v1; Track D-02 trara confidence real do LLM |
| Badge overload visual nos resultados | Media | Design review: limitar a 1 badge de confianca, integrar com badge existente de relevance_source |

---

## Definition of Done

- [ ] Campo `confidence` presente na resposta da API `/buscar`
- [ ] Badge de confianca visivel em cada resultado (3 niveis visuais)
- [ ] Tooltip explicativo por nivel
- [ ] Ordenacao por confianca funcional
- [ ] Contagem por nivel no header de resultados
- [ ] `npm run build` e `pytest` passam sem novos failures
- [ ] `npx tsc --noEmit --pretty` limpo
- [ ] Dark mode funcional em badges de confianca
- [ ] Backward compatible: resultados sem confidence (legacy) funcionam normalmente
