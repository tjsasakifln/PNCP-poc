---
task: performanceDashboard()
responsavel: "PerformanceTracker"
responsavel_type: Agente
atomic_layer: Molecule
Entrada:
  - nome: git_history
    tipo: object
    obrigatorio: true
  - nome: squad_metrics
    tipo: object
    obrigatorio: true
Saida:
  - nome: dashboard_report
    tipo: markdown
    obrigatorio: true
Checklist:
  - Coletar metricas DORA (task frequency, lead time, MTTR, rework rate)
  - Calcular dimensoes BSC (financeiro, cliente, processos, aprendizado)
  - Rastrear progresso OKR por squad
  - Gerar dashboard formatado com template
  - Destacar areas em WARNING ou CRITICAL
---

# Task: Generate Performance Dashboard
# ID: KZ-TP-002
# Executor: performance-tracker
# Trigger: *performance command or weekly cadence

task:
  name: "Performance Dashboard"
  status: ready
  responsible_executor: performance-tracker
  execution_type: agent
  elicit: false

  description: |
    Generate a comprehensive performance dashboard using DORA metrics,
    Balanced Scorecard, and OKR status for all active squads.

  input:
    - "squads/*/config/config.yaml — squad metadata"
    - "git log -- squads/ — activity history"
    - "squads/kaizen-v2/data/reports/ — historical reports"
    - "docs/stories/*.md — story completion status"

  steps:
    - id: "1"
      name: "Collect activity data"
      action: |
        1. For each squad: git log frequency, file changes, commit patterns
        2. Count completed tasks/stories per squad
        3. Measure lead time: story created → story completed
        4. Identify rework: stories with multiple fix commits

    - id: "2"
      name: "Calculate DORA metrics"
      action: |
        Per squad:
        - Task Frequency: commits per week to squad directory
        - Lead Time: avg days from story start to completion
        - MTTR: avg time to fix issues after detection
        - Rework Rate: % of tasks requiring rework commits
        - Classify: Elite / High / Medium / Low

    - id: "2b"
      name: "Calculate METR reality metrics"
      action: |
        METR metrics complement DORA by measuring REAL outcomes vs perceived outcomes.
        Source: "Measuring the Impact of AI on Developer Productivity" (METR 2025).
        Reference: docs/research/2026-03-05-multiagent-orchestration-whitepaper/ cap. 13.3

        Per squad, measure:
        - End-to-End Delivery Time: wall-clock time from task creation to MERGED output
          (not just "task completed" — includes review, fixes, integration)
          Source: git log timestamps from first commit to merge/push
        - Code Churn Rate: % of lines changed within 14 days of initial commit
          (high churn = rework invisible in task completion metrics)
          Source: git log --follow --diff-filter=M on squad files
        - Defect Escape Rate: % of outputs requiring post-completion fixes
          (QA rejections, bug fixes, regression fixes after "Done")
          Source: commits with "fix:" after story marked complete

        CRITICAL INSIGHT (METR 2025):
        - Task Completion Rate is a VISIBLE metric (+55% perceived)
        - End-to-End Delivery Time is the REAL metric (-19% actual)
        - Code Churn is the HIDDEN cost (+41% untracked)
        - Optimizing the visible metric DEGRADES the real metric
        - ALWAYS report METR alongside DORA to prevent perception-reality gap

        Classification:
        - Healthy: E2E stable or decreasing, churn <15%, defect escape <5%
        - Warning: E2E increasing >20%, churn 15-30%, defect escape 5-15%
        - Critical: E2E increasing >50%, churn >30%, defect escape >15%

    - id: "3"
      name: "Build Balanced Scorecard"
      action: |
        Per squad, score 1-10:
        - Financial: cost efficiency (estimated token spend vs output)
        - Customer: output quality (completion rate, acceptance criteria met)
        - Internal Process: workflow efficiency (lead time, throughput)
        - Learning & Growth: new capabilities added, patterns refined

    - id: "4"
      name: "Check OKR status"
      action: |
        1. Read current OKRs from stories/PRDs
        2. Calculate progress per key result
        3. Flag stalled OKRs (KZ_PT_003)
        4. Summarize overall alignment

    - id: "5"
      name: "Generate alerts"
      action: |
        Apply heuristics KZ_PT_001 through KZ_PT_005
        Flag any threshold violations
        Prioritize alerts by severity

  output:
    format: "Performance Dashboard"
    template: "templates/performance-dashboard-tmpl.md"

  acceptance_criteria:
    - "DORA metrics calculated for all active squads"
    - "METR reality metrics calculated for all active squads (E2E, churn, defect escape)"
    - "BSC scored for all active squads"
    - "OKR status checked"
    - "All heuristics applied"
    - "Alerts prioritized by severity"
    - "Perception-reality gap highlighted if DORA and METR diverge"

  veto_conditions:
    - "Métricas DORA calculadas sem dados reais de git log → BLOQUEAR (dados fabricados)"
    - "Alerta sem trend de 2+ períodos → REBAIXAR para observação (não é alerta)"
    - "BSC com score sem justificativa por dimensão → REDO step 3"
    - "Dashboard sem dados de TODOS os squads ativos → BLOQUEAR (análise incompleta)"
    - "Métricas METR calculadas sem dados reais de git log → BLOQUEAR (dados fabricados)"

  action_items:
    - "Run performance-tracker *performance"
    - "Hand off alerts to bottleneck-hunter if constraints detected"
    - "Hand off to kaizen-chief for weekly report"
