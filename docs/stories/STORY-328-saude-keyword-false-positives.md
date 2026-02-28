# STORY-328: Eliminar falsos positivos do setor Saúde — keyword "saúde" matcheando nome do órgão comprador

**Prioridade:** P0 (qualidade de resultados — o mais crítico para a proposta de valor do produto)
**Complexidade:** M (Medium)
**Sprint:** CRIT-SEARCH

## Problema

A busca por setor "Saúde" retorna resultados **bizarramente irrelevantes** que destroem a credibilidade do produto:

| Resultado exibido | Por que é irrelevante | Por que passou no filtro |
|---|---|---|
| Locação de veículos sedan e caminhonete | Transporte, não saúde | "Secretaria de Estado da **Saúde** - SESA" no objetoCompra |
| Gêneros alimentícios e materiais de limpeza | Alimentação/limpeza genérica | "Secretaria Municipal de **Saúde**" no objetoCompra |
| Equipamentos de informática | TI genérico | "Consórcio de **Saúde**" no objetoCompra |
| Material de escritório e papelaria | Suprimentos de escritório | "Secretaria Municipal de **Saúde**" no objetoCompra |
| Construção de muro de contenção | Construção civil | "Unidade de **Saúde**" no objetoCompra |
| Gêneros alimentícios para CAPS | Alimentação | "Secretaria Municipal de **Saúde**" no objetoCompra |

Todos marcados como "Relevância média". Isso é **um atestado de incompetência** para o usuário.

## Causa Raiz

O campo `objetoCompra` do PNCP **inclui o nome do órgão comprador** dentro da descrição do objeto. Exemplo real:

> "Contratação de empresa especializada na prestação de serviços de **locação de veículos** tipo sedan e caminhonete pick-up, sem motorista, para atendimento às necessidades da **Secretaria de Estado da Saúde** - SESA."

A keyword "**saúde**" (`sectors_data.yaml:3395`) matcha nesse texto com **baixa densidade** (~2-3%), enviando para classificação LLM. O LLM vê "Secretaria de Saúde" e classifica como relevante sem perceber que o OBJETO REAL é locação de veículos.

Cadeia de falha:
1. `objetoCompra` contém "Secretaria de Saúde" (padrão PNCP incluir comprador)
2. Keyword "saúde" matcha com density ~2% → classificação `llm_conservative`
3. Exclusões existentes NÃO cobrem: "locação de veículos", "gêneros alimentícios" (sem "merenda"), "material de papelaria", "material de escritório", "equipamentos de informática"
4. LLM prompt não instrui ignorar nomes de órgãos
5. LLM retorna SIM → resultado irrelevante aparece como "Relevância média"

## Critérios de Aceite

### Bloco 1: Exclusões de padrões de órgão (strip org context)
- [ ] AC1: Adicionar ao `filter.py` função `_strip_org_context(texto)` que remove padrões como "da Secretaria [Municipal|Estadual|de Estado] de Saúde", "do Consórcio [.*] de Saúde", "da Unidade [.*] de Saúde", "do Centro de Saúde", "da Fundação [.*] de Saúde" do texto ANTES de calcular keyword density
- [ ] AC2: A função deve usar regex seguro para capturar variações: "secretaria de saude", "secretaria municipal de saude", "sec. mun. de saude", "SMS", "SESA", "FMS" (Fundo Municipal de Saúde)
- [ ] AC3: O texto limpo é usado para keyword matching e density, mas o texto original é preservado para display

### Bloco 2: Exclusões ampliadas no sectors_data.yaml
- [ ] AC4: Adicionar exclusões ao setor Saúde para categorias genéricas que aparecem com frequência:
  - "locação de veículo" / "locação de veículos" / "locacao de veiculo" / "locacao de veiculos"
  - "material de escritório" / "material de escritorio" / "material de papelaria"
  - "gêneros alimentícios" / "generos alimenticios" (já existe "gênero alimentício" singular — adicionar plural)
  - "equipamentos de informática" / "equipamentos de informatica" / "insumos de informática" / "insumos de informatica"
  - "construção de muro" / "construcao de muro"
  - "combustível" / "combustivel" / "abastecimento de combustível" / "abastecimento de combustivel"
  - "serviço de limpeza" / "servico de limpeza"
- [ ] AC5: Manter as exclusões existentes intactas (72 exclusões atuais não são removidas)

### Bloco 3: LLM prompt hardening
- [ ] AC6: No `llm_arbiter.py:_build_zero_match_prompt()`, adicionar instrução explícita: "ATENÇÃO: Ignore o nome da organização/secretaria/órgão comprador se aparecer na descrição. Foque EXCLUSIVAMENTE no que está sendo CONTRATADO ou ADQUIRIDO (o objeto da licitação)."
- [ ] AC7: No `llm_arbiter.py`, o prompt `_build_arbiter_prompt()` (para density 1-5%) também deve receber a mesma instrução
- [ ] AC8: Adicionar exemplos negativos ao prompt: "NÃO é Saúde: 'locação de veículos para Secretaria de Saúde', 'material de escritório para hospital', 'gêneros alimentícios para centro de saúde'"

### Bloco 4: Validação e testes
- [ ] AC9: Teste com os 7 exemplos reais da produção — TODOS devem ser rejeitados pelo filtro
- [ ] AC10: Teste que licitações legítimas de saúde continuam passando: "aquisição de medicamentos para hospital municipal", "material médico-hospitalar", "equipamento cirúrgico"
- [ ] AC11: Teste de regressão: rodar `pytest -k test_filter` com 0 falhas
- [ ] AC12: A taxa de falsos positivos para o setor Saúde deve cair drasticamente (medir antes/depois com um sample de 100 bids reais)

## Arquivos Afetados

- `backend/filter.py` (AC1-AC3: `_strip_org_context()`)
- `backend/sectors_data.yaml` (AC4-AC5: exclusões ampliadas)
- `backend/llm_arbiter.py` (AC6-AC8: prompts hardened)
- `backend/tests/test_filter_saude_false_positives.py` (novo — AC9-AC12)
- `backend/tests/test_llm_arbiter.py` (expandir com exemplos de org name)

## Impacto

Esta story é a **mais crítica** para a proposta de valor do SmartLic. Se o produto retorna "material de escritório" como oportunidade de Saúde, o usuário conclui que a IA não funciona e abandona durante o trial. Sem correção, a taxa de conversão trial→pago será efetivamente zero.

## Notas Técnicas

- O padrão PNCP inclui o comprador no `objetoCompra` — isso é comportamento da API, não bug nosso
- Outros setores provavelmente sofrem o mesmo problema (ex: "Tecnologia" com "Secretaria de Tecnologia")
- Considerar generalizar `_strip_org_context()` para TODOS os setores, não apenas Saúde
- A keyword "saúde" deve ser MANTIDA (com o strip de contexto, ela só matchará quando "saúde" aparece no objeto real)
