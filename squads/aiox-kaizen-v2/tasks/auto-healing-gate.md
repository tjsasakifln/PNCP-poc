---
task: autoHealingGate()
responsavel: "KaizenChief"
responsavel_type: Agente
atomic_layer: Molecule
Entrada:
  - nome: gate_context
    tipo: object
    obrigatorio: true
  - nome: files_to_check
    tipo: array
    obrigatorio: true
Saida:
  - nome: healing_report
    tipo: markdown
    obrigatorio: true
Checklist:
  - Executar checks deterministicos
  - Classificar issues por severidade
  - Auto-corrigir issues triviais
  - Escalar issues nao-triviais
  - Gerar relatorio de acoes
---

# Task: Auto-Healing Gate

# ID: KZ-TP-008
# Executor: kaizen-chief (orchestration) + agent caller (execution)
# Trigger: Pre-commit, pre-QA, ou on-demand
# Inspiracao: Google "Infer and Interrupt" model (Detection at Scale Ep.76)

task:
  name: "Auto-Healing Gate"
  status: ready
  responsible_executor: kaizen-chief
  execution_type: hybrid
  elicit: false

  description: |
    Gate de qualidade que CORRIGE automaticamente issues triviais
    em vez de bloquear e esperar humano. Inspirado no modelo Google
    "Infer and Interrupt": detectar cedo, conter automaticamente,
    investigar apenas excecoes.

    Filosofia: "fail fast, fix automatically, investigate only exceptions"

  input:
    - "files_to_check — arquivos modificados para validar"
    - "gate_context — tipo de gate (pre-commit, pre-qa, pre-publish)"

  healing_rules:
    trivial_auto_fix:
      description: "Issues que podem ser corrigidos sem risco"
      examples:
        - id: "AH-001"
          issue: "Markdown formatting (MD022, MD031, MD040)"
          fix: "Auto-format com markdownlint --fix"
          risk: none

        - id: "AH-002"
          issue: "Trailing whitespace"
          fix: "Trim automatico"
          risk: none

        - id: "AH-003"
          issue: "Missing highlight span em slide"
          fix: "Adicionar <span class='highlight'> na keyword mais relevante"
          risk: low

        - id: "AH-004"
          issue: "Headline acima do limite de palavras"
          fix: "Truncar e reescrever headline (LLM)"
          risk: low

        - id: "AH-005"
          issue: "YAML syntax em bloco Markdown (- [ ] items)"
          fix: "Converter para YAML nativo"
          risk: none

    escalate_to_human:
      description: "Issues que requerem julgamento humano"
      examples:
        - "Mudanca de logica de negocio"
        - "Alteracao de acceptance criteria"
        - "Score de qualidade abaixo de threshold"
        - "Conflito entre gold example e output atual"
        - "Erro de voice DNA que muda significado"

  steps:
    - id: "1"
      name: "Scan deterministico"
      action: |
        Executar checks automaticos nos arquivos:
        1. Markdown lint (MD022, MD031, MD040, MD024, MD029)
        2. YAML syntax validation
        3. Token hardcoded detection (cores, font-sizes)
        4. PII detection (nomes reais em docs publicos)
        5. Structural completeness (campos obrigatorios)

    - id: "2"
      name: "Classificar issues"
      action: |
        Para cada issue encontrado:
        - TRIVIAL (auto-fix): formatting, whitespace, syntax
        - LOW (auto-fix + log): highlight missing, headline length
        - MEDIUM (flag + suggest): voice DNA drift, score borderline
        - HIGH (block + escalate): logica de negocio, PII, security

    - id: "3"
      name: "Auto-corrigir triviais"
      action: |
        Para issues TRIVIAL e LOW:
        1. Aplicar fix automaticamente
        2. Logar acao no healing_report
        3. Re-validar apos fix
        Limite: max 2 iteracoes de auto-fix (evitar loop)

    - id: "4"
      name: "Escalar nao-triviais"
      action: |
        Para issues MEDIUM e HIGH:
        1. Gerar descricao clara do issue
        2. Sugerir fix (nao aplicar)
        3. Marcar como NEEDS_HUMAN no report

    - id: "5"
      name: "Gerar relatorio"
      action: |
        Relatorio com:
        - Total de issues encontrados (por severidade)
        - Issues auto-corrigidos (com diff)
        - Issues escalados (com sugestao de fix)
        - Gate verdict: PASS (0 high/medium) ou NEEDS_REVIEW

  output:
    format: "Auto-Healing Gate Report"
    sections:
      - summary (counts por severidade)
      - auto_fixed (issues corrigidos com diff)
      - escalated (issues para humano com sugestao)
      - verdict (PASS ou NEEDS_REVIEW)

  acceptance_criteria:
    - "Todos os arquivos scanned"
    - "Issues triviais corrigidos automaticamente"
    - "Issues nao-triviais escalados com sugestao"
    - "Max 2 iteracoes de auto-fix (sem loop infinito)"
    - "Healing report gerado com diffs"

  veto_conditions:
    - "Auto-fix que muda logica de negocio → BLOQUEAR"
    - "Auto-fix em arquivo fora do scope → BLOQUEAR"
    - "Mais de 10 issues triviais no mesmo arquivo → ESCALAR (pode ser problema estrutural)"

  action_items:
    - "Integrar como pre-step nos workflows existentes"
    - "Adicionar como pre-commit hook opcional"
    - "Rodar antes de qa-gate em SDC Phase 4"
