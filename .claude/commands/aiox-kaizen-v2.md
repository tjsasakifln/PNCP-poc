# /aiox-kaizen-v2 — Activate Continuous Intelligence + Memory Squad

**Squad:** aiox-kaizen-v2 (vendored from SynkraAI/aiox-squads + SmartLic overlay)

**File:** `squads/aiox-kaizen-v2/squad.yaml` + `squads/aiox-kaizen-v2/config/smartlic-overlay.yaml`

KAIZEN-V2 vigia continuamente o ecossistema AIOS/AIOX do projeto, captura aprendizado diário via hooks (Stop + SessionStart), aplica Ebbinghaus forgetting curve aos patterns, e injeta top-5 active patterns em cada nova sessão. Integra com synapse-engine.cjs existente em SmartLic (coexistência, não substituição).

## Como invocar

```
/aiox-kaizen-v2
```

## Leitura obrigatória antes de agir

1. **`squads/_shared/invariants.md`** — invariantes que kaizen deve validar continuamente
2. **`.claude/hooks/synapse-engine.cjs`** — engine existente que kaizen complementa
3. **`squads/aiox-kaizen-v2/squad.yaml`** — definição upstream
4. **`squads/aiox-kaizen-v2/config/smartlic-overlay.yaml`** — áreas de monitoramento priorizadas (CI drift, LLM SLO, deploy health)
5. **`squads/aiox-kaizen-v2/agents/memory-keeper.smartlic.md`** — encoding criteria + promote pipeline
6. **`squads/aiox-kaizen-v2/hooks/session-start-briefing.md`** — integração com `.claude/hooks/squads-briefing.cjs`

## Cadência

- **Weekly tick**: domingo 20:00 BRT (via cron)
- **Session-triggered**: SessionStart hook injeta top-5 patterns (<2KB)
- **Real-time**: alerta Sentry se invariante crítico falha

## Encoding criteria (antes de salvar pattern)

Um pattern DEVE passar nos 5 critérios:
1. **Verified**: validado empiricamente
2. **Non-obvious**: surpreende vs código atual
3. **Reusable**: aplicável em >1 story/sessão
4. **Actionable**: sugere ação concreta
5. **Empirical**: baseado em dado/incident

Se falha em QUALQUER: **NÃO** captura.

## Quando este squad é apropriado

- Análise de saúde do ecossistema (monthly/quarterly)
- Identificar gaps em coverage (áreas sem atenção)
- Capturar lição aprendida de incidente
- Validar que patterns conhecidos ainda são válidos

## Quando NÃO usar

- Bug urgente → `/squad-creator` com `bidiq-hotfix`
- Planejamento de sprint → `@sm` + `@pm`

## Memory decay

```
R(t) = exp(-t/S)
```
Patterns com R(t) < 0.2 movem para `.synapse/archive/YYYY-MM/`. Reinforcement (+1 strength) quando pattern é citado em PR ou reusado em nova sessão.

## Delegação

- Gap detectado → criar story via `@sm`
- Deploy issue identificado → `@devops`
- Pattern precisa validação com dados → `/aiox-deep-research`
