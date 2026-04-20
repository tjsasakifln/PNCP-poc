# LM_CR_001 — Capture-Reflect Quality Gate

**Type:** Decision Heuristic
**Phase:** Daily Intelligence Pipeline
**Agent:** @kaizen-v2:memory-keeper
**Pattern:** LM-CORE-001 (Claude-Diary)

## Purpose

Heurístico para avaliar a qualidade do pipeline capture-reflect. Determina se o daily capture tem sinais suficientes, se o reflect está extraindo patterns reais, e se o briefing é útil.

## Configuration

```yaml
LM_CR_001:
  name: "Capture-Reflect Quality Gate"
  phase: "daily-intelligence"
  pattern_reference: "LM-CORE-001"

  weights:
    learning_signals_detected: 0.9   # dailies devem ter learning signals
    decision_signals_detected: 0.8   # decisões são valiosas
    pattern_extraction_rate: 0.85    # % de reflects que geram patterns
    briefing_utility: 0.75           # briefing deve ter >= 3 patterns

  thresholds:
    min_learnings_per_daily: 1       # pelo menos 1 learning por sessão
    min_patterns_active: 3           # mínimo de patterns ativos no briefing
    max_briefing_size_kb: 2          # limite de context injection
    min_reflect_frequency_days: 7    # reflect deve rodar pelo menos semanalmente
    max_stale_dailies: 14            # dailies sem reflect > 14 dias = problema

  veto_conditions:
    - condition: "zero_dailies_in_7_days"
      action: "ALERTA — Stop hook pode não estar funcionando. Rodar *health."
    - condition: "reflect_never_ran"
      action: "ALERTA — Sem reflect, dailies acumulam sem processamento. Rodar *reflect."
    - condition: "briefing_empty"
      action: "WARN — Briefing vazio. Verificar patterns.yaml ou rodar *reflect."
    - condition: "all_patterns_below_0.3"
      action: "WARN — Nenhum pattern no briefing. Base de conhecimento estagnada."

  decision_tree:
    - IF dailies_count_7d >= 3 AND patterns_active >= 3 THEN healthy_pipeline
    - IF dailies_count_7d >= 3 AND patterns_active < 3 THEN needs_reflect
    - IF dailies_count_7d < 3 AND dailies_count_7d > 0 THEN low_capture_rate
    - IF dailies_count_7d == 0 THEN capture_broken_check_hooks
    - TERMINATION: pipeline_health_assessed
```

## Assessment Framework

```text
PASSO 1: Verificar Capture
  - Quantos dailies nos últimos 7 dias?
  - Média de learnings por daily?
  - Stop hook está registrado e funcional?

PASSO 2: Verificar Reflect
  - Quando foi o último reflect?
  - Quantos patterns foram extraídos/reinforced?
  - Existe dailies não processados?

PASSO 3: Verificar Brief
  - Briefing atual tem quantos patterns?
  - Tamanho do briefing (deve ser <= 2KB)?
  - Patterns são relevantes (score > 0.3)?

PASSO 4: Diagnóstico
  - Healthy: 3+ dailies/semana, 3+ patterns ativos
  - Needs Reflect: dailies ok mas patterns estagnados
  - Low Capture: poucos dailies, verificar hooks
  - Broken: zero dailies, hooks não funcionando
```

---

**Pattern Compliance:** LM-CORE-001 (Claude-Diary)
**Source:** LM Mind DNA - Capture-Reflect Heuristic
