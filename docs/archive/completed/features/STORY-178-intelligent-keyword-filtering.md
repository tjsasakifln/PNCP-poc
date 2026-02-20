# STORY-178: Filtragem Inteligente por Termos — Busca Contextual com Correspondência Mínima

**Status:** Aprovada (Consenso Unânime — 7/7 agentes)
**Prioridade:** P0 - Crítica (impacta credibilidade do produto)
**Estimativa:** 8 story points (1 sprint)
**Tipo:** Enhancement (Brownfield)
**Épico:** Qualidade de Busca & Relevância
**Revisão:** v2.1 — Aprovada após 2 rodadas de revisão multi-agente (7 agentes, 19 critiques → 0 blocking)

---

## Contexto

### Problema Reportado

> "Coloco no campo 'projeto, levantamento topográfico, estudos geotécnicos, terraplenagem, drenagem, pavimentação' e traz ainda outras licitações fora da engenharia. Só por colocar a palavra 'projeto' ele traz qualquer coisa que tem essa palavra sem refinar se é serviço de engenharia."

### Análise Técnica da Causa Raiz

O sistema atual possui **3 problemas estruturais** no modo de busca por termos customizados (`termos_busca`):

| # | Problema | Impacto | Localização |
|---|---------|---------|-------------|
| 1 | **Lógica OR pura** — cada termo é independente; basta 1 match para incluir | "projeto" sozinho traz qualquer licitação com essa palavra | `filter.py:match_keywords()` — retorna `True` se `len(matched) > 0` |
| 2 | **Sem exclusões para termos custom** — exclusions e context_required são desabilitados | Sem proteção contra falsos positivos | `main.py:1390-1391` — `exclusions=set()` e `context_required=None` |
| 3 | **Sem relevância** — todos os resultados têm peso igual | Licitação com 1 match no mesmo nível de uma com 5 | Sort padrão é por data; `calcular_relevancia()` em `ordenacao.py` é placeholder |

### Comportamento Atual vs Esperado

**Busca:** `projeto, levantamento topográfico, estudos geotécnicos, terraplenagem, drenagem, pavimentação`

| Licitação | Hoje | Esperado |
|-----------|------|----------|
| "Projeto de levantamento topográfico e terraplenagem na BR-101" | Inclusa (match "projeto") | Inclusa — score alto, 3 termos matcham |
| "Projeto básico de rede de computadores" | Inclusa (match "projeto") | **Excluída** — apenas 1 de 6 termos matcha |
| "Terraplenagem, drenagem e pavimentação da Rodovia ES-060" | Inclusa | Inclusa — score alto, 3 termos matcham |

---

## Princípio de Design: Agnóstico de Setor

> **Decisão Arquitetural:** A solução NÃO usa listas de "termos genéricos" nem heurísticas baseadas em comprimento de caractere. Estes mecanismos codificam viés de setor e falham para indústrias onde "obra", "sistema", "equipamento" ou "material" são termos centrais.
>
> Em vez disso, usamos **correspondência mínima adaptativa** — um mecanismo puramente matemático que exige que múltiplos termos matchem quando o usuário fornece múltiplos termos. Isso funciona identicamente para engenharia, saúde, TI, alimentação, segurança, limpeza, ou qualquer outro ramo.

---

## Solução Proposta

### Arquitetura: Matching em 3 Camadas

```
Camada 1: Parsing Inteligente de Termos
├── Vírgula como delimitador de frases compostas
├── Espaço como fallback quando não há vírgulas (backward compatible)
├── Stopword removal apenas em termos individuais
└── Deduplicação e normalização

Camada 2: Matching com Correspondência Mínima
├── match_keywords() inalterado (preserva 60+ callers)
├── Nova função score_relevance() separada
├── Minimum Match Floor adaptativo ao número de termos
└── Exclusões do setor re-habilitadas como safety net

Camada 3: Ranking por Relevância
├── Score = matched_count / total_terms + phrase_bonus
├── Frontend envia ordenacao=relevancia (não override do backend)
├── Indicadores visuais positivos apenas (sem badges negativos)
└── Degradação graciosa quando poucos resultados passam o filtro
```

---

## Fórmula de Relevância (Exata)

### Score

```
base_score = matched_count / total_terms
phrase_bonus = 0.15 × count_of_multi_word_terms_that_matched_as_phrases
relevance_score = min(1.0, base_score + phrase_bonus)
```

**Guarda:** Se `total_terms == 0`, retorna `0.0`.

### Minimum Match Floor (Critério de Inclusão)

Uma licitação é incluída se **qualquer** condição for verdadeira:

```
Condição A: matched_count >= min_matches
  onde min_matches = max(1, min(ceil(total_terms / 3), 3))

Condição B: pelo menos 1 frase multi-palavra matchou como sequência exata
  (phrase match é sinal forte que sobrepõe o minimum match floor)
```

**Tabela de min_matches por quantidade de termos:**

| total_terms | min_matches | Justificativa |
|-------------|-------------|---------------|
| 1 | 1 | Comportamento idêntico ao atual |
| 2 | 1 | Comportamento idêntico ao atual |
| 3 | 1 | Comportamento idêntico ao atual |
| 4-6 | 2 | Exige sobreposição mínima — resolve o caso reportado |
| 7-9 | 3 (cap) | Evita exclusão excessiva em buscas amplas |
| 10+ | 3 (cap) | Cap mantém recall para buscas de equipamentos/insumos |

### Exemplos Trabalhados (com cálculos intermediários)

**Cenário A: Caso reportado (engenharia rodoviária, 6 termos)**
```
Input: "projeto, levantamento topográfico, estudos geotécnicos, terraplenagem, drenagem, pavimentação"
total_terms = 6, min_matches = max(1, min(ceil(6/3), 3)) = max(1, min(2, 3)) = 2

Licitação: "Projeto de levantamento topográfico e terraplenagem na BR-101"
  matched = ["projeto", "levantamento topográfico", "terraplenagem"] → matched_count = 3
  phrase_matches = ["levantamento topográfico"] → 1 frase
  base_score = 3/6 = 0.500
  phrase_bonus = 0.15 × 1 = 0.150
  relevance_score = min(1.0, 0.500 + 0.150) = 0.650
  matched_count(3) >= min_matches(2) → INCLUÍDA ✓

Licitação: "Projeto básico de rede de computadores"
  matched = ["projeto"] → matched_count = 1
  base_score = 1/6 = 0.167
  phrase_bonus = 0
  relevance_score = 0.167
  matched_count(1) < min_matches(2) → NÃO incluída por Condição A
  Nenhuma frase multi-palavra matchou → NÃO incluída por Condição B
  → EXCLUÍDA ✓ (resolve o problema reportado)

Licitação: "Terraplenagem, drenagem e pavimentação da Rodovia ES-060"
  matched = ["terraplenagem", "drenagem", "pavimentação"] → matched_count = 3
  base_score = 3/6 = 0.500
  relevance_score = 0.500
  matched_count(3) >= min_matches(2) → INCLUÍDA ✓
```

**Cenário B: Busca simples (1 termo, backward compatible)**
```
Input: "jaleco"
total_terms = 1, min_matches = 1

Licitação: "Aquisição de jaleco hospitalar"
  matched_count = 1, base_score = 1/1 = 1.0 → INCLUÍDA ✓
  Sem mudança funcional.
```

**Cenário C: Busca ampla de equipamentos médicos (20 termos)**
```
Input: "desfibrilador, monitor multiparâmetro, bomba de infusão, ..."  (20 termos)
total_terms = 20, min_matches = max(1, min(ceil(20/3), 3)) = 3 (cap)

Licitação: "Aquisição de desfibrilador e monitor multiparâmetro"
  matched_count = 2, base_score = 2/20 = 0.10
  matched_count(2) < min_matches(3) → NÃO incluída por Condição A
  "monitor multiparâmetro" é frase multi-palavra que matchou → INCLUÍDA por Condição B ✓
  relevance_score = min(1.0, 0.10 + 0.15) = 0.25

Licitação: "Aquisição de desfibrilador cardíaco"
  matched_count = 1 < min_matches(3) → NÃO por A
  Nenhuma frase multi-palavra → NÃO por B
  → EXCLUÍDA (resultado muito parcial com 1/20 termos)
  → Aparece na zona "ocultos" com opção de expandir
```

**Cenário D: "Construção" é específico para construtora**
```
Input: "construção de muro, alvenaria, fundação"
total_terms = 3, min_matches = 1

Licitação: "Construção de muro de arrimo com fundação profunda"
  matched = ["construção de muro", "fundação"] → matched_count = 2
  phrase_matches = ["construção de muro"] → 1 frase
  base_score = 2/3 = 0.667
  phrase_bonus = 0.15
  relevance_score = 0.817 → INCLUÍDA ✓
  Nota: "construção" NÃO é penalizado. Nenhum termo recebe peso diferenciado.
```

**Cenário E: Alimentação escolar**
```
Input: "fornecimento de refeição, marmita, alimentação escolar"
total_terms = 3, min_matches = 1

Licitação: "Fornecimento de refeições para merenda escolar"
  matched = ["fornecimento de refeição"] → matched_count = 1 (via plural match)
  phrase_matches = ["fornecimento de refeição"] → 1 frase
  base_score = 1/3 = 0.333, phrase_bonus = 0.15
  relevance_score = 0.483 → INCLUÍDA ✓
  Nota: "fornecimento" NÃO é penalizado (não existe lista de genéricos).
```

**Cenário F: TI / Software**
```
Input: "sistema, software, licença"
total_terms = 3, min_matches = 1

Licitação: "Aquisição de licença de software para gestão"
  matched = ["sistema"? NÃO, "software"? SIM, "licença"? SIM] → matched_count = 2
  base_score = 2/3 = 0.667
  relevance_score = 0.667 → INCLUÍDA ✓
```

**Cenário G: Segurança patrimonial**
```
Input: "vigilância, portaria, segurança patrimonial, CFTV"
total_terms = 4, min_matches = 2

Licitação: "Contratação de vigilância e portaria para sede do INSS"
  matched = ["vigilância", "portaria"] → matched_count = 2
  base_score = 2/4 = 0.500
  matched_count(2) >= min_matches(2) → INCLUÍDA ✓
```

**Cenário H: Limpeza**
```
Input: "limpeza, higienização, desinfecção, conservação"
total_terms = 4, min_matches = 2

Licitação: "Serviço de limpeza e conservação predial"
  matched = ["limpeza", "conservação"] → matched_count = 2
  base_score = 2/4 = 0.500 → INCLUÍDA ✓
```

---

## Acceptance Criteria

### AC1: Parsing Inteligente de Termos de Busca

- [ ] **AC1.1: Detecção automática de modo de parsing**
  - Se o input contém vírgula(s): usar vírgula como delimitador de termos
    - `"projeto, levantamento topográfico, terraplenagem"` → `["projeto", "levantamento topográfico", "terraplenagem"]`
  - Se NÃO contém vírgula: usar espaço como delimitador (backward compatible)
    - `"jaleco avental"` → `["jaleco", "avental"]` (idêntico ao comportamento atual)
  - Regra: **presença de vírgula ativa modo frase; ausência preserva modo legado**

- [ ] **AC1.2: Stopwords removidas apenas de termos single-word**
  - Termos multi-palavra (de vírgulas) preservam stopwords internas
  - `"estudos de impacto ambiental, drenagem"` → `["estudos de impacto ambiental", "drenagem"]`
  - Ordem de processamento: (1) split por vírgula, (2) trim, (3) remover stopwords apenas em termos de 1 palavra

- [ ] **AC1.3: Termos duplicados são deduplicados** (após normalização)

- [ ] **AC1.4: Campo vazio ou só stopwords faz fallback** para keywords do setor (preserva comportamento existente)

- [ ] **AC1.5: Edge cases com comportamento definido:**

  | Input | Resultado | Regra |
  |-------|-----------|-------|
  | `"a,,b"` | `["a", "b"]` | Segmentos vazios ignorados |
  | `",a,b,"` | `["a", "b"]` | Leading/trailing vírgulas ignoradas |
  | `",,,"` | `[]` → fallback setor | Sem termos válidos |
  | `"a, , b"` | `["a", "b"]` | Whitespace-only segments ignorados |
  | `"C++, item (A)"` | `["c++", "item (a)"]` | Caracteres especiais preservados, escapados no regex |
  | `"R$ 50.000"` | `["r$ 50.000"]` | Não é split por espaço (modo vírgula ativo) |
  | Texto colado com `\n` | Newlines tratados como espaço | Normalização de whitespace |
  | Input com smart quotes `\u201c\u201d` | Convertidos para aspas normais antes do parse | Sanitização |

- [ ] **AC1.6: SEM suporte a sintaxe de aspas para correspondência exata**
  - Aspas no input são tratadas como caracteres normais (removidas na normalização)
  - Correspondência exata de frase é controlada por toggle visual no chip (ver AC5)
  - **Justificativa:** sintaxe de operadores é padrão de desenvolvedor, inacessível ao público-alvo

### AC2: Matching com Correspondência Mínima e Scoring

- [ ] **AC2.1: Fórmula de relevância** (exata, sem ambiguidade):
  ```
  base_score = matched_count / total_terms
  phrase_bonus = 0.15 × count_of_multi_word_phrase_matches
  relevance_score = min(1.0, base_score + phrase_bonus)
  Guard: if total_terms == 0: return 0.0
  ```
  - **Sem pesos diferenciados.** Todos os termos têm peso igual (1.0x).
  - **Sem lista de termos genéricos.** Nenhum termo é penalizado por nome ou comprimento.
  - **Sem heurística de comprimento de caractere.**

- [ ] **AC2.2: Minimum Match Floor** (critério de inclusão):
  ```
  min_matches = max(1, min(ceil(total_terms / 3), 3))
  ```
  Uma licitação é incluída se:
  - `matched_count >= min_matches` **OU**
  - pelo menos 1 frase multi-palavra matchou como sequência exata

- [ ] **AC2.3: Degradação graciosa** quando poucos resultados passam:
  - Se o filtro de min_matches resulta em **0 resultados**, relaxar automaticamente para `min_matches = 1`
  - Incluir no response: `"filter_relaxed": true` e mensagem para o frontend
  - Log warning: `"Min match floor relaxed from {original} to 1 — zero results with strict filter"`

- [ ] **AC2.4: Resultado com contagem de ocultos:**
  - Response inclui `"hidden_by_min_match": N` — quantidade de licitações que matcharam pelo menos 1 termo mas não atingiram o min_matches
  - Permite ao frontend mostrar: "N resultados com menor correspondência ocultos"

- [ ] **AC2.5: Busca por setor** (`setor_id` sem `termos_busca`) **NÃO aplica** minimum match floor nem scoring. Comportamento 100% inalterado.

### AC3: Re-habilitar Exclusões do Setor para Termos Custom

- [ ] **AC3.1:** Quando `termos_busca` está ativo **E** um `setor_id` está selecionado:
  - Aplicar `sector.exclusions` como safety net (falsos positivos comuns do setor são rejeitados)
  - Aplicar `sector.context_required` para termos que fazem overlap com keywords do setor
  - **Resolve o problema raiz #2** identificado na análise

- [ ] **AC3.2:** Quando `termos_busca` está ativo **SEM** `setor_id` (setor padrão/genérico):
  - Não aplicar exclusões nem context_required (sem setor = sem guardrails de setor)
  - Minimum match floor é a única proteção contra falsos positivos

- [ ] **AC3.3:** Novo campo opcional na API: `exclusion_terms: Optional[list[str]]`
  - Permite que usuários avancem forneçam termos de exclusão manualmente
  - Default: `None` (usa exclusões do setor quando aplicável)

### AC4: Ordenação por Relevância

- [ ] **AC4.1: Implementar sort `relevancia`** no `calcular_relevancia()` existente em `utils/ordenacao.py`:
  - Refatorar para usar a nova `score_relevance()` — eliminar duplicação
  - Primário: `relevance_score` descendente
  - Secundário: `data_abertura_proposta` descendente (desempate)

- [ ] **AC4.2: Frontend envia `ordenacao=relevancia`** quando modo termos está ativo
  - O backend NÃO faz override silencioso da ordenação
  - Dropdown de ordenação pré-seleciona "Relevância" mas o usuário pode trocar
  - **Preserva contrato da API** (AC6.2)

- [ ] **AC4.3: Banner informativo** na primeira vez que resultados aparecem com ordenação por relevância:
  - "Resultados ordenados por relevância aos seus termos. Altere acima se preferir ordenar por data."
  - Dismissível, não reaparece após o primeiro dismiss (localStorage)

### AC5: Frontend — UX do Campo de Busca e Resultados

- [ ] **AC5.1: Modelo de interação do campo de input:**
  - **Commit de chip:** `Enter` ou `vírgula` comita o texto como chip
  - **Espaço NÃO comita** (permite frases multi-palavra como "levantamento topográfico")
  - **Colar texto com vírgulas:** auto-split em múltiplos chips
  - **Colar texto sem vírgulas:** cria um único chip (o texto inteiro)
  - **Chip removível:** click no X remove o chip
  - **Backspace** com cursor no início: remove último chip
  - **Migração UX:** Na primeira sessão, tooltip educativo aparece quando o campo ganha foco: "Novidade: agora você pode digitar frases completas. Use vírgula ou Enter para separar termos."

- [ ] **AC5.2: Toggle de correspondência exata no chip:**
  - Cada chip multi-palavra tem um ícone discreto de "cadeado" 🔒
  - Click no ícone ativa correspondência exata (a frase deve aparecer como sequência no texto)
  - Default: correspondência flexível (cada palavra é buscada individualmente)
  - **Substitui a sintaxe de aspas** por uma affordance visual direta

- [ ] **AC5.3: Placeholder e helper text:**
  - Placeholder: `"Ex: terraplenagem, drenagem, levantamento topográfico"`
  - Helper text (progressive disclosure — aparece quando input ganha foco):
    `"Dica: digite frases completas e separe com vírgula. Ex: levantamento topográfico, pavimentação"`

- [ ] **AC5.4: Indicadores visuais de relevância (APENAS POSITIVOS):**
  - Score ≥ 0.7: badge verde "Muito relevante"
  - Score ≥ 0.4: badge azul "Relevante"
  - Score < 0.4: **sem badge** (ausência é neutra, não negativa)
  - Tooltip no badge mostra termos matchados

- [ ] **AC5.5: Destaque de termos matchados** na descrição do objeto:
  - Termos matchados em **negrito** via React elements (NÃO `dangerouslySetInnerHTML` — previne XSS)
  - Overlapping terms: maior match prevalece
  - Performance: highlight calculado apenas para resultados visíveis (virtual scroll)

- [ ] **AC5.6: Indicador de ocultos** quando `hidden_by_min_match > 0`:
  - Texto abaixo dos resultados: "N resultados com menor correspondência foram ocultados."
  - Botão: "Mostrar todos" → refaz busca com `show_all_matches=true`

- [ ] **AC5.7: Sugestão pós-busca para termos insuficientes:**
  - Quando 0 resultados E filtro foi relaxado: mostrar sugestão
  - "Nenhum resultado combinou 2+ dos seus termos. Mostrando todos os resultados parciais."
  - NÃO mostrar aviso no momento do input (não pré-julgar a intenção)

- [ ] **AC5.8: Compatibilidade com saved searches:**
  - Buscas salvas com formato antigo (espaço-separado) são carregadas normalmente
  - Parser detecta ausência de vírgulas e usa modo legado automaticamente (AC1.1)
  - Novas buscas salvas armazenam o formato com vírgulas

### AC6: Backward Compatibility

- [ ] **AC6.1: `match_keywords()` preserva assinatura**
  - Return type permanece `Tuple[bool, List[str]]` — ZERO mudança
  - Nova função `score_relevance(objeto, terms, matched_terms) -> float` em `relevance.py`
  - Chamada separadamente, DEPOIS de `match_keywords()`
  - **60+ callers inalterados, todos os testes existentes passam sem modificação**

- [ ] **AC6.2: API preserva contrato**
  - Todos os campos existentes inalterados
  - Novos campos ADICIONADOS (opcionais): `relevance_score`, `matched_terms`, `hidden_by_min_match`, `filter_relaxed`
  - Ordenação padrão continua `data_desc` — frontend envia `relevancia` explicitamente
  - Novo campo request: `show_all_matches: Optional[bool] = False`

- [ ] **AC6.3: Modo setor 100% inalterado**
  - Busca por `setor_id` sem `termos_busca` não aplica scoring nem min_match
  - Exclusions e context_required continuam funcionando como antes

- [ ] **AC6.4: Testes existentes passam sem modificação**
  - `match_keywords()` inalterado
  - `aplicar_todos_filtros()` recebe novo parâmetro opcional `min_match_floor: Optional[int] = None`
  - Callers existentes sem o parâmetro = comportamento anterior (sem min_match)

### AC7: Estatísticas e Observabilidade

- [ ] **AC7.1: Novo campo de estatísticas:**
  - `rejeitadas_min_match: int` — bids com keyword match mas abaixo do min_match floor
  - `rejeitadas_keyword: int` — bids com ZERO keyword matches (já existe, preservado)
  - Separação permite diagnosticar: "keywords erradas" vs "threshold muito agressivo"

- [ ] **AC7.2: Logging de busca por termos:**
  - Log: termos parseados, min_matches calculado, resultados antes/depois do min_match
  - Log: se filtro foi relaxado, quantos ocultos
  - **Nível INFO** — sem dados sensíveis do usuário

- [ ] **AC7.3: Analytics event** (frontend):
  - Evento `custom_term_search` com: `term_count`, `result_count`, `hidden_count`, `max_score`, `filter_relaxed`
  - Evento `show_hidden_results` quando usuário clica "Mostrar todos"
  - Permite monitorar: taxa de buscas com 0 resultados, taxa de relaxamento, taxa de "mostrar todos"

### AC8: Testes

- [ ] **AC8.1: Testes unitários para `parse_search_terms()`:**
  - Modo vírgula: frases compostas, deduplicação, trim, segmentos vazios
  - Modo espaço (fallback): comportamento idêntico ao atual
  - Edge cases da tabela AC1.5 (todos os 8 casos)
  - Smart quotes, newlines, caracteres especiais

- [ ] **AC8.2: Testes unitários para `score_relevance()`:**
  - Fórmula: matched/total + phrase_bonus, cap em 1.0
  - Guard: total_terms == 0 retorna 0.0
  - Phrase bonus: 0, 1, múltiplas frases
  - Sem pesos — todos termos iguais

- [ ] **AC8.3: Testes unitários para Minimum Match Floor:**
  - Tabela completa: 1-12 termos → min_matches esperado
  - Condição B: frase multi-palavra override
  - Degradação graciosa: 0 resultados → relaxamento para 1

- [ ] **AC8.4: Testes cross-industry** (1 cenário por setor):
  - Engenharia: `"terraplenagem, drenagem, pavimentação"` (caso reportado)
  - Saúde: `"gaze, seringa, cateter, soro fisiológico"` (termos curtos específicos)
  - TI: `"sistema, software, licença"` (termos que seriam "genéricos" na v1)
  - Alimentação: `"fornecimento de refeição, marmita, alimentação escolar"` (frases)
  - Segurança: `"vigilância, portaria, segurança patrimonial, CFTV"` (sigla curta)
  - Limpeza: `"limpeza, higienização, desinfecção, conservação"` (todos borderline)
  - Mobiliário: `"mesa, cadeira, armário"` (termos ambíguos)
  - Vestuário: `"jaleco, avental, uniforme"` (baseline existente)
  - Construção: `"construção de muro, alvenaria, fundação"` ("construção" = específico)
  - Equipamentos: lista 15+ itens (testa o cap de min_matches=3)
  - **Cada cenário inclui:** input, termos parseados, 3 licitações exemplo com scores calculados

- [ ] **AC8.5: Testes de integração para endpoint `/buscar`:**
  - Score retornado no response
  - `hidden_by_min_match` correto
  - `show_all_matches=true` bypassa min_match
  - `filter_relaxed` quando 0 resultados com strict

- [ ] **AC8.6: Testes frontend:**
  - Chip creation: vírgula comita, espaço não comita
  - Chip removal: click no X, backspace
  - Chip paste: auto-split com vírgulas
  - Toggle exato: cadeado toggle em chips multi-palavra
  - Badges: verde (≥0.7), azul (≥0.4), sem badge (<0.4)
  - Highlight: termos em negrito na descrição (via React elements, não innerHTML)
  - "Mostrar todos": botão aparece quando hidden > 0
  - Saved searches: formato antigo carrega corretamente

- [ ] **AC8.7: Coverage ≥ 90%** para `term_parser.py`, `relevance.py`, e alterações em `filter.py`/`main.py`

### AC9: Performance

- [ ] **AC9.1: Regex pre-compilation:**
  - Patterns de keywords compilados UMA vez no início de `match_keywords()`
  - Armazenados em `dict[str, re.Pattern]` local
  - Elimina ~3M compilações redundantes em batches de 5000 bids

- [ ] **AC9.2: Benchmark:**
  - Scoring + sorting de 1000 bids com 10 termos em < 100ms
  - Incluir como test case em `test_benchmark_filter.py`

---

## Design Técnico

### Backend: Módulos

#### 1. `backend/term_parser.py` (NOVO)

```python
def parse_search_terms(raw_input: str) -> list[str]:
    """
    Parse user search input into structured search terms.

    Strategy: if input contains commas, use commas as delimiters (phrase mode).
    If no commas, fall back to space-as-delimiter (legacy mode).

    Returns: List of normalized, deduplicated search terms.
    """

def _parse_comma_mode(raw: str) -> list[str]:
    """Split by comma, trim each segment, remove empty, deduplicate."""

def _parse_space_mode(raw: str) -> list[str]:
    """Split by whitespace, remove stopwords from individual terms."""
```

#### 2. `backend/relevance.py` (NOVO)

```python
def score_relevance(
    matched_count: int,
    total_terms: int,
    phrase_match_count: int = 0,
) -> float:
    """
    Calculate relevance score (0.0 - 1.0).
    Formula: min(1.0, matched_count/total_terms + 0.15 * phrase_match_count)
    Guard: total_terms == 0 → 0.0
    """

def calculate_min_matches(total_terms: int) -> int:
    """
    Calculate minimum match floor.
    Formula: max(1, min(ceil(total_terms / 3), 3))
    """

def should_include(
    matched_count: int,
    total_terms: int,
    has_phrase_match: bool,
) -> bool:
    """
    Determine if a bid passes the minimum match filter.
    True if: matched_count >= min_matches OR has_phrase_match
    """
```

#### 3. Alterações em `backend/filter.py`

- `match_keywords()` **NÃO MUDA** — retorna `Tuple[bool, List[str]]` como sempre
- `aplicar_todos_filtros()` recebe novo parâmetro opcional: `min_match_floor: Optional[int] = None`
- Quando `min_match_floor` é fornecido: keyword filter coleta matches e aplica floor internamente
- Nova contagem: `rejeitadas_min_match` separada de `rejeitadas_keyword`

#### 4. Alterações em `backend/main.py` (~L1098-1130)

- `parse_search_terms()` substitui o `split()` + `remove_stopwords()` manual
- `min_match_floor` calculado e passado para `aplicar_todos_filtros()`
- Score calculado via `score_relevance()` para cada licitação filtrada
- `relevance_score` e `matched_terms` adicionados a cada item do resultado
- Exclusões do setor re-habilitadas quando `setor_id` presente com `termos_busca`

#### 5. Alterações em `backend/utils/ordenacao.py`

- `calcular_relevancia()` existente refatorado para chamar `score_relevance()`
- Elimina duplicação — single source of truth para cálculo de relevância

#### 6. Alterações em `backend/schemas.py`

- `BuscaRequest`: novo campo `show_all_matches: Optional[bool] = False`
- `BuscaRequest`: novo campo `exclusion_terms: Optional[list[str]] = None`
- Response: novos campos opcionais `relevance_score`, `matched_terms`, `hidden_by_min_match`, `filter_relaxed`

### Frontend: Alterações

#### 1. `frontend/app/buscar/page.tsx`

- **Input field:** chip commit via `vírgula` e `Enter` (não mais `espaço`)
- **Chips:** removíveis, com toggle de correspondência exata para multi-palavra
- **Paste handler:** auto-split quando texto colado contém vírgulas
- **Results:** badges positivos (verde/azul), highlight via React elements
- **Hidden results:** indicador + botão "Mostrar todos"
- **Saved searches:** compatibilidade com formato antigo
- **Ordenação:** pré-seleciona "Relevância" quando modo termos ativo

#### 2. `frontend/app/api/buscar/route.ts`

- Pass-through de novos campos (sem mudanças no proxy)

---

## Arquivos Impactados

| Arquivo | Mudança | Risco | Blast Radius |
|---------|---------|-------|-------------|
| `backend/term_parser.py` | **NOVO** | Baixo | Isolado |
| `backend/relevance.py` | **NOVO** | Baixo | Isolado |
| `backend/filter.py` | Novo param opcional em `aplicar_todos_filtros()` | Médio | Callers existentes sem param = sem mudança |
| `backend/main.py` (~L1098-1130) | Parsing + scoring + exclusions | Médio | Endpoint `/buscar` |
| `backend/schemas.py` | Campos opcionais adicionados | Baixo | Additive only |
| `backend/utils/ordenacao.py` | Refactor `calcular_relevancia()` | Baixo | Delegação para `score_relevance()` |
| `backend/excel.py` | Coluna "Relevância" condicional | Baixo | Apenas quando termos_busca |
| `frontend/app/buscar/page.tsx` | Input, chips, badges, highlight | Médio | Componente principal |
| `backend/tests/test_term_parser.py` | **NOVO** | — | — |
| `backend/tests/test_relevance.py` | **NOVO** | — | — |
| `frontend/__tests__/search-terms.test.tsx` | **NOVO** | — | — |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Min match floor exclui resultados válidos | Média | Alto | AC2.3: degradação graciosa + AC5.6: "mostrar todos" |
| UX de vírgula confunde usuários acostumados a espaço | Média | Médio | AC5.1: tooltip educativo + AC1.1: modo legado sem vírgulas |
| Regressão no modo setor | Baixa | Alto | AC6.3: setor inalterado + AC6.4: testes passam |
| Performance com scoring pós-match | Baixa | Baixo | AC9: pre-compile regex + benchmark |
| Exclusões do setor rejeita termos custom válidos | Baixa | Médio | AC3.1: exclusões são safety net, não veto absoluto — aplicadas apenas a overlap com keywords do setor |

---

## Definição de Pronto (DoD)

- [ ] Todos os ACs marcados como ✅
- [ ] Testes passando (backend + frontend) — **incluindo os 60+ callers de match_keywords() inalterados**
- [ ] TypeScript sem erros (`npx tsc --noEmit`)
- [ ] Coverage dos novos módulos ≥ 90%
- [ ] Testes existentes não regridem (0 novos failures vs baseline)
- [ ] Code review aprovado
- [ ] Testado manualmente com **todos os 10 cenários cross-industry** do AC8.4
- [ ] Documentação de API atualizada (OpenAPI/Swagger)
- [ ] Analytics events implementados e validados (AC7.3)

---

## Ordem de Execução Sugerida

1. **AC1** — `term_parser.py` + testes AC8.1 (foundation)
2. **AC2** — `relevance.py` + testes AC8.2 + AC8.3 (core logic)
3. **AC6** — Integrar no `filter.py`/`main.py` preservando signatures + testes AC6.4 (wiring)
4. **AC3** — Re-habilitar exclusões do setor + testes (safety net)
5. **AC4** — Refatorar `ordenacao.py` + sort por relevância (ranking)
6. **AC7** — Stats + logging + analytics (observability)
7. **AC8.4-8.5** — Testes cross-industry e integração (validation)
8. **AC5** — Frontend: input, chips, badges, highlight (UX)
9. **AC8.6** — Testes frontend (confidence)
10. **AC9** — Performance: regex pre-compile + benchmark (optimization)

---

## Configuração

Novas variáveis de ambiente (opcionais):
```
PHRASE_MATCH_BONUS=0.15         # Bonus por frase multi-palavra matchada (default: 0.15)
MIN_MATCH_DIVISOR=3             # Divisor para min_matches = ceil(N/divisor) (default: 3)
MIN_MATCH_CAP=3                 # Cap máximo do min_matches (default: 3)
```

**Nota:** Sem `GENERIC_TERM_WEIGHT`, `SPECIFIC_TERM_WEIGHT`, nem `MIN_RELEVANCE_SCORE` — estes conceitos foram eliminados do design por serem enviesados de setor.

---

## Notas de Implementação (da Revisão Multi-Agente Rodada 2)

As seguintes observações foram levantadas durante a revisão v2.0 e devem ser resolvidas durante a implementação (não bloqueiam aprovação):

### NI-1: SAFE_SEARCH_PATTERN deve aceitar vírgulas (@data-engineer)
`schemas.py:80` define `SAFE_SEARCH_PATTERN` que **não permite vírgulas**. Se `termos_busca` passar por este validator, inputs com vírgulas serão rejeitados antes de chegar ao `parse_search_terms()`. **Ação:** atualizar o pattern para incluir `,` e os caracteres de AC1.5 (`+`, `$`, `(`, `)`) ou confirmar que `termos_busca` não usa este validator. Atualizar também a `description` do campo em `BuscaRequest` para refletir o novo suporte a vírgulas.

### NI-2: Detecção de phrase match — fórmula derivada (@architect, @dev)
`phrase_match_count` para `score_relevance()` é derivado assim:
```python
phrase_match_count = sum(1 for t in matched_terms if ' ' in t)
```
Termo multi-palavra presente na lista `matched_terms` = frase matchou como sequência (pois `match_keywords()` usa `\b{keyword}\b` regex no keyword inteiro).

### NI-3: AC5.2 toggle de cadeado — contrato com backend (@architect, @qa, @analyst)
O toggle controla a serialização do termo **no frontend antes do envio**:
- **Cadeado fechado (exato):** termo enviado como frase única → `"levantamento topográfico"` (matchado como sequência)
- **Cadeado aberto (flexível):** frontend split o termo em palavras individuais antes de enviar → `"levantamento"` + `"topográfico"` (matchados separadamente)
- Nenhuma mudança necessária na API — a diferença é pré-processamento no frontend.
- **AC5.2 é deferível** para próximo sprint se capacidade for limitada (@po).

### NI-4: AC9.1 regex pre-compilation — escopo correto (@qa, @data-engineer)
Os patterns devem ser compilados **uma vez por invocação de `aplicar_todos_filtros()`** (no início do batch), NÃO dentro de cada chamada a `match_keywords()`. Implementação sugerida: compilar os patterns no caller e passá-los como parâmetro opcional `compiled_patterns: Optional[dict[str, re.Pattern]]` para `match_keywords()`.

### NI-5: `calcular_relevancia()` refactor preserva wrapper (@dev, @data-engineer)
`calcular_relevancia()` em `ordenacao.py` permanece como **wrapper de alto nível** que:
1. Extrai texto de `licitacao['objetoCompra']`, `licitacao['descricao']`, `licitacao['nomeOrgao']`
2. Chama `match_keywords()` para obter matched_count
3. Delega o cálculo numérico para `score_relevance()`
Em modo setor (sem `termos_busca`), o comportamento existente de `ordenar_licitacoes()` é preservado.

### NI-6: "Mostrar todos" — considerar cap de expansão (@analyst, @ux)
`show_all_matches=true` pode retornar centenas de resultados de baixa relevância. Considerar limitar a expansão a 50 resultados adicionais ou mostrar em seção separada "Menor correspondência". Decisão pode ser tomada durante implementação do AC5.6.

### NI-7: AC3.1 context_required — precedência (@qa)
Quando um termo custom coincide com um keyword do setor que tem `context_required`: a regra do setor se aplica como safety net. O usuário ter digitado o termo explicitamente NÃO sobrepõe a validação de contexto — a exclusão protege contra falsos positivos mesmo quando o termo é intencional.

---

## Changelog da Revisão v2.0

| Crítica Original | Agentes | Resolução |
|-----------------|---------|-----------|
| GENERIC_TERMS enviesada por setor | Architect, PO, Analyst | **Eliminada.** Sem lista de genéricos. Todos termos peso igual. |
| Heurística comprimento caractere falha | Architect, Analyst, PO | **Eliminada.** Sem peso por comprimento. |
| Fórmula matematicamente inconsistente | Architect, QA, Dev | **Fórmula exata** com cálculos intermediários para cada cenário |
| Threshold 0.15 falha para 10+ termos | Architect, QA, Analyst, DataEng | **Substituído** por Minimum Match Floor adaptativo com cap |
| Exclusões desabilitadas para custom terms | Architect, Analyst | **Re-habilitadas** quando setor selecionado (AC3) |
| match_keywords() return type quebra callers | QA, Dev, DataEng | **Preservada assinatura.** Nova função separada `score_relevance()` |
| Parser edge cases indefinidos | QA, Dev, DataEng | **Tabela de decisão** com 8 edge cases (AC1.5) |
| Input behavior sem vírgula/aspas indefinido | PO, DataEng, UX | **Regra explícita:** vírgula = modo frase, sem vírgula = modo espaço legado (AC1.1) |
| Sintaxe aspas inacessível | UX | **Eliminada.** Toggle visual de cadeado no chip (AC5.2) |
| Badge "Baixa relevância" causa ansiedade | UX, PO | **Eliminado.** Apenas badges positivos; sem badge = neutro (AC5.4) |
| Chip amarelo "termo genérico" patronizing | UX | **Eliminado.** Sugestão aparece pós-busca apenas se necessário (AC5.7) |
| Zero cenários cross-industry | Analyst, QA | **10 cenários** com cálculos (AC8.4 + seção de exemplos) |
| Sem métricas pós-lançamento | Analyst | **Analytics events** + logging estruturado (AC7) |
| Sort padrão override viola API | Dev | **Frontend envia** `ordenacao=relevancia` explicitamente (AC4.2) |
| Stats perdem granularidade | DataEng | **Novo campo** `rejeitadas_min_match` separado (AC7.1) |
| GENERIC_TERMS normalization bug | Dev, DataEng | **Eliminada** junto com a lista |
| calcular_relevancia() duplicação | Dev | **Refatorado** para usar `score_relevance()` (AC4.1) |
| Regex compilation perf | DataEng | **Pre-compilation** (AC9.1) + benchmark (AC9.2) |
| Excel sem relevância | Dev, DataEng | **Coluna condicional** adicionada (arquivos impactados) |
