# GTM-RESILIENCE-D03 — Co-occurrence Negative Patterns para Redução de Falsos Positivos

| Campo | Valor |
|-------|-------|
| **Track** | D — Classificação de Precisao |
| **Prioridade** | P1 |
| **Sprint** | 2 |
| **Estimativa** | 4-5 horas |
| **Gaps Endereçados** | CL-08 |
| **Dependências** | Nenhuma (extensão do filter.py existente) |
| **Autor** | @pm (Morgan) |
| **Data** | 2026-02-18 |

---

## Contexto

O sistema de exclusão atual em `filter.py` opera com uma lista flat de ~600 termos. Quando um termo de exclusão e detectado, a licitação e rejeitada independentemente do contexto. Isso e insuficiente para padrões onde a combinação de termos determina a relevância, nao os termos individuais.

### Exemplos reais do problema:

| Texto do Objeto | Resultado Atual | Resultado Correto | Por quê |
|-----------------|-----------------|-------------------|---------|
| "Uniformização de fachada do prédio" | **ACEITO** (keyword "uniform*") | REJEITADO | Nao e vestuário, e pintura/reforma |
| "Padronização visual e identidade do órgão" | **ACEITO** ("padronização" ambíguo) | REJEITADO | Nao e vestuário, e design/branding |
| "Uniforme escolar + material didático" | **ACEITO** (keyword "uniforme") | ACEITO | Correto — e vestuário |
| "Uniformização de procedimentos internos" | **ACEITO** (keyword "uniform*") | REJEITADO | Nao e vestuário, e processo/norma |
| "Serviço de costura de cortinas" | **ACEITO** (keyword "costura") | REJEITADO | Nao e vestuário, e decoração |

O padrão: keyword_A + contexto_negativo_B (sem sinal_positivo_C) = falso positivo. A exclusão flat nao captura isso.

## Problema

A lista flat de exclusões nao detecta combinações de termos que invalidam a relevância. "Uniformização" e keyword valida para vestuário, mas "uniformização + fachada" nao e vestuário. Sem co-occurrence rules, esses falsos positivos passam pelo filtro de keywords e sao aceitos automaticamente (density >5%) sem sequer consultar o LLM.

Esses FPs sao particularmente danosos porque:
1. Aparecem no topo (alta density = alta confiança aparente)
2. Nao passam pelo LLM (auto-accept zone)
3. Degradam a percepção de qualidade do produto inteiro

## Solução

Implementar engine de regras de co-occurrence no `filter.py` que avalia combinações de termos antes do auto-accept. Cada regra define: keyword trigger + contexto negativo + sinais positivos que anulam o negativo. Puramente determinístico, zero custo de LLM.

### Lógica:

```
SE keyword_match AND any(negative_context) AND NOT any(positive_signal):
    REJEITAR com motivo "co-occurrence: {keyword} + {negative_context}"
SE keyword_match AND any(negative_context) AND any(positive_signal):
    ACEITAR (sinal positivo anula o negativo)
SE keyword_match AND NOT any(negative_context):
    Fluxo normal (density zone → LLM se necessário)
```

### Exemplo de regra para setor "vestuario":

```yaml
co_occurrence_rules:
  - trigger: "uniform"  # regex prefix match
    negative_contexts:
      - "fachada"
      - "pintura"
      - "identidade visual"
      - "procedimento"
      - "processo"
      - "norma"
      - "padrao"
    positive_signals:
      - "textil"
      - "epi"
      - "costura"
      - "algodao"
      - "tecido"
      - "confeccao"
      - "tamanho"
      - "vestimenta"
```

---

## Acceptance Criteria

### AC1 — Schema de Regras de Co-occurrence
- [ ] Novo campo `co_occurrence_rules` em `sectors_data.yaml` para cada setor
- [ ] Cada regra contém: `trigger` (str, regex-safe), `negative_contexts` (list[str]), `positive_signals` (list[str])
- [ ] Todos os 3 campos obrigatórios por regra (positive_signals pode ser lista vazia, significando que nao ha rescue)
- [ ] Validação no load: trigger deve ser subset dos keywords do setor (senao WARNING no log)
- [ ] Setor `vestuario` configurado com pelo menos 5 regras cobrindo os FP conhecidos

### AC2 — Engine de Co-occurrence no filter.py
- [ ] Nova função `check_co_occurrence(texto: str, rules: list[CoOccurrenceRule], setor_id: str) -> tuple[bool, str | None]`
- [ ] Retorna `(True, motivo)` se co-occurrence negativo detectado (bid deve ser rejeitada)
- [ ] Retorna `(False, None)` se nenhum co-occurrence detectado (bid segue fluxo normal)
- [ ] Matching usa mesma normalização Unicode existente em filter.py (remove acentos, lowercase)
- [ ] Matching usa word boundary para triggers e negative_contexts (evitar false match parcial)
- [ ] Positive signals usam substring match (mais permissivo — qualquer menção salva a bid)

### AC3 — Posição no Pipeline
- [ ] Co-occurrence check executa DEPOIS do keyword match e ANTES da density zone
- [ ] Se co-occurrence detectado, bid e rejeitada MESMO que density >5% (override do auto-accept)
- [ ] Bid rejeitada por co-occurrence NAO vai para LLM (economia de custo)
- [ ] Posição no pipeline de 4 camadas:

```
Camada 0: Pre-Filter (UF, data, status)
Camada 1A: Exclusion check (~600 termos)
Camada 1B: Keyword match (~150+ por setor)
>>> NOVO: Camada 1B.5: Co-occurrence check <<<
Camada 1C: Context validation
Camada 2: Term Density Zoning → LLM
Camada 3: Red Flags
Camada 4: Zero-Match LLM
```

### AC4 — Rejection Tracking
- [ ] Bids rejeitadas por co-occurrence recebem `rejection_reason="co_occurrence"` e `rejection_detail="trigger:{trigger} + negative:{context_found}"`
- [ ] Métrica logada por busca: `co_occurrence_rejections` (contagem)
- [ ] Métrica por setor: `co_occurrence_rejections_by_sector` (para tuning)
- [ ] Rejeições de co-occurrence incluídas no filter stats existente (`filter_stats_tracker`)

### AC5 — Regras para Setor Vestuário (Piloto)
- [ ] Regra 1: `uniform*` + `(fachada|pintura|reforma|revestimento)` - `(textil|epi|costura|tecido)`
- [ ] Regra 2: `uniform*` + `(procedimento|processo|norma|regulamento|protocolo)` - `(vestimenta|roupa|fardamento)`
- [ ] Regra 3: `uniform*` + `(identidade visual|comunicacao visual|sinalizacao)` - `(camisa|camiseta|jaleco)`
- [ ] Regra 4: `costura` + `(cortina|estofado|tapecaria|bandeira|toldo)` - `(uniforme|roupa|vestimenta)`
- [ ] Regra 5: `padronizacao` + `(visual|layout|sistema|software|digital)` - `(vestuario|textil|confeccao)`
- [ ] Cada regra testada com pelo menos 2 exemplos reais (1 que rejeita, 1 que positive_signal salva)

### AC6 — Regras para Outros Setores (Estrutura)
- [ ] Setor `saude` com pelo menos 2 regras (ex: "material + (construção|elétrico) - (hospitalar|cirúrgico)")
- [ ] Setor `ti` com pelo menos 2 regras (ex: "sistema + (hidráulico|elétrico|incêndio) - (informação|software|digital)")
- [ ] Demais setores: campo `co_occurrence_rules: []` (vazio) para aceitar regras futuras sem mudança de schema
- [ ] Documentação inline em sectors_data.yaml explicando como adicionar regras para novos setores

### AC7 — Zero Custo de LLM
- [ ] Co-occurrence check e 100% determinístico (regex + set lookup)
- [ ] Nenhuma chamada de API externa durante co-occurrence evaluation
- [ ] Performance: check de co-occurrence < 1ms por bid (medido e logado no p95)
- [ ] Nao altera o budget de LLM calls existente

### AC8 — Feature Flag
- [ ] `CO_OCCURRENCE_RULES_ENABLED` env var (default `true`)
- [ ] Quando `false`, pipeline pula Camada 1B.5 e segue direto para density zone
- [ ] Flag verificada no runtime (nao na importação)
- [ ] Adicionada ao `_FEATURE_FLAG_REGISTRY` existente

### AC9 — Testes
- [ ] Teste unitário: "Uniformização de fachada" rejeitado por co-occurrence (vestuario)
- [ ] Teste unitário: "Uniforme escolar de algodão" NAO rejeitado (positive_signal "algodao" salva)
- [ ] Teste unitário: "Uniformização de procedimentos" rejeitado (vestuario)
- [ ] Teste unitário: "Costura de cortinas decorativas" rejeitado (vestuario)
- [ ] Teste unitário: "Costura de uniformes em tecido" NAO rejeitado (positive_signals salvam)
- [ ] Teste unitário: bid com density >5% MAS co-occurrence negativo e rejeitada (override)
- [ ] Teste unitário: setor sem regras (lista vazia) nao causa erro
- [ ] Teste unitário: positive_signals vazio significa que nao ha rescue (sempre rejeita se negative encontrado)
- [ ] Teste unitário: normalização Unicode funciona (acentos ignorados)
- [ ] Teste unitário: word boundary impede "uniformização" de ser matched por "forma" (substring)

---

## Arquivos Impactados

| Arquivo | Mudança |
|---------|---------|
| `backend/sectors_data.yaml` | Novo campo `co_occurrence_rules` em cada setor |
| `backend/sectors.py` | Parser para `co_occurrence_rules`, modelo `CoOccurrenceRule` |
| `backend/filter.py` | Nova função `check_co_occurrence()`, integração na Camada 1B.5 |
| `backend/filter_stats.py` | Métrica `co_occurrence_rejections` |
| `backend/config.py` | `CO_OCCURRENCE_RULES_ENABLED` flag |
| `backend/tests/test_co_occurrence.py` | **NOVO** — 10+ testes unitários |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Regras muito agressivas causam falsos negativos | Media | Medio | Positive signals como escape hatch + feature flag |
| Manutenção manual de regras não escala | Media | Baixo | Formato YAML simples + documentação inline |
| Regex performance com muitas regras | Baixa | Baixo | Regras compiladas uma vez no startup, <1ms/bid |
| Conflito com exclusion list existente | Baixa | Baixo | Co-occurrence roda DEPOIS da exclusion (complementar, nao substitutivo) |

---

## Definition of Done

- [ ] Todos os 9 ACs verificados e passando
- [ ] Nenhuma regressão nos testes existentes de filter.py
- [ ] Pelo menos 5 FP conhecidos de vestuário eliminados pelas regras
- [ ] Zero custo adicional de LLM confirmado
- [ ] Performance <1ms/bid no p95 confirmada
- [ ] Feature flag permite desabilitar sem deploy
- [ ] Code review aprovado por @architect
