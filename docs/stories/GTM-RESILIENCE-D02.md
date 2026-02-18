# GTM-RESILIENCE-D02 — LLM Output Estruturado com Evidências e Re-ranking

| Campo | Valor |
|-------|-------|
| **Track** | D — Classificação de Precisao |
| **Prioridade** | P1 |
| **Sprint** | 3 |
| **Estimativa** | 5-7 horas |
| **Gaps Endereçados** | CL-02, CL-05 |
| **Dependências** | Nenhuma (refactor interno do llm_arbiter.py) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

O LLM arbiter atual (`llm_arbiter.py`) opera com `max_tokens=1`, forçando uma resposta binária SIM/NAO. Não há confiança, evidência, motivo de exclusão ou possibilidade de re-ranking. Isso gera três problemas concretos:

1. **Impossibilidade de auditoria**: Quando o LLM rejeita uma licitação, nao sabemos por que. O QA sample de 10% nao tem informação para avaliar qualidade.
2. **Sem re-ranking**: Licitações com 95% de confiança e 51% de confiança recebem o mesmo tratamento (SIM). O usuario vê resultados mediocres misturados com excelentes.
3. **Sem evidência para o usuario**: O badge "Validado por IA" (frontend) nao explica o que a IA detectou. O usuario nao pode avaliar se a classificação faz sentido.

**Custo atual**: ~R$ 0.00002/classificação (1 token output)
**Custo projetado**: ~R$ 0.00007/classificação (5-10 tokens output) = +R$ 0.01/mês com 1000 buscas/dia

## Problema

A classificação binária SIM/NAO impede auditoria de decisões, impossibilita ordenação por confiança, e nao fornece transparência ao usuario sobre o motivo da classificação. O sistema descarta oportunidades ambíguas (confiança 55%) junto com irrelevantes (confiança 5%) sem distinção.

## Solução

Migrar o LLM arbiter de resposta binária (1 token) para output JSON estruturado com schema Pydantic, incluindo classe, confiança percentual, evidências textuais e motivo de exclusão. Implementar re-ranking por confiança nos resultados.

### Schema proposto:

```python
class LLMClassification(BaseModel):
    classe: Literal["SIM", "NAO"]         # Decisão binária mantida
    confianca: int = Field(ge=0, le=100)  # Confiança 0-100%
    evidencias: list[str] = Field(max_length=3)  # Max 3 trechos literais do texto
    motivo_exclusao: Optional[str] = None # Preenchido apenas quando NAO
    precisa_mais_dados: bool = False      # Flag para item inspection (D-01)
```

### Impacto no pipeline:

```
ANTES:  LLM → SIM/NAO → accept/reject
DEPOIS: LLM → {classe, confiança, evidências} → accept(score)/reject(reason) → sort by score
```

---

## Acceptance Criteria

### AC1 — Schema de Output Estruturado
- [ ] Novo modelo Pydantic `LLMClassification` em `llm_arbiter.py` com campos: `classe`, `confianca`, `evidencias`, `motivo_exclusao`, `precisa_mais_dados`
- [ ] `classe`: Literal["SIM", "NAO"] (mantém decisão binária como base)
- [ ] `confianca`: int 0-100 (percentual de certeza)
- [ ] `evidencias`: list[str] com max 3 items, cada um max 100 chars (trechos literais do texto da licitação)
- [ ] `motivo_exclusao`: Optional[str] max 200 chars, preenchido somente quando classe="NAO"
- [ ] `precisa_mais_dados`: bool, True quando LLM detecta que descrição e insuficiente para decidir

### AC2 — Prompt Atualizado
- [ ] Prompt do LLM reformulado para solicitar JSON com o schema definido
- [ ] `max_tokens` aumentado de 1 para 150 (acomoda JSON + evidências)
- [ ] Prompt inclui instrução explicita: "Extraia evidências como CITAÇÕES LITERAIS do texto do objeto, não parafraseie"
- [ ] Prompt inclui instrução: "confianca = 100 se todas as keywords primárias presentes, 50 se ambíguo, 0 se claramente fora do setor"
- [ ] Response format configurado como `response_format={"type": "json_object"}` na chamada OpenAI

### AC3 — Parser com Fallback Robusto
- [ ] Resposta JSON parseada via `LLMClassification.model_validate_json()`
- [ ] Se JSON inválido (parse error): fallback para detecção de "SIM"/"NAO" no texto raw (comportamento atual preservado)
- [ ] Se timeout ou erro de API: `LLMClassification(classe="NAO", confianca=0, evidencias=[], motivo_exclusao="LLM indisponível")` — mantém fallback=REJECT
- [ ] Log WARNING em qualquer fallback com o raw response para debugging
- [ ] Métrica: `llm_structured_parse_success_rate` logada por busca

### AC4 — Scoring de Confiança
- [ ] Cada licitação aceita (classe="SIM") recebe campo `confidence_score` (0-100)
- [ ] Licitações aceitas por keyword (density >5%) recebem `confidence_score=95` (alta certeza)
- [ ] Licitações aceitas por LLM usam o `confianca` retornado pelo modelo
- [ ] Licitações aceitas por zero-match LLM usam `confianca` com cap de 70 (nunca >70 para zero-match)
- [ ] Campo `confidence_score` adicionado ao dict de cada licitação no pipeline

### AC5 — Re-ranking por Confiança
- [ ] Resultados da busca ordenados por `confidence_score` DESC antes de retornar ao frontend
- [ ] Licitações com `confidence_score` >= 80 aparecem primeiro (alta confiança)
- [ ] Licitações com `confidence_score` 50-79 aparecem depois (media confiança)
- [ ] Licitações com `confidence_score` < 50 aparecem por último (baixa confiança)
- [ ] Dentro de cada faixa, ordenação por valor estimado DESC (maior valor primeiro)
- [ ] Re-ranking acontece em `search_pipeline.py` DEPOIS de todos os filtros

### AC6 — Evidências para Auditoria
- [ ] Cada licitação aceita pelo LLM carrega campo `llm_evidence: list[str]` com as evidências extraídas
- [ ] Cada licitação rejeitada pelo LLM carrega campo `llm_rejection_reason: str`
- [ ] Evidências sao trechos LITERAIS do texto — validação: cada evidência deve ser substring de `objetoCompra` (se nao for, loggar WARNING de possível hallucination e descartar a evidência)
- [ ] QA audit (10% sampling existente) agora inclui evidências e confiança no log

### AC7 — Exposição para Frontend
- [ ] Campo `confidence_score` incluído no response JSON de `/buscar` para cada licitação
- [ ] Campo `llm_evidence` incluído no response JSON (lista de strings)
- [ ] Frontend pode usar `confidence_score` para badges visuais (AC separado em Track C, nao implementar UI aqui)
- [ ] BuscaResponse schema em `schemas.py` atualizado com campos opcionais

### AC8 — Compatibilidade e Feature Flag
- [ ] `LLM_STRUCTURED_OUTPUT_ENABLED` env var (default `true`)
- [ ] Quando `false`, arbiter usa comportamento antigo (max_tokens=1, SIM/NAO)
- [ ] Transição gradual: pode rodar old e new em paralelo por feature flag
- [ ] Cache key do arbiter atualizado para incluir versão do prompt (evitar cache hits com formato antigo)

### AC9 — Monitoramento de Custo
- [ ] Métrica logada por busca: `llm_tokens_input`, `llm_tokens_output`, `llm_cost_estimated`
- [ ] Custo estimado calculado com pricing do gpt-4.1-nano (input: $0.10/1M, output: $0.40/1M)
- [ ] Alert threshold: se custo medio por busca > R$ 0.10, log WARNING
- [ ] Comparação logada: custo anterior (1 token) vs novo (N tokens) por busca

### AC10 — Testes
- [ ] Teste unitário: `LLMClassification` valida JSON correto com todos os campos
- [ ] Teste unitário: `LLMClassification` rejeita confiança fora de 0-100
- [ ] Teste unitário: parser fallback funciona quando LLM retorna texto plain em vez de JSON
- [ ] Teste unitário: evidência que nao e substring do objeto e descartada com WARNING
- [ ] Teste unitário: re-ranking ordena por confidence DESC, depois valor DESC
- [ ] Teste unitário: zero-match confidence capped em 70
- [ ] Teste unitário: feature flag `false` usa comportamento antigo (max_tokens=1)
- [ ] Teste de integração: busca com 5 bids, 3 aceitas pelo LLM, resultados ordenados por confiança

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/llm_arbiter.py` | Schema `LLMClassification`, prompts atualizados, parser JSON, scoring |
| `backend/filter.py` | Integração de `confidence_score` e `llm_evidence` no dict de cada bid |
| `backend/search_pipeline.py` | Re-ranking por `confidence_score` antes de retornar resultados |
| `backend/schemas.py` | Campos `confidence_score`, `llm_evidence` em BuscaResponse items |
| `backend/config.py` | `LLM_STRUCTURED_OUTPUT_ENABLED` flag |
| `backend/tests/test_llm_arbiter.py` | Testes para structured output, fallback, scoring |
| `backend/tests/test_reranking.py` | **NOVO** — testes de ordenação por confiança |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| LLM retorna JSON malformado | Media | Baixo | Fallback robusto para SIM/NAO detection no raw text |
| Custo aumenta mais que esperado | Baixa | Baixo | Monitoramento por busca + alert threshold |
| Evidências hallucinated (nao do texto) | Media | Medio | Validação substring + descarte com log |
| Latência aumenta (mais tokens) | Baixa | Baixo | gpt-4.1-nano streaming, overhead <50ms |
| Cache invalidation com novo formato | Media | Baixo | Versão no cache key separa old/new |

---

## Definition of Done

- [ ] Todos os 10 ACs verificados e passando
- [ ] Nenhuma regressão nos testes existentes de llm_arbiter.py e filter.py
- [ ] Coverage do código modificado >= 80%
- [ ] Custo por classificação medido e dentro do budget (<R$ 0.0001)
- [ ] Feature flag permite rollback instantâneo sem deploy
- [ ] QA audit log agora inclui evidências e confiança
- [ ] Code review aprovado por @architect
