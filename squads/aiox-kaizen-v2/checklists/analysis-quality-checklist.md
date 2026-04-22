# Analysis Quality Checklist — Per Dimension

# ID: KZ-QC-003
# Used by: kaizen-chief para validar qualidade de cada dimensão da análise

## Validação por Dimensão

### 1. Estrutura (topology-analyst)

- [ ] Todos os squads ativos inventariados
- [ ] Tipo de team topology classificado (stream-aligned, enabling, complicated-subsystem, platform)
- [ ] Cognitive load score calculado por squad
- [ ] Interações entre squads mapeadas (collaboration, X-as-a-Service, facilitating)
- [ ] Evidência de interação baseada em git log / file references

### 2. Performance (performance-tracker)

- [ ] DORA metrics calculadas com dados reais de git log
- [ ] BSC scored com justificativa por dimensão (financial, customer, process, learning)
- [ ] OKR status verificado contra stories/PRDs
- [ ] Classificação Elite/High/Medium/Low aplicada por squad
- [ ] Trends comparados com período anterior (não spike isolado)

### 3. Bottlenecks (bottleneck-hunter)

- [ ] System constraint identificado com throughput data
- [ ] 5 Focusing Steps aplicados (Identify, Exploit, Subordinate, Elevate, Repeat)
- [ ] OMTM definido para o constraint
- [ ] Impacto no pipeline quantificado
- [ ] Alternativas de resolução listadas com trade-offs

### 4. Capabilities (capability-mapper)

- [ ] Capability matrix construída (domínio → agente → squad)
- [ ] Requirement matrix extraída de stories/PRDs ativos
- [ ] Gaps classificados por N de ocorrências (RULE-RD-001)
- [ ] 4R analysis aplicada (Recruit, Retain, Reskill, Redesign)
- [ ] Cada gap tem score impacto x urgência

### 5. Technology Radar (tech-radar)

- [ ] Todas as ferramentas categorizadas em 4 quadrantes (APIs, MCPs, Libraries, Models)
- [ ] Ring placement com evidência (Adopt >3 usos, Trial 1-3, Assess gap, Hold issues)
- [ ] Movimentos documentados com rationale
- [ ] Fitness functions executadas por squad
- [ ] Consolidação de ferramentas duplicadas avaliada

### 6. Custos (cost-analyst)

- [ ] Custo estimado por squad com breakdown (agentes, tokens, APIs)
- [ ] Waste identificado com savings potencial
- [ ] ROI calculado para cada recomendação com margem de erro
- [ ] Forecast baseado em trend de 2+ períodos
- [ ] FinOps phases aplicadas (Inform, Optimize, Operate)

## Gate de Qualidade Global

- [ ] Todas as 6 dimensões cobertas (nenhuma omitida)
- [ ] Dados de filesystem scans reais em todas as dimensões
- [ ] Recomendações passam no GATE-RD (RULE-RD-001)
- [ ] Max 5 recomendações priorizadas no relatório final
- [ ] Executive summary em max 3 frases

## Validação Sistêmica (7 Pontos)

Checklist complementar para validar coerência do ecossistema como um todo, não apenas dimensões individuais.
Fonte: Framework Lozano, Cap. 13 — ver `docs/research/2026-03-05-cognitive-systems-architecture/systemic-validation-checklist.md`

- [ ] **Completude**: Cada input (PRD/briefing) tem um squad/agent que o processa? Cada output tem um produtor definido?
- [ ] **Contratos**: Conexões entre squads/agents têm inputs/outputs claros? Output de A é compatível com input de B?
- [ ] **Fluxo**: O caminho do PRD ao entregável final é contínuo e sem lacunas?
- [ ] **Loops**: Loops de refinamento (QA Loop, CodeRabbit) têm condição de saída explícita (max iterações OU critério)?
- [ ] **Identidade**: Voice DNA consistente em todos os pontos de contato? Personas mantidas?
- [ ] **Resiliência**: Se um agent/squad falhar, existe fallback ou degradação graciosa?
- [ ] **Simplicidade**: Algum squad/agent pode ser removido sem perda significativa? Se sim, considerar remoção.

## Stress Test Mental (3 Inputs)

Antes de aprovar o relatório, traçar mentalmente o caminho de 3 cenários pelo ecossistema:

1. **Input ideal**: Story simples, squad maduro, pipeline completo
2. **Input desafiador**: Story cross-squad, dependências complexas, nova tecnologia
3. **Input problemático**: PRD incompleto, squad sem agent especialista, ferramenta indisponível

Se o ecossistema lida bem com os três, está robusto. Pontos de falha no 2 ou 3 entram como findings.

## REGRA ANTI-ALINHAMENTO-CEGO (Lesson Learned: Caso Jasmin Alic 2026-03-05)

Quando uma análise comparativa detecta gaps entre artefatos de squads diferentes:

**ANTES de recomendar "alinhar com padrão X"**, perguntar:

1. **Esse gap causa problema real?** Se o agente/artefato funciona sem a seção, o gap é cosmético.
2. **O contexto é o mesmo?** Padrões de um squad de workflows complexos (CE) podem ser over-engineering para um squad de tarefas simples (instagram-spy).
3. **A solução já existe de outra forma?** Exemplos concretos > templates abstratos. Texto livre > YAML estruturado (para LLMs).
4. **Se eu adicionar isso, quem vai usar?** Se a resposta é "ninguém, mas fica bonito no checklist" → NÃO adicionar.

**Teste rápido**: "Se eu NÃO fechar esse gap, o que acontece?" Se a resposta é "nada" → gap cosmético → ignorar.

## Veto Conditions

- Dimensão sem dados reais → BLOQUEAR e refazer scan
- Recomendação sem evidência de N>=3 → REBAIXAR para MONITORAR
- Mais de 5 recomendações no relatório → CORTAR por menor impacto
- Dimensão inteira omitida → NOTAR explicitamente no relatório
- Validação Sistêmica com 3+ itens falhando → NOTAR como finding de alta prioridade
- Recomendação de "alinhar padrões" sem evidência de problema real → REBAIXAR para MONITORAR
