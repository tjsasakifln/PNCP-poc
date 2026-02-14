# STORY-251: LLM Arbiter — Prompts Dinâmicos por Setor

## Metadata
| Field | Value |
|-------|-------|
| **ID** | STORY-251 |
| **Priority** | P2 |
| **Sprint** | Sprint 4 |
| **Estimate** | 5h |
| **Depends on** | STORY-248 (filter precision audit — keywords/exclusions expanded) |
| **Blocks** | Nenhuma |
| **Found by** | STORY-248 Track 3 audit |

## Problema

O prompt conservador do LLM arbiter (`llm_arbiter.py`, linhas 115-137) contém uma **descrição de setor hardcoded** para "Vestuário e Uniformes", que é incorretamente aplicada a **todos os 15 setores**.

### Evidência Concreta

```python
# llm_arbiter.py:115-137 — HARDCODED para vestuario
user_prompt = f"""Você é um classificador de licitações públicas...

SETOR: {setor_name}
DESCRIÇÃO DO SETOR: Aquisição de uniformes, fardas, roupas profissionais para
servidores, estudantes, agentes públicos. NÃO inclui EPIs médicos...

EXEMPLOS DE CLASSIFICAÇÃO:
SIM:
- "Uniformes escolares para rede municipal"
- "Fardamento para guardas municipais"
- "Camisas polo e calças para agentes de trânsito"

NAO:
- "Material de saúde incluindo aventais hospitalares e luvas"
- "Processo seletivo para contratação de servidores"
- "Obra de infraestrutura com fornecimento de uniformes para operários"

Este contrato é PRIMARIAMENTE sobre {setor_name}?
Responda APENAS: SIM ou NAO"""
```

O `setor_name` é dinâmico, mas **DESCRIÇÃO** e **EXEMPLOS** são estáticos de vestuário.

### Impacto Quantificado
- **14 de 15 setores** recebem contexto errado no prompt conservador
- **Modo conservador** é acionado quando density está entre 1-2% — exatamente os contratos borderline onde exemplos fazem mais diferença
- **Modo standard** (density 2-5%) usa prompt genérico sem exemplos e funciona corretamente para todos os setores
- **Custo desperdiçado:** Chamadas LLM com prompt inadequado não agregam valor para decisões borderline

### Root Cause Adicional

`classify_contract_primary_match()` **não recebe `setor_id`** — apenas `setor_name` (string descritiva). Isso impede lookup dinâmico do setor config:

```python
# filter.py:2315-2325 — setor_id disponível mas NÃO passado
setor_config = get_sector(setor)        # ← setor (ID) disponível aqui
setor_name = setor_config.name          # ← Apenas name extraído
is_primary = classify_contract_primary_match(
    setor_name=setor_name,              # ← Apenas name passado
    # setor_id=setor  ← FALTA
)
```

## Solução

Abordagem híbrida em 3 camadas:

1. **Passar `setor_id`** para `classify_contract_primary_match()` (mudança de assinatura + call-site)
2. **Lookup dinâmico** via `get_sector(setor_id)` dentro do arbiter para obter `description`, `keywords`, `exclusions`
3. **Gerar exemplos** SIM a partir de top-3 keywords, NAO a partir de top-3 exclusions do setor

### Porquê NÃO adicionar `llm_examples` ao YAML

Opção descartada. Manter exemplos manuais em 15 setores = 90 strings (3 SIM + 3 NAO × 15) que ficam defasadas rapidamente. Gerar automaticamente das keywords/exclusions que já existem e são mantidas é mais robusto e zero-maintenance.

## Acceptance Criteria

### Interface & Signature
- [ ] **AC1:** `classify_contract_primary_match()` recebe novo parâmetro `setor_id: Optional[str] = None`.
- [ ] **AC2:** `filter.py` passa `setor_id=setor` no call-site (linha ~2325).
- [ ] **AC3:** A assinatura é backward-compatible — `setor_id=None` é default, nenhum caller existente quebra.

### Prompt Dinâmico
- [ ] **AC4:** Quando `setor_id` é fornecido e existe em `sectors_data.yaml`, o prompt conservador usa `sector.description` em vez de descrição hardcoded.
- [ ] **AC5:** Exemplos SIM no prompt conservador são gerados a partir das 3 primeiras keywords do setor (formato: `"Aquisição de {keyword} para órgão público"`).
- [ ] **AC6:** Exemplos NAO no prompt conservador são gerados a partir das 3 primeiras exclusions do setor (formato: `"{exclusion}"`).
- [ ] **AC7:** Quando `setor_id` é `None` ou não encontrado em `sectors_data.yaml`, fallback gracioso para o prompt standard (sem exemplos, sem descrição).

### Qualidade dos Exemplos
- [ ] **AC8:** Para setores com < 3 keywords, gerar o máximo disponível (1 ou 2 exemplos SIM ainda é melhor que 0).
- [ ] **AC9:** Para setores com < 3 exclusions, gerar o máximo disponível. Se 0 exclusions, omitir seção NAO do prompt em vez de gerar exemplos vazios.
- [ ] **AC10:** Validação manual: gerar e inspecionar os prompts conservadores para os 5 maiores setores (vestuario, saude, informatica, engenharia, facilities) — confirmar relevância dos exemplos.

### Testes
- [ ] **AC11:** Teste parametrizado em `test_llm_arbiter.py` para pelo menos 5 setores (vestuario, informatica, saude, engenharia, materiais_eletricos) verificando que:
  - O prompt conservador contém `sector.description` (não a descrição hardcoded de vestuário)
  - Os exemplos SIM contêm keywords do setor correto
  - Os exemplos NAO contêm exclusions do setor correto
- [ ] **AC12:** Teste de fallback: quando `setor_id="inexistente"`, o prompt gerado é o standard (sem exemplos).
- [ ] **AC13:** Testes existentes continuam passando (zero regressão em `pytest`).

### Performance
- [ ] **AC14:** O tamanho do prompt conservador não excede 600 tokens para nenhum setor (medir com `len(prompt) / 4` como aproximação). O prompt atual tem ~226 tokens; o novo terá ~300-400 tokens com conteúdo dinâmico.
- [ ] **AC15:** Nenhuma chamada adicional à API OpenAI — lookup do setor é local via `get_sector()` (in-memory, cached pelo Python module loader).

## Investigação Técnica

### Arquivos a Modificar

| Arquivo | Linhas | Mudança |
|---------|--------|---------|
| `backend/llm_arbiter.py` | 45-55 (signature) | Adicionar `setor_id: Optional[str] = None` |
| `backend/llm_arbiter.py` | 113-137 (conservative prompt) | Extrair para `_build_conservative_prompt()` com lookup dinâmico |
| `backend/filter.py` | ~2325 (call-site) | Passar `setor_id=setor` |
| `backend/tests/test_llm_arbiter.py` | novos testes | Testes parametrizados por setor + fallback |

### Arquivos NÃO Modificados

| Arquivo | Porquê |
|---------|--------|
| `backend/sectors.py` | `get_sector()` já existe e retorna `SectorConfig` com todos os campos necessários |
| `backend/sectors_data.yaml` | Já tem `description`, `keywords`, `exclusions` para todos os 15 setores (expandido em STORY-248) |

### Abordagem de Implementação

```python
# llm_arbiter.py — proposed fix

def _build_conservative_prompt(setor_id: str, setor_name: str, objeto_truncated: str, valor: float) -> str:
    """Build sector-aware conservative prompt with dynamic examples."""
    from sectors import get_sector

    try:
        config = get_sector(setor_id)
    except (KeyError, Exception):
        # Fallback to standard prompt if sector not found
        return _build_standard_prompt(setor_name, objeto_truncated, valor)

    description = config.description or setor_name

    # Generate SIM examples from top keywords
    keywords = sorted(config.keywords)[:3]  # deterministic ordering
    sim_lines = "\n".join(f'- "Aquisição de {kw} para órgão público"' for kw in keywords)

    # Generate NAO examples from top exclusions
    exclusions = sorted(config.exclusions)[:3]  # deterministic ordering
    nao_section = ""
    if exclusions:
        nao_lines = "\n".join(f'- "{exc}"' for exc in exclusions)
        nao_section = f"\nNAO:\n{nao_lines}"

    return f"""Você é um classificador de licitações públicas. Analise se o contrato é PRIMARIAMENTE sobre o setor especificado (> 80% do valor e escopo).

SETOR: {setor_name}
DESCRIÇÃO DO SETOR: {description}

CONTRATO:
Valor: R$ {valor:,.2f}
Objeto: {objeto_truncated}

EXEMPLOS DE CLASSIFICAÇÃO:

SIM:
{sim_lines}
{nao_section}

Este contrato é PRIMARIAMENTE sobre {setor_name}?
Responda APENAS: SIM ou NAO"""
```

### Decisões de Design

| Decisão | Escolha | Justificativa |
|---------|---------|---------------|
| Exemplos manuais vs auto-gerados | Auto-gerados | Zero maintenance, always in sync com YAML |
| `sorted()` nas keywords/exclusions | Sim | Determinístico para cache hits e testabilidade |
| Seção NAO omitida se 0 exclusions | Sim | Prompt menor e sem seção vazia |
| Fallback para standard prompt | Sim | Graceful degradation em vez de erro |
| `setor_id` como Optional | Sim | Backward-compatible, nenhum caller quebra |

## Riscos

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| Keywords genéricas geram exemplos SIM ruins (ex: "Aquisição de mesa para órgão público") | Média | Top-3 keywords sorted() tendem a ser as mais específicas; validar manualmente AC10 |
| Exclusions longas demais no prompt (ex: frases completas) | Baixa | Truncar exclusion em 80 chars se necessário |
| Cache invalidation — mesmo contrato com setor diferente | Nenhuma | Cache key já inclui setor_name; adicionar setor_id não muda comportamento |
| Prompt conservador fica grande demais (>600 tokens) | Baixa | Setores com descriptions longas terão ~400 tokens, bem dentro do limite |

## Definition of Done
- Todos os 15 ACs checked
- Prompt conservador dinâmico para todos os 15 setores
- `pytest` sem regressões (baseline: 20 falhas pre-existentes)
- Validação manual dos prompts gerados para top-5 setores (AC10)
- Nenhum vestígio de hardcoded vestuário no prompt conservador
