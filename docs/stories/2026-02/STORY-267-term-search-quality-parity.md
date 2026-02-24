# STORY-267 — Paridade de Qualidade: Busca por Termos vs. Busca por Setor

**Status:** DONE
**Sprint:** SEARCH-QUALITY
**Priority:** P1 — Core Search Quality
**Estimate:** 13 SP
**Squad:** team-bidiq-backend

---

## Contexto

O SmartLic oferece dois modos de busca: **por setor** (seleciona um dos 15 setores com keywords curadas) e **por termos livres** (o usuario digita termos customizados). Atualmente, a busca por termos herda toda a maquinaria do setor selecionado (LLM prompts, sinonimos, exclusoes, viability ranges, co-occurrence rules), mas essa maquinaria foi desenhada para setores, nao para termos livres.

### Problema Central

`setor_id` e **sempre obrigatorio** no request (default `"vestuario"`), e praticamente todos os layers de qualidade sao indexados por `ctx.sector`. Quando o usuario busca `"levantamento topografico"` com setor `vestuario`, o LLM pergunta "Isto e sobre Vestuario e Uniformes?" — uma pergunta semanticamente errada.

### Impacto

- Usuarios de termos livres recebem resultados com **ruido** (falsos positivos que seriam barrados por exclusoes) e **lacunas** (falsos negativos que o LLM descarta por serem "irrelevantes para o setor")
- A viabilidade (value_fit) usa ranges do setor errado
- Sinonimos e recovery (FLUXO 2) nao funcionam para termos customizados
- Co-occurrence rules e proximity filter do setor causam over-rejection

## Objetivo

Garantir que buscas por termos livres tenham **qualidade equivalente** as buscas por setor, adaptando os layers de classificacao, filtragem, e enriquecimento ao contexto real dos termos do usuario.

## Analise de Gaps (7 lacunas identificadas)

| # | Gap | Severidade | Descricao |
|---|-----|-----------|-----------|
| G1 | LLM orientado ao setor, nao aos termos | **CRITICA** | Zero-match, arbiter, e recovery usam nome do setor no prompt, nao os termos do usuario. Modo `"termos"` no `classify_contract_primary_match` e inalcancavel pois `ctx.sector` sempre resolve |
| G2 | Sinonimos sao sector-keyword-based | **ALTA** | `find_synonym_matches()` usa `setor_config.keywords` para lookup. Termos custom que nao estao no dict do setor nao tem expansao de sinonimos |
| G3 | Viability value_fit usa range do setor | **ALTA** | Busca por `"topografia"` em `vestuario` avalia viabilidade contra R$50k-R$2M. Sem range customizado, score e semanticamente errado |
| G4 | Exclusoes zeradas para vestuario + terms | **MEDIA** | Branch especifico em PrepareSearch (linha 841) zera `ctx.active_exclusions` quando `setor_id == "vestuario"` + custom terms. 80+ exclusoes desaparecem |
| G5 | Camada 1A max_contract_value do setor | **MEDIA** | Ceiling do setor (ex: R$5M vestuario) rejeita licitacoes validas se os termos nao pertencem aquele setor |
| G6 | Co-occurrence e proximity rules do setor | **MEDIA** | Rules curadas para o setor podem causar over-rejection de resultados validos para termos cross-sector |
| G7 | Nenhum feedback ao usuario sobre relaxation | **BAIXA** | Quando min_match_floor relaxa de N para 1, usuario nao sabe que resultados vieram de matching relaxado |

## Acceptance Criteria

### Fase 1 — LLM Term-Aware (G1 — CRITICA)

- [x] **AC1**: Criar funcao `_build_term_search_prompt(termos: list[str], objeto: str) -> str` em `llm_arbiter.py`
  - Prompt pergunta: "O objeto '{objeto}' e relevante para alguem buscando por: {termos}?"
  - Resposta: YES/NO com breve justificativa
  - Nao menciona nome do setor — foca exclusivamente nos termos do usuario
  - Reutiliza mesma estrutura de retorno (`LLMClassificationResult`)

- [x] **AC2**: Em `filter.py`, no path de zero-match (linha ~2618), quando `ctx.custom_terms` nao-vazio:
  - Chamar `classify_contract_primary_match` com `mode="termos"` e `termos_busca=ctx.custom_terms`
  - Garantir que `setor_name` e passado como `None` nesse path para ativar modo termos
  - Manter fallback = REJECT em caso de falha

- [x] **AC3**: Em `filter.py`, no path do LLM arbiter gray-zone (Camada 3A, linha ~2948), quando `ctx.custom_terms` nao-vazio:
  - Usar prompt term-aware em vez de sector-aware
  - `_arbiter_setor_name = None` quando custom_terms presentes
  - Passar `termos_busca=ctx.custom_terms` no call

- [x] **AC4**: Em `filter.py`, no path de LLM false-negative recovery (Camada 3B, linha ~3247), quando `ctx.custom_terms` nao-vazio:
  - Usar prompt term-aware para recovery
  - Nao usar sector keywords como base do recovery prompt

- [x] **AC5**: Testes unitarios para cada path LLM com termos custom:
  - `test_zero_match_uses_term_prompt_when_custom_terms()`
  - `test_arbiter_uses_term_prompt_when_custom_terms()`
  - `test_recovery_uses_term_prompt_when_custom_terms()`
  - Cada teste valida que o prompt enviado ao LLM contem os termos do usuario e NAO o nome do setor

### Fase 2 — Sinonimos para Termos Custom (G2)

- [x] **AC6**: Criar funcao `find_term_synonym_matches(custom_terms: list[str], objeto: str) -> list[str]` em `synonyms.py`
  - Busca sinonimos para cada termo custom (nao apenas sector keywords)
  - Usa dicionario existente de sinonimos + match reverso (se "jaleco" e sinonimo de "guarda-po" e usuario buscou "guarda-po", encontra matches de "jaleco")
  - Retorna lista de termos adicionais encontrados

- [x] **AC7**: Em `filter.py`, FLUXO 2 — Camada 2B, quando `ctx.custom_terms` nao-vazio:
  - Chamar `find_term_synonym_matches(ctx.custom_terms, objeto)` em vez de `find_synonym_matches(setor_keywords, ...)`
  - Manter mesma logica de auto-approve (2+ synonym matches)

- [x] **AC8**: Testes para synonym matching com termos custom:
  - `test_synonym_finds_reverse_match_for_custom_term()`
  - `test_synonym_recovery_uses_custom_terms_not_sector()`

### Fase 3 — Viability e Value Range (G3)

- [x] **AC9**: Em `viability.py`, quando `ctx.custom_terms` nao-vazio e usuario NAO tem `faixa_valor` no perfil:
  - Usar range generico amplo (ex: R$10k-R$50M) em vez do range do setor
  - Alternativamente, inferir range do setor mais proximo baseado nos termos (se 80%+ dos termos matcham keywords de um setor especifico, usar range desse setor)
  - Documentar a logica de fallback

- [x] **AC10**: Se usuario tem `faixa_valor_min`/`faixa_valor_max` no perfil (STORY-260), esse range SEMPRE prevalece (ja implementado, apenas validar teste)

### Fase 4 — Exclusoes e Filtros Contextuais (G4, G5, G6)

- [x] **AC11**: Em `search_pipeline.py` PrepareSearch, corrigir branch de exclusoes (linha ~841):
  - Quando `custom_terms` + `setor_id == "vestuario"`: aplicar exclusoes do setor parcialmente
  - Exclusoes que contem algum dos termos custom devem ser REMOVIDAS da lista (evitar auto-exclusao)
  - Exclusoes que nao tem relacao com os termos custom devem ser MANTIDAS
  - Exemplo: usuario busca "colete" → exclusao "colete salva-vidas" e removida, mas "servico de limpeza" e mantida

- [x] **AC12**: Em `filter.py`, Camada 1A — max_contract_value:
  - Quando `ctx.custom_terms` nao-vazio, desativar ceiling do setor
  - Se usuario tem `faixa_valor_max` no perfil, usar esse como ceiling
  - Caso contrario, nao aplicar ceiling (deixar viability assessment tratar)

- [x] **AC13**: Em `filter.py`, co-occurrence rules e proximity filter:
  - Quando `ctx.custom_terms` nao-vazio, desativar co-occurrence rules do setor
  - Quando `ctx.custom_terms` nao-vazio, desativar proximity context filter
  - Manter essas regras ATIVAS apenas para buscas por setor puro

- [x] **AC14**: Testes para cada ajuste de filtro contextual:
  - `test_exclusions_partial_for_vestuario_with_custom_terms()`
  - `test_max_value_ceiling_disabled_for_custom_terms()`
  - `test_co_occurrence_disabled_for_custom_terms()`
  - `test_proximity_filter_disabled_for_custom_terms()`

### Fase 5 — Feedback e Observabilidade (G7)

- [x] **AC15**: Incluir campo `match_relaxed: bool` no response de busca quando min_match_floor foi relaxado
  - Frontend pode exibir badge informativo: "Resultados com matching ampliado"
  - NAO bloquear resultados — apenas informar

- [x] **AC16**: Adicionar metricas Prometheus para quality tracking:
  - `smartlic_search_mode` label (`sector` vs `terms`) em metricas existentes
  - `smartlic_term_search_llm_accepts` / `smartlic_term_search_llm_rejects`
  - `smartlic_term_search_synonym_recoveries`

## Criterios de Aceite Globais

- [x] **AC17**: 0 regressoes nos 5131+ testes backend existentes (5408 passed, 5 skipped, 0 STORY-267 failures)
- [x] **AC18**: Feature flags para cada fase: `TERM_SEARCH_LLM_AWARE`, `TERM_SEARCH_SYNONYMS`, `TERM_SEARCH_VIABILITY_GENERIC`, `TERM_SEARCH_FILTER_CONTEXT`
  - Todas iniciam `False` (opt-in gradual)
  - Cada flag pode ser ativada independentemente
- [ ] **AC19**: Teste comparativo A/B manual: mesma busca com 3 termos, comparar resultados antes/depois em staging

## Arquivos Impactados

| Arquivo | Mudanca |
|---------|---------|
| `backend/llm_arbiter.py` | AC1: novo prompt term-aware |
| `backend/filter.py` | AC2-4, AC12-13: paths LLM, ceiling, co-occurrence, proximity |
| `backend/synonyms.py` | AC6: `find_term_synonym_matches()` |
| `backend/viability.py` | AC9: range generico para termos |
| `backend/search_pipeline.py` | AC11: exclusoes parciais |
| `backend/config.py` | AC18: feature flags |
| `backend/metrics.py` | AC16: metricas search_mode |
| `backend/schemas.py` | AC15: campo `match_relaxed` |
| `backend/tests/` | AC5, AC8, AC10, AC14, AC17: novos testes |

## Riscos e Mitigacoes

| Risco | Probabilidade | Impacto | Mitigacao |
|-------|--------------|---------|-----------|
| Prompt term-aware gera mais LLM calls (custo) | Media | Medio | Manter mesma logica de skip (keyword density >5% pula LLM). GPT-4.1-nano e barato |
| Desativar co-occurrence/proximity aumenta ruido | Media | Medio | Feature flags permitem rollback instantaneo. Monitorar metricas AC16 |
| Range generico de viabilidade e pouco informativo | Alta | Baixo | Incentivar usuarios a preencher faixa_valor no perfil (STORY-260) |
| Complexidade de manter dois paths (sector vs term) | Media | Alto | Encapsular logica em funcoes helper: `is_term_search(ctx)` centralizado |

## Notas de Implementacao

### Funcao helper central

```python
def is_term_search(ctx: SearchContext) -> bool:
    """True when user provided custom terms (regardless of setor_id)."""
    return bool(ctx.custom_terms)
```

Usar em TODOS os branching points para consistencia.

### Ordem de implementacao recomendada

1. **AC18** — Feature flags (prerequisito)
2. **Fase 1** (AC1-5) — LLM term-aware (maior impacto)
3. **Fase 4** (AC11-14) — Filtros contextuais (segundo maior impacto)
4. **Fase 2** (AC6-8) — Sinonimos
5. **Fase 3** (AC9-10) — Viability
6. **Fase 5** (AC15-16) — Observabilidade
7. **AC17, AC19** — Validacao final

### Referencia de codigo

- Zero-match path: `backend/filter.py:~2618`
- Arbiter gray-zone: `backend/filter.py:~2948`
- Recovery FLUXO 2: `backend/filter.py:~3247`
- Exclusions branch: `backend/search_pipeline.py:~841`
- Synonym lookup: `backend/synonyms.py:find_synonym_matches()`
- Viability value_fit: `backend/viability.py`
- LLM prompt builder: `backend/llm_arbiter.py:_build_zero_match_prompt()`

---

*Story criada por Morgan (PM) com analise de codebase profunda dos 7 gaps identificados.*
