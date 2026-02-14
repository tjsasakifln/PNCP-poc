# STORY-249: LLM Arbiter — Prompts Dinâmicos por Setor

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-249 |
| **Priority** | P2 |
| **Sprint** | Sprint 4 |
| **Estimate** | 4h |
| **Depends on** | STORY-248 (filter precision audit complete) |
| **Blocks** | Nenhuma |
| **Found by** | STORY-248 Track 3 audit |

## Problema

O prompt conservador do LLM arbiter (`llm_arbiter.py`, linhas 115-137) contém uma **descrição de setor hardcoded** para "Vestuário e Uniformes", que é incorretamente aplicada a **todos os 15 setores**.

Quando o LLM arbiter recebe um contrato do setor "Materiais Elétricos" no modo conservador (density 1-2%), ele vê exemplos sobre uniformes escolares e fardamento — completamente irrelevantes para disjuntores e transformadores.

### Impacto
- **Falsos positivos/negativos silenciosos:** O LLM recebe contexto errado para 14 de 15 setores
- **Custo desperdiçado:** Chamadas LLM com prompt inadequado não agregam valor
- **Afeta apenas o modo conservador** (density 1-2%) — o modo standard (density 2-5%) usa apenas o nome do setor, que é correto

### Código Afetado

```python
# llm_arbiter.py:118 — HARDCODED para vestuario
user_prompt = f"""...
SETOR: {setor_name}
DESCRIÇÃO DO SETOR: Aquisição de uniformes, fardas, roupas profissionais...
...
EXEMPLOS DE CLASSIFICAÇÃO:
SIM:
- "Uniformes escolares para rede municipal"
- "Fardamento para guardas municipais"
...
"""
```

O `setor_name` é dinâmico, mas a DESCRIÇÃO e os EXEMPLOS são estáticos de vestuário.

## Solução

Tornar o prompt conservador dinâmico, usando a descrição e keywords do setor vindos de `sectors_data.yaml`. Cada setor já tem `name`, `description`, e `keywords` — basta injetar no prompt.

### Opções de Implementação

1. **Setor-aware prompt com description do YAML** — injetar `sector.description` no campo DESCRIÇÃO DO SETOR
2. **Exemplos dinâmicos por setor** — adicionar campo `llm_examples` ao `sectors_data.yaml` com 3 SIM + 3 NAO por setor
3. **Abordagem híbrida** — description do YAML + gerar exemplos a partir das top-3 keywords e top-3 exclusions

## Acceptance Criteria

### Prompt Dinâmico
- [ ] **AC1:** O prompt conservador usa `sector.description` de `sectors_data.yaml` em vez de descrição hardcoded.
- [ ] **AC2:** Exemplos SIM/NAO no prompt conservador são gerados dinamicamente a partir das keywords e exclusions do setor.
- [ ] **AC3:** Quando `setor_name` não é encontrado em `sectors_data.yaml`, fallback gracioso para o prompt standard (sem exemplos).

### Qualidade dos Exemplos
- [ ] **AC4:** Cada setor tem pelo menos 3 exemplos SIM e 3 exemplos NAO no prompt conservador.
- [ ] **AC5:** Exemplos são relevantes ao setor (validados manualmente para os 5 maiores setores: vestuario, saude, informatica, engenharia, facilities).

### Testes
- [ ] **AC6:** `test_llm_arbiter.py` atualizado para verificar que o prompt conservador contém a descrição correta do setor (não hardcoded vestuario).
- [ ] **AC7:** Teste parametrizado para pelo menos 5 setores verificando que exemplos no prompt são relevantes ao setor.
- [ ] **AC8:** Testes existentes continuam passando (zero regressão).

### Performance
- [ ] **AC9:** O tamanho do prompt conservador não excede 500 tokens (medir com tiktoken ou aproximação 4 chars = 1 token).
- [ ] **AC10:** Nenhuma chamada adicional à API OpenAI — exemplos são gerados localmente a partir do YAML.

## Investigação Técnica

### Arquivos a Modificar

| Arquivo | Mudança |
|---------|---------|
| `backend/llm_arbiter.py:113-137` | Tornar prompt conservador dinâmico |
| `backend/sectors.py` | Expor `get_sector_config()` se não existir |
| `backend/sectors_data.yaml` | (Opcional) Adicionar campo `llm_examples` por setor |
| `backend/tests/test_llm_arbiter.py` | Novos testes para prompts por setor |

### Abordagem Recomendada (Opção 3 — Híbrida)

```python
# llm_arbiter.py — proposed fix
from sectors import get_sector_config

def _build_conservative_prompt(setor_id, setor_name, objeto_truncated, valor):
    config = get_sector_config(setor_id)
    description = config.get("description", setor_name)

    # Generate SIM examples from top keywords
    keywords = config.get("keywords", [])[:5]
    sim_examples = [f'- "Aquisição de {kw} para órgão público"' for kw in keywords[:3]]

    # Generate NAO examples from top exclusions
    exclusions = config.get("exclusions", [])[:5]
    nao_examples = [f'- "{exc}"' for exc in exclusions[:3]]

    return f"""Setor: {setor_name}
Descrição: {description}
...
SIM:
{chr(10).join(sim_examples)}

NAO:
{chr(10).join(nao_examples)}
..."""
```

## Definition of Done
- Todos os ACs checked
- Prompt conservador dinâmico para todos os 15 setores
- `pytest` sem regressões
- Revisão manual dos prompts gerados para top-5 setores
