---
task: auditOutputQuality()
responsavel: "KaizenChief"
responsavel_type: Agente
atomic_layer: Molecule
Entrada:
  - nome: squad_id
    tipo: string
    obrigatorio: true
  - nome: output_paths
    tipo: array
    obrigatorio: true
  - nome: gold_examples_path
    tipo: string
    obrigatorio: false
Saida:
  - nome: quality_audit_report
    tipo: markdown
    obrigatorio: true
Checklist:
  - Coletar outputs recentes do squad
  - Comparar contra gold examples (se disponivel)
  - Avaliar cada output em 5 dimensoes
  - Calcular score agregado
  - Gerar recomendacoes de melhoria
---

# Task: Audit Output Quality

# ID: KZ-TP-007
# Executor: kaizen-chief (primary)
# Trigger: *audit-quality {squad} ou proativo apos batch production
# Inspiracao: Google Autonomous SOC — Overseer Agents (Detection at Scale Ep.76)

task:
  name: "Audit Output Quality"
  status: ready
  responsible_executor: kaizen-chief
  execution_type: agent
  elicit: false

  description: |
    Auditar a qualidade dos outputs produzidos por um squad.
    Funciona como "overseer agent" — avalia outputs em batch
    (nao item a item), comparando contra gold examples e
    checklist de qualidade por tipo de output.

    Inspirado no modelo Google: "AI avaliando AI e humano"
    criando uma meta-camada de quality assurance.

  input:
    - "squad_id — identificador do squad a auditar"
    - "output_paths — caminhos dos outputs recentes"
    - "gold_examples_path — banco de exemplos gold (opcional)"
    - "squad.yaml → automation_boundary + quality_gates"

  steps:
    - id: "1"
      name: "Coletar outputs e contexto"
      action: |
        1. Ler squad.yaml do squad alvo
        2. Identificar quality_gates existentes
        3. Coletar os N outputs mais recentes (default: 5)
        4. Carregar gold examples se disponivel

    - id: "2"
      name: "Avaliar cada output em 5 dimensoes"
      action: |
        Para cada output, pontuar (1-10):
        1. COMPLETUDE — todos os elementos obrigatorios presentes?
        2. VOICE DNA — tom, vocabulario, emotional anchors alinhados?
        3. QUALIDADE TECNICA — formatacao, estrutura, sem erros?
        4. DIFERENCIACAO — output e unico ou generico/template?
        5. IMPACTO ESTIMADO — output atinge o objetivo do squad?

        Score composto: media ponderada (completude 25%, voice 20%,
        tecnica 20%, diferenciacao 15%, impacto 20%)

    - id: "3"
      name: "Comparar contra gold examples"
      action: |
        Se gold examples disponivel:
        1. Comparar estrutura, tom e qualidade
        2. Identificar gaps especificos vs gold standard
        3. Classificar cada output: GOLD (>=8.5), GOOD (7-8.4),
           NEEDS_WORK (5-6.9), POOR (<5)

    - id: "4"
      name: "Detectar patterns de degradacao"
      action: |
        1. Comparar scores dos ultimos outputs vs baseline
        2. Identificar dimensoes em declinio
        3. Classificar: IMPROVING, STABLE, DEGRADING

    - id: "5"
      name: "Gerar recomendacoes"
      action: |
        Para cada dimensao abaixo de 7:
        1. Diagnosticar causa raiz (prompt? template? dados?)
        2. Recomendar acao especifica
        3. Priorizar por impacto

  output:
    format: "Output Quality Audit Report"
    sections:
      - executive_summary (score medio, trend, classificacao)
      - per_output_scores (tabela com 5 dimensoes por output)
      - gold_comparison (se aplicavel)
      - degradation_patterns (trends)
      - prioritized_recommendations

  acceptance_criteria:
    - "Todos os outputs avaliados nas 5 dimensoes"
    - "Score composto calculado para cada output"
    - "Comparacao com gold examples se disponivel"
    - "Trend detection (improving/stable/degrading)"
    - "Cada recomendacao tem acao especifica e prioridade"

  veto_conditions:
    - "Output avaliado sem ler conteudo completo → REDO"
    - "Score POOR sem diagnostico de causa raiz → BLOQUEAR"
    - "Recomendacao generica sem acao especifica → REMOVER"

  action_items:
    - "Run kaizen-chief *audit-quality {squad}"
    - "Review scores and recommendations"
    - "Update gold examples with outputs scored GOLD"
