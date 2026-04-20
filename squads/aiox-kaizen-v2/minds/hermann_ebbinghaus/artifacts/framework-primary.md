# Framework Primário: Forgetting Curve & Spaced Repetition

**Type:** Primary Operating Framework
**Agent:** @kaizen-v2:memory-keeper
**Status:** Validado experimentalmente (1885), replicado em centenas de estudos

## Overview

A Forgetting Curve é o modelo matemático que descreve como a memória decai exponencialmente ao longo do tempo sem reforço. No kaizen-v2, é aplicada a patterns de aprendizado de agentes de IA: cada pattern tem um decay_score que diminui com o tempo e reseta quando o pattern é reutilizado.

## Framework 1: A Curva de Esquecimento

```text
FÓRMULA: R = e^(-t/S)

Onde:
  R = Retenção (0.0 a 1.0)
  t = Tempo desde última revisão
  S = Força da memória (aumenta com repetições)

KAIZEN-V2 ADAPTAÇÃO:
  decay_score = e^(-rate × days_since_observed)

  rate_general  = 0.05   (~60 dias até score 0.05)
  rate_verified = 0.025  (~120 dias, 2x mais lento)
```

## Framework 2: Repetição Espaçada

```text
PRINCÍPIO: Revisões em intervalos crescentes consolidam memória

INTERVALOS ÓTIMOS (Ebbinghaus):
  1. Imediato (dentro da sessão)
  2. 1 dia depois
  3. 3 dias depois
  4. 7 dias depois
  5. 21 dias depois
  6. 60 dias depois

KAIZEN-V2 APLICAÇÃO:
  - Briefing diário = revisão automática (SessionStart hook)
  - Pattern usado pelo agente = reforço natural
  - Reflect semanal = revisão sistemática de todos patterns
  - Decay < 0.3 = pattern sai do briefing (sem revisão)
  - 0.05 <= Decay < 0.1 = archive (esquecimento funcional)
  - Decay < 0.05 = delete (esquecimento completo)
```

## Framework 3: Lifecycle de Retenção

```text
ESTADO         DECAY     AÇÃO NO KAIZEN-V2
─────────────────────────────────────────
FRESH          1.00      Pattern ativo no briefing
ATIVO          0.70      Aparece normalmente
MORNO          0.50      Ainda no briefing
FRIO           0.22      Sai do briefing (< 0.3)
ARCHIVE        0.05-0.10 Movido para archive/
DELETE         <0.05     Removido do sistema
```

## Application

**Input:** Pattern observado em daily capture ou sessão.

**Process:**
1. Pattern extraído → decay_score = 1.0 (fresh)
2. Cada dia sem uso → score decai exponencialmente
3. Cada uso/observação → score reseta para 1.0
4. Reflect overnight → recalcula todos os scores
5. Score < threshold → ação automática (archive/delete)

## Diagnostic Questions

1. "Quantos dias desde a última observação desse pattern?"
2. "O pattern foi verificado em múltiplas sessões independentes?"
3. "O pattern aparece no briefing atual? (score > 0.3)"
4. "Qual a taxa de decay — geral (0.05) ou verificado (0.025)?"
5. "Existem patterns em archive que deveriam ser resgatados?"

---

**Pattern Compliance:** Ebbinghaus Forgetting Curve (1885)
**Source:** HE Mind DNA - Framework Primary
