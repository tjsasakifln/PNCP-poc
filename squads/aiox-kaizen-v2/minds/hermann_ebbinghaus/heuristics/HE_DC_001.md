# HE_DC_001 — Decay Score Assessment

**Type:** Decision Heuristic
**Phase:** Pattern Lifecycle Management
**Agent:** @kaizen-v2:memory-keeper
**Pattern:** HE-CORE-001 (Forgetting Curve)

## Purpose

Heurístico para avaliar e agir sobre o decay score de patterns no kaizen-v2. Baseado na curva de esquecimento de Ebbinghaus, determina quando um pattern deve ser mantido ativo, archivado, ou deletado.

## Configuration

```yaml
HE_DC_001:
  name: "Decay Score Assessment"
  phase: "pattern-lifecycle"
  pattern_reference: "HE-CORE-001"

  # Prioritization weights — used to rank factors when breaking ties
  # or selecting which patterns to surface in briefing. NOT used in the
  # exponential decay formula (decay_score = e^(-rate * days)).
  weights:
    days_since_reinforced: 0.9   # principal fator de decay
    verification_count: 0.85     # patterns verificados decaem mais lento
    usage_in_briefing: 0.8       # se foi usado recentemente via briefing
    cross_session_sighting: 0.75 # observado em múltiplas sessões

  thresholds:
    fresh: 1.0                   # recém-observado ou reinforced
    active: 0.8                  # uso regular (>= 0.8)
    fading: 0.5                  # ainda no briefing com warning (>= 0.5)
    archive: 0.1                 # movido para archive/ [0.05, 0.1)
    delete: 0.05                 # removido permanentemente [0, 0.05)

  decay_rates:
    general: 0.05                # ~60 dias até delete
    verified: 0.025              # ~120 dias (2x mais lento)

  veto_conditions:
    - condition: "pattern_verified_and_score_below_archive"
      action: "WARN — Pattern verificado em decay. Considere reforço antes de archive."
    - condition: "all_patterns_below_fading"
      action: "ALERTA — Nenhum pattern ativo no briefing. Base de conhecimento pode estar estagnada."
    - condition: "pattern_used_today_but_score_was_archive"
      action: "RESCUE — Resgatar do archive, resetar score para 1.0."

  decision_tree:
    - IF score >= 0.8 THEN active_pattern_keep_in_briefing
    - IF score >= 0.5 AND score < 0.8 THEN fading_pattern_include_with_warning
    - IF score >= 0.1 AND score < 0.5 THEN intermediate_pattern_exclude_from_briefing
    - IF score >= 0.05 AND score < 0.1 THEN archive_pattern_move_to_archive
    - IF score < 0.05 THEN delete_pattern_remove_permanently
    - TERMINATION: all_patterns_assessed_and_actioned
```

## Assessment Framework

```text
PASSO 1: Coletar Dados
  - Para cada pattern: last_reinforced, verification_count, decay_rate
  - Calcular: days_since_reinforced = today - last_reinforced

PASSO 2: Calcular Score
  - decay_score = e^(-rate × days_since_reinforced)
  - rate = 0.025 se verified, 0.05 se general

PASSO 3: Classificar
  - Fresh (1.0): recém-reforçado
  - Active (>=0.8): uso regular, incluir no briefing
  - Fading (>=0.5 e <0.8): ainda no briefing com warning
  - Intermediate (>=0.1 e <0.5): fora do briefing, ainda acessível
  - Archive (>=0.05 e <0.1): mover para archive/
  - Delete (<0.05): remover permanentemente

PASSO 4: Agir
  - Archive: mover entry para archive/YYYY-MM.yaml
  - Delete: remover de archive/ após confirmação
  - Rescue: se pattern archivado é re-observado, trazer de volta
```

## Examples

### Pattern Fresh (score 1.0)
- **Observado:** hoje, em daily capture
- **Ação:** Manter no topo do briefing

### Pattern em Decay (score 0.22)
- **Observado:** 30 dias atrás, 0 usos desde então
- **Rate:** general (0.05)
- **Cálculo:** e^(-0.05 × 30) = 0.22
- **Classificação:** Intermediate (>= 0.1 e < 0.5)
- **Ação:** Excluir do briefing, manter acessível. Abaixo do threshold fading (0.5) mas acima do archive (0.1).

### Pattern Verified em Decay Lento (score 0.47)
- **Observado:** 30 dias atrás, verified
- **Rate:** verified (0.025)
- **Cálculo:** e^(-0.025 × 30) = 0.47
- **Classificação:** Intermediate (>= 0.1 e < 0.5)
- **Ação:** Excluir do briefing, manter acessível. Mesmo verificado, score abaixo de fading (0.5) mas acima do archive (0.1). Decay 2x mais lento por ser verificado.

---

**Pattern Compliance:** HE-CORE-001 (Forgetting Curve)
**Source:** HE Mind DNA - Decay Assessment Heuristic
