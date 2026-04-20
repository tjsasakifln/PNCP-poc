# CA_DL_001 — Double-Loop Reflection Quality

**Type:** Decision Heuristic
**Phase:** Reflection Pipeline
**Agent:** @kaizen-v2:memory-keeper
**Pattern:** CA-CORE-001 (Double-Loop Learning)

## Purpose

Heurístico para avaliar se o processo de reflexão do kaizen-v2 está operando em double-loop (questionando pressupostos) ou apenas single-loop (registrando fatos). Reflexão de qualidade deve ir além do "o que aconteceu" para "por que nossos modelos mentais permitiram isso."

## Configuration

```yaml
CA_DL_001:
  name: "Double-Loop Reflection Quality"
  phase: "reflection-pipeline"
  pattern_reference: "CA-CORE-001"

  weights:
    assumption_questioning: 0.9    # reflexão questiona pressupostos?
    espoused_vs_actual_gap: 0.85   # identifica lacunas teoria vs. prática?
    rule_change_proposed: 0.8      # propõe mudança de regra, não só ação?
    defensive_routine_detection: 0.75  # identifica rotinas defensivas?

  thresholds:
    min_double_loop_patterns: 1    # pelo menos 1 pattern com questionamento de pressuposto
    max_single_loop_only: 5        # se 5+ patterns seguidos são single-loop, alertar
    min_reflection_depth: "why"    # reflexão deve conter "por que" não só "o que"

  quality_levels:
    deep: "Questiona pressupostos + propõe mudança de regra + identifica lacuna"
    standard: "Identifica pattern + explica trigger + documenta ação"
    shallow: "Apenas registra o que aconteceu sem questionamento"

  veto_conditions:
    - condition: "all_patterns_single_loop"
      action: "WARN — Reflexão superficial. Nenhum pattern questiona pressupostos."
    - condition: "same_pattern_extracted_3x_without_rule_change"
      action: "ALERTA — Padrão recorrente sem mudança. Possível rotina defensiva."
    - condition: "theory_gap_detected_but_no_action"
      action: "WARN — Lacuna identificada mas sem proposta de correção."

  decision_tree:
    - IF pattern_questions_assumption THEN double_loop_achieved
    - IF pattern_only_describes_action THEN single_loop_only
    - IF same_pattern_repeats_3x THEN defensive_routine_suspected
    - IF reflection_contains_why THEN adequate_depth
    - IF reflection_only_what THEN shallow_reflection_warn
    - TERMINATION: reflection_quality_assessed

  output:
    type: "quality assessment"
    values: ["DEEP", "STANDARD", "SHALLOW"]
```

## Assessment Framework

```text
PASSO 1: Classificar Tipo de Aprendizado
  Para cada pattern extraído no reflect:
  - Single-loop: "Hook falhou → Corrigimos o path"
  - Double-loop: "Hook falhou → Por que assumimos path relativo? →
                   Nova regra: sempre path absoluto"

PASSO 2: Verificar Profundidade
  - Contém "por que"? → Adequado
  - Contém "o que" apenas? → Superficial
  - Propõe mudança de regra? → Profundo
  - Apenas corrige ação? → Necessário mas insuficiente

PASSO 3: Detectar Rotinas Defensivas
  - Mesmo erro 3+ vezes → Rotina defensiva provável
  - Pattern ignorado repetidamente → Resistência a aprendizado
  - "Já sabíamos disso" → Defensive avoidance

PASSO 4: Avaliar
  - DEEP: >= 1 pattern com double-loop + rule change
  - STANDARD: patterns com trigger + action documentados
  - SHALLOW: apenas registro factual sem questionamento
```

## Examples

### Reflexão Deep (Double-Loop)
- **Observação:** "Hooks falharam porque paths eram relativos"
- **Questionamento:** "Por que assumimos que CWD seria o dir do squad?"
- **Regra nova:** "Hooks DEVEM usar paths absolutos calculados de __dirname"
- **Qualidade:** DEEP — questiona pressuposto + muda regra

### Reflexão Standard (Single-Loop)
- **Observação:** "Path corrigido de relativo para absoluto"
- **Ação:** "Scripts atualizados com novo path"
- **Qualidade:** STANDARD — documenta correção mas não questiona por quê

### Reflexão Shallow
- **Observação:** "Hooks funcionando agora"
- **Qualidade:** SHALLOW — apenas estado, sem análise

---

**Pattern Compliance:** CA-CORE-001 (Double-Loop Learning)
**Source:** CA Mind DNA - Reflection Quality Heuristic
