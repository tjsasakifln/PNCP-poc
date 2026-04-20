# Framework Primário: Claude-Diary (Capture → Reflect → Brief)

**Type:** Primary Operating Framework
**Agent:** @kaizen-v2:memory-keeper
**Status:** Implementado no kaizen-v2 via hooks + workflows

## Overview

O padrão Claude-Diary resolve o problema fundamental de agentes de IA: sessões são efêmeras. Sem um sistema de captura e reflexão, cada sessão começa do zero. O framework implementa 3 fases em ciclo contínuo: Capture (gravar), Reflect (extrair), Brief (injetar).

## Framework 1: O Ciclo Capture → Reflect → Brief

```text
CAPTURE (Stop Hook — automático)
  Trigger: Fim de sessão
  Input: stdin JSON (session_id, last_assistant_message)
  Process:
    1. Detectar learning signals ("descobri", "padrão é", "aprendi")
    2. Detectar decision signals ("decidimos", "vamos usar", "optamos")
    3. Extrair agentes mencionados (@agent-name)
    4. Git log do dia (commits, files changed)
  Output: daily/YYYY-MM-DD.yaml

REFLECT (Overnight — cron ou manual)
  Trigger: Cron 2am ou *reflect
  Input: Últimos 7 dailies + patterns.yaml existente
  Process:
    1. Extrair learning candidates
    2. Validar contra 5 critérios (verified, non-obvious, reusable, actionable, empirical)
    3. Patterns novos → add com score 1.0
    4. Patterns existentes → reforço (reset decay)
    5. Recalcular decay de todos
  Output: patterns.yaml atualizado + reflection-YYYY-MM-DD.md

BRIEF (SessionStart Hook — automático)
  Trigger: Início de sessão
  Input: patterns.yaml
  Process:
    1. Filtrar patterns com score > 0.3
    2. Ordenar por score descendente
    3. Top 5 + últimas 3 dailies summary
    4. Truncar para <= 2KB
  Output: additionalContext injection
```

## Framework 2: Learning Signal Detection

```text
LEARNING SIGNALS (capturados no daily):
  - "descobri que", "percebi que", "aprendi que"
  - "o padrão é", "a causa é", "o motivo é"
  - "funciona porque", "não funciona porque"
  - "melhor abordagem é", "solução é"

DECISION SIGNALS (capturados no daily):
  - "decidimos", "vamos usar", "optamos por"
  - "a estratégia é", "o plano é"
  - "escolhemos", "priorizamos"

AGENT SIGNALS (capturados no daily):
  - Regex: @[a-z0-9\-:]+ no last_assistant_message
  - Indica quais agentes participaram da sessão
```

## Diagnostic Questions

1. "O Stop hook está capturando dailies consistentemente?"
2. "Quantos learnings foram extraídos na última semana?"
3. "Quantos patterns foram reinforced vs. decayed?"
4. "O briefing está injetando contexto útil no início das sessões?"
5. "O tamanho do briefing está dentro do limite de 2KB?"

---

**Pattern Compliance:** Claude-Diary (Capture-Reflect-Brief)
**Source:** LM Mind DNA - Framework Primary
